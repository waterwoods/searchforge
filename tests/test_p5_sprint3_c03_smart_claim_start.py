"""P5 Sprint 3 — C03 Smart Claim Start Customer Trust.

Validates presentation consumes C01+C02 only. No AMS. No C01/C02 redesign.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

os.environ["P4_CUSTOMER_LOOKUP_MOCK"] = "1"

from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    MOCK_KEY_AMBIGUOUS,
    MOCK_KEY_S1_EXISTING_ACTIVE,
    MOCK_KEY_S2_MULTI_VEHICLE,
    MOCK_KEY_S3_NO_ACTIVE,
    MOCK_KEY_S4_STALE_POLICY,
    MOCK_KEY_S5_NO_MAPPING,
    MOCK_KEY_S6_UNAVAILABLE,
)
from services.fiqa_api.inbox_triage.workflow_v2.c03_start_entry import (
    decide_start_entry,
    enter_claim_with_smart_start,
    simulate_smart_start_chain,
)

ROOT = Path(__file__).resolve().parents[1]
WF_C03 = ROOT / "services/fiqa_api/inbox_triage/workflow_v2/c03_start_entry.py"
ENGINE = ROOT / "services/fiqa_api/inbox_triage/smart_claim_start/engine.py"


def _banned_imports(path: Path, banned: tuple[str, ...]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if any(b in name for b in banned):
                    hits.append(name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if any(b in node.module for b in banned):
                hits.append(node.module)
    return hits


def test_workflow_c03_never_imports_ams_crm_adapters():
    hits = _banned_imports(
        WF_C03,
        (
            "ams",
            "ezlynx",
            "epic",
            "crm",
            "mock_directory",
            "claim_prefill.engine",
            "claim_prefill.adapters",
            "customer_lookup.adapters",
            "customer_lookup.engine",
            "notification",
            "timeline",
        ),
    )
    assert hits == []


def test_engine_consumes_contracts_only_no_ams():
    src = ENGINE.read_text(encoding="utf-8")
    assert "ams" not in src.lower()
    assert "ezlynx" not in src.lower()
    assert "LookupResult" in src
    assert "PrefillResult" in src


def test_s3_unambiguous_no_chooser_lands_on_story():
    _lookup, _prefill, plan, decision = enter_claim_with_smart_start(MOCK_KEY_S3_NO_ACTIVE)
    assert plan["mode"] == "MATCHED_KNOWN"
    assert decision.no_quiz_on_unambiguous is True
    assert decision.required_confirm_count == 0
    assert decision.lands_on_story is True
    assert "今天发生了什么" in plan["headline_zh"]
    assert "办公室已了解您" in plan["confidence_signal"]
    assert decision.estimated_customer_inputs == 4


def test_s2_multi_vehicle_one_decision():
    _l, _p, plan, decision = enter_claim_with_smart_start(MOCK_KEY_S2_MULTI_VEHICLE)
    assert plan["mode"] == "MATCHED_CONFIRM_VEHICLE"
    assert decision.required_confirm_count == 1
    assert plan["confirm_steps"][0]["step_id"] == "confirm_vehicle"
    assert decision.estimated_customer_inputs == 5


def test_s4_stale_friendly_always_continue():
    _l, _p, plan, decision = enter_claim_with_smart_start(MOCK_KEY_S4_STALE_POLICY)
    assert plan["mode"] == "MATCHED_CONFIRM_POLICY"
    assert decision.required_confirm_count == 0
    assert decision.soft_notice_count == 1
    assert decision.never_blocks_accident is True
    assert "不能" not in plan["subtitle_zh"]
    assert "今天发生了什么" in plan["headline_zh"]


def test_s5_s6_silent_blank_degrade():
    for key in (MOCK_KEY_S5_NO_MAPPING, MOCK_KEY_S6_UNAVAILABLE):
        _l, _p, plan, decision = enter_claim_with_smart_start(key)
        assert plan["mode"] == "BLANK_DEGRADE"
        assert plan["known_chips"] == []
        assert decision.known_chip_count == 0
        assert decision.lands_on_story is True
        blob = f"{plan['headline_zh']}{plan['subtitle_zh']}{plan['confidence_signal']}"
        for banned in ("error", "unavailable", "timeout", "500", "网络不稳定"):
            assert banned not in blob.lower()


def test_ambiguous_never_trapped():
    _l, _p, plan, decision = enter_claim_with_smart_start(MOCK_KEY_AMBIGUOUS)
    assert plan["mode"] == "CONTACT_BROKER"
    assert decision.has_blank_escape is True
    assert plan["secondary_cta_zh"] == "仍要先报案"
    assert decision.never_blocks_accident is True


def test_s1_continue_active_no_second_create():
    _l, _p, plan, decision = enter_claim_with_smart_start(MOCK_KEY_S1_EXISTING_ACTIVE)
    assert plan["mode"] == "CONTINUE_ACTIVE"
    assert plan["primary_cta_zh"] == "继续当前报案"
    assert decision.estimated_customer_inputs == 1


def test_customer_copy_never_exposes_internals():
    for key in (
        MOCK_KEY_S2_MULTI_VEHICLE,
        MOCK_KEY_S3_NO_ACTIVE,
        MOCK_KEY_S4_STALE_POLICY,
        MOCK_KEY_AMBIGUOUS,
    ):
        _l, _p, plan, _d = enter_claim_with_smart_start(key)
        blob = f"{plan['headline_zh']} {plan['subtitle_zh']} {plan['confidence_signal']} {plan['known_chips']}"
        lower = blob.lower()
        for banned in (
            "openid",
            "person_link",
            "confidence",
            "lookup_score",
            "classifier",
            "adapter",
            "match_status",
            "prefillresult",
            "lookupresult",
        ):
            assert banned not in lower


def test_simulate_chain_includes_c03_and_boundaries():
    lookup, prefill, plan, _d = enter_claim_with_smart_start(MOCK_KEY_S3_NO_ACTIVE)
    steps = simulate_smart_start_chain(lookup, prefill, plan)
    assert steps[1]["via"] == "capability_c01"
    assert steps[2]["via"] == "capability_c02"
    assert steps[3]["via"] == "capability_c03"
    assert steps[3]["plan_mode"] == "MATCHED_KNOWN"
    assert steps[4]["c03_wrote_crm"] is False
    assert steps[4]["no_ams"] is True


def test_decide_start_entry_pure():
    _l, _p, plan, _ = enter_claim_with_smart_start(MOCK_KEY_S3_NO_ACTIVE)
    d = decide_start_entry(plan)
    assert d.plan_mode == "MATCHED_KNOWN"
    assert d.owns_start_claim_screens is True
