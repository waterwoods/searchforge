"""
HTTP request lineage — correlation IDs only.

``X-Org-Id`` on triage routes is a **client assertion**, not a cryptographic tenant
boundary. Server-side tenant authority belongs in AUTH_MODEL_V1 (API keys, JWTs, mTLS),
not headers alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass(frozen=True)
class HttpRequestLineage:
    """Per-request trace handle (from RequestIDMiddleware)."""

    request_trace_id: str


def http_request_lineage(request: Request) -> HttpRequestLineage:
    rid = getattr(request.state, "request_id", None)
    return HttpRequestLineage(request_trace_id=str(rid or ""))


@dataclass(frozen=True)
class IntakeTenantTruth:
    """Runtime-visible tenant posture for one HTTP request (honesty layer, not IAM).

    ``tenant_id_authoritative`` is reserved for future server-issued tenant identity
    (JWT/API key scope). Until then it remains ``None`` everywhere.
    """

    tenant_id_authoritative: str | None
    client_asserted_org_id: str | None
    semantics: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "tenant_id_authoritative": self.tenant_id_authoritative,
            "client_asserted_org_id": self.client_asserted_org_id,
            "semantics": self.semantics,
        }


def intake_tenant_truth(request: Request) -> IntakeTenantTruth:
    oid = getattr(request.state, "client_asserted_org_id", None)
    tid = getattr(request.state, "tenant_id_authoritative", None)
    return IntakeTenantTruth(
        tenant_id_authoritative=tid if tid is None or isinstance(tid, str) else None,
        client_asserted_org_id=oid if oid is None or isinstance(oid, str) else None,
        semantics="client_asserted_org_id_not_tenant_authority_v1",
    )


class IntakeClientAssertionMiddleware(BaseHTTPMiddleware):
    """Capture ``X-Org-Id`` into ``request.state`` for downstream honesty APIs.

    Does **not** authenticate or authorize — only normalizes and stores the client
    assertion so routes can emit consistent ``tenant_truth`` without re-parsing headers.

    Register **before** ``RequestIDMiddleware`` in ``app.add_middleware`` so Starlette wraps
    RequestID outside this middleware: inbound order is ``… → RequestID → this → …``.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        raw = (request.headers.get("X-Org-Id") or "").strip()[:256] or None
        request.state.client_asserted_org_id = raw
        request.state.tenant_id_authoritative = None
        return await call_next(request)
