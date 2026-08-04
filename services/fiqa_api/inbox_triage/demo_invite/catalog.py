"""Approved Demo Invite mock-scenario catalog (Chen known-customer demo).

Reuses C01 mock fixtures only. Not a Customers table. Not AMS/CRM.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypedDict

from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    MOCK_KEY_GUIDED_INTAKE_PHONE,
    MOCK_KEY_LANGGRAPH_PHONE,
    MOCK_KEY_S2_MULTI_VEHICLE,
    MOCK_KEY_S3_NO_ACTIVE,
    MOCK_KEY_S4_STALE_POLICY,
    MOCK_KEY_STAGE2_PHONE,
    get_fixture,
)

DEMO_NAME = "chen_known_customer_demo"

# Short aliases accepted by C01 / smart_claim_start resolver.
_SCENARIO_CHEN_CAMRY = "S3"
_SCENARIO_LI_MULTI = "S2"
_SCENARIO_WANG_STALE = "S4"
_SCENARIO_CHEN_STAGE2_PHONE = "S3_STAGE2_PHONE"
_SCENARIO_CHEN_LANGGRAPH_PHONE = "S3_LANGGRAPH_PHONE"
_SCENARIO_CHEN_GUIDED_INTAKE_PHONE = "S3_GUIDED_INTAKE_PHONE"


class DemoScenarioEntry(TypedDict):
    scenario_id: str
    mock_scenario: str
    mock_person_link_key: str
    label: str
    customer_display_name: str
    vehicle_summary: str
    demo_name: str
    is_demo: bool


# Allowlisted catalog — only these may be issued as Demo Invites.
# Optional runtime key `isolated_identity` (bool) opts a scenario into a QA-only
# Active Case namespace so Stage 1 cases on the real wx link stay untouched.
APPROVED_DEMO_SCENARIOS: dict[str, DemoScenarioEntry] = {
    "chen_camry": {
        "scenario_id": "chen_camry",
        "mock_scenario": _SCENARIO_CHEN_CAMRY,
        "mock_person_link_key": MOCK_KEY_S3_NO_ACTIVE,
        "label": "陈明 · 2020 Toyota Camry",
        "customer_display_name": "陈明",
        "vehicle_summary": "2020 Toyota Camry",
        "demo_name": DEMO_NAME,
        "is_demo": True,
    },
    "chen_camry_stage2_phone": {
        "scenario_id": "chen_camry_stage2_phone",
        "mock_scenario": _SCENARIO_CHEN_STAGE2_PHONE,
        "mock_person_link_key": MOCK_KEY_STAGE2_PHONE,
        "label": "陈明 · Stage2 Phone QA (isolated)",
        "customer_display_name": "陈明",
        "vehicle_summary": "2020 Toyota Camry",
        "demo_name": DEMO_NAME,
        "is_demo": True,
        "isolated_identity": True,  # type: ignore[typeddict-unknown-key]
    },
    # LangGraph Final Phone QA — MUST NOT reuse chen_camry_stage2_phone.
    # Same phone OpenID + stage2 scenario resumes Stage 2 Active Case (Santa Ana).
    "langgraph_final_phone_qa": {
        "scenario_id": "langgraph_final_phone_qa",
        "mock_scenario": _SCENARIO_CHEN_LANGGRAPH_PHONE,
        "mock_person_link_key": MOCK_KEY_LANGGRAPH_PHONE,
        "label": "陈明 · LangGraph Final Phone QA (isolated)",
        "customer_display_name": "陈明",
        "vehicle_summary": "2020 Toyota Camry",
        "demo_name": DEMO_NAME,
        "is_demo": True,
        "isolated_identity": True,  # type: ignore[typeddict-unknown-key]
    },
    # Guided Intake clean phone QA — MUST NOT reuse langgraph_final_phone_qa.
    # Founder phone already has Active Case case_f31c3604bb70 (CLM-0042,
    # Santa Ana / 昨天下午1点) under that isolated namespace.
    "guided_intake_clean_phone_qa": {
        "scenario_id": "guided_intake_clean_phone_qa",
        "mock_scenario": _SCENARIO_CHEN_GUIDED_INTAKE_PHONE,
        "mock_person_link_key": MOCK_KEY_GUIDED_INTAKE_PHONE,
        "label": "陈明 · Guided Intake Clean Phone QA (isolated)",
        "customer_display_name": "陈明",
        "vehicle_summary": "2020 Toyota Camry",
        "demo_name": DEMO_NAME,
        "is_demo": True,
        "isolated_identity": True,  # type: ignore[typeddict-unknown-key]
    },
    "li_multi": {
        "scenario_id": "li_multi",
        "mock_scenario": _SCENARIO_LI_MULTI,
        "mock_person_link_key": MOCK_KEY_S2_MULTI_VEHICLE,
        "label": "李娜 · Camry + CR-V (选车)",
        "customer_display_name": "李娜",
        "vehicle_summary": "2020 Toyota Camry / 2019 Honda CR-V",
        "demo_name": DEMO_NAME,
        "is_demo": True,
    },
    "wang_stale": {
        "scenario_id": "wang_stale",
        "mock_scenario": _SCENARIO_WANG_STALE,
        "mock_person_link_key": MOCK_KEY_S4_STALE_POLICY,
        "label": "王强 · 过期保单 Camry",
        "customer_display_name": "王强",
        "vehicle_summary": "2020 Toyota Camry",
        "demo_name": DEMO_NAME,
        "is_demo": True,
    },
}


def list_approved_scenarios() -> list[dict[str, Any]]:
    """Broker-safe catalog rows (no internal keys beyond demo labels)."""
    rows: list[dict[str, Any]] = []
    for entry in APPROVED_DEMO_SCENARIOS.values():
        rows.append(
            {
                "scenario_id": entry["scenario_id"],
                "label": entry["label"],
                "customer_display_name": entry["customer_display_name"],
                "vehicle_summary": entry["vehicle_summary"],
                "demo_name": entry["demo_name"],
                "is_demo": True,
                "mock_scenario": entry["mock_scenario"],
            }
        )
    return rows


def get_approved_scenario(scenario_id: str | None) -> DemoScenarioEntry | None:
    raw = str(scenario_id or "").strip()
    if not raw:
        return None
    entry = APPROVED_DEMO_SCENARIOS.get(raw)
    if entry is None:
        # Also accept mock_scenario short ids when they uniquely map.
        for candidate in APPROVED_DEMO_SCENARIOS.values():
            if candidate["mock_scenario"].upper() == raw.upper():
                return deepcopy(candidate)
        return None
    return deepcopy(entry)


def is_scenario_allowlisted(scenario_id: str | None) -> bool:
    return get_approved_scenario(scenario_id) is not None


def fixture_preview(scenario_id: str) -> dict[str, Any] | None:
    """Optional LookupResult peek for Founder QA (never mutates fixtures)."""
    entry = get_approved_scenario(scenario_id)
    if entry is None:
        return None
    row = get_fixture(entry["mock_person_link_key"])
    if row is None:
        return None
    customer = row.get("customer") if isinstance(row.get("customer"), dict) else {}
    return {
        "scenario_id": entry["scenario_id"],
        "customer_display_name": customer.get("display_name") or entry["customer_display_name"],
        "vehicle_summary": entry["vehicle_summary"],
        "match_status": row.get("match_status"),
        "next_action": row.get("next_action"),
        "is_demo": True,
        "demo_name": DEMO_NAME,
    }
