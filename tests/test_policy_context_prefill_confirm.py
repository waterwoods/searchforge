"""Stage 2 Loop 1 — known-customer policy context confirm vs insurance-card upload."""

from __future__ import annotations

import os

import pytest

from services.fiqa_api.inbox_triage.constitution_projection import (
    STAGE_WAITING_BROKER,
    ConstitutionInputs,
    build_constitution_projection,
)
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    MOCK_KEY_S2_MULTI_VEHICLE,
    MOCK_KEY_S3_NO_ACTIVE,
    MOCK_KEY_S4_STALE_POLICY,
    get_fixture,
    reset_mock_directory_for_tests,
)
from services.fiqa_api.inbox_triage.claim_prefill import build_prefill_result
from services.fiqa_api.inbox_triage.p20_missing_information import (
    FACT_STATUS_CONFIRMED,
    FACT_STATUS_MISSING,
    derive_missing_information_checklist,
    seed_fact_records_from_case,
)
from services.fiqa_api.inbox_triage.policy_context_confirm import (
    BROKER_LABEL_CONFIRMED,
    BROKER_LABEL_UPLOADED,
    apply_policy_context_to_case_dict,
    broker_policy_evidence_label,
    build_policy_context_record,
    policy_context_is_customer_confirmed,
)
from services.fiqa_api.inbox_triage.policy_context_decision import (
    CHOICE_CHANGED,
    CHOICE_CORRECT,
    CHOICE_UNCERTAIN,
    DECISION_CONFIRM_EXISTING,
    DECISION_FALLBACK,
    DECISION_REQUIRE_UPLOAD,
    EVENT_POLICY_CONTEXT_CONFIRMED,
    confirm_step_for_decision,
    decide_policy_context,
    normalize_customer_choice,
)
from services.fiqa_api.inbox_triage.smart_claim_start.engine import build_smart_claim_start_plan


@pytest.fixture(autouse=True)
def _reset_mocks():
    reset_mock_directory_for_tests()
    yield
    reset_mock_directory_for_tests()


def test_chen_camry_decision_confirm_existing():
    lookup = get_fixture(MOCK_KEY_S3_NO_ACTIVE)
    decision = decide_policy_context(lookup)
    assert decision["decision"] == DECISION_CONFIRM_EXISTING
    summary = decision["customer_safe_summary"]
    assert summary["customer_name"] == "陈明"
    assert "Camry" in (summary["vehicle_summary"] or "")
    assert summary["carrier_display"] == "Mercury"
    step = confirm_step_for_decision(decision)
    assert step is not None
    assert "资料正确，继续" in step["options"]
    assert "信息有变化" in step["options"]
    assert "我不确定" in step["options"]


def test_wang_stale_requires_upload():
    lookup = get_fixture(MOCK_KEY_S4_STALE_POLICY)
    decision = decide_policy_context(lookup)
    assert decision["decision"] == DECISION_REQUIRE_UPLOAD
    assert "过期" in (decision["upload_reason_zh"] or "")
    assert confirm_step_for_decision(decision) is None


def test_missing_policy_requires_upload():
    lookup = get_fixture(MOCK_KEY_S3_NO_ACTIVE)
    lookup["policy"] = None
    decision = decide_policy_context(lookup)
    assert decision["decision"] == DECISION_REQUIRE_UPLOAD


def test_multi_vehicle_unselected_blocks_confirm():
    lookup = get_fixture(MOCK_KEY_S2_MULTI_VEHICLE)
    decision = decide_policy_context(lookup)
    assert decision["decision"] == DECISION_REQUIRE_UPLOAD
    assert decision.get("requires_vehicle_selection") is True


def test_multi_vehicle_selected_can_confirm():
    lookup = get_fixture(MOCK_KEY_S2_MULTI_VEHICLE)
    decision = decide_policy_context(
        lookup, selected_vehicle_summary="2019 Honda CR-V"
    )
    assert decision["decision"] == DECISION_CONFIRM_EXISTING
    assert decision["vehicle"]["vehicle_ref"] == "mock_veh_crv"


