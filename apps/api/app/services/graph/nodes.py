import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_openai import ChatOpenAI

from app.core.log import get_logger
from app.core.settings import settings
from app.services.graph.state import (
    ToTChatState, ToTThought, ThoughtEvaluation,
    GenerateThoughtsResponse, EvaluateThoughtResponse, SynthesizeResponse,
)
from app.services.tools.runner import execute_tool
from app.services.tools.code_graph import generate_mermaid_callflow
from app.services.graph.prompts import (
    generate_thoughts_prompt,
    evaluate_thought_prompt,
    synthesize_prompt,
    fallback_answer,
)

logger = get_logger(__name__)


# ── Hybrid scoring helpers ──────────────────────


def compute_source_diversity(thought: ToTThought, all_thoughts: dict[str, ToTThought]) -> float:
    unique_files: set[str] = set(thought.accessed_files)
    ancestor = thought.parent_id
    seen = set()
    while ancestor and ancestor not in seen:
        seen.add(ancestor)
        parent = all_thoughts.get(ancestor)
        if parent:
            unique_files.update(parent.accessed_files)
            ancestor = parent.parent_id
        else:
            break
    count = len(unique_files)
    return min(1.0, count / 3.0)


def compute_hybrid_score(
    llm_relevance: float,
    llm_evidence_strength: float,
    source_diversity: float,
) -> float:
    return 0.5 * llm_relevance + 0.3 * llm_evidence_strength + 0.2 * source_diversity


# ── Serialization helpers (ToTThought ↔ dict for MemorySaver) ────────────────

def _get_thoughts(raw: dict[str, dict]) -> dict[str, ToTThought]:
    """Inflate raw state thoughts dict back into ToTThought objects."""
    return {k: ToTThought(**v) if isinstance(v, dict) else v for k, v in raw.items()}


def _dump_thoughts(thoughts: dict[str, ToTThought]) -> dict[str, dict]:
    """Flatten ToTThought objects into plain dicts for squeaky-clean checkpoints."""
    return {k: v.model_dump() for k, v in thoughts.items()}


# ── Generate ──────────────────────────────────────────────────────────────────

def generate_thoughts(state: ToTChatState) -> dict:
    """BFS Step 1: Generate exploration thoughts (initial or re-generation).

    If state already has thoughts, it's a re-generation — new thoughts are merged
    in, depth is preserved, and previously tried angles are included in the prompt.
    """
    existing = _get_thoughts(state.get("thoughts", {}))
    current_depth = state.get("depth", 1)

    llm = ChatOpenAI(
        model=settings.generation_llm_model,
        api_key=settings.github_token or None,
        base_url="https://models.inference.ai.azure.com",
        temperature=settings.generation_llm_temperature,
        max_tokens=settings.generation_llm_max_tokens,
    )
    prompt = generate_thoughts_prompt(state)

    sllm = llm.with_structured_output(GenerateThoughtsResponse)
    try:
        resp = sllm.invoke(prompt)
    except Exception as e:
        logger.warning("generate_thoughts LLM failed: %s", e)
        resp = None

    if not resp or not resp.angles:
        fallback = fallback_generate(state)
        new_thoughts = _get_thoughts(fallback.get("thoughts", {}))
        new_pending = fallback.get("pending_ids", [])
    else:
        new_thoughts = {}
        new_pending = []
        for i in range(len(resp.angles)):
            tid = str(uuid.uuid4())[:8]
            tool = resp.tools[i] if i < len(resp.tools) else "grep"
            target = resp.targets[i] if i < len(resp.targets) else ""
            hypothesis = resp.hypotheses[i] if i < len(resp.hypotheses) else resp.angles[i]
            expected = resp.expected_evidences[i] if i < len(resp.expected_evidences) else ""
            new_thoughts[tid] = ToTThought(
                id=tid, parent_id="",
                angle=resp.angles[i],
                hypothesis=hypothesis,
                tool=tool,
                target=target,
                expected_evidence=expected,
            )
            new_pending.append(tid)

    return {
        "thoughts": _dump_thoughts(existing | new_thoughts),
        "pending_ids": state.get("pending_ids", []) + new_pending,
        "best_ids": state.get("best_ids", []),
        "rejected_ids": state.get("rejected_ids", []),
        "uncertainties": state.get("uncertainties", []),
        "depth": current_depth,
    }


