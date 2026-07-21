"""P20 Capability 3B — Customer VIN submit → broker review ready.

Scope: customer submit, server VIN validation, timeline append, projection
parity, broker_review_ready. Does NOT cover confirm / apply / correction.
"""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    ITEM_STATUS_SATISFIED,
    P20Slice1CommandService,
    InMemorySlice1Store,
    validate_vin_value,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _case() -> dict:
    return {
        "case_id": "case_cap3b",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-15T10:00:00Z",
        "slice1_capability_version": 1,
        "customer_name": "QA Customer",
    }


def _svc() -> tuple[P20Slice1CommandService, InMemorySlice1Store]:
    store = InMemorySlice1Store({"case_cap3b": _case()})
    return P20Slice1CommandService(store), store


def _create(svc: P20Slice1CommandService) -> dict:
    return svc.accept_request_more(
        case_id="case_cap3b",
        broker_id="office:demo",
        command_id="cmd-cap3b-create",
        idempotency_key="idem-cap3b-create",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Provide the 17-character VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_cap3b",
    )


def _submit(
    svc: P20Slice1CommandService,
    *,
    expected: int,
    vin: str = "1HGCM82633A004352",
    command_id: str = "cmd-cap3b-submit",
    idempotency_key: str = "idem-cap3b-submit",
) -> dict:
    return svc.submit_request_item(
        case_id="case_cap3b",
        customer_id="h5:cap3b",
        active_request_item_id="item_vin",
        command_id=command_id,
        idempotency_key=idempotency_key,
        expected_case_version=expected,
        client_draft_id="draft_cap3b",
        fact={"field": "vin", "value": vin},
    )


def test_validate_vin_value_accepts_17_char_charset():
    assert validate_vin_value("1hgcm82633a004352") == "1HGCM82633A004352"
    assert validate_vin_value(" 1HGCM82633A004352 ") == "1HGCM82633A004352"
    assert validate_vin_value("1HGCM82633A00435") is None  # 16
    assert validate_vin_value("1HGCM82633A004352X") is None  # 18
    assert validate_vin_value("1HGCM82633A00435I") is None  # I illegal
    assert validate_vin_value("") is None


def test_cap3b_customer_vin_submit_reaches_broker_review_ready():
    svc, store = _svc()
    created = _create(svc)
    assert created["outcome"] == "accepted"
    assert created["customer_projection"]["workflow_state"] == "broker_more_requested"

    result = _submit(svc, expected=created["aggregate_version"])
    assert result["outcome"] == "accepted"
    cust = result["customer_projection"]
    broker = result["broker_projection"]

    assert cust["workflow_state"] == "broker_review_ready"
    assert broker["workflow_state"] == "broker_review_ready"
    assert cust["aggregate_version"] == broker["aggregate_version"]
    assert cust["customer_next_action"]["action_type"] == "wait_for_broker_review"
    assert cust["customer_next_action"]["title"] == "资料已收到"
    assert "审核" in (cust["customer_next_action"]["instructions"] or "")
    assert broker["broker_next_action"]["action_type"] == "review_customer_response"
    assert broker["broker_next_action"]["status"] == "review_ready"
    assert broker["request_progress"]["satisfied"] == 1
    assert broker["request_progress"]["remaining"] == 0

    response = broker["open_request"]["items"][0]["customer_response"]
    assert response["submitted_value"] == "1HGCM82633A004352"
    assert response["submitted_by_actor"] == "customer"
    assert response["applied_to_canonical_facts"] is True
    assert response["canonical_value"] == "1HGCM82633A004352"
    assert response["customer_action_label"] == "provided VIN"
    assert store.items["item_vin"].status == ITEM_STATUS_SATISFIED
    assert store.groups["req_cap3b"].status == GROUP_STATUS_COMPLETED
    assert store.cases["case_cap3b"]["known_facts"]["vehicle_vin"] == "1HGCM82633A004352"
    assert store.cases["case_cap3b"]["known_facts"]["vin"] == "1HGCM82633A004352"


def test_cap3b_timeline_append_only_and_idempotent_retry():
    svc, store = _svc()
    created = _create(svc)
    first = _submit(svc, expected=created["aggregate_version"])
    events_after_first = list(store.events["case_cap3b"])
    event_types = [e["event_type"] for e in events_after_first]

    assert "customer_continue_started" in event_types
    assert "field_saved" in event_types
    assert "customer_request_item_satisfied" in event_types
    assert "supplement_submitted" in event_types
    assert event_types.count("field_saved") == 1
    assert event_types.count("supplement_submitted") == 1
    assert events_after_first[-1]["state_after"] == "broker_review_ready"

    field_saved = next(e for e in events_after_first if e["event_type"] == "field_saved")
    assert field_saved["evidence"]["value"] == "1HGCM82633A004352"
    assert field_saved["evidence"]["field_id"] == "vin"

    # Duplicate tap / network retry with same command identity → replay, no new events.
    second = _submit(svc, expected=created["aggregate_version"])
    assert second["outcome"] == "replayed"
    assert second["event_ids"] == first["event_ids"]
    assert len(store.events["case_cap3b"]) == len(events_after_first)
    assert second["broker_projection"]["open_request"]["items"][0]["customer_response"][
        "submitted_value"
    ] == "1HGCM82633A004352"


