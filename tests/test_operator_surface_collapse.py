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


def test_operator_wrappers_exist():
    operator_dir = _REPO / "scripts" / "operator"
    assert operator_dir.is_dir()
    for name in (
        "run_demo_local.sh",
        "deploy_paid_pilot.sh",
        "trial_launch_check.sh",
        "validate_pilot_deploy_env.sh",
    ):
        wrapper = operator_dir / name
        assert wrapper.is_file(), name
        text = wrapper.read_text(encoding="utf-8")
        assert "README_OPERATOR" in text or "validate_pilot_deploy_env" in text


def test_lab_directories_have_readme():
    for rel in (
        "scripts/lab/README.md",
        "experiments/README.md",
        "agents/README.md",
        "modules/autotuner/README.md",
        "orchestrators/README.md",
        "pipelines/README.md",
        "engines/README.md",
        "k8s/README.md",
        "mcp/README.md",
        "ml_models/README.md",
        "jobhunter-clipper/README.md",
    ):
        path = _REPO / rel
        assert path.is_file(), rel
        assert "LAB ONLY" in path.read_text(encoding="utf-8") or "optional" in path.read_text(encoding="utf-8").lower()


def test_lab_script_index_and_wrappers():
    index = _REPO / "scripts" / "LAB_SCRIPT_INDEX.md"
    assert index.is_file()
    text = index.read_text(encoding="utf-8")
    assert "LAB ONLY" in text
    assert "start_all.sh" in text
    wrapper = _REPO / "scripts" / "lab" / "start_all.sh"
    assert wrapper.is_file()
    wtext = wrapper.read_text(encoding="utf-8")
    assert "LAB ONLY" in wtext


def test_founder_wrappers_exist():
    founder_dir = _REPO / "scripts" / "founder"
    assert founder_dir.is_dir()
    assert (founder_dir / "run_demo_local.sh").is_file()


def test_docs_root_bounded():
    root_md = list((_REPO / "docs").glob("*.md"))
    assert len(root_md) <= 50, f"docs root has {len(root_md)} markdown files (target <=50)"


def test_engineer_onboarding_doc_exists():
    path = _REPO / "docs" / "15_MINUTE_ENGINEER_ONBOARDING.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "What NOT to read" in text
    assert "/readyz" in text
    assert "deploy_paid_pilot.sh" in text


def test_lab_infra_index_exists():
    path = _REPO / "docs" / "archive" / "platform" / "README_LAB_INFRA.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Makefile.lab" in text
    assert "run_demo_local.sh" in text
    assert "sprint_reports" in text
