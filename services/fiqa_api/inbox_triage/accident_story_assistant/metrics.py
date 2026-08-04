"""Pilot metrics for Accident Story Assistant (non-sensitive only)."""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from services.fiqa_api.inbox_triage.accident_story_assistant.events import (
    EVENT_ACCEPTED,
    EVENT_CREATED,
    EVENT_EDITED,
    EVENT_FALLBACK,
    EVENT_REJECTED,
    list_ai_story_events_for_tests,
)

EVENT_TIMEOUT = "ai_story_provider_timeout"
EVENT_INVALID = "ai_story_invalid_output"
EVENT_DISABLED = "ai_story_assistant_disabled"
EVENT_TRACE_FAIL = "ai_story_trace_failed"
EVENT_COMPLETION_AFTER_FALLBACK = "ai_story_completion_after_fallback"


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * (p / 100.0)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return float(ordered[lo])
    weight = rank - lo
    return float(ordered[lo] * (1 - weight) + ordered[hi] * weight)


def summarize_pilot_metrics(*, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Compact pilot window summary. Never includes raw stories or PII."""
    rows = events if events is not None else list_ai_story_events_for_tests()
    counts: Counter[str] = Counter()
    latencies: list[float] = []
    question_counts: list[float] = []
    fallback_categories: Counter[str] = Counter()
    unknown_injury_violations = 0
    unnecessary_question_flags = 0

    for row in rows:
        et = str(row.get("event_type") or "")
        counts[et] += 1
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if isinstance(meta.get("latency_ms"), (int, float)):
            latencies.append(float(meta["latency_ms"]))
        if isinstance(meta.get("question_count"), (int, float)):
            question_counts.append(float(meta["question_count"]))
        cat = str(meta.get("fallback_reason_category") or "").strip()
        if cat and cat != "none":
            fallback_categories[cat] += 1
        if meta.get("unknown_injury_violation"):
            unknown_injury_violations += 1
        if meta.get("unnecessary_question"):
            unnecessary_question_flags += 1

    created = counts.get(EVENT_CREATED, 0)
    avg_q = (sum(question_counts) / len(question_counts)) if question_counts else None
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "event_count": len(rows),
        "source": "provided" if events is not None else "memory",
        "proposals_created": created,
        "accepted": counts.get(EVENT_ACCEPTED, 0),
        "edited": counts.get(EVENT_EDITED, 0),
        "rejected": counts.get(EVENT_REJECTED, 0),
        "fallbacks": counts.get(EVENT_FALLBACK, 0),
        "provider_timeouts": counts.get(EVENT_TIMEOUT, 0) + fallback_categories.get("timeout", 0),
        "invalid_output_failures": counts.get(EVENT_INVALID, 0)
        + fallback_categories.get("invalid_json", 0),
        "assistant_disabled_hits": counts.get(EVENT_DISABLED, 0),
        "trace_failures": counts.get(EVENT_TRACE_FAIL, 0),
        "completion_after_fallback": counts.get(EVENT_COMPLETION_AFTER_FALLBACK, 0),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "p95_latency_ms": round(_percentile(latencies, 95) or 0, 2) if latencies else None,
        "avg_question_count": round(avg_q, 3) if avg_q is not None else None,
        "unnecessary_question_rate": (
            round(unnecessary_question_flags / created, 4) if created else None
        ),
        "unknown_injury_safety_violations": unknown_injury_violations,
        "fallback_reason_categories": dict(fallback_categories),
        "pii_policy": "no_raw_stories_phones_openids_tokens_photos_names",
    }


def summarize_durable_pilot_metrics(
    *,
    since: str | None = None,
    until: str | None = None,
    limit: int = 5000,
    include_memory_fallback: bool = True,
) -> dict[str, Any]:
    """Pilot SSOT summary from Postgres when available; optional memory fallback."""
    from services.fiqa_api.inbox_triage.accident_story_assistant.durable_events import (
        load_pilot_events,
    )

    rows = load_pilot_events(since=since, until=until, limit=limit)
    source = "postgres"
    if not rows and include_memory_fallback:
        rows = list_ai_story_events_for_tests()
        source = "memory_fallback"
    summary = summarize_pilot_metrics(events=rows)
    summary["source"] = source
    summary["window"] = {"since": since, "until": until, "limit": limit}
    return summary
