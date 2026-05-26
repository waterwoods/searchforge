"""Optional shared-secret perimeter for ``/api/inbox/*`` (excluding support + WeChat callback)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app


def test_intake_perimeter_open_when_key_unset(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    c = TestClient(app)
    r = c.get("/api/inbox/client-config", params={"client_id": "default"})
    assert r.status_code == 200


def test_intake_perimeter_requires_header_when_key_set(monkeypatch):
    monkeypatch.setenv(
        "UNIFIED_INTAKE_INTAKE_API_KEY",
        "test_intake_secret_key_min_len_ok_12345",
    )
    c = TestClient(app)
    assert c.get("/api/inbox/client-config", params={"client_id": "default"}).status_code == 401
    ok = c.get(
        "/api/inbox/client-config",
        params={"client_id": "default"},
        headers={"X-Unified-Intake-Api-Key": "test_intake_secret_key_min_len_ok_12345"},
    )
    assert ok.status_code == 200


def test_support_routes_use_support_key_not_intake_key(monkeypatch):
    monkeypatch.setenv(
        "UNIFIED_INTAKE_SUPPORT_API_KEY",
        "support_secret_key_min_length_ok_123456",
    )
    monkeypatch.setenv(
        "UNIFIED_INTAKE_INTAKE_API_KEY",
        "intake_secret_key_min_length_ok_123456",
    )
    c = TestClient(app)
    assert c.get("/api/inbox/support/deployment-manifest").status_code == 401
    r = c.get(
        "/api/inbox/support/deployment-manifest",
        headers={"X-Unified-Intake-Support-Key": "support_secret_key_min_length_ok_123456"},
    )
    assert r.status_code == 200
    body = r.json()
    perimeter = body.get("intake_perimeter") or {}
    assert perimeter.get("intake_http_surface") == "api_key_required"
    assert isinstance(perimeter.get("pilot_token_scope_registry"), dict)


def test_wechat_callback_exempt_from_intake_key(monkeypatch):
    monkeypatch.setenv(
        "UNIFIED_INTAKE_INTAKE_API_KEY",
        "test_intake_secret_key_min_len_ok_12345",
    )
    c = TestClient(app, raise_server_exceptions=False)
    r = c.get("/api/inbox/wechat/binding/callback", params={"code": "x", "state": "y"})
    assert r.status_code != 401


def test_intake_auth_posture_prod_risk(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.delenv("UNIFIED_INTAKE_INTAKE_API_KEY", raising=False)
    from services.fiqa_api.security.intake_api_gate import intake_api_auth_posture_dict

    posture = intake_api_auth_posture_dict()
    assert posture.get("production_intake_perimeter_risk") == "production_like_runtime_without_intake_api_key_v1"
