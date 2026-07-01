"""WeCom text event → Active Case resolver bridge (Track A readiness)."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from services.fiqa_api.inbox_triage.active_case_resolver import (
    ResolverOutcome,
    resolve_active_case_for_evidence,
)
from services.fiqa_api.inbox_triage.case_store import (
    append_evidence_event_only,
    append_follow_up_message,
    list_all_cases,
    save_case,
    update_case_customer,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_cases_for_phone_lookup
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.inbox_triage.phone_normalization import normalize_phone_digits
from services.fiqa_api.wecom.identity import extract_phone_from_text, extract_vin_from_text
from services.fiqa_api.wecom.intent import IntentResult, canonical_intent

logger = logging.getLogger(__name__)

WeComIngestOutcome = Literal[
    "skipped",
    "duplicate_msg",
    "need_phone",
    "broker_review",
    "created",
    "attached",
    "intent_not_actionable",
]

_ADD_CAR_CANONICAL = frozenset({"add_vehicle", "add_car"})


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info("%s %s", event, json.dumps(payload, ensure_ascii=False))


def _evidence_filename(msg_id: str) -> str:
    mid = (msg_id or "").strip() or "unknown"
    return f"wecom:{mid}"


def find_case_by_wecom_msg_id(msg_id: str) -> str | None:
    """Return case_id if this WeCom msg_id was already ingested."""
    mid = (msg_id or "").strip()
    if not mid:
        return None
    marker = _evidence_filename(mid)
    for case in list_all_cases():
        for ev in case.get("evidence_events") or []:
            if not isinstance(ev, dict):
                continue
            if ev.get("wecom_msg_id") == mid:
                return str(case.get("case_id") or "").strip() or None
            if ev.get("filename") == marker:
                return str(case.get("case_id") or "").strip() or None
    return None


def _build_add_car_triage_stub(
    phone: str,
    *,
    vin: str | None = None,
    merge_review: bool = False,
) -> dict[str, Any]:
    digits = normalize_phone_digits(phone)
    still_needed = ["year", "make_model", "zip", "delivery_date", "primary_driver", "vin"]
    collected: list[str] = []
    if digits:
        collected.append("phone")
    if vin:
        still_needed = [f for f in still_needed if f != "vin"]
        collected.append("vin")
    stub: dict[str, Any] = {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": (
            "WeCom add-vehicle message received; collect vehicle documents and verify identity."
        ),
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "lifecycle_status": "collecting",
        "collection_stage": "collecting",
        "collected_fields": collected,
        "still_needed_fields": still_needed,
        "quote_ready_status": "need_more",
        "service_type": "add_car",
        "extracted_contact_phone": digits,
    }
    if vin:
        stub["vehicle_key"] = vin
    if merge_review:
        stub["quote_ready_status"] = "almost_ready"
    return stub


def _record_wecom_evidence(case_id: str, msg_id: str) -> None:
    append_evidence_event_only(
        case_id,
        channel="wecom_kf",
        filename=_evidence_filename(msg_id),
    )


def ingest_wecom_text_to_active_case(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> dict[str, Any]:
    """
    Minimal WeCom → Active Case bridge.

    Only high-confidence add_vehicle with valid phone creates or attaches a case.
    No Trusted Packet from text-only evidence.
    """
    msg_id = str(normalized.get("msg_id") or "").strip()
    text = str(normalized.get("text") or "").strip()
    phone = normalized.get("phone") or extract_phone_from_text(text)
    vin = extract_vin_from_text(text)
    detected = canonical_intent(intent_result.intent)

    _log_event(
        "wecom_intent_detected_v1",
        {
            "msg_id": msg_id,
            "intent": detected,
            "internal_intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "matched_by": intent_result.matched_by,
        },
    )

    existing_case = find_case_by_wecom_msg_id(msg_id)
    if existing_case:
        _log_event(
            "wecom_active_case_resolution_v1",
            {"msg_id": msg_id, "outcome": "duplicate_msg", "case_id": existing_case},
        )
        return {
            "outcome": "duplicate_msg",
            "case_id": existing_case,
            "case_created": False,
            "readiness_gate": None,
        }

    if detected not in _ADD_CAR_CANONICAL or intent_result.confidence != "high":
        if phone and vin and normalize_phone_digits(phone):
            detected = "add_vehicle"
        else:
            return {
                "outcome": "intent_not_actionable",
                "case_id": None,
                "case_created": False,
                "readiness_gate": None,
            }

    if not phone or not normalize_phone_digits(phone) or len(normalize_phone_digits(phone)) != 10:
        _log_event(
            "wecom_identity_missing_v1",
            {
                "msg_id": msg_id,
                "external_userid": normalized.get("external_userid"),
                "intent": detected,
                "gate": "NEED_PHONE",
            },
        )
        return {
            "outcome": "need_phone",
            "case_id": None,
            "case_created": False,
            "readiness_gate": "NEED_INFO",
        }

    phone_digits = normalize_phone_digits(phone)
    decision = resolve_active_case_for_evidence(
        phone=phone_digits,
        intent="add_vehicle",
        new_vin=vin,
        cases=list_cases_for_phone_lookup(phone_digits),
    )

    _log_event(
        "wecom_active_case_resolution_v1",
        {
            "msg_id": msg_id,
            "phone_tail": phone_digits[-4:],
            "resolver_outcome": decision.outcome.value,
            "case_id": decision.case_id,
            "conflict_reason": decision.conflict_reason,
            "candidate_count": decision.candidate_count,
            "vin_present": bool(vin),
        },
    )

    source_text = f"[客户] WeCom: {text}"
    merge_review = decision.outcome == ResolverOutcome.BROKER_REVIEW
    triage_stub = _build_add_car_triage_stub(phone_digits, vin=vin, merge_review=merge_review)

    if decision.outcome == ResolverOutcome.CREATE:
        saved = save_case(
            source_text,
            triage_stub,
            status="new",
            service_lane=SERVICE_LANE_ADD_CAR,
        )
        case_id = str(saved.get("case_id") or "").strip()
        if case_id:
            update_case_customer(case_id, customer_phone=phone_digits)
            _record_wecom_evidence(case_id, msg_id)
        _log_event(
            "wecom_active_case_created_or_attached_v1",
            {"msg_id": msg_id, "action": "created", "case_id": case_id},
        )
        return {
            "outcome": "created",
            "case_id": case_id or None,
            "case_created": True,
            "readiness_gate": "NEED_INFO",
        }

    if decision.outcome == ResolverOutcome.BROKER_REVIEW:
        case_id = str(decision.case_id or "").strip()
        if case_id:
            append_follow_up_message(case_id, text, triage_stub)
            _record_wecom_evidence(case_id, msg_id)
        _log_event(
            "wecom_active_case_created_or_attached_v1",
            {
                "msg_id": msg_id,
                "action": "broker_review",
                "case_id": case_id or None,
                "conflict_reason": decision.conflict_reason,
            },
        )
        return {
            "outcome": "broker_review",
            "case_id": case_id or None,
            "case_created": False,
            "readiness_gate": "BROKER_REVIEW",
            "conflict_reason": decision.conflict_reason,
        }

    case_id = str(decision.case_id or "").strip()
    if case_id:
        append_follow_up_message(case_id, text, triage_stub)
        _record_wecom_evidence(case_id, msg_id)
    _log_event(
        "wecom_active_case_created_or_attached_v1",
        {"msg_id": msg_id, "action": "attached", "case_id": case_id},
    )
    return {
        "outcome": "attached",
        "case_id": case_id or None,
        "case_created": False,
        "readiness_gate": "NEED_INFO",
    }
