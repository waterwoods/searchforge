"""P19H-3a — Claim case workbench display enrichment (no schema migration)."""

from __future__ import annotations

from typing import Any, Literal

from services.fiqa_api.inbox_triage.h5_task_token import FLOW_CLAIM_EVIDENCE_PACK
from services.fiqa_api.wecom.claim_state import (
    CLAIM_FORBIDDEN_AUTOMATION_CLAIMS,
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_BROKER_REVIEW,
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    CLAIM_PHASE_MANUAL_HANDLE,
    CLAIM_PHASE_SUMMARY_READY,
    CLAIM_PHOTO_FLOW_SLOTS,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
)

ClaimEvidenceSlotStatus = Literal["missing", "received", "skipped", "needs_retake"]
ClaimEvidenceRequiredLevel = Literal["required", "soft_required", "optional"]
ClaimEvidenceCompletionLevel = Literal["empty", "partial", "required_complete", "review_ready", "complete"]

CLAIM_EVIDENCE_SLOT_DEFINITIONS: tuple[dict[str, str], ...] = (
    {
        "slot_key": "customer_damage_photo",
        "label": "自己车损照片",
        "required_level": "required",
    },
    {
        "slot_key": "other_party_vehicle_photo",
        "label": "对方车辆 / 车牌照片",
        "required_level": "soft_required",
    },
    {
        "slot_key": "scene_photo",
        "label": "现场照片",
        "required_level": "optional",
    },
)

_CLAIM_EVIDENCE_SLOT_KEYS: frozenset[str] = frozenset(
    slot["slot_key"] for slot in CLAIM_EVIDENCE_SLOT_DEFINITIONS
)

_VALID_ATTACHMENT_SOURCES: frozenset[str] = frozenset(
    {"h5_task", "wecom", "broker_upload", "claim_h5"}
)

CLAIM_WORKBENCH_VISIBLE_PHASES: frozenset[str] = frozenset(
    {
        CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        CLAIM_PHASE_SUMMARY_READY,
        CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        CLAIM_PHASE_BROKER_REVIEW,
        CLAIM_PHASE_MANUAL_HANDLE,
    }
)

CLAIM_DISPLAY_TITLE = "Claim · 理赔资料"

_FORBIDDEN_DISPLAY_PHRASES = (
    "claim filed",
    "filed with carrier",
    "liability determined",
    "coverage confirmed",
    "正式报案",
    "已报案",
)


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _known_facts(case: dict[str, Any]) -> dict[str, Any]:
    facts = case.get("known_facts") or {}
    return facts if isinstance(facts, dict) else {}


def build_claim_summary(case: dict[str, Any]) -> dict[str, str | None]:
    """Accident basics for workbench list/drawer — from known_facts."""
    facts = _known_facts(case)
    return {
        "accident_datetime": _str_or_none(facts.get("accident_datetime")),
        "accident_location": _str_or_none(facts.get("accident_location")),
        "accident_description": _str_or_none(facts.get("accident_description")),
    }


def build_claim_display_status(case: dict[str, Any]) -> str:
    """Broker-safe status copy — intake only, never implies carrier filing."""
    phase = derive_claim_phase(case)
    if phase == CLAIM_PHASE_MANUAL_HANDLE:
        return "Manual handle · Broker review pending"
    if phase == CLAIM_PHASE_BROKER_REVIEW:
        return "Broker review pending"
    if phase in (CLAIM_PHASE_SUMMARY_READY, CLAIM_PHASE_INTAKE_READY_FOR_BROKER):
        return "Claim intake ready · Broker review pending"
    if phase == CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE:
        return "Claim Step 1 complete · Accident basics received"
    return "Claim intake in progress · Broker review pending"


def is_claim_workbench_visible(case: dict[str, Any]) -> bool:
    lane = str(case.get("service_lane") or "").strip().lower()
    if lane != SERVICE_LANE_CLAIM:
        return False
    return derive_claim_phase(case) in CLAIM_WORKBENCH_VISIBLE_PHASES


def display_status_is_broker_safe(display_status: str) -> bool:
    lowered = (display_status or "").strip().lower()
    return not any(phrase in lowered for phrase in _FORBIDDEN_DISPLAY_PHRASES)


def _claim_slot_state_map(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = case.get("claim_attachment_slots") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k).strip().lower(): v for k, v in raw.items() if isinstance(v, dict)}


def _h5_flow_skipped_slots(case: dict[str, Any]) -> set[str]:
    state = case.get("h5_photo_flow_state") or {}
    if not isinstance(state, dict):
        return set()
    if str(state.get("flow") or "").strip().lower() != FLOW_CLAIM_EVIDENCE_PACK:
        return set()
    return {str(s).strip().lower() for s in (state.get("skipped_slots") or []) if str(s).strip()}


def _attachment_slot_key(att: dict[str, Any]) -> str:
    for key in ("slot_assignment", "slot_key", "claim_slot"):
        value = str(att.get(key) or "").strip().lower()
        if value:
            return value
    meta = att.get("metadata")
    if isinstance(meta, dict):
        for key in ("slot_assignment", "slot_key", "claim_slot"):
            value = str(meta.get(key) or "").strip().lower()
            if value:
                return value
    return ""


