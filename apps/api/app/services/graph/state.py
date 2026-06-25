from typing import List, Dict, Optional
from typing_extensions import TypedDict

from pydantic import BaseModel, Field


class ThoughtEvaluation(BaseModel):
    relevance: float = Field(description="Qualitative relevance to query (0.0 to 1.0)")
    evidence_strength: float = Field(description="Reliability of retrieved evidence (0.0 to 1.0)")
    source_diversity: float = Field(description="Deterministic score based on unique files accessed (0.0 to 1.0)")
    overall_score: float = Field(description="Weighted overall: 0.5*rel + 0.3*ev + 0.2*div")
    reasoning: str = Field(description="Qualitative justification for scores")


class ToTThought(BaseModel):
    id: str = Field(default="", description="Unique short ID for this thought node")
    parent_id: str = Field(default="", description="Parent thought ID (enables lineage trace)")
    angle: str = Field(default="", description="Perspective or angle being explored")
    hypothesis: str = Field(default="", description="Explicit hypothesis to verify")
    tool: str = Field(default="", description="Selected tool: grep, glob, or read_file")
    target: str = Field(default="", description="Pattern or filepath for the tool")
    expected_evidence: str = Field(default="", description="What code patterns would validate this hypothesis")
    accessed_files: List[str] = Field(default_factory=list, description="Files accessed during execution")
    outcome: str = Field(default="", description="Raw output from tool execution")
    evaluation: Optional[ThoughtEvaluation] = Field(default=None, description="Hybrid evaluation rubric scores")
    is_complete: bool = False
    is_pruned: bool = Field(default=False, description="Pruned from search tree (score < 0.4)")
    child_ids: List[str] = Field(default_factory=list, description="IDs of spawned child thoughts")
    uncertainty: str = Field(default="", description="Unresolved doubt or missing evidence")
    follow_up_angles: List[str] = Field(default_factory=list, description="Temporary: follow-up angles from evaluation")
    follow_up_hypotheses: List[str] = Field(default_factory=list, description="Temporary: follow-up hypotheses")
    follow_up_tools: List[str] = Field(default_factory=list, description="Temporary: follow-up tools")
    follow_up_targets: List[str] = Field(default_factory=list, description="Temporary: follow-up targets")
    follow_up_expected_evidences: List[str] = Field(default_factory=list, description="Temporary: follow-up expected evidence")
    ready_to_synthesize: bool = Field(default=False, description="Evaluation flagged enough evidence gathered")


class ToTChatState(TypedDict):
    user_query: str
    repo_path: str
    session_id: str
    thoughts: Dict[str, dict]  # Stored as plain dicts for serialization via MemorySaver
    pending_ids: List[str]
    best_ids: List[str]
    rejected_ids: List[str]
    current_id: str
    depth: int
    max_depth: int
    max_children: int
    keep_top_k: int
    answer: str
    error: str
    uncertainties: List[str]
    evaluated_ids: List[str]


class GenerateThoughtsResponse(BaseModel):
    angles: List[str] = Field(description="2-3 perspectives or angles to explore")
    hypotheses: List[str] = Field(description="Explicit hypothesis for each angle")
    tools: List[str] = Field(description="Tool for each: 'grep', 'glob', 'read_file'")
    targets: List[str] = Field(description="Pattern or filepath for each tool")
    expected_evidences: List[str] = Field(description="What code patterns would validate each hypothesis")


class EvaluateThoughtResponse(BaseModel):
    relevance: float = Field(description="Relevance to the user query (0-100)")
    evidence_strength: float = Field(description="Strength of evidence found (0-100)")
    reasoning: str = Field(description="Qualitative justification for scores")
    follow_up_angles: List[str] = Field(
        default_factory=list, description="Follow-up perspectives if deeper exploration warranted"
    )
    follow_up_hypotheses: List[str] = Field(
        default_factory=list, description="Hypotheses for each follow-up"
    )
    follow_up_tools: List[str] = Field(
        default_factory=list, description="Tools for each follow-up"
    )
    follow_up_targets: List[str] = Field(
        default_factory=list, description="Targets for each follow-up"
    )
    follow_up_expected_evidences: List[str] = Field(
        default_factory=list, description="Expected evidence for each follow-up"
    )
    ready_to_synthesize: bool = Field(
        default=False, description="True if enough evidence gathered to form answer"
    )
    uncertainty: str = Field(
        default="", description="Unresolved questions or missing evidence"
    )


class SynthesizeResponse(BaseModel):
    answer: str = Field(description="Complete answer with citations referencing files and lines")
    citations: List[str] = Field(
        default_factory=list, description="Cited file paths and line numbers"
    )
    rejected_branches_summary: str = Field(
        default="", description="Summary of pruned branches and why they were rejected"
    )
    uncertainties: str = Field(
        default="", description="Unresolved assumptions or missing evidence"
    )
