"""Bounded regression: Add-Car append / follow-up truth vs formal-submit model."""

from services.fiqa_api.inbox_triage.triage import triage_for_append
from services.fiqa_api.inbox_triage.triage_handoff_reply_policy import (
    resolve_add_car_handoff_phrase_key as _resolve_add_car_handoff_phrase_key,
)


def test_triage_for_append_sets_office_followup_when_formal_submit_truth():
    prior = (
        "[客户] 客户要加一台2021 Tesla Model Y，ZIP 90210，下周一提车，主驾是我自己，"
        "姓名张三电话4155550100\n\n[系统] 已记录"
    )
    ctx = {
        "formal_submitted_at": "2026-03-01T12:00:00Z",
        "service_record_append": True,
        "still_needed_fields": [],
    }
    r = triage_for_append(prior, "好的，谢谢。", client_id="chen_kui", reply_truth_context=ctx)
    assert r.get("lifecycle_status") == "office_followup"
    assert r.get("handoff_ready") is True
    assert r.get("triage_mode") == "append"


def test_resolve_add_car_merges_persisted_still_needed_into_intent_truth():
    """Short append bubble may not restate gaps; case-level still_needed must reach intent ceiling."""
    hp = {
        "add_car_quote_detail": {"zh": "zh", "en": "en"},
        "add_car": {"zh": "zh", "en": "en"},
    }
    _, resolved = _resolve_add_car_handoff_phrase_key(
        "免赔额选500还是1000？",
        "new_info",
        hp,
        4,
        ["name"],
        {
            "formal_submitted_at": "2026-03-01T12:00:00Z",
            "still_needed_fields": ["name"],
            "service_record_append": True,
        },
    )
    assert "still_needed_present_quote_detail" in "".join(resolved.truth_notes)
