"""H5 single-slot guided upload handler (P19D-2)."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from services.fiqa_api.inbox_triage.case_store import append_h5_gcs_attachment_metadata
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
from services.fiqa_api.inbox_triage.h5_task_token import VerifiedH5TaskToken, external_userid_ref
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
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
        "task_label": "请拍车上的 VIN 标签",
        "instruction": (
            "请拍清楚车门边或挡风玻璃下方的 VIN 金属/贴纸标签（不是保险卡或行驶证）。"
            "为了避免资料放错，本步骤只需要 1 张照片。"
        ),
        "step_current": 1,
        "step_total": 4,
        "document_type": "vin_photo",
    },
}


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


def task_info_for_token(claims: VerifiedH5TaskToken) -> dict[str, Any]:
    """Public task metadata for H5 page — no secrets."""
    slot_meta = _SLOT_COPY.get(claims.slot, {})
    return {
        "lane": claims.lane,
        "slot": claims.slot,
        "title": slot_meta.get("title", "资料补充"),
        "task_label": slot_meta.get("task_label", claims.slot),
        "instruction": slot_meta.get("instruction", ""),
        "step_current": slot_meta.get("step_current", 1),
        "step_total": slot_meta.get("step_total", 4),
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
        # WeChat / iOS often send HEIC/JPEG as octet-stream — infer from name or default jpg.
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
    ext_uid = str(case.get("wecom_external_userid") or "").strip()
    if claims.user_ref and ext_uid:
        expected = external_userid_ref(ext_uid)
        if expected != claims.user_ref:
            raise ValueError("user_ref_mismatch")


def sanitize_h5_upload_response(
    *,
    attachment_id: str,
    slot: str,
    status: str = "uploaded",
) -> dict[str, Any]:
    """Broker/customer-safe response — no storage_uri, no external_userid."""
    return {
        "attachment_id": attachment_id,
        "slot_assignment": slot,
        "status": status,
        "next_step": "registration_deferred",
        "message_zh": "VIN 照片已收到。下一步：registration 上传将在后续版本开放。",
    }


def ingest_h5_single_slot_upload(
    claims: VerifiedH5TaskToken,
    *,
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

    ext = _validate_image_upload(content, content_type=content_type, filename=filename)
    upload_id = f"h5_{uuid4().hex[:12]}"
    received_at = datetime.now(timezone.utc)
    storage = _upload_h5_bytes_to_gcs(
        case_id=claims.case_id,
        slot=claims.slot,
        upload_id=upload_id,
        content=content,
        mime_type=content_type,
        ext=ext,
        upload_fn=upload_fn,
    )

    attachment_id = f"att_{uuid4().hex[:12]}"
    slot_meta = _SLOT_COPY.get(claims.slot, {})
    document_type = str(slot_meta.get("document_type") or claims.slot)
    att_meta: dict[str, Any] = {
        "attachment_id": attachment_id,
        "source": "h5_task",
        "msgtype": "image",
        "storage_uri": storage["storage_uri"],
        "mime_type": storage.get("mime_type"),
        "size_bytes": storage.get("size_bytes"),
        "filename": filename or f"{claims.slot}{ext}",
        "received_at": received_at.isoformat(),
        "bound_case_id": claims.case_id,
        "binding_confidence": "high",
        "document_type": document_type,
        "document_type_confidence": "user_selected_step",
        "slot_assignment": claims.slot,
        "intake_status": "promoted",
        "guardrail_status": "accepted",
        "eligible_for_ocr": True,
        "ocr_status": "not_started",
        "ocr_draft": None,
        "broker_confirmed": False,
        "task_token_nonce": claims.nonce,
        "h5_upload_id": upload_id,
    }

    updated = append_h5_gcs_attachment_metadata(claims.case_id, att_meta)
    if updated is None:
        raise ValueError("case_persist_failed")

    logger.info(
        "h5_task_upload_ok_v1 %s",
        {
            "case_id": claims.case_id,
            "slot": claims.slot,
            "attachment_id": attachment_id,
            "size_bytes": len(content),
        },
    )
    return sanitize_h5_upload_response(attachment_id=attachment_id, slot=claims.slot)
