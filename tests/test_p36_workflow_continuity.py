"""P3.6 — Workflow continuity: never Waiting while default journey work remains."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.constitution_projection import (
    TASK_ID_INSURANCE,
    TASK_ID_PHOTOS,
    TASK_STATE_COMPLETED,
    ConstitutionInputs,
    build_constitution_projection,
)
from services.fiqa_api.inbox_triage.p0_customer_context import (
    BROKER_REVIEW,
    UPLOAD_REQUEST_ITEM,
    _next_action_from_task,
)


def _case_after_story_and_insurance(*, photos_done: bool = False) -> dict:
    attachments = [
        {
            "attachment_id": "att_ins",
            "source": "h5_task",
            "msgtype": "image",
            "slot_assignment": "policy_or_insurance_card",
            "evidence_status": "confirmed",
        }
    ]
    slots: dict = {
        "policy_or_insurance_card": {
            "status": "received",
            "attachment_ids": ["att_ins"],
        }
    }
    received = ["policy_or_insurance_card"]
    if photos_done:
        # Match production H5 gallery categories (see P26F photo completion test).
        attachments.extend(
            [
                {
                    "attachment_id": "att_vd_1",
                    "source": "h5_task",
                    "msgtype": "image",
                    "mime_type": "image/jpeg",
                    "slot_assignment": "vehicle_damage",
                    "evidence_category": "vehicle_damage",
                    "evidence_status": "confirmed",
                    "flow": "claim_evidence_pack",
                },
                {
                    "attachment_id": "att_scene_1",
                    "source": "h5_task",
                    "msgtype": "image",
                    "mime_type": "image/jpeg",
                    "slot_assignment": "other_vehicle_scene",
                    "evidence_category": "other_vehicle_scene",
                    "evidence_status": "confirmed",
                    "flow": "claim_evidence_pack",
                },
            ]
        )
        slots["vehicle_damage"] = {
            "status": "received",
            "source_channel": "h5_task",
            "attachment_ids": ["att_vd_1"],
        }
        received = ["policy_or_insurance_card", "customer_damage_photo", "other_party_vehicle_photo"]
    return {
        "case_id": "case-p36",
        "service_lane": "claim",
        "claim_phase": "intake",
        "known_facts": {
            "accident_description": "倒车碰撞前保险杠",
            "accident_datetime": "2026-07-26 09:00",
            "accident_location": "地下车库",
            "injury_status": "no",
        },
        "p20_slice1_projection": {
            "case_id": "case-p36",
            "workflow_state": "intake",
            "customer_next_action": None,
            "broker_next_action": {"action_type": "none", "status": "none"},
            "open_request": None,
        },
        "claim_evidence_summary": {
            "received_slots": received,
            "missing_required_slots": [],
        },
        "claim_attachment_slots": slots,
        "case_attachments": attachments,
    }


def test_scenario_a_insurance_done_photos_open_is_action_needed_not_waiting():
    proj = build_constitution_projection(ConstitutionInputs(case=_case_after_story_and_insurance()))
    customer = proj["customer"]
    by_id = {row["task_id"]: row for row in customer["tasks"]}
    assert by_id[TASK_ID_INSURANCE]["state"] == TASK_STATE_COMPLETED
    assert by_id[TASK_ID_PHOTOS]["actionable"] is True
    assert customer["today"] == "补充照片"
    assert customer["current_stage"] == "customer_action_needed"
    assert "陈总正在看" not in str(customer.get("why") or "")


def test_scenario_a_photos_done_then_waiting_allowed():
    case = _case_after_story_and_insurance(photos_done=True)
    case["p20_slice1_projection"]["broker_next_action"] = {
        "action_type": "review_customer_response",
        "status": "review_ready",
    }
    case["claim_phase"] = "broker_reviewing"
    proj = build_constitution_projection(ConstitutionInputs(case=case))
    customer = proj["customer"]
    assert customer["current_stage"] == "waiting_broker"
    assert "陈总正在看" in str(customer.get("why") or "")


def test_scenario_b_continue_prefers_upload_over_broker_review_while_photos_open():
    proj = build_constitution_projection(ConstitutionInputs(case=_case_after_story_and_insurance()))
    task = {
        "case_id": "case-p36",
        "submitted": False,
        "constitution_projection": proj,
        "slice1_projection": {
            "customer_next_action": {
                "action_type": "wait_for_broker_review",
                "title": "先不用操作",
            }
        },
    }
    assert _next_action_from_task(task) == UPLOAD_REQUEST_ITEM
    assert _next_action_from_task(task) != BROKER_REVIEW


def test_scenario_c_broker_request_insurance_later_is_continue_work():
    case = _case_after_story_and_insurance(photos_done=True)
    # Clear insurance so broker can request it later.
    case["claim_attachment_slots"] = {}
    case["case_attachments"] = [
        a
        for a in case["case_attachments"]
        if a.get("slot_assignment") != "policy_or_insurance_card"
    ]
    case["p20_slice1_projection"] = {
        "case_id": "case-p36",
        "workflow_state": "broker_more_requested",
        "customer_next_action": {
            "action_type": "provide_evidence",
            "title": "上传保险卡",
            "required_input": "policy_or_insurance_card",
            "status": "active",
            "request_item_id": "item_ins",
        },
        "open_request": {
            "status": "open",
            "active_item": {
                "request_item_id": "item_ins",
                "item_type": "policy_or_insurance_card",
                "label": "上传保险卡",
                "status": "active",
            },
            "items": [
                {
                    "request_item_id": "item_ins",
                    "item_type": "policy_or_insurance_card",
                    "label": "上传保险卡",
                    "status": "active",
                }
            ],
            "queued_items": [],
        },
        "broker_next_action": {
            "action_type": "wait_for_customer_item",
            "status": "waiting_for_customer",
        },
    }
    proj = build_constitution_projection(ConstitutionInputs(case=case))
    assert proj["customer"]["current_stage"] == "customer_action_needed"
    task = {
        "case_id": "case-p36",
        "submitted": False,
        "constitution_projection": proj,
        "slice1_projection": case["p20_slice1_projection"],
    }
    assert _next_action_from_task(task) == UPLOAD_REQUEST_ITEM
    assert _next_action_from_task(task) != BROKER_REVIEW
