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
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    case_supports_slice1,
    default_slice1_service,
    slice1_feature_flag_enabled,
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
    "vehicle_other_party": (
        "own_vehicle_info",
        "other_party_plate",
        "other_party_info",
        "police_involved",
        "police_reported",
    ),
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

_H5_DONE_NEXT_STEP: Final[str] = (
    "资料已提交给陈总审核。你仍然可以继续补充照片、对方保险或其他细节。"
)
_H5_DONE_DISCLAIMER: Final[str] = "这只是资料收集，不代表已经正式向保险公司报案。"
_H5_DONE_MISSING_CLEAR: Final[str] = "目前主要资料已收到，陈总会进一步确认。"
_H5_DASHBOARD_TITLE: Final[str] = "我的报案"
_H5_DASHBOARD_SUBTITLE: Final[str] = (
    "先告诉陈总发生了什么。照片和证件如需补充，陈总会再通知您。"
)
_H5_DASHBOARD_SUBMITTED_SUBTITLE: Final[str] = (
    "资料已提交给陈总审核。如需继续补充 VIN、证件或照片，陈总会再通知您。"
)
EVIDENCE_GALLERY_LIMIT: Final[int] = 20
_EVIDENCE_CATEGORY_LABELS: Final[dict[str, str]] = {
    "vehicle_damage": "本车受损",
    "other_vehicle_scene": "对方车辆 / 现场",
    "other_evidence": "其他证据",
}

_POST_SUBMIT_ALLOWED_FIELDS_BY_STEP: Final[dict[str, frozenset[str]]] = {
    "injury": frozenset({"anyone_injured", "injury_status"}),
    "time_location": frozenset({"accident_datetime", "accident_location"}),
    "story": frozenset({"accident_description"}),
    "vehicle_other_party": frozenset(
        {"own_vehicle_info", "other_party_plate", "other_party_info", "police_involved", "police_reported"}
    ),
}


def _load_claim_case(case_id: str) -> dict[str, Any]:
    case = get_case_for_read(case_id)
    if case is None:
        raise ValueError("case_not_found")
    if str(case.get("service_lane") or "").strip().lower() != "claim":
        raise ValueError("lane_mismatch")
    return case


def _load_writable_claim_case(case_id: str) -> dict[str, Any]:
    """Load claim case and reject customer mutations when History."""
    from services.fiqa_api.inbox_triage.case_close import assert_customer_case_writable

    case = _load_claim_case(case_id)
    assert_customer_case_writable(case)
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
        # Nice to Have / Request More — never blocks Must Have submit.
        return True
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
        # Optional: vehicle identity is Request More; other driver is Nice to Have.
        out: dict[str, str] = {}
        own = str(fields.get("own_vehicle_info") or "").strip()
        if own:
            out["own_vehicle_info"] = own
        plate = str(fields.get("other_party_plate") or "").strip()
        other = str(fields.get("other_party_info") or "").strip()
        if plate:
            out["other_party_plate"] = plate
        if other:
            out["other_party_info"] = other
        police = str(fields.get("police_involved") or fields.get("police_reported") or "").strip().lower()
        if police in ("yes", "no", "unknown"):
            out["police_involved"] = police
            out["police_reported"] = police
        return out
    raise ValueError("unsupported_step")


def _collected_keys_for_patch(step: str, facts_patch: dict[str, str]) -> list[str]:
    keys = list(_STEP_FIELD_MAP.get(step, ()))
    if step == "vehicle_other_party" and facts_patch.get("other_party_plate"):
        keys.append("other_party_vehicle_or_plate")
    return keys


def _validate_post_submit_patch_fields(step: str, fields: dict[str, str]) -> None:
    allowed = _POST_SUBMIT_ALLOWED_FIELDS_BY_STEP.get(step)
    if not allowed:
        raise ValueError("post_submit_step_not_allowed")
    incoming = {str(k or "").strip() for k in fields.keys() if str(k or "").strip()}
    if not incoming:
        raise ValueError("post_submit_fields_required")
    disallowed = sorted(incoming - allowed)
    if disallowed:
        raise ValueError("post_submit_field_not_allowed")


