"""Tests for WeCom queue admin manual drain/status (Q0.5)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from io import StringIO
from unittest.mock import patch

import pytest

from services.fiqa_api.wecom import inbox_worker, queue_admin, reply_outbox
from services.fiqa_api.wecom.config import load_wecom_kf_config
from tests.wecom_pipeline_test_db import InMemoryWeComPipelineDb, install_pipeline_db


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


@pytest.fixture
def pipeline_db(monkeypatch):
    db = InMemoryWeComPipelineDb()
    install_pipeline_db(monkeypatch, db)
    return db


def _seed_inbox(db: InMemoryWeComPipelineDb, *, dedup_key: str, status: str = "pending", attempt_count: int = 0):
    row_id = db._next_inbox_id
    db._next_inbox_id += 1
    now = datetime.now(timezone.utc)
    db.inbox_rows[row_id] = {
        "id": row_id,
        "dedup_key": dedup_key,
        "open_kf_id": "wk1",
        "external_userid": None,
        "callback_token": "tok1",
        "event_type": "kf_msg_or_event",
        "payload_json": {"event": "kf_msg_or_event", "open_kf_id": "wk1", "token": "tok1"},
        "status": status,
        "attempt_count": attempt_count,
        "locked_at": None,
        "processed_at": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }
    return row_id


def _seed_outbox(db: InMemoryWeComPipelineDb, *, dedup_key: str, status: str = "pending", attempt_count: int = 0):
    row_id = db._next_outbox_id
    db._next_outbox_id += 1
    now = datetime.now(timezone.utc)
    db.outbox_rows[row_id] = {
        "id": row_id,
        "dedup_key": dedup_key,
        "msg_id": "msg1",
        "external_userid": "wm1",
        "open_kf_id": "wk1",
        "case_id": None,
        "reply_type": "text",
        "reply_payload_json": {"msgtype": "text", "text": {"content": "hello"}},
        "status": status,
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


def test_require_database_url_fails_when_missing(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="wecom_queue_admin_db_required_v1"):
        queue_admin.require_service_record_database_url()

    with pytest.raises(RuntimeError, match="SERVICE_RECORD_DATABASE_URL"):
        queue_admin.fetch_wecom_queue_status()

    with pytest.raises(RuntimeError):
        queue_admin.drain_wecom_queues()


def test_fetch_status_counts_rows(pipeline_db):
    _seed_inbox(pipeline_db, dedup_key="in1", status="pending")
    _seed_inbox(pipeline_db, dedup_key="in2", status="processing")
    _seed_inbox(pipeline_db, dedup_key="in3", status="failed")
    _seed_inbox(pipeline_db, dedup_key="in4", status="processed")
    _seed_outbox(pipeline_db, dedup_key="out1", status="pending")
    _seed_outbox(pipeline_db, dedup_key="out2", status="sent")

    status = queue_admin.fetch_wecom_queue_status()

    assert status["mode"] == "status"
    assert status["inbox"]["pending"] == 1
    assert status["inbox"]["processing"] == 1
    assert status["inbox"]["failed"] == 1
    assert status["inbox"]["processed"] == 1
    assert status["outbox"]["pending"] == 1
    assert status["outbox"]["sent"] == 1


def test_fetch_status_includes_stale_and_exhausted_counts(pipeline_db):
    stale_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    row_id = _seed_inbox(pipeline_db, dedup_key="stale1", status="processing", attempt_count=1)
    pipeline_db.inbox_rows[row_id]["locked_at"] = stale_at
    _seed_inbox(pipeline_db, dedup_key="ex1", status="pending", attempt_count=3)

    status = queue_admin.fetch_wecom_queue_status(stale_timeout_seconds=600)

    assert status["inbox"]["processing_stale"] == 1
    assert status["inbox"]["exhausted"] == 1


def test_drain_runs_inbox_worker_then_reply_sender(pipeline_db, monkeypatch):
    _seed_inbox(pipeline_db, dedup_key="drain_in")

    inbox_called = {"n": 0}
    outbox_called = {"n": 0}

    def fake_inbox(*, limit, max_attempts, stale_timeout_seconds):
        inbox_called["n"] += 1
        assert limit == 5
        return {"claimed": 1, "processed": 1, "failed": 0, "skipped": 0}

    def fake_outbox(*, limit, max_attempts, stale_timeout_seconds):
        outbox_called["n"] += 1
        assert limit == 5
        return {"claimed": 0, "sent": 0, "failed": 0, "skipped": 0}

    monkeypatch.setattr(queue_admin, "process_pending_wecom_inbox_events", fake_inbox)
    monkeypatch.setattr(queue_admin, "process_pending_wecom_reply_outbox", fake_outbox)

    result = queue_admin.drain_wecom_queues(limit=5)

    assert inbox_called["n"] == 1
    assert outbox_called["n"] == 1
    assert result["mode"] == "drain"
    assert result["inbox"]["processed"] == 1
    assert result["outbox"]["sent"] == 0


def test_drain_rejects_invalid_limit(pipeline_db):
    with pytest.raises(ValueError, match="invalid_limit"):
        queue_admin.drain_wecom_queues(limit=0)


def test_format_status_report_is_operator_friendly(pipeline_db):
    _seed_inbox(pipeline_db, dedup_key="fmt1", status="pending")
    status = queue_admin.fetch_wecom_queue_status()
    text = queue_admin.format_wecom_queue_report(status)

    assert "WeCom Queue Report" in text
    assert "mode: status" in text
    assert "Inbox (wecom_inbox_events)" in text
    assert "Outbox (wecom_reply_outbox)" in text
    assert "pending:" in text
    assert "payload" not in text.lower()


def test_format_drain_report_is_operator_friendly():
    result = {
        "mode": "drain",
        "limit": 10,
        "max_attempts": 3,
        "stale_timeout_seconds": 600,
        "inbox": {"claimed": 2, "processed": 2, "failed": 0, "skipped": 0},
        "outbox": {"claimed": 1, "sent": 1, "failed": 0, "skipped": 0},
    }
    text = queue_admin.format_wecom_queue_report(result)

    assert "Inbox worker" in text
    assert "Reply outbox sender" in text
    assert "claimed:   2" in text
    assert "sent:      1" in text


def test_status_mode_does_not_drain(pipeline_db, monkeypatch):
    _seed_inbox(pipeline_db, dedup_key="status_only")

    def must_not_drain(*_a, **_k):
        raise AssertionError("drain must not run in status mode")

    monkeypatch.setattr(queue_admin, "process_pending_wecom_inbox_events", must_not_drain)
    monkeypatch.setattr(queue_admin, "process_pending_wecom_reply_outbox", must_not_drain)

    queue_admin.fetch_wecom_queue_status()
    assert pipeline_db.inbox_rows[1]["status"] == "pending"


def test_drain_integration_with_pipeline_db(pipeline_db, monkeypatch):
    """End-to-end drain helper against in-memory Postgres fake."""
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()

    _seed_inbox(pipeline_db, dedup_key="int_in")

    monkeypatch.setattr(
        inbox_worker,
        "process_kf_msg_or_event",
        lambda *a, **k: [],
    )

    send_calls = {"n": 0}

    def fake_send(*_a, **_k):
        send_calls["n"] += 1
        return {"errcode": 0}

    monkeypatch.setattr(reply_outbox, "send_text_reply", fake_send)
    monkeypatch.setattr(reply_outbox, "send_menu_reply", fake_send)

    inbox_only = queue_admin.drain_wecom_queues(limit=10)
    assert inbox_only["inbox"]["processed"] == 1
    assert inbox_only["outbox"]["sent"] == 0

    _seed_outbox(pipeline_db, dedup_key="int_out")
    outbox_only = queue_admin.drain_wecom_queues(limit=10)
    assert outbox_only["inbox"]["claimed"] == 0
    assert outbox_only["outbox"]["sent"] == 1
    assert send_calls["n"] == 1


def test_cli_status_mode(monkeypatch, pipeline_db, capsys):
    _seed_inbox(pipeline_db, dedup_key="cli1", status="pending")

    from scripts import wecom_drain_queues

    monkeypatch.setattr(
        "sys.argv",
        ["wecom_drain_queues.py", "--status"],
    )
    code = wecom_drain_queues.main()
    out = capsys.readouterr().out

    assert code == 0
    assert "mode: status" in out
    assert "pending:" in out


def test_cli_drain_mode_json(monkeypatch, pipeline_db):
    monkeypatch.setattr(
        queue_admin,
        "process_pending_wecom_inbox_events",
        lambda **k: {"claimed": 0, "processed": 0, "failed": 0, "skipped": 0},
    )
    monkeypatch.setattr(
        queue_admin,
        "process_pending_wecom_reply_outbox",
        lambda **k: {"claimed": 0, "sent": 0, "failed": 0, "skipped": 0},
    )

    from scripts import wecom_drain_queues

    monkeypatch.setattr("sys.argv", ["wecom_drain_queues.py", "--limit", "3", "--json"])
    buf = StringIO()
    with patch("sys.stdout", buf):
        code = wecom_drain_queues.main()

    payload = json.loads(buf.getvalue())
    assert code == 0
    assert payload["mode"] == "drain"
    assert payload["limit"] == 3


def test_cli_missing_db_exits_nonzero(monkeypatch, capsys):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from scripts import wecom_drain_queues

    monkeypatch.setattr("sys.argv", ["wecom_drain_queues.py", "--status"])
    code = wecom_drain_queues.main()
    err = capsys.readouterr().err

    assert code == 2
    assert "SERVICE_RECORD_DATABASE_URL" in err
