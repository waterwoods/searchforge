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
        "label": "事故经过",
        "customer_label": "事故经过",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_MUST_HAVE,
        "severity": "critical",
    },
    {
        "field_key": "accident_datetime",
        "label": "事故时间",
        "customer_label": "事故时间",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_MUST_HAVE,
        "severity": "critical",
    },
    {
        "field_key": "accident_location",
        "label": "事故地点",
        "customer_label": "事故地点",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_MUST_HAVE,
        "severity": "critical",
    },
    {
        "field_key": "injury_status",
        "label": "是否有人受伤",
        "customer_label": "是否有人受伤",
        "item_type": "free_text",
        "business_class": BUSINESS_CLASS_MUST_HAVE,
        "severity": "critical",
    },
    {
        "field_key": "photo_evidence",
        "label": "照片（可选）",
        "customer_label": "事故 / 车辆照片",
        "item_type": "photo_evidence",
        "business_class": BUSINESS_CLASS_NICE_TO_HAVE,
        "severity": "optional",
    },
    {
        "field_key": "vin",
        "label": "VIN",
        "customer_label": "车辆 VIN",
        "item_type": "vin",
        "business_class": BUSINESS_CLASS_REQUEST_MORE,
        "severity": "optional",
    },
    {
        "field_key": "vehicle_information",
        "label": "车辆信息",
        "customer_label": "车辆信息",
        "item_type": "vehicle_information",
        "business_class": BUSINESS_CLASS_REQUEST_MORE,
        "severity": "optional",
    },
    {
        "field_key": "policy_or_insurance_card",
        "label": "保险卡",
        "customer_label": "保险卡照片",
        "item_type": "policy_or_insurance_card",
        "business_class": BUSINESS_CLASS_REQUEST_MORE,
        "severity": "optional",
    },
)

_FIELD_KEYS = frozenset(item["field_key"] for item in CHECKLIST_FIELDS)

# Production Request More items with complete customer submission support.
# VIN / vehicle_information = fact submit via Claim Vehicle Identity;
# policy_or_insurance_card = evidence submit (attachment_id).
MVP_SENDABLE_ITEM_TYPES = frozenset({"vin", "vehicle_information", "policy_or_insurance_card"})


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


def fact_status_is_gap(status: str | None) -> bool:
    """True when the fact is genuinely absent or needs customer correction/follow-up.

    Supplied (even unconfirmed) and confirmed facts are not gaps — they must not
    appear under「仍缺信息」 / accident-gaps alerts.
    """
    normalized = _normalize_status(status) or FACT_STATUS_MISSING
    return normalized in {
        FACT_STATUS_MISSING,
        FACT_STATUS_UNKNOWN,
        FACT_STATUS_NEEDS_CORRECTION,
    }