def _post_submit_change_payload(case: dict[str, Any], facts_patch: dict[str, str]) -> dict[str, dict[str, str | None]]:
    current_facts = _facts(case)
    changed: dict[str, dict[str, str | None]] = {}
    for key, new_value in facts_patch.items():
        before = str(current_facts.get(key) or "").strip() or None
        after = str(new_value or "").strip() or None
        if before == after:
            continue
        changed[key] = {"before": before, "after": after}
    return changed


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


def _all_attachment_photo_count(case: dict[str, Any]) -> int:
    count = 0
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        mime = str(att.get("mime_type") or "").lower()
        msgtype = str(att.get("msgtype") or "").lower()
        if mime.startswith("image/") or msgtype == "image" or str(att.get("type") or "").endswith("photo"):
            count += 1
    return count


def _build_evidence_gallery(case: dict[str, Any]) -> dict[str, Any]:
    """Customer-safe active gallery projection; attachment records remain canonical."""
    items: list[dict[str, Any]] = []
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict) or str(att.get("source") or "").lower() != "h5_task":
            continue
        if str(att.get("msgtype") or "").lower() != "image":
            continue
        category = str(att.get("evidence_category") or att.get("slot_assignment") or "other_evidence")
        if category == "customer_damage_photo":
            category = "vehicle_damage"
        elif category in ("other_party_vehicle_photo", "scene_photo"):
            category = "other_vehicle_scene"
        items.append(
            {
                "attachment_id": str(att.get("attachment_id") or ""),
                "category": category if category in _EVIDENCE_CATEGORY_LABELS else "other_evidence",
                "filename": str(att.get("filename") or ""),
                "mime_type": str(att.get("mime_type") or ""),
                "size_bytes": int(att.get("size_bytes") or 0),
                "created_at": str(att.get("created_at") or att.get("received_at") or ""),
                "created_by": str(att.get("created_by") or "customer"),
                "created_by_channel": str(att.get("created_by_channel") or "h5_task"),
                "submission_phase": str(att.get("submission_phase") or "pre_submit"),
                "status": str(att.get("evidence_status") or "confirmed"),
                "replaces_attachment_id": att.get("replaces_attachment_id"),
                "replaced_by_attachment_id": att.get("replaced_by_attachment_id"),
                # Customer tokens are credentials; attachment previews stay broker-only.
                "preview_available": False,
            }
        )
    items.sort(key=lambda item: item["created_at"])
    active = [item for item in items if item["status"] == "confirmed"]
    return {
        "limit": EVIDENCE_GALLERY_LIMIT,
        "active_count": len(active),
        "categories": [
            {
                "key": key,
                "label": label,
                "items": [item for item in items if item["category"] == key],
            }
            for key, label in _EVIDENCE_CATEGORY_LABELS.items()
        ],
    }


def is_h5_intake_continuable(case: dict[str, Any]) -> bool:
    """True when customer can resume Claim H5 wizard PATCH/submit (not yet submitted)."""
    if str(case.get("service_lane") or "").strip().lower() != "claim":
        return False
    phase = derive_claim_phase(case)
    if phase in _H5_SUBMIT_TERMINAL_PHASES:
        return False
    return not _is_submitted(case)


def is_h5_task_dashboard_available(case: dict[str, Any]) -> bool:
    """True when customer can open Claim H5 task dashboard (including post-submit supplement)."""
    if str(case.get("service_lane") or "").strip().lower() != "claim":
        return False
    return derive_claim_phase(case) != CLAIM_PHASE_BROKER_DONE


def _dashboard_status_label(case: dict[str, Any]) -> str:
    phase = derive_claim_phase(case)
    if phase == CLAIM_PHASE_BROKER_DONE:
        return "陈总已确认"
    if _is_submitted(case):
        return "已提交给陈总审核"
    if phase in (CLAIM_PHASE_BROKER_REVIEW, CLAIM_PHASE_INTAKE_READY_FOR_BROKER):
        return "已提交给陈总审核"
    return "资料收集中"


def _dashboard_injury_label(case: dict[str, Any]) -> str | None:
    value = _injury_value(case)
    if value == "no":
        return "没有受伤"
    if value == "yes":
        return "有人受伤"
    if value == "unknown":
        return "不确定"
    return None


