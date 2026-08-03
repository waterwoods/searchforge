"""Focused tests for tools/export_case_value_metrics.py (fixtures only)."""

from __future__ import annotations

import json
from pathlib import Path

from tools.export_case_value_metrics import compute_case_value_metrics, summarize_metrics

FIXTURE = {
    "case_id": "case_fixture_metrics_001",
    "created_at": "2026-08-03T18:34:50Z",
    "formal_submitted_at": "2026-08-03T18:34:50Z",
    "office_materials_accepted_at": "2026-08-03T19:10:06Z",
    "customer_intake_opened_at": "2026-08-03T18:30:00Z",
    "customer_first_action_at": "2026-08-03T18:32:00Z",
    "broker_first_opened_at": "2026-08-03T18:36:00Z",
    "broker_confirmed_at": None,
    "workbench_test": True,
    "claim_timeline": [
        {
            "event_type": "customer_policy_context_confirmed",
            "created_at": "2026-08-03T18:32:00Z",
            "actor": "customer",
        },
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
    assert row["customer_intake_opened_at"] == "2026-08-03T18:30:00Z"
    assert row["customer_first_action_at"] == "2026-08-03T18:32:00Z"
    assert row["formal_submitted_at"] == "2026-08-03T18:34:50Z"
    assert int(row["intake_open_to_submit_sec"]) == 290
    assert int(row["first_action_to_submit_sec"]) == 170
    assert row["policy_context_confirmed_at"] == "2026-08-03T18:32:00Z"
    assert row["broker_first_opened_at"] == "2026-08-03T18:36:00Z"
    assert int(row["submit_to_broker_first_open_sec"]) == 70
    assert row["first_request_more_at"] == "2026-08-03T18:41:08Z"
    assert row["request_more_loops"] == 1
    assert row["supplement_submitted_at"] == "2026-08-03T19:09:03Z"
    assert int(row["request_more_to_supplement_sec"]) == 1675
    assert int(row["supplement_turnaround_sec"]) == 1675  # legacy alias
    assert row["broker_supplement_reviewed_at"] == "2026-08-03T19:10:05Z"
    assert int(row["supplement_to_broker_review_sec"]) == 62
    assert row["office_materials_accepted_at"] == "2026-08-03T19:10:06Z"
    assert int(row["first_action_to_office_accept_sec"]) == 2286
    assert row["customer_started_at"] == "2026-08-03T18:34:50Z"  # legacy
    assert "note:observational_open_not_active_work" in row["data_quality_notes"]
    assert "qa_or_artificial_timing" in row["data_quality_notes"]
    assert "unsupported:ai_accept_edit_reject_rates_no_events" in row["data_quality_notes"]
    assert "pre_submit_dwell_not_separately_recorded" in row["data_quality_notes"]


def test_missing_timestamps_left_blank():
    row = compute_case_value_metrics({"case_id": "case_empty", "created_at": "2026-08-03T10:00:00Z"})
    assert row["formal_submitted_at"] == ""
    assert row["customer_intake_opened_at"] == ""
    assert row["customer_first_action_at"] == ""
    assert row["broker_first_opened_at"] == ""
    assert row["intake_open_to_submit_sec"] == ""
    assert row["first_action_to_submit_sec"] == ""
    assert row["submit_to_broker_first_open_sec"] == ""
    assert row["time_to_formal_submit_sec"] == ""
    assert row["first_request_more_at"] == ""
    assert row["request_more_loops"] == ""
    assert row["request_more_to_supplement_sec"] == ""
    assert row["office_materials_accepted_at"] == ""
    assert "missing:formal_submitted_at" in row["data_quality_notes"]
    assert "missing:customer_intake_opened_at" in row["data_quality_notes"]
    assert "unsupported:broker_first_open_not_recorded" in row["data_quality_notes"]


def test_never_fabricates_broker_open_when_null():
    case = dict(FIXTURE)
    case["broker_first_opened_at"] = None
    case.pop("case_activity_timing", None)
    row = compute_case_value_metrics(case)
    assert row["broker_first_opened_at"] == ""
    assert row["submit_to_broker_first_open_sec"] == ""
    assert "unsupported:broker_first_open_not_recorded" in row["data_quality_notes"]


def test_summary_mode_small_sample_not_significant():
    rows = [compute_case_value_metrics(FIXTURE)]
    summary = summarize_metrics(rows)
    assert summary["case_count"] == 1
    assert summary["statistically_meaningful"] is False
    assert summary["durations"]["request_more_to_supplement_sec"]["median"] == 1675.0
    assert summary["missing_data_rate"]["broker_first_opened_at"]["missing"] == 0


def test_evidence_case_final_fixture_if_present():
    path = Path("docs/evidence/qa-fast-lane/20260803T190949Z-final-phone/case-final.json")
    if not path.is_file():
        return
    case = json.loads(path.read_text(encoding="utf-8"))
    row = compute_case_value_metrics(case)
    assert row["case_id"] == "case_4e5adf36c637"
    assert row["request_more_loops"] == 1
    assert row["office_materials_accepted_at"] == "2026-08-03T19:10:06Z"
    assert row["request_more_to_supplement_sec"] != ""
    # Pre-instrumentation evidence will lack new open stamps.
    assert row["customer_intake_opened_at"] == "" or row["customer_intake_opened_at"]
    assert "unsupported:broker_first_open_not_recorded" in row["data_quality_notes"] or row[
        "broker_first_opened_at"
    ]
