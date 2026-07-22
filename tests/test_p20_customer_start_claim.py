"""P20 Customer Start Claim — thin facade over Cap2 CreateClaim."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    ADMIN_LIFECYCLE_ACTIVE,
    EVENT_CASE_CREATED,
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_customer_start_claim import (
    customer_start_claim_response,
    normalize_customer_actor_identity,
    start_customer_claim,
)
from services.fiqa_api.inbox_triage.p20_missing_information import FACT_STATUS_MISSING
from services.fiqa_api.routes import h5_task_intake as h5_routes


def test_normalize_customer_actor_identity():
    assert normalize_customer_actor_identity("anon-abc") == "customer:mp:anon-abc"
    assert normalize_customer_actor_identity("") == "customer:mp:anonymous"
    assert normalize_customer_actor_identity("bad id!!") == "customer:mp:badid"


def test_customer_start_claim_reuses_create_claim_and_workbench_projection(monkeypatch):
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
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

    result = start_customer_claim(
        command_id="cmd-customer-create-1",
        idempotency_key="idem-customer-create-1",
        session_id="anon-test-1",
        accident_description="等红灯被追尾",
        is_test=True,
    )
    assert result["outcome"] == "accepted"
    case_id = result["case_id"]
    case = store.cases[case_id]
    # P26G: customer-originated claim is active + collecting (resume issued).
    assert case["admin_lifecycle"] == ADMIN_LIFECYCLE_ACTIVE
    assert case["created_by_actor"] == "customer"
    assert result.get("resume_token")
    assert case["workbench_test"] is True
    assert case["known_facts"]["accident_description"] == "等红灯被追尾"
    assert case["asserted_org_id"] == "office_demo"
    assert case["client_id"] == "tenant_demo"
    projection = result["broker_projection"]
    assert projection["admin_lifecycle"] == ADMIN_LIFECYCLE_ACTIVE
    assert projection["customer_projection"]["customer_next_action"] is None
    vin = next(i for i in projection["missing_information_checklist"] if i["field_key"] == "vin")
    assert vin["status"] == FACT_STATUS_MISSING
    created = next(e for e in store.events[case_id] if e["event_type"] == EVENT_CASE_CREATED)
    assert created["actor"] == "customer"
    assert created["actor_identity"] == "customer:mp:anon-test-1"
    assert created["evidence"]["channel"] == "mini_program"


def test_customer_start_claim_duplicate_replays():
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)

    # Direct Cap2 path with customer actor — same command service as facade.
    first = svc.create_claim(
        broker_id="customer:mp:anon-dup",
        office_id="office_demo",
        tenant_id="tenant_demo",
        command_id="cmd-customer-dup",
        idempotency_key="idem-customer-dup",
        actor="customer",
        inputs={"is_test": True},
    )
    second = svc.create_claim(
        broker_id="customer:mp:anon-dup",
        office_id="office_demo",
        tenant_id="tenant_demo",
        command_id="cmd-customer-dup",
        idempotency_key="idem-customer-dup",
        actor="customer",
        inputs={"is_test": True},
    )
    assert first["outcome"] == "accepted"
    assert second["outcome"] == "replayed"
    assert second["case_id"] == first["case_id"]
    assert len(store.cases) == 1


def test_customer_safe_response_hides_internals():
    raw = {
        "outcome": "accepted",
        "case_id": "case_secret",
        "command_id": "cmd_secret",
        "aggregate_version": 2,
        "broker_projection": {"admin_lifecycle": "draft"},
        "resume_token": "h5t1.opaque-resume",
        "resume_expires_at": "2026-07-25T00:00:00Z",
    }
    safe = customer_start_claim_response(raw)
    assert safe == {
        "ok": True,
        "outcome": "accepted",
        "resume_token": "h5t1.opaque-resume",
        "resume_expires_at": "2026-07-25T00:00:00Z",
    }
    assert "case_id" not in safe
    assert "command_id" not in safe
    assert "aggregate_version" not in safe


def test_customer_start_claim_api_accept_and_replay(monkeypatch):
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
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

    app = FastAPI()
    app.include_router(h5_routes.router)
    client = TestClient(app)
    body = {
        "command_id": "cmd-api-customer-1",
        "idempotency_key": "idem-api-customer-1",
        "session_id": "anon-api",
        "accident_description": "路口刮蹭",
        "is_test": True,
    }
    first = client.post("/api/h5/customer/start-claim", json=body)
    assert first.status_code == 201
    first_body = first.json()
    assert first_body["ok"] is True
    assert first_body["outcome"] == "accepted"
    assert first_body.get("resume_token")
    assert "case_id" not in first_body

    second = client.post("/api/h5/customer/start-claim", json=body)
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["ok"] is True
    # Cap2 idempotent replay or One Active Case resume — never a second case.
    assert second_body["outcome"] in ("replayed", "resumed")
    assert second_body.get("resume_token")
    assert len(store.cases) == 1
    case = next(iter(store.cases.values()))
    assert case["admin_lifecycle"] == ADMIN_LIFECYCLE_ACTIVE
    assert case["created_by_actor"] == "customer"
