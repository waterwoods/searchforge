"""P19E-1 — Add Vehicle Phase 2 text field collection (WeCom chat)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from services.fiqa_api.inbox_triage.case_store import (
    append_follow_up_message,
    get_case_by_id,
    update_add_vehicle_workflow_state,
)
from services.fiqa_api.inbox_triage.h5_task_upload import h5_photo_flow_is_complete
from services.fiqa_api.inbox_triage.phone_normalization import normalize_phone_digits
from services.fiqa_api.wecom.active_case_bridge import find_case_by_wecom_msg_id
from services.fiqa_api.wecom.identity import (
    extract_delivery_date_from_text,
    extract_phone_from_text,
    extract_zip_from_text,
)
from services.fiqa_api.wecom.intent import IntentResult

logger = logging.getLogger(__name__)

PHASE2_TEXT_FIELDS: tuple[str, ...] = ("delivery_date", "zip", "phone")

_FIELD_LABELS_ZH: dict[str, str] = {
    "delivery_date": "提车日期",
    "zip": "停放 ZIP",
    "phone": "联系电话",
}


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info("%s %s", event, json.dumps(payload, ensure_ascii=False))


def _collected_field_names(case: dict[str, Any]) -> set[str]:
    return {str(x).lower() for x in (case.get("collected_fields") or []) if str(x).strip()}


def phase2_text_still_needed(case: dict[str, Any]) -> list[str]:
    collected = _collected_field_names(case)
    return [f for f in PHASE2_TEXT_FIELDS if f not in collected]


def phase2_text_is_complete(case: dict[str, Any]) -> bool:
    return not phase2_text_still_needed(case)


def _s2_already_sent(case: dict[str, Any]) -> bool:
    state = case.get("h5_photo_flow_state") or {}
    if not isinstance(state, dict):
        return False
    return bool(str(state.get("s2_stage_complete_sent_at") or "").strip())


def _field_display_value(case: dict[str, Any], field: str) -> str:
    facts = case.get("known_facts") or {}
    if isinstance(facts, dict):
        raw = facts.get(field)
        if raw:
            return str(raw).strip()
    if field == "phone":
        phone = normalize_phone_digits(case.get("customer_phone") or "")
        if len(phone) == 10:
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
    return _FIELD_LABELS_ZH.get(field, field)


def should_handle_phase2_incoming_text(
    case: dict[str, Any],
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    """Route to Phase 2 handler when H5 photos are done but text fields are not."""
    if not h5_photo_flow_is_complete(case):
        return False
    if phase2_text_is_complete(case):
        return False
    text = str(normalized.get("text") or "").strip()
    from services.fiqa_api.inbox_triage.h5_task_upload import is_explicit_add_car_restart

    if is_explicit_add_car_restart(text):
        return False
    if intent_result.confidence == "high" and intent_result.intent in {
        "policy_review",
        "claim_intake",
        "coverage_risk_intake",
    }:
        return False
    if intent_result.confidence == "high" and intent_result.intent == "add_car":
        text = str(normalized.get("text") or "").strip()
        has_phase2_fields = any(
            [
                extract_delivery_date_from_text(text),
                extract_zip_from_text(text),
                normalized.get("phone") or extract_phone_from_text(text),
            ]
        )
        if not has_phase2_fields:
            return False
    return True


def _extract_phase2_fields(text: str, normalized: dict[str, Any]) -> dict[str, str | None]:
    return {
        "delivery_date": extract_delivery_date_from_text(text),
        "zip": extract_zip_from_text(text),
        "phone": normalized.get("phone") or extract_phone_from_text(text),
    }


def _build_phase2_triage_stub(
    case: dict[str, Any],
    extracted: dict[str, str | None],
) -> dict[str, Any]:
    already = _collected_field_names(case)
    newly_collected: list[str] = []
    known_facts = dict(case.get("known_facts") or {}) if isinstance(case.get("known_facts"), dict) else {}

    for field, value in extracted.items():
        if not value:
            continue
        if field.lower() in already:
            continue
        newly_collected.append(field)
        known_facts[field] = str(value).strip()

    merged_collected = list(case.get("collected_fields") or [])
    seen = _collected_field_names(case)
    for field in newly_collected:
        fl = field.lower()
        if fl not in seen:
            merged_collected.append(field)
            seen.add(fl)

    still_needed = [f for f in PHASE2_TEXT_FIELDS if f.lower() not in seen]
    handoff_ready = not still_needed

    stub: dict[str, Any] = {
        "issue_category": case.get("issue_category") or "add_car_quote",
        "urgency": case.get("urgency") or "medium",
        "client_prep": "",
        "client_reply_draft": "",
        "manual_followup_needed": True,
        "collected_fields": newly_collected,
        "still_needed_fields": still_needed,
        "handoff_ready": handoff_ready,
        "known_facts": known_facts,
        "broker_next_step": (
            "Add Vehicle Phase 2 text complete — broker review."
            if handoff_ready
            else "Add Vehicle Phase 2 — collect remaining text fields."
        ),
    }
    if handoff_ready:
        stub["quote_ready_status"] = "almost_ready"
    return stub


def ingest_phase2_text_collection(
    normalized: dict[str, Any],
    case_id: str,
) -> dict[str, Any]:
    """
    Merge Phase 2 text fields into an open add_car case and build the WeCom reply.

    Returns outcome dict with reply_text, case_id, active_case_outcome, etc.
    """
    msg_id = str(normalized.get("msg_id") or "").strip()
    text = str(normalized.get("text") or "").strip()

    existing_by_msg = find_case_by_wecom_msg_id(msg_id)
    if existing_by_msg:
        from services.fiqa_api.wecom.reply import build_phase2_current_step_reply

        case = get_case_by_id(case_id) or {}
        reply = build_phase2_current_step_reply(case) if not phase2_text_is_complete(case) else None
        return {
            "outcome": "duplicate_msg",
            "case_id": existing_by_msg,
            "case_created": False,
            "reply_text": reply,
            "active_case_outcome": "phase2_duplicate_msg",
        }

    case = get_case_by_id(case_id)
    if case is None:
        return {
            "outcome": "case_not_found",
            "case_id": None,
            "case_created": False,
            "reply_text": None,
            "active_case_outcome": "phase2_case_not_found",
        }

    extracted = _extract_phase2_fields(text, normalized)
    triage_stub = _build_phase2_triage_stub(case, extracted)

    if not text:
        text = "(no text)"
    from services.fiqa_api.wecom.active_case_bridge import _record_wecom_evidence

    updated = append_follow_up_message(case_id, text, triage_stub)
    if updated is None:
        return {
            "outcome": "case_not_found",
            "case_id": None,
            "case_created": False,
            "reply_text": None,
            "active_case_outcome": "phase2_case_not_found",
        }

    _record_wecom_evidence(case_id, msg_id)

    phone = extracted.get("phone")
    if phone:
        from services.fiqa_api.inbox_triage.case_store import update_case_customer

        digits = normalize_phone_digits(phone)
        if digits:
            update_case_customer(case_id, customer_phone=digits)

    refreshed = get_case_by_id(case_id) or updated
    complete = phase2_text_is_complete(refreshed)

    from services.fiqa_api.wecom.reply import (
        build_phase2_current_step_reply,
        build_phase2_stage_complete_s2_reply,
    )

    if complete:
        add_vehicle_phase = "phase_3_broker_review"
        guided_state = "ready_for_broker_review"
        sent_s2_before = _s2_already_sent(refreshed)
        update_add_vehicle_workflow_state(
            case_id,
            guided_workflow_state=guided_state,
            add_vehicle_phase=add_vehicle_phase,
            s2_stage_complete_sent_at=(
                datetime.now(timezone.utc).isoformat() if not sent_s2_before else None
            ),
        )
        refreshed = get_case_by_id(case_id) or refreshed
        if sent_s2_before:
            reply_text = None
            outcome = "phase2_complete_s2_deduped"
        else:
            reply_text = build_phase2_stage_complete_s2_reply(refreshed)
            outcome = "phase2_complete_s2_sent"
    else:
        update_add_vehicle_workflow_state(
            case_id,
            guided_workflow_state="collecting_text_fields",
            add_vehicle_phase="phase_2_text_in_progress",
        )
        refreshed = get_case_by_id(case_id) or refreshed
        reply_text = build_phase2_current_step_reply(refreshed)
        outcome = "phase2_partial_progress"

    _log_event(
        "wecom_phase2_text_ingest_v1",
        {
            "msg_id": msg_id,
            "case_id": case_id,
            "outcome": outcome,
            "delivery_date_present": bool(extracted.get("delivery_date")),
            "zip_present": bool(extracted.get("zip")),
            "phone_present": bool(extracted.get("phone")),
            "still_needed": phase2_text_still_needed(refreshed),
        },
    )

    return {
        "outcome": "attached",
        "case_id": case_id,
        "case_created": False,
        "reply_text": reply_text,
        "active_case_outcome": outcome,
        "still_needed_fields": phase2_text_still_needed(refreshed),
        "guided_workflow_state": refreshed.get("guided_workflow_state"),
        "add_vehicle_phase": refreshed.get("add_vehicle_phase"),
    }
