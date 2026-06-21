from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field
import operator

class Evidence(BaseModel):
    filepath: str = Field(description="The file where the evidence was found.")
    snippet: str = Field(description="Code or text snippet from the file.")
    explanation: str = Field(description="Why this is relevant.")

class NodeState(BaseModel):
    node_id: str
    status: str = Field(default="pending", description="'pending', 'running', 'done', 'failed'")
    findings: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)

class ResearchState(BaseModel):
    """
    The state of the entire repository research process (LangGraph State).
    """
    repo_url: str
    # The five main branches of our ToT
    structure_analysis: NodeState = Field(default_factory=lambda: NodeState(node_id="structure"))
    runtime_analysis: NodeState = Field(default_factory=lambda: NodeState(node_id="runtime"))
    design_reasoning: NodeState = Field(default_factory=lambda: NodeState(node_id="design"))
    developer_onboarding: NodeState = Field(default_factory=lambda: NodeState(node_id="onboarding"))
    risk_assessment: NodeState = Field(default_factory=lambda: NodeState(node_id="risk"))
    
    # Global messages/logs
    messages: Annotated[List[Dict[str, Any]], operator.add] = Field(default_factory=list)
