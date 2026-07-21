"""P29B — Lightweight identity & session foundation (not a Customer Account)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.mp_customer_identity import (
    BROKER_ENTRY_SOURCE_LABEL,
    bind_active_case,
    broker_entry_source_for_case,
    case_is_resumable_active,
    establish_mp_customer_session,
    lookup_bound_case_id,
    person_link_from_session_id,
    reset_mp_active_case_index_for_tests,
    session_id_for_person_link,
)
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_customer_start_claim import (
    customer_start_claim_response,
    start_customer_claim,
)
from services.fiqa_api.inbox_triage.wechat_binding import opaque_person_link_key
from services.fiqa_api.routes import h5_task_intake as h5_routes


@pytest.fixture(autouse=True)
def _clean_index():
    reset_mp_active_case_index_for_tests()
    yield
    reset_mp_active_case_index_for_tests()


def test_openid_never_in_session_response(monkeypatch):
    monkeypatch.setenv("WECHAT_MP_ALLOW_SIMULATE", "1")
    import asyncio

    body = asyncio.run(establish_mp_customer_session("sim:secret-openid-value"))
    assert body["ok"] is True
    assert "openid" not in body
    assert "secret-openid-value" not in str(body)
    assert body["session_id"].startswith("wx_")
    assert body["has_active_case"] is False


def test_session_id_is_opaque_person_link():
    key = opaque_person_link_key("demo-openid")
    assert session_id_for_person_link(key) == key
    assert person_link_from_session_id(key) == key
    assert person_link_from_session_id("anon-local") is None


def test_active_case_bind_and_resume(monkeypatch):
    monkeypatch.setenv("WECHAT_MP_ALLOW_SIMULATE", "1")
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

    link = opaque_person_link_key("resume-openid")
    first = start_customer_claim(
        command_id="cmd-p29b-1",
        idempotency_key="idem-p29b-1",
        session_id=link,
        accident_description="路口追尾",
        is_test=True,
    )
    assert first["outcome"] == "accepted"
    assert first.get("resume_token")
    assert lookup_bound_case_id(link) == first["case_id"]
    case = store.cases[first["case_id"]]
    assert case["entry_channel"] == "mini_program"
    assert case["person_link_key"] == link
    assert "openid" not in str(case.get("source_text") or "").lower()
    assert "WeChat Mini Program" in case["source_text"]
    assert broker_entry_source_for_case(case) == BROKER_ENTRY_SOURCE_LABEL

    # Same session without force_new → resume, no second case
    second = start_customer_claim(
        command_id="cmd-p29b-2",
        idempotency_key="idem-p29b-2",
        session_id=link,
        accident_description="另一段描述",
        is_test=True,
    )
    assert second["outcome"] == "resumed"
    assert second["case_id"] == first["case_id"]
    assert len(store.cases) == 1
    assert customer_start_claim_response(second)["ok"] is True
    assert "case_id" not in customer_start_claim_response(second)

    # P30: customer force_new must not create a second Active Case
    third = start_customer_claim(
        command_id="cmd-p29b-3",
        idempotency_key="idem-p29b-3",
        session_id=link,
        accident_description="新事故",
        is_test=True,
        force_new=True,
    )
    assert third["outcome"] == "resumed"
    assert third["case_id"] == first["case_id"]
    assert lookup_bound_case_id(link) == first["case_id"]
    assert len(store.cases) == 1


def test_customer_session_http_never_returns_openid(monkeypatch):
    monkeypatch.setenv("WECHAT_MP_ALLOW_SIMULATE", "1")
    app = FastAPI()
    app.include_router(h5_routes.router)
    client = TestClient(app)
    res = client.post("/api/h5/customer/session", json={"code": "sim:http-openid"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "openid" not in body
    assert "http-openid" not in res.text
    assert body["session_id"].startswith("wx_")


def test_session_with_active_case_returns_resume(monkeypatch):
    monkeypatch.setenv("WECHAT_MP_ALLOW_SIMULATE", "1")
    link = opaque_person_link_key("bound-openid")
    bind_active_case(link, "case_bounddemo01")
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.mp_customer_identity.issue_resume_for_case",
        lambda case_id: {
            "resume_token": "h5t1.test-resume",
            "resume_expires_at": "2099-01-01T00:00:00Z",
        },
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.mp_customer_identity._load_case",
        lambda case_id: {
            "case_id": case_id,
            "case_status": "new",
            "admin_lifecycle": "active",
        },
    )

    import asyncio

    body = asyncio.run(establish_mp_customer_session("sim:bound-openid"))
    assert body["has_active_case"] is True
    assert body["resume_token"] == "h5t1.test-resume"
    assert "openid" not in body
    assert "case_id" not in body


def test_closed_case_not_resumable():
    assert case_is_resumable_active({"case_id": "x", "case_status": "closed"}) is False
    assert case_is_resumable_active({"case_id": "x", "case_status": "new", "admin_lifecycle": "active"}) is True
