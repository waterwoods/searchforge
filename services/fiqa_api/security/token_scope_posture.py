"""
Pilot-scale token / office **labels** (not IAM).

Exposes optional env-configured hints for support manifest and response headers.
These do **not** bind cryptographic broker identity: one shared intake key can still
serve many humans; expected office slugs are an operator checklist, not proof of caller.
"""

from __future__ import annotations

import os
from typing import Any

# Bumped in lockstep with manifest when new keys are added (operator visibility only).
TOKEN_SCOPE_REGISTRY_VERSION: str = "pilot_token_scope_registry_v1"

_EXPECTED_OFFICE_SLUGS_ENV: str = "UNIFIED_INTAKE_EXPECTED_OFFICE_SLUGS"
_BROKER_LABEL_ENV: str = "UNIFIED_INTAKE_DEPLOY_BROKER_LABEL"


def _parse_slug_list(raw: str) -> frozenset[str]:
    out: set[str] = set()
    for part in (raw or "").split(","):
        s = part.strip()[:256]
        if s:
            out.add(s)
    return frozenset(out)


def expected_office_slugs() -> frozenset[str]:
    return _parse_slug_list(os.getenv(_EXPECTED_OFFICE_SLUGS_ENV) or "")


def deploy_broker_label() -> str | None:
    s = (os.getenv(_BROKER_LABEL_ENV) or "").strip()[:128]
    return s or None


def office_expectation_configured() -> bool:
    return len(expected_office_slugs()) > 0


def office_expectation_header_value(client_asserted_org_id: str | None) -> str | None:
    """
    Value for ``X-Unified-Intake-Office-Expectation`` on POST /api/inbox/triage.

    Returns None when no expectation list is configured (no header).
    """

    expected = expected_office_slugs()
    if not expected:
        return None
    oid = (client_asserted_org_id or "").strip()
    if not oid:
        return "absent_v1"
    if oid in expected:
        return "match_v1"
    return "mismatch_v1"


def token_scope_registry_dict() -> dict[str, Any]:
    """Non-secret fragment for /health, deployment-manifest, intake perimeter JSON."""

    slugs = expected_office_slugs()
    return {
        "registry_version": TOKEN_SCOPE_REGISTRY_VERSION,
        "semantics": (
            "env_configured_office_slug_expectation_list_not_caller_proof_not_iam_v1"
        ),
        "deploy_broker_label": deploy_broker_label(),
        "expected_office_slug_count": len(slugs),
        "expected_office_slugs": sorted(slugs),
        "env_expected_office_slugs": _EXPECTED_OFFICE_SLUGS_ENV,
        "env_deploy_broker_label": _BROKER_LABEL_ENV,
        "rollback": f"unset {_EXPECTED_OFFICE_SLUGS_ENV} and {_BROKER_LABEL_ENV}",
    }


def token_scope_operator_warnings() -> list[str]:
    """Stable codes folded into deployment_operator_warnings()."""

    warnings: list[str] = []
    if not office_expectation_configured():
        return warnings
    try:
        from services.fiqa_api.security.intake_api_gate import intake_api_secret_configured
        from services.fiqa_api.db.service_record_settings import is_production_mode

        if is_production_mode() and not intake_api_secret_configured():
            warnings.append(
                "office_slug_expectation_configured_without_intake_api_key_in_production_like_v1"
            )
    except Exception:
        pass
    return warnings
