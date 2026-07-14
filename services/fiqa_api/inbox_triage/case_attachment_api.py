"""Workbench attachment API helpers (P19B) — sanitize metadata, GCS preview proxy."""

from __future__ import annotations

import contextvars
import logging
import re
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

_GCS_URI_RE = re.compile(r"^gs://([^/]+)/(.+)$")

# Tests inject mock GCS reader — never used in production unless set.
_gcs_download_hook: Callable[[str], tuple[bytes, str | None]] | None = None

# P19F-1 — per-request GCS download timing for preview perf logs (no URI logged).
_preview_gcs_ms: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "preview_gcs_ms", default=None
)


def set_gcs_download_hook_for_tests(
    hook: Callable[[str], tuple[bytes, str | None]] | None,
) -> None:
    global _gcs_download_hook
    _gcs_download_hook = hook


def parse_storage_uri(storage_uri: str) -> tuple[str, str] | None:
    """Return (bucket, object_path) for gs:// URIs."""
    m = _GCS_URI_RE.match((storage_uri or "").strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def find_case_attachment(case: dict[str, Any], attachment_id: str) -> dict[str, Any] | None:
    aid = (attachment_id or "").strip()
    if not aid:
        return None
    for att in case.get("case_attachments") or []:
        if isinstance(att, dict) and str(att.get("attachment_id") or "").strip() == aid:
            return att
    return None


def _preview_path(case_id: str, attachment_id: str) -> str:
    cid = (case_id or "").strip()
    aid = (attachment_id or "").strip()
    return f"/api/inbox/cases/{cid}/attachments/{aid}/preview"


def _attachment_preview_available(att: dict[str, Any]) -> bool:
    source = str(att.get("source") or "").strip().lower()
    if source in ("wecom", "h5_task"):
        return bool(parse_storage_uri(str(att.get("storage_uri") or "")))
    filename = att.get("filename")
    return bool(filename)


def _guardrail_defaults(att: dict[str, Any]) -> dict[str, Any]:
    """Legacy attachments without P19D-1 fields."""
    raw_intake = (att.get("intake_status") or "").strip().lower()
    if raw_intake == "unassigned":
        intake_status = "unassigned"
    elif raw_intake in ("promoted", "quarantined"):
        intake_status = raw_intake
    else:
        intake_status = "promoted"
    guardrail_status = att.get("guardrail_status") or (
        "accepted" if intake_status == "promoted" else "bulk_upload_paused"
    )
    eligible = att.get("eligible_for_ocr")
    if eligible is None:
        # Legacy attachments: not OCR-eligible until explicit P19D-1 guardrail promote.
        eligible = False
    return {
        "intake_status": intake_status,
        "guardrail_status": guardrail_status,
        "eligible_for_ocr": bool(eligible),
        "requires_customer_confirm": bool(att.get("requires_customer_confirm", False)),
        "quarantine_reason": att.get("quarantine_reason"),
        "slot_assignment": att.get("slot_assignment"),
        "bulk_sequence": att.get("bulk_sequence"),
    }


def sanitize_attachment_for_api(case_id: str, att: dict[str, Any]) -> dict[str, Any]:
    """
    Strip sensitive/internal fields; add broker-safe preview_url.
    Never exposes storage_uri, external_userid, media_id, or public GCS URL.
    """
    aid = str(att.get("attachment_id") or "").strip()
    source = str(att.get("source") or "").strip().lower() or "web"
    preview_available = _attachment_preview_available(att)
    guardrail = _guardrail_defaults(att)
    out: dict[str, Any] = {
        "attachment_id": aid,
        "source": source,
        "msgtype": att.get("msgtype"),
        "document_type": att.get("document_type") or att.get("type") or "unknown_document",
        "document_type_confidence": att.get("document_type_confidence") or "unknown",
        "mime_type": att.get("mime_type"),
        "size_bytes": att.get("size_bytes"),
        "received_at": att.get("received_at") or att.get("created_at"),
        "binding_confidence": att.get("binding_confidence") or "unknown",
        "ocr_status": att.get("ocr_status") or "not_started",
        "broker_confirmed": bool(att.get("broker_confirmed", False)),
        "intake_status": guardrail["intake_status"],
        "guardrail_status": guardrail["guardrail_status"],
        "eligible_for_ocr": guardrail["eligible_for_ocr"],
        "requires_customer_confirm": guardrail["requires_customer_confirm"],
        "quarantine_reason": guardrail["quarantine_reason"],
        "slot_assignment": guardrail["slot_assignment"],
        "bulk_sequence": guardrail["bulk_sequence"],
        "preview_available": preview_available,
        "storage_status": "stored" if preview_available or att.get("storage_uri") else "unknown",
        "evidence_category": att.get("evidence_category") or att.get("slot_assignment"),
        "evidence_status": att.get("evidence_status") or "confirmed",
        "submission_phase": att.get("submission_phase") or "pre_submit",
        "created_by": att.get("created_by") or "customer",
        "created_by_channel": att.get("created_by_channel") or source,
        "replaces_attachment_id": att.get("replaces_attachment_id"),
        "replaced_by_attachment_id": att.get("replaced_by_attachment_id"),
        "customer_note": att.get("customer_note"),
    }
    if att.get("filename"):
        out["filename"] = att["filename"]
    if att.get("type") and not att.get("document_type"):
        out["legacy_type"] = att["type"]
    if preview_available and aid:
        out["preview_url"] = _preview_path(case_id, aid)
    return out


def sanitize_case_attachments_for_api(case_id: str, case: dict[str, Any]) -> list[dict[str, Any]]:
    raw = case.get("case_attachments")
    if not isinstance(raw, list):
        return []
    return [sanitize_attachment_for_api(case_id, att) for att in raw if isinstance(att, dict)]


def _sanitize_customer_identity_for_api(identity: Any) -> dict[str, Any] | None:
    if not isinstance(identity, dict):
        return None
    safe = dict(identity)
    safe.pop("wecom_external_userid", None)
    return safe


def sanitize_case_for_workbench_api(case: dict[str, Any]) -> dict[str, Any]:
    """Return case dict safe for workbench API responses."""
    row = dict(case)
    cid = str(case.get("case_id") or "").strip()
    row["case_attachments"] = sanitize_case_attachments_for_api(cid, case)
    ext = row.get("wecom_external_userid")
    if isinstance(ext, str) and ext.strip():
        # Mask — never send full external_userid to frontend.
        row["wecom_external_userid"] = None
    extra = row.get("extra")
    if isinstance(extra, dict):
        extra_copy = dict(extra)
        identity = _sanitize_customer_identity_for_api(extra_copy.get("customer_identity"))
        if identity is not None:
            extra_copy["customer_identity"] = identity
        row["extra"] = extra_copy
    return row


def consume_preview_gcs_ms() -> float | None:
    """Return and clear GCS download ms captured during resolve_attachment_preview."""
    gcs_ms = _preview_gcs_ms.get()
    _preview_gcs_ms.set(None)
    return gcs_ms


def download_wecom_attachment_bytes(storage_uri: str) -> tuple[bytes, str | None]:
    """
    Read attachment bytes from private GCS storage_uri (gs://bucket/path).
    Returns (content, content_type).
    """
    parsed = parse_storage_uri(storage_uri)
    if not parsed:
        raise ValueError("invalid_storage_uri")
    bucket, object_path = parsed
    if _gcs_download_hook is not None:
        t0 = time.perf_counter()
        content, content_type = _gcs_download_hook(storage_uri)
        _preview_gcs_ms.set(round((time.perf_counter() - t0) * 1000, 1))
        return content, content_type

    from google.cloud import storage  # type: ignore[import-untyped]

    client = storage.Client()
    blob = client.bucket(bucket).blob(object_path)
    if not blob.exists():
        raise FileNotFoundError("gcs_object_not_found")
    t0 = time.perf_counter()
    content = blob.download_as_bytes()
    _preview_gcs_ms.set(round((time.perf_counter() - t0) * 1000, 1))
    content_type = blob.content_type or None
    return content, content_type


def resolve_attachment_preview(
    case: dict[str, Any],
    attachment_id: str,
) -> tuple[bytes, str, str | None]:
    """
    Resolve attachment content for preview/download.
    Returns (content, media_type, filename_hint).
    """
    att = find_case_attachment(case, attachment_id)
    if att is None:
        raise FileNotFoundError("attachment_not_found")

    source = str(att.get("source") or "").strip().lower()
    if source in ("wecom", "h5_task"):
        storage_uri = str(att.get("storage_uri") or "").strip()
        if not storage_uri:
            raise FileNotFoundError("storage_uri_missing")
        content, content_type = download_wecom_attachment_bytes(storage_uri)
        mime = content_type or att.get("mime_type") or "application/octet-stream"
        hint_id = str(att.get("msg_id") or att.get("h5_upload_id") or attachment_id)
        prefix = "h5" if source == "h5_task" else "wecom"
        ext = ".jpg"
        mime_l = (mime or "").lower()
        if "png" in mime_l:
            ext = ".png"
        elif "pdf" in mime_l:
            ext = ".pdf"
        elif "heic" in mime_l or "heif" in mime_l:
            ext = ".heic"
        return content, mime, f"{prefix}_{hint_id[:12]}{ext}"

    from services.fiqa_api.inbox_triage.case_store import get_attachment_file_path

    cid = str(case.get("case_id") or "").strip()
    path = get_attachment_file_path(cid, attachment_id)
    if path is None or not path.exists():
        raise FileNotFoundError("local_attachment_not_found")
    content = path.read_bytes()
    filename = att.get("filename") or path.name.split("_", 1)[-1]
    mime = att.get("mime_type") or "application/octet-stream"
    if path.suffix.lower() == ".pdf":
        mime = "application/pdf"
    elif path.suffix.lower() in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif path.suffix.lower() == ".png":
        mime = "image/png"
    return content, mime, str(filename)
