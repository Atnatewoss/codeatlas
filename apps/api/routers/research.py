"""
Research API endpoints.

Provides:
- POST /api/research/start - Start a new research session
- GET  /api/research/status/{session_id} - Get current status (polling)
- GET  /api/research/stream/{session_id} - SSE stream for real-time progress

Architecture:
1. POST /start clones the repo and spawns a background task
2. Background task runs the LangGraph ToT workflow
3. Clients poll /status or subscribe to /stream for progress
"""

import os
import json
import time
import uuid
import tempfile
import subprocess
import shutil
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from research.state import ResearchState
from research.graph import build_research_graph


router = APIRouter(prefix="/api/research", tags=["research"])

# In-memory store for active research sessions
# In production, use Redis or Postgres
SESSIONS: Dict[str, ResearchState] = {}

# Compile the LangGraph ToT workflow once at startup
tot_graph = build_research_graph()


class StartResearchRequest(BaseModel):
    repo_url: str


class StartResearchResponse(BaseModel):
    session_id: str
    status_url: str
    stream_url: str


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

def run_research_workflow(session_id: str, repo_url: str):
    """
    Background task that:
    1. Clones the repository to a temp directory
    2. Builds the knowledge graph
    3. Executes the LangGraph ToT workflow (5 parallel branches)
    4. Aggregates results
    """
    temp_dir = tempfile.mkdtemp(prefix="codeatlas_")
    print(f"[{session_id}] Cloning {repo_url} into {temp_dir}...")
    
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            capture_output=True,
            timeout=60,
        )
        print(f"[{session_id}] Clone successful.")
    except subprocess.CalledProcessError as e:
        print(f"[{session_id}] Failed to clone repo: {e.stderr}")
        state = SESSIONS.get(session_id)
        if state:
            state.current_phase = "failed"
            state.messages = [{"role": "error", "content": f"Failed to clone repository: {e.stderr.decode() if e.stderr else str(e)}"}]
        return
    except subprocess.TimeoutExpired:
        print(f"[{session_id}] Clone timed out.")
        state = SESSIONS.get(session_id)
        if state:
            state.current_phase = "failed"
            state.messages = [{"role": "error", "content": "Repository clone timed out (60s limit)."}]
        return
    
    # Initialize state with the cloned path
    state = SESSIONS[session_id]
    state.repo_path = temp_dir
    
    try:
        # Execute the graph - stream updates
        for output in tot_graph.stream(state):
            # output is a dict mapping node_name -> ResearchState (or updates)
            for node_name, state_update in output.items():
                if isinstance(state_update, ResearchState):
                    SESSIONS[session_id] = state_update
                elif isinstance(state_update, dict):
                    # LangGraph may return partial updates
                    for key, value in state_update.items():
                        if hasattr(SESSIONS[session_id], key):
                            setattr(SESSIONS[session_id], key, value)
        
        print(f"[{session_id}] Workflow completed. Summary: {SESSIONS[session_id].summary}")
    
    except Exception as e:
        print(f"[{session_id}] Error in ToT workflow: {e}")
        state = SESSIONS[session_id]
        state.current_phase = "failed"
        state.messages = [{"role": "error", "content": f"Workflow failed: {str(e)}"}]
    
    finally:
        # Cleanup: remove the temp directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"[{session_id}] Cleaned up temp directory: {temp_dir}")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.post("/start", response_model=StartResearchResponse)
async def start_research(request: StartResearchRequest, background_tasks: BackgroundTasks):
    """
    Initialize a new Tree of Thought repository exploration session.
    
    Returns a session_id that can be used to poll for status or subscribe to SSE stream.
    """
    session_id = str(uuid.uuid4())
    
    # Create initial state
    initial_state = ResearchState(
        repo_url=request.repo_url,
        current_phase="starting",
    )
    SESSIONS[session_id] = initial_state
    
    # Spawn background task
    background_tasks.add_task(run_research_workflow, session_id, request.repo_url)
    
    return StartResearchResponse(
        session_id=session_id,
        status_url=f"/api/research/status/{session_id}",
        stream_url=f"/api/research/stream/{session_id}",
    )


@router.get("/status/{session_id}")
async def get_research_status(session_id: str):
    """
    Get the current execution status and findings of the ToT branches.
    
    Use this for polling-based progress tracking.
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state: ResearchState = SESSIONS[session_id]
    
    branches = {}
    for name, branch in state.get_all_branches().items():
        branches[name] = {
            "status": branch.status,
            "findings": [{"text": f.text, "confidence": f.confidence, "evidence": f.evidence} for f in branch.findings],
            "duration_seconds": branch.duration_seconds,
        }
    
    return {
        "session_id": session_id,
        "repo_url": state.repo_url,
        "current_phase": state.current_phase,
        "branches": branches,
        "evaluation": state.evaluation.model_dump() if state.evaluation else None,
        "synthesis": state.synthesis.model_dump() if state.synthesis else None,
        "started_at": state.started_at,
        "completed_at": state.completed_at,
    }


@router.get("/stream/{session_id}")
async def stream_research_progress(session_id: str):
    """
    SSE endpoint for real-time progress updates.
    
    Events:
    - "progress": Branch status update
    - "branch_complete": A branch finished its analysis
    - "complete": All branches done, final summary
    - "error": Something went wrong
    
    Each event is a JSON object: {"event": "type", "data": {...}}
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def event_generator():
        last_phase = None
        
        while True:
            state = SESSIONS.get(session_id)
            if not state:
                yield f"data: {json.dumps({'event': 'error', 'data': {'message': 'Session not found'}})}\n\n"
                break
            
            # Send progress update if phase changed
            if state.current_phase != last_phase:
                progress = state.to_progress_dict()
                yield f"data: {json.dumps({'event': 'progress', 'data': progress})}\n\n"
                last_phase = state.current_phase
            
            # Check if workflow is done
            if state.current_phase in ("done", "failed"):
                # Send final update
                progress = state.to_progress_dict()
                yield f"data: {json.dumps({'event': 'complete', 'data': progress})}\n\n"
                break
            
            # Check for branch completions
            for name, branch in state.get_all_branches().items():
                if branch.status == "done" and branch.duration_seconds is not None:
                    # Could send individual branch_complete events here
                    pass
            
            # Wait before polling again
            await asyncio.sleep(0.5)
    
    import asyncio
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/{session_id}")
async def cancel_research(session_id: str):
    """
    Cancel a running research session and cleanup resources.
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = SESSIONS[session_id]
    state.current_phase = "cancelled"
    
    # Remove from store
    del SESSIONS[session_id]
    
    return {"status": "cancelled", "session_id": session_id}
