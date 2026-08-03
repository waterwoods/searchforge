"""Focused tests for tools/export_case_value_metrics.py (fixtures only)."""

from __future__ import annotations

import json
from pathlib import Path

from tools.export_case_value_metrics import compute_case_value_metrics

FIXTURE = {
    "case_id": "case_fixture_metrics_001",
    "created_at": "2026-08-03T18:34:50Z",
    "formal_submitted_at": "2026-08-03T18:34:50Z",
    "office_materials_accepted_at": "2026-08-03T19:10:06Z",
    "broker_confirmed_at": None,
    "claim_timeline": [
        {
            "event_type": "broker_supplement_reviewed",
            "created_at": "2026-08-03T19:10:05Z",
            "actor": "broker",
        },
        {
            "event_type": "broker_office_materials_accepted",
            "created_at": "2026-08-03T19:10:06Z",
            "actor": "broker",
        },
    ],
    "p20_slice1_projection": {
        "open_request": {
            "request_id": "req_1",
            "created_at": "2026-08-03T18:41:08Z",
            "completed_at": "2026-08-03T19:09:03Z",
            "items": [
                {
                    "request_item_id": "req_item_1",
                    "status": "satisfied",
                    "satisfied_at": "2026-08-03T19:09:03Z",
                    "customer_response": {
                        "submitted_at": "2026-08-03T19:09:03Z",
                    },
                }
            ],
        },
        "latest_events": [
            {
                "event_type": "broker_request_more_created",
                "created_at": "2026-08-03T18:41:08Z",
            },
            {
                "event_type": "supplement_submitted",
                "created_at": "2026-08-03T19:09:03Z",
            },
            {
                "event_type": "broker_supplement_reviewed",
                "created_at": "2026-08-03T19:10:05Z",
            },
        ],
    },
}


def test_compute_happy_path_timings():
    row = compute_case_value_metrics(FIXTURE)
    assert row["case_id"] == "case_fixture_metrics_001"
    assert row["customer_started_at"] == "2026-08-03T18:34:50Z"
    assert row["formal_submitted_at"] == "2026-08-03T18:34:50Z"
    assert row["time_to_formal_submit_sec"] == "0"
    assert row["first_request_more_at"] == "2026-08-03T18:41:08Z"
    assert row["request_more_loops"] == 1
    assert row["supplement_submitted_at"] == "2026-08-03T19:09:03Z"
    assert int(row["supplement_turnaround_sec"]) == 1675  # 18:41:08 → 19:09:03
    assert row["broker_supplement_reviewed_at"] == "2026-08-03T19:10:05Z"
    assert row["office_materials_accepted_at"] == "2026-08-03T19:10:06Z"
    assert int(row["time_to_office_accept_sec"]) == 2116
    assert "unsupported:broker_first_open_not_recorded" in row["data_quality_notes"]
    assert "unsupported:ai_accept_edit_reject_rates_no_events" in row["data_quality_notes"]
    assert "pre_submit_dwell_not_separately_recorded" in row["data_quality_notes"]


def test_missing_timestamps_left_blank():
    row = compute_case_value_metrics({"case_id": "case_empty", "created_at": "2026-08-03T10:00:00Z"})
    assert row["formal_submitted_at"] == ""
    assert row["time_to_formal_submit_sec"] == ""
    assert row["first_request_more_at"] == ""
    assert row["request_more_loops"] == ""
    assert row["supplement_turnaround_sec"] == ""
    assert row["office_materials_accepted_at"] == ""
    assert "missing:formal_submitted_at" in row["data_quality_notes"]
    assert "unsupported:broker_first_open_not_recorded" in row["data_quality_notes"]


def test_never_fabricates_broker_open_when_null():
    case = dict(FIXTURE)
    case["broker_confirmed_at"] = None
    row = compute_case_value_metrics(case)
    assert "broker_first_open" not in row
    assert "unsupported:broker_first_open_not_recorded" in row["data_quality_notes"]


def test_evidence_case_final_fixture_if_present():
    path = Path("docs/evidence/qa-fast-lane/20260803T190949Z-final-phone/case-final.json")
    if not path.is_file():
        return
    case = json.loads(path.read_text(encoding="utf-8"))
    row = compute_case_value_metrics(case)
    assert row["case_id"] == "case_4e5adf36c637"
    assert row["request_more_loops"] == 1
    assert row["office_materials_accepted_at"] == "2026-08-03T19:10:06Z"
    assert row["supplement_turnaround_sec"] != ""
    assert "unsupported:broker_first_open_not_recorded" in row["data_quality_notes"]