def test_cap3b_invalid_vin_rejected_without_timeline_mutation():
    svc, store = _svc()
    created = _create(svc)
    before = list(store.events.get("case_cap3b") or [])
    result = _submit(
        svc,
        expected=created["aggregate_version"],
        vin="SHORT",
        command_id="cmd-cap3b-bad-vin",
        idempotency_key="idem-cap3b-bad-vin",
    )
    assert result["outcome"] == "rejected"
    assert result["error_code"] == "vin_invalid"
    assert result["customer_projection"]["workflow_state"] == "broker_more_requested"
    assert store.events.get("case_cap3b") == before
    assert store.items["item_vin"].status != ITEM_STATUS_SATISFIED


def test_cap3b_projection_parity_after_fetch():
    svc, _store = _svc()
    created = _create(svc)
    submitted = _submit(svc, expected=created["aggregate_version"])
    assert submitted["outcome"] == "accepted"

    projection = svc.fetch_projection("case_cap3b")
    assert projection is not None
    assert projection["workflow_state"] == "broker_review_ready"
    assert projection["customer_next_action"]["action_type"] == "wait_for_broker_review"
    assert projection["broker_next_action"]["action_type"] == "review_customer_response"
    assert projection["open_request"]["status"] == GROUP_STATUS_COMPLETED
    assert (
        projection["open_request"]["items"][0]["customer_response"]["submitted_value"]
        == "1HGCM82633A004352"
    )
    # Customer and broker share the same projection spine in Slice 1 Cap 3B.
    assert submitted["customer_projection"]["aggregate_version"] == projection["aggregate_version"]
    assert submitted["broker_projection"]["broker_next_action"] == projection["broker_next_action"]


def test_cap3b_h5_route_submit_and_replay(monkeypatch: pytest.MonkeyPatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from services.fiqa_api.routes import h5_task_intake as h5_routes

    store = InMemorySlice1Store(
        {
            "case_slice1_h5": {
                "case_id": "case_slice1_h5",
                "service_lane": SERVICE_LANE_CLAIM,
                "claim_phase": "broker_review",
                "slice1_capability_version": 1,
            }
        }
    )
    svc = P20Slice1CommandService(store)

    class _Claims:
        case_id = "case_slice1_h5"
        user_ref = "cap3b"
        nonce = "n1"

    monkeypatch.setattr(h5_routes, "verify_h5_task_token", lambda _token: _Claims())
    monkeypatch.setattr(h5_routes, "default_slice1_service", lambda: svc)

    app = FastAPI()
    app.include_router(h5_routes.router)
    client = TestClient(app)

    created = svc.accept_request_more(
        case_id="case_slice1_h5",
        broker_id="office:demo",
        command_id="cmd-h5-cap3b-create",
        idempotency_key="idem-h5-cap3b-create",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "h5_item_vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Provide VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_h5_cap3b",
    )
    payload = {
        "command_id": "cmd-h5-cap3b-submit",
        "idempotency_key": "idem-h5-cap3b-submit",
        "expected_case_version": created["aggregate_version"],
        "client_draft_id": "draft-h5-cap3b",
        "fact": {"field": "vin", "value": "1HGCM82633A004352"},
    }
    first = client.post(
        "/api/h5/tasks/h5t1.demo/request-items/h5_item_vin/submit",
        json=payload,
    )
    assert first.status_code == 200
    body = first.json()
    assert body["outcome"] == "accepted"
    assert body["customer_projection"]["workflow_state"] == "broker_review_ready"
    assert body["broker_projection"]["broker_next_action"]["action_type"] == "review_customer_response"
    assert (
        body["broker_projection"]["open_request"]["items"][0]["customer_response"]["submitted_value"]
        == "1HGCM82633A004352"
    )

    replay = client.post(
        "/api/h5/tasks/h5t1.demo/request-items/h5_item_vin/submit",
        json=payload,
    )
    assert replay.status_code == 200
    assert replay.json()["outcome"] == "replayed"
    assert replay.json()["event_ids"] == body["event_ids"]


def test_cap3b_h5_route_rejects_invalid_vin(monkeypatch: pytest.MonkeyPatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from services.fiqa_api.routes import h5_task_intake as h5_routes

    store = InMemorySlice1Store(
        {
            "case_slice1_h5": {
                "case_id": "case_slice1_h5",
                "service_lane": SERVICE_LANE_CLAIM,
                "claim_phase": "broker_review",
                "slice1_capability_version": 1,
            }
        }
    )
    svc = P20Slice1CommandService(store)

    class _Claims:
        case_id = "case_slice1_h5"
        user_ref = "cap3b"
        nonce = "n1"

    monkeypatch.setattr(h5_routes, "verify_h5_task_token", lambda _token: _Claims())
    monkeypatch.setattr(h5_routes, "default_slice1_service", lambda: svc)

    app = FastAPI()
    app.include_router(h5_routes.router)
    client = TestClient(app)

    created = svc.accept_request_more(
        case_id="case_slice1_h5",
        broker_id="office:demo",
        command_id="cmd-h5-cap3b-create-bad",
        idempotency_key="idem-h5-cap3b-create-bad",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "h5_item_vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Provide VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_h5_cap3b_bad",
    )
    bad = client.post(
        "/api/h5/tasks/h5t1.demo/request-items/h5_item_vin/submit",
        json={
            "command_id": "cmd-h5-cap3b-bad",
            "idempotency_key": "idem-h5-cap3b-bad",
            "expected_case_version": created["aggregate_version"],
            "fact": {"field": "vin", "value": "BADVIN"},
        },
    )
    assert bad.status_code == 422
    detail = bad.json()["detail"]
    assert detail["error_code"] == "vin_invalid"
    assert detail["outcome"] == "rejected"
    assert detail["customer_projection"]["workflow_state"] == "broker_more_requested"
