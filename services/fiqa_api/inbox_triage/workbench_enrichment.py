"""
Enrich case list payloads for the office workbench: lane kind + Postgres mirror glance.

When DB-primary reads are off, JSON case_store is authoritative for case payloads; PG fields are observability. When DB-primary reads are on, list payloads are already DB-hydrated; mirror compare remains useful for drift checks.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from services.fiqa_api.db.service_record_settings import service_record_database_url
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.inbox_triage.service_record_consistency import compare_snapshot_with_pg
from services.fiqa_api.inbox_triage.service_record_read import ServiceRecordReadRepository, _is_add_car_lane


def enrich_cases_for_workbench(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not cases:
        return []
    repo = ServiceRecordReadRepository()
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
        row = dict(c)
        lane = str(c.get("service_lane") or "").strip()
        if lane == SERVICE_LANE_ADD_CAR:
            row["workbench_lane_kind"] = "explicit"
        elif _is_add_car_lane(c):
            row["workbench_lane_kind"] = "legacy"
        else:
            row["workbench_lane_kind"] = "other"

        if not db_url:
            row["pg_mirror_state"] = "unknown"
        else:
            cid = str(c.get("case_id") or "").strip()
            snap = repo.get_by_case_id(cid) if cid else None
            pg_row = pg_map.get(cid) if cid else None
            if snap is None:
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
