"""Claim Vehicle T3 — Slice1 Request More ↔ ClaimVehicleIdentityService."""

from __future__ import annotations

from unittest.mock import patch

from services.fiqa_api.inbox_triage.claim_vehicle_identity import ClaimVehicleIdentityService
from services.fiqa_api.inbox_triage.p20_missing_information import MVP_SENDABLE_ITEM_TYPES
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    GROUP_STATUS_OPEN,
    ITEM_STATUS_ACTIVE,
    ITEM_STATUS_SATISFIED,
    InMemorySlice1Store,
    P20Slice1CommandService,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

VALID_VIN = "1HGCM82633A004352"


def _case(case_id: str = "case_cv_t3") -> dict:
    return {
        "case_id": case_id,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-21T10:00:00Z",
        "slice1_capability_version": 1,
        "known_facts": {},
    }


def _svc(case_id: str = "case_cv_t3"):
    vehicle = ClaimVehicleIdentityService()
    store = InMemorySlice1Store({case_id: _case(case_id)})
    return P20Slice1CommandService(store, vehicle_service=vehicle), store, vehicle


def _create_vin(svc: P20Slice1CommandService, case_id: str = "case_cv_t3") -> dict:
    return svc.accept_request_more(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-create-vin",
        idempotency_key="idem-create-vin",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "Provide the 17-character VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_vin",
    )


def _create_vehicle_info(svc: P20Slice1CommandService, case_id: str = "case_cv_t3") -> dict:
    return svc.accept_request_more(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-create-vi",
        idempotency_key="idem-create-vi",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_vi",
                "item_type": "vehicle_information",
                "label": "车辆信息",
                "instructions": "请补充本次事故车辆的基本信息，方便经纪人继续处理。",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need vehicle information",
        request_id="req_vi",
    )


def test_vehicle_information_is_mvp_sendable():
    assert "vehicle_information" in MVP_SENDABLE_ITEM_TYPES


def test_vin_request_writes_canonical_backend_and_satisfies():
    svc, store, vehicle = _svc()
    created = _create_vin(svc)
    with patch.object(vehicle, "upsert", wraps=vehicle.upsert) as upsert:
        result = svc.submit_request_item(
            case_id="case_cv_t3",
            customer_id="h5:t3",
            active_request_item_id="item_vin",
            command_id="cmd-vin-1",
            idempotency_key="idem-vin-1",
            expected_case_version=created["aggregate_version"],
            fact={"field": "vin", "value": VALID_VIN},
        )
    assert result["outcome"] == "accepted"
    assert upsert.called
    assert store.items["item_vin"].status == ITEM_STATUS_SATISFIED
    assert store.groups["req_vin"].status == GROUP_STATUS_COMPLETED
    facts = store.cases["case_cv_t3"]["known_facts"]
    assert facts["vehicle_vin"] == VALID_VIN
    assert facts["vin"] == VALID_VIN
    assert facts["claim_vehicle_id"] == "veh:case_cv_t3"
    response = result["broker_projection"]["open_request"]["items"][0]["customer_response"]
    assert response["applied_to_canonical_facts"] is True
    assert response["customer_action_label"] == "provided VIN"
    event_types = [e["event_type"] for e in store.events["case_cv_t3"]]
    assert "field_saved" in event_types
    assert "customer_request_item_satisfied" in event_types
    field_saved = next(e for e in store.events["case_cv_t3"] if e["event_type"] == "field_saved")
    assert field_saved["evidence"]["customer_action_label"] == "provided VIN"


def test_vehicle_information_request_complete_path_b_satisfies():
    svc, store, vehicle = _svc()
    created = _create_vehicle_info(svc)
    with patch.object(vehicle, "upsert", wraps=vehicle.upsert) as upsert:
        result = svc.submit_request_item(
            case_id="case_cv_t3",
            customer_id="h5:t3",
            active_request_item_id="item_vi",
            command_id="cmd-vi-complete",
            idempotency_key="idem-vi-complete",
            expected_case_version=created["aggregate_version"],
            fact={
                "field": "vehicle_information",
                "year": "2020",
                "make": "Toyota",
                "model": "Camry",
                "vin_unavailable": True,
                "license_plate": "8abc123",
                "plate_state": "ca",
            },
        )
    assert result["outcome"] == "accepted"
    assert upsert.called
    assert store.items["item_vi"].status == ITEM_STATUS_SATISFIED
    facts = store.cases["case_cv_t3"]["known_facts"]
    assert facts["vehicle_year"] == "2020"
    assert facts["vehicle_make"] == "Toyota"
    assert facts["vehicle_model"] == "Camry"
    assert facts["vehicle_vin_unavailable"] == "true"
    assert facts["own_vehicle_info"] == "2020 Toyota Camry"
    assert facts["vehicle_information"] == "2020 Toyota Camry"
    assert "fact_records" in store.cases["case_cv_t3"]
    assert store.cases["case_cv_t3"]["fact_records"]["vehicle_information"]["value"] == "2020 Toyota Camry"
    response = result["broker_projection"]["open_request"]["items"][0]["customer_response"]
    assert response["customer_action_label"] == "submitted vehicle information"
    assert response["applied_to_canonical_facts"] is True


