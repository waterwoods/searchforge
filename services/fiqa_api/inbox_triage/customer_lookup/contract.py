"""LookupResult contract for P4 Capability 01 — Customer Lookup.

Stable for mock harness and future AMS adapter swap.
Never includes OpenID or raw person_link_key in customer/broker-facing fields.
"""

from __future__ import annotations

from typing import Any, Final, Literal, TypedDict

MatchStatus = Literal[
    "MATCH_FOUND",
    "NOT_FOUND",
    "UNMATCHED_IDENTITY",
    "AMBIGUOUS_MATCH",
    "STALE_POLICY",
    "LOOKUP_UNAVAILABLE",
]

LookupConfidence = Literal["HIGH", "MEDIUM", "LOW"]

NextAction = Literal[
    "continue_active_case",
    "confirm_vehicle",
    "start_blank_claim",
    "confirm_stale_policy",
    "contact_broker",
    "relogin",
]

MATCH_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    {
        "MATCH_FOUND",
        "NOT_FOUND",
        "UNMATCHED_IDENTITY",
        "AMBIGUOUS_MATCH",
        "STALE_POLICY",
        "LOOKUP_UNAVAILABLE",
    }
)

LOOKUP_CONFIDENCE_VALUES: Final[frozenset[str]] = frozenset({"HIGH", "MEDIUM", "LOW"})

NEXT_ACTION_VALUES: Final[frozenset[str]] = frozenset(
    {
        "continue_active_case",
        "confirm_vehicle",
        "start_blank_claim",
        "confirm_stale_policy",
        "contact_broker",
        "relogin",
    }
)


class CustomerProjection(TypedDict, total=False):
    display_name: str
    phone_last4: str
    phone_e164_mock: str
    broker_customer_ref: str


class PolicyProjection(TypedDict, total=False):
    policy_ref: str
    carrier_display: str
    status: str  # active | expired | unknown
    freshness: str  # fresh | stale | unknown
    effective_end: str


class VehicleProjection(TypedDict, total=False):
    vehicle_ref: str
    year: str
    make: str
    model: str
    vin_last4: str
    license_plate: str
    is_primary: bool


class ActiveCaseProjection(TypedDict, total=False):
    case_id: str
    resume_available: bool


class PrefillProjection(TypedDict, total=False):
    customer_name: str
    customer_phone: str
    primary_vehicle_summary: str
    policy_number: str


class LookupResult(TypedDict, total=False):
    match_status: MatchStatus
    lookup_confidence: LookupConfidence
    customer: CustomerProjection | None
    policy: PolicyProjection | None
    vehicles: list[VehicleProjection]
    active_case: ActiveCaseProjection | None
    prefill: PrefillProjection
    next_action: NextAction
    reason_codes: list[str]
    lookup_source: str  # mock | unavailable | future ams id — never crm write path


def empty_lookup_result(
    *,
    match_status: MatchStatus,
    lookup_confidence: LookupConfidence = "LOW",
    next_action: NextAction = "start_blank_claim",
    reason_codes: list[str] | None = None,
) -> LookupResult:
    """Complete LookupResult for every failure mode — never a thrown UI break."""
    return {
        "match_status": match_status,
        "lookup_confidence": lookup_confidence,
        "customer": None,
        "policy": None,
        "vehicles": [],
        "active_case": None,
        "prefill": {},
        "next_action": next_action,
        "reason_codes": list(reason_codes or []),
        "lookup_source": "mock",
    }


def assert_lookup_result_complete(result: dict[str, Any]) -> None:
    """Harness invariant: every response has the contract keys."""
    required = (
        "match_status",
        "lookup_confidence",
        "customer",
        "policy",
        "vehicles",
        "active_case",
        "prefill",
        "next_action",
        "reason_codes",
    )
    for key in required:
        if key not in result:
            raise AssertionError(f"LookupResult missing key: {key}")
    if result["match_status"] not in MATCH_STATUS_VALUES:
        raise AssertionError(f"invalid match_status: {result['match_status']}")
    if result["lookup_confidence"] not in LOOKUP_CONFIDENCE_VALUES:
        raise AssertionError(f"invalid lookup_confidence: {result['lookup_confidence']}")
    if result["next_action"] not in NEXT_ACTION_VALUES:
        raise AssertionError(f"invalid next_action: {result['next_action']}")
    if not isinstance(result["vehicles"], list):
        raise AssertionError("vehicles must be a list")
    if not isinstance(result["prefill"], dict):
        raise AssertionError("prefill must be a dict")
    if not isinstance(result["reason_codes"], list):
        raise AssertionError("reason_codes must be a list")
