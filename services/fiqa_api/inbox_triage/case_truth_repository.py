"""
Case / service-record read facade (JSON vs Postgres).

Business logic should use these entry points instead of calling case_store reads directly,
so DB-primary cutover stays behind env flags without rewiring routes every time.

Writes: case_store (JSON by default) with optional UNIFIED_INTAKE_DB_PRIMARY_WRITES +
UNIFIED_INTAKE_JSON_CASE_WRITES (pilot can disable JSON file writes); legacy dual-write
when PG_DUAL_WRITE without DB-primary writes.
"""

from __future__ import annotations

import logging
from typing import Any

from services.fiqa_api.db.service_record_settings import (
    db_primary_reads_enabled,
    db_primary_writes_enabled,
    json_case_writes_enabled,
    json_read_fallback_allowed,
)
from services.fiqa_api.inbox_triage.case_store import (
    _normalize_case,
    count_stored_cases as json_count_stored_cases,
    get_case_by_id as json_get_case_by_id,
    list_all_cases as json_list_all_cases,
    list_recent_cases as json_list_recent_cases,
)

logger = logging.getLogger(__name__)

# Match case_store.MAX_STORED_CASES for list-all parity
_MAX_LIST_ALL = 200

# Grep-friendly prefix for Cloud Run / founder log review (DB-primary path).
_OBS = "UNIFIED_INTAKE_DB_OBS"


def _merge_workbench_flags_from_json(case_id: str, case: dict[str, Any]) -> None:
    """
    Legacy dual-track: when JSON case files are still written and JSON read fallback is
    allowed, workbench flags may have been edited only in JSON — overlay from JSON.

    When JSON case writes are off (DB-primary pilot) or JSON read fallback is disabled
    (strict DB-only reads), Postgres `extra.workbench_*` hydrated in load_full_case_from_postgres
    must win — do not let a stale JSON row override PG truth.
    """
    if not json_case_writes_enabled() or not json_read_fallback_allowed():
        return
    j = json_get_case_by_id(case_id)
    if not j:
        return
    case["workbench_test"] = bool(j.get("workbench_test"))
    case["workbench_archived"] = bool(j.get("workbench_archived"))


def get_case_for_read(case_id: str) -> dict[str, Any] | None:
    """
    Single entry for get-by-id reads used by API/triage.

    When UNIFIED_INTAKE_DB_PRIMARY_READS is on (and DB URL set), prefer Postgres.
    If the row is missing or the DB errors, fall back to JSON when allowed.
    """
    cid = (case_id or "").strip()
    if not cid:
        return None

    if not db_primary_reads_enabled():
        return json_get_case_by_id(cid)

    pg_error = False
    try:
        from services.fiqa_api.db.service_record_repository import load_full_case_from_postgres

        pg_case = load_full_case_from_postgres(cid)
    except Exception:
        pg_error = True
        logger.exception("%s signal=PG_READ_EXCEPTION case_id=%s", _OBS, cid)
        pg_case = None

    if pg_case is not None:
        normalized = _normalize_case(pg_case)
        _merge_workbench_flags_from_json(cid, normalized)
        return normalized

    if json_read_fallback_allowed():
        if db_primary_writes_enabled() and not json_case_writes_enabled():
            logger.warning("%s signal=PG_GET_MISSING_STRICT_NO_JSON_FALLBACK case_id=%s", _OBS, cid)
            return None
        sig = "JSON_READ_FALLBACK_AFTER_PG_ERROR" if pg_error else "JSON_READ_FALLBACK_MISSING_PG_ROW"
        logger.warning("%s signal=%s case_id=%s", _OBS, sig, cid)
        return json_get_case_by_id(cid)
    return None


def count_cases_for_read() -> int:
    """Total persisted cases visible to the list endpoint (PG when DB-primary reads, else JSON)."""
    if not db_primary_reads_enabled():
        return json_count_stored_cases()

    try:
        from services.fiqa_api.db.service_record_repository import count_service_records

        n = count_service_records()
        if n > 0:
            return n
    except Exception:
        logger.exception("%s signal=PG_COUNT_EXCEPTION path=count_cases_for_read", _OBS)

    if json_read_fallback_allowed():
        return json_count_stored_cases()
    return 0


