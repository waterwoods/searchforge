"""P4 Capability 01 — Customer Lookup mock harness (read-only)."""

from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.customer_lookup import (
    FLAG_ENV,
    FORCE_UNAVAILABLE_ENV,
    lookup_customer,
    reset_customer_lookup_mock_for_tests,
)
from services.fiqa_api.inbox_triage.customer_lookup.contract import (
    LOOKUP_CONFIDENCE_VALUES,
    MATCH_STATUS_VALUES,
    assert_lookup_result_complete,
)
from services.fiqa_api.inbox_triage.customer_lookup.facade import (
    broker_header_fields_from_lookup,
    simulate_workflow_steps,
)
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    MOCK_KEY_AMBIGUOUS,
    MOCK_KEY_S1_EXISTING_ACTIVE,
    MOCK_KEY_S2_MULTI_VEHICLE,
    MOCK_KEY_S3_NO_ACTIVE,
    MOCK_KEY_S4_STALE_POLICY,
    MOCK_KEY_S5_NO_MAPPING,
    MOCK_KEY_S6_UNAVAILABLE,
    SCENARIO_KEYS,
)
from services.fiqa_api.routes import h5_task_intake as h5_routes


@pytest.fixture(autouse=True)
def _flag_on(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "1")
    monkeypatch.delenv(FORCE_UNAVAILABLE_ENV, raising=False)
    reset_customer_lookup_mock_for_tests()
    yield
    reset_customer_lookup_mock_for_tests()


def _assert_no_identity_leak(result: dict) -> None:
    blob = str(result).lower()
    assert "openid" not in blob
    assert "person_link_key" not in blob or "invalid_person_link" in str(result.get("reason_codes"))


# ---------------------------------------------------------------------------
# Contract + scenarios
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key,expected_status,expected_confidence,expected_next",
    [
        (MOCK_KEY_S1_EXISTING_ACTIVE, "MATCH_FOUND", "HIGH", "continue_active_case"),
        (MOCK_KEY_S2_MULTI_VEHICLE, "MATCH_FOUND", "MEDIUM", "confirm_vehicle"),
        (MOCK_KEY_S3_NO_ACTIVE, "MATCH_FOUND", "HIGH", "confirm_vehicle"),
        (MOCK_KEY_S4_STALE_POLICY, "STALE_POLICY", "MEDIUM", "confirm_stale_policy"),
        (MOCK_KEY_S5_NO_MAPPING, "NOT_FOUND", "LOW", "start_blank_claim"),
        (MOCK_KEY_S6_UNAVAILABLE, "LOOKUP_UNAVAILABLE", "LOW", "start_blank_claim"),
        (MOCK_KEY_AMBIGUOUS, "AMBIGUOUS_MATCH", "LOW", "contact_broker"),
    ],
)
def test_six_scenarios_plus_ambiguous(key, expected_status, expected_confidence, expected_next):
    result = lookup_customer(key)
    assert_lookup_result_complete(result)
    assert result["match_status"] == expected_status
    assert result["lookup_confidence"] == expected_confidence
    assert result["next_action"] == expected_next
    assert result["match_status"] in MATCH_STATUS_VALUES
    assert result["lookup_confidence"] in LOOKUP_CONFIDENCE_VALUES
    _assert_no_identity_leak(result)


def test_unmatched_identity_invalid_key():
    result = lookup_customer("anon-local")
    assert result["match_status"] == "UNMATCHED_IDENTITY"
    assert result["next_action"] == "relogin"
    assert_lookup_result_complete(result)


