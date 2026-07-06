"""
HMAC-signed H5 guided task token (P19D-2).

Token binds case_id + lane + slot with TTL. No login required.
Never embeds full external_userid — optional user_ref tail for audit only.

Env: H5_TASK_TOKEN_SECRET (preferred), else UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET,
     else WECHAT_BINDING_STATE_SECRET.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Final

TOKEN_PREFIX: Final[str] = "h5t1."
MODEL_VERSION: Final[str] = "h5_task_token_v1"
DEFAULT_TTL_SECONDS: Final[int] = 86400  # 24h

_SUPPORTED_SLOTS: Final[frozenset[str]] = frozenset({"vin_photo"})
_SUPPORTED_LANES: Final[frozenset[str]] = frozenset({"add_car"})


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


def external_userid_ref(external_userid: str | None) -> str:
    """Opaque short ref — never the full external_userid."""
    uid = (external_userid or "").strip()
    if not uid:
        return ""
    digest = hmac.new(_token_secret(), uid.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:8]


def issue_h5_task_token(
    *,
    case_id: str,
    lane: str = "add_car",
    slot: str = "vin_photo",
    external_userid: str | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: float | None = None,
    nonce: str | None = None,
) -> str:
    """Issue signed task token for H5 upload page."""
    cid = (case_id or "").strip()
    if not cid:
        raise ValueError("case_id_required")
    lane_norm = (lane or "").strip().lower()
    slot_norm = (slot or "").strip().lower()
    if lane_norm not in _SUPPORTED_LANES:
        raise ValueError(f"unsupported_lane: {lane_norm}")
    if slot_norm not in _SUPPORTED_SLOTS:
        raise ValueError(f"unsupported_slot: {slot_norm}")

    t = time.time() if now is None else float(now)
    iat = int(t)
    exp = iat + max(60, int(ttl_seconds))
    payload: dict[str, Any] = {
        "v": 1,
        "model": MODEL_VERSION,
        "case_id": cid,
        "lane": lane_norm,
        "slot": slot_norm,
        "iat": iat,
        "exp": exp,
        "nonce": (nonce or uuid.uuid4().hex[:16]),
    }
    user_ref = external_userid_ref(external_userid)
    if user_ref:
        payload["user_ref"] = user_ref

    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    b64 = base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")
    sig = hmac.new(_token_secret(), body, hashlib.sha256).hexdigest()[:32]
    return f"{TOKEN_PREFIX}{b64}.{sig}"


@dataclass(frozen=True)
class VerifiedH5TaskToken:
    case_id: str
    lane: str
    slot: str
    user_ref: str | None
    nonce: str
    iat: int
    exp: int


def verify_h5_task_token(token: str, *, now: float | None = None) -> VerifiedH5TaskToken | None:
    """Return verified claims or None if invalid/expired/tampered."""
    raw = (token or "").strip()
    if not raw.startswith(TOKEN_PREFIX):
        return None
    rest = raw[len(TOKEN_PREFIX) :]
    if "." not in rest:
        return None
    b64, sig = rest.rsplit(".", 1)
    if len(sig) != 32:
        return None
    pad = "=" * ((4 - len(b64) % 4) % 4)
    try:
        body = base64.urlsafe_b64decode(b64 + pad)
    except Exception:
        return None
    expect = hmac.new(_token_secret(), body, hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(expect, sig):
        return None
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if int(payload.get("v") or 0) != 1:
        return None
    if str(payload.get("model") or "") != MODEL_VERSION:
        return None
    try:
        iat = int(payload["iat"])
        exp = int(payload["exp"])
    except Exception:
        return None
    t = time.time() if now is None else float(now)
    if t > float(exp) or t < float(iat - 60):
        return None

    case_id = str(payload.get("case_id") or "").strip()
    lane = str(payload.get("lane") or "").strip().lower()
    slot = str(payload.get("slot") or "").strip().lower()
    nonce = str(payload.get("nonce") or "").strip()
    if not case_id or not lane or not slot or not nonce:
        return None
    if lane not in _SUPPORTED_LANES or slot not in _SUPPORTED_SLOTS:
        return None

    user_ref_raw = payload.get("user_ref")
    user_ref = str(user_ref_raw).strip() if user_ref_raw else None
    return VerifiedH5TaskToken(
        case_id=case_id,
        lane=lane,
        slot=slot,
        user_ref=user_ref or None,
        nonce=nonce,
        iat=iat,
        exp=exp,
    )
