import os
from datetime import datetime, timezone

from app.core.log import get_logger
from app.core.settings import settings
from app.services.graph.state import ToTChatState, ToTThought
from app.services.graph.graph_builder import build_tot_chat_graph
from app.services.tools.code_graph import build_code_graph
from app.services.infra.events import add_event, ChatSSEEvent
from app.services.infra.clone import resolve_repo_path, TEMP_DIRS


logger = get_logger(__name__)

_tot_graph = build_tot_chat_graph()
CHAT_RESULTS: dict[str, str] = {}


def _to_thought(obj):
    return ToTThought(**obj) if isinstance(obj, dict) else obj


def _build_initial_state(query: str, repo_path: str, max_depth: int, max_children: int, keep_top_k: int) -> ToTChatState:
    return {
        "user_query": query, "repo_path": repo_path, "session_id": "",
        "thoughts": {}, "pending_ids": [], "best_ids": [], "rejected_ids": [],
        "current_id": "", "depth": 1, "max_depth": max_depth, "max_children": max_children,
        "keep_top_k": keep_top_k,
        "answer": "", "error": "", "uncertainties": [], "evaluated_ids": [],
    }


def _log_tree(session_id: str, thoughts: dict, best_ids: list, rejected_ids: list, pending_ids: list, depth: int):
    try:
        tree_lines = [f"[{session_id}] ToT tree at depth={depth}:"]
        thought_objs = {k: _to_thought(v) for k, v in thoughts.items()}
        roots = [t for t in thought_objs.values() if not t.parent_id]
        tree_lines.append(f"  roots={len(roots)}, total={len(thought_objs)}, best={len(best_ids)}, rejected={len(rejected_ids)}, pending={len(pending_ids)}")

        def _dump(node: ToTThought, indent: int = 1):
            score = node.evaluation.overall_score if node.evaluation else 0.0
            status = "PRUNED" if node.is_pruned else f"score={score:.2f}"
            children = [thought_objs[cid] for cid in node.child_ids if cid in thought_objs]
            tree_lines.append(f"  {'  ' * indent}\u2514\u2500 {node.id[:6]} [{node.angle[:40]}] {status}")
            for child in children:
                _dump(child, indent + 1)

        for root in roots:
            _dump(root)
        logger.info("\n".join(tree_lines))
    except Exception as e:
        logger.debug("[%s] Tree log failed: %s", session_id, e)


def _emit_generate(session_id: str, update: dict, emitted_ids: set[str]):
    thoughts = update.get("thoughts", {})
    gen_depth = update.get("depth", 1)
    for tid, raw in thoughts.items():
        thought = _to_thought(raw)
        emitted_ids.add(tid)
        add_event(session_id, ChatSSEEvent.THOUGHT_GENERATED, {
            "id": tid, "parent_id": thought.parent_id or "", "depth": gen_depth,
            "description": thought.angle or "", "hypothesis": thought.hypothesis or "",
            "tool": thought.tool, "target": thought.target,
            "expected_evidence": thought.expected_evidence or "",
        })
    add_event(session_id, ChatSSEEvent.STATE, {
        "phase": "generate_thoughts", "pending": len(update.get("pending_ids", [])),
    })
    _log_tree(session_id, thoughts, update.get("best_ids", []), update.get("rejected_ids", []), update.get("pending_ids", []), gen_depth)


def _emit_execute(session_id: str, update: dict):
    executed = update.get("thoughts", {})
    for tid, raw in executed.items():
        t = _to_thought(raw)
        if t.is_complete:
            add_event(session_id, ChatSSEEvent.THOUGHT_EXECUTING, {
                "id": tid, "description": t.angle or "", "tool": t.tool, "target": t.target,
            })
            outcome_preview = (t.outcome[:500] + "...") if t.outcome and len(t.outcome) > 500 else (t.outcome or "")
            add_event(session_id, ChatSSEEvent.THOUGHT_RESULT, {"id": tid, "outcome": outcome_preview})


