"""Current product shape SSOT doc exists and is wired into runbooks."""

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
SSOT = _REPO / "docs" / "CURRENT_PRODUCT_SHAPE.md"


def test_current_product_shape_doc_exists():
    assert SSOT.is_file()
    text = SSOT.read_text(encoding="utf-8")
    assert "Unified Intake" in text
    assert "UNIFIED_INTAKE_PRODUCT_ONLY=1" in text
    assert "DEMO_MODE" in text
    assert "Postgres" in text


def test_deployment_playbook_references_current_product_shape():
    playbook = (_REPO / "docs" / "runbooks" / "DEPLOYMENT_PLAYBOOK.md").read_text(encoding="utf-8")
    assert "CURRENT_PRODUCT_SHAPE.md" in playbook


def test_project_doc_map_lists_current_product_shape():
    doc_map = (_REPO / "docs" / "PROJECT_DOC_SYSTEM_MAP.md").read_text(encoding="utf-8")
    assert "CURRENT_PRODUCT_SHAPE.md" in doc_map


def test_sprints_readme_marks_historical():
    readme = (_REPO / "docs" / "sprints" / "README.md").read_text(encoding="utf-8")
    assert "historical" in readme.lower()
    assert "CURRENT_PRODUCT_SHAPE.md" in readme
