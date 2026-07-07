"""P19H-1 — Claim state machine foundation (pure helpers, no Cloud SQL / routing).

Production routing must hydrate claim cases via ``get_case_for_read`` /
``list_all_cases_for_read`` (Postgres read facade). Legacy JSON-only
``get_case_by_id`` paths are forbidden for phase derivation — same invariant
as Add Vehicle Phase 2 (P19E-1).
"""

from __future__ import annotations

from typing import Any, Final, Literal

# --- Lane / phase constants (recon §8) ---

SERVICE_LANE_CLAIM: Final[str] = "claim"

CLAIM_PHASE_STARTED: Final[str] = "claim_started"
CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS: Final[str] = "accident_basics_in_progress"
CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE: Final[str] = "accident_basics_complete"
CLAIM_PHASE_PHOTOS_IN_PROGRESS: Final[str] = "photos_in_progress"
CLAIM_PHASE_PHOTOS_COMPLETE: Final[str] = "photos_complete"
CLAIM_PHASE_OTHER_PARTY_IN_PROGRESS: Final[str] = "other_party_in_progress"
CLAIM_PHASE_OTHER_PARTY_COMPLETE: Final[str] = "other_party_complete"
CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS: Final[str] = "injury_police_in_progress"
CLAIM_PHASE_INJURY_POLICE_COMPLETE: Final[str] = "injury_police_complete"
CLAIM_PHASE_SUMMARY_READY: Final[str] = "claim_summary_ready"
CLAIM_PHASE_BROKER_REVIEW: Final[str] = "broker_review"
CLAIM_PHASE_BROKER_NEEDS_MORE_INFO: Final[str] = "broker_needs_more_info"
CLAIM_PHASE_BROKER_DONE: Final[str] = "broker_done"
CLAIM_PHASE_MANUAL_HANDLE: Final[str] = "manual_handle"

CLAIM_PHASES: Final[tuple[str, ...]] = (
    CLAIM_PHASE_STARTED,
    CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_PHOTOS_IN_PROGRESS,
    CLAIM_PHASE_PHOTOS_COMPLETE,
    CLAIM_PHASE_OTHER_PARTY_IN_PROGRESS,
    CLAIM_PHASE_OTHER_PARTY_COMPLETE,
    CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS,
    CLAIM_PHASE_INJURY_POLICE_COMPLETE,
    CLAIM_PHASE_SUMMARY_READY,
    CLAIM_PHASE_BROKER_REVIEW,
    CLAIM_PHASE_BROKER_NEEDS_MORE_INFO,
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_MANUAL_HANDLE,
)

CUSTOMER_CLAIM_PHASES: Final[tuple[str, ...]] = (
    CLAIM_PHASE_STARTED,
    CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_PHOTOS_IN_PROGRESS,
    CLAIM_PHASE_PHOTOS_COMPLETE,
    CLAIM_PHASE_OTHER_PARTY_IN_PROGRESS,
    CLAIM_PHASE_OTHER_PARTY_COMPLETE,
    CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS,
    CLAIM_PHASE_INJURY_POLICE_COMPLETE,
    CLAIM_PHASE_SUMMARY_READY,
)

# --- Required / optional text + composite fields (recon §6) ---

CLAIM_REQUIRED_TEXT_FIELDS: Final[tuple[str, ...]] = (
    "accident_datetime",
    "accident_location",
    "accident_description",
    "anyone_injured",
    "police_involved",
)

CLAIM_REQUIRED_COMPOSITE_FIELDS: Final[tuple[str, ...]] = (
    "customer_damage_photo",
    "other_party_vehicle_or_plate",
    "other_party_info",
)

CLAIM_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    *CLAIM_REQUIRED_TEXT_FIELDS,
    *CLAIM_REQUIRED_COMPOSITE_FIELDS,
)

CLAIM_OPTIONAL_FIELDS: Final[tuple[str, ...]] = (
    "scene_photo",
    "police_report_photo",
    "tow_repair_info",
    "witness_info",
    "existing_claim_number",
)

