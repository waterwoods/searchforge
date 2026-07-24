"""P4 Capability 03 — Smart Claim Start planner (Lookup + Prefill → plan)."""

from __future__ import annotations

import os

import pytest

os.environ["P4_CUSTOMER_LOOKUP_MOCK"] = "1"

from services.fiqa_api.inbox_triage.claim_prefill import build_prefill_result
from services.fiqa_api.inbox_triage.customer_lookup import lookup_customer
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    MOCK_KEY_AMBIGUOUS,
    MOCK_KEY_S1_EXISTING_ACTIVE,
    MOCK_KEY_S2_MULTI_VEHICLE,
    MOCK_KEY_S3_NO_ACTIVE,
    MOCK_KEY_S4_STALE_POLICY,
    MOCK_KEY_S5_NO_MAPPING,
    MOCK_KEY_S6_UNAVAILABLE,
    SCENARIO_KEYS,
)
from services.fiqa_api.inbox_triage.smart_claim_start import (
    MUST_HAVE_ACCIDENT_KEYS,
    assert_smart_claim_start_plan_complete,
    build_smart_claim_start_plan,
)


def _plan_for(key: str):
    lookup = lookup_customer(key)
    prefill = build_prefill_result(lookup)
    return build_smart_claim_start_plan(lookup, prefill)


def test_plan_complete_for_all_s1_s6():
    for scenario_id, key in SCENARIO_KEYS.items():
        if scenario_id == "AMBIGUOUS":
            continue
        plan = _plan_for(key)
        assert_smart_claim_start_plan_complete(plan)
        assert plan["adapter_boundary"] == "consumes_LookupResult_and_PrefillResult_only"


def test_s1_continue_active_one_input():
    plan = _plan_for(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert plan["mode"] == "CONTINUE_ACTIVE"
    assert plan["estimated_customer_inputs"] == 1
    assert plan["primary_cta_zh"] == "继续当前报案"
    assert "one_active_case" in [s["screen_id"] for s in plan["screens"]]


def test_s2_vehicle_confirm_then_five_inputs():
    plan = _plan_for(MOCK_KEY_S2_MULTI_VEHICLE)
    assert plan["mode"] == "MATCHED_CONFIRM_VEHICLE"
    assert plan["estimated_customer_inputs"] == 5
    assert plan["confirm_steps"]
    assert plan["confirm_steps"][0]["step_id"] == "confirm_vehicle"
    assert len(plan["confirm_steps"][0]["options"]) >= 2
    screen_ids = [s["screen_id"] for s in plan["screens"]]
    assert screen_ids.index("confirm_vehicle") < screen_ids.index("accident_facts")


def test_s3_matched_known_feels_known():
    plan = _plan_for(MOCK_KEY_S3_NO_ACTIVE)
    assert plan["mode"] == "MATCHED_KNOWN"
    assert plan["estimated_customer_inputs"] == 4
    chip_keys = [c["field_key"] for c in plan["known_chips"]]
    assert "customer_name" in chip_keys
    assert "vehicle" in chip_keys
    # Cap 01 S3 next_action may say confirm_vehicle; Cap 03 must trust AUTO vehicle.
    assert "confirm_vehicle" not in [s["screen_id"] for s in plan["screens"]]
    assert "今天发生了什么" in plan["headline_zh"]


def test_s4_stale_policy_confirm():
    plan = _plan_for(MOCK_KEY_S4_STALE_POLICY)
    assert plan["mode"] == "MATCHED_CONFIRM_POLICY"
    assert plan["estimated_customer_inputs"] == 5
    assert any(s["step_id"] == "confirm_policy" for s in plan["confirm_steps"])
    # No silent trust — confirm before accident.
    assert any(s["screen_id"] == "confirm_policy" for s in plan["screens"])


def test_s5_s6_graceful_blank_no_identity_wall():
    for key in (MOCK_KEY_S5_NO_MAPPING, MOCK_KEY_S6_UNAVAILABLE):
        plan = _plan_for(key)
        assert plan["mode"] == "BLANK_DEGRADE"
        assert plan["known_chips"] == []
        assert plan["estimated_customer_inputs"] == 4
        assert any(s["screen_id"] == "accident_facts" for s in plan["screens"])
        # Must Haves still required; identity not forced.
        blocking = {
            q["field_key"]
            for q in plan["questions"]
            if q["visibility"] == "VISIBLE_REQUIRED" and q["blocks_submit"]
        }
        assert set(MUST_HAVE_ACCIDENT_KEYS) <= blocking


def test_ambiguous_contact_broker():
    plan = _plan_for(MOCK_KEY_AMBIGUOUS)
    assert plan["mode"] == "CONTACT_BROKER"
    assert plan["estimated_customer_inputs"] == 1


def test_never_expose_technical_ids_in_customer_chips():
    for key in (
        MOCK_KEY_S1_EXISTING_ACTIVE,
        MOCK_KEY_S2_MULTI_VEHICLE,
        MOCK_KEY_S3_NO_ACTIVE,
        MOCK_KEY_S4_STALE_POLICY,
    ):
        plan = _plan_for(key)
        blob = str(plan["known_chips"]).lower()
        assert "openid" not in blob
        assert "person_link" not in blob
        assert "mock_veh" not in blob
        assert "pol-mock" not in blob


def test_photos_never_block_start_claim():
    plan = _plan_for(MOCK_KEY_S3_NO_ACTIVE)
    photo_q = next(q for q in plan["questions"] if q["field_key"] == "photos")
    assert photo_q["blocks_submit"] is False
    assert plan["photos_placement"] == "AFTER_SUBMIT_OPTIONAL"


def test_prefill_required():
    lookup = lookup_customer(MOCK_KEY_S3_NO_ACTIVE)
    with pytest.raises(ValueError, match="PrefillResult"):
        build_smart_claim_start_plan(lookup, None)  # type: ignore[arg-type]


def test_must_haves_block_on_new_claim_paths():
    for key in (
        MOCK_KEY_S2_MULTI_VEHICLE,
        MOCK_KEY_S3_NO_ACTIVE,
        MOCK_KEY_S4_STALE_POLICY,
        MOCK_KEY_S5_NO_MAPPING,
    ):
        plan = _plan_for(key)
        for field_key in MUST_HAVE_ACCIDENT_KEYS:
            q = next(x for x in plan["questions"] if x["field_key"] == field_key)
            assert q["visibility"] == "VISIBLE_REQUIRED"
            assert q["blocks_submit"] is True
