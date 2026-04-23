"""
Generic and add-car handoff *timing* policy — extracted from triage orchestration.

Core flow stays in `triage_conversation`; this module holds the replaceable
rules: default handoff when manual follow-up is flagged, add-car turn-1 lifts,
and when a draft `next_ask` should defer immediate handoff.

Engine-level facts (case_usable, V5, quote_ready_status) remain in
`case_draft_engine` and callers; this layer only composes them for decisions.
"""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.case_draft_engine import evaluate_action_ready_rule

# Tunable: customer turns (1-based) at which we allow handoff even when
# `manual_followup_needed` is true. Product default: 2+ (see PTD §7 median turns).
GENERIC_MANUAL_FOLLOWUP_HANDOFF_MIN_CUSTOMER_TURN: int = 2

# Turn-1 add-car: ZH “conversational” opener (requires punctuation) — fact-dense same-line
# facts can still lift when quote_ready (see `compute_add_car_turn1_quote_ready_handoff_lift`).
_ZH_CONV_ADD_CAR_OPENER_RE = re.compile(
    r"^\s*(我?想加车|我要加车|帮忙加车|想加一台车|想加一辆车|加一台车|加一辆车|我想加一台|我想加一辆)([。．，,])",
)


def generic_should_handoff(
    customer_turn_count: int,
    manual_followup_needed: bool,
    issue_category: str,
) -> bool:
    """
    Default multi-category handoff: broker when no manual follow-up is required,
    or after enough customer turns when follow-up is still required.

    `issue_category` is reserved for future per-category policy; unused today.
    """
    _ = issue_category
    if not manual_followup_needed:
        return True
    if customer_turn_count >= GENERIC_MANUAL_FOLLOWUP_HANDOFF_MIN_CUSTOMER_TURN:
        return True
    return False


def compute_add_car_turn1_quote_ready_handoff_lift(
    *,
    qrs: str,
    last_customer_raw: str,
    still_needed: list | None,
    language: str,
) -> bool:
    """
    Turn-1 add-car: lift to handoff when quote_ready and the opener / gap pattern matches.

    Mirrors prior triage.py behavior (cross-client EN opener, ZH fact-dense paste, etc.).
    """
    if str(qrs or "").strip() != "quote_ready":
        return False
    _raw = (last_customer_raw or "").strip()
    _en_add_car_opener = bool(re.match(r"(?i)add\s*car\b", _raw))
    _still = list(still_needed or [])
    _no_struct_still = not bool(_still)
    _still_lo = {str(x).lower() for x in _still}
    _contact_only_still = _still_lo <= {"name", "phone"} and bool(_still_lo)
    _lang = (language or "").strip().lower()
    _zh_conv_add_opener = bool(_ZH_CONV_ADD_CAR_OPENER_RE.match(_raw))
    if _no_struct_still:
        return True
    if _lang == "en" and _en_add_car_opener:
        return True
    if _contact_only_still and _lang == "zh" and not _zh_conv_add_opener:
        return True
    return False


def apply_add_car_turn1_quote_ready_gates_to_would_handoff(
    would_handoff: bool,
    *,
    is_add_car: bool,
    customer_turn: int,
    qrs: str,
    last_customer_raw: str,
    still_needed: list | None,
    language: str,
) -> tuple[bool, bool]:
    """
    On add-car first customer turn, apply quote_ready lift, or force *no* handoff
    when pilot quote state is not quote_ready (confirm-first / slot work).

    Returns (would_handoff, turn1_qr_handoff_lift).
    """
    if not is_add_car or customer_turn != 1:
        return would_handoff, False
    _lift = compute_add_car_turn1_quote_ready_handoff_lift(
        qrs=qrs,
        last_customer_raw=last_customer_raw,
        still_needed=still_needed,
        language=language,
    )
    if _lift:
        return True, True
    if str(qrs or "").strip() != "quote_ready":
        return False, False
    return would_handoff, False


def compute_add_car_turn1_action_ready_handoff_lift(
    qrs: str,
    v4_bundle: dict[str, Any],
    merged_text: str,
    primary_vehicle_summary: str | None,
) -> bool:
    """
    Turn-1: when not quote_ready, min-core / action_ready may still lift to handoff
    (conversion path — not the quote_ready confirm-first line).
    """
    if str(qrs or "").strip() == "quote_ready":
        return False
    return evaluate_action_ready_rule(
        list(v4_bundle.get("collected_fields") or []),
        list(v4_bundle.get("still_needed_fields") or []),
        merged_text=merged_text,
        primary_vehicle_summary=primary_vehicle_summary,
    )


def next_ask_defers_instant_handoff(
    would_handoff: bool,
    next_ask: str | None,
    *,
    is_add_car: bool,
    customer_turn: int,
    turn1_qr_handoff_lift: bool,
    turn1_action_ready_lift: bool,
) -> bool:
    """
    When True, a non-empty `next_ask` draft should block immediate handoff
    (user sees one more question/confirmation first).

    Add-car turn-1 quote_ready or action_ready lifts allow handoff to win over next_ask.
    """
    if not would_handoff or not (next_ask and str(next_ask).strip()):
        return False
    if is_add_car and customer_turn == 1 and (turn1_qr_handoff_lift or turn1_action_ready_lift):
        return False
    return True
