"""WeCom reply outbox — durable outbound queue (Q0.3).

When WECOM_REPLY_OUTBOX=1, business logic enqueues intended replies into
``wecom_reply_outbox`` instead of calling ``send_msg`` directly. A separate
sender function drains pending rows and reuses the existing send helpers.

Dedup key: stable hash from msg_id, external_userid, open_kf_id, reply_type,
case_id (when relevant), and reply payload content.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url
from services.fiqa_api.wecom.config import WeComKfConfig, load_wecom_kf_config
from services.fiqa_api.wecom.queue_db import (
    WeComQueueDbError,
    assert_wecom_queue_postgres_configured,
    wecom_queue_memory_fallback_allowed,
)
from services.fiqa_api.wecom.send_msg import send_menu_reply, send_text_reply

logger = logging.getLogger(__name__)

_MEMORY_ENQUEUED: set[str] = set()
_MEMORY_LOCK = threading.Lock()
_MAX_MEMORY_ROWS = 5000

_DDL_CHECKED = False
_DB_DEGRADED_LOGGED = False

_MAX_ERROR_MESSAGE_LEN = 2000
_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_STALE_TIMEOUT_SECONDS = 600

_WECOM_ERR_RE = re.compile(r"errcode=(?P<errcode>-?\d+)\s+errmsg=(?P<errmsg>[^\s]+(?:\s+[^\s]+)*)")


def wecom_reply_outbox_enabled() -> bool:
    """When True, replies are enqueued — not sent inline from business paths."""
    return (os.getenv("WECOM_REPLY_OUTBOX") or "").strip().lower() in ("1", "true", "yes")


def reset_wecom_reply_outbox_memory_for_tests() -> None:
    """Clear in-process dedup set. Tests only."""
    with _MEMORY_LOCK:
        _MEMORY_ENQUEUED.clear()


def compute_reply_dedup_key(
    *,
    msg_id: str | None = None,
    external_userid: str | None = None,
    open_kf_id: str | None = None,
    reply_type: str | None = None,
    case_id: str | None = None,
    reply_payload: dict[str, Any],
) -> str:
    """Stable idempotency key — same intended reply retry yields the same key."""
    payload_json = json.dumps(reply_payload, sort_keys=True, ensure_ascii=False)
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    parts = [
        str(msg_id or "").strip(),
        str(external_userid or "").strip(),
        str(open_kf_id or "").strip(),
        str(reply_type or "").strip(),
        str(case_id or "").strip(),
        payload_hash,
    ]
    material = "|".join(parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


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
        CREATE TABLE IF NOT EXISTS wecom_reply_outbox (
            id BIGSERIAL PRIMARY KEY,
            dedup_key TEXT NOT NULL UNIQUE,
            msg_id TEXT,
            external_userid TEXT,
            open_kf_id TEXT,
            case_id TEXT,
            reply_type TEXT,
            reply_payload_json JSONB NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            locked_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ,
            failed_at TIMESTAMPTZ,
            errcode INTEGER,
            errmsg TEXT,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_wecom_reply_outbox_status_created
        ON wecom_reply_outbox (status, created_at ASC)
        """
    )
    _DDL_CHECKED = True
    logger.info("wecom_reply_outbox DDL verified (create-if-not-exists)")


def _log_db_degraded(exc: BaseException, dedup_key: str) -> None:
    global _DB_DEGRADED_LOGGED
    if not _DB_DEGRADED_LOGGED:
        _DB_DEGRADED_LOGGED = True
        logger.error(
            "wecom_reply_outbox_db_unavailable_v1 falling back to in-process dedup only: %s [dedup_key=%s]",
            exc,
            dedup_key,
        )
    else:
        logger.debug("wecom_reply_outbox_db_error_v1: %s [dedup_key=%s]", exc, dedup_key)


