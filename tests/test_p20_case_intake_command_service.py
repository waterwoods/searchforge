"""P20 Capability 2 — Create Claim, missing-information, request draft."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    EVENT_CASE_CREATED,
    EVENT_REQUEST_DRAFT_SAVED,
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_missing_information import (
    FACT_STATUS_CONFIRMED,
    FACT_STATUS_MISSING,
    FACT_STATUS_NEEDS_CORRECTION,
    FACT_STATUS_NOT_APPLICABLE,
    FACT_STATUS_SUPPLIED_UNCONFIRMED,
    apply_fact_status_update,
    derive_missing_information_checklist,
    seed_fact_records_from_case,
)


def _svc() -> tuple[P20CaseIntakeCommandService, InMemoryIntakeStore]:
    store = InMemoryIntakeStore()
    return P20CaseIntakeCommandService(store), store


def test_create_incomplete_claim_and_missing_vin():
    svc, store = _svc()
    result = svc.create_claim(
        broker_id="office:demo",
        office_id="demo-office",
        tenant_id="tenant-demo",
        command_id="cmd-create-0001",
        idempotency_key="idem-create-0001",
        inputs={"is_test": True, "customer_name": "QA Customer"},
    )
    assert result["outcome"] == "accepted"
    assert result["aggregate_version"] == 2
    case_id = result["case_id"]
    assert case_id in store.cases
    assert store.cases[case_id]["workbench_test"] is True
    assert store.cases[case_id]["exclude_from_production_metrics"] is True
    checklist = result["broker_projection"]["missing_information_checklist"]
    vin = next(i for i in checklist if i["field_key"] == "vin")
    assert vin["status"] == FACT_STATUS_MISSING
    assert result["customer_projection"]["customer_next_action"] is None
    assert store.open_requests.get(case_id) is None
    assert any(e["event_type"] == EVENT_CASE_CREATED for e in store.events[case_id])


def test_duplicate_create_command_replays_same_outcome():
    svc, store = _svc()
    first = svc.create_claim(
        broker_id="office:demo",
        office_id="demo-office",
        tenant_id="tenant-demo",
        command_id="cmd-create-dup",
        idempotency_key="idem-create-dup",
        inputs={"is_test": True},
    )
    second = svc.create_claim(
        broker_id="office:demo",
        office_id="demo-office",
        tenant_id="tenant-demo",
        command_id="cmd-create-dup",
        idempotency_key="idem-create-dup",
        inputs={"is_test": True},
    )
    assert second["outcome"] == "replayed"
    assert second["case_id"] == first["case_id"]
    assert len(store.cases) == 1


def test_confirmed_fact_not_marked_missing():
    records = seed_fact_records_from_case({"known_facts": {"vin": "1HGCM82633A004352"}})
    records["vin"]["status"] = FACT_STATUS_CONFIRMED
    checklist = derive_missing_information_checklist(records)
    vin = next(i for i in checklist if i["field_key"] == "vin")
    assert vin["status"] == FACT_STATUS_CONFIRMED
    assert vin["suggested_for_request"] is False


def test_needs_correction_preserves_old_fact():
    records = seed_fact_records_from_case({"known_facts": {"vin": "OLDVIN12345678901"}})
    updated = apply_fact_status_update(
        records,
        field_key="vin",
        status=FACT_STATUS_NEEDS_CORRECTION,
        reason="typo",
    )
    assert updated["vin"]["previous_value"] == "OLDVIN12345678901"
    assert updated["vin"]["status"] == FACT_STATUS_NEEDS_CORRECTION
    with pytest.raises(ValueError, match="confirmed_fact_cannot_be_marked_missing"):
        apply_fact_status_update(
            {"vin": {"status": FACT_STATUS_CONFIRMED, "value": "1HGCM82633A004352"}},
            field_key="vin",
            status=FACT_STATUS_MISSING,
        )


def test_request_draft_save_update_and_no_request_more():
    svc, store = _svc()
    created = svc.create_claim(
        broker_id="office:demo",
        office_id="demo-office",
        tenant_id="tenant-demo",
        command_id="cmd-create-draft",
        idempotency_key="idem-create-draft",
        inputs={"is_test": True},
    )
    case_id = created["case_id"]
    saved = svc.save_request_draft(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-draft-1",
        idempotency_key="idem-draft-1",
        expected_case_version=2,
        items=[
            {
                "field_key": "vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Please send VIN",
                "position": 1,
                "selected": True,
            }
        ],
    )
    assert saved["outcome"] == "accepted"
    assert saved["aggregate_version"] == 3
    assert store.drafts[case_id].items[0]["field_key"] == "vin"
    assert store.open_requests.get(case_id) is None
    assert saved["broker_projection"]["customer_next_action"] is None
    assert any(e["event_type"] == EVENT_REQUEST_DRAFT_SAVED for e in store.events[case_id])

    replay = svc.save_request_draft(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-draft-1",
        idempotency_key="idem-draft-1",
        expected_case_version=2,
        items=[
            {
                "field_key": "vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Please send VIN",
                "position": 1,
                "selected": True,
            }
        ],
    )
    assert replay["outcome"] == "replayed"

    conflict = svc.save_request_draft(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-draft-2",
        idempotency_key="idem-draft-2",
        expected_case_version=2,
        items=[
            {
                "field_key": "vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "updated",
                "position": 1,
                "selected": True,
            }
        ],
    )
    assert conflict["outcome"] == "conflict"
    assert conflict["error_code"] == "version_conflict"


def test_version_conflict_and_transaction_rollback():
    svc, store = _svc()
    created = svc.create_claim(
        broker_id="office:demo",
        office_id="demo-office",
        tenant_id="tenant-demo",
        command_id="cmd-create-rb",
        idempotency_key="idem-create-rb",
        inputs={"is_test": True},
    )
    case_id = created["case_id"]
    store.fail_next_write = True
    with pytest.raises(RuntimeError, match="forced_write_failure"):
        # Force failure during a subsequent create to prove rollback path.
        svc.create_claim(
            broker_id="office:demo",
            office_id="demo-office",
            tenant_id="tenant-demo",
            command_id="cmd-create-rb-2",
            idempotency_key="idem-create-rb-2",
            inputs={"is_test": True},
        )
    assert len(store.cases) == 1
    assert case_id in store.cases


def test_not_applicable_and_supplied_unconfirmed_seed():
    seeded = seed_fact_records_from_case({"known_facts": {"vin": "1HGCM82633A004352"}})
    assert seeded["vin"]["status"] == FACT_STATUS_SUPPLIED_UNCONFIRMED
    updated = apply_fact_status_update(
        seeded,
        field_key="photo_evidence",
        status=FACT_STATUS_NOT_APPLICABLE,
        reason="single-vehicle, no scene photos available",
    )
    assert updated["photo_evidence"]["status"] == FACT_STATUS_NOT_APPLICABLE


def test_active_request_more_blocks_draft_save():
    svc, store = _svc()
    created = svc.create_claim(
        broker_id="office:demo",
        office_id="demo-office",
        tenant_id="tenant-demo",
        command_id="cmd-create-open",
        idempotency_key="idem-create-open",
        inputs={"is_test": True},
    )
    case_id = created["case_id"]
    store.open_requests[case_id] = {"request_id": "req_open", "status": "open"}
    result = svc.save_request_draft(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-draft-open",
        idempotency_key="idem-draft-open",
        expected_case_version=2,
        items=[
            {
                "field_key": "vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "",
                "position": 1,
                "selected": True,
            }
        ],
    )
    assert result["outcome"] == "rejected"
    assert result["error_code"] == "active_request_more_exists"
