"""Focused tests: correction → overwrite → truth update (add-car chain)."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.triage import (
    _derive_follow_up_type,
    _extract_add_car_fields_truth_safe,
    _extract_primary_add_car_vehicle_concrete,
    triage_conversation,
)


def _cust_turns(*lines: str) -> list[dict[str, str]]:
    return [{"role": "customer", "text": t} for t in lines]


def test_partial_vin_then_full_vin_correction_truth_and_key() -> None:
    prior = _cust_turns(
        "add car 2024 Toyota Camry zip 90210 delivery 05/15/2026 primary driver is me",
        "VIN 12345",
    )
    latest = "sorry wrong VIN, it is 1HGBH41JXMN109186"
    r = triage_conversation(latest, prior, client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    assert r.get("vehicle_key") == "vin:1HGBH41JXMN109186"
    blob = "\n\n".join(f"[客户] {t['text']}" for t in prior + [{"role": "customer", "text": latest}])
    fields = _extract_add_car_fields_truth_safe(blob)
    assert fields.get("vin") is True


def test_stale_make_correction_updates_summary_concrete() -> None:
    prior = _cust_turns("add car 2024 Toyota Camry zip 90210")
    latest = "not Toyota, it's Honda Accord"
    r = triage_conversation(latest, prior, client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    pvc = (r.get("primary_vehicle_summary") or "").lower()
    assert "honda" in pvc and "accord" in pvc
    assert "toyota" not in pvc and "camry" not in pvc
    merged = "\n\n".join(f"[客户] {t['text']}" for t in prior + [{"role": "customer", "text": latest}])
    assert "honda" in (_extract_primary_add_car_vehicle_concrete(merged) or "").lower()


def test_actually_i_already_sent_is_already_sent_not_correction() -> None:
    assert _derive_follow_up_type("Actually I already sent the screenshot via WeChat") == "already_sent"
    assert _derive_follow_up_type("actually I've sent the registration") == "already_sent"


def test_correction_turn_does_not_force_premature_handoff() -> None:
    prior = _cust_turns("add car")
    latest = "2024 Toyota Camry"
    r = triage_conversation(latest, prior, client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    assert r.get("handoff_ready") is False
