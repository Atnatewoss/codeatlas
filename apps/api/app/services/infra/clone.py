import os
import re
import hashlib
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.log import get_logger
from app.core.settings import settings
from app.services.infra.events import add_event, ChatSSEEvent


logger = get_logger(__name__)

TEMP_DIRS: dict[str, str] = {}

_GIT_URL_RE = re.compile(r'^(https?://|git@|ssh://)', re.IGNORECASE)
_GIT_SUFFIX_RE = re.compile(r'\.git$', re.IGNORECASE)


def _is_git_url(path: str) -> bool:
    return bool(_GIT_URL_RE.match(path)) or bool(_GIT_SUFFIX_RE.match(path))


def clone_repo(session_id: str, repo_url: str) -> str:
    """Clone a git repo to a persistent cache dir, reusing existing clones."""
    add_event(session_id, ChatSSEEvent.CLONE_PROGRESS, {"message": "Initializing clone..."})

    cache_root = Path(settings.codeatlas_cache_dir or Path.home() / ".codeatlas" / "repos")
    cache_root.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:16]
    repo_dir = cache_root / url_hash

    if repo_dir.is_dir():
        add_event(session_id, ChatSSEEvent.CLONE_PROGRESS, {"message": "Using cached clone..."})
        logger.info("[%s] Using cached clone for %s -> %s", session_id, repo_url, repo_dir)
        TEMP_DIRS[session_id] = str(repo_dir)
        return str(repo_dir)

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"

    start = datetime.now(timezone.utc)
    logger.info("[%s] Clone started: %s", session_id, repo_url)

    try:
        process = subprocess.Popen(
            ["git", "clone", "--progress", "--depth", "1", "--single-branch", repo_url, str(repo_dir)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        for line in process.stdout:
            line_str = line.strip()
            if line_str:
                add_event(session_id, ChatSSEEvent.CLONE_PROGRESS, {"message": line_str})

        process.wait()
        if process.returncode != 0:
            shutil.rmtree(repo_dir, ignore_errors=True)
            TEMP_DIRS.pop(session_id, None)
            raise RuntimeError(f"git clone failed (exit {process.returncode})")
    except Exception as e:
        TEMP_DIRS.pop(session_id, None)
        raise RuntimeError(f"Clone failed: {e}")

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info("[%s] Clone complete in %.1fs: %s", session_id, elapsed, repo_url)
    add_event(session_id, ChatSSEEvent.CLONE_PROGRESS, {"message": f"Clone complete ({elapsed:.0f}s)."})
    TEMP_DIRS[session_id] = str(repo_dir)
    return str(repo_dir)


def resolve_repo_path(session_id: str, raw_path: str) -> str:
    """Resolve the repo path: if it's a git URL, clone it; otherwise use as-is."""
    if os.path.exists(raw_path):
        return str(Path(raw_path).resolve())
    if _is_git_url(raw_path):
        return clone_repo(session_id, raw_path)
    return raw_path
