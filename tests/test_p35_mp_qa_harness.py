"""P35.1 — Founder MP QA reset harness security + presets."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage import p35_mp_qa_harness as hx
from services.fiqa_api.inbox_triage.mp_customer_identity import (
    bind_active_case,
    lookup_bound_case_id,
    reset_mp_active_case_index_for_tests,
)
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.wechat_binding import opaque_person_link_key
from services.fiqa_api.routes import p35_mp_qa as p35_routes


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    reset_mp_active_case_index_for_tests()
    hx.reset_audit_events_for_tests()
    monkeypatch.setenv("ENABLE_P35_MP_QA_HARNESS", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_QA_FIXTURE_SURFACE", "1")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.setenv("WECHAT_MP_ALLOW_SIMULATE", "1")
    yield
    reset_mp_active_case_index_for_tests()
    hx.reset_audit_events_for_tests()


def _person() -> str:
    return opaque_person_link_key("p35-founder-openid")


def _wire_intake(monkeypatch) -> InMemoryIntakeStore:
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
        lambda: svc,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_case_intake_command_service.default_case_intake_service",
        lambda: svc,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_server_client_id",
        lambda: "tenant_p35",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_customer_start_claim_office_id",
        lambda: "office_p35",
    )
    return store


def test_production_like_without_flags_rejects():
    import os

    os.environ.pop("ENABLE_P35_MP_QA_HARNESS", None)
    with pytest.raises(ValueError, match="p35_mp_qa_harness_disabled"):
        hx.assert_harness_allowed()


def test_production_like_requires_support_key(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    with pytest.raises(ValueError, match="p35_mp_qa_support_key_required"):
        hx.assert_harness_allowed()


def test_wildcard_identity_rejected():
    with pytest.raises(ValueError, match="wildcard_identity_forbidden"):
        hx.normalize_exact_person_link("wx_abc*")
    with pytest.raises(ValueError, match="exact_wx_session_id_required"):
        hx.normalize_exact_person_link("anon-local")


def test_fresh_is_idempotent_and_clears_binding(monkeypatch):
    person = _person()
    bind_active_case(person, "case_prior_p35")
    assert lookup_bound_case_id(person) == "case_prior_p35"

    first = hx.preset_fresh_customer(session_id=person, confirm=hx.CONFIRM_FRESH)
    assert first["ok"] is True
    assert first["has_active_case"] is False
    assert lookup_bound_case_id(person) is None

    second = hx.preset_fresh_customer(session_id=person, confirm=hx.CONFIRM_FRESH)
    assert second["ok"] is True
    assert lookup_bound_case_id(person) is None
    assert len(hx.list_audit_events()) >= 2


def test_fresh_requires_typed_confirm():
    with pytest.raises(ValueError, match="confirm_fresh_required"):
        hx.preset_fresh_customer(session_id=_person(), confirm="yes")


def test_active_seed_idempotent_one_binding(monkeypatch):
    store = _wire_intake(monkeypatch)
    person = _person()

    first = hx.preset_active_claim(session_id=person, confirm=hx.CONFIRM_ACTIVE)
    assert first["ok"] is True
    assert first["has_active_case"] is True
    assert first["resume_token"]
    cid1 = first["case_id"]
    assert lookup_bound_case_id(person) == cid1
    assert store.cases[cid1].get("demo_name") == hx.DEMO_NAME
    assert store.cases[cid1].get("workbench_test") is True

    second = hx.preset_active_claim(session_id=person, confirm=hx.CONFIRM_ACTIVE)
    assert second["ok"] is True
    cid2 = second["case_id"]
    assert lookup_bound_case_id(person) == cid2
    # Exactly one Active Case binding for this identity after re-seed.
    assert cid2
    assert lookup_bound_case_id(person) == cid2


def test_unrelated_identity_untouched(monkeypatch):
    _wire_intake(monkeypatch)
    a = opaque_person_link_key("p35-a")
    b = opaque_person_link_key("p35-b")
    hx.preset_active_claim(session_id=a, confirm=hx.CONFIRM_ACTIVE)
    bind_active_case(b, "case_other_untouched")
    hx.preset_fresh_customer(session_id=a, confirm=hx.CONFIRM_FRESH)
    assert lookup_bound_case_id(a) is None
    assert lookup_bound_case_id(b) == "case_other_untouched"


def test_request_more_seed_vin(monkeypatch):
    store = _wire_intake(monkeypatch)

    class _FakeSlice1:
        def accept_request_more(self, **kwargs):
            assert kwargs["requested_items"][0]["item_type"] == "vin"
            case_id = kwargs["case_id"]
            case = store.cases[case_id]
            case["claim_phase"] = "broker_needs_more_info"
            case["p35_request_more_vin"] = True
            return {"outcome": "accepted", "customer_projection": {"item": "vin"}}

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_slice1_command_service.default_slice1_service",
        lambda: _FakeSlice1(),
    )

    person = _person()
    out = hx.preset_request_more(session_id=person, confirm=hx.CONFIRM_REQUEST_MORE)
    assert out["ok"] is True
    assert out["requested_item_type"] == "vin"
    assert out["resume_token"]
    assert lookup_bound_case_id(person) == out["case_id"]
    assert store.cases[out["case_id"]].get("p35_request_more_vin") is True


def test_http_disabled_returns_403(monkeypatch):
    monkeypatch.delenv("ENABLE_P35_MP_QA_HARNESS", raising=False)
    app = FastAPI()
    app.include_router(p35_routes.router)
    client = TestClient(app)
    res = client.post(
        "/api/inbox/support/p35-mp-qa/presets/fresh",
        json={"session_id": _person(), "confirm": "FRESH"},
    )
    assert res.status_code == 403


def test_http_unauthorized_support_key(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "super-secret-support-key-123456")
    app = FastAPI()
    app.include_router(p35_routes.router)
    client = TestClient(app)
    res = client.post(
        "/api/inbox/support/p35-mp-qa/presets/fresh",
        json={"session_id": _person(), "confirm": "FRESH"},
    )
    assert res.status_code == 401


def test_http_fresh_with_support_key(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "super-secret-support-key-123456")
    app = FastAPI()
    app.include_router(p35_routes.router)
    client = TestClient(app)
    person = _person()
    bind_active_case(person, "case_http")
    res = client.post(
        "/api/inbox/support/p35-mp-qa/presets/fresh",
        headers={"X-Unified-Intake-Support-Key": "super-secret-support-key-123456"},
        json={"session_id": person, "confirm": "FRESH"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["has_active_case"] is False
    assert lookup_bound_case_id(person) is None
