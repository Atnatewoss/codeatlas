"""
Code Graph - wraps Graphify for AST extraction.

Provides the ToT agent with code intelligence tools:
- Symbol lookup (find where a function/class is defined)
- Call graph (who calls what)
- Import graph (module dependencies)
- File skeletons (class/function signatures)

Uses Graphify for multi-language tree-sitter parsing (36+ languages).
Graph is built in-memory on clone, no persistence needed.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import networkx as nx

from graphify.detect import detect
from graphify.extract import extract
from graphify.build import build_from_json


class CodeGraph:
    """
    In-memory code knowledge graph backed by Graphify.
    
    Built once per research session from the cloned repo.
    Provides query methods for the ToT agent tools.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = str(Path(repo_path).resolve())
        self.graph: Optional[nx.DiGraph] = None
    
    def build(self) -> None:
        """Build the graph from the repository using Graphify."""
        repo_path = Path(self.repo_path)
        
        # Detect code files
        result = detect(repo_path)
        code_files = [Path(f) for f in result["files"]["code"]]
        
        if not code_files:
            self.graph = nx.DiGraph()
            return
        
        # Extract AST with tree-sitter (offline, no API key)
        extraction = extract(code_files)
        
        # Build NetworkX graph
        self.graph = build_from_json(extraction, directed=True)
    
    def lookup_symbol(self, name: str) -> List[Dict[str, Any]]:
        """Find all definitions of a symbol by name."""
        if self.graph is None:
            return []
        
        results = []
        name_lower = name.lower()
        
        for node_id, data in self.graph.nodes(data=True):
            node_name = data.get("label", "")
            if name_lower in node_name.lower():
                results.append({
                    "name": node_name,
                    "kind": data.get("file_type", "code"),
                    "file": data.get("source_file", ""),
                    "line": data.get("source_location", ""),
                })
        
        return results
    
    def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Search symbols by name (substring match)."""
        if self.graph is None:
            return []
        
        results = []
        query_lower = query.lower()
        
        for node_id, data in self.graph.nodes(data=True):
            node_name = data.get("label", "")
            if query_lower in node_name.lower():
                results.append({
                    "name": node_name,
                    "kind": data.get("file_type", "code"),
                    "file": data.get("source_file", ""),
                    "line": data.get("source_location", ""),
                })
        
        return results
    
    def get_callers(self, function_name: str) -> List[str]:
        """Find what calls a function."""
        if self.graph is None:
            return []
        
        callers = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("label") == function_name:
                for pred in self.graph.predecessors(node_id):
                    edge_data = self.graph.edges[pred, node_id]
                    if edge_data.get("relation") == "calls":
                        callers.append(self.graph.nodes[pred].get("label", pred))
        
        return callers
    
    def get_callees(self, function_name: str) -> List[str]:
        """Find what a function calls."""
        if self.graph is None:
            return []
        
        callees = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("label") == function_name:
                for succ in self.graph.successors(node_id):
                    edge_data = self.graph.edges[node_id, succ]
                    if edge_data.get("relation") == "calls":
                        callees.append(self.graph.nodes[succ].get("label", succ))
        
        return callees
    
    def get_files_importing(self, module: str) -> List[str]:
        """Find files that import a module."""
        if self.graph is None:
            return []
        
        results = []
        for node_id, data in self.graph.nodes(data=True):
            if module.lower() in data.get("label", "").lower():
                for pred in self.graph.predecessors(node_id):
                    edge_data = self.graph.edges[pred, node_id]
                    if edge_data.get("relation") in ("imports", "imports_from"):
                        file_path = self.graph.nodes[pred].get("source_file", "")
                        if file_path and file_path not in results:
                            results.append(file_path)
        
        return results
    
    def get_import_graph(self) -> Dict[str, Any]:
        """Return import relationships as a dict."""
        if self.graph is None:
            return {"nodes": [], "edges": []}
        
        nodes = [{"id": n, "label": d.get("label", n)} 
                 for n, d in self.graph.nodes(data=True)]
        
        edges = [{"source": u, "target": v, "relation": d.get("relation")} 
                 for u, v, d in self.graph.edges(data=True) 
                 if d.get("relation") in ("imports", "imports_from")]
        
        return {"nodes": nodes, "edges": edges}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        if self.graph is None:
            return {"nodes": 0, "edges": 0, "files": 0}
        
        files = set(d.get("source_file", "") for _, d in self.graph.nodes(data=True))
        files.discard("")
        
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "files": len(files),
        }


_cache: Dict[str, CodeGraph] = {}


def get_or_build_graph(repo_path: str) -> CodeGraph:
    """Get cached graph or build fresh."""
    if repo_path in _cache:
        return _cache[repo_path]
    
    graph = CodeGraph(repo_path)
    graph.build()
    _cache[repo_path] = graph
    return graph
