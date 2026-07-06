"""Download WeCom KF media by media_id (P19A — no OCR)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from services.fiqa_api.wecom.access_token import get_access_token
from services.fiqa_api.wecom.config import WeComKfConfig

logger = logging.getLogger(__name__)

_MEDIA_GET_URL = "https://qyapi.weixin.qq.com/cgi-bin/media/get"
_DEFAULT_TIMEOUT = 30.0

# Configurable via env in media_intake if needed; defaults per P19A spec.
DEFAULT_MAX_IMAGE_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_FILE_BYTES = 20 * 1024 * 1024


class WeComMediaDownloadError(Exception):
    """WeCom media download failed (API error, empty body, oversize, etc.)."""


@dataclass(frozen=True)
class WeComMediaDownloadResult:
    content: bytes
    content_type: str | None
    filename: str | None


def _size_limit_for_msgtype(msgtype: str) -> int:
    if (msgtype or "").lower() == "file":
        return DEFAULT_MAX_FILE_BYTES
    return DEFAULT_MAX_IMAGE_BYTES


def download_wecom_media(
    cfg: WeComKfConfig,
    *,
    media_id: str,
    msgtype: str = "image",
    timeout: float = _DEFAULT_TIMEOUT,
    http_get: Any | None = None,
) -> WeComMediaDownloadResult:
    """
    Fetch binary media from WeCom ``/cgi-bin/media/get``.

    Raises WeComMediaDownloadError on API JSON errors, empty content, or oversize.
    """
    mid = (media_id or "").strip()
    if not mid:
        raise WeComMediaDownloadError("missing_media_id")

    access_token = get_access_token(cfg)
    if not access_token:
        raise WeComMediaDownloadError("access_token_unavailable")

    get_fn = http_get or httpx.get
    try:
        resp = get_fn(
            _MEDIA_GET_URL,
            params={"access_token": access_token, "media_id": mid},
            timeout=timeout,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("wecom_media_download_transport_failed_v1 media_id_tail=%s error=%s", mid[-6:], exc)
        raise WeComMediaDownloadError(f"transport_error: {exc}") from exc

    content_type = (resp.headers.get("content-type") or "").split(";")[0].strip().lower() or None
    if content_type and "application/json" in content_type:
        try:
            data = resp.json()
        except Exception:
            data = {}
        errcode = data.get("errcode")
        errmsg = data.get("errmsg")
        logger.warning(
            "wecom_media_download_api_error_v1 %s",
            json.dumps({"errcode": errcode, "errmsg": errmsg, "media_id_tail": mid[-6:]}, ensure_ascii=False),
        )
        raise WeComMediaDownloadError(f"wecom_api_error errcode={errcode} errmsg={errmsg}")

    content = resp.content or b""
    if not content:
        raise WeComMediaDownloadError("empty_media_content")

    limit = _size_limit_for_msgtype(msgtype)
    if len(content) > limit:
        raise WeComMediaDownloadError(f"oversize_media bytes={len(content)} limit={limit}")

    filename = None
    cd = resp.headers.get("content-disposition") or ""
    if "filename=" in cd:
        part = cd.split("filename=", 1)[-1].strip().strip('"').strip("'")
        if part:
            filename = part

    logger.info(
        "wecom_media_download_ok_v1 %s",
        {
            "media_id_tail": mid[-6:],
            "msgtype": msgtype,
            "size_bytes": len(content),
            "content_type": content_type,
        },
    )
    return WeComMediaDownloadResult(
        content=content,
        content_type=content_type,
        filename=filename,
    )