def _dashboard_received_items(case: dict[str, Any]) -> list[str]:
    facts = _facts(case)
    items: list[str] = []
    injury = _dashboard_injury_label(case)
    if injury:
        items.append(f"受伤情况：{injury}")
    if str(facts.get("accident_description") or "").strip():
        items.append("事故经过")
    if str(facts.get("accident_datetime") or "").strip():
        items.append(f"事故时间：{facts.get('accident_datetime')}")
    if str(facts.get("accident_location") or "").strip():
        items.append(f"事故地点：{facts.get('accident_location')}")
    photo_count = _all_attachment_photo_count(case)
    items.append(f"照片：{photo_count} 张")
    plate = str(facts.get("other_party_plate") or "").strip()
    if plate:
        items.append(f"对方车牌：{plate}")
    other = str(facts.get("other_party_info") or "").strip()
    if other:
        items.append(f"对方保险：{other}")
    return items


def _dashboard_missing_items(case: dict[str, Any]) -> list[str]:
    missing = get_claim_missing_items(case)
    labels = [str(m.get("label") or "").strip() for m in missing if str(m.get("label") or "").strip()]
    if labels:
        return labels[:5]
    photo_count = _all_attachment_photo_count(case)
    if photo_count == 0:
        return ["车损或现场照片"]
    return []


def _dashboard_next_action(case: dict[str, Any]) -> str:
    if _is_submitted(case):
        return "等待陈总查看；如有新资料可继续补充"
    current = _current_step(case)
    if current == "review":
        return "提交给陈总审核"
    if current == "evidence" and _all_attachment_photo_count(case) == 0:
        return "上传/补充照片"
    if current in CLAIM_INTAKE_STEPS[1:-2]:
        return "继续填写"
    return "继续填写资料"


def _dashboard_primary_cta(case: dict[str, Any]) -> str:
    if _is_submitted(case):
        return "继续补充资料"
    current = _current_step(case)
    if current == "review":
        return "提交给陈总审核"
    if current == "evidence" and _all_attachment_photo_count(case) == 0:
        return "上传/补充照片"
    return "继续填写资料"


def _build_dashboard_summary(case: dict[str, Any]) -> dict[str, Any]:
    submitted = _is_submitted(case)
    return {
        "title": _H5_DASHBOARD_TITLE,
        "subtitle": _H5_DASHBOARD_SUBMITTED_SUBTITLE if submitted else _H5_DASHBOARD_SUBTITLE,
        "status": _dashboard_status_label(case),
        "received": _dashboard_received_items(case),
        "missing": _dashboard_missing_items(case),
        "next_action": _dashboard_next_action(case),
        "primary_cta": _dashboard_primary_cta(case),
        "secondary_cta": "返回微信",
        "submitted_supplement_allowed": submitted,
        "warning": _H5_DONE_DISCLAIMER,
    }


def _customer_task_status(case: dict[str, Any]) -> str:
    if _is_submitted(case):
        return "submitted"
    if _current_step(case) == "review":
        return "review_ready"
    if get_claim_missing_items(case):
        return "collecting"
    return "collecting"


def _customer_task_fields(case: dict[str, Any]) -> dict[str, str]:
    """Expose only fixed Claim input keys with customer-confirmed provenance."""
    facts = _facts(case)
    provenance = case.get("known_fact_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    allowed_keys = (
        "anyone_injured",
        "injury_status",
        "accident_datetime",
        "accident_location",
        "accident_description",
        "own_vehicle_info",
        "other_party_plate",
        "other_party_info",
    )
    accepted_sources = {"customer_task", "h5_form", "customer_confirmed"}
    fields: dict[str, str] = {}
    for key in allowed_keys:
        meta = provenance.get(key)
        if not isinstance(meta, dict):
            continue
        if str(meta.get("source") or "").strip().lower() not in accepted_sources:
            continue
        value = str(facts.get(key) or "").strip()
        if value:
            fields[key] = value
    return fields


