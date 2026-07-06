"""WeCom inbound message idempotency — each msg_id processed at most once (Q0.10).

`wecom_reply_dedup` only guards the outbound send boundary. Historical
``sync_msg`` replay can still re-run intent classification, draft merges, and
outbox enqueues for msg_ids that were never successfully sent. This module
claims a msg_id *before* any business logic so replayed messages are skipped
entirely.

Durability model mirrors ``wecom.reply_dedup``: Postgres ``INSERT … ON CONFLICT
DO NOTHING`` when a database URL is configured; in-process set for tests.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url

logger = logging.getLogger(__name__)

_MEMORY_PROCESSED: set[str] = set()
_MEMORY_LOCK = threading.Lock()
_MAX_MEMORY_ROWS = 10000

_DDL_CHECKED = False
_DB_DEGRADED_LOGGED = False


def reset_message_processed_memory_for_tests() -> None:
    """Clear the in-process guard. Tests only."""
    with _MEMORY_LOCK:
        _MEMORY_PROCESSED.clear()


def _use_postgres() -> bool:
    return service_record_database_url() is not None


def _claim_in_memory(mid: str) -> bool:
    with _MEMORY_LOCK:
        if mid in _MEMORY_PROCESSED:
            return False
        if len(_MEMORY_PROCESSED) >= _MAX_MEMORY_ROWS:
            _MEMORY_PROCESSED.clear()
        _MEMORY_PROCESSED.add(mid)
        return True


def _release_in_memory(mid: str) -> None:
    with _MEMORY_LOCK:
        _MEMORY_PROCESSED.discard(mid)


def _ensure_table_once(cur: Any) -> None:
    global _DDL_CHECKED
    if _DDL_CHECKED:
        return
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS wecom_message_processed (
            msg_id TEXT PRIMARY KEY,
            open_kf_id TEXT,
            external_userid TEXT,
            event_type TEXT,
            case_id TEXT,
            outcome TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    _DDL_CHECKED = True
    logger.info("wecom_message_processed DDL verified (create-if-not-exists)")


def _log_db_degraded(exc: BaseException, mid: str) -> None:
    global _DB_DEGRADED_LOGGED
    if not _DB_DEGRADED_LOGGED:
        _DB_DEGRADED_LOGGED = True
        logger.error(
            "wecom_message_processed_db_unavailable_v1 falling back to in-process guard only: %s [msg_id=%s]",
            exc,
            mid,
        )
    else:
        logger.debug("wecom_message_processed_db_error_v1: %s [msg_id=%s]", exc, mid)


def claim_message_processed(
    msg_id: str,
    *,
    open_kf_id: str | None = None,
    external_userid: str | None = None,
    event_type: str | None = None,
) -> bool:
    """
    Atomically claim processing for ``msg_id``.

    Returns True the first time — caller must run business logic.
    Returns False when already processed — caller must skip entirely.
    """
    mid = (msg_id or "").strip()
    if not mid:
        return True

    if not _use_postgres():
        return _claim_in_memory(mid)

    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    _ensure_table_once(cur)
                    cur.execute(
                        """
                        INSERT INTO wecom_message_processed (
                            msg_id, open_kf_id, external_userid, event_type
                        )
                        VALUES (
                            %(msg_id)s, %(open_kf_id)s, %(external_userid)s, %(event_type)s
                        )
                        ON CONFLICT (msg_id) DO NOTHING
                        """,
                        {
                            "msg_id": mid,
                            "open_kf_id": (open_kf_id or "").strip() or None,
                            "external_userid": (external_userid or "").strip() or None,
                            "event_type": (event_type or "").strip() or None,
                        },
                    )
                    claimed = (cur.rowcount or 0) > 0
        if claimed:
            with _MEMORY_LOCK:
                _MEMORY_PROCESSED.add(mid)
        return claimed
    except Exception as exc:  # noqa: BLE001
        _log_db_degraded(exc, mid)
        return _claim_in_memory(mid)


def update_message_processed_outcome(
    msg_id: str,
    *,
    outcome: str | None = None,
    case_id: str | None = None,
) -> None:
    """Record final outcome after successful business processing."""
    mid = (msg_id or "").strip()
    if not mid or not _use_postgres():
        return
    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    _ensure_table_once(cur)
                    cur.execute(
                        """
                        UPDATE wecom_message_processed
                        SET outcome = COALESCE(%(outcome)s, outcome),
                            case_id = COALESCE(%(case_id)s, case_id),
                            updated_at = NOW()
                        WHERE msg_id = %(msg_id)s
                        """,
                        {
                            "msg_id": mid,
                            "outcome": (outcome or "").strip() or None,
                            "case_id": (case_id or "").strip() or None,
                        },
                    )
    except Exception as exc:  # noqa: BLE001
        _log_db_degraded(exc, mid)


def release_message_processed(msg_id: str) -> None:
    """
    Free a claim after processing failed before durable side effects, so an
    inbox-worker retry can re-run business logic for this msg_id.
    """
    mid = (msg_id or "").strip()
    if not mid:
        return
    _release_in_memory(mid)
    if not _use_postgres():
        return
    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    _ensure_table_once(cur)
                    cur.execute(
                        "DELETE FROM wecom_message_processed WHERE msg_id = %(msg_id)s",
                        {"msg_id": mid},
                    )
    except Exception as exc:  # noqa: BLE001
        _log_db_degraded(exc, mid)
