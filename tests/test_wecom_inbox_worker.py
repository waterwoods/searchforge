"""Tests for WeCom inbox worker (Q0.2 / Q0.2.1)."""

from __future__ import annotations

import contextlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from services.fiqa_api.routes.wecom_kf_callback import router as wecom_kf_router
from services.fiqa_api.wecom import inbox_queue, inbox_worker
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.crypto.WXBizMsgCrypt3 import WXBizMsgCrypt
from tests.test_wecom_kf_callback import (
    SAMPLE_KF_EVENT_XML,
    _build_post_request,
    _test_credentials,
)
from tests.wecom_pipeline_test_db import InMemoryWeComPipelineDb, install_pipeline_db

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    monkeypatch.delenv("WECOM_INBOX_QUEUE", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    load_wecom_kf_config.cache_clear()
    inbox_queue.reset_wecom_inbox_memory_for_tests()
    yield
    inbox_queue.reset_wecom_inbox_memory_for_tests()
    load_wecom_kf_config.cache_clear()


@pytest.fixture
def wecom_env(monkeypatch):
    token, encoding_aes_key, corp_id = _test_credentials()
    monkeypatch.setenv("WECOM_KF_TOKEN", token)
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", encoding_aes_key)
    monkeypatch.setenv("WECOM_CORP_ID", corp_id)
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    return token, encoding_aes_key, corp_id


class _InMemoryInboxTable:
    """Minimal Postgres stand-in for wecom_inbox_events worker tests."""

    def __init__(self) -> None:
        self._next_id = 1
        self.rows: dict[int, dict[str, Any]] = {}
        self._txn_locked: set[int] = set()
        self._claim_params: dict[str, Any] = {}

    def seed_pending(
        self,
        *,
        dedup_key: str,
        open_kf_id: str = "wk1",
        callback_token: str = "tok1",
        event_type: str = "kf_msg_or_event",
        payload_json: dict | None = None,
        attempt_count: int = 0,
    ) -> int:
        row_id = self._next_id
        self._next_id += 1
        now = datetime.now(timezone.utc)
        self.rows[row_id] = {
            "id": row_id,
            "dedup_key": dedup_key,
            "open_kf_id": open_kf_id,
            "external_userid": None,
            "callback_token": callback_token,
            "event_type": event_type,
            "payload_json": payload_json
            or {
                "event": event_type,
                "open_kf_id": open_kf_id,
                "token": callback_token,
            },
            "status": "pending",
            "attempt_count": attempt_count,
            "locked_at": None,
            "processed_at": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
        return row_id

    def seed_processing(
        self,
        *,
        dedup_key: str,
        locked_at: datetime,
        open_kf_id: str = "wk1",
        callback_token: str = "tok1",
        event_type: str = "kf_msg_or_event",
        attempt_count: int = 1,
        payload_json: dict | None = None,
    ) -> int:
        row_id = self._next_id
        self._next_id += 1
        now = datetime.now(timezone.utc)
        self.rows[row_id] = {
            "id": row_id,
            "dedup_key": dedup_key,
            "open_kf_id": open_kf_id,
            "external_userid": None,
            "callback_token": callback_token,
            "event_type": event_type,
            "payload_json": payload_json
            or {
                "event": event_type,
                "open_kf_id": open_kf_id,
                "token": callback_token,
            },
            "status": "processing",
            "attempt_count": attempt_count,
            "locked_at": locked_at,
            "processed_at": None,
            "error_message": None,
            "created_at": now,
            "updated_at": locked_at,
        }
        return row_id

    def begin_txn(self) -> None:
        self._txn_locked.clear()

    def end_txn(self) -> None:
        self._txn_locked.clear()

    def _is_stale(self, row: dict[str, Any]) -> bool:
        stale_seconds = int(self._claim_params.get("stale_timeout_seconds", 600))
        locked_at = row.get("locked_at")
        if locked_at is None:
            return False
        if locked_at.tzinfo is None:
            locked_at = locked_at.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_seconds)
        return locked_at < cutoff

    def _is_claimable(self, row: dict[str, Any]) -> bool:
        max_attempts = int(self._claim_params.get("max_attempts", 3))
        if int(row.get("attempt_count") or 0) >= max_attempts:
            return False
        if row["status"] == "pending":
            return True
        if row["status"] == "processing" and row.get("locked_at") is not None:
            return self._is_stale(row)
        return False

    def execute(self, sql: str, params: dict | None = None) -> list[dict[str, Any]]:
        params = params or {}
        normalized = " ".join(sql.split())

        if normalized.startswith("CREATE TABLE") or normalized.startswith("CREATE INDEX"):
            return []

        if "SELECT COUNT(*) AS n" in normalized and "attempt_count >=" in normalized:
            max_attempts = int(params.get("max_attempts", 3))
            count = sum(
                1
                for row in self.rows.values()
                if int(row.get("attempt_count") or 0) >= max_attempts
                and row["status"] in ("pending", "processing")
            )
            return [{"n": count}]

        if "FROM wecom_inbox_events" in normalized and "FOR UPDATE SKIP LOCKED" in normalized:
            self._claim_params = {
                "max_attempts": int(params.get("max_attempts", 3)),
                "stale_timeout_seconds": int(params.get("stale_timeout_seconds", 600)),
            }
            limit = int(params.get("limit", 10))
            eligible = [
                row
                for row in sorted(self.rows.values(), key=lambda r: r["created_at"])
                if self._is_claimable(row) and row["id"] not in self._txn_locked
            ][:limit]
            for row in eligible:
                self._txn_locked.add(row["id"])
            return [dict(r) for r in eligible]

        if normalized.startswith("UPDATE wecom_inbox_events") and params.get("id") is not None:
            row = self.rows.get(params["id"])
            if row is None:
                return []
            if "status = 'processing'" in normalized:
                row["status"] = "processing"
                row["attempt_count"] = int(row["attempt_count"]) + 1
                row["locked_at"] = datetime.now(timezone.utc)
                row["updated_at"] = row["locked_at"]
            elif "status = 'processed'" in normalized:
                row["status"] = "processed"
                row["processed_at"] = datetime.now(timezone.utc)
                row["updated_at"] = row["processed_at"]
                row["error_message"] = None
            elif "status = 'failed'" in normalized:
                row["status"] = "failed"
                row["updated_at"] = datetime.now(timezone.utc)
                row["error_message"] = params.get("error_message")
            return []

        if normalized.startswith("INSERT INTO wecom_inbox_events"):
            key = params["dedup_key"]
            existing = next((r for r in self.rows.values() if r["dedup_key"] == key), None)
            if existing:
                return []
            row_id = self._next_id
            self._next_id += 1
            now = datetime.now(timezone.utc)
            payload = params.get("payload_json")
            if isinstance(payload, str):
                payload = json.loads(payload)
            self.rows[row_id] = {
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
            return []

        return []


class _FakeCursor:
    def __init__(self, table: _InMemoryInboxTable):
        self._table = table
        self._rows: list[dict[str, Any]] = []

    def execute(self, sql: str, params: dict | tuple | None = None) -> None:
        if params is None:
            params = {}
        elif not isinstance(params, dict):
            raise TypeError("expected dict params")
        self._rows = self._table.execute(sql, params)

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self._rows)

    def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeTransaction:
    def __init__(self, table: _InMemoryInboxTable):
        self._table = table

    def __enter__(self):
        self._table.begin_txn()
        return self

    def __exit__(self, *exc):
        self._table.end_txn()
        return False


class _FakeConnection:
    def __init__(self, table: _InMemoryInboxTable):
        self._table = table

    def transaction(self):
        return _FakeTransaction(self._table)

    def cursor(self, row_factory=None):
        return _FakeCursor(self._table)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def inbox_table(monkeypatch):
    table = _InMemoryInboxTable()

    @contextlib.contextmanager
    def fake_connection():
        yield _FakeConnection(table)

    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        fake_connection,
    )
    return table


