"""P16 Case Memory — collecting-phase triage must persist customer turns to case_messages."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage.case_store import save_case
from services.fiqa_api.routes import inbox_triage
from services.fiqa_api.routes.inbox_triage import TriageRequest, triage_inbox


def _run(req: TriageRequest) -> dict:
    return asyncio.run(triage_inbox(req))


def test_collecting_triage_with_case_id_appends_case_messages(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(tmp_path / "cases.json"))
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "0")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")

    draft = save_case(
        "[客户] 开始加车申请（Customer First 入口）",
        {
            "issue_category": "add_car_quote",
            "urgency": "medium",
            "manual_followup_needed": False,
            "broker_next_step": "Collect vehicle details.",
            "client_prep": "",
            "client_reply_draft": "请继续填写车辆信息。",
            "handoff_ready": False,
            "lifecycle_status": "collecting",
            "collection_stage": "collecting",
            "collected_fields": [],
            "still_needed_fields": ["year", "make_model", "zip"],
            "quote_ready_status": "need_more",
            "service_type": "add_car",
        },
        status="new",
        client_id="sim_client",
        service_lane="add_car",
    )
    case_id = str(draft["case_id"])

    _run(
        TriageRequest(
            text="I bought a BMW X5",
            persist_case=True,
            case_id=case_id,
            client_id="sim_client",
            conversation_turns=[
                inbox_triage.ConversationTurn(role="customer", text="开始加车申请"),
            ],
        )
    )
    after1 = inbox_triage.get_case_for_read(case_id)
    assert after1 is not None
    msgs1 = after1.get("case_messages") or []
    customer_texts1 = [m["text"] for m in msgs1 if m.get("role") == "customer"]
    assert "I bought a BMW X5" in customer_texts1

    _run(
        TriageRequest(
            text="2027",
            persist_case=True,
            case_id=case_id,
            client_id="sim_client",
            conversation_turns=[
                inbox_triage.ConversationTurn(role="customer", text="开始加车申请"),
                inbox_triage.ConversationTurn(role="system", text="请提供年份"),
                inbox_triage.ConversationTurn(role="customer", text="I bought a BMW X5"),
            ],
        )
    )
    after2 = inbox_triage.get_case_for_read(case_id)
    assert after2 is not None
    msgs2 = after2.get("case_messages") or []
    customer_texts2 = [m["text"] for m in msgs2 if m.get("role") == "customer"]
    assert "2027" in customer_texts2
    assert customer_texts2.index("I bought a BMW X5") < customer_texts2.index("2027")


def test_collecting_triage_skips_append_when_append_blocked(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(tmp_path / "cases.json"))
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "0")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")

    vin_a = "1HGCM82633A004352"
    draft = save_case(
        f"[客户] add car VIN {vin_a}",
        {
            "issue_category": "add_car_quote",
            "urgency": "medium",
            "manual_followup_needed": False,
            "broker_next_step": "Follow up.",
            "client_prep": "",
            "client_reply_draft": "已记录。",
            "handoff_ready": False,
            "lifecycle_status": "collecting",
            "collected_fields": ["vin"],
            "still_needed_fields": ["zip"],
            "service_type": "add_car",
            "vehicle_key": f"vin:{vin_a}",
        },
        status="new",
        client_id="sim_client",
        service_lane="add_car",
    )
    case_id = str(draft["case_id"])
    before_count = len((inbox_triage.get_case_for_read(case_id) or {}).get("case_messages") or [])

    def _must_not_append(**_kwargs):
        raise AssertionError("append_follow_up_message must not run when append_allowed is False")

    monkeypatch.setattr(inbox_triage, "append_follow_up_message", _must_not_append)

    out = _run(
        TriageRequest(
            text="I also want to add another car",
            persist_case=True,
            case_id=case_id,
            client_id="sim_client",
        )
    )
    assert out.get("append_allowed") is False
    after = inbox_triage.get_case_for_read(case_id)
    assert len((after or {}).get("case_messages") or []) == before_count
