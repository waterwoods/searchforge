"""P19E-2 — Add Vehicle Progress Card (status / resume layer)."""

from __future__ import annotations

from typing import Any, Literal

from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.h5_task_link import (
    mask_h5_task_url,
    mint_h5_add_vehicle_photo_flow_link,
)
from services.fiqa_api.inbox_triage.h5_task_upload import (
    ADD_VEHICLE_PHOTO_FLOW_SLOTS,
    h5_photo_flow_is_complete,
    is_explicit_add_car_restart,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.add_vehicle_phase2 import (
    PHASE2_TEXT_FIELDS,
    _FIELD_LABELS_ZH,
    _field_display_value,
    phase2_text_is_complete,
    phase2_text_still_needed,
)
from services.fiqa_api.wecom.identity import (
    extract_delivery_date_from_text,
    extract_phone_from_text,
    extract_zip_from_text,
)
from services.fiqa_api.wecom.intent import IntentResult, is_add_vehicle_status_inquiry, is_vague_greeting_for_progress
from services.fiqa_api.wecom.reply import build_add_vehicle_progress_card

AddVehicleProgressPhase = Literal[
    "phase1_in_progress",
    "phase2_incomplete",
    "phase2_partial",
    "phase3_broker_review",
    "broker_done",
]

_H5_SLOT_LABELS: dict[str, str] = {
    "vin_photo": "VIN 照片",
    "registration_photo": "行驶证 / 登记证",
    "insurance_card_photo": "保险卡（可跳过）",
}

_FLOW_OPTIONAL_SLOTS = frozenset({"insurance_card_photo"})


def _completed_h5_slots(case: dict[str, Any]) -> set[str]:
    completed: set[str] = set()
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        if str(att.get("source") or "").strip().lower() != "h5_task":
            continue
        slot = str(att.get("slot_assignment") or "").strip().lower()
        if slot:
            completed.add(slot)
    return completed


def _skipped_h5_slots(case: dict[str, Any]) -> set[str]:
    state = case.get("h5_photo_flow_state") or {}
    if not isinstance(state, dict):
        return set()
    skipped = state.get("skipped_slots") or []
    return {str(s).strip().lower() for s in skipped if s}


def _case_sort_key(case: dict[str, Any]) -> str:
    return str(case.get("updated_at") or case.get("created_at") or "")


def find_open_add_car_cases_for_progress(external_userid: str) -> list[dict[str, Any]]:
    """Return open add_car cases for this WeCom user, newest ``updated_at`` first."""
    ext = (external_userid or "").strip()
    if not ext:
        return []
    matches: list[dict[str, Any]] = []
    for case in list_all_cases_for_read():
        if case.get("wecom_external_userid") != ext:
            continue
        if case.get("case_status") == "closed":
            continue
        lane = str(case.get("service_lane") or "").strip().lower()
        if lane not in ("add_car", SERVICE_LANE_ADD_CAR):
            continue
        matches.append(case)
    matches.sort(key=_case_sort_key, reverse=True)
    return matches


def find_active_add_car_case_for_progress(
    external_userid: str,
) -> tuple[dict[str, Any] | None, int]:
    """Return newest open add_car case and total open count for this user."""
    cases = find_open_add_car_cases_for_progress(external_userid)
    if not cases:
        return None, 0
    return cases[0], len(cases)


def derive_add_vehicle_progress(case: dict[str, Any]) -> dict[str, Any]:
    """Derive customer-facing add-vehicle phase from existing case state."""
    status = str(case.get("case_status") or "").strip().lower()
    if status in ("closed", "confirmed") or case.get("broker_confirmed_at"):
        return {"phase": "broker_done"}

    guided = str(case.get("guided_workflow_state") or "").strip().lower()
    add_phase = str(case.get("add_vehicle_phase") or "").strip().lower()
    if (
        phase2_text_is_complete(case)
        or guided == "ready_for_broker_review"
        or add_phase == "phase_3_broker_review"
    ):
        return {"phase": "phase3_broker_review"}

    if not h5_photo_flow_is_complete(case):
        completed = _completed_h5_slots(case)
        skipped = _skipped_h5_slots(case)
        missing: list[str] = []
        received: list[str] = []
        for slot in ADD_VEHICLE_PHOTO_FLOW_SLOTS:
            label = _H5_SLOT_LABELS.get(slot, slot)
            if slot in completed:
                received.append(label)
            elif slot in _FLOW_OPTIONAL_SLOTS and slot in skipped:
                received.append(f"{label} — 已跳过")
            else:
                missing.append(label)
        return {
            "phase": "phase1_in_progress",
            "missing_photo_labels": missing,
            "received_photo_labels": received,
        }

    collected_names = {str(x).lower() for x in (case.get("collected_fields") or [])}
    still = phase2_text_still_needed(case)
    collected_display = [
        {"field": field, "label": _FIELD_LABELS_ZH[field], "value": _field_display_value(case, field)}
        for field in PHASE2_TEXT_FIELDS
        if field in collected_names
    ]
    missing_fields = [_FIELD_LABELS_ZH[f] for f in still]
    phase: AddVehicleProgressPhase = "phase2_partial" if collected_display else "phase2_incomplete"
    return {
        "phase": phase,
        "collected_fields": collected_display,
        "missing_field_labels": missing_fields,
    }


def message_has_phase2_extractable_fields(text: str, normalized: dict[str, Any]) -> bool:
    """True when free text likely carries Phase 2 delivery_date / zip / phone."""
    return any(
        [
            extract_delivery_date_from_text(text),
            extract_zip_from_text(text),
            normalized.get("phone") or extract_phone_from_text(text),
        ]
    )


def should_route_add_vehicle_progress(
    normalized: dict[str, Any],
    intent_result: IntentResult,
    *,
    guided_menu: bool,
) -> bool:
    """Route to Progress Card instead of generic greeting or duplicate H5 Start."""
    text = str(normalized.get("text") or "").strip()
    if is_explicit_add_car_restart(text):
        return False
    if intent_result.confidence == "high" and intent_result.intent in {
        "policy_review",
        "claim_intake",
        "coverage_risk_intake",
    }:
        return False
    if message_has_phase2_extractable_fields(text, normalized):
        return False

    case, _count = find_active_add_car_case_for_progress(str(normalized.get("external_userid") or ""))
    if case is None:
        return False

    if is_add_vehicle_status_inquiry(text):
        return True
    if guided_menu and is_vague_greeting_for_progress(text):
        return True
    if intent_result.confidence == "high" and intent_result.intent == "add_car":
        return True
    return False


def build_add_vehicle_progress_reply(
    case: dict[str, Any],
    *,
    external_userid: str | None,
    open_case_count: int,
) -> tuple[str | None, dict[str, Any] | None, str | None]:
    """Build Progress Card text/menu and masked H5 URL when Phase 1 resume applies."""
    progress = derive_add_vehicle_progress(case)
    h5_url: str | None = None
    if progress.get("phase") == "phase1_in_progress":
        cid = str(case.get("case_id") or "").strip()
        if cid:
            try:
                h5_url = mint_h5_add_vehicle_photo_flow_link(
                    case_id=cid,
                    external_userid=(external_userid or "").strip() or None,
                )
            except ValueError:
                h5_url = None
    text_content, menu_payload = build_add_vehicle_progress_card(
        case,
        progress=progress,
        h5_url=h5_url,
        multiple_open_cases=open_case_count > 1,
    )
    masked = mask_h5_task_url(h5_url) if h5_url else None
    return text_content, menu_payload, masked
