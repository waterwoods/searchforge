"""Minimal user-behavior signals via structured logging (no external services, no I/O beyond logging)."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger("analytics")


def track_event(event_name: str, payload: dict) -> None:
    """Emit one JSON line on the analytics logger (async-safe: standard logging only)."""
    line = {"event": event_name, **payload}
    logger.info("%s", json.dumps(line, ensure_ascii=False, default=str))
