"""P1 Request More — VIN submit persistence, replay, 3-item progress, closed reject."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.case_close import ERROR_CASE_CLOSED_READ_ONLY
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    GROUP_STATUS_OPEN,
    ITEM_STATUS_ACTIVE,
    ITEM_STATUS_QUEUED,
    ITEM_STATUS_SATISFIED,
    InMemorySlice1Store,
    P20Slice1CommandService,
    STATE_BROKER_REVIEW_READY,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

CASE = "case_vin_stability"
VALID_VIN = "1HGCM82633A004352"


def _case(**extra) -> dict:
    row = {
        "case_id": CASE,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-22T18:00:00Z",
        "slice1_capability_version": 1,
        "entry_channel": "mini_program",
        "created_by_actor": "customer",
        "identity_binding_state": "linked",
        "person_link_source": "wechat",
        "person_link_key": "plk_vin_stability",
        "known_facts": {"accident_description": "倒车碰撞"},
    }
    row.update(extra)
    return row


def _svc(case: dict | None = None) -> tuple[P20Slice1CommandService, InMemorySlice1Store]:
    store = InMemorySlice1Store({CASE: case or _case()})
    return P20Slice1CommandService(store), store


def _item(*, item_id: str, label: str, item_type: str, position: int) -> dict:
    return {
        "request_item_id": item_id,
        "item_type": item_type,
        "label": label,
        "instructions": f"请补充{label}",
        "required": True,
        "position": position,
    }


def _request_three(svc: P20Slice1CommandService) -> dict:
    return svc.accept_request_more(
        case_id=CASE,
        broker_id="office:vin",
        command_id="cmd-vin-req-3",
        idempotency_key="idem-vin-req-3",
        expected_case_version=0,
        requested_items=[
            _item(item_id="item_vin", label="Vehicle VIN", item_type="vin", position=1),
            _item(
                item_id="item_vehicle",
                label="Vehicle Information",
                item_type="vehicle_information",
                position=2,
            ),
            _item(
                item_id="item_card",
                label="Insurance Card",
                item_type="policy_or_insurance_card",
                position=3,
            ),
        ],
        request_id="req_vin_3",
    )


def test_vin_only_completes_and_clears_waiting():
    svc, store = _svc()
    created = svc.accept_request_more(
        case_id=CASE,
        broker_id="office:vin",
        command_id="cmd-vin-only",
        idempotency_key="idem-vin-only",
        expected_case_version=0,
        requested_items=[
            _item(item_id="item_vin_only", label="Vehicle VIN", item_type="vin", position=1),
        ],
        request_id="req_vin_only",
    )
    assert created["outcome"] == "accepted"
    done = svc.submit_request_item(
        case_id=CASE,
        customer_id="h5:bound",
        active_request_item_id="item_vin_only",
        command_id="cmd-vin-submit-only",
        idempotency_key="idem-vin-submit-only",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    assert done["outcome"] == "accepted"
    assert store.items["item_vin_only"].status == ITEM_STATUS_SATISFIED
    assert store.groups["req_vin_only"].status == GROUP_STATUS_COMPLETED
    assert store.aggregates[CASE].workflow_state == STATE_BROKER_REVIEW_READY
    progress = done["customer_projection"]["request_progress"]
    assert progress["satisfied"] == 1
    assert progress["total"] == 1
    assert done["customer_projection"]["customer_next_action"]["action_type"] == "wait_for_broker_review"
    assert store.cases[CASE]["known_facts"].get("vehicle_vin") == VALID_VIN


def test_three_items_progress_0_to_1_to_complete():
    svc, store = _svc()
    created = _request_three(svc)
    assert created["outcome"] == "accepted"
    progress0 = created["customer_projection"]["request_progress"]
    assert progress0["satisfied"] == 0
    assert progress0["total"] == 3
    assert store.items["item_vin"].status == ITEM_STATUS_ACTIVE
    assert store.items["item_vehicle"].status == ITEM_STATUS_QUEUED
    assert store.items["item_card"].status == ITEM_STATUS_QUEUED

    vin = svc.submit_request_item(
        case_id=CASE,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-vin-submit-1",
        idempotency_key="idem-vin-submit-1",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    assert vin["outcome"] == "accepted"
    assert store.items["item_vin"].status == ITEM_STATUS_SATISFIED
    assert store.items["item_vehicle"].status == ITEM_STATUS_ACTIVE
    assert vin["customer_projection"]["request_progress"]["satisfied"] == 1
    assert vin["customer_projection"]["request_progress"]["total"] == 3
    assert vin["customer_projection"]["customer_next_action"]["request_item_id"] == "item_vehicle"
    assert store.groups["req_vin_3"].status == GROUP_STATUS_OPEN

    vehicle = svc.submit_request_item(
        case_id=CASE,
        customer_id="h5:bound",
        active_request_item_id="item_vehicle",
        command_id="cmd-vehicle-submit",
        idempotency_key="idem-vehicle-submit",
        expected_case_version=vin["aggregate_version"],
        fact={
            "field": "vehicle_information",
            "year": "2020",
            "make": "Toyota",
            "model": "Camry",
            "vin": VALID_VIN,
            "final": True,
        },
    )
    assert vehicle["outcome"] == "accepted"
    assert store.items["item_vehicle"].status == ITEM_STATUS_SATISFIED
    assert store.items["item_card"].status == ITEM_STATUS_ACTIVE
    assert vehicle["customer_projection"]["request_progress"]["satisfied"] == 2

    card = svc.submit_request_item(
        case_id=CASE,
        customer_id="h5:bound",
        active_request_item_id="item_card",
        command_id="cmd-card-submit",
        idempotency_key="idem-card-submit",
        expected_case_version=vehicle["aggregate_version"],
        evidence={"attachment_id": "att_card_vin"},
    )
    assert card["outcome"] == "accepted"
    assert store.groups["req_vin_3"].status == GROUP_STATUS_COMPLETED
    assert store.aggregates[CASE].workflow_state == STATE_BROKER_REVIEW_READY
    assert card["customer_projection"]["request_progress"]["satisfied"] == 3


def test_vin_idempotent_replay_no_duplicate_write():
    svc, store = _svc()
    created = _request_three(svc)
    first = svc.submit_request_item(
        case_id=CASE,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-vin-replay",
        idempotency_key="idem-vin-replay",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    assert first["outcome"] == "accepted"
    version_after = first["aggregate_version"]
    satisfied_at = store.items["item_vin"].satisfied_at

    replay = svc.submit_request_item(
        case_id=CASE,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-vin-replay",
        idempotency_key="idem-vin-replay",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    assert replay["outcome"] == "replayed"
    assert store.items["item_vin"].status == ITEM_STATUS_SATISFIED
    assert store.items["item_vin"].satisfied_at == satisfied_at
    assert store.aggregates[CASE].aggregate_version == version_after
    # Still exactly one VIN item — no duplicate request item created.
    vin_items = [i for i in store.items.values() if i.item_type == "vin" and i.request_id == "req_vin_3"]
    assert len(vin_items) == 1


def test_closed_case_rejects_vin_submit_no_mutation():
    svc, store = _svc(
        _case(
            case_history_state="history",
            closed_at="2026-07-22T12:00:00Z",
            case_status="closed",
        )
    )
    # Seed an open request as if it existed before close — submit must still reject.
    store = InMemorySlice1Store(
        {
            CASE: _case(
                case_history_state="history",
                closed_at="2026-07-22T12:00:00Z",
                case_status="closed",
            )
        }
    )
    svc = P20Slice1CommandService(store)
    # Closed before request more
    created = svc.accept_request_more(
        case_id=CASE,
        broker_id="office:vin",
        command_id="cmd-closed-req",
        idempotency_key="idem-closed-req",
        expected_case_version=0,
        requested_items=[
            _item(item_id="item_vin_closed", label="VIN", item_type="vin", position=1),
        ],
        request_id="req_closed",
    )
    assert created["outcome"] == "rejected"
    assert created["error_code"] == ERROR_CASE_CLOSED_READ_ONLY
    assert "item_vin_closed" not in store.items