def build_customer_task_contract(case: dict[str, Any], *, task_id: str) -> dict[str, Any]:
    """Build the additive, customer-safe Claim Task Contract v0 projection."""
    missing_items = get_claim_missing_items(case)
    submitted = _is_submitted(case)
    review_ready = _minimum_submit_ready(case)
    current_step = _current_step(case)
    total = len(CLAIM_INTAKE_STEPS[1:-2])
    state = _h5_intake_state(case)
    gallery = _build_evidence_gallery(case)
    evidence_requirements = [
        {
            "slot": category["key"],
            "label": category["label"],
            "min": 0,
            "received": sum(1 for item in category["items"] if item["status"] == "confirmed"),
        }
        for category in gallery["categories"]
    ]
    sections = [
        {
            "key": "injury",
            "label": "受伤情况",
            "component_type": "choice",
            "required": True,
            "status": "received" if _step_complete(case, "injury") else "needed",
        },
        {
            "key": "time_location",
            "label": "事故时间和地点",
            "component_type": "short_text",
            "required": True,
            "status": "received" if _step_complete(case, "time_location") else "needed",
        },
        {
            "key": "story",
            "label": "事故经过",
            "component_type": "long_text",
            "required": True,
            "status": "received" if _step_complete(case, "story") else "needed",
        },
        {
            "key": "vehicle_other_party",
            "label": "车辆和对方信息（选填）",
            "component_type": "short_text",
            "required": False,
            "status": "received" if _step_complete(case, "vehicle_other_party") else "needed",
        },
    ]
    next_type = "submit" if review_ready and not submitted else "go_to_section"
    next_target = "review" if review_ready else current_step
    next_label = "提交给陈总审核" if review_ready and not submitted else _dashboard_primary_cta(case)
    return {
        "contract_version": "0",
        "task_id": task_id,
        "task_type": "claim_intake",
        "task_status": _customer_task_status(case),
        "title": _H5_DASHBOARD_TITLE,
        "instruction": _dashboard_next_action(case),
        "progress": {"completed": _completed_step_count(case), "total": total},
        "sections": sections,
        "fields": _customer_task_fields(case),
        "missing_items": [
            {"key": str(item.get("field") or ""), "label": str(item.get("label") or "")}
            for item in missing_items
        ],
        "evidence_requirements": evidence_requirements,
        "evidence_gallery": gallery,
        "next_action": {"type": next_type, "target": next_target, "label": next_label},
        "review_ready": review_ready,
        "submit_ready": review_ready and not submitted,
        "revision": int(state.get("task_revision") or 0),
        "timestamps": {"updated_at": str(case.get("updated_at") or "")},
        "capabilities": {"voice": False, "scan": False},
        "branding": {
            "office_name": "陈总办公室",
            "safety_copy": CLAIM_INTAKE_SAFETY_COPY,
        },
        "error": None,
    }


def _case_is_test(case: dict[str, Any]) -> bool:
    if bool(case.get("workbench_test")):
        return True
    intake = case.get("p20_case_intake_projection")
    if isinstance(intake, dict) and bool(intake.get("is_test")):
        return True
    return False


def _customer_qa_marker(
    case: dict[str, Any],
    *,
    next_action: dict[str, Any] | None,
) -> str | None:
    """Human-readable QA marker for test claims only — never includes case IDs."""
    if not _case_is_test(case):
        return None
    required = str((next_action or {}).get("required_input") or "").strip().lower()
    if required == "vin":
        return "TEST · Cap3A VIN QA"
    title = str(case.get("title") or case.get("display_title") or "").upper()
    if "CAP3A" in title or "CAP 3A" in title:
        return "TEST · Cap3A VIN QA"
    return "QA Test Claim"


