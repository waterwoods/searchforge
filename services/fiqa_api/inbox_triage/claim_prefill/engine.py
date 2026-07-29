"""Claim Prefill engine — P4 Capability 02.

Single responsibility: LookupResult → PrefillResult field classification.

Rules (Founder principle):
  Never ask customers for information we already know.
  Ask only for new accident facts.

Does not write CRM, cases, or identity. Mock lookup input only.
"""

from __future__ import annotations

from typing import Any

from services.fiqa_api.inbox_triage.claim_prefill.contract import (
    START_CLAIM_FIELD_KEYS,
    FieldClass,
    FieldPrefill,
    PrefillResult,
    assert_prefill_result_complete,
    empty_field,
)
from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult

# Accident facts — never present in Cap 01 lookup; always customer.
_ACCIDENT_CUSTOMER_FIELDS: frozenset[str] = frozenset(
    {
        "accident_time",
        "accident_location",
        "accident_story",
        "damage",
        "injury",
    }
)

# Follow-up evidence — Business Contract Nice-to-Have / Request More; broker owns.
_BROKER_EVIDENCE_FIELDS: frozenset[str] = frozenset(
    {
        "police_report",
        "photos",
        "documents",
    }
)


def _vehicle_summary(v: dict[str, Any]) -> str:
    parts = [str(v.get(k) or "").strip() for k in ("year", "make", "model")]
    return " ".join(p for p in parts if p).strip()


def _vin_display(v: dict[str, Any]) -> str | None:
    last4 = str(v.get("vin_last4") or "").strip()
    if not last4:
        return None
    return f"****{last4}"


def _build_counts(fields: list[FieldPrefill]) -> dict[str, Any]:
    auto = [f["field_key"] for f in fields if f["classification"] == "AUTO_PREFILL"]
    cust = [f["field_key"] for f in fields if f["classification"] == "CUSTOMER_REQUIRED"]
    broker = [f["field_key"] for f in fields if f["classification"] == "BROKER_REQUIRED"]
    unknown = [f["field_key"] for f in fields if f["classification"] == "UNKNOWN"]
    return {
        "auto_prefill_count": len(auto),
        "customer_required_count": len(cust),
        "broker_required_count": len(broker),
        "unknown_count": len(unknown),
        "customer_ask_fields": cust,
        "auto_fields": auto,
    }


def build_prefill_result(lookup: LookupResult) -> PrefillResult:
    """
    Classify every Start Claim field from a Cap 01 LookupResult.

    Pure function — no I/O, no CRM, no case writes.
    """
    status = str(lookup.get("match_status") or "NOT_FOUND")
    confidence = str(lookup.get("lookup_confidence") or "LOW")
    next_action = str(lookup.get("next_action") or "start_blank_claim")
    customer = lookup.get("customer") or None
    policy = lookup.get("policy") or None
    vehicles = list(lookup.get("vehicles") or [])
    prefill = dict(lookup.get("prefill") or {})
    reasons = list(lookup.get("reason_codes") or [])

    # Weak confidence → zero AUTO (Capability Constitution / Cap Review failure mode).
    matched = status in ("MATCH_FOUND", "STALE_POLICY") and confidence != "LOW"
    stale = status == "STALE_POLICY"
    multi_vehicle = len(vehicles) > 1
    single_vehicle = len(vehicles) == 1
    primary = vehicles[0] if single_vehicle else None
    # Cap 01 withholds primary_vehicle_summary when multi-vehicle.
    vehicle_auto_ok = single_vehicle and bool(
        prefill.get("primary_vehicle_summary")
        or (primary and _vehicle_summary(primary))
    )

    name = ""
    phone = ""
    policy_number = ""
    carrier = ""
    vehicle_value: str | None = None
    vin_value: str | None = None
    plate_value: str | None = None

    if matched and isinstance(customer, dict):
        name = str(
            prefill.get("customer_name") or customer.get("display_name") or ""
        ).strip()
        phone = str(
            prefill.get("customer_phone")
            or customer.get("phone_e164_mock")
            or ""
        ).strip()
        if not phone and customer.get("phone_last4"):
            phone = f"***-***-{customer.get('phone_last4')}"

    if matched and isinstance(policy, dict):
        policy_number = str(
            prefill.get("policy_number") or policy.get("policy_ref") or ""
        ).strip()
        carrier = str(policy.get("carrier_display") or "").strip()

    if vehicle_auto_ok and primary:
        vehicle_value = str(
            prefill.get("primary_vehicle_summary") or _vehicle_summary(primary)
        ).strip() or None
        vin_value = _vin_display(primary)
        plate_value = str(primary.get("license_plate") or "").strip() or None
    elif multi_vehicle:
        vehicle_value = None
        vin_value = None
        plate_value = None

    vehicle_candidates = [_vehicle_summary(v) for v in vehicles if _vehicle_summary(v)]

    fields: list[FieldPrefill] = []
    for key in START_CLAIM_FIELD_KEYS:
        fields.append(
            _classify_field(
                key,
                matched=matched,
                stale=stale,
                multi_vehicle=multi_vehicle,
                name=name,
                phone=phone,
                policy_number=policy_number,
                carrier=carrier,
                vehicle_value=vehicle_value,
                vin_value=vin_value,
                plate_value=plate_value,
                vehicle_candidates=vehicle_candidates,
            )
        )

    source = "lookup_mock"
    if status in ("LOOKUP_UNAVAILABLE", "NOT_FOUND", "UNMATCHED_IDENTITY", "AMBIGUOUS_MATCH"):
        if status == "LOOKUP_UNAVAILABLE":
            source = "lookup_unavailable"

    counts = _build_counts(fields)
    out: PrefillResult = {
        "lookup_match_status": status,
        "lookup_confidence": confidence,
        "lookup_next_action": next_action,
        "fields": fields,
        "prefill_source": source,
        "reason_codes": reasons
        + [
            "cap02_prefill_from_lookup",
            "never_ask_known_facts",
            "ask_only_new_accident_facts",
        ],
        **counts,
    }
    assert_prefill_result_complete(out)
    return out


