"""Deploy script paid-pilot posture — wrong paths must not be the default."""

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DEPLOY = _REPO / "scripts" / "deploy_rag_demo.sh"


def _deploy_source() -> str:
    return _DEPLOY.read_text(encoding="utf-8")


def test_deploy_script_defines_paid_pilot_posture_helper():
    src = _deploy_source()
    assert "_is_paid_pilot_posture" in src


def test_deploy_script_does_not_unconditionally_force_demo_mode():
    src = _deploy_source()
    assert '"DEMO_MODE=true"' not in src
    assert "DEMO_MODE=${DEMO_MODE:-true}" in src


def test_deploy_script_defaults_product_only_for_paid_pilot():
    src = _deploy_source()
    assert 'UNIFIED_INTAKE_PRODUCT_ONLY="${UNIFIED_INTAKE_PRODUCT_ONLY:-1}"' in src


def test_deploy_script_includes_paid_pilot_persistence_defaults():
    src = _deploy_source()
    for needle in (
        "UNIFIED_INTAKE_DB_PRIMARY_WRITES",
        'UNIFIED_INTAKE_JSON_CASE_WRITES="${UNIFIED_INTAKE_JSON_CASE_WRITES:-0}"',
        "UNIFIED_INTAKE_DB_PRIMARY_READS",
    ):
        assert needle in src


def test_deploy_script_requires_pilot_validation_for_paid_posture():
    src = _deploy_source()
    assert "validate_pilot_deploy_env.py" in src
    assert "Paid-pilot deploy posture" in src


def test_deploy_script_passes_intake_and_support_keys_when_set():
    src = _deploy_source()
    assert "UNIFIED_INTAKE_INTAKE_API_KEY" in src
    assert "UNIFIED_INTAKE_SUPPORT_API_KEY" in src


def test_paid_pilot_wrapper_exists_and_defers_to_core():
    paid = (_REPO / "scripts" / "deploy_paid_pilot.sh").read_text(encoding="utf-8")
    assert "deploy_rag_demo.sh" in paid
    assert "UNIFIED_INTAKE_PRODUCT_ONLY=1" in paid
