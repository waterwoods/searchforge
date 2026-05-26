"""Minimal signed broker token — HMAC sketch (not IAM)."""

from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app
from services.fiqa_api.deployment_profile import deployment_operator_warnings
from services.fiqa_api.security.minimal_signed_broker_token import (
    VerifiedMinimalBrokerToken,
    issue_minimal_broker_token,
    minimal_broker_token_posture_dict,
    verify_minimal_broker_token,
)


def test_issue_verify_roundtrip(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET", "s" * 32)
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING", "bind-test-a")
    tok = issue_minimal_broker_token(
        office_slug="office-east",
        ttl_seconds=600,
        deploy_binding="bind-test-a",
        now=1_700_000_000.0,
        jti="trace-fixed-1",
    )
    v = verify_minimal_broker_token(tok, now=1_700_000_100.0)
    assert isinstance(v, VerifiedMinimalBrokerToken)
    assert v.office_slug == "office-east"
    assert v.jti == "trace-fixed-1"
    assert v.deploy_binding == "bind-test-a"


def test_verify_rejects_expired(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET", "s" * 32)
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING", "b")
    tok = issue_minimal_broker_token(
        office_slug=None,
        ttl_seconds=60,
        deploy_binding="b",
        now=1_000.0,
    )
    assert verify_minimal_broker_token(tok, now=9_999.0) is None


def test_verify_rejects_deploy_mismatch(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET", "s" * 32)
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING", "server-binding")
    tok = issue_minimal_broker_token(
        office_slug=None,
        ttl_seconds=600,
        deploy_binding="other-binding",
        now=1_700_000_000.0,
    )
    assert verify_minimal_broker_token(tok, now=1_700_000_050.0) is None


def test_posture_dict_honest_when_unconfigured(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET", raising=False)
    d = minimal_broker_token_posture_dict()
    assert d.get("verification_configured") is False
    assert "not_tenant_authority" in (d.get("semantics") or "")


def test_support_manifest_token_header_without_secret(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET", raising=False)
    c = TestClient(app)
    r = c.get(
        "/api/inbox/support/deployment-manifest",
        headers={"X-Unified-Intake-Broker-Token": "msbt1.garbage.sig"},
    )
    assert r.status_code == 200
    mbt = r.json().get("minimal_broker_token_request") or {}
    assert mbt.get("verified") is False
    assert mbt.get("verification_note") == "verification_disabled_hmac_secret_unset_v1"


def test_support_manifest_verified_token_matches_org(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET", "z" * 32)
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING", "pinned-z")
    tok = issue_minimal_broker_token(
        office_slug="slug-a",
        ttl_seconds=3600,
        deploy_binding="pinned-z",
    )
    c = TestClient(app)
    r = c.get(
        "/api/inbox/support/deployment-manifest",
        headers={"X-Org-Id": "slug-a", "X-Unified-Intake-Broker-Token": tok},
    )
    assert r.status_code == 200
    mbt = r.json().get("minimal_broker_token_request") or {}
    assert mbt.get("verified") is True
    assert mbt.get("token_trace_id")
    assert mbt.get("office_claim_vs_x_org_id") == "match_v1"
    assert mbt.get("tenant_id_authoritative_remains_null") is True


def test_support_manifest_office_mismatch_flag(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET", "z" * 32)
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING", "pinned-z")
    tok = issue_minimal_broker_token(
        office_slug="token-office",
        ttl_seconds=3600,
        deploy_binding="pinned-z",
    )
    c = TestClient(app)
    r = c.get(
        "/api/inbox/support/deployment-manifest",
        headers={"X-Org-Id": "other-office", "X-Unified-Intake-Broker-Token": tok},
    )
    mbt = r.json().get("minimal_broker_token_request") or {}
    assert mbt.get("verified") is True
    assert mbt.get("office_claim_vs_x_org_id") == "mismatch_v1"


def test_operator_warning_short_broker_hmac(monkeypatch):
    monkeypatch.setenv("UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET", "short")
    monkeypatch.delenv("UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING", raising=False)
    w = deployment_operator_warnings()
    assert "broker_token_hmac_secret_shorter_than_recommended_v1" in w


def test_replay_lineage_includes_minimal_broker_posture(monkeypatch):
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    c = TestClient(app)
    rl = c.get("/api/inbox/support/deployment-manifest").json().get("replay_lineage") or {}
    assert isinstance(rl.get("minimal_broker_token_posture"), dict)
