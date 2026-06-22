"""
Tree of Thought research workflow using LangGraph.

Flow:
  build_knowledge_graph
    -> structure | runtime | design | onboarding | risk  (parallel branches)
    -> evaluate (LLM-based, with heuristic fallback)
    -> decide_next
    -> [investigate -> evaluate] loop (max 2 rounds)
    -> synthesize (LLM-based)
    -> END
"""

import json
import os
import time
from typing import Literal

MAX_INVESTIGATION_ROUNDS = int(os.getenv("MAX_INVESTIGATION_ROUNDS", "2"))

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from research.state import ResearchState, NodeState, Finding, EvaluationResult, SynthesisResult
from research.tools import PROMPTS, ALL_TOOLS
from graphify.code_graph import get_or_build_graph


# ---------------------------------------------------------------------------
# LLM routing
# ---------------------------------------------------------------------------

def _get_llm():
    """Route to available LLM provider: Gemini > Anthropic > OpenAI > None.
    Model names are configurable via env vars (pinned defaults below)."""
    if os.environ.get("GOOGLE_API_KEY"):
        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
            temperature=0,
        )
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            temperature=0,
        )
    if os.environ.get("OPENAI_API_KEY"):
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )
    return None


# ---------------------------------------------------------------------------
# Node: Build Knowledge Graph
# ---------------------------------------------------------------------------

