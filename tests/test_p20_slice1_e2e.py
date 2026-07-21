"""P20 Slice 1 end-to-end integration scenarios (Step 4).

Covers broker → command → events → customer projection → submit → broker review
parity without requiring live Postgres.
"""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    GROUP_STATUS_OPEN,
    ITEM_STATUS_ACTIVE,
    ITEM_STATUS_QUEUED,
    ITEM_STATUS_SATISFIED,
    InMemorySlice1Store,
    P20Slice1CommandService,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _case(*, enabled: bool = True, case_id: str = "case_e2e") -> dict:
    row = {
        "case_id": case_id,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-15T12:00:00Z",
    }
    if enabled:
        row["slice1_capability_version"] = 1
    return row


def _svc(*, enabled: bool = True, case_id: str = "case_e2e") -> tuple[P20Slice1CommandService, InMemorySlice1Store]:
    store = InMemorySlice1Store({case_id: _case(enabled=enabled, case_id=case_id)})
    return P20Slice1CommandService(store), store


def _item(
    label: str,
    position: int,
    item_type: str,
    *,
    request_item_id: str | None = None,
) -> dict:
    return {
        "request_item_id": request_item_id or f"item_{position}",
        "item_type": item_type,
        "label": label,
        "instructions": f"Please provide {label}",
        "required": True,
        "position": position,
    }


def _create(
    svc: P20Slice1CommandService,
    *,
    case_id: str = "case_e2e",
    items: list[dict] | None = None,
    command_id: str = "cmd-broker-create",
    idempotency_key: str = "idem-broker-create",
    expected: int = 0,
    request_id: str = "req_e2e",
) -> dict:
    return svc.accept_request_more(
        case_id=case_id,
        broker_id="office:demo",
        command_id=command_id,
        idempotency_key=idempotency_key,
        expected_case_version=expected,
        requested_items=items
        or [
            _item("VIN", 1, "vin"),
        ],
        reason="Need structured follow-up",
        request_id=request_id,
    )


def _submit_fact(
    svc: P20Slice1CommandService,
    *,
    item_id: str,
    expected: int,
    field: str = "vin",
    value: str = "1HGCM82633A004352",
    command_id: str = "cmd-customer-submit",
    idempotency_key: str = "idem-customer-submit",
    case_id: str = "case_e2e",
) -> dict:
    return svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:demo",
        active_request_item_id=item_id,
        command_id=command_id,
        idempotency_key=idempotency_key,
        expected_case_version=expected,
        client_draft_id="draft_e2e",
        fact={"field": field, "value": value},
    )


def _submit_evidence(
    svc: P20Slice1CommandService,
    *,
    item_id: str,
    expected: int,
    attachment_id: str,
    command_id: str,
    idempotency_key: str,
    case_id: str = "case_e2e",
) -> dict:
    return svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:demo",
        active_request_item_id=item_id,
        command_id=command_id,
        idempotency_key=idempotency_key,
        expected_case_version=expected,
        client_draft_id="draft_e2e",
        evidence={"attachment_id": attachment_id},
    )


def _assert_projection_parity(result: dict) -> None:
    customer = result["customer_projection"]
    broker = result["broker_projection"]
    assert customer["case_id"] == broker["case_id"]
    assert customer["workflow_state"] == broker["workflow_state"]
    assert customer["aggregate_version"] == broker["aggregate_version"]
    assert customer["request_progress"] == broker["request_progress"]
    assert (customer.get("open_request") or {}).get("request_id") == (
        (broker.get("open_request") or {}).get("request_id")
    )
    assert customer["customer_next_action"]["action_type"] == broker["customer_next_action"]["action_type"]
    assert broker["broker_next_action"]["action_type"]
    assert customer["aggregate_version"] == result["aggregate_version"]


def test_scenario1_single_fact_request_returns_to_broker_review():
    svc, store = _svc()
    created = _create(svc)
    _assert_projection_parity(created)
    assert created["customer_projection"]["customer_next_action"]["required_input"] == "vin"
    assert created["broker_projection"]["broker_next_action"]["action_type"] == "wait_for_customer_item"

    submitted = _submit_fact(svc, item_id="item_1", expected=created["aggregate_version"])
    _assert_projection_parity(submitted)

    assert submitted["outcome"] == "accepted"
    assert submitted["customer_projection"]["workflow_state"] == "broker_review_ready"
    assert submitted["customer_projection"]["customer_next_action"]["action_type"] == "wait_for_broker_review"
    assert submitted["broker_projection"]["broker_next_action"]["action_type"] == "review_customer_response"
    vin_response = submitted["broker_projection"]["open_request"]["items"][0]["customer_response"]
    assert vin_response["submitted_value"] == "1HGCM82633A004352"
    assert vin_response["applied_to_canonical_facts"] is True
    assert store.groups["req_e2e"].status == GROUP_STATUS_COMPLETED
    assert store.items["item_1"].status == ITEM_STATUS_SATISFIED

    types = [event["event_type"] for event in store.events["case_e2e"]]
    assert types == [
        "broker_request_more_created",
        "customer_continue_started",
        "field_saved",
        "customer_request_item_satisfied",
        "supplement_submitted",
    ]
    assert all(event["command_id"] for event in store.events["case_e2e"])
    assert store.events["case_e2e"][0]["actor"] == "broker"
    assert store.events["case_e2e"][-1]["state_after"] == "broker_review_ready"


