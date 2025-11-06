"""
fs.py - File System Utilities
==============================
Helper functions for file operations, directory creation, and JSON persistence.
"""

import os
import json
import time
import logging
import tempfile
from pathlib import Path
from typing import Any, List, Optional

from .locks import file_lock

logger = logging.getLogger(__name__)


def ensure_dir(path: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        path: Directory path to create
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def read_json(path: str, default: Any = None) -> Any:
    """
    Read JSON file, return default if not found.
    
    Args:
        path: File path
        default: Default value if file doesn't exist
        
    Returns:
        Parsed JSON data or default
    """
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON at {path}: {e}")
        return default
    except Exception as e:
        logger.error(f"Failed to read JSON at {path}: {e}")
        return default


def write_json_atomic(path: str, obj: Any, lock_path: Optional[str] = None) -> None:
    """
    Atomically write JSON file (write to temp file, fsync, then replace).
    
    Args:
        path: Target file path
        obj: Object to serialize
        lock_path: Optional lock file path for process-level exclusive locking
    """
    path_dir = os.path.dirname(path)
    if path_dir:
        os.makedirs(path_dir, exist_ok=True)
    
    # Create temp file in same directory
    d = path_dir or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_", suffix="", text=True)
    tmp_path = tmp
    
    try:
        # Write to temporary file with fsync
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk
        
        # Replace atomically (with optional lock)
        if lock_path:
            with file_lock(lock_path):
                os.replace(tmp_path, path)
        else:
            os.replace(tmp_path, path)
        
        # Sync parent directory to ensure metadata is written
        if path_dir:
            try:
                dir_fd = os.open(path_dir, os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except Exception as e:
                # Directory fsync may fail on some filesystems, log but don't fail
                logger.warning(f"Failed to fsync directory {path_dir}: {e}")
            
    except Exception as e:
        logger.error(f"Failed to write JSON at {path}: {e}")
        # Clean up temp file on error
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise
    finally:
        # Clean up temp file if it still exists (shouldn't happen normally)
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def tail_file(path: str, n: int = 200) -> List[str]:
    """
    Read last N lines from a file.
    
    Args:
        path: File path
        n: Number of lines to read (default: 200)
        
    Returns:
        List of lines (empty if file doesn't exist)
    """
    if not os.path.exists(path):
        return []
    
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
            return lines[-n:] if len(lines) > n else lines
    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        return []


def write_text_file(path: str, content: str) -> None:
    """
    Write text content to file.
    
    Args:
        path: File path
        content: Text content to write
    """
    try:
        with open(path, 'w') as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to write file {path}: {e}")
        raise


def read_text_file(path: str) -> str:
    """
    Read text file.
    
    Args:
        path: File path
        
    Returns:
        File content as string
    """
    if not os.path.exists(path):
        return ""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        return ""