def fallback_generate(state: ToTChatState) -> dict:
    query = state["user_query"].lower()
    words = re.findall(r'\w+', query)
    important = [w for w in words if len(w) > 2][:4]

    searches: list[tuple[str, str, str, str, str]] = []

    if any(w in query for w in ["package", "library", "depend", "import", "setup"]):
        searches.append(("Dependency declarations", "Projects declare deps in requirements files", "glob", "*requirements*", "pinned dependency lines"))
        searches.append(("Project config", "pyproject.toml contains metadata and deps", "read_file", "pyproject.toml", "project metadata and dependency entries"))
    elif any(w in query for w in ["auth", "login", "user", "password", "token"]):
        searches.append(("Auth files", "Auth-related files exist in the codebase", "glob", "*auth*", "files with auth in the name"))
        searches.append(("Auth patterns", "Auth uses tokens, JWTs, or sessions", "grep", "authenticate|login|jwt|token|password", "lines showing auth implementation"))
    elif any(w in query for w in ["api", "route", "endpoint"]):
        searches.append(("Route definitions", "Routes are defined via decorators", "grep", r"@(?:app|router)\.(?:get|post|put|delete)", "route decorator lines"))
        searches.append(("API files", "Router/route files exist", "glob", "*route*", "route definition files"))
    elif any(w in query for w in ["test"]):
        searches.append(("Test files", "Test files exist with standard naming", "glob", "*test*", "test files"))
        searches.append(("Test config", "Test fixtures in conftest.py", "glob", "conftest.py", "test configuration"))
    elif any(w in query for w in ["config", "setting", "env"]):
        searches.append(("Config files", "Dotenv or config files exist", "glob", ".env*", "environment configuration"))
        searches.append(("Configuration", "Config modules or files exist", "glob", "*config*", "configuration files"))
    else:
        for word in important[:3]:
            searches.append((f"Keyword '{word}'", f"Searching for '{word}' in codebase", "grep", word, f"references to {word}"))
        searches.append(("Project structure", "Python files reveal project layout", "glob", "*.py", "project file listing"))

    thoughts = {}
    pending = []
    for i, (angle, hypothesis, tool, target, expected) in enumerate(searches[:4]):
        tid = str(uuid.uuid4())[:8]
        thoughts[tid] = ToTThought(
            id=tid, parent_id="",
            angle=angle,
            hypothesis=hypothesis,
            tool=tool,
            target=target,
            expected_evidence=expected,
        )
        pending.append(tid)

    return {
        "thoughts": _dump_thoughts(thoughts),
        "pending_ids": pending,
        "best_ids": [],
        "rejected_ids": [],
        "uncertainties": [],
        "depth": 1,
    }


# ── Execute ───────────────────────────────────────────────────────────────────

def execute_batch(state: ToTChatState) -> dict:
    """BFS Step 2: Execute ALL pending incomplete thoughts (parallelized)."""
    all_thoughts = _get_thoughts(state.get("thoughts", {}))
    pending = list(state.get("pending_ids", []))
    repo_path = state["repo_path"]

    to_execute = [
        tid for tid in pending
        if tid in all_thoughts and not all_thoughts[tid].is_complete
    ]

    if not to_execute:
        return {}

    with ThreadPoolExecutor(max_workers=settings.execution_workers) as pool:
        futures = {
            pool.submit(execute_tool, all_thoughts[tid].tool, all_thoughts[tid].target, repo_path): tid
            for tid in to_execute
        }
        for future in as_completed(futures):
            tid = futures[future]
            try:
                outcome, accessed = future.result()
            except Exception as e:
                outcome, accessed = f"Tool error: {e}", []
            thought = all_thoughts[tid]
            thought.outcome = outcome
            thought.accessed_files = accessed
            thought.is_complete = True
            all_thoughts[tid] = thought

    return {"thoughts": _dump_thoughts(all_thoughts)}


# ── Evaluate ──────────────────────────────────────────────────────────────────

