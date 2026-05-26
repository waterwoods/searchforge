"""
Minimal office ownership hints for Unified Intake (not IAM).

``asserted_org_id`` on a persisted case is the **office ownership hint** captured at
case creation from ``X-Org-Id`` (client assertion). It is not cryptographic tenant
authority.

When ``UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP`` is enabled, HTTP routes that read
or mutate a single case require a matching ``X-Org-Id`` for cases that already carry
``asserted_org_id``. Legacy cases without ``asserted_org_id`` remain reachable (demo /
migration). ``GET /api/inbox/cases`` becomes office-scoped: ``X-Org-Id`` is required and
the list is filtered.

Rollback: unset ``UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP``.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def case_office_enforcement_enabled() -> bool:
    raw = (os.getenv("UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP") or "").strip().lower()
    return raw in _TRUTHY


def office_list_strict_exclude_legacy_no_org() -> bool:
    """When true, list endpoint hides cases with empty asserted_org_id under enforcement."""

    raw = (os.getenv("UNIFIED_INTAKE_OFFICE_LIST_STRICT_NO_LEGACY") or "").strip().lower()
    return raw in _TRUTHY


def client_asserted_office_id(request: Request | None) -> str | None:
    if request is None:
        return None
    oid = getattr(request.state, "client_asserted_org_id", None)
    if isinstance(oid, str):
        s = oid.strip()[:256]
        return s or None
    return None


def assert_case_office_access_allowed(request: Request | None, case: dict[str, Any]) -> None:
    """
    Enforce optional office boundary for a concrete case row.

    Raises HTTPException(403) when enforcement is on, the case is office-stamped, and the
    request org is missing or mismatched.
    """

    if not case_office_enforcement_enabled():
        return
    owned = str(case.get("asserted_org_id") or "").strip()
    if not owned:
        return
    req_org = client_asserted_office_id(request)
    if not req_org:
        raise HTTPException(status_code=403, detail="case_office_assertion_required_v1")
    if owned != req_org:
        raise HTTPException(status_code=403, detail="case_office_mismatch_v1")


def case_visible_in_office_list(case: dict[str, Any], req_org: str) -> bool:
    stamp = str(case.get("asserted_org_id") or "").strip()
    if stamp:
        return stamp == req_org
    return not office_list_strict_exclude_legacy_no_org()


def office_ownership_posture_dict() -> dict[str, Any]:
    """Non-secret fragment for deployment-manifest / replay lineage."""

    strict_legacy = office_list_strict_exclude_legacy_no_org()
    return {
        "case_office_enforcement": "enabled" if case_office_enforcement_enabled() else "disabled",
        "office_ownership_field": "asserted_org_id",
        "persistence_office_owner_column": "office_owner_org_id",
        "persistence_office_owner_semantics": (
            "nullable_indexed_mirror_of_asserted_org_id_postgres_service_records_v1"
        ),
        "office_ownership_semantics": (
            "client_asserted_org_from_x_org_id_at_case_create_not_cryptographic_tenant_v1"
        ),
        "office_list_strict_no_legacy": strict_legacy,
        "binding_candidates_when_x_org_id_present": (
            "filtered_like_case_visible_in_office_list_tri_recent_stub_path_v1"
        ),
        "session_trim_preserves_asserted_org_id": (
            "save_session_binding_after_case_created_carries_org_hint_v1"
        ),
        "rollback": "unset UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP",
    }
