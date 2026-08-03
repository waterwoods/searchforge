"""Durable case activity timing events (observational telemetry).

Not customer Timeline. First-wins timestamps for intake open, first meaningful
customer action, and broker first case-detail open.

Never stores accident text, messages, raw tokens, or sensitive PII.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

EVENT_CUSTOMER_INTAKE_OPENED = "customer_intake_opened"
EVENT_CUSTOMER_FIRST_ACTION = "customer_first_action"
EVENT_BROKER_FIRST_OPENED = "broker_first_opened"

FIRST_WINS_EVENTS = frozenset(
    {
        EVENT_CUSTOMER_INTAKE_OPENED,
        EVENT_CUSTOMER_FIRST_ACTION,
        EVENT_BROKER_FIRST_OPENED,
    }
)

CASE_FIELD_BY_EVENT = {
    EVENT_CUSTOMER_INTAKE_OPENED: "customer_intake_opened_at",
    EVENT_CUSTOMER_FIRST_ACTION: "customer_first_action_at",
    EVENT_BROKER_FIRST_OPENED: "broker_first_opened_at",
}

ACTOR_CUSTOMER = "customer"
ACTOR_BROKER = "broker"
ACTOR_SYSTEM = "system"

_ALLOWED_META_KEYS = frozenset(
    {
        "command_type",
        "surface_detail",
        "outcome",
    }
)

_lock = threading.RLock()
_memory: dict[str, dict[str, Any]] = {}  # event_id -> row
_memory_by_case_type: dict[tuple[str, str], str] = {}  # (case_id, event_type) -> event_id


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def hash_session_id(session_id: str | None) -> str | None:
    raw = str(session_id or "").strip()
    if not raw:
        return None
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _sanitize_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    out: dict[str, Any] = {}
    for key, value in meta.items():
        k = str(key or "").strip()
        if k not in _ALLOWED_META_KEYS:
            continue
        if value is None:
            continue
        if isinstance(value, (bool, int)):
            out[k] = value
        else:
            text = str(value).strip()
            if text and len(text) <= 128:
                out[k] = text
    return out


def _pg_enabled() -> bool:
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url

        return bool(service_record_database_url())
    except Exception:
        return False


def _ensure_table(conn: Any) -> None:
    prev = bool(getattr(conn, "autocommit", False))
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS case_activity_events (
                    event_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor_role TEXT NOT NULL,
                    source_surface TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1,
                    idempotency_key TEXT NOT NULL,
                    session_id_hash TEXT,
                    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_case_activity_events_idempotency
                ON case_activity_events (case_id, event_type, idempotency_key)
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_case_activity_events_first_wins
                ON case_activity_events (case_id, event_type)
                WHERE event_type IN (
                    'customer_intake_opened',
                    'customer_first_action',
                    'broker_first_opened'
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_case_activity_events_case_created
                ON case_activity_events (case_id, created_at ASC)
                """
            )
    finally:
        try:
            conn.autocommit = prev
        except Exception:
            pass


def _fmt_db_ts(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    s = str(value).strip()
    if s.endswith("+00:00"):
        return s[:-6] + "Z"
    return s


def reset_case_activity_events_for_tests() -> None:
    """Clear in-memory store (unit tests only)."""
    with _lock:
        _memory.clear()
        _memory_by_case_type.clear()


def _memory_get(case_id: str, event_type: str) -> dict[str, Any] | None:
    eid = _memory_by_case_type.get((case_id, event_type))
    if not eid:
        return None
    row = _memory.get(eid)
    return dict(row) if row else None


def _memory_insert(row: dict[str, Any]) -> dict[str, Any]:
    key = (str(row["case_id"]), str(row["event_type"]))
    existing_id = _memory_by_case_type.get(key)
    if existing_id and existing_id in _memory:
        return dict(_memory[existing_id])
    eid = str(row["event_id"])
    _memory[eid] = dict(row)
    _memory_by_case_type[key] = eid
    return dict(row)


def _pg_get(case_id: str, event_type: str) -> dict[str, Any] | None:
    from services.fiqa_api.db.service_record_repository import service_record_connection

    with service_record_connection() as conn:
        _ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_id, case_id, event_type, actor_role, source_surface,
                       schema_version, idempotency_key, session_id_hash, meta, created_at
                FROM case_activity_events
                WHERE case_id = %s AND event_type = %s
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (case_id, event_type),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "event_id": str(row[0]),
        "case_id": str(row[1]),
        "event_type": str(row[2]),
        "actor_role": str(row[3]),
        "source_surface": str(row[4]),
        "schema_version": int(row[5] or SCHEMA_VERSION),
        "idempotency_key": str(row[6]),
        "session_id_hash": str(row[7]) if row[7] else None,
        "meta": row[8] if isinstance(row[8], dict) else {},
        "created_at": _fmt_db_ts(row[9]),
        "duplicate": True,
        "recorded": False,
    }


