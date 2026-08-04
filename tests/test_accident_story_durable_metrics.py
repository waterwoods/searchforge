"""Durable Accident Story pilot event persistence tests."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.accident_story_assistant.events import (
    EVENT_CREATED,
    emit_ai_story_event,
    list_ai_story_events_for_tests,
    reset_ai_story_events_for_tests,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.metrics import (
    summarize_pilot_metrics,
)


def setup_function() -> None:
    reset_ai_story_events_for_tests()


def test_emit_includes_idempotency_and_no_story_pii():
    row = emit_ai_story_event(
        EVENT_CREATED,
        case_id="case_synth_1",
        meta={
            "question_count": 2,
            "latency_ms": 12,
            "raw_story": "SHOULD_NOT_APPEAR",
            "phone": "408-555-0100",
        },
        idempotency_key="idem_durable_1:created",
    )
    assert row is not None
    assert row["idempotency_key"] == "idem_durable_1:created"
    assert "SHOULD_NOT" not in str(row)
    assert "408-555" not in str(row)
    assert row["meta"].get("question_count") == 2


def test_emit_idempotent_memory_mirror_still_records():
    emit_ai_story_event(
        EVENT_CREATED,
        meta={"question_count": 1},
        idempotency_key="idem_dup_mem:created",
    )
    emit_ai_story_event(
        EVENT_CREATED,
        meta={"question_count": 1},
        idempotency_key="idem_dup_mem:created",
    )
    # Memory keeps both mirrors; PG would dedupe — exporter SSOT is PG when available.
    assert len(list_ai_story_events_for_tests()) >= 1
    summary = summarize_pilot_metrics()
    assert summary["proposals_created"] >= 1
    assert "昨天" not in str(summary)
