"""Tests for P16 broker packet persistence blob."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from services.fiqa_api.inbox_triage.case_store import get_case_by_id
from services.fiqa_api.p16.packet_persist import (
    build_p16_broker_packet_blob,
    build_portal_copy_text_add_car,
    map_add_car_readiness,
    map_policy_review_readiness,
)
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


def test_map_readiness_labels() -> None:
    assert map_add_car_readiness(still_needed=["vin"], warnings=[]) == "NEED_INFO"
    assert map_add_car_readiness(still_needed=[], warnings=["Multiple VINs found"]) == "BROKER_REVIEW"
    assert map_add_car_readiness(still_needed=[], warnings=[]) == "READY"
    assert map_policy_review_readiness("ready") == "READY"
    assert map_policy_review_readiness("needs_info") == "NEED_INFO"
    assert map_policy_review_readiness("broker_review") == "BROKER_REVIEW"


def test_portal_copy_text_add_car() -> None:
    packet = {
        "customer_name": _intake_field("Andy Li"),
        "phone": _intake_field("6265550000"),
        "garaging_zip": _intake_field("91101"),
        "vin": _extracted_field("5UXZV4C56BL402905"),
        "year": _extracted_field("2011"),
        "make": _extracted_field("BMW"),
        "model": _extracted_field("X5"),
    }
    text = build_portal_copy_text_add_car(packet=packet, warnings=[], request_type="add_vehicle")
    assert "Customer Name: Andy Li" in text
    assert "BMW" in text
    assert "5UXZV4C56BL402905" in text


def test_persist_add_car_includes_p16_broker_packet() -> None:
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
        copy_text="ADD-CAR PACKET\nCustomer: Andy Li",
        sources=[{"file": "insurance_card.png", "fields": "vin"}],
    )
    assert case_id
    stored = get_case_by_id(case_id)
    assert stored is not None
    blob = stored.get("p16_broker_packet")
    assert isinstance(blob, dict)
    assert blob.get("request_type") == "add_vehicle"
    assert blob.get("readiness_status") == "READY"
    assert blob.get("copy_text", "").startswith("ADD-CAR")
    assert "portal_copy_text" in blob
    assert blob.get("packet", {}).get("vin", {}).get("value") == "5UXZV4C56BL402905"


def test_build_p16_broker_packet_blob_shape() -> None:
    blob = build_p16_broker_packet_blob(
        request_type="policy_review",
        readiness_status="READY",
        copy_text="POLICY REVIEW PACKET",
        opportunity_signals=[{"code": "requote", "meaning": "test"}],
        broker_next_action={"en": "Shop", "zh": "比价"},
        follow_up_message_zh="请补充",
    )
    assert blob["request_type"] == "policy_review"
    assert blob["opportunity_signals"][0]["code"] == "requote"
    assert blob["broker_next_action"]["en"] == "Shop"
