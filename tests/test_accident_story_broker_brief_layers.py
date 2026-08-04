"""Broker Brief — Accident Story three layers + fallback visibility (pilot blockers)."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_case_brief
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _case_with_assistant(*, used_fallback: bool = False) -> dict:
    return {
        "case_id": "case_rehearse_pilot_01",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "known_facts": {
            "accident_datetime": "昨天下午3点",
            "accident_location": "San Jose 停车场",
            "accident_description": "追尾",
            "injury_status": "no",
        },
        "accident_story_assistant": {
            "schema_version": 1,
            "ai_involved": True,
            "authority": "customer_confirmed",
            "raw_story": "昨天下午3点在 San Jose 停车场被追尾，没有受伤。",
            "incident_summary": "追尾，无受伤",
            "questions_asked": ["事故大约发生在几点？"],
            "edited_field_names": ["accident_datetime"],
            "used_fallback": used_fallback,
            "fallback_reason_category": "timeout" if used_fallback else "none",
            "layers": {
                "customer_raw": {
                    "label_zh": "客户原始描述",
                    "text": "昨天下午3点在 San Jose 停车场被追尾，没有受伤。",
                },
                "ai_draft": {
                    "label_zh": "AI整理草稿",
                    "incident_summary": "AI草稿摘要",
                    "accident_time_text": "昨天",
                    "accident_location_text": "San Jose",
                    "injury_status": "no",
                    "authority": "ai_proposed",
                },
                "customer_confirmed": {
                    "label_zh": "客户已确认事实",
                    "incident_summary": "客户确认摘要",
                    "accident_time_text": "昨天下午3点",
                    "accident_location_text": "San Jose 停车场",
                    "injury_status": "no",
                    "edited_field_names": ["accident_datetime"],
                    "authority": "customer_confirmed",
                },
            },
        },
    }


def test_brief_exposes_three_layers_and_support_ref():
    brief = build_claim_case_brief(_case_with_assistant())
    asa = brief["accident_story_assistant"]
    assert asa is not None
    assert asa["ai_involved"] is True
    assert asa["authority"] == "customer_confirmed"
    assert asa["layers"]["customer_raw"]["label_zh"] == "客户原始描述"
    assert asa["layers"]["ai_draft"]["label_zh"] == "AI整理草稿"
    assert asa["layers"]["customer_confirmed"]["label_zh"] == "客户已确认事实"
    assert asa["layers"]["ai_draft"]["authority"] == "ai_proposed"
    assert asa["layers"]["customer_confirmed"]["authority"] == "customer_confirmed"
    assert asa["support_case_ref"] == "case_rehearse_pi"
    assert "确认" in (asa.get("pilot_review_hint_zh") or "")
    assert "事故事实已确认" in (brief.get("next_best_question") or "")


def test_brief_surfaces_fallback_for_office():
    brief = build_claim_case_brief(_case_with_assistant(used_fallback=True))
    asa = brief["accident_story_assistant"]
    assert asa["used_fallback"] is True
    assert asa["fallback_reason_category"] == "timeout"
    assert "回退" in (asa.get("pilot_review_hint_zh") or "")
    kinds = [h.get("kind") for h in brief.get("highlights") or []]
    assert "accident_story_fallback" in kinds
    assert "回退" in (brief.get("next_best_question") or "")


def test_unconfirmed_ai_not_labeled_as_customer_fact():
    case = _case_with_assistant()
    case["accident_story_assistant"]["authority"] = "ai_proposed"
    brief = build_claim_case_brief(case)
    asa = brief["accident_story_assistant"]
    assert "未确认" in (asa.get("label_zh") or "")
    assert asa["layers"]["customer_confirmed"]["authority"] is None
