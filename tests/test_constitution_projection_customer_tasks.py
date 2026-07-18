"""P26A — Constitution customer.tasks for Customer Task Home skeleton."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.constitution_projection import (
    TASK_ID_DRIVER_LICENSE,
    TASK_ID_INSURANCE,
    TASK_ID_PHOTOS,
    TASK_ID_STORY,
    TASK_STATE_BLOCKED,
    TASK_STATE_COMPLETED,
    TASK_STATE_IN_PROGRESS,
    TASK_STATE_WAITING_BROKER,
    ConstitutionInputs,
    build_constitution_projection,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _camry_before_upload_case() -> dict:
    return {
        "case_id": "case-chen-camry",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_needs_more_info",
        "customer_name": "陈明",
        "known_facts": {
            "own_vehicle_info": "2020 Toyota Camry",
            "accident_location": "停车场",
            "accident_description": "倒车碰撞，前保险杠受损",
        },
        "p20_slice1_projection": {
            "case_id": "case-chen-camry",
            "workflow_state": "broker_more_requested",
            "customer_next_action": {
                "action_type": "provide_evidence",
                "title": "上传保险卡",
                "required_input": "policy_or_insurance_card",
                "status": "active",
                "instructions": "请上传清晰的保险卡照片",
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
                        "item_type": "free_text",
                        "label": "驾驶证",
                        "status": "queued",
                    }
                ],
            },
        },
        "claim_case_brief": {
            "summary": "客户已提交事故经过和现场照片。",
            "missing_info": ["保险卡"],
            "brief_version": 1,
        },
        "claim_evidence_summary": {
            "received_slots": ["scene_photo"],
            "missing_required_slots": [],
        },
    }


def _camry_after_upload_case() -> dict:
    case = _camry_before_upload_case()
    case["claim_phase"] = "intake_ready_for_broker"
    case["p20_slice1_projection"] = {
        "case_id": "case-chen-camry",
        "workflow_state": "broker_review_ready",
        "customer_next_action": {
            "action_type": "wait_for_broker_review",
            "title": "资料已收到",
            "required_input": None,
            "status": "waiting",
            "instructions": "陈总正在审核中。",
        },
        "broker_next_action": {
            "action_type": "review_customer_response",
            "status": "review_ready",
        },
        "open_request": {
            "status": "completed",
            "active_item": None,
            "queued_items": [],
            "items": [
                {
                    "item_type": "policy_or_insurance_card",
                    "label": "上传保险卡",
                    "status": "satisfied",
                }
            ],
        },
    }
    case["claim_case_brief"] = {
        "summary": "客户已提交事故经过、现场照片和保险卡。",
        "missing_info": [],
        "brief_version": 2,
    }
    case["claim_evidence_summary"] = {
        "received_slots": ["scene_photo", "policy_or_insurance_card"],
        "missing_required_slots": [],
    }
    return case


def _by_id(tasks: list[dict]) -> dict[str, dict]:
    return {str(t["task_id"]): t for t in tasks}


def test_camry_before_upload_task_cards():
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_before_upload_case())
    )
    # Broker next-action must stay unchanged by Task Home skeleton.
    assert projection["broker"]["next_action"]["enabled"] is False
    assert projection["broker"]["next_action"]["label"] == "暂无动作"

    tasks = projection["customer"]["tasks"]
    by_id = _by_id(tasks)
    assert set(by_id) == {
        TASK_ID_INSURANCE,
        TASK_ID_PHOTOS,
        TASK_ID_STORY,
        TASK_ID_DRIVER_LICENSE,
    }

    insurance = by_id[TASK_ID_INSURANCE]
    assert insurance["state"] == TASK_STATE_IN_PROGRESS
    assert insurance["is_today"] is True
    assert insurance["actionable"] is True
    assert insurance["route"] == "request_item"

    assert by_id[TASK_ID_PHOTOS]["state"] == TASK_STATE_COMPLETED
    assert by_id[TASK_ID_STORY]["state"] == TASK_STATE_COMPLETED

    dl = by_id[TASK_ID_DRIVER_LICENSE]
    assert dl["state"] == TASK_STATE_BLOCKED
    assert dl["actionable"] is False
    assert dl["route"] is None


def test_camry_after_upload_insurance_waiting_broker_and_dl_omitted():
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_after_upload_case())
    )
    assert projection["broker"]["next_action"]["enabled"] is True
    assert projection["broker"]["next_action"]["label"] == "审核保险卡"

    tasks = projection["customer"]["tasks"]
    by_id = _by_id(tasks)
    assert TASK_ID_DRIVER_LICENSE not in by_id
    assert by_id[TASK_ID_INSURANCE]["state"] == TASK_STATE_WAITING_BROKER
    assert by_id[TASK_ID_INSURANCE]["actionable"] is False
    assert by_id[TASK_ID_PHOTOS]["state"] == TASK_STATE_COMPLETED
    assert by_id[TASK_ID_STORY]["state"] == TASK_STATE_COMPLETED


def test_insurance_today_one_truth_even_when_photo_slots_empty():
    """Why says story+photos done; cards must not show competing pending photos."""
    case = _camry_before_upload_case()
    case["claim_evidence_summary"] = {
        "received_slots": [],
        "missing_required_slots": [],
    }
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    customer = projection["customer"]
    assert "现场照片已经完成" in str(customer.get("why") or "")
    by_id = _by_id(customer["tasks"])
    assert by_id[TASK_ID_INSURANCE]["is_today"] is True
    assert by_id[TASK_ID_PHOTOS]["state"] == TASK_STATE_COMPLETED
    assert by_id[TASK_ID_PHOTOS]["actionable"] is False
    assert by_id[TASK_ID_STORY]["state"] == TASK_STATE_COMPLETED
    assert by_id[TASK_ID_STORY]["actionable"] is False


def test_photo_uploads_as_gallery_categories_complete_accident_photos_task():
    """P26F — live H5 uploads may store vehicle_damage; Constitution must still reconcile."""
    case = _camry_after_upload_case()
    # Stale seed summary with no photo slots (Founder regression shape).
    case["claim_evidence_summary"] = {
        "received_slots": ["policy_or_insurance_card"],
        "missing_required_slots": ["customer_damage_photo"],
    }
    case["case_attachments"] = [
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
    case["claim_attachment_slots"] = {
        "vehicle_damage": {
            "status": "received",
            "source_channel": "h5_task",
            "attachment_ids": ["att_vd_1"],
        }
    }

    projection = build_constitution_projection(ConstitutionInputs(case=case))
    by_id = _by_id(projection["customer"]["tasks"])
    photos = by_id[TASK_ID_PHOTOS]
    assert photos["state"] == TASK_STATE_COMPLETED
    assert photos["actionable"] is False
    assert photos["progress"]["completed"] >= 1
    assert photos["route"] is None


def test_stale_summary_without_attachments_still_used_for_seeded_golden():
    """Without live attachments, seeded claim_evidence_summary remains authority."""
    case = _camry_before_upload_case()
    case["case_attachments"] = []
    case["claim_attachment_slots"] = {}
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    by_id = _by_id(projection["customer"]["tasks"])
    # Seeded scene_photo + insurance Today → photos completed (One Truth with Why).
    assert by_id[TASK_ID_PHOTOS]["state"] == TASK_STATE_COMPLETED


def test_tasks_are_projection_only_not_hardcoded_empty_when_no_case_signals():
    case = {
        "case_id": "case-empty-signals",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "accident_basics_complete",
        "known_facts": {},
        "p20_slice1_projection": {
            "case_id": "case-empty-signals",
            "workflow_state": "intake",
            "customer_next_action": None,
            "broker_next_action": {"action_type": "none", "status": "none"},
            "open_request": None,
        },
        "claim_evidence_summary": {"received_slots": [], "missing_required_slots": []},
    }
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    tasks = projection["customer"]["tasks"]
    by_id = _by_id(tasks)
    # Core three skeleton cards still project from Case/Evidence emptiness.
    assert TASK_ID_INSURANCE in by_id
    assert TASK_ID_PHOTOS in by_id
    assert TASK_ID_STORY in by_id
    # P26G: default intake is actionable without a broker request row.
    assert by_id[TASK_ID_INSURANCE]["actionable"] is True
    assert by_id[TASK_ID_INSURANCE]["task_source"] == "system_default"
    assert projection["customer"]["today"] != "先不用操作"
    # DL omitted — production path not open.
    assert TASK_ID_DRIVER_LICENSE not in by_id
