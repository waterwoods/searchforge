"""P26G — Default intake tasks + persistent customer resume (flow contract).

Three permanent flow gates:
1. First-Time Customer Gate — new claim, zero broker requests → default tasks
2. Return-Later Gate — resume token restores the same case
3. Exceptional Follow-Up Gate — broker request adds without wiping defaults
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.constitution_projection import (
    TASK_ID_INSURANCE,
    TASK_ID_PHOTOS,
    TASK_ID_STORY,
    TASK_STATE_BLOCKED,
    TASK_STATE_COMPLETED,
    TASK_STATE_PENDING,
    ConstitutionInputs,
    build_constitution_projection,
)
from services.fiqa_api.inbox_triage.default_intake_plan import (
    TASK_SOURCE_BROKER_REQUESTED,
    TASK_SOURCE_SYSTEM_DEFAULT,
    default_intake_plan_for_case,
)
from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    ADMIN_LIFECYCLE_ACTIVE,
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_customer_start_claim import (
    customer_start_claim_response,
    start_customer_claim,
)
from services.fiqa_api.routes import h5_task_intake as h5_routes
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)


def _by_id(tasks: list[dict]) -> dict[str, dict]:
    return {str(t["task_id"]): t for t in tasks}


def _fresh_claim_case(**overrides) -> dict:
    case = {
        "case_id": "case-p26g-fresh",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "known_facts": {
            "accident_description": "倒车刮蹭",
            "accident_datetime": "2026-07-18 10:00",
            "accident_location": "停车场",
            "injury_status": "no",
        },
        "p20_slice1_projection": {
            "case_id": "case-p26g-fresh",
            "workflow_state": "intake",
            "customer_next_action": None,
            "broker_next_action": {"action_type": "none", "status": "none"},
            "open_request": None,
        },
        "claim_evidence_summary": {"received_slots": [], "missing_required_slots": []},
        "case_attachments": [],
        "claim_attachment_slots": {},
    }
    case.update(overrides)
    return case


# --- Gate 1: First-Time Customer Gate (Constitution) ---


def test_gate1_new_claim_zero_broker_requests_has_default_tasks():
    plan_ids = {row["task_id"] for row in default_intake_plan_for_case({})}
    projection = build_constitution_projection(ConstitutionInputs(case=_fresh_claim_case()))
    customer = projection["customer"]
    by_id = _by_id(customer["tasks"])

    assert TASK_ID_STORY in by_id
    assert TASK_ID_PHOTOS in by_id
    assert TASK_ID_INSURANCE in by_id
    assert plan_ids <= set(by_id)

    # Must not wait on broker when defaults remain.
    assert customer["today"] != "先不用操作"
    assert customer["current_stage"] == "customer_action_needed"

    insurance = by_id[TASK_ID_INSURANCE]
    assert insurance["task_source"] == TASK_SOURCE_SYSTEM_DEFAULT
    assert insurance["actionable"] is True
    assert insurance["route"] == "insurance"
    assert insurance["action"]["route"] == "insurance"
    assert "request_item_id" not in insurance["action"]
    assert insurance["state"] in {TASK_STATE_PENDING, "in_progress"}
    assert insurance["is_today"] is True
    assert customer["today"] == "上传保险卡"

    photos = by_id[TASK_ID_PHOTOS]
    assert photos["task_source"] == TASK_SOURCE_SYSTEM_DEFAULT
    # Today First: defer behind insurance Focus — blocked, never fake-completed.
    assert photos["state"] == TASK_STATE_BLOCKED
    assert photos["actionable"] is False
    assert photos["progress"]["completed"] == 0

    story = by_id[TASK_ID_STORY]
    assert story["task_source"] == TASK_SOURCE_SYSTEM_DEFAULT
    # Story completed only because this case has accident_description (Start Claim).
    assert story["state"] == TASK_STATE_COMPLETED


def test_gate1_completed_story_does_not_require_broker():
    case = _fresh_claim_case()
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    by_id = _by_id(projection["customer"]["tasks"])
    assert by_id[TASK_ID_STORY]["state"] == TASK_STATE_COMPLETED
    assert by_id[TASK_ID_INSURANCE]["actionable"] is True


def test_gate1_early_broker_review_phase_does_not_hide_defaults():
    case = _fresh_claim_case(claim_phase="broker_review")
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    customer = projection["customer"]
    assert customer["today"] != "先不用操作"
    assert customer["current_stage"] == "customer_action_needed"
    by_id = _by_id(customer["tasks"])
    assert by_id[TASK_ID_INSURANCE]["actionable"] is True


# --- Gate 3: Exceptional Follow-Up Gate ---


def test_gate3_broker_followup_adds_without_wiping_defaults():
    case = _fresh_claim_case(
        p20_slice1_projection={
            "case_id": "case-p26g-fresh",
            "workflow_state": "broker_more_requested",
            "customer_next_action": {
                "action_type": "provide_evidence",
                "title": "上传保险卡",
                "required_input": "policy_or_insurance_card",
                "status": "active",
                "instructions": "请补一张更清晰的保险卡",
            },
            "broker_next_action": {
                "action_type": "wait_for_customer_item",
                "status": "waiting_for_customer",
            },
            "open_request": {
                "status": "open",
                "active_item": {
                    "item_type": "policy_or_insurance_card",
                    "label": "上传保险卡",
                    "status": "active",
                },
                "queued_items": [
                    {
                        "item_type": "driver_license",
                        "label": "驾驶证",
                        "status": "queued",
                    }
                ],
            },
        }
    )
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    by_id = _by_id(projection["customer"]["tasks"])

    assert TASK_ID_STORY in by_id
    assert TASK_ID_PHOTOS in by_id
    assert TASK_ID_INSURANCE in by_id
    assert by_id[TASK_ID_INSURANCE]["task_source"] == TASK_SOURCE_BROKER_REQUESTED
    assert by_id[TASK_ID_INSURANCE]["reason"]
    assert by_id[TASK_ID_INSURANCE]["route"] == "request_item"
    assert by_id[TASK_ID_INSURANCE]["action"]["route"] == "request_item"
    # Defaults remain present (photos still a card).
    assert by_id[TASK_ID_PHOTOS]["task_source"] == TASK_SOURCE_SYSTEM_DEFAULT


def test_gate3_stale_summary_does_not_remove_default_tasks():
    case = _fresh_claim_case(
        claim_evidence_summary={
            "received_slots": ["policy_or_insurance_card"],
            "missing_required_slots": ["customer_damage_photo"],
        },
        case_attachments=[],
        claim_attachment_slots={},
    )
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    by_id = _by_id(projection["customer"]["tasks"])
    assert TASK_ID_INSURANCE in by_id
    assert TASK_ID_PHOTOS in by_id
    assert TASK_ID_STORY in by_id


def test_insurance_satisfied_from_system_default_upload_slot():
    case = _fresh_claim_case(
        claim_attachment_slots={
            "policy_or_insurance_card": {
                "status": "received",
                "attachment_ids": ["att_ins_1"],
            }
        },
        case_attachments=[
            {
                "attachment_id": "att_ins_1",
                "source": "h5_task",
                "msgtype": "image",
                "slot_assignment": "policy_or_insurance_card",
                "evidence_status": "confirmed",
            }
        ],
    )
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    by_id = _by_id(projection["customer"]["tasks"])
    assert by_id[TASK_ID_INSURANCE]["state"] == TASK_STATE_COMPLETED
    assert by_id[TASK_ID_INSURANCE]["actionable"] is False


# --- Gate 2: Return-Later / Resume ---


def test_gate2_start_claim_issues_resume_token(monkeypatch):
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
        command_id="cmd-p26g-1",
        idempotency_key="idem-p26g-1",
        session_id="anon-p26g",
        accident_description="停车场倒车碰撞",
        accident_datetime="2026-07-18",
        accident_location="停车场",
        injury_status="no",
        is_test=True,
    )
    assert result["outcome"] == "accepted"
    assert result["resume_token"]
    claims = verify_h5_task_token(result["resume_token"])
    assert claims is not None
    assert claims.case_id == result["case_id"]

    case = store.cases[result["case_id"]]
    assert case["admin_lifecycle"] == ADMIN_LIFECYCLE_ACTIVE
    assert case["claim_phase"] == CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE

    safe = customer_start_claim_response(result)
    assert safe["ok"] is True
    assert safe["resume_token"] == result["resume_token"]
    assert "case_id" not in safe


def test_gate2_start_claim_api_returns_resume_token(monkeypatch):
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
        "command_id": "cmd-p26g-api",
        "idempotency_key": "idem-p26g-api",
        "session_id": "anon-api-p26g",
        "accident_description": "路口刮蹭",
        "accident_datetime": "2026-07-18",
        "accident_location": "路口",
        "injury_status": "no",
        "is_test": True,
    }
    first = client.post("/api/h5/customer/start-claim", json=body)
    assert first.status_code == 201
    payload = first.json()
    assert payload["ok"] is True
    assert payload["resume_token"]
    assert "case_id" not in payload

    claims = verify_h5_task_token(payload["resume_token"])
    assert claims is not None
    case_id = claims.case_id

    # Same session replay keeps one case; resume token still issued.
    second = client.post("/api/h5/customer/start-claim", json=body)
    assert second.status_code == 200
    assert second.json()["resume_token"]
    claims2 = verify_h5_task_token(second.json()["resume_token"])
    assert claims2 is not None
    assert claims2.case_id == case_id


def test_gate2_expired_token_rejected():
    from services.fiqa_api.inbox_triage.p20_customer_launch import issue_customer_launch_token

    launch = issue_customer_launch_token(case_id="case_expired", ttl_seconds=60, now=1_000_000.0)
    # Far in the future relative to token iat/exp.
    assert verify_h5_task_token(launch.token, now=1_000_000.0 + 120) is None


# --- Golden simulation (no broker) ---


def test_e2e_fresh_claim_default_tasks_then_broker_followup(monkeypatch):
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

    created = start_customer_claim(
        command_id="cmd-p26g-e2e",
        idempotency_key="idem-p26g-e2e",
        session_id="anon-e2e",
        accident_description="倒车碰撞前保险杠",
        accident_datetime="2026-07-18 09:00",
        accident_location="地下车库",
        injury_status="no",
        is_test=True,
    )
    case = dict(store.cases[created["case_id"]])
    case["p20_slice1_projection"] = {
        "case_id": created["case_id"],
        "workflow_state": "intake",
        "customer_next_action": None,
        "broker_next_action": {"action_type": "none", "status": "none"},
        "open_request": None,
    }
    case["claim_evidence_summary"] = {"received_slots": [], "missing_required_slots": []}

    before = build_constitution_projection(ConstitutionInputs(case=case))
    by_id = _by_id(before["customer"]["tasks"])
    assert by_id[TASK_ID_INSURANCE]["task_source"] == TASK_SOURCE_SYSTEM_DEFAULT
    assert by_id[TASK_ID_INSURANCE]["actionable"] is True
    assert TASK_ID_PHOTOS in by_id

    # Simulate customer completing insurance via system_default upload slot.
    case["claim_attachment_slots"] = {
        "policy_or_insurance_card": {
            "status": "received",
            "attachment_ids": ["att_e2e_ins"],
        }
    }
    case["case_attachments"] = [
        {
            "attachment_id": "att_e2e_ins",
            "source": "h5_task",
            "msgtype": "image",
            "slot_assignment": "policy_or_insurance_card",
            "evidence_status": "confirmed",
        }
    ]
    mid = build_constitution_projection(ConstitutionInputs(case=case))
    mid_by = _by_id(mid["customer"]["tasks"])
    assert mid_by[TASK_ID_INSURANCE]["state"] == TASK_STATE_COMPLETED
    # After insurance is done, photos remain in the continuous journey (P3.6).
    assert mid_by[TASK_ID_PHOTOS]["actionable"] is True
    assert mid["customer"]["today"] == "补充照片"
    assert mid["customer"]["current_stage"] == "customer_action_needed"
    assert mid["customer"]["current_stage"] != "waiting_broker"

    # Broker exceptional follow-up (VIN) — defaults remain.
    case["p20_slice1_projection"] = {
        "case_id": created["case_id"],
        "workflow_state": "broker_more_requested",
        "customer_next_action": {
            "action_type": "provide_fact",
            "title": "补充 VIN",
            "required_input": "vin",
            "status": "active",
            "instructions": "请提供车辆 VIN",
        },
        "open_request": {
            "status": "open",
            "active_item": {
                "item_type": "vin",
                "label": "补充 VIN",
                "status": "active",
            },
            "queued_items": [],
            "items": [
                {
                    "item_type": "vin",
                    "label": "补充 VIN",
                    "status": "active",
                }
            ],
        },
    }
    after = build_constitution_projection(ConstitutionInputs(case=case))
    after_by = _by_id(after["customer"]["tasks"])
    assert after_by[TASK_ID_INSURANCE]["state"] == TASK_STATE_COMPLETED
    assert after_by[TASK_ID_STORY]["state"] == TASK_STATE_COMPLETED
    assert after["customer"]["today"] == "补充 VIN"
