"""P20 MVP request-type gating helpers."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.p20_missing_information import (
    derive_missing_information_checklist,
    is_mvp_sendable_item_type,
    list_unsupported_send_item_labels,
)


def test_mvp_sendable_is_vin_only():
    assert is_mvp_sendable_item_type("vin") is True
    assert is_mvp_sendable_item_type("VIN") is True
    assert is_mvp_sendable_item_type("free_text") is False
    assert is_mvp_sendable_item_type("policy_or_insurance_card") is False
    assert is_mvp_sendable_item_type("photo_evidence") is False


def test_checklist_flags_mvp_sendable_and_suggests_vin_only():
    checklist = derive_missing_information_checklist({})
    by_key = {row["field_key"]: row for row in checklist}
    assert by_key["vin"]["mvp_sendable"] is True
    assert by_key["vin"]["suggested_for_request"] is True
    assert by_key["vehicle_information"]["mvp_sendable"] is False
    assert by_key["vehicle_information"]["suggested_for_request"] is False
    assert by_key["policy_or_insurance_card"]["mvp_sendable"] is False
    assert by_key["policy_or_insurance_card"]["suggested_for_request"] is False


def test_list_unsupported_send_item_labels():
    labels = list_unsupported_send_item_labels(
        [
            {"item_type": "vin", "label": "VIN"},
            {"item_type": "free_text", "label": "Vehicle year / make / model"},
        ]
    )
    assert labels == ["Vehicle year / make / model"]
