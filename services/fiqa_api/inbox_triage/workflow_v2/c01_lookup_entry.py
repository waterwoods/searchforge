"""Workflow V2 — C01 Customer Lookup entry (journey owner).

Call pattern (Capability Constitution):
  Workflow needs "who is this?"
    → calls Customer Lookup capability
    → receives LookupResult
    → branches on stable result fields
    → never imports MockDirectory / AMS / CRM

Scope: C01 only. Does not call C02 Prefill or C03 Smart Claim Start.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult
from services.fiqa_api.inbox_triage.customer_lookup.facade import (
    broker_header_fields_from_lookup,
    lookup_customer,
)

JourneyMode = Literal[
    "continue_active",
    "confirm_vehicle",
    "confirm_stale_policy",
    "blank_claim",
    "contact_broker",
    "relogin",
]

# Customer-visible screen intent — human language, not match_status enums.
_SCREEN_BY_MODE: dict[JourneyMode, str] = {
    "continue_active": "继续当前报案",
    "confirm_vehicle": "哪辆车出险？",
    "confirm_stale_policy": "确认保单信息后继续",
    "blank_claim": "今天发生了什么？",
    "contact_broker": "联系顾问核对身份",
    "relogin": "请重新进入小程序",
}


@dataclass(frozen=True)
class LookupEntryDecision:
    """Workflow decision derived only from LookupResult contract fields."""

    journey_mode: JourneyMode
    customer_next_screen: str
    primary_cta: str
    # Graceful degrade law: accident reporting must remain possible.
    blocks_accident_report: bool
    allows_manual_claim: bool
    match_status: str
    next_action: str
    vehicle_count: int
    lookup_source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _mode_from_lookup(result: LookupResult) -> JourneyMode:
    next_action = str(result.get("next_action") or "").strip()
    status = str(result.get("match_status") or "").strip()

    if next_action == "continue_active_case" or (
        status == "MATCH_FOUND" and result.get("active_case")
    ):
        return "continue_active"
    if next_action == "confirm_vehicle":
        return "confirm_vehicle"
    if next_action == "confirm_stale_policy" or status == "STALE_POLICY":
        return "confirm_stale_policy"
    if next_action == "contact_broker" or status == "AMBIGUOUS_MATCH":
        return "contact_broker"
    if next_action == "relogin" or status == "UNMATCHED_IDENTITY":
        return "relogin"
    # NOT_FOUND / LOOKUP_UNAVAILABLE / start_blank_claim → Pilot blank path
    return "blank_claim"


def _cta_for_mode(mode: JourneyMode) -> str:
    return {
        "continue_active": "继续当前报案",
        "confirm_vehicle": "确认车辆",
        "confirm_stale_policy": "确认后继续",
        "blank_claim": "开始报案",
        "contact_broker": "联系顾问",
        "relogin": "重新登录",
    }[mode]


def decide_lookup_entry(result: LookupResult) -> LookupEntryDecision:
    """
    Pure Workflow policy: LookupResult → journey branch.

    Depends only on contract fields. Never reads adapter/vendor payloads.
    """
    mode = _mode_from_lookup(result)
    vehicles = result.get("vehicles") or []
    # Only soft identity failure asks relogin; every other path can still report.
    blocks = mode == "relogin"
    # Ambiguous: primary CTA is contact broker, but blank claim must remain available.
    allows_manual = mode in (
        "blank_claim",
        "confirm_vehicle",
        "confirm_stale_policy",
        "contact_broker",
    )
    return LookupEntryDecision(
        journey_mode=mode,
        customer_next_screen=_SCREEN_BY_MODE[mode],
        primary_cta=_cta_for_mode(mode),
        blocks_accident_report=blocks,
        allows_manual_claim=allows_manual,
        match_status=str(result.get("match_status") or ""),
        next_action=str(result.get("next_action") or ""),
        vehicle_count=len(vehicles) if isinstance(vehicles, list) else 0,
        lookup_source=str(result.get("lookup_source") or ""),
    )


def enter_claim_with_lookup(person_link_key: str | None) -> tuple[LookupResult, LookupEntryDecision]:
    """
    Workflow entry for C01:
      call Capability → branch on LookupResult → never touch datasource.
    """
    result = lookup_customer(person_link_key)
    decision = decide_lookup_entry(result)
    return result, decision


def simulate_main_chain_from_lookup(result: LookupResult) -> list[dict[str, Any]]:
    """
    Narrative simulation of the main chain using LookupResult only.

    Lookup remains read-only: this does not create customers/claims.
    Lives in Workflow (journey), not in the Capability facade.
    """
    header = broker_header_fields_from_lookup(result)
    decision = decide_lookup_entry(result)
    status = result.get("match_status")
    steps: list[dict[str, Any]] = [
        {"step": "mini_program", "ok": True, "note": "wx.login → person_link_key"},
        {
            "step": "lookup",
            "ok": True,
            "match_status": status,
            "confidence": result.get("lookup_confidence"),
            "via": "capability_c01",
            "journey_mode": decision.journey_mode,
            "customer_next_screen": decision.customer_next_screen,
            "blocks_accident_report": decision.blocks_accident_report,
        },
        {
            "step": "broker_header",
            "ok": True,
            "fields": header,
            "note": "human fields only; no OpenID",
        },
        {
            "step": "workbench",
            "ok": True,
            "prefill": result.get("prefill") or {},
            "duplicate_customer": False,
        },
    ]

    if decision.journey_mode == "continue_active":
        steps.append(
            {
                "step": "request_more",
                "ok": True,
                "note": "optional gaps only; identity not re-captured",
            }
        )
        steps.append(
            {
                "step": "customer_continue",
                "ok": True,
                "next_action": "continue_active_case",
                "duplicate_claim": False,
            }
        )
    elif decision.journey_mode == "confirm_stale_policy":
        steps.append(
            {
                "step": "request_more",
                "ok": True,
                "note": "stale policy confirm / broker Request More",
            }
        )
        steps.append(
            {
                "step": "customer_continue",
                "ok": True,
                "next_action": result.get("next_action"),
                "duplicate_claim": False,
            }
        )
    elif decision.journey_mode == "blank_claim":
        steps.append(
            {
                "step": "request_more",
                "ok": True,
                "note": "degrade to blank claim path; no CRM write",
            }
        )
        steps.append(
            {
                "step": "customer_continue",
                "ok": True,
                "next_action": "start_blank_claim",
                "duplicate_claim": False,
                "graceful_degradation": True,
            }
        )
    elif decision.journey_mode == "contact_broker":
        steps.append(
            {
                "step": "request_more",
                "ok": True,
                "note": "no auto-merge; broker assist",
            }
        )
        steps.append(
            {
                "step": "customer_continue",
                "ok": True,
                "next_action": "contact_broker",
                "duplicate_claim": False,
                "duplicate_customer": False,
            }
        )
    elif decision.journey_mode == "relogin":
        steps.append(
            {
                "step": "request_more",
                "ok": True,
                "note": "blocked until relogin",
            }
        )
        steps.append(
            {
                "step": "customer_continue",
                "ok": True,
                "next_action": "relogin",
                "duplicate_claim": False,
            }
        )
    else:
        # confirm_vehicle (multi or single confirm chip)
        steps.append(
            {
                "step": "request_more",
                "ok": True,
                "note": "confirm vehicle or collect gaps only",
            }
        )
        steps.append(
            {
                "step": "customer_continue",
                "ok": True,
                "next_action": result.get("next_action"),
                "duplicate_claim": False,
                "vehicle_selection_required": decision.vehicle_count > 1,
            }
        )

    steps.append({"step": "review", "ok": True, "note": "broker review uses case facts"})
    steps.append(
        {
            "step": "close",
            "ok": True,
            "note": "Close clears Active Case via existing lifecycle — lookup does not write",
            "lookup_mutated_crm": False,
        }
    )
    return steps
