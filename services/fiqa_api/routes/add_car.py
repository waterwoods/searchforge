"""
P16 Trust Layer — Add-Car Trusted Packet extraction endpoint.

POST /api/intake/add-car/extract
    Accepts: multipart/form-data
        files: list[UploadFile]   (PDF, JPG, PNG, HEIC — max 10)
        customer_name: str
        phone: str
        garaging_zip: str
    Returns:
        {
            "packet": {...},
            "warnings": [...],
            "sources": [...],
            "copy_text": "...",
            "mock_mode": bool,
            "model_used": str
        }

Mock mode: if no GEMINI_API_KEY / OPENAI_API_KEY, runs MOCK_EXTRACTION_ONLY.
Never claims real OCR if mock mode was used.
"""

import logging
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

logger = logging.getLogger(__name__)

router = APIRouter()

# ─────────────────────────────────────────────
# VIN Validation (NHTSA checksum)
# ─────────────────────────────────────────────

_VIN_TRANSLITERATION: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5,
    "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}
_VIN_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".heic"}
BLOCKED_EXTENSIONS = {".mp4", ".zip", ".exe", ".mov", ".avi", ".dmg", ".sh"}


def validate_vin(vin: str) -> tuple[bool, str]:
    """Return (is_valid, reason). Does NOT block packet generation — warning only."""
    if not vin:
        return False, "VIN is empty"
    v = vin.upper().strip()
    if len(v) != 17:
        return False, f"VIN must be 17 characters (got {len(v)})"
    invalid_chars = set(v) & {"I", "O", "Q"}
    if invalid_chars:
        return False, f"VIN contains invalid characters: {', '.join(sorted(invalid_chars))}"
    if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", v):
        return False, "VIN contains invalid characters"
    total = 0
    for i, ch in enumerate(v):
        val = int(ch) if ch.isdigit() else _VIN_TRANSLITERATION.get(ch, 0)
        total += val * _VIN_WEIGHTS[i]
    remainder = total % 11
    expected = "X" if remainder == 10 else str(remainder)
    if v[8] != expected:
        return False, f"VIN checksum may be invalid (expected '{expected}' at position 9, got '{v[8]}')"
    return True, "VIN format valid"