def _is_claim_evidence_attachment(att: dict[str, Any]) -> bool:
    if not isinstance(att, dict):
        return False
    flow = str(att.get("flow") or "").strip().lower()
    slot = _attachment_slot_key(att)
    if flow == FLOW_CLAIM_EVIDENCE_PACK:
        return True
    return slot in _CLAIM_EVIDENCE_SLOT_KEYS


def _normalize_source_channel(source: str | None) -> str:
    normalized = str(source or "").strip().lower()
    if not normalized:
        return "none"
    if normalized in _VALID_ATTACHMENT_SOURCES:
        return normalized
    return normalized


def _claim_evidence_attachments_for_slot(
    case: dict[str, Any],
    slot_key: str,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        if not _is_claim_evidence_attachment(att):
            continue
        if _attachment_slot_key(att) != slot_key:
            continue
        matches.append(att)
    matches.sort(key=lambda item: str(item.get("received_at") or ""))
    return matches


def _latest_attachment_preview(att: dict[str, Any]) -> dict[str, Any]:
    return {
        "attachment_id": _str_or_none(att.get("attachment_id")),
        "filename": _str_or_none(att.get("filename")),
        "mime_type": _str_or_none(att.get("mime_type")),
        "source": _normalize_source_channel(att.get("source")),
        "received_at": _str_or_none(att.get("received_at")),
    }


def _resolve_slot_status(
    case: dict[str, Any],
    slot_key: str,
    *,
    attachments: list[dict[str, Any]],
) -> tuple[ClaimEvidenceSlotStatus, str | None, str]:
    explicit = _claim_slot_state_map(case).get(slot_key) or {}
    explicit_status = str(explicit.get("status") or "").strip().lower()
    skip_reason = _str_or_none(explicit.get("skip_reason"))

    if explicit_status == "needs_retake":
        source_channel = "none"
        if attachments:
            source_channel = _normalize_source_channel(attachments[-1].get("source"))
        return "needs_retake", skip_reason, source_channel

    if explicit_status == "skipped" or slot_key in _h5_flow_skipped_slots(case):
        if skip_reason is None and explicit_status == "skipped":
            skip_reason = _str_or_none(explicit.get("reason"))
        return "skipped", skip_reason, "none"

    if attachments:
        return "received", None, _normalize_source_channel(attachments[-1].get("source"))

    return "missing", None, "none"


def _slot_counts_for_required(
    slot_key: str,
    status: ClaimEvidenceSlotStatus,
    *,
    broker_override: bool,
) -> tuple[bool, bool]:
    """Return (received_or_skipped_for_activity, satisfies_required_gate)."""
    if status == "received":
        return True, True
    if status == "skipped":
        activity = True
        if slot_key == "customer_damage_photo" and not broker_override:
            return activity, False
        return activity, True
    return False, False


def _build_summary_text(
    slots: list[dict[str, Any]],
    *,
    completion_level: ClaimEvidenceCompletionLevel,
) -> str:
    received_labels = [s["label"] for s in slots if s["status"] == "received"]
    skipped_labels = [s["label"] for s in slots if s["status"] == "skipped"]
    missing_required = [s["label"] for s in slots if s["status"] == "missing" and s["required_level"] == "required"]
    missing_soft = [
        s["label"] for s in slots if s["status"] == "missing" and s["required_level"] == "soft_required"
    ]
    retake_labels = [s["label"] for s in slots if s["status"] == "needs_retake"]

    parts: list[str] = []
    if received_labels:
        parts.append(f"已收到{'、'.join(received_labels)}")
    if skipped_labels:
        parts.append(f"已记录跳过{'、'.join(skipped_labels)}")
    if retake_labels:
        parts.append(f"{'、'.join(retake_labels)}需要重新上传")
    if missing_required:
        parts.append(f"还缺{'、'.join(missing_required)}")
    elif missing_soft:
        parts.append(f"还缺{'、'.join(missing_soft)}")
    scene = next((s for s in slots if s["slot_key"] == "scene_photo"), None)
    if scene and scene["status"] == "missing" and completion_level in ("review_ready", "complete"):
        parts.append("现场照片可选")
    if not parts:
        return "尚未收到理赔照片资料。"
    return "；".join(parts) + "。"


def _build_broker_next_action(
    slots: list[dict[str, Any]],
    *,
    completion_level: ClaimEvidenceCompletionLevel,
) -> str:
    by_key = {s["slot_key"]: s for s in slots}
    if any(s["status"] == "needs_retake" for s in slots):
        return "有照片需要重新上传，请陈总确认后联系客户补充。"

    customer = by_key.get("customer_damage_photo") or {}
    other_party = by_key.get("other_party_vehicle_photo") or {}
    scene = by_key.get("scene_photo") or {}

    if customer.get("status") == "missing":
        return "请客户补充自己车损照片。"

    if other_party.get("status") == "missing":
        return "请客户补充对方车辆/车牌照片，或记录无法提供原因。"

    if completion_level in ("review_ready", "complete"):
        if scene.get("status") == "missing":
            return "资料基本够陈总先看；现场照片可选，有的话可继续补充。"
        return "资料已基本齐全，请陈总人工确认后决定下一步。"

    return "请继续收集理赔照片资料。"


def _derive_completion_level(
    slots: list[dict[str, Any]],
    *,
    missing_required_slots: list[str],
    missing_soft_required_slots: list[str],
    received_slots: list[str],
    skipped_slots: list[str],
) -> ClaimEvidenceCompletionLevel:
    if not received_slots and not skipped_slots:
        return "empty"

    customer = next((s for s in slots if s["slot_key"] == "customer_damage_photo"), None)
    other_party = next((s for s in slots if s["slot_key"] == "other_party_vehicle_photo"), None)
    scene = next((s for s in slots if s["slot_key"] == "scene_photo"), None)

    if customer is None or customer["status"] not in ("received",):
        return "partial"

    if other_party is None or other_party["status"] not in ("received", "skipped"):
        return "required_complete"

    if scene is None or scene["status"] not in ("received", "skipped"):
        return "review_ready"

    if missing_required_slots or missing_soft_required_slots:
        return "review_ready"

    return "complete"


def build_claim_evidence_summary(case: dict[str, Any]) -> dict[str, Any]:
    """Pure Claim evidence checklist summary for Workbench enrichment."""
    slot_state_map = _claim_slot_state_map(case)
    slot_rows: list[dict[str, Any]] = []
    missing_required_slots: list[str] = []
    missing_soft_required_slots: list[str] = []
    received_slots: list[str] = []
    skipped_slots: list[str] = []

    for definition in CLAIM_EVIDENCE_SLOT_DEFINITIONS:
        slot_key = definition["slot_key"]
        required_level = definition["required_level"]
        attachments = _claim_evidence_attachments_for_slot(case, slot_key)
        status, skip_reason, source_channel = _resolve_slot_status(
            case,
            slot_key,
            attachments=attachments,
        )
        explicit = slot_state_map.get(slot_key) or {}
        broker_override = bool(explicit.get("broker_override"))

        latest_attachment = None
        if attachments and status in ("received", "needs_retake"):
            latest_attachment = _latest_attachment_preview(attachments[-1])

        needs_broker_review = status in ("received", "needs_retake")

        slot_rows.append(
            {
                "slot_key": slot_key,
                "label": definition["label"],
                "required_level": required_level,
                "status": status,
                "source_channel": source_channel,
                "attachment_count": len(attachments) if status in ("received", "needs_retake") else 0,
                "latest_attachment": latest_attachment,
                "skip_reason": skip_reason,
                "needs_broker_review": needs_broker_review,
            }
        )

        _, satisfies_gate = _slot_counts_for_required(
            slot_key,
            status,
            broker_override=broker_override,
        )
        if status == "received":
            received_slots.append(slot_key)
        elif status == "skipped":
            skipped_slots.append(slot_key)

        if required_level == "required" and not satisfies_gate:
            missing_required_slots.append(slot_key)
        elif required_level == "soft_required" and status == "missing":
            missing_soft_required_slots.append(slot_key)

    completion_level = _derive_completion_level(
        slot_rows,
        missing_required_slots=missing_required_slots,
        missing_soft_required_slots=missing_soft_required_slots,
        received_slots=received_slots,
        skipped_slots=skipped_slots,
    )
    broker_next_action = _build_broker_next_action(slot_rows, completion_level=completion_level)
    summary_text = _build_summary_text(slot_rows, completion_level=completion_level)

    return {
        "slots": slot_rows,
        "missing_required_slots": missing_required_slots,
        "missing_soft_required_slots": missing_soft_required_slots,
        "received_slots": received_slots,
        "skipped_slots": skipped_slots,
        "completion_level": completion_level,
        "broker_next_action": broker_next_action,
        "summary_text": summary_text,
    }


def claim_evidence_copy_is_broker_safe(text: str) -> bool:
    """Return True when summary / broker copy contains no forbidden automation claims."""
    content = text or ""
    for phrase in CLAIM_FORBIDDEN_AUTOMATION_CLAIMS:
        if phrase in content:
            return False
    forbidden_extra = ("一定会赔",)
    return not any(phrase in content for phrase in forbidden_extra)


def enrich_claim_for_workbench(case: dict[str, Any]) -> dict[str, Any]:
    """Add Claim workbench display fields when service_lane=claim."""
    row = dict(case)
    lane = str(case.get("service_lane") or "").strip().lower()
    if lane != SERVICE_LANE_CLAIM:
        return row

    phase = derive_claim_phase(case)
    display_status = build_claim_display_status(case)
    row["workflow_id"] = "claim_simplified"
    row["workflow_phase"] = phase
    row["display_title"] = CLAIM_DISPLAY_TITLE
    row["display_status"] = display_status
    row["claim_summary"] = build_claim_summary(case)
    row["claim_evidence_summary"] = build_claim_evidence_summary(case)
    row["workbench_visible"] = is_claim_workbench_visible(case)
    return row
