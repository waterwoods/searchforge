"""
Server-derived client (tenant) boundary for Unified Intake Cases.

``client_id`` on a persisted case is the **ownership stamp** set at create time from
trusted server configuration (``CLIENT_ID`` env / deployment default). It is never
authoritative when supplied by a client header or request body field.

``X-Org-Id`` remains a separate office hint (see ``case_office_access``); it does not
replace ``client_id`` for tenant ownership.

Rollback: unset ``UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP``.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def resolve_server_client_id() -> str:
    """Return the deployment's authoritative client/tenant id (never from HTTP)."""

    from services.fiqa_api.inbox_triage.config_loader import get_active_client_id

    return get_active_client_id()


def case_client_enforcement_enabled() -> bool:
    raw = (os.getenv("UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP") or "").strip().lower()
    return raw in _TRUTHY


def client_list_strict_exclude_legacy_no_client() -> bool:
    """When true, list endpoint hides cases with empty client_id under enforcement."""

    raw = (os.getenv("UNIFIED_INTAKE_CLIENT_LIST_STRICT_NO_LEGACY") or "").strip().lower()
    return raw in _TRUTHY


def assert_case_client_access_allowed(request: Request | None, case: dict[str, Any]) -> None:
    """
    Enforce optional client boundary for a concrete case row.

    Raises HTTPException(403) when enforcement is on, the case is client-stamped, and the
    resolved server client does not match.
    """

    _ = request  # reserved for future signed-broker client scope
    if not case_client_enforcement_enabled():
        return
    owned = str(case.get("client_id") or "").strip()
    if not owned:
        return
    resolved = resolve_server_client_id()
    if owned != resolved:
        raise HTTPException(status_code=403, detail="case_client_mismatch_v1")


def case_visible_in_client_list(case: dict[str, Any], req_client: str) -> bool:
    stamp = str(case.get("client_id") or "").strip()
    if stamp:
        return stamp == req_client
    return not client_list_strict_exclude_legacy_no_client()


def client_ownership_posture_dict() -> dict[str, Any]:
    """Non-secret fragment for deployment-manifest / replay lineage."""

    strict_legacy = client_list_strict_exclude_legacy_no_client()
    return {
        "case_client_enforcement": "enabled" if case_client_enforcement_enabled() else "disabled",
        "client_ownership_field": "client_id",
        "client_ownership_semantics": "server_derived_from_client_id_env_at_case_create_v1",
        "client_ownership_never_trusted_from": "request_body_client_id_or_x_org_id_v1",
        "client_list_strict_no_legacy": strict_legacy,
        "rollback": "unset UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP",
    }
