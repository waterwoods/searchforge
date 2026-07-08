"""P19H-3a — Claim case workbench display enrichment (no schema migration)."""

from __future__ import annotations

from typing import Any

from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_BROKER_REVIEW,
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    CLAIM_PHASE_MANUAL_HANDLE,
    CLAIM_PHASE_SUMMARY_READY,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
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
    row["workbench_visible"] = is_claim_workbench_visible(case)
    return row
