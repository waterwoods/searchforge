"""WeCom outbound reply idempotency guard — same msg_id sends at most once.

Root cause this exists for: `process_kf_msg_or_event` can run more than once
for the exact same customer message (WeCom callback retry, `sync_msg` never
persists a cursor so an already-seen message can be re-delivered on the next
callback, or two Cloud Run instances handling overlapping requests). Without
a guard at the actual send boundary, each re-run independently decides to
send a reply, producing duplicate WeCom messages to the customer.

`claim_reply_send(msg_id)` is the single choke point: it returns True at most
once per msg_id — only that caller may perform the outbound `kf/send_msg`
call. Every other caller (retry, replay, concurrent instance) gets False and
must skip sending.

Durability model:
- When a Postgres URL is configured (the paid-pilot / Cloud Run case), the
  claim is a single atomic `INSERT ... ON CONFLICT DO NOTHING`, so the
  guarantee holds across process restarts and multiple Cloud Run instances.
  The table is created on first use (`CREATE TABLE IF NOT EXISTS`), the same
  pattern already used for `intake_sessions` — no separate migration step is
  required at deploy time.
- Without a database URL (local dev, unit tests), an in-process set gives
  best-effort same-process protection only.
- If the send itself fails after a successful claim, `release_reply_claim`
  frees the slot so a genuine retry can still deliver the reply — the
  guarantee is "never more than one successful send", not "never retry a
  failed send".
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url

logger = logging.getLogger(__name__)

_MEMORY_CLAIMED: set[str] = set()
_MEMORY_LOCK = threading.Lock()
_MAX_MEMORY_ROWS = 5000

_DDL_CHECKED = False
_DB_DEGRADED_LOGGED = False


def reset_reply_dedup_memory_for_tests() -> None:
    """Clear the in-process claim set. Tests only — not for production use."""
    with _MEMORY_LOCK:
        _MEMORY_CLAIMED.clear()


def _use_postgres() -> bool:
    return service_record_database_url() is not None


def _claim_in_memory(mid: str) -> bool:
    with _MEMORY_LOCK:
        if mid in _MEMORY_CLAIMED:
            return False
        if len(_MEMORY_CLAIMED) >= _MAX_MEMORY_ROWS:
            _MEMORY_CLAIMED.clear()
        _MEMORY_CLAIMED.add(mid)
        return True


def _release_in_memory(mid: str) -> None:
    with _MEMORY_LOCK:
        _MEMORY_CLAIMED.discard(mid)


def _ensure_table_once(cur: Any) -> None:
    global _DDL_CHECKED
    if _DDL_CHECKED:
        return
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS wecom_reply_dedup (
            msg_id TEXT PRIMARY KEY,
            claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    _DDL_CHECKED = True
    logger.info("wecom_reply_dedup DDL verified (create-if-not-exists)")


def _log_db_degraded(exc: BaseException, mid: str) -> None:
    global _DB_DEGRADED_LOGGED
    if not _DB_DEGRADED_LOGGED:
        _DB_DEGRADED_LOGGED = True
        logger.error(
            "wecom_reply_dedup_db_unavailable_v1 falling back to in-process guard only: %s [msg_id=%s]",
            exc,
            mid,
        )
    else:
        logger.debug("wecom_reply_dedup_db_error_v1: %s [msg_id=%s]", exc, mid)


def claim_reply_send(msg_id: str) -> bool:
    """
    Atomically claim the right to send exactly one reply for `msg_id`.

    Returns True the first time it is called for a given msg_id — the caller
    must proceed to send. Returns False on every subsequent call for the
    same msg_id — the caller must skip the send (already sent, or another
    caller is currently sending it).

    Never raises: on any unexpected DB error, degrades to the in-process
    guard so a single call site failure cannot silently disable the
    callback's "always return 200" contract.
    """
    mid = (msg_id or "").strip()
    if not mid:
        # No msg_id to key on. Callers already log "missing_ids" separately;
        # never suppress a reply just because we cannot dedup it.
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
                        INSERT INTO wecom_reply_dedup (msg_id)
                        VALUES (%(mid)s)
                        ON CONFLICT (msg_id) DO NOTHING
                        """,
                        {"mid": mid},
                    )
                    claimed = (cur.rowcount or 0) > 0
        if claimed:
            with _MEMORY_LOCK:
                _MEMORY_CLAIMED.add(mid)
        return claimed
    except Exception as exc:  # noqa: BLE001 — dedup errors must never block replies
        _log_db_degraded(exc, mid)
        return _claim_in_memory(mid)


def release_reply_claim(msg_id: str) -> None:
    """
    Free a previously claimed slot after the send attempt failed, so a
    genuine retry (WeCom redelivery, another callback) can try again.
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
                        "DELETE FROM wecom_reply_dedup WHERE msg_id = %(mid)s",
                        {"mid": mid},
                    )
    except Exception as exc:  # noqa: BLE001
        _log_db_degraded(exc, mid)
