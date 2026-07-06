"""In-memory Postgres stand-in for WeCom queued pipeline e2e tests (Q0.4).

Supports wecom_inbox_events, wecom_reply_outbox, and wecom_reply_dedup in one
connection so callback → inbox worker → reply outbox → sender tests can run
without a real database.
"""

from __future__ import annotations

import contextlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any


class InMemoryWeComPipelineDb:
    """Minimal multi-table Postgres fake for WeCom queue + outbox pipeline tests."""

    def __init__(self) -> None:
        self._next_inbox_id = 1
        self._next_outbox_id = 1
        self.inbox_rows: dict[int, dict[str, Any]] = {}
        self.outbox_rows: dict[int, dict[str, Any]] = {}
        self.reply_dedup: set[str] = set()
        self.message_processed: set[str] = set()
        self.sync_cursors: dict[str, str] = {}
        self._txn_locked: set[int] = set()
        self._claim_params: dict[str, Any] = {}

    @property
    def inbox_by_status(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in self.inbox_rows.values():
            grouped.setdefault(str(row["status"]), []).append(row)
        return grouped

    @property
    def outbox_by_status(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in self.outbox_rows.values():
            grouped.setdefault(str(row["status"]), []).append(row)
        return grouped

    def begin_txn(self) -> None:
        self._txn_locked.clear()

    def end_txn(self) -> None:
        self._txn_locked.clear()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _is_stale(self, row: dict[str, Any], *, status: str) -> bool:
        stale_seconds = int(self._claim_params.get("stale_timeout_seconds", 600))
        locked_at = row.get("locked_at")
        if locked_at is None or row.get("status") != status:
            return False
        if locked_at.tzinfo is None:
            locked_at = locked_at.replace(tzinfo=timezone.utc)
        cutoff = self._now() - timedelta(seconds=stale_seconds)
        return locked_at < cutoff

    def _is_inbox_claimable(self, row: dict[str, Any]) -> bool:
        max_attempts = int(self._claim_params.get("max_attempts", 3))
        if int(row.get("attempt_count") or 0) >= max_attempts:
            return False
        if row["status"] == "pending":
            return True
        if row["status"] == "processing":
            return self._is_stale(row, status="processing")
        return False

    def _is_outbox_claimable(self, row: dict[str, Any]) -> bool:
        max_attempts = int(self._claim_params.get("max_attempts", 3))
        if int(row.get("attempt_count") or 0) >= max_attempts:
            return False
        if row["status"] == "pending":
            return True
        if row["status"] == "sending":
            return self._is_stale(row, status="sending")
        return False

    def execute(self, sql: str, params: dict | None = None) -> tuple[list[dict[str, Any]], int]:
        """Return (rows, rowcount) — rowcount is set for INSERT dedup checks."""
        params = params or {}
        normalized = " ".join(sql.split())
        rowcount = 0

        if normalized == "SELECT 1":
            return [{"?column?": 1}], 0

        if "FROM wecom_inbox_events LIMIT 0" in normalized:
            return [], 0

        if "FROM wecom_reply_outbox LIMIT 0" in normalized:
            return [], 0

        if normalized.startswith("CREATE TABLE") or normalized.startswith("CREATE INDEX"):
            return [], 0

        if "wecom_reply_dedup" in normalized and normalized.startswith("INSERT INTO"):
            mid = str(params.get("mid") or "").strip()
            if mid and mid not in self.reply_dedup:
                self.reply_dedup.add(mid)
                rowcount = 1
            return [], rowcount

        if "wecom_reply_dedup" in normalized and normalized.startswith("DELETE FROM"):
            mid = str(params.get("mid") or "").strip()
            if mid in self.reply_dedup:
                self.reply_dedup.discard(mid)
            return [], 0

        if "wecom_message_processed" in normalized and normalized.startswith("INSERT INTO"):
            mid = str(params.get("msg_id") or "").strip()
            if mid and mid not in self.message_processed:
                self.message_processed.add(mid)
                rowcount = 1
            return [], rowcount

        if "wecom_message_processed" in normalized and normalized.startswith("DELETE FROM"):
            mid = str(params.get("msg_id") or "").strip()
            self.message_processed.discard(mid)
            return [], 0

        if "wecom_message_processed" in normalized and normalized.startswith("UPDATE"):
            return [], 0

        if "wecom_sync_cursors" in normalized and "SELECT cursor FROM" in normalized:
            kf = str(params.get("kf") or "").strip()
            cursor = self.sync_cursors.get(kf)
            if cursor is None:
                return [], 0
            return [{"cursor": cursor}], 0

        if "wecom_sync_cursors" in normalized and normalized.startswith("INSERT INTO"):
            kf = str(params.get("kf") or "").strip()
            cursor = str(params.get("cursor") or "").strip()
            if kf and cursor:
                self.sync_cursors[kf] = cursor
                rowcount = 1
            return [], rowcount

        if "wecom_inbox_events" in normalized and "SELECT COUNT(*) AS n" in normalized:
            max_attempts = int(params.get("max_attempts", 3))
            count = sum(
                1
                for row in self.inbox_rows.values()
                if int(row.get("attempt_count") or 0) >= max_attempts
                and row["status"] in ("pending", "processing")
            )
            return [{"n": count}], 0

        if "wecom_reply_outbox" in normalized and "SELECT COUNT(*) AS n" in normalized:
            max_attempts = int(params.get("max_attempts", 3))
            count = sum(
                1
                for row in self.outbox_rows.values()
                if int(row.get("attempt_count") or 0) >= max_attempts
                and row["status"] in ("pending", "sending")
            )
            return [{"n": count}], 0

        if "FROM wecom_inbox_events" in normalized and "FOR UPDATE SKIP LOCKED" in normalized:
            self._claim_params = {
                "max_attempts": int(params.get("max_attempts", 3)),
                "stale_timeout_seconds": int(params.get("stale_timeout_seconds", 600)),
            }
            limit = int(params.get("limit", 10))
            eligible = [
                row
                for row in sorted(self.inbox_rows.values(), key=lambda r: r["created_at"])
                if self._is_inbox_claimable(row) and row["id"] not in self._txn_locked
            ][:limit]
            for row in eligible:
                self._txn_locked.add(row["id"])
            return [dict(r) for r in eligible], 0

        if "FROM wecom_reply_outbox" in normalized and "FOR UPDATE SKIP LOCKED" in normalized:
            self._claim_params = {
                "max_attempts": int(params.get("max_attempts", 3)),
                "stale_timeout_seconds": int(params.get("stale_timeout_seconds", 600)),
            }
            limit = int(params.get("limit", 10))
            eligible = [
                row
                for row in sorted(self.outbox_rows.values(), key=lambda r: r["created_at"])
                if self._is_outbox_claimable(row) and row["id"] not in self._txn_locked
            ][:limit]
            for row in eligible:
                self._txn_locked.add(row["id"])
            return [dict(r) for r in eligible], 0

        if normalized.startswith("UPDATE wecom_inbox_events") and params.get("id") is not None:
            row = self.inbox_rows.get(params["id"])
            if row is not None:
                if "status = 'processing'" in normalized:
                    row["status"] = "processing"
                    row["attempt_count"] = int(row["attempt_count"]) + 1
                    row["locked_at"] = self._now()
                    row["updated_at"] = row["locked_at"]
                elif "status = 'processed'" in normalized:
                    row["status"] = "processed"
                    row["processed_at"] = self._now()
                    row["updated_at"] = row["processed_at"]
                    row["error_message"] = None
                elif "status = 'failed'" in normalized:
                    row["status"] = "failed"
                    row["updated_at"] = self._now()
                    row["error_message"] = params.get("error_message")
            return [], 0

        if normalized.startswith("UPDATE wecom_reply_outbox") and params.get("id") is not None:
            row = self.outbox_rows.get(params["id"])
            if row is not None:
                if "status = 'sending'" in normalized:
                    row["status"] = "sending"
                    row["attempt_count"] = int(row["attempt_count"]) + 1
                    row["locked_at"] = self._now()
                    row["updated_at"] = row["locked_at"]
                elif "status = 'sent'" in normalized:
                    row["status"] = "sent"
                    row["sent_at"] = self._now()
                    row["updated_at"] = row["sent_at"]
                    row["errcode"] = params.get("errcode")
                    row["errmsg"] = params.get("errmsg")
                    row["error_message"] = None
                    row["failed_at"] = None
                elif "status = 'failed'" in normalized:
                    row["status"] = "failed"
                    row["failed_at"] = self._now()
                    row["updated_at"] = row["failed_at"]
                    row["errcode"] = params.get("errcode")
                    row["errmsg"] = params.get("errmsg")
                    row["error_message"] = params.get("error_message")
            return [], 0

        if "wecom_inbox_events" in normalized and "GROUP BY status" in normalized:
            counts: dict[str, int] = {}
            for row in self.inbox_rows.values():
                status = str(row["status"])
                counts[status] = counts.get(status, 0) + 1
            return [{"status": status, "n": count} for status, count in sorted(counts.items())], 0

        if "wecom_reply_outbox" in normalized and "GROUP BY status" in normalized:
            counts = {}
            for row in self.outbox_rows.values():
                status = str(row["status"])
                counts[status] = counts.get(status, 0) + 1
            return [{"status": status, "n": count} for status, count in sorted(counts.items())], 0

        if (
            "wecom_inbox_events" in normalized
            and "SELECT COUNT(*)" in normalized
            and "status = 'processing'" in normalized
            and "locked_at < NOW()" in normalized
        ):
            stale_seconds = int(params.get("stale_timeout_seconds", 600))
            cutoff = self._now() - timedelta(seconds=stale_seconds)
            count = sum(
                1
                for row in self.inbox_rows.values()
                if row["status"] == "processing"
                and row.get("locked_at") is not None
                and (
                    row["locked_at"].replace(tzinfo=timezone.utc)
                    if row["locked_at"].tzinfo is None
                    else row["locked_at"]
                )
                < cutoff
            )
            return [{"n": count}], 0

        if (
            "wecom_reply_outbox" in normalized
            and "SELECT COUNT(*)" in normalized
            and "status = 'sending'" in normalized
            and "locked_at < NOW()" in normalized
        ):
            stale_seconds = int(params.get("stale_timeout_seconds", 600))
            cutoff = self._now() - timedelta(seconds=stale_seconds)
            count = sum(
                1
                for row in self.outbox_rows.values()
                if row["status"] == "sending"
                and row.get("locked_at") is not None
                and (
                    row["locked_at"].replace(tzinfo=timezone.utc)
                    if row["locked_at"].tzinfo is None
                    else row["locked_at"]
                )
                < cutoff
            )
            return [{"n": count}], 0

        if (
            "wecom_inbox_events" in normalized
            and "attempt_count >=" in normalized
            and "status IN ('pending', 'processing')" in normalized
        ):
            max_attempts = int(params.get("max_attempts", 3))
            count = sum(
                1
                for row in self.inbox_rows.values()
                if int(row.get("attempt_count") or 0) >= max_attempts
                and row["status"] in ("pending", "processing")
            )
            return [{"n": count}], 0

        if (
            "wecom_reply_outbox" in normalized
            and "attempt_count >=" in normalized
            and "status IN ('pending', 'sending')" in normalized
        ):
            max_attempts = int(params.get("max_attempts", 3))
            count = sum(
                1
                for row in self.outbox_rows.values()
                if int(row.get("attempt_count") or 0) >= max_attempts
                and row["status"] in ("pending", "sending")
            )
            return [{"n": count}], 0

        if (
            "wecom_inbox_events" in normalized
            and "SET status = 'pending'" in normalized
            and "status = 'processing'" in normalized
        ):
            stale_seconds = int(params.get("stale_timeout_seconds", 600))
            cutoff = self._now() - timedelta(seconds=stale_seconds)
            repaired = 0
            for row in self.inbox_rows.values():
                if row["status"] != "processing" or row.get("locked_at") is None:
                    continue
                locked_at = row["locked_at"]
                if locked_at.tzinfo is None:
                    locked_at = locked_at.replace(tzinfo=timezone.utc)
                if locked_at < cutoff:
                    row["status"] = "pending"
                    row["locked_at"] = None
                    row["updated_at"] = self._now()
                    repaired += 1
            return [], repaired

        if (
            "wecom_reply_outbox" in normalized
            and "SET status = 'pending'" in normalized
            and "status = 'sending'" in normalized
        ):
            stale_seconds = int(params.get("stale_timeout_seconds", 600))
            cutoff = self._now() - timedelta(seconds=stale_seconds)
            repaired = 0
            for row in self.outbox_rows.values():
                if row["status"] != "sending" or row.get("locked_at") is None:
                    continue
                locked_at = row["locked_at"]
                if locked_at.tzinfo is None:
                    locked_at = locked_at.replace(tzinfo=timezone.utc)
                if locked_at < cutoff:
                    row["status"] = "pending"
                    row["locked_at"] = None
                    row["updated_at"] = self._now()
                    repaired += 1
            return [], repaired

        if normalized.startswith("INSERT INTO wecom_inbox_events"):
            key = params["dedup_key"]
            existing = next((r for r in self.inbox_rows.values() if r["dedup_key"] == key), None)
            if existing:
                return [], 0
            row_id = self._next_inbox_id
            self._next_inbox_id += 1
            now = self._now()
            payload = params.get("payload_json")
            if isinstance(payload, str):
                payload = json.loads(payload)
            self.inbox_rows[row_id] = {
                "id": row_id,
                "dedup_key": key,
                "open_kf_id": params.get("open_kf_id"),
                "external_userid": params.get("external_userid"),
                "callback_token": params.get("callback_token"),
                "event_type": params.get("event_type"),
                "payload_json": payload,
                "status": "pending",
                "attempt_count": 0,
                "locked_at": None,
                "processed_at": None,
                "error_message": None,
                "created_at": now,
                "updated_at": now,
            }
            return [], 1

        if normalized.startswith("INSERT INTO wecom_reply_outbox"):
            key = params["dedup_key"]
            existing = next((r for r in self.outbox_rows.values() if r["dedup_key"] == key), None)
            if existing:
                return [], 0
            row_id = self._next_outbox_id
            self._next_outbox_id += 1
            now = self._now()
            payload = params.get("reply_payload_json")
            if isinstance(payload, str):
                payload = json.loads(payload)
            self.outbox_rows[row_id] = {
                "id": row_id,
                "dedup_key": key,
                "msg_id": params.get("msg_id"),
                "external_userid": params.get("external_userid"),
                "open_kf_id": params.get("open_kf_id"),
                "case_id": params.get("case_id"),
                "reply_type": params.get("reply_type"),
                "reply_payload_json": payload,
                "status": "pending",
                "attempt_count": 0,
                "locked_at": None,
                "sent_at": None,
                "failed_at": None,
                "errcode": None,
                "errmsg": None,
                "error_message": None,
                "created_at": now,
                "updated_at": now,
            }
            return [], 1

        return [], 0


class _PipelineFakeCursor:
    def __init__(self, db: InMemoryWeComPipelineDb):
        self._db = db
        self._rows: list[dict[str, Any]] = []
        self.rowcount = 0

    def execute(self, sql: str, params: dict | tuple | None = None) -> None:
        if params is None:
            params = {}
        elif not isinstance(params, dict):
            raise TypeError("expected dict params")
        self._rows, self.rowcount = self._db.execute(sql, params)

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self._rows)

    def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _PipelineFakeTransaction:
    def __init__(self, db: InMemoryWeComPipelineDb):
        self._db = db

    def __enter__(self):
        self._db.begin_txn()
        return self

    def __exit__(self, *exc):
        self._db.end_txn()
        return False


class _PipelineFakeConnection:
    def __init__(self, db: InMemoryWeComPipelineDb):
        self._db = db

    def transaction(self):
        return _PipelineFakeTransaction(self._db)

    def cursor(self, row_factory=None):
        return _PipelineFakeCursor(self._db)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def install_pipeline_db(monkeypatch, db: InMemoryWeComPipelineDb) -> None:
    """Wire the in-memory DB into service_record_connection for tests."""

    @contextlib.contextmanager
    def fake_connection():
        yield _PipelineFakeConnection(db)

    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/wecom_pipeline")
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        fake_connection,
    )
