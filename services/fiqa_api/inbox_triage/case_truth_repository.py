"""
Case / service-record read facade (JSON vs Postgres).

Business logic should use these entry points instead of calling case_store reads directly,
so DB-primary cutover stays behind env flags without rewiring routes every time.

Writes: case_store (JSON by default) with optional UNIFIED_INTAKE_DB_PRIMARY_WRITES +
UNIFIED_INTAKE_JSON_CASE_WRITES (pilot can disable JSON file writes); legacy dual-write
(UNIFIED_INTAKE_PG_DUAL_WRITE) mirrors to Postgres while JSON remains the default local
authoritative file unless DB-primary reads are on (including auto-on when dual-write is
enabled — see service_record_settings.db_primary_reads_enabled).
"""

from __future__ import annotations

import copy
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from services.fiqa_api.db.service_record_settings import (
    db_primary_reads_enabled,
    is_production_mode,
    json_read_fallback_allowed,
    json_case_writes_enabled,
    postgres_case_persistence_primary,
    service_record_database_url,
)
from services.fiqa_api.inbox_triage.case_store import (
    _normalize_case,
    count_stored_cases as json_count_stored_cases,
    get_case_by_id as json_get_case_by_id,
    list_all_cases as json_list_all_cases,
    list_recent_cases as json_list_recent_cases,
)

from services.fiqa_api.inbox_triage.phone_normalization import normalize_phone_digits

logger = logging.getLogger(__name__)

# Per HTTP request: dedupe get_case_triage_stub_for_read(case_id) (binding + reopen paths).
_TRIAGE_STUB_REQ_CACHE: ContextVar[dict[str, dict[str, Any] | None] | None] = ContextVar(
    "_TRIAGE_STUB_REQ_CACHE", default=None
)


@contextmanager
def triage_stub_read_cache_scope():
    """Use around POST /api/inbox/triage hot path when multiple stub reads may repeat the same case_id."""
    tok = _TRIAGE_STUB_REQ_CACHE.set({})
    try:
        yield
    finally:
        _TRIAGE_STUB_REQ_CACHE.reset(tok)


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
    if is_production_mode():
        return
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

    if is_production_mode() and not service_record_database_url():
        logger.warning(
            "JSON path should not be used in production (missing database URL; case_id=%s) %s",
            cid,
            _OBS,
        )
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

    if not json_read_fallback_allowed():
        if postgres_case_persistence_primary():
            logger.warning("%s signal=PG_GET_MISSING_STRICT_NO_JSON_FALLBACK case_id=%s", _OBS, cid)
        return None
    sig = "JSON_READ_FALLBACK_AFTER_PG_ERROR" if pg_error else "JSON_READ_FALLBACK_MISSING_PG_ROW"
    logger.warning("%s signal=%s case_id=%s", _OBS, sig, cid)
    return json_get_case_by_id(cid)


def count_cases_for_read() -> int:
    """Total persisted cases visible to the list endpoint (PG when DB-primary reads, else JSON)."""
    if is_production_mode() and not service_record_database_url():
        logger.warning("JSON path should not be used in production (missing database URL) %s", _OBS)
        return 0

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


def count_broker_workbench_cases_for_read() -> int:
    """P19H-3f-1c — broker queue total excluding raw inbound (wecom_media_intake)."""
    from services.fiqa_api.inbox_triage.workbench_enrichment import filter_broker_workbench_cases

    all_cases = list_all_cases_for_read()
    return len(filter_broker_workbench_cases(all_cases))


