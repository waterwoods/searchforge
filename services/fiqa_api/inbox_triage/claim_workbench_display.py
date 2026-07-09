"""P19H-3a — Claim case workbench display enrichment (no schema migration)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from services.fiqa_api.inbox_triage.h5_task_token import FLOW_CLAIM_EVIDENCE_PACK
from services.fiqa_api.wecom.claim_state import (
    CLAIM_ACCIDENT_BASICS_FIELDS,
    CLAIM_FORBIDDEN_AUTOMATION_CLAIMS,
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
    CLAIM_PHASE_BROKER_REVIEW,
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    CLAIM_PHASE_MANUAL_HANDLE,
    CLAIM_PHASE_STARTED,
    CLAIM_PHASE_SUMMARY_READY,
    CLAIM_PHOTO_FLOW_SLOTS,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
    is_accident_basics_complete,
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
        return "Claim · Broker Review · Manual handle"
    if phase in (CLAIM_PHASE_BROKER_REVIEW, CLAIM_PHASE_INTAKE_READY_FOR_BROKER):
        return "Claim · Broker Review"
    if phase in (CLAIM_PHASE_SUMMARY_READY, CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE):
        return "Claim · 记录中 · Broker Review pending"
    if phase in (CLAIM_PHASE_STARTED, CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS):
        return "Claim · 记录中"
    return "Claim intake in progress · Broker review pending"


def build_wecom_media_intake_display_status(case: dict[str, Any]) -> str:
    """P19H-3f-1 — Unassigned WeCom media is not a formal Claim case."""
    return "待确认材料 · 未分配微信资料 · 不是正式 case"


def build_wecom_media_intake_display_title() -> str:
    return "待确认材料"


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
        channel = _normalize_source_channel(explicit.get("source_channel"))
        return "skipped", skip_reason, channel if channel != "none" else "none"

    if explicit_status == "received":
        channel = _normalize_source_channel(explicit.get("source_channel"))
        if attachments:
            return (
                "received",
                None,
                channel if channel != "none" else _normalize_source_channel(attachments[-1].get("source")),
            )
        if channel != "none":
            return "received", None, channel

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


def _collect_unassigned_wecom_claim_photos(case: dict[str, Any]) -> list[dict[str, Any]]:
    """WeCom claim photos bound to case but not assigned to an evidence slot."""
    matches: list[dict[str, Any]] = []
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        if str(att.get("source") or "").strip().lower() != "wecom":
            continue
        slot = _attachment_slot_key(att)
        if slot in _CLAIM_EVIDENCE_SLOT_KEYS:
            continue
        if slot == "unassigned" or str(att.get("flow") or "").strip().lower() == "claim_multichannel_evidence":
            matches.append(att)
    matches.sort(key=lambda item: str(item.get("received_at") or ""))
    return matches


def _build_unassigned_wecom_photos_summary(case: dict[str, Any]) -> dict[str, Any]:
    photos = _collect_unassigned_wecom_claim_photos(case)
    items = [
        {
            "attachment_id": _str_or_none(att.get("attachment_id")),
            "filename": _str_or_none(att.get("filename")) or "wecom_image.jpg",
            "mime_type": _str_or_none(att.get("mime_type")),
            "source": "wecom",
            "received_at": _str_or_none(att.get("received_at")),
            "needs_broker_review": bool(att.get("needs_broker_review", True)),
        }
        for att in photos
    ]
    count = len(items)
    broker_next_action = (
        f"有 {count} 张微信照片待陈总人工归类。"
        if count
        else ""
    )
    return {
        "count": count,
        "items": items,
        "broker_next_action": broker_next_action,
    }


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
    unassigned_wecom = _build_unassigned_wecom_photos_summary(case)
    broker_next_action = _build_broker_next_action(slot_rows, completion_level=completion_level)
    if unassigned_wecom["count"] and unassigned_wecom.get("broker_next_action"):
        if broker_next_action == "请继续收集理赔照片资料。":
            broker_next_action = str(unassigned_wecom["broker_next_action"])
        else:
            broker_next_action = f"{broker_next_action} {unassigned_wecom['broker_next_action']}"
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
        "unassigned_wecom_photos": unassigned_wecom,
    }


def claim_evidence_copy_is_broker_safe(text: str) -> bool:
    """Return True when summary / broker copy contains no forbidden automation claims."""
    content = text or ""
    for phrase in CLAIM_FORBIDDEN_AUTOMATION_CLAIMS:
        if phrase in content:
            return False
    forbidden_extra = ("一定会赔", "对方全责", "已受理", "已报案")
    return not any(phrase in content for phrase in forbidden_extra)


# ---------------------------------------------------------------------------
# P19H-3e-1 — Claim Case Brief (deterministic, no LLM)
# ---------------------------------------------------------------------------

InjuryStatus = Literal["yes", "no", "unknown"]
PoliceStatus = Literal["yes", "no", "unknown"]
BriefConfidence = Literal["low", "medium", "high"]

_INJURY_NO_KEYWORDS = ("没受伤", "人没事", "没有受伤", "无人受伤", "没事", "no injury")
_INJURY_YES_KEYWORDS = ("受伤", "救护车", "医院", "疼", "骨折", "流血")
_POLICE_YES_KEYWORDS = ("报警", "police", "police report", "报案号", "警号")
_POLICE_NO_KEYWORDS = ("没报警", "未报警", "没有报警")
_OTHER_PARTY_KEYWORDS = ("对方", "车牌", "保险卡", "driver license", "驾照", "对方车")


def _claim_timeline_events(case: dict[str, Any]) -> list[dict[str, Any]]:
    raw = case.get("claim_timeline")
    if not isinstance(raw, list):
        return []
    events = [e for e in raw if isinstance(e, dict)]
    return sorted(events, key=lambda e: str(e.get("created_at") or ""))


def _scan_timeline_text(case: dict[str, Any]) -> str:
    parts: list[str] = []
    for event in _claim_timeline_events(case):
        if str(event.get("event_type") or "") in ("customer_text", "basics_complete"):
            text = str(event.get("text") or "").strip()
            if text:
                parts.append(text)
    return " ".join(parts)


def _resolve_injury_status(case: dict[str, Any]) -> InjuryStatus:
    facts = _known_facts(case)
    stored = str(facts.get("injury_status") or "").strip().lower()
    if stored in ("yes", "no", "unknown"):
        return stored  # type: ignore[return-value]
    corpus = _scan_timeline_text(case)
    if not corpus:
        return "unknown"
    if any(k in corpus for k in _INJURY_NO_KEYWORDS):
        return "no"
    if any(k in corpus for k in _INJURY_YES_KEYWORDS):
        return "yes"
    return "unknown"


def _resolve_police_status(case: dict[str, Any]) -> PoliceStatus:
    facts = _known_facts(case)
    stored = str(facts.get("police_involved") or "").strip().lower()
    if stored in ("yes", "no", "unknown"):
        return stored  # type: ignore[return-value]
    corpus = _scan_timeline_text(case)
    if not corpus:
        return "unknown"
    if any(k in corpus for k in _POLICE_NO_KEYWORDS):
        return "no"
    if any(k in corpus for k in _POLICE_YES_KEYWORDS):
        return "yes"
    return "unknown"


def _resolve_other_party_info(case: dict[str, Any]) -> str | None:
    facts = _known_facts(case)
    stored = str(facts.get("other_party_info") or "").strip()
    if stored:
        return stored
    corpus = _scan_timeline_text(case)
    if any(k in corpus for k in _OTHER_PARTY_KEYWORDS):
        return "mentioned"
    return None


def _count_photos(case: dict[str, Any]) -> tuple[int, dict[str, int]]:
    sources: dict[str, int] = {"wecom": 0, "h5_task": 0, "broker_upload": 0}
    count = 0
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        mime = str(att.get("mime_type") or "").lower()
        msgtype = str(att.get("msgtype") or "").lower()
        if mime.startswith("image/") or msgtype == "image" or str(att.get("type") or "").endswith("photo"):
            count += 1
            src = _normalize_source_channel(str(att.get("source") or ""))
            if src in sources:
                sources[src] += 1
            elif src == "claim_h5":
                sources["h5_task"] += 1
    return count, sources


def _count_voice(case: dict[str, Any]) -> int:
    timeline = _claim_timeline_events(case)
    return sum(1 for e in timeline if str(e.get("event_type") or "") == "customer_voice_stub")


def _build_brief_summary(
    case: dict[str, Any],
    *,
    key_facts: dict[str, Any],
    photo_count: int,
) -> str:
    facts = _known_facts(case)
    dt = _str_or_none(key_facts.get("accident_datetime") or facts.get("accident_datetime"))
    loc = _str_or_none(key_facts.get("accident_location") or facts.get("accident_location"))
    desc = _str_or_none(key_facts.get("accident_description") or facts.get("accident_description"))
    injury = key_facts.get("injury_status", "unknown")

    has_basics = bool(dt and loc and desc)
    if not has_basics:
        return f"客户已发起理赔记录。事故时间、地点或经过仍需补充。已收到 {photo_count} 张照片。"

    injury_phrase = {
        "no": "客户表示人没事",
        "yes": "客户表示有人受伤",
        "unknown": "受伤情况尚未确认",
    }.get(str(injury), "受伤情况尚未确认")

    desc_short = desc[:80] + ("…" if desc and len(desc) > 80 else "") if desc else "事故经过已记录"
    parts = [f"客户报告{dt or '时间待确认'}在{loc or '地点待确认'}{desc_short}。"]
    parts.append(f"{injury_phrase}。")
    parts.append(f"已收到 {photo_count} 张微信照片。")
    other = key_facts.get("other_party_info")
    if other:
        parts.append("对方信息已在叙述中提及。")
    else:
        parts.append("对方保险信息尚未确认。")
    return "".join(parts)


def _build_missing_info(key_facts: dict[str, Any], photo_count: int) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []

    def add(key: str, label: str, severity: str, reason: str) -> None:
        if len(items) >= 5:
            return
        items.append({"key": key, "label": label, "severity": severity, "reason": reason})

    injury = str(key_facts.get("injury_status") or "unknown")
    if injury == "unknown":
        add("injury_status", "是否有人受伤", "critical", "unknown")

    if not _str_or_none(key_facts.get("accident_datetime")):
        add("accident_datetime", "事故时间", "important", "missing")
    if not _str_or_none(key_facts.get("accident_location")):
        add("accident_location", "事故地点", "important", "missing")
    if not _str_or_none(key_facts.get("accident_description")):
        add("accident_description", "事故经过", "important", "missing")
    if not key_facts.get("other_party_info"):
        add("other_party_info", "对方车牌或保险信息", "important", "missing")

    police = str(key_facts.get("police_involved") or "unknown")
    if police == "unknown":
        add("police_involved", "是否报警", "optional", "unknown")

    if photo_count == 0:
        add("photos", "车损或现场照片", "optional", "missing")

    return items


def _build_next_best_question(missing_info: list[dict[str, str]]) -> str:
    priority_order = [
        ("injury_status", "请问有人受伤吗？"),
        ("accident_datetime", "请问事故大概是什么时候？"),
        ("accident_location", "请问事故在哪里发生的？"),
        ("accident_description", "能简单说一下事故是怎么发生的吗？"),
        ("other_party_info", "请问对方车牌或保险信息拿到了吗？"),
        ("police_involved", "请问现场有没有报警或 police report number？"),
        ("photos", "如果方便，可以发几张车损或现场照片吗？"),
    ]
    missing_keys = {item["key"] for item in missing_info}
    for key, question in priority_order:
        if key in missing_keys:
            return question
    return "如果方便，可以发几张车损或现场照片吗？"


def _derive_brief_confidence(
    *,
    basics_complete: bool,
    injury: InjuryStatus,
    photo_count: int,
    other_party: str | None,
    police: PoliceStatus,
    description: str | None,
) -> BriefConfidence:
    if not basics_complete:
        return "low"
    if not description or (len(description or "") < 8 and photo_count == 0):
        return "low"
    if basics_complete and photo_count > 0 and injury != "unknown":
        if other_party or police in ("yes", "no"):
            return "high"
    if basics_complete or photo_count > 0:
        return "medium"
    return "low"


def _source_event_ids(case: dict[str, Any]) -> list[str]:
    relevant_types = {"customer_text", "customer_photo", "basics_complete"}
    ids: list[str] = []
    for event in reversed(_claim_timeline_events(case)):
        if str(event.get("event_type") or "") not in relevant_types:
            continue
        eid = str(event.get("event_id") or "").strip()
        if eid:
            ids.append(eid)
        if len(ids) >= 5:
            break
    return list(reversed(ids))


def build_claim_case_brief(case: dict[str, Any]) -> dict[str, Any]:
    """Deterministic Claim Case Brief for Workbench hero panel (P19H-3e-1)."""
    facts = _known_facts(case)
    injury = _resolve_injury_status(case)
    police = _resolve_police_status(case)
    other_party = _resolve_other_party_info(case)
    photo_count, photo_sources = _count_photos(case)
    evidence_summary = build_claim_evidence_summary(case)
    unassigned_count = int((evidence_summary.get("unassigned_wecom_photos") or {}).get("count") or 0)

    key_facts: dict[str, Any] = {
        "accident_datetime": _str_or_none(facts.get("accident_datetime")),
        "accident_location": _str_or_none(facts.get("accident_location")),
        "accident_description": _str_or_none(facts.get("accident_description")),
        "injury_status": injury,
        "police_involved": police,
        "other_party_info": other_party,
        "own_vehicle_info": _str_or_none(facts.get("own_vehicle_info")),
    }

    basics_complete = is_accident_basics_complete(case)
    missing_info = _build_missing_info(key_facts, photo_count)
    next_question = _build_next_best_question(missing_info)
    confidence = _derive_brief_confidence(
        basics_complete=basics_complete,
        injury=injury,
        photo_count=photo_count,
        other_party=other_party,
        police=police,
        description=key_facts.get("accident_description"),
    )

    return {
        "summary": _build_brief_summary(case, key_facts=key_facts, photo_count=photo_count),
        "customer": {
            "name": _str_or_none(case.get("customer_name")),
            "phone": _str_or_none(case.get("customer_phone")),
            "wecom_external_userid": _str_or_none(case.get("wecom_external_userid")),
        },
        "key_facts": key_facts,
        "evidence_received": {
            "photo_count": photo_count,
            "photo_sources": photo_sources,
            "voice_count": _count_voice(case),
            "has_basics": basics_complete,
            "slots_received": list(evidence_summary.get("received_slots") or []),
            "slots_missing": list(evidence_summary.get("missing_required_slots") or [])
            + list(evidence_summary.get("missing_soft_required_slots") or []),
            "unassigned_wecom_photos": unassigned_count,
        },
        "missing_info": missing_info,
        "next_best_question": next_question,
        "confidence": confidence,
        "source_event_ids": _source_event_ids(case),
        "brief_updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "brief_version": 1,
    }


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
    row["claim_timeline"] = _claim_timeline_events(case)
    row["claim_case_brief"] = build_claim_case_brief(case)
    row["workbench_visible"] = is_claim_workbench_visible(case)
    return row
