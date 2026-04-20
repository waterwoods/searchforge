"""
Thin Stage-1 service-record read abstraction.

Runtime reads use case_truth_repository (JSON default; optional Postgres-primary reads).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.fiqa_api.inbox_triage.case_truth_repository import (
    get_case_for_read,
    list_all_cases_for_read,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR

_ADD_CAR_SIGNAL_FIELDS = {
    "year",
    "make_model",
    "vin",
    "zip",
    "delivery_date",
    "primary_driver",
}


@dataclass(frozen=True)
class ServiceRecordSnapshot:
    case_id: str
    formal_submitted_at: str
    customer_name: str
    customer_phone: str
    lifecycle_status: str
    quote_ready_status: str
    still_needed_fields: list[str]
    collected_fields: list[str]
    service_type: str = ""
    vehicle_key: str = ""
    # Explicit Stage-1 lane when set on JSON (e.g. add_car); empty when legacy/unlabeled.
    service_lane: str = ""
    source: str = "json_case_store"


def _to_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def _is_add_car_case(case: dict[str, Any]) -> bool:
    collected = set(_to_str_list(case.get("collected_fields")))
    still_needed = set(_to_str_list(case.get("still_needed_fields")))
    return bool((collected | still_needed) & _ADD_CAR_SIGNAL_FIELDS)


def _is_add_car_lane(case: dict[str, Any]) -> bool:
    """Prefer explicit service_lane; fall back to Add-Car field heuristics for legacy JSON."""
    lane = str(case.get("service_lane") or "").strip()
    if lane == SERVICE_LANE_ADD_CAR:
        return True
    if lane:
        return False
    return _is_add_car_case(case)


def _is_formally_submitted(case: dict[str, Any]) -> bool:
    return bool(str(case.get("formal_submitted_at") or "").strip())


def _to_snapshot(case: dict[str, Any]) -> ServiceRecordSnapshot:
    return ServiceRecordSnapshot(
        case_id=str(case.get("case_id") or "").strip(),
        formal_submitted_at=str(case.get("formal_submitted_at") or "").strip(),
        customer_name=str(case.get("customer_name") or "").strip(),
        customer_phone=str(case.get("customer_phone") or "").strip(),
        lifecycle_status=str(case.get("lifecycle_status") or "").strip(),
        quote_ready_status=str(case.get("quote_ready_status") or "").strip(),
        still_needed_fields=_to_str_list(case.get("still_needed_fields")),
        collected_fields=_to_str_list(case.get("collected_fields")),
        service_type=str(case.get("service_type") or "").strip(),
        vehicle_key=str(case.get("vehicle_key") or "").strip(),
        service_lane=str(case.get("service_lane") or "").strip(),
    )


class ServiceRecordReadRepository:
    """
    Thin read interface for Stage-1 service records.

    Reads go through case_truth_repository (JSON by default; Postgres when DB-primary flag is on).
    """

    def get_by_case_id(self, case_id: str) -> ServiceRecordSnapshot | None:
        case = get_case_for_read(case_id)
        if not case:
            return None
        return _to_snapshot(case)

    def list_formally_submitted_add_car(self) -> list[ServiceRecordSnapshot]:
        out: list[ServiceRecordSnapshot] = []
        for case in list_all_cases_for_read():
            if not _is_formally_submitted(case):
                continue
            if not _is_add_car_lane(case):
                continue
            snap = _to_snapshot(case)
            if not snap.case_id:
                continue
            out.append(snap)
        return out
