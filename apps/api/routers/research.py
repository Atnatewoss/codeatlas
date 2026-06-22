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
import asyncio
import uuid
import tempfile
import subprocess
import shutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from research.state import ResearchState, NodeState, EvaluationResult, SynthesisResult
from research.graph import build_research_graph


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])

# In-memory store for active research sessions
# In production, use Redis or Postgres
SESSIONS: Dict[str, ResearchState] = {}

# Store additional session metadata not in ResearchState
SESSION_META: Dict[str, dict] = {}

# Compile the LangGraph ToT workflow once at startup
tot_graph = build_research_graph()


class StartResearchRequest(BaseModel):
    repo_url: str


class StartResearchResponse(BaseModel):
    session_id: str
    status_url: str
    stream_url: str


BRANCH_NAMES = ["structure", "runtime", "design", "onboarding", "risk"]


def _serialize_session(session_id: str) -> Optional[dict]:
    """Serialize ResearchState + metadata into a frontend-friendly dict."""
    state = SESSIONS.get(session_id)
    if state is None:
        return None
    meta = SESSION_META.get(session_id, {})

    branches = {}
    for name in BRANCH_NAMES:
        node = state[name]
        branches[name] = {
            "status": node.status,
            "findings": [
                {
                    "text": f.text,
                    "confidence": f.confidence,
                    "evidence": f.evidence,
                }
                for f in node.findings
            ],
            "error": node.error,
        }

    return {
        "session_id": session_id,
        "repo_url": meta.get("repo_url", ""),
        "status": meta.get("status", "pending"),
        "clone_progress": meta.get("clone_progress"),
        "branches": branches,
        "evaluation": _serialize_evaluation(state["evaluation"]),
        "synthesis": _serialize_synthesis(state["synthesis"]),
        "investigation_round": state["investigation_round"],
        "investigation_log": state["investigation_log"],
        "started_at": meta.get("started_at"),
        "completed_at": meta.get("completed_at"),
    }


def _serialize_evaluation(eval_result: EvaluationResult) -> Optional[dict]:
    if eval_result is None:
        return None
    return {
        "contradictions": eval_result.contradictions,
        "agreements": eval_result.agreements,
        "low_confidence": [
            {"text": f.text, "confidence": f.confidence}
            for f in eval_result.low_confidence
        ],
        "investigation_needed": eval_result.investigation_needed,
    }


def _serialize_synthesis(syn: SynthesisResult) -> Optional[dict]:
    if syn is None:
        return None
    return {
        "summary": syn.summary,
        "architecture_overview": syn.architecture_overview,
        "key_insights": syn.key_insights,
        "learning_path": syn.learning_path,
        "risk_summary": syn.risk_summary,
    }


def _make_initial_state(repo_url: str) -> ResearchState:
    return {
        "repo_path": "",
        "knowledge_graph_built": False,
        "structure": NodeState(status="idle"),
        "runtime": NodeState(status="idle"),
        "design": NodeState(status="idle"),
        "onboarding": NodeState(status="idle"),
        "risk": NodeState(status="idle"),
        "evaluation": EvaluationResult(),
        "investigation_round": 0,
        "max_investigation_rounds": int(os.getenv("MAX_INVESTIGATION_ROUNDS", "2")),
        "investigation_log": [],
        "synthesis": SynthesisResult(),
        "error": None,
    }


def _merge_update(state: ResearchState, update: dict) -> ResearchState:
    """Merge a partial update dict into ResearchState TypedDict."""
    for k, v in update.items():
        if k in ResearchState.__annotations__:
            state[k] = v
    return state


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

