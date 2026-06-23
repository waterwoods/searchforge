"""
Policy Review extract handler — called from add-car route when request_type=policy_review.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import List

from fastapi import File, Form, HTTPException, UploadFile

from services.fiqa_api.policy_review.extractor import run_policy_review_extraction
from services.fiqa_api.policy_review.packet import (
    build_copy_text,
    build_policy_review_packet,
    build_sources,
)
from services.fiqa_api.policy_review.readiness import (
    BROKER_NEXT_ACTION,
    build_chinese_follow_up,
    build_opportunity_signals,
    compute_readiness,
)

logger = logging.getLogger(__name__)

_EXTRACTION_FAILED_MESSAGE = (
    "We couldn't read these documents. Please try uploading clearer policy documents "
    "or contact your broker."
)
_EXTRACTION_FAILED_MESSAGE_ZH = (
    "系统未能读取这些保单文件。请重新上传更清晰的资料，或联系您的保险经纪人。"
)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".heic"}
BLOCKED_EXTENSIONS = {".mp4", ".zip", ".exe", ".mov", ".avi", ".dmg", ".sh"}


def _allow_mock_extraction() -> bool:
    from services.fiqa_api.db.service_record_settings import is_production_mode

    return not is_production_mode()


def _raise_extraction_failed(reason: str = "") -> None:
    detail: dict = {
        "extraction_failed": True,
        "message": _EXTRACTION_FAILED_MESSAGE,
        "message_zh": _EXTRACTION_FAILED_MESSAGE_ZH,
    }
    if reason:
        detail["reason"] = reason[:200]
    raise HTTPException(status_code=422, detail=detail)


def _mock_merged_from_filenames(file_names: list[str]) -> dict:
    """Local-dev mock: filename hints for demo scenarios."""
    names_lower = " ".join(file_names).lower()
    is_dec = any(k in names_lower for k in ("declaration", "dec_page", "decpage", "renewal"))
    is_card_only = any(k in names_lower for k in ("insurance_card", "ins_card", "card_only")) and not is_dec

    if is_dec:
        return {
            "fields": {
                "current_carrier": {"value": "GEICO", "confidence": 0.95, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "policy_number": {"value": "CA-1234567", "confidence": 0.9, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "policy_term_start": {"value": "2025-06-01", "confidence": 0.9, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "policy_term_end": {"value": "2025-12-01", "confidence": 0.9, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "premium_amount": {"value": "1842.00", "confidence": 0.92, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "premium_period": {"value": "6 months", "confidence": 0.9, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "bodily_injury": {"value": "100/300", "confidence": 0.88, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "property_damage": {"value": "100", "confidence": 0.88, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "uninsured_motorist": {"value": "100/300", "confidence": 0.85, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "comprehensive_deductible": {"value": "500", "confidence": 0.85, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
                "collision_deductible": {"value": "500", "confidence": 0.85, "confidence_label": "high", "source_file": file_names[0] if file_names else "mock"},
            },
            "vehicles": [{
                "year": "2022", "make": "Toyota", "model": "Camry", "vin": "4T1BF1FK5CU123456",
                "vehicle_premium": "920.00", "source_file": file_names[0] if file_names else "mock",
            }],
            "drivers": [{
                "name": "Li Hua", "relationship": "Named Insured", "license_state": "CA",
                "visible_violation_or_accident": "", "source_file": file_names[0] if file_names else "mock",
            }],
            "document_types": ["declaration_page"],
            "warnings": ["MOCK_EXTRACTION_ONLY — Set GEMINI_API_KEY or OPENAI_API_KEY for real extraction."],
            "cross_sell_clues": [],
            "extraction_notes": [],
            "conflicts": [],
            "model_used": "MOCK_EXTRACTION_ONLY",
        }

    if is_card_only:
        return {
            "fields": {
                "current_carrier": {"value": "Progressive", "confidence": 0.8, "confidence_label": "medium", "source_file": file_names[0] if file_names else "mock"},
            },
            "vehicles": [{
                "year": "2020", "make": "Honda", "model": "Accord", "vin": "1HGCV1F34LA123456",
                "vehicle_premium": "", "source_file": file_names[0] if file_names else "mock",
            }],
            "drivers": [],
            "document_types": ["insurance_card"],
            "warnings": ["MOCK_EXTRACTION_ONLY — Insurance card only; declaration page not detected."],
            "cross_sell_clues": [],
            "extraction_notes": ["Insurance card alone usually lacks full coverage limits and total premium."],
            "conflicts": [],
            "model_used": "MOCK_EXTRACTION_ONLY",
        }

    return {
        "fields": {},
        "vehicles": [],
        "drivers": [],
        "document_types": ["unknown"],
        "warnings": [
            "MOCK_EXTRACTION_ONLY — Set GEMINI_API_KEY or OPENAI_API_KEY to enable real AI extraction.",
            "Rename files with 'declaration' or 'insurance_card' for demo scenarios.",
        ],
        "cross_sell_clues": [],
        "extraction_notes": [],
        "conflicts": [],
        "model_used": "MOCK_EXTRACTION_ONLY",
    }


def _build_triage_result(
    *,
    customer_name: str,
    phone: str,
    readiness: str,
    merged: dict,
) -> dict:
    fields = merged.get("fields") or {}
    carrier = str((fields.get("current_carrier") or {}).get("value") or "").strip()
    premium = str((fields.get("premium_amount") or {}).get("value") or "").strip()
    vehicles = merged.get("vehicles") or []

    missing: list[str] = []
    if not carrier:
        missing.append("carrier")
    if not premium:
        missing.append("premium")
    if not vehicles:
        missing.append("vehicles")

    if readiness == "ready":
        broker_next = "Policy snapshot ready — broker can manually re-shop in carrier portal."
        quote_ready_status = "quote_ready"
        handoff_ready = True
        case_status = "reviewing"
    elif readiness == "broker_review":
        broker_next = "Policy snapshot has conflicts — verify before re-shopping."
        quote_ready_status = "almost_ready"
        handoff_ready = True
        case_status = "reviewing"
    else:
        broker_next = f"Policy review — missing: {', '.join(missing) or 'declaration page / premium'}."
        quote_ready_status = "need_more"
        handoff_ready = False
        case_status = "waiting_client"

    vehicle_summary = None
    if vehicles:
        v0 = vehicles[0]
        vehicle_summary = " ".join(filter(None, [v0.get("year"), v0.get("make"), v0.get("model")])).strip() or None

    return {
        "issue_category": "premium_review",
        "urgency": "medium",
        "manual_followup_needed": readiness != "ready",
        "broker_next_step": broker_next,
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": handoff_ready,
        "lifecycle_status": "handed_off",
        "service_type": "policy_review",
        "extracted_contact_name": customer_name,
        "extracted_contact_phone": phone,
        "quote_ready_status": quote_ready_status,
        "collected_fields": [f for f in ("carrier", "premium", "vehicles") if f not in missing],
        "still_needed_fields": missing,
        "primary_vehicle_summary": vehicle_summary,
        "vehicle_key": (vehicles[0].get("vin") if vehicles else None),
    }


def _persist_policy_review_case(
    *,
    customer_name: str,
    phone: str,
    readiness: str,
    merged: dict,
    file_names: list[str],
    packet: dict,
    vehicles: list[dict],
    drivers: list[dict],
    copy_text: str,
    sources: list[dict],
    warnings: list[str],
    opportunity_signals: list[dict],
    broker_next_action: dict[str, str],
    follow_up_message_zh: str,
    document_types_detected: list[str],
    mock_mode: bool = False,
) -> str | None:
    try:
        from services.fiqa_api.inbox_triage.case_store import save_case
        from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_POLICY_REVIEW
        from services.fiqa_api.p16.packet_persist import (
            build_p16_broker_packet_blob,
            build_portal_copy_text_policy_review,
            map_policy_review_readiness,
        )

        triage_result = _build_triage_result(
            customer_name=customer_name,
            phone=phone,
            readiness=readiness,
            merged=merged,
        )
        office_readiness = map_policy_review_readiness(readiness)
        portal_copy = build_portal_copy_text_policy_review(
            packet=packet,
            vehicles=vehicles,
            drivers=drivers,
            broker_next_action=broker_next_action,
        )
        triage_result["p16_broker_packet"] = build_p16_broker_packet_blob(
            request_type="policy_review",
            readiness_status=office_readiness,
            packet=packet,
            vehicles=vehicles,
            drivers=drivers,
            copy_text=copy_text,
            portal_copy_text=portal_copy,
            opportunity_signals=opportunity_signals,
            broker_next_action=broker_next_action,
            follow_up_message_zh=follow_up_message_zh,
            sources=sources,
            warnings=warnings,
            document_types_detected=document_types_detected,
            mock_mode=mock_mode,
        )
        case_status = "waiting_client" if readiness == "needs_info" else "reviewing"
        upload_label = ", ".join(file_names) if file_names else "intake only"
        saved = save_case(
            source_text=f"[客户] P16 Policy Review upload: {upload_label}",
            triage_result=triage_result,
            status=case_status,
            service_lane=SERVICE_LANE_POLICY_REVIEW,
        )
        return str(saved.get("case_id") or "").strip() or None
    except Exception:
        logger.exception("Failed to persist policy_review case — non-blocking")
        return None


def _assemble_response(
    *,
    customer_name: str,
    phone: str,
    garaging_zip: str,
    merged: dict,
    file_names: list[str],
    mock_mode: bool,
) -> dict:
    readiness, reasons = compute_readiness(
        fields=merged.get("fields") or {},
        vehicles=merged.get("vehicles") or [],
        document_types=merged.get("document_types") or [],
        warnings=merged.get("warnings") or [],
        conflicts=merged.get("conflicts") or [],
        extraction_notes=merged.get("extraction_notes") or [],
    )
    opportunity_signals = build_opportunity_signals(
        readiness=readiness,
        fields=merged.get("fields") or {},
        vehicles=merged.get("vehicles") or [],
        drivers=merged.get("drivers") or [],
        warnings=merged.get("warnings") or [],
        cross_sell_clues=merged.get("cross_sell_clues") or [],
        extraction_notes=merged.get("extraction_notes") or [],
    )
    follow_up_zh = build_chinese_follow_up(readiness, reasons)
    broker_next = BROKER_NEXT_ACTION[readiness]

    built = build_policy_review_packet(
        customer_name=customer_name,
        phone=phone,
        garaging_zip=garaging_zip,
        merged=merged,
        is_mock=mock_mode,
    )
    packet = built["packet"]
    vehicles = built["vehicles"]
    drivers = built["drivers"]
    sources = build_sources(packet, vehicles, drivers, file_names)
    copy_text = build_copy_text(
        packet=packet,
        vehicles=vehicles,
        drivers=drivers,
        warnings=merged.get("warnings") or [],
        sources=sources,
        opportunity_signals=opportunity_signals,
        broker_next_action=broker_next,
        mock_mode=mock_mode,
    )

    document_guidance = None
    if readiness == "needs_info" and "declaration_page" in reasons:
        document_guidance = (
            "We couldn't find a declaration page or full policy snapshot in your uploads. "
            "Please upload your Declaration Page or Renewal Notice.\n"
            "未找到完整保单首页。请上传 Declaration Page 或续保通知。"
        )

    from services.fiqa_api.p16.packet_persist import build_portal_copy_text_policy_review

    portal_copy_text = build_portal_copy_text_policy_review(
        packet=packet,
        vehicles=vehicles,
        drivers=drivers,
        broker_next_action=broker_next,
    )

    case_id = None if mock_mode else _persist_policy_review_case(
        customer_name=customer_name,
        phone=phone,
        readiness=readiness,
        merged=merged,
        file_names=file_names,
        packet=packet,
        vehicles=vehicles,
        drivers=drivers,
        copy_text=copy_text,
        sources=sources,
        warnings=merged.get("warnings") or [],
        opportunity_signals=opportunity_signals,
        broker_next_action=broker_next,
        follow_up_message_zh=follow_up_zh,
        document_types_detected=built.get("document_types_detected") or [],
        mock_mode=mock_mode,
    )

    return {
        "packet": packet,
        "vehicles": vehicles,
        "drivers": drivers,
        "warnings": merged.get("warnings") or [],
        "sources": sources,
        "copy_text": copy_text,
        "portal_copy_text": portal_copy_text,
        "mock_mode": mock_mode,
        "model_used": merged.get("model_used") or ("MOCK_EXTRACTION_ONLY" if mock_mode else "unknown"),
        "confirmation_notices": [],
        "document_guidance": document_guidance,
        "readiness_status": readiness,
        "follow_up_message_zh": follow_up_zh,
        "opportunity_signals": opportunity_signals,
        "broker_next_action": broker_next,
        "document_types_detected": built.get("document_types_detected") or [],
        "case_id": case_id,
        "request_type": "policy_review",
    }


async def handle_policy_review_extract(
    files: List[UploadFile],
    customer_name: str,
    phone: str,
    garaging_zip: str,
) -> dict:
    customer_name = customer_name.strip()
    phone = phone.strip()
    garaging_zip = garaging_zip.strip()

    if not customer_name:
        raise HTTPException(status_code=422, detail="customer_name is required")
    if not phone:
        raise HTTPException(status_code=422, detail="phone is required")
    if not garaging_zip:
        raise HTTPException(status_code=422, detail="garaging_zip is required")
    if len(files) > 10:
        raise HTTPException(status_code=422, detail="Maximum 10 files allowed per request.")

    file_names: list[str] = []
    for f in files:
        fname = (f.filename or "unknown").strip()
        ext = Path(fname).suffix.lower()
        if ext in BLOCKED_EXTENSIONS:
            raise HTTPException(status_code=422, detail=f"File type not allowed: {fname}")
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail=f"File type not supported: {fname}")
        file_names.append(fname)

    import os

    has_gemini = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    can_extract = (has_gemini or has_openai) and bool(files)

    if not can_extract:
        if not _allow_mock_extraction():
            if not files:
                raise HTTPException(status_code=422, detail="At least one document is required.")
            _raise_extraction_failed("Extraction service unavailable")
        merged = _mock_merged_from_filenames(file_names)
        return _assemble_response(
            customer_name=customer_name,
            phone=phone,
            garaging_zip=garaging_zip,
            merged=merged,
            file_names=file_names,
            mock_mode=True,
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        file_paths: list[Path] = []
        for upload in files:
            fname = upload.filename or f"upload_{len(file_paths)}"
            dest = Path(tmpdir) / fname
            dest.write_bytes(await upload.read())
            file_paths.append(dest)

        try:
            merged = run_policy_review_extraction(file_paths, file_names)
        except Exception as exc:
            logger.exception("Policy review extraction failed")
            if not _allow_mock_extraction():
                _raise_extraction_failed(str(exc))
            merged = _mock_merged_from_filenames(file_names)
            merged["warnings"] = [f"Extraction error — mock fallback: {str(exc)[:120]}"] + (merged.get("warnings") or [])

    if merged.get("warnings") and not any(
        (merged.get("fields") or {}).get(k, {}).get("value")
        for k in ("current_carrier", "premium_amount")
    ) and not merged.get("vehicles") and not _allow_mock_extraction():
        _raise_extraction_failed("; ".join(merged["warnings"][:2]))

    return _assemble_response(
        customer_name=customer_name,
        phone=phone,
        garaging_zip=garaging_zip,
        merged=merged,
        file_names=file_names,
        mock_mode=False,
    )
