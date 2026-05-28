"""Operator surface collapse — README and OPERATOR_SURFACE guardrails."""

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def test_readme_leads_with_unified_intake_not_searchforge_lab():
    readme = (_REPO / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Unified Intake")
    assert "15-minute onboarding" in readme
    assert "OPERATOR_SURFACE.md" in readme
    assert "README_LEGACY_SEARCHFORGE_LAB.md" in readme
    # Collapsed README should not dominate with lab archaeology
    assert len(readme.splitlines()) < 200
    assert "AutoTuner vs heavy baseline" not in readme
    assert "Metrics Hub 使用说明" not in readme
    assert "make ci" not in readme


def test_operator_surface_doc_exists_and_bounded():
    path = _REPO / "docs" / "runbooks" / "OPERATOR_SURFACE.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "THE ONLY IMPORTANT SCRIPTS" in text
    assert "THE ONLY IMPORTANT DOCS" in text
    assert "THE ONLY IMPORTANT ENDPOINTS" in text
    assert "15-MINUTE ONBOARDING PATH" in text
    assert "deploy_paid_pilot.sh" in text
    assert "/health/live" in text
    assert "WHAT MUST NEVER BE BUILT" in text


def test_legacy_readme_archived_with_banner():
    legacy = _REPO / "docs" / "archive" / "README_LEGACY_SEARCHFORGE_LAB.md"
    assert legacy.is_file()
    text = legacy.read_text(encoding="utf-8")
    assert "HISTORICAL / LAB ONLY" in text
    assert "Code Lookup Agent" in text


def test_scripts_readme_points_to_operator_surface():
    readme = (_REPO / "scripts" / "README.md").read_text(encoding="utf-8")
    operator = _REPO / "scripts" / "README_OPERATOR.md"
    assert operator.is_file()
    assert "README_OPERATOR.md" in readme
    assert "run_demo_local.sh" in readme
    assert "start_all.sh" in readme
    op_text = operator.read_text(encoding="utf-8")
    assert "trial_launch_check.sh" in op_text
    assert len(op_text.splitlines()) < 80


def test_lab_infra_index_exists():
    path = _REPO / "docs" / "archive" / "platform" / "README_LAB_INFRA.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Makefile.lab" in text
    assert "run_demo_local.sh" in text