def run_research_workflow(session_id: str, repo_url: str):
    """
    Background task that:
    1. Clones the repository to a temp directory
    2. Builds the knowledge graph
    3. Executes the LangGraph ToT workflow
    4. Aggregates results
    """
    temp_dir = tempfile.mkdtemp(prefix="codeatlas_")
    meta = SESSION_META.get(session_id, {})

    try:
        logger.info(f"[{session_id}] Starting clone for {repo_url} into {temp_dir}")
        meta["status"] = "cloning"
        meta["clone_progress"] = "Initializing clone..."
        
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        
        # We use Popen to stream progress from git clone
        process = subprocess.Popen(
            ["git", "clone", "--progress", "--depth", "1", repo_url, temp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )
        
        for line in process.stdout:
            line_str = line.strip()
            if line_str:
                meta["clone_progress"] = line_str
                logger.debug(f"[{session_id}] Git clone: {line_str}")
                
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args, output=meta.get("clone_progress", ""))
            
        logger.info(f"[{session_id}] Clone successful.")
        meta["clone_progress"] = "Clone complete."
        
    except subprocess.CalledProcessError as e:
        logger.error(f"[{session_id}] Clone failed: {e.output}")
        meta["status"] = "failed"
        meta["error"] = f"Failed to clone repository: {e.output}"
        return
    except Exception as e:
        logger.error(f"[{session_id}] Clone error: {str(e)}")
        meta["status"] = "failed"
        meta["error"] = f"Repository clone error: {str(e)}"
        return

    state = SESSIONS[session_id]
    state["repo_path"] = temp_dir
    meta["status"] = "running"

    try:
        logger.info(f"[{session_id}] Starting LangGraph ToT workflow")
        for output in tot_graph.stream(state):
            for node_name, state_update in output.items():
                if isinstance(state_update, dict):
                    state = _merge_update(state, state_update)

        meta["status"] = "complete"
        meta["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"[{session_id}] Workflow completed successfully.")

    except Exception as e:
        logger.error(f"[{session_id}] Error in ToT workflow: {e}", exc_info=True)
        meta["status"] = "failed"
        meta["error"] = f"Workflow failed: {str(e)}"

    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"[{session_id}] Failed to cleanup temp directory: {e}")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.post("/start", response_model=StartResearchResponse)
async def start_research(request: StartResearchRequest, background_tasks: BackgroundTasks):
    """Initialize a new Tree of Thought repository exploration session."""
    session_id = str(uuid.uuid4())

    SESSIONS[session_id] = _make_initial_state(request.repo_url)
    SESSION_META[session_id] = {
        "repo_url": request.repo_url,
        "status": "pending",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    background_tasks.add_task(run_research_workflow, session_id, request.repo_url)

    return StartResearchResponse(
        session_id=session_id,
        status_url=f"/api/research/status/{session_id}",
        stream_url=f"/api/research/stream/{session_id}",
    )


@router.get("/status/{session_id}")
async def get_research_status(session_id: str):
    """Get the current execution status and findings of the ToT branches."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    result = _serialize_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.get("/stream/{session_id}")
async def stream_research_progress(session_id: str):
    """
    SSE endpoint for real-time progress updates.

    Events:
    - "progress": Generic progress update (including cloning)
    - "branch_update": A branch changed status
    - "complete": All branches done, final synthesis
    - "error": Something went wrong
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        last_branch_statuses = {}
        last_clone_progress = None
        last_status = None

        while True:
            if session_id not in SESSIONS:
                yield f"data: {json.dumps({'event': 'error', 'data': {'message': 'Session not found'}})}\n\n"
                break

            meta = SESSION_META.get(session_id, {})
            current_status = meta.get("status", "pending")
            current_clone = meta.get("clone_progress")

            # Emitting status changes
            if current_status != last_status:
                last_status = current_status
                snapshot = _serialize_session(session_id)
                yield f"data: {json.dumps({'event': 'status_change', 'data': snapshot})}\n\n"

            # Emitting clone progress
            if current_status == "cloning" and current_clone != last_clone_progress:
                last_clone_progress = current_clone
                yield f"data: {json.dumps({'event': 'clone_progress', 'data': {'message': current_clone}})}\n\n"

            # Emitting branch changes
            state = SESSIONS[session_id]
            for name in BRANCH_NAMES:
                node = state[name]
                prev = last_branch_statuses.get(name)
                if node.status != prev:
                    last_branch_statuses[name] = node.status
                    yield f"data: {json.dumps({'event': 'branch_update', 'data': {'branch': name, 'status': node.status}})}\n\n"

            # Check terminal states
            if current_status in ("complete", "failed"):
                snapshot = _serialize_session(session_id)
                yield f"data: {json.dumps({'event': 'complete', 'data': snapshot})}\n\n"
                break

            await asyncio.sleep(0.5)

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
    """Cancel a running research session and cleanup resources."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    meta = SESSION_META.get(session_id, {})
    meta["status"] = "cancelled"

    del SESSIONS[session_id]
    if session_id in SESSION_META:
        del SESSION_META[session_id]

    return {"status": "cancelled", "session_id": session_id}
