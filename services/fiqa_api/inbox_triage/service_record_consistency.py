"""
Narrow JSON <-> Postgres consistency helpers for Add-Car formal submissions.
"""

from __future__ import annotations

from typing import Any

from services.fiqa_api.inbox_triage.service_record_read import ServiceRecordSnapshot


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _norm_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _norm_text(item)
        if text:
            out.append(text)
    return out


def compare_snapshot_with_pg(
    snap: ServiceRecordSnapshot,
    pg_row: dict[str, Any] | None,
) -> list[str]:
    """
    Return mismatch labels for a single JSON snapshot vs Postgres row.
    """
    if pg_row is None:
        return ["missing_postgres_row"]

    mismatches: list[str] = []
    if _norm_text(pg_row.get("record_id")) != snap.case_id:
        mismatches.append("case_id")
    if _norm_text(pg_row.get("customer_name")) != _norm_text(snap.customer_name):
        mismatches.append("customer_name")
    if _norm_text(pg_row.get("customer_phone")) != _norm_text(snap.customer_phone):
        mismatches.append("customer_phone")
    if _norm_text(pg_row.get("lifecycle_status")) != _norm_text(snap.lifecycle_status):
        mismatches.append("lifecycle_status")

    pg_quote = _norm_text(pg_row.get("quote_readiness"))
    if pg_quote != _norm_text(snap.quote_ready_status):
        mismatches.append("quote_ready_status")

    extra = pg_row.get("extra") if isinstance(pg_row.get("extra"), dict) else {}
    if _norm_text(extra.get("formal_submitted_at")) != _norm_text(snap.formal_submitted_at):
        mismatches.append("formal_submitted_at")

    structured = pg_row.get("structured_payload") if isinstance(pg_row.get("structured_payload"), dict) else {}
    pg_still_needed = _norm_str_list(structured.get("still_needed_fields"))
    if pg_still_needed != snap.still_needed_fields:
        mismatches.append("still_needed_fields")

    pg_lane = _norm_text(structured.get("service_lane"))
    snap_lane = _norm_text(snap.service_lane)
    if snap_lane and pg_lane != snap_lane:
        mismatches.append("service_lane")

    return mismatches
