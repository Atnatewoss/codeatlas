from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.services.graph.state import ToTChatState
from app.services.graph.nodes import (
    generate_thoughts,
    execute_batch,
    evaluate_batch,
    prune_expand,
    decide_loop,
    synthesize,
)


def build_tot_chat_graph():
    """Build the BFS Tree-of-Thought LangGraph with MemorySaver checkpointer.

    State values use plain dicts instead of Pydantic objects so that
    MemorySaver serialises cleanly without warnings.
    """
    workflow = StateGraph(ToTChatState)

    workflow.add_node("generate_thoughts", generate_thoughts)
    workflow.add_node("execute_batch", execute_batch)
    workflow.add_node("evaluate_batch", evaluate_batch)
    workflow.add_node("prune_expand", prune_expand)
    workflow.add_node("synthesize", synthesize)

    workflow.set_entry_point("generate_thoughts")

    workflow.add_edge("generate_thoughts", "execute_batch")
    workflow.add_edge("execute_batch", "evaluate_batch")
    workflow.add_edge("evaluate_batch", "prune_expand")

    workflow.add_conditional_edges(
        "prune_expand",
        decide_loop,
        {
            "execute_batch": "execute_batch",
            "synthesize": "synthesize",
            "generate_thoughts": "generate_thoughts",
        }
    )

    workflow.add_edge("synthesize", END)

    return workflow.compile(checkpointer=MemorySaver())
