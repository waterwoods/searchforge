#!/usr/bin/env python3
"""End-to-end in-process simulations for P1 Request More refresh + VIN submit.

Does not hit Production. Covers Simulations 2–7 at the Slice1 command layer.
Simulation 1 (drawer stability) is covered by UI unit/source contracts.
"""

from __future__ import annotations

import sys

from services.fiqa_api.inbox_triage.case_close import ERROR_CASE_CLOSED_READ_ONLY
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    ITEM_STATUS_ACTIVE,
    ITEM_STATUS_SATISFIED,
    InMemorySlice1Store,
    P20Slice1CommandService,
    STATE_BROKER_REVIEW_READY,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

VALID_VIN = "1HGCM82633A004352"


def _case(case_id: str, **extra) -> dict:
    row = {
        "case_id": case_id,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-22T18:00:00Z",
        "slice1_capability_version": 1,
        "entry_channel": "mini_program",
        "created_by_actor": "customer",
        "identity_binding_state": "linked",
        "person_link_source": "wechat",
        "person_link_key": f"plk_{case_id}",
        "known_facts": {"accident_description": "倒车碰撞"},
    }
    row.update(extra)
    return row


def _item(item_id: str, label: str, item_type: str, position: int) -> dict:
    return {
        "request_item_id": item_id,
        "item_type": item_type,
        "label": label,
        "instructions": f"请补充{label}",
        "required": True,
        "position": position,
    }


def _svc(case_id: str, case: dict | None = None) -> tuple[P20Slice1CommandService, InMemorySlice1Store]:
    store = InMemorySlice1Store({case_id: case or _case(case_id)})
    return P20Slice1CommandService(store), store


def sim2_vin_only() -> None:
    case_id = "sim2_vin_only"
    svc, store = _svc(case_id)
    created = svc.accept_request_more(
        case_id=case_id,
        broker_id="office:sim",
        command_id="cmd-sim2-req",
        idempotency_key="idem-sim2-req",
        expected_case_version=0,
        requested_items=[_item("item_vin", "Vehicle VIN", "vin", 1)],
        request_id="req_sim2",
    )
    assert created["outcome"] == "accepted"
    done = svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-sim2-vin",
        idempotency_key="idem-sim2-vin",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    assert done["outcome"] == "accepted"
    progress = done["customer_projection"]["request_progress"]
    assert int(progress.get("satisfied") or 0) == 1
    assert int(progress.get("total") or 0) == 1
    assert store.aggregates[case_id].workflow_state == STATE_BROKER_REVIEW_READY
    assert store.items["item_vin"].status == ITEM_STATUS_SATISFIED
    print("SIM2 VIN-only: PASS")


def sim3_three_items() -> None:
    case_id = "sim3_three"
    svc, store = _svc(case_id)
    created = svc.accept_request_more(
        case_id=case_id,
        broker_id="office:sim",
        command_id="cmd-sim3-req",
        idempotency_key="idem-sim3-req",
        expected_case_version=0,
        requested_items=[
            _item("item_vin", "Vehicle VIN", "vin", 1),
            _item("item_vehicle", "Vehicle Information", "vehicle_information", 2),
            _item("item_card", "Insurance Card", "policy_or_insurance_card", 3),
        ],
        request_id="req_sim3",
    )
    assert created["customer_projection"]["request_progress"]["total"] == 3
    assert created["customer_projection"]["request_progress"]["satisfied"] == 0
    vin = svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-sim3-vin",
        idempotency_key="idem-sim3-vin",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    assert vin["outcome"] == "accepted"
    assert vin["customer_projection"]["request_progress"]["satisfied"] == 1
    assert vin["customer_projection"]["customer_next_action"]["request_item_id"] == "item_vehicle"
    vehicle = svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:bound",
        active_request_item_id="item_vehicle",
        command_id="cmd-sim3-vehicle",
        idempotency_key="idem-sim3-vehicle",
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
    card = svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:bound",
        active_request_item_id="item_card",
        command_id="cmd-sim3-card",
        idempotency_key="idem-sim3-card",
        expected_case_version=vehicle["aggregate_version"],
        evidence={"attachment_id": "att_sim3"},
    )
    assert card["outcome"] == "accepted"
    assert store.groups["req_sim3"].status == GROUP_STATUS_COMPLETED
    assert store.aggregates[case_id].workflow_state == STATE_BROKER_REVIEW_READY
    print("SIM3 three-items: PASS")


