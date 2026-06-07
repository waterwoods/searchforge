"""
P16 Customer First — active add-car case lookup by phone (Rule 2 + Rule 7).
"""

from __future__ import annotations

import logging
from typing import Any

from services.fiqa_api.inbox_triage.case_binding import is_case_open_for_binding
from services.fiqa_api.inbox_triage.phone_normalization import normalize_phone_digits

logger = logging.getLogger(__name__)

_ADD_CAR_FIELD_IDS = frozenset(
    {"year", "make_model", "model", "zip", "delivery_date", "primary_driver", "vin"}
)


def _case_phone_digits(case: dict[str, Any]) -> str:
    return normalize_phone_digits(str(case.get("customer_phone") or ""))


def _looks_like_add_car(case: dict[str, Any]) -> bool:
    lane = str(case.get("service_lane") or "").strip().lower()
    if lane == "add_car":
        return True
    svc = str(case.get("service_type") or "").strip().lower()
    if "add" in svc and "car" in svc:
        return True
    if case.get("quote_ready_status"):
        return True
    fields = set(case.get("collected_fields") or []) | set(case.get("still_needed_fields") or [])
    if fields & _ADD_CAR_FIELD_IDS:
        return True
    cat = str(case.get("issue_category") or "").strip().lower()
    return cat in ("add_car_quote", "add_vehicle", "new_vehicle")


def is_customer_formal_submitted(case: dict[str, Any]) -> bool:
    """Saved draft ≠ submitted to office — mirrors customer UI `isFormalSubmissionToOfficeComplete`."""
    if _missing_fields_display(case):
        return False
    ls = str(case.get("lifecycle_status") or "").strip()
    if ls in ("handoff_pending", "collecting"):
        return False
    if str(case.get("formal_submitted_at") or "").strip():
        return True
    return ls in ("handed_off", "office_followup")


def _vehicle_display(case: dict[str, Any]) -> str:
    pvs = str(case.get("primary_vehicle_summary") or "").strip()
    if pvs:
        return pvs
    collected = case.get("collected_fields") or []
    still = case.get("still_needed_fields") or []
    # Lightweight fallback when summary not materialized
    if "year" in collected or "make_model" in collected:
        return "加车申请（车辆信息已部分填写）"
    if "year" in still or "make_model" in still or "vin" in still:
        return "加车申请（车辆信息待补充）"
    return "加车申请"


def _missing_fields_display(case: dict[str, Any]) -> list[str]:
    raw = [str(x).strip() for x in (case.get("still_needed_fields") or []) if str(x).strip()]
    return raw


CUSTOMER_CONTACT_STATES = (
    "waiting_for_customer",
    "office_reviewing",
    "broker_reviewing",
)

CUSTOMER_BUSINESS_STATES = (
    "awaiting_customer",
    "submitted_to_office",
    "office_processing",
    "closed",
)


def resolve_customer_contact_state(case: dict[str, Any]) -> str:
    """
    Map office coordination truth (waiting_on, still_needed, submit state) to
    customer-visible contact state — no SLA promises.
    """
    still = _missing_fields_display(case)
    waiting_on = str(case.get("waiting_on") or "none").strip().lower()
    submitted = is_customer_formal_submitted(case)
    lifecycle = str(case.get("lifecycle_status") or "").strip()

    if still or waiting_on == "client":
        return "waiting_for_customer"

    if waiting_on == "broker":
        return "broker_reviewing"

    if waiting_on in ("carrier", "underwriting"):
        return "office_reviewing"

    if submitted:
        if lifecycle in ("handed_off", "office_followup"):
            return "office_reviewing"
        if lifecycle == "handoff_pending":
            return "broker_reviewing"
        return "office_reviewing"

    return "waiting_for_customer"


def customer_status_label(case: dict[str, Any]) -> str:
    """Customer-facing submit dimension — Saved ≠ Submitted."""
    return "submitted_to_office" if is_customer_formal_submitted(case) else "saved_not_yet_submitted"


def resolve_customer_business_state(case: dict[str, Any]) -> str:
    """
    Single customer-visible business state (four states only).

    A awaiting_customer — collecting / gaps / formal submit not complete
    B submitted_to_office — formal submit done; office has record; not actively processing
    C office_processing — office_followup, broker/carrier review, waiting_on office
    D closed — broker closed case
    """
    st = str(case.get("case_status") or "new").strip().lower()
    if st == "closed":
        return "closed"

    if not is_customer_formal_submitted(case):
        return "awaiting_customer"

    lifecycle = str(case.get("lifecycle_status") or "").strip()
    waiting_on = str(case.get("waiting_on") or "none").strip().lower()

    if lifecycle == "office_followup":
        return "office_processing"
    if waiting_on in ("broker", "carrier", "underwriting"):
        return "office_processing"

    return "submitted_to_office"


