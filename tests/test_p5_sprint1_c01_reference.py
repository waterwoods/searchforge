"""P5 Sprint 1 — C01 Customer Lookup reference implementation.

Validates Workflow → Capability → Adapter boundaries in real code.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.customer_lookup import (
    FLAG_ENV,
    FORCE_UNAVAILABLE_ENV,
    lookup_customer,
    reset_customer_lookup_mock_for_tests,
    set_directory_adapter_for_tests,
)
from services.fiqa_api.inbox_triage.customer_lookup.adapters import (
    MockCustomerDirectoryAdapter,
)
from services.fiqa_api.inbox_triage.customer_lookup.contract import (
    assert_lookup_result_complete,
    empty_lookup_result,
)
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    MOCK_KEY_S1_EXISTING_ACTIVE,
    MOCK_KEY_S2_MULTI_VEHICLE,
    MOCK_KEY_S4_STALE_POLICY,
    MOCK_KEY_S5_NO_MAPPING,
    MOCK_KEY_S6_UNAVAILABLE,
    SCENARIO_KEYS,
)
from services.fiqa_api.inbox_triage.workflow_v2 import (
    enter_claim_with_lookup,
    simulate_main_chain_from_lookup,
)
from services.fiqa_api.inbox_triage.workflow_v2.c01_lookup_entry import decide_lookup_entry

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FILE = ROOT / "services/fiqa_api/inbox_triage/workflow_v2/c01_lookup_entry.py"
FACADE_FILE = ROOT / "services/fiqa_api/inbox_triage/customer_lookup/facade.py"


@pytest.fixture(autouse=True)
def _flag_on(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "1")
    monkeypatch.delenv(FORCE_UNAVAILABLE_ENV, raising=False)
    reset_customer_lookup_mock_for_tests()
    yield
    reset_customer_lookup_mock_for_tests()


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    return mods


# ---------------------------------------------------------------------------
# Architecture boundaries
# ---------------------------------------------------------------------------


def test_workflow_never_imports_adapter_or_mock_directory():
    mods = _imported_modules(WORKFLOW_FILE)
    banned_substrings = (
        "customer_lookup.adapters",
        "customer_lookup.mock_directory",
        "mock_adapter",
        "ezlynx",
        "ams",
        "crm",
    )
    blob = " ".join(sorted(mods)).lower()
    for banned in banned_substrings:
        assert banned not in blob, f"Workflow imported forbidden module matching {banned}: {mods}"


def test_facade_does_not_import_fixture_tables_directly():
    """Capability calls Adapter; fixture rows stay adapter-owned."""
    mods = _imported_modules(FACADE_FILE)
    # Allowed: reset helper + adapters package. Not get_fixture / SCENARIO_KEYS usage via mock_directory APIs beyond reset.
    assert "services.fiqa_api.inbox_triage.customer_lookup.adapters" in mods
    src = FACADE_FILE.read_text(encoding="utf-8")
    assert "get_fixture" not in src
    assert "SCENARIO_KEYS" not in src
    assert "MOCK_KEY_" not in src


def test_adapter_swap_changes_datasource_not_workflow_contract():
    class FakeAmsAdapter:
        adapter_id = "fake_ams"

        def lookup_by_person_link(self, person_link_key: str):
            result = empty_lookup_result(
                match_status="MATCH_FOUND",
                lookup_confidence="HIGH",
                next_action="confirm_vehicle",
                reason_codes=["fake_ams_hit"],
            )
            result["customer"] = {
                "display_name": "AMS客户",
                "phone_last4": "0000",
                "broker_customer_ref": "ams_1",
            }
            result["vehicles"] = [
                {
                    "vehicle_ref": "ams_v1",
                    "year": "2021",
                    "make": "Toyota",
                    "model": "Camry",
                    "is_primary": True,
                }
            ]
            result["prefill"] = {
                "customer_name": "AMS客户",
                "primary_vehicle_summary": "2021 Toyota Camry",
            }
            result["lookup_source"] = "fake_ams"
            return result

    set_directory_adapter_for_tests(FakeAmsAdapter())
    result, decision = enter_claim_with_lookup(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert_lookup_result_complete(result)
    assert result["lookup_source"] == "fake_ams"
    assert result["customer"]["display_name"] == "AMS客户"
    assert decision.journey_mode == "confirm_vehicle"
    assert decision.blocks_accident_report is False


def test_mock_adapter_id_is_not_required_by_workflow():
    result, decision = enter_claim_with_lookup(MOCK_KEY_S2_MULTI_VEHICLE)
    assert decision.journey_mode == "confirm_vehicle"
    assert decision.vehicle_count == 2
    # Workflow decision dict has no adapter class name.
    assert "MockCustomerDirectory" not in str(decision.to_dict())
    assert isinstance(MockCustomerDirectoryAdapter().adapter_id, str)


# ---------------------------------------------------------------------------
# Graceful degrade (Workflow branches)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key,expected_mode,blocks,manual",
    [
        (MOCK_KEY_S1_EXISTING_ACTIVE, "continue_active", False, False),
        (MOCK_KEY_S2_MULTI_VEHICLE, "confirm_vehicle", False, True),
        (MOCK_KEY_S4_STALE_POLICY, "confirm_stale_policy", False, True),
        (MOCK_KEY_S5_NO_MAPPING, "blank_claim", False, True),
        (MOCK_KEY_S6_UNAVAILABLE, "blank_claim", False, True),
    ],
)
def test_graceful_degrade_never_blocks_accident_except_relogin(key, expected_mode, blocks, manual):
    result, decision = enter_claim_with_lookup(key)
    assert decision.journey_mode == expected_mode
    assert decision.blocks_accident_report is blocks
    assert decision.allows_manual_claim is manual
    assert_lookup_result_complete(result)


def test_flag_off_is_pilot_blank_workflow(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "0")
    result, decision = enter_claim_with_lookup(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert result["match_status"] == "LOOKUP_UNAVAILABLE"
    assert decision.journey_mode == "blank_claim"
    assert decision.blocks_accident_report is False
    assert decision.allows_manual_claim is True


def test_multi_vehicle_requires_customer_select():
    result, decision = enter_claim_with_lookup(MOCK_KEY_S2_MULTI_VEHICLE)
    assert decision.vehicle_count == 2
    assert decision.customer_next_screen == "哪辆车出险？"
    steps = simulate_main_chain_from_lookup(result)
    cont = next(s for s in steps if s["step"] == "customer_continue")
    assert cont.get("vehicle_selection_required") is True


# ---------------------------------------------------------------------------
# Main chain still complete for every scenario
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario_id", list(SCENARIO_KEYS.keys()))
def test_reference_main_chain_complete(scenario_id):
    key = SCENARIO_KEYS[scenario_id]
    result = lookup_customer(key)
    steps = simulate_main_chain_from_lookup(result)
    names = [s["step"] for s in steps]
    assert names == [
        "mini_program",
        "lookup",
        "broker_header",
        "workbench",
        "request_more",
        "customer_continue",
        "review",
        "close",
    ]
    assert all(s.get("ok") is True for s in steps)
    assert steps[1].get("via") == "capability_c01"
    assert steps[-1].get("lookup_mutated_crm") is False


def test_decide_lookup_entry_is_pure_contract():
    result = lookup_customer(MOCK_KEY_S6_UNAVAILABLE)
    decision = decide_lookup_entry(result)
    assert decision.journey_mode == "blank_claim"
    assert decision.primary_cta == "开始报案"
