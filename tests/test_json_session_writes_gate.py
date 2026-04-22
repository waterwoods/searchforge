"""Session JSON write gating (UNIFIED_INTAKE_JSON_SESSION_WRITES)."""

from __future__ import annotations

import json

from services.fiqa_api.inbox_triage import session_store as ss


def test_session_json_not_written_when_disabled(tmp_path, monkeypatch):
    store = tmp_path / "sessions.json"
    monkeypatch.setenv("UNIFIED_INTAKE_SESSIONS_PATH", str(store))
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_SESSION_WRITES", "0")
    # Reset module-level log guard from other tests
    ss._SESSION_WRITES_DISABLED_LOGGED = False  # noqa: SLF001

    ss.save_in_progress_session(
        "sess_gate_1",
        [{"role": "customer", "text": "hello"}],
        {"collection_stage": "x"},
    )
    assert not store.exists()


def test_session_json_written_when_enabled(tmp_path, monkeypatch):
    store = tmp_path / "sessions.json"
    monkeypatch.setenv("UNIFIED_INTAKE_SESSIONS_PATH", str(store))
    monkeypatch.delenv("UNIFIED_INTAKE_JSON_SESSION_WRITES", raising=False)

    ss.save_in_progress_session(
        "sess_gate_2",
        [{"role": "customer", "text": "hello"}],
        {"collection_stage": "x"},
    )
    assert store.exists()
    data = json.loads(store.read_text(encoding="utf-8"))
    assert any(s.get("session_id") == "sess_gate_2" for s in data.get("sessions", []))