CLAIM_ACCIDENT_BASICS_FIELDS: Final[tuple[str, ...]] = (
    "accident_datetime",
    "accident_location",
    "accident_description",
)

CLAIM_INJURY_POLICE_FIELDS: Final[tuple[str, ...]] = (
    "anyone_injured",
    "police_involved",
)

OTHER_PARTY_INFO_SIGNALS: Final[tuple[str, ...]] = (
    "other_party_insurance_card",
    "other_party_license",
    "other_party_plate",
    "other_party_phone",
    "other_party_name",
)

OTHER_PARTY_INFO_PHOTO_SLOTS: Final[tuple[str, ...]] = (
    "other_party_insurance_card",
    "other_party_license",
)

# --- Photo / document slots (recon §7) ---

CLAIM_PHOTO_FLOW_SLOTS: Final[tuple[str, ...]] = (
    "customer_damage_photo",
    "other_party_vehicle_photo",
    "scene_photo",
)

CLAIM_PHOTO_FLOW_OPTIONAL_SLOTS: Final[frozenset[str]] = frozenset({"scene_photo"})

CLAIM_ALL_ATTACHMENT_SLOTS: Final[tuple[str, ...]] = (
    "customer_damage_photo",
    "other_party_vehicle_photo",
    "scene_photo",
    "other_party_insurance_card",
    "other_party_license",
    "police_report_photo",
)

CLAIM_SLOT_REQUIRED_FOR_PHOTO_PHASE: Final[frozenset[str]] = frozenset(
    {"customer_damage_photo", "other_party_vehicle_photo"}
)

ClaimSlotStatus = Literal["empty", "received", "skipped", "needs_retake"]

CLAIM_SLOT_STATUSES: Final[tuple[str, ...]] = ("empty", "received", "skipped", "needs_retake")

_SLOT_LABELS_ZH: dict[str, str] = {
    "accident_datetime": "事故时间",
    "accident_location": "事故地点",
    "accident_description": "事故描述",
    "customer_damage_photo": "您的车损伤照片",
    "other_party_vehicle_or_plate": "对方车辆 / 车牌",
    "other_party_vehicle_photo": "对方车辆 / 车牌照片",
    "other_party_info": "对方信息",
    "other_party_insurance_card": "对方保险卡",
    "other_party_license": "对方驾照",
    "other_party_plate": "对方车牌",
    "other_party_phone": "对方电话",
    "other_party_name": "对方姓名",
    "anyone_injured": "是否有人受伤",
    "police_involved": "是否报警",
    "scene_photo": "现场照片",
    "police_report_photo": "警方报告",
    "tow_repair_info": "拖车 / 修理厂信息",
    "witness_info": "证人信息",
    "existing_claim_number": "已有报案号",
}

# --- Validation / guardrail constants (recon §14) ---

CLAIM_MAX_DESCRIPTION_LENGTH: Final[int] = 500

CLAIM_FORBIDDEN_AUTOMATION_CLAIMS: Final[tuple[str, ...]] = (
    "已经帮您报案",
    "理赔已经提交",
    "是对方责任",
    "您的保险一定会赔",
    "我们已经联系保险公司",
    "不用担心，肯定没问题",
    "我帮您报案了",
    "已帮您报案",
    "这是对方的责任",
    "您的保险可以赔",
    "理赔已完成",
    "已联系保险公司",
    "claim 已正式提交",
    "已向保险公司报案",
)

CLAIM_SAFE_COPY_INVARIANTS: Final[tuple[str, ...]] = (
    "我们先帮您收集资料",
    "陈总会人工查看",
    "这不代表已正式报案",
    "我们不能判断责任",
    "是否报案 / coverage 需要陈总确认",
    "如果有人受伤，请优先确保安全并联系陈总/紧急服务",
    "资料已转陈总人工处理",
    "陈总会帮您核实",
    "陈总会跟进后续步骤",
)

