"""North Star scoring, funnel aggregation, and funnel dedupe."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.analytics.funnel_events import (
    CANONICAL_FUNNEL_EVENTS,
    emit_funnel_event,
    iter_funnel_events,
    reset_funnel_store,
)
from services.fiqa_api.analytics.funnel_metrics import compute_funnel, group_events_by_session
from services.fiqa_api.analytics.north_star_score import compute_north_star_score
from services.fiqa_api.analytics.triage_funnel import is_meaningful_customer_text


@pytest.fixture(autouse=True)
def _clean_buffer():
    reset_funnel_store()
    yield
    reset_funnel_store()


def _snap(**kwargs: object) -> dict:
    base = {
        "quote_ready_status": "quote_ready",
        "still_needed_fields": [],
        "collected_fields": ["vin", "zip"],
        "next_best_question": "",
        "client_reply_draft": "好的，我们已收到信息。",
        "handoff_ready": True,
        "triage_mode": "greenfield",
        "append_allowed": True,
        "conversion_stage": "",
        "issue_category": "customer_question",
        "reroute_occurred": False,
        "customer_turn_index": 3,
        "customer_text_len": 40,
    }
    base.update(kwargs)
    return base


def test_perfect_session_score_at_least_eight():
    events = [
        {
            "event": "session_started",
            "session_id": "s-perfect",
            "metadata": {},
        },
        {
            "event": "first_meaningful_input",
            "session_id": "s-perfect",
            "metadata": {"customer_turn_index": 1, "case_snapshot": _snap(customer_turn_index=1)},
        },
        {
            "event": "case_created",
            "session_id": "s-perfect",
            "case_id": "c1",
            "metadata": {"customer_turn_index": 2, "case_snapshot": _snap(customer_turn_index=2)},
        },
        {
            "event": "quote_ready_reached",
            "session_id": "s-perfect",
            "case_id": "c1",
            "metadata": {"customer_turn_index": 5, "case_snapshot": _snap(customer_turn_index=5)},
        },
        {
            "event": "handoff_started",
            "session_id": "s-perfect",
            "case_id": "c1",
            "metadata": {"customer_turn_index": 5, "case_snapshot": _snap(customer_turn_index=5)},
        },
    ]
    case_state = _snap()
    out = compute_north_star_score(events, case_state)
    assert out["total_score"] >= 8.0


def test_broken_session_score_at_most_four():
    events = [
        {"event": "append_blocked", "session_id": "s-bad", "metadata": {}},
        {"event": "append_blocked", "session_id": "s-bad", "metadata": {}},
        {
            "event": "first_meaningful_input",
            "session_id": "s-bad",
            "metadata": {"customer_turn_index": 4},
        },
    ]
    case_state = {
        "quote_ready_status": "need_more",
        "still_needed_fields": ["vin"],
        "collected_fields": [],
        "next_best_question": "",
        "client_reply_draft": "资料已经齐全，我们马上处理。",
        "handoff_ready": False,
        "reroute_occurred": True,
    }
    out = compute_north_star_score(events, case_state)
    assert out["total_score"] <= 4.0


def test_funnel_counts_per_session_milestone():
    reset_funnel_store()
    emit_funnel_event("session_started", session_id="a", metadata={})
    emit_funnel_event("first_meaningful_input", session_id="a", metadata={})
    emit_funnel_event("case_created", session_id="a", case_id="c-a", metadata={})
    emit_funnel_event("quote_ready_reached", session_id="a", case_id="c-a", metadata={})
    emit_funnel_event("handoff_started", session_id="a", case_id="c-a", metadata={})

    emit_funnel_event("session_started", session_id="b", metadata={})
    emit_funnel_event("first_meaningful_input", session_id="b", metadata={})
    # b stops before case

    f = compute_funnel(iter_funnel_events())
    assert f["counts"]["session_started"] == 2
    assert f["counts"]["case_created"] == 1
    assert f["counts"]["quote_ready_reached"] == 1
    assert f["counts"]["handoff_started"] == 1


def test_quote_ready_not_double_emitted_same_session_case():
    reset_funnel_store()
    meta = {"customer_turn_index": 2, "case_snapshot": _snap(customer_turn_index=2)}
    assert emit_funnel_event("quote_ready_reached", session_id="sx", case_id="cx", metadata=meta) is True
    assert emit_funnel_event("quote_ready_reached", session_id="sx", case_id="cx", metadata=meta) is False
    types = [e.get("event") for e in iter_funnel_events()]
    assert types.count("quote_ready_reached") == 1


def test_canonical_funnel_event_list_stable():
    assert "session_started" in CANONICAL_FUNNEL_EVENTS
    assert "quote_ready_reached" in CANONICAL_FUNNEL_EVENTS


def test_group_events_by_session_unknown_bucket():
    evs = [{"event": "field_progress", "session_id": "", "case_id": "", "metadata": {}}]
    g = group_events_by_session(evs)
    assert "unknown" in g


def test_short_english_ack_counts_as_meaningful_for_funnel():
    assert is_meaningful_customer_text("ok") is True
    assert is_meaningful_customer_text("OK") is True
    assert is_meaningful_customer_text("yes") is True
