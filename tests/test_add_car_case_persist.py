"""Minimal add-car case persistence via save_case (P16 SAVE_CASE + CASE_ID)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from services.fiqa_api.inbox_triage.case_store import get_case_by_id
from services.fiqa_api.routes.add_car import (
    _build_add_car_triage_result,
    _persist_add_car_case,
)


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


def test_build_add_car_triage_result_complete_packet() -> None:
    packet = {
        "customer_name": _intake_field("Andy Li"),
        "phone": _intake_field("6265550000"),
        "garaging_zip": _intake_field("91101"),
        "vin": _extracted_field("5UXZV4C56BL402905"),
        "year": _extracted_field("2011"),
        "make": _extracted_field("BMW"),
        "model": _extracted_field("X5"),
    }
    result = _build_add_car_triage_result(
        customer_name="Andy Li",
        phone="6265550000",
        garaging_zip="91101",
        packet=packet,
        warnings=[],
        request_type="add_vehicle",
    )
    assert result["issue_category"] == "add_car_quote"
    assert result["service_type"] == "add_car"
    assert result["lifecycle_status"] == "handed_off"
    assert result["handoff_ready"] is True
    assert result["quote_ready_status"] == "quote_ready"
    assert result["still_needed_fields"] == []
    assert "vin" in result["collected_fields"]
    assert result["primary_vehicle_summary"] == "2011 BMW X5"
    assert result["vehicle_key"] == "5UXZV4C56BL402905"


def test_build_add_car_triage_result_missing_vin() -> None:
    packet = {
        "vin": _extracted_field(""),
        "year": _extracted_field("2011"),
        "make": _extracted_field("BMW"),
        "model": _extracted_field("X5"),
    }
    result = _build_add_car_triage_result(
        customer_name="Andy Li",
        phone="6265550000",
        garaging_zip="91101",
        packet=packet,
        warnings=[],
        request_type="add_vehicle",
    )
    assert "vin" in result["still_needed_fields"]
    assert result["handoff_ready"] is False
    assert result["quote_ready_status"] == "need_more"


def test_persist_add_car_case_returns_case_id() -> None:
    _setup_json_store()
    packet = {
        "customer_name": _intake_field("Andy Li"),
        "phone": _intake_field("6265550000"),
        "garaging_zip": _intake_field("91101"),
        "vin": _extracted_field("5UXZV4C56BL402905"),
        "year": _extracted_field("2011"),
        "make": _extracted_field("BMW"),
        "model": _extracted_field("X5"),
    }
    case_id = _persist_add_car_case(
        customer_name="Andy Li",
        phone="6265550000",
        garaging_zip="91101",
        packet=packet,
        warnings=[],
        file_names=["insurance_card.png"],
        request_type="add_vehicle",
    )
    assert case_id
    assert case_id.startswith("case_")
    stored = get_case_by_id(case_id)
    assert stored is not None
    assert stored.get("service_lane") == "add_car"
    assert stored.get("customer_name") == "Andy Li"
    assert stored.get("customer_phone") == "6265550000"
    assert stored.get("lifecycle_status") == "handed_off"
