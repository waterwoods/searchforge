"""Office-scoped analytics dashboard filtering (in-memory buffer; not IAM)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.analytics.funnel_events import reset_funnel_store
from services.fiqa_api.analytics.triage_funnel import emit_funnel_from_triage_result
from services.fiqa_api.app_main import app


@pytest.fixture(autouse=True)
def _reset_buffer():
    reset_funnel_store()
    yield
    reset_funnel_store()


def _minimal_result(qrs: str = "need_more") -> dict:
    return {
        "quote_ready_status": qrs,
        "handoff_ready": True,
        "case_usable": True,
        "issue_category": "customer_question",
        "collected_fields": [],
        "still_needed_fields": ["vin"],
        "append_allowed": True,
    }


def test_dashboard_filters_by_x_org_id_header():
    emit_funnel_from_triage_result(
        _minimal_result(),
        turns=[],
        text="a",
        session_id="s-a",
        case_id="c-a",
        client_asserted_org_id="office-one",
    )
    emit_funnel_from_triage_result(
        _minimal_result(),
        turns=[],
        text="b",
        session_id="s-b",
        case_id="c-b",
        client_asserted_org_id="office-two",
    )
    c = TestClient(app)
    r = c.get("/api/analytics/dashboard", headers={"X-Org-Id": "office-one"})
    assert r.status_code == 200
    body = r.json()
    scope = body.get("dashboard_scope") or {}
    assert scope.get("client_asserted_org_id_filter") == "office-one"
    assert scope.get("events_included") == 1
    assert scope.get("events_total_unfiltered") == 2


def test_dashboard_unfiltered_without_org_header():
    emit_funnel_from_triage_result(
        _minimal_result(),
        turns=[],
        text="a",
        session_id="s-a",
        case_id="c-a",
        client_asserted_org_id="office-one",
    )
    c = TestClient(app)
    r = c.get("/api/analytics/dashboard")
    assert r.status_code == 200
    scope = r.json().get("dashboard_scope") or {}
    assert scope.get("client_asserted_org_id_filter") is None
    assert scope.get("events_included") == scope.get("events_total_unfiltered") == 1
