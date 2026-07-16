from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    GROUP_STATUS_OPEN,
    ITEM_STATUS_ACTIVE,
    ITEM_STATUS_QUEUED,
    ITEM_STATUS_SATISFIED,
    P20Slice1CommandService,
    InMemorySlice1Store,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _case(*, enabled: bool = True) -> dict:
    row = {
        "case_id": "case_slice1",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-15T10:00:00Z",
    }
    if enabled:
        row["slice1_capability_version"] = 1
    return row


def _svc(*, enabled: bool = True) -> tuple[P20Slice1CommandService, InMemorySlice1Store]:
    store = InMemorySlice1Store({"case_slice1": _case(enabled=enabled)})
    return P20Slice1CommandService(store), store


def _item(label: str, position: int = 1, item_type: str = "vin") -> dict:
    return {
        "request_item_id": f"item_{position}",
        "item_type": item_type,
        "label": label,
        "instructions": f"Please provide {label}",
        "required": True,
        "position": position,
    }


def _create(
    svc: P20Slice1CommandService,
    *,
    items: list[dict] | None = None,
    command_id: str = "cmd-create-0001",
    idempotency_key: str = "idem-create-0001",
    expected: int = 0,
) -> dict:
    return svc.accept_request_more(
        case_id="case_slice1",
        broker_id="office:demo",
        command_id=command_id,
        idempotency_key=idempotency_key,
        expected_case_version=expected,
        requested_items=items or [_item("VIN")],
        reason="Need structured follow-up",
        request_id="req_demo",
    )


def _submit(
    svc: P20Slice1CommandService,
    *,
    item_id: str,
    expected: int,
    command_id: str = "cmd-submit-0001",
    idempotency_key: str = "idem-submit-0001",
) -> dict:
    return svc.submit_request_item(
        case_id="case_slice1",
        customer_id="h5:demo",
        active_request_item_id=item_id,
        command_id=command_id,
        idempotency_key=idempotency_key,
        expected_case_version=expected,
        client_draft_id="draft_1",
        fact={"field": "vin", "value": "1HGCM82633A004352"},
    )


def test_broker_creates_one_requested_item():
    svc, store = _svc()
    result = _create(svc)

    assert result["outcome"] == "accepted"
    assert result["aggregate_version"] == 1
    assert store.groups["req_demo"].status == GROUP_STATUS_OPEN
    assert store.items["item_1"].label == "VIN"


def test_broker_creates_multiple_ordered_items():
    svc, store = _svc()
    _create(svc, items=[_item("VIN", 1), _item("Insurance card", 2, "policy_or_insurance_card")])

    assert [item.request_item_id for item in store.items.values()] == ["item_1", "item_2"]
    assert [item.position for item in store.items.values()] == [1, 2]


def test_exactly_one_item_becomes_active_and_remaining_are_queued():
    svc, store = _svc()
    result = _create(svc, items=[_item("VIN", 1), _item("Insurance card", 2, "policy_or_insurance_card")])

    assert store.items["item_1"].status == ITEM_STATUS_ACTIVE
    assert store.items["item_2"].status == ITEM_STATUS_QUEUED
    queued = result["customer_projection"]["queued_request_items"]
    assert [item["request_item_id"] for item in queued] == ["item_2"]
    assert queued[0]["actionable"] is False


def test_fetch_authoritative_task_returns_active_and_queued_items():
    svc, _store = _svc()
    _create(svc, items=[_item("VIN", 1), _item("Insurance card", 2, "policy_or_insurance_card")])

    projection = svc.fetch_projection("case_slice1")

    assert projection is not None
    assert projection["workflow_state"] == "broker_more_requested"
    assert projection["aggregate_version"] == 1
    assert projection["customer_next_action"]["request_item_id"] == "item_1"
    assert [item["request_item_id"] for item in projection["queued_request_items"]] == ["item_2"]


def test_same_create_command_retry_produces_no_duplicate_effects():
    svc, store = _svc()
    first = _create(svc)
    second = _create(svc)

    assert first["event_ids"] == second["event_ids"]
    assert second["outcome"] == "replayed"
    assert len(store.events["case_slice1"]) == 1
    assert len(store.groups) == 1


def test_stale_expected_version_is_rejected_without_business_event():
    svc, store = _svc()
    result = _create(svc, expected=7)

    assert result["outcome"] == "conflict"
    assert result["error_code"] == "version_conflict"
    assert store.events.get("case_slice1") is None
    assert store.groups == {}


def test_valid_item_submission_marks_item_satisfied():
    svc, store = _svc()
    created = _create(svc, items=[_item("VIN", 1), _item("Insurance card", 2, "policy_or_insurance_card")])
    submitted = _submit(svc, item_id="item_1", expected=created["aggregate_version"])

    assert submitted["outcome"] == "accepted"
    assert store.items["item_1"].status == ITEM_STATUS_SATISFIED
    assert store.items["item_1"].satisfied_by_event_id


def test_completing_one_item_activates_next_item():
    svc, store = _svc()
    created = _create(svc, items=[_item("VIN", 1), _item("Insurance card", 2, "policy_or_insurance_card")])
    submitted = _submit(svc, item_id="item_1", expected=created["aggregate_version"])

    assert store.items["item_2"].status == ITEM_STATUS_ACTIVE
    action = submitted["customer_projection"]["customer_next_action"]
    assert action["request_item_id"] == "item_2"
    assert action["action_type"] == "provide_evidence"
    assert action["required_input"] == "policy_or_insurance_card"


