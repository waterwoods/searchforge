"""Deployment profile — product-only honesty and inline route inventory."""

from fastapi.testclient import TestClient

from services.fiqa_api.deployment_profile import (
    PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN,
    deployment_operator_warnings,
    intake_schema_epoch,
    is_unified_intake_product_only,
    operator_runtime_hints,
    platform_inline_route_leak_count,
)
from services.fiqa_api.app_main import app


def test_platform_inline_inventory_empty_after_platform_extract():
    """Ungated inline leaks were moved to ``platform_inline_routes`` (platform-full only)."""
    assert PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN == ()
    assert platform_inline_route_leak_count() == 0


def test_platform_inline_count_matches_tuple():
    assert platform_inline_route_leak_count() == len(PLATFORM_INLINE_ROUTES_UNGATED_IN_APP_MAIN)


def test_is_product_only_default_off(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_PRODUCT_ONLY", raising=False)
    assert is_unified_intake_product_only() is False
    monkeypatch.setenv("UNIFIED_INTAKE_PRODUCT_ONLY", "1")
    assert is_unified_intake_product_only() is True


def test_health_exposes_deployment_profile_operational_truth():
    """Support/operators read GET /health for persistence mode; profile must match env."""
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    dp = body.get("deployment_profile")
    assert isinstance(dp, dict)
    assert dp.get("unified_intake_product_only") == is_unified_intake_product_only()
    assert dp.get("platform_inline_route_leak_count") == platform_inline_route_leak_count()
    assert dp.get("intake_schema_epoch") == intake_schema_epoch()
    auth = dp.get("auth_posture")
    assert isinstance(auth, dict)
    assert auth.get("support_export_surface") in ("anonymous_ok", "api_key_required")
    tt = dp.get("tenant_truth")
    assert isinstance(tt, dict)
    assert tt.get("tenant_id_authoritative") is None
    assert tt.get("semantics") == "client_asserted_org_id_not_tenant_authority_v1"
    hints = dp.get("operator_runtime_hints")
    assert isinstance(hints, dict)
    assert hints.get("unified_intake_product_only") == is_unified_intake_product_only()
    assert "demo_mode" in hints and "env_equals_prod" in hints
    assert "env_label_raw" in hints and "demo_mode_raw" in hints
    assert "unified_intake_allow_inmemory_sessions_for_tests" in hints
    ow = hints.get("operator_warnings")
    assert isinstance(ow, list)


def test_operator_runtime_hints_follows_env(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("FAST_STARTUP", "0")
    monkeypatch.delenv("UNIFIED_INTAKE_PRODUCT_ONLY", raising=False)
    h = operator_runtime_hints()
    assert h["demo_mode"] is True
    assert h["env_equals_prod"] is True
    assert h["fast_startup"] is False
    assert h["unified_intake_product_only"] is False
    assert h.get("env_label_raw") == "prod"
    assert h.get("demo_mode_raw") == "true"
    assert "env_prod_with_demo_mode_truthy_v1" in (h.get("operator_warnings") or [])


def test_deployment_operator_warnings_prod_demo_contradiction(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    w = deployment_operator_warnings()
    assert "env_prod_with_demo_mode_truthy_v1" in w


def test_health_tenant_truth_reflects_x_org_id(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    c = TestClient(app)
    r = c.get("/health", headers={"X-Org-Id": "office-alpha"})
    assert r.status_code == 200
    tt = (r.json().get("deployment_profile") or {}).get("tenant_truth") or {}
    assert tt.get("client_asserted_org_id") == "office-alpha"
