"""
Optional shared-secret gate for operator/support export HTTP surface.

Runtime truth:
- When ``UNIFIED_INTAKE_SUPPORT_API_KEY`` is unset or empty, ``GET /api/inbox/support/*``
  remains anonymously reachable (legacy pilot / local demo).
- When set, callers must send the same value via ``X-Unified-Intake-Support-Key`` or
  ``Authorization: Bearer <key>``.

This is **not** multi-tenant IAM — only reduces accidental internet-wide reconnaissance
when operators configure a secret.
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from fastapi import HTTPException, Request

# Minimum recommended length for operator-shared secrets (not cryptographic policy).
_SUPPORT_KEY_RECOMMENDED_MIN_LEN = 24


def support_export_secret_configured() -> bool:
    return bool((os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip())


def assert_support_export_authorized(request: Request) -> None:
    expected = (os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if not expected:
        return
    hdr = (request.headers.get("X-Unified-Intake-Support-Key") or "").strip()
    auth = (request.headers.get("Authorization") or "").strip()
    bearer = ""
    if auth.lower().startswith("bearer "):
        bearer = auth[7:].strip()
    candidate = hdr or bearer
    if not candidate or not secrets.compare_digest(candidate, expected):
        raise HTTPException(status_code=401, detail="support_export_unauthorized")


def support_export_auth_posture_dict() -> dict[str, Any]:
    """Stable JSON fragment for health + deployment-manifest (no secrets)."""

    if support_export_secret_configured():
        surface = "api_key_required"
        notes = (
            "Support export routes require UNIFIED_INTAKE_SUPPORT_API_KEY via "
            "X-Unified-Intake-Support-Key or Authorization: Bearer."
        )
    else:
        surface = "anonymous_ok"
        notes = (
            "Support export routes have no shared-secret gate (pilot default). "
            "Set UNIFIED_INTAKE_SUPPORT_API_KEY to require an operator key."
        )
    out: dict[str, Any] = {
        "support_export_surface": surface,
        "support_export_notes": notes,
        "x_org_id_semantics": "client_asserted_untrusted_not_tenant_authority",
    }
    key = (os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if key and len(key) < _SUPPORT_KEY_RECOMMENDED_MIN_LEN:
        out["support_operator_warnings"] = [
            "support_api_key_shorter_than_recommended_v1",
        ]
    # Runtime honesty: prod-profile without a support secret is a reconnaissance risk.
    try:
        from services.fiqa_api.db.service_record_settings import is_production_mode

        if is_production_mode() and not support_export_secret_configured():
            out["production_support_export_risk"] = (
                "production_like_runtime_without_support_key_v1"
            )
    except Exception:
        pass
    return out
