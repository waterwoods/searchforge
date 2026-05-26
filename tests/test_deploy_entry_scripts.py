"""Paid-pilot vs demo-cloud deploy entry scripts — posture must not mix."""

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PAID = _REPO / "scripts" / "deploy_paid_pilot.sh"
_DEMO = _REPO / "scripts" / "deploy_demo_cloud_smoke.sh"
_CORE = _REPO / "scripts" / "deploy_cloud_run_core.sh"
_WRAPPER = _REPO / "scripts" / "deploy_rag_demo.sh"
_SHAPE = _REPO / "docs" / "CURRENT_PRODUCT_SHAPE.md"


def test_paid_pilot_entry_forces_product_only_and_no_demo_mode():
    src = _PAID.read_text(encoding="utf-8")
    assert "UNIFIED_INTAKE_PRODUCT_ONLY=1" in src
    assert "DEPLOY_ENTRY=paid_pilot" in src
    assert "unset DEMO_MODE" in src
    assert "deploy_cloud_run_core.sh" in src
    assert "CURRENT_PRODUCT_SHAPE" in src


def test_core_deploy_reapplies_posture_after_env_file():
    src = _CORE.read_text(encoding="utf-8")
    assert "_apply_deploy_entry_posture" in src
    assert 'paid_pilot)' in src
    assert 'demo_smoke)' in src


def test_demo_cloud_smoke_sets_demo_mode_and_unsets_pilot_strict():
    src = _DEMO.read_text(encoding="utf-8")
    assert "DEMO_MODE=true" in src
    assert "unset PILOT_DEPLOY_STRICT" in src
    assert "deploy_paid_pilot.sh" in src
    assert "deploy_cloud_run_core.sh" in src


def test_deprecated_wrapper_warns_and_delegates_to_core():
    src = _WRAPPER.read_text(encoding="utf-8")
    assert "DEPRECATED" in src
    assert "deploy_cloud_run_core.sh" in src
    assert "deploy_paid_pilot.sh" in src


def test_core_deploy_documents_wrappers_not_operator_default():
    src = _CORE.read_text(encoding="utf-8")
    assert "deploy_paid_pilot.sh" in src
    assert "deploy_demo_cloud_smoke.sh" in src


def test_current_product_shape_documents_deploy_split():
    src = _SHAPE.read_text(encoding="utf-8")
    assert "deploy_paid_pilot.sh" in src
    assert "deploy_demo_cloud_smoke.sh" in src
    assert "Postgres is the only supported persistence truth" in src
    assert "platform_full" in src
    assert "legacy/dev" in src.lower() or "legacy/dev" in src


def test_deployment_docs_reference_current_product_shape():
    for rel in (
        "docs/runbooks/DEPLOYMENT_PLAYBOOK.md",
        "docs/DEPLOYMENT_READINESS.md",
    ):
        text = (_REPO / rel).read_text(encoding="utf-8")
        assert "CURRENT_PRODUCT_SHAPE.md" in text
        assert "deploy_paid_pilot.sh" in text