def sim4_retry_after_uncertain() -> None:
    case_id = "sim4_retry"
    svc, store = _svc(case_id)
    created = svc.accept_request_more(
        case_id=case_id,
        broker_id="office:sim",
        command_id="cmd-sim4-req",
        idempotency_key="idem-sim4-req",
        expected_case_version=0,
        requested_items=[_item("item_vin", "Vehicle VIN", "vin", 1)],
        request_id="req_sim4",
    )
    first = svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-sim4-vin",
        idempotency_key="idem-sim4-vin",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    assert first["outcome"] == "accepted"
    # Lost client response → retry same identity
    replay = svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-sim4-vin",
        idempotency_key="idem-sim4-vin",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    assert replay["outcome"] == "replayed"
    assert store.items["item_vin"].status == ITEM_STATUS_SATISFIED
    print("SIM4 retry-after-uncertain: PASS")


def sim5_app_reopen() -> None:
    case_id = "sim5_reopen"
    svc, _store = _svc(case_id)
    created = svc.accept_request_more(
        case_id=case_id,
        broker_id="office:sim",
        command_id="cmd-sim5-req",
        idempotency_key="idem-sim5-req",
        expected_case_version=0,
        requested_items=[
            _item("item_vin", "Vehicle VIN", "vin", 1),
            _item("item_card", "Insurance Card", "policy_or_insurance_card", 2),
        ],
        request_id="req_sim5",
    )
    svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-sim5-vin",
        idempotency_key="idem-sim5-vin",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN, "vin": VALID_VIN},
    )
    again = svc.fetch_projection(case_id)
    assert again is not None
    assert again["customer_next_action"]["request_item_id"] == "item_card"
    assert again["request_progress"]["satisfied"] == 1
    print("SIM5 app-reopen: PASS")


def sim6_closed_case() -> None:
    case_id = "sim6_closed"
    svc, store = _svc(
        case_id,
        _case(
            case_id,
            case_history_state="history",
            closed_at="2026-07-22T12:00:00Z",
            case_status="closed",
        ),
    )
    created = svc.accept_request_more(
        case_id=case_id,
        broker_id="office:sim",
        command_id="cmd-sim6-req",
        idempotency_key="idem-sim6-req",
        expected_case_version=0,
        requested_items=[_item("item_vin", "VIN", "vin", 1)],
        request_id="req_sim6",
    )
    assert created["outcome"] == "rejected"
    assert created["error_code"] == ERROR_CASE_CLOSED_READ_ONLY
    assert "item_vin" not in store.items
    print("SIM6 closed-case: PASS")


def sim7_bound_no_qr_same_case() -> None:
    case_id = "sim7_bound"
    svc, store = _svc(case_id)
    created = svc.accept_request_more(
        case_id=case_id,
        broker_id="office:sim",
        command_id="cmd-sim7-req",
        idempotency_key="idem-sim7-req",
        expected_case_version=0,
        requested_items=[
            _item("item_vin", "Vehicle VIN", "vin", 1),
            _item("item_vehicle", "Vehicle Information", "vehicle_information", 2),
            _item("item_card", "Insurance Card", "policy_or_insurance_card", 3),
        ],
        request_id="req_sim7",
    )
    assert created["outcome"] == "accepted"
    again = svc.fetch_projection(case_id)
    assert again is not None
    assert again["open_request"]["request_id"] == "req_sim7"
    assert again["case_id"] == case_id
    assert again["request_progress"]["total"] == 3
    assert list(store.groups.keys()) == ["req_sim7"]
    print("SIM7 bound-no-qr same Active Case: PASS")


def main() -> int:
    print("SIM1 workbench-drawer: covered by ui workbenchDrawerRefresh.test.ts")
    sim2_vin_only()
    sim3_three_items()
    sim4_retry_after_uncertain()
    sim5_app_reopen()
    sim6_closed_case()
    sim7_bound_no_qr_same_case()
    print("ALL SIMULATIONS PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"SIMULATION FAIL: {exc}", file=sys.stderr)
        raise
