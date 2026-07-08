"""P19H-3c-3C — Claim evidence slot JSONB mutation helpers (no schema migration)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

OTHER_PARTY_SKIP_REASONS: tuple[dict[str, str], ...] = (
    {"key": "no_other_party", "label": "没有对方车辆 / 单方事故"},
    {"key": "not_available", "label": "当时无法拍摄"},
    {"key": "hit_and_run", "label": "对方逃逸"},
    {"key": "customer_not_safe_to_collect", "label": "当时不安全未能拍摄"},
)

SCENE_SKIP_REASONS: tuple[dict[str, str], ...] = (
    {"key": "not_available", "label": "当时无法拍摄"},
    {"key": "not_needed", "label": "不需要现场照片"},
    {"key": "customer_not_safe_to_collect", "label": "当时不安全未能拍摄"},
)

_OTHER_PARTY_SKIP_REASON_KEYS: frozenset[str] = frozenset(
    reason["key"] for reason in OTHER_PARTY_SKIP_REASONS
)
_SCENE_SKIP_REASON_KEYS: frozenset[str] = frozenset(reason["key"] for reason in SCENE_SKIP_REASONS)

_CLAIM_SKIPPABLE_SLOTS: frozenset[str] = frozenset(
    {"other_party_vehicle_photo", "scene_photo"}
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def allowed_skip_reasons_for_slot(slot_key: str) -> frozenset[str]:
    slot_norm = (slot_key or "").strip().lower()
    if slot_norm == "other_party_vehicle_photo":
        return _OTHER_PARTY_SKIP_REASON_KEYS
    if slot_norm == "scene_photo":
        return _SCENE_SKIP_REASON_KEYS
    return frozenset()


def normalize_claim_slot_skip_reason(
    slot_key: str,
    skip_reason: str | None,
    *,
    default: str = "not_available",
) -> str:
    """Validate and normalize skip reason for a claim evidence slot."""
    slot_norm = (slot_key or "").strip().lower()
    if slot_norm not in _CLAIM_SKIPPABLE_SLOTS:
        raise ValueError("slot_not_skippable")
    reason = (skip_reason or default).strip()
    if not reason:
        reason = default
    allowed = allowed_skip_reasons_for_slot(slot_norm)
    if reason not in allowed:
        raise ValueError("invalid_skip_reason")
    return reason


def patch_claim_slot_received(
    case: dict[str, Any],
    slot_key: str,
    attachment_id: str,
    *,
    source_channel: str = "h5_task",
    updated_at: str | None = None,
) -> dict[str, Any]:
    """Update claim_attachment_slots[slot] to received; clears skip / retake flags."""
    slot_norm = (slot_key or "").strip().lower()
    if not slot_norm:
        raise ValueError("slot_required")

    slots = dict(case.get("claim_attachment_slots") or {})
    prev = dict(slots.get(slot_norm) or {})
    attachment_ids = list(prev.get("attachment_ids") or [])
    att_id = (attachment_id or "").strip()
    if att_id and att_id not in attachment_ids:
        attachment_ids.append(att_id)

    ts = updated_at or _utc_now_iso()
    slots[slot_norm] = {
        "status": "received",
        "source_channel": source_channel,
        "attachment_ids": attachment_ids,
        "latest_attachment_id": att_id or None,
        "updated_at": ts,
    }
    case["claim_attachment_slots"] = slots
    return case


def patch_claim_slot_skipped(
    case: dict[str, Any],
    slot_key: str,
    skip_reason: str,
    *,
    source_channel: str = "h5_task",
    updated_at: str | None = None,
) -> dict[str, Any]:
    """Update claim_attachment_slots[slot] to skipped with reason."""
    slot_norm = (slot_key or "").strip().lower()
    reason = normalize_claim_slot_skip_reason(slot_norm, skip_reason)
    ts = updated_at or _utc_now_iso()
    slots = dict(case.get("claim_attachment_slots") or {})
    slots[slot_norm] = {
        "status": "skipped",
        "skip_reason": reason,
        "source_channel": source_channel,
        "updated_at": ts,
    }
    case["claim_attachment_slots"] = slots
    return case
