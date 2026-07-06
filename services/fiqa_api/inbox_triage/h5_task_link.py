"""H5 guided task link minting (P19D-2 / P19D-3)."""

from __future__ import annotations

import os
import re

from services.fiqa_api.inbox_triage.h5_task_token import (
    DEFAULT_TTL_SECONDS,
    TOKEN_PREFIX,
    issue_h5_task_token,
)

_DEFAULT_H5_FRONTEND_BASE = "https://ui-smoky-beta.vercel.app"
_TOKEN_IN_URL_RE = re.compile(re.escape(TOKEN_PREFIX) + r"[^/\s]+")


def h5_task_frontend_base() -> str:
    """Frontend origin for H5 task upload pages."""
    raw = (
        (os.getenv("H5_TASK_FRONTEND_BASE_URL") or "").strip()
        or (os.getenv("UNIFIED_INTAKE_FRONTEND_ORIGIN") or "").strip()
    ).rstrip("/")
    if raw:
        return raw
    return _DEFAULT_H5_FRONTEND_BASE


def mint_h5_task_link(
    *,
    case_id: str,
    lane: str = "add_car",
    slot: str = "vin_photo",
    external_userid: str | None = None,
    base_url: str | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> str:
    """Mint signed H5 upload URL for one case/slot. Never logs secrets."""
    token = issue_h5_task_token(
        case_id=case_id,
        lane=lane,
        slot=slot,
        external_userid=external_userid,
        ttl_seconds=ttl_seconds,
    )
    base = (base_url or h5_task_frontend_base()).rstrip("/")
    return f"{base}/task/upload/{token}"


def mask_h5_task_url(url: str) -> str:
    """Mask token in URL for logs — prefix only."""
    if not url:
        return ""
    return _TOKEN_IN_URL_RE.sub(f"{TOKEN_PREFIX}…", url)