def list_broker_workbench_cases_for_read(
    limit: int = 8,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Recent broker-workbench cases (newest first), excluding raw inbound lanes."""
    from services.fiqa_api.inbox_triage.workbench_enrichment import filter_broker_workbench_cases

    safe_limit = max(1, min(int(limit or 8), 50))
    safe_offset = max(0, min(int(offset or 0), 10_000))
    filtered = filter_broker_workbench_cases(list_all_cases_for_read())
    total = len(filtered)
    return filtered[safe_offset : safe_offset + safe_limit], total


def list_recent_cases_for_read(limit: int = 8, offset: int = 0) -> list[dict[str, Any]]:
    """Recent cases for GET /api/inbox/cases (newest first)."""
    safe_limit = max(1, min(int(limit or 8), 50))
    safe_offset = max(0, min(int(offset or 0), 10_000))

    if is_production_mode() and not service_record_database_url():
        logger.warning("JSON path should not be used in production (missing database URL) %s", _OBS)
        return []

    if not db_primary_reads_enabled():
        return json_list_recent_cases(limit=safe_limit, offset=safe_offset)

    db_error = False
    ids: list[str] = []
    try:
        from services.fiqa_api.db.service_record_repository import (
            list_record_ids_recent,
            load_workbench_queue_cases_from_postgres,
        )

        ids = list_record_ids_recent(safe_limit, safe_offset)
        raw_rows = load_workbench_queue_cases_from_postgres(ids)
        out: list[dict[str, Any]] = []
        missing_hydration: list[str] = []
        seen: set[str] = set()
        for norm in raw_rows:
            rid = str(norm.get("case_id") or "").strip()
            if not rid:
                continue
            seen.add(rid)
            norm = _normalize_case(norm)
            _merge_workbench_flags_from_json(rid, norm)
            out.append(norm)
        for rid in ids:
            if rid not in seen:
                missing_hydration.append(rid)
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


def list_cases_for_office_enforcement_read(
    req_org: str,
    *,
    limit: int,
    offset: int,
    exclude_raw_inbound: bool = True,
) -> tuple[list[dict[str, Any]], int]:
    """
    Office-scoped slice for ``GET /api/inbox/cases`` when
    ``UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP`` is enabled.

    Postgres path uses indexed filters + stub hydration (no full-case N× load).
    JSON path filters the bounded in-file queue (same semantics as
    :func:`case_visible_in_office_list`).
    """
    from services.fiqa_api.security.case_office_access import (
        case_visible_in_office_list,
        office_list_strict_exclude_legacy_no_org,
    )

    safe_limit = max(1, min(int(limit or 8), 50))
    safe_offset = max(0, min(int(offset or 0), 5000))
    ro = (req_org or "").strip()[:256]
    if not ro:
        return [], 0

    strict = office_list_strict_exclude_legacy_no_org()

    from services.fiqa_api.inbox_triage.workbench_enrichment import filter_broker_workbench_cases

    if is_production_mode() and not service_record_database_url():
        logger.warning(
            "JSON path should not be used in production (missing database URL) %s",
            _OBS,
        )
        return [], 0

    if not db_primary_reads_enabled():
        scoped: list[dict[str, Any]] = []
        for c in json_list_all_cases():
            if not isinstance(c, dict):
                continue
            norm = _normalize_case(dict(c))
            if case_visible_in_office_list(norm, ro):
                scoped.append(norm)
        if exclude_raw_inbound:
            scoped = filter_broker_workbench_cases(scoped)
        total = len(scoped)
        return scoped[safe_offset : safe_offset + safe_limit], total

    try:
        from services.fiqa_api.db.service_record_repository import (
            count_service_records_office_scoped,
            list_record_ids_office_scoped,
            load_workbench_queue_cases_from_postgres,
        )

        total = count_service_records_office_scoped(ro, strict)
        ids = list_record_ids_office_scoped(ro, strict, safe_limit, safe_offset)
        raw_rows = load_workbench_queue_cases_from_postgres(ids)
        out: list[dict[str, Any]] = []
        for norm in raw_rows:
            rid = str(norm.get("case_id") or "").strip()
            if not rid:
                continue
            norm = _normalize_case(dict(norm))
            _merge_workbench_flags_from_json(rid, norm)
            out.append(norm)
        if exclude_raw_inbound:
            out = filter_broker_workbench_cases(out)
        return out, total
    except Exception:
        logger.exception("%s signal=PG_OFFICE_LIST_EXCEPTION path=list_cases_office", _OBS)
        if not json_read_fallback_allowed():
            return [], 0
        scoped_fb: list[dict[str, Any]] = []
        for c in json_list_all_cases():
            if not isinstance(c, dict):
                continue
            norm = _normalize_case(dict(c))
            if case_visible_in_office_list(norm, ro):
                scoped_fb.append(norm)
        if exclude_raw_inbound:
            scoped_fb = filter_broker_workbench_cases(scoped_fb)
        total_fb = len(scoped_fb)
        slice_fb = scoped_fb[safe_offset : safe_offset + safe_limit]
        logger.warning(
            "%s signal=JSON_READ_FALLBACK_LIST_AFTER_PG_OFFICE_ERROR path=list_cases_office json_case_count=%s",
            _OBS,
            len(slice_fb),
        )
        return slice_fb, total_fb


def list_cases_for_client_scoped_read(
    req_client: str,
    *,
    limit: int,
    offset: int,
    exclude_raw_inbound: bool = True,
) -> tuple[list[dict[str, Any]], int]:
    """
    Client-scoped slice for ``GET /api/inbox/cases`` when
    ``UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP`` is enabled.

    ``req_client`` must be the server-resolved client id (never a client header).
    """
    from services.fiqa_api.security.case_client_access import (
        case_visible_in_client_list,
        client_list_strict_exclude_legacy_no_client,
    )

    safe_limit = max(1, min(int(limit or 8), 50))
    safe_offset = max(0, min(int(offset or 0), 5000))
    rc = (req_client or "").strip()[:128]
    if not rc:
        return [], 0

    strict = client_list_strict_exclude_legacy_no_client()

    from services.fiqa_api.inbox_triage.workbench_enrichment import filter_broker_workbench_cases

    if is_production_mode() and not service_record_database_url():
        logger.warning(
            "JSON path should not be used in production (missing database URL) %s",
            _OBS,
        )
        return [], 0

    if not db_primary_reads_enabled():
        scoped: list[dict[str, Any]] = []
        for c in json_list_all_cases():
            if not isinstance(c, dict):
                continue
            norm = _normalize_case(dict(c))
            if case_visible_in_client_list(norm, rc):
                scoped.append(norm)
        if exclude_raw_inbound:
            scoped = filter_broker_workbench_cases(scoped)
        total = len(scoped)
        return scoped[safe_offset : safe_offset + safe_limit], total

    try:
        from services.fiqa_api.db.service_record_repository import (
            count_service_records_client_scoped,
            list_record_ids_client_scoped,
            load_workbench_queue_cases_from_postgres,
        )

        total = count_service_records_client_scoped(rc, strict)
        ids = list_record_ids_client_scoped(rc, strict, safe_limit, safe_offset)
        raw_rows = load_workbench_queue_cases_from_postgres(ids)
        out: list[dict[str, Any]] = []
        for norm in raw_rows:
            rid = str(norm.get("case_id") or "").strip()
            if not rid:
                continue
            norm = _normalize_case(dict(norm))
            _merge_workbench_flags_from_json(rid, norm)
            out.append(norm)
        if exclude_raw_inbound:
            out = filter_broker_workbench_cases(out)
        return out, total
    except Exception:
        logger.exception("%s signal=PG_CLIENT_LIST_EXCEPTION path=list_cases_client", _OBS)
        if not json_read_fallback_allowed():
            return [], 0
        scoped_fb: list[dict[str, Any]] = []
        for c in json_list_all_cases():
            if not isinstance(c, dict):
                continue
            norm = _normalize_case(dict(c))
            if case_visible_in_client_list(norm, rc):
                scoped_fb.append(norm)
        if exclude_raw_inbound:
            scoped_fb = filter_broker_workbench_cases(scoped_fb)
        total_fb = len(scoped_fb)
        slice_fb = scoped_fb[safe_offset : safe_offset + safe_limit]
        logger.warning(
            "%s signal=JSON_READ_FALLBACK_LIST_AFTER_PG_CLIENT_ERROR path=list_cases_client json_case_count=%s",
            _OBS,
            len(slice_fb),
        )
        return slice_fb, total_fb


def list_all_cases_for_read() -> list[dict[str, Any]]:
    """All persisted cases (bounded), newest-first — used by service_record_read and similar."""
    if is_production_mode() and not service_record_database_url():
        logger.warning("JSON path should not be used in production (missing database URL) %s", _OBS)
        return []

    if not db_primary_reads_enabled():
        return json_list_all_cases()

    db_error = False
    ids: list[str] = []
    try:
        from services.fiqa_api.db.service_record_repository import (
            list_record_ids_recent,
            load_workbench_queue_cases_from_postgres,
        )

        ids = list_record_ids_recent(_MAX_LIST_ALL)
        raw_rows = load_workbench_queue_cases_from_postgres(ids)
        out: list[dict[str, Any]] = []
        missing_hydration: list[str] = []
        seen: set[str] = set()
        for norm in raw_rows:
            rid = str(norm.get("case_id") or "").strip()
            if not rid:
                continue
            seen.add(rid)
            norm = _normalize_case(norm)
            _merge_workbench_flags_from_json(rid, norm)
            out.append(norm)
        for rid in ids:
            if rid not in seen:
                missing_hydration.append(rid)
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


def _get_case_triage_stub_for_read_uncached(case_id: str) -> dict[str, Any] | None:
    """Resolve triage stub without request-level memoization."""
    cid = (case_id or "").strip()
    if not cid:
        return None

    if is_production_mode() and not service_record_database_url():
        logger.warning(
            "JSON path should not be used in production (missing database URL; case_id=%s) %s",
            cid,
            _OBS,
        )
        return None

    if not db_primary_reads_enabled():
        return get_case_for_read(cid)

    try:
        from services.fiqa_api.db.service_record_repository import load_case_triage_stub_from_postgres

        pg_case = load_case_triage_stub_from_postgres(cid)
    except Exception:
        logger.exception("%s signal=PG_TRIAGE_STUB_EXCEPTION case_id=%s", _OBS, cid)
        pg_case = None

    if pg_case is not None:
        normalized = _normalize_case(pg_case)
        _merge_workbench_flags_from_json(cid, normalized)
        return normalized

    if not json_read_fallback_allowed():
        if postgres_case_persistence_primary():
            logger.warning(
                "%s signal=PG_TRIAGE_STUB_MISSING_STRICT_NO_JSON_FALLBACK case_id=%s",
                _OBS,
                cid,
            )
        return None
    logger.warning("%s signal=JSON_READ_FALLBACK_TRIAGE_STUB case_id=%s", _OBS, cid)
    return json_get_case_by_id(cid)


def get_case_triage_stub_for_read(case_id: str) -> dict[str, Any] | None:
    """
    Triage / inbox route hot path: truth fields for ``reply_truth_context`` without loading
    all messages and state history on Postgres. Non-DB mode uses full JSON read (local queues).
    """
    cid = (case_id or "").strip()
    if not cid:
        return None

    bucket = _TRIAGE_STUB_REQ_CACHE.get()
    if bucket is not None:
        if cid in bucket:
            hit = bucket[cid]
            return copy.deepcopy(hit) if hit is not None else None

    resolved = _get_case_triage_stub_for_read_uncached(cid)
    if bucket is not None:
        bucket[cid] = copy.deepcopy(resolved) if resolved is not None else None
    return resolved


def list_cases_for_phone_lookup(phone: str, *, client_id: str | None = None) -> list[dict[str, Any]]:
    """
    Bounded candidate cases for Customer First phone return-key (indexed PG path when enabled).
    """
    digits = normalize_phone_digits(phone)
    if len(digits) != 10:
        return []

    out: list[dict[str, Any]] = []
    if db_primary_reads_enabled() and service_record_database_url():
        try:
            from services.fiqa_api.db.service_record_repository import list_binding_stub_rows_by_phone_digits

            out = list_binding_stub_rows_by_phone_digits(digits, limit=24)
        except Exception:
            logger.exception("%s signal=PG_PHONE_LOOKUP_EXCEPTION", _OBS)

    if not out and json_read_fallback_allowed():
        for case in json_list_all_cases():
            cp = normalize_phone_digits(str(case.get("customer_phone") or ""))
            if cp != digits:
                continue
            cid = str(case.get("client_id") or "").strip()
            if client_id and cid and cid != client_id.strip():
                continue
            out.append(_normalize_case(case))

    return out


def find_case_id_for_case_ref(case_ref: str) -> str | None:
    """
    Resolve a human CLM-#### reference to one case_id (indexed PG path when enabled).

    Read-only. Returns None for an unparseable ref or when nothing matches.
    """
    from services.fiqa_api.inbox_triage.case_ref import normalize_case_ref

    ref = normalize_case_ref(case_ref)
    if not ref:
        return None

    if is_production_mode() and not service_record_database_url():
        logger.warning("JSON path should not be used in production (missing database URL) %s", _OBS)
        return None

    db_primary = db_primary_reads_enabled() and bool(service_record_database_url())
    if db_primary:
        try:
            from services.fiqa_api.db.service_record_repository import find_record_id_by_case_ref

            found = find_record_id_by_case_ref(ref)
            if found:
                return found
        except Exception:
            logger.exception("%s signal=PG_CASE_REF_LOOKUP_EXCEPTION", _OBS)

    # JSON is the primary read when DB-primary is off (same rule as get_case_for_read);
    # under DB-primary it is only a miss/error fallback.
    if not db_primary or json_read_fallback_allowed():
        for case in json_list_all_cases():
            if normalize_case_ref(str(case.get("case_ref") or "")) != ref:
                continue
            cid = str(case.get("case_id") or "").strip()
            if cid:
                return cid

    return None


def list_recent_cases_for_binding(
    limit: int = 30,
    offset: int = 0,
    *,
    client_asserted_org_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Recent cases for session/case binding: **triage stub** shape (truth fields for routing, no PG
    messages/history). Same list can be reused as ``existing_case`` on the inbox route to avoid a
    second ``get_case_triage_stub_for_read`` for the resolved ``case_id``.

    When ``client_asserted_org_id`` is set (``X-Org-Id`` client assertion), candidates use the
    same visibility rule as workbench list filtering (:func:`case_visible_in_office_list`), reducing
    cross-office vehicle/single-case auto-bind accidents without claiming cryptographic tenancy.
    """
    from services.fiqa_api.security.case_office_access import (
        case_visible_in_office_list,
        office_list_strict_exclude_legacy_no_org,
    )

    if is_production_mode() and not service_record_database_url():
        logger.warning("JSON path should not be used in production (missing database URL) %s", _OBS)
        return []

    safe_limit = max(1, min(int(limit or 8), 50))
    safe_offset = max(0, min(int(offset or 0), 10_000))
    req_org = (client_asserted_org_id or "").strip()[:256] or None
    strict_legacy = office_list_strict_exclude_legacy_no_org()

    def _normalize_binding_candidate(c: dict[str, Any]) -> dict[str, Any] | None:
        cid = str(c.get("case_id") or "").strip()
        if not cid:
            return None
        norm = _normalize_case(dict(c))
        _merge_workbench_flags_from_json(cid, norm)
        return norm

    def _filter_org_slice(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not req_org:
            return rows
        out_f: list[dict[str, Any]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            norm = _normalize_binding_candidate(item)
            if norm is None:
                continue
            if case_visible_in_office_list(norm, req_org):
                out_f.append(norm)
        return out_f

    if not db_primary_reads_enabled():
        raw = json_list_recent_cases(limit=safe_limit, offset=safe_offset)
        bound = _filter_org_slice([c for c in raw if isinstance(c, dict)])
        return bound if req_org else [x for x in (_normalize_binding_candidate(c) for c in raw) if x]

    try:
        from services.fiqa_api.db.service_record_repository import (
            list_binding_stub_rows_office_scoped,
            list_binding_stub_rows_recent,
        )

        if req_org:
            raw_rows = list_binding_stub_rows_office_scoped(
                req_org, strict_legacy, safe_limit, safe_offset
            )
        else:
            raw_rows = list_binding_stub_rows_recent(safe_limit, safe_offset)
    except Exception:
        logger.exception("%s signal=PG_BINDING_STUB_LIST_EXCEPTION", _OBS)
        raw_rows = []

    if raw_rows:
        out_pg: list[dict[str, Any]] = []
        for c in raw_rows:
            if not isinstance(c, dict):
                continue
            cid = str(c.get("case_id") or "").strip()
            if not cid:
                continue
            norm = _normalize_case(dict(c))
            _merge_workbench_flags_from_json(cid, norm)
            out_pg.append(norm)
        return out_pg

    if json_read_fallback_allowed():
        logger.warning("%s signal=JSON_READ_FALLBACK_BINDING_LIST", _OBS)
        raw_fb = json_list_recent_cases(limit=safe_limit, offset=safe_offset)
        if req_org:
            return _filter_org_slice([c for c in raw_fb if isinstance(c, dict)])
        out_fb: list[dict[str, Any]] = []
        for c in raw_fb:
            if not isinstance(c, dict):
                continue
            norm = _normalize_binding_candidate(c)
            if norm is not None:
                out_fb.append(norm)
        return out_fb
    return []
