"""
gitinfo.py - Git Information Utilities
======================================
Utility functions for retrieving git SHA information.
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple


def get_git_sha() -> Tuple[str, str]:
    """
    Get git SHA with priority:
    1. Environment variable GIT_SHA or SOURCE_REV
    2. Git command: git rev-parse --short=9 HEAD
    3. Fallback to "unknown"
    
    Returns:
        Tuple of (sha, source) where source is "env", "git", or "unknown"
    """
    # Priority 1: Environment variable
    env_sha = os.getenv("GIT_SHA") or os.getenv("SOURCE_REV")
    if env_sha:
        return env_sha.strip(), "env"
    
    # Priority 2: Git command
    try:
        repo_root = find_repo_root_for_git()
        result = subprocess.run(
            ["git", "rev-parse", "--short=9", "HEAD"],
            capture_output=True,
            text=True,
            timeout=1,
            stderr=subprocess.DEVNULL,
            cwd=str(repo_root)
        )
        if result.returncode == 0:
            sha = result.stdout.strip()
            if sha:
                return sha, "git"
    except Exception:
        pass
    
    # Fallback
    return "unknown", "unknown"


def find_repo_root_for_git() -> str:
    """
    Find repository root by searching upward for pyproject.toml or .git.
    
    Returns:
        Path to repository root (as string)
    """
    current = Path(__file__).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return str(candidate)
    # Fallback to current directory
    return str(Path.cwd())