def enqueue_wecom_reply(
    *,
    msg_id: str | None = None,
    external_userid: str,
    open_kf_id: str,
    case_id: str | None = None,
    reply_type: str,
    reply_payload: dict[str, Any],
) -> bool:
    """
    Insert one outbox row if dedup_key is new.

    Returns True when a new row was inserted, False on duplicate.

    When WECOM_REPLY_OUTBOX=1 (production outbox mode), Postgres is required —
    raises WeComQueueDbError if the database is unavailable. In-memory dedup is
    only used when the outbox flag is off or WECOM_QUEUE_ALLOW_MEMORY_FALLBACK=1.
    """
    dedup_key = compute_reply_dedup_key(
        msg_id=msg_id,
        external_userid=external_userid,
        open_kf_id=open_kf_id,
        reply_type=reply_type,
        case_id=case_id,
        reply_payload=reply_payload,
    )

    if not _use_postgres():
        if not wecom_queue_memory_fallback_allowed():
            assert_wecom_queue_postgres_configured()
        created = _enqueue_in_memory(dedup_key)
        _log_enqueue(dedup_key, created, backend="memory", reply_type=reply_type)
        return created

    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    _ensure_table_once(cur)
                    cur.execute(
                        """
                        INSERT INTO wecom_reply_outbox (
                            dedup_key,
                            msg_id,
                            external_userid,
                            open_kf_id,
                            case_id,
                            reply_type,
                            reply_payload_json
                        )
                        VALUES (
                            %(dedup_key)s,
                            %(msg_id)s,
                            %(external_userid)s,
                            %(open_kf_id)s,
                            %(case_id)s,
                            %(reply_type)s,
                            %(reply_payload_json)s::jsonb
                        )
                        ON CONFLICT (dedup_key) DO NOTHING
                        """,
                        {
                            "dedup_key": dedup_key,
                            "msg_id": (msg_id or "").strip() or None,
                            "external_userid": external_userid,
                            "open_kf_id": open_kf_id,
                            "case_id": (case_id or "").strip() or None,
                            "reply_type": reply_type,
                            "reply_payload_json": json.dumps(reply_payload, ensure_ascii=False),
                        },
                    )
                    created = (cur.rowcount or 0) > 0
        if created:
            with _MEMORY_LOCK:
                _MEMORY_ENQUEUED.add(dedup_key)
        _log_enqueue(dedup_key, created, backend="postgres", reply_type=reply_type)
        return created
    except Exception as exc:  # noqa: BLE001 — enqueue must not break business path
        if not wecom_queue_memory_fallback_allowed():
            _log_db_degraded(exc, dedup_key)
            raise WeComQueueDbError(
                f"wecom_reply_outbox_enqueue_db_failed_v1: Postgres required when "
                f"WECOM_REPLY_OUTBOX=1: {exc}"
            ) from exc
        _log_db_degraded(exc, dedup_key)
        created = _enqueue_in_memory(dedup_key)
        _log_enqueue(dedup_key, created, backend="memory", reply_type=reply_type)
        return created


def _log_enqueue(dedup_key: str, created: bool, *, backend: str, reply_type: str) -> None:
    logger.info(
        "wecom_reply_outbox_enqueued_v1 %s",
        json.dumps(
            {
                "dedup_key": dedup_key,
                "created": created,
                "duplicate": not created,
                "backend": backend,
                "reply_type": reply_type,
            },
            ensure_ascii=False,
        ),
    )


def _parse_wecom_error(exc: BaseException) -> tuple[int | None, str | None, str]:
    msg = str(exc)
    match = _WECOM_ERR_RE.search(msg)
    if match:
        errcode = int(match.group("errcode"))
        errmsg = match.group("errmsg")
        return errcode, errmsg, msg
    return None, None, msg[:_MAX_ERROR_MESSAGE_LEN]


