"""
P3-B Slice 1 — Human-readable case reference (CLM-####).

case_id remains the immutable internal primary key.
case_ref is additive, unique, and immutable after assignment.
Uniqueness comes from a Postgres sequence (or JSON-store max+1), never from
the displayed 8-character hex fragment of case_id.
"""

from __future__ import annotations

import logging
import re
import threading
from typing import Any

logger = logging.getLogger(__name__)

_CASE_REF_RE = re.compile(r"^CLM-(\d+)$", re.IGNORECASE)
_JSON_LOCK = threading.Lock()
_JSON_NEXT = 1


def format_case_ref(n: int) -> str:
    """Format a positive integer as CLM-#### (at least 4 digits)."""
    if n < 1:
        raise ValueError("case_ref_sequence_must_be_positive")
    return f"CLM-{n:04d}"


def parse_case_ref_number(case_ref: str | None) -> int | None:
    raw = str(case_ref or "").strip().upper()
    m = _CASE_REF_RE.match(raw)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def is_valid_case_ref(case_ref: str | None) -> bool:
    return parse_case_ref_number(case_ref) is not None


def normalize_case_ref(case_ref: str | None) -> str | None:
    n = parse_case_ref_number(case_ref)
    if n is None:
        return None
    return format_case_ref(n)


def _max_case_ref_number_from_cases(cases: list[dict[str, Any]]) -> int:
    max_n = 0
    for case in cases:
        n = parse_case_ref_number(str(case.get("case_ref") or ""))
        if n is not None and n > max_n:
            max_n = n
    return max_n


def _next_json_case_ref_number() -> int:
    """Assign the next case_ref for JSON case_store / tests without Postgres."""
    global _JSON_NEXT
    with _JSON_LOCK:
        try:
            from services.fiqa_api.inbox_triage.case_store import list_all_cases

            max_existing = _max_case_ref_number_from_cases(list_all_cases())
        except Exception:
            max_existing = 0
        n = max(_JSON_NEXT, max_existing + 1)
        _JSON_NEXT = n + 1
        return n


def _next_pg_case_ref_number() -> int | None:
    """Return next sequence value from Postgres, or None when DB unavailable."""
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url

        if not service_record_database_url():
            return None
        from services.fiqa_api.db.service_record_repository import allocate_case_ref_number

        return allocate_case_ref_number()
    except Exception:
        logger.exception("case_ref_pg_allocate_failed")
        return None


def allocate_case_ref() -> str:
    """Allocate a new unique case_ref (PG sequence preferred; JSON fallback)."""
    n = _next_pg_case_ref_number()
    if n is None:
        n = _next_json_case_ref_number()
    return format_case_ref(n)


def ensure_case_ref(case: dict[str, Any]) -> str:
    """
    Return existing case_ref or assign one.

    Existing non-empty valid refs are never rewritten (immutability).
    """
    if not isinstance(case, dict):
        raise TypeError("ensure_case_ref requires a case dict")
    existing = normalize_case_ref(str(case.get("case_ref") or ""))
    if existing:
        case["case_ref"] = existing
        return existing
    assigned = allocate_case_ref()
    case["case_ref"] = assigned
    return assigned


def reset_json_case_ref_counter_for_tests(next_n: int = 1) -> None:
    """Test helper — reset in-process JSON allocator."""
    global _JSON_NEXT
    with _JSON_LOCK:
        _JSON_NEXT = max(1, int(next_n))
