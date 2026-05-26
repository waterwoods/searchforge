"""Optional shared-secret gate for ``/api/inbox/support/*``."""

from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app
from services.fiqa_api.security.support_export_gate import support_export_auth_posture_dict


def test_support_manifest_anonymous_when_secret_unset(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    c = TestClient(app)
    r = c.get("/api/inbox/support/deployment-manifest")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    ap = body.get("auth_posture") or {}
    assert ap.get("support_export_surface") == "anonymous_ok"
    assert (body.get("request_lineage") or {}).get("request_trace_id")
    rl = body.get("replay_lineage") or {}
    assert rl.get("support_export_manifest_version")
    assert rl.get("intake_schema_epoch")
    assert rl.get("semantics") == "support_replay_handoff_metadata_v1_not_legal_hold"
    assert isinstance(rl.get("minimal_broker_token_posture"), dict)
    tt = body.get("tenant_truth") or {}
    assert tt.get("tenant_id_authoritative") is None
    assert tt.get("semantics") == "client_asserted_org_id_not_tenant_authority_v1"
    hints = body.get("operator_runtime_hints") or {}
    assert isinstance(hints, dict)
    assert "demo_mode" in hints
    assert isinstance(hints.get("operator_warnings"), list)


def test_support_manifest_requires_key_when_configured(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "sekrit-demo-key")
    c = TestClient(app)
    assert c.get("/api/inbox/support/deployment-manifest").status_code == 401
    ok = c.get(
        "/api/inbox/support/deployment-manifest",
        headers={"X-Unified-Intake-Support-Key": "sekrit-demo-key"},
    )
    assert ok.status_code == 200
    ap = ok.json().get("auth_posture") or {}
    assert ap.get("support_export_surface") == "api_key_required"


def test_support_manifest_accepts_bearer_when_configured(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "bearer-abc")
    c = TestClient(app)
    r = c.get(
        "/api/inbox/support/deployment-manifest",
        headers={"Authorization": "Bearer bearer-abc"},
    )
    assert r.status_code == 200


def test_health_includes_auth_posture(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    c = TestClient(app)
    dp = c.get("/health").json().get("deployment_profile") or {}
    assert (dp.get("auth_posture") or {}).get("support_export_surface") == "anonymous_ok"


def test_auth_posture_surfaces_prod_support_export_risk(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    posture = support_export_auth_posture_dict()
    assert posture.get("production_support_export_risk") == "production_like_runtime_without_support_key_v1"


def test_auth_posture_no_prod_risk_when_support_key_configured(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv(
        "UNIFIED_INTAKE_SUPPORT_API_KEY",
        "configured-demo-key-long-enough-for-operator-secret-v1",
    )
    posture = support_export_auth_posture_dict()
    assert "production_support_export_risk" not in posture
    assert "support_operator_warnings" not in posture


def test_auth_posture_warns_short_support_key(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "short")
    posture = support_export_auth_posture_dict()
    assert posture.get("support_operator_warnings") == ["support_api_key_shorter_than_recommended_v1"]
