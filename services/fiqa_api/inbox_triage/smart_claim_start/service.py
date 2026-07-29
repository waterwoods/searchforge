"""P4 Integration 01 — Smart Claim Start request helper.

Chains Cap 01 Lookup → Cap 02 Prefill → Cap 03 Plan for Mini Program.
READ ONLY. Never writes CRM / identity / cases.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from services.fiqa_api.inbox_triage.claim_prefill import build_prefill_result
from services.fiqa_api.inbox_triage.customer_lookup import (
    customer_lookup_mock_enabled,
    lookup_customer,
    lookup_customer_for_session,
    lookup_demo_invite_fixture,
)
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import SCENARIO_KEYS
from services.fiqa_api.inbox_triage.smart_claim_start.engine import (
    build_smart_claim_start_plan,
)

# Founder QA / DevTools scenario aliases (honored only when mock flag is on).
_SCENARIO_ALIASES: dict[str, str] = {
    "S1": "S1_existing_active",
    "S2": "S2_multi_vehicle",
    "S3": "S3_no_active",
    "S4": "S4_stale_policy",
    "S5": "S5_no_mapping",
    "S6": "S6_unavailable",
    "AMBIGUOUS": "AMBIGUOUS",
}


def resolve_mock_scenario_person_link(mock_scenario: str | None) -> str | None:
    """Map S1…S6 / long ids → mock person_link_key. None if unknown."""
    raw = str(mock_scenario or "").strip()
    if not raw:
        return None
    upper = raw.upper()
    scenario_id = _SCENARIO_ALIASES.get(upper) or raw
    if scenario_id in SCENARIO_KEYS:
        return SCENARIO_KEYS[scenario_id]
    # Allow direct mock keys (wx_mock_cap01_…).
    if raw.startswith("wx_mock_cap01_"):
        return raw
    return None


def _strip_banned(plan: dict[str, Any]) -> dict[str, Any]:
    """Never leak identity/technical keys to Mini Program clients."""
    out = deepcopy(plan)
    for banned in (
        "openid",
        "person_link_key",
        "raw_openid",
        "wechat_openid",
        "case_id",
        "vehicle_ref",
        "broker_customer_ref",
        "policy_ref",
    ):
        out.pop(banned, None)
    # Chips/confirm options are already customer-safe from Cap 03.
    return out


def build_smart_claim_start_response(
    *,
    session_id: str | None = None,
    person_link_key: str | None = None,
    mock_scenario: str | None = None,
) -> dict[str, Any]:
    """
    Cap 01 → Cap 02 → Cap 03 for one request.

    Demo Invite overlay (CHEN_DEMO_INVITE_ENABLED + redeemed session):
      supplies mock Lookup/Prefill without requiring P4_CUSTOMER_LOOKUP_MOCK.
      person_link_key is never rewritten.

    Client-supplied mock_scenario remains DevTools-only and still requires
    P4_CUSTOMER_LOOKUP_MOCK so ordinary QA traffic stays on blank claim.

    When neither overlay nor (flag + mock_scenario) applies, lookup degrades
    to LOOKUP_UNAVAILABLE → BLANK_DEGRADE.
    """
    overlay_scenario = None
    if session_id and str(session_id).strip():
        try:
            from services.fiqa_api.inbox_triage.demo_invite import (
                resolve_overlay_mock_scenario,
            )

            overlay_scenario = resolve_overlay_mock_scenario(str(session_id).strip())
        except Exception:
            overlay_scenario = None

    if overlay_scenario:
        mock_key = resolve_mock_scenario_person_link(overlay_scenario)
        if mock_key:
            lookup = lookup_demo_invite_fixture(mock_key)
            identity_source = "demo_invite_overlay"
        else:
            lookup = lookup_customer(None)
            identity_source = "demo_invite_overlay_invalid"
    elif customer_lookup_mock_enabled() and mock_scenario:
        # Global mock flag — Founder QA / DevTools only; not ordinary QA traffic.
        mock_key = resolve_mock_scenario_person_link(mock_scenario)
        if mock_key:
            lookup = lookup_customer(mock_key)
            identity_source = "mock_scenario"
        elif person_link_key and str(person_link_key).strip():
            lookup = lookup_customer(str(person_link_key).strip())
            identity_source = "person_link_key"
        elif session_id and str(session_id).strip():
            lookup = lookup_customer_for_session(str(session_id).strip())
            identity_source = "session_id"
        else:
            lookup = lookup_customer(None)
            identity_source = "none"
    elif person_link_key and str(person_link_key).strip():
        lookup = lookup_customer(str(person_link_key).strip())
        identity_source = "person_link_key"
    elif session_id and str(session_id).strip():
        lookup = lookup_customer_for_session(str(session_id).strip())
        identity_source = "session_id"
    else:
        lookup = lookup_customer(None)
        identity_source = "none"

    prefill = build_prefill_result(lookup)
    plan = build_smart_claim_start_plan(lookup, prefill)
    safe_plan = _strip_banned(dict(plan))

    out: dict[str, Any] = {
        "ok": True,
        # True when global mock flag is on OR this response used a demo overlay.
        "lookup_enabled": bool(
            customer_lookup_mock_enabled() or identity_source == "demo_invite_overlay"
        ),
        "identity_source": identity_source,
        "plan": safe_plan,
        # Thin diagnostics for Founder QA / simulation — not customer UI.
        "lookup_match_status": str(lookup.get("match_status") or ""),
        "prefill_source": str(prefill.get("prefill_source") or ""),
    }
    if overlay_scenario:
        out["demo_invite_overlay"] = True
        try:
            from services.fiqa_api.inbox_triage.demo_invite import DEMO_NAME

            out["demo_name"] = DEMO_NAME
        except Exception:
            out["demo_name"] = "chen_known_customer_demo"
    return out
