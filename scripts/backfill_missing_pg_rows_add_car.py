#!/usr/bin/env python3
"""
One-off backfill for missing PG mirror rows on formally-submitted Add-Car cases.

Scope is intentionally narrow:
- loads case payloads via case_truth_repository (Postgres-first when DB-primary reads are on)
- only explicit service_lane=add_car cases are considered
- only cases with missing Postgres row are inserted
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from services.fiqa_api.db.service_record_repository import fetch_service_records, persist_new_case
from services.fiqa_api.db.service_record_settings import (
    service_record_database_url,
    service_record_dual_write_enabled,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
from services.fiqa_api.inbox_triage.service_record_read import ServiceRecordReadRepository


def _is_explicit_add_car(snap: Any) -> bool:
    return (snap.service_lane or "").strip() == "add_car"


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill missing PG rows for explicit Add-Car formal cases")
    ap.add_argument("--apply", action="store_true", help="Execute inserts (default is dry-run)")
    args = ap.parse_args()

    summary: dict[str, Any] = {
        "scope": "backfill_missing_pg_rows_explicit_add_car",
        "dual_write_enabled": service_record_dual_write_enabled(),
        "database_configured": bool(service_record_database_url()),
        "mode": "apply" if args.apply else "dry_run",
    }
    if not service_record_database_url():
        summary["status"] = "aborted_no_database_url"
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1

    repo = ServiceRecordReadRepository()
    snapshots = [s for s in repo.list_formally_submitted_add_car() if _is_explicit_add_car(s)]
    case_ids = [s.case_id for s in snapshots]
    pg_map = fetch_service_records(case_ids)
    missing_case_ids = [cid for cid in case_ids if cid not in pg_map]

    summary["explicit_add_car_cases"] = len(case_ids)
    summary["missing_postgres_row_count"] = len(missing_case_ids)
    summary["missing_case_ids"] = missing_case_ids

    inserted: list[str] = []
    failed: list[dict[str, str]] = []
    if args.apply:
        for cid in missing_case_ids:
            case = get_case_for_read(cid)
            if not case:
                failed.append({"case_id": cid, "error": "missing_case_payload"})
                continue
            try:
                persist_new_case(case)
                inserted.append(cid)
            except Exception as exc:  # noqa: BLE001
                failed.append({"case_id": cid, "error": str(exc)})

    summary["inserted_count"] = len(inserted)
    summary["inserted_case_ids"] = inserted
    summary["failed_count"] = len(failed)
    summary["failed"] = failed
    summary["status"] = "ok" if not failed else "warn_partial_failure"
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
