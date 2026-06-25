import os
import re
from pathlib import Path

EXCLUDE_DIRS = {
    "node_modules", "venv", ".venv", "env", "__pycache__",
    "dist", "build", "out", "target", "vendor",
    ".git", ".next", ".github", ".vscode", ".idea",
}

TEXT_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".json", ".md", ".html", ".css", ".scss", ".less",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".rs", ".go", ".c", ".cpp", ".cc", ".h", ".hpp", ".hxx",
    ".java", ".kt", ".rb", ".php", ".sql", ".r", ".m", ".mm",
    ".xml", ".svg", ".tex", ".rst", ".txt",
    ".sh", ".bash", ".ps1", ".bat", ".cmd", ".psm1",
    ".pyi", ".pxd", ".pxi",
}


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTS


def walk_repo(repo_path: str, max_files: int = 500) -> list[Path]:
    root = Path(repo_path)
    if not root.exists():
        return []
    files = []
    try:
        for entry in root.rglob("*"):
            if entry.is_file() and is_text_file(entry):
                parts = entry.relative_to(root).parts
                if any(p in EXCLUDE_DIRS for p in parts):
                    continue
                if any(p.startswith(".") for p in parts):
                    continue
                files.append(entry)
                if len(files) >= max_files:
                    break
    except (PermissionError, OSError):
        pass
    return files[:max_files]


def tool_grep(repo_path: str, target: str) -> tuple[str, list[str]]:
    root = Path(repo_path)
    if not root.exists():
        return "Repository path does not exist.", []
    results = []
    accessed = []
    try:
        for f in walk_repo(repo_path):
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    if re.search(target, line, re.IGNORECASE):
                        short = line.strip()[:120]
                        rel = str(f.relative_to(root))
                        results.append(f"{rel}:{i}  {short}")
                        if rel not in accessed:
                            accessed.append(rel)
                        if len(results) >= 30:
                            break
            except Exception:
                pass
            if len(results) >= 30:
                break
    except Exception:
        pass
    if not results:
        return f"No matches found for '{target}'.", accessed
    return "\n".join(results[:30]), accessed


def tool_glob(repo_path: str, target: str) -> tuple[str, list[str]]:
    root = Path(repo_path)
    if not root.exists():
        return "Repository path does not exist.", []
    accessed = []
    try:
        matches = []
        for f in root.rglob(target):
            if f.is_file() and is_text_file(f):
                rel = str(f.relative_to(root))
                matches.append(rel)
                accessed.append(rel)
                if len(matches) >= 30:
                    break
        if not matches:
            return f"No files matching '{target}'.", accessed
        return "\n".join(matches[:30]), accessed
    except Exception as e:
        return f"Glob error: {e}", accessed


def tool_read_file(repo_path: str, target: str) -> tuple[str, list[str]]:
    path = Path(repo_path) / target
    if not path.exists():
        return f"File not found: {target}", []
    if not is_text_file(path):
        return f"Binary file: {target}", []
    accessed = [target]
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        if len(lines) > 80:
            return "\n".join(lines[:80]) + f"\n... ({len(lines) - 80} more lines)", accessed
        return text, accessed
    except Exception as e:
        return f"Read error: {e}", accessed


TOOL_MAP = {
    "grep": tool_grep,
    "glob": tool_glob,
    "read_file": tool_read_file,
}

try:
    from app.services.tools.code_graph import (
        lookup_symbol as cg_lookup_symbol,
        get_callers as cg_get_callers,
        get_callees as cg_get_callees,
        get_graph_stats as cg_get_graph_stats,
        HAS_GRAPHIFY,
    )
    HAS_CODE_GRAPH = HAS_GRAPHIFY
except ImportError:
    HAS_CODE_GRAPH = False


def tool_lookup_symbol(repo_path: str, target: str) -> tuple[str, list[str]]:
    if not HAS_CODE_GRAPH:
        return "Code graph unavailable (graphifyy not installed).", []
    results = cg_lookup_symbol(target)
    if not results:
        return f"No symbol found for '{target}'", []
    lines = [f"{r['name']} — {r['kind']} in {r['file']}:{r['line']}" for r in results]
    return "\n".join(lines[:20]), list(set(r["file"] for r in results))


def tool_get_callers(repo_path: str, target: str) -> tuple[str, list[str]]:
    if not HAS_CODE_GRAPH:
        return "Code graph unavailable (graphifyy not installed).", []
    callers = cg_get_callers(target)
    if not callers:
        return f"No callers found for '{target}'", []
    return "\n".join(callers[:20]), []


def tool_get_callees(repo_path: str, target: str) -> tuple[str, list[str]]:
    if not HAS_CODE_GRAPH:
        return "Code graph unavailable (graphifyy not installed).", []
    callees = cg_get_callees(target)
    if not callees:
        return f"No callees found for '{target}'", []
    return "\n".join(callees[:20]), []


def tool_get_graph_stats(repo_path: str, target: str) -> tuple[str, list[str]]:
    if not HAS_CODE_GRAPH:
        return "Code graph unavailable (graphifyy not installed).", []
    stats = cg_get_graph_stats()
    return (
        f"Code graph: {stats['nodes']} nodes, {stats['edges']} edges, {stats['files']} files",
        [],
    )


if HAS_CODE_GRAPH:
    TOOL_MAP["lookup_symbol"] = tool_lookup_symbol
    TOOL_MAP["get_callers"] = tool_get_callers
    TOOL_MAP["get_callees"] = tool_get_callees
    TOOL_MAP["graph_stats"] = tool_get_graph_stats


def execute_tool(tool: str, target: str, repo_path: str) -> tuple[str, list[str]]:
    fn = TOOL_MAP.get(tool)
    if fn is None:
        return f"Unknown tool: {tool}", []
    try:
        return fn(repo_path, target)
    except Exception as e:
        return f"Tool error: {e}", []

