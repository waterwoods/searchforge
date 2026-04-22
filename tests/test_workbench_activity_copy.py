"""Workbench activity copy loads from configs/common/workbench_activity_copy.json."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.config_loader import get_workbench_activity_copy


def test_workbench_activity_has_defaults():
    wb = get_workbench_activity_copy()
    assert wb["prefix"]
    assert wb["mark_test_on"]
    assert wb["archive_on"]
