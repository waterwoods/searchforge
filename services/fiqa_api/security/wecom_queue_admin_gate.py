"""
Shared-secret gate for WeCom queue admin HTTP surface (Q0.8.1).

When ``WECOM_QUEUE_ADMIN_TOKEN`` is unset or empty, admin routes fail closed (503).
When set, callers must send the same value via ``X-Admin-Token`` or
``Authorization: Bearer <token>``.
"""

from __future__ import annotations

import os
import secrets

from fastapi import HTTPException, Request


def wecom_queue_admin_token_configured() -> bool:
    return bool((os.getenv("WECOM_QUEUE_ADMIN_TOKEN") or "").strip())


def assert_wecom_queue_admin_authorized(request: Request) -> None:
    expected = (os.getenv("WECOM_QUEUE_ADMIN_TOKEN") or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail=(
                "wecom_queue_admin_not_configured_v1: set WECOM_QUEUE_ADMIN_TOKEN "
                "on Cloud Run before using /api/admin/wecom/queues/*"
            ),
        )
    hdr = (request.headers.get("X-Admin-Token") or "").strip()
    auth = (request.headers.get("Authorization") or "").strip()
    bearer = ""
    if auth.lower().startswith("bearer "):
        bearer = auth[7:].strip()
    candidate = hdr or bearer
    if not candidate or not secrets.compare_digest(candidate, expected):
        raise HTTPException(status_code=401, detail="wecom_queue_admin_unauthorized")