def _must_not_process(*_args, **_kwargs):
    raise AssertionError("must not process")


def _must_not_call_slice(*_args, **_kwargs):
    raise AssertionError("must not call slice")


def _empty_summary(**overrides: int) -> dict[str, int]:
    base = {"claimed": 0, "processed": 0, "failed": 0, "skipped": 0}
    base.update(overrides)
    return base


def test_worker_without_db_returns_zeros(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    summary = inbox_worker.process_pending_wecom_inbox_events(limit=5)
    assert summary == _empty_summary()


def test_worker_claims_and_processes_pending_rows(wecom_env, inbox_table, monkeypatch):
    inbox_table.seed_pending(dedup_key="k1", callback_token="tok_a", open_kf_id="wk_a")
    inbox_table.seed_pending(dedup_key="k2", callback_token="tok_b", open_kf_id="wk_b")

    calls: list[tuple[str, str]] = []

    def _fake_process(cfg, *, callback_token, open_kf_id, pull_messages=None):
        calls.append((callback_token, open_kf_id))
        return []

    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _fake_process)

    summary = inbox_worker.process_pending_wecom_inbox_events(limit=10)

    assert summary == _empty_summary(claimed=2, processed=2)
    assert set(calls) == {("tok_a", "wk_a"), ("tok_b", "wk_b")}
    statuses = {row["status"] for row in inbox_table.rows.values()}
    assert statuses == {"processed"}
    for row in inbox_table.rows.values():
        assert row["attempt_count"] == 1
        assert row["locked_at"] is not None
        assert row["processed_at"] is not None


