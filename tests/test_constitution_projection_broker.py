"""P24C — Broker Constitution Projection (queue / conclusion / next / priority)."""

from __future__ import annotations

import copy

from services.fiqa_api.inbox_triage.constitution_projection import (
    BAND_CUSTOMER_DONE_AWAITING,
    BAND_CUSTOMER_MISSING,
    STAGE_CUSTOMER_ACTION_NEEDED,
    STAGE_WAITING_BROKER,
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
                    {"item_type": "free_text", "label": "驾驶证", "status": "queued"}
                ],
            },
        },
        "claim_case_brief": {
            "summary": "今天下午停车场倒车碰撞，前保险杠受损。客户已提交事故经过和现场照片。",
            "missing_info": ["保险卡内容", "驾驶证", "联系电话"],
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
    case["claim_case_brief"] = {
        "summary": "今天下午停车场倒车碰撞，前保险杠受损。客户已提交事故经过、现场照片和保险卡。",
        "missing_info": ["驾驶证", "联系电话"],
        "brief_version": 1,
    }
    case["p20_slice1_projection"] = {
        "case_id": "case-chen-camry",
        "workflow_state": "broker_review_ready",
        "customer_next_action": {
            "action_type": "wait_for_broker_review",
            "title": "资料已收到",
            "required_input": None,
            "status": "waiting",
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
    return case


def test_camry_before_upload_broker_fields():
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_before_upload_case())
    )
    customer = projection["customer"]
    broker = projection["broker"]

    assert customer["today"] == "上传保险卡"
    assert customer["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED

    assert broker["next_action"]["label"] == "暂无动作"
    assert broker["next_action"]["enabled"] is False
    assert broker["next_action"]["action_type"] == "none"
    assert broker["next_action"]["note"] == "等客户上传保险卡后再开始审核。"

    assert broker["priority"]["band"] == BAND_CUSTOMER_MISSING
    assert broker["priority"]["rank"] == 3
    assert broker["queue_summary"]["band"] == BAND_CUSTOMER_MISSING
    assert broker["queue_summary"]["label"] == "还缺客户关键资料"
    assert broker["queue_summary"]["why_attention"] == "关键保险卡还在客户手里，今天案件推不动。"

    assert broker["case_conclusion"]["customer_focus"] == "上传保险卡"
    assert broker["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED


def test_camry_after_upload_broker_fields():
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_after_upload_case())
    )
    customer = projection["customer"]
    broker = projection["broker"]

    assert customer["today"] == "先不用操作"
    assert customer["current_stage"] == STAGE_WAITING_BROKER

    assert broker["next_action"]["label"] == "审核保险卡"
    assert broker["next_action"]["enabled"] is True
    assert broker["next_action"]["action_type"] == "review_insurance_card"
    assert broker["next_action"]["note"] == "审核通过后，客户会看到你在处理。"

    # P21 Camry after-upload equivalent band
    assert broker["priority"]["band"] == BAND_CUSTOMER_DONE_AWAITING
    assert broker["priority"]["rank"] == 2
    assert broker["queue_summary"]["band"] == BAND_CUSTOMER_DONE_AWAITING
    assert broker["queue_summary"]["why_attention"] == "客户刚完成今天的任务，正在等你开始审核。"

    assert broker["case_conclusion"]["customer_focus"] == "先不用操作"
    assert broker["current_stage"] == STAGE_WAITING_BROKER


def test_no_broker_cta_while_customer_action_active():
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_before_upload_case())
    )
    assert projection["customer"]["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED
    assert projection["broker"]["next_action"]["enabled"] is False
    assert projection["broker"]["next_action"]["label"] == "暂无动作"


def test_review_ready_enables_broker_cta():
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_after_upload_case())
    )
    assert projection["broker"]["next_action"]["enabled"] is True
    assert projection["broker"]["next_action"]["label"] == "审核保险卡"


def test_broker_next_action_precedence_slice1_review_wins():
    case = _camry_after_upload_case()
    # Even with a vague claim phase, Slice1 review action must win.
    case["claim_phase"] = "accident_basics_complete"
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    assert projection["broker"]["next_action"]["label"] == "审核保险卡"
    assert projection["broker"]["next_action"]["enabled"] is True


def test_customer_broker_current_stage_equality():
    for factory in (_camry_before_upload_case, _camry_after_upload_case):
        projection = build_constitution_projection(ConstitutionInputs(case=factory()))
        assert projection["customer"]["current_stage"] == projection["broker"]["current_stage"]
        assert projection["current_stage"] == projection["customer"]["current_stage"]


def test_conclusion_mirrors_customer_today_why_after_trust():
    for factory in (_camry_before_upload_case, _camry_after_upload_case):
        projection = build_constitution_projection(ConstitutionInputs(case=factory()))
        customer = projection["customer"]
        conclusion = projection["broker"]["case_conclusion"]
        assert conclusion["customer_focus"] == customer["today"]
        assert conclusion["customer_why"] == customer["why"]
        assert conclusion["customer_after"] == customer["after"]
        assert conclusion["customer_trust"] == customer["trust"]["care_line"]


def test_priority_band_deterministic():
    before = build_constitution_projection(ConstitutionInputs(case=_camry_before_upload_case()))
    after = build_constitution_projection(ConstitutionInputs(case=_camry_after_upload_case()))
    assert before["broker"]["priority"] == {"band": BAND_CUSTOMER_MISSING, "rank": 3}
    assert after["broker"]["priority"] == {"band": BAND_CUSTOMER_DONE_AWAITING, "rank": 2}


def test_build_idempotent_and_no_case_mutation():
    case = _camry_before_upload_case()
    before = copy.deepcopy(case)
    first = build_constitution_projection(ConstitutionInputs(case=case))
    second = build_constitution_projection(ConstitutionInputs(case=case))
    assert first == second
    assert case == before
