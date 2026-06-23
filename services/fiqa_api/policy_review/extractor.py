"""
Policy Review document extraction — declaration page, renewal notice, insurance card, etc.
Reuses OCR kill-test image/PDF prep; separate prompt/schema from Add-Car.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

from services.fiqa_api.ocr_kill_test.extractor import (
    _parse_extraction_json,
    _prepare_file,
)

logger = logging.getLogger(__name__)

POLICY_REVIEW_PROMPT = """You are an AI assistant helping a California auto insurance broker review a customer's CURRENT policy.

Your task: extract policy snapshot fields from declaration pages, renewal notices, insurance cards, policy PDFs, or premium screenshots.

Extract ONLY what is visibly present. NEVER invent values.

document_type: one of [
  declaration_page, renewal_notice, insurance_card, policy_pdf, premium_screenshot, mixed, unrelated, unknown
]

Policy fields (flat):
- current_carrier
- policy_number
- policy_term_start (ISO YYYY-MM-DD if possible)
- policy_term_end (ISO YYYY-MM-DD if possible)
- premium_amount (numeric total premium as shown, e.g. "1842.00")
- premium_period (e.g. "6 months", "12 months", "annual")

Coverage (only if visible):
- bodily_injury (e.g. "100/300")
- property_damage
- uninsured_motorist
- comprehensive_deductible
- collision_deductible

vehicles: array of {
  year, make, model, vin, vehicle_premium (if shown per vehicle), source_quote
}

drivers: array of {
  name, relationship, license_state, visible_violation_or_accident (true/false or short note if visible), source_quote
}

CRITICAL RULES:
1. Insurance card alone usually lacks full coverage limits and total premium — note in extraction_notes if so.
2. If TWO different premium amounts or carriers conflict across documents, list in conflicts_found.
3. Violations/accidents: only set visible_violation_or_accident when explicitly shown (surcharge, accident, violation, SR-22).
4. Multi-policy / home / umbrella clues: set cross_sell_clues array with short evidence strings when visible.
5. Do NOT estimate savings, recommend carriers, or guess missing fields.

