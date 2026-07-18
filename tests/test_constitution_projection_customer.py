"""P24B — Customer Constitution Projection (Today / Why / After / Trust)."""

from __future__ import annotations

import copy

from services.fiqa_api.inbox_triage.constitution_projection import (
    STAGE_CUSTOMER_ACTION_NEEDED,
    STAGE_WAITING,
    STAGE_WAITING_BROKER,
    ConstitutionInputs,
    build_constitution_projection,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _camry_before_upload_case() -> dict:
    """Production-like Camry: Slice1 still asking for insurance card."""
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
    """Same Camry case after insurance card satisfied → broker review ready."""
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
    return case


def test_camry_before_insurance_card_upload():
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_before_upload_case())
    )
    customer = projection["customer"]
    assert customer["today"] == "上传保险卡"
    assert customer["why"] == "事故经过和现场照片已经完成。"
    assert customer["after"] == "陈总开始审核。"
    assert customer["trust"] == {
        "care_line": "陈总已收到资料",
        "care_note": "如有需要，我们会联系您",
    }
    assert customer["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED
    assert projection["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED


def test_camry_after_insurance_card_upload():
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_after_upload_case())
    )
    customer = projection["customer"]
    assert customer["today"] == "先不用操作"
    assert customer["why"] == "资料已齐，陈总正在审核。"
    assert customer["after"] == "请等待确认。"
    assert customer["trust"] == {
        "care_line": "下一步由陈总审核",
        "care_note": "我们会联系您（如需要）",
    }
    assert customer["current_stage"] == STAGE_WAITING_BROKER
    assert projection["current_stage"] == STAGE_WAITING_BROKER


def test_customer_has_one_today_only_ignores_queued_items():
    case = _camry_before_upload_case()
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    today = projection["customer"]["today"]
    assert today == "上传保险卡"
    assert isinstance(today, str)
    assert "驾驶证" not in today
    assert "\n" not in today


def test_structured_slice1_customer_action_wins_over_fallback():
    case = _camry_before_upload_case()
    case["p20_slice1_projection"]["customer_next_action"] = {
        "action_type": "provide_fact",
        "title": "确认驾驶员",
        "required_input": "free_text",
        "status": "active",
    }
    case["p20_slice1_projection"]["open_request"]["active_item"] = {
        "item_type": "free_text",
        "label": "确认驾驶员",
        "status": "active",
    }
    # Phase alone would only yield safe wait; Slice1 title must win.
    case["claim_phase"] = "intake_ready_for_broker"
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    assert projection["customer"]["today"] == "确认驾驶员"
    assert projection["customer"]["why"] == "请先完成这一步，方便我们继续处理。"
    assert projection["customer"]["after"] == "完成后我们会继续处理。"
    assert projection["customer"]["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED


def test_no_customer_action_returns_safe_waiting_state():
    case = {
        "case_id": "case-neutral-wait",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "accident_basics_in_progress",
        "p20_slice1_projection": {
            "workflow_state": "broker_reviewing",
            "customer_next_action": {
                "action_type": "contact_broker",
                "title": "请联系陈总办公室",
                "status": "blocked",
            },
            "broker_next_action": {
                "action_type": "none",
                "status": "none",
            },
            "open_request": None,
        },
    }
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    customer = projection["customer"]
    assert customer["today"] == "先不用操作"
    assert customer["why"] == "目前没有需要您操作的事项。"
    assert customer["after"] == "有进展时我们会联系您。"
    assert customer["trust"] == {
        "care_line": "下一步由陈总审核",
        "care_note": "我们会联系您（如需要）",
    }
    assert customer["current_stage"] == STAGE_WAITING


def test_build_is_idempotent():
    case = _camry_before_upload_case()
    first = build_constitution_projection(ConstitutionInputs(case=case))
    second = build_constitution_projection(ConstitutionInputs(case=case))
    assert first == second


def test_build_does_not_mutate_camry_case():
    case = _camry_before_upload_case()
    before = copy.deepcopy(case)
    _ = build_constitution_projection(ConstitutionInputs(case=case))
    assert case == before


def test_broker_mirrors_customer_one_truth_on_camry():
    """P24C fills broker half; One Truth still mirrors customer Today/Why/After."""
    projection = build_constitution_projection(
        ConstitutionInputs(case=_camry_before_upload_case())
    )
    customer = projection["customer"]
    broker = projection["broker"]
    assert broker["case_conclusion"]["customer_focus"] == customer["today"]
    assert broker["case_conclusion"]["customer_why"] == customer["why"]
    assert broker["case_conclusion"]["customer_after"] == customer["after"]
    assert broker["current_stage"] == customer["current_stage"]
    assert broker["next_action"]["enabled"] is False
    assert broker["next_action"]["label"] == "暂无动作"
