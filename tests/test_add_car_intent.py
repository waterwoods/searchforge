"""Regression: Add-Car bounded Intent Layer + Truth × Intent routing."""

from services.fiqa_api.inbox_triage.add_car_intent import (
    INTENT_GENERIC_FOLLOWUP,
    INTENT_MATERIALS_CLAIM,
    INTENT_OFFICE_RECEIPT_QUESTION,
    INTENT_QUOTE_DETAIL_QUESTION,
    INTENT_TIMELINE_QUESTION,
    INTENT_SUPPLEMENT_INFO,
    ResolvedAddCarIntent,
    nudge_append_generic_to_supplement_intent,
    resolve_add_car_turn_intent,
)


def test_timeline_vs_quote_detail_routes_differently():
    t = resolve_add_car_turn_intent("大概多久能出报价？", "new_info", 3, None)
    assert t.intent_family == INTENT_TIMELINE_QUESTION
    assert t.handoff_base_key == "add_car_timeline"
    q = resolve_add_car_turn_intent("免赔额选500还是1000？", "new_info", 3, None)
    assert q.intent_family == INTENT_QUOTE_DETAIL_QUESTION
    assert q.handoff_base_key == "add_car_quote_detail"
    assert t.handoff_base_key != q.handoff_base_key


def test_messy_timeline_markers_not_clarification_only():
    t = resolve_add_car_turn_intent("为什么还要等这么久，你们那边没回我啊？", "clarification_question", 6, None)
    assert t.intent_family == INTENT_TIMELINE_QUESTION


def test_follow_up_urgency_maps_timeline():
    u = resolve_add_car_turn_intent("今天最要紧是不是先把资料补齐？", "urgency_question", 5, None)
    assert u.intent_family == INTENT_TIMELINE_QUESTION
    assert "follow_up_urgency_question" in u.truth_notes


def test_new_info_long_question_is_supplement_not_generic():
    # Avoid quote/detail markers so we exercise the new_info branch (not quote_detail_question)
    s = resolve_add_car_turn_intent(
        "我就是想跟你们说一下我家这边临时有点事，可能要晚一两天才能去盖章可以吗？",
        "new_info",
        6,
        None,
    )
    assert s.intent_family == INTENT_SUPPLEMENT_INFO
    assert "new_info_long_question_supplement_not_generic" in s.truth_notes


def test_office_receipt_vs_materials_claim():
    r = resolve_add_car_turn_intent("材料昨天发你了，你们收到了吗？", "already_sent", 4, None)
    assert r.intent_family == INTENT_OFFICE_RECEIPT_QUESTION
    assert r.handoff_base_key == "add_car_office_receipt"
    m = resolve_add_car_turn_intent("行驶证发你微信了", "already_sent", 4, None)
    assert m.intent_family == INTENT_MATERIALS_CLAIM
    assert m.handoff_base_key == "add_car_supplement"


def test_truth_notes_pre_submit_office_receipt():
    r = resolve_add_car_turn_intent("办公室收到了吗？", "new_info", 3, None)
    assert r.intent_family == INTENT_OFFICE_RECEIPT_QUESTION
    assert "office_receipt_no_formal_submit" in "".join(r.truth_notes)


def test_post_submit_office_receipt_no_false_claim_note():
    r = resolve_add_car_turn_intent(
        "你们那边收到了吗？",
        "new_info",
        3,
        {"formal_submitted_at": "2026-01-01T00:00:00Z"},
    )
    assert r.intent_family == INTENT_OFFICE_RECEIPT_QUESTION
    assert not any("no_formal_submit" in n for n in r.truth_notes)


def test_materials_turn2_uses_supplement_routing():
    m = resolve_add_car_turn_intent("截图发你了", "already_sent", 2, None)
    assert m.handoff_base_key == "add_car_supplement"


def test_materials_turn1_uses_flagship_key():
    m = resolve_add_car_turn_intent("截图发你了", "already_sent", 1, None)
    assert m.handoff_base_key == "add_car"


def test_supplement_info_late_turn():
    s = resolve_add_car_turn_intent("VIN 是 12345", "new_info", 3, None)
    assert s.intent_family == INTENT_SUPPLEMENT_INFO
    assert s.handoff_base_key == "add_car_supplement"


def test_append_nudge_generic_flagship_to_supplement():
    raw = ResolvedAddCarIntent(
        intent_family=INTENT_GENERIC_FOLLOWUP,
        handoff_base_key="add_car",
        truth_notes=(),
    )
    nudged = nudge_append_generic_to_supplement_intent(
        raw,
        {"formal_submitted_at": "2026-01-01T00:00:00Z", "service_record_append": True},
    )
    assert nudged.handoff_base_key == "add_car_supplement"
    assert nudged.intent_family == INTENT_SUPPLEMENT_INFO
    assert "append_continuation_supplement_tone" in nudged.truth_notes


def test_append_nudge_skips_without_flag():
    raw = ResolvedAddCarIntent(
        intent_family=INTENT_GENERIC_FOLLOWUP,
        handoff_base_key="add_car",
        truth_notes=(),
    )
    same = nudge_append_generic_to_supplement_intent(raw, {"formal_submitted_at": "2026-01-01T00:00:00Z"})
    assert same.handoff_base_key == "add_car"


def test_validate_triage_result_preserves_add_car_turn_intent():
    from services.fiqa_api.inbox_triage.case_store import _validate_triage_result

    r = {
        "issue_category": "customer_question",
        "urgency": "low",
        "broker_next_step": "a",
        "client_prep": "b",
        "client_reply_draft": "c",
        "manual_followup_needed": False,
        "add_car_turn_intent": {
            "intent_family": "timeline_question",
            "handoff_base_key": "add_car_timeline",
            "truth_notes": ["note_a"],
            "phrase_storage_key": "add_car_timeline_submitted",
        },
    }
    v = _validate_triage_result(r)
    ac = v.get("add_car_turn_intent") or {}
    assert ac.get("intent_family") == "timeline_question"
    assert ac.get("phrase_storage_key") == "add_car_timeline_submitted"
    assert ac.get("truth_notes") == ["note_a"]


def test_extract_contact_labeled_name_and_mobile():
    from services.fiqa_api.inbox_triage.triage import _extract_contact_fields

    blob = "[客户] 姓名：王五 手机：415-555-0199"
    n, p = _extract_contact_fields(blob)
    assert n == "王五"
    assert p == "415-555-0199"


def test_extract_contact_name_zh_no_colon_before_phone():
    from services.fiqa_api.inbox_triage.triage import _extract_contact_fields

    blob = "[客户] 我想给2024款BMW 330i做加车报价，邮编90210，下周三提车，主驾是我本人，姓名张三，电话415-555-0101。"
    n, p = _extract_contact_fields(blob)
    assert n == "张三"
    assert p == "415-555-0101"