def _payload_dict(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("reply_payload_json") or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload if isinstance(payload, dict) else {}


def _send_outbox_row(cfg: WeComKfConfig, row: dict[str, Any]) -> dict[str, Any]:
    """Call existing send_msg helpers for one outbox row. Raises on failure."""
    payload = _payload_dict(row)
    external_userid = str(row.get("external_userid") or "")
    open_kf_id = str(row.get("open_kf_id") or "")
    msgtype = str(payload.get("msgtype") or row.get("reply_type") or "").strip()

    if msgtype == "text":
        content = str((payload.get("text") or {}).get("content") or "")
        return send_text_reply(
            cfg,
            external_userid=external_userid,
            open_kf_id=open_kf_id,
            content=content,
        )
    if msgtype == "msgmenu":
        menu = payload.get("msgmenu")
        if not isinstance(menu, dict):
            raise ValueError("wecom_reply_outbox_invalid_payload_v1: msgmenu missing")
        return send_menu_reply(
            cfg,
            external_userid=external_userid,
            open_kf_id=open_kf_id,
            menu=menu,
        )
    raise ValueError(f"wecom_reply_outbox_unsupported_msgtype_v1: {msgtype!r}")


def _claim_eligible_rows(
    limit: int,
    *,
    max_attempts: int,
    stale_timeout_seconds: int,
) -> tuple[list[dict[str, Any]], int]:
    from psycopg.rows import dict_row

    from services.fiqa_api.db.service_record_repository import service_record_connection

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                _ensure_table_once(cur)
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM wecom_reply_outbox
                    WHERE attempt_count >= %(max_attempts)s
                      AND status IN ('pending', 'sending')
                    """,
                    {"max_attempts": max_attempts},
                )
                skipped_row = cur.fetchone()
                skipped = int((skipped_row or {}).get("n") or 0)

                cur.execute(
                    """
                    SELECT
                        id,
                        dedup_key,
                        msg_id,
                        external_userid,
                        open_kf_id,
                        case_id,
                        reply_type,
                        reply_payload_json,
                        status,
                        attempt_count,
                        locked_at
                    FROM wecom_reply_outbox
                    WHERE attempt_count < %(max_attempts)s
                      AND (
                        status = 'pending'
                        OR (
                          status = 'sending'
                          AND locked_at IS NOT NULL
                          AND locked_at < NOW() - (%(stale_timeout_seconds)s * INTERVAL '1 second')
                        )
                      )
                    ORDER BY created_at ASC
                    LIMIT %(limit)s
                    FOR UPDATE SKIP LOCKED
                    """,
                    {
                        "limit": limit,
                        "max_attempts": max_attempts,
                        "stale_timeout_seconds": stale_timeout_seconds,
                    },
                )
                rows = list(cur.fetchall())
                for row in rows:
                    prior_status = row.get("status")
                    stale_reclaim = prior_status == "sending"
                    cur.execute(
                        """
                        UPDATE wecom_reply_outbox
                        SET status = 'sending',
                            locked_at = NOW(),
                            attempt_count = attempt_count + 1,
                            updated_at = NOW()
                        WHERE id = %(id)s
                        """,
                        {"id": row["id"]},
                    )
                    logger.info(
                        "wecom_reply_outbox_claimed_v1 %s",
                        json.dumps(
                            {
                                "row_id": row["id"],
                                "dedup_key": row.get("dedup_key"),
                                "prior_status": prior_status,
                                "stale_reclaim": stale_reclaim,
                                "attempt_count_after_claim": int(row.get("attempt_count") or 0) + 1,
                            },
                            ensure_ascii=False,
                        ),
                    )
    return rows, skipped


def _mark_row_sent(row_id: int, *, errcode: int | None = None, errmsg: str | None = None) -> None:
    from services.fiqa_api.db.service_record_repository import service_record_connection

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE wecom_reply_outbox
                    SET status = 'sent',
                        sent_at = NOW(),
                        updated_at = NOW(),
                        errcode = %(errcode)s,
                        errmsg = %(errmsg)s,
                        error_message = NULL,
                        failed_at = NULL
                    WHERE id = %(id)s
                    """,
                    {"id": row_id, "errcode": errcode, "errmsg": errmsg},
                )
    logger.info(
        "wecom_reply_outbox_status_v1 %s",
        json.dumps({"row_id": row_id, "status": "sent"}, ensure_ascii=False),
    )


def _try_mark_row_sent(row_id: int, *, errcode: int | None = None, errmsg: str | None = None) -> bool:
    try:
        _mark_row_sent(row_id, errcode=errcode, errmsg=errmsg)
        return True
    except Exception as exc:  # noqa: BLE001 — stale reclaim will retry if mark fails
        logger.error(
            "wecom_reply_outbox_mark_sent_failed_v1 row_id=%s err=%s "
            "— row stays sending until stale reclaim or repair-stale",
            row_id,
            exc,
        )
        return False


