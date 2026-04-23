"""Surgical regression tests for live blocking trust bugs (handoff vs still_needed; vehicle correction)."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.triage import triage_conversation
from services.fiqa_api.inbox_triage.triage_handoff_reply_composer import (
    enforce_add_car_handoff_structural_consistency,
)


def test_enforce_clears_ready_when_quote_ready_and_contact_still_open() -> None:
    """
    When quote_ready but name/phone are still in still_needed, action_ready + ready copy
    must be downgraded (regression: trust helper used to no-op for action_ready-only paths).
    """
    r: dict = {
        "service_type": "add_car",
        "triage_mode": "greenfield",
        "handoff_ready": False,
        "action_ready": True,
        "quote_ready_status": "quote_ready",
        "still_needed_fields": ["name", "phone"],
        "collected_fields": [
            "vin",
            "zip",
            "year",
            "make_model",
            "delivery_date",
            "primary_driver",
        ],
        "lifecycle_status": "collecting",
        "intake_next_best_ask": "Please add your name and phone.",
        "client_reply_draft": (
            "I've got everything I need to get started. I'll begin preparing your quote "
            "and follow up if anything else is needed."
        ),
    }
    enforce_add_car_handoff_structural_consistency(r)
    assert r.get("action_ready") is False
    assert "everything i need" not in (r.get("client_reply_draft") or "").lower()


def test_explicit_honda_to_toyota_correction_binds_primary_and_reply() -> None:
    prior = [
        {"role": "customer", "text": "add car 2021 Honda Accord zip 90210 VIN 1HGBH41JXMN109186 driver is me"},
    ]
    latest = "Actually not Honda, Toyota Camry 2021"
    r = triage_conversation(latest, prior, client_id="chen_kui")
    pvs = (r.get("primary_vehicle_summary") or "").lower()
    assert "toyota" in pvs and "camry" in pvs
    assert "honda" not in pvs and "accord" not in pvs
    draft = (r.get("client_reply_draft") or "").lower()
    assert "honda" not in draft
    assert "accord" not in draft


def test_dense_add_car_path_still_handoffs_when_complete() -> None:
    """Light regression: dense happy path should still reach a coherent add-car outcome."""
    lines = [
        "I want to add a vehicle",
        "2023 Toyota RAV4 zip 94110",
        "VIN 2T3B1RFV8PC123456 delivery March 1 2026 I am the only driver",
        "name Jane Doe phone 415-555-0100",
    ]
    conv: list[dict[str, str]] = []
    last = None
    for line in lines:
        last = triage_conversation(line, conv, client_id="chen_kui")
        conv.append({"role": "customer", "text": line})
    assert last is not None
    assert last.get("service_type") == "add_car"
    assert last.get("primary_vehicle_summary")
    assert last.get("handoff_ready") is True or last.get("quote_ready_status") == "quote_ready"
