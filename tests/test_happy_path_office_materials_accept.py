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
        # Slice1 Request More enabled for Founder QA regression.
        "slice1_capability_version": 1,
        "entry_channel": "mini_program",
        "created_by_actor": "customer",
        "identity_binding_state": "linked",
        "person_link_source": "wechat",
        "person_link_key": "plk_happy_path_qa",
    }
    stub.update(extra)
    return stub


def _claim_case(*, known_facts: dict | None = None, **extra) -> dict:
    saved = save_case(
        "[客户] claim happy path",
        _claim_stub(known_facts=known_facts, **extra),
        service_lane=SERVICE_LANE_CLAIM,
    )
    # save_case may drop Slice1 enablement keys — re-stamp for Request More QA.
    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
    )

    row = _load_case_for_mutation(saved["case_id"])
    if row is not None:
        row["slice1_capability_version"] = int(row.get("slice1_capability_version") or 1) or 1
        row.setdefault("entry_channel", "mini_program")
        row.setdefault("person_link_key", "plk_happy_path_qa")
        _persist_case_after_update(saved["case_id"], row)
        refreshed = get_case_by_id(saved["case_id"])
        if refreshed is not None:
            return refreshed
    return saved


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


# --- Automated Loop 1 Founder QA -------------------------------------------


@pytest.mark.parametrize(
    "injury_raw,expected",
    [
        ("yes", "yes"),
        ("no", "no"),
        ("unknown", "unknown"),
        ("是", "yes"),
        ("否", "no"),
        ("未知", "unknown"),
    ],
)
def test_founder_qa_injury_normalized_yes_no_unknown(injury_raw, expected):
    facts = _complete_known_facts()
    facts["injury_status"] = injury_raw
    case = _claim_case(known_facts=facts)
    brief = build_claim_case_brief(case)
    assert brief["key_facts"]["injury_status"] == expected
    if expected in ("yes", "no"):
        assert brief["can_accept_office_materials"] is True
        assert not any(item.get("key") == "injury_status" for item in brief["missing_info"])
    else:
        # Cap2 treats literal "unknown" value as supplied_unconfirmed (not is_gap);
        # Brief still surfaces injury as unknown for broker scan.
        assert brief["key_facts"]["injury_status"] == "unknown"


def test_founder_qa_all_four_must_haves_present_optional_absent():
    case = _claim_case()
    # Optional photo / VIN / insurance card intentionally absent.
    assert not (case.get("case_attachments") or [])
    facts = case.get("known_facts") or {}
    assert not facts.get("vin")
    assert not facts.get("policy_or_insurance_card")
    checklist = derive_missing_information_checklist(None, case=case)
    must_gaps = [
        i for i in checklist if i["business_class"] == BUSINESS_CLASS_MUST_HAVE and i["is_gap"]
    ]
    assert must_gaps == []
    brief = build_claim_case_brief(case)
    assert brief["can_accept_office_materials"] is True
    # VIN / insurance remain Request More class — not Must Have blockers.
    rm = [i for i in checklist if i["field_key"] in ("vin", "policy_or_insurance_card")]
    assert all(i["business_class"] != BUSINESS_CLASS_MUST_HAVE for i in rm)


@pytest.mark.parametrize("missing_key", sorted(CAP2_MUST_HAVE_OFFICE_KEYS))
def test_founder_qa_one_must_have_missing_blocks_accept(missing_key):
    facts = _complete_known_facts()
    facts.pop(missing_key, None)
    case = _claim_case(known_facts=facts)
    assert office_materials_accept_eligible(case) is False
    with pytest.raises(OfficeMaterialsAcceptError, match="must_have_gaps"):
        accept_office_materials(case["case_id"])