def list_recent_cases_for_read(limit: int = 8, offset: int = 0) -> list[dict[str, Any]]:
    """Recent cases for GET /api/inbox/cases (newest first)."""
    safe_limit = max(1, min(int(limit or 8), 50))
    safe_offset = max(0, min(int(offset or 0), 10_000))

    if not db_primary_reads_enabled():
        return json_list_recent_cases(limit=safe_limit, offset=safe_offset)

    db_error = False
    ids: list[str] = []
    try:
        from services.fiqa_api.db.service_record_repository import (
            list_record_ids_recent,
            load_full_case_from_postgres,
        )

        ids = list_record_ids_recent(safe_limit, safe_offset)
        out: list[dict[str, Any]] = []
        missing_hydration: list[str] = []
        for rid in ids:
            raw = load_full_case_from_postgres(rid)
            if not raw:
                missing_hydration.append(rid)
                continue
            norm = _normalize_case(raw)
            _merge_workbench_flags_from_json(rid, norm)
            out.append(norm)
        if missing_hydration:
            sample = ",".join(missing_hydration[:12])
            logger.warning(
                "%s signal=PG_LIST_HYDRATION_GAP path=list_recent missing_count=%s record_ids_sample=%s",
                _OBS,
                len(missing_hydration),
                sample,
            )
        if out:
            return out
        if ids and not out:
            logger.warning(
                "%s signal=PG_LIST_ALL_IDS_FAILED_HYDRATION path=list_recent id_count=%s",
                _OBS,
                len(ids),
            )
    except Exception:
        db_error = True
        logger.exception("%s signal=PG_LIST_EXCEPTION path=list_recent", _OBS)

    # Postgres returned row ids but nothing hydrated — do not mask with JSON (misleading queue).
    if ids and not db_error:
        return []

    if not json_read_fallback_allowed():
        return []

    j_cases = json_list_recent_cases(limit=safe_limit, offset=safe_offset)
    if db_error:
        logger.warning("%s signal=JSON_READ_FALLBACK_LIST_AFTER_PG_ERROR path=list_recent", _OBS)
    elif j_cases and not ids:
        logger.warning(
            "%s signal=JSON_READ_FALLBACK_LIST_STALE_JSON path=list_recent json_case_count=%s",
            _OBS,
            len(j_cases),
        )
    return j_cases


def list_all_cases_for_read() -> list[dict[str, Any]]:
    """All persisted cases (bounded), newest-first — used by service_record_read and similar."""
    if not db_primary_reads_enabled():
        return json_list_all_cases()

    db_error = False
    ids: list[str] = []
    try:
        from services.fiqa_api.db.service_record_repository import (
            list_record_ids_recent,
            load_full_case_from_postgres,
        )

        ids = list_record_ids_recent(_MAX_LIST_ALL)
        out: list[dict[str, Any]] = []
        missing_hydration: list[str] = []
        for rid in ids:
            raw = load_full_case_from_postgres(rid)
            if not raw:
                missing_hydration.append(rid)
                continue
            norm = _normalize_case(raw)
            _merge_workbench_flags_from_json(rid, norm)
            out.append(norm)
        if missing_hydration:
            sample = ",".join(missing_hydration[:12])
            logger.warning(
                "%s signal=PG_LIST_HYDRATION_GAP path=list_all missing_count=%s record_ids_sample=%s",
                _OBS,
                len(missing_hydration),
                sample,
            )
        if out:
            return out
        if ids and not out:
            logger.warning(
                "%s signal=PG_LIST_ALL_IDS_FAILED_HYDRATION path=list_all id_count=%s",
                _OBS,
                len(ids),
            )
    except Exception:
        db_error = True
        logger.exception("%s signal=PG_LIST_EXCEPTION path=list_all", _OBS)

    if ids and not db_error:
        return []

    if not json_read_fallback_allowed():
        return []

    j_cases = json_list_all_cases()
    if db_error:
        logger.warning("%s signal=JSON_READ_FALLBACK_LIST_AFTER_PG_ERROR path=list_all", _OBS)
    elif j_cases and not ids:
        logger.warning(
            "%s signal=JSON_READ_FALLBACK_LIST_STALE_JSON path=list_all json_case_count=%s",
            _OBS,
            len(j_cases),
        )
    return j_cases
