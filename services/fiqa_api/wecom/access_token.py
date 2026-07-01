"""WeCom KF API access_token cache (微信客服 Secret)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from services.fiqa_api.wecom.config import WeComKfConfig

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"


@dataclass
class _TokenCache:
    token: str
    expires_at: float


_cache: _TokenCache | None = None


def _kf_secret(cfg: WeComKfConfig) -> str | None:
    return cfg.kf_secret


def get_access_token(cfg: WeComKfConfig, *, force_refresh: bool = False) -> str | None:
    """Return cached access_token or fetch via 微信客服 Secret. None if secret unset."""
    secret = _kf_secret(cfg)
    if not secret:
        return None

    global _cache
    now = time.time()
    if not force_refresh and _cache and _cache.expires_at > now + 60:
        return _cache.token

    try:
        resp = httpx.get(
            _TOKEN_URL,
            params={"corpid": cfg.corp_id, "corpsecret": secret},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("wecom_access_token_fetch_failed_v1 error=%s", exc)
        return None

    if data.get("errcode") != 0:
        logger.warning(
            "wecom_access_token_error_v1 %s",
            {"errcode": data.get("errcode"), "errmsg": data.get("errmsg")},
        )
        return None

    token = str(data.get("access_token") or "")
    if not token:
        return None

    expires_in = int(data.get("expires_in") or 7200)
    _cache = _TokenCache(token=token, expires_at=now + expires_in)
    return token


def clear_access_token_cache() -> None:
    global _cache
    _cache = None
