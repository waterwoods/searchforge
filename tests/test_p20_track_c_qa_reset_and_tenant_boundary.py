"""P20 Track C — QA reset idempotency and server-derived client_id boundary."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import delete_case, get_case_by_id, save_case
from services.fiqa_api.security.case_client_access import resolve_server_client_id
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


@pytest.fixture
def client(monkeypatch):
    from services.fiqa_api.app_main import app

    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    return TestClient(app)


@pytest.fixture(autouse=True)
def _case_storage(monkeypatch, tmp_path: Path):
    path = tmp_path / "cases.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(path))
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
    monkeypatch.setenv("ENV", "test")
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    monkeypatch.setenv("CLIENT_ID", "chen_kui")
    yield


def _triage_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Collect claim facts.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def test_new_case_receives_server_derived_client_id(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "chen_kui")
    saved = save_case("claim", _triage_stub(), service_lane=SERVICE_LANE_CLAIM)
    assert saved.get("client_id") == "chen_kui"


def test_spoofed_client_id_body_cannot_change_ownership(monkeypatch):
    monkeypatch.setenv("CLIENT_ID", "chen_kui")
    saved = save_case(
        "claim",
        _triage_stub(),
        client_id="foreign_office",
        service_lane=SERVICE_LANE_CLAIM,
    )
    assert saved.get("client_id") == "chen_kui"
    assert saved.get("client_id") != "foreign_office"


def test_resolve_server_client_id_ignores_request_state():
    assert resolve_server_client_id() == "chen_kui"


def test_workbench_list_client_scoped(monkeypatch, client):
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP", "1")
    with patch("services.fiqa_api.routes.inbox_triage.list_cases_for_client_scoped_read") as m:
        m.return_value = ([{"case_id": "case_a", "client_id": "chen_kui"}], 1)
        r = client.get("/api/inbox/cases")
        assert r.status_code == 200
        m.assert_called_once()
        assert m.call_args.args[0] == "chen_kui"


def test_workbench_detail_blocks_foreign_client(monkeypatch, client):
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP", "1")
    monkeypatch.setenv("CLIENT_ID", "chen_kui")
    with patch("services.fiqa_api.routes.inbox_triage.get_case_for_read") as m:
        m.return_value = {"case_id": "case_x", "client_id": "other_tenant"}
        r = client.get("/api/inbox/cases/case_x")
        assert r.status_code == 403
        assert r.json()["detail"] == "case_client_mismatch_v1"


def test_workbench_detail_allows_matching_client(monkeypatch, client):
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP", "1")
    monkeypatch.setenv("CLIENT_ID", "chen_kui")
    with patch("services.fiqa_api.routes.inbox_triage.get_case_for_read") as m:
        m.return_value = {"case_id": "case_x", "client_id": "chen_kui"}
        r = client.get("/api/inbox/cases/case_x")
        assert r.status_code == 200


def test_spoofed_x_org_id_does_not_change_list_scope(monkeypatch, client):
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP", "1")
    monkeypatch.setenv("CLIENT_ID", "chen_kui")
    with patch("services.fiqa_api.routes.inbox_triage.list_cases_for_client_scoped_read") as m:
        m.return_value = ([], 0)
        client.get("/api/inbox/cases", headers={"X-Org-Id": "foreign_office"})
        assert m.call_args.args[0] == "chen_kui"


def test_purge_case_domain_data_idempotent():
    from services.fiqa_api.db.service_record_repository import purge_case_domain_data

    class _Cur:
        def __init__(self):
            self._counts = {
                "wecom_message_processed": 2,
                "wecom_reply_outbox": 0,
                "wecom_inbox_events": 1,
                "wecom_sync_cursors": 1,
                "intake_sessions": 1,
                "service_records": 5,
            }
            self._last_sql = ""

        def execute(self, sql, params=None):
            self._last_sql = sql

        def fetchone(self):
            return (0,)

        @property
        def rowcount(self):
            for key in self._counts:
                if key in self._last_sql:
                    return self._counts[key]
            return 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class _Conn:
        def cursor(self):
            return _Cur()

        def commit(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        return_value=_Conn(),
    ):
        first = purge_case_domain_data(dry_run=False)
        second = purge_case_domain_data(dry_run=False)
    assert first["service_records"] == 5
    assert second["service_records"] == 5


def test_local_case_store_empty_after_delete_cycle(monkeypatch, tmp_path: Path):
    saved = save_case("claim", _triage_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = str(saved["case_id"])
    assert get_case_by_id(cid) is not None
    assert delete_case(cid)
    assert get_case_by_id(cid) is None


def test_client_ownership_posture_in_support_manifest(client):
    r = client.get("/api/inbox/support/deployment-manifest")
    assert r.status_code == 200
    assert "client_ownership" in r.json()