def evaluate_batch(state: ToTChatState) -> dict:
    """BFS Step 3: Evaluate ALL completed but unevaluated thoughts (parallelized LLM calls).

    Uses LLM for relevance + evidence strength (qualitative),
    then computes source diversity (deterministic),
    then combines into a hybrid weighted score.
    """
    all_thoughts = _get_thoughts(state.get("thoughts", {}))
    pending = list(state.get("pending_ids", []))
    query = state["user_query"]
    evaluated_ids = state.get("evaluated_ids", [])

    to_evaluate = [
        tid for tid in pending
        if tid in all_thoughts
        and all_thoughts[tid].is_complete
        and tid not in evaluated_ids
    ]

    if not to_evaluate:
        return {}

    llm = ChatOpenAI(
        model=settings.evaluation_llm_model,
        api_key=settings.github_token or None,
        base_url="https://models.inference.ai.azure.com",
        temperature=settings.evaluation_llm_temperature,
        max_tokens=settings.evaluation_llm_max_tokens,
    )
    sllm = llm.with_structured_output(EvaluateThoughtResponse)

    # Parallel LLM calls with small worker pool to respect rate limits
    llm_results: dict[str, EvaluateThoughtResponse | None] = {}
    with ThreadPoolExecutor(max_workers=settings.evaluation_workers) as pool:
        futures = {
            pool.submit(sllm.invoke, evaluate_thought_prompt(query, all_thoughts[tid])): tid
            for tid in to_evaluate
        }
        for future in as_completed(futures):
            tid = futures[future]
            try:
                llm_results[tid] = future.result()
            except Exception as e:
                logger.warning("evaluate thought %s LLM failed: %s", tid, e)
                llm_results[tid] = None

    new_evaluated = list(evaluated_ids)
    uncertainties = list(state.get("uncertainties", []))

    for tid in to_evaluate:
        thought = all_thoughts[tid]
        resp = llm_results[tid]

        if resp is None:
            resp = EvaluateThoughtResponse(
                relevance=50, evidence_strength=30,
                reasoning="Evaluation failed, using moderate scores.",
                ready_to_synthesize=False,
            )

        relevance = float(resp.relevance)
        evidence_strength = float(resp.evidence_strength)
        if relevance > 1:
            relevance /= 100
        if evidence_strength > 1:
            evidence_strength /= 100

        source_diversity = compute_source_diversity(thought, all_thoughts)
        overall_score = compute_hybrid_score(relevance, evidence_strength, source_diversity)

        thought.evaluation = ThoughtEvaluation(
            relevance=relevance,
            evidence_strength=evidence_strength,
            source_diversity=source_diversity,
            overall_score=overall_score,
            reasoning=resp.reasoning,
        )

        thought.follow_up_tools = resp.follow_up_tools
        thought.follow_up_targets = resp.follow_up_targets
        thought.follow_up_angles = resp.follow_up_angles
        thought.follow_up_hypotheses = resp.follow_up_hypotheses
        thought.follow_up_expected_evidences = resp.follow_up_expected_evidences
        thought.ready_to_synthesize = resp.ready_to_synthesize

        if resp.uncertainty:
            entry = f"[{tid}] {thought.angle}: {resp.uncertainty}"
            if entry not in uncertainties:
                uncertainties.append(entry)

        all_thoughts[tid] = thought
        new_evaluated.append(tid)

    return {
        "thoughts": _dump_thoughts(all_thoughts),
        "evaluated_ids": new_evaluated,
        "uncertainties": uncertainties,
    }


# ── Prune & Expand ────────────────────────────────────────────────────────────

