"""
LangChain tools for Tree of Thought repository exploration.

Two categories:
1. File tools - navigate the repo (search, read, skeleton)
2. Graph tools - understand code relationships (callers, callees, imports)

Both feed the ToT agent's branches:
- Structure: search_file_tree, get_import_graph
- Runtime: find_references, get_callers, get_callees
- Design: get_file_skeleton, lookup_symbol
- Onboarding: search_file_tree, get_stats
- Risk: get_callers, search_symbols
"""

import os
import re
import json
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool
from graphify.code_graph import get_or_build_graph


# ---------------------------------------------------------------------------
# File exploration tools
# ---------------------------------------------------------------------------

@tool
def search_file_tree(repo_path: str, pattern: str) -> List[str]:
    """Search for files matching a regex pattern. Returns up to 50 paths."""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return []
    
    matches = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if regex.search(f):
                matches.append(os.path.relpath(os.path.join(root, f), repo_path))
    return matches[:50]


@tool
def read_file_chunk(repo_path: str, filepath: str, start_line: int, end_line: int) -> str:
    """Read specific lines of a file (1-indexed). Use to examine implementations."""
    full_path = os.path.join(repo_path, filepath)
    if not os.path.exists(full_path):
        return f"File not found: {filepath}"
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        return "".join(lines[max(0, start_line-1):min(len(lines), end_line)])
    except Exception as e:
        return f"Error: {e}"


@tool
def read_file(repo_path: str, filepath: str) -> str:
    """Read an entire file. Returns up to 8000 chars."""
    full_path = os.path.join(repo_path, filepath)
    if not os.path.exists(full_path):
        return f"File not found: {filepath}"
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()[:8000]
    except Exception as e:
        return f"Error: {e}"


@tool
def find_references(repo_path: str, symbol: str) -> List[str]:
    """Find where a symbol is mentioned (word-boundary match). Returns up to 50 results."""
    pattern = re.compile(r'\b' + re.escape(symbol) + r'\b')
    matches = []
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_path)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as fh:
                    for i, line in enumerate(fh):
                        if pattern.search(line):
                            matches.append(f"{rel_path}:{i+1}: {line.strip()[:120]}")
            except Exception:
                continue
    return matches[:50]


@tool
def get_file_skeleton(repo_path: str, filepath: str) -> str:
    """Get class/function signatures from a file (via knowledge graph). Omit bodies."""
    graph = get_or_build_graph(repo_path)
    if graph.graph is None:
        return "Graph not built"
    
    lines = []
    for node_id, data in graph.graph.nodes(data=True):
        if data.get("source_file") == filepath:
            name = data.get("label", node_id)
            kind = data.get("file_type", "code")
            lines.append(f"[{kind}] {name}")
    
    return "\n".join(lines) if lines else f"No symbols found in {filepath}"


# ---------------------------------------------------------------------------
# Knowledge graph tools (Graphify-backed)
# ---------------------------------------------------------------------------

@tool
def lookup_symbol(repo_path: str, name: str) -> List[Dict[str, Any]]:
    """Find definitions of a symbol (class, function, method). Returns file, line, kind."""
    graph = get_or_build_graph(repo_path)
    return graph.lookup_symbol(name)[:20]


@tool
def search_symbols(repo_path: str, query: str) -> List[Dict[str, Any]]:
    """Search symbols by name (substring match)."""
    graph = get_or_build_graph(repo_path)
    return graph.search_symbols(query)[:30]


@tool
def get_callers(repo_path: str, function_name: str) -> List[str]:
    """Find what calls a function (upstream dependencies)."""
    graph = get_or_build_graph(repo_path)
    return graph.get_callers(function_name)[:30]


@tool
def get_callees(repo_path: str, function_name: str) -> List[str]:
    """Find what a function calls (downstream dependencies)."""
    graph = get_or_build_graph(repo_path)
    return graph.get_callees(function_name)[:30]


@tool
def get_files_importing(repo_path: str, module: str) -> List[str]:
    """Find files that import a given module."""
    graph = get_or_build_graph(repo_path)
    return graph.get_files_importing(module)[:30]


@tool
def get_import_graph(repo_path: str) -> str:
    """Get module dependency graph. Returns nodes and import edges."""
    graph = get_or_build_graph(repo_path)
    return json.dumps(graph.get_import_graph(), indent=2)[:4000]


@tool
def get_graph_stats(repo_path: str) -> Dict[str, Any]:
    """Get codebase stats: node count, edge count, file count."""
    graph = get_or_build_graph(repo_path)
    return graph.get_stats()


# ---------------------------------------------------------------------------
# Submit findings (concludes a ToT branch)
# ---------------------------------------------------------------------------

@tool
def submit_findings(findings: List[Dict[str, Any]]) -> str:
    """Submit your final analysis. Call when done exploring.
    
    Args:
        findings: List of dicts, each with:
            - "text": The finding (e.g., "Repository uses layered architecture")
            - "confidence": Float 0-1 (e.g., 0.85 = high confidence, 0.4 = uncertain)
            - "evidence": List of {"filepath", "snippet", "explanation"} dicts
    
    Be honest about confidence. Low confidence findings help the evaluator
    identify areas that need investigation.
    """
    return "Findings submitted."


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

