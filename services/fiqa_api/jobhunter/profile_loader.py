"""
profile_loader.py - Load candidate profile from configuration file.

This module provides utilities for loading candidate profiles from disk,
following the same path resolution patterns as applications_tracker.py
and preferences_store.py.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ProfileMode(str, Enum):
    """Enumeration of available candidate profile modes."""
    AGENT = "agent"
    DATA_ENG = "data_eng"


def get_project_root() -> Path:
    """
    Get the project root directory by looking for common markers.
    
    Returns:
        Path to project root directory.
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / "poetry.lock").exists():
            return parent
    
    # Fallback: assume we're in project root relative to current working directory
    return Path(".").resolve()


def get_profile_path_for_mode(mode: Optional[str]) -> Path:
    """
    Map a profile_mode string to a concrete profile file path.
    
    Defaults to the original 'agent' profile for backward compatibility.
    
    Args:
        mode: Profile mode string (e.g., "agent", "data_eng"). 
              If None or unrecognized, defaults to "agent".
    
    Returns:
        Path to the corresponding profile file.
    """
    root = get_project_root()
    
    if mode == ProfileMode.DATA_ENG or mode == ProfileMode.DATA_ENG.value:
        path = root / "data" / "jobhunter" / "candidate_profile_andy_data_eng.md"
    else:
        # Default to the original agent / LLM profile
        path = root / "data" / "jobhunter" / "candidate_profile_andy.md"
    
    return path


def get_default_profile_path() -> Path:
    """
    Get the default candidate profile path relative to project root.
    
    Returns:
        Path to candidate_profile_andy.md in data/jobhunter/ directory.
    """
    # Reuse get_profile_path_for_mode with None to get default (agent) profile
    return get_profile_path_for_mode(None)


def load_candidate_profile(path: Optional[Path] = None) -> str:
    """
    Load candidate profile from a file.
    
    Reads the file content, removes BOM if present, and strips extra whitespace.
    Raises clear exceptions if the file cannot be read.
    
    Args:
        path: Path to the candidate profile file. If None, uses get_default_profile_path().
    
    Returns:
        Candidate profile text as a string.
        
    Raises:
        FileNotFoundError: If the profile file does not exist.
        IOError: If the file cannot be read.
        ValueError: If the file is empty after cleaning.
    """
    if path is None:
        path = get_default_profile_path()
    
    if not path.exists():
        raise FileNotFoundError(
            f"Candidate profile file not found: {path}. "
            f"Please ensure the file exists or provide a custom path."
        )
    
    try:
        # Read file with UTF-8 encoding
        content = path.read_text(encoding="utf-8")
        
        # Remove BOM if present (UTF-8 BOM is \ufeff)
        if content.startswith("\ufeff"):
            content = content[1:]
        
        # Strip leading/trailing whitespace and normalize line endings
        content = content.strip()
        
        # Remove excessive blank lines (more than 2 consecutive newlines)
        lines = content.split("\n")
        cleaned_lines = []
        prev_blank = False
        for line in lines:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue  # Skip consecutive blank lines
            cleaned_lines.append(line)
            prev_blank = is_blank
        
        content = "\n".join(cleaned_lines).strip()
        
        if not content:
            raise ValueError(f"Candidate profile file is empty: {path}")
        
        logger.info(f"Loaded candidate profile from {path} ({len(content)} characters)")
        return content
        
    except UnicodeDecodeError as e:
        raise IOError(
            f"Failed to decode candidate profile file {path} as UTF-8: {e}. "
            f"Please ensure the file is encoded in UTF-8."
        ) from e
    except Exception as e:
        raise IOError(
            f"Failed to read candidate profile file {path}: {e}"
        ) from e