def test_founder_qa_accept_persists_after_reload_and_idempotent():
    case = _claim_case()
    first = accept_office_materials(case["case_id"])
    stamp = first["office_materials_accepted_at"]
    reloaded = get_case_by_id(case["case_id"])
    assert reloaded is not None
    assert reloaded.get("office_materials_accepted_at") == stamp
    events = [
        e
        for e in (reloaded.get("claim_timeline") or [])
        if e.get("event_type") == EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED
    ]
    assert len(events) == 1

    again = accept_office_materials(case["case_id"])
    assert again["already_accepted"] is True
    reloaded2 = get_case_by_id(case["case_id"])
    events2 = [
        e
        for e in (reloaded2.get("claim_timeline") or [])
        if e.get("event_type") == EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED
    ]
    assert len(events2) == 1
    assert reloaded2.get("claim_phase") != "broker_done"
    assert not reloaded2.get("broker_confirmed_at")
    assert not reloaded2.get("case_history_state")


def test_founder_qa_closed_history_rejects_accept():
    from services.fiqa_api.inbox_triage.case_close import close_case

    case = _claim_case()
    close_case(case["case_id"], actor="founder_qa")
    with pytest.raises(OfficeMaterialsAcceptError, match="case_closed"):
        accept_office_materials(case["case_id"])


def test_founder_qa_request_more_still_available_after_office_accept():
    """Office accept must not block Request More (Close/History remain separate)."""
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
        InMemorySlice1Store,
        P20Slice1CommandService,
        STATE_BROKER_MORE_REQUESTED,
    )

    case = _claim_case()
    accepted = accept_office_materials(case["case_id"])
    stamp = accepted["office_materials_accepted_at"]
    row = get_case_by_id(case["case_id"])
    assert row is not None
    assert row.get("office_materials_accepted_at") == stamp

    store = InMemorySlice1Store({row["case_id"]: dict(row)})
    svc = P20Slice1CommandService(store)
    result = svc.accept_request_more(
        case_id=row["case_id"],
        broker_id="office:founder_qa",
        command_id="cmd-hp-rm-1",
        idempotency_key="idem-hp-rm-1",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_vin_hp",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "请补充 VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN after office accept",
        request_id="req_hp_rm_1",
    )
    assert result["outcome"] == "accepted"
    assert store.aggregates[row["case_id"]].workflow_state == STATE_BROKER_MORE_REQUESTED
    # Stamp untouched; not Close / broker_done.
    assert store.cases[row["case_id"]].get("office_materials_accepted_at") == stamp
    assert store.cases[row["case_id"]].get("claim_phase") != "broker_done"
    assert store.cases[row["case_id"]].get("case_history_state") != "history"


# --- Happy Path Loop 2 — customer + broker office-processing presentation ---


def test_loop2_office_processing_customer_copy_and_broker_label():
    from services.fiqa_api.inbox_triage.claim_workbench_display import (
        build_claim_display_status,
    )
    from services.fiqa_api.inbox_triage.constitution_projection import (
        STAGE_WAITING_BROKER,
        ConstitutionInputs,
        build_constitution_projection,
    )

    case = _claim_case()
    accept_office_materials(case["case_id"])
    row = get_case_by_id(case["case_id"])
    assert row is not None

    assert build_claim_display_status(row) == "办公室处理中"

    proj = build_constitution_projection(ConstitutionInputs(case=row))
    customer = proj["customer"]
    assert customer["office_materials_accepted"] is True
    assert customer["office_processing"] is True
    assert customer["current_stage"] == STAGE_WAITING_BROKER
    assert customer["today"] == "先不用操作"
    assert customer["why"] == "资料已齐，等待办公室处理"
    assert customer["after"] == (
        "办公室已收到您的资料，将继续处理。如需补充，我们会再通知您。"
    )
    assert not any(t.get("actionable") for t in (customer.get("tasks") or []))


