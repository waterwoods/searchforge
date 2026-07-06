"""GCS storage for WeCom media (P19A — private bucket, metadata URI only)."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

DEFAULT_WECOM_MEDIA_BUCKET = "caseiq-wecom-media-qa"

_ALLOWED_MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}

# Test hook — replaced in unit tests to avoid real GCS calls.
_gcs_upload_hook: Callable[..., str] | None = None


def set_gcs_upload_hook_for_tests(hook: Callable[..., str] | None) -> None:
    """Tests only: inject mock upload returning storage_uri."""
    global _gcs_upload_hook
    _gcs_upload_hook = hook


def wecom_media_gcs_bucket() -> str:
    return (os.getenv("WECOM_MEDIA_GCS_BUCKET") or DEFAULT_WECOM_MEDIA_BUCKET).strip()


def infer_extension(
    *,
    mime_type: str | None,
    filename: str | None = None,
    msgtype: str = "image",
) -> str:
    """Map mime/filename to a safe extension; raise ValueError when unsupported."""
    mime = (mime_type or "").split(";")[0].strip().lower()
    if mime in _ALLOWED_MIME_TO_EXT:
        return _ALLOWED_MIME_TO_EXT[mime]
    name = (filename or "").lower()
    for ext in (".jpg", ".jpeg", ".png", ".pdf"):
        if name.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    if (msgtype or "").lower() == "image" and not mime:
        return ".jpg"
    if (msgtype or "").lower() == "file" and name.endswith(".pdf"):
        return ".pdf"
    raise ValueError(f"unsupported_mime_type: {mime or 'unknown'}")


def build_wecom_media_object_path(
    *,
    external_userid: str,
    msg_id: str,
    ext: str,
    received_at: datetime | None = None,
) -> str:
    """``wecom/<external_userid>/<yyyy>/<mm>/<msg_id>.<ext>``"""
    ext_norm = ext if ext.startswith(".") else f".{ext}"
    ext_norm = re.sub(r"[^.\w]", "", ext_norm) or ".bin"
    ts = received_at or datetime.now(timezone.utc)
    uid = (external_userid or "unknown").strip() or "unknown"
    mid = (msg_id or "unknown").strip() or "unknown"
    return f"wecom/{uid}/{ts.year:04d}/{ts.month:02d}/{mid}{ext_norm}"


def build_storage_uri(bucket: str, object_path: str) -> str:
    b = (bucket or "").strip().strip("/")
    p = (object_path or "").lstrip("/")
    return f"gs://{b}/{p}"


def _default_gcs_upload(
    *,
    bucket: str,
    object_path: str,
    content: bytes,
    content_type: str | None,
) -> str:
    from google.cloud import storage  # type: ignore[import-untyped]

    client = storage.Client()
    blob = client.bucket(bucket).blob(object_path)
    blob.upload_from_string(content, content_type=content_type or "application/octet-stream")
    return build_storage_uri(bucket, object_path)


def upload_wecom_media_to_gcs(
    *,
    external_userid: str,
    msg_id: str,
    content: bytes,
    mime_type: str | None,
    msgtype: str = "image",
    filename: str | None = None,
    received_at: datetime | None = None,
    bucket: str | None = None,
) -> dict[str, Any]:
    """
    Upload bytes to the private WeCom media bucket. Returns metadata dict with storage_uri.
    Never generates a public URL.
    """
    if not content:
        raise ValueError("empty_content")
    ext = infer_extension(mime_type=mime_type, filename=filename, msgtype=msgtype)
    bkt = (bucket or wecom_media_gcs_bucket()).strip()
    object_path = build_wecom_media_object_path(
        external_userid=external_userid,
        msg_id=msg_id,
        ext=ext,
        received_at=received_at,
    )
    upload_fn = _gcs_upload_hook or _default_gcs_upload
    storage_uri = upload_fn(
        bucket=bkt,
        object_path=object_path,
        content=content,
        content_type=mime_type,
    )
    logger.info(
        "wecom_media_gcs_upload_ok_v1 %s",
        {"bucket": bkt, "object_path": object_path, "size_bytes": len(content)},
    )
    return {
        "storage_uri": storage_uri,
        "bucket": bkt,
        "object_path": object_path,
        "mime_type": mime_type,
        "size_bytes": len(content),
        "extension": ext,
    }
