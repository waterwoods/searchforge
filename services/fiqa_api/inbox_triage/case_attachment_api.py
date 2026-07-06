"""Workbench attachment API helpers (P19B) — sanitize metadata, GCS preview proxy."""

from __future__ import annotations

import logging
import re
from typing import Any, Callable

logger = logging.getLogger(__name__)

_GCS_URI_RE = re.compile(r"^gs://([^/]+)/(.+)$")

# Tests inject mock GCS reader — never used in production unless set.
_gcs_download_hook: Callable[[str], tuple[bytes, str | None]] | None = None


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
    if att.get("source") == "wecom":
        return bool(parse_storage_uri(str(att.get("storage_uri") or "")))
    filename = att.get("filename")
    return bool(filename)


def sanitize_attachment_for_api(case_id: str, att: dict[str, Any]) -> dict[str, Any]:
    """
    Strip sensitive/internal fields; add broker-safe preview_url.
    Never exposes storage_uri, external_userid, media_id, or public GCS URL.
    """
    aid = str(att.get("attachment_id") or "").strip()
    source = str(att.get("source") or "").strip().lower() or "web"
    preview_available = _attachment_preview_available(att)
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
        "intake_status": att.get("intake_status"),
        "preview_available": preview_available,
        "storage_status": "stored" if preview_available or att.get("storage_uri") else "unknown",
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


def sanitize_case_for_workbench_api(case: dict[str, Any]) -> dict[str, Any]:
    """Return case dict safe for workbench API responses."""
    row = dict(case)
    cid = str(case.get("case_id") or "").strip()
    row["case_attachments"] = sanitize_case_attachments_for_api(cid, case)
    ext = row.get("wecom_external_userid")
    if isinstance(ext, str) and ext.strip():
        # Mask — never send full external_userid to frontend.
        row["wecom_external_userid"] = None
    return row


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
        return _gcs_download_hook(storage_uri)

    from google.cloud import storage  # type: ignore[import-untyped]

    client = storage.Client()
    blob = client.bucket(bucket).blob(object_path)
    if not blob.exists():
        raise FileNotFoundError("gcs_object_not_found")
    content = blob.download_as_bytes()
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

    if att.get("source") == "wecom":
        storage_uri = str(att.get("storage_uri") or "").strip()
        if not storage_uri:
            raise FileNotFoundError("storage_uri_missing")
        content, content_type = download_wecom_attachment_bytes(storage_uri)
        mime = content_type or att.get("mime_type") or "application/octet-stream"
        msg_id = str(att.get("msg_id") or attachment_id)
        ext = ".jpg"
        mime_l = (mime or "").lower()
        if "png" in mime_l:
            ext = ".png"
        elif "pdf" in mime_l:
            ext = ".pdf"
        return content, mime, f"wecom_{msg_id[:12]}{ext}"

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
