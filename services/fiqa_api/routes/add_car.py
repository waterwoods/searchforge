"""
P16 Trust Layer — Add-Car Trusted Packet extraction endpoint.

POST /api/intake/add-car/extract
    Accepts: multipart/form-data
        files: list[UploadFile]   (PDF, JPG, PNG, HEIC — max 10)
        customer_name: str
        phone: str
        garaging_zip: str
        request_type: add_vehicle | replace_vehicle | policy_review
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

_EXTRACTION_FAILED_MESSAGE = (
    "We couldn't read these documents. Please try uploading clearer vehicle documents "
    "or contact your broker."
)
_EXTRACTION_FAILED_MESSAGE_ZH = (
    "系统未能读取这些文件。请重新上传更清晰的车辆资料，或联系您的保险经纪人。"
)


def _allow_mock_extraction() -> bool:
    """Mock extraction is local-dev only — never in production / QA Cloud Run."""
    from services.fiqa_api.db.service_record_settings import is_production_mode

    return not is_production_mode()


def _raise_extraction_failed(reason: str = "") -> None:
    detail: dict[str, str | bool] = {
        "extraction_failed": True,
        "message": _EXTRACTION_FAILED_MESSAGE,
        "message_zh": _EXTRACTION_FAILED_MESSAGE_ZH,
    }
    if reason:
        detail["reason"] = reason[:200]
    raise HTTPException(status_code=422, detail=detail)

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
# Primary driver default rule (shared — runs for all extraction paths)
# ─────────────────────────────────────────────

def _apply_primary_driver_default(
    packet: dict,
    customer_name: str,
    confirmation_notices: list[str],
) -> None:
    """
    Business rule: if primary_driver is absent after extraction (real or mock)
    but customer_name is present, default primary_driver to customer_name with
    source_file="default_from_customer_name" and needs_confirmation=True.
    Mutates packet and confirmation_notices in place.
    """
    pd = packet.get("primary_driver", {})
    if not (pd.get("value") or "").strip() and customer_name:
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


# ─────────────────────────────────────────────
# Copy text builder
# ─────────────────────────────────────────────

def _build_copy_text(
    packet: dict,
    warnings: list[str],
    sources: list[dict],
    mock_mode: bool,
    request_type: str = "add_vehicle",
    old_vehicle_vin: str = "",
    old_vehicle_plate: str = "",
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

    packet_header = "REPLACE-VEHICLE PACKET" if request_type == "replace_vehicle" else "ADD-CAR PACKET"

    old_vehicle_section = ""
    if request_type == "replace_vehicle":
        old_vin = old_vehicle_vin.strip() or "MISSING"
        old_plate = old_vehicle_plate.strip() or "MISSING"
        broker_note = ""
        if old_vin == "MISSING" and old_plate == "MISSING":
            broker_note = "\n  ⚠ Broker confirmation required — neither old VIN nor old plate provided"
        old_vehicle_section = (
            f"\nVehicle to Remove (Reference Only):\n"
            f"  Old VIN: {old_vin}\n"
            f"  Old Plate: {old_plate}{broker_note}"
        )

    return f"""{mock_label}{packet_header}

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
{old_vehicle_section}
Warnings:
{warning_lines}

