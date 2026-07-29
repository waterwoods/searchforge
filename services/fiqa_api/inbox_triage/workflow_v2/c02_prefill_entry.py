"""Workflow V2 — C02 Claim Prefill entry (journey owner).

Call pattern (Capability Constitution):
  Workflow needs "what do we already know?"
    → calls Customer Lookup (C01) for LookupResult
    → calls Claim Prefill capability (C02)
    → receives PrefillResult
    → branches on stable result fields
    → never imports Prefill adapters / engine / CRM

Scope: C02 only. Does not call C03 Smart Claim Start. Does not invent screens.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.fiqa_api.inbox_triage.claim_prefill.contract import PrefillResult
from services.fiqa_api.inbox_triage.claim_prefill.facade import (
    customer_visible_effects,
    prefill_from_lookup,
)
from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult
from services.fiqa_api.inbox_triage.customer_lookup.facade import lookup_customer
from services.fiqa_api.inbox_triage.workflow_v2.c01_lookup_entry import (
    LookupEntryDecision,
    decide_lookup_entry,
)

# Baseline askable fields before Prefill (Founder reduction table).
_BEFORE_ASK_FIELDS = 18


@dataclass(frozen=True)
class PrefillEntryDecision:
    """Workflow decision derived only from PrefillResult (+ Lookup journey mode)."""

    lookup_journey_mode: str
    auto_prefill_count: int
    customer_required_count: int
    customer_ask_fields: tuple[str, ...]
    needs_vehicle_confirm: bool
    needs_stale_policy_confirm: bool
    zero_auto: bool
    typing_reduction_removed: int
    auto_chip_values: tuple[str, ...]
    # Journey remains open: Prefill never blocks accident reporting.
    blocks_accident_report: bool
    prefill_source: str
    # Explicit out of scope for this Workflow module
    owns_start_claim_screens: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decide_prefill_entry(
    lookup: LookupResult,
    prefill: PrefillResult,
    *,
    lookup_decision: LookupEntryDecision | None = None,
) -> PrefillEntryDecision:
    """
    Pure Workflow policy: PrefillResult → ask / confirm summary.

    Does not invent Start Claim presentation (C03). Does not re-encode taxonomy.
    """
    ld = lookup_decision or decide_lookup_entry(lookup)
    effects = customer_visible_effects(prefill)
    after = int(prefill.get("customer_required_count") or 0)
    removed = max(0, _BEFORE_ASK_FIELDS - after)
    return PrefillEntryDecision(
        lookup_journey_mode=ld.journey_mode,
        auto_prefill_count=int(prefill.get("auto_prefill_count") or 0),
        customer_required_count=after,
        customer_ask_fields=tuple(prefill.get("customer_ask_fields") or ()),
        needs_vehicle_confirm=bool(effects.get("vehicle_confirm_required")),
        needs_stale_policy_confirm=bool(effects.get("stale_policy_confirm_required")),
        zero_auto=bool(effects.get("zero_auto")),
        typing_reduction_removed=removed,
        auto_chip_values=tuple(effects.get("auto_chip_values") or ()),
        blocks_accident_report=False,
        prefill_source=str(prefill.get("prefill_source") or ""),
        owns_start_claim_screens=False,
    )


def enter_claim_with_prefill(
    person_link_key: str | None,
) -> tuple[LookupResult, PrefillResult, PrefillEntryDecision]:
    """
    Workflow entry for C02:
      C01 Capability → LookupResult
      C02 Capability → PrefillResult
      branch on contract fields → never touch classification adapters.
    """
    lookup = lookup_customer(person_link_key)
    prefill = prefill_from_lookup(lookup)
    decision = decide_prefill_entry(lookup, prefill)
    return lookup, prefill, decision


def simulate_prefill_chain(
    lookup: LookupResult,
    prefill: PrefillResult | None = None,
) -> list[dict[str, Any]]:
    """
    Founder-readable narrative: Lookup → Prefill → (C03 later).

    Does not render Start Claim screens. Does not call Smart Claim Start.
    """
    result = prefill if prefill is not None else prefill_from_lookup(lookup)
    lookup_decision = decide_lookup_entry(lookup)
    decision = decide_prefill_entry(lookup, result, lookup_decision=lookup_decision)
    effects = customer_visible_effects(result)
    steps: list[dict[str, Any]] = [
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
            "auto_prefill_count": decision.auto_prefill_count,
            "customer_required_count": decision.customer_required_count,
            "customer_ask_fields": list(decision.customer_ask_fields),
            "zero_auto": decision.zero_auto,
            "typing_reduction_removed": decision.typing_reduction_removed,
            "auto_chip_values": list(decision.auto_chip_values),
            "needs_vehicle_confirm": decision.needs_vehicle_confirm,
            "needs_stale_policy_confirm": decision.needs_stale_policy_confirm,
            "exposes_enums_to_customer": effects.get("exposes_classification_enums"),
            "blocks_accident_report": decision.blocks_accident_report,
            "owns_start_claim_screens": decision.owns_start_claim_screens,
        },
        {
            "step": "start_claim_presentation",
            "ok": True,
            "deferred_to": "C03",
            "note": "Sprint 2 stops before Smart Claim Start / Mini Program wire",
        },
        {
            "step": "close_boundary",
            "ok": True,
            "prefill_wrote_crm": False,
            "prefill_is_suggestion_only": True,
        },
    ]
    return steps
