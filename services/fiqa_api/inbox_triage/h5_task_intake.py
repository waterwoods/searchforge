"""H5 Claim structured intake form (P19H-3h-1A)."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Final

from services.fiqa_api.inbox_triage.case_store import (
    append_case_collected_fields,
    append_claim_timeline_event,
    build_claim_timeline_event,
    patch_case_known_facts,
    update_claim_workflow_state,
    update_case_h5_intake_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_case_brief
from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_evidence_pack_link
from services.fiqa_api.inbox_triage.h5_task_token import (
    FLOW_CLAIM_INTAKE_FORM,
    VerifiedH5TaskToken,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_MAX_DESCRIPTION_LENGTH,
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_BROKER_REVIEW,
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    GUIDED_STATE_READY_FOR_BROKER_REVIEW,
    derive_claim_phase,
    get_claim_missing_items,
    is_injury_yes,
)
from services.fiqa_api.wecom.h5_submit_confirmation import try_send_h5_submit_confirmation

logger = logging.getLogger(__name__)

CLAIM_INTAKE_SAFETY_COPY: Final[str] = (
    "此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。"
)

CLAIM_INTAKE_STEPS: Final[tuple[str, ...]] = (
    "start",
    "injury",
    "time_location",
    "story",
    "vehicle_other_party",
    "evidence",
    "review",
    "done",
)

_STEP_FIELD_MAP: Final[dict[str, tuple[str, ...]]] = {
    "injury": ("anyone_injured", "injury_status"),
    "time_location": ("accident_datetime", "accident_location"),
    "story": ("accident_description",),
    "vehicle_other_party": ("own_vehicle_info", "other_party_plate", "other_party_info"),
}

_H5_SUBMIT_TERMINAL_PHASES: Final[frozenset[str]] = frozenset(
    {
        CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        CLAIM_PHASE_BROKER_REVIEW,
        CLAIM_PHASE_BROKER_DONE,
    }
)

_H5_RECEIVED_STEP_LABELS: Final[tuple[tuple[str, str], ...]] = (
    ("injury", "受伤情况"),
    ("time_location", "事故时间/地点"),
    ("story", "事故经过"),
    ("vehicle_other_party", "车辆/对方信息"),
)

_H5_DONE_NEXT_STEP: Final[str] = "陈总会查看资料，如还需要补充，会通过微信联系你。"
_H5_DONE_DISCLAIMER: Final[str] = "这只是资料收集，不代表已经正式向保险公司报案。"
_H5_DONE_MISSING_CLEAR: Final[str] = "目前主要资料已收到，陈总会进一步确认。"


def _load_claim_case(case_id: str) -> dict[str, Any]:
    case = get_case_for_read(case_id)
    if case is None:
        raise ValueError("case_not_found")
    if str(case.get("service_lane") or "").strip().lower() != "claim":
        raise ValueError("lane_mismatch")
    return case


def _facts(case: dict[str, Any]) -> dict[str, Any]:
    raw = case.get("known_facts") or {}
    return raw if isinstance(raw, dict) else {}


def _injury_value(case: dict[str, Any]) -> str | None:
    facts = _facts(case)
    for key in ("anyone_injured", "injury_status"):
        value = str(facts.get(key) or "").strip().lower()
        if value in ("yes", "no", "unknown"):
            return value
    return None


def _step_complete(case: dict[str, Any], step: str) -> bool:
    facts = _facts(case)
    if step == "injury":
        return _injury_value(case) is not None
    if step == "time_location":
        return bool(str(facts.get("accident_datetime") or "").strip()) and bool(
            str(facts.get("accident_location") or "").strip()
        )
    if step == "story":
        desc = str(facts.get("accident_description") or "").strip()
        return len(desc) >= 10
    if step == "vehicle_other_party":
        return len(str(facts.get("own_vehicle_info") or "").strip()) >= 2
    if step == "evidence":
        # Optional step — skip allowed; never blocks submit or review.
        return True
    return False


def _h5_intake_state(case: dict[str, Any]) -> dict[str, Any]:
    raw = case.get("h5_intake_state") or {}
    return raw if isinstance(raw, dict) else {}


def _is_submitted(case: dict[str, Any]) -> bool:
    state = _h5_intake_state(case)
    if state.get("submitted_at"):
        return True
    phase = derive_claim_phase(case)
    return phase in _H5_SUBMIT_TERMINAL_PHASES


def _current_step(case: dict[str, Any]) -> str:
    if _is_submitted(case):
        return "done"
    for step in CLAIM_INTAKE_STEPS[1:-2]:
        if not _step_complete(case, step):
            return step
    return "review"


def _completed_step_count(case: dict[str, Any]) -> int:
    return sum(1 for step in CLAIM_INTAKE_STEPS[1:-2] if _step_complete(case, step))


def _normalize_injury_fields(fields: dict[str, str]) -> dict[str, str]:
    value = str(fields.get("anyone_injured") or fields.get("injury_status") or "").strip().lower()
    if value not in ("yes", "no", "unknown"):
        raise ValueError("invalid_injury_value")
    return {"anyone_injured": value, "injury_status": value}


def _validate_step_fields(step: str, fields: dict[str, str]) -> dict[str, str]:
    if step == "injury":
        return _normalize_injury_fields(fields)
    if step == "time_location":
        dt = str(fields.get("accident_datetime") or "").strip()
        loc = str(fields.get("accident_location") or "").strip()
        if not dt:
            raise ValueError("accident_datetime_required")
        if len(loc) < 3:
            raise ValueError("accident_location_required")
        return {"accident_datetime": dt, "accident_location": loc}
    if step == "story":
        desc = str(fields.get("accident_description") or "").strip()
        if len(desc) < 10:
            raise ValueError("accident_description_too_short")
        if len(desc) > CLAIM_MAX_DESCRIPTION_LENGTH:
            raise ValueError("accident_description_too_long")
        return {"accident_description": desc}
    if step == "vehicle_other_party":
        own = str(fields.get("own_vehicle_info") or "").strip()
        if len(own) < 2:
            raise ValueError("own_vehicle_info_required")
        out: dict[str, str] = {"own_vehicle_info": own}
        plate = str(fields.get("other_party_plate") or "").strip()
        other = str(fields.get("other_party_info") or "").strip()
        if plate:
            out["other_party_plate"] = plate
        if other:
            out["other_party_info"] = other
        return out
    raise ValueError("unsupported_step")


def _collected_keys_for_patch(step: str, facts_patch: dict[str, str]) -> list[str]:
    keys = list(_STEP_FIELD_MAP.get(step, ()))
    if step == "vehicle_other_party" and facts_patch.get("other_party_plate"):
        keys.append("other_party_vehicle_or_plate")
    return keys


def _build_completion_summary(case: dict[str, Any]) -> dict[str, Any]:
    received = [
        label for step, label in _H5_RECEIVED_STEP_LABELS if _step_complete(case, step)
    ]
    photo_count = _h5_attachment_photo_count(case)
    received.append(f"照片数量：{photo_count} 张")
    missing_items = get_claim_missing_items(case)
    missing_labels = [str(m.get("label") or "").strip() for m in missing_items if str(m.get("label") or "").strip()]
    return {
        "title": "已提交给陈总 ✅",
        "message": "你的事故资料已经提交给陈总审核。",
        "received": received,
        "missing": missing_labels,
        "missing_clear_message": _H5_DONE_MISSING_CLEAR if not missing_labels else None,
        "next_step": _H5_DONE_NEXT_STEP,
        "disclaimer": _H5_DONE_DISCLAIMER,
    }


def _wecom_confirmation_fields(case: dict[str, Any], send_result: dict[str, Any] | None = None) -> dict[str, Any]:
    state = _h5_intake_state(case)
    sent_marker = bool(str(state.get("h5_submit_confirmation_sent_at") or "").strip())
    if send_result is not None:
        sent = bool(send_result.get("sent"))
        pending = bool(send_result.get("pending")) or (
            not sent and send_result.get("reason") not in ("already_sent", "outbox_dedup")
        )
        return {
            "wecom_confirmation_sent": sent,
            "wecom_confirmation_pending": pending and not sent,
            "wecom_confirmation_reason": send_result.get("reason"),
        }
    return {
        "wecom_confirmation_sent": sent_marker,
        "wecom_confirmation_pending": not sent_marker and bool(case.get("wecom_external_userid")),
    }


def _h5_attachment_photo_count(case: dict[str, Any]) -> int:
    count = 0
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        if str(att.get("source") or "").strip().lower() != "h5_task":
            continue
        mime = str(att.get("mime_type") or "").lower()
        msgtype = str(att.get("msgtype") or "").lower()
        if mime.startswith("image/") or msgtype == "image":
            count += 1
    return count


def is_h5_intake_continuable(case: dict[str, Any]) -> bool:
    """True when customer can resume Claim H5 structured intake (not yet submitted)."""
    if str(case.get("service_lane") or "").strip().lower() != "claim":
        return False
    phase = derive_claim_phase(case)
    if phase in _H5_SUBMIT_TERMINAL_PHASES:
        return False
    return not _is_submitted(case)


def _field_value_hash(step: str, facts_patch: dict[str, str]) -> str:
    joined = "|".join(f"{k}={facts_patch[k]}" for k in sorted(facts_patch))
    digest = hashlib.sha256(f"{step}:{joined}".encode("utf-8")).hexdigest()[:16]
    return digest


def intake_info_for_token(claims: VerifiedH5TaskToken) -> dict[str, Any]:
    if not claims.is_intake_form_token:
        raise ValueError("unsupported_flow")
    case = _load_claim_case(claims.case_id)
    brief = build_claim_case_brief(case)
    current = _current_step(case)
    submitted = _is_submitted(case)
    photo_count = _h5_attachment_photo_count(case)
    upload_url: str | None = None
    try:
        ext_uid = str(case.get("wecom_external_userid") or "").strip() or None
        upload_url = mint_h5_claim_evidence_pack_link(
            case_id=claims.case_id,
            external_userid=ext_uid,
        )
    except ValueError:
        upload_url = None
    return {
        "lane": claims.lane,
        "flow": claims.flow or FLOW_CLAIM_INTAKE_FORM,
        "case_id": claims.case_id,
        "title": "事故资料收集",
        "safety_copy": CLAIM_INTAKE_SAFETY_COPY,
        "steps": list(CLAIM_INTAKE_STEPS),
        "current_step": current,
        "completed_count": _completed_step_count(case),
        "step_total": len(CLAIM_INTAKE_STEPS) - 2,
        "submitted": submitted,
        "phase": derive_claim_phase(case),
        "key_facts": brief.get("key_facts") or {},
        "missing_info": get_claim_missing_items(case),
        "injury_alert": is_injury_yes(_injury_value(case)),
        "upload_url": upload_url,
        "attachment_count": photo_count,
        "photo_count": photo_count,
        "completion_summary": _build_completion_summary(case),
    }


def patch_intake_fields(
    claims: VerifiedH5TaskToken,
    *,
    step: str,
    fields: dict[str, str],
) -> dict[str, Any]:
    if not claims.is_intake_form_token:
        raise ValueError("unsupported_flow")
    step_norm = (step or "").strip().lower()
    if step_norm not in _STEP_FIELD_MAP:
        raise ValueError("unsupported_step")

    case = _load_claim_case(claims.case_id)
    if _is_submitted(case):
        raise ValueError("already_submitted")

    facts_patch = _validate_step_fields(step_norm, fields)
    value_hash = _field_value_hash(step_norm, facts_patch)
    state = _h5_intake_state(case)
    dedup_key = f"h5_field:{claims.case_id}:{step_norm}:{value_hash}"
    if dedup_key in set(state.get("field_dedup_keys") or []):
        return intake_info_for_token(claims)

    patch_case_known_facts(claims.case_id, facts_patch)
    append_case_collected_fields(claims.case_id, _collected_keys_for_patch(step_norm, facts_patch))
    append_claim_timeline_event(
        claims.case_id,
        build_claim_timeline_event(
            event_type="h5_step_complete",
            source_channel="h5_task",
            actor="customer",
            metadata={"step": step_norm, "fields": list(facts_patch.keys())},
        ),
    )

    refreshed = _load_claim_case(claims.case_id)
    new_state = dict(_h5_intake_state(refreshed))
    dedup_keys = list(new_state.get("field_dedup_keys") or [])
    if dedup_key not in dedup_keys:
        dedup_keys.append(dedup_key)
    new_state["field_dedup_keys"] = dedup_keys[-50:]
    new_state["last_step"] = step_norm
    update_case_h5_intake_state(claims.case_id, new_state)

    return intake_info_for_token(claims)


def _minimum_submit_ready(case: dict[str, Any]) -> bool:
    return all(_step_complete(case, step) for step in CLAIM_INTAKE_STEPS[1:-2])


def submit_intake_form(
    claims: VerifiedH5TaskToken,
    *,
    submit_intent_id: str,
) -> dict[str, Any]:
    if not claims.is_intake_form_token:
        raise ValueError("unsupported_flow")
    intent = (submit_intent_id or "").strip()
    if not intent:
        raise ValueError("submit_intent_id_required")

    case = _load_claim_case(claims.case_id)
    state = _h5_intake_state(case)
    prior_intents = [str(x) for x in (state.get("submit_intent_ids") or []) if str(x).strip()]
    already_submitted = _is_submitted(case)

    if intent in prior_intents or already_submitted:
        return {
            **intake_info_for_token(claims),
            "already_submitted": True,
            "submit_intent_id": intent,
            **_wecom_confirmation_fields(case),
        }

    if not _minimum_submit_ready(case):
        raise ValueError("missing_required_fields")

    phase = derive_claim_phase(case)
    if phase in (CLAIM_PHASE_BROKER_REVIEW, CLAIM_PHASE_BROKER_DONE):
        return {
            **intake_info_for_token(claims),
            "already_submitted": True,
            "submit_intent_id": intent,
            **_wecom_confirmation_fields(case),
        }

    append_claim_timeline_event(
        claims.case_id,
        build_claim_timeline_event(
            event_type="customer_submitted_intake",
            source_channel="h5_task",
            actor="customer",
            metadata={"flow": FLOW_CLAIM_INTAKE_FORM, "submit_intent_id": intent},
        ),
    )
    update_claim_workflow_state(
        claims.case_id,
        claim_phase=CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        guided_workflow_state=GUIDED_STATE_READY_FOR_BROKER_REVIEW,
    )

    submit_state = dict(state)
    intents = list(submit_state.get("submit_intent_ids") or [])
    intents.append(intent)
    submit_state["submit_intent_ids"] = intents[-20:]
    submit_state["submitted_at"] = build_claim_timeline_event(
        event_type="customer_submitted_intake",
        source_channel="h5_task",
    )["created_at"]
    submit_state["submitted"] = True
    update_case_h5_intake_state(claims.case_id, submit_state)

    confirm_result = try_send_h5_submit_confirmation(claims.case_id)
    refreshed_case = _load_claim_case(claims.case_id)

    logger.info(
        "h5_claim_intake_submit_ok case_id=%s intent=%s wecom_sent=%s",
        claims.case_id,
        intent[:8],
        confirm_result.get("sent"),
    )
    return {
        **intake_info_for_token(claims),
        "already_submitted": False,
        "submit_intent_id": intent,
        **_wecom_confirmation_fields(refreshed_case, confirm_result),
    }
