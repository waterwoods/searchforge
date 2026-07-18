"""P20 Capability 2 — deterministic missing-information projection.

Statuses are derived from authoritative fact records and workflow/admin state.
AI may suggest gaps but must not write confirmed status or transition state.
"""

from __future__ import annotations

from typing import Any

FACT_STATUS_MISSING = "missing"
FACT_STATUS_UNKNOWN = "unknown"
FACT_STATUS_SUPPLIED_UNCONFIRMED = "supplied_unconfirmed"
FACT_STATUS_CONFIRMED = "confirmed"
FACT_STATUS_NEEDS_CORRECTION = "needs_correction"
FACT_STATUS_NOT_APPLICABLE = "not_applicable"

ALL_FACT_STATUSES = frozenset(
    {
        FACT_STATUS_MISSING,
        FACT_STATUS_UNKNOWN,
        FACT_STATUS_SUPPLIED_UNCONFIRMED,
        FACT_STATUS_CONFIRMED,
        FACT_STATUS_NEEDS_CORRECTION,
        FACT_STATUS_NOT_APPLICABLE,
    }
)

# Business Contract classes (SSOT: docs/product/p20_business_contract.md).
BUSINESS_CLASS_MUST_HAVE = "must_have"
BUSINESS_CLASS_NICE_TO_HAVE = "nice_to_have"
BUSINESS_CLASS_REQUEST_MORE = "request_more"

# Checklist fields for Cap2 Missing Information + Request More.
# Must Have = accident understanding (opens Broker Review).
# Nice to Have = helpful on initial intake; never blocks review.
# Request More = broker-ordered follow-up (VIN / docs / evidence).
CHECKLIST_FIELDS: tuple[dict[str, str], ...] = (
    {
        "field_key": "accident_description",
        "label": "Accident description",
        "customer_label": "What happened",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_MUST_HAVE,
        "severity": "critical",
    },
    {
        "field_key": "accident_datetime",
        "label": "Accident date",
        "customer_label": "When it happened",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_MUST_HAVE,
        "severity": "critical",
    },
    {
        "field_key": "accident_location",
        "label": "Accident location",
        "customer_label": "Where it happened",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_MUST_HAVE,
        "severity": "critical",
    },
    {
        "field_key": "injury_status",
        "label": "Anyone injured?",
        "customer_label": "Was anyone injured?",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_MUST_HAVE,
        "severity": "critical",
    },
    {
        "field_key": "photo_evidence",
        "label": "Photos (optional)",
        "customer_label": "Accident / vehicle photos",
        "item_type": "photo_evidence",
        "business_class": BUSINESS_CLASS_NICE_TO_HAVE,
        "severity": "optional",
    },
    {
        "field_key": "vin",
        "label": "VIN",
        "customer_label": "Vehicle VIN",
        "item_type": "vin",
        "business_class": BUSINESS_CLASS_REQUEST_MORE,
        "severity": "optional",
    },
    {
        "field_key": "vehicle_information",
        "label": "Vehicle information",
        "customer_label": "Vehicle year / make / model",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_REQUEST_MORE,
        "severity": "optional",
    },
    {
        "field_key": "policy_or_insurance_card",
        "label": "Insurance card",
        "customer_label": "Insurance card photo",
        "item_type": "policy_or_insurance_card",
        "business_class": BUSINESS_CLASS_REQUEST_MORE,
        "severity": "optional",
    },
)

_FIELD_KEYS = frozenset(item["field_key"] for item in CHECKLIST_FIELDS)

# Production Request More items with complete customer submission support.
# VIN = fact submit; policy_or_insurance_card = evidence submit (attachment_id).
MVP_SENDABLE_ITEM_TYPES = frozenset({"vin", "policy_or_insurance_card"})


def is_mvp_sendable_item_type(item_type: str) -> bool:
    return str(item_type or "").strip().lower() in MVP_SENDABLE_ITEM_TYPES


def list_unsupported_send_item_labels(items: list[dict[str, Any]]) -> list[str]:
    """Human labels for draft items that cannot be sent in the current MVP."""
    unsupported: list[str] = []
    for raw in items or []:
        item = raw if isinstance(raw, dict) else {}
        item_type = str(item.get("item_type") or "").strip().lower()
        if is_mvp_sendable_item_type(item_type):
            continue
        label = str(item.get("label") or item.get("customer_label") or item_type).strip()
        unsupported.append(label or item_type)
    return unsupported

