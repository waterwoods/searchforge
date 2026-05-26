"""
Optional shared-secret perimeter for ``/api/inbox/*`` (excluding ``/api/inbox/support/*``).

Runtime truth:
- When ``UNIFIED_INTAKE_INTAKE_API_KEY`` is unset or empty, inbox HTTP routes behave as today
  (open intake surface — demo / legacy pilot).
- When set, every request whose path starts with ``/api/inbox/`` **except** support export paths
  and the WeChat OAuth callback must present the same value via ``X-Unified-Intake-Api-Key`` or
  ``Authorization: Bearer <key>``.

This is **not** broker IAM — only a coarse deployment perimeter so an exposed URL cannot be
drive-by scraped or scripted without a configured operator secret.

Rollback: unset ``UNIFIED_INTAKE_INTAKE_API_KEY``.
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

_INTAKE_KEY_RECOMMENDED_MIN_LEN = 24


def intake_api_secret_configured() -> bool:
    return bool((os.getenv("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip())


def assert_intake_api_authorized(request: Request) -> None:
    expected = (os.getenv("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    if not expected:
        return
    hdr = (request.headers.get("X-Unified-Intake-Api-Key") or "").strip()
    auth = (request.headers.get("Authorization") or "").strip()
    bearer = ""
    if auth.lower().startswith("bearer "):
        bearer = auth[7:].strip()
    candidate = hdr or bearer
    if not candidate or not secrets.compare_digest(candidate, expected):
        raise HTTPException(status_code=401, detail="intake_api_unauthorized")


def intake_api_auth_posture_dict() -> dict[str, Any]:
    """Stable JSON fragment for health + deployment-manifest (no secrets)."""

    if intake_api_secret_configured():
        surface = "api_key_required"
        notes = (
            "Inbox routes require UNIFIED_INTAKE_INTAKE_API_KEY via "
            "X-Unified-Intake-Api-Key or Authorization: Bearer (support paths use the support key; "
            "WeChat GET /wechat/binding/callback is exempt for OAuth redirects)."
        )
    else:
        surface = "anonymous_ok"
        notes = (
            "Inbox HTTP surface has no shared-secret perimeter (demo default). "
            "Set UNIFIED_INTAKE_INTAKE_API_KEY to require an operator secret."
        )
    out: dict[str, Any] = {
        "intake_http_surface": surface,
        "intake_http_notes": notes,
    }
    key = (os.getenv("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    if key and len(key) < _INTAKE_KEY_RECOMMENDED_MIN_LEN:
        out["intake_operator_warnings"] = [
            "intake_api_key_shorter_than_recommended_v1",
        ]
    try:
        from services.fiqa_api.db.service_record_settings import is_production_mode

        if is_production_mode() and not intake_api_secret_configured():
            out["production_intake_perimeter_risk"] = (
                "production_like_runtime_without_intake_api_key_v1"
            )
    except Exception:
        pass
    try:
        from services.fiqa_api.security.token_scope_posture import token_scope_registry_dict

        out["pilot_token_scope_registry"] = token_scope_registry_dict()
    except Exception:
        pass
    try:
        from services.fiqa_api.security.minimal_signed_broker_token import (
            minimal_broker_token_posture_dict,
        )

        out["minimal_signed_broker_token"] = minimal_broker_token_posture_dict()
    except Exception:
        pass
    return out


_WECHAT_OAUTH_CALLBACK_PATH = "/api/inbox/wechat/binding/callback"


class IntakeApiPerimeterMiddleware(BaseHTTPMiddleware):
    """Enforce optional intake shared secret for /api/inbox (excluding /support + OAuth callback)."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path or ""
        method = (request.method or "").upper()
        if not path.startswith("/api/inbox"):
            return await call_next(request)
        if path.startswith("/api/inbox/support/"):
            return await call_next(request)
        if path == _WECHAT_OAUTH_CALLBACK_PATH:
            return await call_next(request)
        if method == "OPTIONS":
            return await call_next(request)
        try:
            assert_intake_api_authorized(request)
        except HTTPException as exc:
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return await call_next(request)
