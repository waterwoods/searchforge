"""Tests for WeCom reply outbox (Q0.3 — WECOM_REPLY_OUTBOX)."""

from __future__ import annotations

import contextlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from services.fiqa_api.wecom import reply_outbox
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    monkeypatch.delenv("WECOM_REPLY_OUTBOX", raising=False)
    monkeypatch.delenv("WECOM_SLICE_SEND_REPLY", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    load_wecom_kf_config.cache_clear()
    reply_outbox.reset_wecom_reply_outbox_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    yield
    reply_outbox.reset_wecom_reply_outbox_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    load_wecom_kf_config.cache_clear()


@pytest.fixture
def wecom_env(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    return load_wecom_kf_config()


class _InMemoryOutboxTable:
    """Minimal Postgres stand-in for wecom_reply_outbox tests."""

    def __init__(self) -> None:
        self._next_id = 1
        self.rows: dict[int, dict[str, Any]] = {}
        self._txn_locked: set[int] = set()
        self._claim_params: dict[str, Any] = {}

    def seed_pending(
        self,
        *,
        dedup_key: str,
        external_userid: str = "wm1",
        open_kf_id: str = "wk1",
        reply_type: str = "text",
        reply_payload_json: dict | None = None,
        attempt_count: int = 0,
        msg_id: str | None = "msg1",
        case_id: str | None = None,
    ) -> int:
        row_id = self._next_id
        self._next_id += 1
        now = datetime.now(timezone.utc)
        self.rows[row_id] = {
            "id": row_id,
            "dedup_key": dedup_key,
            "msg_id": msg_id,
            "external_userid": external_userid,
            "open_kf_id": open_kf_id,
            "case_id": case_id,
            "reply_type": reply_type,
            "reply_payload_json": reply_payload_json
            or {"msgtype": "text", "text": {"content": "hello"}},
            "status": "pending",
            "attempt_count": attempt_count,
            "locked_at": None,
            "sent_at": None,
            "failed_at": None,
            "errcode": None,
            "errmsg": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
        return row_id

    def seed_sending(
        self,
        *,
        dedup_key: str,
        locked_at: datetime,
        external_userid: str = "wm1",
        open_kf_id: str = "wk1",
        reply_type: str = "text",
        attempt_count: int = 1,
        reply_payload_json: dict | None = None,
    ) -> int:
        row_id = self._next_id
        self._next_id += 1
        now = datetime.now(timezone.utc)
        self.rows[row_id] = {
            "id": row_id,
            "dedup_key": dedup_key,
            "msg_id": "msg1",
            "external_userid": external_userid,
            "open_kf_id": open_kf_id,
            "case_id": None,
            "reply_type": reply_type,
            "reply_payload_json": reply_payload_json
            or {"msgtype": "text", "text": {"content": "hello"}},
            "status": "sending",
            "attempt_count": attempt_count,
            "locked_at": locked_at,
            "sent_at": None,
            "failed_at": None,
            "errcode": None,
            "errmsg": None,
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
        if row["status"] == "sending" and row.get("locked_at") is not None:
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
                and row["status"] in ("pending", "sending")
            )
            return [{"n": count}]

        if "FROM wecom_reply_outbox" in normalized and "FOR UPDATE SKIP LOCKED" in normalized:
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

        if normalized.startswith("UPDATE wecom_reply_outbox") and params.get("id") is not None:
            row = self.rows.get(params["id"])
            if row is None:
                return []
            if "status = 'sending'" in normalized:
                row["status"] = "sending"
                row["attempt_count"] = int(row["attempt_count"]) + 1
                row["locked_at"] = datetime.now(timezone.utc)
                row["updated_at"] = row["locked_at"]
            elif "status = 'sent'" in normalized:
                row["status"] = "sent"
                row["sent_at"] = datetime.now(timezone.utc)
                row["updated_at"] = row["sent_at"]
                row["errcode"] = params.get("errcode")
                row["errmsg"] = params.get("errmsg")
                row["error_message"] = None
                row["failed_at"] = None
            elif "status = 'failed'" in normalized:
                row["status"] = "failed"
                row["failed_at"] = datetime.now(timezone.utc)
                row["updated_at"] = row["failed_at"]
                row["errcode"] = params.get("errcode")
                row["errmsg"] = params.get("errmsg")
                row["error_message"] = params.get("error_message")
            return []

        if normalized.startswith("INSERT INTO wecom_reply_outbox"):
            key = params["dedup_key"]
            existing = next((r for r in self.rows.values() if r["dedup_key"] == key), None)
            if existing:
                return []
            row_id = self._next_id
            self._next_id += 1
            now = datetime.now(timezone.utc)
            payload = params.get("reply_payload_json")
            if isinstance(payload, str):
                payload = json.loads(payload)
            self.rows[row_id] = {
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
            return []

        return []


class _FakeCursor:
    def __init__(self, table: _InMemoryOutboxTable):
        self._table = table
        self._rows: list[dict[str, Any]] = []
        self.rowcount = 0

    def execute(self, sql: str, params: dict | tuple | None = None) -> None:
        if params is None:
            params = {}
        elif not isinstance(params, dict):
            raise TypeError("expected dict params")
        normalized = " ".join(sql.split())
        if normalized.startswith("INSERT INTO wecom_reply_outbox"):
            before = len(self._table.rows)
            self._table.execute(sql, params)
            after = len(self._table.rows)
            self.rowcount = 1 if after > before else 0
            self._rows = []
        else:
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
    def __init__(self, table: _InMemoryOutboxTable):
        self._table = table

    def __enter__(self):
        self._table.begin_txn()
        return self

    def __exit__(self, *exc):
        self._table.end_txn()
        return False


class _FakeConnection:
    def __init__(self, table: _InMemoryOutboxTable):
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
def outbox_table(monkeypatch):
    table = _InMemoryOutboxTable()

    @contextlib.contextmanager
    def fake_connection():
        yield _FakeConnection(table)

    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        fake_connection,
    )
    return table


def _empty_summary(**overrides: int) -> dict[str, int]:
    base = {"claimed": 0, "sent": 0, "failed": 0, "skipped": 0}
    base.update(overrides)
    return base


def _one_message_pull(msg_id: str, content: str = "hi"):
    def pull(_cfg, *, token, open_kf_id):
        return [
            {
                "msgid": msg_id,
                "open_kfid": "wktest001",
                "external_userid": "wmexternal001",
                "origin": 3,
                "msgtype": "text",
                "text": {"content": content},
            }
        ]

    return pull


def test_outbox_off_direct_send_unchanged(monkeypatch, wecom_env):
    """WECOM_REPLY_OUTBOX OFF: slice still calls send_msg directly."""
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    text_calls: list[dict] = []
    menu_calls: list[dict] = []

    def fake_text(cfg, *, external_userid, open_kf_id, content):
        text_calls.append({"content": content})
        return {"errcode": 0}

    def fake_menu(cfg, *, external_userid, open_kf_id, menu):
        menu_calls.append({"menu": menu})
        return {"errcode": 0}

    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_text_reply", fake_text)
    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", fake_menu)

    enqueue_called = {"n": 0}

    def fake_enqueue(**kwargs):
        enqueue_called["n"] += 1
        return True

    monkeypatch.setattr("services.fiqa_api.wecom.slice.enqueue_wecom_reply", fake_enqueue)

    results = process_kf_msg_or_event(
        wecom_env,
        callback_token="t",
        open_kf_id="wktest001",
        pull_messages=_one_message_pull("m1"),
    )

    assert results[0]["reply_sent"] is True
    assert len(menu_calls) == 1
    assert len(text_calls) == 0
    assert enqueue_called["n"] == 0


def test_outbox_on_enqueues_without_direct_send(monkeypatch, wecom_env, outbox_table):
    """WECOM_REPLY_OUTBOX ON: reply enqueued, send_msg not called from slice."""
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    monkeypatch.setenv("WECOM_REPLY_OUTBOX", "1")
    monkeypatch.setattr("services.fiqa_api.wecom.slice.claim_reply_send", lambda _msg_id: True)

    def must_not_send(*_a, **_k):
        raise AssertionError("send_msg must not be called when outbox is ON")

    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_text_reply", must_not_send)
    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", must_not_send)

    results = process_kf_msg_or_event(
        wecom_env,
        callback_token="t",
        open_kf_id="wktest001",
        pull_messages=_one_message_pull("m_outbox_1"),
    )

    assert results[0]["reply_sent"] is True
    assert results[0].get("reply_enqueued") is True
    assert len(outbox_table.rows) == 1
    row = next(iter(outbox_table.rows.values()))
    assert row["status"] == "pending"
    assert row["reply_type"] == "msgmenu"
    assert row["msg_id"] == "m_outbox_1"


def test_duplicate_enqueue_same_dedup_key(monkeypatch, outbox_table):
    """Duplicate enqueue with same dedup_key creates only one outbox row."""
    payload = {"msgtype": "text", "text": {"content": "same reply"}}

    first = reply_outbox.enqueue_wecom_reply(
        msg_id="dup1",
        external_userid="wm1",
        open_kf_id="wk1",
        reply_type="text",
        reply_payload=payload,
    )
    second = reply_outbox.enqueue_wecom_reply(
        msg_id="dup1",
        external_userid="wm1",
        open_kf_id="wk1",
        reply_type="text",
        reply_payload=payload,
    )

    assert first is True
    assert second is False
    assert len(outbox_table.rows) == 1


def test_compute_dedup_key_differs_for_different_payloads():
    base_kwargs = {
        "msg_id": "m1",
        "external_userid": "wm1",
        "open_kf_id": "wk1",
        "reply_type": "text",
    }
    key_a = reply_outbox.compute_reply_dedup_key(
        **base_kwargs,
        reply_payload={"msgtype": "text", "text": {"content": "A"}},
    )
    key_b = reply_outbox.compute_reply_dedup_key(
        **base_kwargs,
        reply_payload={"msgtype": "text", "text": {"content": "B"}},
    )
    assert key_a != key_b


def test_sender_claims_pending_and_marks_sent(monkeypatch, wecom_env, outbox_table):
    row_id = outbox_table.seed_pending(
        dedup_key="send1",
        reply_payload_json={"msgtype": "text", "text": {"content": "hello world"}},
    )

    def fake_send(cfg, *, external_userid, open_kf_id, content):
        assert content == "hello world"
        return {"errcode": 0, "errmsg": "ok"}

    monkeypatch.setattr(reply_outbox, "send_text_reply", fake_send)

    summary = reply_outbox.process_pending_wecom_reply_outbox(limit=5)

    assert summary == _empty_summary(claimed=1, sent=1)
    row = outbox_table.rows[row_id]
    assert row["status"] == "sent"
    assert row["sent_at"] is not None
    assert row["attempt_count"] == 1


def test_sender_marks_failed_and_stores_error(monkeypatch, wecom_env, outbox_table):
    row_id = outbox_table.seed_pending(dedup_key="fail1")

    def fake_send(*_a, **_k):
        raise RuntimeError("wecom_send_msg_api_error_v1 errcode=40001 errmsg=invalid token")

    monkeypatch.setattr(reply_outbox, "send_text_reply", fake_send)

    summary = reply_outbox.process_pending_wecom_reply_outbox(limit=5)

    assert summary == _empty_summary(claimed=1, failed=1)
    row = outbox_table.rows[row_id]
    assert row["status"] == "failed"
    assert row["failed_at"] is not None
    assert row["errcode"] == 40001
    assert "invalid token" in (row["errmsg"] or "")
    assert row["error_message"]


def test_sender_respects_max_attempts(monkeypatch, wecom_env, outbox_table):
    outbox_table.seed_pending(dedup_key="exhausted", attempt_count=3)

    def must_not_send(*_a, **_k):
        raise AssertionError("must not send exhausted row")

    monkeypatch.setattr(reply_outbox, "send_text_reply", must_not_send)

    summary = reply_outbox.process_pending_wecom_reply_outbox(limit=5, max_attempts=3)

    assert summary == _empty_summary(skipped=1)
    assert outbox_table.rows[1]["status"] == "pending"
    assert outbox_table.rows[1]["attempt_count"] == 3


def test_stale_sending_row_is_reclaimed_and_sent(monkeypatch, wecom_env, outbox_table):
    stale_locked_at = datetime.now(timezone.utc) - timedelta(minutes=15)
    row_id = outbox_table.seed_sending(
        dedup_key="stale1",
        locked_at=stale_locked_at,
        attempt_count=1,
    )

    sent = {"n": 0}

    def fake_send(*_a, **_k):
        sent["n"] += 1
        return {"errcode": 0}

    monkeypatch.setattr(reply_outbox, "send_text_reply", fake_send)

    summary = reply_outbox.process_pending_wecom_reply_outbox(
        limit=5,
        stale_timeout_seconds=600,
    )

    assert summary == _empty_summary(claimed=1, sent=1)
    assert sent["n"] == 1
    row = outbox_table.rows[row_id]
    assert row["status"] == "sent"
    assert row["attempt_count"] == 2


def test_fresh_sending_row_is_not_reclaimed(monkeypatch, wecom_env, outbox_table):
    fresh_locked_at = datetime.now(timezone.utc) - timedelta(seconds=30)
    row_id = outbox_table.seed_sending(
        dedup_key="fresh1",
        locked_at=fresh_locked_at,
        attempt_count=1,
    )

    def must_not_send(*_a, **_k):
        raise AssertionError("must not send fresh sending row")

    monkeypatch.setattr(reply_outbox, "send_text_reply", must_not_send)

    summary = reply_outbox.process_pending_wecom_reply_outbox(
        limit=5,
        stale_timeout_seconds=600,
    )

    assert summary == _empty_summary()
    row = outbox_table.rows[row_id]
    assert row["status"] == "sending"
    assert row["attempt_count"] == 1


def test_sender_without_db_returns_zeros(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    summary = reply_outbox.process_pending_wecom_reply_outbox(limit=5)
    assert summary == _empty_summary()


def test_existing_inbox_tests_still_importable():
    """Sanity: Q0.1/Q0.2 modules remain importable alongside reply outbox."""
    from services.fiqa_api.wecom import inbox_queue, inbox_worker  # noqa: F401

    assert inbox_queue.wecom_inbox_queue_enabled() is False
    assert inbox_worker.process_pending_wecom_inbox_events is not None