def merge_fact_records(
    existing: dict[str, Any] | None,
    *,
    case: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Merge stored fact records with deterministic seed without demoting confirmed facts.

    Case ``known_facts`` (seed) remains the presence SSOT when the aggregate still
    says missing/empty after a later customer patch — prevents Brief vs checklist
    contradiction.
    """
    seeded = seed_fact_records_from_case(case)
    stored = existing if isinstance(existing, dict) else {}
    merged: dict[str, dict[str, Any]] = {}
    for key in _FIELD_KEYS:
        base = dict(seeded.get(key) or {})
        raw = stored.get(key)
        if isinstance(raw, dict):
            status = _normalize_status(raw.get("status"))
            stored_value = raw.get("value") if "value" in raw else None
            seed_value = _str(base.get("value"))
            stale_empty_gap = (
                (status is None or status in {FACT_STATUS_MISSING, FACT_STATUS_UNKNOWN})
                and not _str(stored_value)
                and bool(seed_value)
            )
            if not stale_empty_gap:
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
                    base["value"] = seed_value or base.get("value")
                if status == FACT_STATUS_CONFIRMED:
                    base["status"] = FACT_STATUS_CONFIRMED
            # else: keep seed (supplied_unconfirmed + case value)
        base["field_key"] = key
        merged[key] = base
    return merged


# Happy Path Loop 1 — Cap2 Must Have keys that gate "资料已齐" (Business Contract).
# Exactly the Cap2 must_have checklist fields; do not invent a parallel engine.
CAP2_MUST_HAVE_OFFICE_KEYS: frozenset[str] = frozenset(
    meta["field_key"]
    for meta in CHECKLIST_FIELDS
    if meta.get("business_class") == BUSINESS_CLASS_MUST_HAVE
)

OFFICE_MATERIALS_READY_SUGGESTION: str = "建议确认资料已齐"
OFFICE_MATERIALS_ACCEPT_CTA: str = "确认资料已齐"
EVENT_BROKER_OFFICE_MATERIALS_ACCEPTED: str = "broker_office_materials_accepted"
EVENT_BROKER_SUPPLEMENT_REVIEWED: str = "broker_supplement_reviewed"


def _checklist_from_case(case: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    if not isinstance(case, dict):
        return None
    raw = case.get("missing_information_checklist")
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    for proj_key in ("p20_case_intake_projection", "case_intake_projection"):
        proj = case.get(proj_key)
        if not isinstance(proj, dict):
            continue
        nested = proj.get("missing_information_checklist")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
    return None


def cap2_must_have_gaps_empty(
    case: dict[str, Any] | None = None,
    *,
    fact_records: dict[str, Any] | None = None,
    checklist: list[dict[str, Any]] | None = None,
) -> bool:
    """True when Cap2 Must Have fields have no gaps — sole Happy Path completeness gate.

    Uses ``derive_missing_information_checklist`` / Cap2 checklist rows only.
    Does not consult claim_state CLAIM_REQUIRED_FIELDS or Brief legacy missing_info.
    """
    items = checklist if isinstance(checklist, list) else _checklist_from_case(case)
    if items is None:
        stored = fact_records
        if stored is None and isinstance(case, dict):
            raw_fr = case.get("fact_records")
            stored = raw_fr if isinstance(raw_fr, dict) else None
        items = derive_missing_information_checklist(stored, case=case)
    for item in items:
        if not isinstance(item, dict):
            continue
        key = _str(item.get("field_key"))
        if key not in CAP2_MUST_HAVE_OFFICE_KEYS:
            continue
        business_class = _str(item.get("business_class")) or BUSINESS_CLASS_REQUEST_MORE
        if business_class != BUSINESS_CLASS_MUST_HAVE:
            continue
        if fact_status_is_gap(item.get("status")):
            return False
    return True


def _slice1_projection_of(case: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(case, dict):
        return None
    for key in ("p20_slice1_projection", "slice1_projection"):
        proj = case.get(key)
        if isinstance(proj, dict):
            return proj
    return None


def office_materials_request_more_block(
    case: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any]]:
    """Block office accept while Request More is unresolved or awaiting broker review.

    Returns ``(error_code, detail)`` when blocked, else ``(None, {})``.
    Does not cancel, close, or satisfy the Request More.
    """
    if not isinstance(case, dict):
        return None, {}

    proj = _slice1_projection_of(case) or {}
    ws = _str(proj.get("workflow_state")).lower()
    action = proj.get("customer_next_action")
    action = action if isinstance(action, dict) else {}
    action_type = _str(action.get("action_type")).lower()
    open_req = proj.get("open_request")
    open_req = open_req if isinstance(open_req, dict) else {}
    progress = open_req.get("progress") if isinstance(open_req.get("progress"), dict) else {}
    try:
        total = int(progress.get("total") or 0)
    except (TypeError, ValueError):
        total = 0
    try:
        satisfied = int(progress.get("satisfied") or 0)
    except (TypeError, ValueError):
        satisfied = 0

    unresolved_items: list[dict[str, Any]] = []
    items = open_req.get("items")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            st = _str(item.get("status")).lower()
            if st in {"", "active", "queued", "in_progress"}:
                unresolved_items.append(item)
    active_item = open_req.get("active_item")
    if isinstance(active_item, dict):
        st = _str(active_item.get("status")).lower()
        if st in {"", "active", "queued", "in_progress"}:
            if not any(
                _str(i.get("request_item_id")) == _str(active_item.get("request_item_id"))
                for i in unresolved_items
            ):
                unresolved_items.append(active_item)

    unresolved = bool(
        action_type in {"provide_fact", "provide_evidence"}
        or ws in {"broker_more_requested", "customer_continuing"}
        or unresolved_items
        or (total > 0 and satisfied < total)
    )
    if unresolved:
        return "office_materials_accept_blocked_open_request_more", {
            "error": "office_materials_accept_blocked_open_request_more",
            "reason": "unresolved_request_more",
            "workflow_state": ws or None,
            "open_request": {
                "request_id": open_req.get("request_id"),
                "status": open_req.get("status"),
                "progress": progress or None,
                "active_item": open_req.get("active_item"),
                "unresolved_item_ids": [
                    _str(i.get("request_item_id"))
                    for i in unresolved_items
                    if _str(i.get("request_item_id"))
                ],
                "unresolved_labels": [
                    _str(i.get("label") or i.get("item_type"))
                    for i in unresolved_items
                    if _str(i.get("label") or i.get("item_type"))
                ],
            },
            "message": (
                "Cannot confirm materials complete while an unresolved Request More "
                "is still open for the customer."
            ),
        }

    if ws == "broker_review_ready":
        return "office_materials_accept_blocked_awaiting_supplement_review", {
            "error": "office_materials_accept_blocked_awaiting_supplement_review",
            "reason": "awaiting_supplement_review",
            "workflow_state": ws,
            "open_request": {
                "request_id": open_req.get("request_id"),
                "status": open_req.get("status"),
                "progress": progress or None,
            },
            "message": (
                "Customer supplement is waiting for broker「已核对补充资料」"
                " before office acceptance."
            ),
        }

    return None, {}


def office_materials_accept_eligible(case: dict[str, Any] | None) -> bool:
    """Suggestion + CTA eligible: Cap2 complete, no open Request More, not accepted/History."""
    if not isinstance(case, dict):
        return False
    if str(case.get("office_materials_accepted_at") or "").strip():
        return False
    try:
        from services.fiqa_api.inbox_triage.case_close import case_is_closed_history

        if case_is_closed_history(case):
            return False
    except Exception:
        pass
    block_code, _detail = office_materials_request_more_block(case)
    if block_code:
        return False
    return cap2_must_have_gaps_empty(case)


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
        is_gap = fact_status_is_gap(status)
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
                "is_gap": is_gap,
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