_VIN_FACT_KEYS = ("vin", "vehicle_vin", "own_vehicle_vin")
_VEHICLE_FACT_KEYS = (
    "vehicle_year",
    "vehicle_make",
    "vehicle_model",
    "primary_vehicle_summary",
    "vehicle_information",
    "own_vehicle_info",
)
_POLICY_FACT_KEYS = ("policy_number", "insurance_card", "policy_or_insurance_card")
_ACCIDENT_FACT_KEYS = ("accident_description", "accident_summary")
_DATETIME_FACT_KEYS = ("accident_datetime", "accident_date", "accident_time")
_LOCATION_FACT_KEYS = ("accident_location",)
_INJURY_FACT_KEYS = ("injury_status", "anyone_injured")


def _str(value: Any) -> str:
    return str(value or "").strip()


def _normalize_status(raw: Any) -> str | None:
    status = _str(raw).lower().replace(" ", "_").replace("-", "_")
    if status == "supplied_but_unconfirmed":
        status = FACT_STATUS_SUPPLIED_UNCONFIRMED
    if status == "disputed":
        status = FACT_STATUS_NEEDS_CORRECTION
    if status in ALL_FACT_STATUSES:
        return status
    return None


def _first_nonempty(facts: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = _str(facts.get(key))
        if value:
            return value
    return None


def _vehicle_value(facts: dict[str, Any]) -> str | None:
    direct = _first_nonempty(
        facts,
        ("vehicle_information", "primary_vehicle_summary", "own_vehicle_info"),
    )
    if direct:
        return direct
    parts = [
        _str(facts.get("vehicle_year")),
        _str(facts.get("vehicle_make")),
        _str(facts.get("vehicle_model")),
    ]
    joined = " ".join(p for p in parts if p).strip()
    return joined or None


def _photo_evidence_present(case: dict[str, Any], facts: dict[str, Any]) -> bool:
    if _str(facts.get("photo_evidence")):
        return True
    attachments = case.get("case_attachments")
    if isinstance(attachments, list) and any(isinstance(a, dict) and a for a in attachments):
        return True
    slots = case.get("claim_attachment_slots")
    if isinstance(slots, dict):
        for slot in slots.values():
            if not isinstance(slot, dict):
                continue
            status = _str(slot.get("status")).lower()
            if status in {"received", "needs_retake"}:
                return True
            ids = slot.get("attachment_ids")
            if isinstance(ids, list) and any(_str(x) for x in ids):
                return True
    return False


def seed_fact_records_from_case(case: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Build initial fact records from case known_facts / attachments (no confirmed writes)."""
    case = case if isinstance(case, dict) else {}
    facts = case.get("known_facts") if isinstance(case.get("known_facts"), dict) else {}
    out: dict[str, dict[str, Any]] = {}
    for meta in CHECKLIST_FIELDS:
        key = meta["field_key"]
        value: str | None = None
        if key == "vin":
            value = _first_nonempty(facts, _VIN_FACT_KEYS)
        elif key == "vehicle_information":
            value = _vehicle_value(facts)
        elif key == "policy_or_insurance_card":
            value = _first_nonempty(facts, _POLICY_FACT_KEYS) or _str(case.get("policy_number")) or None
        elif key == "accident_description":
            value = _first_nonempty(facts, _ACCIDENT_FACT_KEYS)
        elif key == "accident_datetime":
            value = _first_nonempty(facts, _DATETIME_FACT_KEYS)
        elif key == "accident_location":
            value = _first_nonempty(facts, _LOCATION_FACT_KEYS)
        elif key == "injury_status":
            value = _first_nonempty(facts, _INJURY_FACT_KEYS)
        elif key == "photo_evidence":
            value = "received" if _photo_evidence_present(case, facts) else None
        if value:
            out[key] = {
                "field_key": key,
                "status": FACT_STATUS_SUPPLIED_UNCONFIRMED,
                "value": value,
                "previous_value": None,
                "reason": "",
                "source": "case_seed",
            }
        else:
            out[key] = {
                "field_key": key,
                "status": FACT_STATUS_MISSING,
                "value": None,
                "previous_value": None,
                "reason": "",
                "source": "case_seed",
            }
    return out


def merge_fact_records(
    existing: dict[str, Any] | None,
    *,
    case: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Merge stored fact records with deterministic seed without demoting confirmed facts."""
    seeded = seed_fact_records_from_case(case)
    stored = existing if isinstance(existing, dict) else {}
    merged: dict[str, dict[str, Any]] = {}
    for key in _FIELD_KEYS:
        base = dict(seeded.get(key) or {})
        raw = stored.get(key)
        if isinstance(raw, dict):
            status = _normalize_status(raw.get("status"))
            if status:
                base["status"] = status
            if "value" in raw:
                base["value"] = raw.get("value")
            if "previous_value" in raw:
                base["previous_value"] = raw.get("previous_value")
            if raw.get("reason") is not None:
                base["reason"] = _str(raw.get("reason"))
            if raw.get("source"):
                base["source"] = _str(raw.get("source"))
            # Never classify an existing confirmed value as missing.
            if status == FACT_STATUS_CONFIRMED and not _str(base.get("value")):
                base["value"] = _str(seeded.get(key, {}).get("value")) or base.get("value")
            if status == FACT_STATUS_CONFIRMED:
                base["status"] = FACT_STATUS_CONFIRMED
        base["field_key"] = key
        merged[key] = base
    return merged


def derive_missing_information_checklist(
    fact_records: dict[str, Any] | None,
    *,
    case: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Authoritative checklist projection for broker review."""
    records = merge_fact_records(fact_records, case=case)
    items: list[dict[str, Any]] = []
    for meta in CHECKLIST_FIELDS:
        key = meta["field_key"]
        record = records[key]
        status = _normalize_status(record.get("status")) or FACT_STATUS_MISSING
        # Confirmed and N/A are never default request suggestions.
        # Missing / needs_correction are suggested; unconfirmed suggests confirmation mode.
        if status in {FACT_STATUS_CONFIRMED, FACT_STATUS_NOT_APPLICABLE}:
            suggested = False
            request_mode = "none"
        elif status == FACT_STATUS_SUPPLIED_UNCONFIRMED:
            suggested = True
            request_mode = "request_confirmation"
        elif status == FACT_STATUS_NEEDS_CORRECTION:
            suggested = True
            request_mode = "request_correction"
        elif status == FACT_STATUS_MISSING:
            suggested = True
            request_mode = "request_missing"
        elif status == FACT_STATUS_UNKNOWN:
            suggested = True
            request_mode = "request_follow_up"
        else:
            suggested = False
            request_mode = "none"
        mvp_sendable = is_mvp_sendable_item_type(meta["item_type"])
        business_class = meta.get("business_class") or BUSINESS_CLASS_REQUEST_MORE
        # Request More suggestions only — Must Have / Nice to Have are intake, not sendable draft seeds.
        suggest_for_request = (
            suggested
            and mvp_sendable
            and business_class == BUSINESS_CLASS_REQUEST_MORE
        )
        items.append(
            {
                "field_key": key,
                "label": meta["label"],
                "customer_label": meta["customer_label"],
                "item_type": meta["item_type"],
                "business_class": business_class,
                "severity": meta["severity"],
                "status": status,
                "value": record.get("value"),
                "previous_value": record.get("previous_value"),
                "reason": _str(record.get("reason")),
                "suggested_for_request": suggest_for_request,
                "request_mode": request_mode,
                "mvp_sendable": mvp_sendable,
                "is_authoritative_fact": status
                in {
                    FACT_STATUS_CONFIRMED,
                    FACT_STATUS_SUPPLIED_UNCONFIRMED,
                    FACT_STATUS_NEEDS_CORRECTION,
                },
            }
        )
    return items


def apply_fact_status_update(
    fact_records: dict[str, Any] | None,
    *,
    field_key: str,
    status: str,
    reason: str = "",
    value: Any = None,
    preserve_previous: bool = True,
) -> dict[str, dict[str, Any]]:
    """Append-safe status update. Confirmed values are never silently deleted."""
    key = _str(field_key)
    if key not in _FIELD_KEYS:
        raise ValueError("unsupported_checklist_field")
    new_status = _normalize_status(status)
    if not new_status:
        raise ValueError("invalid_fact_status")
    merged = merge_fact_records(fact_records)
    current = dict(merged[key])
    current_value = current.get("value")
    if new_status == FACT_STATUS_NEEDS_CORRECTION and preserve_previous:
        if current_value is not None and _str(current_value):
            current["previous_value"] = current_value
        if value is not None:
            current["value"] = value
    elif new_status == FACT_STATUS_NOT_APPLICABLE:
        if not _str(reason):
            raise ValueError("not_applicable_reason_required")
        # Keep prior value for audit; do not wipe confirmed history.
        if current_value is not None and _str(current_value) and current.get("previous_value") is None:
            current["previous_value"] = current_value
    elif value is not None:
        current["value"] = value
    if new_status == FACT_STATUS_MISSING and _normalize_status(current.get("status")) == FACT_STATUS_CONFIRMED:
        raise ValueError("confirmed_fact_cannot_be_marked_missing")
    current["status"] = new_status
    current["reason"] = _str(reason)
    current["source"] = "broker_command"
    current["field_key"] = key
    merged[key] = current
    return merged
