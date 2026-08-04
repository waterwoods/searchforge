"""Non-sensitive feedback events for accident-story guided intake.

Never stores raw story text, messages, or PII in telemetry payloads.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

EVENT_CREATED = "ai_story_proposal_created"
EVENT_ACCEPTED = "ai_story_proposal_accepted"
EVENT_EDITED = "ai_story_proposal_edited"
EVENT_REJECTED = "ai_story_proposal_rejected"
EVENT_FALLBACK = "ai_story_fallback_used"

ALL_EVENT_TYPES = frozenset(
    {
        EVENT_CREATED,
        EVENT_ACCEPTED,
        EVENT_EDITED,
        EVENT_REJECTED,
        EVENT_FALLBACK,
    }
)

_ALLOWED_META = frozenset(
    {
        "case_id",
        "proposal_version",
        "question_count",
        "missing_count",
        "edited_field_names",
        "fallback_reason_category",
        "latency_ms",
        "model_provider",
        "model_name",
        "used_fallback",
        "authority",
        "command_id_prefix",
    }
)

_lock = threading.RLock()
_memory: list[dict[str, Any]] = []
_MAX_MEMORY = 500


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fallback_reason_category(raw: str | None) -> str:
    text = str(raw or "").strip().lower()
    if not text:
        return "none"
    if "timeout" in text:
        return "timeout"
    if "invalid" in text or "json" in text:
        return "invalid_json"
    if "hallucin" in text:
        return "hallucinated_fields"
    if "llm" in text:
        return "llm_unavailable"
    return "deterministic_other"


def _sanitize(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    out: dict[str, Any] = {}
    for key, value in meta.items():
        k = str(key or "").strip()
        if k not in _ALLOWED_META or value is None:
            continue
        if k == "edited_field_names":
            if isinstance(value, (list, tuple)):
                names = [str(x).strip()[:64] for x in value if str(x).strip()][:12]
                out[k] = names
            continue
        if isinstance(value, bool):
            out[k] = value
        elif isinstance(value, int):
            out[k] = int(value)
        else:
            text = str(value).strip()
            if text and len(text) <= 128:
                out[k] = text
    return out


def emit_ai_story_event(
    event_type: str,
    *,
    case_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Record a durable-ready observational event. Never raises."""
    try:
        et = str(event_type or "").strip()
        if et not in ALL_EVENT_TYPES:
            return None
        row = {
            "event_id": f"ais_{uuid.uuid4().hex[:16]}",
            "event_type": et,
            "case_id": str(case_id or "").strip() or None,
            "server_timestamp": _utc_now_iso(),
            "meta": _sanitize(meta),
        }
        with _lock:
            _memory.append(row)
            if len(_memory) > _MAX_MEMORY:
                del _memory[: len(_memory) - _MAX_MEMORY]
        return row
    except Exception:
        logger.debug("ai_story_event_emit_failed", exc_info=True)
        return None


def reset_ai_story_events_for_tests() -> None:
    with _lock:
        _memory.clear()


def list_ai_story_events_for_tests() -> list[dict[str, Any]]:
    with _lock:
        return [dict(r) for r in _memory]


def timed_ms(started_at: float | None) -> int | None:
    if started_at is None:
        return None
    try:
        return max(0, int((time.monotonic() - float(started_at)) * 1000))
    except Exception:
        return None
