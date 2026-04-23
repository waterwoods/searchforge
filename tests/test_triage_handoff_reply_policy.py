"""Unit tests for handoff phrase-key policy helpers (extracted from triage)."""

from services.fiqa_api.inbox_triage.triage_handoff_reply_policy import (
    merge_still_needed_for_intent,
    resolve_non_add_car_handoff_phrase_key,
)


def test_merge_still_needed_for_intent_dedupes_case_insensitive():
    assert merge_still_needed_for_intent(["ZIP", "zip"], ["phone"]) == ["ZIP", "phone"]


def test_resolve_non_add_car_remove_car():
    phrases = {"remove_car": {"zh": "x"}}
    assert (
        resolve_non_add_car_handoff_phrase_key(
            is_remove_car=True, follow_up_type="new_info", handoff_phrases=phrases
        )
        == "remove_car"
    )
    assert (
        resolve_non_add_car_handoff_phrase_key(
            is_remove_car=True, follow_up_type="new_info", handoff_phrases={}
        )
        == "other"
    )


def test_resolve_non_add_car_follow_up_types():
    phrases = {
        "other_clarification": {"zh": "c"},
        "other_received": {"zh": "r"},
        "other_corrected": {"zh": "x"},
    }
    assert (
        resolve_non_add_car_handoff_phrase_key(
            is_remove_car=False, follow_up_type="clarification_question", handoff_phrases=phrases
        )
        == "other_clarification"
    )
    assert (
        resolve_non_add_car_handoff_phrase_key(
            is_remove_car=False, follow_up_type="already_sent", handoff_phrases=phrases
        )
        == "other_received"
    )
    assert (
        resolve_non_add_car_handoff_phrase_key(
            is_remove_car=False, follow_up_type="correction", handoff_phrases=phrases
        )
        == "other_corrected"
    )
    assert (
        resolve_non_add_car_handoff_phrase_key(
            is_remove_car=False, follow_up_type="new_info", handoff_phrases=phrases
        )
        == "other"
    )
