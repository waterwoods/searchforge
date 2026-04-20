"""Unit tests for bounded Add-Car LLM slot candidate layer (no live API)."""

from __future__ import annotations

import re

import pytest

from services.fiqa_api.inbox_triage.add_car_llm_slot_candidates import (
    _build_augmentation_fragments,
    _parse_llm_json,
    add_car_llm_slot_extraction_enabled,
    maybe_augment_merged_text_for_add_car_slots,
)
from services.fiqa_api.inbox_triage.triage import _extract_add_car_fields


def test_parse_llm_json_strips_markdown_fence() -> None:
    raw = '```json\n{"certainty":"high","candidate_year":"2022"}\n```'
    p = _parse_llm_json(raw)
    assert p is not None
    assert p.get("candidate_year") == "2022"


def test_build_augmentation_validates_and_drops_hallucinated_zip() -> None:
    parts, acc = _build_augmentation_fragments(
        {
            "candidate_zip": "12345",
            "candidate_year": "2021",
            "candidate_vehicle_make": "Honda",
            "candidate_vehicle_model": "Civic",
        },
        last_customer_bubble="adding a 2021 Honda Civic",
    )
    blob = " ".join(parts)
    assert "12345" not in blob
    assert "2021" in blob
    assert "make_model" in acc
    assert "zip" not in acc


def test_build_augmentation_accepts_ca_zip() -> None:
    _, acc = _build_augmentation_fragments(
        {"candidate_zip": "garaging 95131 thanks"},
        last_customer_bubble="garaging zip thanks",
    )
    assert "zip" in acc


def test_maybe_augment_disabled_no_op(monkeypatch: pytest.MonkeyPatch) -> None:
    merged = "[客户] 想加一台车"
    monkeypatch.delenv("ADD_CAR_LLM_SLOT_EXTRACTION", raising=False)
    out, meta = maybe_augment_merged_text_for_add_car_slots(
        merged,
        "想加一台车",
        rule_fields=_extract_add_car_fields(merged),
        invoke_llm=True,
    )
    assert out == merged
    assert meta.get("skip_reason") == "disabled"
    assert add_car_llm_slot_extraction_enabled() is False


def test_maybe_augment_invoke_false_skips(monkeypatch: pytest.MonkeyPatch) -> None:
    merged = "[客户] 想加一台车"
    monkeypatch.setenv("ADD_CAR_LLM_SLOT_EXTRACTION", "1")
    out, meta = maybe_augment_merged_text_for_add_car_slots(
        merged,
        "想加一台车",
        rule_fields=_extract_add_car_fields(merged),
        invoke_llm=False,
        skip_reason="unit_test",
    )
    assert out == merged
    assert meta.get("skip_reason") == "unit_test"


def test_prepend_synthetic_preserves_last_customer_for_vehicle_concrete() -> None:
    """Synthetic [客户] line is prepended so last bubble stays the real correction message."""
    merged = "[客户] 邮编95131\n\n[客户] 不是X5是2022 Honda Civic"
    frags, _ = _build_augmentation_fragments(
        {"candidate_year": "2020", "candidate_vehicle_make": "Toyota", "candidate_vehicle_model": "Camry"},
        last_customer_bubble="correction: 2020 Toyota Camry",
    )
    assert frags
    syn = " ".join(frags)
    aug = "[客户] " + syn + "\n\n" + merged.strip()
    matches = re.findall(r"\[客户\]\s*([^[]+)", aug)
    assert matches
    assert "不是X5" in (matches[-1] or "")


@pytest.mark.parametrize(
    "payload,expect_year,expect_zip",
    [
        (
            '{"candidate_year":"2024","candidate_zip":"90210","candidate_vin":null,'
            '"candidate_vehicle_make":"Tesla","candidate_vehicle_model":"Model Y",'
            '"candidate_phone":null,"candidate_name":null,"certainty":"high",'
            '"candidate_delivery_note":null,"candidate_primary_driver_self":null,'
            '"correction_intent":false,"ambiguous_vehicle":false}',
            True,
            True,
        ),
    ],
)
def test_rule_extraction_picks_up_validated_fragments(payload: str, expect_year: bool, expect_zip: bool) -> None:
    parsed = _parse_llm_json(payload)
    assert parsed is not None
    frags, _ = _build_augmentation_fragments(
        parsed,
        last_customer_bubble="2024 Tesla Model Y garaging 90210",
    )
    syn = " ".join(frags)
    base = "[客户] messy blob about adding a car no digits"
    aug = "[客户] " + syn + "\n\n" + base
    fields = _extract_add_car_fields(aug)
    assert fields.get("year") is expect_year
    assert fields.get("zip") is expect_zip
    assert fields.get("model") is True
