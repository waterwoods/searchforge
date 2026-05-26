"""Pilot token scope registry + optional triage rate limit (honest perimeter helpers)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app
from services.fiqa_api.deployment_profile import deployment_operator_warnings
from services.fiqa_api.security import pilot_intake_middleware as lim


def test_token_scope_registry_on_health(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_EXPECTED_OFFICE_SLUGS", " alpha , beta ")
    monkeypatch.setenv("UNIFIED_INTAKE_DEPLOY_BROKER_LABEL", "demo-broker")
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    reg = (r.json().get("deployment_profile") or {}).get("token_scope_registry") or {}
    assert reg.get("expected_office_slug_count") == 2
    assert set(reg.get("expected_office_slugs") or []) == {"alpha", "beta"}
    assert reg.get("deploy_broker_label") == "demo-broker"
    assert reg.get("registry_version")


def test_office_expectation_warning_prod_without_intake_key(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("UNIFIED_INTAKE_EXPECTED_OFFICE_SLUGS", "o1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    w = deployment_operator_warnings()
    assert "office_slug_expectation_configured_without_intake_api_key_in_production_like_v1" in w


def test_triage_office_expectation_header_mismatch(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_EXPECTED_OFFICE_SLUGS", "good-office")
    c = TestClient(app)
    r = c.post(
        "/api/inbox/triage",
        json={"text": "notice cancellation"},
        headers={"X-Org-Id": "other-office"},
    )
    assert r.status_code == 200
    assert r.headers.get("x-unified-intake-office-expectation") == "mismatch_v1"


def test_triage_rate_limit_429(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_EXPECTED_OFFICE_SLUGS", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_TRIAGE_POST_MAX_PER_MINUTE_PER_IP", "2")
    lim._store.clear()
    c = TestClient(app)
    hdr = {"X-Forwarded-For": "198.51.100.77"}
    assert c.post("/api/inbox/triage", json={"text": "a"}, headers=hdr).status_code == 200
    assert c.post("/api/inbox/triage", json={"text": "b"}, headers=hdr).status_code == 200
    r3 = c.post("/api/inbox/triage", json={"text": "c"}, headers=hdr)
    assert r3.status_code == 429
    assert r3.json().get("detail") == "triage_post_rate_limited_v1"