def test_scenario2_vin_then_insurance_card_then_photo_blocked():
    svc, store = _svc()
    items = [
        _item("VIN", 1, "vin"),
        _item("Insurance card", 2, "policy_or_insurance_card"),
        _item("Damage photos", 3, "photo_evidence"),
    ]
    created = _create(svc, items=items)
    cust = created["customer_projection"]
    assert cust["customer_next_action"]["request_item_id"] == "item_1"
    assert cust["customer_next_action"]["action_type"] == "provide_fact"

    step1 = _submit_fact(svc, item_id="item_1", expected=created["aggregate_version"])
    assert step1["outcome"] == "accepted"
    assert step1["customer_projection"]["customer_next_action"]["request_item_id"] == "item_2"
    assert step1["customer_projection"]["customer_next_action"]["required_input"] == "policy_or_insurance_card"
    assert store.items["item_2"].status == ITEM_STATUS_ACTIVE

    step2 = _submit_evidence(
        svc,
        item_id="item_2",
        expected=step1["aggregate_version"],
        attachment_id="att_insurance_1",
        command_id="cmd-customer-submit-2",
        idempotency_key="idem-customer-submit-2",
    )
    assert step2["outcome"] == "accepted"
    assert store.items["item_2"].status == ITEM_STATUS_SATISFIED
    assert step2["customer_projection"]["customer_next_action"]["request_item_id"] == "item_3"
    assert step2["customer_projection"]["customer_next_action"]["required_input"] == "photo_evidence"
    assert store.items["item_3"].status == ITEM_STATUS_ACTIVE
    assert store.groups["req_e2e"].status == GROUP_STATUS_OPEN

    blocked = _submit_evidence(
        svc,
        item_id="item_3",
        expected=step2["aggregate_version"],
        attachment_id="att_damage_1",
        command_id="cmd-customer-submit-3",
        idempotency_key="idem-customer-submit-3",
    )
    assert blocked["outcome"] == "rejected"
    assert blocked["error_code"] == "customer_submit_not_supported"
    assert store.items["item_3"].status == ITEM_STATUS_ACTIVE
    assert store.groups["req_e2e"].status == GROUP_STATUS_OPEN


def test_scenario3_duplicate_broker_submit_replays_without_duplicate_effects():
    svc, store = _svc()
    first = _create(svc)
    second = _create(svc)
    assert second["outcome"] == "replayed"
    assert second["event_ids"] == first["event_ids"]
    assert len(store.groups) == 1
    assert len(store.items) == 1
    assert len(store.events["case_e2e"]) == 1
    assert [event["event_type"] for event in store.events["case_e2e"]] == ["broker_request_more_created"]


def test_scenario4_duplicate_customer_submit_replays_without_skipping_queue():
    svc, store = _svc()
    created = _create(
        svc,
        items=[
            _item("VIN", 1, "vin"),
            _item("Insurance card", 2, "policy_or_insurance_card"),
        ],
    )
    first = _submit_fact(svc, item_id="item_1", expected=created["aggregate_version"])
    count_after = len(store.events["case_e2e"])
    second = _submit_fact(svc, item_id="item_1", expected=created["aggregate_version"])
    assert second["outcome"] == "replayed"
    assert second["event_ids"] == first["event_ids"]
    assert len(store.events["case_e2e"]) == count_after
    assert store.items["item_1"].status == ITEM_STATUS_SATISFIED
    assert store.items["item_2"].status == ITEM_STATUS_ACTIVE
    assert first["customer_projection"]["customer_next_action"]["request_item_id"] == "item_2"
    assert second["customer_projection"]["customer_next_action"]["request_item_id"] == "item_2"


