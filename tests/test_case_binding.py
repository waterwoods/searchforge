"""Case binding resolver + session continuity (lightweight, no login)."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage.case_binding import is_case_open_for_binding, resolve_active_case
from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append
from services.fiqa_api.routes import inbox_triage


def _open_case(case_id: str, **kwargs) -> dict:
    row = {
        "case_id": case_id,
        "case_status": "new",
        "workbench_archived": False,
        "vehicle_key": None,
    }
    row.update(kwargs)
    return row


def test_same_session_continuity_uses_active_case_id():
    session = {"active_case_id": "case_a", "turns": []}
    recent = [
        _open_case("case_b", vehicle_key="vin:ZZZ"),
        _open_case("case_a", vehicle_key="vin:AAA"),
    ]
    assert resolve_active_case(session, recent, "vin:BBB") == "case_a"


def test_vehicle_match_binds_single_open_case_with_vin():
    vin = "1HGCM82633A004352"
    session = {}
    recent = [
        _open_case("c1", vehicle_key=f"vin:{vin}"),
        _open_case("c2", vehicle_key="vin:1HGBH41JXMN109186"),
    ]
    assert resolve_active_case(session, recent, f"vin:{vin}") == "c1"


def test_single_open_case_auto_bind_without_vehicle_key():
    session = {}
    recent = [_open_case("only_one", vehicle_key="vin:1HGCM82633A004352")]
    assert resolve_active_case(session, recent, None) == "only_one"


def test_multiple_open_cases_no_auto_bind_without_signals():
    session = {}
    recent = [
        _open_case("x", vehicle_key="vin:1HGCM82633A004352"),
        _open_case("y", vehicle_key="vin:1HGBH41JXMN109186"),
    ]
    assert resolve_active_case(session, recent, None) is None


def test_closed_case_not_counted_as_open_for_binding():
    assert is_case_open_for_binding(_open_case("z", case_status="closed")) is False
    assert is_case_open_for_binding(_open_case("z", workbench_archived=True)) is False


def test_conflict_clears_binding_via_append_api(monkeypatch, tmp_path):
    from services.fiqa_api.inbox_triage import session_store as ss

    sid = "sess-bind-clear-1"
    ss.patch_session_case_binding(sid, active_case_id="case_old")

    case = {
        "case_id": "case_old",
        "source_text": "[客户] add car 2024 Camry\n\n[系统] ok",
        "lifecycle_status": "office_followup",
        "client_id": "chen_kui",
        "vehicle_key": "vin:1HGCM82633A004352",
    }
    monkeypatch.setattr(inbox_triage, "get_case_for_read", lambda _id: case)

    async def _run():
        return await inbox_triage.append_case_message(
            "case_old",
            inbox_triage.AppendMessageRequest(
                new_message="new car VIN 1HGBH41JXMN109186",
                session_id=sid,
            ),
        )

    body = asyncio.run(_run())
    assert body.get("append_allowed") is False
    assert body.get("case_boundary_action") == "requires_new_case"
    data = ss.get_in_progress_session(sid)
    assert data is not None
    assert "active_case_id" not in data


def test_short_reply_continuity_same_case_greenfield_context():
    """Short ack with persisted VIN scope stays same_case (mirrors append routing)."""
    ctx = {
        "formal_submitted_at": "2026-03-01T12:00:00Z",
        "service_record_continuation": True,
        "vehicle_key": "vin:1HGCM82633A004352",
    }
    out = triage_conversation(
        "ok",
        [
            {"role": "customer", "text": "我想加车"},
            {"role": "system", "text": "请补充信息"},
        ],
        client_id="chen_kui",
        reply_truth_context=ctx,
    )
    assert out.get("append_allowed") is True
    assert out.get("case_boundary_action") == "append_allowed"


def test_short_reply_append_path():
    thread = (
        "[客户] 我想加车，2024 Toyota Camry，ZIP 90210，下周提车，我自己开\n\n"
        "[系统] 已记录加车信息，会继续整理。"
    )
    out = triage_for_append(
        thread,
        "ok",
        client_id="chen_kui",
        reply_truth_context={
            "formal_submitted_at": "2026-03-01T12:00:00Z",
            "service_record_append": True,
            "vehicle_key": "vin:1HGCM82633A004352",
        },
    )
    assert out.get("append_allowed") is True