def _slice1_projection_for_case(
    case: dict[str, Any],
) -> tuple[dict[str, Any] | None, bool]:
    """Return (projection, load_failed).

    load_failed is True only when Slice 1 is expected and live fetch failed
    with no usable cached projection — callers must not silent-fallback to overview.
    """
    if not (case_supports_slice1(case) or slice1_feature_flag_enabled()):
        return None, False
    cid = str(case.get("case_id") or "").strip()
    if not cid:
        return None, False
    try:
        projection = default_slice1_service().fetch_projection(cid)
    except Exception:
        logger.warning("p20_slice1_projection_fetch_failed case_id=%s", cid)
        raw = case.get("p20_slice1_projection")
        if isinstance(raw, dict):
            # Stale cached projection is still authoritative enough to land correctly.
            return dict(raw), False
        return None, True
    return (projection if isinstance(projection, dict) else None), False


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
    upload_url: str | None = None
    try:
        ext_uid = str(case.get("wecom_external_userid") or "").strip() or None
        upload_url = mint_h5_claim_evidence_pack_link(
            case_id=claims.case_id,
            external_userid=ext_uid,
        )
    except ValueError:
        upload_url = None
    dashboard = _build_dashboard_summary(case)
    is_test = _case_is_test(case)
    # Claim Vehicle T4 — customer form hydration (H5 only; not Workbench brief).
    key_facts = dict(brief.get("key_facts") or {})
    known = case.get("known_facts") if isinstance(case.get("known_facts"), dict) else {}
    for fact_key in (
        "vehicle_year",
        "vehicle_make",
        "vehicle_model",
        "vehicle_vin",
        "vin",
        "own_vehicle_vin",
        "vehicle_vin_unavailable",
        "vehicle_license_plate",
        "vehicle_plate_state",
        "vehicle_information",
        "vehicle_verification_status",
        "primary_vehicle_summary",
    ):
        value = known.get(fact_key)
        if value is None:
            continue
        text = str(value).strip()
        if text and fact_key not in key_facts:
            key_facts[fact_key] = text
    if not str(key_facts.get("own_vehicle_info") or "").strip():
        alias = str(known.get("own_vehicle_info") or known.get("vehicle_information") or "").strip()
        if alias:
            key_facts["own_vehicle_info"] = alias
    from services.fiqa_api.inbox_triage.case_close import case_is_closed_history

    closed_history = case_is_closed_history(case)
    result: dict[str, Any] = {
        "lane": claims.lane,
        "flow": claims.flow or FLOW_CLAIM_INTAKE_FORM,
        "case_id": claims.case_id,
        "title": _H5_DASHBOARD_TITLE,
        "safety_copy": CLAIM_INTAKE_SAFETY_COPY,
        "steps": list(CLAIM_INTAKE_STEPS),
        "current_step": current,
        "completed_count": _completed_step_count(case),
        "step_total": len(CLAIM_INTAKE_STEPS) - 2,
        "submitted": submitted,
        "phase": derive_claim_phase(case),
        "key_facts": key_facts,
        "missing_info": get_claim_missing_items(case),
        "injury_alert": is_injury_yes(_injury_value(case)),
        "upload_url": upload_url,
        "attachment_count": _all_attachment_photo_count(case),
        "photo_count": _all_attachment_photo_count(case),
        "evidence_gallery": _build_evidence_gallery(case),
        "completion_summary": _build_completion_summary(case),
        "dashboard_summary": dashboard,
        "task_contract": build_customer_task_contract(case, task_id=claims.nonce),
        "is_test": is_test,
        "slice1_projection_error": False,
        "customer_qa_marker": None,
        # Home resume authority when /customer/session is unavailable (QA WeChat gap).
        "case_status": str(case.get("case_status") or "").strip() or None,
        "case_history_state": str(case.get("case_history_state") or "").strip() or None,
        "case_closed_read_only": closed_history,
    }
    slice1_projection, slice1_load_failed = _slice1_projection_for_case(case)
    if slice1_load_failed:
        result["slice1_projection_error"] = True
        result["customer_qa_marker"] = _customer_qa_marker(case, next_action=None)
        _attach_h5_constitution_projection(
            result,
            case=case,
            brief=brief,
            slice1=None,
        )
        try:
            from services.fiqa_api.inbox_triage.case_activity_events import (
                record_customer_intake_opened,
                safe_record,
            )

            safe_record(
                record_customer_intake_opened,
                claims.case_id,
                source_surface="h5_intake",
                meta={"command_type": "intake_info_render"},
            )
        except Exception:
            pass
        return result
    if slice1_projection:
        result["slice1_projection"] = slice1_projection
        next_action = slice1_projection.get("customer_next_action")
        next_action = next_action if isinstance(next_action, dict) else None
        result["customer_qa_marker"] = _customer_qa_marker(case, next_action=next_action)
        result["task_contract_v1"] = {
            "contract_version": "1",
            "task_id": claims.nonce,
            "task_type": "claim_request_more",
            "workflow_state": slice1_projection.get("workflow_state"),
            "aggregate_version": slice1_projection.get("aggregate_version"),
            "next_action": next_action,
            "queued_request_items": slice1_projection.get("queued_request_items") or [],
            "request_progress": slice1_projection.get("request_progress") or {},
            "server_timestamp": slice1_projection.get("server_timestamp"),
        }
    else:
        result["customer_qa_marker"] = _customer_qa_marker(case, next_action=None)
    _attach_h5_constitution_projection(
        result,
        case=case,
        brief=brief,
        slice1=slice1_projection if isinstance(slice1_projection, dict) else None,
    )
    try:
        from services.fiqa_api.inbox_triage.case_activity_events import (
            record_customer_intake_opened,
            safe_record,
        )

        safe_record(
            record_customer_intake_opened,
            claims.case_id,
            source_surface="h5_intake",
            meta={"command_type": "intake_info_render"},
        )
    except Exception:
        pass
    return result


