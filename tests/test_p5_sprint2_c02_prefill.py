"""P5 Sprint 2 — C02 Claim Prefill reference implementation.

Validates Workflow → Capability → Adapter boundaries. No C03. No AMS.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.claim_prefill import (
    START_CLAIM_FIELD_KEYS,
    assert_prefill_result_complete,
    classification_map,
    empty_prefill_result,
    prefill_from_lookup,
    reset_claim_prefill_for_tests,
    set_classifier_adapter_for_tests,
)
from services.fiqa_api.inbox_triage.claim_prefill.adapters import (
    MockPrefillClassifierAdapter,
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
from services.fiqa_api.inbox_triage.workflow_v2 import (
    enter_claim_with_prefill,
    simulate_prefill_chain,
)
from services.fiqa_api.inbox_triage.workflow_v2.c02_prefill_entry import (
    decide_prefill_entry,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FILE = ROOT / "services/fiqa_api/inbox_triage/workflow_v2/c02_prefill_entry.py"
FACADE_FILE = ROOT / "services/fiqa_api/inbox_triage/claim_prefill/facade.py"

_ACCIDENT = (
    "accident_time",
    "accident_location",
    "accident_story",
    "damage",
    "injury",
)


@pytest.fixture(autouse=True)
def _flags(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "1")
    monkeypatch.delenv(FORCE_UNAVAILABLE_ENV, raising=False)
    reset_customer_lookup_mock_for_tests()
    reset_claim_prefill_for_tests()
    yield
    reset_customer_lookup_mock_for_tests()
    reset_claim_prefill_for_tests()


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


def test_workflow_never_imports_adapter_engine_or_c03():
    mods = _imported_modules(WORKFLOW_FILE)
    blob = " ".join(sorted(mods)).lower()
    banned = (
        "claim_prefill.adapters",
        "claim_prefill.engine",
        "mock_adapter",
        "smart_claim_start",
        "ezlynx",
        "ams",
        "crm",
        "mock_directory",
    )
    for banned_item in banned:
        assert banned_item not in blob, f"Workflow imported forbidden {banned_item}: {mods}"


def test_facade_does_not_import_smart_claim_start():
    mods = _imported_modules(FACADE_FILE)
    blob = " ".join(sorted(mods)).lower()
    assert "smart_claim_start" not in blob
    assert "services.fiqa_api.inbox_triage.claim_prefill.adapters" in mods
    src = FACADE_FILE.read_text(encoding="utf-8")
    assert "MOCK_KEY_" not in src


def test_adapter_swap_changes_classification_not_workflow_contract():
    class FakeRicherAdapter:
        adapter_id = "fake_richer_prefill"

        def classify(self, lookup):
            # Still complete PrefillResult — promote email when adapter has data.
            base = MockPrefillClassifierAdapter().classify(lookup)
            fields = []
            for f in base["fields"]:
                row = dict(f)
                if row["field_key"] == "email" and base["auto_prefill_count"] > 0:
                    row["classification"] = "AUTO_PREFILL"
                    row["founder_shorthand"] = "AUTO"
                    row["value"] = "known@example.com"
                    row["reason_code"] = "fake_richer_email"
                fields.append(row)
            auto = [f["field_key"] for f in fields if f["classification"] == "AUTO_PREFILL"]
            cust = [
                f["field_key"] for f in fields if f["classification"] == "CUSTOMER_REQUIRED"
            ]
            broker = [
                f["field_key"] for f in fields if f["classification"] == "BROKER_REQUIRED"
            ]
            unknown = [f["field_key"] for f in fields if f["classification"] == "UNKNOWN"]
            out = dict(base)
            out["fields"] = fields
            out["auto_fields"] = auto
            out["customer_ask_fields"] = cust
            out["auto_prefill_count"] = len(auto)
            out["customer_required_count"] = len(cust)
            out["broker_required_count"] = len(broker)
            out["unknown_count"] = len(unknown)
            out["prefill_source"] = "fake_richer"
            return out

    set_classifier_adapter_for_tests(FakeRicherAdapter())
    lookup, prefill, decision = enter_claim_with_prefill(MOCK_KEY_S3_NO_ACTIVE)
    assert_prefill_result_complete(prefill)
    assert prefill["prefill_source"] == "fake_richer"
    assert classification_map(prefill)["email"] == "AUTO_PREFILL"
    assert decision.blocks_accident_report is False
    assert decision.owns_start_claim_screens is False
    assert "FakeRicher" not in str(decision.to_dict())


def test_mock_adapter_id_not_required_by_workflow():
    _lookup, prefill, decision = enter_claim_with_prefill(MOCK_KEY_S2_MULTI_VEHICLE)
    assert decision.needs_vehicle_confirm is True
    assert "MockPrefill" not in str(decision.to_dict())
    assert isinstance(MockPrefillClassifierAdapter().adapter_id, str)
    assert_prefill_result_complete(prefill)


# ---------------------------------------------------------------------------
# S1–S6 matrix + degrade
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario_id", list(SCENARIO_KEYS.keys()))
def test_every_scenario_complete_via_workflow(scenario_id):
    key = SCENARIO_KEYS[scenario_id]
    lookup, prefill, decision = enter_claim_with_prefill(key)
    assert_prefill_result_complete(prefill)
    assert len(prefill["fields"]) == len(START_CLAIM_FIELD_KEYS)
    assert decision.blocks_accident_report is False
    steps = simulate_prefill_chain(lookup, prefill)
    assert [s["step"] for s in steps] == [
        "mini_program",
        "lookup",
        "prefill",
        "start_claim_presentation",
        "close_boundary",
    ]
    assert all(s.get("ok") is True for s in steps)
    assert steps[2].get("via") == "capability_c02"
    assert steps[3].get("deferred_to") == "C03"
    assert steps[-1].get("prefill_wrote_crm") is False


def test_s1_matched_auto_identity_ask_accident_only():
    _lookup, prefill, decision = enter_claim_with_prefill(MOCK_KEY_S1_EXISTING_ACTIVE)
    cmap = classification_map(prefill)
    assert cmap["customer_name"] == "AUTO_PREFILL"
    assert cmap["vehicle"] == "AUTO_PREFILL"
    assert set(prefill["customer_ask_fields"]) == set(_ACCIDENT)
    assert decision.auto_prefill_count >= 8
    assert decision.typing_reduction_removed >= 10
    assert "陈明" in decision.auto_chip_values


def test_s2_multi_vehicle_confirm_not_silent_auto():
    _lookup, prefill, decision = enter_claim_with_prefill(MOCK_KEY_S2_MULTI_VEHICLE)
    cmap = classification_map(prefill)
    assert cmap["customer_name"] == "AUTO_PREFILL"
    assert cmap["vehicle"] == "CUSTOMER_REQUIRED"
    assert decision.needs_vehicle_confirm is True


def test_s3_prefill_ready():
    _lookup, prefill, decision = enter_claim_with_prefill(MOCK_KEY_S3_NO_ACTIVE)
    assert classification_map(prefill)["vehicle"] == "AUTO_PREFILL"
    assert "accident_story" in decision.customer_ask_fields


def test_s4_stale_policy_confirm():
    _lookup, prefill, decision = enter_claim_with_prefill(MOCK_KEY_S4_STALE_POLICY)
    cmap = classification_map(prefill)
    assert cmap["policy_number"] == "CUSTOMER_REQUIRED"
    assert cmap["insurance_company"] == "CUSTOMER_REQUIRED"
    assert decision.needs_stale_policy_confirm is True


@pytest.mark.parametrize(
    "key",
    [MOCK_KEY_S5_NO_MAPPING, MOCK_KEY_S6_UNAVAILABLE, MOCK_KEY_AMBIGUOUS],
)
def test_weak_ambiguous_unavailable_zero_auto(key):
    _lookup, prefill, decision = enter_claim_with_prefill(key)
    assert prefill["auto_prefill_count"] == 0
    assert decision.zero_auto is True
    assert classification_map(prefill)["accident_story"] == "CUSTOMER_REQUIRED"
    assert classification_map(prefill)["email"] == "UNKNOWN"


def test_lookup_flag_off_still_classifies_blank(monkeypatch):
    monkeypatch.setenv(FLAG_ENV, "0")
    _lookup, prefill, decision = enter_claim_with_prefill(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert prefill["lookup_match_status"] == "LOOKUP_UNAVAILABLE"
    assert decision.zero_auto is True
    assert decision.blocks_accident_report is False


def test_facade_exception_degrades_to_complete_zero_auto():
    class BoomAdapter:
        adapter_id = "boom"

        def classify(self, lookup):
            raise RuntimeError("classifier exploded")

    set_classifier_adapter_for_tests(BoomAdapter())
    result = prefill_from_lookup(lookup_customer(MOCK_KEY_S3_NO_ACTIVE))
    assert_prefill_result_complete(result)
    assert result["auto_prefill_count"] == 0
    assert "prefill_exception_degraded" in result["reason_codes"]


def test_empty_prefill_helper_is_complete():
    result = empty_prefill_result(reason_codes=["unit"])
    assert_prefill_result_complete(result)
    assert result["auto_prefill_count"] == 0


def test_decide_prefill_entry_is_pure_contract():
    lookup = lookup_customer(MOCK_KEY_S6_UNAVAILABLE)
    prefill = prefill_from_lookup(lookup)
    decision = decide_prefill_entry(lookup, prefill)
    assert decision.zero_auto is True
    assert decision.owns_start_claim_screens is False
