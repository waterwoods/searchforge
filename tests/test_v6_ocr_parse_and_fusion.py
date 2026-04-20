"""V6 OCR parsing, fusion, and intake alignment (no network)."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.case_draft_engine import build_v4_case_draft_bundle
from services.fiqa_api.inbox_triage.ocr_case_fusion import build_supplemental_extraction_blob, fuse_ocr_into_inferred
from services.fiqa_api.inbox_triage.parse_ocr_text_to_fields import parse_ocr_text_to_fields


def test_parse_ocr_extracts_vin_and_zip():
    raw = """
    INSURED: JANE DOE
    VIN 1HGCM82633A004352
    GARAGE ZIP 92602
    GEICO
    """
    out = parse_ocr_text_to_fields(raw)
    sf = out["structured_fields"]
    assert sf.get("vin") and "1HGCM82633A004352" in sf["vin"]["value"].upper()
    assert sf.get("zip") and sf["zip"]["value"] == "92602"


def test_fusion_prefers_ocr_over_heuristic():
    inferred = {"usage_guess": {"value": "daily_commute", "confidence": 0.35, "tier": "low"}}
    ocr = {
        "structured_fields": {
            "zip": {"value": "94102", "confidence": 0.7, "source": "ocr_regex"},
        }
    }
    fused = fuse_ocr_into_inferred("text", inferred_fields=inferred, ocr_structured=ocr, v6_variant="B")
    assert "zip_from_ocr" in fused


def test_build_v4_bundle_includes_v6_confirmation():
    b = build_v4_case_draft_bundle(
        merged_text="",
        collected_fields=["vin"],
        missing_fields=["zip"],
        primary_vehicle_summary="2020 Toyota Camry",
        quote_ready_status="almost_ready",
        human_confirmation_fields=[],
        issue_category="customer_question",
        language="en",
        variant="B",
        ocr_context={"structured_fields": {"zip": {"value": "92602", "confidence": 0.6, "source": "ocr_regex"}}},
        v6_auto_input_variant="B",
    )
    assert b.get("v6_confirmation")
    assert b.get("v6_error_tolerance", {}).get("submission_blocked") is False


def test_supplemental_blob_ocr():
    sig = {"last_raw_text": "VIN 1HGCM82633A004352", "structured_fields": {"zip": {"value": "92602"}}}
    blob = build_supplemental_extraction_blob(sig)
    assert "92602" in blob
    assert "OCR" not in blob  # blob is raw; [OCR] added in triage