def _attach_h5_constitution_projection(
    result: dict[str, Any],
    *,
    case: dict[str, Any],
    brief: dict[str, Any] | None,
    slice1: dict[str, Any] | None,
) -> None:
    """Additive customer Constitution on H5 intake. Never raises to caller."""
    cid = str(case.get("case_id") or result.get("case_id") or "").strip() or "?"
    try:
        from services.fiqa_api.inbox_triage.constitution_projection import (
            ConstitutionInputs,
            build_constitution_customer_projection,
        )

        result["constitution_projection"] = build_constitution_customer_projection(
            ConstitutionInputs(
                case=case,
                slice1=slice1,
                brief=brief if isinstance(brief, dict) else None,
                claim_phase=str(result.get("phase") or case.get("claim_phase") or "").strip()
                or None,
            )
        )
    except Exception as exc:
        logger.warning(
            "Constitution projection attach failed for H5 intake case %s: %s",
            cid,
            exc,
        )


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def patch_intake_fields(
    claims: VerifiedH5TaskToken,
    *,
    step: str,
    fields: dict[str, str],
    voice_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not claims.is_intake_form_token:
        raise ValueError("unsupported_flow")
    step_norm = (step or "").strip().lower()
    if step_norm not in _STEP_FIELD_MAP:
        raise ValueError("unsupported_step")

    case = _load_writable_claim_case(claims.case_id)
    submitted = _is_submitted(case)
    if submitted:
        _validate_post_submit_patch_fields(step_norm, fields)

    facts_patch = _validate_step_fields(step_norm, fields)
    if submitted and not facts_patch:
        raise ValueError("post_submit_fields_required")

    # P28: voice audit never enters known_facts; only confirmed text is case truth.
    voice_meta: dict[str, Any] | None = None
    if voice_audit and step_norm == "story":
        from services.fiqa_api.inbox_triage.voice_story import (
            build_voice_audit_metadata,
            emit_voice_confirm_metrics,
        )

        confirmed = str(facts_patch.get("accident_description") or "").strip()
        voice_meta = build_voice_audit_metadata(
            raw_transcript=str(voice_audit.get("raw_transcript") or ""),
            confirmed_story=str(voice_audit.get("confirmed_story") or confirmed),
            speech_provider=str(voice_audit.get("speech_provider") or "") or None,
            stt_latency_ms=_optional_int(voice_audit.get("stt_latency_ms")),
            recording_duration_ms=_optional_int(voice_audit.get("recording_duration_ms")),
        )
        if voice_meta["confirmed_story"] != confirmed:
            facts_patch = {**facts_patch, "accident_description": voice_meta["confirmed_story"]}
        emit_voice_confirm_metrics(claims.case_id, voice_meta)

    value_hash = _field_value_hash(step_norm, facts_patch)
    state = _h5_intake_state(case)
    dedup_key = f"h5_field:{claims.case_id}:{step_norm}:{value_hash}"
    if dedup_key in set(state.get("field_dedup_keys") or []):
        return intake_info_for_token(claims)

    supplement_changes = _post_submit_change_payload(case, facts_patch) if submitted else {}
    event_metadata: dict[str, Any] = {
        "step": step_norm,
        "fields": list(facts_patch.keys()),
        "post_submit": submitted,
        "submitted_at": str(state.get("submitted_at") or ""),
        "changes": supplement_changes,
    }
    if voice_meta:
        event_metadata["voice"] = {
            "raw_transcript": voice_meta["raw_transcript"],
            "confirmed_story": voice_meta["confirmed_story"],
            "speech_provider": voice_meta["speech_provider"],
            "edit_distance": voice_meta["edit_distance"],
            "edit_distance_normalized": voice_meta["edit_distance_normalized"],
            "stt_latency_ms": voice_meta.get("stt_latency_ms"),
            "recording_duration_ms": voice_meta.get("recording_duration_ms"),
            "audio_retained": False,
        }
        event_metadata["source"] = "voice"

    patch_case_known_facts(
        claims.case_id,
        facts_patch,
        source="customer_confirmed" if submitted else "customer_task",
        status="customer_supplement" if submitted else "customer_confirmed",
    )
    append_case_collected_fields(claims.case_id, _collected_keys_for_patch(step_norm, facts_patch))
    append_claim_timeline_event(
        claims.case_id,
        build_claim_timeline_event(
            event_type="h5_post_submit_supplement" if submitted else "h5_step_complete",
            source_channel="h5_task",
            actor="customer",
            metadata=event_metadata,
        ),
    )

    refreshed = _load_claim_case(claims.case_id)
    new_state = dict(_h5_intake_state(refreshed))
    dedup_keys = list(new_state.get("field_dedup_keys") or [])
    if dedup_key not in dedup_keys:
        dedup_keys.append(dedup_key)
    new_state["field_dedup_keys"] = dedup_keys[-50:]
    new_state["last_step"] = step_norm
    if voice_meta:
        new_state["last_voice_story"] = {
            "raw_transcript": voice_meta["raw_transcript"],
            "confirmed_story": voice_meta["confirmed_story"],
            "speech_provider": voice_meta["speech_provider"],
            "edit_distance": voice_meta["edit_distance"],
            "edit_distance_normalized": voice_meta["edit_distance_normalized"],
            "stt_latency_ms": voice_meta.get("stt_latency_ms"),
            "recording_duration_ms": voice_meta.get("recording_duration_ms"),
            "audio_retained": False,
        }
    if submitted:
        new_state["last_post_submit_supplement_at"] = build_claim_timeline_event(
            event_type="h5_post_submit_supplement",
            source_channel="h5_task",
        )["created_at"]
    new_state["task_revision"] = int(new_state.get("task_revision") or 0) + 1
    update_case_h5_intake_state(claims.case_id, new_state)

    try:
        from services.fiqa_api.inbox_triage.case_activity_events import (
            record_customer_first_action,
            safe_record,
        )

        safe_record(
            record_customer_first_action,
            claims.case_id,
            source_surface="h5_intake",
            meta={"command_type": f"patch_fields:{step_norm}"},
        )
    except Exception:
        pass

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

    case = _load_writable_claim_case(claims.case_id)
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
    submit_state["task_revision"] = int(submit_state.get("task_revision") or 0) + 1
    update_case_h5_intake_state(claims.case_id, submit_state)

    confirm_result = try_send_h5_submit_confirmation(claims.case_id)
    refreshed_case = _load_claim_case(claims.case_id)

    logger.info(
        "h5_claim_intake_submit_ok case_id=%s intent=%s wecom_sent=%s",
        claims.case_id,
        intent[:8],
        confirm_result.get("sent"),
    )
    try:
        from services.fiqa_api.inbox_triage.case_activity_events import (
            record_customer_first_action,
            safe_record,
        )

        safe_record(
            record_customer_first_action,
            claims.case_id,
            source_surface="h5_intake",
            meta={"command_type": "submit_intake_form"},
        )
    except Exception:
        pass
    return {
        **intake_info_for_token(claims),
        "already_submitted": False,
        "submit_intent_id": intent,
        **_wecom_confirmation_fields(refreshed_case, confirm_result),
    }
