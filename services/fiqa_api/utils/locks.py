"""
locks.py - File Locking Utilities
==================================
V11: Process-level exclusive locks for file operations.
"""

from contextlib import contextmanager
import os

try:
    import fcntl  # POSIX
except ImportError:
    fcntl = None  # Windows 等环境可后续替换为 portalocker


@contextmanager
def file_lock(lock_path: str):
    """
    进程间排他锁。POSIX 使用 fcntl.flock；无 fcntl 时降级为无锁（仍可跑，但不强保证）。
    
    Args:
        lock_path: Path to lock file
        
    Yields:
        None (lock is held during context)
    """
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    f = open(lock_path, "a+")
    try:
        if fcntl is not None:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        finally:
            f.close()

