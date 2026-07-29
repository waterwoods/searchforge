"""Server-owned Mini Program customer context and next-action resolution.

This is intentionally a small orchestration layer over the existing identity,
Active Case, signed-token, and task projection contracts.  It does not create
another workflow or customer identifier.
"""

from __future__ import annotations

from typing import Any

from services.fiqa_api.inbox_triage.h5_task_intake import intake_info_for_token
from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token
from services.fiqa_api.inbox_triage.mp_customer_identity import (
    bind_active_case,
    case_is_resumable_active,
    issue_resume_for_case,
    resolve_active_case_for_person_link,
    resolve_customer_identity_key,
)

START_NEW_CLAIM = "START_NEW_CLAIM"
CONTINUE_ACTIVE_CASE = "CONTINUE_ACTIVE_CASE"
UPLOAD_REQUEST_ITEM = "UPLOAD_REQUEST_ITEM"
BROKER_REVIEW = "BROKER_REVIEW"
CASE_CLOSED = "CASE_CLOSED"


def _next_action_from_task(task: dict[str, Any]) -> str:
    if bool(task.get("case_closed_read_only")) or str(task.get("case_status") or "").lower() == "closed":
        return CASE_CLOSED

    # Unfinished actionable tasks win over wait signals — Continue must not
    # land on Waiting while Story / Insurance / Photos still remain.
    constitution = task.get("constitution_projection")
    customer = constitution.get("customer") if isinstance(constitution, dict) else None
    tasks = customer.get("tasks") if isinstance(customer, dict) else None
    if isinstance(tasks, list) and any(isinstance(item, dict) and item.get("actionable") for item in tasks):
        return UPLOAD_REQUEST_ITEM
    stage = ""
    today = ""
    if isinstance(customer, dict):
        stage = str(customer.get("current_stage") or "").strip()
        today = str(customer.get("today") or "").strip()
    if not stage and isinstance(constitution, dict):
        stage = str(constitution.get("current_stage") or "").strip()
    if stage == "customer_action_needed" or (
        today and today not in {"先不用操作", "案件已关闭"}
    ):
        return CONTINUE_ACTIVE_CASE
    if stage == "waiting_broker" or today == "先不用操作":
        return BROKER_REVIEW

    slice1 = task.get("slice1_projection")
    customer_action = slice1.get("customer_next_action") if isinstance(slice1, dict) else None
    action_type = str(customer_action.get("action_type") or "").strip() if isinstance(customer_action, dict) else ""
    if action_type in ("provide_fact", "provide_evidence"):
        return UPLOAD_REQUEST_ITEM
    if action_type in ("wait_for_broker_review", "contact_broker"):
        return BROKER_REVIEW

    contract = task.get("task_contract")
    contract_action = contract.get("next_action") if isinstance(contract, dict) else None
    contract_type = str(contract_action.get("type") or "").strip() if isinstance(contract_action, dict) else ""
    if contract_type in ("go_to_section", "submit"):
        return UPLOAD_REQUEST_ITEM
    if contract_type in ("view_status", "contact_broker"):
        return BROKER_REVIEW

    if bool(task.get("submitted")):
        return BROKER_REVIEW
    return CONTINUE_ACTIVE_CASE


def _context_for_token(*, token: str, active_case: bool) -> dict[str, Any]:
    claims = verify_h5_task_token(token)
    if claims is None:
        raise ValueError("invalid_or_expired_task_link")
    task = intake_info_for_token(claims)
    return {
        "has_active_case": active_case,
        "resume_token": token,
        "resume_expires_at": "",
        "next_action": _next_action_from_task(task),
    }


def resolve_customer_context(
    *,
    session_id: str,
    launch_token: str | None = None,
) -> dict[str, Any]:
    """Resolve one customer context after identity is established.

    A launch token is proof for a first binding only.  An existing Active Case
    always wins, so a stale QR cannot replace or fork the customer's case.
    """
    identity_key = resolve_customer_identity_key(session_id)
    if not identity_key:
        raise ValueError("durable_identity_required")

    active = resolve_active_case_for_person_link(identity_key)
    if active:
        case_id = str(active.get("case_id") or "").strip()
        if not case_id:
            raise ValueError("case_not_found")
        resume = issue_resume_for_case(case_id)
        context = _context_for_token(token=resume["resume_token"], active_case=True)
        context["resume_expires_at"] = resume["resume_expires_at"]
        return context

    presented = str(launch_token or "").strip()
    if presented:
        claims = verify_h5_task_token(presented)
        if claims is None:
            raise ValueError("invalid_or_expired_task_link")
        from services.fiqa_api.inbox_triage.mp_customer_identity import _load_case

        launched_case = _load_case(claims.case_id)
        if launched_case and case_is_resumable_active(launched_case):
            bind_active_case(identity_key, claims.case_id)
            resume = issue_resume_for_case(claims.case_id)
            context = _context_for_token(token=resume["resume_token"], active_case=True)
            context["resume_expires_at"] = resume["resume_expires_at"]
            return context
        return _context_for_token(token=presented, active_case=False)

    return {
        "has_active_case": False,
        "resume_token": "",
        "resume_expires_at": "",
        "next_action": START_NEW_CLAIM,
    }
