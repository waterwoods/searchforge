"""P19H-2' — Simplified Claim WeCom: safety gate + accident basics + C1."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from services.fiqa_api.inbox_triage.case_store import (
    add_case_risk_flag,
    append_claim_timeline_event,
    append_follow_up_message,
    bind_case_channel_identity,
    build_claim_timeline_event,
    patch_case_known_facts,
    save_case,
    update_claim_collision_pending,
    update_lane_switch_pending,
)
from services.fiqa_api.inbox_triage.case_truth_repository import (
    get_case_for_read,
    list_all_cases_for_read,
)
from services.fiqa_api.inbox_triage.h5_task_upload import is_explicit_add_car_restart
from services.fiqa_api.wecom.active_case_bridge import (
    _record_wecom_evidence,
    find_case_by_wecom_msg_id,
    find_open_add_car_case_by_external_userid,
)
from services.fiqa_api.wecom.claim_extractors import (
    extract_accident_basics_fields,
    has_accident_basics_signals,
    message_mentions_injury,
)
from services.fiqa_api.wecom.claim_identity import (
    ClaimIdentityDecision,
    is_explicit_new_accident,
    is_open_claim_candidate_for_basics,
    newest_open_claim_id,
    resolve_claim_identity,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_ACCIDENT_BASICS_FIELDS,
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_STARTED,
    GUIDED_STATE_COLLECTING_TEXT,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
    evaluate_claim_simplified_snapshot,
    get_claim_simplified_current_step,
    is_accident_basics_complete,
    suggest_next_claim_transition,
    transition_to_manual_handle,
)
from services.fiqa_api.wecom.intent import IntentResult, is_add_vehicle_status_inquiry, is_claim_status_request
from services.fiqa_api.wecom.routing_observability import (
    DECISION_CLAIM_IDENTITY_BROKER_CONFIRM,
    DECISION_CLAIM_QUESTION_SAFE_REPLY,
    DECISION_COLLECT_CLAIM_BASICS,
    DECISION_CONTACT_BROKER_ACK,
    DECISION_CONTINUE_ADD_VEHICLE,
    DECISION_LANE_SWITCH_PROMPT,
    DECISION_SAFETY_MANUAL_REPLY,
    DECISION_SEND_CLAIM_C1,
    DECISION_START_CLAIM_FLOW,
    PRIORITY_ACTIVE_CLAIM_BASICS_COLLECTION,
    PRIORITY_CLAIM_CONFIRMED_START,
    PRIORITY_CLAIM_IDENTITY_BROKER_CONFIRM,
    PRIORITY_CLAIM_INTERRUPT_DURING_ACTIVE_ADD_VEHICLE,
    PRIORITY_CLAIM_QUESTION_DURING_ACTIVE_ADD_VEHICLE,
    PRIORITY_CLAIM_START_NO_ACTIVE_CASE,
    PRIORITY_INJURY_SAFETY_OVERRIDE,
    PRIORITY_LANE_SWITCH_CONTACT_BROKER,
    PRIORITY_LANE_SWITCH_CONTINUE_ADD_VEHICLE,
    RESPONSE_CLAIM_C1,
    RESPONSE_CLAIM_IDENTITY_BROKER_CONFIRM,
    RESPONSE_CLAIM_LANE_SWITCH,
    RESPONSE_CLAIM_MISSING_BASICS,
    RESPONSE_CLAIM_QUESTION_SAFE,
    RESPONSE_CLAIM_SAFETY_MANUAL,
    RESPONSE_CLAIM_START,
    add_vehicle_context_for_user,
    build_routing_decision,
    claim_context_for_case,
    emit_routing_decision,
    identity_context_for_decision,
)

logger = logging.getLogger(__name__)

# Re-export extractors under prompt naming.
extract_claim_accident_basics = extract_accident_basics_fields

CLAIM_GUIDED_START_MARKERS: tuple[str, ...] = (
    "我要理赔",
    "我现在要理赔",
    "我要进行理赔",
    "我现在要进行理赔",
    "进行理赔",
    "开始理赔",
    "我要报理赔",
    "我要记录事故",
    "我要记录新事故",
    "我要开一个事故记录",
    "出事故了我要理赔",
    "新事故",
    "file a claim",
    "i had an accident",
    "accident claim",
)

CLAIM_PASSIVE_NARRATIVE_MARKERS: tuple[str, ...] = (
    "追尾",
    "被撞",
    "后保险杠",
    "刮蹭",
    "撞了",
    "车祸",
    "事故",
    "出险",
    "rear-end",
    "rear ended",
    "got hit",
    "collision",
    "hit and run",
)

CLAIM_LANE_SWITCH_CONFIRM_MARKERS: tuple[str, ...] = (
    "开始事故记录",
    "start accident record",
)

CLAIM_LANE_SWITCH_CONTINUE_MARKERS: tuple[str, ...] = (
    "继续加车",
)

CLAIM_LANE_SWITCH_BROKER_MARKERS: tuple[str, ...] = (
    "联系陈总",
)

CLAIM_COLLISION_CONTINUE_MARKERS: tuple[str, ...] = (
    "继续上一个事故",
    "继续当前事故",
    "同一个事故",
    "继续补资料",
)

CLAIM_COLLISION_NEW_MARKERS: tuple[str, ...] = (
    "开始新的事故记录",
    "新的事故",
    "新事故",
)

CLAIM_COLLISION_CONTACT_MARKERS: tuple[str, ...] = (
    "联系陈总",
)

CLAIM_QUESTION_MARKERS: tuple[str, ...] = (
    "怎么办",
    "要不要报",
    "是不是对方",
    "会不会赔",
    "会不会涨",
    "谁的责任",
    "能赔吗",
    "should i file",
)

RESTART_CLAIM_MARKERS: tuple[str, ...] = (
    "重新理赔",
    "新事故",
    "重新开始理赔",
)

_CLAIM_PROGRESS_MARKERS: tuple[str, ...] = (
    "进度",
    "继续",
    "还差什么",
    "到哪了",
    "第 1 步",
    "第一步",
    "status",
    "progress",
    "continue",
)


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info("%s %s", event, json.dumps(payload, ensure_ascii=False))


def _emit_claim_routing_decision(
    *,
    normalized: dict[str, Any],
    intent_result: IntentResult | None,
    **kwargs: Any,
) -> None:
    emit_routing_decision(
        build_routing_decision(
            route_id=str(normalized.get("msg_id") or ""),
            normalized=normalized,
            incoming_intent=intent_result.intent if intent_result else None,
            **kwargs,
        )
    )


def is_explicit_claim_restart(text: str) -> bool:
    return is_explicit_new_accident(text)


def is_claim_guided_start_message(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    if any(m in raw or m in lowered for m in CLAIM_QUESTION_MARKERS):
        explicit_only = (
            "我要理赔",
            "我现在要理赔",
            "我要进行理赔",
            "我现在要进行理赔",
            "进行理赔",
            "开始理赔",
            "我要报理赔",
            "我要记录事故",
            "新事故",
            "重新理赔",
            "我要记录新事故",
            "我要开一个事故记录",
            "出事故了我要理赔",
        )
        if not any(m in raw for m in explicit_only):
            return False
    if is_explicit_claim_restart(raw):
        return True
    if any(m in raw for m in CLAIM_GUIDED_START_MARKERS):
        return True
    lowered = raw.lower()
    if lowered in ("claim", "accident"):
        return True
    # "被撞了" only counts as explicit start when phrased as a request for help.
    if "被撞" in raw and any(
        cue in raw for cue in ("怎么办", "帮我", "请帮", "要理赔", "开始", "记录")
    ):
        return True
    return False


def is_claim_passive_narrative(text: str) -> bool:
    """Accident-like narrative without explicit formal start intent (P19H-3f-1)."""
    raw = (text or "").strip()
    if not raw:
        return False
    if is_claim_guided_start_message(raw):
        return False
    if is_claim_question_not_guided_intake(raw):
        return False
    lowered = raw.lower()
    if any(m in raw or m in lowered for m in CLAIM_PASSIVE_NARRATIVE_MARKERS):
        return True
    parsed = extract_accident_basics_fields(raw)
    if parsed.get("accident_datetime") and parsed.get("accident_location"):
        return True
    return False


def is_claim_lane_switch_confirm(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    if lowered in ("1", "start accident record"):
        return True
    return any(m in raw for m in CLAIM_LANE_SWITCH_CONFIRM_MARKERS)


def is_claim_lane_switch_continue(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw == "2":
        return True
    return any(m in raw for m in CLAIM_LANE_SWITCH_CONTINUE_MARKERS)


def is_claim_lane_switch_broker(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw == "3":
        return True
    return any(m in raw for m in CLAIM_LANE_SWITCH_BROKER_MARKERS)


def should_route_add_car_to_claim_lane_switch(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    """True when active Add Car must show lane-switch confirm (not minimal_lane defer).

    Independent of open Claim cases — an existing Claim in broker_review must not
    block explicit Claim start during active Add Car (production bug 2026-07-10).
    """
    ext = str(normalized.get("external_userid") or "").strip()
    if not find_open_add_car_case_by_external_userid(ext):
        return False
    text = str(normalized.get("text") or "").strip()
    injury_mentioned = message_mentions_injury(text)
    if injury_mentioned and is_claim_guided_start_message(text):
        return True
    return _active_add_car_blocks_claim_start(
        text=text,
        intent_result=intent_result,
        injury_mentioned=injury_mentioned,
    )


def should_route_claim_interrupt_during_add_car(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    """Live WeCom slice: claim interrupt must win over minimal_lane secondary-topic defer."""
    from services.fiqa_api.wecom.intent import CLAIM_INJURY_CLICK_INTENTS

    ext = str(normalized.get("external_userid") or "").strip()
    if not find_open_add_car_case_by_external_userid(ext):
        return False
    if should_route_add_car_to_claim_lane_switch(normalized, intent_result):
        return True
    if should_route_claim_lane_switch_choice(normalized):
        return True
    if intent_result.intent in (
        "lane_switch_start_claim_click",
        "lane_switch_continue_add_car_click",
    ):
        return True
    if intent_result.intent in CLAIM_INJURY_CLICK_INTENTS:
        return True
    if should_route_claim_question_safe_reply(normalized, intent_result):
        return True
    if should_route_claim_holding_ack(normalized, intent_result):
        return True
    if should_route_claim_guided_workflow(normalized, intent_result):
        return True
    return False


def should_route_claim_lane_switch_choice(normalized: dict[str, Any]) -> bool:
    """Route lane-switch follow-up (confirm / continue / broker) while Add Vehicle is active."""
    ext = str(normalized.get("external_userid") or "").strip()
    if not find_open_add_car_case_by_external_userid(ext):
        return False
    text = str(normalized.get("text") or "").strip()
    return (
        is_claim_lane_switch_confirm(text)
        or is_claim_lane_switch_continue(text)
        or is_claim_lane_switch_broker(text)
    )


def _lane_switch_pending(case: dict[str, Any] | None) -> dict[str, Any]:
    if not case:
        return {}
    raw = case.get("lane_switch_pending") or {}
    return dict(raw) if isinstance(raw, dict) else {}


def _lane_switch_pending_confirm(case: dict[str, Any] | None) -> bool:
    pending = _lane_switch_pending(case)
    if pending.get("confirmed_claim_id"):
        return False
    state = str(pending.get("state") or "").strip().lower()
    if state == "pending_confirm":
        return True
    return str(pending.get("pending_lane_switch") or "").strip() == "add_car_to_claim"


def _add_car_received_material_summary(case: dict[str, Any]) -> dict[str, bool]:
    from services.fiqa_api.inbox_triage.h5_task_upload import h5_photo_flow_is_complete

    state = case.get("h5_photo_flow_state") or {}
    uploads = state.get("uploads") if isinstance(state.get("uploads"), list) else []
    photo_received = bool(uploads) or h5_photo_flow_is_complete(case)
    activity = case.get("activity_log") or []
    customer_turns = sum(
        1
        for entry in activity
        if isinstance(entry, dict) and "Customer" in str(entry.get("message") or "")
    )
    text_received = customer_turns > 0 or bool(str(case.get("vehicle_key") or "").strip())
    return {"photo_received": photo_received, "text_received": text_received}


def _set_lane_switch_pending(case_id: str | None, *, trigger_text: str = "") -> None:
    if not case_id:
        return
    case = get_case_for_read(case_id) or {}
    if _lane_switch_pending_confirm(case):
        return
    now = datetime.now(timezone.utc).isoformat()
    update_lane_switch_pending(
        case_id,
        {
            "from_lane": "add_car",
            "to_lane": "claim",
            "state": "pending_confirm",
            "pending_lane_switch": "add_car_to_claim",
            "source_case_id": case_id,
            "trigger_text": (trigger_text or "").strip(),
            "created_at": now,
            "status_before": str(case.get("guided_workflow_state") or case.get("add_vehicle_phase") or "").strip() or None,
            "received_material_summary": _add_car_received_material_summary(case),
        },
    )


def _clear_lane_switch_pending(case_id: str | None) -> None:
    if case_id:
        update_lane_switch_pending(case_id, None)


def _mark_lane_switch_confirmed(case_id: str | None, claim_id: str) -> None:
    if not case_id or not claim_id:
        return
    pending = _lane_switch_pending(get_case_for_read(case_id))
    pending.update(
        {
            "pending_lane_switch": "add_car_to_claim",
            "source_case_id": case_id,
            "confirmed_claim_id": claim_id,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    update_lane_switch_pending(case_id, pending)


def ingest_claim_lane_switch_confirm(normalized: dict[str, Any]) -> dict[str, Any]:
    """Create formal Claim after user confirms lane switch from active Add Vehicle."""
    from services.fiqa_api.inbox_triage.case_store import update_claim_workflow_state
    from services.fiqa_api.wecom.reply import build_claim_start_injury_menu_payload

    ext = str(normalized.get("external_userid") or "").strip()
    add_car_id = find_open_add_car_case_by_external_userid(ext)
    add_car_case = get_case_for_read(add_car_id) if add_car_id else None
    pending = _lane_switch_pending(add_car_case)
    existing_claim_id = str(pending.get("confirmed_claim_id") or "").strip() or None

    if existing_claim_id:
        case = get_case_for_read(existing_claim_id) or {}
        injury_menu = build_claim_start_injury_menu_payload()
        return {
            "outcome": "claim_start_card_sent",
            "case_id": existing_claim_id,
            "case_created": False,
            "reply_text": injury_menu["head_content"],
            "menu_payload": injury_menu,
            "active_case_outcome": "claim_start_card_sent",
            "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
            "service_lane": SERVICE_LANE_CLAIM,
        }

    created = _create_claim_case(normalized, injury_mentioned=False)
    case_id = str(created.get("case_id") or "").strip() or None
    if not case_id:
        return {
            "outcome": "claim_case_not_found",
            "case_id": None,
            "case_created": False,
            "reply_text": None,
            "active_case_outcome": "claim_case_not_found",
            "service_lane": None,
        }

    _mark_lane_switch_confirmed(add_car_id, case_id)
    update_claim_workflow_state(
        case_id,
        claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
        guided_workflow_state=GUIDED_STATE_COLLECTING_TEXT,
    )
    injury_menu = build_claim_start_injury_menu_payload()
    av_ctx = add_vehicle_context_for_user(ext)
    _emit_claim_routing_decision(
        normalized=normalized,
        intent_result=None,
        priority_rule=PRIORITY_CLAIM_CONFIRMED_START,
        decision=DECISION_START_CLAIM_FLOW,
        reason="user_confirmed_lane_switch_start_claim",
        response_type=RESPONSE_CLAIM_START,
        created_case_id=case_id,
        switched_workflow="claim",
        workflow_id="claim_simplified",
        **av_ctx,
    )
    return {
        "outcome": "claim_start_card_sent",
        "case_id": case_id,
        "case_created": True,
        "reply_text": injury_menu["head_content"],
        "menu_payload": injury_menu,
        "active_case_outcome": "claim_start_card_sent",
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
        "service_lane": SERVICE_LANE_CLAIM,
    }


def ingest_claim_lane_switch_choice(normalized: dict[str, Any]) -> dict[str, Any]:
    """Handle confirm / continue-add-vehicle / broker-contact after lane-switch prompt."""
    from services.fiqa_api.wecom.reply import (
        build_add_vehicle_continue_reply,
        build_lane_switch_broker_contact_reply,
    )

    text = str(normalized.get("text") or "").strip()
    ext = str(normalized.get("external_userid") or "").strip()
    add_car_id = find_open_add_car_case_by_external_userid(ext)

    if is_claim_lane_switch_confirm(text):
        return ingest_claim_lane_switch_confirm(normalized)

    if is_claim_lane_switch_broker(text):
        av_ctx = add_vehicle_context_for_user(ext)
        _emit_claim_routing_decision(
            normalized=normalized,
            intent_result=None,
            priority_rule=PRIORITY_LANE_SWITCH_CONTACT_BROKER,
            decision=DECISION_CONTACT_BROKER_ACK,
            reason="user_chose_contact_broker_after_lane_switch_prompt",
            response_type="contact_broker_ack",
            **av_ctx,
        )
        return {
            "outcome": "claim_lane_switch_broker",
            "case_id": add_car_id,
            "case_created": False,
            "reply_text": build_lane_switch_broker_contact_reply(),
            "active_case_outcome": "claim_lane_switch_broker",
            "service_lane": None,
        }

    reply_text = build_add_vehicle_continue_reply()
    active_outcome = "claim_lane_switch_continue"
    _clear_lane_switch_pending(add_car_id)
    if add_car_id:
        case = get_case_for_read(add_car_id)
        if case:
            from services.fiqa_api.wecom.add_vehicle_progress import build_add_vehicle_progress_reply

            progress_text, _menu, _masked = build_add_vehicle_progress_reply(
                case,
                external_userid=ext,
                open_case_count=1,
            )
            if progress_text:
                reply_text = progress_text
                active_outcome = "add_vehicle_progress_card"

    av_ctx = add_vehicle_context_for_user(ext)
    _emit_claim_routing_decision(
        normalized=normalized,
        intent_result=None,
        priority_rule=PRIORITY_LANE_SWITCH_CONTINUE_ADD_VEHICLE,
        decision=DECISION_CONTINUE_ADD_VEHICLE,
        reason="user_chose_continue_add_vehicle_after_lane_switch_prompt",
        response_type="add_vehicle_progress" if active_outcome == "add_vehicle_progress_card" else "add_vehicle_continue",
        **av_ctx,
    )

    return {
        "outcome": active_outcome,
        "case_id": add_car_id,
        "case_created": False,
        "reply_text": reply_text,
        "active_case_outcome": active_outcome,
        "service_lane": None,
    }


# --- P19H-3f-3 Claim Collision Resolver ---


def _claim_collision_pending(case: dict[str, Any] | None) -> dict[str, Any]:
    if not case:
        return {}
    raw = case.get("claim_collision_pending") or {}
    return dict(raw) if isinstance(raw, dict) else {}


def _claim_collision_pending_active(case: dict[str, Any] | None) -> bool:
    pending = _claim_collision_pending(case)
    state = str(pending.get("state") or "").strip().lower()
    if state == "resolved":
        return False
    return state == "pending_choice"


def find_claim_collision_pending_for_user(external_userid: str) -> tuple[str | None, dict[str, Any]]:
    """Return (anchor_case_id, pending_dict) when user has active collision resolver."""
    ext = (external_userid or "").strip()
    if not ext:
        return None, {}
    for case in list_open_claim_candidates_for_basics(ext):
        pending = _claim_collision_pending(case)
        if _claim_collision_pending_active(case):
            return str(case.get("case_id") or "").strip() or None, pending
    return None, {}


def _set_claim_collision_pending(
    case_id: str | None,
    *,
    trigger_text: str,
    candidate_claim_ids: list[str],
    reason: str,
    msg_id: str = "",
) -> None:
    if not case_id:
        return
    case = get_case_for_read(case_id) or {}
    if _claim_collision_pending_active(case):
        return
    now = datetime.now(timezone.utc).isoformat()
    update_claim_collision_pending(
        case_id,
        {
            "state": "pending_choice",
            "candidate_claim_ids": list(candidate_claim_ids),
            "trigger_text": (trigger_text or "").strip(),
            "trigger_msg_id": (msg_id or "").strip() or None,
            "created_at": now,
            "source": "wecom",
            "reason": reason,
        },
    )


def _clear_claim_collision_pending(case_id: str | None) -> None:
    if case_id:
        update_claim_collision_pending(case_id, None)


def _mark_collision_resolved(case_id: str | None, *, choice: str, resolved_claim_id: str | None = None) -> None:
    if not case_id:
        return
    pending = _claim_collision_pending(get_case_for_read(case_id))
    pending.update(
        {
            "state": "resolved",
            "choice": choice,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    if resolved_claim_id:
        pending["resolved_claim_id"] = resolved_claim_id
    update_claim_collision_pending(case_id, pending)


def is_claim_collision_continue(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw == "1":
        return True
    return any(m in raw for m in CLAIM_COLLISION_CONTINUE_MARKERS)


def is_claim_collision_new(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw == "2":
        return True
    return any(m in raw for m in CLAIM_COLLISION_NEW_MARKERS)


def is_claim_collision_contact(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw == "3":
        return True
    return any(m in raw for m in CLAIM_COLLISION_CONTACT_MARKERS)


def find_collision_resolved_start_new_claim(external_userid: str) -> str | None:
    ext = (external_userid or "").strip()
    if not ext:
        return None
    for case in list_open_claim_candidates_for_basics(ext):
        pending = _claim_collision_pending(case)
        if str(pending.get("choice") or "") == "start_new":
            resolved_id = str(pending.get("resolved_claim_id") or "").strip()
            if resolved_id:
                return resolved_id
    return None


def should_route_claim_collision_choice(normalized: dict[str, Any]) -> bool:
    ext = str(normalized.get("external_userid") or "").strip()
    text = str(normalized.get("text") or "").strip()
    if is_claim_collision_new(text) and find_collision_resolved_start_new_claim(ext):
        return True
    anchor_id, pending = find_claim_collision_pending_for_user(ext)
    if not anchor_id or not pending:
        return False
    return (
        is_claim_collision_continue(text)
        or is_claim_collision_new(text)
        or is_claim_collision_contact(text)
    )


def _maybe_flag_multi_claim_context(
    case_id: str | None,
    *,
    open_claim_count: int,
    trigger_text: str = "",
    source: str = "wecom_text",
) -> None:
    if not case_id or open_claim_count < 2:
        return
    add_case_risk_flag(
        case_id,
        "possible_multi_claim_context",
        workbench_tag="possible_multi_claim_context",
        details={
            "open_claim_count": open_claim_count,
            "source": source,
            "trigger_text_preview": (trigger_text or "")[:120] or None,
        },
        activity_note=(
            "系统：该客户有多份未完成事故记录；本条已按最近活跃事故记录归档，请 broker 核对。"
        ),
    )


def _emit_collision_resolver(
    *,
    normalized: dict[str, Any],
    intent_result: IntentResult | None,
    identity_decision: ClaimIdentityDecision,
    open_claims: list[dict[str, Any]],
    identity_kwargs: dict[str, Any],
) -> dict[str, Any]:
    from services.fiqa_api.wecom.reply import build_claim_collision_resolver_menu_payload

    multiple_open = len(open_claims) >= 2
    anchor_id = (
        str(identity_decision.case_id or "").strip()
        or str(open_claims[0].get("case_id") or "").strip()
        or None
    )
    candidate_ids = list(identity_decision.candidate_case_ids or [])
    if not candidate_ids:
        candidate_ids = [
            str(c.get("case_id") or "").strip()
            for c in open_claims
            if str(c.get("case_id") or "").strip()
        ]

    _set_claim_collision_pending(
        anchor_id,
        trigger_text=str(normalized.get("text") or ""),
        candidate_claim_ids=candidate_ids,
        reason="existing_open_claim_plus_new_accident_like_input",
        msg_id=str(normalized.get("msg_id") or ""),
    )

    menu = build_claim_collision_resolver_menu_payload(multiple_open=False)
    claim_ctx = claim_context_for_case(open_claims[0] if open_claims else None)
    _emit_claim_routing_decision(
        normalized=normalized,
        intent_result=intent_result,
        priority_rule=PRIORITY_CLAIM_IDENTITY_BROKER_CONFIRM,
        decision=DECISION_CLAIM_IDENTITY_BROKER_CONFIRM,
        reason="claim_collision_resolver_prompt",
        response_type=RESPONSE_CLAIM_IDENTITY_BROKER_CONFIRM,
        **identity_kwargs,
        **claim_ctx,
    )
    return {
        "outcome": "claim_collision_resolver",
        "case_id": anchor_id,
        "case_created": False,
        "reply_text": menu["head_content"],
        "menu_payload": menu,
        "active_case_outcome": "claim_collision_resolver",
        "service_lane": SERVICE_LANE_CLAIM,
        "needs_broker_manual_handle": False,
    }


def ingest_claim_collision_continue(
    normalized: dict[str, Any],
    *,
    anchor_id: str,
    pending: dict[str, Any],
) -> dict[str, Any]:
    from services.fiqa_api.wecom.reply import (
        build_claim_collision_continue_reply,
        build_claim_collision_multiple_open_reply,
        build_claim_missing_basics_reply,
    )

    candidate_ids = pending.get("candidate_claim_ids") or []
    target_id = str(newest_open_claim_id(
        [get_case_for_read(cid) or {"case_id": cid} for cid in candidate_ids if str(cid).strip()]
    ) or (candidate_ids[0] if candidate_ids else "") or "").strip()
    if not target_id:
        _mark_collision_resolved(anchor_id, choice="continue_blocked_no_target")
        return {
            "outcome": "claim_collision_multiple_open",
            "case_id": anchor_id,
            "case_created": False,
            "reply_text": build_claim_collision_multiple_open_reply(),
            "active_case_outcome": "claim_collision_multiple_open",
            "service_lane": SERVICE_LANE_CLAIM,
            "needs_broker_manual_handle": True,
        }

    trigger_text = str(pending.get("trigger_text") or "").strip()
    trigger_msg_id = str(pending.get("trigger_msg_id") or "").strip()
    msg_id = str(normalized.get("msg_id") or "").strip()

    if trigger_text and trigger_msg_id and not find_case_by_wecom_msg_id(trigger_msg_id):
        triage_stub = _build_claim_triage_stub(
            get_case_for_read(target_id) or {},
            extract_accident_basics_fields(trigger_text),
            injury_mentioned=message_mentions_injury(trigger_text),
        )
        append_follow_up_message(target_id, trigger_text, triage_stub)
        _append_claim_text_timeline(target_id, message_id=trigger_msg_id, text=trigger_text)
        _record_wecom_evidence(target_id, trigger_msg_id)

    _mark_collision_resolved(anchor_id, choice="continue_existing", resolved_claim_id=target_id)
    _clear_claim_collision_pending(anchor_id)

    case = get_case_for_read(target_id) or {}
    reply_text = build_claim_collision_continue_reply()
    missing = build_claim_missing_basics_reply(case)
    if missing and "请先确认" not in reply_text:
        reply_text = f"{reply_text}\n\n{missing}"

    _emit_claim_routing_decision(
        normalized=normalized,
        intent_result=None,
        priority_rule=PRIORITY_ACTIVE_CLAIM_BASICS_COLLECTION,
        decision=DECISION_COLLECT_CLAIM_BASICS,
        reason="collision_resolver_continue_existing",
        response_type=RESPONSE_CLAIM_MISSING_BASICS,
        created_case_id=target_id,
    )
    return {
        "outcome": "claim_collision_continue",
        "case_id": target_id,
        "case_created": False,
        "reply_text": reply_text,
        "active_case_outcome": "claim_collision_continue",
        "service_lane": SERVICE_LANE_CLAIM,
    }


def ingest_claim_collision_new(normalized: dict[str, Any], *, anchor_id: str, pending: dict[str, Any]) -> dict[str, Any]:
    from services.fiqa_api.wecom.reply import (
        build_claim_collision_multiple_open_reply,
        build_claim_start_injury_menu_payload,
    )

    candidate_ids = pending.get("candidate_claim_ids") or []
    _ = candidate_ids  # multi-open allowed — always create new Claim on choice 2

    existing_new_id = str(pending.get("resolved_claim_id") or "").strip()
    if existing_new_id and str(pending.get("choice") or "") == "start_new":
        case = get_case_for_read(existing_new_id) or {}
        injury_menu = build_claim_start_injury_menu_payload()
        return {
            "outcome": "claim_start_card_sent",
            "case_id": existing_new_id,
            "case_created": False,
            "reply_text": injury_menu["head_content"],
            "menu_payload": injury_menu,
            "active_case_outcome": "claim_start_card_sent",
            "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
            "service_lane": SERVICE_LANE_CLAIM,
        }

    trigger_text = str(pending.get("trigger_text") or "").strip()
    seed_normalized = dict(normalized)
    if trigger_text:
        seed_normalized["text"] = trigger_text
        seed_normalized["msg_id"] = str(pending.get("trigger_msg_id") or normalized.get("msg_id") or "")

    created = _create_claim_case(seed_normalized, injury_mentioned=message_mentions_injury(trigger_text))
    case_id = str(created.get("case_id") or "").strip() or None
    if not case_id:
        return {
            "outcome": "claim_case_not_found",
            "case_id": None,
            "case_created": False,
            "reply_text": None,
            "active_case_outcome": "claim_case_not_found",
            "service_lane": None,
        }

    from services.fiqa_api.inbox_triage.case_store import update_claim_workflow_state

    update_claim_workflow_state(
        case_id,
        claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
        guided_workflow_state=GUIDED_STATE_COLLECTING_TEXT,
    )
    _mark_collision_resolved(anchor_id, choice="start_new", resolved_claim_id=case_id)

    injury_menu = build_claim_start_injury_menu_payload()
    _emit_claim_routing_decision(
        normalized=normalized,
        intent_result=None,
        priority_rule=PRIORITY_CLAIM_START_NO_ACTIVE_CASE,
        decision=DECISION_START_CLAIM_FLOW,
        reason="collision_resolver_start_new_claim",
        response_type=RESPONSE_CLAIM_START,
        created_case_id=case_id,
        workflow_id="claim_simplified",
    )
    return {
        "outcome": "claim_start_card_sent",
        "case_id": case_id,
        "case_created": True,
        "reply_text": injury_menu["head_content"],
        "menu_payload": injury_menu,
        "active_case_outcome": "claim_start_card_sent",
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
        "service_lane": SERVICE_LANE_CLAIM,
    }


def ingest_claim_collision_contact(normalized: dict[str, Any], *, anchor_id: str) -> dict[str, Any]:
    from services.fiqa_api.wecom.reply import build_claim_collision_contact_broker_reply

    _mark_collision_resolved(anchor_id, choice="contact_broker")
    _clear_claim_collision_pending(anchor_id)
    _emit_claim_routing_decision(
        normalized=normalized,
        intent_result=None,
        priority_rule=PRIORITY_CLAIM_IDENTITY_BROKER_CONFIRM,
        decision=DECISION_CONTACT_BROKER_ACK,
        reason="collision_resolver_contact_broker",
        response_type="contact_broker_ack",
    )
    return {
        "outcome": "claim_collision_contact",
        "case_id": anchor_id,
        "case_created": False,
        "reply_text": build_claim_collision_contact_broker_reply(),
        "active_case_outcome": "claim_collision_contact",
        "service_lane": SERVICE_LANE_CLAIM,
        "needs_broker_manual_handle": True,
    }


def ingest_claim_collision_choice(normalized: dict[str, Any]) -> dict[str, Any]:
    ext = str(normalized.get("external_userid") or "").strip()
    text = str(normalized.get("text") or "").strip()

    if is_claim_collision_new(text):
        existing_new_id = find_collision_resolved_start_new_claim(ext)
        if existing_new_id:
            from services.fiqa_api.wecom.reply import build_claim_start_injury_menu_payload

            injury_menu = build_claim_start_injury_menu_payload()
            return {
                "outcome": "claim_start_card_sent",
                "case_id": existing_new_id,
                "case_created": False,
                "reply_text": injury_menu["head_content"],
                "menu_payload": injury_menu,
                "active_case_outcome": "claim_start_card_sent",
                "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
                "service_lane": SERVICE_LANE_CLAIM,
            }

    anchor_id, pending = find_claim_collision_pending_for_user(ext)
    if not anchor_id or not pending:
        return {
            "outcome": "claim_collision_no_pending",
            "case_id": None,
            "case_created": False,
            "reply_text": None,
            "active_case_outcome": "claim_collision_no_pending",
            "service_lane": None,
        }

    if is_claim_collision_continue(text):
        return ingest_claim_collision_continue(normalized, anchor_id=anchor_id, pending=pending)
    if is_claim_collision_new(text):
        return ingest_claim_collision_new(normalized, anchor_id=anchor_id, pending=pending)
    if is_claim_collision_contact(text):
        return ingest_claim_collision_contact(normalized, anchor_id=anchor_id)
    return {
        "outcome": "claim_collision_unrecognized_choice",
        "case_id": anchor_id,
        "case_created": False,
        "reply_text": None,
        "active_case_outcome": "claim_collision_unrecognized_choice",
        "service_lane": SERVICE_LANE_CLAIM,
    }


def _active_add_car_blocks_claim_start(
    *,
    text: str,
    intent_result: IntentResult,
    injury_mentioned: bool,
) -> bool:
    """True when active Add Vehicle should show lane-switch confirm card instead of starting Claim."""
    if injury_mentioned:
        return False
    if is_claim_lane_switch_confirm(text):
        return False
    if is_claim_question_not_guided_intake(text):
        return False
    return is_claim_guided_start_message(text)


# Prompt aliases
is_claim_start_intent = is_claim_guided_start_message


def _kernel_basics_missing_keys(case: dict[str, Any]) -> set[str]:
    """Accident basics still needed per CLAIM_SIMPLIFIED_DEFINITION."""
    view = evaluate_claim_simplified_snapshot(case)
    return {
        item["key"]
        for item in view.get("missing", [])
        if item.get("key") in CLAIM_ACCIDENT_BASICS_FIELDS
    }


def is_claim_substantive_with_questions(text: str) -> bool:
    """Accident facts + how-to questions → keep claim_lite minimal lane."""
    raw = (text or "").strip()
    lowered = raw.lower()
    if not any(m in raw or m in lowered for m in CLAIM_QUESTION_MARKERS):
        return False
    return has_accident_basics_signals(raw) and len(raw) >= 28


def is_claim_question_not_guided_intake(text: str) -> bool:
    """Conservative gate: how-to / liability questions skip guided intake creation."""
    raw = (text or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    if not any(m in raw or m in lowered for m in CLAIM_QUESTION_MARKERS):
        return False
    if has_accident_basics_signals(raw) and len(raw) >= 28:
        return False
    if is_claim_guided_start_message(raw) and "怎么办" not in raw:
        return False
    return True


is_claim_question_intent = is_claim_question_not_guided_intake


def is_claim_progress_inquiry(text: str) -> bool:
    return is_claim_status_request(text)


def should_route_claim_status_request(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    """Route Claim Status Card before guided basics ingestion."""
    text = str(normalized.get("text") or "").strip()
    if not is_claim_status_request(text):
        return False
    if is_claim_guided_start_message(text):
        return False
    return True


def ingest_claim_status_request(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> dict[str, Any]:
    """Return Claim Status Card for active case, or no-active guidance."""
    from services.fiqa_api.wecom.reply import (
        build_claim_status_card_reply,
        build_claim_status_no_active_reply,
    )

    ext = str(normalized.get("external_userid") or "").strip()
    open_claims = list_open_claim_candidates_for_basics(ext)
    active = find_active_claim_case_for_basics(ext)
    if not active:
        _emit_claim_routing_decision(
            normalized=normalized,
            intent_result=intent_result,
            priority_rule=PRIORITY_CLAIM_START_NO_ACTIVE_CASE,
            decision=DECISION_CLAIM_QUESTION_SAFE_REPLY,
            reason="claim_status_request_without_active_case",
            response_type="claim_status_no_active",
        )
        return {
            "outcome": "claim_status_no_active",
            "case_id": None,
            "case_created": False,
            "reply_text": build_claim_status_no_active_reply(),
            "menu_payload": None,
            "active_case_outcome": "claim_status_no_active",
            "service_lane": None,
        }

    case_id = str(active.get("case_id") or "").strip() or None
    reply_text = build_claim_status_card_reply(
        active,
        multiple_open_claims=len(open_claims) > 1,
    )
    claim_ctx = claim_context_for_case(active)
    _emit_claim_routing_decision(
        normalized=normalized,
        intent_result=intent_result,
        priority_rule=PRIORITY_ACTIVE_CLAIM_BASICS_COLLECTION,
        decision=DECISION_COLLECT_CLAIM_BASICS,
        reason="claim_status_request_active_case",
        response_type="claim_status_card",
        created_case_id=case_id,
        **claim_ctx,
    )
    return {
        "outcome": "claim_status_card",
        "case_id": case_id,
        "case_created": False,
        "reply_text": reply_text,
        "menu_payload": None,
        "active_case_outcome": "claim_status_card",
        "claim_phase": active.get("claim_phase"),
        "service_lane": SERVICE_LANE_CLAIM,
    }


def _case_sort_key(case: dict[str, Any]) -> str:
    return str(case.get("updated_at") or case.get("created_at") or "")


def list_open_claim_candidates_for_basics(external_userid: str) -> list[dict[str, Any]]:
    """All open guided claim cases for this WeCom user (not broker_done), newest first."""
    ext = (external_userid or "").strip()
    if not ext:
        return []
    matches: list[dict[str, Any]] = []
    for case in list_all_cases_for_read():
        if not is_open_claim_candidate_for_basics(case, ext):
            continue
        matches.append(case)
    matches.sort(key=_case_sort_key, reverse=True)
    return matches


def find_active_claim_case_for_basics(external_userid: str) -> dict[str, Any] | None:
    """Return one open claim for routing checks only — ingestion uses resolve_claim_identity()."""
    candidates = list_open_claim_candidates_for_basics(external_userid)
    return candidates[0] if candidates else None


def should_route_claim_guided_workflow(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    """Route to Claim guided basics handler (before minimal claim_lite lane)."""
    text = str(normalized.get("text") or "").strip()
    ext = str(normalized.get("external_userid") or "")

    if is_claim_status_request(text):
        return False

    if is_explicit_add_car_restart(text):
        return False

    active = find_active_claim_case_for_basics(ext)
    if active:
        phase = derive_claim_phase(active)
        if phase in (
            CLAIM_PHASE_STARTED,
            CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
            CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        ):
            return True
        return False

    if intent_result.confidence != "high" or intent_result.intent != "claim_intake":
        return False

    if is_claim_question_not_guided_intake(text):
        return False

    if is_claim_substantive_with_questions(text):
        return False

    if is_claim_guided_start_message(text):
        return True

    return False


def should_route_claim_holding_ack(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    """Route ambiguous accident-like messages to Holding ack — no formal Claim case."""
    text = str(normalized.get("text") or "").strip()
    ext = str(normalized.get("external_userid") or "")

    if is_claim_status_request(text):
        return False

    if find_active_claim_case_for_basics(ext):
        return False
    if is_explicit_add_car_restart(text):
        return False
    if is_claim_guided_start_message(text):
        return False
    if is_claim_question_not_guided_intake(text):
        return False
    if is_claim_substantive_with_questions(text):
        return False
    if intent_result.matched_by in ("menu_number", "menu_id", "menu_text"):
        return False
    if is_claim_passive_narrative(text):
        return True
    if intent_result.confidence == "high" and intent_result.intent == "claim_intake":
        return True
    return False


def ingest_claim_holding_ack(normalized: dict[str, Any]) -> dict[str, Any]:
    """Acknowledge ambiguous accident content without creating a formal Claim case."""
    from services.fiqa_api.wecom.reply import build_claim_holding_ack_reply

    return {
        "outcome": "claim_holding_ack",
        "case_id": None,
        "case_created": False,
        "reply_text": build_claim_holding_ack_reply(),
        "menu_payload": None,
        "active_case_outcome": "claim_holding_ack",
        "service_lane": None,
    }


def should_route_claim_question_safe_reply(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    text = str(normalized.get("text") or "").strip()
    if find_active_claim_case_for_basics(str(normalized.get("external_userid") or "")):
        return False
    if is_claim_question_not_guided_intake(text):
        return True
    if intent_result.confidence != "high" or intent_result.intent != "claim_intake":
        return False
    return is_claim_question_not_guided_intake(text)


def _collected_field_names(case: dict[str, Any]) -> set[str]:
    return {str(x).lower() for x in (case.get("collected_fields") or []) if str(x).strip()}


def _build_claim_triage_stub(
    case: dict[str, Any],
    extracted: dict[str, str | None],
    *,
    injury_mentioned: bool = False,
) -> dict[str, Any]:
    already = _collected_field_names(case)
    known_facts = dict(case.get("known_facts") or {}) if isinstance(case.get("known_facts"), dict) else {}
    newly_collected: list[str] = []

    for field in CLAIM_ACCIDENT_BASICS_FIELDS:
        value = extracted.get(field)
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

    still_needed = [f for f in CLAIM_ACCIDENT_BASICS_FIELDS if f.lower() not in seen]
    handoff_ready = not still_needed

    stub: dict[str, Any] = {
        "issue_category": case.get("issue_category") or "claim_intake",
        "urgency": "high" if injury_mentioned else (case.get("urgency") or "high"),
        "client_prep": "",
        "client_reply_draft": "",
        "manual_followup_needed": True,
        "collected_fields": newly_collected,
        "still_needed_fields": still_needed,
        "handoff_ready": handoff_ready,
        "known_facts": known_facts,
        "broker_next_step": (
            "Claim accident basics complete — await photos (P19H-3)."
            if handoff_ready
            else "Claim guided workflow — collect accident basics."
        ),
    }
    if injury_mentioned:
        stub["workbench_tags"] = list(
            dict.fromkeys([*(case.get("workbench_tags") or []), "Urgent", "Manual Handle"])
        )
    return stub


def _build_new_claim_case_stub(*, injury_mentioned: bool = False) -> dict[str, Any]:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Claim guided workflow — collect accident basics.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "collected_fields": [],
        "still_needed_fields": list(CLAIM_ACCIDENT_BASICS_FIELDS),
        "known_facts": {},
        "claim_phase": CLAIM_PHASE_STARTED,
        "guided_workflow_state": GUIDED_STATE_COLLECTING_TEXT,
        "workbench_tags": ["Urgent", "Manual Handle"] if injury_mentioned else ["Claim"],
    }


def _c1_already_sent(case: dict[str, Any]) -> bool:
    state = case.get("claim_flow_state") or {}
    if not isinstance(state, dict):
        return False
    return bool(str(state.get("c1_stage_complete_sent_at") or "").strip())


def _append_claim_text_timeline(case_id: str | None, *, message_id: str, text: str) -> None:
    if not case_id or not (text or "").strip():
        return
    append_claim_timeline_event(
        case_id,
        build_claim_timeline_event(
            event_type="customer_text",
            source_channel="wecom",
            actor="customer",
            message_id=message_id or None,
            text=(text or "").strip(),
        ),
    )


def _append_claim_started(case_id: str | None) -> None:
    if not case_id:
        return
    append_claim_timeline_event(
        case_id,
        build_claim_timeline_event(
            event_type="claim_started",
            source_channel="wecom",
            actor="customer",
            text="Claim story recording started",
        ),
    )


def _append_basics_complete_if_needed(case_id: str | None, case: dict[str, Any]) -> None:
    if not case_id or not is_accident_basics_complete(case):
        return
    facts = case.get("known_facts") or {}
    append_claim_timeline_event(
        case_id,
        build_claim_timeline_event(
            event_type="basics_complete",
            source_channel="wecom",
            actor="system",
            metadata={
                "facts_snapshot": {
                    "accident_datetime": str(facts.get("accident_datetime") or "").strip() or None,
                    "accident_location": str(facts.get("accident_location") or "").strip() or None,
                    "accident_description": str(facts.get("accident_description") or "").strip() or None,
                    "injury_status": str(facts.get("injury_status") or "").strip() or None,
                }
            },
        ),
    )


def ingest_claim_injury_quick_reply(
    normalized: dict[str, Any],
    *,
    injury_value: str,
) -> dict[str, Any]:
    """Handle injury quick-reply button click on active Claim case."""
    from services.fiqa_api.inbox_triage.case_store import update_claim_workflow_state
    from services.fiqa_api.wecom.reply import (
        build_claim_safety_manual_reply,
        build_claim_start_card_reply,
    )

    msg_id = str(normalized.get("msg_id") or "").strip()
    ext = str(normalized.get("external_userid") or "").strip()
    value = (injury_value or "").strip().lower()

    label_map = {
        "no": ("没有受伤", "no"),
        "yes": ("有人受伤", "yes"),
        "unknown": ("不确定", "unknown"),
    }
    if value not in label_map:
        return {
            "outcome": "claim_injury_reply_invalid",
            "case_id": None,
            "case_created": False,
            "reply_text": build_claim_start_card_reply(injury_mentioned=False),
            "active_case_outcome": "claim_injury_reply_invalid",
            "service_lane": SERVICE_LANE_CLAIM,
        }

    click_label, injury_status = label_map[value]
    open_claims = list_open_claim_candidates_for_basics(ext)
    case = open_claims[0] if open_claims else None
    case_id = str(case.get("case_id") or "").strip() if case else None

    if not case_id:
        from services.fiqa_api.wecom.reply import build_claim_injury_holding_gate_reply

        return {
            "outcome": "claim_injury_holding_gate",
            "case_id": None,
            "case_created": False,
            "reply_text": build_claim_injury_holding_gate_reply(),
            "menu_payload": None,
            "active_case_outcome": "claim_injury_holding_gate",
            "service_lane": None,
            "needs_broker_manual_handle": False,
        }

    patch_case_known_facts(case_id, {"injury_status": injury_status})
    append_claim_timeline_event(
        case_id,
        build_claim_timeline_event(
            event_type="customer_text",
            source_channel="wecom",
            actor="customer",
            message_id=msg_id or None,
            text=click_label,
            metadata={"quick_reply_key": "injury_status", "quick_reply_value": injury_status},
        ),
    )

    needs_manual = value == "yes"
    if needs_manual and case_id:
        refreshed = get_case_for_read(case_id) or case or {}
        update_claim_workflow_state(case_id, **transition_to_manual_handle(refreshed))

    if needs_manual:
        reply_text = build_claim_safety_manual_reply()
        active_outcome = "claim_injury_manual_handle"
    elif value == "unknown":
        reply_text = (
            "好的，已记录。\n\n"
            "如果安全，请用一条消息告诉我：\n"
            "大概什么时候、在哪里、发生了什么事。\n"
            "不用写得很正式，说清楚就行。"
        )
        active_outcome = "claim_injury_reply_recorded"
    else:
        reply_text = (
            "好的，已记录。\n\n"
            "请用一条消息告诉我：\n"
            "大概什么时候、在哪里、发生了什么事。\n"
            "不用写得很正式，说清楚就行。"
        )
        active_outcome = "claim_injury_reply_recorded"

    return {
        "outcome": "attached",
        "case_id": case_id,
        "case_created": not bool(open_claims),
        "reply_text": reply_text,
        "menu_payload": None,
        "active_case_outcome": active_outcome,
        "service_lane": SERVICE_LANE_CLAIM,
        "needs_broker_manual_handle": needs_manual,
    }


def _create_claim_case(
    normalized: dict[str, Any],
    *,
    injury_mentioned: bool = False,
) -> dict[str, Any]:
    text = str(normalized.get("text") or "").strip() or "[客户] WeCom: Claim start"
    saved = save_case(
        text,
        _build_new_claim_case_stub(injury_mentioned=injury_mentioned),
        service_lane=SERVICE_LANE_CLAIM,
    )
    case_id = str(saved.get("case_id") or "").strip()
    ext = str(normalized.get("external_userid") or "").strip()
    if case_id and ext:
        bind_case_channel_identity(
            case_id,
            wecom_external_userid=ext,
            wecom_open_kf_id=str(normalized.get("open_kf_id") or "").strip() or None,
        )
    _record_wecom_evidence(case_id, str(normalized.get("msg_id") or ""))
    _append_claim_started(case_id)
    if text := str(normalized.get("text") or "").strip():
        _append_claim_text_timeline(case_id, message_id=str(normalized.get("msg_id") or ""), text=text)
    return {"case_id": case_id, "case_created": True, "outcome": "created"}


def _build_claim_start_h5_intake_response(
    case_id: str,
    *,
    external_userid: str | None,
) -> dict[str, Any]:
    """Build Claim Start Card with H5 intake form link as primary CTA."""
    from services.fiqa_api.inbox_triage.h5_task_link import (
        mask_h5_task_url,
        mint_h5_claim_intake_form_link,
    )
    from services.fiqa_api.wecom.reply import (
        build_claim_start_card_reply,
        build_claim_start_h5_intake_card_payload,
    )

    if not case_id:
        return {
            "reply_text": build_claim_start_card_reply(injury_mentioned=False),
            "menu_payload": None,
            "h5_task_link_masked": None,
        }
    try:
        h5_url = mint_h5_claim_intake_form_link(
            case_id=case_id,
            external_userid=external_userid,
        )
    except ValueError:
        return {
            "reply_text": build_claim_start_card_reply(injury_mentioned=False),
            "menu_payload": None,
            "h5_task_link_masked": None,
        }
    menu = build_claim_start_h5_intake_card_payload(h5_url=h5_url)
    return {
        "reply_text": menu["head_content"],
        "menu_payload": menu,
        "h5_task_link_masked": mask_h5_task_url(h5_url),
    }


def _build_claim_c1_h5_response(
    case: dict[str, Any],
    *,
    external_userid: str | None,
    already_complete: bool = False,
) -> dict[str, Any]:
    """Build Claim C1 reply with WeCom H5 evidence upload button when case_id is known."""
    from services.fiqa_api.inbox_triage.h5_task_link import (
        mask_h5_task_url,
        mint_h5_claim_evidence_pack_link,
    )
    from services.fiqa_api.wecom.reply import (
        build_claim_basics_already_complete_reply,
        build_claim_c1_h5_evidence_card_payload,
        build_claim_stage_complete_c1_reply,
    )

    text_fallback = (
        build_claim_basics_already_complete_reply(case)
        if already_complete
        else build_claim_stage_complete_c1_reply(case)
    )
    case_id = str(case.get("case_id") or "").strip()
    if not case_id:
        return {
            "reply_text": text_fallback,
            "menu_payload": None,
            "h5_task_link_masked": None,
        }

    try:
        h5_url = mint_h5_claim_evidence_pack_link(
            case_id=case_id,
            external_userid=external_userid,
        )
    except ValueError:
        return {
            "reply_text": text_fallback,
            "menu_payload": None,
            "h5_task_link_masked": None,
        }

    menu = build_claim_c1_h5_evidence_card_payload(
        h5_url=h5_url,
        case=case,
        already_complete=already_complete,
    )
    return {
        "reply_text": menu["head_content"],
        "menu_payload": menu,
        "h5_task_link_masked": mask_h5_task_url(h5_url),
    }


def ingest_claim_basics_message(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> dict[str, Any]:
    """Create/update guided claim case and return WeCom reply metadata."""
    from services.fiqa_api.inbox_triage.case_store import update_claim_workflow_state
    from services.fiqa_api.wecom.reply import (
        build_claim_basics_already_complete_reply,
        build_claim_interrupt_safety_manual_reply,
        build_claim_missing_basics_reply,
        build_claim_safety_manual_reply,
        build_claim_stage_complete_c1_reply,
        build_claim_start_card_reply,
        build_claim_start_injury_menu_payload,
    )

    msg_id = str(normalized.get("msg_id") or "").strip()
    text = str(normalized.get("text") or "").strip()
    ext = str(normalized.get("external_userid") or "").strip()
    injury_mentioned = message_mentions_injury(text)

    anchor_id, collision_pending = find_claim_collision_pending_for_user(ext)
    if anchor_id and collision_pending and not should_route_claim_collision_choice(normalized):
        return _emit_collision_resolver(
            normalized=normalized,
            intent_result=intent_result,
            identity_decision=ClaimIdentityDecision(
                tier="B",
                action="broker_confirm",
                case_id=anchor_id,
                score=80,
                reasons=["collision_pending_repeat_prompt"],
                candidate_case_ids=list(collision_pending.get("candidate_claim_ids") or []),
            ),
            open_claims=list_open_claim_candidates_for_basics(ext),
            identity_kwargs={},
        )

    existing_by_msg = find_case_by_wecom_msg_id(msg_id)
    if existing_by_msg:
        case = get_case_for_read(existing_by_msg) or {}
        phase = derive_claim_phase(case)
        if phase == CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE:
            c1 = _build_claim_c1_h5_response(
                case,
                external_userid=ext or None,
                already_complete=True,
            )
            reply = c1["reply_text"]
            menu_payload = c1["menu_payload"]
            h5_masked = c1["h5_task_link_masked"]
        else:
            reply = build_claim_missing_basics_reply(case)
            menu_payload = None
            h5_masked = None
        return {
            "outcome": "duplicate_msg",
            "case_id": existing_by_msg,
            "case_created": False,
            "reply_text": reply,
            "menu_payload": menu_payload,
            "h5_task_link_masked": h5_masked,
            "active_case_outcome": "claim_duplicate_msg",
            "service_lane": SERVICE_LANE_CLAIM,
        }

    if find_open_add_car_case_by_external_userid(ext) and _active_add_car_blocks_claim_start(
        text=text,
        intent_result=intent_result,
        injury_mentioned=injury_mentioned,
    ):
        from services.fiqa_api.wecom.reply import build_claim_lane_switch_menu_payload

        add_car_id = find_open_add_car_case_by_external_userid(ext)
        add_car_case = get_case_for_read(add_car_id) if add_car_id else None
        if _lane_switch_pending_confirm(add_car_case):
            lane_menu = build_claim_lane_switch_menu_payload()
            av_ctx = add_vehicle_context_for_user(ext)
            _emit_claim_routing_decision(
                normalized=normalized,
                intent_result=intent_result,
                priority_rule=PRIORITY_CLAIM_INTERRUPT_DURING_ACTIVE_ADD_VEHICLE,
                decision=DECISION_LANE_SWITCH_PROMPT,
                reason="claim_start_repeat_while_lane_switch_pending_confirm",
                response_type=RESPONSE_CLAIM_LANE_SWITCH,
                safety_flags=("injury_mentioned",) if injury_mentioned else (),
                **av_ctx,
            )
            return {
                "outcome": "claim_lane_switch_prompt",
                "case_id": add_car_id,
                "case_created": False,
                "reply_text": lane_menu["head_content"],
                "menu_payload": lane_menu,
                "active_case_outcome": "claim_lane_switch_prompt",
                "service_lane": None,
            }

        _set_lane_switch_pending(add_car_id, trigger_text=text)
        lane_menu = build_claim_lane_switch_menu_payload()
        av_ctx = add_vehicle_context_for_user(ext)
        _emit_claim_routing_decision(
            normalized=normalized,
            intent_result=intent_result,
            priority_rule=PRIORITY_CLAIM_INTERRUPT_DURING_ACTIVE_ADD_VEHICLE,
            decision=DECISION_LANE_SWITCH_PROMPT,
            reason="claim_start_intent_outranks_active_add_vehicle_secondary_topic",
            response_type=RESPONSE_CLAIM_LANE_SWITCH,
            safety_flags=("injury_mentioned",) if injury_mentioned else (),
            **av_ctx,
        )
        return {
            "outcome": "claim_lane_switch_prompt",
            "case_id": add_car_id,
            "case_created": False,
            "reply_text": lane_menu["head_content"],
            "menu_payload": lane_menu,
            "active_case_outcome": "claim_lane_switch_prompt",
            "service_lane": None,
        }

    add_car_active = bool(find_open_add_car_case_by_external_userid(ext))

    case_id: str | None = None
    case_created = False
    open_claims = list_open_claim_candidates_for_basics(ext)
    identity_decision = resolve_claim_identity(
        external_userid=ext,
        incoming_text=text,
        open_claims=open_claims,
        channel="wecom_text",
    )
    if (
        injury_mentioned
        and identity_decision.action == "broker_confirm"
        and len(open_claims) == 1
    ):
        only_id = str(open_claims[0].get("case_id") or "").strip() or None
        identity_decision = ClaimIdentityDecision(
            tier="A",
            action="append_existing",
            case_id=only_id,
            score=90,
            rule_ids=["ID-INJURY"],
            reasons=["injury_override_append_single_open_claim"],
            candidate_case_ids=[only_id] if only_id else [],
        )
    identity_kwargs = identity_context_for_decision(identity_decision)

    if identity_decision.action == "broker_confirm":
        return _emit_collision_resolver(
            normalized=normalized,
            intent_result=intent_result,
            identity_decision=identity_decision,
            open_claims=open_claims,
            identity_kwargs=identity_kwargs,
        )

    if identity_decision.action == "create_new":
        created = _create_claim_case(normalized, injury_mentioned=injury_mentioned)
        case_id = created["case_id"]
        case_created = created["case_created"]
        case = get_case_for_read(case_id) or {}
    else:
        case_id = str(identity_decision.case_id or "").strip() or None
        case = get_case_for_read(case_id) or {} if case_id else {}
        if case_id and len(open_claims) >= 2 and identity_decision.action == "append_existing":
            _maybe_flag_multi_claim_context(
                case_id,
                open_claim_count=len(open_claims),
                trigger_text=text,
                source="wecom_text",
            )

    if injury_mentioned and case_id:
        manual_patch = transition_to_manual_handle(case)
        update_claim_workflow_state(case_id, **manual_patch)

    phase = derive_claim_phase(case)
    if phase == CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE:
        c1 = _build_claim_c1_h5_response(
            case,
            external_userid=ext or None,
            already_complete=True,
        )
        return {
            "outcome": "claim_basics_already_complete",
            "case_id": case_id,
            "case_created": case_created,
            "reply_text": c1["reply_text"],
            "menu_payload": c1["menu_payload"],
            "h5_task_link_masked": c1["h5_task_link_masked"],
            "active_case_outcome": "claim_basics_already_complete",
            "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
            "service_lane": SERVICE_LANE_CLAIM,
        }

    extracted = extract_accident_basics_fields(text)
    has_extractable = any(extracted.values())

    if not has_extractable and not case_created:
        reply_text = build_claim_missing_basics_reply(case)
        update_claim_workflow_state(
            case_id,
            claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
            guided_workflow_state=GUIDED_STATE_COLLECTING_TEXT,
        )
        claim_ctx = claim_context_for_case(case)
        _emit_claim_routing_decision(
            normalized=normalized,
            intent_result=intent_result,
            priority_rule=PRIORITY_ACTIVE_CLAIM_BASICS_COLLECTION,
            decision=DECISION_COLLECT_CLAIM_BASICS,
            reason="active_claim_waiting_for_accident_basics",
            response_type=RESPONSE_CLAIM_MISSING_BASICS,
            created_case_id=case_id,
            **identity_kwargs,
            **claim_ctx,
        )
        return {
            "outcome": "claim_start_no_fields",
            "case_id": case_id,
            "case_created": case_created,
            "reply_text": reply_text,
            "active_case_outcome": "claim_basics_prompt",
            "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
            "service_lane": SERVICE_LANE_CLAIM,
        }

    if case_created and not has_extractable:
        menu_payload = None
        h5_masked = None
        if injury_mentioned:
            reply_text = (
                build_claim_interrupt_safety_manual_reply()
                if add_car_active
                else build_claim_safety_manual_reply()
            )
            if add_car_active:
                av_ctx = add_vehicle_context_for_user(ext)
                _emit_claim_routing_decision(
                    normalized=normalized,
                    intent_result=intent_result,
                    priority_rule=PRIORITY_INJURY_SAFETY_OVERRIDE,
                    decision=DECISION_SAFETY_MANUAL_REPLY,
                    reason="injury_marker_detected_highest_priority",
                    response_type=RESPONSE_CLAIM_SAFETY_MANUAL,
                    safety_flags=("injury_mentioned",),
                    created_case_id=case_id,
                    switched_workflow="claim",
                    workflow_id="claim_simplified",
                    **identity_kwargs,
                    **av_ctx,
                )
            else:
                claim_ctx = claim_context_for_case(case)
                _emit_claim_routing_decision(
                    normalized=normalized,
                    intent_result=intent_result,
                    priority_rule=PRIORITY_INJURY_SAFETY_OVERRIDE,
                    decision=DECISION_SAFETY_MANUAL_REPLY,
                    reason="injury_marker_detected_highest_priority",
                    response_type=RESPONSE_CLAIM_SAFETY_MANUAL,
                    safety_flags=("injury_mentioned",),
                    created_case_id=case_id,
                    **identity_kwargs,
                    **claim_ctx,
                )
        else:
            start_h5 = _build_claim_start_h5_intake_response(
                case_id or "",
                external_userid=ext,
            )
            reply_text = start_h5["reply_text"]
            menu_payload = start_h5["menu_payload"]
            h5_masked = start_h5.get("h5_task_link_masked")
            if add_car_active and is_claim_lane_switch_confirm(text):
                av_ctx = add_vehicle_context_for_user(ext)
                _emit_claim_routing_decision(
                    normalized=normalized,
                    intent_result=intent_result,
                    priority_rule=PRIORITY_CLAIM_CONFIRMED_START,
                    decision=DECISION_START_CLAIM_FLOW,
                    reason="user_confirmed_claim_start_during_active_workflow",
                    response_type=RESPONSE_CLAIM_START,
                    created_case_id=case_id,
                    switched_workflow="claim",
                    workflow_id="claim_simplified",
                    **identity_kwargs,
                    **av_ctx,
                )
            elif not add_car_active:
                _emit_claim_routing_decision(
                    normalized=normalized,
                    intent_result=intent_result,
                    priority_rule=PRIORITY_CLAIM_START_NO_ACTIVE_CASE,
                    decision=DECISION_START_CLAIM_FLOW,
                    reason="claim_start_intent_without_active_workflow",
                    response_type=RESPONSE_CLAIM_START,
                    created_case_id=case_id,
                    workflow_id="claim_simplified",
                    active_workflow=None,
                    **identity_kwargs,
                )
        update_claim_workflow_state(
            case_id,
            claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
            guided_workflow_state=GUIDED_STATE_COLLECTING_TEXT,
        )
        return {
            "outcome": "claim_injury_manual_handle" if injury_mentioned else "claim_start_card_sent",
            "case_id": case_id,
            "case_created": True,
            "reply_text": reply_text,
            "menu_payload": menu_payload if not injury_mentioned else None,
            "h5_task_link_masked": h5_masked if not injury_mentioned else None,
            "active_case_outcome": (
                "claim_injury_manual_handle" if injury_mentioned else "claim_start_card_sent"
            ),
            "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
            "service_lane": SERVICE_LANE_CLAIM,
            "needs_broker_manual_handle": injury_mentioned,
        }

    if has_extractable:
        triage_stub = _build_claim_triage_stub(case, extracted, injury_mentioned=injury_mentioned)
        updated = append_follow_up_message(case_id, text or "(no text)", triage_stub)
        if updated is None:
            return {
                "outcome": "case_not_found",
                "case_id": None,
                "case_created": False,
                "reply_text": None,
                "active_case_outcome": "claim_case_not_found",
                "service_lane": None,
            }
        _append_claim_text_timeline(case_id, message_id=msg_id, text=text)
        _record_wecom_evidence(case_id, msg_id)
        refreshed = get_case_for_read(case_id) or updated
        _append_basics_complete_if_needed(case_id, refreshed)
        refreshed = get_case_for_read(case_id) or refreshed

        if injury_mentioned:
            update_claim_workflow_state(
                case_id,
                **transition_to_manual_handle(refreshed),
            )
            refreshed = get_case_for_read(case_id) or refreshed
            reply_text = (
                build_claim_interrupt_safety_manual_reply()
                if add_car_active
                else build_claim_safety_manual_reply()
            )
            if add_car_active:
                av_ctx = add_vehicle_context_for_user(ext)
                _emit_claim_routing_decision(
                    normalized=normalized,
                    intent_result=intent_result,
                    priority_rule=PRIORITY_INJURY_SAFETY_OVERRIDE,
                    decision=DECISION_SAFETY_MANUAL_REPLY,
                    reason="injury_marker_detected_highest_priority",
                    response_type=RESPONSE_CLAIM_SAFETY_MANUAL,
                    safety_flags=("injury_mentioned",),
                    created_case_id=case_id,
                    switched_workflow="claim",
                    workflow_id="claim_simplified",
                    **identity_kwargs,
                    **av_ctx,
                )
            else:
                claim_ctx = claim_context_for_case(refreshed)
                _emit_claim_routing_decision(
                    normalized=normalized,
                    intent_result=intent_result,
                    priority_rule=PRIORITY_INJURY_SAFETY_OVERRIDE,
                    decision=DECISION_SAFETY_MANUAL_REPLY,
                    reason="injury_marker_detected_highest_priority",
                    response_type=RESPONSE_CLAIM_SAFETY_MANUAL,
                    safety_flags=("injury_mentioned",),
                    created_case_id=case_id,
                    **identity_kwargs,
                    **claim_ctx,
                )
            kernel_view = evaluate_claim_simplified_snapshot(refreshed)
            _log_event(
                "wecom_claim_basics_ingest_v1",
                {
                    "msg_id": msg_id,
                    "case_id": case_id,
                    "outcome": "claim_injury_manual_handle",
                    "injury_mentioned": True,
                    "kernel_current_step": kernel_view.get("current_step"),
                },
            )
            return {
                "outcome": "attached",
                "case_id": case_id,
                "case_created": case_created,
                "reply_text": reply_text,
                "active_case_outcome": "claim_injury_manual_handle",
                "claim_phase": refreshed.get("claim_phase"),
                "service_lane": SERVICE_LANE_CLAIM,
                "needs_broker_manual_handle": True,
            }

        if is_accident_basics_complete(refreshed):
            sent_c1_before = _c1_already_sent(refreshed)
            update_claim_workflow_state(
                case_id,
                claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
                guided_workflow_state=GUIDED_STATE_COLLECTING_TEXT,
                c1_stage_complete_sent_at=(
                    datetime.now(timezone.utc).isoformat() if not sent_c1_before else None
                ),
            )
            refreshed = get_case_for_read(case_id) or refreshed
            _append_basics_complete_if_needed(case_id, refreshed)
            refreshed = get_case_for_read(case_id) or refreshed
            if sent_c1_before:
                c1 = _build_claim_c1_h5_response(
                    refreshed,
                    external_userid=ext or None,
                    already_complete=True,
                )
                reply_text = c1["reply_text"]
                menu_payload = c1["menu_payload"]
                h5_masked = c1["h5_task_link_masked"]
                outcome = "claim_c1_deduped"
            else:
                c1 = _build_claim_c1_h5_response(
                    refreshed,
                    external_userid=ext or None,
                    already_complete=False,
                )
                reply_text = c1["reply_text"]
                menu_payload = c1["menu_payload"]
                h5_masked = c1["h5_task_link_masked"]
                outcome = "claim_c1_sent"
            active_outcome = outcome
        else:
            update_claim_workflow_state(
                case_id,
                claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
                guided_workflow_state=GUIDED_STATE_COLLECTING_TEXT,
            )
            refreshed = get_case_for_read(case_id) or refreshed
            reply_text = build_claim_missing_basics_reply(refreshed)
            menu_payload = None
            h5_masked = None
            active_outcome = "claim_basics_partial"

        transition = suggest_next_claim_transition(refreshed)
        kernel_step = get_claim_simplified_current_step(refreshed)
        claim_ctx = claim_context_for_case(refreshed)
        if active_outcome == "claim_c1_sent":
            _emit_claim_routing_decision(
                normalized=normalized,
                intent_result=intent_result,
                priority_rule=PRIORITY_ACTIVE_CLAIM_BASICS_COLLECTION,
                decision=DECISION_SEND_CLAIM_C1,
                reason="active_claim_waiting_for_accident_basics",
                response_type=RESPONSE_CLAIM_C1,
                created_case_id=case_id,
                **identity_kwargs,
                **claim_ctx,
            )
        else:
            _emit_claim_routing_decision(
                normalized=normalized,
                intent_result=intent_result,
                priority_rule=PRIORITY_ACTIVE_CLAIM_BASICS_COLLECTION,
                decision=DECISION_COLLECT_CLAIM_BASICS,
                reason="active_claim_waiting_for_accident_basics",
                response_type=RESPONSE_CLAIM_MISSING_BASICS,
                created_case_id=case_id,
                **identity_kwargs,
                **claim_ctx,
            )
        _log_event(
            "wecom_claim_basics_ingest_v1",
            {
                "msg_id": msg_id,
                "case_id": case_id,
                "outcome": active_outcome,
                "datetime_present": bool(extracted.get("accident_datetime")),
                "location_present": bool(extracted.get("accident_location")),
                "description_present": bool(extracted.get("accident_description")),
                "basics_complete": is_accident_basics_complete(refreshed),
                "injury_mentioned": injury_mentioned,
                "kernel_current_step": kernel_step,
                "kernel_basics_missing": sorted(_kernel_basics_missing_keys(refreshed)),
            },
        )
        return {
            "outcome": "attached",
            "case_id": case_id,
            "case_created": case_created,
            "reply_text": reply_text,
            "menu_payload": menu_payload,
            "h5_task_link_masked": h5_masked,
            "active_case_outcome": active_outcome,
            "claim_phase": refreshed.get("claim_phase"),
            "service_lane": SERVICE_LANE_CLAIM,
            "needs_broker_manual_handle": transition.get("needs_broker_manual_handle", False),
        }

    reply_text = build_claim_start_card_reply(injury_mentioned=injury_mentioned)
    return {
        "outcome": "claim_start_card_sent",
        "case_id": case_id,
        "case_created": case_created,
        "reply_text": reply_text,
        "active_case_outcome": "claim_start_card_sent",
        "service_lane": SERVICE_LANE_CLAIM,
    }


def ingest_claim_question_safe_reply(normalized: dict[str, Any]) -> dict[str, Any]:
    """Safe reply for claim how-to / liability questions — no guided case creation."""
    from services.fiqa_api.wecom.reply import (
        build_claim_question_safe_reply,
        build_claim_question_safe_reply_during_add_vehicle,
    )

    ext = str(normalized.get("external_userid") or "").strip()
    add_car_active = bool(find_open_add_car_case_by_external_userid(ext))
    if add_car_active:
        reply_text = build_claim_question_safe_reply_during_add_vehicle()
        av_ctx = add_vehicle_context_for_user(ext)
        _emit_claim_routing_decision(
            normalized=normalized,
            intent_result=None,
            priority_rule=PRIORITY_CLAIM_QUESTION_DURING_ACTIVE_ADD_VEHICLE,
            decision=DECISION_CLAIM_QUESTION_SAFE_REPLY,
            reason="claim_question_handled_before_secondary_topic_deferral",
            response_type=RESPONSE_CLAIM_QUESTION_SAFE,
            **av_ctx,
        )
    else:
        reply_text = build_claim_question_safe_reply()

    return {
        "outcome": "claim_question_safe_reply",
        "case_id": None,
        "case_created": False,
        "reply_text": reply_text,
        "active_case_outcome": "claim_question_safe_reply",
        "service_lane": None,
    }


def build_claim_start_reply(*, injury_mentioned: bool = False) -> str:
    from services.fiqa_api.wecom.reply import build_claim_start_card_reply

    return build_claim_start_card_reply(injury_mentioned=injury_mentioned)


def build_claim_missing_basics_reply(case: dict[str, Any]) -> str:
    from services.fiqa_api.wecom.reply import build_claim_missing_basics_reply as _build

    return _build(case)


def build_claim_c1_reply(case: dict[str, Any]) -> str:
    from services.fiqa_api.wecom.reply import build_claim_stage_complete_c1_reply

    return build_claim_stage_complete_c1_reply(case)


def build_claim_safety_manual_reply() -> str:
    from services.fiqa_api.wecom.reply import build_claim_safety_manual_reply as _build

    return _build()