def active_add_car_case_summary(case: dict[str, Any]) -> dict[str, Any]:
    """Customer-facing active-case card payload."""
    missing = _missing_fields_display(case)
    formal = is_customer_formal_submitted(case)
    contact_state = resolve_customer_contact_state(case)
    status_label = customer_status_label(case)
    business_state = resolve_customer_business_state(case)
    return {
        "case_id": str(case.get("case_id") or "").strip(),
        "vehicle_display": _vehicle_display(case),
        "missing_fields": missing,
        "missing_fields_display": missing,
        "is_formal_submitted": formal,
        "submit_state": "submitted" if formal else "not_yet",
        "business_state": business_state,
        "status_label": status_label,
        "contact_state": contact_state,
        "waiting_on": str(case.get("waiting_on") or "none").strip().lower() or "none",
        "primary_vehicle_summary": case.get("primary_vehicle_summary"),
        "still_needed_fields": missing,
        "lifecycle_status": case.get("lifecycle_status"),
        "formal_submitted_at": case.get("formal_submitted_at"),
        "customer_name": case.get("customer_name"),
        "updated_at": case.get("updated_at"),
    }


def find_active_add_car_case_by_phone(
    phone: str,
    cases: list[dict[str, Any]],
    *,
    client_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Return the single active add-car case for normalized phone, or None.

    Rule 7: at most one active case — if multiple match, newest updated_at wins (logged).
    """
    target = normalize_phone_digits(phone)
    if len(target) != 10:
        return None

    matches: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        if not is_case_open_for_binding(case):
            continue
        if not _looks_like_add_car(case):
            continue
        cid = str(case.get("client_id") or "").strip()
        if client_id and cid and cid != client_id.strip():
            continue
        if _case_phone_digits(case) != target:
            continue
        matches.append(case)

    if not matches:
        return None

    if len(matches) > 1:
        logger.warning(
            "active_case_lookup multiple_open_add_car phone_tail=%s count=%s — returning newest",
            target[-4:],
            len(matches),
        )

    matches.sort(key=lambda c: (str(c.get("updated_at") or ""), str(c.get("created_at") or "")), reverse=True)
    return matches[0]


def create_customer_first_add_car_draft(
    phone: str,
    *,
    customer_name: str | None = None,
    client_id: str | None = None,
    origin_session_id: str | None = None,
) -> dict[str, Any]:
    """
    Persist a collecting-phase add-car draft keyed by claimed phone (Phase 1 early claim).

    Raises ValueError when phone invalid or an active case already exists (Rule 7).
    """
    from services.fiqa_api.inbox_triage.case_store import save_case, update_case_customer
    from services.fiqa_api.inbox_triage.case_truth_repository import list_cases_for_phone_lookup
    from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR

    normalized = normalize_phone_digits(phone)
    if len(normalized) != 10:
        raise ValueError("invalid_phone")

    existing = find_active_add_car_case_by_phone(
        normalized,
        list_cases_for_phone_lookup(normalized, client_id=client_id),
        client_id=client_id,
    )
    if existing is not None:
        raise ValueError("active_case_exists")

    display_name = (customer_name or "").strip()
    triage_stub: dict[str, Any] = {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": False,
        "broker_next_step": "Customer started add-car from Customer First entry; collect vehicle details.",
        "client_prep": "",
        "client_reply_draft": "已开始加车申请。请继续填写车辆信息。",
        "handoff_ready": False,
        "lifecycle_status": "collecting",
        "collection_stage": "collecting",
        "collected_fields": [],
        "still_needed_fields": ["year", "make_model", "zip", "delivery_date", "primary_driver", "vin"],
        "quote_ready_status": "need_more",
        "service_type": "add_car",
        "extracted_contact_phone": normalized,
    }
    if display_name:
        triage_stub["extracted_contact_name"] = display_name

    saved = save_case(
        "[客户] 开始加车申请（Customer First 入口）",
        triage_stub,
        status="new",
        origin_session_id=origin_session_id,
        client_id=client_id,
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    cid = str(saved.get("case_id") or "").strip()
    if cid and display_name:
        patched = update_case_customer(cid, customer_name=display_name, customer_phone=normalized)
        if patched:
            saved = patched
    return saved