def _pg_insert(row: dict[str, Any]) -> dict[str, Any]:
    from psycopg.types.json import Json

    from services.fiqa_api.db.service_record_repository import service_record_connection

    with service_record_connection() as conn:
        _ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO case_activity_events (
                    event_id, case_id, event_type, actor_role, source_surface,
                    schema_version, idempotency_key, session_id_hash, meta, created_at
                ) VALUES (
                    %(event_id)s, %(case_id)s, %(event_type)s, %(actor_role)s, %(source_surface)s,
                    %(schema_version)s, %(idempotency_key)s, %(session_id_hash)s, %(meta)s,
                    %(created_at)s::timestamptz
                )
                ON CONFLICT (case_id, event_type, idempotency_key)
                DO NOTHING
                RETURNING event_id, created_at
                """,
                {
                    "event_id": row["event_id"],
                    "case_id": row["case_id"],
                    "event_type": row["event_type"],
                    "actor_role": row["actor_role"],
                    "source_surface": row["source_surface"],
                    "schema_version": row["schema_version"],
                    "idempotency_key": row["idempotency_key"],
                    "session_id_hash": row.get("session_id_hash"),
                    "meta": Json(row.get("meta") or {}),
                    "created_at": row["created_at"],
                },
            )
            inserted = cur.fetchone()
            if inserted:
                conn.commit()
                out = dict(row)
                out["created_at"] = _fmt_db_ts(inserted[1])
                out["recorded"] = True
                out["duplicate"] = False
                return out
            cur.execute(
                """
                SELECT event_id, created_at FROM case_activity_events
                WHERE case_id = %s AND event_type = %s
                ORDER BY created_at ASC LIMIT 1
                """,
                (row["case_id"], row["event_type"]),
            )
            existing = cur.fetchone()
            conn.commit()
    if existing:
        return {
            **row,
            "event_id": str(existing[0]),
            "created_at": _fmt_db_ts(existing[1]),
            "recorded": False,
            "duplicate": True,
        }
    # Fallback idempotency unique index path
    return {**row, "recorded": False, "duplicate": True}


def _denormalize_case_field(case_id: str, event_type: str, created_at: str) -> None:
    """Best-effort immutable stamp on case.extra (events table remains SSOT)."""
    field = CASE_FIELD_BY_EVENT.get(event_type)
    if not field or not created_at:
        return
    if not _pg_enabled():
        return
    try:
        from psycopg.types.json import Json

        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE service_records SET
                        updated_at = now(),
                        extra = COALESCE(extra, '{}'::jsonb) || %(patch)s::jsonb
                    WHERE record_id = %(case_id)s
                      AND COALESCE(extra->>%(field)s, '') = ''
                    """,
                    {
                        "case_id": case_id,
                        "field": field,
                        "patch": Json({field: created_at}),
                    },
                )
            conn.commit()
    except Exception as exc:
        logger.warning("case_activity denorm failed case=%s: %s", case_id, exc)


