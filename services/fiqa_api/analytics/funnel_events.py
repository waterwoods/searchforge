"""Canonical funnel events + in-memory ring buffer (no external infra)."""

from __future__ import annotations

import json
import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("analytics")

# Ordered funnel stages (for drop-off naming).
CANONICAL_FUNNEL_EVENTS: tuple[str, ...] = (
    "session_started",
    "first_meaningful_input",
    "case_created",
    "quote_ready_reached",
    "handoff_started",
    "handoff_confirmed",
    "broker_followup_started",
)

_MAX_EVENTS = 10_000
_MAX_DEDUPE_KEYS = 25_000

_lock = threading.Lock()
_events: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
_dedupe_keys: set[str] = set()


def reset_funnel_store() -> None:
    """Clear buffered events and dedupe keys (tests only)."""
    with _lock:
        _events.clear()
        _dedupe_keys.clear()


def iter_funnel_events() -> list[dict[str, Any]]:
    with _lock:
        return list(_events)


def _trim_dedupe_if_needed() -> None:
    if len(_dedupe_keys) <= _MAX_DEDUPE_KEYS:
        return
    # Simple shrink: clear dedupe (may allow rare re-emit after long run; acceptable for MVP).
    _dedupe_keys.clear()


def _dedupe_key_for(event: str, session_id: str | None, case_id: str | None) -> str | None:
    sid = (session_id or "").strip()
    cid = (case_id or "").strip()
    if event == "case_created":
        if not cid and not sid:
            return None
        return f"case_created|{cid or sid}"
    if event == "quote_ready_reached":
        if not sid and not cid:
            return None
        return f"quote_ready_reached|{sid}|{cid}"
    if event == "handoff_started":
        if not sid and not cid:
            return None
        return f"handoff_started|{sid}|{cid}"
    if event == "handoff_confirmed":
        if not sid and not cid:
            return None
        return f"handoff_confirmed|{sid}|{cid}"
    if event == "session_started":
        if not sid:
            return None
        return f"session_started|{sid}"
    if event == "first_meaningful_input":
        if not sid:
            return None
        return f"first_meaningful_input|{sid}"
    if event == "broker_followup_started":
        if not sid and not cid:
            return None
        return f"broker_followup_started|{sid}|{cid}"
    if not sid and not cid:
        return None
    return f"{event}|{sid}|{cid}"


def append_session_analytics_event(
    event: str,
    *,
    session_id: str | None = None,
    case_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append a non-funnel analytics row (dedupe not applied). Used for continuity signals."""
    with _lock:
        ts = datetime.now(timezone.utc).isoformat()
        payload: dict[str, Any] = {
            "event": event,
            "session_id": (session_id or "").strip(),
            "case_id": (case_id or "").strip(),
            "timestamp": ts,
            "metadata": dict(metadata or {}),
        }
        _events.append(payload)
    logger.info("%s", json.dumps(payload, ensure_ascii=False, default=str))


def emit_funnel_event(
    event: str,
    *,
    session_id: str | None = None,
    case_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Record one canonical funnel event (deduped). Logs JSON in standard shape.

    Returns True if the event was newly recorded (False if deduped).
    """
    if event not in CANONICAL_FUNNEL_EVENTS:
        raise ValueError(f"unknown funnel event: {event}")

    key = _dedupe_key_for(event, session_id, case_id)
    with _lock:
        if key is not None:
            if key in _dedupe_keys:
                return False
            _dedupe_keys.add(key)
            _trim_dedupe_if_needed()

        ts = datetime.now(timezone.utc).isoformat()
        payload: dict[str, Any] = {
            "event": event,
            "session_id": (session_id or "").strip(),
            "case_id": (case_id or "").strip(),
            "timestamp": ts,
            "metadata": dict(metadata or {}),
        }
        _events.append(payload)

    logger.info("%s", json.dumps(payload, ensure_ascii=False, default=str))
    return True


def emit_analytics_signal(event: str, payload: dict[str, Any]) -> None:
    """Non-funnel structured log (append_blocked, field_progress, etc.)."""
    line = {"event": event, **payload}
    logger.info("%s", json.dumps(line, ensure_ascii=False, default=str))
