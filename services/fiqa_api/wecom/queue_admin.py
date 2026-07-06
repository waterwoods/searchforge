"""WeCom queue admin — manual drain and status for operators (Q0.5).

Drains existing ``wecom_inbox_events`` and ``wecom_reply_outbox`` rows using the
same worker/sender functions as production. Does not enable feature flags or
enqueue new work — only processes rows already in Postgres.

Safe logging: counts and summaries only — never payload bodies.
"""

from __future__ import annotations

import json
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url
from services.fiqa_api.wecom.inbox_queue import _ensure_table_once as _ensure_inbox_table_once
from services.fiqa_api.wecom.inbox_worker import (
    _DEFAULT_MAX_ATTEMPTS as _INBOX_DEFAULT_MAX_ATTEMPTS,
)
from services.fiqa_api.wecom.inbox_worker import (
    _DEFAULT_STALE_TIMEOUT_SECONDS as _INBOX_DEFAULT_STALE_TIMEOUT,
)
from services.fiqa_api.wecom.inbox_worker import process_pending_wecom_inbox_events
from services.fiqa_api.wecom.queue_db import (
    WeComQueueDbError,
    preflight_wecom_queue_db,
)
from services.fiqa_api.wecom.reply_outbox import (
    _ensure_table_once as _ensure_outbox_table_once,
)
from services.fiqa_api.wecom.reply_outbox import process_pending_wecom_reply_outbox

_DB_REQUIRED_ERROR = (
    "wecom_queue_admin_db_required_v1: set SERVICE_RECORD_DATABASE_URL "
    "(or DATABASE_URL) to drain or inspect WeCom queue tables"
)


def require_service_record_database_url() -> str:
    """Return configured Postgres URL or raise with a clear operator message."""
    url = service_record_database_url()
    if not url:
        raise RuntimeError(_DB_REQUIRED_ERROR)
    return url


def _run_db_preflight() -> dict[str, Any]:
    """Preflight Postgres before admin status/drain/repair — fail closed on error."""
    try:
        return preflight_wecom_queue_db()
    except WeComQueueDbError as exc:
        raise RuntimeError(str(exc)) from exc


def _count_inbox_by_status(cur: Any) -> dict[str, int]:
    cur.execute(
        """
        SELECT status, COUNT(*)::int AS n
        FROM wecom_inbox_events
        GROUP BY status
        """
    )
    rows = cur.fetchall()
    counts = {str(row["status"]): int(row["n"]) for row in rows}
    return {
        "pending": counts.get("pending", 0),
        "processing": counts.get("processing", 0),
        "processed": counts.get("processed", 0),
        "failed": counts.get("failed", 0),
    }


def _count_outbox_by_status(cur: Any) -> dict[str, int]:
    cur.execute(
        """
        SELECT status, COUNT(*)::int AS n
        FROM wecom_reply_outbox
        GROUP BY status
        """
    )
    rows = cur.fetchall()
    counts = {str(row["status"]): int(row["n"]) for row in rows}
    return {
        "pending": counts.get("pending", 0),
        "sending": counts.get("sending", 0),
        "sent": counts.get("sent", 0),
        "failed": counts.get("failed", 0),
    }


def _count_inbox_stale(cur: Any, *, stale_timeout_seconds: int) -> int:
    cur.execute(
        """
        SELECT COUNT(*)::int AS n
        FROM wecom_inbox_events
        WHERE status = 'processing'
          AND locked_at IS NOT NULL
          AND locked_at < NOW() - (%(stale_timeout_seconds)s * INTERVAL '1 second')
        """,
        {"stale_timeout_seconds": stale_timeout_seconds},
    )
    row = cur.fetchone()
    return int((row or {}).get("n") or 0)


def _count_outbox_stale(cur: Any, *, stale_timeout_seconds: int) -> int:
    cur.execute(
        """
        SELECT COUNT(*)::int AS n
        FROM wecom_reply_outbox
        WHERE status = 'sending'
          AND locked_at IS NOT NULL
          AND locked_at < NOW() - (%(stale_timeout_seconds)s * INTERVAL '1 second')
        """,
        {"stale_timeout_seconds": stale_timeout_seconds},
    )
    row = cur.fetchone()
    return int((row or {}).get("n") or 0)


def _count_inbox_exhausted(cur: Any, *, max_attempts: int) -> int:
    cur.execute(
        """
        SELECT COUNT(*)::int AS n
        FROM wecom_inbox_events
        WHERE attempt_count >= %(max_attempts)s
          AND status IN ('pending', 'processing')
        """,
        {"max_attempts": max_attempts},
    )
    row = cur.fetchone()
    return int((row or {}).get("n") or 0)


def _count_outbox_exhausted(cur: Any, *, max_attempts: int) -> int:
    cur.execute(
        """
        SELECT COUNT(*)::int AS n
        FROM wecom_reply_outbox
        WHERE attempt_count >= %(max_attempts)s
          AND status IN ('pending', 'sending')
        """,
        {"max_attempts": max_attempts},
    )
    row = cur.fetchone()
    return int((row or {}).get("n") or 0)


