from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import services.fiqa_api.routes.h5_task_intake as h5_routes
import services.fiqa_api.routes.inbox_triage as inbox_routes
from services.fiqa_api.inbox_triage.h5_task_token import VerifiedH5TaskToken
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    InMemorySlice1Store,
    P20Slice1CommandService,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _case(*, enabled: bool = True, case_id: str = "case_slice1_api") -> dict:
    row = {
        "case_id": case_id,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-15T10:00:00Z",
    }
    if enabled:
        row["slice1_capability_version"] = 1
    return row


def _client(monkeypatch: pytest.MonkeyPatch, *, case: dict | None = None) -> tuple[TestClient, InMemorySlice1Store]:
    row = case or _case()
    store = InMemorySlice1Store({row["case_id"]: row})
    svc = P20Slice1CommandService(store)
    monkeypatch.setattr(inbox_routes, "default_slice1_service", lambda: svc)
    monkeypatch.setattr(inbox_routes, "get_case_for_read", lambda case_id: store.cases.get(case_id))
    monkeypatch.setattr(inbox_routes, "assert_case_office_access_allowed", lambda _request, _row: None)
    monkeypatch.setattr(inbox_routes, "client_asserted_office_id", lambda _request: "demo-office")
    app = FastAPI()
    app.include_router(inbox_routes.router)
    return TestClient(app), store


def _h5_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    case: dict | None = None,
) -> tuple[TestClient, InMemorySlice1Store]:
    row = case or _case(case_id="case_slice1_h5")
    store = InMemorySlice1Store({row["case_id"]: row})
    svc = P20Slice1CommandService(store)
    claims = VerifiedH5TaskToken(
        case_id=row["case_id"],
        lane="claim",
        user_ref="demo_user",
        nonce="nonce_demo",
        iat=1,
        exp=9_999_999_999,
        version=3,
        flow="claim_intake_form",
    )
    monkeypatch.setattr(h5_routes, "default_slice1_service", lambda: svc)
    monkeypatch.setattr(h5_routes, "verify_h5_task_token", lambda _token: claims)
    app = FastAPI()
    app.include_router(h5_routes.router)
    return TestClient(app), store, svc


def _payload(*, command_id: str = "cmd-api-create-0001", idempotency_key: str = "idem-api-create-0001") -> dict:
    return {
        "command_id": command_id,
        "idempotency_key": idempotency_key,
        "expected_case_version": 0,
        "reason": "Please provide the requested claim information.",
        "requested_items": [
            {
                "request_item_id": "api_item_1",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Please provide VIN.",
                "required": True,
                "position": 1,
            }
        ],
    }


