from pathlib import Path
import sys
from typing import Any, Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app
from services.fiqa_api.routes import contract_v1


client = TestClient(app)


def _status_stub(status: str = "SUCCEEDED", started: float = 1731160000.0) -> Tuple[contract_v1._StatusData, Dict[str, Any]]:
    return contract_v1._StatusData(status=status, rc=0, started=started, ended=started + 10), {}


def test_status_ok_invalid_id_returns_400():
    response = client.get("/api/v1/experiment/status/BAD!")
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "invalid_job_id"
    assert body["code"] == "invalid_job_id"


def test_review_normalizes_metrics_keys(monkeypatch):
    monkeypatch.setattr(
        contract_v1,
        "load_manifest",
        lambda job_id: (
            {
                "summary": {
                    "p95_ms": 0,  # should become null
                    "err_rate": "0.002",
                    "recall@10": 0.51,
                    "cost_tokens": "0",
                }
            },
            "manifest/path.json",
        ),
    )
    monkeypatch.setattr(
        contract_v1,
        "load_baseline",
        lambda: (
            {"summary": {"p95_ms": 900, "recall_at_10": 0.6, "cost_tokens": 8000}},
            "baseline/path.json",
        ),
    )
    monkeypatch.setattr(contract_v1, "_get_log_lines", lambda job_id, tail, status: ([], None))
    monkeypatch.setattr(contract_v1, "_resolve_status", lambda job_id, allow_missing=False: _status_stub())

    response = client.get("/api/v1/experiment/review", params={"job_id": "abcdef", "suggest": 1})
    assert response.status_code == 200
    payload = response.json()
    summary = payload["summary"]
    assert summary["recall_at_10"] == pytest.approx(0.51)
    assert summary["cost_tokens"] == 0
    assert summary["p95_ms"] is None


def test_apply_returns_links_and_job_id(monkeypatch):
    class DummyResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return {
                "job_id": "aaaaaa",
                "poll": "/api/experiment/status/aaaaaa",
                "logs": "/api/experiment/logs/aaaaaa",
            }

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *_args, **_kwargs):
            return DummyResponse()

    monkeypatch.setattr(contract_v1.httpx, "AsyncClient", lambda *a, **kw: DummyClient())
    monkeypatch.setattr(contract_v1, "_resolve_status", lambda job_id, allow_missing=False: _status_stub(started=42.0))

    response = client.post(
        "/api/v1/experiment/apply",
        json={"job_id": "abcdef", "preset": "smoke-fast"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == "aaaaaa"
    assert body["poll"].endswith("/aaaaaa")
    assert body["logs"].endswith("/aaaaaa")


def test_logs_tail_param_bounds():
    response = client.get("/api/v1/experiment/logs/abcdef?tail=0")
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_tail"


def test_error_shape_is_uniform(monkeypatch):
    def raise_not_found(job_id: str, allow_missing: bool = False):
        raise contract_v1.ContractApiError(404, "not_found", "missing")

    monkeypatch.setattr(contract_v1, "_resolve_status", raise_not_found)
    response = client.get("/api/v1/experiment/status/abcdef")
    assert response.status_code == 404
    body = response.json()
    assert body == {"error": "not_found", "code": "not_found", "detail": "missing"}

