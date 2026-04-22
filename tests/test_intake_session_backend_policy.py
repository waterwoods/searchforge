"""Intake session backend: explicit in-memory vs Postgres (no silent memory fallback)."""

from __future__ import annotations

import os

import pytest

from services.fiqa_api.inbox_triage import session_repository as sr
from services.fiqa_api.inbox_triage import session_store as ss


def test_production_like_no_db_requires_explicit_allow_for_writes(monkeypatch):
    """Without DB URL and without allow flag, persistence is disabled (no memory fallback)."""
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS", raising=False)
    sr.reset_intake_session_memory_for_tests()
    sid = "sess-policy-disabled"
    ok = sr.upsert_session(
        sid,
        {
            "session_id": sid,
            "turns": [],
            "workflow_state": {},
            "updated_at": "2026-04-22T00:00:00Z",
        },
    )
    assert ok is False
    assert sr.get_session(sid) is None


def test_explicit_allow_uses_in_memory_when_no_db(monkeypatch):
    """Tests opt in via UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS (set in conftest)."""
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS", "1")
    sr.reset_intake_session_memory_for_tests()
    sid = "sess-policy-memory"
    assert sr.upsert_session(
        sid,
        {
            "session_id": sid,
            "turns": [{"role": "customer", "text": "hi"}],
            "workflow_state": {"lifecycle_status": "collecting"},
            "updated_at": "2026-04-22T00:00:01Z",
        },
    )
    got = sr.get_session(sid)
    assert got is not None
    assert len(got.get("turns") or []) == 1


def test_session_store_get_after_save_contract(monkeypatch):
    """save_in_progress_session → get_in_progress_session preserves workflow_state (refresh contract)."""
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS", "1")
    sr.reset_intake_session_memory_for_tests()
    sid = "sess-refresh-contract"
    ss.save_in_progress_session(
        sid,
        [{"role": "customer", "text": "ping"}],
        {"handoff_ready": False, "lifecycle_status": "collecting", "still_needed_fields": ["vin"]},
    )
    data = ss.get_in_progress_session(sid)
    assert data is not None
    ws = data.get("workflow_state") or {}
    assert ws.get("still_needed_fields") == ["vin"]
    assert ws.get("handoff_ready") is False


@pytest.mark.skipif(
    not (os.getenv("SERVICE_RECORD_DATABASE_URL") or os.getenv("DATABASE_URL") or "").strip(),
    reason="Set SERVICE_RECORD_DATABASE_URL or DATABASE_URL for Postgres session integration check.",
)
def test_when_db_url_set_uses_postgres_not_memory():
    """
    Production-like: DB URL present → repository persists via Postgres (not only memory).

    Skipped when no DB URL in the environment.
    """
    sr.reset_intake_session_memory_for_tests()
    sid = "sess-pg-policy-check"
    assert sr.upsert_session(
        sid,
        {
            "session_id": sid,
            "turns": [{"role": "customer", "text": "pg"}],
            "workflow_state": {},
            "updated_at": "2026-04-22T00:00:02Z",
        },
    )
    got = sr.get_session(sid)
    assert got is not None
    assert got["turns"][0]["text"] == "pg"
    sr.delete_session(sid)