# Back-compat alias used by early P19H-1 tests
CLAIM_FORBIDDEN_CUSTOMER_COPY: Final[tuple[str, ...]] = CLAIM_FORBIDDEN_AUTOMATION_CLAIMS

CLAIM_SAFE_STATUS_COPY: Final[tuple[str, ...]] = CLAIM_SAFE_COPY_INVARIANTS

INJURY_YES_VALUES: Final[frozenset[str]] = frozenset(
    {"yes", "y", "true", "1", "是", "有", "受伤", "有人受伤", "injured"}
)
INJURY_NO_VALUES: Final[frozenset[str]] = frozenset(
    {"no", "n", "false", "0", "否", "没有", "没受伤", "无人受伤"}
)
POLICE_YES_VALUES: Final[frozenset[str]] = frozenset(
    {"yes", "y", "true", "1", "是", "有", "已报警", "报了警"}
)
POLICE_NO_VALUES: Final[frozenset[str]] = frozenset(
    {"no", "n", "false", "0", "否", "没有", "未报警", "没报警"}
)

CLAIM_YES_NO_VALUES: Final[frozenset[str]] = INJURY_YES_VALUES | INJURY_NO_VALUES

CUSTOMER_ACTION_COLLECT_ACCIDENT_BASICS: Final[str] = "collect_accident_basics"
CUSTOMER_ACTION_COLLECT_CLAIM_PHOTOS: Final[str] = "collect_claim_photos"
CUSTOMER_ACTION_COLLECT_OTHER_PARTY_INFO: Final[str] = "collect_other_party_info"
CUSTOMER_ACTION_COLLECT_INJURY_POLICE: Final[str] = "collect_injury_police"
CUSTOMER_ACTION_AWAIT_BROKER_REVIEW: Final[str] = "await_broker_review"
CUSTOMER_ACTION_BROKER_DONE: Final[str] = "broker_done_readonly"

BROKER_NOTE_INJURY_YES_PHONE_FIRST: Final[str] = "injury_yes_phone_first"

GUIDED_STATE_COLLECTING_TEXT: Final[str] = "collecting_text_fields"
GUIDED_STATE_READY_FOR_BROKER_REVIEW: Final[str] = "ready_for_broker_review"
GUIDED_STATE_BROKER_NEEDS_MORE_INFO: Final[str] = "broker_needs_more_info"


def _collected_field_names(case_extra: dict[str, Any]) -> set[str]:
    return {str(x).lower() for x in (case_extra.get("collected_fields") or []) if str(x).strip()}


def _known_facts(case_extra: dict[str, Any]) -> dict[str, Any]:
    facts = case_extra.get("known_facts") or {}
    return facts if isinstance(facts, dict) else {}


def _fact_value(case_extra: dict[str, Any], key: str) -> str | None:
    raw = _known_facts(case_extra).get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _has_collected_field(case_extra: dict[str, Any], field: str) -> bool:
    return field.lower() in _collected_field_names(case_extra)


def normalize_claim_yes_no(value: str | None) -> Literal["yes", "no"] | None:
    """Normalize common Chinese/English yes/no inputs for injury/police fields."""
    lowered = (value or "").strip().lower()
    if not lowered:
        return None
    if lowered in INJURY_YES_VALUES or lowered in POLICE_YES_VALUES:
        return "yes"
    if lowered in INJURY_NO_VALUES or lowered in POLICE_NO_VALUES:
        return "no"
    return None


def is_valid_claim_required_text(value: str | None) -> bool:
    """Foundation check: non-empty required text (no deep datetime parsing)."""
    return bool((value or "").strip())


def _text_field_satisfied(case_extra: dict[str, Any], field: str) -> bool:
    if not _has_collected_field(case_extra, field):
        return False
    return is_valid_claim_required_text(_fact_value(case_extra, field))


def _boolean_field_satisfied(case_extra: dict[str, Any], field: str) -> bool:
    if not _has_collected_field(case_extra, field):
        return False
    value = _fact_value(case_extra, field)
    return normalize_claim_yes_no(value) is not None


