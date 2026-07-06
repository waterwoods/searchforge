"""Tests for WeCom callback inbox queue (Q0.1 — WECOM_INBOX_QUEUE)."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from services.fiqa_api.routes.wecom_kf_callback import router as wecom_kf_router
from services.fiqa_api.wecom import inbox_queue
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.crypto.WXBizMsgCrypt3 import WXBizMsgCrypt
from tests.test_wecom_kf_callback import (
    SAMPLE_KF_EVENT_XML,
    _build_post_request,
    _test_credentials,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_inbox_state(monkeypatch):
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
    load_wecom_kf_config.cache_clear()
    return token, encoding_aes_key, corp_id


@pytest.fixture
async def wecom_client():
    app = FastAPI()
    app.include_router(wecom_kf_router)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


class _FakeCursor:
    def __init__(self, store: dict[str, dict]):
        self._store = store
        self.rowcount = 0

    def execute(self, sql: str, params: dict | tuple | None = None) -> None:
        normalized = " ".join(sql.split())
        if normalized.startswith("CREATE TABLE") or normalized.startswith("CREATE INDEX"):
            return
        if normalized.startswith("INSERT INTO wecom_inbox_events"):
            key = params["dedup_key"]
            if key in self._store:
                self.rowcount = 0
            else:
                self._store[key] = dict(params)
                self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConnection:
    def __init__(self, store: dict[str, dict]):
        self._store = store

    def transaction(self):
        return _FakeTransaction()

    def cursor(self):
        return _FakeCursor(self._store)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def fake_inbox_store(monkeypatch):
    store: dict[str, dict] = {}
    import contextlib

    @contextlib.contextmanager
    def fake_connection():
        yield _FakeConnection(store)

    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        fake_connection,
    )
    return store


async def test_queue_off_still_calls_process_kf_msg_or_event(wecom_env, wecom_client, monkeypatch):
    """Default (flag unset): existing synchronous slice path is unchanged."""
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    body, params = _build_post_request(crypto, SAMPLE_KF_EVENT_XML)

    called = {"process": False}

    def _fake_process(*args, **kwargs):
        called["process"] = True
        return []

    monkeypatch.setattr(
        "services.fiqa_api.routes.wecom_kf_callback.process_kf_msg_or_event",
        _fake_process,
    )

    resp = await wecom_client.post(
        "/api/wecom/kf/callback",
        params=params,
        content=body,
        headers={"Content-Type": "text/xml"},
    )
    assert resp.status_code == 200
    assert resp.text == "success"
    assert called["process"] is True


async def test_queue_on_skips_process_and_enqueues(wecom_env, wecom_client, monkeypatch, fake_inbox_store):
    """WECOM_INBOX_QUEUE=1: verify/decrypt/enqueue only — no slice."""
    monkeypatch.setenv("WECOM_INBOX_QUEUE", "1")
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    body, params = _build_post_request(crypto, SAMPLE_KF_EVENT_XML)

    def _should_not_run(*args, **kwargs):
        raise AssertionError("process_kf_msg_or_event must not run in queue mode")

    monkeypatch.setattr(
        "services.fiqa_api.routes.wecom_kf_callback.process_kf_msg_or_event",
        _should_not_run,
    )

    with patch("services.fiqa_api.wecom.sync_msg.pull_customer_text_messages") as mock_sync:
        resp = await wecom_client.post(
            "/api/wecom/kf/callback",
            params=params,
            content=body,
            headers={"Content-Type": "text/xml"},
        )

    assert resp.status_code == 200
    assert resp.text == "success"
    assert len(fake_inbox_store) == 1
    row = next(iter(fake_inbox_store.values()))
    assert row["open_kf_id"] == "wkxxxxxxx"
    assert row["callback_token"] == "ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR"
    assert row["event_type"] == "kf_msg_or_event"
    mock_sync.assert_not_called()


async def test_queue_on_duplicate_callback_creates_one_row(
    wecom_env, wecom_client, monkeypatch, fake_inbox_store
):
    """WeCom retries with the same token must not insert a second inbox row."""
    monkeypatch.setenv("WECOM_INBOX_QUEUE", "1")
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    body, params = _build_post_request(crypto, SAMPLE_KF_EVENT_XML)

    for _ in range(3):
        resp = await wecom_client.post(
            "/api/wecom/kf/callback",
            params=params,
            content=body,
            headers={"Content-Type": "text/xml"},
        )
        assert resp.status_code == 200

    assert len(fake_inbox_store) == 1


async def test_queue_on_returns_quickly_without_waiting_for_slice(
    wecom_env, wecom_client, monkeypatch, fake_inbox_store
):
    """Callback ack must not block on sync_msg / classify / reply work."""
    monkeypatch.setenv("WECOM_INBOX_QUEUE", "1")
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    body, params = _build_post_request(crypto, SAMPLE_KF_EVENT_XML)

    def _slow_process(*args, **kwargs):
        time.sleep(2)
        return []

    monkeypatch.setattr(
        "services.fiqa_api.routes.wecom_kf_callback.process_kf_msg_or_event",
        _slow_process,
    )

    started = time.monotonic()
    resp = await wecom_client.post(
        "/api/wecom/kf/callback",
        params=params,
        content=body,
        headers={"Content-Type": "text/xml"},
    )
    elapsed = time.monotonic() - started

    assert resp.status_code == 200
    assert elapsed < 0.5


def test_compute_dedup_key_prefers_open_kf_id_and_token():
    parsed = {"OpenKfId": "wk1", "Token": "tok_abc", "Event": "kf_msg_or_event"}
    key = inbox_queue.compute_dedup_key(parsed_event=parsed, raw_body=b"encrypted-body")
    assert key == "wk1:tok_abc"


def test_compute_dedup_key_falls_back_to_body_hash_without_token():
    parsed = {"OpenKfId": "wk1", "Event": "kf_msg_or_event"}
    body = b"same-encrypted-payload"
    key1 = inbox_queue.compute_dedup_key(parsed_event=parsed, raw_body=body)
    key2 = inbox_queue.compute_dedup_key(parsed_event=parsed, raw_body=body)
    key3 = inbox_queue.compute_dedup_key(parsed_event=parsed, raw_body=b"different")
    assert key1 == key2
    assert key1.startswith("wk1:")
    assert key3 != key1


def test_enqueue_in_memory_dedup():
    parsed = {"OpenKfId": "wk1", "Token": "t1", "Event": "kf_msg_or_event"}
    payload = {"event": "kf_msg_or_event"}
    key = inbox_queue.compute_dedup_key(parsed_event=parsed, raw_body=b"x")
    assert inbox_queue.enqueue_wecom_callback_event(
        dedup_key=key, parsed_event=parsed, payload_json=payload
    ) is True
    assert inbox_queue.enqueue_wecom_callback_event(
        dedup_key=key, parsed_event=parsed, payload_json=payload
    ) is False


async def test_queue_on_logs_enqueue_with_created_flag(
    wecom_env, wecom_client, monkeypatch, fake_inbox_store, caplog
):
    monkeypatch.setenv("WECOM_INBOX_QUEUE", "1")
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    body, params = _build_post_request(crypto, SAMPLE_KF_EVENT_XML)

    with caplog.at_level("INFO"):
        await wecom_client.post(
            "/api/wecom/kf/callback",
            params=params,
            content=body,
            headers={"Content-Type": "text/xml"},
        )
        await wecom_client.post(
            "/api/wecom/kf/callback",
            params=params,
            content=body,
            headers={"Content-Type": "text/xml"},
        )

    enqueued = [r.message for r in caplog.records if "wecom_inbox_enqueued_v1" in r.message]
    assert len(enqueued) == 2
    first = json.loads(enqueued[0].split("wecom_inbox_enqueued_v1 ", 1)[1])
    second = json.loads(enqueued[1].split("wecom_inbox_enqueued_v1 ", 1)[1])
    assert first["created"] is True
    assert second["created"] is False
    assert second["duplicate"] is True