def prune_expand(state: ToTChatState) -> dict:
    """BFS Step 4: Prune low-scoring, expand high-scoring thoughts.

    - Score < 0.4: Prune (reject, do not expand)
    - Score 0.4-0.7: Keep in best_ids, no expansion
    - Score >= 0.7 AND depth < max_depth: Keep + expand with children
    """
    all_thoughts = _get_thoughts(state.get("thoughts", {}))
    pending = list(state.get("pending_ids", []))
    best_ids = list(state.get("best_ids", []))
    rejected_ids = list(state.get("rejected_ids", []))
    current_depth = state.get("depth", 1)
    max_depth = state.get("max_depth", 3)
    max_children = state.get("max_children", 2)
    keep_top_k = state.get("keep_top_k", 5)

    new_thoughts: dict[str, ToTThought] = {}
    new_pending: list[str] = []
    expanded = False

    for tid in pending:
        if tid not in all_thoughts:
            continue
        thought = all_thoughts[tid]
        if not thought.evaluation:
            best_ids.append(tid)
            continue

        score = thought.evaluation.overall_score

        if score < 0.4:
            thought.is_pruned = True
            all_thoughts[tid] = thought
            rejected_ids.append(tid)
            best_ids = [b for b in best_ids if b != tid]

        elif score >= 0.7 and current_depth < max_depth and not thought.ready_to_synthesize:
            expanded = True
            best_ids.append(tid)

            angles = getattr(thought, "follow_up_angles", None) or []
            tools = getattr(thought, "follow_up_tools", None) or []
            targets = getattr(thought, "follow_up_targets", None) or []
            hypotheses = getattr(thought, "follow_up_hypotheses", None) or []
            expected_evidences = getattr(thought, "follow_up_expected_evidences", None) or []

            child_count = min(len(angles), max_children) if angles else 0
            children = []
            for i in range(child_count):
                cid = str(uuid.uuid4())[:8]
                tool = tools[i] if i < len(tools) else "grep"
                target = targets[i] if i < len(targets) else ""
                hypothesis = hypotheses[i] if i < len(hypotheses) else ""
                expected = expected_evidences[i] if i < len(expected_evidences) else ""
                child = ToTThought(
                    id=cid, parent_id=tid,
                    angle=angles[i] if angles else "",
                    hypothesis=hypothesis,
                    tool=tool,
                    target=target,
                    expected_evidence=expected,
                )
                new_thoughts[cid] = child
                new_pending.append(cid)
                children.append(cid)

            thought.child_ids = children
            all_thoughts[tid] = thought

        else:
            best_ids.append(tid)

    all_thoughts.update(new_thoughts)

    next_pending = new_pending if expanded else []
    next_depth = current_depth + 1 if expanded else current_depth

    scored_best = [
        (bid, all_thoughts[bid]) for bid in best_ids
        if bid in all_thoughts and all_thoughts[bid].evaluation
    ]
    scored_best.sort(key=lambda x: x[1].evaluation.overall_score, reverse=True)
    keep_count = max(1, keep_top_k)
    trimmed_best = [bid for bid, _ in scored_best[:keep_count]]

    return {
        "thoughts": _dump_thoughts(all_thoughts),
        "pending_ids": next_pending,
        "best_ids": trimmed_best,
        "rejected_ids": rejected_ids,
        "depth": next_depth,
    }


def decide_loop(state: ToTChatState) -> str:
    """BFS Step 5 decision: continue, re-generate, or synthesize.

    Returns one of:
      - "execute_batch"    → continue BFS as usual
      - "generate_thoughts" → all branches dead, try fresh angles
      - "synthesize"        → enough evidence or budget exhausted
    """
    pending = state.get("pending_ids", [])
    depth = state.get("depth", 1)
    max_depth = state.get("max_depth", 3)

    # Gap A: All branches pruned — try fresh generation if budget remains
    if not pending and depth < max_depth:
        logger.info("All branches pruned at depth %s/%s — re-generating", depth, max_depth)
        return "generate_thoughts"

    # Gap C: Early termination if most best branches are ready to synthesize
    best_ids = state.get("best_ids", [])
    if depth >= 2 and best_ids:
        thoughts = _get_thoughts(state.get("thoughts", {}))
        ready_count = sum(
            1 for tid in best_ids
            if tid in thoughts and thoughts[tid].ready_to_synthesize
        )
        ready_pct = ready_count / len(best_ids)
        if ready_pct >= 0.7:
            logger.info(
                "Early termination: %.0f%% best branches ready at depth %s",
                ready_pct * 100, depth,
            )
            return "synthesize"

    # Normal BFS continuation
    if pending and depth <= max_depth:
        logger.info("BFS loop: depth=%s/%s, pending=%s", depth, max_depth, len(pending))
        return "execute_batch"

    logger.info("BFS done: depth=%s/%s, pending=%s → synthesize", depth, max_depth, len(pending))
    return "synthesize"


# ── Synthesize ────────────────────────────────────────────────────────────────

