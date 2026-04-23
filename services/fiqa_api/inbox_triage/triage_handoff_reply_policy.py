"""
Handoff phrase-key selection for customer-visible replies.

Core triage decides orchestration and handoff gating; this module picks which
`handoff_phrases.json` storage key and add-car intent resolution drive reply copy.
"""

from __future__ import annotations

from typing import Any

from services.fiqa_api.inbox_triage.add_car_intent import (
    ResolvedAddCarIntent,
    nudge_append_generic_to_supplement_intent,
    resolve_add_car_turn_intent,
)


def merge_still_needed_for_intent(still_gap: list[str], prior_still: list[str]) -> list[str]:
    """Dedupe-merge extraction gaps with persisted case gaps for intent ceiling checks."""
    merged: list[str] = []
    seen: set[str] = set()
    for x in list(still_gap or []) + list(prior_still or []):
        xs = str(x).strip()
        if not xs:
            continue
        key = xs.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(xs)
    return merged


def resolve_add_car_handoff_phrase_key(
    last_customer_raw: str,
    follow_up_type: str,
    handoff_phrases: dict[str, dict[str, str]],
    customer_turn_index: int,
    merged_still_for_intent: list[str],
    reply_truth_context: dict[str, Any] | None,
) -> tuple[str, ResolvedAddCarIntent]:
    """
    Pick handoff_phrases.json base key for add-car using bounded Intent Layer (add_car_intent.py).
    `merged_still_for_intent` should combine live extraction gaps with persisted still_needed (append).
    """
    truth_for_intent: dict[str, Any] = dict(reply_truth_context or {})
    if merged_still_for_intent:
        truth_for_intent["still_needed_fields"] = merged_still_for_intent
    resolved = resolve_add_car_turn_intent(
        last_customer_raw,
        follow_up_type,
        customer_turn_index,
        truth_for_intent,
    )
    resolved = nudge_append_generic_to_supplement_intent(resolved, reply_truth_context)
    base = resolved.handoff_base_key
    if handoff_phrases.get(base):
        return base, resolved
    return "add_car", resolved


def resolve_non_add_car_handoff_phrase_key(
    *,
    is_remove_car: bool,
    follow_up_type: str,
    handoff_phrases: dict[str, dict[str, str]],
) -> str:
    """Map follow-up shape + lane to a phrases.json key (non-add-car paths)."""
    if is_remove_car:
        return "remove_car" if handoff_phrases.get("remove_car") else "other"
    if follow_up_type in (
        "clarification_question",
        "urgency_question",
        "next_step_question",
        "office_review_question",
    ):
        return "other_clarification" if handoff_phrases.get("other_clarification") else "other"
    if follow_up_type == "already_sent":
        return "other_received" if handoff_phrases.get("other_received") else "other"
    if follow_up_type == "correction":
        return "other_corrected" if handoff_phrases.get("other_corrected") else "other"
    return "other"
