"""Assist layer: missing_required_fields union for Add-Car (Unified Intake)."""

from services.fiqa_api.inbox_triage.assist_layer import _missing_required_fields_for_assist


def test_add_car_unions_critical_fields_before_still_needed():
    tr = {
        "service_type": "add_car",
        "still_needed_fields": ["year", "make_model", "zip"],
        "collected_fields": [],
    }
    m = _missing_required_fields_for_assist(tr)
    assert m[:4] == ["vin", "delivery_date", "zip", "primary_driver"]
    assert "year" in m and "make_model" in m
    assert m.count("zip") == 1


def test_non_add_car_unchanged():
    tr = {
        "service_type": "general_inquiry",
        "still_needed_fields": ["payment_notice_or_screenshot"],
        "collected_fields": [],
    }
    assert _missing_required_fields_for_assist(tr) == ["payment_notice_or_screenshot"]


def test_structural_still_needed_triggers_union_without_service_type():
    tr = {
        "service_type": "customer_question",
        "still_needed_fields": ["year", "make_model", "zip"],
        "collected_fields": [],
    }
    m = _missing_required_fields_for_assist(tr)
    assert m[0] == "vin"
    assert "zip" in m


def test_skips_critical_slots_already_collected():
    tr = {
        "service_type": "add_car",
        "still_needed_fields": ["year"],
        "collected_fields": ["vin", "zip", "delivery_date", "primary_driver"],
    }
    m = _missing_required_fields_for_assist(tr)
    assert "vin" not in m
    assert "zip" not in m
    assert "delivery_date" not in m
    assert "primary_driver" not in m
    assert "year" in m