def _conf_label(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


# ─────────────────────────────────────────────
# Copy text builder
# ─────────────────────────────────────────────

def _build_copy_text(
    packet: dict,
    warnings: list[str],
    sources: list[dict],
    mock_mode: bool,
) -> str:
    def fv(key: str) -> str:
        field = packet.get(key, {})
        v = (field.get("value") or "").strip()
        return v if v else "MISSING"

    mock_label = "\n⚠ MOCK_EXTRACTION_ONLY — No real AI extraction performed.\n" if mock_mode else ""
    warning_lines = "\n".join(f"  ⚠ {w}" for w in warnings) if warnings else "  (none)"
    source_lines = (
        "\n".join(f"  {s['file']} → {s['fields']}" for s in sources)
        if sources
        else "  (none)"
    )

    return f"""{mock_label}ADD-CAR PACKET

Customer:
  Name: {fv('customer_name')}
  Phone: {fv('phone')}
  Garaging ZIP: {fv('garaging_zip')}

Vehicle:
  VIN: {fv('vin')}
  Year: {fv('year')}
  Make: {fv('make')}
  Model: {fv('model')}

Driver:
  Primary Driver: {fv('primary_driver')}

Dates:
  Effective Date: {fv('effective_date')}

Finance:
  Lienholder: {fv('finance_or_lienholder')}

Warnings:
{warning_lines}

Sources:
{source_lines}""".strip()


# ─────────────────────────────────────────────
# Mock mode
# ─────────────────────────────────────────────

def _make_mock_packet(
    customer_name: str,
    phone: str,
    garaging_zip: str,
    file_names: list[str],
) -> tuple[dict, list[str], list[dict]]:
    """Build a clearly labeled mock packet — never claims real extraction."""

    def intake_field(value: str) -> dict:
        return {
            "value": value,
            "confidence": 1.0,
            "confidence_label": "high",
            "source_file": "intake_form",
            "is_mock": False,
        }

    def mock_field() -> dict:
        return {
            "value": "",
            "confidence": 0.0,
            "confidence_label": "low",
            "source_file": "MOCK_EXTRACTION_ONLY",
            "is_mock": True,
        }

    packet = {
        "customer_name": intake_field(customer_name),
        "phone": intake_field(phone),
        "garaging_zip": intake_field(garaging_zip),
        "vin": mock_field(),
        "year": mock_field(),
        "make": mock_field(),
        "model": mock_field(),
        "primary_driver": mock_field(),
        "effective_date": mock_field(),
        "finance_or_lienholder": mock_field(),
    }

    warnings = [
        "MOCK_EXTRACTION_ONLY — Set GEMINI_API_KEY or OPENAI_API_KEY to enable real AI extraction.",
        "Vehicle fields cannot be populated without an extraction API key.",
    ]
    if not file_names:
        warnings.append("No files were uploaded.")

    sources = [{"file": "intake_form", "fields": "customer_name, phone, garaging_zip"}]
    for fn in file_names:
        sources.append({"file": fn, "fields": "not extracted (mock mode)"})

    return packet, warnings, sources


# ─────────────────────────────────────────────
# Real extraction using existing ocr_kill_test
# ─────────────────────────────────────────────

def _run_real_extraction(
    customer_name: str,
    phone: str,
    garaging_zip: str,
    file_paths: list[Path],
    file_names: list[str],
) -> tuple[dict, list[str], list[dict], str, list[str]]:
    """Run Gemini/OpenAI extraction via existing ocr_kill_test modules."""
    from services.fiqa_api.ocr_kill_test.extractor import get_extractor
    from services.fiqa_api.ocr_kill_test.packet_builder import process_case
    from services.fiqa_api.ocr_kill_test.schema import ExtractedField

    extractor = get_extractor("auto")
    model_used: str = getattr(extractor, "MODEL", "unknown")

    case_id = f"add-car-{uuid.uuid4().hex[:8]}"
    result = process_case(case_id=case_id, files=file_paths, extractor=extractor)

    def ef_to_dict(key: str) -> dict:
        ef: ExtractedField = result.extracted_fields.get(key, ExtractedField())
        return {
            "value": ef.value if ef.is_present() else "",
            "confidence": ef.confidence,
            "confidence_label": _conf_label(ef.confidence),
            "source_file": ef.source_file or "",
            "is_mock": False,
        }

    def intake_field(value: str) -> dict:
        return {
            "value": value,
            "confidence": 1.0,
            "confidence_label": "high",
            "source_file": "intake_form",
            "is_mock": False,
        }

    # Split make_model → make + model
    make_model_ef: ExtractedField = result.extracted_fields.get("make_model", ExtractedField())
    make_model_val = make_model_ef.value or ""
    mm_parts = make_model_val.split(" ", 1)
    make_val = mm_parts[0] if mm_parts else ""
    model_val = mm_parts[1] if len(mm_parts) > 1 else ""

    packet: dict = {
        "customer_name": intake_field(customer_name),
        "phone": intake_field(phone),
        "garaging_zip": intake_field(garaging_zip),
        "vin": ef_to_dict("vin"),
        "year": ef_to_dict("year"),
        "make": {
            "value": make_val,
            "confidence": make_model_ef.confidence,
            "confidence_label": _conf_label(make_model_ef.confidence),
            "source_file": make_model_ef.source_file or "",
            "is_mock": False,
        },
        "model": {
            "value": model_val,
            "confidence": make_model_ef.confidence,
            "confidence_label": _conf_label(make_model_ef.confidence),
            "source_file": make_model_ef.source_file or "",
            "is_mock": False,
        },
        "primary_driver": ef_to_dict("primary_driver"),
        "effective_date": ef_to_dict("delivery_or_effective_date"),
        "finance_or_lienholder": {
            "value": "",
            "confidence": 0.0,
            "confidence_label": "low",
            "source_file": "",
            "is_mock": False,
        },
    }

    confirmation_notices: list[str] = []

    # Primary driver default — if not found in docs but customer_name is known,
    # populate from customer_name with needs_confirmation=True (soft confirm, not hard missing).
    if not packet["primary_driver"]["value"] and customer_name:
        packet["primary_driver"] = {
            "value": customer_name,
            "confidence": 1.0,
            "confidence_label": "high",
            "source_file": "default_from_customer_name",
            "is_mock": False,
            "needs_confirmation": True,
        }
        confirmation_notices.append(
            "Primary driver defaulted to customer name — please confirm. "
            "/ 主要驾驶人已默认使用客户姓名，请确认。"
        )

    warnings: list[str] = []

    # VIN format validation (warn only — never block)
    vin_value = packet["vin"]["value"]
    if vin_value:
        vin_valid, vin_reason = validate_vin(vin_value)
        if not vin_valid:
            warnings.append(f"VIN format may be invalid — verify manually ({vin_reason})")
    else:
        warnings.append("VIN not found in uploaded documents — verify manually")

    # Multiple VINs / second vehicle
    vin_conflicts = [c for c in result.conflicts if c.field == "vin"]
    if vin_conflicts or result.second_vehicle_detected:
        warnings.append(
            "Multiple VINs detected. Please verify which one is the new vehicle."
        )

    # Other field conflicts
    for c in result.conflicts:
        if c.field != "vin":
            warnings.append(
                f"Conflicting {c.field} values detected across documents — verify manually"
            )

    # Missing critical fields
    missing = [f for f in ["vin", "year", "make", "model"] if not packet[f]["value"]]
    if missing:
        warnings.append(f"Fields not found in documents: {', '.join(missing)}")

    # Surface extraction errors (e.g. API quota exceeded)
    if result.error:
        warnings.append(f"Extraction error for one or more files: {result.error[:120]}")

    # Build source map (file → extracted fields); skip synthetic sources.
    _synthetic_sources = {"intake_form", "default_from_customer_name"}
    source_map: dict[str, list[str]] = {}
    for key, field_data in packet.items():
        src = field_data.get("source_file", "")
        if src and src not in _synthetic_sources and field_data.get("value"):
            source_map.setdefault(src, []).append(key)

    sources: list[dict] = [{"file": "intake_form", "fields": "customer_name, phone, garaging_zip"}]
    for src, flds in source_map.items():
        sources.append({"file": src, "fields": ", ".join(flds)})

    return packet, warnings, sources, model_used, confirmation_notices


# ─────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────

@router.post("/api/intake/add-car/extract")
async def extract_add_car(
    files: List[UploadFile] = File(default=[]),
    customer_name: str = Form(...),
    phone: str = Form(...),
    garaging_zip: str = Form(...),
) -> dict:
    """
    Extract Trusted Packet fields from uploaded customer documents.

    Falls back to MOCK_EXTRACTION_ONLY if no AI API key is configured.
    Never claims real extraction when running in mock mode.
    """
    # Validate required form fields
    customer_name = customer_name.strip()
    phone = phone.strip()
    garaging_zip = garaging_zip.strip()

    if not customer_name:
        raise HTTPException(status_code=422, detail="customer_name is required")
    if not phone:
        raise HTTPException(status_code=422, detail="phone is required")
    if not garaging_zip:
        raise HTTPException(status_code=422, detail="garaging_zip is required")

    # Validate file types and count
    if len(files) > 10:
        raise HTTPException(status_code=422, detail="Maximum 10 files allowed per request.")

    file_names: list[str] = []
    for f in files:
        fname = (f.filename or "unknown").strip()
        ext = Path(fname).suffix.lower()
        if ext in BLOCKED_EXTENSIONS:
            raise HTTPException(
                status_code=422,
                detail=f"File type not allowed: {fname}. Accepted: PDF, JPG, PNG, HEIC.",
            )
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=422,
                detail=f"File type not supported: {fname}. Accepted: PDF, JPG, PNG, HEIC.",
            )
        file_names.append(fname)

    # Detect available extraction provider
    has_gemini = bool(
        os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    can_extract = (has_gemini or has_openai) and bool(files)

    if not can_extract:
        # Mock mode — no real extraction
        packet, warnings, sources = _make_mock_packet(
            customer_name=customer_name,
            phone=phone,
            garaging_zip=garaging_zip,
            file_names=file_names,
        )
        copy_text = _build_copy_text(
            packet=packet,
            warnings=warnings,
            sources=sources,
            mock_mode=True,
        )
        return {
            "packet": packet,
            "warnings": warnings,
            "sources": sources,
            "copy_text": copy_text,
            "mock_mode": True,
            "model_used": "MOCK_EXTRACTION_ONLY",
            "confirmation_notices": [],
        }

    # Real extraction — save to temp dir and run
    with tempfile.TemporaryDirectory() as tmpdir:
        file_paths: list[Path] = []
        for upload in files:
            fname = upload.filename or f"upload_{len(file_paths)}"
            dest = Path(tmpdir) / fname
            content = await upload.read()
            dest.write_bytes(content)
            file_paths.append(dest)

        try:
            packet, warnings, sources, model_used, confirmation_notices = _run_real_extraction(
                customer_name=customer_name,
                phone=phone,
                garaging_zip=garaging_zip,
                file_paths=file_paths,
                file_names=file_names,
            )
        except Exception as exc:
            logger.exception("Extraction failed — falling back to mock mode")
            packet, warnings, sources = _make_mock_packet(
                customer_name=customer_name,
                phone=phone,
                garaging_zip=garaging_zip,
                file_names=file_names,
            )
            warnings.insert(
                0, f"Extraction error — falling back to mock mode: {str(exc)[:120]}"
            )
            copy_text = _build_copy_text(
                packet=packet,
                warnings=warnings,
                sources=sources,
                mock_mode=True,
            )
            return {
                "packet": packet,
                "warnings": warnings,
                "sources": sources,
                "copy_text": copy_text,
                "mock_mode": True,
                "model_used": "MOCK_EXTRACTION_ONLY",
                "confirmation_notices": [],
            }

    copy_text = _build_copy_text(
        packet=packet,
        warnings=warnings,
        sources=sources,
        mock_mode=False,
    )

    return {
        "packet": packet,
        "warnings": warnings,
        "sources": sources,
        "copy_text": copy_text,
        "mock_mode": False,
        "model_used": model_used,
        "confirmation_notices": confirmation_notices,
    }
