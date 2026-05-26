"""
Minimal pilot middleware: triage POST rate limit + office-expectation hint header.

Rollback:
- ``UNIFIED_INTAKE_TRIAGE_POST_MAX_PER_MINUTE_PER_IP``: unset or ``0`` disables rate limit.
- Office expectation headers: unset ``UNIFIED_INTAKE_EXPECTED_OFFICE_SLUGS``.
"""

from __future__ import annotations

import collections
import logging
import os
import threading
import time
from typing import Final

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from services.fiqa_api.security.token_scope_posture import office_expectation_header_value

logger = logging.getLogger(__name__)

_TRIAGE_PATH: Final[str] = "/api/inbox/triage"
_RATE_ENV: Final[str] = "UNIFIED_INTAKE_TRIAGE_POST_MAX_PER_MINUTE_PER_IP"
_WINDOW_SEC: Final[float] = 60.0

_store: dict[str, collections.deque[float]] = {}
_store_lock = threading.Lock()


def _triage_rate_limit_per_minute() -> int:
    raw = (os.getenv(_RATE_ENV) or "").strip()
    if not raw:
        return 0
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def _client_ip(request: Request) -> str:
    fwd = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if fwd:
        return fwd[:128]
    try:
        if request.client and request.client.host:
            return str(request.client.host)[:128]
    except Exception:
        pass
    return "unknown"


def _rate_limited(key: str, limit: int) -> bool:
    now = time.monotonic()
    cutoff = now - _WINDOW_SEC
    with _store_lock:
        dq = _store.setdefault(key, collections.deque())
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= limit:
            return True
        dq.append(now)
    return False


class TriagePostRateLimitMiddleware(BaseHTTPMiddleware):
    """Optional sliding-window limit per client IP for POST /api/inbox/triage only."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.method != "POST" or (request.url.path or "") != _TRIAGE_PATH:
            return await call_next(request)
        limit = _triage_rate_limit_per_minute()
        if limit <= 0:
            return await call_next(request)
        ip = _client_ip(request)
        if _rate_limited(f"triage:{ip}", limit):
            logger.warning(
                "triage_post_rate_limited_v1 ip_prefix=%s limit_per_minute=%s",
                ip[:16],
                limit,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "triage_post_rate_limited_v1",
                    "semantics": "coarse_per_ip_not_authenticated_actor_v1",
                },
            )
        return await call_next(request)


class IntakeOfficeExpectationHintMiddleware(BaseHTTPMiddleware):
    """Adds honest office-slug expectation hint header after POST /api/inbox/triage."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response = await call_next(request)
        if request.method != "POST" or (request.url.path or "") != _TRIAGE_PATH:
            return response
        val = office_expectation_header_value(getattr(request.state, "client_asserted_org_id", None))
        if val:
            response.headers["X-Unified-Intake-Office-Expectation"] = val
        return response
