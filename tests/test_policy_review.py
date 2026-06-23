"""Unit tests for Policy Review lane — readiness, signals, follow-up, mock scenarios."""

from __future__ import annotations

from services.fiqa_api.policy_review.handler import _mock_merged_from_filenames
from services.fiqa_api.policy_review.readiness import (
    SIGNAL_FOLLOW_UP,
    SIGNAL_NO_OVERPROMISE,
    SIGNAL_REQUOTE,
    SIGNAL_VIOLATION,
    build_chinese_follow_up,
    build_opportunity_signals,
    compute_readiness,
)
from services.fiqa_api.policy_review.packet import build_copy_text


def _ready_fields() -> dict:
    return {
        "current_carrier": {"value": "GEICO"},
        "premium_amount": {"value": "1200"},
        "premium_period": {"value": "6 months"},
        "bodily_injury": {"value": "100/300"},
        "property_damage": {"value": "100"},
        "comprehensive_deductible": {"value": "500"},
        "collision_deductible": {"value": "500"},
    }


def test_declaration_mock_is_ready() -> None:
    merged = _mock_merged_from_filenames(["declaration_page.pdf"])
    readiness, _ = compute_readiness(
        fields=merged["fields"],
        vehicles=merged["vehicles"],
        document_types=merged["document_types"],
        warnings=merged["warnings"],
        conflicts=merged["conflicts"],
        extraction_notes=merged["extraction_notes"],
    )
    assert readiness == "ready"


def test_insurance_card_only_is_needs_info() -> None:
    merged = _mock_merged_from_filenames(["insurance_card.jpg"])
    readiness, reasons = compute_readiness(
        fields=merged["fields"],
        vehicles=merged["vehicles"],
        document_types=merged["document_types"],
        warnings=merged["warnings"],
        conflicts=merged["conflicts"],
        extraction_notes=merged["extraction_notes"],
    )
    assert readiness == "needs_info"
    assert "declaration_page" in reasons or "premium" in reasons


def test_chinese_follow_up_on_needs_info() -> None:
    msg = build_chinese_follow_up("needs_info", ["declaration_page"])
    assert "Declaration Page" in msg
    assert msg.startswith("您好")


def test_opportunity_signals_no_savings_claims() -> None:
    fields = _ready_fields()
    vehicles = [{"year": "2022", "make": "Toyota", "model": "Camry", "vin": "X"}]
    signals = build_opportunity_signals(
        readiness="ready",
        fields=fields,
        vehicles=vehicles,
        drivers=[],
        warnings=[],
        cross_sell_clues=[],
        extraction_notes=[],
    )
    codes = {s["code"] for s in signals}
    assert SIGNAL_REQUOTE in codes
    assert not any("save" in s["meaning"].lower() for s in signals)


def test_violation_signal_when_visible() -> None:
    drivers = [{"name": "Li", "visible_violation_or_accident": "At-fault accident 2023"}]
    signals = build_opportunity_signals(
        readiness="broker_review",
        fields=_ready_fields(),
        vehicles=[{"year": "2020", "make": "Honda", "model": "Accord", "vin": "Y"}],
        drivers=drivers,
        warnings=[],
        cross_sell_clues=[],
        extraction_notes=[],
    )
    codes = {s["code"] for s in signals}
    assert SIGNAL_VIOLATION in codes
    assert SIGNAL_NO_OVERPROMISE in codes


def test_broker_review_on_conflicting_premium() -> None:
    readiness, reasons = compute_readiness(
        fields=_ready_fields(),
        vehicles=[{"year": "2020", "make": "Honda", "model": "Accord", "vin": "Y"}],
        document_types=["declaration_page"],
        warnings=["Conflicting premium_amount values detected across documents — verify manually"],
        conflicts=[{"field": "premium_amount"}],
        extraction_notes=[],
    )
    assert readiness == "broker_review"
    assert "conflicting" in reasons[0]


def test_copy_text_includes_packet_header() -> None:
    from services.fiqa_api.policy_review.packet import build_policy_review_packet

    merged = _mock_merged_from_filenames(["declaration.pdf"])
    built = build_policy_review_packet(
        customer_name="Li Hua",
        phone="6265550000",
        garaging_zip="91101",
        merged=merged,
        is_mock=True,
    )
    text = build_copy_text(
        packet=built["packet"],
        vehicles=built["vehicles"],
        drivers=built["drivers"],
        warnings=merged["warnings"],
        sources=[{"file": "declaration.pdf", "fields": "carrier"}],
        opportunity_signals=[{"code": SIGNAL_REQUOTE, "meaning": "test"}],
        broker_next_action={"en": "Act", "zh": "行动"},
        mock_mode=True,
    )
    assert "Policy Review Packet" in text
    assert "当前保单分析资料包" in text
    assert "Broker Next Action" in text
    assert "GEICO" in text


def test_follow_up_required_signal_on_needs_info() -> None:
    signals = build_opportunity_signals(
        readiness="needs_info",
        fields={},
        vehicles=[],
        drivers=[],
        warnings=[],
        cross_sell_clues=[],
        extraction_notes=[],
    )
    assert any(s["code"] == SIGNAL_FOLLOW_UP for s in signals)
