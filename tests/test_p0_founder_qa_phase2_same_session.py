"""P0 Founder QA UX Phase 2 — same launch token across sequential Request More.

Proves one Golden session token can read insurance-card then vehicle-information
after the first group completes, without minting a second token/QR.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.claim_vehicle_identity import ClaimVehicleIdentityService
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    InMemorySlice1Store,
    P20Slice1CommandService,
)
from services.fiqa_api.routes import h5_task_intake as h5_routes
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

CASE_ID = "case_phase2_same_session"
TOKEN = "h5t1.phase2-same-session"


def _case() -> dict:
    return {
        "case_id": CASE_ID,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-22T10:00:00Z",
        "slice1_capability_version": 1,
        "customer_name": "陈明",
        "known_facts": {"own_vehicle_info": "2020 Toyota Camry"},
        "demo_name": "camry_golden_qa",
        "workbench_test": True,
    }


def _svc() -> tuple[P20Slice1CommandService, InMemorySlice1Store]:
    vehicle = ClaimVehicleIdentityService()
    store = InMemorySlice1Store({CASE_ID: _case()})
    return P20Slice1CommandService(store, vehicle_service=vehicle), store


class _Claims:
    case_id = CASE_ID
    user_ref = "phase2"
    nonce = "phase2-nonce"
    lane = "claim"
    flow = "claim_intake_form"
    is_intake_form_token = True


def _client(svc: P20Slice1CommandService, monkeypatch) -> TestClient:
    monkeypatch.setattr(h5_routes, "verify_h5_task_token", lambda _token: _Claims())
    monkeypatch.setattr(h5_routes, "default_slice1_service", lambda: svc)

    def _load_case(case_id: str):
        assert case_id == CASE_ID
        return dict(svc.store.cases[CASE_ID])

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_intake._load_claim_case",
        _load_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_intake._slice1_projection_for_case",
        lambda _case: (svc.fetch_projection(CASE_ID) or {}, False),
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_intake.mint_h5_claim_evidence_pack_link",
        lambda **_kwargs: None,
    )

    app = FastAPI()
    app.include_router(h5_routes.router)
    return TestClient(app)


def test_same_token_discovers_two_sequential_request_more(monkeypatch):
    svc, store = _svc()
    client = _client(svc, monkeypatch)

    first = svc.accept_request_more(
        case_id=CASE_ID,
        broker_id="office:camry_golden_qa",
        command_id="cmd-phase2-insurance",
        idempotency_key="idem-phase2-insurance",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_insurance",
                "item_type": "policy_or_insurance_card",
                "label": "上传保险卡",
                "instructions": "请上传清晰的保险卡照片",
                "required": True,
                "position": 1,
            }
        ],
        reason="Camry Golden QA initial state",
        request_id="req_phase2_1",
    )
    assert first["outcome"] == "accepted"

    # One launch token — first current-task read.
    intake1 = client.get(f"/api/h5/tasks/{TOKEN}/intake")
    assert intake1.status_code == 200
    body1 = intake1.json()
    assert body1["case_id"] == CASE_ID
    next1 = body1["slice1_projection"]["customer_next_action"]
    assert next1["required_input"] == "policy_or_insurance_card"
    assert next1["title"] == "上传保险卡"

    submitted = svc.submit_request_item(
        case_id=CASE_ID,
        customer_id="h5:phase2",
        active_request_item_id="item_insurance",
        command_id="cmd-phase2-submit-insurance",
        idempotency_key="idem-phase2-submit-insurance",
        expected_case_version=first["aggregate_version"],
        client_draft_id="draft-phase2-insurance",
        evidence={"attachment_id": "att_insurance_phase2"},
    )
    assert submitted["outcome"] == "accepted"
    assert submitted["customer_projection"]["workflow_state"] == "broker_review_ready"
    assert store.groups["req_phase2_1"].status == GROUP_STATUS_COMPLETED

    # Same case receives a later supported Request More — no new token.
    second = svc.accept_request_more(
        case_id=CASE_ID,
        broker_id="office:camry_golden_qa",
        command_id="cmd-phase2-vehicle",
        idempotency_key="idem-phase2-vehicle",
        expected_case_version=submitted["aggregate_version"],
        requested_items=[
            {
                "request_item_id": "item_vehicle",
                "item_type": "vehicle_information",
                "label": "车辆信息",
                "instructions": "请补充本次事故车辆的基本信息",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need vehicle information",
        request_id="req_phase2_2",
    )
    assert second["outcome"] == "accepted", second

    # Foreground refresh equivalent: same token, new current task.
    intake2 = client.get(f"/api/h5/tasks/{TOKEN}/intake")
    assert intake2.status_code == 200
    body2 = intake2.json()
    assert body2["case_id"] == CASE_ID
    next2 = body2["slice1_projection"]["customer_next_action"]
    assert next2["required_input"] == "vehicle_information"
    assert next2["title"] == "车辆信息"
    assert next2["request_id"] == "req_phase2_2"

    # Token path unchanged — no second mint/QR required for task 2.
    assert intake1.request.url.path == intake2.request.url.path
    assert TOKEN in str(intake1.request.url)
    assert TOKEN in str(intake2.request.url)


def test_expired_token_fails_closed_without_repair(monkeypatch):
    svc, _store = _svc()
    client = _client(svc, monkeypatch)
    monkeypatch.setattr(h5_routes, "verify_h5_task_token", lambda _token: None)

    resp = client.get(f"/api/h5/tasks/{TOKEN}/intake")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "invalid_or_expired_task_link"
