"""H5 guided upload handler (P19D-2 single-slot / P19D-4A photo flow)."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from services.fiqa_api.inbox_triage.case_store import (
    append_h5_gcs_attachment_metadata,
    record_h5_photo_flow_skip,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
from services.fiqa_api.inbox_triage.h5_task_token import (
    ADD_VEHICLE_PHOTO_FLOW_SLOTS,
    CLAIM_EVIDENCE_PACK_FLOW_SLOTS,
    FLOW_ADD_VEHICLE_PHOTO,
    FLOW_CLAIM_EVIDENCE_PACK,
    VerifiedH5TaskToken,
    external_userid_ref,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.h5_photo_end_card import try_send_h5_photo_flow_end_card
from services.fiqa_api.wecom.media_storage import (
    infer_extension,
    wecom_media_gcs_bucket,
)

logger = logging.getLogger(__name__)

H5_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

_ALLOWED_IMAGE_MIMES = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/heic",
        "image/heif",
        "application/octet-stream",
    }
)

_SLOT_COPY: dict[str, dict[str, Any]] = {
    "vin_photo": {
        "title": "加车资料补充",
        "task_label": "请拍 VIN 照片",
        "instruction": "请拍清楚车门边或挡风玻璃下方的 VIN 标签。",
        "document_type": "vin_photo",
        "required": True,
    },
    "registration_photo": {
        "title": "加车资料补充",
        "task_label": "请拍行驶证 / 登记证",
        "instruction": "请拍清楚行驶证或登记证页面。",
        "document_type": "registration_photo",
        "required": True,
    },
    "insurance_card_photo": {
        "title": "加车资料补充",
        "task_label": "请拍保险卡（可跳过）",
        "instruction": "请拍清楚保险卡正面（可选步骤，可跳过）。",
        "document_type": "insurance_card_photo",
        "required": False,
    },
}

_FLOW_OPTIONAL_SLOTS = frozenset({"insurance_card_photo"})

CLAIM_EVIDENCE_SAFETY_COPY = "这只是资料收集，不代表 claim 已正式提交。"

CLAIM_ACCEPTED_MEDIA_TYPES: tuple[str, ...] = (
    "image/jpeg",
    "image/png",
    "image/heic",
    "image/heif",
)

OTHER_PARTY_SKIP_REASONS: tuple[dict[str, str], ...] = (
    {"key": "no_other_party", "label": "没有对方车辆 / 单方事故"},
    {"key": "not_available", "label": "当时无法拍摄"},
    {"key": "hit_and_run", "label": "对方逃逸"},
    {"key": "customer_not_safe_to_collect", "label": "当时不安全未能拍摄"},
)

_CLAIM_SLOT_COPY: dict[str, dict[str, Any]] = {
    "customer_damage_photo": {
        "title": "理赔资料 · 车损照片",
        "slot_title": "理赔资料 · 车损照片",
        "task_label": "自己车损照片",
        "slot_label": "自己车损照片",
        "instruction": "请拍摄您车辆的损伤部位（远景 + 近景更清晰）",
        "document_type": "customer_damage_photo",
        "required_level": "required",
        "required": True,
        "skippable": False,
        "max_files": 2,
    },
    "other_party_vehicle_photo": {
        "title": "理赔资料 · 对方车辆",
        "slot_title": "理赔资料 · 对方车辆 / 车牌",
        "task_label": "对方车辆 / 车牌照片",
        "slot_label": "对方车辆 / 车牌照片",
        "instruction": "请拍摄对方车辆或车牌。如无法拍摄，可跳过并选择原因。",
        "document_type": "other_party_vehicle_photo",
        "required_level": "soft_required",
        "required": True,
        "skippable": True,
        "skip_reasons": list(OTHER_PARTY_SKIP_REASONS),
        "max_files": 2,
    },
    "scene_photo": {
        "title": "理赔资料 · 现场照片",
        "slot_title": "理赔资料 · 现场照片",
        "task_label": "现场照片",
        "slot_label": "现场照片",
        "instruction": "可选：拍摄事故现场环境照片。",
        "document_type": "scene_photo",
        "required_level": "optional",
        "required": False,
        "skippable": True,
        "max_files": 2,
    },
}

_CLAIM_FLOW_SKIPPABLE_SLOTS = frozenset({"other_party_vehicle_photo", "scene_photo"})

RESTART_ADD_CAR_PHOTO_MARKERS: tuple[str, ...] = (
    "重新加车",
    "重新开始加车",
    "重新上传加车资料",
    "新加一辆车",
    "再加一辆车",
    "再加一台车",
    "换一辆车",
    "另加一辆车",
    "add another car",
    "new vehicle",
    "start over add vehicle",
    "restart add vehicle",
    "restart add car",
    "new add car",
)


def get_claim_evidence_slot_metadata(slot_key: str) -> dict[str, Any]:
    """Public Claim evidence slot metadata for H5 task API and tests."""
    slot_norm = (slot_key or "").strip().lower()
    meta = dict(_CLAIM_SLOT_COPY.get(slot_norm, {}))
    if not meta:
        raise ValueError(f"unsupported_claim_slot: {slot_norm}")
    slots = CLAIM_EVIDENCE_PACK_FLOW_SLOTS
    idx = slots.index(slot_norm) if slot_norm in slots else -1
    next_slot = slots[idx + 1] if 0 <= idx < len(slots) - 1 else None
    return {
        "slot_key": slot_norm,
        "slot_label": meta.get("slot_label", slot_norm),
        "slot_title": meta.get("slot_title", meta.get("title", "")),
        "title": meta.get("title", ""),
        "task_label": meta.get("task_label", slot_norm),
        "instruction": meta.get("instruction", ""),
        "required_level": meta.get("required_level", "required"),
        "skippable": bool(meta.get("skippable", False)),
        "skip_reasons": list(meta.get("skip_reasons") or []),
        "accepted_media_types": list(CLAIM_ACCEPTED_MEDIA_TYPES),
        "max_files": int(meta.get("max_files") or 1),
        "next_slot": next_slot,
        "safety_copy": CLAIM_EVIDENCE_SAFETY_COPY,
        "eligible_for_ocr": False,
    }


def _is_claim_evidence_flow(claims: VerifiedH5TaskToken) -> bool:
    return claims.lane == "claim" and claims.flow == FLOW_CLAIM_EVIDENCE_PACK


def _flow_slots_for_claims(claims: VerifiedH5TaskToken) -> tuple[str, ...]:
    if _is_claim_evidence_flow(claims):
        return CLAIM_EVIDENCE_PACK_FLOW_SLOTS
    return tuple(claims.slots or ADD_VEHICLE_PHOTO_FLOW_SLOTS)


def _slot_copy_for(claims: VerifiedH5TaskToken, slot: str) -> dict[str, Any]:
    if _is_claim_evidence_flow(claims):
        return _CLAIM_SLOT_COPY.get(slot, {})
    return _SLOT_COPY.get(slot, {})


def _flow_skippable_slots(claims: VerifiedH5TaskToken) -> frozenset[str]:
    if _is_claim_evidence_flow(claims):
        return _CLAIM_FLOW_SKIPPABLE_SLOTS
    return _FLOW_OPTIONAL_SLOTS


def is_explicit_add_car_restart(text: str) -> bool:
    """True when customer explicitly asks to start a fresh add-car photo flow."""
    lowered = (text or "").strip().lower()
    return any(m in lowered for m in RESTART_ADD_CAR_PHOTO_MARKERS)


def wants_restart_add_car_photo_flow(text: str) -> bool:
    """Alias for ``is_explicit_add_car_restart`` (P19D-4B compat)."""
    return is_explicit_add_car_restart(text)


def h5_photo_flow_is_complete(case: dict[str, Any]) -> bool:
    """True when all required H5 photo slots are uploaded or optionally skipped."""
    slots = ADD_VEHICLE_PHOTO_FLOW_SLOTS
    completed = _completed_h5_slots(case)
    skipped = _skipped_h5_slots(case)
    for slot in slots:
        if slot in completed:
            continue
        if slot in _FLOW_OPTIONAL_SLOTS and slot in skipped:
            continue
        return False
    return True


def build_h5_media_object_path(
    *,
    case_id: str,
    slot: str,
    upload_id: str,
    ext: str,
    received_at: datetime | None = None,
) -> str:
    """``h5/{case_id}/{slot}/{yyyy}/{mm}/{upload_id}.<ext>``"""
    ext_norm = ext if ext.startswith(".") else f".{ext}"
    ext_norm = re.sub(r"[^.\w]", "", ext_norm) or ".jpg"
    ts = received_at or datetime.now(timezone.utc)
    cid = (case_id or "unknown").strip() or "unknown"
    slot_norm = (slot or "unknown").strip() or "unknown"
    uid = (upload_id or "unknown").strip() or "unknown"
    return f"h5/{cid}/{slot_norm}/{ts.year:04d}/{ts.month:02d}/{uid}{ext_norm}"


def _completed_h5_slots(case: dict[str, Any]) -> set[str]:
    completed: set[str] = set()
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        if str(att.get("source") or "").strip().lower() != "h5_task":
            continue
        slot = str(att.get("slot_assignment") or "").strip().lower()
        if slot:
            completed.add(slot)
    return completed


def _skipped_h5_slots(case: dict[str, Any]) -> set[str]:
    state = case.get("h5_photo_flow_state") or {}
    if not isinstance(state, dict):
        return set()
    skipped = state.get("skipped_slots") or []
    return {str(s).strip().lower() for s in skipped if s}


def _slot_status(slot: str, *, completed: set[str], skipped: set[str]) -> str:
    if slot in completed:
        return "completed"
    if slot in skipped:
        return "skipped"
    return "pending"


def _resolve_flow_progress(
    claims: VerifiedH5TaskToken,
    case: dict[str, Any],
) -> dict[str, Any]:
    slots = _flow_slots_for_claims(claims)
    completed = _completed_h5_slots(case)
    skipped = _skipped_h5_slots(case)
    skippable = _flow_skippable_slots(claims)
    steps: list[dict[str, Any]] = []
    current_step: str | None = None
    step_index = 0

    for idx, slot in enumerate(slots, start=1):
        meta = _slot_copy_for(claims, slot)
        status = _slot_status(slot, completed=completed, skipped=skipped)
        step: dict[str, Any] = {
            "slot": slot,
            "label": meta.get("task_label", slot),
            "instruction": meta.get("instruction", ""),
            "required": bool(meta.get("required", True)),
            "status": status,
        }
        if _is_claim_evidence_flow(claims):
            step["required_level"] = meta.get("required_level", "required")
            step["skippable"] = bool(meta.get("skippable", slot in skippable))
        steps.append(step)
        if current_step is None and status == "pending":
            current_step = slot
            step_index = idx

    flow_complete = current_step is None
    return {
        "slots": slots,
        "steps": steps,
        "current_step": current_step,
        "step_index": step_index if not flow_complete else len(slots),
        "step_total": len(slots),
        "flow_complete": flow_complete,
        "completed": completed,
        "skipped": skipped,
    }


def _build_claim_flow_task_info(
    claims: VerifiedH5TaskToken,
    case: dict[str, Any],
    progress: dict[str, Any],
) -> dict[str, Any]:
    current = progress["current_step"]
    if progress["flow_complete"]:
        current = CLAIM_EVIDENCE_PACK_FLOW_SLOTS[-1]
    slot_meta = get_claim_evidence_slot_metadata(current or CLAIM_EVIDENCE_PACK_FLOW_SLOTS[0])
    accept = ", ".join(CLAIM_ACCEPTED_MEDIA_TYPES)
    return {
        "lane": claims.lane,
        "flow": claims.flow,
        "case_id": claims.case_id,
        "slot_key": slot_meta["slot_key"],
        "slot_label": slot_meta["slot_label"],
        "slot_title": slot_meta["slot_title"],
        "title": slot_meta["title"],
        "task_label": slot_meta["task_label"],
        "instruction": slot_meta["instruction"],
        "required_level": slot_meta["required_level"],
        "skippable": slot_meta["skippable"],
        "skip_reasons": slot_meta["skip_reasons"],
        "accepted_media_types": slot_meta["accepted_media_types"],
        "max_files": slot_meta["max_files"],
        "next_slot": None if progress["flow_complete"] else slot_meta.get("next_slot"),
        "safety_copy": CLAIM_EVIDENCE_SAFETY_COPY,
        "eligible_for_ocr": False,
        "max_images": slot_meta["max_files"],
        "accept": accept,
        "flow_complete": progress["flow_complete"],
        "current_step": progress["current_step"],
        "step_index": progress["step_index"],
        "step_total": progress["step_total"],
        "steps": progress["steps"],
        "slot": current,
    }


def task_info_for_token(claims: VerifiedH5TaskToken) -> dict[str, Any]:
    """Public task metadata for H5 page — no secrets."""
    case = get_case_for_read(claims.case_id)
    if case is None:
        raise ValueError("case_not_found")

    if claims.is_flow_token:
        progress = _resolve_flow_progress(claims, case)
        if _is_claim_evidence_flow(claims):
            return _build_claim_flow_task_info(claims, case, progress)
        current = progress["current_step"]
        current_meta = _SLOT_COPY.get(current or "", _SLOT_COPY["vin_photo"])
        if progress["flow_complete"]:
            current_meta = _SLOT_COPY["vin_photo"]
        return {
            "lane": claims.lane,
            "flow": claims.flow,
            "case_id": claims.case_id,
            "title": "加车资料补充",
            "max_images": 1,
            "accept": "image/jpeg,image/png,image/heic",
            "flow_complete": progress["flow_complete"],
            "current_step": progress["current_step"],
            "step_index": progress["step_index"],
            "step_total": progress["step_total"],
            "steps": progress["steps"],
            "task_label": current_meta.get("task_label", ""),
            "instruction": current_meta.get("instruction", ""),
            "slot": current,
        }

    slot_meta = _SLOT_COPY.get(claims.slot or "vin_photo", {})
    return {
        "lane": claims.lane,
        "slot": claims.slot,
        "title": slot_meta.get("title", "资料补充"),
        "task_label": slot_meta.get("task_label", claims.slot),
        "instruction": slot_meta.get("instruction", ""),
        "step_current": 1,
        "step_total": 1,
        "max_images": 1,
        "accept": "image/jpeg,image/png,image/heic",
    }


def _validate_image_upload(
    content: bytes,
    *,
    content_type: str | None,
    filename: str | None,
) -> str:
    if not content:
        raise ValueError("empty_file")
    if len(content) > H5_MAX_UPLOAD_BYTES:
        raise ValueError("file_too_large")
    mime = (content_type or "").split(";")[0].strip().lower()
    name = (filename or "").lower()
    if mime and mime not in _ALLOWED_IMAGE_MIMES and not mime.startswith("image/"):
        raise ValueError("not_an_image")
    if mime in _ALLOWED_IMAGE_MIMES or (mime.startswith("image/") and mime != "image/gif"):
        pass
    elif mime == "application/octet-stream":
        pass
    elif any(name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".heic", ".heif")):
        pass
    else:
        raise ValueError("unsupported_image_type")
    try:
        return infer_extension(mime_type=mime or None, filename=filename, msgtype="image")
    except ValueError:
        if name.endswith(".heic"):
            return ".heic"
        if name.endswith(".heif"):
            return ".heif"
        if mime == "application/octet-stream":
            return ".jpg"
        raise


def _upload_h5_bytes_to_gcs(
    *,
    case_id: str,
    slot: str,
    upload_id: str,
    content: bytes,
    mime_type: str | None,
    ext: str,
    upload_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from services.fiqa_api.wecom.media_storage import _gcs_upload_hook, _default_gcs_upload

    bkt = wecom_media_gcs_bucket()
    object_path = build_h5_media_object_path(
        case_id=case_id,
        slot=slot,
        upload_id=upload_id,
        ext=ext,
    )
    fn = upload_fn or _gcs_upload_hook or _default_gcs_upload
    storage_uri = fn(
        bucket=bkt,
        object_path=object_path,
        content=content,
        content_type=mime_type,
    )
    return {
        "storage_uri": storage_uri,
        "bucket": bkt,
        "object_path": object_path,
        "mime_type": mime_type,
        "size_bytes": len(content),
        "extension": ext,
    }


def _assert_case_eligible(case: dict[str, Any], claims: VerifiedH5TaskToken) -> None:
    cid = str(case.get("case_id") or "").strip()
    if cid != claims.case_id:
        raise ValueError("case_mismatch")
    lane = str(case.get("service_lane") or "").strip().lower()
    if claims.lane == "add_car" and lane not in ("add_car", SERVICE_LANE_ADD_CAR):
        raise ValueError("lane_mismatch")
    if claims.lane == "claim" and lane not in ("claim", SERVICE_LANE_CLAIM):
        raise ValueError("lane_mismatch")
    ext_uid = str(case.get("wecom_external_userid") or "").strip()
    if claims.user_ref and ext_uid:
        expected = external_userid_ref(ext_uid)
        if expected != claims.user_ref:
            raise ValueError("user_ref_mismatch")


def _assert_flow_slot_allowed(
    claims: VerifiedH5TaskToken,
    case: dict[str, Any],
    slot: str,
) -> None:
    slot_norm = (slot or "").strip().lower()
    allowed = _flow_slots_for_claims(claims)
    if slot_norm not in allowed:
        raise ValueError("slot_not_in_flow")
    progress = _resolve_flow_progress(claims, case)
    current = progress["current_step"]
    if progress["flow_complete"]:
        raise ValueError("flow_already_complete")
    if slot_norm != current:
        raise ValueError("wrong_slot_order")


def sanitize_h5_upload_response(
    *,
    attachment_id: str | None = None,
    slot: str,
    status: str = "uploaded",
    flow_complete: bool = False,
    next_slot: str | None = None,
    message_zh: str | None = None,
    end_card_result: dict[str, Any] | None = None,
    flow: str | None = None,
) -> dict[str, Any]:
    """Broker/customer-safe response — no storage_uri, no external_userid."""
    slot_copy = _CLAIM_SLOT_COPY if flow == FLOW_CLAIM_EVIDENCE_PACK else _SLOT_COPY
    if flow_complete:
        msg = message_zh or (
            "照片资料已收到。下一步请回微信补充：提车日期、停车 ZIP、联系电话。"
            if flow != FLOW_CLAIM_EVIDENCE_PACK
            else "理赔照片资料已收到。请返回微信，陈总会人工查看。"
        )
        body: dict[str, Any] = {
            "attachment_id": attachment_id,
            "slot_assignment": slot,
            "status": status,
            "flow_complete": True,
            "next_step": "return_wecom_for_text_fields",
            "message_zh": msg,
        }
        if end_card_result is not None:
            body["end_card_sent"] = bool(end_card_result.get("sent"))
            if not end_card_result.get("sent"):
                body["end_card_send_warning"] = (
                    "confirmation_message_pending"
                    if end_card_result.get("reason") == "send_failed"
                    else None
                )
        return body
    if next_slot:
        msg = message_zh or f"{slot_copy.get(slot, {}).get('task_label', slot)}已收到，请继续下一步。"
        return {
            "attachment_id": attachment_id,
            "slot_assignment": slot,
            "status": status,
            "flow_complete": False,
            "next_slot": next_slot,
            "next_step": next_slot,
            "message_zh": msg,
        }
    return {
        "attachment_id": attachment_id,
        "slot_assignment": slot,
        "status": status,
        "next_step": "registration_deferred",
        "message_zh": message_zh or "VIN 照片已收到。下一步：registration 上传将在后续版本开放。",
    }


def _complete_flow_response(
    *,
    attachment_id: str | None,
    slot: str,
    status: str,
    case_id: str,
    claims: VerifiedH5TaskToken,
) -> dict[str, Any]:
    if _is_claim_evidence_flow(claims):
        return sanitize_h5_upload_response(
            attachment_id=attachment_id,
            slot=slot,
            status=status,
            flow_complete=True,
            message_zh="理赔照片资料已收到。请返回微信，陈总会人工查看。",
            flow=FLOW_CLAIM_EVIDENCE_PACK,
        )
    end_card_result = try_send_h5_photo_flow_end_card(case_id)
    return sanitize_h5_upload_response(
        attachment_id=attachment_id,
        slot=slot,
        status=status,
        flow_complete=True,
        end_card_result=end_card_result,
    )


def skip_h5_flow_slot(claims: VerifiedH5TaskToken, *, slot: str) -> dict[str, Any]:
    """Skip optional / soft-required flow slot."""
    if not claims.is_flow_token:
        raise ValueError("skip_not_supported")
    slot_norm = (slot or "").strip().lower()
    skippable = _flow_skippable_slots(claims)
    if slot_norm not in skippable:
        raise ValueError("slot_not_skippable")

    case = get_case_for_read(claims.case_id)
    if case is None:
        raise ValueError("case_not_found")
    _assert_case_eligible(case, claims)
    _assert_flow_slot_allowed(claims, case, slot_norm)

    updated = record_h5_photo_flow_skip(
        claims.case_id,
        flow=str(claims.flow or FLOW_ADD_VEHICLE_PHOTO),
        slot=slot_norm,
    )
    if updated is None:
        raise ValueError("case_persist_failed")

    progress = _resolve_flow_progress(claims, updated)
    if progress["flow_complete"]:
        return _complete_flow_response(
            attachment_id=None,
            slot=slot_norm,
            status="skipped",
            case_id=claims.case_id,
            claims=claims,
        )
    skip_msg = "已跳过此步骤。请继续下一步。"
    if _is_claim_evidence_flow(claims):
        skip_msg = "已记录跳过原因。请继续下一步。"
    return sanitize_h5_upload_response(
        attachment_id=None,
        slot=slot_norm,
        status="skipped",
        flow_complete=False,
        next_slot=progress["current_step"],
        message_zh=skip_msg,
        flow=claims.flow,
    )


def ingest_h5_slot_upload(
    claims: VerifiedH5TaskToken,
    *,
    slot: str | None,
    content: bytes,
    content_type: str | None,
    filename: str | None,
    upload_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Validate token context, upload one image to GCS, append attachment metadata.
    Raises ValueError for client errors.
    """
    case = get_case_for_read(claims.case_id)
    if case is None:
        raise ValueError("case_not_found")
    _assert_case_eligible(case, claims)

    if claims.is_flow_token:
        if not slot:
            raise ValueError("slot_required")
        _assert_flow_slot_allowed(claims, case, slot)
        target_slot = slot.strip().lower()
    else:
        target_slot = (claims.slot or "").strip().lower()
        if slot and slot.strip().lower() != target_slot:
            raise ValueError("slot_mismatch")

    ext = _validate_image_upload(content, content_type=content_type, filename=filename)
    upload_id = f"h5_{uuid4().hex[:12]}"
    received_at = datetime.now(timezone.utc)
    storage = _upload_h5_bytes_to_gcs(
        case_id=claims.case_id,
        slot=target_slot,
        upload_id=upload_id,
        content=content,
        mime_type=content_type,
        ext=ext,
        upload_fn=upload_fn,
    )

    attachment_id = f"att_{uuid4().hex[:12]}"
    slot_meta = _slot_copy_for(claims, target_slot)
    document_type = str(slot_meta.get("document_type") or target_slot)
    eligible_for_ocr = not _is_claim_evidence_flow(claims)
    att_meta: dict[str, Any] = {
        "attachment_id": attachment_id,
        "source": "h5_task",
        "msgtype": "image",
        "storage_uri": storage["storage_uri"],
        "mime_type": storage.get("mime_type"),
        "size_bytes": storage.get("size_bytes"),
        "filename": filename or f"{target_slot}{ext}",
        "received_at": received_at.isoformat(),
        "bound_case_id": claims.case_id,
        "binding_confidence": "high",
        "document_type": document_type,
        "document_type_confidence": "user_selected_step",
        "slot_assignment": target_slot,
        "intake_status": "promoted",
        "guardrail_status": "accepted",
        "eligible_for_ocr": eligible_for_ocr,
        "ocr_status": "not_started",
        "ocr_draft": None,
        "broker_confirmed": False,
        "task_token_nonce": claims.nonce,
        "h5_upload_id": upload_id,
    }
    if claims.is_flow_token:
        att_meta["flow"] = claims.flow

    updated = append_h5_gcs_attachment_metadata(claims.case_id, att_meta)
    if updated is None:
        raise ValueError("case_persist_failed")

    logger.info(
        "h5_task_upload_ok %s",
        {
            "case_id": claims.case_id,
            "slot": target_slot,
            "attachment_id": attachment_id,
            "size_bytes": len(content),
            "flow": claims.flow,
        },
    )

    if claims.is_flow_token:
        progress = _resolve_flow_progress(claims, updated)
        if progress["flow_complete"]:
            return _complete_flow_response(
                attachment_id=attachment_id,
                slot=target_slot,
                status="uploaded",
                case_id=claims.case_id,
                claims=claims,
            )
        return sanitize_h5_upload_response(
            attachment_id=attachment_id,
            slot=target_slot,
            flow_complete=False,
            next_slot=progress["current_step"],
            flow=claims.flow,
        )

    return sanitize_h5_upload_response(attachment_id=attachment_id, slot=target_slot, flow=claims.flow)


# Backward-compatible alias for P19D-2 tests
ingest_h5_single_slot_upload = ingest_h5_slot_upload
