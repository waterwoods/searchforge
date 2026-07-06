"""End-to-end tests for queued WeCom pipeline (Q0.4).

Verifies callback → inbox → worker → reply outbox → sender when both
WECOM_INBOX_QUEUE=1 and WECOM_REPLY_OUTBOX=1 are enabled, plus idempotency
and flag-off backward compatibility.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from services.fiqa_api.routes.wecom_kf_callback import router as wecom_kf_router
from services.fiqa_api.wecom import inbox_queue, inbox_worker, reply_outbox
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.crypto.WXBizMsgCrypt3 import WXBizMsgCrypt
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.sync_cursor import reset_sync_cursor_memory_for_tests
from services.fiqa_api.wecom.sync_msg import SyncPullResult
from tests.test_wecom_kf_callback import (
    SAMPLE_KF_EVENT_XML,
    _build_post_request,
    _test_credentials,
)
from tests.wecom_pipeline_test_db import InMemoryWeComPipelineDb, install_pipeline_db

pytestmark = pytest.mark.anyio

_CALLBACK_OPEN_KF_ID = "wkxxxxxxx"
_CALLBACK_TOKEN = "ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR"
_E2E_MSG_ID = "e2e_pipeline_msg_001"
_E2E_EXTERNAL_USERID = "wmexternal001"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_pipeline_state(monkeypatch):
    monkeypatch.delenv("WECOM_INBOX_QUEUE", raising=False)
    monkeypatch.delenv("WECOM_REPLY_OUTBOX", raising=False)
    monkeypatch.delenv("WECOM_SLICE_SEND_REPLY", raising=False)
    monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    load_wecom_kf_config.cache_clear()
    inbox_queue.reset_wecom_inbox_memory_for_tests()
    reply_outbox.reset_wecom_reply_outbox_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    reset_sync_cursor_memory_for_tests()
    yield
    inbox_queue.reset_wecom_inbox_memory_for_tests()
    reply_outbox.reset_wecom_reply_outbox_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    reset_sync_cursor_memory_for_tests()
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


@pytest.fixture
def queued_flags(monkeypatch):
    monkeypatch.setenv("WECOM_INBOX_QUEUE", "1")
    monkeypatch.setenv("WECOM_REPLY_OUTBOX", "1")
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")


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


def _pipeline_pull_messages(_cfg, *, token, open_kf_id, start_cursor=""):
    assert token == _CALLBACK_TOKEN
    assert open_kf_id == _CALLBACK_OPEN_KF_ID
    return SyncPullResult(
        messages=[
            {
                "msgid": _E2E_MSG_ID,
                "open_kfid": _CALLBACK_OPEN_KF_ID,
                "external_userid": _E2E_EXTERNAL_USERID,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "hi"},
            }
        ],
        next_cursor="pipeline_cursor_next",
    )


def _install_send_tracker(monkeypatch) -> dict[str, list[dict[str, Any]]]:
    """Track outbound send_msg calls at the reply_outbox sender boundary."""
    calls: dict[str, list[dict[str, Any]]] = {"text": [], "menu": []}

    def fake_text(cfg, *, external_userid, open_kf_id, content):
        calls["text"].append(
            {
                "external_userid": external_userid,
                "open_kf_id": open_kf_id,
                "content": content,
            }
        )
        return {"errcode": 0, "errmsg": "ok"}

    def fake_menu(cfg, *, external_userid, open_kf_id, menu):
        calls["menu"].append(
            {
                "external_userid": external_userid,
                "open_kf_id": open_kf_id,
                "menu": menu,
            }
        )
        return {"errcode": 0, "errmsg": "ok"}

    monkeypatch.setattr(reply_outbox, "send_text_reply", fake_text)
    monkeypatch.setattr(reply_outbox, "send_menu_reply", fake_menu)
    return calls


def _drain_queued_pipeline() -> dict[str, dict[str, int]]:
    """Run inbox worker then reply sender — the manual two-step drain path."""
    inbox_summary = inbox_worker.process_pending_wecom_inbox_events(limit=10)
    reply_summary = reply_outbox.process_pending_wecom_reply_outbox(limit=10)
    return {"inbox": inbox_summary, "reply": reply_summary}


async def _post_kf_callback(wecom_client, wecom_env) -> None:
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    body, params = _build_post_request(crypto, SAMPLE_KF_EVENT_XML)
    resp = await wecom_client.post(
        "/api/wecom/kf/callback",
        params=params,
        content=body,
        headers={"Content-Type": "text/xml"},
    )
    assert resp.status_code == 200
    assert resp.text == "success"


def _total_send_calls(send_calls: dict[str, list]) -> int:
    return len(send_calls["text"]) + len(send_calls["menu"])


# ---------------------------------------------------------------------------
# Scenario A — normal queued flow
# ---------------------------------------------------------------------------


async def test_scenario_a_normal_queued_pipeline(
    wecom_env,
    wecom_client,
    queued_flags,
    pipeline_db,
    monkeypatch,
):
    send_calls = _install_send_tracker(monkeypatch)
    monkeypatch.setattr(
        "services.fiqa_api.wecom.slice.pull_customer_text_messages",
        _pipeline_pull_messages,
    )

    started = time.monotonic()
    await _post_kf_callback(wecom_client, wecom_env)
    callback_elapsed = time.monotonic() - started

    assert callback_elapsed < 0.5
    assert len(pipeline_db.inbox_rows) == 1
    inbox_row = next(iter(pipeline_db.inbox_rows.values()))
    assert inbox_row["status"] == "pending"
    assert inbox_row["event_type"] == "kf_msg_or_event"

    drain1 = _drain_queued_pipeline()
    assert drain1["inbox"] == {"claimed": 1, "processed": 1, "failed": 0, "skipped": 0}
    assert drain1["reply"] == {"claimed": 1, "sent": 1, "failed": 0, "skipped": 0}

    assert inbox_row["status"] == "processed"
    assert inbox_row["processed_at"] is not None
    assert len(pipeline_db.outbox_rows) == 1
    outbox_row = next(iter(pipeline_db.outbox_rows.values()))
    assert outbox_row["status"] == "sent"
    assert outbox_row["sent_at"] is not None
    assert outbox_row["msg_id"] == _E2E_MSG_ID
    assert _total_send_calls(send_calls) == 1


# ---------------------------------------------------------------------------
# Scenario B — duplicate callback retry
# ---------------------------------------------------------------------------


async def test_scenario_b_duplicate_callback_retry(
    wecom_env,
    wecom_client,
    queued_flags,
    pipeline_db,
    monkeypatch,
):
    send_calls = _install_send_tracker(monkeypatch)
    monkeypatch.setattr(
        "services.fiqa_api.wecom.slice.pull_customer_text_messages",
        _pipeline_pull_messages,
    )

    for _ in range(3):
        await _post_kf_callback(wecom_client, wecom_env)

    assert len(pipeline_db.inbox_rows) == 1

    drain1 = _drain_queued_pipeline()
    assert drain1["inbox"]["processed"] == 1
    assert drain1["reply"]["sent"] == 1
    assert len(pipeline_db.outbox_rows) == 1
    assert _total_send_calls(send_calls) == 1

    drain2 = _drain_queued_pipeline()
    assert drain2["inbox"] == {"claimed": 0, "processed": 0, "failed": 0, "skipped": 0}
    assert drain2["reply"] == {"claimed": 0, "sent": 0, "failed": 0, "skipped": 0}
    assert _total_send_calls(send_calls) == 1


# ---------------------------------------------------------------------------
# Scenario C — repeated inbox worker run
# ---------------------------------------------------------------------------


async def test_scenario_c_repeated_inbox_worker_run(
    wecom_env,
    wecom_client,
    queued_flags,
    pipeline_db,
    monkeypatch,
):
    send_calls = _install_send_tracker(monkeypatch)
    pull_count = {"n": 0}

    def counting_pull(*args, **kwargs):
        pull_count["n"] += 1
        return _pipeline_pull_messages(*args, **kwargs)

    monkeypatch.setattr(
        "services.fiqa_api.wecom.slice.pull_customer_text_messages",
        counting_pull,
    )

    await _post_kf_callback(wecom_client, wecom_env)

    first = inbox_worker.process_pending_wecom_inbox_events(limit=10)
    second = inbox_worker.process_pending_wecom_inbox_events(limit=10)

    assert first == {"claimed": 1, "processed": 1, "failed": 0, "skipped": 0}
    assert second == {"claimed": 0, "processed": 0, "failed": 0, "skipped": 0}
    assert pull_count["n"] == 1
    assert len(pipeline_db.outbox_rows) == 1

    reply_outbox.process_pending_wecom_reply_outbox(limit=10)
    assert _total_send_calls(send_calls) == 1


# ---------------------------------------------------------------------------
# Scenario D — repeated reply sender run
# ---------------------------------------------------------------------------


async def test_scenario_d_repeated_reply_sender_run(
    wecom_env,
    wecom_client,
    queued_flags,
    pipeline_db,
    monkeypatch,
):
    send_calls = _install_send_tracker(monkeypatch)
    monkeypatch.setattr(
        "services.fiqa_api.wecom.slice.pull_customer_text_messages",
        _pipeline_pull_messages,
    )

    await _post_kf_callback(wecom_client, wecom_env)
    inbox_worker.process_pending_wecom_inbox_events(limit=10)

    first = reply_outbox.process_pending_wecom_reply_outbox(limit=10)
    second = reply_outbox.process_pending_wecom_reply_outbox(limit=10)

    assert first == {"claimed": 1, "sent": 1, "failed": 0, "skipped": 0}
    assert second == {"claimed": 0, "sent": 0, "failed": 0, "skipped": 0}
    assert _total_send_calls(send_calls) == 1
    outbox_row = next(iter(pipeline_db.outbox_rows.values()))
    assert outbox_row["status"] == "sent"


# ---------------------------------------------------------------------------
# Scenario E — failure safety
# ---------------------------------------------------------------------------


async def test_scenario_e_reply_sender_failure_marks_failed_not_sent(
    wecom_env,
    wecom_client,
    queued_flags,
    pipeline_db,
    monkeypatch,
):
    monkeypatch.setattr(
        "services.fiqa_api.wecom.slice.pull_customer_text_messages",
        _pipeline_pull_messages,
    )

    def failing_send(*_a, **_k):
        raise RuntimeError("wecom_send_msg_api_error_v1 errcode=40001 errmsg=invalid token")

    monkeypatch.setattr(reply_outbox, "send_menu_reply", failing_send)
    monkeypatch.setattr(reply_outbox, "send_text_reply", failing_send)

    await _post_kf_callback(wecom_client, wecom_env)
    inbox_worker.process_pending_wecom_inbox_events(limit=10)

    summary = reply_outbox.process_pending_wecom_reply_outbox(limit=10)
    assert summary == {"claimed": 1, "sent": 0, "failed": 1, "skipped": 0}

    outbox_row = next(iter(pipeline_db.outbox_rows.values()))
    assert outbox_row["status"] == "failed"
    assert outbox_row["sent_at"] is None
    assert outbox_row["failed_at"] is not None
    assert outbox_row["errcode"] == 40001
    assert outbox_row["error_message"]

    retry = reply_outbox.process_pending_wecom_reply_outbox(limit=10)
    assert retry == {"claimed": 0, "sent": 0, "failed": 0, "skipped": 0}


def test_scenario_e_exhausted_outbox_row_respects_max_attempts(
    wecom_env, pipeline_db, monkeypatch
):
    """Rows at max_attempts are skipped — no auto-retry of failed terminal rows."""
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    dedup_key = reply_outbox.compute_reply_dedup_key(
        msg_id="exhausted_msg",
        external_userid="wm1",
        open_kf_id="wk1",
        reply_type="text",
        reply_payload={"msgtype": "text", "text": {"content": "x"}},
    )
    row_id = pipeline_db._next_outbox_id
    pipeline_db._next_outbox_id += 1
    now = pipeline_db._now()
    pipeline_db.outbox_rows[row_id] = {
        "id": row_id,
        "dedup_key": dedup_key,
        "msg_id": "exhausted_msg",
        "external_userid": "wm1",
        "open_kf_id": "wk1",
        "case_id": None,
        "reply_type": "text",
        "reply_payload_json": {"msgtype": "text", "text": {"content": "x"}},
        "status": "pending",
        "attempt_count": 3,
        "locked_at": None,
        "sent_at": None,
        "failed_at": None,
        "errcode": None,
        "errmsg": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }

    def must_not_send(*_a, **_k):
        raise AssertionError("must not send exhausted row")

    monkeypatch.setattr(reply_outbox, "send_text_reply", must_not_send)

    summary = reply_outbox.process_pending_wecom_reply_outbox(limit=5, max_attempts=3)
    assert summary == {"claimed": 0, "sent": 0, "failed": 0, "skipped": 1}
    assert pipeline_db.outbox_rows[row_id]["status"] == "pending"


# ---------------------------------------------------------------------------
# Scenario F — flags off (backward compatibility)
# ---------------------------------------------------------------------------


async def test_scenario_f_flags_off_synchronous_path_unchanged(
    wecom_env, wecom_client, monkeypatch
):
    """Both flags OFF: callback runs slice inline; no inbox/outbox enqueue."""
    direct_send_calls: list[dict] = []
    enqueue_calls: list[dict] = []
    process_calls: list[dict] = []

    def fake_process(cfg, *, callback_token, open_kf_id, pull_messages=None):
        process_calls.append({"callback_token": callback_token, "open_kf_id": open_kf_id})
        return [{"reply_sent": True}]

    def fake_enqueue(**kwargs):
        enqueue_calls.append(kwargs)
        return True

    def fake_text(cfg, *, external_userid, open_kf_id, content):
        direct_send_calls.append({"content": content})
        return {"errcode": 0}

    def fake_menu(cfg, *, external_userid, open_kf_id, menu):
        direct_send_calls.append({"menu": menu})
        return {"errcode": 0}

    monkeypatch.setattr(
        "services.fiqa_api.routes.wecom_kf_callback.process_kf_msg_or_event",
        fake_process,
    )
    monkeypatch.setattr("services.fiqa_api.wecom.slice.enqueue_wecom_reply", fake_enqueue)
    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_text_reply", fake_text)
    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", fake_menu)

    assert inbox_queue.wecom_inbox_queue_enabled() is False
    assert reply_outbox.wecom_reply_outbox_enabled() is False

    with patch("services.fiqa_api.wecom.inbox_queue.enqueue_wecom_callback_event") as mock_enqueue:
        await _post_kf_callback(wecom_client, wecom_env)

    mock_enqueue.assert_not_called()
    assert len(process_calls) == 1
    assert process_calls[0]["open_kf_id"] == _CALLBACK_OPEN_KF_ID
    assert enqueue_calls == []


async def test_scenario_f_flags_off_direct_send_when_slice_runs(
    wecom_env, wecom_client, monkeypatch, pipeline_db
):
    """Flags OFF with real slice: direct send, no outbox rows."""
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    send_calls: dict[str, list] = {"text": [], "menu": []}

    def fake_text(cfg, *, external_userid, open_kf_id, content):
        send_calls["text"].append({"content": content})
        return {"errcode": 0}

    def fake_menu(cfg, *, external_userid, open_kf_id, menu):
        send_calls["menu"].append({"menu": menu})
        return {"errcode": 0}

    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_text_reply", fake_text)
    monkeypatch.setattr("services.fiqa_api.wecom.slice.send_menu_reply", fake_menu)
    monkeypatch.setattr(
        "services.fiqa_api.wecom.slice.pull_customer_text_messages",
        _pipeline_pull_messages,
    )

    await _post_kf_callback(wecom_client, wecom_env)

    assert len(pipeline_db.inbox_rows) == 0
    assert len(pipeline_db.outbox_rows) == 0
    assert _total_send_calls(send_calls) == 1
    assert inbox_worker.process_pending_wecom_inbox_events() == {
        "claimed": 0,
        "processed": 0,
        "failed": 0,
        "skipped": 0,
    }
