import threading
from datetime import datetime, timezone


class ChatSSEEvent:
    RESEARCH_STARTED = "research_started"
    CLONE_PROGRESS = "clone_progress"
    THOUGHT_GENERATED = "thought_generated"
    THOUGHT_EXECUTING = "thought_executing"
    THOUGHT_RESULT = "thought_result"
    THOUGHT_EVALUATED = "thought_evaluated"
    THOUGHT_PRUNED = "thought_pruned"
    ANSWER_CHUNK = "answer_chunk"
    COMPLETE = "complete"
    ERROR = "error"
    STATE = "state"
    HEARTBEAT = "heartbeat"
    GRAPH_STATUS = "graph_status"
    GRAPH_DIAGRAM = "graph_diagram"
    REJECTED_BRANCHES = "rejected_branches"
    UNCERTAINTIES = "uncertainties"
    CITATIONS = "citations"


CHAT_EVENTS: dict[str, list[dict]] = {}
CHAT_EVENT_LOCKS: dict[str, threading.Lock] = {}


def add_event(session_id: str, event: str, data: dict):
    lock = CHAT_EVENT_LOCKS.setdefault(session_id, threading.Lock())
    with lock:
        CHAT_EVENTS.setdefault(session_id, []).append({
            "event": event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


def get_and_clear_events(session_id: str, since_index: int = 0) -> tuple[list[dict], int]:
    lock = CHAT_EVENT_LOCKS.setdefault(session_id, threading.Lock())
    with lock:
        events = CHAT_EVENTS.get(session_id, [])
        if since_index >= len(events):
            return [], since_index
        return events[since_index:], len(events)