def test_loop2_open_request_more_overrides_office_processing():
    from services.fiqa_api.inbox_triage.claim_workbench_display import (
        build_claim_display_status,
    )
    from services.fiqa_api.inbox_triage.constitution_projection import (
        STAGE_CUSTOMER_ACTION_NEEDED,
        ConstitutionInputs,
        build_constitution_projection,
    )
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
        InMemorySlice1Store,
        P20Slice1CommandService,
    )

    case = _claim_case()
    accept_office_materials(case["case_id"])
    row = get_case_by_id(case["case_id"])
    assert row is not None

    store = InMemorySlice1Store({row["case_id"]: dict(row)})
    svc = P20Slice1CommandService(store)
    result = svc.accept_request_more(
        case_id=row["case_id"],
        broker_id="office:loop2",
        command_id="cmd-hp-l2-rm",
        idempotency_key="idem-hp-l2-rm",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_vin_l2",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "请补充 VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_hp_l2_rm",
    )
    assert result["outcome"] == "accepted"
    updated = dict(store.cases[row["case_id"]])
    updated["p20_slice1_projection"] = result["customer_projection"]

    assert build_claim_display_status(updated) == "等待客户"

    proj = build_constitution_projection(ConstitutionInputs(case=updated))
    customer = proj["customer"]
    assert customer["office_materials_accepted"] is True
    assert customer["office_processing"] is False
    assert customer["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED
    assert customer["why"] != "资料已齐，等待办公室处理"
    assert customer["today"] not in {"先不用操作", ""}


# --- P0: open Request More must block office acceptance ---------------------


def _stamp_slice1_on_case(case_id: str, projection: dict) -> dict:
    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
    )

    row = _load_case_for_mutation(case_id)
    assert row is not None
    row["p20_slice1_projection"] = projection
    row["slice1_projection"] = projection
    assert _persist_case_after_update(case_id, row)
    refreshed = get_case_by_id(case_id)
    assert refreshed is not None
    return refreshed


def _open_vin_request_more(case_id: str, *, suffix: str = "p0") -> tuple[object, object, dict]:
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
        InMemorySlice1Store,
        P20Slice1CommandService,
        STATE_BROKER_MORE_REQUESTED,
    )

    row = get_case_by_id(case_id)
    assert row is not None
    store = InMemorySlice1Store({case_id: dict(row)})
    svc = P20Slice1CommandService(store)
    created = svc.accept_request_more(
        case_id=case_id,
        broker_id="office:p0_rm_block",
        command_id=f"cmd-p0-rm-{suffix}",
        idempotency_key=f"idem-p0-rm-{suffix}",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": f"item_vin_{suffix}",
                "item_type": "vin",
                "label": "车架号 VIN",
                "instructions": "请补充车架号",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id=f"req_p0_{suffix}",
    )
    assert created["outcome"] == "accepted"
    assert store.aggregates[case_id].workflow_state == STATE_BROKER_MORE_REQUESTED
    projection = created["customer_projection"]
    _stamp_slice1_on_case(case_id, projection)
    return svc, store, projection


def test_p0_open_request_more_blocks_accept_and_brief():
    from services.fiqa_api.inbox_triage.p20_missing_information import (
        office_materials_request_more_block,
    )

    case = _claim_case()
    _svc, _store, projection = _open_vin_request_more(case["case_id"], suffix="block")

    row = get_case_by_id(case["case_id"])
    assert row is not None
    brief = build_claim_case_brief(row)
    assert brief["can_accept_office_materials"] is False
    assert brief["office_materials_ready_suggestion"] is None

    block_code, detail = office_materials_request_more_block(row)
    assert block_code == "office_materials_accept_blocked_open_request_more"
    assert detail["reason"] == "unresolved_request_more"
    assert "VIN" in " ".join(detail.get("open_request", {}).get("unresolved_labels") or [])

    with pytest.raises(OfficeMaterialsAcceptError, match="open_request_more") as excinfo:
        accept_office_materials(case["case_id"])
    assert excinfo.value.detail.get("reason") == "unresolved_request_more"

    persisted = get_case_by_id(case["case_id"])
    assert persisted is not None
    assert persisted.get("office_materials_accepted_at") in (None, "")
    assert persisted.get("claim_phase") != "broker_done"
    assert persisted.get("case_history_state") != "history"
    # Request More left open — not cancelled/satisfied by the blocked accept.
    assert (persisted.get("p20_slice1_projection") or {}).get("workflow_state") == (
        projection.get("workflow_state")
    )


