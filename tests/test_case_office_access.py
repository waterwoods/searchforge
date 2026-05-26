"""Minimal office ownership enforcement (opt-in via UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_case_get_no_enforcement_legacy_open(client):
    with patch("services.fiqa_api.routes.inbox_triage.get_case_for_read") as m:
        m.return_value = {"case_id": "case_x", "asserted_org_id": "office-a"}
        r = client.get("/api/inbox/cases/case_x")
        assert r.status_code == 200


def test_case_get_enforcement_requires_matching_org(monkeypatch, client):
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP", "1")
    with patch("services.fiqa_api.routes.inbox_triage.get_case_for_read") as m:
        m.return_value = {"case_id": "case_x", "asserted_org_id": "office-a"}
        assert client.get("/api/inbox/cases/case_x").status_code == 403
        ok = client.get(
            "/api/inbox/cases/case_x",
            headers={"X-Org-Id": "office-a"},
        )
        assert ok.status_code == 200


def test_case_list_enforcement_requires_org_header(monkeypatch, client):
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP", "1")
    with patch("services.fiqa_api.routes.inbox_triage.list_cases_for_office_enforcement_read") as m:
        m.return_value = ([], 0)
        assert client.get("/api/inbox/cases").status_code == 403
        r = client.get("/api/inbox/cases", headers={"X-Org-Id": "o1"})
        assert r.status_code == 200


def test_office_ownership_posture_in_support_manifest(monkeypatch, client):
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    r = client.get("/api/inbox/support/deployment-manifest")
    assert r.status_code == 200
    assert "office_ownership" in r.json()
    assert r.json()["replay_lineage"].get("office_ownership") is not None