def test_create_request_more_route_returns_authoritative_projection(monkeypatch: pytest.MonkeyPatch):
    client, _store = _client(monkeypatch)

    response = client.post("/api/inbox/cases/case_slice1_api/request-more", json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == "accepted"
    assert body["aggregate_version"] == 1
    assert body["broker_projection"]["workflow_state"] == "broker_more_requested"
    assert body["broker_projection"]["customer_next_action"]["request_item_id"] == "api_item_1"
    assert body["request_summary"]["active_item"]["label"] == "VIN"


def test_create_request_more_route_preserves_multiple_ordered_items(monkeypatch: pytest.MonkeyPatch):
    client, _store = _client(monkeypatch)
    payload = _payload()
    payload["requested_items"].append(
        {
            "request_item_id": "api_item_2",
            "item_type": "policy_or_insurance_card",
            "label": "Insurance card",
            "instructions": "Please upload insurance card.",
            "required": True,
            "position": 2,
        }
    )

    response = client.post("/api/inbox/cases/case_slice1_api/request-more", json=payload)

    assert response.status_code == 201
    items = response.json()["request_summary"]["items"]
    assert [item["request_item_id"] for item in items] == ["api_item_1", "api_item_2"]
    assert response.json()["request_summary"]["active_item"]["request_item_id"] == "api_item_1"
    assert response.json()["request_summary"]["queued_items"][0]["request_item_id"] == "api_item_2"


def test_create_request_more_route_replays_duplicate_command(monkeypatch: pytest.MonkeyPatch):
    client, store = _client(monkeypatch)
    payload = _payload()

    first = client.post("/api/inbox/cases/case_slice1_api/request-more", json=payload)
    replay = client.post("/api/inbox/cases/case_slice1_api/request-more", json=payload)

    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.json()["outcome"] == "replayed"
    assert replay.json()["event_ids"] == first.json()["event_ids"]
    assert len(store.events["case_slice1_api"]) == 1


def test_create_request_more_route_conflicts_on_stale_expected_version(monkeypatch: pytest.MonkeyPatch):
    client, store = _client(monkeypatch)
    payload = _payload()
    payload["expected_case_version"] = 7

    response = client.post("/api/inbox/cases/case_slice1_api/request-more", json=payload)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["outcome"] == "conflict"
    assert detail["error_code"] == "version_conflict"
    assert detail["broker_projection"]["aggregate_version"] == 0
    assert store.events.get("case_slice1_api") is None


def test_create_request_more_route_rejects_feature_disabled_case(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("P20_SLICE1_REQUEST_MORE", raising=False)
    client, _store = _client(monkeypatch, case=_case(enabled=False))

    response = client.post("/api/inbox/cases/case_slice1_api/request-more", json=_payload())

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["outcome"] == "rejected"
    assert detail["error_code"] == "slice1_not_enabled"


def test_create_request_more_route_rejects_unauthorized_office(monkeypatch: pytest.MonkeyPatch):
    client, _store = _client(monkeypatch)

    def _deny(_request, _row):
        raise HTTPException(status_code=403, detail="case_office_access_denied_v1")

    monkeypatch.setattr(inbox_routes, "assert_case_office_access_allowed", _deny)

    response = client.post("/api/inbox/cases/case_slice1_api/request-more", json=_payload())

    assert response.status_code == 403
    assert response.json()["detail"] == "case_office_access_denied_v1"


def test_create_request_more_route_requires_broker_actor_identity(monkeypatch: pytest.MonkeyPatch):
    client, _store = _client(monkeypatch)
    monkeypatch.setattr(inbox_routes, "client_asserted_office_id", lambda _request: None)
    monkeypatch.setattr(inbox_routes, "resolve_server_client_id", lambda: "")

    response = client.post("/api/inbox/cases/case_slice1_api/request-more", json=_payload())

    assert response.status_code == 403
    assert response.json()["detail"] == "broker_actor_identity_required"


def test_customer_submit_route_accepts_active_item_and_returns_review_ready(monkeypatch: pytest.MonkeyPatch):
    client, store, svc = _h5_client(monkeypatch)
    created = svc.accept_request_more(
        case_id="case_slice1_h5",
        broker_id="office:demo",
        command_id="cmd-h5-create",
        idempotency_key="idem-h5-create",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "h5_item_1",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Provide VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_h5",
    )

    response = client.post(
        "/api/h5/tasks/h5t1.demo/request-items/h5_item_1/submit",
        json={
            "command_id": "cmd-h5-submit",
            "idempotency_key": "idem-h5-submit",
            "expected_case_version": created["aggregate_version"],
            "client_draft_id": "draft-h5",
            "fact": {"field": "vin", "value": "1HGCM82633A004352"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "accepted"
    assert body["customer_projection"]["workflow_state"] == "broker_review_ready"
    assert body["broker_projection"]["broker_next_action"]["action_type"] == "review_customer_response"
    assert store.items["h5_item_1"].status == "satisfied"


def test_customer_submit_route_replays_duplicate_and_conflicts_on_stale_version(
    monkeypatch: pytest.MonkeyPatch,
):
    client, store, svc = _h5_client(monkeypatch)
    created = svc.accept_request_more(
        case_id="case_slice1_h5",
        broker_id="office:demo",
        command_id="cmd-h5-create-2",
        idempotency_key="idem-h5-create-2",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "h5_item_1",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Provide VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_h5_2",
    )
    payload = {
        "command_id": "cmd-h5-submit-2",
        "idempotency_key": "idem-h5-submit-2",
        "expected_case_version": created["aggregate_version"],
        "fact": {"field": "vin", "value": "1HGCM82633A004352"},
    }
    first = client.post("/api/h5/tasks/h5t1.demo/request-items/h5_item_1/submit", json=payload)
    replay = client.post("/api/h5/tasks/h5t1.demo/request-items/h5_item_1/submit", json=payload)
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["outcome"] == "replayed"
    assert replay.json()["event_ids"] == first.json()["event_ids"]

    conflict = client.post(
        "/api/h5/tasks/h5t1.demo/request-items/h5_item_1/submit",
        json={
            "command_id": "cmd-h5-stale",
            "idempotency_key": "idem-h5-stale",
            "expected_case_version": 0,
            "fact": {"field": "vin", "value": "1HGCM82633A004352"},
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["error_code"] == "version_conflict"
    assert len(store.events["case_slice1_h5"]) == len(
        [event for event in store.events["case_slice1_h5"]]
    )
