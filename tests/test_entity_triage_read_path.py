"""Entity-backed primary line / vehicle_key when get_active_vehicle returns payload."""
from __future__ import annotations

from unittest.mock import patch

from services.fiqa_api.inbox_triage.triage import triage_conversation


def test_add_car_uses_entity_for_primary_and_key_when_present() -> None:
    # Simulates merged row after VIN turn (persist merges VIN; read uses it for key).
    fake_row = {
        "payload": {
            "year": "2021",
            "make": "",
            "model": "toyota_camry",
            "vin": "1HGBH41JXMN109186",
            "zip": "94103",
            "driver": "",
            "source_turns": [],
            "confidence": {},
        }
    }

    with patch(
        "services.fiqa_api.inbox_triage.triage.get_active_vehicle",
        return_value=fake_row,
    ):
        out = triage_conversation(
            "VIN is 1HGBH41JXMN109186.",
            [
                {"role": "customer", "text": "Toyota Camry, zip 94103."},
                {"role": "customer", "text": "Actually 2021 Camry."},
            ],
            client_id="chen_kui",
            reply_truth_context={"session_id": "unit_entity_read_1"},
        )
    assert out.get("service_type") == "add_car"
    assert "2021" in (out.get("primary_vehicle_summary") or "")
    vk = (out.get("vehicle_key") or "").lower()
    assert "vin:" in vk


def test_first_vehicle_anchor_skips_entity_override() -> None:
    fake_row = {
        "payload": {
            "year": "2022",
            "make": "",
            "model": "tesla_model_y",
            "vin": "",
            "zip": "90210",
            "driver": "",
            "source_turns": [],
            "confidence": {},
        }
    }

    with patch(
        "services.fiqa_api.inbox_triage.triage.get_active_vehicle",
        return_value=fake_row,
    ):
        out = triage_conversation(
            "Use the first car I mentioned for the quote please.",
            [
                {"role": "customer", "text": "Adding a 2020 Toyota Camry, ZIP 90210, Friday pickup, I drive."},
                {"role": "customer", "text": "Change to 2022 Tesla Model Y, same zip."},
            ],
            client_id="chen_kui",
            reply_truth_context={"session_id": "unit_entity_read_2"},
        )
    assert out.get("service_type") == "add_car"
    summary = out.get("primary_vehicle_summary") or ""
    assert "Camry" in summary
    assert "2020" in summary