def synthesize(state: ToTChatState) -> dict:
    """BFS Final: Generate comprehensive answer from best thoughts."""
    query = state["user_query"]
    best_ids = state.get("best_ids", [])
    rejected_ids = state.get("rejected_ids", [])
    uncertainties = state.get("uncertainties", [])
    thoughts = _get_thoughts(state.get("thoughts", {}))

    best_thoughts = [thoughts[tid] for tid in best_ids if tid in thoughts]
    rejected_thoughts = [thoughts[tid] for tid in rejected_ids if tid in thoughts]

    if not best_thoughts:
        best_thoughts = [
            t for t in thoughts.values()
            if t.is_complete and t.evaluation and t.evaluation.overall_score > 0
        ]

    if not best_thoughts:
        return {
            "answer": fallback_answer(query),
        }

    evidence_parts = []
    citations: list[str] = []
    for t in best_thoughts:
        angle = t.angle
        outcome = t.outcome[:600] if t.outcome else "(no results)"
        score = t.evaluation.overall_score if t.evaluation else 0.0
        evidence_parts.append(
            f"--- {angle} (score: {score:.2f}) ---\n"
            f"Hypothesis: {t.hypothesis}\n"
            f"{outcome}"
        )
        for af in t.accessed_files[:5]:
            citation = f"{af} (from: {angle})"
            if citation not in citations:
                citations.append(citation)

    evidence_text = "\n\n".join(evidence_parts)

    rejected_text = ""
    if rejected_thoughts:
        lines = []
        for t in rejected_thoughts:
            reason = t.evaluation.reasoning[:120] if t.evaluation and t.evaluation.reasoning else "low score"
            lines.append(f"  - {t.angle}: {t.hypothesis[:80]} → pruned: {reason}")
        rejected_text = "\nRejected branches:\n" + "\n".join(lines)

    uncertainty_text = ""
    if uncertainties:
        uncertainty_text = "\nUncertainties:\n" + "\n".join(f"  - {u}" for u in uncertainties)

    mermaid_diagram = generate_mermaid_callflow(max_nodes=30)
    mermaid_text = f"\nArchitecture call-flow diagram:\n{mermaid_diagram}\n" if mermaid_diagram else ""

    llm = ChatOpenAI(
        model=settings.synthesis_llm_model,
        api_key=settings.github_token or None,
        base_url="https://models.inference.ai.azure.com",
        temperature=settings.synthesis_llm_temperature,
        max_tokens=settings.synthesis_llm_max_tokens,
    )
    sllm = llm.with_structured_output(SynthesizeResponse)

    prompt = synthesize_prompt(query, evidence_text, rejected_text, uncertainty_text, mermaid_text)

    rejected_branches = ""
    uncertainties_summary = ""
    citations = []
    try:
        resp = sllm.invoke(prompt)
        answer = resp.answer
        citations = resp.citations
        rejected_branches = resp.rejected_branches_summary
        uncertainties_summary = resp.uncertainties
    except Exception as e:
        logger.warning("synthesize LLM failed: %s", e)
        answer = fallback_synthesize(query, best_thoughts, rejected_thoughts, uncertainties)

    return {
        "answer": answer,
        "citations": citations,
        "rejected_branches_summary": rejected_branches,
        "uncertainties_summary": uncertainties_summary,
    }


def fallback_synthesize(
    query: str,
    best_thoughts: list[ToTThought],
    rejected_thoughts: list[ToTThought],
    uncertainties: list[str],
) -> str:
    parts = [f"Findings for '{query}':\n"]
    for t in best_thoughts:
        score = t.evaluation.overall_score if t.evaluation else 0.0
        outcome_preview = (t.outcome[:300] + "...") if t.outcome and len(t.outcome) > 300 else (t.outcome or "")
        parts.append(f"  \u2022 {t.angle} (score: {score:.2f})")
        if outcome_preview:
            parts.append(f"    {outcome_preview}")

    if rejected_thoughts:
        parts.append("\nRejected/Pruned paths:")
        for t in rejected_thoughts:
            parts.append(f"  \u2013 {t.angle}: {t.hypothesis[:80]}")

    if uncertainties:
        parts.append("\nUncertainties:")
        for u in uncertainties:
            parts.append(f"  \u2013 {u}")

    return "\n".join(parts)