def _mark_row_failed(
    row_id: int,
    *,
    errcode: int | None,
    errmsg: str | None,
    error_message: str,
) -> None:
    from services.fiqa_api.db.service_record_repository import service_record_connection

    msg = (error_message or "unknown error")[:_MAX_ERROR_MESSAGE_LEN]
    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE wecom_reply_outbox
                    SET status = 'failed',
                        failed_at = NOW(),
                        updated_at = NOW(),
                        errcode = %(errcode)s,
                        errmsg = %(errmsg)s,
                        error_message = %(error_message)s
                    WHERE id = %(id)s
                    """,
                    {
                        "id": row_id,
                        "errcode": errcode,
                        "errmsg": errmsg,
                        "error_message": msg,
                    },
                )
    logger.info(
        "wecom_reply_outbox_status_v1 %s",
        json.dumps({"row_id": row_id, "status": "failed"}, ensure_ascii=False),
    )


def _try_mark_row_failed(
    row_id: int,
    *,
    errcode: int | None,
    errmsg: str | None,
    error_message: str,
) -> bool:
    try:
        _mark_row_failed(row_id, errcode=errcode, errmsg=errmsg, error_message=error_message)
        return True
    except Exception as exc:  # noqa: BLE001 — stale reclaim will retry if mark fails
        logger.error(
            "wecom_reply_outbox_mark_failed_failed_v1 row_id=%s err=%s "
            "— row stays sending until stale reclaim or repair-stale",
            row_id,
            exc,
        )
        return False


def process_pending_wecom_reply_outbox(
    limit: int = 10,
    *,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    stale_timeout_seconds: int = _DEFAULT_STALE_TIMEOUT_SECONDS,
) -> dict[str, int]:
    """
    Claim eligible outbox rows and send each via existing send_msg helpers.

    Returns counts: claimed, sent, failed, skipped.
    """
    empty = {"claimed": 0, "sent": 0, "failed": 0, "skipped": 0}
    if not _use_postgres():
        logger.info(
            "wecom_reply_outbox_batch_v1 %s",
            json.dumps({**empty, "backend": "none"}, ensure_ascii=False),
        )
        return empty

    cfg = load_wecom_kf_config()
    if cfg is None:
        logger.warning("wecom_reply_outbox_batch_skipped_v1 reason=wecom_kf_not_configured")
        return empty

    claimed_rows, skipped = _claim_eligible_rows(
        limit,
        max_attempts=max_attempts,
        stale_timeout_seconds=stale_timeout_seconds,
    )
    sent = 0
    failed = 0

    for row in claimed_rows:
        row_id = row["id"]
        try:
            result = _send_outbox_row(cfg, row)
            errcode = int(result.get("errcode") or 0) if isinstance(result, dict) else 0
            errmsg = str(result.get("errmsg") or "") if isinstance(result, dict) else None
            if _try_mark_row_sent(row_id, errcode=errcode or None, errmsg=errmsg or None):
                sent += 1
            else:
                failed += 1
        except Exception as exc:  # noqa: BLE001 — per-row failure must not abort batch
            errcode, errmsg, error_message = _parse_wecom_error(exc)
            if _try_mark_row_failed(row_id, errcode=errcode, errmsg=errmsg, error_message=error_message):
                failed += 1
            else:
                failed += 1
            logger.warning(
                "wecom_reply_outbox_row_failed_v1 %s",
                json.dumps(
                    {
                        "row_id": row_id,
                        "dedup_key": row.get("dedup_key"),
                        "errcode": errcode,
                        "errmsg": errmsg,
                        "error": error_message,
                    },
                    ensure_ascii=False,
                ),
            )

    summary = {
        "claimed": len(claimed_rows),
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
    }
    logger.info("wecom_reply_outbox_batch_v1 %s", json.dumps(summary, ensure_ascii=False))
    return summary
