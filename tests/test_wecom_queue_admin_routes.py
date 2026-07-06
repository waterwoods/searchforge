"""HTTP tests for WeCom queue admin routes (Q0.8.1)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app

_ADMIN_TOKEN = "wecom-queue-admin-test-token-v1"
_AUTH_HEADERS = {"Authorization": f"Bearer {_ADMIN_TOKEN}"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("WECOM_QUEUE_ADMIN_TOKEN", _ADMIN_TOKEN)
    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://test:test@localhost/test")
    return TestClient(app)


def _sample_status() -> dict:
    return {
        "mode": "status",
        "max_attempts": 3,
        "stale_timeout_seconds": 600,
        "inbox": {
            "pending": 1,
            "processing": 0,
            "processed": 2,
            "failed": 0,
            "processing_stale": 0,
            "exhausted": 0,
        },
        "outbox": {
            "pending": 0,
            "sending": 0,
            "sent": 0,
            "failed": 0,
            "sending_stale": 0,
            "exhausted": 0,
        },
    }


def _sample_drain(limit: int = 1) -> dict:
    return {
        "mode": "drain",
        "limit": limit,
        "max_attempts": 3,
        "stale_timeout_seconds": 600,
        "inbox": {"claimed": 1, "processed": 1, "failed": 0, "skipped": 0},
        "outbox": {"claimed": 1, "sent": 1, "failed": 0, "skipped": 0},
    }


def test_status_requires_token_when_unset(monkeypatch):
    monkeypatch.delenv("WECOM_QUEUE_ADMIN_TOKEN", raising=False)
    c = TestClient(app)
    r = c.get("/api/admin/wecom/queues/status")
    assert r.status_code == 503
    assert "wecom_queue_admin_not_configured_v1" in r.json()["detail"]


def test_drain_requires_token_when_unset(monkeypatch):
    monkeypatch.delenv("WECOM_QUEUE_ADMIN_TOKEN", raising=False)
    c = TestClient(app)
    r = c.post("/api/admin/wecom/queues/drain")
    assert r.status_code == 503
    assert "wecom_queue_admin_not_configured_v1" in r.json()["detail"]


def test_status_rejects_wrong_token(client):
    r = client.get(
        "/api/admin/wecom/queues/status",
        headers={"X-Admin-Token": "wrong-token"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "wecom_queue_admin_unauthorized"


def test_drain_rejects_wrong_token(client):
    r = client.post(
        "/api/admin/wecom/queues/drain",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert r.status_code == 401


def test_status_accepts_x_admin_token(client):
    with patch(
        "services.fiqa_api.routes.wecom_queue_admin.fetch_wecom_queue_status",
        return_value=_sample_status(),
    ):
        r = client.get(
            "/api/admin/wecom/queues/status",
            headers={"X-Admin-Token": _ADMIN_TOKEN},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["mode"] == "status"
    assert body["inbox"]["pending"] == 1
    assert "payload" not in json.dumps(body).lower()


def test_status_accepts_bearer_token(client):
    with patch(
        "services.fiqa_api.routes.wecom_queue_admin.fetch_wecom_queue_status",
        return_value=_sample_status(),
    ):
        r = client.get("/api/admin/wecom/queues/status", headers=_AUTH_HEADERS)
    assert r.status_code == 200


def test_drain_calls_drain_wecom_queues_with_default_limit(client):
    with patch(
        "services.fiqa_api.routes.wecom_queue_admin.fetch_wecom_queue_status",
        return_value=_sample_status(),
    ) as fetch_status:
        with patch(
            "services.fiqa_api.routes.wecom_queue_admin.drain_wecom_queues",
            return_value=_sample_drain(1),
        ) as drain:
            r = client.post("/api/admin/wecom/queues/drain", headers=_AUTH_HEADERS)
    assert r.status_code == 200
    drain.assert_called_once_with(limit=1)
    assert fetch_status.call_count == 2
    body = r.json()
    assert body["ok"] is True
    assert body["limit"] == 1
    assert body["inbox"]["processed"] == 1
    assert body["outbox"]["sent"] == 1
    assert body["status_before"]["mode"] == "status"
    assert body["status_after"]["mode"] == "status"
    assert "payload" not in json.dumps(body).lower()


def test_drain_respects_limit_query_param(client):
    with patch(
        "services.fiqa_api.routes.wecom_queue_admin.fetch_wecom_queue_status",
        return_value=_sample_status(),
    ):
        with patch(
            "services.fiqa_api.routes.wecom_queue_admin.drain_wecom_queues",
            return_value=_sample_drain(5),
        ) as drain:
            r = client.post(
                "/api/admin/wecom/queues/drain?limit=5",
                headers=_AUTH_HEADERS,
            )
    assert r.status_code == 200
    drain.assert_called_once_with(limit=5)
    assert r.json()["limit"] == 5


def test_drain_caps_limit_at_25(client):
    with patch(
        "services.fiqa_api.routes.wecom_queue_admin.fetch_wecom_queue_status",
        return_value=_sample_status(),
    ):
        with patch(
            "services.fiqa_api.routes.wecom_queue_admin.drain_wecom_queues",
            return_value=_sample_drain(25),
        ) as drain:
            r = client.post(
                "/api/admin/wecom/queues/drain?limit=100",
                headers=_AUTH_HEADERS,
            )
    assert r.status_code == 200
    drain.assert_called_once_with(limit=25)
    assert r.json()["limit"] == 25


def test_drain_ok_false_when_failures(client):
    drain_result = _sample_drain(1)
    drain_result["inbox"]["failed"] = 1
    with patch(
        "services.fiqa_api.routes.wecom_queue_admin.fetch_wecom_queue_status",
        return_value=_sample_status(),
    ):
        with patch(
            "services.fiqa_api.routes.wecom_queue_admin.drain_wecom_queues",
            return_value=drain_result,
        ):
            r = client.post("/api/admin/wecom/queues/drain", headers=_AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json()["ok"] is False


def test_status_missing_db_returns_503(client):
    with patch(
        "services.fiqa_api.routes.wecom_queue_admin.fetch_wecom_queue_status",
        side_effect=RuntimeError("wecom_queue_admin_db_required_v1"),
    ):
        r = client.get("/api/admin/wecom/queues/status", headers=_AUTH_HEADERS)
    assert r.status_code == 503
    assert "wecom_queue_admin_db_required_v1" in r.json()["detail"]
