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

    mock_scenario is honored only when P4_CUSTOMER_LOOKUP_MOCK is enabled.
    When flag is off, lookup degrades to LOOKUP_UNAVAILABLE → BLANK_DEGRADE plan.
    """
    mock_key = None
    if customer_lookup_mock_enabled():
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

    prefill = build_prefill_result(lookup)
    plan = build_smart_claim_start_plan(lookup, prefill)
    safe_plan = _strip_banned(dict(plan))

    return {
        "ok": True,
        "lookup_enabled": customer_lookup_mock_enabled(),
        "identity_source": identity_source,
        "plan": safe_plan,
        # Thin diagnostics for Founder QA / simulation — not customer UI.
        "lookup_match_status": str(lookup.get("match_status") or ""),
        "prefill_source": str(prefill.get("prefill_source") or ""),
    }