def test_p0_request_more_full_sequence_ack_then_accept_idempotent():
    from services.fiqa_api.inbox_triage.p20_missing_information import (
        EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED,
        EVENT_BROKER_SUPPLEMENT_REVIEWED,
    )
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
        STATE_BROKER_REVIEW_READY,
        STATE_BROKER_REVIEWING,
    )

    case = _claim_case()
    cid = case["case_id"]
    svc, store, _proj = _open_vin_request_more(cid, suffix="seq")

    # Open RM → queue/Brief cannot suggest accept.
    open_row = get_case_by_id(cid)
    assert open_row is not None
    assert build_claim_case_brief(open_row)["can_accept_office_materials"] is False
    with pytest.raises(OfficeMaterialsAcceptError, match="open_request_more"):
        accept_office_materials(cid)

    submitted = svc.submit_request_item(
        case_id=cid,
        customer_id="h5:p0_seq",
        active_request_item_id="item_vin_seq",
        command_id="cmd-p0-submit-seq",
        idempotency_key="idem-p0-submit-seq",
        expected_case_version=store.aggregates[cid].aggregate_version,
        fact={"field": "vin", "value": "4T1B11HK5JU123456"},
    )
    assert submitted["outcome"] == "accepted"
    assert submitted["customer_projection"]["workflow_state"] == STATE_BROKER_REVIEW_READY
    review_row = _stamp_slice1_on_case(cid, submitted["broker_projection"])
    assert build_claim_case_brief(review_row)["can_accept_office_materials"] is False
    with pytest.raises(OfficeMaterialsAcceptError, match="awaiting_supplement_review"):
        accept_office_materials(cid)

    ack = svc.acknowledge_supplement_review(
        case_id=cid,
        broker_id="office:p0_seq",
        command_id="cmd-p0-ack-seq",
        idempotency_key="idem-p0-ack-seq",
    )
    assert ack["outcome"] == "accepted"
    assert ack["event_appended"] is True
    assert ack["broker_projection"]["workflow_state"] == STATE_BROKER_REVIEWING
    # Persist Slice1 + timeline stamp from the in-memory companion onto case SSOT.
    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
    )

    mem = store.cases[cid]
    persist_row = _load_case_for_mutation(cid)
    assert persist_row is not None
    persist_row["p20_slice1_projection"] = ack["broker_projection"]
    persist_row["slice1_projection"] = ack["broker_projection"]
    persist_row["claim_timeline"] = list(mem.get("claim_timeline") or [])
    assert _persist_case_after_update(cid, persist_row)
    ready_row = get_case_by_id(cid)
    assert ready_row is not None
    brief = build_claim_case_brief(ready_row)
    assert brief["can_accept_office_materials"] is True
    assert brief["office_materials_ready_suggestion"] == OFFICE_MATERIALS_READY_SUGGESTION

    first = accept_office_materials(cid)
    assert first["already_accepted"] is False
    assert first["event_appended"] is True
    stamp = first["office_materials_accepted_at"]
    assert stamp

    ack_again = svc.acknowledge_supplement_review(
        case_id=cid,
        broker_id="office:p0_seq",
        command_id="cmd-p0-ack-seq-2",
        idempotency_key="idem-p0-ack-seq-2",
    )
    assert ack_again["already_acknowledged"] is True
    assert ack_again["event_appended"] is False
    mem_timeline = store.cases[cid].get("claim_timeline") or []
    assert len([e for e in mem_timeline if e.get("event_type") == EVENT_BROKER_SUPPLEMENT_REVIEWED]) == 1

    second = accept_office_materials(cid)
    assert second["already_accepted"] is True
    assert second["event_appended"] is False
    assert second["office_materials_accepted_at"] == stamp

    final = get_case_by_id(cid)
    assert final is not None
    timeline = final.get("claim_timeline") or []
    assert len([e for e in timeline if e.get("event_type") == EVENT_BROKER_SUPPLEMENT_REVIEWED]) == 1
    assert len([e for e in timeline if e.get("event_type") == EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED]) == 1
    assert final.get("claim_phase") != "broker_done"
    assert final.get("case_history_state") != "history"
    assert final.get("case_status") != "closed"


