"""Claim Vehicle T5 — Workbench structured vehicle projection / read-after-write."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.claim_vehicle_identity import (
    ClaimVehicleIdentityService,
    claim_vehicle_to_known_facts_patch,
    normalize_claim_vehicle_input,
)
from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_case_brief
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    ITEM_STATUS_SATISFIED,
    InMemorySlice1Store,
    P20Slice1CommandService,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

VALID_VIN = "1HGCM82633A004352"


def _base_case(case_id: str = "case_cv_t5") -> dict:
    return {
        "case_id": case_id,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-21T10:00:00Z",
        "slice1_capability_version": 1,
        "known_facts": {
            "accident_datetime": "今天上午10点",
            "accident_location": "Irvine",
            "accident_description": "追尾",
            "injury_status": "no",
        },
    }


def test_brief_projects_structured_vehicle_from_known_facts():
    vehicle = normalize_claim_vehicle_input(
        {
            "year": "2020",
            "make": "Toyota",
            "model": "Camry",
            "vin_unavailable": True,
            "license_plate": "8ABC123",
            "plate_state": "CA",
        },
        case_id="case_cv_t5",
    )
    case = _base_case()
    case["known_facts"].update(claim_vehicle_to_known_facts_patch(vehicle))

    brief = build_claim_case_brief(case)
    key_facts = brief["key_facts"]
    claim_vehicle = key_facts["claim_vehicle"]

    assert key_facts["own_vehicle_info"] == "2020 Toyota Camry"
    assert claim_vehicle is not None
    assert claim_vehicle["vehicle_id"] == "veh:case_cv_t5"
    assert claim_vehicle["year"] == "2020"
    assert claim_vehicle["make"] == "Toyota"
    assert claim_vehicle["model"] == "Camry"
    assert claim_vehicle["vin"] is None
    assert claim_vehicle["vin_unavailable"] is True
    assert claim_vehicle["license_plate"] == "8ABC123"
    assert claim_vehicle["plate_state"] == "CA"
    assert claim_vehicle["summary"] == "2020 Toyota Camry"
    assert claim_vehicle["complete"] is True


def test_brief_projects_vin_path_structured_vehicle():
    vehicle = normalize_claim_vehicle_input({"vin": VALID_VIN}, case_id="case_cv_t5_vin")
    case = _base_case("case_cv_t5_vin")
    case["known_facts"].update(claim_vehicle_to_known_facts_patch(vehicle))

    brief = build_claim_case_brief(case)
    claim_vehicle = brief["key_facts"]["claim_vehicle"]
    assert claim_vehicle is not None
    assert claim_vehicle["vin"] == VALID_VIN
    assert claim_vehicle["complete"] is True
    assert brief["key_facts"]["own_vehicle_info"]


def test_brief_omits_claim_vehicle_when_absent():
    brief = build_claim_case_brief(_base_case("case_cv_t5_empty"))
    assert brief["key_facts"]["claim_vehicle"] is None
    assert brief["key_facts"]["own_vehicle_info"] is None


def test_slice1_vehicle_information_submit_updates_workbench_brief():
    case_id = "case_cv_t5_flow"
    vehicle_svc = ClaimVehicleIdentityService()
    store = InMemorySlice1Store({case_id: _base_case(case_id)})
    svc = P20Slice1CommandService(store, vehicle_service=vehicle_svc)

    created = svc.accept_request_more(
        case_id=case_id,
        broker_id="office:demo",
        command_id="cmd-t5-create",
        idempotency_key="idem-t5-create",
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": "item_vi",
                "item_type": "vehicle_information",
                "label": "车辆信息",
                "instructions": "请补充车辆信息",
                "required": True,
                "position": 1,
            }
        ],
        reason="Need vehicle",
        request_id="req_t5_vi",
    )
    assert created["outcome"] == "accepted"

    submitted = svc.submit_request_item(
        case_id=case_id,
        customer_id="h5:t5",
        active_request_item_id="item_vi",
        command_id="cmd-t5-submit",
        idempotency_key="idem-t5-submit",
        expected_case_version=created["aggregate_version"],
        fact={
            "field": "vehicle_information",
            "year": "2020",
            "make": "Toyota",
            "model": "Camry",
            "vin_unavailable": True,
        },
    )
    assert submitted["outcome"] == "accepted"

    case = store.cases[case_id]
    brief = build_claim_case_brief(case)
    claim_vehicle = brief["key_facts"]["claim_vehicle"]
    assert claim_vehicle is not None
    assert claim_vehicle["year"] == "2020"
    assert claim_vehicle["make"] == "Toyota"
    assert claim_vehicle["model"] == "Camry"
    assert claim_vehicle["complete"] is True
    assert brief["key_facts"]["own_vehicle_info"] == "2020 Toyota Camry"

    items = (submitted.get("request_summary") or {}).get("items") or []
    assert items and items[0]["status"] == ITEM_STATUS_SATISFIED
    response = items[0].get("customer_response") or {}
    assert response.get("kind") == "fact"
    assert response.get("canonical_value") == "2020 Toyota Camry"
    assert response.get("applied_to_canonical_facts") is True
