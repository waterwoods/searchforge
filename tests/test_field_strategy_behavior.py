"""Field strategy drives runtime: partition, deferral, confirm priority, default metadata."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage.case_draft_engine import (
    auto_fill_defaults,
    build_confirm_priority_fields,
    build_v4_case_draft_bundle,
)
from services.fiqa_api.inbox_triage.field_strategy import (
    partition_still_needed_by_strategy,
    should_skip_user_prompt_for_missing_field,
)


def test_partition_defers_vin_name_phone_tier3_nonblocking():
    part = partition_still_needed_by_strategy(["year", "vin", "name", "zip"])
    uf = part["still_needed_user_flow"]
    d = part["deferred_to_broker_fields"]
    assert "zip" in uf
    assert "year" in uf
    assert "vin" in d
    assert "name" in d


def test_non_blocking_tier2_deferred_from_user_flow():
    part = partition_still_needed_by_strategy(["phone", "delivery_date"])
    assert "delivery_date" in part["still_needed_user_flow"]
    assert "phone" in part["deferred_to_broker_fields"]


def test_should_skip_prompt_for_vin():
    assert should_skip_user_prompt_for_missing_field("vin") is True
    assert should_skip_user_prompt_for_missing_field("zip") is False


def test_auto_fill_carries_default_engine_metadata():
    out = auto_fill_defaults(
        "92602 add car",
        collected_field_ids=[],
        missing_field_ids=["zip", "year", "make_model"],
        primary_vehicle_summary="2020 Camry",
    )
    inf = out.get("inferred_fields") or {}
    gh = inf.get("garaging_area_hint")
    assert isinstance(gh, dict)
    assert gh.get("field_strategy_id") == "garaging_area_hint"
    assert "default_engine" in gh
    vs = inf.get("vehicle_from_summary")
    assert isinstance(vs, dict)
    assert vs.get("default_engine", {}).get("rule_id") == "vehicle_from_summary_hint"


def test_build_v4_bundle_broker_completion_and_user_flow():
    b = build_v4_case_draft_bundle(
        merged_text="2020 Camry zip 92602 delivery May 1 primary driver me",
        collected_fields=["year", "make_model", "zip", "delivery_date", "primary_driver"],
        missing_fields=["vin", "name", "phone"],
        primary_vehicle_summary="2020 Camry",
        quote_ready_status="almost_ready",
        human_confirmation_fields=[],
        issue_category="customer_question",
        language="en",
        variant="B",
    )
    assert "vin" in (b.get("deferred_to_broker_fields") or [])
    assert "vin" not in (b.get("still_needed_user_flow") or [])
    bc = b.get("broker_completion") or {}
    assert bc.get("broker_usable_case") is True
    assert "vin" in (bc.get("deferred_fields") or [])


def test_confirm_priority_excludes_tier3():
    inferred = {
        "usage_guess": {"confidence": 0.52, "tier": "medium"},
        "make_keyword_hint": {"confidence": 0.33, "tier": "low"},
    }
    cm = {"inferred:usage_guess": 0.52, "inferred:make_keyword_hint": 0.33}
    out = build_confirm_priority_fields(cm, inferred, variant="B")
    assert "usage_guess" in out
    assert "make_keyword_hint" not in out


def test_learning_signals_jsonl(tmp_path, monkeypatch: pytest.MonkeyPatch):
    p = tmp_path / "sig.jsonl"
    monkeypatch.setenv("LEARNING_SIGNALS_PATH", str(p))
    from services.fiqa_api.inbox_triage import learning_signals as ls

    ls.record_user_correction_signal(
        session_id="s1",
        case_id="c1",
        field_key="zip",
        prior_value="90001",
        new_value="92602",
        source="thread",
    )
    ls.record_broker_field_edit_signal(case_id="c1", fields_touched=["vin", "name"])
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert "user_correction" in lines[0]
    assert "broker_field_edit" in lines[1]