def test_flag_off_degrades_without_throw(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "0")
    result = lookup_customer(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert result["match_status"] == "LOOKUP_UNAVAILABLE"
    assert result["next_action"] == "start_blank_claim"
    assert "lookup_flag_off" in result["reason_codes"]


def test_force_unavailable(monkeypatch):
    monkeypatch.setenv(FORCE_UNAVAILABLE_ENV, "1")
    result = lookup_customer(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert result["match_status"] == "LOOKUP_UNAVAILABLE"


def test_read_only_facade_has_no_write_api():
    import services.fiqa_api.inbox_triage.customer_lookup.facade as facade

    banned = (
        "create_customer",
        "merge_customer",
        "update_customer",
        "update_policy",
        "update_vehicle",
        "write_crm",
    )
    for name in banned:
        assert not hasattr(facade, name)


def test_s1_prefill_and_active_case():
    result = lookup_customer(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert result["prefill"]["customer_name"] == "陈明"
    assert result["prefill"]["primary_vehicle_summary"] == "2020 Toyota Camry"
    assert result["active_case"]["case_id"] == "case_mock_cap01_s1"
    assert len(result["vehicles"]) == 1


def test_s2_multi_vehicle_no_auto_primary_summary():
    result = lookup_customer(MOCK_KEY_S2_MULTI_VEHICLE)
    assert len(result["vehicles"]) == 2
    assert "primary_vehicle_summary" not in result["prefill"]


def test_broker_header_projection():
    result = lookup_customer(MOCK_KEY_S1_EXISTING_ACTIVE)
    header = broker_header_fields_from_lookup(result)
    assert header["customer_display_name"] == "陈明"
    assert header["vehicle_summary"] == "2020 Toyota Camry"
    assert header["lookup_confidence"] == "HIGH"
    assert "openid" not in str(header).lower()


# ---------------------------------------------------------------------------
# End-to-end workflow simulation (narrative harness)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario_id", ["S1_existing_active", "S2_multi_vehicle", "S3_no_active", "S4_stale_policy", "S5_no_mapping", "S6_unavailable"])
def test_workflow_simulation_main_chain(scenario_id):
    key = SCENARIO_KEYS[scenario_id]
    result = lookup_customer(key)
    steps = simulate_workflow_steps(result)
    names = [s["step"] for s in steps]
    assert names == [
        "mini_program",
        "lookup",
        "broker_header",
        "workbench",
        "request_more",
        "customer_continue",
        "review",
        "close",
    ]
    assert all(s.get("ok") is True for s in steps)
    workbench = next(s for s in steps if s["step"] == "workbench")
    assert workbench.get("duplicate_customer") is False
    continue_step = next(s for s in steps if s["step"] == "customer_continue")
    assert continue_step.get("duplicate_claim") is False
    close_step = next(s for s in steps if s["step"] == "close")
    assert close_step.get("lookup_mutated_crm") is False


def test_s1_simulation_continue_not_new_claim():
    result = lookup_customer(MOCK_KEY_S1_EXISTING_ACTIVE)
    steps = simulate_workflow_steps(result)
    cont = next(s for s in steps if s["step"] == "customer_continue")
    assert cont["next_action"] == "continue_active_case"


def test_s6_graceful_degradation():
    result = lookup_customer(MOCK_KEY_S6_UNAVAILABLE)
    steps = simulate_workflow_steps(result)
    cont = next(s for s in steps if s["step"] == "customer_continue")
    assert cont.get("graceful_degradation") is True


# ---------------------------------------------------------------------------
# HTTP endpoint
# ---------------------------------------------------------------------------


def test_http_lookup_endpoint():
    app = FastAPI()
    app.include_router(h5_routes.router)
    client = TestClient(app)
    res = client.post(
        "/api/h5/customer/lookup",
        json={"person_link_key": MOCK_KEY_S3_NO_ACTIVE},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["lookup_enabled"] is True
    assert body["lookup"]["match_status"] == "MATCH_FOUND"
    assert "openid" not in res.text.lower()
    assert MOCK_KEY_S3_NO_ACTIVE not in res.text  # do not echo key in lookup body


def test_http_lookup_flag_off(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "0")
    app = FastAPI()
    app.include_router(h5_routes.router)
    client = TestClient(app)
    res = client.post(
        "/api/h5/customer/lookup",
        json={"person_link_key": MOCK_KEY_S1_EXISTING_ACTIVE},
    )
    assert res.status_code == 200
    assert res.json()["lookup"]["match_status"] == "LOOKUP_UNAVAILABLE"
    assert res.json()["lookup_enabled"] is False


def test_scenario_key_map_complete():
    for required in (
        "S1_existing_active",
        "S2_multi_vehicle",
        "S3_no_active",
        "S4_stale_policy",
        "S5_no_mapping",
        "S6_unavailable",
    ):
        assert required in SCENARIO_KEYS
