import os
import re
import ast
from typing import List

SUPPORTED_EXTS = {'.py', '.js', '.ts', '.tsx', '.go', '.java', '.c', '.cpp', '.h', '.hpp'}

def search_file_tree(repo_path: str, pattern: str) -> List[str]:
    """Search for files in the repository matching a regex pattern."""
    matches = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return []

    for root, dirs, files in os.walk(repo_path):
        # Exclude hidden dirs like .git
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if regex.search(f):
                rel_path = os.path.relpath(os.path.join(root, f), repo_path)
                matches.append(rel_path)
    return matches

def read_file_chunk(repo_path: str, filepath: str, start_line: int, end_line: int) -> str:
    """Read specific lines of a file."""
    full_path = os.path.join(repo_path, filepath)
    if not os.path.exists(full_path):
        return f"File not found: {filepath}"
        
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        chunk = lines[start_idx:end_idx]
        return "".join(chunk)
    except Exception as e:
        return f"Error reading file {filepath}: {str(e)}"

def get_file_skeleton(repo_path: str, filepath: str) -> str:
    """Extract classes and function signatures from a file, omitting the body."""
    full_path = os.path.join(repo_path, filepath)
    if not os.path.exists(full_path):
        return f"File not found: {filepath}"
        
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Special handling for Python using AST for accuracy
        if filepath.endswith('.py'):
            try:
                tree = ast.parse(content)
                skeleton = []
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        skeleton.append(f"class {node.name}:")
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                skeleton.append(f"    def {item.name}(...): ...")
                    elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                        skeleton.append(f"{prefix} {node.name}(...): ...")
                
                return "\n".join(skeleton) if skeleton else "(No classes or functions found)"
            except SyntaxError:
                pass # Fall back to regex if syntax error

        # Generic regex-based fallback for TS/JS/etc.
        lines = content.split('\n')
        skeleton = []
        # Basic regex to catch class definitions, function definitions, and const arrow functions
        sig_regex = re.compile(r'^(?:export\s+)?(?:default\s+)?(?:class|function|const|let|var)\s+([a-zA-Z0-9_]+)')
        for line in lines:
            if sig_regex.search(line.strip()):
                skeleton.append(line.strip())
                
        return "\n".join(skeleton) if skeleton else "(No signatures found)"
    except Exception as e:
        return f"Error parsing skeleton for {filepath}: {str(e)}"

def find_references(repo_path: str, symbol: str) -> List[str]:
    """Find files and line numbers where a symbol is mentioned."""
    matches = []
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext not in SUPPORTED_EXTS:
                continue
                
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_path)
            
            try:
                with open(full_path, 'r', encoding='utf-8') as file_obj:
                    for i, line in enumerate(file_obj):
                        if symbol in line:
                            matches.append(f"{rel_path}:{i+1}: {line.strip()[:100]}")
            except Exception:
                continue # Skip unreadable files
                
    return matches
