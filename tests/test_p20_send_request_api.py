"""API route tests for Capability 3A SendRequest."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    ADMIN_LIFECYCLE_DRAFT,
    IntakeAggregate,
    RequestDraft,
)
from services.fiqa_api.inbox_triage.p20_send_request_command_service import (
    InMemorySendRequestStore,
    P20SendRequestCommandService,
)
from services.fiqa_api.routes import inbox_triage as routes
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _case() -> dict:
    return {
        "case_id": "case_api_3a",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-15T10:00:00Z",
        "client_id": "tenant_demo",
        "asserted_org_id": "office_demo",
        "workbench_test": True,
    }


def _build_client(monkeypatch, svc: P20SendRequestCommandService) -> TestClient:
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(routes, "default_send_request_service", lambda: svc)
    monkeypatch.setattr(routes, "get_case_for_read", lambda case_id: _case() if case_id == "case_api_3a" else None)
    monkeypatch.setattr(routes, "assert_case_office_access_allowed", lambda *_a, **_k: None)
    monkeypatch.setattr(routes, "assert_case_client_access_allowed", lambda *_a, **_k: None)
    monkeypatch.setattr(routes, "_broker_actor_identity", lambda _req: "office:demo")
    monkeypatch.setattr(routes, "client_asserted_office_id", lambda _req: "office_demo")
    monkeypatch.setattr(routes, "resolve_server_client_id", lambda: "tenant_demo")
    return TestClient(app)


def _svc_ready() -> P20SendRequestCommandService:
    store = InMemorySendRequestStore(
        cases={"case_api_3a": _case()},
        intake_aggregates={
            "case_api_3a": IntakeAggregate(
                case_id="case_api_3a",
                admin_lifecycle=ADMIN_LIFECYCLE_DRAFT,
                aggregate_version=1,
                is_test=True,
                office_id="office_demo",
                tenant_id="tenant_demo",
                fact_records={},
                created_at="2026-07-15T09:00:00Z",
                updated_at="2026-07-15T09:30:00Z",
            )
        },
        drafts={
            "case_api_3a": RequestDraft(
                draft_id="draft_api",
                case_id="case_api_3a",
                draft_version=1,
                items=[
                    {
                        "draft_item_id": "di_1",
                        "field_key": "vin",
                        "item_type": "vin",
                        "label": "VIN",
                        "instructions": "Please provide VIN",
                        "required": True,
                        "position": 1,
                        "selected": True,
                    }
                ],
                content_hash="h",
                updated_by="office:demo",
                created_at="2026-07-15T09:30:00Z",
                updated_at="2026-07-15T09:30:00Z",
                status="draft",
            )
        },
    )
    return P20SendRequestCommandService(store)


def test_send_request_route_accepted(monkeypatch):
    svc = _svc_ready()
    client = _build_client(monkeypatch, svc)
    resp = client.post(
        "/api/inbox/cases/case_api_3a/send-request",
        json={
            "command_id": "cmd_api_send_0001",
            "idempotency_key": "idem_api_send_0001",
            "expected_case_version": 1,
            "request_draft_id": "draft_api",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["outcome"] == "accepted"
    assert body["customer_access"]["access_ready"] is True
    assert body["customer_access"]["copy_link"]


def test_send_request_route_replay(monkeypatch):
    svc = _svc_ready()
    client = _build_client(monkeypatch, svc)
    payload = {
        "command_id": "cmd_api_send_0001",
        "idempotency_key": "idem_api_send_0001",
        "expected_case_version": 1,
        "request_draft_id": "draft_api",
    }
    assert client.post("/api/inbox/cases/case_api_3a/send-request", json=payload).status_code == 201
    resp = client.post("/api/inbox/cases/case_api_3a/send-request", json=payload)
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "replayed"


def test_send_request_route_conflict(monkeypatch):
    svc = _svc_ready()
    client = _build_client(monkeypatch, svc)
    resp = client.post(
        "/api/inbox/cases/case_api_3a/send-request",
        json={
            "command_id": "cmd_api_send_stale",
            "idempotency_key": "idem_api_send_stale",
            "expected_case_version": 0,
            "request_draft_id": "draft_api",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error_code"] == "version_conflict"


def test_send_request_route_unauthorized_without_broker(monkeypatch):
    svc = _svc_ready()
    client = _build_client(monkeypatch, svc)

    def _deny(_req):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="broker_actor_identity_required")

    monkeypatch.setattr(routes, "_broker_actor_identity", _deny)
    resp = client.post(
        "/api/inbox/cases/case_api_3a/send-request",
        json={
            "command_id": "cmd_api_send_auth",
            "idempotency_key": "idem_api_send_auth",
            "expected_case_version": 1,
            "request_draft_id": "draft_api",
        },
    )
    assert resp.status_code == 403