def test_vehicle_information_partial_save_keeps_request_open():
    svc, store, _vehicle = _svc()
    created = _create_vehicle_info(svc)
    result = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vi",
        command_id="cmd-vi-partial",
        idempotency_key="idem-vi-partial",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vehicle_information", "year": "2020", "make": "Toyota"},
    )
    assert result["outcome"] == "accepted"
    assert store.items["item_vi"].status == ITEM_STATUS_ACTIVE
    assert store.groups["req_vi"].status == GROUP_STATUS_OPEN
    assert result["customer_projection"]["workflow_state"] == "customer_continuing"
    assert store.cases["case_cv_t3"]["known_facts"]["vehicle_year"] == "2020"
    assert store.cases["case_cv_t3"]["known_facts"]["vehicle_make"] == "Toyota"
    event_types = [e["event_type"] for e in store.events["case_cv_t3"]]
    assert "field_saved" in event_types
    assert "customer_request_item_satisfied" not in event_types


def test_vehicle_information_resume_then_complete():
    svc, store, _vehicle = _svc()
    created = _create_vehicle_info(svc)
    partial = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vi",
        command_id="cmd-vi-r1",
        idempotency_key="idem-vi-r1",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vehicle_information", "year": "2020", "make": "Toyota"},
    )
    assert partial["outcome"] == "accepted"
    assert store.items["item_vi"].status == ITEM_STATUS_ACTIVE

    final = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vi",
        command_id="cmd-vi-r2",
        idempotency_key="idem-vi-r2",
        expected_case_version=partial["aggregate_version"],
        fact={
            "field": "vehicle_information",
            "year": "2020",
            "make": "Toyota",
            "model": "Camry",
            "vin_unavailable": True,
        },
    )
    assert final["outcome"] == "accepted"
    assert store.items["item_vi"].status == ITEM_STATUS_SATISFIED
    assert store.groups["req_vi"].status == GROUP_STATUS_COMPLETED
    assert store.cases["case_cv_t3"]["known_facts"]["vehicle_model"] == "Camry"
    assert store.cases["case_cv_t3"]["known_facts"]["claim_vehicle_id"] == "veh:case_cv_t3"


def test_duplicate_submit_replays_without_new_events():
    svc, store, _vehicle = _svc()
    created = _create_vin(svc)
    first = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vin",
        command_id="cmd-vin-dup",
        idempotency_key="idem-vin-dup",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN},
    )
    events_after = list(store.events["case_cv_t3"])
    second = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vin",
        command_id="cmd-vin-dup",
        idempotency_key="idem-vin-dup",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN},
    )
    assert second["outcome"] == "replayed"
    assert second["event_ids"] == first["event_ids"]
    assert len(store.events["case_cv_t3"]) == len(events_after)


def test_invalid_vin_rejected_request_still_open():
    svc, store, _vehicle = _svc()
    created = _create_vin(svc)
    before = list(store.events.get("case_cv_t3") or [])
    result = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vin",
        command_id="cmd-vin-bad",
        idempotency_key="idem-vin-bad",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vin", "value": "SHORT"},
    )
    assert result["outcome"] == "rejected"
    assert result["error_code"] == "vin_invalid"
    assert store.items["item_vin"].status == ITEM_STATUS_ACTIVE
    assert store.events.get("case_cv_t3") == before


def test_vin_and_vehicle_information_share_single_vehicle_slot():
    svc, store, _vehicle = _svc()
    # First collect structured vehicle via vehicle_information.
    created = _create_vehicle_info(svc)
    vi = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vi",
        command_id="cmd-slot-vi",
        idempotency_key="idem-slot-vi",
        expected_case_version=created["aggregate_version"],
        fact={
            "field": "vehicle_information",
            "year": "2020",
            "make": "Toyota",
            "model": "Camry",
            "vin_unavailable": True,
        },
    )
    assert vi["outcome"] == "accepted"
    assert store.cases["case_cv_t3"]["known_facts"]["claim_vehicle_id"] == "veh:case_cv_t3"

    # New VIN request on same case merges into the same slot.
    store.aggregates["case_cv_t3"].workflow_state = "broker_reviewing"
    store.aggregates["case_cv_t3"].aggregate_version = vi["aggregate_version"]
    created_vin = svc.accept_request_more(
        case_id="case_cv_t3",
        broker_id="office:demo",
        command_id="cmd-create-vin-2",
        idempotency_key="idem-create-vin-2",
        expected_case_version=vi["aggregate_version"],
        requested_items=[
            {
                "request_item_id": "item_vin_2",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "VIN",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need VIN",
        request_id="req_vin_2",
    )
    vin_result = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vin_2",
        command_id="cmd-slot-vin",
        idempotency_key="idem-slot-vin",
        expected_case_version=created_vin["aggregate_version"],
        fact={"field": "vin", "value": VALID_VIN},
    )
    assert vin_result["outcome"] == "accepted"
    facts = store.cases["case_cv_t3"]["known_facts"]
    assert facts["claim_vehicle_id"] == "veh:case_cv_t3"
    assert facts["vehicle_vin"] == VALID_VIN
    assert facts["vehicle_year"] == "2020"
    assert facts["vehicle_make"] == "Toyota"


def test_legacy_free_text_vehicle_value_still_accepted():
    svc, store, _vehicle = _svc()
    created = _create_vehicle_info(svc)
    result = svc.submit_request_item(
        case_id="case_cv_t3",
        customer_id="h5:t3",
        active_request_item_id="item_vi",
        command_id="cmd-vi-legacy",
        idempotency_key="idem-vi-legacy",
        expected_case_version=created["aggregate_version"],
        fact={"field": "vehicle_information", "value": "2021 Tesla Model Y"},
    )
    assert result["outcome"] == "accepted"
    assert store.items["item_vi"].status == ITEM_STATUS_SATISFIED
    assert store.cases["case_cv_t3"]["known_facts"]["vehicle_year"] == "2021"
    assert store.cases["case_cv_t3"]["known_facts"]["vehicle_make"] == "Tesla"
    assert store.cases["case_cv_t3"]["known_facts"]["vehicle_model"] == "Model Y"