def fetch_wecom_queue_status(
    *,
    max_attempts: int = _INBOX_DEFAULT_MAX_ATTEMPTS,
    stale_timeout_seconds: int = _INBOX_DEFAULT_STALE_TIMEOUT,
) -> dict[str, Any]:
    """
    Status-only snapshot — no drain, no side effects beyond DDL ensure.

    Returns inbox/outbox row counts by status plus stale and exhausted counts.
    """
    db_preflight = _run_db_preflight()
    from psycopg.rows import dict_row

    from services.fiqa_api.db.service_record_repository import service_record_connection

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                _ensure_inbox_table_once(cur)
                _ensure_outbox_table_once(cur)
                inbox = _count_inbox_by_status(cur)
                outbox = _count_outbox_by_status(cur)
                inbox_stale = _count_inbox_stale(cur, stale_timeout_seconds=stale_timeout_seconds)
                outbox_stale = _count_outbox_stale(cur, stale_timeout_seconds=stale_timeout_seconds)
                inbox_exhausted = _count_inbox_exhausted(cur, max_attempts=max_attempts)
                outbox_exhausted = _count_outbox_exhausted(cur, max_attempts=max_attempts)

    return {
        "mode": "status",
        "db_preflight": db_preflight,
        "max_attempts": max_attempts,
        "stale_timeout_seconds": stale_timeout_seconds,
        "inbox": {
            **inbox,
            "processing_stale": inbox_stale,
            "exhausted": inbox_exhausted,
        },
        "outbox": {
            **outbox,
            "sending_stale": outbox_stale,
            "exhausted": outbox_exhausted,
        },
    }


def drain_wecom_queues(
    limit: int = 10,
    *,
    max_attempts: int = _INBOX_DEFAULT_MAX_ATTEMPTS,
    stale_timeout_seconds: int = _INBOX_DEFAULT_STALE_TIMEOUT,
) -> dict[str, Any]:
    """
    Manually drain inbox then reply outbox — one batch each, in order.

    Reuses ``process_pending_wecom_inbox_events`` and
    ``process_pending_wecom_reply_outbox``. Does not toggle feature flags.

    **Transaction safety (Q0.8.3):** Preflight runs before any row is claimed.
    Rows are claimed in one DB transaction, processed outside it, then marked
    processed/failed in separate transactions. If marking fails due to a DB flap,
    the row stays ``processing`` until ``stale_timeout_seconds`` elapses; the
    worker then reclaims it (``stale_reclaim``) or use ``repair_stale_wecom_queue_rows``.
    """
    _run_db_preflight()
    if limit < 1:
        raise ValueError("wecom_queue_admin_invalid_limit_v1: limit must be >= 1")

    try:
        inbox_summary = process_pending_wecom_inbox_events(
            limit=limit,
            max_attempts=max_attempts,
            stale_timeout_seconds=stale_timeout_seconds,
        )
        outbox_summary = process_pending_wecom_reply_outbox(
            limit=limit,
            max_attempts=max_attempts,
            stale_timeout_seconds=stale_timeout_seconds,
        )
    except Exception as exc:  # noqa: BLE001 — convert DB flap mid-drain to clear operator error
        raise RuntimeError(
            f"wecom_queue_admin_drain_failed_v1: drain aborted — no new rows claimed "
            f"after preflight; if rows are stuck in processing, run repair-stale: {exc}"
        ) from exc
    return {
        "mode": "drain",
        "limit": limit,
        "max_attempts": max_attempts,
        "stale_timeout_seconds": stale_timeout_seconds,
        "inbox": inbox_summary,
        "outbox": outbox_summary,
    }


def _scalar_count(row: Any) -> int:
    if row is None:
        return 0
    if isinstance(row, dict):
        return int(row.get("n") or 0)
    return int(row[0] or 0)


