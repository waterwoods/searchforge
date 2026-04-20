"""Minimal analytics: structured logging only; routes must stay behavior-identical when tracking is no-op."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dataclasses import dataclass

from services.fiqa_api.analytics.funnel_events import iter_funnel_events, reset_funnel_store
from services.fiqa_api.analytics.triage_funnel import emit_funnel_from_triage_result
from services.fiqa_api.routes import inbox_triage


@dataclass
class _Turn:
    role: str
    text: str


@pytest.fixture(autouse=True)
def _reset_funnel_buffer():
    reset_funnel_store()
    yield
    reset_funnel_store()


@pytest.fixture
def capture_events(monkeypatch):
    events: list[tuple[str, dict]] = []

    def _cap(name: str, payload: dict) -> None:
        events.append((name, dict(payload)))

    monkeypatch.setattr(inbox_triage, "track_event", _cap)
    return events


def test_triage_emits_field_progress_and_related_events(capture_events):
    req = inbox_triage.TriageRequest(
        text="I want to add a car to my policy",
        client_id="chen_kui",
    )
    asyncio.run(inbox_triage.triage_inbox(req))
    names = [n for n, _ in capture_events]
    assert "field_progress" in names
    assert "case_binding_decision" not in names  # no session_id → no binding branch


def test_append_blocked_event_on_new_vehicle_path(monkeypatch, capture_events):
    case = {
        "case_id": "case_1",
        "source_text": "[客户] 老案子内容",
        "lifecycle_status": "office_followup",
        "client_id": "chen_kui",
    }
    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _case_id: case)
    monkeypatch.setattr(
        inbox_triage,
        "triage_for_append",
        lambda **_kwargs: {
            "issue_category": "claim_intake",
            "urgency": "medium",
            "manual_followup_needed": True,
            "client_prep": "N/A",
            "case_boundary": "new_issue",
            "case_boundary_action": "requires_new_case",
            "boundary_reason": "Detected clear matter separation from current case.",
            "broker_next_step": "Case boundary: possible new issue in the same thread—confirm whether to split.",
            "client_reply_draft": "这是新事项，请新开服务记录。",
            "conversation_summary": "Boundary: new_issue",
            "service_type": "claim_intake",
            "vehicle_key": None,
            "collected_fields": [],
            "still_needed_fields": [],
            "handoff_ready": True,
            "triage_mode": "append",
        },
    )
    monkeypatch.setattr(
        inbox_triage,
        "append_follow_up_message",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("append_follow_up_message must not run")),
    )
    asyncio.run(
        inbox_triage.append_case_message(
            "case_1",
            inbox_triage.AppendMessageRequest(new_message="我还有一个理赔新问题"),
        )
    )
    blocked = [p for n, p in capture_events if n == "append_blocked"]
    assert blocked and blocked[0].get("reason") == "requires_new_case"


def test_handoff_started_emits_when_handoff_ready_without_quote_ready():
    """V5 case_usable path: funnel must record handoff_started whenever handoff_ready is true."""
    result = {
        "quote_ready_status": "need_more",
        "handoff_ready": True,
        "case_usable": True,
        "issue_category": "customer_question",
        "collected_fields": ["year", "make_model"],
        "still_needed_fields": ["vin"],
        "append_allowed": True,
    }
    emit_funnel_from_triage_result(
        result,
        turns=[_Turn("customer", "2020 Camry zip 92602")],
        text="2020 Camry zip 92602",
        session_id="s-v5-handoff",
        case_id="c-v5",
    )
    funnel_names = [e.get("event") for e in iter_funnel_events()]
    assert "handoff_started" in funnel_names
    hs = next(e for e in iter_funnel_events() if e.get("event") == "handoff_started")
    assert hs.get("metadata", {}).get("case_usable") is True


def test_emit_handoff_confirmed_when_conversion_stage_set(capture_events):
    """Funnel: user acknowledged handoff after quote-ready conversion (conversion_layer CS_HANDOFF_CONFIRMED)."""
    result = {
        "quote_ready_status": "quote_ready",
        "handoff_ready": True,
        "conversion_stage": "handoff_confirmed",
        "collected_fields": ["vin"],
        "still_needed_fields": [],
        "append_allowed": True,
    }
    inbox_triage._emit_route_analytics_for_triage_result(result, [], session_id="s1", text="ok")
    funnel_names = [e.get("event") for e in iter_funnel_events()]
    assert "handoff_confirmed" in funnel_names
    names = [n for n, _ in capture_events]
    assert "handoff_confirmed" not in names


def test_quote_ready_event_when_structurally_complete(capture_events):
    msg = (
        "VIN 1HGBH41JXMN109186 zip 94043 delivery 2026-05-01 primary driver is me "
        "2020 Honda Civic"
    )
    req = inbox_triage.TriageRequest(text=msg, client_id="chen_kui")
    asyncio.run(inbox_triage.triage_inbox(req))
    funnel_names = [e.get("event") for e in iter_funnel_events()]
    assert "quote_ready_reached" in funnel_names
    assert "handoff_started" in funnel_names
    names = [n for n, _ in capture_events]
    assert "quote_ready" not in names
    assert "handoff_started" not in names
    fp = next(p for n, p in capture_events if n == "field_progress")
    assert fp.get("quote_ready_status") == "quote_ready"


def test_tracking_does_not_change_triage_response(monkeypatch):
    text = (
        "VIN 1HGBH41JXMN109186 zip 94043 delivery 2026-05-01 primary driver is me "
        "2020 Honda Civic"
    )
    req = inbox_triage.TriageRequest(text=text, client_id="chen_kui")
    baseline = asyncio.run(inbox_triage.triage_inbox(req))
    monkeypatch.setattr(inbox_triage, "track_event", lambda *a, **k: None)
    req2 = inbox_triage.TriageRequest(text=text, client_id="chen_kui")
    silent = asyncio.run(inbox_triage.triage_inbox(req2))

    def _without_assist(d: dict) -> dict:
        out = dict(d)
        out.pop("assist", None)
        return out

    assert _without_assist(baseline) == _without_assist(silent)


def test_contract_v1_testclient_still_importable():
    """Guard: TestClient(app) must construct (httpx/starlette compatibility)."""
    from fastapi.testclient import TestClient

    from services.fiqa_api.app_main import app

    c = TestClient(app)
    r = c.get("/api/v1/experiment/logs/abcdef?tail=10")
    assert r.status_code in (200, 400, 404, 500)
