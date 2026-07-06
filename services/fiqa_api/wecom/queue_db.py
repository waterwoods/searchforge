"""WeCom queue Postgres preflight and production fail-closed helpers (Q0.8.3).

When WECOM_INBOX_QUEUE=1 or WECOM_REPLY_OUTBOX=1, Postgres is required —
in-memory dedup fallback is not allowed unless WECOM_QUEUE_ALLOW_MEMORY_FALLBACK=1
(tests only).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url

logger = logging.getLogger(__name__)

_WECOM_QUEUE_TABLES = ("wecom_inbox_events", "wecom_reply_outbox")

_DB_URL_MISSING = (
    "wecom_queue_db_preflight_v1: set SERVICE_RECORD_DATABASE_URL "
    "(or DATABASE_URL) — Postgres is required when WECOM_INBOX_QUEUE=1 "
    "or WECOM_REPLY_OUTBOX=1"
)


def _truthy_env(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in ("1", "true", "yes", "on")


class WeComQueueDbError(RuntimeError):
    """Postgres unavailable or misconfigured for WeCom queue/outbox mode."""


def wecom_queue_postgres_required() -> bool:
    """True when queue or outbox feature flags require durable Postgres."""
    return _truthy_env("WECOM_INBOX_QUEUE") or _truthy_env("WECOM_REPLY_OUTBOX")


def wecom_queue_allow_memory_fallback() -> bool:
    """
    Explicit test-only override for in-memory enqueue dedup.

    Env: WECOM_QUEUE_ALLOW_MEMORY_FALLBACK=1|true|yes|on
    """
    raw = (os.getenv("WECOM_QUEUE_ALLOW_MEMORY_FALLBACK") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def wecom_queue_memory_fallback_allowed() -> bool:
    """In-memory enqueue is allowed only when Postgres is not required or tests opt in."""
    if wecom_queue_postgres_required():
        return wecom_queue_allow_memory_fallback()
    return True


def assert_wecom_queue_postgres_configured() -> str:
    """
    Fail closed when queue/outbox flags are on but no database URL is configured.

    Returns the configured URL when present.
    """
    url = service_record_database_url()
    if wecom_queue_postgres_required() and not url:
        raise WeComQueueDbError(_DB_URL_MISSING)
    if not url:
        raise WeComQueueDbError(_DB_URL_MISSING)
    return url


def preflight_wecom_queue_db() -> dict[str, Any]:
    """
    Verify Postgres is reachable and WeCom queue tables exist.

    Used by admin status/drain/repair before touching queue rows.
    Raises WeComQueueDbError on any failure — never claims rows when this fails.
    """
    assert_wecom_queue_postgres_configured()

    from services.fiqa_api.db.service_record_repository import service_record_connection

    try:
        with service_record_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                row = cur.fetchone()
                if row is None:
                    raise WeComQueueDbError(
                        "wecom_queue_db_preflight_v1: SELECT 1 returned no row"
                    )
                val = row.get("?column?") if isinstance(row, dict) else row[0]
                if val != 1:
                    raise WeComQueueDbError(
                        "wecom_queue_db_preflight_v1: SELECT 1 returned unexpected result"
                    )
                for table in _WECOM_QUEUE_TABLES:
                    cur.execute(f"SELECT 1 FROM {table} LIMIT 0")
    except WeComQueueDbError:
        raise
    except Exception as exc:  # noqa: BLE001 — surface as operator-facing preflight error
        raise WeComQueueDbError(
            f"wecom_queue_db_preflight_v1: Postgres check failed: {exc}"
        ) from exc

    result = {
        "ok": True,
        "database_url_configured": True,
        "select_1": True,
        "tables_verified": list(_WECOM_QUEUE_TABLES),
    }
    logger.info("wecom_queue_db_preflight_ok_v1 %s", result)
    return result
