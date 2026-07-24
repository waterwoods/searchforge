"""PrefillResult contract for P4 Capability 02 — Claim Prefill.

Consumes Cap 01 LookupResult only. Never CRM, never identity redesign.
Classifies every Start Claim / claim-journey field for Founder review.
"""

from __future__ import annotations

from typing import Any, Final, Literal, TypedDict

FieldClass = Literal[
    "AUTO_PREFILL",
    "CUSTOMER_REQUIRED",
    "BROKER_REQUIRED",
    "UNKNOWN",
]

FIELD_CLASS_VALUES: Final[frozenset[str]] = frozenset(
    {
        "AUTO_PREFILL",
        "CUSTOMER_REQUIRED",
        "BROKER_REQUIRED",
        "UNKNOWN",
    }
)

# Founder-required review list (Capability 02). Stable keys for sim + QA.
START_CLAIM_FIELD_KEYS: Final[tuple[str, ...]] = (
    "customer_name",
    "policy",
    "vehicle",
    "vin",
    "license_plate",
    "insurance_company",
    "policy_number",
    "driver",
    "phone",
    "email",
    "accident_time",
    "accident_location",
    "accident_story",
    "damage",
    "injury",
    "police_report",
    "photos",
    "documents",
)

FIELD_LABELS: Final[dict[str, str]] = {
    "customer_name": "Customer Name",
    "policy": "Policy",
    "vehicle": "Vehicle",
    "vin": "VIN",
    "license_plate": "License Plate",
    "insurance_company": "Insurance Company",
    "policy_number": "Policy Number",
    "driver": "Driver",
    "phone": "Phone",
    "email": "Email",
    "accident_time": "Accident Time",
    "accident_location": "Accident Location",
    "accident_story": "Accident Story",
    "damage": "Damage",
    "injury": "Injury",
    "police_report": "Police Report",
    "photos": "Photos",
    "documents": "Documents",
}


class FieldPrefill(TypedDict, total=False):
    field_key: str
    label: str
    classification: FieldClass
    """AUTO / ASK / UNKNOWN shorthand for Founder table (derived from classification)."""
    founder_shorthand: Literal["AUTO", "ASK", "UNKNOWN"]
    value: str | None
    reason_code: str
    needs_confirm: bool
    candidates: list[str]


class PrefillResult(TypedDict, total=False):
    lookup_match_status: str
    lookup_confidence: str
    lookup_next_action: str
    fields: list[FieldPrefill]
    """Counts for Founder Customer Input Reduction."""
    auto_prefill_count: int
    customer_required_count: int
    broker_required_count: int
    unknown_count: int
    """Customer fields that still require customer input on this path."""
    customer_ask_fields: list[str]
    """Fields stamped from lookup without asking."""
    auto_fields: list[str]
    prefill_source: str  # lookup_mock | lookup_unavailable
    reason_codes: list[str]


def founder_shorthand_for(classification: FieldClass) -> Literal["AUTO", "ASK", "UNKNOWN"]:
    if classification == "AUTO_PREFILL":
        return "AUTO"
    if classification == "UNKNOWN":
        return "UNKNOWN"
    # CUSTOMER_REQUIRED and BROKER_REQUIRED both mean "not auto" — ASK
    return "ASK"


def empty_field(
    field_key: str,
    classification: FieldClass,
    *,
    value: str | None = None,
    reason_code: str,
    needs_confirm: bool = False,
    candidates: list[str] | None = None,
) -> FieldPrefill:
    return {
        "field_key": field_key,
        "label": FIELD_LABELS.get(field_key, field_key),
        "classification": classification,
        "founder_shorthand": founder_shorthand_for(classification),
        "value": value,
        "reason_code": reason_code,
        "needs_confirm": needs_confirm,
        "candidates": list(candidates or []),
    }


def assert_prefill_result_complete(result: dict[str, Any]) -> None:
    required = (
        "lookup_match_status",
        "lookup_confidence",
        "lookup_next_action",
        "fields",
        "auto_prefill_count",
        "customer_required_count",
        "broker_required_count",
        "unknown_count",
        "customer_ask_fields",
        "auto_fields",
        "prefill_source",
        "reason_codes",
    )
    for key in required:
        if key not in result:
            raise AssertionError(f"PrefillResult missing key: {key}")
    fields = result["fields"]
    if not isinstance(fields, list):
        raise AssertionError("fields must be a list")
    keys = [f.get("field_key") for f in fields]
    if list(keys) != list(START_CLAIM_FIELD_KEYS):
        raise AssertionError(
            f"fields must cover START_CLAIM_FIELD_KEYS in order; got {keys}"
        )
    for f in fields:
        if f.get("classification") not in FIELD_CLASS_VALUES:
            raise AssertionError(f"invalid classification: {f.get('classification')}")
