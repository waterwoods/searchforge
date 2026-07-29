"""C02 Claim Prefill Capability — facade.

Answers only: "What do we already know vs still need?"
Suggestion only: never writes CRM, never invents truth, never owns Start Claim screens.

Architecture (Capability Constitution L-01…L-03, L-06, L-08, L-11):
  Workflow → this Capability → Adapter → PrefillResult

No customer-facing feature flag: Prefill is not customer-visible until C03 renders.
Customer Lookup flag (C01) still gates whether LookupResult carries match truth.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from services.fiqa_api.inbox_triage.claim_prefill.adapters import (
    PrefillClassifierAdapter,
    get_default_classifier_adapter,
)
from services.fiqa_api.inbox_triage.claim_prefill.contract import (
    PrefillResult,
    assert_prefill_result_complete,
    empty_prefill_result,
)
from services.fiqa_api.inbox_triage.claim_prefill.engine import (
    classification_map,
    founder_shorthand_map,
)
from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult

# Test / DI override — Workflow never sets this; tests may inject a fake adapter.
_ADAPTER_OVERRIDE: PrefillClassifierAdapter | None = None


def reset_claim_prefill_for_tests() -> None:
    global _ADAPTER_OVERRIDE
    _ADAPTER_OVERRIDE = None


def set_classifier_adapter_for_tests(adapter: PrefillClassifierAdapter | None) -> None:
    """Inject a fake classifier (tests only). Proves Capability↔Adapter swappability."""
    global _ADAPTER_OVERRIDE
    _ADAPTER_OVERRIDE = adapter


def _resolve_adapter() -> PrefillClassifierAdapter:
    if _ADAPTER_OVERRIDE is not None:
        return _ADAPTER_OVERRIDE
    return get_default_classifier_adapter()


def _sanitize_result(result: PrefillResult) -> PrefillResult:
    """Never leak OpenID / person_link / enum theater into unexpected keys."""
    out = deepcopy(result)
    blob = str(out).lower()
    if "openid" in blob:
        raise AssertionError("PrefillResult must never contain openid")
    for banned in ("openid", "person_link_key", "raw_openid", "wechat_openid"):
        out.pop(banned, None)  # type: ignore[misc]
    assert_prefill_result_complete(out)
    return out


def prefill_from_lookup(lookup: LookupResult | dict[str, Any] | None) -> PrefillResult:
    """
    Capability entry: LookupResult → PrefillResult.

    Always returns a complete PrefillResult (never raises for classify failures).
    Does not import AMS/CRM — only the Adapter protocol.
    """
    try:
        return _prefill_from_lookup_inner(lookup)
    except Exception:
        return _sanitize_result(
            empty_prefill_result(
                lookup=dict(lookup or {}),
                reason_codes=["prefill_exception_degraded"],
            )
        )


def _prefill_from_lookup_inner(
    lookup: LookupResult | dict[str, Any] | None,
) -> PrefillResult:
    if not isinstance(lookup, dict):
        return _sanitize_result(
            empty_prefill_result(reason_codes=["prefill_missing_lookup"])
        )
    adapter = _resolve_adapter()
    return _sanitize_result(adapter.classify(lookup))  # type: ignore[arg-type]


def build_prefill_result(lookup: LookupResult) -> PrefillResult:
    """
    Backward-compatible Capability entry (P4 harness + C03 consumers).

    Prefer `prefill_from_lookup` in new Workflow V2 code.
    """
    return prefill_from_lookup(lookup)


def customer_visible_effects(prefill: PrefillResult) -> dict[str, Any]:
    """
    Human consequences only — never classification enum names for UI copy.

    C03 will render; this helper exists for Workflow / Founder simulation.
    """
    by_key = {f["field_key"]: f for f in (prefill.get("fields") or [])}
    auto_chips: list[str] = []
    for key in ("customer_name", "vehicle", "policy_number", "insurance_company"):
        f = by_key.get(key) or {}
        if f.get("classification") == "AUTO_PREFILL" and f.get("value"):
            auto_chips.append(str(f["value"]))
    return {
        "auto_chip_values": auto_chips,
        "customer_must_provide": list(prefill.get("customer_ask_fields") or []),
        "vehicle_confirm_required": bool(
            (by_key.get("vehicle") or {}).get("needs_confirm")
        ),
        "stale_policy_confirm_required": bool(
            (by_key.get("policy_number") or {}).get("needs_confirm")
            or (by_key.get("policy") or {}).get("needs_confirm")
        ),
        "zero_auto": int(prefill.get("auto_prefill_count") or 0) == 0,
        # Explicit: never expose these to customers
        "exposes_classification_enums": False,
    }


__all__ = [
    "build_prefill_result",
    "classification_map",
    "customer_visible_effects",
    "founder_shorthand_map",
    "prefill_from_lookup",
    "reset_claim_prefill_for_tests",
    "set_classifier_adapter_for_tests",
]
