"""Persist WeCom kf/sync_msg next_cursor per open_kf_id (Q0.10)."""

from __future__ import annotations

import logging
from typing import Any

from services.fiqa_api.db.service_record_settings import service_record_database_url

logger = logging.getLogger(__name__)

_DDL_CHECKED = False
_MEMORY_CURSORS: dict[str, str] = {}


def reset_sync_cursor_memory_for_tests() -> None:
    """Clear in-process cursor store. Tests only."""
    _MEMORY_CURSORS.clear()


def _use_postgres() -> bool:
    return service_record_database_url() is not None


def _ensure_table_once(cur: Any) -> None:
    global _DDL_CHECKED
    if _DDL_CHECKED:
        return
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS wecom_sync_cursors (
            open_kf_id TEXT PRIMARY KEY,
            cursor TEXT,
            last_sync_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    _DDL_CHECKED = True
    logger.info("wecom_sync_cursors DDL verified (create-if-not-exists)")


def load_sync_cursor(open_kf_id: str) -> str:
    """Return stored cursor for ``open_kf_id``, or empty string when unset."""
    kf = (open_kf_id or "").strip()
    if not kf:
        return ""
    if not _use_postgres():
        return _MEMORY_CURSORS.get(kf, "")

    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.cursor() as cur:
                _ensure_table_once(cur)
                cur.execute(
                    "SELECT cursor FROM wecom_sync_cursors WHERE open_kf_id = %(kf)s",
                    {"kf": kf},
                )
                row = cur.fetchone()
        if not row or row[0] is None:
            return ""
        return str(row[0])
    except Exception as exc:  # noqa: BLE001
        logger.debug("wecom_sync_cursor_load_failed_v1 open_kf_id=%s err=%s", kf, exc)
        return _MEMORY_CURSORS.get(kf, "")


def save_sync_cursor(open_kf_id: str, cursor: str) -> None:
    """Persist ``next_cursor`` after a successful sync batch."""
    kf = (open_kf_id or "").strip()
    cur = (cursor or "").strip()
    if not kf or not cur:
        return
    if not _use_postgres():
        _MEMORY_CURSORS[kf] = cur
        return

    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur_obj:
                    _ensure_table_once(cur_obj)
                    cur_obj.execute(
                        """
                        INSERT INTO wecom_sync_cursors (open_kf_id, cursor, last_sync_at, updated_at)
                        VALUES (%(kf)s, %(cursor)s, NOW(), NOW())
                        ON CONFLICT (open_kf_id) DO UPDATE SET
                            cursor = EXCLUDED.cursor,
                            last_sync_at = EXCLUDED.last_sync_at,
                            updated_at = NOW()
                        """,
                        {"kf": kf, "cursor": cur},
                    )
        _MEMORY_CURSORS[kf] = cur
        logger.info(
            "wecom_sync_cursor_saved_v1 %s",
            {"open_kf_id": kf, "cursor_len": len(cur)},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("wecom_sync_cursor_save_failed_v1 open_kf_id=%s err=%s", kf, exc)
