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
    clear_active_case_bindings_for_case,
    establish_mp_customer_session,
    lookup_bound_case_id,
    person_link_from_session_id,
    reset_mp_active_case_index_for_tests,
    resolve_active_case_for_person_link,
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


def test_missing_bound_case_self_heals_and_clears_binding(monkeypatch):
    link = opaque_person_link_key("ghost-openid")
    bind_active_case(link, "case_deleted_ghost_01")
    assert lookup_bound_case_id(link) == "case_deleted_ghost_01"
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.mp_customer_identity._load_case",
        lambda case_id: None,
    )
    assert resolve_active_case_for_person_link(link) is None
    assert lookup_bound_case_id(link) is None


def test_customer_session_missing_bound_case_has_no_resume(monkeypatch):
    monkeypatch.setenv("WECHAT_MP_ALLOW_SIMULATE", "1")
    link = opaque_person_link_key("session-ghost-openid")
    bind_active_case(link, "case_missing_for_session")
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.mp_customer_identity._load_case",
        lambda case_id: None,
    )
    import asyncio

    body = asyncio.run(establish_mp_customer_session("sim:session-ghost-openid"))
    assert body["ok"] is True
    assert body["has_active_case"] is False
    assert "resume_token" not in body
    assert lookup_bound_case_id(link) is None


def test_clear_bindings_for_case_removes_index_entry():
    a = opaque_person_link_key("clear-a")
    b = opaque_person_link_key("clear-b")
    bind_active_case(a, "case_shared_delete")
    bind_active_case(b, "case_other_keep")
    cleared = clear_active_case_bindings_for_case("case_shared_delete")
    assert cleared == 1
    assert lookup_bound_case_id(a) is None
    assert lookup_bound_case_id(b) == "case_other_keep"


def test_delete_case_clears_active_case_binding(monkeypatch):
    from services.fiqa_api.db import service_record_settings as settings
    from services.fiqa_api.inbox_triage import case_store as cs

    link = opaque_person_link_key("delete-bind-openid")
    cid = "case_delete_clears_bind"
    bind_active_case(link, cid)
    assert lookup_bound_case_id(link) == cid

    monkeypatch.setattr(settings, "json_case_writes_enabled", lambda: True)
    monkeypatch.setattr(settings, "db_primary_writes_enabled", lambda: False)
    monkeypatch.setattr(cs, "_read_payload", lambda: {"cases": [{"case_id": cid}]})
    writes: list[dict] = []
    monkeypatch.setattr(cs, "_write_payload", lambda payload: writes.append(payload))

    assert cs.delete_case(cid) is True
    assert writes and writes[0]["cases"] == []
    assert lookup_bound_case_id(link) is None


def test_delete_case_failure_does_not_clear_binding(monkeypatch):
    from services.fiqa_api.db import service_record_settings as settings
    from services.fiqa_api.inbox_triage import case_store as cs

    link = opaque_person_link_key("delete-fail-openid")
    cid = "case_delete_fail_keep"
    bind_active_case(link, cid)
    monkeypatch.setattr(settings, "json_case_writes_enabled", lambda: True)
    monkeypatch.setattr(settings, "db_primary_writes_enabled", lambda: False)
    monkeypatch.setattr(cs, "_read_payload", lambda: {"cases": [{"case_id": "other"}]})
    monkeypatch.setattr(cs, "_write_payload", lambda payload: None)

    assert cs.delete_case(cid) is False
    assert lookup_bound_case_id(link) == cid
