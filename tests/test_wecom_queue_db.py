"""Tests for WeCom queue Postgres preflight and fail-closed mode (Q0.8.3)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from services.fiqa_api.wecom import inbox_queue, queue_admin, reply_outbox
from services.fiqa_api.wecom.queue_db import (
    WeComQueueDbError,
    preflight_wecom_queue_db,
    wecom_queue_postgres_required,
)
from tests.wecom_pipeline_test_db import InMemoryWeComPipelineDb, install_pipeline_db


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    monkeypatch.delenv("WECOM_INBOX_QUEUE", raising=False)
    monkeypatch.delenv("WECOM_REPLY_OUTBOX", raising=False)
    monkeypatch.delenv("WECOM_QUEUE_ALLOW_MEMORY_FALLBACK", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    inbox_queue.reset_wecom_inbox_memory_for_tests()
    reply_outbox.reset_wecom_reply_outbox_memory_for_tests()
    yield
    inbox_queue.reset_wecom_inbox_memory_for_tests()
    reply_outbox.reset_wecom_reply_outbox_memory_for_tests()


@pytest.fixture
def pipeline_db(monkeypatch):
    db = InMemoryWeComPipelineDb()
    install_pipeline_db(monkeypatch, db)
    return db


def test_postgres_required_when_inbox_queue_flag_on(monkeypatch):
    monkeypatch.setenv("WECOM_INBOX_QUEUE", "1")
    assert wecom_queue_postgres_required() is True


def test_postgres_required_when_outbox_flag_on(monkeypatch):
    monkeypatch.setenv("WECOM_REPLY_OUTBOX", "1")
    assert wecom_queue_postgres_required() is True


def test_preflight_fails_when_db_url_missing():
    with pytest.raises(WeComQueueDbError, match="wecom_queue_db_preflight_v1"):
        preflight_wecom_queue_db()


def test_preflight_fails_when_select_1_fails(monkeypatch):
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")

    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        boom,
    )

    with pytest.raises(WeComQueueDbError, match="Postgres check failed"):
        preflight_wecom_queue_db()


def test_preflight_succeeds_with_pipeline_db(pipeline_db):
    result = preflight_wecom_queue_db()
    assert result["ok"] is True
    assert result["select_1"] is True
    assert "wecom_inbox_events" in result["tables_verified"]


def test_inbox_enqueue_fails_closed_when_queue_on_and_db_down(monkeypatch):
    monkeypatch.setenv("WECOM_INBOX_QUEUE", "1")
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")

    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        boom,
    )

    with pytest.raises(WeComQueueDbError, match="wecom_inbox_enqueue_db_failed_v1"):
        inbox_queue.enqueue_wecom_callback_event(
            dedup_key="k1",
            parsed_event={"OpenKfId": "wk1", "Token": "t1"},
            payload_json={"event": "kf_msg_or_event"},
        )


def test_outbox_enqueue_fails_closed_when_outbox_on_and_db_down(monkeypatch):
    monkeypatch.setenv("WECOM_REPLY_OUTBOX", "1")
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")

    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.service_record_connection",
        boom,
    )

    with pytest.raises(WeComQueueDbError, match="wecom_reply_outbox_enqueue_db_failed_v1"):
        reply_outbox.enqueue_wecom_reply(
            external_userid="wm1",
            open_kf_id="wk1",
            reply_type="text",
            reply_payload={"msgtype": "text", "text": {"content": "hi"}},
        )


def test_inbox_enqueue_allows_memory_when_flag_off_and_no_db():
    created = inbox_queue.enqueue_wecom_callback_event(
        dedup_key="mem1",
        parsed_event={"OpenKfId": "wk1", "Token": "t1"},
        payload_json={"event": "kf_msg_or_event"},
    )
    assert created is True


def test_admin_drain_fails_before_claim_when_preflight_fails(monkeypatch):
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://fake/db")

    with patch(
        "services.fiqa_api.wecom.queue_admin.preflight_wecom_queue_db",
        side_effect=WeComQueueDbError("wecom_queue_db_preflight_v1: SELECT 1 failed"),
    ):
        with pytest.raises(RuntimeError, match="wecom_queue_db_preflight_v1"):
            queue_admin.drain_wecom_queues(limit=1)


def test_admin_status_includes_db_preflight(pipeline_db):
    status = queue_admin.fetch_wecom_queue_status()
    assert status["db_preflight"]["ok"] is True


def test_repair_stale_resets_only_old_processing_rows(pipeline_db):
    stale_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    fresh_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    stale_id = pipeline_db._next_inbox_id
    pipeline_db._next_inbox_id += 1
    pipeline_db.inbox_rows[stale_id] = {
        "id": stale_id,
        "dedup_key": "stale1",
        "open_kf_id": "wk1",
        "external_userid": None,
        "callback_token": "tok1",
        "event_type": "kf_msg_or_event",
        "payload_json": {},
        "status": "processing",
        "attempt_count": 1,
        "locked_at": stale_at,
        "processed_at": None,
        "error_message": None,
        "created_at": stale_at,
        "updated_at": stale_at,
    }

    fresh_id = pipeline_db._next_inbox_id
    pipeline_db._next_inbox_id += 1
    pipeline_db.inbox_rows[fresh_id] = {
        "id": fresh_id,
        "dedup_key": "fresh1",
        "open_kf_id": "wk1",
        "external_userid": None,
        "callback_token": "tok2",
        "event_type": "kf_msg_or_event",
        "payload_json": {},
        "status": "processing",
        "attempt_count": 1,
        "locked_at": fresh_at,
        "processed_at": None,
        "error_message": None,
        "created_at": fresh_at,
        "updated_at": fresh_at,
    }

    result = queue_admin.repair_stale_wecom_queue_rows(stale_timeout_seconds=600)

    assert result["inbox_repaired"] == 1
    assert pipeline_db.inbox_rows[stale_id]["status"] == "pending"
    assert pipeline_db.inbox_rows[stale_id]["locked_at"] is None
    assert pipeline_db.inbox_rows[fresh_id]["status"] == "processing"


def test_stale_processing_row_reclaimed_by_worker(pipeline_db, monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")

    from services.fiqa_api.wecom import inbox_worker
    from services.fiqa_api.wecom.config import load_wecom_kf_config

    load_wecom_kf_config.cache_clear()

    stale_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    row_id = pipeline_db._next_inbox_id
    pipeline_db._next_inbox_id += 1
    pipeline_db.inbox_rows[row_id] = {
        "id": row_id,
        "dedup_key": "reclaim1",
        "open_kf_id": "wk1",
        "external_userid": None,
        "callback_token": "tok1",
        "event_type": "kf_msg_or_event",
        "payload_json": {"event": "kf_msg_or_event", "open_kf_id": "wk1", "token": "tok1"},
        "status": "processing",
        "attempt_count": 1,
        "locked_at": stale_at,
        "processed_at": None,
        "error_message": None,
        "created_at": stale_at,
        "updated_at": stale_at,
    }

    monkeypatch.setattr(
        inbox_worker,
        "process_kf_msg_or_event",
        lambda *a, **k: [],
    )

    summary = inbox_worker.process_pending_wecom_inbox_events(
        limit=1,
        stale_timeout_seconds=600,
    )

    assert summary["claimed"] == 1
    assert summary["processed"] == 1
    assert pipeline_db.inbox_rows[row_id]["status"] == "processed"
