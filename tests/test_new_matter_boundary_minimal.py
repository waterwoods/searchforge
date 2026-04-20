"""Focused checks for minimal new-vs-existing matter boundary behavior."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage.triage import triage_for_append


def _add_car_prior_thread() -> str:
    return (
        "[客户] 我想加车，2024 Toyota Camry，ZIP 90210，下周提车，我自己开\n\n"
        "[系统] 已记录加车信息，会继续整理。"
    )


def test_same_case_append_contract_and_fields_present():
    out = triage_for_append(
        _add_car_prior_thread(),
        "补充：VIN 是 1HGCM82633A004352",
        client_id="chen_kui",
        reply_truth_context={"formal_submitted_at": "2026-03-01T12:00:00Z", "service_record_append": True},
    )
    assert out.get("case_boundary") == "same_case"
    assert out.get("case_boundary_action") == "append_allowed"
    assert isinstance(out.get("boundary_reason"), str) and out.get("boundary_reason")
    assert out.get("service_type") == "add_car"
    assert out.get("vehicle_key")


def test_new_issue_append_requires_new_case():
    out = triage_for_append(
        _add_car_prior_thread(),
        "另外我有个理赔问题，昨晚被追尾了。",
        client_id="chen_kui",
        reply_truth_context={"formal_submitted_at": "2026-03-01T12:00:00Z", "service_record_append": True},
    )
    assert out.get("case_boundary") == "new_issue"
    assert out.get("case_boundary_action") == "requires_new_case"
    assert isinstance(out.get("boundary_reason"), str) and out.get("boundary_reason")


def test_borderline_append_requires_confirmation():
    out = triage_for_append(
        _add_car_prior_thread(),
        "顺便问下办公室现在收到没？",
        client_id="chen_kui",
        reply_truth_context={"formal_submitted_at": "2026-03-01T12:00:00Z", "service_record_append": True},
    )
    assert out.get("case_boundary") == "borderline"
    assert out.get("case_boundary_action") == "requires_confirmation"
    br = (out.get("boundary_reason") or "").lower()
    assert "appended" in br and "audit" in br


def test_premium_and_add_car_markers_requote_stays_same_case():
    """Re-quote with price language can hit both premium_review + add_vehicle domains — still same matter."""
    out = triage_for_append(
        _add_car_prior_thread(),
        "续保太贵了，那台车能不能再报一次价",
        client_id="chen_kui",
        reply_truth_context={"formal_submitted_at": "2026-03-01T12:00:00Z", "service_record_append": True},
    )
    assert out.get("case_boundary") == "same_case"
    assert out.get("case_boundary_action") == "append_allowed"


def test_cn_cheap_price_pushback_same_vehicle_stays_same_case():
    """Role C: 便宜一点 without 报价 substring — still same add-car matter, not premium-only new_issue."""
    out = triage_for_append(
        _add_car_prior_thread(),
        "那台车再帮我看看能不能便宜一点",
        client_id="chen_kui",
        reply_truth_context={"formal_submitted_at": "2026-03-01T12:00:00Z", "service_record_append": True},
    )
    assert out.get("case_boundary") == "same_case"
    assert out.get("case_boundary_action") == "append_allowed"


def test_renewal_policy_coordination_append_is_borderline():
    """Another-policy renewal + coordinate with this car: borderline, not hard-split blocked append."""
    out = triage_for_append(
        _add_car_prior_thread(),
        "我想顺便问一下：我另一张保单续保的事能不能和这辆车一起让办公室看？",
        client_id="chen_kui",
        reply_truth_context={"formal_submitted_at": "2026-03-01T12:00:00Z", "service_record_append": True},
    )
    assert out.get("case_boundary") == "borderline"
    assert out.get("case_boundary_action") == "requires_confirmation"


def test_untagged_case_source_text_still_infers_add_car_prior():
    """Formal persist often saves raw customer text without [客户] lines — append must not lose lane."""
    prior_plain = (
        "加车：2022 Mazda CX-5，邮编94501，下周提车，主驾本人，姓名钱七，电话510-555-0303。"
    )
    out = triage_for_append(
        prior_plain,
        "续保太贵了，那台车能不能再报一次价",
        client_id="chen_kui",
        reply_truth_context={"formal_submitted_at": "2026-03-01T12:00:00Z", "service_record_append": True},
    )
    assert out.get("case_boundary") == "same_case"
    assert out.get("service_type") == "add_car"