def _classify_field(
    key: str,
    *,
    matched: bool,
    stale: bool,
    multi_vehicle: bool,
    name: str,
    phone: str,
    policy_number: str,
    carrier: str,
    vehicle_value: str | None,
    vin_value: str | None,
    plate_value: str | None,
    vehicle_candidates: list[str],
) -> FieldPrefill:
    if key in _ACCIDENT_CUSTOMER_FIELDS:
        return empty_field(
            key,
            "CUSTOMER_REQUIRED",
            value=None,
            reason_code="new_accident_fact",
        )

    if key in _BROKER_EVIDENCE_FIELDS:
        return empty_field(
            key,
            "BROKER_REQUIRED",
            value=None,
            reason_code="request_more_or_nice_to_have",
        )

    if key == "email":
        # Mock Cap 01 has no email source — do not invent or force-ask.
        return empty_field(
            key,
            "UNKNOWN",
            value=None,
            reason_code="no_lookup_source_mock",
        )

    if not matched:
        # Identity / policy unknown — do not expand Start Claim Must Haves.
        # Broker Request More / workbench owns gaps (Business Contract).
        return empty_field(
            key,
            "BROKER_REQUIRED",
            value=None,
            reason_code="no_customer_match_broker_gap",
        )

    # --- Matched path (MATCH_FOUND or STALE_POLICY) ---

    if key == "customer_name":
        if name:
            return empty_field(
                key,
                "AUTO_PREFILL",
                value=name,
                reason_code="lookup_customer_display_name",
            )
        return empty_field(
            key, "BROKER_REQUIRED", value=None, reason_code="matched_but_name_missing"
        )

    if key == "phone":
        if phone:
            return empty_field(
                key,
                "AUTO_PREFILL",
                value=phone,
                reason_code="lookup_customer_phone",
            )
        return empty_field(
            key, "BROKER_REQUIRED", value=None, reason_code="matched_but_phone_missing"
        )

    if key == "driver":
        # First-party default: named insured is the driver until customer corrects.
        if name:
            return empty_field(
                key,
                "AUTO_PREFILL",
                value=name,
                reason_code="default_driver_named_insured",
                needs_confirm=False,
            )
        return empty_field(
            key, "CUSTOMER_REQUIRED", value=None, reason_code="driver_unknown"
        )

    if key in ("policy", "policy_number"):
        value = policy_number or None
        if not value:
            return empty_field(
                key, "BROKER_REQUIRED", value=None, reason_code="policy_missing"
            )
        if stale:
            # Value known but must not be silently trusted.
            return empty_field(
                key,
                "CUSTOMER_REQUIRED",
                value=value,
                reason_code="confirm_stale_policy",
                needs_confirm=True,
            )
        return empty_field(
            key,
            "AUTO_PREFILL",
            value=value,
            reason_code="lookup_policy_ref",
        )

    if key == "insurance_company":
        if not carrier:
            return empty_field(
                key, "BROKER_REQUIRED", value=None, reason_code="carrier_missing"
            )
        if stale:
            return empty_field(
                key,
                "CUSTOMER_REQUIRED",
                value=carrier,
                reason_code="confirm_stale_policy",
                needs_confirm=True,
            )
        return empty_field(
            key,
            "AUTO_PREFILL",
            value=carrier,
            reason_code="lookup_carrier_display",
        )

    if key == "vehicle":
        if multi_vehicle:
            return empty_field(
                key,
                "CUSTOMER_REQUIRED",
                value=None,
                reason_code="confirm_which_vehicle",
                needs_confirm=True,
                candidates=vehicle_candidates,
            )
        if vehicle_value:
            return empty_field(
                key,
                "AUTO_PREFILL",
                value=vehicle_value,
                reason_code="lookup_single_vehicle",
            )
        return empty_field(
            key, "BROKER_REQUIRED", value=None, reason_code="vehicle_missing"
        )

    if key == "vin":
        if multi_vehicle:
            return empty_field(
                key,
                "CUSTOMER_REQUIRED",
                value=None,
                reason_code="confirm_which_vehicle",
                needs_confirm=True,
            )
        if vin_value:
            return empty_field(
                key,
                "AUTO_PREFILL",
                value=vin_value,
                reason_code="lookup_vin_last4_only",
            )
        # Full VIN is Request More; last4 missing → broker gap, not Start Claim.
        return empty_field(
            key, "BROKER_REQUIRED", value=None, reason_code="vin_not_in_lookup"
        )

    if key == "license_plate":
        if multi_vehicle:
            return empty_field(
                key,
                "CUSTOMER_REQUIRED",
                value=None,
                reason_code="confirm_which_vehicle",
                needs_confirm=True,
            )
        if plate_value:
            return empty_field(
                key,
                "AUTO_PREFILL",
                value=plate_value,
                reason_code="lookup_license_plate",
            )
        return empty_field(
            key, "BROKER_REQUIRED", value=None, reason_code="plate_not_in_lookup"
        )

    # Defensive — should be unreachable for START_CLAIM_FIELD_KEYS.
    return empty_field(key, "UNKNOWN", value=None, reason_code="unclassified")


def classification_map(result: PrefillResult) -> dict[str, FieldClass]:
    return {f["field_key"]: f["classification"] for f in result.get("fields") or []}


def founder_shorthand_map(result: PrefillResult) -> dict[str, str]:
    return {f["field_key"]: f["founder_shorthand"] for f in result.get("fields") or []}