def test_scenario5_version_conflict_is_structured_and_non_mutating():
    svc, store = _svc()
    created = _create(svc)
    before_events = list(store.events["case_e2e"])
    conflict = _submit_fact(
        svc,
        item_id="item_1",
        expected=999,
        command_id="cmd-stale",
        idempotency_key="idem-stale",
    )
    assert conflict["outcome"] == "conflict"
    assert conflict["error_code"] == "version_conflict"
    assert conflict["customer_projection"]["aggregate_version"] == created["aggregate_version"]
    assert conflict["customer_projection"]["customer_next_action"]["request_item_id"] == "item_1"
    assert store.events["case_e2e"] == before_events
    assert store.items["item_1"].status == ITEM_STATUS_ACTIVE


def test_scenario6_resume_next_day_server_state_wins():
    svc, _store = _svc()
    created = _create(
        svc,
        items=[
            _item("VIN", 1, "vin"),
            _item("Insurance card", 2, "policy_or_insurance_card"),
        ],
    )
    after_vin = _submit_fact(svc, item_id="item_1", expected=created["aggregate_version"])
    # Next-day resume: authoritative fetch, not local draft inference.
    projection = svc.fetch_projection("case_e2e")
    assert projection is not None
    assert projection["aggregate_version"] == after_vin["aggregate_version"]
    assert projection["customer_next_action"]["request_item_id"] == "item_2"
    assert projection["customer_next_action"]["action_type"] == "provide_evidence"
    assert [row["request_item_id"] for row in projection["queued_request_items"]] == []
    assert projection["request_progress"]["satisfied"] == 1
    # Stale draft targeting item_1 must not be treated as active by server.
    assert projection["customer_next_action"]["request_item_id"] != "item_1"


def test_scenario7_network_loss_after_acceptance_replays_same_identity():
    svc, store = _svc()
    created = _create(svc)
    first = _submit_fact(
        svc,
        item_id="item_1",
        expected=created["aggregate_version"],
        command_id="cmd-lost-response",
        idempotency_key="idem-lost-response",
    )
    count_after = len(store.events["case_e2e"])
    # Client never saw response; retries with same identity.
    replay = _submit_fact(
        svc,
        item_id="item_1",
        expected=created["aggregate_version"],
        command_id="cmd-lost-response",
        idempotency_key="idem-lost-response",
    )
    assert replay["outcome"] == "replayed"
    assert replay["event_ids"] == first["event_ids"]
    assert len(store.events["case_e2e"]) == count_after
    assert replay["customer_projection"]["workflow_state"] == "broker_review_ready"
    assert replay["customer_projection"]["customer_next_action"]["action_type"] == "wait_for_broker_review"


def test_scenario8_legacy_case_remains_unaffected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("P20_SLICE1_REQUEST_MORE", raising=False)
    svc, store = _svc(enabled=False)
    assert svc.fetch_projection("case_e2e") is None
    rejected = _create(svc)
    assert rejected["outcome"] == "rejected"
    assert rejected["error_code"] == "slice1_not_enabled"
    assert store.groups == {}
    assert store.items == {}
    assert store.events == {}


def test_expected_vin_timeline_event_fields():
    svc, store = _svc()
    created = _create(svc)
    _submit_fact(svc, item_id="item_1", expected=created["aggregate_version"])
    events = store.events["case_e2e"]
    for index, event in enumerate(events, start=1):
        assert event["sequence_number"] == index
        assert event["aggregate_version"] == index
        assert event["case_id"] == "case_e2e"
        assert event["command_id"]
        assert event["correlation_id"]
        assert event["idempotency_key"]
        assert event["visibility"]
        assert event["state_before"]
        assert event["state_after"]
    created_event = events[0]
    assert created_event["event_type"] == "broker_request_more_created"
    assert created_event["evidence"]["request_id"] == "req_e2e"
    satisfied = next(event for event in events if event["event_type"] == "customer_request_item_satisfied")
    assert satisfied["evidence"]["request_item_id"] == "item_1"
    supplement = events[-1]
    assert supplement["event_type"] == "supplement_submitted"
    assert supplement["actor"] == "customer"


def test_migration_sql_has_required_uniques_and_rollback_notes():
    from pathlib import Path

    sql_path = Path("services/fiqa_api/db/schema/migrations/002_p20_slice1_request_more.sql")
    text = sql_path.read_text(encoding="utf-8")
    for needle in [
        "claim_slice1_aggregates",
        "claim_request_groups",
        "claim_request_items",
        "claim_slice1_events",
        "claim_slice1_command_outcomes",
        "uq_claim_request_groups_one_open",
        "uq_claim_request_items_position",
        "uq_claim_slice1_events_sequence",
        "uq_claim_slice1_command_outcome_idempotency",
        "uq_claim_slice1_command_outcome_command",
        "DROP TABLE IF EXISTS claim_slice1_command_outcomes",
    ]:
        assert needle in text
