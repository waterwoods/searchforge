"""Happy Path Loop 1 — Cap2 Must Have office-materials accept.

Completeness = Cap2 Must Have gaps only. No broker_done / Done Card / Close.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    OfficeMaterialsAcceptError,
    accept_office_materials,
    get_case_by_id,
    save_case,
)
from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_case_brief
from services.fiqa_api.inbox_triage.p20_missing_information import (
    BUSINESS_CLASS_MUST_HAVE,
    CAP2_MUST_HAVE_OFFICE_KEYS,
    EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED,
    OFFICE_MATERIALS_READY_SUGGESTION,
    cap2_must_have_gaps_empty,
    derive_missing_information_checklist,
    office_materials_accept_eligible,
    seed_fact_records_from_case,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
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
    }
    stub.update(extra)
    return stub


def _claim_case(*, known_facts: dict | None = None, **extra) -> dict:
    return save_case(
        "[客户] claim happy path",
        _claim_stub(known_facts=known_facts, **extra),
        service_lane=SERVICE_LANE_CLAIM,
    )


def test_cap2_must_have_keys_match_business_contract():
    assert CAP2_MUST_HAVE_OFFICE_KEYS == {
        "accident_description",
        "accident_datetime",
        "accident_location",
        "injury_status",
    }
    checklist = derive_missing_information_checklist(None, case={"known_facts": {}})
    must = {i["field_key"] for i in checklist if i["business_class"] == BUSINESS_CLASS_MUST_HAVE}
    assert must == CAP2_MUST_HAVE_OFFICE_KEYS


def test_cap2_must_have_gaps_empty_requires_all_four():
    incomplete = {"known_facts": {"accident_description": "刮蹭"}}
    assert cap2_must_have_gaps_empty(incomplete) is False

    complete = {"known_facts": _complete_known_facts()}
    assert cap2_must_have_gaps_empty(complete) is True
    # Photos / VIN must not block.
    with_extras = {
        "known_facts": _complete_known_facts(),
        "case_attachments": [],
    }
    assert cap2_must_have_gaps_empty(with_extras) is True


def test_brief_suggests_ready_when_cap2_complete():
    case = _claim_case()
    brief = build_claim_case_brief(case)
    assert brief["can_accept_office_materials"] is True
    assert brief["office_materials_ready_suggestion"] == OFFICE_MATERIALS_READY_SUGGESTION
    assert brief["next_best_question"] == OFFICE_MATERIALS_READY_SUGGESTION
    assert office_materials_accept_eligible(case) is True


def test_brief_normalizes_chinese_injury_value_without_completeness_contradiction():
    facts = _complete_known_facts()
    facts["injury_status"] = "否"
    case = _claim_case(known_facts=facts)

    brief = build_claim_case_brief(case)

    assert brief["key_facts"]["injury_status"] == "no"
    assert brief["can_accept_office_materials"] is True
    assert not any(item.get("key") == "injury_status" for item in brief["missing_info"])
    assert not any("还缺受伤情况" in item.get("label", "") for item in brief["highlights"])


def test_brief_no_suggest_when_must_have_gap():
    case = _claim_case(
        known_facts={
            "accident_description": "刮蹭",
            "accident_datetime": "今天",
            "accident_location": "Irvine",
        }
    )
    brief = build_claim_case_brief(case)
    assert brief["can_accept_office_materials"] is False
    assert brief["office_materials_ready_suggestion"] is None


def test_accept_stamps_and_appends_idempotent_event():
    case = _claim_case()
    first = accept_office_materials(case["case_id"], source="workbench")
    assert first["already_accepted"] is False
    assert first["event_appended"] is True
    stamp = first["office_materials_accepted_at"]
    assert stamp
    refreshed = first["case"]
    assert refreshed["office_materials_accepted_at"] == stamp
    timeline = refreshed.get("claim_timeline") or []
    accept_events = [
        e for e in timeline if e.get("event_type") == EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED
    ]
    assert len(accept_events) == 1
    assert accept_events[0].get("text") == "资料已齐，等待办公室处理"
    assert refreshed.get("claim_phase") != "broker_done"
    assert not refreshed.get("broker_confirmed_at")
    assert not refreshed.get("case_history_state")

    persisted = get_case_by_id(case["case_id"])
    assert persisted is not None
    assert persisted.get("office_materials_accepted_at") == stamp

    second = accept_office_materials(case["case_id"], source="workbench")
    assert second["already_accepted"] is True
    assert second["event_appended"] is False
    assert second["office_materials_accepted_at"] == stamp
    timeline2 = (second["case"] or {}).get("claim_timeline") or []
    accept_events2 = [
        e for e in timeline2 if e.get("event_type") == EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED
    ]
    assert len(accept_events2) == 1

    brief = build_claim_case_brief(second["case"])
    assert brief["can_accept_office_materials"] is False
    assert brief["office_materials_accepted_at"] == stamp


def test_accept_blocked_when_gaps():
    case = _claim_case(known_facts={"accident_description": "only story"})
    with pytest.raises(OfficeMaterialsAcceptError, match="must_have_gaps"):
        accept_office_materials(case["case_id"])


def test_accept_blocked_when_closed():
    from services.fiqa_api.inbox_triage.case_close import close_case

    case = _claim_case()
    closed = close_case(case["case_id"], actor="broker_test")
    assert closed is not None
    with pytest.raises(OfficeMaterialsAcceptError, match="case_closed"):
        accept_office_materials(case["case_id"])


def test_accept_blocked_non_claim_lane():
    case = save_case(
        "[客户] add car",
        {
            "issue_category": "add_car",
            "urgency": "medium",
            "broker_next_step": "x",
            "client_prep": "",
            "client_reply_draft": "",
            "manual_followup_needed": False,
            "known_facts": _complete_known_facts(),
        },
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    with pytest.raises(OfficeMaterialsAcceptError, match="not_claim_lane"):
        accept_office_materials(case["case_id"])


def test_seed_fact_records_still_cap2_engine():
    """Guard: Loop 1 helpers must not invent a second completeness engine."""
    records = seed_fact_records_from_case({"known_facts": _complete_known_facts()})
    checklist = derive_missing_information_checklist(records)
    assert cap2_must_have_gaps_empty({"known_facts": _complete_known_facts()}, checklist=checklist)
