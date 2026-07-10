"""Best-effort WeCom KF customer profile lookup via kf/customer/batchget."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from services.fiqa_api.wecom.access_token import get_access_token
from services.fiqa_api.wecom.config import WeComKfConfig, load_wecom_kf_config
from services.fiqa_api.wecom.identity import wecom_external_userid_display_suffix

logger = logging.getLogger(__name__)

_CUSTOMER_BATCHGET_URL = "https://qyapi.weixin.qq.com/cgi-bin/kf/customer/batchget"
_PROFILE_SOURCE = "kf_customer_batchget"
_PROFILE_TTL = timedelta(hours=24)
_FETCH_TIMEOUT_S = 3.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_fetched_at(value: str | None) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def should_fetch_kf_customer_profile(customer_identity: dict[str, Any] | None) -> bool:
    """True when profile lookup is worth attempting (TTL + nickname cache)."""
    identity = customer_identity if isinstance(customer_identity, dict) else {}
    if str(identity.get("wecom_nickname") or "").strip():
        return False
    fetched_at = _parse_fetched_at(str(identity.get("profile_fetched_at") or ""))
    if fetched_at is not None:
        if datetime.now(timezone.utc) - fetched_at < _PROFILE_TTL:
            return False
    return True


def fetch_kf_customer_profile(
    external_userid: str,
    *,
    cfg: WeComKfConfig | None = None,
) -> dict[str, Any] | None:
    """
    Best-effort POST kf/customer/batchget for nickname / avatar / unionid.

    Returns normalized profile dict or None on failure. Never raises.
    Real WeChat ID (微信号) is not available from this API.
    """
    ext = (external_userid or "").strip()
    if not ext:
        return None

    resolved_cfg = cfg or load_wecom_kf_config()
    if resolved_cfg is None:
        logger.warning("wecom_kf_profile_lookup_skipped_v1 reason=config_missing ext_suffix=%s", ext[-6:])
        return None

    access_token = get_access_token(resolved_cfg)
    if not access_token:
        logger.warning("wecom_kf_profile_lookup_skipped_v1 reason=no_access_token ext_suffix=%s", ext[-6:])
        return None

    try:
        resp = httpx.post(
            f"{_CUSTOMER_BATCHGET_URL}?access_token={access_token}",
            json={
                "external_userid_list": [ext],
                "need_enter_session_context": 0,
            },
            timeout=_FETCH_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning(
            "wecom_kf_profile_lookup_failed_v1 ext_suffix=%s error=%s",
            ext[-6:],
            exc,
        )
        return None

    errcode = data.get("errcode")
    if errcode != 0:
        logger.warning(
            "wecom_kf_profile_lookup_error_v1 %s",
            {
                "errcode": errcode,
                "errmsg": data.get("errmsg"),
                "ext_suffix": ext[-6:],
            },
        )
        return None

    invalid = data.get("invalid_external_userid") or []
    if isinstance(invalid, list) and ext in invalid:
        logger.info(
            "wecom_kf_profile_lookup_invalid_id_v1 ext_suffix=%s hint=48h_activity_or_permission",
            ext[-6:],
        )
        return None

    customer_list = data.get("customer_list") or []
    if not isinstance(customer_list, list) or not customer_list:
        logger.info("wecom_kf_profile_lookup_empty_v1 ext_suffix=%s", ext[-6:])
        return None

    row = customer_list[0] if isinstance(customer_list[0], dict) else {}
    nickname = str(row.get("nickname") or "").strip()
    avatar = str(row.get("avatar") or "").strip()
    unionid = str(row.get("unionid") or "").strip()

    raw_fields = [k for k in ("nickname", "avatar", "unionid", "gender") if row.get(k)]

    if not nickname and not avatar and not unionid:
        logger.info(
            "wecom_kf_profile_lookup_no_identity_fields_v1 ext_suffix=%s raw_fields=%s",
            ext[-6:],
            raw_fields,
        )
        return None

    return {
        "wecom_external_userid_suffix": wecom_external_userid_display_suffix(ext),
        "wecom_nickname": nickname or None,
        "wecom_avatar": avatar or None,
        "wecom_unionid": unionid or None,
        "profile_source": _PROFILE_SOURCE,
        "profile_fetched_at": _utc_now_iso(),
        "raw_available_fields": raw_fields,
        "real_wechat_id_available": False,
    }


def merge_customer_identity(
    existing: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    *,
    external_userid: str,
) -> dict[str, Any]:
    """Merge profile lookup into extra.customer_identity bag."""
    ext = (external_userid or "").strip()
    merged: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    merged["wecom_external_userid_suffix"] = wecom_external_userid_display_suffix(ext)

    if profile:
        for key in (
            "wecom_nickname",
            "wecom_avatar",
            "wecom_unionid",
            "profile_source",
            "profile_fetched_at",
            "raw_available_fields",
            "real_wechat_id_available",
        ):
            if profile.get(key) is not None:
                merged[key] = profile[key]
    elif "profile_fetched_at" not in merged:
        merged["profile_fetched_at"] = _utc_now_iso()
        merged["profile_source"] = _PROFILE_SOURCE

    return merged