def test_worker_marks_failed_row_and_stores_error_message(wecom_env, inbox_table, monkeypatch):
    row_id = inbox_table.seed_pending(dedup_key="fail1")

    def _boom(cfg, *, callback_token, open_kf_id, pull_messages=None):
        raise RuntimeError("sync_msg exploded")

    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _boom)

    summary = inbox_worker.process_pending_wecom_inbox_events(limit=5)

    assert summary == _empty_summary(claimed=1, failed=1)
    row = inbox_table.rows[row_id]
    assert row["status"] == "failed"
    assert row["error_message"] == "sync_msg exploded"
    assert row["attempt_count"] == 1
    assert row["processed_at"] is None


def test_worker_does_not_process_same_row_twice_in_one_run(wecom_env, inbox_table, monkeypatch):
    inbox_table.seed_pending(dedup_key="once")

    call_count = {"n": 0}

    def _count(cfg, *, callback_token, open_kf_id, pull_messages=None):
        call_count["n"] += 1
        return []

    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _count)

    summary = inbox_worker.process_pending_wecom_inbox_events(limit=10)
    assert summary == _empty_summary(claimed=1, processed=1)
    assert call_count["n"] == 1


def test_worker_second_run_skips_already_processed_rows(wecom_env, inbox_table, monkeypatch):
    inbox_table.seed_pending(dedup_key="done")

    monkeypatch.setattr(
        inbox_worker,
        "process_kf_msg_or_event",
        lambda *a, **k: [],
    )

    first = inbox_worker.process_pending_wecom_inbox_events(limit=5)
    second = inbox_worker.process_pending_wecom_inbox_events(limit=5)

    assert first == _empty_summary(claimed=1, processed=1)
    assert second == _empty_summary()


def test_stale_processing_row_is_reclaimed_and_processed(wecom_env, inbox_table, monkeypatch):
    stale_locked_at = datetime.now(timezone.utc) - timedelta(minutes=15)
    row_id = inbox_table.seed_processing(
        dedup_key="stale1",
        locked_at=stale_locked_at,
        attempt_count=1,
    )

    called = {"n": 0}

    def _process(cfg, *, callback_token, open_kf_id, pull_messages=None):
        called["n"] += 1
        return []

    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _process)

    summary = inbox_worker.process_pending_wecom_inbox_events(
        limit=5,
        stale_timeout_seconds=600,
    )

    assert summary == _empty_summary(claimed=1, processed=1)
    assert called["n"] == 1
    row = inbox_table.rows[row_id]
    assert row["status"] == "processed"
    assert row["attempt_count"] == 2


def test_fresh_processing_row_is_not_reclaimed(wecom_env, inbox_table, monkeypatch):
    fresh_locked_at = datetime.now(timezone.utc) - timedelta(seconds=30)
    row_id = inbox_table.seed_processing(
        dedup_key="fresh1",
        locked_at=fresh_locked_at,
        attempt_count=1,
    )

    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _must_not_process)

    summary = inbox_worker.process_pending_wecom_inbox_events(
        limit=5,
        stale_timeout_seconds=600,
    )

    assert summary == _empty_summary()
    row = inbox_table.rows[row_id]
    assert row["status"] == "processing"
    assert row["attempt_count"] == 1