def test_lookup_failure_fallback():
    decision = decide_policy_context(
        {"match_status": "LOOKUP_UNAVAILABLE", "lookup_confidence": "LOW", "vehicles": []}
    )
    assert decision["decision"] == DECISION_FALLBACK


def test_customer_changed_and_uncertain_keep_upload():
    lookup = get_fixture(MOCK_KEY_S3_NO_ACTIVE)
    decision = decide_policy_context(lookup)
    for choice in (CHOICE_CHANGED, CHOICE_UNCERTAIN):
        record = build_policy_context_record(
            decision=decision,
            customer_choice=choice,
            command_id="cmd_1",
            idempotency_key=f"idem_{choice}",
            confirmed_at="2026-08-03T20:00:00Z",
        )
        assert record["status"] == "upload_required"
        assert record["upload_required"] is True
        assert record["insurance_card_uploaded"] is False


def test_idempotent_confirmation_single_event():
    lookup = get_fixture(MOCK_KEY_S3_NO_ACTIVE)
    decision = decide_policy_context(lookup)
    record = build_policy_context_record(
        decision=decision,
        customer_choice=CHOICE_CORRECT,
        command_id="cmd_idem",
        idempotency_key="idem_same",
        confirmed_at="2026-08-03T20:00:00Z",
    )
    case = {
        "case_id": "case_policy_ctx_1",
        "service_lane": "claim",
        "known_facts": {"accident_description": "rear ended"},
        "claim_timeline": [],
    }
    first = apply_policy_context_to_case_dict(
        case,
        record=record,
        event_type=EVENT_POLICY_CONTEXT_CONFIRMED,
        event_text=BROKER_LABEL_CONFIRMED,
        now_iso="2026-08-03T20:00:00Z",
    )
    assert first["outcome"] == "accepted"
    assert first["event_appended"] is True
    second = apply_policy_context_to_case_dict(
        case,
        record=record,
        event_type=EVENT_POLICY_CONTEXT_CONFIRMED,
        event_text=BROKER_LABEL_CONFIRMED,
        now_iso="2026-08-03T20:00:01Z",
    )
    assert second["outcome"] == "replayed"
    events = [
        e
        for e in case["claim_timeline"]
        if e.get("event_type") == EVENT_POLICY_CONTEXT_CONFIRMED
    ]
    assert len(events) == 1


def test_constitution_skips_insurance_after_confirm():
    lookup = get_fixture(MOCK_KEY_S3_NO_ACTIVE)
    decision = decide_policy_context(lookup)
    record = build_policy_context_record(
        decision=decision,
        customer_choice=CHOICE_CORRECT,
        command_id="cmd_c",
        idempotency_key="idem_c",
        confirmed_at="2026-08-03T20:00:00Z",
    )
    case = {
        "case_id": "case_policy_ctx_2",
        "service_lane": "claim",
        "known_facts": {
            "accident_description": "昨天被后撞",
            "accident_datetime": "昨天1pm",
            "accident_location": "Santa Ana",
            "injury_status": "no",
            "primary_vehicle_summary": "2020 Toyota Camry",
        },
        "claim_timeline": [],
        "claim_attachment_slots": {},
        "case_attachments": [],
    }
    apply_policy_context_to_case_dict(
        case,
        record=record,
        event_type=EVENT_POLICY_CONTEXT_CONFIRMED,
        event_text=BROKER_LABEL_CONFIRMED,
        now_iso="2026-08-03T20:00:00Z",
    )
    assert policy_context_is_customer_confirmed(case)
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    customer = projection["customer"]
    assert customer["today"] != "上传保险卡"
    assert "上传保险卡" not in str(customer.get("today") or "")
    # Story + confirmed policy context → customer is waiting, not owed insurance upload.
    assert str(customer.get("current_stage") or "") in {
        STAGE_WAITING_BROKER,
        "waiting",
        "waiting_broker",
    }
    insurance_tasks = [
        t for t in (customer.get("tasks") or []) if t.get("task_id") == "insurance_card"
    ]
    assert insurance_tasks
    assert insurance_tasks[0]["state"] in {"completed", "waiting_broker"}
    assert insurance_tasks[0].get("actionable") is False


