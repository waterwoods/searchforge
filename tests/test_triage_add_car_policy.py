"""Unit tests for add-car policy extraction (handoff gates + structural helpers)."""

from services.fiqa_api.inbox_triage.triage_add_car_policy import (
    AddCarHandoffReadinessContext,
    add_car_enough_for_handoff,
    apply_add_car_handoff_readiness_gates,
)


def test_add_car_enough_for_handoff_requires_all_pilot_slots():
    assert not add_car_enough_for_handoff(
        {"vin": True, "zip": True, "delivery": True, "driver": False}
    )
    assert add_car_enough_for_handoff(
        {"vin": True, "zip": True, "delivery": True, "driver": True}
    )


def test_handoff_readiness_contact_gate_suppresses_when_quote_ready_and_turn_high():
    # v4_bundle=None → skip in-bundle V5 block; still applies §4.2 contact gate.
    # quote_ready, turn 4, name still needed, no post-submit / on-record contact → no handoff
    ctx = AddCarHandoffReadinessContext(
        handoff=True,
        is_add_car=True,
        for_append=False,
        customer_turn=4,
        qrs="quote_ready",
        still_needed=["name"],
        v4_bundle=None,
        merged_for_add_car_extraction="x",
        primary_vehicle_summary=None,
        reply_truth_context={},
        variant="A",
    )
    assert apply_add_car_handoff_readiness_gates(ctx) is False

    # same but post-submitted at → handoff can stay true
    ctx2 = AddCarHandoffReadinessContext(
        handoff=True,
        is_add_car=True,
        for_append=False,
        customer_turn=4,
        qrs="quote_ready",
        still_needed=["name"],
        v4_bundle=None,
        merged_for_add_car_extraction="x",
        primary_vehicle_summary=None,
        reply_truth_context={"formal_submitted_at": "2026-01-01"},
        variant="A",
    )
    assert apply_add_car_handoff_readiness_gates(ctx2) is True