def _emit_evaluate(session_id: str, update: dict):
    eval_thoughts = update.get("thoughts", {})
    for tid, raw in eval_thoughts.items():
        t = _to_thought(raw)
        if t.is_complete and t.evaluation and t.evaluation.overall_score > 0:
            add_event(session_id, ChatSSEEvent.THOUGHT_EVALUATED, {
                "id": tid, "score": t.evaluation.overall_score,
                "relevance": t.evaluation.relevance, "evidence_strength": t.evaluation.evidence_strength,
                "source_diversity": t.evaluation.source_diversity, "reasoning": t.evaluation.reasoning,
                "description": t.angle or "",
            })
    add_event(session_id, ChatSSEEvent.STATE, {
        "phase": "evaluate_batch", "evaluated": len(update.get("evaluated_ids", [])),
    })
    _log_tree(session_id, update.get("thoughts", {}), update.get("best_ids", []), update.get("rejected_ids", []), update.get("pending_ids", []), update.get("depth", 1))


def _emit_prune(session_id: str, update: dict, emitted_ids: set[str], previous_rejected: list[str]):
    pending = update.get("pending_ids", [])
    best = update.get("best_ids", [])
    rejected = update.get("rejected_ids", [])
    thoughts_all = update.get("thoughts", {})
    current_depth = update.get("depth") or 1

    # Emit per-node pruning rationale for newly rejected
    newly_rejected = [tid for tid in rejected if tid not in previous_rejected]
    for tid in newly_rejected:
        t = _to_thought(thoughts_all.get(tid, {}))
        if t and t.evaluation:
            add_event(session_id, ChatSSEEvent.THOUGHT_PRUNED, {
                "id": tid, "description": t.angle or "",
                "score": t.evaluation.overall_score,
                "reasoning": t.evaluation.reasoning,
                "threshold": 0.4,
            })

    for tid, raw in thoughts_all.items():
        if tid not in emitted_ids:
            thought = _to_thought(raw)
            emitted_ids.add(tid)
            add_event(session_id, ChatSSEEvent.THOUGHT_GENERATED, {
                "id": tid, "parent_id": thought.parent_id or "", "depth": current_depth,
                "description": thought.angle or "", "hypothesis": thought.hypothesis or "",
                "tool": thought.tool, "target": thought.target,
                "expected_evidence": thought.expected_evidence or "",
            })
    add_event(session_id, ChatSSEEvent.STATE, {
        "phase": "prune_expand", "pending": len(pending), "best": len(best),
        "rejected": len(rejected), "depth": current_depth,
    })
    _log_tree(session_id, thoughts_all, best, rejected, pending, current_depth)


def _emit_synthesize(session_id: str, update: dict) -> tuple[str, list[str]]:
    answer = update.get("answer", "")
    if answer:
        add_event(session_id, ChatSSEEvent.ANSWER_CHUNK, {"answer": answer})
    rejected_branches = update.get("rejected_branches_summary", "")
    if rejected_branches:
        add_event(session_id, ChatSSEEvent.REJECTED_BRANCHES, {"summary": rejected_branches})
    uncertainties_summary = update.get("uncertainties_summary", "")
    if uncertainties_summary:
        add_event(session_id, ChatSSEEvent.UNCERTAINTIES, {"summary": uncertainties_summary})
    citations = update.get("citations", [])
    if citations:
        add_event(session_id, ChatSSEEvent.CITATIONS, {"citations": citations})
    return answer, citations


def _make_prune_handler(prev_rejected_ptr: list[list[str]]):
    """Return a handler that can detect newly rejected nodes via a mutable reference."""
    def _handler(session_id, update, emitted_ids):
        _emit_prune(session_id, update, emitted_ids, prev_rejected_ptr[0])
        prev_rejected_ptr[0] = list(update.get("rejected_ids", []))
    return _handler

_NODE_HANDLERS_BASE = {
    "generate_thoughts": _emit_generate,
    "execute_batch": _emit_execute,
    "evaluate_batch": _emit_evaluate,
    "synthesize": _emit_synthesize,
}


