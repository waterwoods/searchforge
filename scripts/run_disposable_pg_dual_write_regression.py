#!/usr/bin/env python3
"""
Disposable Postgres + dual-write regression harness for Unified Intake (Stage 1).

Goals:
  - Apply stage1_service_record.sql without requiring psql (uses psycopg).
  - Run the high-risk Add-Car battery with JSON persistence + dual-write.
  - Emit row counts and PASS/FAIL against minimum expectations.

Usage (local disposable DB example):
  docker run -d --rm --name sf_pg_regress -e POSTGRES_PASSWORD=sprint -e POSTGRES_DB=sf_regress \\
    -p 54339:5432 postgres:16-alpine
  export SERVICE_RECORD_DATABASE_URL=postgresql://postgres:sprint@127.0.0.1:54339/sf_regress
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_disposable_pg_dual_write_regression.py --apply-schema

Env:
  SERVICE_RECORD_DATABASE_URL or DATABASE_URL — required for --apply-schema and verification.
  UNIFIED_INTAKE_PG_DUAL_WRITE — set to 1 by this script during the battery subprocess.

Exit codes:
  0 — checks passed
  1 — connection / SQL / battery / count failure
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SQL_REL = Path("services/fiqa_api/db/schema/stage1_service_record.sql")


def _database_url(explicit: str) -> str:
    u = (explicit or "").strip() or (os.getenv("SERVICE_RECORD_DATABASE_URL") or "").strip() or (
        os.getenv("DATABASE_URL") or ""
    ).strip()
    if not u:
        raise SystemExit("Set SERVICE_RECORD_DATABASE_URL or DATABASE_URL, or pass --database-url")
    return u


def _strip_sql_comments_apply(conn: object) -> None:
    import psycopg

    sql_path = REPO / SQL_REL
    raw = sql_path.read_text(encoding="utf-8")
    lines: list[str] = []
    for line in raw.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    blob = "\n".join(lines)
    statements = [s.strip() for s in blob.split(";") if s.strip()]
    if not statements:
        raise RuntimeError(f"no SQL statements parsed from {sql_path}")
    with conn.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)


def _apply_schema(url: str) -> None:
    import psycopg

    conn = psycopg.connect(url, connect_timeout=15, autocommit=True)
    try:
        _strip_sql_comments_apply(conn)
    finally:
        conn.close()


def _fetch_counts(url: str) -> dict[str, int]:
    import psycopg

    conn = psycopg.connect(url, connect_timeout=15)
    try:
        with conn.cursor() as cur:
            out: dict[str, int] = {}
            for table in (
                "service_records",
                "structured_record_data",
                "record_messages",
                "state_history",
            ):
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                row = cur.fetchone()
                out[table] = int(row[0]) if row else 0
            return out
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="Disposable Postgres dual-write regression harness")
    ap.add_argument("--database-url", default="", help="Postgres URL (else env SERVICE_RECORD_DATABASE_URL / DATABASE_URL)")
    ap.add_argument(
        "--apply-schema",
        action="store_true",
        help=f"Apply {SQL_REL} (idempotent CREATE IF NOT EXISTS)",
    )
    ap.add_argument(
        "--min-service-records",
        type=int,
        default=16,
        help="Minimum service_records rows after battery (default: 16 high-risk scenarios)",
    )
    ap.add_argument(
        "--battery-script",
        default=str(REPO / "scripts/run_high_risk_add_car_pg_stage2_sprint_battery.py"),
        help="Battery script path",
    )
    args = ap.parse_args()

    url = _database_url(args.database_url)
    os.environ["SERVICE_RECORD_DATABASE_URL"] = url

    if args.apply_schema:
        print("Applying Stage 1 schema via psycopg…")
        try:
            _apply_schema(url)
        except Exception as e:
            print(f"FAIL schema apply: {e}", file=sys.stderr)
            return 1
        print("Schema apply OK.")

    cases_fd, cases_path = tempfile.mkstemp(prefix="sf_pg_regress_", suffix=".json")
    os.close(cases_fd)
    Path(cases_path).write_text('{"cases": []}\n', encoding="utf-8")

    env = os.environ.copy()
    env["LLM_GENERATION_ENABLED"] = "0"
    env["PYTHONPATH"] = str(REPO)
    env["UNIFIED_INTAKE_PG_DUAL_WRITE"] = "1"
    env["UNIFIED_INTAKE_CASES_PATH"] = cases_path
    env["SERVICE_RECORD_DATABASE_URL"] = url

    bat = Path(args.battery_script)
    if not bat.is_file():
        print(f"FAIL battery script missing: {bat}", file=sys.stderr)
        return 1

    print(f"Running battery: {bat.name} --persist-pg …")
    proc = subprocess.run(
        [sys.executable, str(bat), "--persist-pg", "--cases-json", cases_path],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "", file=sys.stderr)
        print(f"FAIL battery exit {proc.returncode}", file=sys.stderr)
        return 1

    try:
        counts = _fetch_counts(url)
    except Exception as e:
        print(f"FAIL count query: {e}", file=sys.stderr)
        return 1

    print(json.dumps({"postgres_row_counts": counts}, indent=2))
    sr = counts.get("service_records", 0)
    if sr < args.min_service_records:
        print(
            f"FAIL expected at least {args.min_service_records} service_records, got {sr}",
            file=sys.stderr,
        )
        return 1

    print(
        f"PASS dual-write regression (service_records={sr}, "
        f"messages={counts.get('record_messages', 0)}, state_history={counts.get('state_history', 0)})"
    )
    try:
        Path(cases_path).unlink(missing_ok=True)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
