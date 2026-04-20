#!/usr/bin/env python3
"""
Check JSON <-> Postgres consistency for formally submitted Add-Car cases.

Default behavior is report/warn mode (exit 0 even on mismatches).
Use --strict to fail on mismatches.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from services.fiqa_api.db.service_record_repository import fetch_service_records
from services.fiqa_api.db.service_record_settings import (
    service_record_database_url,
    service_record_dual_write_enabled,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.inbox_triage.service_record_consistency import compare_snapshot_with_pg
from services.fiqa_api.inbox_triage.service_record_read import ServiceRecordReadRepository


def _summarize_mismatch_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        for key in item.get("mismatches") or []:
            out[key] = out.get(key, 0) + 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Add-Car formal-submit JSON/PG consistency check")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero on any mismatch")
    ap.add_argument(
        "--explicit-lane-only",
        action="store_true",
        help="Report only explicit service_lane=add_car cases (ignore legacy heuristic cohort in output scope)",
    )
    args = ap.parse_args()

    repo = ServiceRecordReadRepository()
    snapshots = repo.list_formally_submitted_add_car()
    explicit_lane = [s for s in snapshots if (s.service_lane or "").strip()]
    legacy_heuristic_lane = [s for s in snapshots if not (s.service_lane or "").strip()]
    case_ids = [s.case_id for s in explicit_lane]

    snapshots_in_scope = explicit_lane if args.explicit_lane_only else snapshots
    summary: dict[str, Any] = {
        "scope": "add_car_formally_submitted_stage1",
        "service_lane": SERVICE_LANE_ADD_CAR,
        "lane_selection": (
            "explicit service_lane only"
            if args.explicit_lane_only
            else "explicit service_lane plus legacy Add-Car field heuristics (see service_record_read)"
        ),
        "json_source_of_truth": True,
        "total_formally_submitted_add_car_cases": len(snapshots),
        "explicit_lane_case_count": len(explicit_lane),
        "legacy_heuristic_lane_case_count": len(legacy_heuristic_lane),
        "legacy_heuristic_treatment": "historical_non_blocking_for_pg_mirror_health",
        "dual_write_enabled": service_record_dual_write_enabled(),
        "database_configured": bool(service_record_database_url()),
    }

    if not snapshots_in_scope:
        summary["status"] = "ok_no_cases"
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if not (service_record_dual_write_enabled() and service_record_database_url()):
        summary["status"] = "skipped_pg_consistency_check"
        summary["reason"] = "dual-write disabled or database not configured"
        summary["checked_case_count"] = len(explicit_lane)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if not explicit_lane:
        summary["status"] = "skipped_pg_consistency_check_no_explicit_lane_cases"
        summary["reason"] = "no explicit service_lane cases found; legacy heuristic cases are not expected to exist in Postgres"
        summary["cases_checked"] = [
            {"case_id": s.case_id, "service_lane": s.service_lane or "(legacy heuristic historical)"}
            for s in snapshots_in_scope[:40]
        ]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    pg_rows = fetch_service_records(case_ids)
    mismatched: list[dict[str, Any]] = []
    for snap in explicit_lane:
        mismatch_keys = compare_snapshot_with_pg(snap, pg_rows.get(snap.case_id))
        if mismatch_keys:
            mismatched.append({"case_id": snap.case_id, "mismatches": mismatch_keys})

    summary["status"] = "warn_mismatch" if mismatched else "ok_aligned"
    summary["checked_case_count"] = len(explicit_lane)
    summary["mismatch_count"] = len(mismatched)
    summary["mismatch_breakdown"] = _summarize_mismatch_counts(mismatched)
    summary["mismatches"] = mismatched[:50]
    summary["cases_checked"] = [
        {"case_id": s.case_id, "service_lane": s.service_lane or "(legacy heuristic historical)"}
        for s in snapshots_in_scope[:40]
    ]
    summary["legacy_examples"] = [s.case_id for s in legacy_heuristic_lane[:10]]
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.strict and mismatched:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
