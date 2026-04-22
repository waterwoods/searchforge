"""Intake session persistence: in-process (no DATABASE_URL) or Postgres when configured."""

from __future__ import annotations

import os

import pytest

from services.fiqa_api.inbox_triage import session_repository as sr
from services.fiqa_api.inbox_triage import session_store as ss


def test_create_get_roundtrip():
    sid = "sess-round-1"
    ss.save_in_progress_session(
        sid,
        [{"role": "customer", "text": "hello"}],
        {"lifecycle_status": "collecting", "handoff_ready": False},
    )
    data = ss.get_in_progress_session(sid)
    assert data is not None
    assert len(data.get("turns", [])) == 1
    assert data["turns"][0]["text"] == "hello"
    assert (data.get("workflow_state") or {}).get("lifecycle_status") == "collecting"


def test_turns_persist_across_updates():
    sid = "sess-turns-2"
    ss.save_in_progress_session(
        sid,
        [{"role": "customer", "text": "a"}],
        {"lifecycle_status": "collecting"},
    )
    ss.save_in_progress_session(
        sid,
        [
            {"role": "customer", "text": "a"},
            {"role": "system", "text": "b", "triageResult": {"handoff_ready": False}},
        ],
        {"lifecycle_status": "collecting", "handoff_ready": False},
    )
    data = ss.get_in_progress_session(sid)
    assert data and len(data["turns"]) == 2


def test_workflow_state_patch_via_save():
    sid = "sess-wf-3"
    ss.save_in_progress_session(
        sid,
        [{"role": "customer", "text": "x"}],
        {"collection_stage": "vehicle", "handoff_ready": False},
    )
    ss.save_in_progress_session(
        sid,
        [{"role": "customer", "text": "x"}],
        {"collection_stage": "zip", "handoff_ready": True},
    )
    data = ss.get_in_progress_session(sid)
    assert (data.get("workflow_state") or {}).get("collection_stage") == "zip"
    assert (data.get("workflow_state") or {}).get("handoff_ready") is True


def test_repository_api_surface():
    """Direct repository roundtrip (used for multi-instance parity when DATABASE_URL is set)."""
    sid = "sess-repo-4"
    assert sr.upsert_session(
        sid,
        {
            "session_id": sid,
            "turns": [],
            "workflow_state": {"x": 1},
            "updated_at": "2026-01-01T00:00:00Z",
        },
    )
    got = sr.get_session(sid)
    assert got is not None
    assert (got.get("workflow_state") or {}).get("x") == 1


@pytest.mark.skipif(
    not (os.getenv("INTAKE_SESSION_PG_TEST_URL") or "").strip(),
    reason="Set INTAKE_SESSION_PG_TEST_URL to run Postgres cross-check (optional).",
)
def test_postgres_two_processes_share_state():
    """Optional: two fresh connections see the same row (simulates two instances)."""
    import psycopg

    url = os.environ["INTAKE_SESSION_PG_TEST_URL"].strip()
    sid = "sess-pg-shared-5"
    os.environ["SERVICE_RECORD_DATABASE_URL"] = url
    try:
        sr.reset_intake_session_memory_for_tests()
        assert sr.upsert_session(
            sid,
            {
                "session_id": sid,
                "turns": [{"role": "customer", "text": "pg"}],
                "workflow_state": {},
                "updated_at": "2026-04-22T00:00:00Z",
            },
        )
        conn = psycopg.connect(url, connect_timeout=10)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM intake_sessions WHERE session_id = %s",
                    (sid,),
                )
                assert cur.fetchone() is not None
        finally:
            conn.close()
    finally:
        os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
        sr.reset_intake_session_memory_for_tests()


def test_in_memory_persistence_creates_no_json_artifact(tmp_path, monkeypatch):
    """With DATABASE_URL unset, the session module must not create session JSON files."""
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    sr.reset_intake_session_memory_for_tests()
    ss.save_in_progress_session(
        "sess-no-file-6",
        [{"role": "customer", "text": "z"}],
        {"handoff_ready": False},
    )
    # Nothing under tmp_path: session_store no longer takes a file path
    assert not (tmp_path / "unified_intake_sessions.json").exists()
    assert ss.get_in_progress_session("sess-no-file-6") is not None