# --- Pilot Reliability Fix 1 — atomic office accept -------------------------


def _accept_events(case: dict | None) -> list[dict]:
    timeline = (case or {}).get("claim_timeline") or []
    return [e for e in timeline if e.get("event_type") == EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED]


def test_atomic_accept_normal_once():
    case = _claim_case()
    result = accept_office_materials(case["case_id"], source="workbench")
    assert result["outcome"] == "office_materials_accepted"
    assert result["already_accepted"] is False
    assert result["event_appended"] is True
    stamp = result["office_materials_accepted_at"]
    assert stamp
    persisted = get_case_by_id(case["case_id"])
    assert persisted is not None
    assert persisted.get("office_materials_accepted_at") == stamp
    assert len(_accept_events(persisted)) == 1


def test_atomic_accept_sequential_double_idempotent():
    case = _claim_case()
    first = accept_office_materials(case["case_id"])
    second = accept_office_materials(case["case_id"])
    assert first["already_accepted"] is False
    assert first["event_appended"] is True
    assert second["already_accepted"] is True
    assert second["event_appended"] is False
    assert second["office_materials_accepted_at"] == first["office_materials_accepted_at"]
    persisted = get_case_by_id(case["case_id"])
    assert len(_accept_events(persisted)) == 1


def test_atomic_accept_concurrent_double_one_effect():
    """True in-process concurrency against the JSON accept lock path.

    Limitation: this does not exercise a live multi-connection Postgres
    ``FOR UPDATE`` race. Paid-pilot PG path uses ``mutate_full_case_under_lock``;
    see ``test_atomic_accept_db_path_lock_reread_before_mutate``.
    """
    import threading

    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
    )

    case = _claim_case()
    cid = case["case_id"]
    row = _load_case_for_mutation(cid)
    assert row is not None
    row["contact_note"] = "sibling-note-keep"
    row["customer_name"] = "陈测试"
    row["policy_context"] = {"status": "confirmed", "customer_choice": "use_on_file"}
    assert _persist_case_after_update(cid, row)

    barrier = threading.Barrier(2)
    results: list[dict] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def _worker() -> None:
        try:
            barrier.wait(timeout=5)
            out = accept_office_materials(cid, source="workbench")
            with lock:
                results.append(out)
        except BaseException as exc:  # noqa: BLE001 — collect any worker failure
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
        assert not t.is_alive()

    assert errors == []
    assert len(results) == 2
    accepted = [r for r in results if r.get("already_accepted") is False]
    replayed = [r for r in results if r.get("already_accepted") is True]
    assert len(accepted) == 1
    assert len(replayed) == 1
    assert accepted[0].get("event_appended") is True
    assert replayed[0].get("event_appended") is False
    stamp = accepted[0]["office_materials_accepted_at"]
    assert stamp
    assert replayed[0]["office_materials_accepted_at"] == stamp

    final = get_case_by_id(cid)
    assert final is not None
    assert final.get("office_materials_accepted_at") == stamp
    assert len(_accept_events(final)) == 1
    assert final.get("contact_note") == "sibling-note-keep"
    assert final.get("customer_name") == "陈测试"
    assert (final.get("policy_context") or {}).get("customer_choice") == "use_on_file"


def test_atomic_accept_blocked_open_request_more_no_stamp():
    case = _claim_case()
    cid = case["case_id"]
    _open_vin_request_more(cid, suffix="atomic_rm")
    with pytest.raises(OfficeMaterialsAcceptError, match="open_request_more"):
        accept_office_materials(cid)
    persisted = get_case_by_id(cid)
    assert persisted is not None
    assert not persisted.get("office_materials_accepted_at")
    assert _accept_events(persisted) == []