Respond ONLY with valid JSON:
{
  "document_type": "",
  "extraction_notes": "",
  "cross_sell_clues": [],
  "fields": {
    "current_carrier": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "policy_number": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "policy_term_start": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "policy_term_end": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "premium_amount": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "premium_period": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "bodily_injury": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "property_damage": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "uninsured_motorist": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "comprehensive_deductible": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false},
    "collision_deductible": {"value": "", "confidence": 0.0, "source_quote": "", "needs_confirmation": false}
  },
  "vehicles": [],
  "drivers": [],
  "conflicts_found": []
}
"""


def _conf_label(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


def _field_dict(value: str, confidence: float, source_file: str, *, needs_confirmation: bool = False) -> dict:
    return {
        "value": value,
        "confidence": confidence,
        "confidence_label": _conf_label(confidence),
        "source_file": source_file,
        "is_mock": False,
        "needs_confirmation": needs_confirmation,
    }


def _empty_field() -> dict:
    return {
        "value": "",
        "confidence": 0.0,
        "confidence_label": "low",
        "source_file": "",
        "is_mock": False,
    }


def _extract_single_file_openai(file_path: Path) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    parts = _prepare_file(file_path)
    if not parts:
        return {"document_type": "unknown", "fields": {}, "vehicles": [], "drivers": [], "conflicts_found": [], "_error": "Could not render file"}

    content: list[dict[str, Any]] = [{"type": "text", "text": POLICY_REVIEW_PROMPT}]
    for b64, mime, label in parts:
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}})
        content.append({"type": "text", "text": f"[Document: {label}]"})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        temperature=0.0,
        max_tokens=4096,
    )
    raw = response.choices[0].message.content or ""
    parsed = _parse_extraction_json(raw)
    if parsed is None:
        return {"document_type": "unknown", "fields": {}, "vehicles": [], "drivers": [], "conflicts_found": [], "_parse_error": True}
    parsed["_model"] = "gpt-4o"
    return parsed


def _extract_single_file_gemini(file_path: Path) -> dict:
    import io

    import google.generativeai as genai
    import PIL.Image

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    parts = _prepare_file(file_path)
    if not parts:
        return {"document_type": "unknown", "fields": {}, "vehicles": [], "drivers": [], "conflicts_found": [], "_error": "Could not render file"}

    content_parts: list[Any] = [POLICY_REVIEW_PROMPT]
    for b64, _mime, label in parts:
        img_bytes = base64.b64decode(b64)
        content_parts.append(PIL.Image.open(io.BytesIO(img_bytes)))
        content_parts.append(f"[Document: {label}]")

    response = model.generate_content(content_parts)
    raw = response.text or ""
    parsed = _parse_extraction_json(raw)
    if parsed is None:
        return {"document_type": "unknown", "fields": {}, "vehicles": [], "drivers": [], "conflicts_found": [], "_parse_error": True}
    parsed["_model"] = "gemini-2.0-flash"
    return parsed


def _get_policy_review_extractor():
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    return None


def _extract_single_file(file_path: Path) -> dict:
    provider = _get_policy_review_extractor()
    if provider == "openai":
        return _extract_single_file_openai(file_path)
    if provider == "gemini":
        return _extract_single_file_gemini(file_path)
    return {
        "document_type": "unknown",
        "fields": {},
        "vehicles": [],
        "drivers": [],
        "conflicts_found": [],
        "_dry_run": True,
    }


def _merge_scalar_field(existing: dict | None, new_val: str, conf: float, source: str, needs_conf: bool) -> dict:
    if not new_val:
        return existing or _empty_field()
    if existing and (existing.get("value") or "").strip():
        if (existing.get("value") or "").strip().lower() == new_val.strip().lower():
            return existing
        # conflict — keep higher confidence; caller handles conflicts list
        if float(existing.get("confidence") or 0) >= conf:
            return existing
    return _field_dict(new_val, conf, source, needs_confirmation=needs_conf)


def merge_policy_review_extractions(per_file: list[tuple[str, dict]]) -> dict:
    """Merge per-file extraction JSON into unified snapshot."""
    merged_fields: dict[str, dict] = {}
    vehicles: list[dict] = []
    drivers: list[dict] = []
    document_types: list[str] = []
    warnings: list[str] = []
    cross_sell: list[str] = []
    all_conflicts: list[dict] = []
    extraction_notes: list[str] = []
    model_used = "unknown"

    for fname, result in per_file:
        if result.get("_model"):
            model_used = str(result["_model"])
        doc_type = (result.get("document_type") or "unknown").strip()
        if doc_type:
            document_types.append(doc_type)
        if result.get("extraction_notes"):
            extraction_notes.append(str(result["extraction_notes"]))
        for clue in result.get("cross_sell_clues") or []:
            c = str(clue).strip()
            if c and c not in cross_sell:
                cross_sell.append(c)
        all_conflicts.extend(result.get("conflicts_found") or [])
        if result.get("_error"):
            warnings.append(f"{fname}: {result['_error']}")

        raw_fields = result.get("fields") or {}
        for key, fdata in raw_fields.items():
            val = (fdata.get("value") or "").strip()
            conf = float(fdata.get("confidence") or 0.0)
            needs = bool(fdata.get("needs_confirmation"))
            merged_fields[key] = _merge_scalar_field(merged_fields.get(key), val, conf, fname, needs)

        for v in result.get("vehicles") or []:
            if not isinstance(v, dict):
                continue
            entry = {
                "year": (v.get("year") or "").strip(),
                "make": (v.get("make") or "").strip(),
                "model": (v.get("model") or "").strip(),
                "vin": (v.get("vin") or "").strip().upper(),
                "vehicle_premium": (v.get("vehicle_premium") or "").strip(),
                "source_file": fname,
            }
            if any(entry[k] for k in ("year", "make", "model", "vin")):
                vehicles.append(entry)

        for d in result.get("drivers") or []:
            if not isinstance(d, dict):
                continue
            entry = {
                "name": (d.get("name") or "").strip(),
                "relationship": (d.get("relationship") or "").strip(),
                "license_state": (d.get("license_state") or "").strip(),
                "visible_violation_or_accident": (d.get("visible_violation_or_accident") or "").strip(),
                "source_file": fname,
            }
            if entry["name"]:
                drivers.append(entry)

    for c in all_conflicts:
        field = c.get("field") or "unknown"
        warnings.append(f"Conflicting {field} values detected across documents — verify manually")

    return {
        "fields": merged_fields,
        "vehicles": vehicles,
        "drivers": drivers,
        "document_types": document_types,
        "warnings": warnings,
        "cross_sell_clues": cross_sell,
        "extraction_notes": extraction_notes,
        "conflicts": all_conflicts,
        "model_used": model_used,
    }


def run_policy_review_extraction(file_paths: list[Path], file_names: list[str]) -> dict:
    per_file: list[tuple[str, dict]] = []
    for path, name in zip(file_paths, file_names):
        try:
            per_file.append((name, _extract_single_file(path)))
        except Exception as exc:
            logger.exception("Policy review extraction failed for %s", name)
            per_file.append((name, {"document_type": "unknown", "fields": {}, "vehicles": [], "drivers": [], "_error": str(exc)[:200]}))
    return merge_policy_review_extractions(per_file)
