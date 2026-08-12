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

import logging
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

logger = logging.getLogger(__name__)

_SESSION_SAFE = re.compile(r"[^a-zA-Z0-9_.:-]+")

# Bounded, customer-safe codes for post-CreateClaim enrichment that did not land.
# CreateClaim itself stays authoritative and durable when any of these appear.
WARNING_POLICY_CONTEXT_UNCONFIRMED = "policy_context_not_confirmed"
WARNING_ACCIDENT_STORY_UNCONFIRMED = "accident_story_not_confirmed"
WARNING_RESUME_TOKEN_UNAVAILABLE = "resume_token_unavailable"

SIDE_EFFECT_STATUS_SKIPPED = "skipped"
SIDE_EFFECT_STATUS_CONFIRMED = "confirmed"
SIDE_EFFECT_STATUS_FAILED = "failed"

_POLICY_CONTEXT_SUCCESS_OUTCOMES = ("accepted", "replayed", "already_confirmed")


def resolve_customer_start_claim_office_id() -> str | None:
    """Server-derived office stamp for customer-originated Cap2 drafts."""
    raw = (os.getenv("UNIFIED_INTAKE_CUSTOMER_START_CLAIM_OFFICE_ID") or "").strip()
    return raw[:256] or None


def normalize_customer_actor_identity(session_id: str | None) -> str:
    cleaned = _SESSION_SAFE.sub("", (session_id or "").strip())[:80]
    if cleaned:
        return f"customer:mp:{cleaned}"
    return "customer:mp:anonymous"


def _add_warning(result: dict[str, Any], code: str) -> None:
    """Record one bounded side-effect warning on the internal result."""
    warnings = [str(w) for w in (result.get("side_effect_warnings") or []) if str(w).strip()]
    if code not in warnings:
        warnings.append(code)
    result["side_effect_warnings"] = warnings


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
    out = dict(result)
    try:
        launch = issue_customer_launch_token(case_id=case_id)
    except Exception as exc:
        # Claim exists but the customer has no continuation handle — say so.
        logger.warning("start_claim resume token unavailable case=%s: %s", case_id, exc)
        _add_warning(out, WARNING_RESUME_TOKEN_UNAVAILABLE)
        return out
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
        # Claim is durable, but enrichment did not fully land: never look more
        # complete than the case really is.
        warnings = [str(w) for w in (result.get("side_effect_warnings") or []) if str(w).strip()]
        if warnings:
            body["warnings"] = warnings
            body["degraded"] = True
        return body
    return {
        "ok": False,
        "outcome": outcome or "rejected",
        "error_code": str(result.get("error_code") or "create_claim_failed"),
    }


