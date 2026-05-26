"""Intake session persistence: in-process (no DATABASE_URL) or Postgres when configured."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from services.fiqa_api.inbox_triage import session_repository as sr
from services.fiqa_api.inbox_triage import session_store as ss


def test_payload_unchanged_fast_path_length_mismatch():
    """No-op detection must short-circuit when turn counts differ (skip expensive JSON compare)."""
    from services.fiqa_api.inbox_triage.session_store import _in_progress_session_payload_unchanged

    prev_turns = [{"role": "customer", "text": "hello"}]
    next_turns = [
        {"role": "customer", "text": "hello"},
        {"role": "customer", "text": "more"},
    ]
    wf = {"lifecycle_status": "collecting", "handoff_ready": False}
    assert (
        _in_progress_session_payload_unchanged(
            {"turns": prev_turns, "workflow_state": wf},
            next_turns,
            wf,
        )
        is False
    )


def test_payload_unchanged_true_when_identical():
    from services.fiqa_api.inbox_triage.session_store import _in_progress_session_payload_unchanged

    turns = [{"role": "customer", "text": "a"}]
    wf = {"lifecycle_status": "collecting", "handoff_ready": False}
    raw = {"turns": list(turns), "workflow_state": dict(wf)}
    assert _in_progress_session_payload_unchanged(raw, list(turns), dict(wf)) is True


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


def test_assume_fresh_co_read_skips_get_session():
    """Route co-read miss: avoid a second repo read before first upsert."""
    sid = "sess-fresh-co-read"
    sr.reset_intake_session_memory_for_tests()
    calls: list[str] = []

    def tracked_get(_sid: str):
        calls.append("get")
        return None

    with patch.object(ss.repo, "get_session", side_effect=tracked_get):
        ss.save_in_progress_session(
            sid,
            [{"role": "customer", "text": "only"}],
            {"lifecycle_status": "collecting", "handoff_ready": False},
            pre_read_raw=None,
            assume_fresh_co_read=True,
        )
    assert calls == []
    assert sr.get_session(sid) is not None


def test_patch_case_binding_no_op_skips_upsert():
    """Redundant clear_active_case on row without binding should not write."""
    sid = "sess-patch-noop"
    sr.reset_intake_session_memory_for_tests()
    ss.save_in_progress_session(
        sid,
        [{"role": "customer", "text": "b"}],
        {"lifecycle_status": "collecting", "handoff_ready": False},
    )
    raw = sr.get_session(sid)
    assert raw is not None
    n_upsert = 0
    real_up = sr.upsert_session

    def counted_upsert(s: str, p: dict, **_kw):
        nonlocal n_upsert
        n_upsert += 1
        return real_up(s, p, **_kw)

    with patch.object(ss.repo, "upsert_session", side_effect=counted_upsert):
        out = ss.patch_session_case_binding(sid, clear_active_case=True, reuse_session_row=raw)
    assert out is not None
    assert n_upsert == 0


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


def test_save_session_binding_preserves_asserted_org_after_trim():
    """Post-create session trim must not drop office hint (continuity for multi-office pilots)."""
    sid = "sess-org-trim-1"
    sr.reset_intake_session_memory_for_tests()
    ss.patch_session_case_binding(sid, active_case_id=None, reuse_session_row=None)
    raw = sr.get_session(sid)
    assert raw is not None
    raw["asserted_org_id"] = "org-west"
    sr.upsert_session(sid, raw)
    reuse = sr.get_session(sid)
    ss.save_session_binding_after_case_created(
        sid,
        "case_new_1",
        "vin:TEST123",
        reuse_session_row=reuse,
        asserted_org_id="org-west",
    )
    got = ss.get_in_progress_session(sid)
    assert got is not None
    assert got.get("asserted_org_id") == "org-west"
    assert got.get("active_case_id") == "case_new_1"
