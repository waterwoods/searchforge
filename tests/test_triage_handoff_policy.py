"""Unit tests for triage_handoff_policy (generic + add-car turn-1 handoff timing)."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.triage_handoff_policy import (
    GENERIC_MANUAL_FOLLOWUP_HANDOFF_MIN_CUSTOMER_TURN,
    apply_add_car_turn1_quote_ready_gates_to_would_handoff,
    compute_add_car_turn1_quote_ready_handoff_lift,
    generic_should_handoff,
    next_ask_defers_instant_handoff,
)


def test_generic_should_handoff_no_manual() -> None:
    assert generic_should_handoff(1, False, "unclear") is True


def test_generic_should_handoff_turn_one_manual() -> None:
    assert generic_should_handoff(1, True, "unclear") is False


def test_generic_should_handoff_reaches_min_turn() -> None:
    assert (
        generic_should_handoff(
            GENERIC_MANUAL_FOLLOWUP_HANDOFF_MIN_CUSTOMER_TURN, True, "unclear"
        )
        is True
    )


def test_quote_ready_lift_empty_still() -> None:
    assert (
        compute_add_car_turn1_quote_ready_handoff_lift(
            qrs="quote_ready",
            last_customer_raw="VIN…",
            still_needed=[],
            language="zh",
        )
        is True
    )


def test_quote_ready_gates_forces_false_when_not_ready() -> None:
    w, lift = apply_add_car_turn1_quote_ready_gates_to_would_handoff(
        True,
        is_add_car=True,
        customer_turn=1,
        qrs="need_more",
        last_customer_raw="add car",
        still_needed=["vin"],
        language="en",
    )
    assert w is False
    assert lift is False


def test_next_ask_defers_except_turn1_lifts() -> None:
    assert (
        next_ask_defers_instant_handoff(
            True,
            "one more ask",
            is_add_car=True,
            customer_turn=1,
            turn1_qr_handoff_lift=True,
            turn1_action_ready_lift=False,
        )
        is False
    )
    assert (
        next_ask_defers_instant_handoff(
            True,
            "one more ask",
            is_add_car=True,
            customer_turn=1,
            turn1_qr_handoff_lift=False,
            turn1_action_ready_lift=True,
        )
        is False
    )
    assert (
        next_ask_defers_instant_handoff(
            True,
            "one more ask",
            is_add_car=True,
            customer_turn=1,
            turn1_qr_handoff_lift=False,
            turn1_action_ready_lift=False,
        )
        is True
    )
    assert (
        next_ask_defers_instant_handoff(
            True,
            "x",
            is_add_car=True,
            customer_turn=2,
            turn1_qr_handoff_lift=False,
            turn1_action_ready_lift=False,
        )
        is True
    )