def test_atomic_accept_blocked_must_have_gap_no_partial_mutation():
    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
    )

    case = _claim_case(known_facts={"accident_description": "only story"})
    cid = case["case_id"]
    row = _load_case_for_mutation(cid)
    assert row is not None
    row["contact_note"] = "gap-sibling"
    assert _persist_case_after_update(cid, row)

    with pytest.raises(OfficeMaterialsAcceptError, match="must_have_gaps"):
        accept_office_materials(cid)
    persisted = get_case_by_id(cid)
    assert persisted is not None
    assert not persisted.get("office_materials_accepted_at")
    assert _accept_events(persisted) == []
    assert persisted.get("contact_note") == "gap-sibling"
    assert (persisted.get("known_facts") or {}).get("accident_description") == "only story"


def test_atomic_accept_preserves_sibling_fields():
    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
        build_claim_timeline_event,
    )

    case = _claim_case()
    cid = case["case_id"]
    row = _load_case_for_mutation(cid)
    assert row is not None
    row["contact_note"] = "keep-me"
    row["customer_name"] = "Sibling Customer"
    row["customer_phone"] = "9495550199"
    row["policy_context"] = {"status": "confirmed", "customer_choice": "use_on_file"}
    row["accident_story_assistant"] = {
        "authority": "customer_confirmed",
        "ai_involved": True,
    }
    prior = build_claim_timeline_event(
        event_type="claim_started",
        source_channel="mini_program",
        actor="customer",
        text="案件已开始",
    )
    row["claim_timeline"] = [prior]
    row["demo_name"] = "atomic_sibling_demo"
    assert _persist_case_after_update(cid, row)

    result = accept_office_materials(cid)
    assert result["already_accepted"] is False
    final = get_case_by_id(cid)
    assert final is not None
    assert final.get("contact_note") == "keep-me"
    assert final.get("customer_name") == "Sibling Customer"
    assert final.get("customer_phone") == "9495550199"
    assert (final.get("policy_context") or {}).get("status") == "confirmed"
    assert (final.get("accident_story_assistant") or {}).get("authority") == "customer_confirmed"
    assert final.get("demo_name") == "atomic_sibling_demo"
    types = [e.get("event_type") for e in (final.get("claim_timeline") or [])]
    assert types.count("claim_started") == 1
    assert types.count(EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED) == 1


def test_atomic_accept_db_path_lock_reread_before_mutate(monkeypatch):
    """PG-primary path must mutate only the case loaded under lock (not a stale snapshot)."""
    from services.fiqa_api.inbox_triage import case_store as cs

    case = _claim_case(contact_note="pre-lock-sibling")
    cid = case["case_id"]
    order: list[str] = []
    locked_case = {
        "case_id": cid,
        "service_lane": SERVICE_LANE_CLAIM,
        "known_facts": _complete_known_facts(),
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "office_materials_accepted_at": None,
        "claim_timeline": [],
        "contact_note": "locked-authoritative-sibling",
        "customer_name": "FromLockedRead",
        "slice1_capability_version": 1,
        "entry_channel": "mini_program",
    }

    def _fake_mutate(case_id: str, mutator):
        order.append("lock_and_load")
        assert case_id == cid
        # Authoritative state under lock — includes sibling not present on stale clients.
        result, should_persist = mutator(locked_case)
        order.append("mutated")
        assert should_persist is True
        assert locked_case.get("office_materials_accepted_at")
        assert locked_case.get("contact_note") == "locked-authoritative-sibling"
        order.append("persist_under_same_txn")
        return result

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.db_primary_writes_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.mutate_full_case_under_lock",
        _fake_mutate,
    )

    result = cs.accept_office_materials(cid)
    assert order == ["lock_and_load", "mutated", "persist_under_same_txn"]
    assert result["already_accepted"] is False
    assert result["event_appended"] is True
    assert (result.get("case") or {}).get("contact_note") == "locked-authoritative-sibling"
    assert (result.get("case") or {}).get("customer_name") == "FromLockedRead"
    assert len(_accept_events(result.get("case"))) == 1