def _slot_state_map(case_extra: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = case_extra.get("claim_attachment_slots") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k).strip().lower(): v for k, v in raw.items() if isinstance(v, dict)}


def _attachments_by_slot(case_extra: dict[str, Any]) -> set[str]:
    slots: set[str] = set()
    for att in case_extra.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        source = str(att.get("source") or "").strip().lower()
        if source not in ("h5_task", "wecom", "claim_h5"):
            continue
        slot = str(att.get("slot_assignment") or "").strip().lower()
        if slot:
            slots.add(slot)
    return slots


def get_claim_attachment_slot_status(case_extra: dict[str, Any], slot: str) -> ClaimSlotStatus:
    """Return slot status from explicit state map or inferred from attachments."""
    slot_norm = (slot or "").strip().lower()
    state_map = _slot_state_map(case_extra)
    explicit = state_map.get(slot_norm) or {}
    status = str(explicit.get("status") or "").strip().lower()
    if status in CLAIM_SLOT_STATUSES:
        return status  # type: ignore[return-value]
    if slot_norm in _attachments_by_slot(case_extra):
        return "received"
    return "empty"


def get_claim_attachment_slots(case_extra: dict[str, Any]) -> dict[str, ClaimSlotStatus]:
    """All known claim slots with current status."""
    slots = set(CLAIM_ALL_ATTACHMENT_SLOTS) | _attachments_by_slot(case_extra) | set(_slot_state_map(case_extra))
    return {slot: get_claim_attachment_slot_status(case_extra, slot) for slot in sorted(slots)}


def _slot_is_received(case_extra: dict[str, Any], slot: str) -> bool:
    return get_claim_attachment_slot_status(case_extra, slot) == "received"


def _slot_is_satisfied(case_extra: dict[str, Any], slot: str) -> bool:
    status = get_claim_attachment_slot_status(case_extra, slot)
    return status in ("received", "skipped")


def is_customer_damage_photo_complete(case_extra: dict[str, Any]) -> bool:
    return _slot_is_received(case_extra, "customer_damage_photo")


def is_other_party_vehicle_or_plate_complete(case_extra: dict[str, Any]) -> bool:
    if _slot_is_received(case_extra, "other_party_vehicle_photo"):
        return True
    plate = _fact_value(case_extra, "other_party_plate")
    return bool(plate)


def is_other_party_info_complete(case_extra: dict[str, Any]) -> bool:
    """At least one other-party artifact (recon §6.3 partial-OK rule)."""
    facts = _known_facts(case_extra)
    for slot in OTHER_PARTY_INFO_PHOTO_SLOTS:
        if _slot_is_received(case_extra, slot):
            return True
    if _slot_is_received(case_extra, "other_party_vehicle_photo"):
        return True
    for key in ("other_party_plate", "other_party_phone", "other_party_name"):
        if str(facts.get(key) or "").strip():
            return True
    return False


def is_accident_basics_complete(case_extra: dict[str, Any]) -> bool:
    return all(_text_field_satisfied(case_extra, field) for field in CLAIM_ACCIDENT_BASICS_FIELDS)


def are_claim_photos_complete(case_extra: dict[str, Any]) -> bool:
    if not is_customer_damage_photo_complete(case_extra):
        return False
    return is_other_party_vehicle_or_plate_complete(case_extra)


def is_injury_police_complete(case_extra: dict[str, Any]) -> bool:
    return all(_boolean_field_satisfied(case_extra, field) for field in CLAIM_INJURY_POLICE_FIELDS)


