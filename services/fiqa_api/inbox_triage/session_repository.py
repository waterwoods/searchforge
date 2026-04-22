"""
Pure persistence for in-progress intake sessions.

Postgres when SERVICE_RECORD_DATABASE_URL / DATABASE_URL is set.

Without a database URL, an in-process store is used only when
UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS is explicitly enabled (see
:func:`allow_inmemory_intake_sessions`). Otherwise reads return None and writes
return False — no silent “production-like” persistence on memory.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

from services.fiqa_api.db.service_record_settings import (
    allow_inmemory_intake_sessions,
    service_record_database_url,
)

logger = logging.getLogger(__name__)

# In-process store when no DB URL: session_id -> full session document (one row, same shape as JSON file element).
_MEMORY: dict[str, dict[str, Any]] = {}
_MEMORY_CREATED: dict[str, datetime] = {}

_MAX_SESSION_ROWS = 50

_INTAKE_DDL_CHECKED = False
_DB_DEGRADED_LOGGED = False
_NO_BACKEND_LOGGED = False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _dt_iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def reset_intake_session_memory_for_tests() -> None:
    """Clear the in-process session store. Used by tests; not for production."""
    global _NO_BACKEND_LOGGED
    _MEMORY.clear()
    _MEMORY_CREATED.clear()
    _NO_BACKEND_LOGGED = False


@contextmanager
def intake_session_connection() -> Generator[Any, None, None]:
    import psycopg

    url = service_record_database_url()
    if not url:
        raise RuntimeError("no database URL configured for intake session persistence")
    conn = psycopg.connect(url, connect_timeout=10)
    try:
        yield conn
    finally:
        conn.close()


def _intake_session_use_postgres() -> bool:
    return service_record_database_url() is not None


def _intake_session_use_memory() -> bool:
    return not _intake_session_use_postgres() and allow_inmemory_intake_sessions()


def _log_intake_session_backend_disabled() -> None:
    global _NO_BACKEND_LOGGED
    if _NO_BACKEND_LOGGED:
        return
    _NO_BACKEND_LOGGED = True
    logger.error(
        "intake session persistence disabled: set SERVICE_RECORD_DATABASE_URL (or DATABASE_URL) "
        "for Postgres, or set UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS=1 only for tests/local scripts"
    )


def get_session(session_id: str) -> dict[str, Any] | None:
    """Return a copy of the stored session document, or None if missing or on DB error."""
    sid = (session_id or "").strip()
    if not sid:
        return None
    if _intake_session_use_memory():
        row = _MEMORY.get(sid)
        return _copy_row(row) if row else None
    if not _intake_session_use_postgres():
        _log_intake_session_backend_disabled()
        return None
    try:
        with intake_session_connection() as conn:
            with conn.cursor() as cur:
                _ensure_intake_table_once(cur)
                cur.execute(
                    """
                    SELECT payload, updated_at, created_at
                    FROM intake_sessions
                    WHERE session_id = %(sid)s
                    """,
                    {"sid": sid},
                )
                r = cur.fetchone()
                if r is None:
                    return None
                payload, updated_at, _created_at = r[0] or {}, r[1], r[2]
                if not isinstance(payload, dict):
                    return None
                out = dict(payload)
                out["session_id"] = sid
                if updated_at is not None:
                    u = updated_at
                    if u.tzinfo is None:
                        u = u.replace(tzinfo=timezone.utc)
                    out["updated_at"] = _dt_iso(u)
                return out
    except Exception as exc:  # noqa: BLE001 — graceful degrade to “not found”
        _log_db_unavailable_read(exc, sid)
        return None


def _copy_row(row: dict[str, Any]) -> dict[str, Any]:
    import copy

    return copy.deepcopy(row)


def _log_db_unavailable_read(exc: BaseException, sid: str) -> None:
    global _DB_DEGRADED_LOGGED
    if not _DB_DEGRADED_LOGGED:
        _DB_DEGRADED_LOGGED = True
        logger.warning(
            "intake session read failed (session will appear missing to clients): %s [session_id=%s]",
            exc,
            sid,
        )
    else:
        logger.debug("intake session read failed: %s [session_id=%s]", exc, sid)


def _log_db_unavailable_write(exc: BaseException) -> None:
    global _DB_DEGRADED_LOGGED
    if not _DB_DEGRADED_LOGGED:
        _DB_DEGRADED_LOGGED = True
        logger.error("intake session write failed: %s", exc)
    else:
        logger.debug("intake session write failed: %s", exc)


def _log_table_create_hint(exc: BaseException) -> None:
    logger.error(
        "intake session upsert failed — apply schema: services/fiqa_api/db/schema/intake_sessions.sql (%s)",
        exc,
    )


def _ensure_intake_table_once(cur: Any) -> None:
    """Create table + index on first use so greenfield deploys work without a separate step."""
    global _INTAKE_DDL_CHECKED
    if _INTAKE_DDL_CHECKED:
        return
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS intake_sessions (
            session_id TEXT PRIMARY KEY,
            payload JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_intake_sessions_updated_at
        ON intake_sessions (updated_at DESC)
        """
    )
    _INTAKE_DDL_CHECKED = True
    logger.info("intake_sessions DDL verified (create-if-not-exists)")


