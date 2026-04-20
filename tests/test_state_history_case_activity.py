"""Unit tests for PG case_activity reconstruction from state_history."""

from __future__ import annotations

from datetime import datetime, timezone

from services.fiqa_api.db.service_record_repository import _case_activity_from_state_history_rows


def test_case_activity_maps_case_created_and_appended():
    rows = [
        (
            "550e8400-e29b-41d4-a716-446655440001",
            "conversation_appended",
            "reviewing",
            "handoff_pending",
            datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        ),
        (
            "550e8400-e29b-41d4-a716-446655440000",
            "case_created",
            "new",
            "Hello",
            datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]
    out = _case_activity_from_state_history_rows(rows)
    assert len(out) == 2
    assert out[0]["activity_type"] == "conversation_appended"
    assert "handoff_pending" in out[0]["message"]
    assert out[1]["activity_type"] == "case_created"
    assert "Case record created" in out[1]["message"]