def run_tot_research(session_id: str, query: str, repo_path: str,
                     max_depth: int = settings.max_depth,
                     max_children: int = settings.max_children,
                     keep_top_k: int = settings.keep_top_k):
    logger.info("[%s] Starting ToT research: query='%s' repo=%s", session_id, query[:80], repo_path)

    add_event(session_id, ChatSSEEvent.RESEARCH_STARTED, {
        "query": query, "repo_path": repo_path, "max_depth": max_depth,
        "max_children": max_children, "keep_top_k": keep_top_k,
    })

    try:
        resolved_path = resolve_repo_path(session_id, repo_path)
        if not os.path.isdir(resolved_path):
            resolved_path = os.getcwd()
            logger.info("[%s] Using working directory: %s", session_id, resolved_path)
            add_event(session_id, ChatSSEEvent.CLONE_PROGRESS, {"message": f"Using working directory: {resolved_path}"})
    except Exception as e:
        logger.error("[%s] Path resolution failed: %s", session_id, e, exc_info=True)
        add_event(session_id, ChatSSEEvent.ERROR, {"message": str(e)})
        return

    try:
        from app.services.tools.code_graph import _graph_built as _code_graph_cached
        from app.services.tools.code_graph import generate_mermaid_callflow
        if _code_graph_cached:
            logger.info("[%s] Using cached code graph", session_id)
            add_event(session_id, ChatSSEEvent.GRAPH_STATUS, {"status": "cached"})
        else:
            logger.info("[%s] Building code graph...", session_id)
            add_event(session_id, ChatSSEEvent.STATE, {"phase": "building_graph"})
            add_event(session_id, ChatSSEEvent.GRAPH_STATUS, {"status": "building"})
            t0 = datetime.now(timezone.utc)
            build_code_graph(resolved_path)
            elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
            logger.info("[%s] Code graph built in %.1fs", session_id, elapsed)
            add_event(session_id, ChatSSEEvent.GRAPH_STATUS, {"status": "ready"})
            add_event(session_id, ChatSSEEvent.CLONE_PROGRESS, {"message": f"Code graph ready ({elapsed:.0f}s)."})
        diagram = generate_mermaid_callflow(max_nodes=30)
        if diagram:
            add_event(session_id, ChatSSEEvent.GRAPH_DIAGRAM, {"diagram": diagram})
    except Exception as e:
        logger.warning("[%s] Code graph build failed (using fallback): %s", session_id, e)
        add_event(session_id, ChatSSEEvent.CLONE_PROGRESS, {"message": "Code graph unavailable, using fallback tools."})

    state = _build_initial_state(query, resolved_path, max_depth, max_children, keep_top_k)
    answer = ""
    synthesize_citations = []
    emitted_ids: set[str] = set()
    prev_rejected_ptr: list[list[str]] = [[]]
    _NODE_HANDLERS = _NODE_HANDLERS_BASE | {
        "prune_expand": _make_prune_handler(prev_rejected_ptr),
    }

    try:
        config = {"configurable": {"thread_id": session_id}}
        total_start = datetime.now(timezone.utc)
        node_times: dict[str, float] = {}
        for event in _tot_graph.stream(state, config):
            for node_name, update in event.items():
                logger.info("[%s] Node executing: %s", session_id, node_name)
                t0 = datetime.now(timezone.utc)

                handler = _NODE_HANDLERS.get(node_name)
                if handler is None:
                    continue
                if node_name == "synthesize":
                    answer, synthesize_citations = handler(session_id, update)
                elif node_name in ("generate_thoughts", "prune_expand"):
                    handler(session_id, update, emitted_ids)
                else:
                    handler(session_id, update)

                elapsed_node = (datetime.now(timezone.utc) - t0).total_seconds()
                node_times[node_name] = node_times.get(node_name, 0) + elapsed_node
                logger.info("[%s] Node %s done in %.1fs", session_id, node_name, elapsed_node)

    except Exception as e:
        logger.error("[%s] ToT research failed: %s", session_id, e, exc_info=True)
        add_event(session_id, ChatSSEEvent.ERROR, {"message": str(e)})
        return
    finally:
        TEMP_DIRS.pop(session_id, None)

    if not answer:
        try:
            final_state = _tot_graph.get_state(config)
            answer = final_state.values.get("answer", "") or ""
        except Exception:
            pass

    if answer:
        add_event(session_id, ChatSSEEvent.ANSWER_CHUNK, {"answer": answer})

    total_elapsed = (datetime.now(timezone.utc) - total_start).total_seconds()
    node_summary = ", ".join(f"{k}: {v:.1f}s" for k, v in sorted(node_times.items()))
    logger.info("[%s] ToT research complete in %.1fs (%s)", session_id, total_elapsed, node_summary)

    CHAT_RESULTS[session_id] = answer
    add_event(session_id, ChatSSEEvent.COMPLETE, {
        "answer": answer, "elapsed_seconds": total_elapsed, "citations": synthesize_citations,
    })
