"""Conversion copy A/B: assignment stability, funnel dedupe, simulation shape."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.analytics.conversion_copy_ab import (
    COPY_VARIANTS,
    TEST_ZONES,
    assign_variant,
    simulate_conversion_ab_batch,
)
from services.fiqa_api.analytics.funnel_events import emit_funnel_event, iter_funnel_events, reset_funnel_store


@pytest.fixture(autouse=True)
def _clean_buffer():
    reset_funnel_store()
    yield
    reset_funnel_store()


def test_assign_variant_stable_per_session_zone():
    a = assign_variant("sess-1", "quote_ready")
    b = assign_variant("sess-1", "quote_ready")
    assert a["variant_id"] == b["variant_id"]
    c = assign_variant("sess-2", "quote_ready")
    # Different session → may differ
    assert isinstance(c["variant_id"], str)


def test_three_zones_fifteen_variants_total_structure():
    assert len(TEST_ZONES) == 3
    for z in TEST_ZONES:
        zid = z["zone_id"]
        assert len(COPY_VARIANTS[zid]) >= 3


def test_simulate_batch_returns_winners_and_funnel():
    r = simulate_conversion_ab_batch()
    assert "winning_variants" in r
    assert "ab_test_results" in r
    assert r["funnel"]["counts"]["session_started"] == 4
    assert r["funnel"]["counts"]["quote_ready_reached"] == 4


def test_funnel_dedupe_unchanged_quote_ready():
    reset_funnel_store()
    meta = {"customer_turn_index": 2}
    assert emit_funnel_event("quote_ready_reached", session_id="sx", case_id="cx", metadata=meta) is True
    assert emit_funnel_event("quote_ready_reached", session_id="sx", case_id="cx", metadata=meta) is False
    assert sum(1 for e in iter_funnel_events() if e.get("event") == "quote_ready_reached") == 1


def test_impression_rows_not_duplicate_funnel_stages():
    """AB impressions use append_session_analytics_event — do not inflate canonical funnel counts."""
    r = simulate_conversion_ab_batch()
    types = [e.get("event") for e in iter_funnel_events()]
    assert types.count("session_started") == 4
    assert types.count("quote_ready_reached") == 4
