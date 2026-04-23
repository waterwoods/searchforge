"""Hot-swappable reply template layer: policy keys, composer rendering, fallbacks, handoff overlay."""

from services.fiqa_api.inbox_triage.reply_template_composer import (
    add_car_collecting_fallback_line,
    apply_template_variables,
    render_family,
)
from services.fiqa_api.inbox_triage.reply_template_policy import (
    FAMILY_ADD_CAR_ASK_ZIP,
    FAMILY_HANDOFF_CORRECTION_ACK,
    FAMILY_MISSING_DOC_ALREADY_SENT_NO_ITEM,
    FAMILY_MISSING_DOC_ALREADY_SENT_WITH_ITEM,
    other_corrected_urgency_uses_stitched_line,
    select_add_car_collecting_family_id,
    select_missing_doc_already_sent_family_id,
)
from services.fiqa_api.inbox_triage.triage_handoff_reply_composer import compose_handoff_reply


def test_select_missing_doc_already_sent_family_ids():
    assert (
        select_missing_doc_already_sent_family_id(has_item=True)
        == FAMILY_MISSING_DOC_ALREADY_SENT_WITH_ITEM
    )
    assert (
        select_missing_doc_already_sent_family_id(has_item=False)
        == FAMILY_MISSING_DOC_ALREADY_SENT_NO_ITEM
    )


def test_select_add_car_collecting_zip_when_vehicle_ok_no_zip():
    fields = {
        "year": True,
        "model": True,
        "zip": False,
        "vin": False,
        "delivery": False,
        "driver": False,
    }
    assert select_add_car_collecting_family_id(fields) == FAMILY_ADD_CAR_ASK_ZIP


def test_render_family_substitutes_item_text():
    families = {
        FAMILY_MISSING_DOC_ALREADY_SENT_WITH_ITEM: {
            "zh": "（测）含 {item_text} 尾",
            "en": "test {item_text} tail",
        }
    }
    out = render_family(
        families,
        FAMILY_MISSING_DOC_ALREADY_SENT_WITH_ITEM,
        "zh",
        {"item_text": "声明页"},
        "fallback",
    )
    assert "声明页" in out
    assert "{item_text}" not in out


def test_render_family_falls_back_when_key_missing():
    assert render_family({}, "nope", "zh", None, "  keep  ") == "keep"


def test_add_car_collecting_fallback_line():
    s = add_car_collecting_fallback_line(FAMILY_ADD_CAR_ASK_ZIP, "zh")
    assert len(s) > 5
    assert "报价" in s


def test_compose_handoff_other_corrected_template_overlay():
    layer = {FAMILY_HANDOFF_CORRECTION_ACK: {"zh": "【模板层覆盖】矫正已收到。", "en": "layer-override"}}
    out = compose_handoff_reply(
        language="zh",
        handoff=True,
        key="other_corrected",
        is_add_car=False,
        is_remove_car=False,
        follow_up_type="correction",
        post_submit_phrasing=False,
        customer_turn_index=1,
        last_customer_raw="改好了",
        merged_text="x",
        handoff_phrases={"other_corrected": {"zh": "应被覆盖", "en": "old en"}},
        stitched_cfg={},
        add_car_handoff_base_key="",
        add_car_resolved_intent=None,
        phrases={"zh": "应被覆盖", "en": "old en"},
        issue_category="missing_document",
        tailored_doc_clarification_reply="",
        has_doc_clarification=False,
        prospective_send_prefix="",
        last_customer_lower="改好了",
        add_car_materials_sent=False,
        reply_template_families=layer,
    )
    assert "【模板层覆盖】" in out


def test_urgency_supersedes_correction_template_overlay():
    """Payment correction + urgency question uses stitched line, not generic handoff.correction_ack."""
    layer = {FAMILY_HANDOFF_CORRECTION_ACK: {"zh": "【不应出现】", "en": "bad"}}
    out = compose_handoff_reply(
        language="zh",
        handoff=True,
        key="other_corrected",
        is_add_car=False,
        is_remove_car=False,
        follow_up_type="correction",
        post_submit_phrasing=False,
        customer_turn_index=1,
        last_customer_raw="我改好了，最要紧的是什么？",
        merged_text="x",
        handoff_phrases={"other_corrected": {"zh": "应被覆盖", "en": "e"}},
        stitched_cfg={
            "handoff_payment_correction_urgency": {
                "zh": "【紧急支付线】",
                "en": "u",
            }
        },
        add_car_handoff_base_key="",
        add_car_resolved_intent=None,
        phrases={"zh": "应被覆盖", "en": "e"},
        issue_category="payment_lapse_expiration",
        tailored_doc_clarification_reply="",
        has_doc_clarification=False,
        prospective_send_prefix="",
        last_customer_lower="我改好了，最要紧的是什么？",
        add_car_materials_sent=False,
        reply_template_families=layer,
    )
    assert "【紧急支付线】" in out
    assert "【不应出现】" not in out


def test_apply_template_variables_unknown_placeholder_preserved():
    assert apply_template_variables("a {x} {y}", {"x": "1"}) == "a 1 {y}"


def test_other_corrected_urgency_uses_stitched_line_detection():
    assert other_corrected_urgency_uses_stitched_line(
        "payment_lapse_expiration",
        "先干嘛呢",
    )
    assert not other_corrected_urgency_uses_stitched_line("payment_lapse_expiration", "ok thanks")
