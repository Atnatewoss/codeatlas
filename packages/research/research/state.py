"""
Research state definitions for Tree of Thought repository analysis.

State flows: build_knowledge_graph -> structure|runtime|design|onboarding|risk
  -> evaluate -> decide_next -> [investigate -> evaluate] -> synthesize -> END
"""

from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    """A single finding from a ToT branch."""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[Dict[str, str]] = Field(default_factory=list)


class NodeState(BaseModel):
    """State of a single branch node."""
    findings: List[Finding] = Field(default_factory=list)
    status: str = "idle"  # idle, running, complete, error
    error: Optional[str] = None


class EvaluationResult(BaseModel):
    """Result of evaluating all branch findings."""
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    agreements: List[Dict[str, Any]] = Field(default_factory=list)
    low_confidence: List[Finding] = Field(default_factory=list)
    investigation_needed: bool = False


class SynthesisResult(BaseModel):
    """Final synthesis output."""
    summary: str = ""
    architecture_overview: str = ""
    key_insights: List[Dict[str, Any]] = Field(default_factory=list)
    learning_path: List[Dict[str, str]] = Field(default_factory=list)
    risk_summary: str = ""


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------

class ResearchState(TypedDict):
    """Overall research workflow state."""
    repo_path: str
    knowledge_graph_built: bool

    # Branch findings
    structure: NodeState
    runtime: NodeState
    design: NodeState
    onboarding: NodeState
    risk: NodeState

    # Evaluation
    evaluation: EvaluationResult
    investigation_round: int
    max_investigation_rounds: int
    investigation_log: List[str]

    # Synthesis
    synthesis: SynthesisResult
    error: Optional[str]


# ---------------------------------------------------------------------------
# Pydantic models for structured LLM output
# ---------------------------------------------------------------------------

class EvaluationResponse(BaseModel):
    """Structured output from the evaluation LLM."""
    contradictions: List[Dict[str, Any]] = Field(
        description="List of conflicting findings with branch names"
    )
    agreements: List[Dict[str, Any]] = Field(
        description="List of confirmed insights across branches"
    )
    low_confidence: List[Dict[str, Any]] = Field(
        description="Findings with confidence < 0.5"
    )
    investigation_needed: bool = Field(
        description="Whether contradictions or low-confidence items need investigation"
    )


class SynthesisResponse(BaseModel):
    """Structured output from the synthesis LLM."""
    summary: str = Field(description="2-3 sentence overview of the codebase")
    architecture_overview: str = Field(
        description="How the codebase is organized"
    )
    key_insights: List[Dict[str, Any]] = Field(
        description="Top 5 insights with confidence scores"
    )
    learning_path: List[Dict[str, str]] = Field(
        description="Ordered list of files/concepts to learn"
    )
    risk_summary: str = Field(
        description="Top risks and mitigation suggestions"
    )