FILE_TOOLS = [search_file_tree, read_file_chunk, read_file, find_references, get_file_skeleton]
GRAPH_TOOLS = [lookup_symbol, search_symbols, get_callers, get_callees, 
               get_files_importing, get_import_graph, get_graph_stats]
ALL_TOOLS = FILE_TOOLS + GRAPH_TOOLS + [submit_findings]


# ---------------------------------------------------------------------------
# ToT Branch Prompts
# ---------------------------------------------------------------------------

PROMPTS = {
    "structure": """You are analyzing the structure of {repo_path}.

APPROACH: Mental Model → Zoom In
1. Start broad: `get_graph_stats` for overview
2. Map dependencies: `get_import_graph`
3. Find config files: `search_file_tree` for package.json, pyproject.toml, etc.
4. Get skeletons FIRST: `get_file_skeleton` on entry points before reading code
5. Only `read_file_chunk` when you need specific implementation details

Generate 3-5 findings with CONFIDENCE SCORES (0-1):
- 0.9+ = certain (directly observed)
- 0.7-0.9 = confident (strong evidence)
- 0.5-0.7 = moderate (inferred)
- <0.5 = uncertain (needs investigation)

Cite specific files as evidence.""",

    "runtime": """You are analyzing runtime execution of {repo_path}.

APPROACH: Mental Model → Zoom In
1. Find entry points: `search_file_tree` for main.py, index.ts, App.tsx
2. Get skeletons: `lookup_symbol` then `get_file_skeleton` before reading code
3. Trace execution: `get_callees` to see what entry points call
4. Only `read_file_chunk` for specific implementation details

Generate 3-5 findings with CONFIDENCE SCORES (0-1):
- 0.9+ = certain (directly observed)
- 0.7-0.9 = confident (strong evidence)
- 0.5-0.7 = moderate (inferred)
- <0.5 = uncertain (needs investigation)

Cite specific files as evidence.""",

    "design": """You are analyzing design patterns in {repo_path}.

APPROACH: Mental Model → Zoom In
1. Find abstractions: `search_symbols` for classes, interfaces, traits
2. Get skeletons: `get_file_skeleton` on core files before reading code
3. Understand interfaces: `lookup_symbol` on key types
4. Trace interactions: `get_callers` and `get_callees`

Generate 3-5 findings with CONFIDENCE SCORES (0-1):
- 0.9+ = certain (directly observed)
- 0.7-0.9 = confident (strong evidence)
- 0.5-0.7 = moderate (inferred)
- <0.5 = uncertain (needs investigation)

Cite specific files as evidence.""",

    "onboarding": """You are creating an onboarding path for {repo_path}.

APPROACH: Mental Model → Zoom In
1. Find docs: `search_file_tree` for README.md, CONTRIBUTING.md, docs/
2. Get overview: `get_graph_stats`
3. Identify key files: `get_file_skeleton` on core modules
4. Find main abstractions: `search_symbols`

Generate 3-5 findings with CONFIDENCE SCORES (0-1):
- 0.9+ = certain (directly observed)
- 0.7-0.9 = confident (strong evidence)
- 0.5-0.7 = moderate (inferred)
- <0.5 = uncertain (needs investigation)

Cite specific files as evidence.""",

    "risk": """You are assessing risks in {repo_path}.

APPROACH: Mental Model → Zoom In
1. Get overview: `get_graph_stats`
2. Find complexity: `search_symbols` for large classes
3. Find single points of failure: `get_callers` (called by many)
4. Examine hotspots: `get_file_skeleton` on complex files

Generate 3-5 findings with CONFIDENCE SCORES (0-1):
- 0.9+ = certain (directly observed)
- 0.7-0.9 = confident (strong evidence)
- 0.5-0.7 = moderate (inferred)
- <0.5 = uncertain (needs investigation)

Cite specific files as evidence.""",

    "evaluate": """You are evaluating the findings from 5 analysis branches.

INPUT: Findings from Structure, Runtime, Design, Onboarding, Risk branches.

YOUR TASK:
1. Detect CONTRADICTIONS between branches (e.g., Structure says "microservice" but Runtime says "single process")
2. Identify AGREEMENTS (branches confirming the same insight)
3. Flag LOW CONFIDENCE findings that need investigation
4. Determine which contradictions need resolution

OUTPUT:
- contradictions: List of conflicting findings with branch names
- agreements: List of confirmed insights
- low_confidence: Findings with confidence < 0.5
- investigation_needed: What the synthesis node should investigate""",

    "synthesize": """You are synthesizing findings from all analysis branches and evaluation.

INPUT: All branch findings, evaluation results (contradictions, agreements, low confidence items).

YOUR TASK:
1. Resolve contradictions (investigate if needed, or note uncertainty)
2. Merge agreements into strong insights
3. Address low-confidence items
4. Create a coherent narrative of the codebase

OUTPUT:
- summary: 2-3 sentence overview
- key_insights: Top 5 insights with confidence
- architecture_overview: How the codebase is organized
- learning_path: Ordered list of files/concepts to learn
- risk_summary: Top risks and mitigation suggestions"""
}