def _field_is_satisfied(case_extra: dict[str, Any], field: str) -> bool:
    if field in CLAIM_ACCIDENT_BASICS_FIELDS:
        return _text_field_satisfied(case_extra, field)
    if field == "customer_damage_photo":
        return is_customer_damage_photo_complete(case_extra)
    if field == "other_party_vehicle_or_plate":
        return is_other_party_vehicle_or_plate_complete(case_extra)
    if field == "other_party_info":
        return is_other_party_info_complete(case_extra)
    if field in CLAIM_INJURY_POLICE_FIELDS:
        return _boolean_field_satisfied(case_extra, field)
    if field in CLAIM_OPTIONAL_FIELDS:
        if field.endswith("_photo"):
            return _slot_is_satisfied(case_extra, field)
        return _text_field_satisfied(case_extra, field) or bool(_fact_value(case_extra, field))
    return False


def is_claim_summary_ready(case_extra: dict[str, Any]) -> bool:
    """All MVP required fields satisfied; optional gaps allowed."""
    return all(_field_is_satisfied(case_extra, field) for field in CLAIM_REQUIRED_FIELDS)


def get_claim_collected_fields(case_extra: dict[str, Any]) -> dict[str, bool]:
    """Required + optional field satisfaction map."""
    all_fields = (*CLAIM_REQUIRED_FIELDS, *CLAIM_OPTIONAL_FIELDS)
    return {field: _field_is_satisfied(case_extra, field) for field in all_fields}


def get_claim_missing_items(case_extra: dict[str, Any]) -> list[dict[str, str]]:
    """Missing required items for Progress Card / broker checklist."""
    missing: list[dict[str, str]] = []
    for field in CLAIM_REQUIRED_FIELDS:
        if _field_is_satisfied(case_extra, field):
            continue
        missing.append(
            {
                "field": field,
                "label": _SLOT_LABELS_ZH.get(field, field),
                "kind": "photo" if field.endswith("_photo") or "photo" in field else "text",
            }
        )
    return missing


def _has_photo_slot_activity(case_extra: dict[str, Any]) -> bool:
    for slot in CLAIM_PHOTO_FLOW_SLOTS:
        status = get_claim_attachment_slot_status(case_extra, slot)
        if status in ("received", "skipped", "needs_retake"):
            return True
    return False


def _has_other_party_activity(case_extra: dict[str, Any]) -> bool:
    if is_other_party_info_complete(case_extra):
        return True
    for slot in (*OTHER_PARTY_INFO_PHOTO_SLOTS, "other_party_vehicle_photo"):
        if get_claim_attachment_slot_status(case_extra, slot) != "empty":
            return True
    for key in OTHER_PARTY_INFO_SIGNALS:
        if _fact_value(case_extra, key):
            return True
    return False


def derive_claim_phase(case_extra: dict[str, Any]) -> str:
    """Derive customer/broker claim phase from hydrated case JSON (recon §8)."""
    explicit = str(case_extra.get("claim_phase") or "").strip().lower()

    if case_extra.get("broker_confirmed_at") or explicit == CLAIM_PHASE_BROKER_DONE:
        return CLAIM_PHASE_BROKER_DONE

    if explicit == CLAIM_PHASE_MANUAL_HANDLE or bool(case_extra.get("manual_handle")):
        return CLAIM_PHASE_MANUAL_HANDLE

    guided = str(case_extra.get("guided_workflow_state") or "").strip().lower()
    if guided == GUIDED_STATE_BROKER_NEEDS_MORE_INFO or explicit == CLAIM_PHASE_BROKER_NEEDS_MORE_INFO:
        return CLAIM_PHASE_BROKER_NEEDS_MORE_INFO

    if is_claim_summary_ready(case_extra):
        if guided == GUIDED_STATE_READY_FOR_BROKER_REVIEW or explicit == CLAIM_PHASE_BROKER_REVIEW:
            return CLAIM_PHASE_BROKER_REVIEW
        if explicit in (CLAIM_PHASE_SUMMARY_READY, CLAIM_PHASE_BROKER_REVIEW):
            return explicit
        return CLAIM_PHASE_SUMMARY_READY

    if not is_accident_basics_complete(case_extra):
        if explicit == CLAIM_PHASE_STARTED:
            return CLAIM_PHASE_STARTED
        return CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS

    if not are_claim_photos_complete(case_extra):
        if explicit == CLAIM_PHASE_PHOTOS_IN_PROGRESS or _has_photo_slot_activity(case_extra):
            return CLAIM_PHASE_PHOTOS_IN_PROGRESS
        return CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE

    if not is_other_party_info_complete(case_extra):
        if explicit == CLAIM_PHASE_OTHER_PARTY_IN_PROGRESS or _has_other_party_activity(case_extra):
            return CLAIM_PHASE_OTHER_PARTY_IN_PROGRESS
        return CLAIM_PHASE_PHOTOS_COMPLETE

    if not is_injury_police_complete(case_extra):
        if explicit == CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS:
            return CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS
        return CLAIM_PHASE_OTHER_PARTY_COMPLETE

    return CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS


def get_claim_progress_snapshot(case_extra: dict[str, Any]) -> dict[str, Any]:
    """Customer-facing progress summary for future Progress Card builder."""
    phase = derive_claim_phase(case_extra)
    missing = get_claim_missing_items(case_extra)
    collected = get_claim_collected_fields(case_extra)
    slots = get_claim_attachment_slots(case_extra)

    done_labels: list[str] = []
    current_labels: list[str] = []
    pending_labels: list[str] = []

    if is_accident_basics_complete(case_extra):
        done_labels.append("事故基本信息")
    elif phase in (CLAIM_PHASE_STARTED, CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS):
        current_labels.append("事故基本信息")
    else:
        pending_labels.append("事故基本信息")

    if are_claim_photos_complete(case_extra):
        done_labels.append("事故照片")
    elif phase in (
        CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        CLAIM_PHASE_PHOTOS_IN_PROGRESS,
    ):
        current_labels.append("事故照片")
    else:
        pending_labels.append("事故照片")

    if is_other_party_info_complete(case_extra):
        done_labels.append("对方信息")
    elif phase in (CLAIM_PHASE_PHOTOS_COMPLETE, CLAIM_PHASE_OTHER_PARTY_IN_PROGRESS):
        current_labels.append("对方信息")
    else:
        pending_labels.append("对方信息")

    if is_injury_police_complete(case_extra):
        done_labels.append("受伤 / 报警")
    elif phase in (CLAIM_PHASE_OTHER_PARTY_COMPLETE, CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS):
        current_labels.append("受伤 / 报警")
    else:
        pending_labels.append("受伤 / 报警")

    if phase in (CLAIM_PHASE_SUMMARY_READY, CLAIM_PHASE_BROKER_REVIEW):
        current_labels.append("陈总人工确认中")
    elif phase == CLAIM_PHASE_BROKER_DONE:
        done_labels.append("陈总已确认收到")

    required_done = sum(1 for f in CLAIM_REQUIRED_FIELDS if collected.get(f))
    optional_done = sum(1 for f in CLAIM_OPTIONAL_FIELDS if collected.get(f))
    injury_yes = is_injury_yes(_fact_value(case_extra, "anyone_injured"))

    return {
        "phase": phase,
        "done_labels": done_labels,
        "current_labels": current_labels,
        "pending_labels": pending_labels,
        "missing_items": missing,
        "attachment_slots": slots,
        "required_complete_count": required_done,
        "required_total_count": len(CLAIM_REQUIRED_FIELDS),
        "optional_complete_count": optional_done,
        "optional_total_count": len(CLAIM_OPTIONAL_FIELDS),
        "summary_ready": is_claim_summary_ready(case_extra),
        "broker_review": phase in (CLAIM_PHASE_SUMMARY_READY, CLAIM_PHASE_BROKER_REVIEW),
        "broker_done": phase == CLAIM_PHASE_BROKER_DONE,
        "manual_handle": phase == CLAIM_PHASE_MANUAL_HANDLE,
        "needs_broker_manual_handle": injury_yes or bool(case_extra.get("manual_handle")),
        "injury_yes": injury_yes,
    }


