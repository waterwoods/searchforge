"""
Minimal HMAC-signed broker token (pilot identity sketch, not enterprise IAM).

Semantics:
- When ``UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET`` is set, an optional
  ``X-Unified-Intake-Broker-Token`` header can carry a server-verifiable blob.
- Verified claims are **stronger than a bare ``X-Org-Id``** (anyone can forge the header)
  but are **not** ``tenant_id_authoritative`` — still one shared secret per deployment;
  rotation is redeploy-side; revocation is TTL + secret rotation only (no CRL).

Token shape: ``msbt1.<urlsafe_b64_payload_json>.<urlsafe_b64_hmac_sha256>``

Rollback: unset ``UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET`` (verification becomes a no-op).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Final

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

MODEL_VERSION: Final[str] = "minimal_signed_broker_token_v1"
TOKEN_PREFIX: Final[str] = "msbt1."
_ENV_SECRET: Final[str] = "UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET"
_ENV_DEPLOY_BINDING: Final[str] = "UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING"
_ENV_CLOCK_SKEW: Final[str] = "UNIFIED_INTAKE_BROKER_TOKEN_MAX_CLOCK_SKEW_SEC"
_HEADER_NAME: Final[str] = "X-Unified-Intake-Broker-Token"


def broker_token_hmac_secret_configured() -> bool:
    return bool((os.getenv(_ENV_SECRET) or "").strip())


def effective_deploy_binding() -> str:
    """
    Short deployment label bound into every verified token.

    Prefer explicit ``UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING``; else first commit
    env label from deployment_identity_truth; else ``unbound_v1``.
    """

    raw = (os.getenv(_ENV_DEPLOY_BINDING) or "").strip()
    if raw:
        return raw[:128]
    try:
        from services.fiqa_api.deployment_profile import deployment_identity_truth

        dit = deployment_identity_truth()
        sha = dit.get("commit_sha_from_env")
        if isinstance(sha, str) and sha.strip():
            return sha.strip()[:64]
    except Exception:
        logger.debug("effective_deploy_binding: fallback", exc_info=True)
    return "unbound_v1"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(seg: str) -> bytes:
    pad = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode((seg + pad).encode("ascii"))


def _canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    """Stable JSON for signing (sorted keys, no whitespace)."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def issue_minimal_broker_token(
    *,
    office_slug: str | None,
    ttl_seconds: int = 3600,
    deploy_binding: str | None = None,
    now: float | None = None,
    jti: str | None = None,
) -> str:
    """
    Issue a token (operators / fixture tests). Requires ``UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET``.
    """

    secret = (os.getenv(_ENV_SECRET) or "").strip().encode("utf-8")
    if not secret:
        raise RuntimeError("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET is not set")
    t = time.time() if now is None else float(now)
    iat = int(t)
    exp = iat + int(ttl_seconds)
    bind = (deploy_binding or effective_deploy_binding()).strip()[:128]
    tid = (jti or str(uuid.uuid4())).strip()[:128]
    payload: dict[str, Any] = {
        "v": 1,
        "iat": iat,
        "exp": exp,
        "deploy_binding": bind,
        "jti": tid,
        "model": MODEL_VERSION,
    }
    if office_slug and str(office_slug).strip():
        payload["office_slug"] = str(office_slug).strip()[:256]
    body = _canonical_payload_bytes(payload)
    payload_b64 = _b64url_encode(body)
    sig = hmac.new(secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{TOKEN_PREFIX}{payload_b64}.{_b64url_encode(sig)}"


@dataclass(frozen=True)
class VerifiedMinimalBrokerToken:
    """Parsed verified claims (never implies IAM tenancy)."""

    office_slug: str | None
    deploy_binding: str
    jti: str
    iat: int
    exp: int
    model: str


def verify_minimal_broker_token(token: str, *, now: float | None = None) -> VerifiedMinimalBrokerToken | None:
    """Return claims if signature, TTL, and deploy binding match; else None."""

    raw = (token or "").strip()
    if not raw.startswith(TOKEN_PREFIX):
        return None
    rest = raw[len(TOKEN_PREFIX) :]
    parts = rest.split(".")
    if len(parts) != 2:
        return None
    payload_b64, sig_b64 = parts
    secret = (os.getenv(_ENV_SECRET) or "").strip().encode("utf-8")
    if not secret:
        return None
    try:
        expect_sig = hmac.new(secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
        got_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expect_sig, got_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
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
    skew_raw = (os.getenv(_ENV_CLOCK_SKEW) or "").strip()
    try:
        skew = max(0, int(skew_raw)) if skew_raw else 120
    except ValueError:
        skew = 120
    t = time.time() if now is None else float(now)
    if t > float(exp + skew) or t < float(iat - skew):
        return None
    bind = str(payload.get("deploy_binding") or "").strip()
    if bind != effective_deploy_binding():
        return None
    jti = str(payload.get("jti") or "").strip()
    if not jti:
        return None
    office = payload.get("office_slug")
    office_slug: str | None
    if isinstance(office, str) and office.strip():
        office_slug = office.strip()[:256]
    else:
        office_slug = None
    return VerifiedMinimalBrokerToken(
        office_slug=office_slug,
        deploy_binding=bind,
        jti=jti[:128],
        iat=iat,
        exp=exp,
        model=str(payload.get("model") or MODEL_VERSION),
    )


def minimal_broker_token_posture_dict() -> dict[str, Any]:
    """Non-secret fragment for health / deployment-manifest / replay lineage."""

    return {
        "model_version": MODEL_VERSION,
        "semantics": (
            "hmac_sha256_optional_header_not_tenant_authority_shared_secret_per_deploy_v1"
        ),
        "verification_configured": broker_token_hmac_secret_configured(),
        "deploy_binding_effective": effective_deploy_binding(),
        "header_name": _HEADER_NAME,
        "env_secret": _ENV_SECRET,
        "env_deploy_binding": _ENV_DEPLOY_BINDING,
        "revocation_story": "rotate_hmac_secret_or_wait_ttl_no_crl_v1",
        "rollback": f"unset {_ENV_SECRET}",
    }


def minimal_broker_token_request_truth(request: Request) -> dict[str, Any]:
    """Per-request honesty fragment (set by middleware)."""

    v = getattr(request.state, "minimal_broker_token_verified", None)
    err = getattr(request.state, "minimal_broker_token_error", None)
    hdr_office_vs_asserted = getattr(
        request.state, "minimal_broker_token_office_vs_x_org_id", None
    )
    base: dict[str, Any] = {
        "semantics": "minimal_signed_broker_token_request_truth_v1",
        "tenant_id_authoritative_remains_null": True,
    }
    if isinstance(v, VerifiedMinimalBrokerToken):
        base.update(
            {
                "verified": True,
                "token_trace_id": v.jti,
                "token_office_slug": v.office_slug,
                "token_deploy_binding": v.deploy_binding,
                "token_exp": v.exp,
            }
        )
    else:
        base["verified"] = False
    if isinstance(err, str) and err:
        base["verification_note"] = err
    if isinstance(hdr_office_vs_asserted, str) and hdr_office_vs_asserted:
        base["office_claim_vs_x_org_id"] = hdr_office_vs_asserted
    return base


class MinimalBrokerTokenMiddleware(BaseHTTPMiddleware):
    """
    Parse optional broker token after ``X-Org-Id`` is stored (register **inside**
    ``IntakeClientAssertionMiddleware``).
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        token = (request.headers.get(_HEADER_NAME) or "").strip()
        if not token:
            return await call_next(request)

        if not broker_token_hmac_secret_configured():
            request.state.minimal_broker_token_verified = None
            request.state.minimal_broker_token_error = "verification_disabled_hmac_secret_unset_v1"
            request.state.minimal_broker_token_office_vs_x_org_id = None
            return await call_next(request)

        verified = verify_minimal_broker_token(token)
        if verified is None:
            request.state.minimal_broker_token_verified = None
            request.state.minimal_broker_token_error = "invalid_or_expired_or_deploy_mismatch_v1"
            request.state.minimal_broker_token_office_vs_x_org_id = None
        else:
            request.state.minimal_broker_token_verified = verified
            request.state.minimal_broker_token_error = None
            asserted = getattr(request.state, "client_asserted_org_id", None)
            if verified.office_slug:
                ao = (asserted or "").strip() if isinstance(asserted, str) else ""
                if not ao:
                    request.state.minimal_broker_token_office_vs_x_org_id = (
                        "token_office_present_x_org_absent_v1"
                    )
                elif ao != verified.office_slug:
                    request.state.minimal_broker_token_office_vs_x_org_id = "mismatch_v1"
                else:
                    request.state.minimal_broker_token_office_vs_x_org_id = "match_v1"
            else:
                request.state.minimal_broker_token_office_vs_x_org_id = "token_office_absent_v1"

        return await call_next(request)
