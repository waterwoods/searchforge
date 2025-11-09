from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Dict

import yaml

_CONFIG_LOCK = threading.Lock()
_CONFIG_CACHE: Dict[str, Any] | None = None


def get_config_path() -> Path:
    return Path(__file__).resolve().parent / "config.yaml"


def get_orchestrator_config() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    with _CONFIG_LOCK:
        if _CONFIG_CACHE is None:
            config_path = get_config_path()
            with config_path.open("r", encoding="utf-8") as fp:
                _CONFIG_CACHE = yaml.safe_load(fp) or {}
    return _CONFIG_CACHE or {}

