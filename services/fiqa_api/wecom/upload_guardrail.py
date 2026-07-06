"""Strict WeCom upload guardrail (P19D-1) — promote vs quarantine, no OCR."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_CLAIM_LITE

BULK_WINDOW_SECONDS = 120
BULK_MISTAKE_THRESHOLD = 3
DEFAULT_SLOT_MAX = 1
CLAIM_BATCH_MAX = 5

WIDENED_SLOT_MAX: dict[str, int] = {
    "registration": 2,
    "insurance_card": 2,
    "dmv_notice": 3,
}

GuardrailAction = Literal["promote", "quarantine"]
GuardrailStatus = Literal[
    "accepted",
    "bulk_confirm_needed",
    "bulk_upload_paused",
    "claim_batch_confirm_needed",
]


@dataclass(frozen=True)
class GuardrailDecision:
    action: GuardrailAction
    guardrail_status: GuardrailStatus
    reply_kind: str
    metadata: dict[str, Any]


def slot_max_for(slot_assignment: str | None) -> int:
    key = (slot_assignment or "unknown_document").strip().lower()
    return WIDENED_SLOT_MAX.get(key, DEFAULT_SLOT_MAX)


def _parse_att_received_at(att: dict[str, Any]) -> datetime | None:
    raw = att.get("received_at") or att.get("created_at")
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str) and raw.strip():
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _is_promoted_att(att: dict[str, Any]) -> bool:
    status = (att.get("intake_status") or "").strip().lower()
    if status == "quarantined":
        return False
    if status in ("promoted", "unassigned"):
        return status == "promoted"
    # Legacy attachments without guardrail fields count as promoted.
    return status != "quarantined"


def list_recent_wecom_attachments(
    external_userid: str,
    *,
    received_at: datetime,
    window_seconds: int = BULK_WINDOW_SECONDS,
) -> list[tuple[str, dict[str, Any]]]:
    """Return (case_id, attachment) for same user within rolling window, oldest first."""
    ext = (external_userid or "").strip()
    if not ext:
        return []
    window_start = received_at - timedelta(seconds=window_seconds)
    found: list[tuple[datetime, str, dict[str, Any]]] = []
    for case in list_all_cases_for_read():
        cid = str(case.get("case_id") or "").strip()
        if not cid:
            continue
        for att in case.get("case_attachments") or []:
            if not isinstance(att, dict):
                continue
            if att.get("source") != "wecom":
                continue
            if (att.get("external_userid") or "").strip() != ext:
                continue
            ts = _parse_att_received_at(att)
            if ts is None or ts < window_start or ts > received_at:
                continue
            found.append((ts, cid, att))
    found.sort(key=lambda row: row[0])
    return [(cid, att) for _, cid, att in found]


def _count_promoted_in_window(
    recent: list[tuple[str, dict[str, Any]]],
    *,
    case_id: str | None = None,
) -> int:
    count = 0
    for cid, att in recent:
        if case_id is not None and cid != case_id:
            continue
        if _is_promoted_att(att):
            count += 1
    return count


def _bulk_group_id_for_window(
    recent: list[tuple[str, dict[str, Any]]],
    *,
    external_userid: str,
    received_at: datetime,
) -> str:
    for _, att in recent:
        gid = (att.get("bulk_group_id") or "").strip()
        if gid:
            return gid
    suffix = (external_userid or "user")[-8:] or "user"
    return f"bulk_{int(received_at.timestamp())}_{suffix}"


def _quarantine_reason(
    *,
    batch_position: int,
    service_lane: str | None,
    promoted_in_window: int,
    slot_max: int,
) -> str:
    lane = (service_lane or "").strip()
    if lane == SERVICE_LANE_CLAIM_LITE and promoted_in_window >= CLAIM_BATCH_MAX:
        return "claim_batch_over_limit"
    if batch_position > BULK_MISTAKE_THRESHOLD:
        return "bulk_upload_over_limit"
    if promoted_in_window >= slot_max:
        return "slot_primary_limit_exceeded"
    return "bulk_upload_confirm_needed"


def evaluate_upload_guardrail(
    *,
    external_userid: str,
    received_at: datetime,
    service_lane: str | None,
    case_id: str | None,
    slot_assignment: str = "unknown_document",
) -> GuardrailDecision:
    """
    Classify incoming WeCom media as promote or quarantine.
    Deterministic; uses existing case attachment metadata only (no schema migration).
    """
    recent = list_recent_wecom_attachments(
        external_userid,
        received_at=received_at,
        window_seconds=BULK_WINDOW_SECONDS,
    )
    batch_position = len(recent) + 1
    slot_max = slot_max_for(slot_assignment)
    promoted_in_window = _count_promoted_in_window(recent)
    promoted_in_case = _count_promoted_in_window(recent, case_id=case_id) if case_id else promoted_in_window
    bulk_group_id = _bulk_group_id_for_window(recent, external_userid=external_userid, received_at=received_at)
    lane = (service_lane or "").strip()

    action: GuardrailAction = "promote"
    guardrail_status: GuardrailStatus = "accepted"
    reply_kind = "single_image"

    if lane == SERVICE_LANE_CLAIM_LITE:
        if promoted_in_case < CLAIM_BATCH_MAX:
            action = "promote"
            guardrail_status = "accepted" if batch_position == 1 else "claim_batch_confirm_needed"
            reply_kind = "claim_single" if batch_position == 1 else "claim_batch"
        else:
            action = "quarantine"
            guardrail_status = "claim_batch_confirm_needed"
            reply_kind = "claim_batch"
    elif batch_position > BULK_MISTAKE_THRESHOLD:
        if batch_position == 1:
            action = "promote"
            guardrail_status = "accepted"
            reply_kind = "single_image"
        else:
            action = "quarantine"
            guardrail_status = "bulk_upload_paused"
            reply_kind = "bulk_pause"
    elif batch_position == 1:
        action = "promote"
        guardrail_status = "accepted"
        reply_kind = "single_image"
    elif batch_position <= BULK_MISTAKE_THRESHOLD:
        if promoted_in_window < slot_max:
            action = "promote"
            guardrail_status = "bulk_confirm_needed" if batch_position > 1 else "accepted"
            reply_kind = "bulk_confirm" if batch_position > 1 else "single_image"
        else:
            action = "quarantine"
            guardrail_status = "bulk_confirm_needed"
            reply_kind = "bulk_confirm"
    else:
        action = "quarantine"
        guardrail_status = "bulk_upload_paused"
        reply_kind = "bulk_pause"

    requires_confirm = guardrail_status in (
        "bulk_confirm_needed",
        "bulk_upload_paused",
        "claim_batch_confirm_needed",
    )
    eligible_for_ocr = action == "promote"
    intake_status = "promoted" if action == "promote" else "quarantined"
    quarantine_reason = (
        None
        if action == "promote"
        else _quarantine_reason(
            batch_position=batch_position,
            service_lane=service_lane,
            promoted_in_window=promoted_in_window,
            slot_max=slot_max,
        )
    )

    metadata: dict[str, Any] = {
        "intake_status": intake_status,
        "guardrail_status": guardrail_status,
        "slot_assignment": slot_assignment if action == "promote" else None,
        "slot_max": slot_max,
        "bulk_group_id": bulk_group_id if batch_position > 1 or action == "quarantine" else None,
        "bulk_sequence": batch_position,
        "bulk_window_seconds": BULK_WINDOW_SECONDS,
        "requires_customer_confirm": requires_confirm,
        "eligible_for_ocr": eligible_for_ocr,
        "quarantine_reason": quarantine_reason,
    }
    return GuardrailDecision(
        action=action,
        guardrail_status=guardrail_status,
        reply_kind=reply_kind,
        metadata=metadata,
    )


def apply_guardrail_to_attachment_metadata(
    attachment_meta: dict[str, Any],
    decision: GuardrailDecision,
) -> dict[str, Any]:
    """Merge guardrail fields into attachment metadata (additive JSON only)."""
    out = dict(attachment_meta)
    out.update(decision.metadata)
    if out.get("intake_status") == "promoted" and not out.get("slot_assignment"):
        out["slot_assignment"] = "unknown_document"
    return out


def new_bulk_group_id() -> str:
    return f"bulk_{uuid4().hex[:12]}"
