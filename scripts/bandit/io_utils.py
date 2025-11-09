#!/usr/bin/env python3
"""Shared I/O helpers for bandit scripts (state path, locking, atomic JSON)."""

from __future__ import annotations

import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import fcntl

DEFAULT_STATE_PATH = Path.home() / "data" / "searchforge" / "bandit" / "bandit_state.json"
DEFAULT_POLICIES_PATH = Path("configs/policies.json")
LOCK_SUFFIX = ".lock"
LOCK_RETRIES = 5
LOCK_BASE_DELAY = 0.1


def resolve_state_path() -> Path:
    env = os.environ.get("BANDIT_STATE")
    path = Path(env).expanduser() if env else DEFAULT_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_policies_path() -> Path:
    env = os.environ.get("BANDIT_POLICIES")
    path = Path(env).expanduser() if env else DEFAULT_POLICIES_PATH
    return path


def _lock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + LOCK_SUFFIX)


@contextmanager
def file_lock(path: Path, exclusive: bool) -> None:
    """Context manager acquiring flock-based lock with retries."""

    lock_file_path = _lock_path(path)
    lock_file_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = open(lock_file_path, "a+", encoding="utf-8")
    try:
        flags = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        for attempt in range(LOCK_RETRIES):
            try:
                fcntl.flock(lock_file.fileno(), flags | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if attempt + 1 == LOCK_RETRIES:
                    raise
                time.sleep(LOCK_BASE_DELAY * (2**attempt))
        yield
    finally:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()


def read_json(path: Path, default: Any) -> Any:
    with file_lock(path, exclusive=False):
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(path, exclusive=True):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(path.parent)) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp.write("\n")
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)