def _evict_oldest_in_pg(cur: Any) -> None:
    cur.execute(
        """
        WITH keep AS (
            SELECT session_id FROM intake_sessions
            ORDER BY updated_at DESC
            LIMIT %s
        )
        DELETE FROM intake_sessions a
        WHERE NOT EXISTS (SELECT 1 FROM keep k WHERE k.session_id = a.session_id)
        """,
        (_MAX_SESSION_ROWS,),
    )


def _evict_oldest_in_memory() -> None:
    if len(_MEMORY) <= _MAX_SESSION_ROWS:
        return
    ordered = sorted(
        _MEMORY.items(),
        key=lambda kv: (kv[1].get("updated_at") or ""),
        reverse=True,
    )[:_MAX_SESSION_ROWS]
    keep = {k for k, _ in ordered}
    for sid in list(_MEMORY.keys()):
        if sid not in keep:
            _MEMORY.pop(sid, None)
            _MEMORY_CREATED.pop(sid, None)


def upsert_session(session_id: str, payload: dict[str, Any]) -> bool:
    """
    Replace document for session_id. `payload` should include session_id and updated_at
    and all fields the client layer expects. Returns False on total persistence failure.
    """
    sid = (session_id or "").strip()
    if not sid:
        return False
    doc = _copy_row(payload) if payload else {}
    if doc.get("session_id") != sid:
        doc["session_id"] = sid
    if _intake_session_use_memory():
        created = _MEMORY_CREATED.get(sid) or _utc_now()
        if sid not in _MEMORY_CREATED:
            _MEMORY_CREATED[sid] = created
        _MEMORY[sid] = doc
        _evict_oldest_in_memory()
        return True
    if not _intake_session_use_postgres():
        _log_intake_session_backend_disabled()
        return False

    from psycopg.types.json import Json

    try:
        with intake_session_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    _ensure_intake_table_once(cur)
                    u = _utc_now()
                    doc.setdefault("updated_at", _dt_iso(u))
                    inner = {k: v for k, v in doc.items() if k != "session_id"}
                    cur.execute(
                        """
                        INSERT INTO intake_sessions (session_id, payload, updated_at, created_at)
                        VALUES (%(sid)s, %(payload)s, %(u)s, %(u)s)
                        ON CONFLICT (session_id) DO UPDATE SET
                            payload = EXCLUDED.payload,
                            updated_at = EXCLUDED.updated_at
                        """,
                        {"sid": sid, "payload": Json(inner), "u": u},
                    )
                    _evict_oldest_in_pg(cur)
        return True
    except Exception as exc:  # noqa: BLE001
        if "42P01" in str(exc) or "undefined_table" in str(exc).lower():
            _log_table_create_hint(exc)
        _log_db_unavailable_write(exc)
        return False


def patch_session(session_id: str, partial_payload: dict[str, Any], *, create_if_missing: bool = False) -> bool:
    """
    Shallow merge of partial_payload into the stored document, then upsert.
    If create_if_missing, starts from empty turns/workflow; otherwise no-op when missing.
    """
    sid = (session_id or "").strip()
    if not sid:
        return False
    existing = get_session(sid)
    if existing is None:
        if not create_if_missing:
            return False
        base: dict[str, Any] = {
            "session_id": sid,
            "turns": [],
            "workflow_state": {},
            "updated_at": _dt_iso(_utc_now()),
        }
    else:
        base = _copy_row(existing)
    for k, v in partial_payload.items():
        base[k] = v
    return upsert_session(sid, base)


def delete_session(session_id: str) -> bool:
    """Remove the session. Returns True if a row was removed or memory entry cleared."""
    sid = (session_id or "").strip()
    if not sid:
        return False
    if _intake_session_use_memory():
        had = sid in _MEMORY
        _MEMORY.pop(sid, None)
        _MEMORY_CREATED.pop(sid, None)
        return had
    if not _intake_session_use_postgres():
        _log_intake_session_backend_disabled()
        return False
    try:
        with intake_session_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    _ensure_intake_table_once(cur)
                    cur.execute("DELETE FROM intake_sessions WHERE session_id = %(sid)s", {"sid": sid})
                    deleted = (cur.rowcount or 0) > 0
        return deleted
    except Exception as exc:  # noqa: BLE001
        _log_db_unavailable_write(exc)
        return False
