"""Customer Lookup Facade — P4 Capability 01.

READ ONLY: match + project + prefill suggestion.
Never updates/merges/creates customers, policies, vehicles, or CRM.

Feature flag (default OFF):
  P4_CUSTOMER_LOOKUP_MOCK=1

Force degrade:
  P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE=1
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Any

from services.fiqa_api.inbox_triage.customer_lookup.contract import (
    LookupResult,
    assert_lookup_result_complete,
    empty_lookup_result,
)
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    MOCK_KEY_S5_NO_MAPPING,
    MOCK_KEY_S6_UNAVAILABLE,
    get_fixture,
    reset_mock_directory_for_tests,
)

FLAG_ENV = "P4_CUSTOMER_LOOKUP_MOCK"
FORCE_UNAVAILABLE_ENV = "P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE"

# Valid opaque MP identity prefix (P29B). Does not redesign identity.
_PERSON_LINK_PREFIX = "wx_"


def _truthy_env(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def customer_lookup_mock_enabled() -> bool:
    return _truthy_env(FLAG_ENV)


def reset_customer_lookup_mock_for_tests() -> None:
    reset_mock_directory_for_tests()


def _is_valid_person_link_shape(person_link_key: str) -> bool:
    key = str(person_link_key or "").strip()
    if not key.startswith(_PERSON_LINK_PREFIX):
        return False
    # Opaque HMAC keys are longer; mock harness keys are also wx_* with body.
    return len(key) >= len(_PERSON_LINK_PREFIX) + 8


def _sanitize_result(result: LookupResult) -> LookupResult:
    """Never leak OpenID / person_link_key into LookupResult payload."""
    out = deepcopy(result)
    blob = str(out)
    if "openid" in blob.lower():
        raise AssertionError("LookupResult must never contain openid")
    # Drop accidental identity keys if a future adapter misbehaves.
    for banned in ("openid", "person_link_key", "raw_openid", "wechat_openid"):
        out.pop(banned, None)  # type: ignore[misc]
        cust = out.get("customer")
        if isinstance(cust, dict):
            cust.pop(banned, None)
    assert_lookup_result_complete(out)
    return out


def lookup_customer(person_link_key: str | None) -> LookupResult:
    """
    Facade entry: person_link_key → LookupResult.

    Always returns a complete LookupResult (never raises for match failures).
    When the feature flag is off, returns LOOKUP_UNAVAILABLE so callers degrade.
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


def lookup_demo_invite_fixture(person_link_key: str | None) -> LookupResult:
    """
    Read an allowlisted C01 mock fixture for a redeemed Demo Invite overlay.

    Does NOT require P4_CUSTOMER_LOOKUP_MOCK. Ordinary QA traffic without an
    overlay must keep using lookup_customer (flag-gated → blank degrade).
    Still respects FORCE_UNAVAILABLE for controlled degrade tests.
    """
    try:
        return _lookup_demo_invite_fixture_inner(person_link_key)
    except Exception:
        return _sanitize_result(
            empty_lookup_result(
                match_status="LOOKUP_UNAVAILABLE",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["demo_invite_lookup_exception_degraded"],
            )
        )


def _lookup_demo_invite_fixture_inner(person_link_key: str | None) -> LookupResult:
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
                next_action="start_blank_claim",
                reason_codes=["invalid_demo_fixture_key"],
            )
        )

    if key == MOCK_KEY_S6_UNAVAILABLE:
        result = empty_lookup_result(
            match_status="LOOKUP_UNAVAILABLE",
            lookup_confidence="LOW",
            next_action="start_blank_claim",
            reason_codes=["mock_lookup_unavailable"],
        )
        result["lookup_source"] = "unavailable"
        return _sanitize_result(result)

    if key == MOCK_KEY_S5_NO_MAPPING:
        return _sanitize_result(
            empty_lookup_result(
                match_status="NOT_FOUND",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["identity_without_customer_mapping"],
            )
        )

    fixture = get_fixture(key)
    if fixture is None:
        return _sanitize_result(
            empty_lookup_result(
                match_status="NOT_FOUND",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["no_mock_directory_row"],
            )
        )

    out = _sanitize_result(fixture)
    # Mark source so callers can distinguish invite overlay from global mock flag.
    reasons = list(out.get("reason_codes") or [])
    if "demo_invite_overlay" not in reasons:
        reasons.append("demo_invite_overlay")
    out["reason_codes"] = reasons
    out["lookup_source"] = "demo_invite_mock"
    return out


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

    # Scenario 6: reserved key forces unavailable while flag is on.
    if key == MOCK_KEY_S6_UNAVAILABLE:
        result = empty_lookup_result(
            match_status="LOOKUP_UNAVAILABLE",
            lookup_confidence="LOW",
            next_action="start_blank_claim",
            reason_codes=["mock_lookup_unavailable"],
        )
        result["lookup_source"] = "unavailable"
        return _sanitize_result(result)

    # Scenario 5: valid identity shape, no customer mapping in directory.
    if key == MOCK_KEY_S5_NO_MAPPING:
        return _sanitize_result(
            empty_lookup_result(
                match_status="NOT_FOUND",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["identity_without_customer_mapping"],
            )
        )

    fixture = get_fixture(key)
    if fixture is None:
        return _sanitize_result(
            empty_lookup_result(
                match_status="NOT_FOUND",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["no_mock_directory_row"],
            )
        )

    return _sanitize_result(fixture)


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
    Narrative simulation of the main chain using LookupResult only.

    Lookup remains read-only: this does not create customers/claims.
    """
    header = broker_header_fields_from_lookup(result)
    status = result.get("match_status")
    steps: list[dict[str, Any]] = [
        {"step": "mini_program", "ok": True, "note": "wx.login → person_link_key"},
        {"step": "lookup", "ok": True, "match_status": status, "confidence": result.get("lookup_confidence")},
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

    if status == "MATCH_FOUND" and result.get("active_case"):
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
    elif status == "STALE_POLICY":
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
    elif status in ("NOT_FOUND", "LOOKUP_UNAVAILABLE"):
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
    elif status == "AMBIGUOUS_MATCH":
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
    elif status == "UNMATCHED_IDENTITY":
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
        # Multi-vehicle / no-active MATCH_FOUND
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
