"""WeCom inbox worker — drain pending wecom_inbox_events (Q0.2 / Q0.2.1).

Claims rows with ``SELECT … FOR UPDATE SKIP LOCKED``, runs the same slice path
the callback used to invoke inline, then marks rows processed or failed.

Q0.2.1 hardening:
- Reclaim stale ``processing`` rows (``locked_at`` older than timeout).
- Respect ``max_attempts`` — exhausted rows are not claimed.
- Fail unknown event types instead of silent no-op.
- Richer batch summary and safe logging (no payload bodies).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url
from services.fiqa_api.wecom.config import WeComKfConfig, load_wecom_kf_config
from services.fiqa_api.wecom.inbox_queue import _ensure_table_once
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

logger = logging.getLogger(__name__)

_MAX_ERROR_MESSAGE_LEN = 2000
_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_STALE_TIMEOUT_SECONDS = 600  # 10 minutes

_UNHANDLED_EVENT_ERROR = "wecom_inbox_unhandled_event_type_v1"


def _use_postgres() -> bool:
    return service_record_database_url() is not None


def _payload_dict(event_row: dict[str, Any]) -> dict[str, Any]:
    payload = event_row.get("payload_json") or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload if isinstance(payload, dict) else {}


def _is_kf_msg_or_event_payload(event_row: dict[str, Any], payload: dict[str, Any]) -> bool:
    """True when payload clearly represents a WeCom kf_msg_or_event callback."""
    if str(payload.get("event") or "").strip() == "kf_msg_or_event":
        return True
    raw = payload.get("raw_fields") or {}
    if str(raw.get("Event") or "").strip() == "kf_msg_or_event":
        return True
    open_kf_id = str(
        event_row.get("open_kf_id")
        or payload.get("open_kf_id")
        or raw.get("OpenKfId")
        or ""
    ).strip()
    callback_token = str(
        event_row.get("callback_token")
        or payload.get("token")
        or raw.get("Token")
        or ""
    ).strip()
    if open_kf_id and callback_token and str(payload.get("channel") or "").strip() == "wecom_kf":
        return True
    return False


def resolve_wecom_inbox_event_type(event_row: dict[str, Any]) -> str:
    """
    Resolve the effective event type for worker dispatch.

    Empty event_type falls back to payload fields; clearly kf callbacks become
    ``kf_msg_or_event``. Unknown types are returned as-is for the caller to reject.
    """
    payload = _payload_dict(event_row)
    event_type = str(event_row.get("event_type") or "").strip()
    if not event_type:
        event_type = str(payload.get("event") or "").strip()
    if not event_type:
        raw = payload.get("raw_fields") or {}
        event_type = str(raw.get("Event") or "").strip()
    if not event_type and _is_kf_msg_or_event_payload(event_row, payload):
        return "kf_msg_or_event"
    return event_type


def _resolve_kf_ids(event_row: dict[str, Any], payload: dict[str, Any]) -> tuple[str, str]:
    open_kf_id = str(event_row.get("open_kf_id") or "").strip()
    callback_token = str(event_row.get("callback_token") or "").strip()
    if not open_kf_id:
        open_kf_id = str(
            payload.get("open_kf_id")
            or (payload.get("raw_fields") or {}).get("OpenKfId")
            or ""
        ).strip()
    if not callback_token:
        callback_token = str(
            payload.get("token")
            or (payload.get("raw_fields") or {}).get("Token")
            or ""
        ).strip()
    return open_kf_id, callback_token


def process_wecom_inbox_event(event_row: dict[str, Any], *, cfg: WeComKfConfig | None = None) -> None:
    """
    Run existing WeCom slice logic for one inbox row.

    Raises on unexpected errors so the worker can mark the row failed.
    """
    if cfg is None:
        cfg = load_wecom_kf_config()
    if cfg is None:
        raise RuntimeError(
            "wecom_kf_callback_not_configured_v1: set WECOM_KF_TOKEN, "
            "WECOM_KF_ENCODING_AES_KEY, WECOM_CORP_ID"
        )

    payload = _payload_dict(event_row)
    event_type = resolve_wecom_inbox_event_type(event_row)
    open_kf_id, callback_token = _resolve_kf_ids(event_row, payload)

    if event_type == "kf_msg_or_event":
        process_kf_msg_or_event(
            cfg,
            callback_token=callback_token,
            open_kf_id=open_kf_id,
        )
        return

    if not event_type:
        raise ValueError(f"{_UNHANDLED_EVENT_ERROR}: empty event_type")
    raise ValueError(f"{_UNHANDLED_EVENT_ERROR}: {event_type!r}")


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
                    FROM wecom_inbox_events
                    WHERE attempt_count >= %(max_attempts)s
                      AND status IN ('pending', 'processing')
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
                        open_kf_id,
                        external_userid,
                        callback_token,
                        event_type,
                        payload_json,
                        status,
                        attempt_count,
                        locked_at
                    FROM wecom_inbox_events
                    WHERE attempt_count < %(max_attempts)s
                      AND (
                        status = 'pending'
                        OR (
                          status = 'processing'
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
                    stale_reclaim = prior_status == "processing"
                    cur.execute(
                        """
                        UPDATE wecom_inbox_events
                        SET status = 'processing',
                            locked_at = NOW(),
                            attempt_count = attempt_count + 1,
                            updated_at = NOW()
                        WHERE id = %(id)s
                        """,
                        {"id": row["id"]},
                    )
                    logger.info(
                        "wecom_inbox_worker_claimed_v1 %s",
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


def _mark_row_processed(row_id: int) -> None:
    from services.fiqa_api.db.service_record_repository import service_record_connection

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE wecom_inbox_events
                    SET status = 'processed',
                        processed_at = NOW(),
                        updated_at = NOW(),
                        error_message = NULL
                    WHERE id = %(id)s
                    """,
                    {"id": row_id},
                )
    logger.info(
        "wecom_inbox_worker_status_v1 %s",
        json.dumps({"row_id": row_id, "status": "processed"}, ensure_ascii=False),
    )


