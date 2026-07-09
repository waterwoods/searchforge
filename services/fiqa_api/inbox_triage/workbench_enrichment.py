"""
Enrich case list payloads for the office workbench: lane kind + Postgres mirror glance.

When DB-primary reads are off, JSON case_store is authoritative for case payloads; PG fields are observability. When DB-primary reads are on, list payloads are already DB-hydrated; mirror compare remains useful for drift checks.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from services.fiqa_api.db.service_record_settings import service_record_database_url
from services.fiqa_api.inbox_triage.claim_workbench_display import (
    build_wecom_media_intake_display_status,
    build_wecom_media_intake_display_title,
    enrich_claim_for_workbench,
    is_claim_broker_done,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_ADD_CAR,
    SERVICE_LANE_WECOM_MEDIA_INTAKE,
)

# P19H-3f-1c — lanes that are raw inbound only; never broker business queue by default.
_BROKER_QUEUE_EXCLUDED_LANES: frozenset[str] = frozenset({SERVICE_LANE_WECOM_MEDIA_INTAKE})


def is_raw_inbound_case(case: dict[str, Any]) -> bool:
    """True when case is pre-Start-Ceremony technical buffer, not broker work."""
    lane = str(case.get("service_lane") or "").strip()
    return lane in _BROKER_QUEUE_EXCLUDED_LANES


def is_broker_active_queue_case(case: dict[str, Any]) -> bool:
    """Default broker queue: exclude raw inbound and broker-done Claim cases."""
    if is_raw_inbound_case(case):
        return False
    lane = str(case.get("service_lane") or "").strip().lower()
    if lane == SERVICE_LANE_CLAIM and is_claim_broker_done(case):
        return False
    return True


def filter_broker_workbench_cases(
    cases: list[dict[str, Any]],
    *,
    include_raw_inbound: bool = False,
) -> list[dict[str, Any]]:
    """Default Workbench list excludes raw inbound (wecom_media_intake) and done Claims."""
    if include_raw_inbound:
        return cases
    return [c for c in cases if is_broker_active_queue_case(c)]
from services.fiqa_api.inbox_triage.service_record_consistency import compare_snapshot_with_pg
from services.fiqa_api.inbox_triage.service_record_read import _is_add_car_lane, _to_snapshot
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def enrich_cases_for_workbench(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not cases:
        return []
    ids = [str(c.get("case_id") or "").strip() for c in cases if c.get("case_id")]
    pg_map: dict[str, dict[str, Any]] = {}
    db_url = service_record_database_url()
    if db_url and ids:
        try:
            from services.fiqa_api.db.service_record_repository import fetch_service_records

            pg_map = fetch_service_records(ids)
        except Exception:
            logger.exception(
                "UNIFIED_INTAKE_DB_OBS signal=PG_FETCH_FOR_WORKBENCH_FAIL case_id_count=%s",
                len(ids),
            )
            pg_map = {}

    out: list[dict[str, Any]] = []
    for c in cases:
        row = enrich_claim_for_workbench(dict(c))
        lane = str(c.get("service_lane") or "").strip()
        if lane == SERVICE_LANE_WECOM_MEDIA_INTAKE:
            row["display_title"] = build_wecom_media_intake_display_title()
            row["display_status"] = build_wecom_media_intake_display_status(c)
            row["workbench_lane_kind"] = "raw_inbound"
        elif lane == SERVICE_LANE_ADD_CAR:
            row["workbench_lane_kind"] = "explicit"
        elif lane == SERVICE_LANE_CLAIM:
            row["workbench_lane_kind"] = "explicit"
        elif _is_add_car_lane(c):
            row["workbench_lane_kind"] = "legacy"
        else:
            row["workbench_lane_kind"] = "other"

        if not db_url:
            row["pg_mirror_state"] = "unknown"
        else:
            cid = str(c.get("case_id") or "").strip()
            snap = _to_snapshot(c) if cid else None
            pg_row = pg_map.get(cid) if cid else None
            if snap is None or not snap.case_id:
                row["pg_mirror_state"] = "unknown"
            else:
                mismatches = compare_snapshot_with_pg(snap, pg_row)
                if pg_row is None:
                    row["pg_mirror_state"] = "pg_missing"
                elif mismatches:
                    row["pg_mirror_state"] = "mismatch"
                else:
                    row["pg_mirror_state"] = "mirrored"
        out.append(row)
    return out
