"""P35.2 — Founder QA Console BFF: auth, identity prefs, presets, no support key leak."""

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
from services.fiqa_api.routes import founder_qa_console as console_routes


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    reset_mp_active_case_index_for_tests()
    hx.reset_audit_events_for_tests()
    hx.reset_identity_prefs_for_tests()
    monkeypatch.setenv("ENABLE_P35_MP_QA_HARNESS", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_QA_FIXTURE_SURFACE", "1")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    monkeypatch.setenv("WECHAT_MP_ALLOW_SIMULATE", "1")
    yield
    reset_mp_active_case_index_for_tests()
    hx.reset_audit_events_for_tests()
    hx.reset_identity_prefs_for_tests()


def _person() -> str:
    return opaque_person_link_key("p35-console-openid")


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(console_routes.router)
    return TestClient(app)


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
        lambda: "tenant_p35c",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_customer_start_claim_office_id",
        lambda: "office_p35c",
    )
    return store


def test_status_without_identity_disables_mutations():
    c = _client()
    r = c.get("/api/internal/founder-qa/status")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["enabled"] is True
    assert body["selected_identity"] is None
    assert body["mutations_allowed"] is False
    assert "support_key" not in str(body).lower() or body.get("support_key_configured") is False


def test_rejects_support_key_header_from_browser():
    c = _client()
    r = c.get(
        "/api/internal/founder-qa/status",
        headers={"X-Unified-Intake-Support-Key": "should-not-be-accepted"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "support_key_not_accepted_on_console"


def test_intake_key_required_when_configured(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_INTAKE_API_KEY", "intake-key-value-32chars-minimum!!")
    c = _client()
    denied = c.get("/api/internal/founder-qa/status")
    assert denied.status_code == 401
    ok = c.get(
        "/api/internal/founder-qa/status",
        headers={"X-Unified-Intake-Api-Key": "intake-key-value-32chars-minimum!!"},
    )
    assert ok.status_code == 200


def test_identity_preference_user_and_env_scoped(monkeypatch):
    person = _person()
    c = _client()
    r = c.post(
        "/api/internal/founder-qa/identity",
        json={"session_id": person, "label": "DevTools A"},
    )
    assert r.status_code == 200
    assert r.json()["selected_identity"]["session_id"] == person

    status = c.get("/api/internal/founder-qa/status").json()
    assert status["selected_identity"]["session_id"] == person
    assert status["mutations_allowed"] is True

    # Different actor does not see the preference.
    other = c.get(
        "/api/internal/founder-qa/status",
        headers={"X-Founder-Qa-Actor": "other-operator"},
    ).json()
    assert other["selected_identity"] is None

    forgotten = c.delete("/api/internal/founder-qa/identity")
    assert forgotten.status_code == 200
    assert forgotten.json()["forgotten"] is True
    assert c.get("/api/internal/founder-qa/status").json()["selected_identity"] is None


def test_rejects_non_wx_and_wildcard_identity():
    c = _client()
    bad = c.post("/api/internal/founder-qa/identity", json={"session_id": "anon-local-12345"})
    assert bad.status_code == 400
    wild = c.post("/api/internal/founder-qa/identity", json={"session_id": "wx_abcdef*zzz"})
    assert wild.status_code == 400


def test_preset_requires_selected_identity_and_typed_confirm(monkeypatch):
    _wire_intake(monkeypatch)
    person = _person()
    c = _client()

    missing = c.post("/api/internal/founder-qa/presets/fresh", json={"confirm": "FRESH"})
    assert missing.status_code == 400
    assert missing.json()["detail"] == "selected_identity_required"

    c.post("/api/internal/founder-qa/identity", json={"session_id": person})
    wrong = c.post("/api/internal/founder-qa/presets/fresh", json={"confirm": "YES"})
    assert wrong.status_code == 400
    assert wrong.json()["detail"] == "confirm_fresh_required"

    ok = c.post("/api/internal/founder-qa/presets/fresh", json={"confirm": "FRESH"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["ok"] is True
    assert body["preset"] == "fresh"
    assert "resume_token" not in (body.get("result") or {})
    assert lookup_bound_case_id(person) is None


def test_active_and_request_more_via_console(monkeypatch):
    store = _wire_intake(monkeypatch)
    person = _person()
    c = _client()
    c.post("/api/internal/founder-qa/identity", json={"session_id": person})

    active = c.post("/api/internal/founder-qa/presets/active", json={"confirm": "ACTIVE"})
    assert active.status_code == 200
    result = active.json()["result"]
    assert result["has_active_case"] is True
    assert result.get("case_id")
    assert "resume_token" not in result
    assert result.get("resume_token_masked")
    assert lookup_bound_case_id(person) == result["case_id"]

    # Second active: new harness case, still exactly one binding.
    active2 = c.post("/api/internal/founder-qa/presets/active", json={"confirm": "ACTIVE"})
    assert active2.status_code == 200
    assert lookup_bound_case_id(person) == active2.json()["result"]["case_id"]

    class _FakeSlice1:
        def accept_request_more(self, **kwargs):
            assert kwargs["requested_items"][0]["item_type"] == "vin"
            case_id = kwargs["case_id"]
            case = store.cases[case_id]
            case["p20_slice1"] = {
                "open_request": {
                    "active_item": {
                        "request_item_id": "item_vin",
                        "item_type": "vin",
                        "label": "补充车架号（VIN）",
                        "status": "open",
                    }
                }
            }
            return {"outcome": "accepted"}

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_slice1_command_service.default_slice1_service",
        lambda: _FakeSlice1(),
    )

    rm = c.post("/api/internal/founder-qa/presets/request-more", json={"confirm": "REQUEST_MORE"})
    assert rm.status_code == 200
    assert rm.json()["result"]["requested_item_type"] == "vin"
    status = rm.json()["status"]
    assert status["active_case"]["has_active_case"] is True


def test_disabled_harness_rejects_mutations(monkeypatch):
    monkeypatch.delenv("ENABLE_P35_MP_QA_HARNESS", raising=False)
    person = _person()
    c = _client()
    # Identity select may still work for prep; mutations must fail.
    c.post("/api/internal/founder-qa/identity", json={"session_id": person})
    denied = c.post("/api/internal/founder-qa/presets/fresh", json={"confirm": "FRESH"})
    assert denied.status_code == 403


def test_production_like_without_support_key_rejects(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_INTAKE_API_KEY", "intake-key-value-32chars-minimum!!")
    person = _person()
    c = _client()
    headers = {"X-Unified-Intake-Api-Key": "intake-key-value-32chars-minimum!!"}
    c.post("/api/internal/founder-qa/identity", json={"session_id": person}, headers=headers)
    denied = c.post(
        "/api/internal/founder-qa/presets/fresh",
        json={"confirm": "FRESH"},
        headers=headers,
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "p35_mp_qa_support_key_required"


def test_unrelated_identity_not_affected(monkeypatch):
    _wire_intake(monkeypatch)
    a = opaque_person_link_key("console-a")
    b = opaque_person_link_key("console-b")
    bind_active_case(b, "case_unrelated_keep")
    c = _client()
    c.post("/api/internal/founder-qa/identity", json={"session_id": a})
    c.post("/api/internal/founder-qa/presets/fresh", json={"confirm": "FRESH"})
    assert lookup_bound_case_id(b) == "case_unrelated_keep"


def test_console_status_normalized_shape():
    person = _person()
    hx.set_selected_identity(session_id=person, actor="founder", label="T")
    body = hx.console_status(actor="founder", authorized=True)
    assert body["environment"]
    assert "enabled" in body
    assert "authorized" in body
    assert body["selected_identity"]["session_id"] == person
    assert "active_case" in body
    assert "resume_binding" in body
    assert "open_request_more" in body
    assert "latest_qa_preset" in body
    assert "latest_qa_audit_event" in body


def test_cloud_qa_status_production_like_false(monkeypatch):
    """fiqa-api-qa / ENV=qa must not brand as Production even with PG-primary writes."""
    monkeypatch.setenv("ENV", "qa")
    monkeypatch.setenv("SERVICE_NAME", "fiqa-api-qa")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "support-key-value-32chars-minimum!!")
    body = hx.console_status(actor="founder", authorized=True)
    assert body["environment"] == "qa"
    assert body["production_like"] is False
    assert body["require_support_key"] is True  # still gated by is_production_mode
    assert body["production_safety"] == "qa_reset_enabled"


def test_production_env_status_production_like_true(monkeypatch):
    """ENV=prod preserves Production branding (support key still required for mutations)."""
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("SERVICE_NAME", "fiqa-api")
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "support-key-value-32chars-minimum!!")
    monkeypatch.setenv("UNIFIED_INTAKE_INTAKE_API_KEY", "intake-key-value-32chars-minimum!!")
    body = hx.console_status(actor="founder", authorized=True)
    assert body["production_like"] is True
    assert body["require_support_key"] is True


def test_ambiguous_env_status_not_silently_production(monkeypatch):
    """Missing/invalid ENV must not silently classify as Production."""
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("SERVICE_NAME", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    body = hx.console_status(actor="founder", authorized=True)
    assert body["production_like"] is False
    assert body["require_support_key"] is True