def test_row_with_attempt_count_at_max_is_not_claimed(wecom_env, inbox_table, monkeypatch):
    inbox_table.seed_pending(dedup_key="exhausted", attempt_count=3)

    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _must_not_process)

    summary = inbox_worker.process_pending_wecom_inbox_events(limit=5, max_attempts=3)

    assert summary == _empty_summary(skipped=1)
    assert inbox_table.rows[1]["status"] == "pending"
    assert inbox_table.rows[1]["attempt_count"] == 3


def test_unknown_event_type_becomes_failed(wecom_env, inbox_table, monkeypatch):
    row_id = inbox_table.seed_pending(
        dedup_key="unknown1",
        event_type="subscribe",
        payload_json={"event": "subscribe"},
    )

    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _must_not_call_slice)

    summary = inbox_worker.process_pending_wecom_inbox_events(limit=5)

    assert summary == _empty_summary(claimed=1, failed=1)
    row = inbox_table.rows[row_id]
    assert row["status"] == "failed"
    assert "wecom_inbox_unhandled_event_type_v1" in row["error_message"]
    assert "subscribe" in row["error_message"]


def test_empty_event_type_with_kf_payload_falls_back_to_kf_msg_or_event(
    wecom_env, inbox_table, monkeypatch
):
    row_id = inbox_table.seed_pending(
        dedup_key="fallback1",
        event_type="",
        open_kf_id="wk_fb",
        callback_token="tok_fb",
        payload_json={
            "event_type": "wecom_kf_callback",
            "channel": "wecom_kf",
            "event": "kf_msg_or_event",
            "open_kf_id": "wk_fb",
            "token": "tok_fb",
            "raw_fields": {"Event": "kf_msg_or_event", "OpenKfId": "wk_fb", "Token": "tok_fb"},
        },
    )

    calls: list[tuple[str, str]] = []

    def _process(cfg, *, callback_token, open_kf_id, pull_messages=None):
        calls.append((callback_token, open_kf_id))
        return []

    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _process)

    summary = inbox_worker.process_pending_wecom_inbox_events(limit=5)

    assert summary == _empty_summary(claimed=1, processed=1)
    assert calls == [("tok_fb", "wk_fb")]
    assert inbox_table.rows[row_id]["status"] == "processed"


def test_process_wecom_inbox_event_raises_for_unknown_event_type(wecom_env, monkeypatch):
    monkeypatch.setattr(inbox_worker, "process_kf_msg_or_event", _must_not_call_slice)

    row = {
        "id": 99,
        "event_type": "subscribe",
        "open_kf_id": "",
        "callback_token": "",
        "payload_json": {"event": "subscribe"},
    }
    with pytest.raises(ValueError, match="wecom_inbox_unhandled_event_type_v1"):
        inbox_worker.process_wecom_inbox_event(row)


def test_resolve_wecom_inbox_event_type_empty_with_kf_channel():
    row = {
        "event_type": "",
        "open_kf_id": "wk1",
        "callback_token": "tok1",
        "payload_json": {
            "channel": "wecom_kf",
            "open_kf_id": "wk1",
            "token": "tok1",
        },
    }
    assert inbox_worker.resolve_wecom_inbox_event_type(row) == "kf_msg_or_event"


@pytest.fixture
def pipeline_db(monkeypatch):
    db = InMemoryWeComPipelineDb()
    install_pipeline_db(monkeypatch, db)
    return db


@pytest.fixture
async def wecom_client():
    app = FastAPI()
    app.include_router(wecom_kf_router)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def test_callback_queue_mode_still_skips_sync_msg(wecom_env, wecom_client, monkeypatch, pipeline_db):
    """Q0.1 fast ack unchanged: callback must not call sync_msg even after Q0.2."""
    monkeypatch.setenv("WECOM_INBOX_QUEUE", "1")
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    body, params = _build_post_request(crypto, SAMPLE_KF_EVENT_XML)

    with patch("services.fiqa_api.wecom.sync_msg.pull_customer_text_messages") as mock_sync:
        resp = await wecom_client.post(
            "/api/wecom/kf/callback",
            params=params,
            content=body,
            headers={"Content-Type": "text/xml"},
        )

    assert resp.status_code == 200
    mock_sync.assert_not_called()
