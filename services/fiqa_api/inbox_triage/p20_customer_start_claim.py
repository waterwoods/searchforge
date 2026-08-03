"""P20 Customer Start Claim — thin facade over Capability 2 CreateClaim.

Does not implement a second CreateClaim. Server derives tenant/office and
calls P20CaseIntakeCommandService.create_claim(actor="customer").

P26G: after create, issue a signed resume token so the customer can open
Task Home and continue default intake without a broker Request More / QR.

P29B / P0 Identity Foundation: when session_id is a durable WeChat
person_link_key (wx_*), resolve→resume or create→bind Active Case.
Customer force_new never opens a second Active Case.
Production rejects anon-only create (durable identity required).
"""

from __future__ import annotations

import os
import re
from typing import Any

from services.fiqa_api.inbox_triage.mp_customer_identity import (
    bind_active_case,
    issue_resume_for_case,
    person_link_from_session_id,
    resolve_active_case_for_person_link,
    resolve_customer_identity_key,
)
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
    if outcome not in ("accepted", "replayed", "resumed"):
        return result
    case_id = str(result.get("case_id") or "").strip()
    if not case_id:
        return result
    if result.get("resume_token"):
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
    if outcome in ("accepted", "replayed", "resumed"):
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


def _resume_existing(case_id: str) -> dict[str, Any]:
    try:
        resume = issue_resume_for_case(case_id)
    except Exception:
        resume = {}
    return _attach_resume_token(
        {
            "outcome": "resumed",
            "case_id": case_id,
            "resume_token": resume.get("resume_token"),
            "resume_expires_at": resume.get("resume_expires_at"),
            "error_code": None,
        }
    )


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
    force_new: bool = False,
    policy_context_choice: str | None = None,
    selected_vehicle_ref: str | None = None,
    selected_vehicle_summary: str | None = None,
) -> dict[str, Any]:
    """Facade: Cap2 CreateClaim with actor=customer + resume token (P26G/P29B/P0).

    One Active Case (server invariant):
    - Resolve identity → if Active Case exists, always resume (never create second).
    - Customer force_new is ignored (compat only).
    - Production deployment requires durable wx_* identity; anon create rejected.
    """
    # force_new remains in the signature for client/API compat but never opens a
    # second Active Case (P30 / One Active Case Constitution).
    _ = bool(force_new)

    durable_link = person_link_from_session_id(session_id)
    identity_key = resolve_customer_identity_key(session_id)

    # Every customer create must carry a bindable identity (wx_* always;
    # anon-/p26h-/p35-* only when allow_prototype_anon_customer_create).
    if not identity_key:
        return {
            "outcome": "rejected",
            "error_code": "durable_identity_required",
            "case_id": None,
        }

    existing = resolve_active_case_for_person_link(identity_key)
    if existing:
        case_id = str(existing.get("case_id") or "").strip()
        if case_id:
            return _resume_existing(case_id)

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

    # Stamp durable WeChat link on the case only; prototype keys bind the index only.
    # Demo Invite overlay (if any) supplies presentation identity for Workbench only.
    demo_inputs: dict[str, Any] = {}
    try:
        from services.fiqa_api.inbox_triage.demo_invite import (
            DEMO_NAME,
            get_approved_scenario,
            peek_session_overlay,
        )

        overlay = peek_session_overlay(session_id)
        if overlay:
            entry = get_approved_scenario(str(overlay.get("scenario_id") or ""))
            if entry:
                demo_inputs = {
                    "customer_name": entry["customer_display_name"],
                    "primary_vehicle_summary": entry["vehicle_summary"],
                    "qa_label": f"演示·{entry['customer_display_name']}",
                    "demo_name": DEMO_NAME,
                    "is_test": True,
                }
                known_facts["primary_vehicle_summary"] = entry["vehicle_summary"]
                known_facts["qa_label"] = f"演示·{entry['customer_display_name']}"
    except Exception:
        demo_inputs = {}

    result = default_case_intake_service().create_claim(
        broker_id=actor_identity,
        office_id=office,
        tenant_id=tenant,
        command_id=command_id,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        actor="customer",
        inputs={
            "is_test": bool(is_test or demo_inputs.get("is_test")),
            "accident_description": description or None,
            "accident_datetime": datetime_value or None,
            "accident_location": location or None,
            "injury_status": injury or None,
            "known_facts": known_facts,
            "title": "Customer Claim intake" if not (is_test or demo_inputs) else "QA Customer Claim intake",
            "entry_channel": "mini_program",
            "identity_binding_state": "linked" if durable_link else "unbound",
            "person_link_key": durable_link,
            "person_link_source": "wechat" if durable_link else None,
            "person_link_confidence": 0.9 if durable_link else None,
            **demo_inputs,
        },
    )
    out = _attach_resume_token(result)
    case_id = str(out.get("case_id") or "").strip()
    if case_id and str(out.get("outcome") or "") in ("accepted", "replayed"):
        bind_active_case(identity_key, case_id)
        # Stage 2 — persist known-customer policy context choice (idempotent).
        choice = str(policy_context_choice or "").strip()
        if choice:
            try:
                from services.fiqa_api.inbox_triage.policy_context_confirm import (
                    confirm_policy_context_for_case,
                    lookup_from_session_overlay,
                )

                lookup = lookup_from_session_overlay(session_id)
                # Prefer demo-invite fixture even when overlay already consumed.
                if lookup is None or str(lookup.get("match_status") or "") in (
                    "LOOKUP_UNAVAILABLE",
                    "NOT_FOUND",
                ):
                    try:
                        from services.fiqa_api.inbox_triage.customer_lookup.facade import (
                            lookup_demo_invite_fixture,
                        )
                        from services.fiqa_api.inbox_triage.demo_invite import (
                            get_approved_scenario,
                            peek_session_overlay,
                        )

                        overlay = peek_session_overlay(session_id)
                        if overlay:
                            entry = get_approved_scenario(str(overlay.get("scenario_id") or ""))
                            if entry:
                                lookup = lookup_demo_invite_fixture(entry["mock_person_link_key"])
                    except Exception:
                        pass
                confirm_policy_context_for_case(
                    case_id,
                    lookup=lookup,
                    customer_choice=choice,
                    command_id=f"{command_id}:policy_context",
                    idempotency_key=f"{idempotency_key}:policy_context",
                    selected_vehicle_ref=selected_vehicle_ref,
                    selected_vehicle_summary=selected_vehicle_summary,
                )
            except Exception:
                # Never fail Start Claim because confirm side-effect failed;
                # customer can still upload insurance card (FALLBACK).
                pass
    return out
