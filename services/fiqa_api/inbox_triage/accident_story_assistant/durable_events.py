"""Durable Accident Story pilot events (Postgres) — non-sensitive only.

Survives Cloud Run cold starts. In-memory list remains a convenience mirror.
Never stores raw story, phone, OpenID, invite tokens, names, or photo refs.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

TABLE = "accident_story_pilot_events"


def _pg_enabled() -> bool:
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url

        return bool(service_record_database_url())
    except Exception:
        return False


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


def _ensure_table(conn: Any) -> None:
    prev = bool(getattr(conn, "autocommit", False))
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE} (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    case_id TEXT,
                    idempotency_key TEXT NOT NULL,
                    meta JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(
                f"""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_accident_story_pilot_events_idem
                ON {TABLE} (event_type, idempotency_key)
                """
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_accident_story_pilot_events_created
                ON {TABLE} (created_at DESC)
                """
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_accident_story_pilot_events_type_created
                ON {TABLE} (event_type, created_at DESC)
                """
            )
    finally:
        try:
            conn.autocommit = prev
        except Exception:
            pass


def persist_pilot_event(row: dict[str, Any]) -> dict[str, Any]:
    """Insert one sanitized event. Idempotent on (event_type, idempotency_key). Never raises."""
    out = {
        "recorded": False,
        "duplicate": False,
        "durable": False,
        "event_id": row.get("event_id"),
    }
    if not _pg_enabled():
        return out
    try:
        from psycopg.types.json import Json

        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            _ensure_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {TABLE} (
                        event_id, event_type, case_id, idempotency_key, meta, created_at
                    ) VALUES (
                        %(event_id)s, %(event_type)s, %(case_id)s, %(idempotency_key)s,
                        %(meta)s, %(created_at)s::timestamptz
                    )
                    ON CONFLICT (event_type, idempotency_key) DO NOTHING
                    RETURNING event_id, created_at
                    """,
                    {
                        "event_id": row["event_id"],
                        "event_type": row["event_type"],
                        "case_id": row.get("case_id"),
                        "idempotency_key": row["idempotency_key"],
                        "meta": Json(row.get("meta") or {}),
                        "created_at": row["server_timestamp"],
                    },
                )
                inserted = cur.fetchone()
                if inserted:
                    conn.commit()
                    out["recorded"] = True
                    out["durable"] = True
                    out["event_id"] = str(inserted[0])
                    out["created_at"] = _fmt_db_ts(inserted[1])
                    return out
                cur.execute(
                    f"""
                    SELECT event_id, created_at FROM {TABLE}
                    WHERE event_type = %s AND idempotency_key = %s
                    LIMIT 1
                    """,
                    (row["event_type"], row["idempotency_key"]),
                )
                existing = cur.fetchone()
                conn.commit()
            if existing:
                out["duplicate"] = True
                out["durable"] = True
                out["event_id"] = str(existing[0])
                out["created_at"] = _fmt_db_ts(existing[1])
        return out
    except Exception:
        logger.debug("accident_story_pilot_event_persist_failed", exc_info=True)
        return out


def load_pilot_events(
    *,
    since: str | None = None,
    until: str | None = None,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    """Load durable events for a time window. Empty list if PG unavailable."""
    if not _pg_enabled():
        return []
    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        clauses = ["TRUE"]
        params: list[Any] = []
        if since:
            clauses.append("created_at >= %s::timestamptz")
            params.append(since)
        if until:
            clauses.append("created_at <= %s::timestamptz")
            params.append(until)
        params.append(max(1, min(int(limit), 20000)))
        where = " AND ".join(clauses)
        with service_record_connection() as conn:
            _ensure_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT event_id, event_type, case_id, idempotency_key, meta, created_at
                    FROM {TABLE}
                    WHERE {where}
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    tuple(params),
                )
                rows = cur.fetchall() or []
        out: list[dict[str, Any]] = []
        for r in rows:
            meta = r[4] if isinstance(r[4], dict) else {}
            out.append(
                {
                    "event_id": str(r[0]),
                    "event_type": str(r[1]),
                    "case_id": str(r[2]) if r[2] else None,
                    "idempotency_key": str(r[3]),
                    "meta": meta,
                    "server_timestamp": _fmt_db_ts(r[5]),
                    "durable": True,
                }
            )
        return out
    except Exception:
        logger.debug("accident_story_pilot_event_load_failed", exc_info=True)
        return []


__all__ = ["load_pilot_events", "persist_pilot_event"]
