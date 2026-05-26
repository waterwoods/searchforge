"""Simplification master plan remains the reduction SSOT."""

from pathlib import Path


def test_simplification_master_plan_exists_and_points_to_product_shape():
    path = Path("docs/SIMPLIFICATION_MASTER_PLAN.md")
    assert path.is_file(), "docs/SIMPLIFICATION_MASTER_PLAN.md is required"
    text = path.read_text(encoding="utf-8")
    assert "CURRENT_REAL_PRODUCT" in text
    assert "THE_10_HIGHEST_ROI_SIMPLIFICATIONS" in text
    assert "docs/CURRENT_PRODUCT_SHAPE.md" in text
    assert "UNIFIED_INTAKE_PRODUCT_ONLY=1" in text
