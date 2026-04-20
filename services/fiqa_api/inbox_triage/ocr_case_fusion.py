"""
V6: Multi-source fusion — OCR field candidates > typed text extraction > auto_fill defaults.

Produces merged inferred_fields entries with source tags for UI (ocr vs heuristic).
"""

from __future__ import annotations

from typing import Any

# Match case_draft_engine tier strings (avoid import cycle with case_draft_engine)
CONF_HIGH = "high"
CONF_MEDIUM = "medium"
CONF_LOW = "low"


def fuse_ocr_into_inferred(
    merged_text: str,
    *,
    inferred_fields: dict[str, Any],
    ocr_structured: dict[str, Any] | None,
    v6_variant: str,
) -> dict[str, Any]:
    """
    Merge OCR structured_fields into inferred_fields. OCR wins on same slot when confidence adequate.
    v6_variant: A=text-first (downweight OCR in UI tier), B=aggressive (boost OCR), C=conservative confirm.
    """
    out = dict(inferred_fields or {})
    if not ocr_structured or not isinstance(ocr_structured, dict):
        return out

    v = (v6_variant or "A").strip().upper()
    boost = 0.0
    if v == "B":
        boost = 0.08
    elif v == "C":
        boost = -0.05

    sf = ocr_structured.get("structured_fields") if isinstance(ocr_structured.get("structured_fields"), dict) else {}
    for key, blob in sf.items():
        if not isinstance(blob, dict):
            continue
        val = blob.get("value")
        if val is None or str(val).strip() == "":
            continue
        conf = float(blob.get("confidence") or 0.5) + boost
        tier = CONF_MEDIUM if conf >= 0.55 else CONF_LOW
        if conf >= 0.82:
            tier = CONF_HIGH
        entry = {
            "value": str(val).strip(),
            "confidence": min(0.95, max(0.12, conf)),
            "tier": tier,
            "source": "ocr_extract",
            "v6_highlight": True,
            "needs_confirmation": v in ("A", "C") or conf < 0.72,
        }
        # Map to inferred pack keys used elsewhere
        if key == "make_model":
            out["vehicle_from_summary"] = {
                "hint": entry["value"],
                "confidence": entry["confidence"],
                "tier": tier,
                "source": "ocr_vehicle",
                "needs_confirmation": entry["needs_confirmation"],
                "v6_highlight": True,
            }
        elif key == "year":
            out["year_from_ocr"] = entry
        elif key == "zip":
            out["zip_from_ocr"] = entry
        elif key == "vin":
            out["vin_from_ocr"] = entry
        elif key in ("insurance_provider_guess",):
            out["insurance_provider_guess"] = entry
        elif key == "primary_name_guess":
            out["name_from_ocr"] = entry

    return out


def build_supplemental_extraction_blob(ocr_signals: dict[str, Any] | None) -> str:
    """Append to merged extraction text so rule/LLM layers see OCR tokens."""
    if not ocr_signals or not isinstance(ocr_signals, dict):
        return ""
    parts: list[str] = []
    raw = str(ocr_signals.get("last_raw_text") or "").strip()
    if raw:
        parts.append(raw[:4000])
    sf = ocr_signals.get("structured_fields")
    if isinstance(sf, dict):
        for k, v in sf.items():
            if isinstance(v, dict) and v.get("value"):
                parts.append(f"{k}: {v.get('value')}")
    return "\n".join(parts).strip()