def repair_stale_wecom_queue_rows(
    *,
    stale_timeout_seconds: int = _INBOX_DEFAULT_STALE_TIMEOUT,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Reset stale locked inbox/outbox rows back to pending.

    Only touches rows where ``locked_at`` is older than ``stale_timeout_seconds``.
    Fresh ``processing`` / ``sending`` rows are never modified.

    Prefer this over ad-hoc SQL when Cloud Run drain left rows stuck after a DB flap.
    Normal drain also reclaims stale rows automatically on the next claim batch.
    """
    _run_db_preflight()
    from services.fiqa_api.db.service_record_repository import service_record_connection

    inbox_repaired = 0
    outbox_repaired = 0

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                if dry_run:
                    cur.execute(
                        """
                        SELECT COUNT(*)::int AS n
                        FROM wecom_inbox_events
                        WHERE status = 'processing'
                          AND locked_at IS NOT NULL
                          AND locked_at < NOW() - (%(stale_timeout_seconds)s * INTERVAL '1 second')
                        """,
                        {"stale_timeout_seconds": stale_timeout_seconds},
                    )
                    inbox_repaired = _scalar_count(cur.fetchone())
                    cur.execute(
                        """
                        SELECT COUNT(*)::int AS n
                        FROM wecom_reply_outbox
                        WHERE status = 'sending'
                          AND locked_at IS NOT NULL
                          AND locked_at < NOW() - (%(stale_timeout_seconds)s * INTERVAL '1 second')
                        """,
                        {"stale_timeout_seconds": stale_timeout_seconds},
                    )
                    outbox_repaired = _scalar_count(cur.fetchone())
                else:
                    cur.execute(
                        """
                        UPDATE wecom_inbox_events
                        SET status = 'pending',
                            locked_at = NULL,
                            updated_at = NOW()
                        WHERE status = 'processing'
                          AND locked_at IS NOT NULL
                          AND locked_at < NOW() - (%(stale_timeout_seconds)s * INTERVAL '1 second')
                        """,
                        {"stale_timeout_seconds": stale_timeout_seconds},
                    )
                    inbox_repaired = int(cur.rowcount or 0)
                    cur.execute(
                        """
                        UPDATE wecom_reply_outbox
                        SET status = 'pending',
                            locked_at = NULL,
                            updated_at = NOW()
                        WHERE status = 'sending'
                          AND locked_at IS NOT NULL
                          AND locked_at < NOW() - (%(stale_timeout_seconds)s * INTERVAL '1 second')
                        """,
                        {"stale_timeout_seconds": stale_timeout_seconds},
                    )
                    outbox_repaired = int(cur.rowcount or 0)

    return {
        "mode": "repair_stale",
        "dry_run": dry_run,
        "stale_timeout_seconds": stale_timeout_seconds,
        "inbox_repaired": inbox_repaired,
        "outbox_repaired": outbox_repaired,
    }


def format_wecom_queue_report(result: dict[str, Any]) -> str:
    """Operator-friendly text summary — no payload bodies."""
    mode = str(result.get("mode") or "unknown")
    lines = [
        "WeCom Queue Report",
        "==================",
        f"mode: {mode}",
    ]

    if mode == "status":
        lines.append(f"max_attempts: {result.get('max_attempts')}")
        lines.append(f"stale_timeout_seconds: {result.get('stale_timeout_seconds')}")
        lines.append("")
        lines.append("Inbox (wecom_inbox_events)")
        inbox = result.get("inbox") or {}
        lines.extend(
            [
                f"  pending:            {inbox.get('pending', 0)}",
                f"  processing:         {inbox.get('processing', 0)}",
                f"  processing_stale:   {inbox.get('processing_stale', 0)}",
                f"  failed:             {inbox.get('failed', 0)}",
                f"  processed:          {inbox.get('processed', 0)}",
                f"  exhausted:          {inbox.get('exhausted', 0)}",
            ]
        )
        lines.append("")
        lines.append("Outbox (wecom_reply_outbox)")
        outbox = result.get("outbox") or {}
        lines.extend(
            [
                f"  pending:            {outbox.get('pending', 0)}",
                f"  sending:            {outbox.get('sending', 0)}",
                f"  sending_stale:      {outbox.get('sending_stale', 0)}",
                f"  failed:             {outbox.get('failed', 0)}",
                f"  sent:               {outbox.get('sent', 0)}",
                f"  exhausted:          {outbox.get('exhausted', 0)}",
            ]
        )
    elif mode == "repair_stale":
        lines.append(f"dry_run: {result.get('dry_run')}")
        lines.append(f"stale_timeout_seconds: {result.get('stale_timeout_seconds')}")
        lines.append(f"inbox_repaired:  {result.get('inbox_repaired', 0)}")
        lines.append(f"outbox_repaired: {result.get('outbox_repaired', 0)}")
    elif mode == "drain":
        lines.append(f"limit: {result.get('limit')}")
        lines.append(f"max_attempts: {result.get('max_attempts')}")
        lines.append(f"stale_timeout_seconds: {result.get('stale_timeout_seconds')}")
        lines.append("")
        lines.append("Inbox worker")
        inbox = result.get("inbox") or {}
        lines.extend(
            [
                f"  claimed:   {inbox.get('claimed', 0)}",
                f"  processed: {inbox.get('processed', 0)}",
                f"  failed:    {inbox.get('failed', 0)}",
                f"  skipped:   {inbox.get('skipped', 0)}",
            ]
        )
        lines.append("")
        lines.append("Reply outbox sender")
        outbox = result.get("outbox") or {}
        lines.extend(
            [
                f"  claimed:   {outbox.get('claimed', 0)}",
                f"  sent:      {outbox.get('sent', 0)}",
                f"  failed:    {outbox.get('failed', 0)}",
                f"  skipped:   {outbox.get('skipped', 0)}",
            ]
        )
    else:
        lines.append(json.dumps(result, ensure_ascii=False, indent=2))

    return "\n".join(lines)
