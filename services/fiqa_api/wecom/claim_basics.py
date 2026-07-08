"""P19H-2 — Claim WeCom guided workflow: start card + accident basics + C1."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from services.fiqa_api.inbox_triage.case_store import (
    append_follow_up_message,
    bind_case_channel_identity,
    save_case,
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
from services.fiqa_api.wecom.claim_state import (
    CLAIM_ACCIDENT_BASICS_FIELDS,
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_STARTED,
    GUIDED_STATE_COLLECTING_TEXT,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
    is_accident_basics_complete,
    suggest_next_claim_transition,
    transition_to_manual_handle,
)
from services.fiqa_api.wecom.intent import IntentResult, is_add_vehicle_status_inquiry

logger = logging.getLogger(__name__)

CLAIM_GUIDED_START_MARKERS: tuple[str, ...] = (
    "我要理赔",
    "我撞车了",
    "出事故了",
    "发生事故了",
    "车祸了",
    "事故理赔",
    "file a claim",
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


def is_explicit_claim_restart(text: str) -> bool:
    lowered = (text or "").strip().lower()
    return any(m in lowered for m in RESTART_CLAIM_MARKERS)


def is_claim_guided_start_message(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if is_explicit_claim_restart(raw):
        return True
    if any(m in raw for m in CLAIM_GUIDED_START_MARKERS):
        return True
    lowered = raw.lower()
    if lowered in ("claim", "accident"):
        return True
    return False


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


def is_claim_progress_inquiry(text: str) -> bool:
    raw = (text or "").strip().lower()
    if is_add_vehicle_status_inquiry(text):
        return False
    return any(m in raw for m in _CLAIM_PROGRESS_MARKERS)


def _case_sort_key(case: dict[str, Any]) -> str:
    return str(case.get("updated_at") or case.get("created_at") or "")


def find_active_claim_case_for_basics(external_userid: str) -> dict[str, Any] | None:
    """Newest open guided claim case for this WeCom user (not broker_done)."""
    ext = (external_userid or "").strip()
    if not ext:
        return None
    matches: list[dict[str, Any]] = []
    for case in list_all_cases_for_read():
        if case.get("wecom_external_userid") != ext:
            continue
        if case.get("case_status") == "closed":
            continue
        lane = str(case.get("service_lane") or "").strip().lower()
        if lane != SERVICE_LANE_CLAIM:
            continue
        if case.get("broker_confirmed_at"):
            continue
        if derive_claim_phase(case) == CLAIM_PHASE_BROKER_DONE:
            continue
        matches.append(case)
    if not matches:
        return None
    matches.sort(key=_case_sort_key, reverse=True)
    return matches[0]


def should_route_claim_guided_workflow(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    """Route to Claim guided basics handler (before minimal claim_lite lane)."""
    text = str(normalized.get("text") or "").strip()
    ext = str(normalized.get("external_userid") or "")

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

    return has_accident_basics_signals(text)


def should_route_claim_question_safe_reply(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> bool:
    text = str(normalized.get("text") or "").strip()
    if intent_result.confidence != "high" or intent_result.intent != "claim_intake":
        return False
    if find_active_claim_case_for_basics(str(normalized.get("external_userid") or "")):
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
    return {"case_id": case_id, "case_created": True, "outcome": "created"}


def ingest_claim_basics_message(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> dict[str, Any]:
    """Create/update guided claim case and return WeCom reply metadata."""
    from services.fiqa_api.inbox_triage.case_store import update_claim_workflow_state
    from services.fiqa_api.wecom.reply import (
        build_claim_basics_already_complete_reply,
        build_claim_missing_basics_reply,
        build_claim_stage_complete_c1_reply,
        build_claim_start_card_reply,
    )

    msg_id = str(normalized.get("msg_id") or "").strip()
    text = str(normalized.get("text") or "").strip()
    ext = str(normalized.get("external_userid") or "").strip()
    injury_mentioned = message_mentions_injury(text)

    existing_by_msg = find_case_by_wecom_msg_id(msg_id)
    if existing_by_msg:
        case = get_case_for_read(existing_by_msg) or {}
        phase = derive_claim_phase(case)
        if phase == CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE:
            reply = build_claim_basics_already_complete_reply(case)
        else:
            reply = build_claim_missing_basics_reply(case)
        return {
            "outcome": "duplicate_msg",
            "case_id": existing_by_msg,
            "case_created": False,
            "reply_text": reply,
            "active_case_outcome": "claim_duplicate_msg",
            "service_lane": SERVICE_LANE_CLAIM,
        }

    if find_open_add_car_case_by_external_userid(ext) and intent_result.intent == "claim_intake":
        from services.fiqa_api.wecom.reply import build_secondary_topic_deferred_reply

        return {
            "outcome": "secondary_topic_deferred",
            "case_id": None,
            "case_created": False,
            "reply_text": build_secondary_topic_deferred_reply(),
            "active_case_outcome": "claim_secondary_topic_deferred",
            "service_lane": None,
        }

    case_id: str | None = None
    case_created = False
    active = find_active_claim_case_for_basics(ext)

    if active and is_explicit_claim_restart(text):
        active = None

    if not active:
        created = _create_claim_case(normalized, injury_mentioned=injury_mentioned)
        case_id = created["case_id"]
        case_created = created["case_created"]
        case = get_case_for_read(case_id) or {}
    else:
        case_id = str(active.get("case_id") or "").strip()
        case = active

    if injury_mentioned and case_id:
        manual_patch = transition_to_manual_handle(case)
        update_claim_workflow_state(case_id, **manual_patch)

    phase = derive_claim_phase(case)
    if phase == CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE:
        reply_text = build_claim_basics_already_complete_reply(case)
        return {
            "outcome": "claim_basics_already_complete",
            "case_id": case_id,
            "case_created": case_created,
            "reply_text": reply_text,
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
        reply_text = build_claim_start_card_reply(injury_mentioned=injury_mentioned)
        update_claim_workflow_state(
            case_id,
            claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
            guided_workflow_state=GUIDED_STATE_COLLECTING_TEXT,
        )
        return {
            "outcome": "claim_start_card_sent",
            "case_id": case_id,
            "case_created": True,
            "reply_text": reply_text,
            "active_case_outcome": "claim_start_card_sent",
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
        _record_wecom_evidence(case_id, msg_id)
        refreshed = get_case_for_read(case_id) or updated

        if injury_mentioned:
            update_claim_workflow_state(
                case_id,
                **transition_to_manual_handle(refreshed),
            )
            refreshed = get_case_for_read(case_id) or refreshed

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
            if sent_c1_before:
                reply_text = build_claim_basics_already_complete_reply(refreshed)
                outcome = "claim_c1_deduped"
            else:
                reply_text = build_claim_stage_complete_c1_reply(refreshed)
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
            active_outcome = "claim_basics_partial"

        transition = suggest_next_claim_transition(refreshed)
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
            },
        )
        return {
            "outcome": "attached",
            "case_id": case_id,
            "case_created": case_created,
            "reply_text": reply_text,
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
    from services.fiqa_api.wecom.reply import build_claim_question_safe_reply

    return {
        "outcome": "claim_question_safe_reply",
        "case_id": None,
        "case_created": False,
        "reply_text": build_claim_question_safe_reply(),
        "active_case_outcome": "claim_question_safe_reply",
        "service_lane": None,
    }
