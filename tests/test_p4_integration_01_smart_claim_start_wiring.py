"""P4 Integration 01 — Smart Claim Start Mini Program wiring (backend + chain)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ["P4_CUSTOMER_LOOKUP_MOCK"] = "1"

from services.fiqa_api.app_main import app  # noqa: E402
from services.fiqa_api.inbox_triage.smart_claim_start.service import (  # noqa: E402
    build_smart_claim_start_response,
    resolve_mock_scenario_person_link,
)


@pytest.fixture(autouse=True)
def _mock_on(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("P4_CUSTOMER_LOOKUP_MOCK", "1")
    monkeypatch.delenv("P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE", raising=False)


def test_resolve_mock_scenario_aliases():
    assert resolve_mock_scenario_person_link("S3").endswith("s3_no_active")
    assert resolve_mock_scenario_person_link("s1").endswith("s1_existing_active")
    assert resolve_mock_scenario_person_link("nope") is None


def test_s1_continue_active_no_duplicate_create_signal():
    res = build_smart_claim_start_response(mock_scenario="S1")
    plan = res["plan"]
    assert plan["mode"] == "CONTINUE_ACTIVE"
    assert plan["estimated_customer_inputs"] == 1
    assert "openid" not in str(res).lower()
    assert "person_link_key" not in str(res)


def test_s2_vehicle_confirm():
    plan = build_smart_claim_start_response(mock_scenario="S2")["plan"]
    assert plan["mode"] == "MATCHED_CONFIRM_VEHICLE"
    assert any(s["step_id"] == "confirm_vehicle" for s in plan["confirm_steps"])
    assert plan["estimated_customer_inputs"] >= 5


def test_s3_matched_minimal_inputs():
    plan = build_smart_claim_start_response(mock_scenario="S3")["plan"]
    assert plan["mode"] == "MATCHED_KNOWN"
    assert plan["estimated_customer_inputs"] == 4
    chip_keys = {c["field_key"] for c in plan["known_chips"]}
    assert "customer_name" in chip_keys
    assert "vehicle" in chip_keys
    # Never re-ask identity as primary accident fields
    assert "accident_story" in plan["never_ask_again"] or "customer_name" in plan["never_ask_again"]


def test_s4_stale_policy_soft_notice():
    plan = build_smart_claim_start_response(mock_scenario="S4")["plan"]
    assert plan["mode"] == "MATCHED_CONFIRM_POLICY"
    step = next(s for s in plan["confirm_steps"] if s["step_id"] == "confirm_policy")
    assert step["required_before_accident"] is False
    assert plan["estimated_customer_inputs"] == 4


def test_s5_s6_blank_degrade():
    for sc in ("S5", "S6"):
        plan = build_smart_claim_start_response(mock_scenario=sc)["plan"]
        assert plan["mode"] == "BLANK_DEGRADE"
        assert plan["known_chips"] == []
        assert plan["estimated_customer_inputs"] == 4


def test_flag_off_degrades_without_fake_prefill(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("P4_CUSTOMER_LOOKUP_MOCK", "0")
    res = build_smart_claim_start_response(mock_scenario="S3")
    assert res["lookup_enabled"] is False
    assert res["plan"]["mode"] == "BLANK_DEGRADE"
    assert res["plan"]["known_chips"] == []


def test_http_smart_claim_start_endpoint():
    client = TestClient(app)
    r = client.post(
        "/api/h5/customer/smart-claim-start",
        json={"session_id": "wx_integration_test_session", "mock_scenario": "S3"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["plan"]["mode"] == "MATCHED_KNOWN"
    blob = r.text.lower()
    assert "openid" not in blob
    assert "person_link_key" not in blob


def test_http_lookup_still_available():
    client = TestClient(app)
    r = client.post(
        "/api/h5/customer/lookup",
        json={"mock_scenario": "unused", "person_link_key": "wx_mock_cap01_s3_no_active"},
    )
    # Cap 01 body does not take mock_scenario — person_link still works.
    assert r.status_code == 200
    assert r.json()["lookup"]["match_status"] == "MATCH_FOUND"


def test_start_claim_still_reachable_empty_body_does_not_create():
    """Deployment QA Gate contract: empty start-claim must not invent a case."""
    client = TestClient(app)
    r = client.post("/api/h5/customer/start-claim", json={})
    assert r.status_code != 404
    # Validation / 422 is fine — must not be missing route.
    assert r.status_code in (401, 403, 422, 400)
