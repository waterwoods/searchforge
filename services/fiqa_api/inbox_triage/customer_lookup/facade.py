"""C01 Customer Lookup Capability — facade.

Answers only: "Who is this customer?"
READ ONLY: match + project. Never updates/merges/creates CRM records.

Architecture (Capability Constitution L-01…L-03, L-05, L-08, L-11):
  Workflow → this Capability → Adapter → LookupResult

Feature flag (default OFF):
  P4_CUSTOMER_LOOKUP_MOCK=1

Force degrade:
  P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE=1
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Any

from services.fiqa_api.inbox_triage.customer_lookup.adapters import (
    CustomerDirectoryAdapter,
    get_default_directory_adapter,
)
from services.fiqa_api.inbox_triage.customer_lookup.contract import (
    LookupResult,
    assert_lookup_result_complete,
    empty_lookup_result,
)
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    reset_mock_directory_for_tests,
)

FLAG_ENV = "P4_CUSTOMER_LOOKUP_MOCK"
FORCE_UNAVAILABLE_ENV = "P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE"

# Valid opaque MP identity prefix (P29B). Does not redesign identity.
_PERSON_LINK_PREFIX = "wx_"

# Test / DI override — Workflow never sets this; tests may inject a fake adapter.
_ADAPTER_OVERRIDE: CustomerDirectoryAdapter | None = None


def _truthy_env(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def customer_lookup_mock_enabled() -> bool:
    return _truthy_env(FLAG_ENV)


def reset_customer_lookup_mock_for_tests() -> None:
    global _ADAPTER_OVERRIDE
    _ADAPTER_OVERRIDE = None
    reset_mock_directory_for_tests()


def set_directory_adapter_for_tests(adapter: CustomerDirectoryAdapter | None) -> None:
    """Inject a fake adapter (tests only). Proves Capability↔Adapter swappability."""
    global _ADAPTER_OVERRIDE
    _ADAPTER_OVERRIDE = adapter


def _resolve_adapter() -> CustomerDirectoryAdapter:
    if _ADAPTER_OVERRIDE is not None:
        return _ADAPTER_OVERRIDE
    return get_default_directory_adapter()


def _is_valid_person_link_shape(person_link_key: str) -> bool:
    key = str(person_link_key or "").strip()
    if not key.startswith(_PERSON_LINK_PREFIX):
        return False
    return len(key) >= len(_PERSON_LINK_PREFIX) + 8


def _sanitize_result(result: LookupResult) -> LookupResult:
    """Never leak OpenID / person_link_key into LookupResult payload."""
    out = deepcopy(result)
    blob = str(out)
    if "openid" in blob.lower():
        raise AssertionError("LookupResult must never contain openid")
    for banned in ("openid", "person_link_key", "raw_openid", "wechat_openid"):
        out.pop(banned, None)  # type: ignore[misc]
        cust = out.get("customer")
        if isinstance(cust, dict):
            cust.pop(banned, None)
    assert_lookup_result_complete(out)
    return out


def lookup_customer(person_link_key: str | None) -> LookupResult:
    """
    Capability entry: person_link_key → LookupResult.

    Always returns a complete LookupResult (never raises for match failures).
    When the feature flag is off, returns LOOKUP_UNAVAILABLE so callers degrade.
    Does not import AMS/CRM SDKs — only the Adapter protocol.
    """
    try:
        return _lookup_customer_inner(person_link_key)
    except Exception:
        # Production-safe degrade — never break Mini Program / Workbench UI.
        return _sanitize_result(
            empty_lookup_result(
                match_status="LOOKUP_UNAVAILABLE",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["lookup_exception_degraded"],
            )
        )


def _lookup_customer_inner(person_link_key: str | None) -> LookupResult:
    if not customer_lookup_mock_enabled():
        result = empty_lookup_result(
            match_status="LOOKUP_UNAVAILABLE",
            lookup_confidence="LOW",
            next_action="start_blank_claim",
            reason_codes=["lookup_flag_off"],
        )
        result["lookup_source"] = "unavailable"
        return _sanitize_result(result)

    if _truthy_env(FORCE_UNAVAILABLE_ENV):
        result = empty_lookup_result(
            match_status="LOOKUP_UNAVAILABLE",
            lookup_confidence="LOW",
            next_action="start_blank_claim",
            reason_codes=["lookup_force_unavailable"],
        )
        result["lookup_source"] = "unavailable"
        return _sanitize_result(result)

    key = str(person_link_key or "").strip()
    if not key or not _is_valid_person_link_shape(key):
        return _sanitize_result(
            empty_lookup_result(
                match_status="UNMATCHED_IDENTITY",
                lookup_confidence="LOW",
                next_action="relogin",
                reason_codes=["invalid_person_link_key"],
            )
        )

    # Adapter owns datasource. Capability never reads fixture tables itself.
    adapter = _resolve_adapter()
    return _sanitize_result(adapter.lookup_by_person_link(key))


def lookup_customer_for_session(session_id: str | None) -> LookupResult:
    """
    Resolve person_link_key from MP session_id, then lookup.

    Uses existing P29B mapping only — no identity redesign.
    """
    from services.fiqa_api.inbox_triage.mp_customer_identity import person_link_from_session_id

    link = person_link_from_session_id(str(session_id or "").strip())
    if not link:
        return lookup_customer(None)
    return lookup_customer(link)


def broker_header_fields_from_lookup(result: LookupResult) -> dict[str, str]:
    """
    Read-only projection helpers for Broker Header simulation.

    Does not mutate cases. Callers may copy these into case facts elsewhere.
    """
    prefill = result.get("prefill") or {}
    customer = result.get("customer") or {}
    vehicles = result.get("vehicles") or []
    name = str(prefill.get("customer_name") or customer.get("display_name") or "").strip()
    vehicle = str(prefill.get("primary_vehicle_summary") or "").strip()
    if not vehicle and len(vehicles) == 1:
        v0 = vehicles[0]
        vehicle = " ".join(
            str(v0.get(k) or "").strip() for k in ("year", "make", "model") if v0.get(k)
        ).strip()
    next_action = str(result.get("next_action") or "").strip()
    action_label = {
        "continue_active_case": "继续当前案件",
        "confirm_vehicle": "确认事故车辆",
        "start_blank_claim": "开始新报案",
        "confirm_stale_policy": "确认过期保单信息",
        "contact_broker": "联系经纪人核对身份",
        "relogin": "请重新登录",
    }.get(next_action, "打开核对")
    return {
        "customer_display_name": name or "—",
        "vehicle_summary": vehicle or "—",
        "current_next_action": action_label,
        "lookup_confidence": str(result.get("lookup_confidence") or "LOW"),
        "match_status": str(result.get("match_status") or "NOT_FOUND"),
    }


def simulate_workflow_steps(result: LookupResult) -> list[dict[str, Any]]:
    """
    Backward-compatible shim.

    Prefer: workflow_v2.c01_lookup_entry.simulate_main_chain_from_lookup
    """
    from services.fiqa_api.inbox_triage.workflow_v2.c01_lookup_entry import (
        simulate_main_chain_from_lookup,
    )

    return simulate_main_chain_from_lookup(result)
