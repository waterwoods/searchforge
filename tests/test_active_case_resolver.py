"""P17 Phase 1 — Active Case resolver and Chen Kui consolidation tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from services.fiqa_api.inbox_triage.active_case_resolver import (
    ResolverOutcome,
    find_open_cases_for_intent,
    resolve_active_case_for_evidence,
)
from services.fiqa_api.inbox_triage.case_store import count_stored_cases, get_case_by_id, list_all_cases
from services.fiqa_api.routes.add_car import _persist_add_car_case


def _intake_field(value: str) -> dict:
    return {
        "value": value,
        "confidence": 1.0,
        "confidence_label": "high",
        "source_file": "intake_form",
        "is_mock": False,
    }


def _extracted_field(value: str, source: str = "doc.pdf") -> dict:
    return {
        "value": value,
        "confidence": 0.9,
        "confidence_label": "high",
        "source_file": source,
        "is_mock": False,
    }


def _setup_json_store() -> None:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)


def _open_add_car_case(
    case_id: str,
    phone: str,
    *,
    vin: str | None = None,
    status: str = "new",
) -> dict:
    row = {
        "case_id": case_id,
        "case_status": status,
        "customer_phone": phone,
        "service_lane": "add_car",
        "lifecycle_status": "handed_off",
        "updated_at": "2026-06-29T12:00:00Z",
        "created_at": "2026-06-29T10:00:00Z",
    }
    if vin:
        row["vehicle_key"] = vin
    return row


def test_resolve_no_existing_case_create() -> None:
    decision = resolve_active_case_for_evidence(
        phone="6265550101",
        intent="add_vehicle",
        new_vin=None,
        cases=[],
    )
    assert decision.outcome == ResolverOutcome.CREATE
    assert decision.case_id is None


def test_resolve_same_phone_attach() -> None:
    cases = [_open_add_car_case("case_a", "6265550101")]
    decision = resolve_active_case_for_evidence(
        phone="6265550101",
        intent="add_vehicle",
        new_vin=None,
        cases=cases,
    )
    assert decision.outcome == ResolverOutcome.ATTACH
    assert decision.case_id == "case_a"


def test_resolve_vin_conflict_broker_review() -> None:
    cases = [_open_add_car_case("case_a", "6265550101", vin="5UXZV4C56BL402905")]
    decision = resolve_active_case_for_evidence(
        phone="6265550101",
        intent="add_vehicle",
        new_vin="1HGBH41JXMN109186",
        cases=cases,
    )
    assert decision.outcome == ResolverOutcome.BROKER_REVIEW
    assert decision.conflict_reason == "vin_conflict"
    assert decision.case_id == "case_a"


def test_resolve_two_open_cases_broker_review() -> None:
    cases = [
        {**_open_add_car_case("case_new", "6265550101"), "updated_at": "2026-06-29T14:00:00Z"},
        {**_open_add_car_case("case_old", "6265550101"), "updated_at": "2026-06-29T12:00:00Z"},
    ]
    decision = resolve_active_case_for_evidence(
        phone="6265550101",
        intent="add_vehicle",
        new_vin=None,
        cases=cases,
    )
    assert decision.outcome == ResolverOutcome.BROKER_REVIEW
    assert decision.conflict_reason == "multiple_open_cases"
    assert decision.candidate_count == 2
    assert decision.case_id == "case_new"


def test_resolve_closed_case_create() -> None:
    cases = [_open_add_car_case("case_closed", "6265550101", status="closed")]
    decision = resolve_active_case_for_evidence(
        phone="6265550101",
        intent="add_vehicle",
        new_vin=None,
        cases=cases,
    )
    assert decision.outcome == ResolverOutcome.CREATE


def test_resolve_different_intent_create() -> None:
    cases = [
        {
            "case_id": "case_pr",
            "case_status": "new",
            "customer_phone": "6265550101",
            "service_lane": "policy_review",
            "lifecycle_status": "handed_off",
        }
    ]
    decision = resolve_active_case_for_evidence(
        phone="6265550101",
        intent="add_vehicle",
        new_vin=None,
        cases=cases,
    )
    assert decision.outcome == ResolverOutcome.CREATE
    assert find_open_cases_for_intent("6265550101", "add_vehicle", cases) == []


def test_chen_kui_three_uploads_one_case_one_inbox_row() -> None:
    _setup_json_store()
    phone = "6265550101"
    zip_code = "91101"

    upload1_packet = {
        "customer_name": _intake_field("Chen Kui"),
        "phone": _intake_field(phone),
        "garaging_zip": _intake_field(zip_code),
        "year": _extracted_field("2024", "insurance_card.png"),
        "make": _extracted_field("Tesla", "insurance_card.png"),
        "model": _extracted_field("Model Y", "insurance_card.png"),
    }
    case_id_1 = _persist_add_car_case(
        customer_name="Chen Kui",
        phone=phone,
        garaging_zip=zip_code,
        packet=upload1_packet,
        warnings=[],
        file_names=["insurance_card.png"],
        request_type="add_vehicle",
    )
    assert case_id_1

    upload2_packet = {
        "customer_name": _intake_field("Chen Kui"),
        "phone": _intake_field(phone),
        "garaging_zip": _intake_field(zip_code),
        "vin": _extracted_field("", "dec_page.pdf"),
        "year": _extracted_field("2024", "dec_page.pdf"),
        "make": _extracted_field("Tesla", "dec_page.pdf"),
        "model": _extracted_field("Model Y", "dec_page.pdf"),
    }
    case_id_2 = _persist_add_car_case(
        customer_name="Chen Kui",
        phone=phone,
        garaging_zip=zip_code,
        packet=upload2_packet,
        warnings=[],
        file_names=["dec_page.pdf"],
        request_type="add_vehicle",
    )
    assert case_id_2 == case_id_1

    upload3_packet = {
        "customer_name": _intake_field("Chen Kui"),
        "phone": _intake_field(phone),
        "garaging_zip": _intake_field(zip_code),
        "vin": _extracted_field("5YJ3E1EA8PF123456", "vin_photo.jpg"),
        "year": _extracted_field("2024", "vin_photo.jpg"),
        "make": _extracted_field("Tesla", "vin_photo.jpg"),
        "model": _extracted_field("Model Y", "vin_photo.jpg"),
    }
    case_id_3 = _persist_add_car_case(
        customer_name="Chen Kui",
        phone=phone,
        garaging_zip=zip_code,
        packet=upload3_packet,
        warnings=[],
        file_names=["vin_photo.jpg"],
        request_type="add_vehicle",
    )
    assert case_id_3 == case_id_1

    assert count_stored_cases() == 1
    open_rows = [
        c
        for c in list_all_cases()
        if c.get("customer_phone") == phone and c.get("case_status") != "closed"
    ]
    assert len(open_rows) == 1

    stored = get_case_by_id(case_id_1)
    assert stored is not None
    blob = stored.get("p16_broker_packet") or {}
    assert blob.get("readiness_status") == "READY"
    pkt = blob.get("packet") or {}
    assert pkt.get("vin", {}).get("value") == "5YJ3E1EA8PF123456"
    events = stored.get("evidence_events") or []
    assert len(events) == 3
    filenames = {e.get("filename") for e in events}
    assert "insurance_card.png" in filenames
    assert "dec_page.pdf" in filenames
    assert "vin_photo.jpg" in filenames


def test_vin_conflict_keeps_packet_broker_review() -> None:
    _setup_json_store()
    phone = "6265550101"
    zip_code = "91101"
    vin_a = "5YJ3E1EA8PF123456"
    vin_b = "1HGBH41JXMN109186"

    packet1 = {
        "customer_name": _intake_field("Chen Kui"),
        "phone": _intake_field(phone),
        "garaging_zip": _intake_field(zip_code),
        "vin": _extracted_field(vin_a, "insurance_card.png"),
        "year": _extracted_field("2024", "insurance_card.png"),
        "make": _extracted_field("Tesla", "insurance_card.png"),
        "model": _extracted_field("Model Y", "insurance_card.png"),
    }
    case_id = _persist_add_car_case(
        customer_name="Chen Kui",
        phone=phone,
        garaging_zip=zip_code,
        packet=packet1,
        warnings=[],
        file_names=["insurance_card.png"],
        request_type="add_vehicle",
    )
    assert case_id

    packet2 = {
        "customer_name": _intake_field("Chen Kui"),
        "phone": _intake_field(phone),
        "garaging_zip": _intake_field(zip_code),
        "vin": _extracted_field(vin_b, "vin_photo.jpg"),
        "year": _extracted_field("2024", "vin_photo.jpg"),
        "make": _extracted_field("Tesla", "vin_photo.jpg"),
        "model": _extracted_field("Model Y", "vin_photo.jpg"),
    }
    same_id = _persist_add_car_case(
        customer_name="Chen Kui",
        phone=phone,
        garaging_zip=zip_code,
        packet=packet2,
        warnings=[],
        file_names=["vin_photo.jpg"],
        request_type="add_vehicle",
    )
    assert same_id == case_id
    assert count_stored_cases() == 1

    stored = get_case_by_id(case_id)
    assert stored is not None
    assert stored.get("merge_review_required") is True
    assert stored.get("conflict_state") == "vin_conflict"
    blob = stored.get("p16_broker_packet") or {}
    assert blob.get("readiness_status") == "BROKER_REVIEW"
    assert blob.get("packet", {}).get("vin", {}).get("value") == vin_a