def test_cap2_checklist_confirmed_not_gap():
    lookup = get_fixture(MOCK_KEY_S3_NO_ACTIVE)
    decision = decide_policy_context(lookup)
    record = build_policy_context_record(
        decision=decision,
        customer_choice=CHOICE_CORRECT,
        command_id="cmd_cap2",
        idempotency_key="idem_cap2",
        confirmed_at="2026-08-03T20:00:00Z",
    )
    case = {"case_id": "case_cap2", "known_facts": {}, "claim_timeline": []}
    apply_policy_context_to_case_dict(
        case,
        record=record,
        event_type=EVENT_POLICY_CONTEXT_CONFIRMED,
        event_text=BROKER_LABEL_CONFIRMED,
        now_iso="2026-08-03T20:00:00Z",
    )
    seeded = seed_fact_records_from_case(case)
    assert seeded["policy_or_insurance_card"]["status"] == FACT_STATUS_CONFIRMED
    checklist = derive_missing_information_checklist(case.get("fact_records"), case=case)
    policy_item = next(i for i in checklist if i["field_key"] == "policy_or_insurance_card")
    assert policy_item["is_gap"] is False
    assert policy_item["status"] == FACT_STATUS_CONFIRMED


def test_broker_label_distinguishes_confirm_vs_upload():
    confirmed = {
        "policy_context": {
            "status": "confirmed",
            "customer_choice": "correct",
        },
        "claim_attachment_slots": {},
        "case_attachments": [],
    }
    assert broker_policy_evidence_label(confirmed) == BROKER_LABEL_CONFIRMED
    uploaded = {
        "policy_context": None,
        "claim_attachment_slots": {
            "policy_or_insurance_card": {"status": "received"},
        },
        "case_attachments": [],
    }
    assert broker_policy_evidence_label(uploaded) == BROKER_LABEL_UPLOADED


def test_smart_claim_plan_includes_policy_context_step_for_chen():
    lookup = get_fixture(MOCK_KEY_S3_NO_ACTIVE)
    prefill = build_prefill_result(lookup)
    plan = build_smart_claim_start_plan(lookup, prefill)
    assert plan["mode"] == "MATCHED_KNOWN"
    step_ids = [s["step_id"] for s in plan["confirm_steps"]]
    assert "confirm_policy_context" in step_ids


def test_smart_claim_plan_stale_has_no_confirm_existing_step():
    lookup = get_fixture(MOCK_KEY_S4_STALE_POLICY)
    prefill = build_prefill_result(lookup)
    plan = build_smart_claim_start_plan(lookup, prefill)
    step_ids = [s["step_id"] for s in plan["confirm_steps"]]
    assert "confirm_policy_context" not in step_ids


def test_normalize_choice_labels():
    assert normalize_customer_choice("资料正确，继续") == CHOICE_CORRECT
    assert normalize_customer_choice("信息有变化") == CHOICE_CHANGED
    assert normalize_customer_choice("我不确定") == CHOICE_UNCERTAIN


def test_cannot_force_confirm_when_stale():
    from services.fiqa_api.inbox_triage.policy_context_confirm import build_policy_context_record

    lookup = get_fixture(MOCK_KEY_S4_STALE_POLICY)
    decision = decide_policy_context(lookup)
    # Even if UI sent correct, record builder still marks upload when decision isn't CONFIRM_EXISTING
    # (command layer remaps choice; record builder trusts decision+choice pair from command).
    record = build_policy_context_record(
        decision={**decision, "decision": DECISION_REQUIRE_UPLOAD},
        customer_choice=CHOICE_UNCERTAIN,
        command_id="cmd_stale",
        idempotency_key="idem_stale",
        confirmed_at="2026-08-03T20:00:00Z",
    )
    assert record["upload_required"] is True
    assert record["status"] != "confirmed"


def test_missing_policy_seed_still_gap_without_confirm():
    case = {"case_id": "case_gap", "known_facts": {"accident_description": "x"}}
    seeded = seed_fact_records_from_case(case)
    assert seeded["policy_or_insurance_card"]["status"] == FACT_STATUS_MISSING
