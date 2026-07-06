"""P19D-3 — H5 task link helper tests."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.h5_task_link import (
    h5_task_frontend_base,
    mask_h5_task_url,
    mint_h5_task_link,
)
from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token


def test_h5_task_frontend_base_prefers_env(monkeypatch):
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://custom.example")
    monkeypatch.delenv("UNIFIED_INTAKE_FRONTEND_ORIGIN", raising=False)
    assert h5_task_frontend_base() == "https://custom.example"


def test_h5_task_frontend_base_default_smoky(monkeypatch):
    monkeypatch.delenv("H5_TASK_FRONTEND_BASE_URL", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_FRONTEND_ORIGIN", raising=False)
    assert h5_task_frontend_base() == "https://ui-smoky-beta.vercel.app"


def test_mask_h5_task_url():
    url = "https://example.test/task/upload/h5t1.abc123.def456"
    masked = mask_h5_task_url(url)
    assert masked == "https://example.test/task/upload/h5t1.…"
    assert "abc123" not in masked


def test_mint_h5_task_link_shape(monkeypatch):
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "unit-test-secret")
    url = mint_h5_task_link(case_id="case_mint", base_url="https://example.test")
    assert url.startswith("https://example.test/task/upload/h5t1.")
    token = url.rsplit("/", 1)[-1]
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.case_id == "case_mint"
    assert claims.lane == "add_car"
    assert claims.slot == "vin_photo"
