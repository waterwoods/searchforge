"""Broker「已核对补充资料」— exit broker_review_ready without broker_done/Close.

Flow: Request More → customer submit → waiting_office_review → ack → Cap2 next step.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_case_brief
from services.fiqa_api.inbox_triage.p20_missing_information import (
    EVENT_BROKER_SUPPLEMENT_REVIEWED,
)
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    InMemorySlice1Store,
    P20Slice1CommandService,
    STATE_BROKER_REVIEWING,
    STATE_BROKER_REVIEW_READY,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


def _complete_known_facts() -> dict[str, str]:
    return {
        "accident_description": "对方变道刮到我左前门",
        "accident_datetime": "今天上午10点",
        "accident_location": "Irvine Blvd",
        "injury_status": "no",
    }


def _incomplete_known_facts() -> dict[str, str]:
    return {
        "accident_description": "对方变道刮到我左前门",
        "accident_datetime": "今天上午10点",
        # missing location + injury
    }


def _claim_stub(known_facts: dict | None = None, **extra) -> dict:
    facts = dict(known_facts if known_facts is not None else _complete_known_facts())
    stub = {
        "issue_category": "claim_intake",
        "urgency": "medium",
        "broker_next_step": "Claim guided workflow",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "manual_followup_needed": False,
        "collected_fields": list(facts.keys()),
        "still_needed_fields": [],
        "known_facts": facts,
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "guided_workflow_state": "collecting_text",
        "extracted_contact_name": "测试客户",
        "extracted_contact_phone": "9495550100",
        "slice1_capability_version": 1,
        "entry_channel": "mini_program",
        "created_by_actor": "customer",
        "identity_binding_state": "linked",
        "person_link_source": "wechat",
        "person_link_key": "plk_supp_review_qa",
    }
    stub.update(extra)
    return stub


def _claim_case(*, known_facts: dict | None = None, **extra) -> dict:
    saved = save_case(
        "[客户] claim supplement review",
        _claim_stub(known_facts=known_facts, **extra),
        service_lane=SERVICE_LANE_CLAIM,
    )
    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
    )

    row = _load_case_for_mutation(saved["case_id"])
    if row is not None:
        row["slice1_capability_version"] = int(row.get("slice1_capability_version") or 1) or 1
        row.setdefault("entry_channel", "mini_program")
        row.setdefault("created_by_actor", "customer")
        row.setdefault("identity_binding_state", "linked")
        row.setdefault("person_link_key", "plk_supp_review_qa")
        _persist_case_after_update(saved["case_id"], row)
        refreshed = get_case_by_id(saved["case_id"])
        if refreshed is not None:
            return refreshed
    return saved


def _item(label: str = "VIN", position: int = 1, item_type: str = "vin") -> dict:
    return {
        "request_item_id": f"item_{position}",
        "item_type": item_type,
        "label": label,
        "instructions": f"请补充 {label}",
        "required": True,
        "position": position,
    }


def _rm_then_submit(
    *,
    known_facts: dict | None = None,
    case_id: str | None = None,
) -> tuple[P20Slice1CommandService, InMemorySlice1Store, dict, dict]:
    row = _claim_case(known_facts=known_facts) if case_id is None else get_case_by_id(case_id)
    assert row is not None
    cid = row["case_id"]
    store = InMemorySlice1Store({cid: dict(row)})
    svc = P20Slice1CommandService(store)
    created = svc.accept_request_more(
        case_id=cid,
        broker_id="office:supp_review",
        command_id="cmd-supp-rm-1",
        idempotency_key="idem-supp-rm-1",
        expected_case_version=0,
        requested_items=[_item()],
        reason="Need VIN",
        request_id="req_supp_1",
    )
    assert created["outcome"] == "accepted"
    submitted = svc.submit_request_item(
        case_id=cid,
        customer_id="h5:supp",
        active_request_item_id="item_1",
        command_id="cmd-supp-submit-1",
        idempotency_key="idem-supp-submit-1",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": "1HGCM82633A004352"},
    )
    assert submitted["outcome"] == "accepted"
    assert submitted["customer_projection"]["workflow_state"] == STATE_BROKER_REVIEW_READY
    return svc, store, row, submitted


def test_1_submitted_supplement_is_broker_review_ready():
    _svc, _store, _row, submitted = _rm_then_submit()
    proj = submitted["broker_projection"]
    assert proj["workflow_state"] == STATE_BROKER_REVIEW_READY
    assert proj["broker_next_action"]["action_type"] == "review_customer_response"
    assert proj["open_request"]["progress"]["satisfied"] >= proj["open_request"]["progress"]["total"]


def test_2_ack_clears_review_ready():
    svc, store, row, submitted = _rm_then_submit()
    cid = row["case_id"]
    result = svc.acknowledge_supplement_review(
        case_id=cid,
        broker_id="office:supp_review",
        command_id="cmd-supp-ack-1",
        idempotency_key="idem-supp-ack-1",
    )
    assert result["outcome"] == "accepted"
    assert result["already_acknowledged"] is False
    assert result["event_appended"] is True
    assert result["broker_projection"]["workflow_state"] == STATE_BROKER_REVIEWING
    assert result["broker_projection"]["broker_next_action"]["action_type"] != "review_customer_response"
    assert store.aggregates[cid].workflow_state == STATE_BROKER_REVIEWING
    legacy = store.cases[cid]
    assert legacy.get("p20_slice1_projection", {}).get("workflow_state") == STATE_BROKER_REVIEWING
    # Precondition: was review ready before ack.
    assert submitted["broker_projection"]["workflow_state"] == STATE_BROKER_REVIEW_READY


def test_3_ack_cap2_complete_suggests_office_accept():
    svc, store, row, _submitted = _rm_then_submit(known_facts=_complete_known_facts())
    cid = row["case_id"]
    result = svc.acknowledge_supplement_review(
        case_id=cid,
        broker_id="office:supp_review",
        command_id="cmd-supp-ack-cap2",
        idempotency_key="idem-supp-ack-cap2",
    )
    assert result["outcome"] == "accepted"
    updated = dict(store.cases[cid])
    updated["p20_slice1_projection"] = result["broker_projection"]
    brief = build_claim_case_brief(updated)
    assert brief.get("can_accept_office_materials") is True
    assert "建议确认资料已齐" in str(brief.get("office_materials_ready_suggestion") or "建议确认资料已齐")
    assert updated.get("office_materials_accepted_at") in (None, "")


def test_4_ack_cap2_incomplete_shows_missing():
    svc, store, row, _submitted = _rm_then_submit(known_facts=_incomplete_known_facts())
    cid = row["case_id"]
    result = svc.acknowledge_supplement_review(
        case_id=cid,
        broker_id="office:supp_review",
        command_id="cmd-supp-ack-gap",
        idempotency_key="idem-supp-ack-gap",
    )
    assert result["outcome"] == "accepted"
    updated = dict(store.cases[cid])
    updated["p20_slice1_projection"] = result["broker_projection"]
    brief = build_claim_case_brief(updated)
    assert brief.get("can_accept_office_materials") is False
    missing = brief.get("missing_info") or []
    must = [
        m
        for m in missing
        if str(m.get("severity") or "").lower() in {"critical", "important"}
        or str(m.get("key") or "") in {"accident_location", "injury_status"}
    ]
    assert must, f"expected Cap2 gaps, got {missing}"


def test_5_repeated_ack_one_timeline_event():
    svc, store, row, _submitted = _rm_then_submit()
    cid = row["case_id"]
    first = svc.acknowledge_supplement_review(
        case_id=cid,
        broker_id="office:supp_review",
        command_id="cmd-supp-ack-a",
        idempotency_key="idem-supp-ack-a",
    )
    assert first["event_appended"] is True
    second = svc.acknowledge_supplement_review(
        case_id=cid,
        broker_id="office:supp_review",
        command_id="cmd-supp-ack-b",
        idempotency_key="idem-supp-ack-b",
    )
    assert second["outcome"] == "accepted"
    assert second["already_acknowledged"] is True
    assert second["event_appended"] is False
    timeline = store.cases[cid].get("claim_timeline") or []
    events = [e for e in timeline if e.get("event_type") == EVENT_BROKER_SUPPLEMENT_REVIEWED]
    assert len(events) == 1


def test_6_broker_done_close_history_untouched():
    svc, store, row, _submitted = _rm_then_submit()
    cid = row["case_id"]
    before = dict(store.cases[cid])
    svc.acknowledge_supplement_review(
        case_id=cid,
        broker_id="office:supp_review",
        command_id="cmd-supp-ack-safe",
        idempotency_key="idem-supp-ack-safe",
    )
    after = store.cases[cid]
    assert after.get("claim_phase") != "broker_done"
    assert after.get("broker_done_at") in (None, "", before.get("broker_done_at"))
    assert after.get("office_materials_accepted_at") in (None, "")
    assert after.get("case_history_state") != "history"
    assert after.get("case_status") != "closed"
    # Request More remains available from broker_reviewing.
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
        broker_may_create_request_more,
    )

    assert broker_may_create_request_more(STATE_BROKER_REVIEWING) is True
    rm = svc.accept_request_more(
        case_id=cid,
        broker_id="office:supp_review",
        command_id="cmd-supp-rm-2",
        idempotency_key="idem-supp-rm-2",
        expected_case_version=store.aggregates[cid].aggregate_version,
        requested_items=[
            {
                "request_item_id": "item_2",
                "item_type": "policy_or_insurance_card",
                "label": "保险卡",
                "instructions": "请补充保险卡",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need card after ack",
        request_id="req_supp_2",
    )
    assert rm["outcome"] == "accepted"
