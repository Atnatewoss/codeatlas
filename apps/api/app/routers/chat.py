import uuid
import threading
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.log import get_logger


class DeepResearchRequest(BaseModel):
    repo_path: str
    query: str = ""
    max_depth: int = 3
    max_children: int = 2
    keep_top_k: int = 5


class DeepResearchResponse(BaseModel):
    session_id: str
    repo_path: str
from app.services.research import run_tot_research, CHAT_RESULTS
from app.services.infra.events import get_and_clear_events, ChatSSEEvent, CHAT_EVENTS, CHAT_EVENT_LOCKS


logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

SESSIONS: dict[str, dict] = {}


@router.post("/research", response_model=DeepResearchResponse)
async def start_deep_research(request: DeepResearchRequest):
    session_id = uuid.uuid4().hex[:12]
    query = request.query or "Explore this repository and provide a comprehensive overview."

    SESSIONS[session_id] = {
        "repo_path": request.repo_path, "query": query,
        "status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
    }

    CHAT_EVENTS[session_id] = []
    CHAT_EVENT_LOCKS[session_id] = threading.Lock()

    thread = threading.Thread(
        target=run_tot_research,
        args=(session_id, query, request.repo_path, request.max_depth, request.max_children, request.keep_top_k),
        daemon=True,
    )
    thread.start()

    return DeepResearchResponse(session_id=session_id, repo_path=request.repo_path)


@router.websocket("/ws/{session_id}")
async def ws_research(websocket: WebSocket, session_id: str):
    if session_id not in CHAT_EVENTS and session_id not in SESSIONS:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()
    last_index = 0
    sent_complete = False
    try:
        while True:
            if session_id not in CHAT_EVENTS:
                await websocket.send_json({"event": "error", "data": {"message": "Session not found"}})
                break

            events, last_index = get_and_clear_events(session_id, last_index)

            for evt in events:
                await websocket.send_json(evt)
                if evt["event"] in (ChatSSEEvent.COMPLETE, ChatSSEEvent.ERROR):
                    sent_complete = True

            if sent_complete:
                break

            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        logger.info("[%s] WebSocket disconnected", session_id)

    try:
        await websocket.close()
    except Exception:
        pass


@router.get("/status/{session_id}")
async def get_research_status(session_id: str):
    if session_id not in SESSIONS and session_id not in CHAT_EVENTS:
        raise HTTPException(status_code=404, detail="Session not found")

    meta = SESSIONS.get(session_id, {})
    is_complete = session_id in CHAT_RESULTS
    is_error = False

    events = CHAT_EVENTS.get(session_id, [])
    for evt in events:
        if evt["event"] == ChatSSEEvent.ERROR:
            is_error = True
            break

    return {
        "session_id": session_id,
        "query": meta.get("query", ""),
        "repo_path": meta.get("repo_path", ""),
        "status": "error" if is_error else ("complete" if is_complete else "running"),
        "answer": CHAT_RESULTS.get(session_id, ""),
        "started_at": meta.get("started_at"),
    }
