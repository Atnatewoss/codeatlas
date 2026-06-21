from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time
from agents.state import ResearchState
from agents.graph import build_research_graph

router = APIRouter(prefix="/api/research", tags=["research"])

# In-memory store for active research sessions
# In production, use Redis or Postgres
SESSIONS = {}

# Compile the LangGraph ToT workflow
tot_graph = build_research_graph()

class StartResearchRequest(BaseModel):
    repo_url: str

class StartResearchResponse(BaseModel):
    session_id: str

import tempfile
import subprocess
import shutil

def run_research_workflow(session_id: str, repo_url: str):
    """
    Background task that executes the LangGraph workflow.
    """
    # Create a temporary directory for this session
    temp_dir = tempfile.mkdtemp(prefix="codeatlas_")
    print(f"[{session_id}] Cloning {repo_url} into {temp_dir}...")
    
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[{session_id}] Failed to clone repo: {e.stderr}")
        # In a real app, we'd update state to "failed" here
        # For now, we'll continue with an empty temp_dir or handle it in nodes
    
    # Initialize the state
    initial_state = ResearchState(repo_url=repo_url, repo_path=temp_dir)
    
    # Store initial state
    SESSIONS[session_id] = initial_state
    
    # Execute the graph
    # In LangGraph 0.1+, invoke returns the final state or you can stream the steps.
    # We will stream the steps to update the in-memory store dynamically.
    try:
        for output in tot_graph.stream(initial_state):
            # output is a dict mapping node_name -> ResearchState (or updates)
            # Update the session with the latest state
            for node, state_update in output.items():
                if isinstance(state_update, ResearchState):
                    SESSIONS[session_id] = state_update
            
            # Simulate processing time for demo purposes
            time.sleep(2)
            
    except Exception as e:
        print(f"Error in ToT workflow: {e}")

@router.post("/start", response_model=StartResearchResponse)
async def start_research(request: StartResearchRequest, background_tasks: BackgroundTasks):
    """
    Initialize a new Tree of Thought repository exploration session.
    """
    session_id = str(uuid.uuid4())
    
    # Add to background tasks so API returns immediately
    background_tasks.add_task(run_research_workflow, session_id, request.repo_url)
    
    return {"session_id": session_id}

@router.get("/status/{session_id}")
async def get_research_status(session_id: str):
    """
    Get the current execution status and findings of the ToT branches.
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
        
    state: ResearchState = SESSIONS[session_id]
    
    return {
        "repo_url": state.repo_url,
        "branches": {
            "structure": state.structure_analysis.model_dump(),
            "runtime": state.runtime_analysis.model_dump(),
            "design": state.design_reasoning.model_dump(),
            "onboarding": state.developer_onboarding.model_dump(),
            "risk": state.risk_assessment.model_dump()
        }
    }
