"""Smoke tests for handoff reply composer (stitched resolution + core assembly)."""

from services.fiqa_api.inbox_triage.triage_handoff_reply_composer import (
    compose_handoff_reply,
    stitched_customer_visible_line,
    stitched_customer_visible_line_prefer,
)


def test_stitched_line_defaults_when_key_missing():
    assert (
        stitched_customer_visible_line({}, "missing", "zh", "默认", "def")
        == "默认"
    )


def test_stitched_line_prefer_post_submit():
    stitched = {
        "a_submitted": {"zh": "提交后", "en": "post"},
        "a": {"zh": "前", "en": "pre"},
    }
    assert (
        stitched_customer_visible_line_prefer(
            stitched,
            "a",
            "a_submitted",
            "zh",
            "dzh",
            "den",
            use_post_submit=True,
        )
        == "提交后"
    )


def test_compose_handoff_remove_car_other_branch():
    reply = compose_handoff_reply(
        language="zh",
        handoff=True,
        key="other",
        is_add_car=False,
        is_remove_car=False,
        follow_up_type="new_info",
        post_submit_phrasing=False,
        customer_turn_index=1,
        last_customer_raw="hello",
        merged_text="hello",
        handoff_phrases={},
        stitched_cfg={},
        add_car_handoff_base_key="",
        add_car_resolved_intent=None,
        phrases={},
        issue_category="informational",
        tailored_doc_clarification_reply="",
        has_doc_clarification=False,
        prospective_send_prefix="",
        last_customer_lower="hello",
        add_car_materials_sent=False,
    )
    assert "办公室" in reply
