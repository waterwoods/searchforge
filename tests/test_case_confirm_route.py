"""PATCH /api/inbox/cases/{case_id}/confirm — Track B0.3 Broker Confirm (HTTP layer).

Governed by docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md §7/§9. Exercises the
route wiring on top of the bridge-level coverage in tests/test_wecom_active_case.py
(TestTrackB0BrokerConfirm) — same JSON-store test style as test_case_office_access.py.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app
from services.fiqa_api.inbox_triage.case_store import save_case, update_case_customer


@pytest.fixture
def client(monkeypatch):
    # Isolate from ambient env loaded when app_main is imported (e.g. a local
    # .env.cloudrun pointing at a real Postgres URL / setting ENV=prod / an
    # operator-key gate) so this suite exercises Broker Confirm behavior
    # against the JSON case store, not an unreachable production database.
    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_JSON_READ_FALLBACK", raising=False)
    return TestClient(app)


def _setup_json_store() -> None:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)


def _minimal_triage_stub() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Collect remaining fields.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def test_confirm_missing_case_returns_404(client) -> None:
    _setup_json_store()
    r = client.patch("/api/inbox/cases/does-not-exist/confirm")
    assert r.status_code == 404


def test_confirm_without_phone_returns_400(client) -> None:
    _setup_json_store()
    saved = save_case("[客户] WeCom: Start / 开始", _minimal_triage_stub(), status="new")
    case_id = saved["case_id"]

    r = client.patch(f"/api/inbox/cases/{case_id}/confirm")
    assert r.status_code == 400

    stored = client.get(f"/api/inbox/cases/{case_id}").json()
    assert stored.get("broker_confirmed_at") is None


def test_confirm_with_phone_sets_flag_and_is_idempotent(client) -> None:
    _setup_json_store()
    saved = save_case("[客户] WeCom: Start / 开始", _minimal_triage_stub(), status="new")
    case_id = saved["case_id"]
    update_case_customer(case_id, customer_phone="6265550101")

    first = client.patch(f"/api/inbox/cases/{case_id}/confirm")
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["broker_confirmed_at"]
    assert first_body["already_confirmed"] is False

    second = client.patch(f"/api/inbox/cases/{case_id}/confirm")
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["already_confirmed"] is True
    assert second_body["broker_confirmed_at"] == first_body["broker_confirmed_at"]

    stored = client.get(f"/api/inbox/cases/{case_id}").json()
    activity_types = [a.get("activity_type") for a in stored.get("case_activity") or []]
    assert activity_types.count("broker_confirmed") == 1


def test_broker_confirmed_at_defaults_null_on_new_case(client) -> None:
    """Additive field: every case, including ones created before B0.3 shipped
    (no broker_confirmed_at key at all in the legacy JSON), normalizes to null."""
    _setup_json_store()
    saved = save_case("[客户] hello", _minimal_triage_stub(), status="new")
    assert saved.get("broker_confirmed_at") is None

    r = client.get(f"/api/inbox/cases/{saved['case_id']}")
    assert r.status_code == 200
    assert r.json().get("broker_confirmed_at") is None
