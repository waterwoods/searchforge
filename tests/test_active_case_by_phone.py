"""P16 Customer First — phone normalization and active case lookup tests."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.active_case_lookup import (
    active_add_car_case_summary,
    find_active_add_car_case_by_phone,
    is_customer_formal_submitted,
    resolve_customer_business_state,
    resolve_customer_contact_state,
)
from services.fiqa_api.inbox_triage.phone_normalization import (
    is_valid_customer_phone,
    normalize_phone_digits,
)


def test_normalize_phone_us_formats():
    assert normalize_phone_digits("(626) 555-0101") == "6265550101"
    assert normalize_phone_digits("+1 626-555-0101") == "6265550101"
    assert normalize_phone_digits("6265550101") == "6265550101"
    assert normalize_phone_digits("") == ""
    assert is_valid_customer_phone("(626) 555-0101") is True
    assert is_valid_customer_phone("626555010") is False


def test_find_active_add_car_case_by_phone():
    cases = [
        {
            "case_id": "case_closed",
            "case_status": "closed",
            "customer_phone": "6265550101",
            "service_lane": "add_car",
            "lifecycle_status": "collecting",
        },
        {
            "case_id": "case_tesla",
            "case_status": "new",
            "customer_phone": "6265550101",
            "service_lane": "add_car",
            "lifecycle_status": "collecting",
            "primary_vehicle_summary": "2024 Tesla Model Y",
            "still_needed_fields": ["vin"],
            "updated_at": "2026-06-07T12:00:00Z",
        },
        {
            "case_id": "case_other_phone",
            "case_status": "new",
            "customer_phone": "4155550101",
            "service_lane": "add_car",
            "lifecycle_status": "collecting",
        },
    ]
    found = find_active_add_car_case_by_phone("6265550101", cases)
    assert found is not None
    assert found["case_id"] == "case_tesla"
    assert find_active_add_car_case_by_phone("4155550101", cases)["case_id"] == "case_other_phone"
    assert find_active_add_car_case_by_phone("9995550101", cases) is None


def test_submit_state_collecting_is_not_formal():
    case = {
        "lifecycle_status": "collecting",
        "formal_submitted_at": "2026-06-07T10:00:00Z",
    }
    assert is_customer_formal_submitted(case) is False
    summary = active_add_car_case_summary(
        {
            "case_id": "c1",
            "lifecycle_status": "collecting",
            "primary_vehicle_summary": "2024 Tesla Model Y",
            "still_needed_fields": ["vin"],
        }
    )
    assert summary["submit_state"] == "not_yet"
    assert summary["status_label"] == "saved_not_yet_submitted"
    assert summary["contact_state"] == "waiting_for_customer"
    assert summary["business_state"] == "awaiting_customer"
    assert summary["vehicle_display"] == "2024 Tesla Model Y"
    assert summary["missing_fields"] == ["vin"]


def test_contact_state_submitted_office_reviewing():
    case = {
        "case_id": "c2",
        "lifecycle_status": "handed_off",
        "formal_submitted_at": "2026-06-07T10:00:00Z",
        "still_needed_fields": [],
        "waiting_on": "none",
    }
    assert resolve_customer_contact_state(case) == "office_reviewing"
    summary = active_add_car_case_summary(case)
    assert summary["status_label"] == "submitted_to_office"
    assert summary["contact_state"] == "office_reviewing"
    assert summary["business_state"] == "submitted_to_office"


def test_contact_state_broker_reviewing():
    case = {
        "case_id": "c3",
        "lifecycle_status": "handed_off",
        "formal_submitted_at": "2026-06-07T10:00:00Z",
        "still_needed_fields": [],
        "waiting_on": "broker",
    }
    assert resolve_customer_contact_state(case) == "broker_reviewing"
    summary = active_add_car_case_summary(case)
    assert summary["contact_state"] == "broker_reviewing"
    assert summary["business_state"] == "office_processing"


def test_contact_state_missing_vin_waiting_for_customer():
    case = {
        "case_id": "c4",
        "lifecycle_status": "collecting",
        "still_needed_fields": ["vin", "primary_driver"],
        "waiting_on": "none",
    }
    assert resolve_customer_contact_state(case) == "waiting_for_customer"
    summary = active_add_car_case_summary(case)
    assert summary["still_needed_fields"] == ["vin", "primary_driver"]


def test_corrupted_office_followup_with_gaps_not_formal_submitted():
    """P16 status truth: missing fields must never read as submitted_to_office."""
    case = {
        "case_id": "c5",
        "lifecycle_status": "office_followup",
        "formal_submitted_at": "2026-06-07T10:00:00Z",
        "still_needed_fields": ["year", "make_model"],
        "waiting_on": "none",
        "service_lane": "add_car",
    }
    assert is_customer_formal_submitted(case) is False
    summary = active_add_car_case_summary(case)
    assert summary["status_label"] == "saved_not_yet_submitted"
    assert summary["contact_state"] == "waiting_for_customer"
    assert summary["business_state"] == "awaiting_customer"


def test_business_state_office_followup():
    case = {
        "case_id": "c6",
        "lifecycle_status": "office_followup",
        "formal_submitted_at": "2026-06-07T10:00:00Z",
        "still_needed_fields": [],
        "waiting_on": "none",
    }
    assert resolve_customer_business_state(case) == "office_processing"
    summary = active_add_car_case_summary(case)
    assert summary["business_state"] == "office_processing"


def test_business_state_closed():
    case = {
        "case_id": "c7",
        "case_status": "closed",
        "lifecycle_status": "handed_off",
        "formal_submitted_at": "2026-06-07T10:00:00Z",
        "still_needed_fields": [],
    }
    assert resolve_customer_business_state(case) == "closed"
