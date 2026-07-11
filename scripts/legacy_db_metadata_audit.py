#!/usr/bin/env python3
"""
Read-only metadata audit: legacy Neon vs GCP Cloud SQL (caseiq SSOT).

Prints counts, timestamps, and case-id deltas only — no customer content.
Performs no writes. Fails closed if a source cannot be resolved safely.

Usage:
  PYTHONPATH=. python3 scripts/legacy_db_metadata_audit.py
  PYTHONPATH=. python3 scripts/legacy_db_metadata_audit.py --json-out docs/evidence/legacy_db_audit.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator
from urllib.parse import urlparse

from scripts.demo_db_resolve import (
    LEGACY_NEON_SECRET,
    QA_CLOUD_SQL_SECRET,
    apply_qa_postgres_env,
    resolve_db_identity,
)

READONLY_SESSION_SQL = "SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY"


@contextmanager
def _pg_conn(url: str, *, readonly: bool) -> Generator[Any, None, None]:
    import psycopg

    conn = psycopg.connect(url, connect_timeout=15)
    try:
        if readonly:
            with conn.cursor() as cur:
                cur.execute(READONLY_SESSION_SQL)
        yield conn
    finally:
        conn.close()


def _resolve_urls() -> tuple[str, str, str, str]:
    neon_ident = resolve_db_identity("legacy-neon", for_write=False)
    qa_ident = resolve_db_identity("qa", for_write=False)

    neon_raw = os.environ.get("SERVICE_RECORD_DATABASE_URL") or ""
    if not neon_raw:
        from scripts.demo_db_resolve import _gcloud_secret

        neon_raw = _gcloud_secret(LEGACY_NEON_SECRET)
    qa_raw = os.environ.get("QA_SERVICE_RECORD_DATABASE_URL") or ""
    if not qa_raw:
        from scripts.demo_db_resolve import _gcloud_secret, _cloud_sql_public_ip, _rewrite_host

        qa_raw = _gcloud_secret(QA_CLOUD_SQL_SECRET)
        host = urlparse(qa_raw).hostname or ""
        if host.startswith("10."):
            qa_raw = _rewrite_host(qa_raw, _cloud_sql_public_ip())

    if "neon" not in (urlparse(neon_raw).hostname or "").lower():
        raise RuntimeError("legacy-neon source does not resolve to a Neon host — aborting")
    return neon_raw, qa_raw, neon_ident.masked(), qa_ident.masked()


def _table_names(conn: Any) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'service_records' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        return [str(r[0]) for r in cur.fetchall()]


def _audit_source(conn: Any, label: str) -> dict[str, Any]:
    out: dict[str, Any] = {"label": label}
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM service_records")
        out["service_records_count"] = int(cur.fetchone()[0] or 0)

        cur.execute(
            """
            SELECT MIN(created_at), MAX(created_at), MIN(updated_at), MAX(updated_at)
            FROM service_records
            """
        )
        row = cur.fetchone()
        out["created_at_min"] = row[0].isoformat() if row and row[0] else None
        out["created_at_max"] = row[1].isoformat() if row and row[1] else None
        out["updated_at_min"] = row[2].isoformat() if row and row[2] else None
        out["updated_at_max"] = row[3].isoformat() if row and row[3] else None

        cur.execute(
            """
            SELECT record_id::text FROM service_records ORDER BY updated_at DESC NULLS LAST LIMIT 5000
            """
        )
        out["case_ids_sample"] = [str(r[0]) for r in cur.fetchall() if r and r[0]]

        def _count_group(sql: str) -> list[dict[str, Any]]:
            cur.execute(sql)
            return [{"key": str(r[0] or "(null)"), "count": int(r[1])} for r in cur.fetchall()]

        out["by_workbench_test"] = _count_group(
            """
            SELECT COALESCE(extra->>'workbench_test', '(null)'), COUNT(*)
            FROM service_records GROUP BY 1 ORDER BY 2 DESC
            """
        )
        out["by_demo_name"] = _count_group(
            """
            SELECT COALESCE(NULLIF(TRIM(extra->>'demo_name'), ''), '(null)'), COUNT(*)
            FROM service_records GROUP BY 1 ORDER BY 2 DESC LIMIT 20
            """
        )
        out["by_qa_label"] = _count_group(
            """
            SELECT COALESCE(NULLIF(TRIM(extra->>'qa_label'), ''), '(null)'), COUNT(*)
            FROM service_records GROUP BY 1 ORDER BY 2 DESC LIMIT 20
            """
        )
        out["by_source_channel"] = _count_group(
            """
            SELECT COALESCE(NULLIF(TRIM(extra->>'source_channel'), ''), '(null)'), COUNT(*)
            FROM service_records GROUP BY 1 ORDER BY 2 DESC LIMIT 20
            """
        )
        out["by_claim_phase"] = _count_group(
            """
            SELECT COALESCE(NULLIF(TRIM(extra->>'claim_phase'), ''), '(null)'), COUNT(*)
            FROM service_records GROUP BY 1 ORDER BY 2 DESC LIMIT 20
            """
        )

        cur.execute(
            """
            SELECT COUNT(*) FROM service_records
            WHERE extra ? 'evidence' OR extra ? 'attachments'
            """
        )
        out["cases_with_evidence_or_attachments_extra"] = int(cur.fetchone()[0] or 0)

        if _table_exists(cur, "service_records", "timeline_events"):
            cur.execute("SELECT COUNT(*) FROM service_records.timeline_events")
            out["timeline_event_count"] = int(cur.fetchone()[0] or 0)
        else:
            out["timeline_event_count"] = None

    out["tables"] = _table_names(conn)
    return out


def _table_exists(cur: Any, schema: str, table: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        (schema, table),
    )
    return cur.fetchone() is not None


def run_audit() -> dict[str, Any]:
    neon_url, qa_url, neon_masked, qa_masked = _resolve_urls()
    result: dict[str, Any] = {
        "audited_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "neon_identity": neon_masked,
        "cloud_sql_identity": qa_masked,
        "sources": {},
        "comparison": {},
    }

    with _pg_conn(neon_url, readonly=True) as neon_conn:
        result["sources"]["legacy_neon"] = _audit_source(neon_conn, "legacy_neon")

    with _pg_conn(qa_url, readonly=True) as qa_conn:
        result["sources"]["cloud_sql"] = _audit_source(qa_conn, "cloud_sql")

    neon_ids = set(result["sources"]["legacy_neon"]["case_ids_sample"])
    qa_ids = set(result["sources"]["cloud_sql"]["case_ids_sample"])
    only_neon = sorted(neon_ids - qa_ids)
    only_qa = sorted(qa_ids - neon_ids)

    neon_max = result["sources"]["legacy_neon"].get("updated_at_max")
    qa_max = result["sources"]["cloud_sql"].get("updated_at_max")

    result["comparison"] = {
        "only_in_neon_count": len(only_neon),
        "only_in_cloud_sql_count": len(only_qa),
        "only_in_neon_sample": only_neon[:30],
        "only_in_cloud_sql_sample": only_qa[:30],
        "neon_updated_at_max": neon_max,
        "cloud_sql_updated_at_max": qa_max,
        "neon_newer_than_cloud_sql": bool(
            neon_max and qa_max and neon_max > qa_max
        ),
        "row_count_delta_neon_minus_cloud_sql": (
            result["sources"]["legacy_neon"]["service_records_count"]
            - result["sources"]["cloud_sql"]["service_records_count"]
        ),
    }

    # Strip large id lists from printed payload
    for src in result["sources"].values():
        src.pop("case_ids_sample", None)

    stop_gate = False
    reasons: list[str] = []
    neon_newer = result["comparison"]["neon_newer_than_cloud_sql"]
    only_neon_n = len(only_neon)
    if neon_newer and only_neon_n > 0:
        stop_gate = True
        reasons.append(
            f"Neon updated_at_max ({neon_max}) is newer than Cloud SQL ({qa_max}) with {only_neon_n} Neon-only IDs"
        )
    elif neon_newer:
        stop_gate = True
        reasons.append("Neon updated_at_max is newer than Cloud SQL — possible drift")

    result["stop_gate"] = stop_gate
    result["stop_gate_reasons"] = reasons
    result["recommendation"] = (
        "BLOCKED — Neon has newer writes than Cloud SQL; investigate before isolation/delete"
        if stop_gate
        else (
            "READY TO ISOLATE — Cloud SQL is current SSOT; Neon is stale fork (export backup before delete)"
            if only_neon_n > 0
            else "READY TO ISOLATE — Cloud SQL is current SSOT"
        )
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Legacy Neon vs Cloud SQL metadata audit")
    parser.add_argument("--json-out", help="Write full JSON report to path")
    args = parser.parse_args()

    # Ensure QA env not polluted by shell Neon URL
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    os.environ.pop("DATABASE_URL", None)

    try:
        report = run_audit()
    except Exception as exc:
        print(f"FAIL: audit aborted — {exc}", file=sys.stderr)
        return 2

    summary = {
        "neon_rows": report["sources"]["legacy_neon"]["service_records_count"],
        "cloud_sql_rows": report["sources"]["cloud_sql"]["service_records_count"],
        "only_in_neon": report["comparison"]["only_in_neon_count"],
        "only_in_cloud_sql": report["comparison"]["only_in_cloud_sql_count"],
        "neon_updated_at_max": report["comparison"]["neon_updated_at_max"],
        "cloud_sql_updated_at_max": report["comparison"]["cloud_sql_updated_at_max"],
        "stop_gate": report["stop_gate"],
        "recommendation": report["recommendation"],
    }
    print(json.dumps(summary, indent=2))

    if args.json_out:
        path = args.json_out
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        print(f"\nFull report: {path}", file=sys.stderr)

    return 1 if report["stop_gate"] else 0


if __name__ == "__main__":
    sys.exit(main())