def test_completing_all_items_returns_case_to_broker_review():
    svc, store = _svc()
    created = _create(svc)
    result = _submit(svc, item_id="item_1", expected=created["aggregate_version"])

    assert result["customer_projection"]["workflow_state"] == "broker_review_ready"
    assert result["customer_projection"]["customer_next_action"]["action_type"] == "wait_for_broker_review"
    assert result["customer_projection"]["broker_next_action"]["action_type"] == "review_customer_response"
    assert store.groups["req_demo"].status == GROUP_STATUS_COMPLETED


def test_broker_projection_includes_exact_submitted_vin_response():
    svc, _store = _svc()
    created = _create(svc)
    result = _submit(svc, item_id="item_1", expected=created["aggregate_version"])

    items = result["broker_projection"]["open_request"]["items"]
    assert len(items) == 1
    response = items[0]["customer_response"]
    assert response["kind"] == "fact"
    assert response["submitted_value"] == "1HGCM82633A004352"
    assert response["submitted_by_actor"] == "customer"
    assert response["submitted_by"] == "h5:demo"
    assert response["submitted_at"]
    assert response["review_status"] == "satisfied"
    assert response["applied_to_canonical_facts"] is False
    assert response.get("canonical_value") in (None, "")


def test_broker_projection_distinguishes_canonical_vin_when_present():
    store = InMemorySlice1Store(
        {
            "case_slice1": {
                **_case(),
                "known_facts": {"vin": "CANONICALVIN00001"},
            }
        }
    )
    svc = P20Slice1CommandService(store)
    created = _create(svc)
    result = _submit(svc, item_id="item_1", expected=created["aggregate_version"])
    response = result["broker_projection"]["open_request"]["items"][0]["customer_response"]
    assert response["submitted_value"] == "1HGCM82633A004352"
    assert response["canonical_value"] == "CANONICALVIN00001"
    assert response["applied_to_canonical_facts"] is False


def test_fetch_projection_keeps_completed_request_response_visible():
    svc, _store = _svc()
    created = _create(svc)
    submitted = _submit(svc, item_id="item_1", expected=created["aggregate_version"])
    assert submitted["broker_projection"]["workflow_state"] == "broker_review_ready"

    projection = svc.fetch_projection("case_slice1")
    assert projection is not None
    assert projection["workflow_state"] == "broker_review_ready"
    assert projection["open_request"]["status"] == GROUP_STATUS_COMPLETED
    response = projection["open_request"]["items"][0]["customer_response"]
    assert response["submitted_value"] == "1HGCM82633A004352"
    assert response["applied_to_canonical_facts"] is False


def test_list_redaction_omits_submitted_vin_value():
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
        redact_case_slice1_responses_for_list,
    )

    svc, _store = _svc()
    created = _create(svc)
    result = _submit(svc, item_id="item_1", expected=created["aggregate_version"])
    case = {
        "case_id": "case_slice1",
        "slice1_projection": result["broker_projection"],
        "p20_slice1_projection": result["broker_projection"],
        "slice1_request_summary": result["broker_projection"]["open_request"],
    }
    redacted = redact_case_slice1_responses_for_list(case)
    item = redacted["slice1_projection"]["open_request"]["items"][0]
    assert item["customer_response"]["submitted_value"] is None
    assert item["customer_response"]["value_redacted"] is True
    events = redacted["slice1_projection"]["latest_events"]
    field_saved = next(e for e in events if e.get("event_type") == "field_saved")
    assert field_saved["evidence"]["value"] is None
    assert field_saved["evidence"]["value_redacted"] is True


def test_photo_evidence_response_exposes_safe_metadata_not_raw_bytes():
    svc, _store = _svc()
    created = _create(
        svc,
        items=[_item("Damage photos", 1, "photo_evidence")],
    )
    result = svc.submit_request_item(
        case_id="case_slice1",
        customer_id="h5:demo",
        active_request_item_id="item_1",
        command_id="cmd-submit-photo",
        idempotency_key="idem-submit-photo",
        expected_case_version=created["aggregate_version"],
        client_draft_id="draft_photo",
        evidence={"attachment_id": "att_damage_1"},
    )
    response = result["broker_projection"]["open_request"]["items"][0]["customer_response"]
    assert response["kind"] == "evidence"
    assert response["evidence_ref"] == "att_damage_1"
    assert "bytes" not in response
    assert "storage_uri" not in response


def test_duplicate_submission_creates_no_duplicate_event_or_task():
    svc, store = _svc()
    created = _create(svc)
    first = _submit(svc, item_id="item_1", expected=created["aggregate_version"])
    count_after_first = len(store.events["case_slice1"])
    second = _submit(svc, item_id="item_1", expected=created["aggregate_version"])

    assert second["outcome"] == "replayed"
    assert second["event_ids"] == first["event_ids"]
    assert len(store.events["case_slice1"]) == count_after_first
    assert len(store.items) == 1


def test_non_slice1_case_remains_compatible(monkeypatch):
    monkeypatch.delenv("P20_SLICE1_REQUEST_MORE", raising=False)
    svc, store = _svc(enabled=False)

    assert svc.fetch_projection("case_slice1") is None
    result = _create(svc)
    assert result["outcome"] == "rejected"
    assert result["error_code"] == "slice1_not_enabled"
    assert store.groups == {}


class _FailingEventStore(InMemorySlice1Store):
    def insert_events(self, events: list[dict]) -> None:
        raise RuntimeError("simulated_event_store_failure")


def test_failure_during_acceptance_rolls_back_business_effects():
    store = _FailingEventStore({"case_slice1": _case()})
    svc = P20Slice1CommandService(store)

    with pytest.raises(RuntimeError):
        _create(svc)

    assert store.groups == {}
    assert store.items == {}
    assert store.events == {}
    assert store.outcomes == {}