def _try_mark_row_processed(row_id: int) -> bool:
    try:
        _mark_row_processed(row_id)
        return True
    except Exception as exc:  # noqa: BLE001 — stale reclaim will retry if mark fails
        logger.error(
            "wecom_inbox_worker_mark_processed_failed_v1 row_id=%s err=%s "
            "— row stays processing until stale reclaim or repair-stale",
            row_id,
            exc,
        )
        return False


def _mark_row_failed(row_id: int, error_message: str) -> None:
    from services.fiqa_api.db.service_record_repository import service_record_connection

    msg = (error_message or "unknown error")[:_MAX_ERROR_MESSAGE_LEN]
    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE wecom_inbox_events
                    SET status = 'failed',
                        updated_at = NOW(),
                        error_message = %(error_message)s
                    WHERE id = %(id)s
                    """,
                    {"id": row_id, "error_message": msg},
                )
    logger.info(
        "wecom_inbox_worker_status_v1 %s",
        json.dumps({"row_id": row_id, "status": "failed"}, ensure_ascii=False),
    )


def _try_mark_row_failed(row_id: int, error_message: str) -> bool:
    try:
        _mark_row_failed(row_id, error_message)
        return True
    except Exception as exc:  # noqa: BLE001 — stale reclaim will retry if mark fails
        logger.error(
            "wecom_inbox_worker_mark_failed_failed_v1 row_id=%s err=%s "
            "— row stays processing until stale reclaim or repair-stale",
            row_id,
            exc,
        )
        return False


def process_pending_wecom_inbox_events(
    limit: int = 10,
    *,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    stale_timeout_seconds: int = _DEFAULT_STALE_TIMEOUT_SECONDS,
) -> dict[str, int]:
    """
    Claim eligible inbox rows and process each.

    Claims ``pending`` rows and stale ``processing`` rows (``locked_at`` older
    than ``stale_timeout_seconds``). Rows with ``attempt_count >= max_attempts``
    are not claimed; their count is returned as ``skipped``.

    Failed rows are not retried unless a future explicit retry path is added.

    Returns counts: claimed, processed, failed, skipped.
    """
    empty = {"claimed": 0, "processed": 0, "failed": 0, "skipped": 0}
    if not _use_postgres():
        logger.info(
            "wecom_inbox_worker_batch_v1 %s",
            json.dumps({**empty, "backend": "none"}, ensure_ascii=False),
        )
        return empty

    cfg = load_wecom_kf_config()
    claimed_rows, skipped = _claim_eligible_rows(
        limit,
        max_attempts=max_attempts,
        stale_timeout_seconds=stale_timeout_seconds,
    )
    processed = 0
    failed = 0

    for row in claimed_rows:
        row_id = row["id"]
        try:
            process_wecom_inbox_event(row, cfg=cfg)
            if _try_mark_row_processed(row_id):
                processed += 1
            else:
                failed += 1
        except Exception as exc:  # noqa: BLE001 — per-row failure must not abort batch
            if _try_mark_row_failed(row_id, str(exc)):
                failed += 1
            else:
                failed += 1
            logger.warning(
                "wecom_inbox_worker_row_failed_v1 %s",
                json.dumps(
                    {
                        "row_id": row_id,
                        "dedup_key": row.get("dedup_key"),
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                ),
            )

    summary = {
        "claimed": len(claimed_rows),
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
    }
    logger.info("wecom_inbox_worker_batch_v1 %s", json.dumps(summary, ensure_ascii=False))
    return summary
