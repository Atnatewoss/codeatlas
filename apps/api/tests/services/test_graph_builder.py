import sys
import os

from app.services.graph.graph_builder import build_tot_chat_graph

REPO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")


def test_tot_graph_builds():
    g = build_tot_chat_graph()
    nodes = list(g.get_graph().nodes.keys())
    assert "generate_thoughts" in nodes
    assert "execute_batch" in nodes
    assert "evaluate_batch" in nodes
    assert "prune_expand" in nodes
    assert "synthesize" in nodes


def test_quick_answer():
    g = build_tot_chat_graph()
    state = {
        "user_query": "What Python packages are used in this project?",
        "repo_path": REPO_PATH,
        "session_id": "test-session",
        "thoughts": {},
        "pending_ids": [],
        "best_ids": [],
        "rejected_ids": [],
        "current_id": "",
        "depth": 1,
        "max_depth": 2,
        "max_children": 2,
        "keep_top_k": 5,
        "answer": "",
        "error": "",
        "uncertainties": [],
        "evaluated_ids": [],
    }
    config = {"configurable": {"thread_id": "test-1"}}

    for event in g.stream(state, config):
        pass

    final = g.get_state(config)
    answer = final.values.get("answer", "")
    print(f"\nAnswer:\n{answer[:500]}")
    assert answer, "Answer should not be empty"
    assert len(answer) > 20, "Answer should be substantive"


if __name__ == "__main__":
    print("Test 1: Graph builds")
    test_tot_graph_builds()
    print("  PASS")
    print()
    print("Test 2: Quick answer (this will call Ollama)")
    test_quick_answer()
    print("  PASS")
