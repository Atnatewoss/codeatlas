import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from typing import List, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from agents.local_tools import search_file_tree, read_file_chunk, get_file_skeleton, find_references

class AnalysisOutput(BaseModel):
    findings: List[str] = Field(description="List of key architectural findings or insights.")
    evidence: List[Dict[str, str]] = Field(
        description="Evidence supporting the findings. Must contain 'filepath', 'snippet', and 'explanation'."
    )

@tool
def tool_search_file_tree(repo_path: str, pattern: str) -> List[str]:
    """Search for files in the repository matching a regex pattern. Useful for finding files by name."""
    return search_file_tree(repo_path, pattern)[:50] # Limit to 50 results

@tool
def tool_read_file_chunk(repo_path: str, filepath: str, start_line: int, end_line: int) -> str:
    """Read specific lines of a file. Use this to read the implementation of a function or class."""
    return read_file_chunk(repo_path, filepath, start_line, end_line)

@tool
def tool_get_file_skeleton(repo_path: str, filepath: str) -> str:
    """Extract classes and function signatures from a file, omitting the body. Use this to get an overview of a file's structure."""
    return get_file_skeleton(repo_path, filepath)

@tool
def tool_find_references(repo_path: str, symbol: str) -> List[str]:
    """Find files and line numbers where a symbol is mentioned. Useful for tracing execution flow."""
    return find_references(repo_path, symbol)[:50] # Limit to 50 results

@tool
def submit_findings(findings: List[str], evidence: List[Dict[str, str]]) -> str:
    """Call this tool when you have finished exploring and are ready to submit your final findings and evidence.
    Evidence must be a list of dictionaries with 'filepath', 'snippet', and 'explanation'.
    """
    return "Findings submitted successfully."

# List of tools to bind to the LLM
GET_TOOLS = [tool_search_file_tree, tool_read_file_chunk, tool_get_file_skeleton, tool_find_references, submit_findings]

# Prompts for the different branches
PROMPTS = {
    "structure": """You are an expert software architect analyzing the structure of {repo_url}.
Focus on: Modules, Dependencies, Layers, and Boundaries.
Generate 2-3 key findings about how the codebase is organized, and cite specific files as evidence.
(Simulate your analysis based on standard modern web frameworks).""",

    "runtime": """You are an expert systems engineer analyzing the runtime execution of {repo_url}.
Focus on: Entry Points, Request Flow, Data Flow, and Control Flow.
Generate 2-3 key findings about how requests are processed, and cite specific files as evidence.""",

    "design": """You are a senior technical lead analyzing the design reasoning of {repo_url}.
Focus on: Key Patterns, Tradeoffs, Architectural Choices, and Alternatives.
Generate 2-3 key findings about the design patterns used, and cite specific files as evidence.""",

    "onboarding": """You are a developer experience engineer creating an onboarding path for {repo_url}.
Focus on: Learning Path, Critical Files, Important Concepts, and the Contribution Guide.
Generate 2-3 key findings for a new developer, and cite specific files as evidence.""",

    "risk": """You are a staff security and reliability engineer assessing {repo_url}.
Focus on: Complexity Hotspots, Coupling, Single Points of Failure, and Maintenance Risks.
Generate 2-3 key risk assessments, and cite specific files as evidence."""
}