# --- Transition suggestion (no WeCom / I/O) ---


def _suggest_next_phase(case_extra: dict[str, Any]) -> str:
    if derive_claim_phase(case_extra) == CLAIM_PHASE_BROKER_DONE:
        return CLAIM_PHASE_BROKER_DONE
    if not is_accident_basics_complete(case_extra):
        return CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS
    if not are_claim_photos_complete(case_extra):
        return CLAIM_PHASE_PHOTOS_IN_PROGRESS
    if not is_other_party_info_complete(case_extra):
        return CLAIM_PHASE_OTHER_PARTY_IN_PROGRESS
    if not is_injury_police_complete(case_extra):
        return CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS
    if is_claim_summary_ready(case_extra):
        return CLAIM_PHASE_SUMMARY_READY
    return CLAIM_PHASE_INJURY_POLICE_IN_PROGRESS


def _suggest_customer_next_action(case_extra: dict[str, Any]) -> str:
    if derive_claim_phase(case_extra) == CLAIM_PHASE_BROKER_DONE:
        return CUSTOMER_ACTION_BROKER_DONE
    if not is_accident_basics_complete(case_extra):
        return CUSTOMER_ACTION_COLLECT_ACCIDENT_BASICS
    if not are_claim_photos_complete(case_extra):
        return CUSTOMER_ACTION_COLLECT_CLAIM_PHOTOS
    if not is_other_party_info_complete(case_extra):
        return CUSTOMER_ACTION_COLLECT_OTHER_PARTY_INFO
    if not is_injury_police_complete(case_extra):
        return CUSTOMER_ACTION_COLLECT_INJURY_POLICE
    return CUSTOMER_ACTION_AWAIT_BROKER_REVIEW


def suggest_next_claim_transition(
    case_extra: dict[str, Any],
    event_type: str | None = None,
) -> dict[str, Any]:
    """Pure transition suggestion for routing layers — does not emit WeCom replies."""
    _ = event_type  # reserved for future event-specific routing (P19H-2+)
    current = derive_claim_phase(case_extra)
    if not (case_extra.get("collected_fields") or case_extra.get("known_facts") or case_extra.get("case_attachments")):
        if str(case_extra.get("claim_phase") or "").strip().lower() == CLAIM_PHASE_STARTED:
            current = CLAIM_PHASE_STARTED

    missing = get_claim_missing_items(case_extra)
    injury_yes = is_injury_yes(_fact_value(case_extra, "anyone_injured"))
    needs_manual = injury_yes or bool(case_extra.get("manual_handle"))
    ready_for_broker = is_claim_summary_ready(case_extra)

    broker_note: str | None = None
    if needs_manual:
        broker_note = BROKER_NOTE_INJURY_YES_PHONE_FIRST

    return {
        "current_phase": current,
        "next_phase": _suggest_next_phase(case_extra),
        "ready_for_broker_review": ready_for_broker,
        "needs_broker_manual_handle": needs_manual,
        "missing_items": missing,
        "customer_next_action": _suggest_customer_next_action(case_extra),
        "broker_note": broker_note,
    }


# --- Safe transition helpers (return patches; no I/O) ---


def build_claim_phase_transition_patch(
    *,
    target_phase: str,
    guided_workflow_state: str | None = None,
    manual_handle: bool | None = None,
    urgent: bool | None = None,
) -> dict[str, Any]:
    """Return a merge-safe patch for claim workflow fields."""
    phase = (target_phase or "").strip().lower()
    if phase not in CLAIM_PHASES:
        raise ValueError(f"invalid claim phase: {target_phase}")
    patch: dict[str, Any] = {"claim_phase": phase}
    if guided_workflow_state is not None:
        patch["guided_workflow_state"] = guided_workflow_state.strip()
    if manual_handle is not None:
        patch["manual_handle"] = manual_handle
    if urgent is not None:
        patch["urgent"] = urgent
    return patch