def _build_knowledge_graph(state: ResearchState) -> dict:
    """Build the Graphify knowledge graph for the repo."""
    try:
        get_or_build_graph(state["repo_path"])
        return {"knowledge_graph_built": True}
    except Exception as e:
        return {"knowledge_graph_built": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Node: Branch runners (partial dicts to avoid LangGraph concurrent write errors)
# ---------------------------------------------------------------------------

def _run_branch(state: ResearchState, branch: str) -> dict:
    """Run a single ToT branch."""
    llm = _get_llm()
    if llm is None:
        return {branch: NodeState(findings=[Finding(text=f"{branch} analysis skipped (no LLM)", confidence=0.1)], status="complete")}
    agent = create_react_agent(
        llm,
        tools=ALL_TOOLS,
        prompt=PROMPTS[branch].format(repo_path=state["repo_path"]),
    )
    result = agent.invoke(
        {"messages": [HumanMessage(f"Analyze the {branch} of this repository.")]}
    )
    return {branch: NodeState(findings=[Finding(text=f"{branch} analysis complete", confidence=0.5)], status="complete")}


def _run_structure(state: ResearchState) -> dict:
    return _run_branch(state, "structure")


def _run_runtime(state: ResearchState) -> dict:
    return _run_branch(state, "runtime")


def _run_design(state: ResearchState) -> dict:
    return _run_branch(state, "design")


def _run_onboarding(state: ResearchState) -> dict:
    return _run_branch(state, "onboarding")


def _run_risk(state: ResearchState) -> dict:
    return _run_branch(state, "risk")


# ---------------------------------------------------------------------------
# Node: Evaluate
# ---------------------------------------------------------------------------

def _heuristic_evaluate(state: ResearchState) -> EvaluationResult:
    """Fallback: keyword-based contradiction detection when no LLM."""
    contradictions = []
    agreements = []
    low_confidence = []
    
    all_findings = []
    for branch_name in ["structure", "runtime", "design", "onboarding", "risk"]:
        for f in state[branch_name].findings:
            all_findings.append((branch_name, f))
            if f.confidence < 0.5:
                low_confidence.append(f)
    
    # Check for contradictions between known keyword pairs
    keyword_pairs = [
        ("microservice", "single process"),
        ("event-driven", "request-response"),
        ("serverless", "dedicated server"),
        ("monolith", "microservice"),
        ("GraphQL", "REST"),
    ]
    
    found_categories = {}
    for branch_name, f in all_findings:
        text_lower = f.text.lower()
        for cat_a, cat_b in keyword_pairs:
            if cat_a in text_lower:
                found_categories.setdefault(cat_a, []).append(branch_name)
            if cat_b in text_lower:
                found_categories.setdefault(cat_b, []).append(branch_name)
    
    for cat_a, cat_b in keyword_pairs:
        if cat_a in found_categories and cat_b in found_categories:
            contradictions.append({
                "finding_a": f"{cat_a} in {found_categories[cat_a]}",
                "finding_b": f"{cat_b} in {found_categories[cat_b]}",
                "reason": f"{cat_a} conflicts with {cat_b}",
            })
    
    investigation_needed = len(contradictions) > 0 or len(low_confidence) > 0
    
    return EvaluationResult(
        contradictions=contradictions,
        agreements=agreements,
        low_confidence=low_confidence,
        investigation_needed=investigation_needed,
    )


def _evaluate(state: ResearchState) -> dict:
    """Evaluate branch findings for contradictions, agreements, low confidence."""
    llm = _get_llm()
    
    if llm is None:
        result = _heuristic_evaluate(state)
    else:
        try:
            from research.state import EvaluationResponse
            
            llm_with_struct = llm.with_structured_output(EvaluationResponse)
            
            branches_text = []
            for branch_name in ["structure", "runtime", "design", "onboarding", "risk"]:
                node = state[branch_name]
                if node.status == "complete" and node.findings:
                    branch_text = f"\n=== {branch_name.upper()} ===\n"
                    for f in node.findings:
                        branch_text += f"- [{f.confidence:.1f}] {f.text}\n"
                    branches_text.append(branch_text)
            
            prompt = PROMPTS["evaluate"] + "\n\nBRANCH FINDINGS:\n" + "\n".join(branches_text)
            
            response = llm_with_struct.invoke(prompt)
            result = EvaluationResult(
                contradictions=response.contradictions,
                agreements=response.agreements,
                low_confidence=[
                    f for f in
                    [Finding(**item) if isinstance(item, dict) else item
                     for item in response.low_confidence]
                    if isinstance(f, Finding)
                ],
                investigation_needed=response.investigation_needed,
            )
        except Exception:
            result = _heuristic_evaluate(state)
    
    # Log investigation round
    log_entries = []
    if result.contradictions:
        log_entries.append(f"Contradictions: {len(result.contradictions)}")
    if result.low_confidence:
        log_entries.append(f"Low confidence: {len(result.low_confidence)}")
    
    return {
        "evaluation": result,
        "investigation_round": state.get("investigation_round", 0) + 1,
        "investigation_log": state.get("investigation_log", [])
            + [f"Round {state.get('investigation_round', 0) + 1}: " + "; ".join(log_entries)]
            if log_entries else state.get("investigation_log", []),
    }


# ---------------------------------------------------------------------------
# Node: Decide next action
# ---------------------------------------------------------------------------

def _decide_next(state: ResearchState) -> Literal["investigate", "synthesize", "end"]:
    """Route to investigate, synthesize, or end based on evaluation."""
    if state["evaluation"].investigation_needed:
        if state["investigation_round"] < state["max_investigation_rounds"]:
            return "investigate"
        return "synthesize"
    return "synthesize"


# ---------------------------------------------------------------------------
# Node: Investigate
# ---------------------------------------------------------------------------

def _investigate(state: ResearchState) -> dict:
    """Investigate contradictions and low-confidence findings."""
    llm = _get_llm()
    contradictions = state["evaluation"].contradictions
    low_confidence = state["evaluation"].low_confidence
    
    context = "Investigation needed for:\n"
    if contradictions:
        context += "Contradictions:\n"
        for c in contradictions:
            context += f"- {c.get('finding_a', '?')} vs {c.get('finding_b', '?')}: {c.get('reason', '')}\n"
    if low_confidence:
        context += "Low confidence findings:\n"
        for f in low_confidence:
            context += f"- [{f.confidence}] {f.text}\n"
    
    if llm is not None:
        agent = create_react_agent(
            llm,
            tools=ALL_TOOLS,
            prompt=(
                f"Repository: {state['repo_path']}\n\n"
                f"You are investigating to resolve contradictions and improve low-confidence findings.\n\n"
                f"{context}\n\n"
                f"Use the available tools to gather more evidence. Be thorough."
            ),
        )
        agent.invoke(
            {"messages": [HumanMessage("Investigate the contradictions and low-confidence findings.")]}
        )
    
    return {"investigation_round": state["investigation_round"] + 1}


# ---------------------------------------------------------------------------
# Node: Synthesize
# ---------------------------------------------------------------------------

def _synthesize(state: ResearchState) -> dict:
    """Synthesize all findings into a unified report."""
    llm = _get_llm()
    
    if llm is None:
        # Fallback: simple ranking by confidence
        all_findings = []
        for branch_name in ["structure", "runtime", "design", "onboarding", "risk"]:
            for f in state[branch_name].findings:
                all_findings.append((branch_name, f))
        
        sorted_findings = sorted(all_findings, key=lambda x: x[1].confidence, reverse=True)
        
        synthesis = SynthesisResult(
            summary=f"Analysis of {state['repo_path']} completed with {len(all_findings)} findings.",
            architecture_overview="Architecture analysis not available (no LLM).",
            key_insights=[
                {"text": f.text, "confidence": f.confidence, "branch": branch}
                for branch, f in sorted_findings[:5]
            ],
            learning_path=[
                {"file": f.text, "reason": "Key finding"}
                for _, f in sorted_findings[:5]
            ],
            risk_summary="Risk analysis limited (no LLM).",
        )
    else:
        try:
            from research.state import SynthesisResponse
            
            llm_with_struct = llm.with_structured_output(SynthesisResponse)
            
            branches_text = []
            for branch_name in ["structure", "runtime", "design", "onboarding", "risk"]:
                node = state[branch_name]
                if node.status == "complete" and node.findings:
                    branch_text = f"\n=== {branch_name.upper()} ===\n"
                    for f in node.findings:
                        branch_text += f"- [{f.confidence:.1f}] {f.text}\n"
                    branches_text.append(branch_text)
            
            eval_text = f"\n=== EVALUATION ===\n"
            eval_text += f"Contradictions: {len(state['evaluation'].contradictions)}\n"
            eval_text += f"Agreements: {len(state['evaluation'].agreements)}\n"
            eval_text += f"Low confidence: {len(state['evaluation'].low_confidence)}\n"
            for c in state["evaluation"].contradictions:
                eval_text += f"- {c.get('finding_a', '?')} vs {c.get('finding_b', '?')}\n"
            
            prompt = (
                PROMPTS["synthesize"]
                + "\n\nBRANCH FINDINGS:\n" + "\n".join(branches_text)
                + "\n\nEVALUATION:\n" + eval_text
            )
            
            response = llm_with_struct.invoke(prompt)
            synthesis = SynthesisResult(
                summary=response.summary,
                architecture_overview=response.architecture_overview,
                key_insights=response.key_insights,
                learning_path=response.learning_path,
                risk_summary=response.risk_summary,
            )
        except Exception as e:
            synthesis = SynthesisResult(
                summary=f"Synthesis failed: {e}",
                architecture_overview="",
                key_insights=[],
                learning_path=[],
                risk_summary="",
            )
    
    return {"synthesis": synthesis}


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def build_research_graph() -> StateGraph:
    """Build the Tree of Thought research workflow graph."""
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("build_knowledge_graph", _build_knowledge_graph)
    workflow.add_node("structure", _run_structure)
    workflow.add_node("runtime", _run_runtime)
    workflow.add_node("design", _run_design)
    workflow.add_node("onboarding", _run_onboarding)
    workflow.add_node("risk", _run_risk)
    workflow.add_node("evaluate", _evaluate)
    workflow.add_node("investigate", _investigate)
    workflow.add_node("synthesize", _synthesize)
    
    # Set entry point
    workflow.set_entry_point("build_knowledge_graph")
    
    # Build knowledge graph -> fan out to all 5 branches
    for branch in ["structure", "runtime", "design", "onboarding", "risk"]:
        workflow.add_edge("build_knowledge_graph", branch)
    
    # All branches -> evaluate
    for branch in ["structure", "runtime", "design", "onboarding", "risk"]:
        workflow.add_edge(branch, "evaluate")
    
    # Evaluate -> conditional route
    workflow.add_conditional_edges(
        "evaluate",
        _decide_next,
        {
            "investigate": "investigate",
            "synthesize": "synthesize",
            "end": END,
        }
    )
    
    # Investigate -> evaluate (loop)
    workflow.add_edge("investigate", "evaluate")
    
    # Synthesize -> END
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()
