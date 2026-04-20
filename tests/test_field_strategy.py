"""Declarative add-car field strategy (PTD): config load + case_draft attachment."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage.case_draft_engine import auto_fill_defaults, build_v4_case_draft_bundle
from services.fiqa_api.inbox_triage.field_strategy import (
    build_field_strategy_view,
    get_field_spec,
    load_add_car_field_strategy,
    usage_default_from_strategy,
)


def test_load_field_strategy_has_usage_guess():
    data = load_add_car_field_strategy()
    assert data.get("version") == 2
    ug = (data.get("fields") or {}).get("usage_guess")
    assert isinstance(ug, dict)
    assert ug.get("priority_tier") == 2
    assert ug.get("blocking") is False


def test_get_field_spec_vin_non_blocking():
    spec = get_field_spec("vin")
    assert spec is not None
    assert spec.get("blocking") is False
    assert spec.get("priority_tier") == 2


def test_usage_default_from_strategy_matches_config():
    dv, conf, tier = usage_default_from_strategy()
    spec = get_field_spec("usage_guess")
    assert spec is not None
    assert dv == spec.get("default_value")
    assert conf == float(spec.get("confidence_score") or 0)
    assert tier == int(spec.get("priority_tier") or 0)


def test_auto_fill_usage_industry_default_tags_strategy():
    out = auto_fill_defaults(
        "add car please",
        collected_field_ids=[],
        missing_field_ids=["usage"],
        primary_vehicle_summary=None,
    )
    inf = out.get("inferred_fields") or {}
    ug = inf.get("usage_guess")
    assert isinstance(ug, dict)
    assert ug.get("field_strategy_id") == "usage_guess"
    assert ug.get("priority_tier") == 2


def test_build_v4_bundle_includes_field_strategy():
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
    fs = b.get("field_strategy")
    assert isinstance(fs, dict)
    assert fs.get("lane") == "add_car"
    assert "vin" in (fs.get("fields") or {})
    vin_row = fs["fields"]["vin"]
    assert vin_row.get("session_status") == "missing"
    assert isinstance(fs.get("tier1_blocking_missing"), list)


def test_field_strategy_view_tier1_blocking_list():
    v = build_field_strategy_view(
        collected_field_ids=["year"],
        missing_field_ids=["zip", "make_model"],
        inferred_field_keys={"usage_guess"},
    )
    miss = v.get("tier1_blocking_missing") or []
    assert "zip" in miss
    assert "make_model" in miss
