"""
ToT workflow integration tests.

Tests the contradiction detection and re-investigation loop.
Uses heuristic fallback when no API key; LLM when key is available.
"""
import os
import sys
import json

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

from research.state import ResearchState, Finding, NodeState, EvaluationResult, SynthesisResult
from research.graph import (
    build_research_graph,
    _evaluate,
    _decide_next,
    _investigate,
    MAX_INVESTIGATION_ROUNDS,
)


def _make_state(overrides: dict = None) -> ResearchState:
    base: ResearchState = {
        "repo_path": "https://github.com/test/repo",
        "knowledge_graph_built": False,
        "structure": NodeState(findings=[], status="idle"),
        "runtime": NodeState(findings=[], status="idle"),
        "design": NodeState(findings=[], status="idle"),
        "onboarding": NodeState(findings=[], status="idle"),
        "risk": NodeState(findings=[], status="idle"),
        "evaluation": EvaluationResult(),
        "investigation_round": 0,
        "max_investigation_rounds": MAX_INVESTIGATION_ROUNDS,
        "investigation_log": [],
        "synthesis": SynthesisResult(),
        "error": None,
    }
    if overrides:
        base.update(overrides)
    return base


def _merge(state: ResearchState, update: dict) -> ResearchState:
    for k, v in update.items():
        if k in ResearchState.__annotations__:
            state[k] = v
    return state


def test_contradiction_detection():
    state = _make_state({
        "structure": NodeState(
            findings=[Finding(text="Uses microservices architecture with separate services running independently", confidence=0.85, evidence=[])],
            status="complete",
        ),
        "runtime": NodeState(
            findings=[Finding(text="Single process FastAPI application handles all HTTP traffic", confidence=0.92, evidence=[])],
            status="complete",
        ),
        "design": NodeState(
            findings=[Finding(text="Clean domain-driven design with service layers", confidence=0.78, evidence=[])],
            status="complete",
        ),
        "onboarding": NodeState(
            findings=[Finding(text="Well-documented API with OpenAPI specs", confidence=0.82, evidence=[])],
            status="complete",
        ),
        "risk": NodeState(
            findings=[Finding(text="Authentication via external OAuth provider", confidence=0.75, evidence=[])],
            status="complete",
        ),
    })

    update = _evaluate(state)
    state = _merge(state, update)

    assert state["evaluation"].investigation_needed, (
        f"Should investigate (contradictions: {len(state['evaluation'].contradictions)})"
    )
    print(f"  Contradictions: {len(state['evaluation'].contradictions)}")
    for c in state["evaluation"].contradictions:
        print(f"    - {c['finding_a']} vs {c['finding_b']}")

    decision = _decide_next(state)
    assert decision == "investigate", f"Expected investigate, got {decision}"

    round_before = state["investigation_round"]
    update = _investigate(state)
    state = _merge(state, update)
    assert state["investigation_round"] == round_before + 1

    update = _evaluate(state)
    state = _merge(state, update)
    decision = _decide_next(state)
    assert decision in ("investigate", "synthesize")

    if decision == "investigate":
        update = _investigate(state)
        state = _merge(state, update)
        update = _evaluate(state)
        state = _merge(state, update)

    decision = _decide_next(state)
    assert decision == "synthesize", f"Expected synthesize, got {decision}"

    print("  PASS: contradiction detection -> investigation -> evaluation -> synthesis")


def test_graph_streams_complete():
    g = build_research_graph()
    state = _make_state()

    path = []
    for output in g.stream(state, {"recursion_limit": 50}):
        for node_name, update in output.items():
            path.append(node_name)
            if isinstance(update, dict):
                state = _merge(state, update)

    path_str = " -> ".join(path)
    print(f"  Path: {path_str}")
    print(f"  Rounds: {state['investigation_round']}")

    assert "evaluate" in path
    assert "synthesize" in path
    assert state["synthesis"] is not None
    print("  PASS: graph completes with evaluation and synthesis")


if __name__ == "__main__":
    print("Test 1: Contradiction detection loop")
    test_contradiction_detection()
    print()
    print("Test 2: Graph stream completion")
    test_graph_streams_complete()
    print()
    print("ALL TESTS PASSED")