Sources:
{source_lines}""".strip()


# ─────────────────────────────────────────────
# Document Relevance Gate (V1 — post-extraction assessment)
# ─────────────────────────────────────────────

def _assess_document_relevance(packet: dict, request_type: str = "add_vehicle") -> str | None:
    """
    Post-extraction relevance gate.

    Trigger: VIN, year, make, and model are ALL empty after extraction.
    Meaning: the uploaded documents did not produce usable vehicle information.

    Returns a bilingual customer-facing guidance string, or None if vehicle info was found.
    Does NOT use a second AI call — this is a pure packet inspection.
    Works for both PDF and image uploads (checks extracted field values, not file type).
    """
    vin = (packet.get("vin", {}).get("value") or "").strip()
    year = (packet.get("year", {}).get("value") or "").strip()
    make = (packet.get("make", {}).get("value") or "").strip()
    model = (packet.get("model", {}).get("value") or "").strip()

    if vin or year or make or model:
        return None

    if request_type == "replace_vehicle":
        return (
            "We couldn't find information for the new vehicle. "
            "Please upload the new vehicle purchase agreement, registration card, insurance card, or a clear VIN photo.\n"
            "我们没有找到新车信息。请上传新车购车合同、新车登记证、保险卡，或清晰的 VIN 照片。"
        )
    return (
        "We couldn't find vehicle information in your uploaded files. "
        "Please upload a purchase agreement, vehicle registration card, insurance card, or a clear VIN photo.\n"
        "我们在您上传的文件中没有找到车辆信息。请上传购车合同、车辆登记证、保险卡，或清晰的 VIN 照片。"
    )


# ─────────────────────────────────────────────
# Old vehicle reference (Replace Vehicle V1 Safe)
# ─────────────────────────────────────────────

def _add_old_vehicle_to_packet(
    packet: dict,
    request_type: str,
    old_vehicle_vin: str,
    old_vehicle_plate: str,
    warnings: list[str],
) -> None:
    """
    Add old vehicle reference fields to the packet for replace_vehicle requests.
    Never validates. Never blocks. Never downgraves readiness.
    Mutates packet and warnings in place.
    """
    if request_type != "replace_vehicle":
        return

    def intake_field(value: str) -> dict:
        return {
            "value": value.strip(),
            "confidence": 1.0,
            "confidence_label": "high",
            "source_file": "intake_form",
            "is_mock": False,
        }

    packet["old_vehicle_vin"] = intake_field(old_vehicle_vin)
    packet["old_vehicle_plate"] = intake_field(old_vehicle_plate)

    if not old_vehicle_vin.strip() and not old_vehicle_plate.strip():
        warnings.append(
            "Old vehicle not identified — broker must verify existing vehicle in AMS before processing removal."
        )


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
    _apply_primary_driver_default(packet, customer_name, confirmation_notices)

    warnings: list[str] = []

    # VIN format validation — warn only when VIN exists but format is invalid (broker-review conflict)
    vin_value = packet["vin"]["value"]
    if vin_value:
        vin_valid, vin_reason = validate_vin(vin_value)
        if not vin_valid:
            warnings.append(f"VIN format may be invalid — verify manually ({vin_reason})")
    # No warning when VIN is absent — that is handled by document_guidance (NEED_INFO path)

    # Multiple VINs / second vehicle — broker must resolve the conflict
    vin_conflicts = [c for c in result.conflicts if c.field == "vin"]
    if vin_conflicts or result.second_vehicle_detected:
        warnings.append(
            "Multiple VINs detected. Please verify which one is the new vehicle."
        )

    # Other field conflicts — broker-review ambiguity only (not missing-info)
    for c in result.conflicts:
        if c.field != "vin":
            warnings.append(
                f"Conflicting {c.field} values detected across documents — verify manually"
            )

    # Surface extraction errors (e.g. API quota exceeded, PDF render failure)
    if result.error:
        if (
            file_names
            and not any(_packet_field_value(packet, k) for k in ("vin", "year", "make", "model"))
            and not _allow_mock_extraction()
        ):
            _raise_extraction_failed(result.error)
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
# Case persistence (minimal — no Timeline / Inbox UI)
# ─────────────────────────────────────────────

def _packet_field_value(packet: dict, key: str) -> str:
    return str((packet.get(key) or {}).get("value") or "").strip()


def _build_add_car_triage_result(
    *,
    customer_name: str,
    phone: str,
    garaging_zip: str,
    packet: dict,
    warnings: list[str],
    request_type: str,
) -> dict:
    """Minimal triage_result for save_case() — broker-ready case record only."""
    vin_val = _packet_field_value(packet, "vin")
    year_val = _packet_field_value(packet, "year")
    make_val = _packet_field_value(packet, "make")
    model_val = _packet_field_value(packet, "model")

    missing: list[str] = []
    if not vin_val:
        missing.append("vin")
    if not year_val:
        missing.append("year")
    if not make_val or not model_val:
        missing.append("make_model")
    if not garaging_zip:
        missing.append("zip")

    collected = [f for f in ("vin", "year", "make_model", "zip") if f not in missing]
    has_conflict = any("Multiple VINs" in w for w in warnings)
    vehicle_summary = " ".join(filter(None, [year_val, make_val, model_val])).strip() or None

    if missing:
        broker_next_step = f"Packet received — verify missing: {', '.join(missing)}."
        quote_ready_status = "need_more"
        handoff_ready = False
        case_status = "waiting_client"
    elif has_conflict:
        broker_next_step = "Packet ready — verify VIN/conflicts before quoting."
        quote_ready_status = "almost_ready"
        handoff_ready = True
        case_status = "reviewing"
    else:
        broker_next_step = "Packet ready — all required fields extracted."
        quote_ready_status = "quote_ready"
        handoff_ready = True
        case_status = "reviewing"

    issue = "replace_vehicle_quote" if request_type == "replace_vehicle" else "add_car_quote"
    return {
        "issue_category": issue,
        "urgency": "medium",
        "manual_followup_needed": bool(missing or has_conflict),
        "broker_next_step": broker_next_step,
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": handoff_ready,
        "lifecycle_status": "handed_off",
        "service_type": "add_car",
        "extracted_contact_name": customer_name,
        "extracted_contact_phone": phone,
        "quote_ready_status": quote_ready_status,
        "collected_fields": collected,
        "still_needed_fields": missing,
        "primary_vehicle_summary": vehicle_summary,
        "vehicle_key": vin_val.upper() if vin_val else None,
        "additional_vehicle_mentioned": has_conflict or None,
    }


def _persist_add_car_case(
    *,
    customer_name: str,
    phone: str,
    garaging_zip: str,
    packet: dict,
    warnings: list[str],
    file_names: list[str],
    request_type: str,
    copy_text: str = "",
    sources: list[dict] | None = None,
) -> str | None:
    """Persist add-car case via resolver — CREATE or ATTACH to Active Case."""
    try:
        from services.fiqa_api.inbox_triage.active_case_resolver import (
            ResolverOutcome,
            resolve_active_case_for_evidence,
        )
        from services.fiqa_api.inbox_triage.case_store import (
            append_evidence_event_only,
            attach_add_car_evidence,
            save_case,
        )
        from services.fiqa_api.inbox_triage.case_truth_repository import list_cases_for_phone_lookup
        from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
        from services.fiqa_api.p16.packet_persist import (
            build_p16_broker_packet_blob,
            build_portal_copy_text_add_car,
            map_add_car_readiness,
        )

        triage_result = _build_add_car_triage_result(
            customer_name=customer_name,
            phone=phone,
            garaging_zip=garaging_zip,
            packet=packet,
            warnings=warnings,
            request_type=request_type,
        )
        missing = triage_result.get("still_needed_fields") or []
        has_conflict = any("Multiple VINs" in w for w in warnings)
        case_status = "waiting_client" if missing else "reviewing"
        readiness = map_add_car_readiness(
            still_needed=missing,
            warnings=warnings,
            quote_ready_status=str(triage_result.get("quote_ready_status") or ""),
        )
        portal_copy = build_portal_copy_text_add_car(
            packet=packet,
            warnings=warnings,
            request_type=request_type,
            broker_next_step=str(triage_result.get("broker_next_step") or ""),
        )
        p16_blob = build_p16_broker_packet_blob(
            request_type=request_type,
            readiness_status=readiness,
            packet=packet,
            copy_text=copy_text,
            portal_copy_text=portal_copy,
            sources=sources or [],
            warnings=warnings,
        )
        triage_result["p16_broker_packet"] = p16_blob

        upload_label = ", ".join(file_names) if file_names else "intake only"
        source_text = f"[客户] P16 Add-Car upload: {upload_label}"
        evidence_filename = file_names[0] if file_names else upload_label
        new_vin = _packet_field_value(packet, "vin") or None

        decision = resolve_active_case_for_evidence(
            phone=phone,
            intent=request_type,
            new_vin=new_vin,
            cases=list_cases_for_phone_lookup(phone),
        )

        if decision.outcome == ResolverOutcome.CREATE:
            saved = save_case(
                source_text=source_text,
                triage_result=triage_result,
                status=case_status,
                service_lane=SERVICE_LANE_ADD_CAR,
            )
            case_id = str(saved.get("case_id") or "").strip()
            if case_id:
                append_evidence_event_only(case_id, filename=evidence_filename)
        else:
            merge_review = decision.outcome == ResolverOutcome.BROKER_REVIEW
            if merge_review:
                attach_triage = dict(triage_result)
                attach_triage["quote_ready_status"] = "almost_ready"
            else:
                attach_triage = triage_result
            saved = attach_add_car_evidence(
                str(decision.case_id or ""),
                source_text=source_text,
                triage_result=attach_triage,
                p16_broker_packet=p16_blob,
                incoming_packet=packet,
                garaging_zip=garaging_zip,
                evidence_filename=evidence_filename,
                merge_review_required=merge_review,
                conflict_reason=str(decision.conflict_reason or ""),
            )
            case_id = str(decision.case_id or "").strip() if saved else None

        if case_id:
            logger.info(
                "add_car_case_persisted case_id=%s outcome=%s vin=%s conflict=%s missing=%s",
                case_id,
                decision.outcome.value,
                _packet_field_value(packet, "vin") or "(none)",
                has_conflict or decision.outcome == ResolverOutcome.BROKER_REVIEW,
                missing,
            )
        return case_id or None
    except Exception:
        logger.exception("Failed to persist add-car case — non-blocking")
        return None


# ─────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────

@router.post("/api/intake/add-car/extract")
async def extract_add_car(
    files: List[UploadFile] = File(default=[]),
    customer_name: str = Form(...),
    phone: str = Form(...),
    garaging_zip: str = Form(...),
    request_type: str = Form(default="add_vehicle"),
    old_vehicle_vin: str = Form(default=""),
    old_vehicle_plate: str = Form(default=""),
) -> dict:
    """
    Extract Trusted Packet fields from uploaded customer documents.

    Falls back to MOCK_EXTRACTION_ONLY if no AI API key is configured.
    Never claims real extraction when running in mock mode.

    request_type: "add_vehicle" (default), "replace_vehicle", or "policy_review"
    old_vehicle_vin: optional — old vehicle identifier for replace_vehicle
    old_vehicle_plate: optional — old vehicle plate for replace_vehicle
    """
    request_type_early = (request_type or "add_vehicle").strip() or "add_vehicle"
    if request_type_early == "policy_review":
        from services.fiqa_api.policy_review.handler import handle_policy_review_extract

        return await handle_policy_review_extract(
            files=files,
            customer_name=customer_name,
            phone=phone,
            garaging_zip=garaging_zip,
        )

    # Validate required form fields
    customer_name = customer_name.strip()
    phone = phone.strip()
    garaging_zip = garaging_zip.strip()
    request_type = request_type.strip() or "add_vehicle"
    old_vehicle_vin = old_vehicle_vin.strip()
    old_vehicle_plate = old_vehicle_plate.strip()

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
        if not _allow_mock_extraction():
            if not files:
                raise HTTPException(status_code=422, detail="At least one document is required.")
            _raise_extraction_failed("Extraction service unavailable")
        # Mock mode — local dev only; document_guidance is null (mock does not assess relevance)
        packet, warnings, sources = _make_mock_packet(
            customer_name=customer_name,
            phone=phone,
            garaging_zip=garaging_zip,
            file_names=file_names,
        )
        mock_confirmation_notices: list[str] = []
        _apply_primary_driver_default(packet, customer_name, mock_confirmation_notices)
        _add_old_vehicle_to_packet(packet, request_type, old_vehicle_vin, old_vehicle_plate, warnings)
        copy_text = _build_copy_text(
            packet=packet,
            warnings=warnings,
            sources=sources,
            mock_mode=True,
            request_type=request_type,
            old_vehicle_vin=old_vehicle_vin,
            old_vehicle_plate=old_vehicle_plate,
        )
        return {
            "packet": packet,
            "warnings": warnings,
            "sources": sources,
            "copy_text": copy_text,
            "mock_mode": True,
            "model_used": "MOCK_EXTRACTION_ONLY",
            "confirmation_notices": mock_confirmation_notices,
            "document_guidance": None,
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
            logger.exception("Extraction failed")
            if not _allow_mock_extraction():
                _raise_extraction_failed(str(exc))
            logger.warning("Extraction failed — falling back to mock mode (local dev only)")
            packet, warnings, sources = _make_mock_packet(
                customer_name=customer_name,
                phone=phone,
                garaging_zip=garaging_zip,
                file_names=file_names,
            )
            warnings.insert(
                0, f"Extraction error — falling back to mock mode: {str(exc)[:120]}"
            )
            fallback_notices: list[str] = []
            _apply_primary_driver_default(packet, customer_name, fallback_notices)
            _add_old_vehicle_to_packet(packet, request_type, old_vehicle_vin, old_vehicle_plate, warnings)
            copy_text = _build_copy_text(
                packet=packet,
                warnings=warnings,
                sources=sources,
                mock_mode=True,
                request_type=request_type,
                old_vehicle_vin=old_vehicle_vin,
                old_vehicle_plate=old_vehicle_plate,
            )
            return {
                "packet": packet,
                "warnings": warnings,
                "sources": sources,
                "copy_text": copy_text,
                "mock_mode": True,
                "model_used": "MOCK_EXTRACTION_ONLY",
                "confirmation_notices": fallback_notices,
                "document_guidance": None,
            }

    _add_old_vehicle_to_packet(packet, request_type, old_vehicle_vin, old_vehicle_plate, warnings)

    # Document Relevance Gate: assess after extraction, before building copy text
    document_guidance = _assess_document_relevance(packet, request_type)

    copy_text = _build_copy_text(
        packet=packet,
        warnings=warnings,
        sources=sources,
        mock_mode=False,
        request_type=request_type,
        old_vehicle_vin=old_vehicle_vin,
        old_vehicle_plate=old_vehicle_plate,
    )

    from services.fiqa_api.p16.packet_persist import build_portal_copy_text_add_car

    portal_copy_text = build_portal_copy_text_add_car(
        packet=packet,
        warnings=warnings,
        request_type=request_type,
    )

    case_id = _persist_add_car_case(
        customer_name=customer_name,
        phone=phone,
        garaging_zip=garaging_zip,
        packet=packet,
        warnings=warnings,
        file_names=file_names,
        request_type=request_type,
        copy_text=copy_text,
        sources=sources,
    )

    return {
        "packet": packet,
        "warnings": warnings,
        "sources": sources,
        "copy_text": copy_text,
        "portal_copy_text": portal_copy_text,
        "mock_mode": False,
        "model_used": model_used,
        "confirmation_notices": confirmation_notices,
        "document_guidance": document_guidance,
        "case_id": case_id,
    }
