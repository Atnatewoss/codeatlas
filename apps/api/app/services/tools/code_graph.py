"""Code graph — wraps graphifyy for AST code intelligence.

Provides ToT agents with:
- Symbol lookups (function/class definitions)
- Call graph (who calls what)
- Import graph (module dependencies)
- Mermaid diagram generation
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.log import get_logger

logger = get_logger(__name__)
_code_graph = None
_graph_built = False

try:
    from graphify.detect import detect
    from graphify.extract import extract as graphify_extract
    from graphify.build import build_from_json
    import networkx as nx
    HAS_GRAPHIFY = True
except ImportError:
    HAS_GRAPHIFY = False
    nx = None


def build_code_graph(repo_path: str) -> bool:
    """Build the code graph from a repo path. Safe to call multiple times (cached)."""
    global _code_graph, _graph_built

    if _graph_built:
        return True

    if not HAS_GRAPHIFY:
        logger.warning("graphifyy not installed — code graph unavailable")
        return False

    try:
        root = Path(repo_path).resolve()
        result = detect(root)
        code_files = [Path(f) for f in result["files"]["code"]]

        if not code_files:
            logger.info("No code files detected in %s", repo_path)
            _code_graph = nx.DiGraph()
            _graph_built = True
            return True

        extraction = graphify_extract(code_files)
        _code_graph = build_from_json(extraction, directed=True)
        _graph_built = True
        logger.info("Code graph built: %d nodes, %d edges, %d files",
                     _code_graph.number_of_nodes(),
                     _code_graph.number_of_edges(),
                     len(set(
                         d.get("source_file", "")
                         for _, d in _code_graph.nodes(data=True)
                         if d.get("source_file")
                     )))
        return True

    except Exception as e:
        logger.warning("Code graph build failed: %s", e)
        return False


def get_or_build_graph(repo_path: str):
    """Build or retrieve cached code graph."""
    build_code_graph(repo_path)
    return _code_graph


def lookup_symbol(name: str) -> List[Dict[str, Any]]:
    """Find all definitions of a symbol by name (substring match)."""
    if _code_graph is None:
        return []
    name_lower = name.lower()
    results = []
    for node_id, data in _code_graph.nodes(data=True):
        node_name = data.get("label", "")
        if name_lower in node_name.lower():
            results.append({
                "name": node_name,
                "kind": data.get("file_type", "code"),
                "file": data.get("source_file", ""),
                "line": data.get("source_location", ""),
            })
    return results


def search_symbols(query: str) -> List[Dict[str, Any]]:
    """Search symbols by name substring."""
    return lookup_symbol(query)


def get_callers(function_name: str) -> List[str]:
    """Find what calls a function."""
    if _code_graph is None:
        return []
    callers = []
    for node_id, data in _code_graph.nodes(data=True):
        if data.get("label") == function_name:
            for pred in _code_graph.predecessors(node_id):
                edge_data = _code_graph.edges[pred, node_id]
                if edge_data.get("relation") == "calls":
                    callers.append(_code_graph.nodes[pred].get("label", pred))
    return callers


def get_callees(function_name: str) -> List[str]:
    """Find what a function calls."""
    if _code_graph is None:
        return []
    callees = []
    for node_id, data in _code_graph.nodes(data=True):
        if data.get("label") == function_name:
            for succ in _code_graph.successors(node_id):
                edge_data = _code_graph.edges[node_id, succ]
                if edge_data.get("relation") == "calls":
                    callees.append(_code_graph.nodes[succ].get("label", succ))
    return callees


def get_files_importing(module: str) -> List[str]:
    """Find files that import a module."""
    if _code_graph is None:
        return []
    results = []
    for node_id, data in _code_graph.nodes(data=True):
        if module.lower() in data.get("label", "").lower():
            for pred in _code_graph.predecessors(node_id):
                edge_data = _code_graph.edges[pred, node_id]
                if edge_data.get("relation") in ("imports", "imports_from"):
                    file_path = _code_graph.nodes[pred].get("source_file", "")
                    if file_path and file_path not in results:
                        results.append(file_path)
    return results


def get_graph_stats() -> Dict[str, Any]:
    """Get code graph statistics."""
    if _code_graph is None:
        return {"nodes": 0, "edges": 0, "files": 0}
    files = set(
        d.get("source_file", "")
        for _, d in _code_graph.nodes(data=True)
    )
    files.discard("")
    return {
        "nodes": _code_graph.number_of_nodes(),
        "edges": _code_graph.number_of_edges(),
        "files": len(files),
    }


def generate_mermaid_callflow(max_nodes: int = 25) -> str:
    """Generate a Mermaid flowchart from the code graph showing call relationships.

    Returns an empty string if the graph isn't built or has no call edges.
    """
    if _code_graph is None or _code_graph.number_of_nodes() == 0:
        return ""

    lines = ["```mermaid", "flowchart TD"]
    edges_added = 0

    for u, v, data in _code_graph.edges(data=True):
        if data.get("relation") in ("calls", "imports", "imports_from"):
            u_label = _code_graph.nodes[u].get("label", str(u))[:40]
            v_label = _code_graph.nodes[v].get("label", str(v))[:40]
            safe_u = u.replace("-", "_").replace(" ", "_")[:30]
            safe_v = v.replace("-", "_").replace(" ", "_")[:30]
            rel = data.get("relation", "calls")
            lines.append(f'  {safe_u}["{u_label}"]-->{safe_v}["{v_label}"]')
            edges_added += 1
            if edges_added >= max_nodes:
                break

    lines.append("```")
    return "\n".join(lines) if edges_added > 0 else ""