def transition_after_accident_basics_complete(case_extra: dict[str, Any]) -> dict[str, Any] | None:
    if not is_accident_basics_complete(case_extra):
        return None
    return build_claim_phase_transition_patch(target_phase=CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE)


def transition_after_photos_complete(case_extra: dict[str, Any]) -> dict[str, Any] | None:
    if not are_claim_photos_complete(case_extra):
        return None
    return build_claim_phase_transition_patch(target_phase=CLAIM_PHASE_PHOTOS_COMPLETE)


def transition_after_other_party_complete(case_extra: dict[str, Any]) -> dict[str, Any] | None:
    if not is_other_party_info_complete(case_extra):
        return None
    return build_claim_phase_transition_patch(target_phase=CLAIM_PHASE_OTHER_PARTY_COMPLETE)


def transition_after_injury_police_complete(case_extra: dict[str, Any]) -> dict[str, Any] | None:
    if not is_injury_police_complete(case_extra):
        return None
    return build_claim_phase_transition_patch(target_phase=CLAIM_PHASE_INJURY_POLICE_COMPLETE)


def transition_to_claim_summary_ready(case_extra: dict[str, Any]) -> dict[str, Any] | None:
    if not is_claim_summary_ready(case_extra):
        return None
    return build_claim_phase_transition_patch(
        target_phase=CLAIM_PHASE_SUMMARY_READY,
        guided_workflow_state=GUIDED_STATE_READY_FOR_BROKER_REVIEW,
    )


def transition_to_broker_review(case_extra: dict[str, Any]) -> dict[str, Any] | None:
    if not is_claim_summary_ready(case_extra):
        return None
    return build_claim_phase_transition_patch(
        target_phase=CLAIM_PHASE_BROKER_REVIEW,
        guided_workflow_state=GUIDED_STATE_READY_FOR_BROKER_REVIEW,
    )


def transition_to_broker_needs_more_info(
    case_extra: dict[str, Any],
    *,
    resume_phase: str,
) -> dict[str, Any]:
    """Broker requests more info — resume a prior customer phase."""
    resume = (resume_phase or "").strip().lower()
    if resume not in CUSTOMER_CLAIM_PHASES:
        raise ValueError(f"invalid resume phase: {resume_phase}")
    return build_claim_phase_transition_patch(
        target_phase=resume,
        guided_workflow_state=GUIDED_STATE_BROKER_NEEDS_MORE_INFO,
    )


def transition_to_broker_done(case_extra: dict[str, Any]) -> dict[str, Any] | None:
    if not is_claim_summary_ready(case_extra):
        return None
    return build_claim_phase_transition_patch(target_phase=CLAIM_PHASE_BROKER_DONE)


def transition_to_manual_handle(case_extra: dict[str, Any]) -> dict[str, Any]:
    """Injury / sensitive path — skip normal checklist (recon §14.3)."""
    return build_claim_phase_transition_patch(
        target_phase=CLAIM_PHASE_MANUAL_HANDLE,
        guided_workflow_state=GUIDED_STATE_READY_FOR_BROKER_REVIEW,
        manual_handle=True,
        urgent=True,
    )


def validate_accident_description(text: str) -> tuple[str | None, str | None]:
    """Return (accepted_value, rejection_reason)."""
    cleaned = (text or "").strip()
    if not cleaned:
        return None, "empty"
    if len(cleaned) > CLAIM_MAX_DESCRIPTION_LENGTH:
        return None, "too_long"
    return cleaned, None


def is_injury_yes(value: str | None) -> bool:
    return (value or "").strip().lower() in INJURY_YES_VALUES


def is_police_yes(value: str | None) -> bool:
    return (value or "").strip().lower() in POLICE_YES_VALUES


def customer_copy_contains_forbidden_phrase(text: str) -> str | None:
    """Return matched forbidden phrase if any (ADR-003 guardrail)."""
    for phrase in CLAIM_FORBIDDEN_AUTOMATION_CLAIMS:
        if phrase in (text or ""):
            return phrase
    return None
