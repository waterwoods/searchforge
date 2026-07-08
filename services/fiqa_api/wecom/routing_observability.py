"""P19J-1a — Structured WeCom routing decision logs (no DB persistence)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

LOGGER = logging.getLogger(__name__)

ROUTING_DECISION_EVENT = "wecom_routing_decision_v1"

# --- priority_rule ---
PRIORITY_INJURY_SAFETY_OVERRIDE = "injury_safety_override"
PRIORITY_CLAIM_INTERRUPT_DURING_ACTIVE_ADD_VEHICLE = "claim_interrupt_during_active_add_vehicle"
PRIORITY_CLAIM_CONFIRMED_START = "claim_confirmed_start"
PRIORITY_CLAIM_QUESTION_DURING_ACTIVE_ADD_VEHICLE = "claim_question_during_active_add_vehicle"
PRIORITY_LANE_SWITCH_CONTINUE_ADD_VEHICLE = "lane_switch_continue_add_vehicle"
PRIORITY_LANE_SWITCH_CONTACT_BROKER = "lane_switch_contact_broker"
PRIORITY_ACTIVE_CLAIM_BASICS_COLLECTION = "active_claim_basics_collection"
PRIORITY_CLAIM_START_NO_ACTIVE_CASE = "claim_start_no_active_case"
PRIORITY_CLAIM_IDENTITY_BROKER_CONFIRM = "claim_identity_broker_confirm"
PRIORITY_ADD_VEHICLE_ACTIVE_PROGRESS = "add_vehicle_active_progress"
PRIORITY_ADD_VEHICLE_PHASE2_COLLECTION = "add_vehicle_phase2_collection"
PRIORITY_GENERIC_SECONDARY_TOPIC_DEFERRAL = "generic_secondary_topic_deferral"

# --- decision ---
DECISION_SAFETY_MANUAL_REPLY = "safety_manual_reply"
DECISION_LANE_SWITCH_PROMPT = "lane_switch_prompt"
DECISION_START_CLAIM_FLOW = "start_claim_flow"
DECISION_CLAIM_QUESTION_SAFE_REPLY = "claim_question_safe_reply"
DECISION_CONTINUE_ADD_VEHICLE = "continue_add_vehicle"
DECISION_CONTACT_BROKER_ACK = "contact_broker_ack"
DECISION_COLLECT_CLAIM_BASICS = "collect_claim_basics"
DECISION_CLAIM_IDENTITY_BROKER_CONFIRM = "claim_identity_broker_confirm"
DECISION_SEND_CLAIM_C1 = "send_claim_c1"
DECISION_SEND_ADD_VEHICLE_PROGRESS = "send_add_vehicle_progress"
DECISION_COLLECT_ADD_VEHICLE_PHASE2 = "collect_add_vehicle_phase2"
DECISION_DEFER_SECONDARY_TOPIC = "defer_secondary_topic"

# --- response_type ---
RESPONSE_CLAIM_SAFETY_MANUAL = "claim_safety_manual"
RESPONSE_CLAIM_LANE_SWITCH = "claim_lane_switch"
RESPONSE_CLAIM_START = "claim_start"
RESPONSE_CLAIM_QUESTION_SAFE = "claim_question_safe"
RESPONSE_CLAIM_MISSING_BASICS = "claim_missing_basics"
RESPONSE_CLAIM_IDENTITY_BROKER_CONFIRM = "claim_identity_broker_confirm"
RESPONSE_CLAIM_C1 = "claim_c1"
RESPONSE_ADD_VEHICLE_PROGRESS = "add_vehicle_progress"
RESPONSE_ADD_VEHICLE_PHASE2_MISSING = "add_vehicle_phase2_missing"
RESPONSE_SECONDARY_TOPIC_DEFERRED = "secondary_topic_deferred"

_PHONE_RE = re.compile(r"\d{10,}")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.IGNORECASE)


@dataclass(frozen=True)
class RoutingDecision:
    event: str
    route_id: str
    priority_rule: str
    decision: str
    reason: str
    response_type: str

    active_case_id: Optional[str] = None
    active_workflow: Optional[str] = None
    active_state: Optional[str] = None
    active_phase: Optional[str] = None

    incoming_intent: Optional[str] = None
    workflow_id: Optional[str] = None
    safety_flags: tuple[str, ...] = ()

    created_case_id: Optional[str] = None
    switched_workflow: Optional[str] = None

    external_user_hash: Optional[str] = None
    text_hash: Optional[str] = None
    text_length: Optional[int] = None
    text_redacted_preview: Optional[str] = None

    identity_tier: Optional[str] = None
    identity_action: Optional[str] = None
    identity_score: Optional[int] = None
    identity_rule_ids: tuple[str, ...] = ()
    identity_reasons: tuple[str, ...] = ()
    identity_case_id: Optional[str] = None

    source: str = "wecom"
    version: str = "v1"


def hash_text(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_external_user_id(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    return hashlib.sha256(f"wecom_ext:{raw}".encode("utf-8")).hexdigest()


def redact_text_preview(text: str | None, max_len: int = 80) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    redacted = _PHONE_RE.sub("[PHONE]", raw)
    redacted = _EMAIL_RE.sub("[EMAIL]", redacted)
    redacted = _VIN_RE.sub("[VIN]", redacted)
    if len(redacted) > max_len:
        return redacted[: max_len - 3] + "..."
    return redacted


def message_metadata_from_normalized(normalized: Mapping[str, Any] | None) -> dict[str, Any]:
    if not normalized:
        return {}
    text = str(normalized.get("text") or "")
    ext = str(normalized.get("external_userid") or "").strip() or None
    return {
        "external_user_hash": hash_external_user_id(ext),
        "text_hash": hash_text(text),
        "text_length": len(text) if text else 0,
        "text_redacted_preview": redact_text_preview(text),
    }


def add_vehicle_context_for_user(external_userid: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
    from services.fiqa_api.wecom.active_case_bridge import find_open_add_car_case_by_external_userid

    cid = find_open_add_car_case_by_external_userid((external_userid or "").strip())
    if not cid:
        return {}
    case = get_case_for_read(cid) or {}
    return {
        "active_case_id": cid,
        "active_workflow": "add_vehicle",
        "active_state": str(case.get("guided_workflow_state") or "").strip() or None,
        "active_phase": str(case.get("add_vehicle_phase") or case.get("claim_phase") or "").strip() or None,
    }


def claim_context_for_case(case: dict[str, Any] | None) -> dict[str, Any]:
    if not case:
        return {}
    from services.fiqa_api.wecom.claim_state import derive_claim_phase

    cid = str(case.get("case_id") or "").strip() or None
    return {
        "active_case_id": cid,
        "active_workflow": "claim",
        "active_state": str(case.get("guided_workflow_state") or "").strip() or None,
        "active_phase": derive_claim_phase(case),
        "workflow_id": "claim_simplified",
    }


def identity_context_for_decision(identity_decision: Any) -> dict[str, Any]:
    """Map ClaimIdentityDecision fields into routing log kwargs."""
    return {
        "identity_tier": identity_decision.tier,
        "identity_action": identity_decision.action,
        "identity_score": identity_decision.score,
        "identity_rule_ids": tuple(identity_decision.rule_ids or ()),
        "identity_reasons": tuple(identity_decision.reasons or ()),
        "identity_case_id": identity_decision.case_id,
    }


def build_routing_decision(
    *,
    route_id: str,
    priority_rule: str,
    decision: str,
    reason: str,
    response_type: str,
    normalized: Mapping[str, Any] | None = None,
    incoming_intent: str | None = None,
    active_case_id: str | None = None,
    active_workflow: str | None = None,
    active_state: str | None = None,
    active_phase: str | None = None,
    safety_flags: tuple[str, ...] = (),
    created_case_id: str | None = None,
    switched_workflow: str | None = None,
    workflow_id: str | None = None,
    identity_tier: str | None = None,
    identity_action: str | None = None,
    identity_score: int | None = None,
    identity_rule_ids: tuple[str, ...] = (),
    identity_reasons: tuple[str, ...] = (),
    identity_case_id: str | None = None,
) -> RoutingDecision:
    meta = message_metadata_from_normalized(normalized)
    return RoutingDecision(
        event=ROUTING_DECISION_EVENT,
        route_id=(route_id or "").strip() or "unknown",
        priority_rule=priority_rule,
        decision=decision,
        reason=reason,
        response_type=response_type,
        active_case_id=active_case_id,
        active_workflow=active_workflow,
        active_state=active_state,
        active_phase=active_phase,
        incoming_intent=incoming_intent,
        workflow_id=workflow_id,
        safety_flags=safety_flags,
        created_case_id=created_case_id,
        switched_workflow=switched_workflow,
        external_user_hash=meta.get("external_user_hash"),
        text_hash=meta.get("text_hash"),
        text_length=meta.get("text_length"),
        text_redacted_preview=meta.get("text_redacted_preview"),
        identity_tier=identity_tier,
        identity_action=identity_action,
        identity_score=identity_score,
        identity_rule_ids=identity_rule_ids,
        identity_reasons=identity_reasons,
        identity_case_id=identity_case_id,
    )


def emit_routing_decision(decision: RoutingDecision) -> None:
    payload = asdict(decision)
    LOGGER.info(
        "%s %s",
        ROUTING_DECISION_EVENT,
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
    )


def routing_decision_from_log_message(message: str) -> dict[str, Any] | None:
    """Parse routing decision JSON from a log line (test helper)."""
    if ROUTING_DECISION_EVENT not in message:
        return None
    idx = message.find("{")
    if idx < 0:
        return None
    try:
        return json.loads(message[idx:])
    except json.JSONDecodeError:
        return None
