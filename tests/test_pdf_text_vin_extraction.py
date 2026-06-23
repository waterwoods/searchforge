"""PDF text-layer VIN preference over Vision OCR (P16 conditional fix)."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.fiqa_api.ocr_kill_test.extractor import (
    _apply_pdf_text_vin_preference,
    try_pdf_text_layer_vin,
)

CORPUS = Path(__file__).resolve().parent.parent / "test_data" / "p16_real_docs"


def test_try_pdf_text_layer_vin_pa_001_exact_match() -> None:
    pdf = CORPUS / "purchase_agreements/pa_001_toyota_camry.pdf"
    assert pdf.exists()
    vin = try_pdf_text_layer_vin(pdf)
    assert vin == "4T1BF1FK5CU512345"
    assert len(vin) == 17


def test_try_pdf_text_layer_vin_all_purchase_agreements() -> None:
    pdfs = sorted((CORPUS / "purchase_agreements").glob("*.pdf"))
    assert len(pdfs) >= 5
    for pdf in pdfs:
        vin = try_pdf_text_layer_vin(pdf)
        assert len(vin) == 17, f"Expected 17-char VIN from {pdf.name}, got {vin!r}"


def test_try_pdf_text_layer_vin_non_pdf_returns_empty() -> None:
    jpg = CORPUS / "registrations/reg_001_ca_dmv.jpg"
    if jpg.exists():
        assert try_pdf_text_layer_vin(jpg) == ""


def test_apply_pdf_text_vin_preference_overrides_wrong_vision_vin() -> None:
    pdf = CORPUS / "purchase_agreements/pa_001_toyota_camry.pdf"
    result = {
        "fields": {
            "vin": {
                "value": "1B1F1FK5CU512345",
                "confidence": 0.9,
                "source_quote": "vision",
                "needs_confirmation": True,
                "notes": "",
            }
        }
    }
    out = _apply_pdf_text_vin_preference(pdf, result)
    assert out["fields"]["vin"]["value"] == "4T1BF1FK5CU512345"
    assert out["fields"]["vin"]["confidence"] == 0.99
    assert "PDF text layer" in out["fields"]["vin"]["notes"]
    assert "Vision OCR had" in out["fields"]["vin"]["notes"]


def test_apply_pdf_text_vin_preference_no_op_when_vision_matches() -> None:
    pdf = CORPUS / "purchase_agreements/pa_001_toyota_camry.pdf"
    result = {
        "fields": {
            "vin": {
                "value": "4T1BF1FK5CU512345",
                "confidence": 0.9,
                "source_quote": "vision",
                "needs_confirmation": False,
                "notes": "",
            }
        }
    }
    out = _apply_pdf_text_vin_preference(pdf, result)
    assert out["fields"]["vin"]["notes"] == ""


def test_apply_pdf_text_vin_preference_fills_empty_vision_vin() -> None:
    pdf = CORPUS / "purchase_agreements/pa_002_honda_civic.pdf"
    result = {"fields": {"vin": {"value": "", "confidence": 0.0, "notes": ""}}}
    out = _apply_pdf_text_vin_preference(pdf, result)
    assert out["fields"]["vin"]["value"] == "2HGFC2F69MH123456"
