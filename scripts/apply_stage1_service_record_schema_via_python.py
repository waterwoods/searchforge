#!/usr/bin/env python3
"""
Apply the Stage-1 service-record schema to Postgres using psycopg.

This is a minimal fallback for environments where the `psql` client
is not available. It uses the same URL resolution as the runtime
code (SERVICE_RECORD_DATABASE_URL or DATABASE_URL) and executes the
existing SQL file:

    services/fiqa_api/db/schema/stage1_service_record.sql

Usage (from repo root):

    export SERVICE_RECORD_DATABASE_URL='postgresql://user:pass@host/db?sslmode=require'
    export UNIFIED_INTAKE_PG_DUAL_WRITE=1  # optional, for later smokes
    PYTHONPATH=. python3 scripts/apply_stage1_service_record_schema_via_python.py

This script is intentionally tiny and bounded; it does not implement
any migration framework and should only be used to apply the Stage-1
schema to a pre-provisioned database.
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

from services.fiqa_api.db.service_record_settings import service_record_database_url


def main() -> int:
    url = service_record_database_url()
    if not url:
        print(
            "ERROR: No service record database URL configured.\n"
            "Set SERVICE_RECORD_DATABASE_URL or DATABASE_URL in the environment.",
            file=sys.stderr,
        )
        return 1

    repo_root = Path(__file__).resolve().parent.parent
    sql_path = repo_root / "services" / "fiqa_api" / "db" / "schema" / "stage1_service_record.sql"
    if not sql_path.is_file():
        print(f"ERROR: Schema file not found at {sql_path}", file=sys.stderr)
        return 1

    sql_text = sql_path.read_text(encoding="utf-8")

    try:
        with psycopg.connect(url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_text)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Failed to apply Stage-1 schema via psycopg: {exc}", file=sys.stderr)
        return 1

    print(f"Stage-1 service-record schema applied successfully to database at: {url!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

