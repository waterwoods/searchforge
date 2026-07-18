"""P20 Customer Start Claim — thin facade over Capability 2 CreateClaim.

Does not implement a second CreateClaim. Server derives tenant/office and
calls P20CaseIntakeCommandService.create_claim(actor="customer").

P26G: after create, issue a signed resume token so the customer can open
Task Home and continue default intake without a broker Request More / QR.
"""

from __future__ import annotations

import os
import re
from typing import Any

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    default_case_intake_service,
)
from services.fiqa_api.inbox_triage.p20_customer_launch import issue_customer_launch_token
from services.fiqa_api.security.case_client_access import resolve_server_client_id

_SESSION_SAFE = re.compile(r"[^a-zA-Z0-9_.:-]+")


def resolve_customer_start_claim_office_id() -> str | None:
    """Server-derived office stamp for customer-originated Cap2 drafts."""
    raw = (os.getenv("UNIFIED_INTAKE_CUSTOMER_START_CLAIM_OFFICE_ID") or "").strip()
    return raw[:256] or None


def normalize_customer_actor_identity(session_id: str | None) -> str:
    cleaned = _SESSION_SAFE.sub("", (session_id or "").strip())[:80]
    if cleaned:
        return f"customer:mp:{cleaned}"
    return "customer:mp:anonymous"


def _attach_resume_token(result: dict[str, Any]) -> dict[str, Any]:
    """Issue opaque resume token bound to case_id (never expose bare case_id)."""
    outcome = str(result.get("outcome") or "").strip()
    if outcome not in ("accepted", "replayed"):
        return result
    case_id = str(result.get("case_id") or "").strip()
    if not case_id:
        return result
    try:
        launch = issue_customer_launch_token(case_id=case_id)
    except Exception:
        return result
    out = dict(result)
    out["resume_token"] = launch.token
    out["resume_expires_at"] = launch.expires_at_iso
    return out


def customer_start_claim_response(result: dict[str, Any]) -> dict[str, Any]:
    """Customer-safe response — no case_id / versions / command internals."""
    outcome = str(result.get("outcome") or "").strip()
    if outcome in ("accepted", "replayed"):
        body: dict[str, Any] = {"ok": True, "outcome": outcome}
        resume = str(result.get("resume_token") or "").strip()
        if resume:
            body["resume_token"] = resume
            expires = str(result.get("resume_expires_at") or "").strip()
            if expires:
                body["resume_expires_at"] = expires
        return body
    return {
        "ok": False,
        "outcome": outcome or "rejected",
        "error_code": str(result.get("error_code") or "create_claim_failed"),
    }


def start_customer_claim(
    *,
    command_id: str,
    idempotency_key: str,
    correlation_id: str | None = None,
    session_id: str | None = None,
    accident_description: str | None = None,
    accident_datetime: str | None = None,
    accident_location: str | None = None,
    injury_status: str | None = None,
    is_test: bool = False,
    office_id: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Facade: Cap2 CreateClaim with actor=customer + resume token (P26G)."""
    actor_identity = normalize_customer_actor_identity(session_id)
    office = (office_id if office_id is not None else resolve_customer_start_claim_office_id())
    tenant = tenant_id if tenant_id is not None else (resolve_server_client_id() or None)
    description = str(accident_description or "").strip()[:2000]
    datetime_value = str(accident_datetime or "").strip()[:120]
    location = str(accident_location or "").strip()[:500]
    injury = str(injury_status or "").strip().lower()
    if injury not in ("yes", "no", "unknown"):
        injury = ""
    known_facts: dict[str, Any] = {}
    if description:
        known_facts["accident_description"] = description
    if datetime_value:
        known_facts["accident_datetime"] = datetime_value
    if location:
        known_facts["accident_location"] = location
    if injury:
        known_facts["injury_status"] = injury
        known_facts["anyone_injured"] = injury
    result = default_case_intake_service().create_claim(
        broker_id=actor_identity,
        office_id=office,
        tenant_id=tenant,
        command_id=command_id,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        actor="customer",
        inputs={
            "is_test": bool(is_test),
            "accident_description": description or None,
            "accident_datetime": datetime_value or None,
            "accident_location": location or None,
            "injury_status": injury or None,
            "known_facts": known_facts,
            "title": "Customer Claim intake" if not is_test else "QA Customer Claim intake",
        },
    )
    return _attach_resume_token(result)
