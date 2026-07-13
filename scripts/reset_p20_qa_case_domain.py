#!/usr/bin/env python3
"""
P20 Track C — controlled QA Case-domain reset (Cloud SQL SSOT).

Deletes synthetic Case / Claim / Workbench / inbox pipeline rows only.
Preserves database instance, schema, migrations, and application configuration.

Usage:
  PYTHONPATH=. python3 scripts/reset_p20_qa_case_domain.py --qa
  PYTHONPATH=. python3 scripts/reset_p20_qa_case_domain.py --qa --dry-run
  PYTHONPATH=. python3 scripts/reset_p20_qa_case_domain.py --local

Never logs credentials or customer content.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ROLLBACK_DIR = Path.home() / ".searchforge_rollback"

_CASE_DOMAIN_TABLES = (
    "service_records",
    "record_messages",
    "structured_record_data",
    "state_history",
    "office_actions",
    "intake_sessions",
    "wecom_inbox_events",
    "wecom_message_processed",
    "wecom_reply_outbox",
    "wecom_sync_cursors",
)

_LABEL_SQL = """
SELECT
  COUNT(*) FILTER (
    WHERE COALESCE(extra->>'workbench_test', 'false') IN ('true', 't', '1')
  ) AS workbench_test,
  COUNT(*) FILTER (WHERE COALESCE(extra->>'demo_name', '') <> '') AS has_demo_name,
  COUNT(*) FILTER (WHERE client_id IS NOT NULL AND TRIM(client_id) <> '') AS has_client_id
FROM service_records
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _count_table(cur: Any, table: str) -> int:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return int(cur.fetchone()[0] or 0)
    except Exception:
        return -1


def _snapshot_counts_postgres() -> dict[str, Any]:
    from services.fiqa_api.db.service_record_repository import service_record_connection

    out: dict[str, Any] = {"tables": {}, "labels": {}}
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            for table in _CASE_DOMAIN_TABLES:
                out["tables"][table] = _count_table(cur, table)
            try:
                cur.execute(_LABEL_SQL)
                row = cur.fetchone()
                out["labels"] = {
                    "workbench_test": int(row[0] or 0),
                    "demo_name": int(row[1] or 0),
                    "has_client_id": int(row[2] or 0),
                }
            except Exception:
                out["labels"] = {}
    return out


def _snapshot_counts_local() -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.case_store import count_stored_cases, list_all_cases

    cases = list_all_cases()
    workbench_test = sum(1 for c in cases if c.get("workbench_test"))
    demo_name = sum(
        1 for c in cases if str((c.get("demo_name") or c.get("extra", {}).get("demo_name") or "")).strip()
    )
    has_client_id = sum(1 for c in cases if str(c.get("client_id") or "").strip())
    return {
        "tables": {"unified_intake_cases_json": count_stored_cases()},
        "labels": {
            "workbench_test": workbench_test,
            "demo_name": demo_name,
            "has_client_id": has_client_id,
        },
    }


def save_rollback_snapshot(target: str, phase: str) -> Path:
    _ROLLBACK_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _ROLLBACK_DIR / f"p20_track_c_qa_reset_{target}_{phase}_{ts}.json"
    payload = {
        "timestamp_utc": _utc_now(),
        "phase": phase,
        "target": target,
        "counts": _snapshot_counts_postgres() if target == "qa" else _snapshot_counts_local(),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[snapshot] {path}")
    return path


def purge_postgres_case_domain(*, dry_run: bool) -> dict[str, int]:
    from services.fiqa_api.db.service_record_repository import purge_case_domain_data

    return purge_case_domain_data(dry_run=dry_run)


def purge_local_json(*, dry_run: bool) -> int:
    from services.fiqa_api.inbox_triage.case_store import list_all_cases
    from services.fiqa_api.inbox_triage.case_store import delete_case

    removed = 0
    for case in list_all_cases():
        cid = str(case.get("case_id") or "").strip()
        if not cid:
            continue
        if dry_run:
            print(f"[DRY-RUN] Would remove local case {cid}")
        elif delete_case(cid):
            removed += 1
    return removed


def _configure_qa() -> None:
    from scripts.demo_db_resolve import apply_qa_postgres_env

    ident = apply_qa_postgres_env(for_write=True)
    print(f"[INFO] QA Postgres: {ident.masked()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="P20 Track C QA case-domain reset")
    parser.add_argument("--qa", "--cloud", action="store_true", help="GCP Cloud SQL (QA SSOT)")
    parser.add_argument("--local", action="store_true", help="Local JSON case store only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target = "qa" if args.qa else "local"
    if args.local:
        target = "local"

    print("==========================================")
    print(f"P20 Track C QA Case-Domain Reset (target={target})")
    print("==========================================")

    if target == "qa":
        _configure_qa()

    pre = save_rollback_snapshot(target, "pre")

    if target == "qa":
        counts = purge_postgres_case_domain(dry_run=args.dry_run)
        for table, n in counts.items():
            print(f"[purge] {table}: {n}")
    else:
        n = purge_local_json(dry_run=args.dry_run)
        print(f"[purge] local cases removed: {n}")

    if not args.dry_run:
        post = save_rollback_snapshot(target, "post")
        print(f"[OK] Rollback metadata: pre={pre.name} post={post.name}")
    else:
        print("[DRY-RUN] No mutation performed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