def record_case_activity_event(
    *,
    case_id: str,
    event_type: str,
    actor_role: str,
    source_surface: str,
    idempotency_key: str | None = None,
    session_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record one activity event. First-wins types never reset timestamps."""
    cid = str(case_id or "").strip()
    et = str(event_type or "").strip()
    if not cid or et not in FIRST_WINS_EVENTS:
        return {
            "ok": False,
            "recorded": False,
            "duplicate": False,
            "error": "invalid_event",
        }
    actor = str(actor_role or "").strip() or ACTOR_SYSTEM
    surface = str(source_surface or "").strip() or "unknown"
    idem = str(idempotency_key or "").strip() or f"{cid}:{et}"
    now = _utc_now_iso()
    row = {
        "event_id": f"cae_{uuid.uuid4().hex[:16]}",
        "case_id": cid,
        "event_type": et,
        "actor_role": actor,
        "source_surface": surface[:64],
        "schema_version": SCHEMA_VERSION,
        "idempotency_key": idem[:256],
        "session_id_hash": hash_session_id(session_id),
        "meta": _sanitize_meta(meta),
        "created_at": now,
        "recorded": True,
        "duplicate": False,
    }

    with _lock:
        existing_mem = _memory_get(cid, et)
        if existing_mem:
            return {
                "ok": True,
                "recorded": False,
                "duplicate": True,
                "event_id": existing_mem["event_id"],
                "created_at": existing_mem["created_at"],
                "event_type": et,
                "case_id": cid,
            }

        result = dict(row)
        if _pg_enabled():
            try:
                pg_row = _pg_get(cid, et)
                if pg_row:
                    _memory_insert({**pg_row, "recorded": False, "duplicate": True})
                    return {
                        "ok": True,
                        "recorded": False,
                        "duplicate": True,
                        "event_id": pg_row["event_id"],
                        "created_at": pg_row["created_at"],
                        "event_type": et,
                        "case_id": cid,
                    }
                result = _pg_insert(row)
            except Exception as exc:
                logger.warning("case_activity PG write failed case=%s type=%s: %s", cid, et, exc)
                result = _memory_insert(row)
                result["recorded"] = True
                result["duplicate"] = False
        else:
            result = _memory_insert(row)
            result["recorded"] = True
            result["duplicate"] = False

        if result.get("recorded"):
            _memory_insert(result)
            _denormalize_case_field(cid, et, str(result.get("created_at") or now))
        else:
            _memory_insert({**result, "duplicate": True})

        return {
            "ok": True,
            "recorded": bool(result.get("recorded")),
            "duplicate": bool(result.get("duplicate")),
            "event_id": result.get("event_id"),
            "created_at": result.get("created_at") or now,
            "event_type": et,
            "case_id": cid,
            "schema_version": SCHEMA_VERSION,
            "actor_role": actor,
            "source_surface": surface[:64],
            "idempotency_key": idem[:256],
            "session_id_hash": row.get("session_id_hash"),
            "meta": row.get("meta") or {},
        }


def get_case_activity_timing(case_id: str) -> dict[str, str]:
    """Return first-wins timestamps for a case (blank strings when absent)."""
    cid = str(case_id or "").strip()
    out = {
        "customer_intake_opened_at": "",
        "customer_first_action_at": "",
        "broker_first_opened_at": "",
    }
    if not cid:
        return out

    with _lock:
        for et, field in CASE_FIELD_BY_EVENT.items():
            mem = _memory_get(cid, et)
            if mem and mem.get("created_at"):
                out[field] = str(mem["created_at"])

    if _pg_enabled():
        try:
            from services.fiqa_api.db.service_record_repository import service_record_connection

            with service_record_connection() as conn:
                _ensure_table(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT event_type, MIN(created_at) AS first_at
                        FROM case_activity_events
                        WHERE case_id = %s
                          AND event_type IN (
                            'customer_intake_opened',
                            'customer_first_action',
                            'broker_first_opened'
                          )
                        GROUP BY event_type
                        """,
                        (cid,),
                    )
                    for event_type, first_at in cur.fetchall() or []:
                        field = CASE_FIELD_BY_EVENT.get(str(event_type))
                        if field:
                            out[field] = _fmt_db_ts(first_at)
        except Exception as exc:
            logger.warning("case_activity timing read failed case=%s: %s", cid, exc)

    return out


def attach_case_activity_timing(case: dict[str, Any]) -> dict[str, Any]:
    """Merge timing fields onto a case dict for API/export (additive)."""
    if not isinstance(case, dict):
        return case
    cid = str(case.get("case_id") or case.get("id") or "").strip()
    if not cid:
        return case
    timing = get_case_activity_timing(cid)
    for field, value in timing.items():
        if value and not str(case.get(field) or "").strip():
            case[field] = value
        elif not str(case.get(field) or "").strip():
            case[field] = value or case.get(field) or None
    case["case_activity_timing"] = {
        k: (str(case.get(k) or "").strip() or None) for k in CASE_FIELD_BY_EVENT.values()
    }
    return case


def record_customer_intake_opened(
    case_id: str,
    *,
    source_surface: str,
    session_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return record_case_activity_event(
        case_id=case_id,
        event_type=EVENT_CUSTOMER_INTAKE_OPENED,
        actor_role=ACTOR_CUSTOMER,
        source_surface=source_surface,
        session_id=session_id,
        meta=meta,
    )


def record_customer_first_action(
    case_id: str,
    *,
    source_surface: str,
    session_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Ensure open precedes or equals first action when both fire in one request.
    record_customer_intake_opened(
        case_id,
        source_surface=source_surface,
        session_id=session_id,
        meta={"command_type": "implied_open_before_action"},
    )
    return record_case_activity_event(
        case_id=case_id,
        event_type=EVENT_CUSTOMER_FIRST_ACTION,
        actor_role=ACTOR_CUSTOMER,
        source_surface=source_surface,
        session_id=session_id,
        meta=meta,
    )


def record_broker_first_opened(
    case_id: str,
    *,
    source_surface: str = "broker_workbench",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return record_case_activity_event(
        case_id=case_id,
        event_type=EVENT_BROKER_FIRST_OPENED,
        actor_role=ACTOR_BROKER,
        source_surface=source_surface,
        meta=meta,
    )


def safe_record(fn: Any, *args: Any, **kwargs: Any) -> dict[str, Any] | None:
    """Never let telemetry break the business path."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        logger.warning("case_activity safe_record failed: %s", exc)
        return None
