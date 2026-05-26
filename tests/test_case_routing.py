"""Case routing + append convergence: vehicle scope vs persisted case (CASE_CONTRACT_V1)."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage.routing_guard import detect_vehicle_conflict
from services.fiqa_api.inbox_triage.triage import triage_for_append
from services.fiqa_api.routes import inbox_triage
from tests.route_request_stub import minimal_route_request


def test_detect_vehicle_conflict_matrix():
    assert detect_vehicle_conflict(None, "vin:AAA", False) == "same_vehicle"
    assert detect_vehicle_conflict("", "vin:AAA", False) == "same_vehicle"
    assert detect_vehicle_conflict("vin:AAA", "vin:AAA", False) == "same_vehicle"
    assert detect_vehicle_conflict("vin:AAA", "vin:BBB", False) == "new_vehicle"
    assert detect_vehicle_conflict("vin:AAA", None, True) == "new_vehicle"
    assert detect_vehicle_conflict(None, None, True) == "new_vehicle"
    assert (
        detect_vehicle_conflict("vin:AAA", None, False, message_suggests_vehicle_scope_ambiguity=True)
        == "ambiguous"
    )


def _add_car_thread_zh() -> str:
    return (
        "[客户] 我想加车，2024 Toyota Camry，ZIP 90210，下周提车，我自己开\n\n"
        "[系统] 已记录加车信息，会继续整理。"
    )


def test_same_vehicle_append_allowed():
    vin = "1HGCM82633A004352"
    ctx = {
        "formal_submitted_at": "2026-03-01T12:00:00Z",
        "service_record_append": True,
        "vehicle_key": f"vin:{vin}",
    }
    out = triage_for_append(
        _add_car_thread_zh(),
        f"补充：VIN 是 {vin}",
        client_id="chen_kui",
        reply_truth_context=ctx,
    )
    assert out.get("append_allowed") is True
    assert out.get("case_boundary") == "same_case"
    assert out.get("case_boundary_action") == "append_allowed"


def test_different_vehicle_requires_new_case():
    ctx = {
        "formal_submitted_at": "2026-03-01T12:00:00Z",
        "service_record_append": True,
        "vehicle_key": "vin:1HGCM82633A004352",
    }
    out = triage_for_append(
        _add_car_thread_zh(),
        "更正：VIN 是 1HGBH41JXMN109186",
        client_id="chen_kui",
        reply_truth_context=ctx,
    )
    assert out.get("append_allowed") is False
    assert out.get("case_boundary") == "new_issue"
    assert out.get("case_boundary_action") == "requires_new_case"


def test_another_car_wording_requires_new_case():
    out = triage_for_append(
        _add_car_thread_zh(),
        "I also want to add another car",
        client_id="chen_kui",
        reply_truth_context={
            "formal_submitted_at": "2026-03-01T12:00:00Z",
            "service_record_append": True,
            "vehicle_key": "vin:1HGCM82633A004352",
        },
    )
    assert out.get("case_boundary_action") == "requires_new_case"
    assert out.get("append_allowed") is False


def test_ambiguous_other_car_requires_confirmation_and_blocks_append():
    out = triage_for_append(
        _add_car_thread_zh(),
        "same as my other car",
        client_id="chen_kui",
        reply_truth_context={
            "formal_submitted_at": "2026-03-01T12:00:00Z",
            "service_record_append": True,
            "vehicle_key": "vin:1HGCM82633A004352",
        },
    )
    assert out.get("case_boundary_action") == "requires_confirmation"
    assert out.get("append_allowed") is False
    assert out.get("case_boundary") == "borderline"


def test_short_reply_ok_stays_same_case():
    out = triage_for_append(
        _add_car_thread_zh(),
        "ok",
        client_id="chen_kui",
        reply_truth_context={
            "formal_submitted_at": "2026-03-01T12:00:00Z",
            "service_record_append": True,
            "vehicle_key": "vin:1HGCM82633A004352",
        },
    )
    assert out.get("case_boundary") == "same_case"
    assert out.get("append_allowed") is True


def test_no_persisted_truth_normal_flow():
    out = triage_for_append(
        _add_car_thread_zh(),
        "补充：VIN 是 1HGCM82633A004352",
        client_id="chen_kui",
        reply_truth_context=None,
    )
    assert out.get("case_boundary") == "same_case"
    assert out.get("append_allowed") is True


def test_multi_turn_second_vehicle_triggers_new_case():
    prior = (
        "[客户] I want to add a car\n\n"
        "[系统] Sure — please send VIN when you have it.\n\n"
        "[客户] VIN 1HGCM82633A004352"
    )
    out = triage_for_append(
        prior,
        "I also have another car VIN 1HGBH41JXMN109186",
        client_id="chen_kui",
        reply_truth_context={
            "formal_submitted_at": "2026-03-01T12:00:00Z",
            "service_record_append": True,
            "vehicle_key": "vin:1HGCM82633A004352",
        },
    )
    assert out.get("case_boundary") == "new_issue"
    assert out.get("case_boundary_action") == "requires_new_case"
    assert out.get("append_allowed") is False


def test_append_api_blocked_when_append_allowed_false(monkeypatch):
    case = {
        "case_id": "case_amb",
        "source_text": "[客户] add car",
        "lifecycle_status": "office_followup",
        "client_id": "chen_kui",
        "vehicle_key": "vin:1HGCM82633A004352",
    }

    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _id: case)

    def _fake_append(**_kwargs):
        return {
            "case_boundary": "borderline",
            "case_boundary_action": "requires_confirmation",
            "append_allowed": False,
            "boundary_reason": "Vehicle scope is unclear.",
            "client_reply_draft": "Please confirm.",
            "collected_fields": [],
            "still_needed_fields": [],
        }

    monkeypatch.setattr(inbox_triage, "triage_for_append", _fake_append)

    def _must_not_append(**_kwargs):
        raise AssertionError("append_follow_up_message must not run when append_allowed is False")

    monkeypatch.setattr(inbox_triage, "append_follow_up_message", _must_not_append)

    body = asyncio.run(
        inbox_triage.append_case_message(
            "case_amb",
            inbox_triage.AppendMessageRequest(new_message="same as my other car"),
            minimal_route_request(),
        )
    )
    assert body.get("append_blocked") is True
    assert body.get("old_case_mutated") is False