def _record_side_effect_failure_signal(
    case_id: str,
    *,
    command_id: str,
    warnings: list[str],
    side_effects: dict[str, str],
) -> None:
    """Leave a durable, idempotent support signal on the case timeline.

    Best effort: the honest response warnings and the log line stand on their own
    if the case store is the thing that is broken.
    """
    try:
        from services.fiqa_api.inbox_triage.case_store import (
            append_claim_timeline_event,
            build_claim_timeline_event,
        )

        append_claim_timeline_event(
            case_id,
            build_claim_timeline_event(
                event_type="start_claim_side_effect_failed",
                source_channel="mini_program",
                actor="system",
                message_id=f"start_claim_side_effect:{str(command_id or '').strip()}"[:200],
                text="开案已成功保存，部分补充信息未写入，需人工检查",
                metadata={
                    "source": "customer_start_claim",
                    "command_id": str(command_id or "").strip(),
                    "warnings": list(warnings),
                    "side_effects": dict(side_effects),
                },
            ),
        )
    except Exception as exc:
        logger.warning(
            "start_claim side effect signal not recorded case=%s: %s", case_id, exc
        )


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
    ai_story_confirmed: bool = False,
    ai_story_proposal: dict[str, Any] | None = None,
    ai_story_customer_edits: dict[str, Any] | None = None,
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
    # Stage 2 isolated demo overlay uses a QA namespaced key so Start Claim does
    # not resume a prior Stage 1 case bound to the real wx person_link.
    try:
        from services.fiqa_api.inbox_triage.demo_invite import effective_customer_identity_key

        identity_key = effective_customer_identity_key(session_id) or resolve_customer_identity_key(
            session_id
        )
    except Exception:
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
            out = _resume_existing(case_id)
            try:
                from services.fiqa_api.inbox_triage.case_activity_events import (
                    record_customer_intake_opened,
                    safe_record,
                )

                safe_record(
                    record_customer_intake_opened,
                    case_id,
                    source_surface="mini_program",
                    session_id=session_id,
                    meta={"command_type": "start_claim_resume"},
                )
            except Exception:
                pass
            return out

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
            # Bind case metadata to the effective identity (isolated key when
            # Stage 2 phone overlay is active) so One Active Case stays per-key.
            "identity_binding_state": "linked" if identity_key else "unbound",
            "person_link_key": identity_key,
            "person_link_source": "wechat" if (durable_link or identity_key) else None,
            "person_link_confidence": 0.9 if identity_key else None,
            **demo_inputs,
        },
    )
    out = _attach_resume_token(result)
    case_id = str(out.get("case_id") or "").strip()
    if case_id and str(out.get("outcome") or "") in ("accepted", "replayed"):
        bind_active_case(identity_key, case_id)
        side_effects: dict[str, str] = {}
        # Stage 2 — persist known-customer policy context choice (idempotent).
        choice = str(policy_context_choice or "").strip()
        if not choice:
            side_effects["policy_context"] = SIDE_EFFECT_STATUS_SKIPPED
        else:
            status = SIDE_EFFECT_STATUS_FAILED
            failure = ""
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
                confirmed = confirm_policy_context_for_case(
                    case_id,
                    lookup=lookup,
                    customer_choice=choice,
                    command_id=f"{command_id}:policy_context",
                    idempotency_key=f"{idempotency_key}:policy_context",
                    selected_vehicle_ref=selected_vehicle_ref,
                    selected_vehicle_summary=selected_vehicle_summary,
                )
                outcome = str((confirmed or {}).get("outcome") or "").strip()
                if outcome in _POLICY_CONTEXT_SUCCESS_OUTCOMES:
                    status = SIDE_EFFECT_STATUS_CONFIRMED
                else:
                    failure = outcome or "unknown_outcome"
            except Exception as exc:
                failure = f"exception:{type(exc).__name__}"
            if status != SIDE_EFFECT_STATUS_CONFIRMED:
                # Never fail Start Claim because a confirm side-effect failed, but
                # never look confirmed either: customer keeps the insurance-card
                # upload fallback and the office can see the gap.
                logger.warning(
                    "start_claim policy_context side effect failed case=%s reason=%s",
                    case_id,
                    failure,
                )
                _add_warning(out, WARNING_POLICY_CONTEXT_UNCONFIRMED)
            side_effects["policy_context"] = status
        # Guided intake — stamp customer-confirmed AI layers after CreateClaim.
        if not ai_story_confirmed:
            side_effects["accident_story"] = SIDE_EFFECT_STATUS_SKIPPED
        else:
            status = SIDE_EFFECT_STATUS_FAILED
            failure = ""
            try:
                from services.fiqa_api.inbox_triage.accident_story_assistant import (
                    confirm_accident_story,
                )

                story_result = confirm_accident_story(
                    case_id=case_id,
                    command_id=f"{command_id}:ai_story",
                    idempotency_key=f"{idempotency_key}:ai_story",
                    raw_story=str(description or ""),
                    confirm=True,
                    customer_edits=ai_story_customer_edits
                    if isinstance(ai_story_customer_edits, dict)
                    else {
                        "accident_time_text": str(datetime_value or ""),
                        "accident_location_text": str(location or ""),
                        "injury_status": str(injury or "unknown"),
                        "raw_story": str(description or ""),
                    },
                    proposal=ai_story_proposal if isinstance(ai_story_proposal, dict) else None,
                    proposal_id=(
                        str((ai_story_proposal or {}).get("proposal_id") or "").strip() or None
                        if isinstance(ai_story_proposal, dict)
                        else None
                    ),
                    proposal_version=(
                        int(ai_story_proposal.get("proposal_version") or 1)
                        if isinstance(ai_story_proposal, dict)
                        and ai_story_proposal.get("proposal_version") is not None
                        else None
                    ),
                )
                story = story_result if isinstance(story_result, dict) else {}
                if (
                    bool(story.get("ok"))
                    and str(story.get("outcome") or "") in ("accepted", "replayed")
                    and str(story.get("authority") or "") == "customer_confirmed"
                ):
                    status = SIDE_EFFECT_STATUS_CONFIRMED
                else:
                    failure = str(story.get("error_code") or story.get("outcome") or "unknown_outcome")
            except Exception as exc:
                failure = f"exception:{type(exc).__name__}"
            if status != SIDE_EFFECT_STATUS_CONFIRMED:
                # The AI story stays a proposal: CreateClaim success must never
                # promote it to customer-confirmed truth.
                logger.warning(
                    "start_claim accident_story side effect failed case=%s reason=%s",
                    case_id,
                    failure,
                )
                _add_warning(out, WARNING_ACCIDENT_STORY_UNCONFIRMED)
            side_effects["accident_story"] = status
        out["side_effects"] = side_effects
        if out.get("side_effect_warnings"):
            _record_side_effect_failure_signal(
                case_id,
                command_id=command_id,
                warnings=[str(w) for w in out["side_effect_warnings"]],
                side_effects=side_effects,
            )
        try:
            from services.fiqa_api.inbox_triage.case_activity_events import (
                record_customer_first_action,
                record_customer_intake_opened,
                safe_record,
            )

            safe_record(
                record_customer_intake_opened,
                case_id,
                source_surface="mini_program",
                session_id=session_id,
                meta={"command_type": "start_claim_create"},
            )
            meaningful = bool(
                known_facts
                or str(policy_context_choice or "").strip()
                or description
                or datetime_value
                or location
                or injury
            )
            if meaningful:
                safe_record(
                    record_customer_first_action,
                    case_id,
                    source_surface="mini_program",
                    session_id=session_id,
                    meta={"command_type": "start_claim_mutation"},
                )
        except Exception:
            pass
    return out
