"""P4 Capability 02 — Claim Prefill classification (mock, LookupResult in)."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.claim_prefill import (
    FIELD_CLASS_VALUES,
    START_CLAIM_FIELD_KEYS,
    assert_prefill_result_complete,
    build_prefill_result,
    classification_map,
    founder_shorthand_map,
)
from services.fiqa_api.inbox_triage.customer_lookup import (
    FLAG_ENV,
    FORCE_UNAVAILABLE_ENV,
    lookup_customer,
    reset_customer_lookup_mock_for_tests,
)
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

_ACCIDENT = (
    "accident_time",
    "accident_location",
    "accident_story",
    "damage",
    "injury",
)


@pytest.fixture(autouse=True)
def _flag_on(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "1")
    monkeypatch.delenv(FORCE_UNAVAILABLE_ENV, raising=False)
    reset_customer_lookup_mock_for_tests()
    yield
    reset_customer_lookup_mock_for_tests()


def _prefill_for(key: str):
    return build_prefill_result(lookup_customer(key))


@pytest.mark.parametrize("scenario_id", list(SCENARIO_KEYS.keys()))
def test_every_scenario_complete_prefill_result(scenario_id):
    key = SCENARIO_KEYS[scenario_id]
    result = _prefill_for(key)
    assert_prefill_result_complete(result)
    assert len(result["fields"]) == len(START_CLAIM_FIELD_KEYS)
    for f in result["fields"]:
        assert f["classification"] in FIELD_CLASS_VALUES
        assert f["founder_shorthand"] in ("AUTO", "ASK", "UNKNOWN")


@pytest.mark.parametrize("field_key", _ACCIDENT)
def test_accident_facts_always_customer_required(field_key):
    for key in (
        MOCK_KEY_S1_EXISTING_ACTIVE,
        MOCK_KEY_S2_MULTI_VEHICLE,
        MOCK_KEY_S5_NO_MAPPING,
        MOCK_KEY_S6_UNAVAILABLE,
    ):
        cmap = classification_map(_prefill_for(key))
        assert cmap[field_key] == "CUSTOMER_REQUIRED"


def test_s1_auto_identity_and_ask_accident_only():
    result = _prefill_for(MOCK_KEY_S1_EXISTING_ACTIVE)
    cmap = classification_map(result)
    assert cmap["customer_name"] == "AUTO_PREFILL"
    assert cmap["vehicle"] == "AUTO_PREFILL"
    assert cmap["vin"] == "AUTO_PREFILL"
    assert cmap["license_plate"] == "AUTO_PREFILL"
    assert cmap["insurance_company"] == "AUTO_PREFILL"
    assert cmap["policy_number"] == "AUTO_PREFILL"
    assert cmap["phone"] == "AUTO_PREFILL"
    assert cmap["driver"] == "AUTO_PREFILL"
    assert cmap["email"] == "UNKNOWN"
    assert cmap["photos"] == "BROKER_REQUIRED"
    assert cmap["documents"] == "BROKER_REQUIRED"
    assert set(result["customer_ask_fields"]) == set(_ACCIDENT)
    # Values
    by_key = {f["field_key"]: f for f in result["fields"]}
    assert by_key["customer_name"]["value"] == "陈明"
    assert by_key["vehicle"]["value"] == "2020 Toyota Camry"
    assert by_key["vin"]["value"] == "****4352"
    assert by_key["license_plate"]["value"] == "7ABC123"


def test_s2_multi_vehicle_asks_vehicle_not_name():
    result = _prefill_for(MOCK_KEY_S2_MULTI_VEHICLE)
    cmap = classification_map(result)
    assert cmap["customer_name"] == "AUTO_PREFILL"
    assert cmap["phone"] == "AUTO_PREFILL"
    assert cmap["policy_number"] == "AUTO_PREFILL"
    assert cmap["vehicle"] == "CUSTOMER_REQUIRED"
    assert cmap["vin"] == "CUSTOMER_REQUIRED"
    assert cmap["license_plate"] == "CUSTOMER_REQUIRED"
    by_key = {f["field_key"]: f for f in result["fields"]}
    assert by_key["vehicle"]["needs_confirm"] is True
    assert "2020 Toyota Camry" in by_key["vehicle"]["candidates"]
    assert "2019 Honda CR-V" in by_key["vehicle"]["candidates"]


def test_s3_prefill_ready_no_active_case():
    result = _prefill_for(MOCK_KEY_S3_NO_ACTIVE)
    cmap = classification_map(result)
    assert cmap["customer_name"] == "AUTO_PREFILL"
    assert cmap["vehicle"] == "AUTO_PREFILL"
    assert cmap["policy_number"] == "AUTO_PREFILL"
    assert "accident_story" in result["customer_ask_fields"]


def test_s4_stale_policy_requires_confirm():
    result = _prefill_for(MOCK_KEY_S4_STALE_POLICY)
    cmap = classification_map(result)
    assert cmap["customer_name"] == "AUTO_PREFILL"
    assert cmap["vehicle"] == "AUTO_PREFILL"
    assert cmap["policy_number"] == "CUSTOMER_REQUIRED"
    assert cmap["insurance_company"] == "CUSTOMER_REQUIRED"
    assert cmap["policy"] == "CUSTOMER_REQUIRED"
    by_key = {f["field_key"]: f for f in result["fields"]}
    assert by_key["policy_number"]["needs_confirm"] is True
    assert by_key["policy_number"]["value"] == "POL-MOCK-CAMRY-EXPIRED"


def test_s5_s6_no_auto_prefill_identity():
    for key in (MOCK_KEY_S5_NO_MAPPING, MOCK_KEY_S6_UNAVAILABLE):
        result = _prefill_for(key)
        assert result["auto_prefill_count"] == 0
        cmap = classification_map(result)
        assert cmap["customer_name"] == "BROKER_REQUIRED"
        assert cmap["vehicle"] == "BROKER_REQUIRED"
        assert cmap["accident_story"] == "CUSTOMER_REQUIRED"
        assert cmap["email"] == "UNKNOWN"


def test_ambiguous_no_auto_merge_prefill():
    result = _prefill_for(MOCK_KEY_AMBIGUOUS)
    assert result["auto_prefill_count"] == 0
    assert classification_map(result)["customer_name"] == "BROKER_REQUIRED"


def test_founder_shorthand_auto_ask_unknown():
    result = _prefill_for(MOCK_KEY_S1_EXISTING_ACTIVE)
    smap = founder_shorthand_map(result)
    assert smap["customer_name"] == "AUTO"
    assert smap["accident_story"] == "ASK"
    assert smap["email"] == "UNKNOWN"
    assert smap["documents"] == "ASK"  # broker ask path, not AUTO


def test_customer_input_reduction_s1():
    """Before: all 18 fields potentially asked; after S1: only 5 accident facts."""
    result = _prefill_for(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert result["customer_required_count"] == 5
    assert result["auto_prefill_count"] >= 8


def test_engine_is_pure_no_lookup_write_side_effects():
    import services.fiqa_api.inbox_triage.claim_prefill.engine as engine

    for banned in (
        "create_customer",
        "merge_customer",
        "update_policy",
        "write_crm",
        "create_claim",
    ):
        assert not hasattr(engine, banned)


def test_flag_off_lookup_still_classifies_blank_path(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "0")
    result = build_prefill_result(lookup_customer(MOCK_KEY_S1_EXISTING_ACTIVE))
    assert result["lookup_match_status"] == "LOOKUP_UNAVAILABLE"
    assert result["auto_prefill_count"] == 0
    assert classification_map(result)["accident_time"] == "CUSTOMER_REQUIRED"
