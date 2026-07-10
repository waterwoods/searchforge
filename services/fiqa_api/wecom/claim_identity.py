"""P19H-3c-R3 — Lightweight Claim identity resolution (pure helpers)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
)

RECENT_OPEN_CLAIM_WINDOW_HOURS = 72

EXPLICIT_NEW_ACCIDENT_MARKERS: tuple[str, ...] = (
    "新事故",
    "另一次事故",
    "另一个事故",
    "另一个理赔",
    "这是另一个事故",
    "不是刚才那个事故",
    "不是刚才那个",
    "又发生了一次新的事故",
    "又发生一个事故",
    "重新理赔",
    "重新开一个理赔",
    "重新开一个",
    "新的事故",
    "不是上次那个",
    "不是同一个事故",
    "今天又撞了",
    "new accident",
    "another accident",
    "separate accident",
    "different accident",
    "not the same accident",
    "start a new claim",
)

EXPLICIT_CONTINUATION_MARKERS: tuple[str, ...] = (
    "继续刚才那个",
    "还是同一个事故",
    "同一个事故",
    "补充一下",
    "再发一张照片",
    "继续上一个事故",
    "继续补资料",
    "还是上次那个",
)

RULE_ID_EXPLICIT_NEW_ACCIDENT = "ID-A1"
RULE_ID_NO_OPEN_CLAIM = "ID-A2"
RULE_ID_SINGLE_RECENT_OPEN = "ID-A3"
RULE_ID_OLD_OPEN_CLAIM = "ID-A4"
RULE_ID_MULTIPLE_OPEN = "ID-A5"
RULE_ID_EXPLICIT_CONTINUATION = "ID-A6"
RULE_ID_COLLISION_RESOLVER = "ID-A7"
RULE_ID_ACTIVE_APPEND_MULTI = "ID-A8"


@dataclass(frozen=True)
class ClaimIdentityCandidate:
    case_id: str
    service_lane: str
    workflow_phase: str | None
    created_at: str | None
    updated_at: str | None
    accident_datetime: str | None = None
    accident_location: str | None = None
    is_closed: bool = False
    broker_done: bool = False
    broker_confirmed_at: str | None = None


@dataclass(frozen=True)
class ClaimIdentityDecision:
    tier: Literal["A", "B", "C"]
    action: Literal["append_existing", "create_new", "broker_confirm"]
    case_id: str | None
    score: int
    rule_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    candidate_case_ids: list[str] = field(default_factory=list)


def is_explicit_new_accident(text: str | None) -> bool:
    lowered = (text or "").strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in EXPLICIT_NEW_ACCIDENT_MARKERS)


def is_explicit_continuation(text: str | None) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    return any(m in raw or m in lowered for m in EXPLICIT_CONTINUATION_MARKERS)


def _claim_has_accident_story(case: dict[str, Any]) -> bool:
    from services.fiqa_api.wecom.claim_extractors import has_accident_basics_signals

    facts = case.get("known_facts") or {}
    if not isinstance(facts, dict):
        facts = {}
    if str(facts.get("accident_datetime") or "").strip() or str(facts.get("accident_location") or "").strip():
        return True
    timeline = case.get("claim_timeline") or []
    if not isinstance(timeline, list):
        return False
    for entry in timeline:
        if not isinstance(entry, dict) or entry.get("event_type") != "customer_text":
            continue
        text = str(entry.get("text") or "").strip()
        if has_accident_basics_signals(text):
            return True
    return False


def is_collision_triggering_input(text: str | None) -> bool:
    """Strong explicit new-accident signal only (P19H-3h append-first, split-later).

    Ordinary accident words, time+location, photos, and supplements append to the
    active Claim timeline. Passive markers must not interrupt the customer.
    """
    return is_explicit_new_accident(text)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _case_recency_datetime(case: dict[str, Any]) -> datetime | None:
    return _parse_iso_datetime(str(case.get("updated_at") or case.get("created_at") or ""))


def _sort_open_claims_newest_first(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        cases,
        key=lambda case: str(case.get("updated_at") or case.get("created_at") or ""),
        reverse=True,
    )


def newest_open_claim_id(open_claims: list[dict[str, Any]]) -> str | None:
    sorted_cases = _sort_open_claims_newest_first(open_claims)
    if not sorted_cases:
        return None
    return str(sorted_cases[0].get("case_id") or "").strip() or None


def is_closed_or_terminal_claim(case: dict[str, Any]) -> bool:
    if case.get("case_status") == "closed":
        return True
    if case.get("broker_confirmed_at"):
        return True
    if derive_claim_phase(case) == CLAIM_PHASE_BROKER_DONE:
        return True
    return False


def case_to_identity_candidate(case: dict[str, Any]) -> ClaimIdentityCandidate:
    facts = case.get("known_facts") or {}
    if not isinstance(facts, dict):
        facts = {}
    broker_done = derive_claim_phase(case) == CLAIM_PHASE_BROKER_DONE
    return ClaimIdentityCandidate(
        case_id=str(case.get("case_id") or "").strip(),
        service_lane=str(case.get("service_lane") or "").strip().lower(),
        workflow_phase=derive_claim_phase(case),
        created_at=str(case.get("created_at") or "").strip() or None,
        updated_at=str(case.get("updated_at") or "").strip() or None,
        accident_datetime=str(facts.get("accident_datetime") or "").strip() or None,
        accident_location=str(facts.get("accident_location") or "").strip() or None,
        is_closed=case.get("case_status") == "closed",
        broker_done=broker_done,
        broker_confirmed_at=str(case.get("broker_confirmed_at") or "").strip() or None,
    )


def is_open_claim_candidate_for_basics(case: dict[str, Any], external_userid: str) -> bool:
    ext = (external_userid or "").strip()
    if not ext or case.get("wecom_external_userid") != ext:
        return False
    if str(case.get("service_lane") or "").strip().lower() != SERVICE_LANE_CLAIM:
        return False
    return not is_closed_or_terminal_claim(case)


def resolve_claim_identity(
    *,
    external_userid: str,
    incoming_text: str | None,
    open_claims: list[dict[str, Any]],
    now: datetime | None = None,
    channel: str = "wecom_text",
) -> ClaimIdentityDecision:
    """Resolve whether inbound Claim traffic should append, create, or ask broker."""
    _ = channel  # reserved for future channel-specific rules
    ext = (external_userid or "").strip()
    if not ext:
        return ClaimIdentityDecision(
            tier="C",
            action="create_new",
            case_id=None,
            score=0,
            rule_ids=[RULE_ID_NO_OPEN_CLAIM],
            reasons=["no_external_userid"],
        )

    active_cases = _sort_open_claims_newest_first(
        [
            case
            for case in open_claims
            if is_open_claim_candidate_for_basics(case, ext)
        ]
    )
    candidate_ids = [
        str(case.get("case_id") or "").strip()
        for case in active_cases
        if str(case.get("case_id") or "").strip()
    ]
    newest_case_id = candidate_ids[0] if candidate_ids else None

    if not active_cases:
        return ClaimIdentityDecision(
            tier="C",
            action="create_new",
            case_id=None,
            score=0,
            rule_ids=[RULE_ID_NO_OPEN_CLAIM],
            reasons=["no_open_claim"],
        )

    if len(active_cases) == 1 and is_explicit_continuation(incoming_text):
        only_case_id = candidate_ids[0] if candidate_ids else None
        return ClaimIdentityDecision(
            tier="A",
            action="append_existing",
            case_id=only_case_id,
            score=95,
            rule_ids=[RULE_ID_EXPLICIT_CONTINUATION],
            reasons=["customer_explicit_continuation"],
            candidate_case_ids=[only_case_id] if only_case_id else [],
        )

    if is_explicit_new_accident(incoming_text):
        return ClaimIdentityDecision(
            tier="B",
            action="broker_confirm",
            case_id=newest_case_id,
            score=80,
            rule_ids=[RULE_ID_EXPLICIT_NEW_ACCIDENT, RULE_ID_COLLISION_RESOLVER],
            reasons=["customer_said_new_accident"],
            candidate_case_ids=candidate_ids,
        )

    if len(active_cases) >= 2:
        return ClaimIdentityDecision(
            tier="A",
            action="append_existing",
            case_id=newest_case_id,
            score=88,
            rule_ids=[RULE_ID_ACTIVE_APPEND_MULTI],
            reasons=["multiple_open_claims", "active_append_newest"],
            candidate_case_ids=candidate_ids,
        )

    only_case = active_cases[0]
    only_case_id = str(only_case.get("case_id") or "").strip() or None
    recency = _case_recency_datetime(only_case)
    reference_now = now or datetime.now(timezone.utc)
    recent_cutoff = reference_now - timedelta(hours=RECENT_OPEN_CLAIM_WINDOW_HOURS)

    if recency and recency >= recent_cutoff:
        reason = "single_recent_open_claim"
    else:
        reason = "old_open_claim_append_first"

    return ClaimIdentityDecision(
        tier="A",
        action="append_existing",
        case_id=only_case_id,
        score=90 if recency and recency >= recent_cutoff else 85,
        rule_ids=[RULE_ID_SINGLE_RECENT_OPEN if reason == "single_recent_open_claim" else RULE_ID_OLD_OPEN_CLAIM],
        reasons=[reason],
        candidate_case_ids=[only_case_id] if only_case_id else [],
    )
