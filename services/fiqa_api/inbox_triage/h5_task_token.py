"""
HMAC-signed H5 guided task token (P19D-2 / P19D-4A).

Token binds case_id + lane + slot (v1) or flow + slots (v2) with TTL.
No login required. Never embeds full external_userid.

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

_ADD_CAR_SLOTS: Final[frozenset[str]] = frozenset(
    {"vin_photo", "registration_photo", "insurance_card_photo"}
)
_CLAIM_EVIDENCE_SLOTS: Final[frozenset[str]] = frozenset(
    {"customer_damage_photo", "other_party_vehicle_photo", "scene_photo"}
)
_SUPPORTED_LANES: Final[frozenset[str]] = frozenset({"add_car", "claim"})
FLOW_ADD_VEHICLE_PHOTO: Final[str] = "add_vehicle_photo_flow"
FLOW_CLAIM_EVIDENCE_PACK: Final[str] = "claim_evidence_pack"
FLOW_CLAIM_INTAKE_FORM: Final[str] = "claim_intake_form"
INTAKE_FORM_TTL_SECONDS: Final[int] = 72 * 3600  # 72h — multi-day accident resume
ADD_VEHICLE_PHOTO_FLOW_SLOTS: Final[tuple[str, ...]] = (
    "vin_photo",
    "registration_photo",
    "insurance_card_photo",
)
CLAIM_EVIDENCE_PACK_FLOW_SLOTS: Final[tuple[str, ...]] = (
    "customer_damage_photo",
    "other_party_vehicle_photo",
    "scene_photo",
)

# Backward-compatible alias for add-car-only callers
_SUPPORTED_SLOTS: Final[frozenset[str]] = _ADD_CAR_SLOTS


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


def _slots_for_lane(lane_norm: str) -> frozenset[str]:
    if lane_norm == "add_car":
        return _ADD_CAR_SLOTS
    if lane_norm == "claim":
        return _CLAIM_EVIDENCE_SLOTS
    raise ValueError(f"unsupported_lane: {lane_norm}")


def _validate_lane_slot(lane_norm: str, slot_norm: str) -> None:
    if lane_norm not in _SUPPORTED_LANES:
        raise ValueError(f"unsupported_lane: {lane_norm}")
    if slot_norm not in _slots_for_lane(lane_norm):
        raise ValueError(f"unsupported_slot: {slot_norm}")


def _expected_flow_slots(lane_norm: str, flow_norm: str) -> tuple[str, ...] | None:
    if lane_norm == "add_car" and flow_norm == FLOW_ADD_VEHICLE_PHOTO:
        return ADD_VEHICLE_PHOTO_FLOW_SLOTS
    if lane_norm == "claim" and flow_norm == FLOW_CLAIM_EVIDENCE_PACK:
        return CLAIM_EVIDENCE_PACK_FLOW_SLOTS
    return None


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
    """Issue signed v1 single-slot task token for H5 upload page."""
    cid = (case_id or "").strip()
    if not cid:
        raise ValueError("case_id_required")
    lane_norm = (lane or "").strip().lower()
    slot_norm = (slot or "").strip().lower()
    _validate_lane_slot(lane_norm, slot_norm)

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


def issue_h5_flow_token(
    *,
    case_id: str,
    lane: str = "add_car",
    flow: str = FLOW_ADD_VEHICLE_PHOTO,
    slots: tuple[str, ...] | None = None,
    external_userid: str | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: float | None = None,
    nonce: str | None = None,
) -> str:
    """Issue signed v2 multi-slot photo flow token."""
    cid = (case_id or "").strip()
    if not cid:
        raise ValueError("case_id_required")
    lane_norm = (lane or "").strip().lower()
    if lane_norm not in _SUPPORTED_LANES:
        raise ValueError(f"unsupported_lane: {lane_norm}")
    flow_norm = (flow or "").strip()
    if lane_norm == "add_car" and not flow_norm:
        flow_norm = FLOW_ADD_VEHICLE_PHOTO
    if lane_norm == "claim" and not flow_norm:
        flow_norm = FLOW_CLAIM_EVIDENCE_PACK
    expected_slots = _expected_flow_slots(lane_norm, flow_norm)
    if expected_slots is None:
        raise ValueError(f"unsupported_flow: {flow_norm}")
    slot_list = list(slots or expected_slots)
    if tuple(slot_list) != expected_slots:
        raise ValueError("invalid_flow_slots")

    t = time.time() if now is None else float(now)
    iat = int(t)
    exp = iat + max(60, int(ttl_seconds))
    payload: dict[str, Any] = {
        "v": 2,
        "model": MODEL_VERSION,
        "case_id": cid,
        "lane": lane_norm,
        "flow": flow_norm,
        "slots": slot_list,
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


def issue_h5_intake_form_token(
    *,
    case_id: str,
    lane: str = "claim",
    flow: str = FLOW_CLAIM_INTAKE_FORM,
    external_userid: str | None = None,
    ttl_seconds: int = INTAKE_FORM_TTL_SECONDS,
    now: float | None = None,
    nonce: str | None = None,
) -> str:
    """Issue signed v3 intake-form task token (structured fields, no photo slots)."""
    cid = (case_id or "").strip()
    if not cid:
        raise ValueError("case_id_required")
    lane_norm = (lane or "").strip().lower()
    if lane_norm not in _SUPPORTED_LANES:
        raise ValueError(f"unsupported_lane: {lane_norm}")
    flow_norm = (flow or "").strip()
    if lane_norm == "claim" and flow_norm != FLOW_CLAIM_INTAKE_FORM:
        raise ValueError(f"unsupported_flow: {flow_norm}")

    t = time.time() if now is None else float(now)
    iat = int(t)
    exp = iat + max(60, int(ttl_seconds))
    payload: dict[str, Any] = {
        "v": 3,
        "model": MODEL_VERSION,
        "case_id": cid,
        "lane": lane_norm,
        "flow": flow_norm,
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
    user_ref: str | None
    nonce: str
    iat: int
    exp: int
    version: int = 1
    slot: str | None = None
    flow: str | None = None
    slots: tuple[str, ...] = ()

    @property
    def is_flow_token(self) -> bool:
        return self.version == 2 and bool(self.flow)

    @property
    def is_intake_form_token(self) -> bool:
        return self.version == 3 and self.flow == FLOW_CLAIM_INTAKE_FORM


def _verify_common(payload: dict[str, Any], *, now: float | None) -> tuple[int, int, str, str, str, str | None] | None:
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
    nonce = str(payload.get("nonce") or "").strip()
    if not case_id or not lane or not nonce:
        return None
    if lane not in _SUPPORTED_LANES:
        return None

    user_ref_raw = payload.get("user_ref")
    user_ref = str(user_ref_raw).strip() if user_ref_raw else None
    return iat, exp, case_id, lane, nonce, user_ref or None


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

    version = int(payload.get("v") or 0)
    common = _verify_common(payload, now=now)
    if common is None:
        return None
    iat, exp, case_id, lane, nonce, user_ref = common

    if version == 1:
        slot = str(payload.get("slot") or "").strip().lower()
        if not slot:
            return None
        try:
            allowed = _slots_for_lane(lane)
        except ValueError:
            return None
        if slot not in allowed:
            return None
        return VerifiedH5TaskToken(
            case_id=case_id,
            lane=lane,
            slot=slot,
            user_ref=user_ref,
            nonce=nonce,
            iat=iat,
            exp=exp,
            version=1,
        )

    if version == 2:
        flow = str(payload.get("flow") or "").strip()
        expected_slots = _expected_flow_slots(lane, flow)
        if expected_slots is None:
            return None
        raw_slots = payload.get("slots")
        if not isinstance(raw_slots, list) or len(raw_slots) != len(expected_slots):
            return None
        slots = tuple(str(s).strip().lower() for s in raw_slots)
        if slots != expected_slots:
            return None
        return VerifiedH5TaskToken(
            case_id=case_id,
            lane=lane,
            flow=flow,
            slots=slots,
            user_ref=user_ref,
            nonce=nonce,
            iat=iat,
            exp=exp,
            version=2,
        )

    if version == 3:
        flow = str(payload.get("flow") or "").strip()
        if lane == "claim" and flow != FLOW_CLAIM_INTAKE_FORM:
            return None
        return VerifiedH5TaskToken(
            case_id=case_id,
            lane=lane,
            flow=flow,
            user_ref=user_ref,
            nonce=nonce,
            iat=iat,
            exp=exp,
            version=3,
        )

    return None
