"""Assist layer: Add-Car missing_required_fields union (critical + triage still_needed)."""

from services.fiqa_api.inbox_triage.assist_layer import _missing_required_fields_for_assist


def test_assist_merges_critical_add_car_fields_with_still_needed():
    triage = {
        "service_type": "add_car",
        "still_needed_fields": ["year", "make_model", "zip", "delivery_date", "primary_driver"],
        "collected_fields": ["insurance_status_add_to_existing"],
    }
    m = _missing_required_fields_for_assist(triage)
    assert m[:4] == ["vin", "delivery_date", "zip", "primary_driver"]
    assert "year" in m and "make_model" in m
    assert m.count("zip") == 1
    assert m.count("delivery_date") == 1


def test_assist_soft_route_starter_shape_union():
    triage = {
        "service_type": "general_inquiry",
        "still_needed_fields": ["year", "make_model", "zip"],
        "collected_fields": [],
    }
    m = _missing_required_fields_for_assist(triage)
    assert "vin" in m
    assert "delivery_date" in m
    assert "zip" in m
    assert "primary_driver" in m


def test_assist_normalizes_legacy_model_id_to_make_model():
    triage = {
        "service_type": "add_car",
        "still_needed_fields": ["year", "model", "zip"],
        "collected_fields": [],
    }
    m = _missing_required_fields_for_assist(triage)
    assert "make_model" in m
    assert "model" not in m


def test_assist_skips_critical_when_collected():
    triage = {
        "service_type": "add_car",
        "still_needed_fields": ["year"],
        "collected_fields": ["vin", "zip", "delivery_date", "primary_driver"],
    }
    m = _missing_required_fields_for_assist(triage)
    assert "vin" not in m
    assert "zip" not in m
    assert "delivery_date" not in m
    assert "primary_driver" not in m
    assert "year" in m
