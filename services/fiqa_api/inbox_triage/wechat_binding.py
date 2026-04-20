"""
Optional WeChat OAuth2 (snsapi_base) binding for Stage-1 continuity metadata.

- Stores opaque person_link_key (hashed openid); never persists raw openid in JSON.
- Requires client-pack wechat_binding_mode=live and env WECHAT_APP_ID / WECHAT_APP_SECRET.
- Dev/staging: WECHAT_BINDING_ALLOW_SIMULATE=1 enables simulate-complete without WeChat.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
import urllib.parse
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_WECHAT_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
_AUTH_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"


def _state_secret() -> bytes:
    raw = (os.getenv("WECHAT_BINDING_STATE_SECRET") or os.getenv("UNIFIED_INTAKE_BINDING_STATE_SECRET") or "").strip()
    if not raw:
        raw = os.getenv("OPENAI_API_KEY", "")[:32] or "dev-insecure-wechat-binding-state"
    return raw.encode("utf-8")


def _pepper() -> bytes:
    p = (os.getenv("WECHAT_BINDING_PEPPER") or os.getenv("WECHAT_BINDING_STATE_SECRET") or "").strip()
    if not p:
        p = "dev-pepper-set-WECHAT_BINDING_PEPPER"
    return p.encode("utf-8")


def opaque_person_link_key(openid: str) -> str:
    """Opaque linkage key stored on case JSON (not reversible without pepper + openid)."""
    raw = f"{openid.strip()}".encode("utf-8")
    digest = hmac.new(_pepper(), raw, hashlib.sha256).hexdigest()
    return f"wx_{digest[:40]}"


def sign_state(session_id: str, client_id: str) -> str:
    payload = {
        "sid": (session_id or "").strip(),
        "cid": (client_id or "").strip() or "chen_kui",
        "exp": int(time.time()) + 900,
        "nonce": os.urandom(8).hex(),
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    b64 = base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")
    sig = hmac.new(_state_secret(), body, hashlib.sha256).hexdigest()[:32]
    return f"{b64}.{sig}"


def verify_state(token: str) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    b64, sig = token.rsplit(".", 1)
    if len(sig) != 32:
        return None
    pad = "=" * ((4 - len(b64) % 4) % 4)
    try:
        body = base64.urlsafe_b64decode(b64 + pad)
    except Exception:
        return None
    expect = hmac.new(_state_secret(), body, hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(expect, sig):
        return None
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return None
    if int(payload.get("exp") or 0) < int(time.time()):
        return None
    sid = str(payload.get("sid") or "").strip()
    if not sid:
        return None
    return {"session_id": sid, "client_id": str(payload.get("cid") or "").strip() or "chen_kui"}


def wechat_credentials_configured() -> bool:
    app_id = (os.getenv("WECHAT_APP_ID") or "").strip()
    secret = (os.getenv("WECHAT_APP_SECRET") or "").strip()
    return bool(app_id and secret)


def build_redirect_uri() -> str:
    raw = (os.getenv("WECHAT_BINDING_REDIRECT_URI") or "").strip()
    if raw:
        return raw
    base = (os.getenv("PUBLIC_API_BASE_URL") or os.getenv("API_PUBLIC_URL") or "").strip().rstrip("/")
    if base:
        return f"{base}/api/inbox/wechat/binding/callback"
    return "http://127.0.0.1:8001/api/inbox/wechat/binding/callback"


def build_authorize_url(state: str) -> str:
    app_id = (os.getenv("WECHAT_APP_ID") or "").strip()
    redirect_uri = build_redirect_uri()
    qs = urllib.parse.urlencode(
        {
            "appid": app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "snsapi_base",
            "state": state,
        }
    )
    return f"{_AUTH_URL}?{qs}#wechat_redirect"


async def exchange_code_for_openid(code: str) -> tuple[str | None, str | None]:
    """Returns (openid, error_message)."""
    app_id = (os.getenv("WECHAT_APP_ID") or "").strip()
    secret = (os.getenv("WECHAT_APP_SECRET") or "").strip()
    if not app_id or not secret:
        return None, "wechat_not_configured"
    params = {
        "appid": app_id,
        "secret": secret,
        "code": code.strip(),
        "grant_type": "authorization_code",
    }
    url = f"{_WECHAT_TOKEN_URL}?{urllib.parse.urlencode(params)}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url)
            data = r.json()
    except Exception as exc:
        logger.warning("WeChat token exchange failed: %s", exc)
        return None, "token_http_error"
    if data.get("errcode"):
        logger.warning("WeChat token error: %s", data)
        return None, str(data.get("errmsg") or "wechat_error")
    oid = str(data.get("openid") or "").strip()
    if not oid:
        return None, "no_openid"
    return oid, None


def simulate_allowed() -> bool:
    v = (os.getenv("WECHAT_BINDING_ALLOW_SIMULATE") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def frontend_return_base() -> str:
    raw = (os.getenv("UNIFIED_INTAKE_FRONTEND_ORIGIN") or "").strip().rstrip("/")
    if raw:
        return raw
    return "http://127.0.0.1:5173"


def build_frontend_return_url(query: dict[str, str]) -> str:
    base = frontend_return_base()
    path = "/workbench/unified-intake"
    q = urllib.parse.urlencode(query)
    return f"{base}{path}?{q}"
