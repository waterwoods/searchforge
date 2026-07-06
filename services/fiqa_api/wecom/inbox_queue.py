"""WeCom callback inbox queue — fast ack with Postgres-backed dedup (Q0.1).

When WECOM_INBOX_QUEUE=1, the callback verifies/decrypts, enqueues one row, and
returns 200 immediately. A future worker will drain pending rows.

Dedup key priority:
1. open_kf_id + callback Token (WeCom event token)
2. open_kf_id + SHA-256 of the raw encrypted POST body
3. SHA-256 of normalized decrypted callback payload
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url
from services.fiqa_api.wecom.queue_db import (
    WeComQueueDbError,
    assert_wecom_queue_postgres_configured,
    wecom_queue_memory_fallback_allowed,
)

logger = logging.getLogger(__name__)

_MEMORY_ENQUEUED: set[str] = set()
_MEMORY_LOCK = threading.Lock()
_MAX_MEMORY_ROWS = 5000

_DDL_CHECKED = False
_DB_DEGRADED_LOGGED = False


def wecom_inbox_queue_enabled() -> bool:
    """When True, callback enqueues only — no sync_msg / classify / reply in-request."""
    return (os.getenv("WECOM_INBOX_QUEUE") or "").strip().lower() in ("1", "true", "yes")


def reset_wecom_inbox_memory_for_tests() -> None:
    """Clear in-process dedup set. Tests only."""
    with _MEMORY_LOCK:
        _MEMORY_ENQUEUED.clear()


def compute_dedup_key(
    *,
    parsed_event: dict[str, Any],
    raw_body: bytes,
) -> str:
    """Stable idempotency key for WeCom callback retries."""
    open_kf_id = str(parsed_event.get("OpenKfId") or "").strip()
    token = str(parsed_event.get("Token") or "").strip()
    if open_kf_id and token:
        return f"{open_kf_id}:{token}"
    if open_kf_id and raw_body:
        body_hash = hashlib.sha256(raw_body).hexdigest()
        return f"{open_kf_id}:{body_hash}"
    normalized = json.dumps(parsed_event, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _use_postgres() -> bool:
    return service_record_database_url() is not None


def _enqueue_in_memory(dedup_key: str) -> bool:
    with _MEMORY_LOCK:
        if dedup_key in _MEMORY_ENQUEUED:
            return False
        if len(_MEMORY_ENQUEUED) >= _MAX_MEMORY_ROWS:
            _MEMORY_ENQUEUED.clear()
        _MEMORY_ENQUEUED.add(dedup_key)
        return True


def _ensure_table_once(cur: Any) -> None:
    global _DDL_CHECKED
    if _DDL_CHECKED:
        return
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS wecom_inbox_events (
            id BIGSERIAL PRIMARY KEY,
            dedup_key TEXT NOT NULL UNIQUE,
            open_kf_id TEXT,
            external_userid TEXT,
            callback_token TEXT,
            event_type TEXT,
            payload_json JSONB NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            locked_at TIMESTAMPTZ,
            processed_at TIMESTAMPTZ,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_wecom_inbox_events_status_created
        ON wecom_inbox_events (status, created_at ASC)
        """
    )
    _DDL_CHECKED = True
    logger.info("wecom_inbox_events DDL verified (create-if-not-exists)")


def _log_db_degraded(exc: BaseException, dedup_key: str) -> None:
    global _DB_DEGRADED_LOGGED
    if not _DB_DEGRADED_LOGGED:
        _DB_DEGRADED_LOGGED = True
        logger.error(
            "wecom_inbox_queue_db_unavailable_v1 falling back to in-process dedup only: %s [dedup_key=%s]",
            exc,
            dedup_key,
        )
    else:
        logger.debug("wecom_inbox_queue_db_error_v1: %s [dedup_key=%s]", exc, dedup_key)


def enqueue_wecom_callback_event(
    *,
    dedup_key: str,
    parsed_event: dict[str, Any],
    payload_json: dict[str, Any],
) -> bool:
    """
    Insert one inbox row if dedup_key is new.

    Returns True when a new row was inserted, False on duplicate (WeCom retry).

    When WECOM_INBOX_QUEUE=1 (production queue mode), Postgres is required —
    raises WeComQueueDbError if the database is unavailable. In-memory dedup is
    only used when the queue flag is off or WECOM_QUEUE_ALLOW_MEMORY_FALLBACK=1.
    """
    key = (dedup_key or "").strip()
    if not key:
        logger.warning("wecom_inbox_enqueue_skipped_v1 reason=empty_dedup_key")
        return False

    open_kf_id = str(parsed_event.get("OpenKfId") or "").strip() or None
    callback_token = str(parsed_event.get("Token") or "").strip() or None
    event_type = str(parsed_event.get("Event") or parsed_event.get("MsgType") or "").strip() or None
    external_userid = str(parsed_event.get("ExternalUserId") or "").strip() or None

    if not _use_postgres():
        if not wecom_queue_memory_fallback_allowed():
            assert_wecom_queue_postgres_configured()
        created = _enqueue_in_memory(key)
        _log_enqueue(key, created, backend="memory")
        return created

    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    _ensure_table_once(cur)
                    cur.execute(
                        """
                        INSERT INTO wecom_inbox_events (
                            dedup_key,
                            open_kf_id,
                            external_userid,
                            callback_token,
                            event_type,
                            payload_json
                        )
                        VALUES (
                            %(dedup_key)s,
                            %(open_kf_id)s,
                            %(external_userid)s,
                            %(callback_token)s,
                            %(event_type)s,
                            %(payload_json)s::jsonb
                        )
                        ON CONFLICT (dedup_key) DO NOTHING
                        """,
                        {
                            "dedup_key": key,
                            "open_kf_id": open_kf_id,
                            "external_userid": external_userid,
                            "callback_token": callback_token,
                            "event_type": event_type,
                            "payload_json": json.dumps(payload_json, ensure_ascii=False),
                        },
                    )
                    created = (cur.rowcount or 0) > 0
        if created:
            with _MEMORY_LOCK:
                _MEMORY_ENQUEUED.add(key)
        _log_enqueue(key, created, backend="postgres")
        return created
    except Exception as exc:  # noqa: BLE001 — enqueue errors must not block 200 ack
        if not wecom_queue_memory_fallback_allowed():
            _log_db_degraded(exc, key)
            raise WeComQueueDbError(
                f"wecom_inbox_enqueue_db_failed_v1: Postgres required when "
                f"WECOM_INBOX_QUEUE=1: {exc}"
            ) from exc
        _log_db_degraded(exc, key)
        created = _enqueue_in_memory(key)
        _log_enqueue(key, created, backend="memory")
        return created


def _log_enqueue(dedup_key: str, created: bool, *, backend: str) -> None:
    logger.info(
        "wecom_inbox_enqueued_v1 %s",
        json.dumps(
            {
                "dedup_key": dedup_key,
                "created": created,
                "duplicate": not created,
                "backend": backend,
            },
            ensure_ascii=False,
        ),
    )
