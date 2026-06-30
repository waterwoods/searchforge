"""
P17 Phase 1 — Active Case resolver (deterministic merge rules).

ADR-005 north star; Phase 1 implements add-car extract consolidation only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from services.fiqa_api.inbox_triage.active_case_lookup import find_active_add_car_case_by_phone
from services.fiqa_api.inbox_triage.case_binding import is_case_open_for_binding
from services.fiqa_api.inbox_triage.phone_normalization import normalize_phone_digits

_ADD_CAR_INTENTS = frozenset({"add_vehicle", "add_car", "replace_vehicle"})
_POLICY_REVIEW_INTENTS = frozenset({"policy_review"})


class ResolverOutcome(str, Enum):
    ATTACH = "attach"
    CREATE = "create"
    BROKER_REVIEW = "broker_review"


@dataclass(frozen=True)
class ResolverDecision:
    outcome: ResolverOutcome
    case_id: str | None = None
    conflict_reason: str | None = None
    candidate_count: int = 0


def _intent_lane(intent: str) -> str:
    raw = (intent or "").strip().lower()
    if raw in _ADD_CAR_INTENTS:
        return "add_car"
    if raw in _POLICY_REVIEW_INTENTS:
        return "policy_review"
    return raw


def _case_lane(case: dict[str, Any]) -> str:
    lane = str(case.get("service_lane") or "").strip().lower()
    if lane:
        return lane
    svc = str(case.get("service_type") or "").strip().lower()
    if svc == "add_car" or ("add" in svc and "car" in svc):
        return "add_car"
    if svc == "policy_review":
        return "policy_review"
    cat = str(case.get("issue_category") or "").strip().lower()
    if cat in ("add_car_quote", "add_vehicle", "new_vehicle", "replace_vehicle_quote"):
        return "add_car"
    if "policy" in cat and "review" in cat:
        return "policy_review"
    return lane or svc or cat


def _norm_vin(vin: str | None) -> str:
    v = (vin or "").strip().upper()
    return v if len(v) == 17 else ""


def _vin_conflict(case_vin: str | None, new_vin: str | None) -> bool:
    existing = _norm_vin(case_vin)
    incoming = _norm_vin(new_vin)
    if not existing or not incoming:
        return False
    return existing != incoming


def _case_phone_digits(case: dict[str, Any]) -> str:
    return normalize_phone_digits(str(case.get("customer_phone") or ""))


def find_open_cases_for_intent(
    phone: str,
    intent: str,
    cases: list[dict[str, Any]],
    *,
    client_id: str | None = None,
) -> list[dict[str, Any]]:
    """Open cases for same normalized phone and intent lane (deterministic, no fuzzy match)."""
    target_phone = normalize_phone_digits(phone)
    if len(target_phone) != 10:
        return []
    lane = _intent_lane(intent)
    matches: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        if not is_case_open_for_binding(case):
            continue
        if _case_lane(case) != lane:
            continue
        cid = str(case.get("client_id") or "").strip()
        if client_id and cid and cid != client_id.strip():
            continue
        if _case_phone_digits(case) != target_phone:
            continue
        matches.append(case)
    matches.sort(
        key=lambda c: (str(c.get("updated_at") or ""), str(c.get("created_at") or "")),
        reverse=True,
    )
    return matches


def resolve_active_case_for_evidence(
    *,
    phone: str,
    intent: str,
    new_vin: str | None,
    cases: list[dict[str, Any]],
    client_id: str | None = None,
) -> ResolverDecision:
    """
    Pure deterministic resolver — same phone, same intent, open case, VIN conflict check.

    0 candidates → CREATE
    1 candidate, no VIN conflict → ATTACH
    1 candidate, VIN conflict → BROKER_REVIEW
    2+ candidates → BROKER_REVIEW
    """
    candidates = find_open_cases_for_intent(phone, intent, cases, client_id=client_id)
    count = len(candidates)

    if count == 0:
        return ResolverDecision(outcome=ResolverOutcome.CREATE, candidate_count=0)

    if count >= 2:
        newest = candidates[0]
        return ResolverDecision(
            outcome=ResolverOutcome.BROKER_REVIEW,
            case_id=str(newest.get("case_id") or "").strip() or None,
            conflict_reason="multiple_open_cases",
            candidate_count=count,
        )

    case = candidates[0]
    case_id = str(case.get("case_id") or "").strip() or None
    case_vin = str(case.get("vehicle_key") or "").strip() or None
    if not case_vin:
        blob = case.get("p16_broker_packet")
        if isinstance(blob, dict):
            pkt = blob.get("packet")
            if isinstance(pkt, dict):
                vin_field = pkt.get("vin")
                if isinstance(vin_field, dict):
                    case_vin = str(vin_field.get("value") or "").strip() or None

    if _vin_conflict(case_vin, new_vin):
        return ResolverDecision(
            outcome=ResolverOutcome.BROKER_REVIEW,
            case_id=case_id,
            conflict_reason="vin_conflict",
            candidate_count=1,
        )

    return ResolverDecision(
        outcome=ResolverOutcome.ATTACH,
        case_id=case_id,
        candidate_count=1,
    )


def find_active_add_car_case_for_phone(
    phone: str,
    cases: list[dict[str, Any]],
    *,
    client_id: str | None = None,
) -> dict[str, Any] | None:
    """Phone return-key lookup — delegates to existing helper (Rule 2 + Rule 7)."""
    return find_active_add_car_case_by_phone(phone, cases, client_id=client_id)
