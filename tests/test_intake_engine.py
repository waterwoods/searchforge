"""State consistency for Intake Engine (additive fields on triage result)."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.add_car_field_contract import quote_ready_matches_still_needed
from services.fiqa_api.inbox_triage.intake_engine import (
    assert_state_consistency,
    compute_fields,
    compute_next_step,
    compute_quote_state,
    run_intake_engine,
)
from services.fiqa_api.inbox_triage.triage import triage_conversation


def test_empty_input_in_add_car_thread():
    """Minimal follow-up in an add-car lane: need_more, gaps remain, collecting."""
    turns = [{"role": "customer", "text": "I want to add a car to my policy"}]
    r = triage_conversation("hi", turns, client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    assert r.get("quote_ready_status") == "need_more"
    assert r.get("still_needed_fields")
    assert r.get("case_lifecycle") == "collecting"


def test_vin_only_almost_ready():
    r = triage_conversation("VIN is 1HGBH41JXMN109186", [], client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    assert r.get("quote_ready_status") == "almost_ready"
    coll = [str(x).lower() for x in (r.get("collected_fields") or [])]
    assert "vin" in coll


def test_vin_zip_driver_delivery_quote_ready():
    msg = (
        "VIN 1HGBH41JXMN109186 zip 94043 delivery 2026-05-01 primary driver is me "
        "2020 Honda Civic"
    )
    r = triage_conversation(msg, [], client_id="chen_kui")
    assert r.get("quote_ready_status") == "quote_ready"
    assert quote_ready_matches_still_needed(
        str(r.get("quote_ready_status") or ""),
        r.get("still_needed_fields"),
    )


def test_partial_merge_two_turns():
    t1 = triage_conversation("I want to add a car", [], client_id="chen_kui")
    assert t1.get("quote_ready_status") == "need_more"
    turns = [{"role": "customer", "text": "I want to add a car"}]
    t2 = triage_conversation("VIN is 1HGBH41JXMN109186", turns, client_id="chen_kui")
    assert t2.get("quote_ready_status") in ("almost_ready", "quote_ready")
    coll = {str(x).lower() for x in (t2.get("collected_fields") or [])}
    assert "vin" in coll


def test_persisted_continuity_ok_ack():
    ctx = {
        "persisted_collected_fields": ["vin"],
    }
    r = triage_conversation(
        "ok",
        [{"role": "customer", "text": "I need to add a vehicle"}],
        client_id="chen_kui",
        reply_truth_context=ctx,
    )
    assert r.get("service_type") == "add_car"
    assert r.get("quote_ready_status") in ("almost_ready", "quote_ready", "need_more")
    assert_state_consistency(r)


def test_state_invariant_all_samples():
    samples = [
        triage_conversation("hi", [{"role": "customer", "text": "add a car"}], client_id="chen_kui"),
        triage_conversation("VIN 1HGBH41JXMN109186", [], client_id="chen_kui"),
        triage_conversation(
            "VIN 1HGBH41JXMN109186 zip 94043 delivery May 1 2026 driver is me",
            [],
            client_id="chen_kui",
        ),
    ]
    for r in samples:
        if r.get("service_type") == "add_car":
            assert quote_ready_matches_still_needed(
                str(r.get("quote_ready_status") or ""),
                r.get("still_needed_fields"),
            )


def test_compute_quote_state_unit():
    assert compute_quote_state([], ["vin", "zip"]) == "need_more"
    assert compute_quote_state(["vin"], ["zip", "delivery_date"]) == "almost_ready"
    assert compute_quote_state(["vin", "zip", "delivery_date", "primary_driver"], []) == "quote_ready"


def test_compute_next_step_empty():
    assert compute_next_step([]) == ""
    assert "请提供" in compute_next_step(["zip"], language="zh")


def test_compute_fields_passthrough():
    r = {"service_type": "general_inquiry", "collected_fields": ["a"], "still_needed_fields": []}
    c, s = compute_fields(r, None)
    assert c == ["a"]
    assert s == []


def test_run_intake_engine_synthetic_add_car():
    r = {
        "service_type": "add_car",
        "collected_fields": ["vin", "zip", "delivery_date", "primary_driver"],
        "still_needed_fields": [],
        "handoff_ready": False,
        "triage_mode": "greenfield",
        "quote_ready_status": "quote_ready",
    }
    out = run_intake_engine(r, None)
    assert out["case_lifecycle"] in ("collecting", "almost_ready", "ready_for_handoff", "submitted")
    assert "intake_next_best_ask" in out
