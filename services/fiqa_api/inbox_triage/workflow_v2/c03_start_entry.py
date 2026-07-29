"""Workflow V2 — C03 Smart Claim Start entry (journey owner).

Call pattern (Capability Constitution):
  Workflow needs "how should Start Claim feel?"
    → calls Customer Lookup (C01) for LookupResult
    → calls Claim Prefill (C02) for PrefillResult
    → calls Smart Claim Start (C03) for SmartClaimStartPlan
    → branches on stable plan fields (mode / CTAs / confirms)
    → never imports Cap 03 engine internals beyond capability facade
    → never imports AMS / CRM / adapters

Scope: C03 presentation plan only. Does not implement AMS, Notification, Timeline.
Does not redesign C01 or C02.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.fiqa_api.inbox_triage.claim_prefill.contract import PrefillResult
from services.fiqa_api.inbox_triage.claim_prefill.facade import prefill_from_lookup
from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult
from services.fiqa_api.inbox_triage.customer_lookup.facade import lookup_customer
from services.fiqa_api.inbox_triage.smart_claim_start.contract import SmartClaimStartPlan
from services.fiqa_api.inbox_triage.smart_claim_start.engine import (
    build_smart_claim_start_plan,
)
from services.fiqa_api.inbox_triage.workflow_v2.c01_lookup_entry import (
    decide_lookup_entry,
)
from services.fiqa_api.inbox_triage.workflow_v2.c02_prefill_entry import (
    decide_prefill_entry,
)


@dataclass(frozen=True)
class StartEntryDecision:
    """Workflow decision derived only from SmartClaimStartPlan (+ prior journey)."""

    plan_mode: str
    headline_zh: str
    primary_cta_zh: str
    secondary_cta_zh: str
    known_chip_count: int
    required_confirm_count: int
    soft_notice_count: int
    estimated_customer_inputs: int
    # Customer Trust invariants
    has_blank_escape: bool
    never_blocks_accident: bool
    no_quiz_on_unambiguous: bool
    lands_on_story: bool
    owns_start_claim_screens: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decide_start_entry(plan: SmartClaimStartPlan) -> StartEntryDecision:
    """
    Pure Workflow policy: SmartClaimStartPlan → presentation summary.

    Does not invent matching rules. Does not call AMS.
    """
    mode = str(plan.get("mode") or "")
    confirms = list(plan.get("confirm_steps") or [])
    required = sum(1 for s in confirms if s.get("required_before_accident"))
    soft = sum(1 for s in confirms if not s.get("required_before_accident"))
    screens = [str(s.get("screen_id") or "") for s in (plan.get("screens") or [])]
    secondary = str(plan.get("secondary_cta_zh") or "")
    headline = str(plan.get("headline_zh") or "")

    has_blank_escape = mode == "CONTACT_BROKER" and (
        "仍要先报案" in secondary or "blank_claim_escape" in screens
    )
    # Stale / blank / matched story paths must not imply claim blocked.
    never_blocks = mode != "CONTINUE_ACTIVE"  # continue gate is intentional
    if mode == "MATCHED_CONFIRM_POLICY":
        never_blocks = required == 0
    if mode == "CONTACT_BROKER":
        never_blocks = has_blank_escape

    no_quiz = True
    if mode == "MATCHED_KNOWN":
        no_quiz = "known_context" not in screens and required == 0
        no_quiz = no_quiz and "confirm_vehicle" not in screens

    lands_on_story = (
        "今天发生了什么" in headline
        or "accident_facts" in screens
        or "blank_claim_escape" in screens
    )

    return StartEntryDecision(
        plan_mode=mode,
        headline_zh=headline,
        primary_cta_zh=str(plan.get("primary_cta_zh") or ""),
        secondary_cta_zh=secondary,
        known_chip_count=len(plan.get("known_chips") or []),
        required_confirm_count=required,
        soft_notice_count=soft,
        estimated_customer_inputs=int(plan.get("estimated_customer_inputs") or 0),
        has_blank_escape=has_blank_escape,
        never_blocks_accident=never_blocks,
        no_quiz_on_unambiguous=no_quiz,
        lands_on_story=lands_on_story,
        owns_start_claim_screens=True,
    )


def enter_claim_with_smart_start(
    person_link_key: str | None,
) -> tuple[LookupResult, PrefillResult, SmartClaimStartPlan, StartEntryDecision]:
    """
    Workflow entry for C03:
      C01 → LookupResult
      C02 → PrefillResult
      C03 → SmartClaimStartPlan
      branch on plan fields — never touch AMS / adapters.
    """
    lookup = lookup_customer(person_link_key)
    prefill = prefill_from_lookup(lookup)
    plan = build_smart_claim_start_plan(lookup, prefill)
    decision = decide_start_entry(plan)
    return lookup, prefill, plan, decision


def simulate_smart_start_chain(
    lookup: LookupResult,
    prefill: PrefillResult | None = None,
    plan: SmartClaimStartPlan | None = None,
) -> list[dict[str, Any]]:
    """Founder-readable narrative: Lookup → Prefill → Smart Start presentation."""
    result_prefill = prefill if prefill is not None else prefill_from_lookup(lookup)
    result_plan = (
        plan
        if plan is not None
        else build_smart_claim_start_plan(lookup, result_prefill)
    )
    lookup_decision = decide_lookup_entry(lookup)
    prefill_decision = decide_prefill_entry(
        lookup, result_prefill, lookup_decision=lookup_decision
    )
    start_decision = decide_start_entry(result_plan)
    return [
        {"step": "mini_program", "ok": True, "note": "wx.login → person_link_key"},
        {
            "step": "lookup",
            "ok": True,
            "via": "capability_c01",
            "match_status": lookup.get("match_status"),
            "journey_mode": lookup_decision.journey_mode,
        },
        {
            "step": "prefill",
            "ok": True,
            "via": "capability_c02",
            "auto_prefill_count": prefill_decision.auto_prefill_count,
            "zero_auto": prefill_decision.zero_auto,
            "owns_start_claim_screens": prefill_decision.owns_start_claim_screens,
        },
        {
            "step": "smart_claim_start",
            "ok": True,
            "via": "capability_c03",
            "plan_mode": start_decision.plan_mode,
            "headline_zh": start_decision.headline_zh,
            "primary_cta_zh": start_decision.primary_cta_zh,
            "secondary_cta_zh": start_decision.secondary_cta_zh,
            "known_chip_count": start_decision.known_chip_count,
            "required_confirm_count": start_decision.required_confirm_count,
            "soft_notice_count": start_decision.soft_notice_count,
            "estimated_customer_inputs": start_decision.estimated_customer_inputs,
            "has_blank_escape": start_decision.has_blank_escape,
            "never_blocks_accident": start_decision.never_blocks_accident,
            "no_quiz_on_unambiguous": start_decision.no_quiz_on_unambiguous,
            "lands_on_story": start_decision.lands_on_story,
            "owns_start_claim_screens": start_decision.owns_start_claim_screens,
        },
        {
            "step": "close_boundary",
            "ok": True,
            "c03_wrote_crm": False,
            "c03_is_presentation_only": True,
            "no_ams": True,
            "no_notification": True,
            "no_timeline": True,
        },
    ]
