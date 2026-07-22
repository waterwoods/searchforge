"""P0 — One Active Case identity foundation (server-enforced)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.mp_customer_identity import (
    allow_prototype_anon_customer_create,
    lookup_bound_case_id,
    reset_mp_active_case_index_for_tests,
    resolve_customer_identity_key,
)
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_customer_start_claim import start_customer_claim
from services.fiqa_api.inbox_triage.wechat_binding import opaque_person_link_key
from services.fiqa_api.routes import h5_task_intake as h5_routes


@pytest.fixture(autouse=True)
def _clean_index():
    reset_mp_active_case_index_for_tests()
    yield
    reset_mp_active_case_index_for_tests()


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
        lambda: "tenant_demo",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_customer_start_claim_office_id",
        lambda: "office_demo",
    )
    return store


def test_resolve_customer_identity_key_durable_and_prototype(monkeypatch):
    link = opaque_person_link_key("id-foundation")
    assert resolve_customer_identity_key(link) == link
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_deployment",
        lambda: False,
    )
    assert resolve_customer_identity_key("anon-device-1").startswith("anon-")
    assert resolve_customer_identity_key("p26h-run-a") == "p26h-run-a"
    assert resolve_customer_identity_key("random-sess") is None
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_deployment",
        lambda: True,
    )
    assert resolve_customer_identity_key("anon-device-1") is None
    assert resolve_customer_identity_key(link) == link
    assert allow_prototype_anon_customer_create() is False


def test_same_identity_ten_creates_one_active_case(monkeypatch):
    store = _wire_intake(monkeypatch)
    link = opaque_person_link_key("ten-creates")
    case_ids: list[str] = []
    for i in range(10):
        out = start_customer_claim(
            command_id=f"cmd-ten-{i}",
            idempotency_key=f"idem-ten-{i}",
            session_id=link,
            accident_description=f"事故描述 {i}",
            is_test=True,
        )
        assert out["outcome"] in ("accepted", "resumed")
        case_ids.append(out["case_id"])
    assert len(set(case_ids)) == 1
    assert len(store.cases) == 1
    assert lookup_bound_case_id(link) == case_ids[0]


def test_new_device_same_identity_resumes(monkeypatch):
    """Phone B / cleared storage: same wx_* identity resumes Active Case."""
    store = _wire_intake(monkeypatch)
    link = opaque_person_link_key("phone-a-and-b")
    first = start_customer_claim(
        command_id="cmd-phone-a",
        idempotency_key="idem-phone-a",
        session_id=link,
        accident_description="Phone A create",
        is_test=True,
    )
    assert first["outcome"] == "accepted"
    # Simulate new device: no client token; only durable identity.
    second = start_customer_claim(
        command_id="cmd-phone-b",
        idempotency_key="idem-phone-b",
        session_id=link,
        accident_description="Phone B start again",
        is_test=True,
        force_new=True,
    )
    assert second["outcome"] == "resumed"
    assert second["case_id"] == first["case_id"]
    assert len(store.cases) == 1


def test_force_new_ignored_for_customer(monkeypatch):
    store = _wire_intake(monkeypatch)
    link = opaque_person_link_key("force-new-ignored")
    first = start_customer_claim(
        command_id="cmd-fn-1",
        idempotency_key="idem-fn-1",
        session_id=link,
        accident_description="first",
        is_test=True,
    )
    second = start_customer_claim(
        command_id="cmd-fn-2",
        idempotency_key="idem-fn-2",
        session_id=link,
        accident_description="second accident",
        is_test=True,
        force_new=True,
    )
    assert first["case_id"] == second["case_id"]
    assert second["outcome"] == "resumed"
    assert len(store.cases) == 1


def test_different_identities_independent_active_cases(monkeypatch):
    store = _wire_intake(monkeypatch)
    a = opaque_person_link_key("user-a")
    b = opaque_person_link_key("user-b")
    out_a = start_customer_claim(
        command_id="cmd-a",
        idempotency_key="idem-a",
        session_id=a,
        accident_description="A",
        is_test=True,
    )
    out_b = start_customer_claim(
        command_id="cmd-b",
        idempotency_key="idem-b",
        session_id=b,
        accident_description="B",
        is_test=True,
    )
    assert out_a["outcome"] == "accepted"
    assert out_b["outcome"] == "accepted"
    assert out_a["case_id"] != out_b["case_id"]
    assert len(store.cases) == 2
    assert lookup_bound_case_id(a) == out_a["case_id"]
    assert lookup_bound_case_id(b) == out_b["case_id"]


def test_production_rejects_anon_create(monkeypatch):
    _wire_intake(monkeypatch)
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_deployment",
        lambda: True,
    )
    out = start_customer_claim(
        command_id="cmd-prod-anon",
        idempotency_key="idem-prod-anon",
        session_id="anon-should-fail",
        accident_description="prod anon",
        is_test=True,
    )
    assert out["outcome"] == "rejected"
    assert out["error_code"] == "durable_identity_required"


def test_production_accepts_durable_wx_identity(monkeypatch):
    store = _wire_intake(monkeypatch)
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_deployment",
        lambda: True,
    )
    link = opaque_person_link_key("prod-durable")
    out = start_customer_claim(
        command_id="cmd-prod-wx",
        idempotency_key="idem-prod-wx",
        session_id=link,
        accident_description="prod durable",
        is_test=True,
    )
    assert out["outcome"] == "accepted"
    assert len(store.cases) == 1


def test_prototype_anon_still_works_non_production(monkeypatch):
    store = _wire_intake(monkeypatch)
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_deployment",
        lambda: False,
    )
    first = start_customer_claim(
        command_id="cmd-anon-1",
        idempotency_key="idem-anon-1",
        session_id="anon-local-qa",
        accident_description="local anon",
        is_test=True,
    )
    second = start_customer_claim(
        command_id="cmd-anon-2",
        idempotency_key="idem-anon-2",
        session_id="anon-local-qa",
        accident_description="local anon again",
        is_test=True,
    )
    assert first["outcome"] == "accepted"
    assert second["outcome"] == "resumed"
    assert first["case_id"] == second["case_id"]
    assert len(store.cases) == 1


def test_http_start_claim_resumes_without_client_token(monkeypatch):
    store = _wire_intake(monkeypatch)
    monkeypatch.setenv("WECHAT_MP_ALLOW_SIMULATE", "1")
    app = FastAPI()
    app.include_router(h5_routes.router)
    client = TestClient(app)

    session = client.post("/api/h5/customer/session", json={"code": "sim:http-foundation"})
    assert session.status_code == 200
    sid = session.json()["session_id"]
    assert sid.startswith("wx_")

    first = client.post(
        "/api/h5/customer/start-claim",
        json={
            "command_id": "cmd-http-1",
            "idempotency_key": "idem-http-1",
            "session_id": sid,
            "accident_description": "HTTP create",
            "is_test": True,
        },
    )
    assert first.status_code == 201
    token1 = first.json()["resume_token"]

    # Cleared client storage simulation: no resume token sent; only session_id.
    second = client.post(
        "/api/h5/customer/start-claim",
        json={
            "command_id": "cmd-http-2",
            "idempotency_key": "idem-http-2",
            "session_id": sid,
            "accident_description": "HTTP create again",
            "is_test": True,
        },
    )
    assert second.status_code == 200
    assert second.json()["outcome"] == "resumed"
    assert second.json()["resume_token"]
    assert len(store.cases) == 1
    assert token1  # first create issued a token


def test_founder_qa_harness_identity_unaffected_by_production_gate(monkeypatch):
    """Non-Production + wx_* harness seed path still creates/binds."""
    store = _wire_intake(monkeypatch)
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_deployment",
        lambda: False,
    )
    link = opaque_person_link_key("founder-qa-harness")
    out = start_customer_claim(
        command_id="cmd-qa-h",
        idempotency_key="idem-qa-h",
        session_id=link,
        accident_description="QA harness",
        is_test=True,
    )
    assert out["outcome"] == "accepted"
    assert lookup_bound_case_id(link) == out["case_id"]
    assert len(store.cases) == 1
