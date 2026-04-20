"""Add-Car Stage 1 field contract: canonical keys, triage lists, quote_ready coherence."""

from services.fiqa_api.inbox_triage.add_car_field_contract import (
    load_add_car_stage1_contract,
    quote_ready_matches_still_needed,
    validate_add_car_field_lists,
)
from services.fiqa_api.inbox_triage.triage import _is_add_vehicle_request, triage_conversation


def test_english_add_a_car_is_add_vehicle_intent():
    assert _is_add_vehicle_request("I want to add a car")


def test_contract_json_loads_and_labels_cover_canonical_ids():
    data = load_add_car_stage1_contract()
    assert data.get("version") == 1
    ids = set(data["canonical_field_ids"])
    labels = data["labels_zh"]
    for k in ids:
        assert k in labels, f"missing zh label for canonical id {k!r}"


def test_triage_add_car_respects_contract_lists_and_quote_coherence():
    """VIN required for quote_ready; partial vehicle + zip + relative delivery stays need_more / lists VIN."""
    turns = [
        {"role": "customer", "text": "想加一台 2024 Tesla Model Y 在 90210 下周提车"},
        {"role": "customer", "text": "我姓张 电话 415-555-0100"},
    ]
    out = triage_conversation("我姓张 电话 415-555-0100", turns, client_id="chen_kui", reply_truth_context=None)
    validate_add_car_field_lists(out.get("collected_fields"), out.get("still_needed_fields"), strict=True)
    assert out.get("quote_ready_status") == "need_more"
    assert "vin" in (out.get("still_needed_fields") or [])
    assert quote_ready_matches_still_needed(
        str(out.get("quote_ready_status") or ""),
        out.get("still_needed_fields"),
    )


def test_quote_ready_mismatch_detected():
    assert not quote_ready_matches_still_needed("quote_ready", ["zip", "name"])


def test_triage_add_car_emits_coherent_lists_single_turn():
    turns = [{"role": "customer", "text": "加车 2024 BMW X5 90210 下周提车 就我开"}]
    out = triage_conversation(
        "加车 2024 BMW X5 90210 下周提车 就我开",
        turns,
        client_id="chen_kui",
        reply_truth_context=None,
    )
    assert out.get("issue_category") == "customer_question"
    assert out.get("triage_mode") == "greenfield"
    validate_add_car_field_lists(out.get("collected_fields"), out.get("still_needed_fields"), strict=True)
    assert quote_ready_matches_still_needed(
        str(out.get("quote_ready_status") or ""),
        out.get("still_needed_fields"),
    )


def test_contact_gate_turn4_forces_collecting():
    """Turn 4+ without name/phone: handoff_ready false when quote_ready (contract §4.2)."""
    turns = [
        {
            "role": "customer",
            "text": (
                "Add a car VIN 1HGBH41JXMN109186 zip 90210 "
                "delivery 04/16/2026 I am the primary driver"
            ),
        },
        {"role": "customer", "text": "ok"},
        {"role": "customer", "text": "thanks"},
    ]
    out = triage_conversation("When can I get the quote?", turns, client_id="chen_kui", reply_truth_context=None)
    assert out.get("quote_ready_status") == "quote_ready"
    assert out.get("handoff_ready") is False
    assert out.get("lifecycle_status") == "collecting"
    sn = out.get("still_needed_fields") or []
    assert "name" in sn or "phone" in sn
