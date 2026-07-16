"""P20 Capability 3A — customer launch URL / QR target builder.

Reuses the existing signed H5 intake-form task token (v3) that already opens
the Mini Program / H5 customer continuation flow. Isolates Preview vs pilot
URL differences behind one contract.

Production blocker (documented): native WeChat unlimited Mini Program QR
(wxacode.getUnlimited) is not wired here. Pilot QR encodes the HTTPS launch
URL that carries the opaque signed token.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

from services.fiqa_api.inbox_triage.h5_task_link import h5_task_frontend_base, mask_h5_task_url
from services.fiqa_api.inbox_triage.h5_task_token import (
    FLOW_CLAIM_INTAKE_FORM,
    issue_h5_intake_form_token,
    verify_h5_task_token,
)

logger = logging.getLogger(__name__)

DEFAULT_ACCESS_TTL_SECONDS = 7 * 24 * 3600  # 7 days MVP policy
MINI_PROGRAM_ENTRY_PATH = "pages/entry/entry"


def _token_secret() -> bytes:
    raw = (
        os.getenv("H5_TASK_TOKEN_SECRET")
        or os.getenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET")
        or os.getenv("WECHAT_BINDING_STATE_SECRET")
        or os.getenv("UNIFIED_INTAKE_BINDING_STATE_SECRET")
        or ""
    ).strip()
    if not raw:
        raw = "dev-insecure-h5-task-token-set-H5_TASK_TOKEN_SECRET"
    return raw.encode("utf-8")


def hash_launch_token(token: str) -> str:
    """Storeable fingerprint — never log the raw token."""
    digest = hmac.new(_token_secret(), (token or "").encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


@dataclass(frozen=True)
class CustomerLaunchTarget:
    """Authoritative customer launch representation for Workbench QR / Copy Link."""

    launch_url: str
    mini_program_path: str
    token: str
    token_hash: str
    token_nonce: str
    token_iat: int
    token_exp: int
    expires_at_iso: str
    qr_payload: str
    channel: str = "https_deep_link"
    production_qr_blocker: str = (
        "Native WeChat wxacode.getUnlimited Mini Program QR is not configured; "
        "pilot QR encodes the HTTPS claim-task deep link."
    )

    def public_card(self) -> dict[str, Any]:
        """Broker-safe access card fields (no raw internal IDs required)."""
        return {
            "status": "ready",
            "launch_url": self.launch_url,
            "qr_payload": self.qr_payload,
            "copy_link": self.launch_url,
            "mini_program_path": self.mini_program_path,
            "expires_at": self.expires_at_iso,
            "channel": self.channel,
            "instruction_zh": "让客户用微信扫码并补充资料。",
            "production_qr_blocker": self.production_qr_blocker,
        }


def issue_customer_launch_token(
    *,
    case_id: str,
    external_userid: str | None = None,
    ttl_seconds: int = DEFAULT_ACCESS_TTL_SECONDS,
    now: float | None = None,
    nonce: str | None = None,
) -> CustomerLaunchTarget:
    """Issue one reconstructible launch token bound to the case (no PII in payload)."""
    t = time.time() if now is None else float(now)
    iat = int(t)
    ttl = max(60, int(ttl_seconds))
    token = issue_h5_intake_form_token(
        case_id=case_id,
        lane="claim",
        flow=FLOW_CLAIM_INTAKE_FORM,
        external_userid=external_userid,
        ttl_seconds=ttl,
        now=t,
        nonce=nonce,
    )
    claims = verify_h5_task_token(token, now=t)
    if claims is None:
        raise RuntimeError("customer_launch_token_verify_failed")
    base = h5_task_frontend_base().rstrip("/")
    launch_url = f"{base}/task/claim/{token}"
    mini_path = f"{MINI_PROGRAM_ENTRY_PATH}?token={token}"
    exp = int(claims.exp)
    from datetime import datetime, timezone

    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return CustomerLaunchTarget(
        launch_url=launch_url,
        mini_program_path=mini_path,
        token=token,
        token_hash=hash_launch_token(token),
        token_nonce=str(claims.nonce),
        token_iat=int(claims.iat),
        token_exp=exp,
        expires_at_iso=expires_at,
        qr_payload=launch_url,
    )


def rebuild_customer_launch_from_material(
    *,
    case_id: str,
    token_nonce: str,
    token_iat: int,
    token_exp: int,
    external_userid: str | None = None,
) -> CustomerLaunchTarget:
    """Rebuild the exact same launch token from durable material (refresh-safe)."""
    ttl = max(60, int(token_exp) - int(token_iat))
    return issue_customer_launch_token(
        case_id=case_id,
        external_userid=external_userid,
        ttl_seconds=ttl,
        now=float(token_iat),
        nonce=token_nonce,
    )


def validate_access_token(
    *,
    presented_token: str,
    expected_hash: str,
    token_exp: int,
    now: float | None = None,
) -> str | None:
    """Return None if valid; otherwise a safe error code (no case details)."""
    t = time.time() if now is None else float(now)
    if t > float(token_exp):
        return "access_expired"
    claims = verify_h5_task_token(presented_token, now=t)
    if claims is None:
        return "access_invalid"
    if not hmac.compare_digest(hash_launch_token(presented_token), expected_hash or ""):
        return "access_invalid"
    return None


def mask_launch_for_logs(url_or_token: str) -> str:
    return mask_h5_task_url(url_or_token)
