"""In-memory mock customer directory for P4 Capability 01.

Keyed by person_link_key only. Read-only fixtures — never a CRM SoR.
Swappable later with an AMS adapter that returns the same LookupResult shape.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult

# Stable mock keys (not derived from OpenID). QA / sim only.
MOCK_KEY_S1_EXISTING_ACTIVE = "wx_mock_cap01_s1_existing_active"
MOCK_KEY_S2_MULTI_VEHICLE = "wx_mock_cap01_s2_multi_vehicle"
MOCK_KEY_S3_NO_ACTIVE = "wx_mock_cap01_s3_no_active"
MOCK_KEY_S4_STALE_POLICY = "wx_mock_cap01_s4_stale_policy"
MOCK_KEY_S5_NO_MAPPING = "wx_mock_cap01_s5_identity_no_mapping"
MOCK_KEY_S6_UNAVAILABLE = "wx_mock_cap01_s6_lookup_unavailable"
MOCK_KEY_AMBIGUOUS = "wx_mock_cap01_ambiguous"
# Stage 2 phone QA — same 陈明/Camry/Mercury presentation, unique identity key.
MOCK_KEY_STAGE2_PHONE = "wx_mock_cap01_stage2_phone"
# LangGraph Final Phone QA — same presentation, separate mock key + isolated scenario.
MOCK_KEY_LANGGRAPH_PHONE = "wx_mock_cap01_langgraph_phone"

SCENARIO_KEYS: dict[str, str] = {
    "S1_existing_active": MOCK_KEY_S1_EXISTING_ACTIVE,
    "S2_multi_vehicle": MOCK_KEY_S2_MULTI_VEHICLE,
    "S3_no_active": MOCK_KEY_S3_NO_ACTIVE,
    "S4_stale_policy": MOCK_KEY_S4_STALE_POLICY,
    "S5_no_mapping": MOCK_KEY_S5_NO_MAPPING,
    "S6_unavailable": MOCK_KEY_S6_UNAVAILABLE,
    "AMBIGUOUS": MOCK_KEY_AMBIGUOUS,
    "S3_STAGE2_PHONE": MOCK_KEY_STAGE2_PHONE,
    "S3_LANGGRAPH_PHONE": MOCK_KEY_LANGGRAPH_PHONE,
}


def _camry_vehicle(*, primary: bool = True) -> dict[str, Any]:
    return {
        "vehicle_ref": "mock_veh_camry",
        "year": "2020",
        "make": "Toyota",
        "model": "Camry",
        "vin_last4": "4352",
        "license_plate": "7ABC123",
        "is_primary": primary,
    }


def _crv_vehicle() -> dict[str, Any]:
    return {
        "vehicle_ref": "mock_veh_crv",
        "year": "2019",
        "make": "Honda",
        "model": "CR-V",
        "vin_last4": "9910",
        "license_plate": "8XYZ456",
        "is_primary": False,
    }


def _customer_chen() -> dict[str, Any]:
    return {
        "display_name": "陈明",
        "phone_last4": "1234",
        "phone_e164_mock": "+14155551234",
        "broker_customer_ref": "mock_cust_camry",
    }


def _policy_active() -> dict[str, Any]:
    return {
        "policy_ref": "POL-MOCK-CAMRY-001",
        "carrier_display": "Mercury",
        "status": "active",
        "freshness": "fresh",
        "effective_end": "2027-06-01",
    }


def _policy_expired() -> dict[str, Any]:
    return {
        "policy_ref": "POL-MOCK-CAMRY-EXPIRED",
        "carrier_display": "Mercury",
        "status": "expired",
        "freshness": "stale",
        "effective_end": "2025-01-01",
    }


def _prefill_chen_camry(*, policy_ref: str = "POL-MOCK-CAMRY-001") -> dict[str, Any]:
    return {
        "customer_name": "陈明",
        "customer_phone": "+14155551234",
        "primary_vehicle_summary": "2020 Toyota Camry",
        "policy_number": policy_ref,
    }


def build_mock_directory() -> dict[str, LookupResult]:
    """Six Founder scenarios + AMBIGUOUS_MATCH fixture."""
    return {
        MOCK_KEY_S1_EXISTING_ACTIVE: {
            "match_status": "MATCH_FOUND",
            "lookup_confidence": "HIGH",
            "customer": _customer_chen(),
            "policy": _policy_active(),
            "vehicles": [_camry_vehicle()],
            "active_case": {
                "case_id": "case_mock_cap01_s1",
                "resume_available": True,
            },
            "prefill": _prefill_chen_camry(),
            "next_action": "continue_active_case",
            "reason_codes": ["mock_existing_customer", "mock_active_case"],
            "lookup_source": "mock",
        },
        MOCK_KEY_S2_MULTI_VEHICLE: {
            "match_status": "MATCH_FOUND",
            "lookup_confidence": "MEDIUM",
            "customer": {
                "display_name": "李娜",
                "phone_last4": "5678",
                "phone_e164_mock": "+14155555678",
                "broker_customer_ref": "mock_cust_multi",
            },
            "policy": {
                "policy_ref": "POL-MOCK-MULTI-001",
                "carrier_display": "Mercury",
                "status": "active",
                "freshness": "fresh",
                "effective_end": "2027-03-15",
            },
            "vehicles": [_camry_vehicle(primary=True), _crv_vehicle()],
            "active_case": None,
            "prefill": {
                "customer_name": "李娜",
                "customer_phone": "+14155555678",
                "policy_number": "POL-MOCK-MULTI-001",
                # No primary_vehicle_summary — must confirm
            },
            "next_action": "confirm_vehicle",
            "reason_codes": ["mock_existing_customer", "mock_multi_vehicle"],
            "lookup_source": "mock",
        },
        MOCK_KEY_S3_NO_ACTIVE: {
            "match_status": "MATCH_FOUND",
            "lookup_confidence": "HIGH",
            "customer": _customer_chen(),
            "policy": _policy_active(),
            "vehicles": [_camry_vehicle()],
            "active_case": None,
            "prefill": _prefill_chen_camry(),
            "next_action": "confirm_vehicle",
            "reason_codes": ["mock_existing_customer", "mock_no_active_case"],
            "lookup_source": "mock",
        },
        MOCK_KEY_STAGE2_PHONE: {
            "match_status": "MATCH_FOUND",
            "lookup_confidence": "HIGH",
            "customer": {
                "display_name": "陈明",
                "phone_last4": "1234",
                "phone_e164_mock": "+14155551234",
                "broker_customer_ref": "mock_cust_stage2_phone",
            },
            "policy": {
                "policy_ref": "POL-MOCK-STAGE2-CAMRY-001",
                "carrier_display": "Mercury",
                "status": "active",
                "freshness": "fresh",
                "effective_end": "2027-06-01",
            },
            "vehicles": [
                {
                    "vehicle_ref": "mock_veh_stage2_camry",
                    "year": "2020",
                    "make": "Toyota",
                    "model": "Camry",
                    "vin_last4": "4352",
                    "license_plate": "7ABC123",
                    "is_primary": True,
                }
            ],
            "active_case": None,
            "prefill": _prefill_chen_camry(policy_ref="POL-MOCK-STAGE2-CAMRY-001"),
            "next_action": "confirm_vehicle",
            "reason_codes": [
                "mock_existing_customer",
                "mock_no_active_case",
                "mock_stage2_phone_isolated",
            ],
            "lookup_source": "mock",
        },
        MOCK_KEY_LANGGRAPH_PHONE: {
            "match_status": "MATCH_FOUND",
            "lookup_confidence": "HIGH",
            "customer": {
                "display_name": "陈明",
                "phone_last4": "1234",
                "phone_e164_mock": "+14155551234",
                "broker_customer_ref": "mock_cust_langgraph_phone",
            },
            "policy": {
                "policy_ref": "POL-MOCK-LANGGRAPH-CAMRY-001",
                "carrier_display": "Mercury",
                "status": "active",
                "freshness": "fresh",
                "effective_end": "2027-06-01",
            },
            "vehicles": [
                {
                    "vehicle_ref": "mock_veh_langgraph_camry",
                    "year": "2020",
                    "make": "Toyota",
                    "model": "Camry",
                    "vin_last4": "4352",
                    "license_plate": "7ABC123",
                    "is_primary": True,
                }
            ],
            "active_case": None,
            "prefill": _prefill_chen_camry(policy_ref="POL-MOCK-LANGGRAPH-CAMRY-001"),
            "next_action": "confirm_vehicle",
            "reason_codes": [
                "mock_existing_customer",
                "mock_no_active_case",
                "mock_langgraph_final_phone_isolated",
            ],
            "lookup_source": "mock",
        },
        MOCK_KEY_S4_STALE_POLICY: {
            "match_status": "STALE_POLICY",
            "lookup_confidence": "MEDIUM",
            "customer": {
                "display_name": "王强",
                "phone_last4": "9999",
                "phone_e164_mock": "+14155559999",
                "broker_customer_ref": "mock_cust_stale",
            },
            "policy": _policy_expired(),
            "vehicles": [_camry_vehicle()],
            "active_case": None,
            "prefill": {
                "customer_name": "王强",
                "customer_phone": "+14155559999",
                "primary_vehicle_summary": "2020 Toyota Camry",
                "policy_number": "POL-MOCK-CAMRY-EXPIRED",
            },
            "next_action": "confirm_stale_policy",
            "reason_codes": ["mock_existing_customer", "mock_policy_expired"],
            "lookup_source": "mock",
        },
        # S5: key exists as identity shape but deliberately absent from directory
        # (resolved as NOT_FOUND by facade — no row here).
        MOCK_KEY_AMBIGUOUS: {
            "match_status": "AMBIGUOUS_MATCH",
            "lookup_confidence": "LOW",
            "customer": None,
            "policy": None,
            "vehicles": [],
            "active_case": None,
            "prefill": {},
            "next_action": "contact_broker",
            "reason_codes": ["mock_ambiguous_person_match"],
            "lookup_source": "mock",
        },
    }


_DIRECTORY: dict[str, LookupResult] | None = None


def get_mock_directory() -> dict[str, LookupResult]:
    global _DIRECTORY
    if _DIRECTORY is None:
        _DIRECTORY = build_mock_directory()
    return _DIRECTORY


def reset_mock_directory_for_tests() -> None:
    global _DIRECTORY
    _DIRECTORY = None


def get_fixture(person_link_key: str) -> LookupResult | None:
    row = get_mock_directory().get(str(person_link_key or "").strip())
    if row is None:
        return None
    return deepcopy(row)


def list_scenario_keys() -> dict[str, str]:
    return dict(SCENARIO_KEYS)
