from __future__ import annotations

import json

from services.fiqa_api.inbox_triage.service_record_read import ServiceRecordReadRepository


def test_list_formally_submitted_add_car_uses_json_truth(monkeypatch, tmp_path):
    store = tmp_path / "cases.json"
    payload = {
        "cases": [
            {
                "case_id": "case_addcar_1",
                "formal_submitted_at": "2026-03-30T00:00:00Z",
                "collected_fields": ["year", "make_model", "zip"],
                "still_needed_fields": ["delivery_date"],
                "quote_ready_status": "almost_ready",
                "customer_name": "Alice",
                "customer_phone": "4155550101",
                "lifecycle_status": "handoff_pending",
            },
            {
                "case_id": "case_not_formal",
                "formal_submitted_at": "",
                "collected_fields": ["year", "make_model", "zip"],
                "still_needed_fields": [],
            },
            {
                "case_id": "case_non_addcar",
                "formal_submitted_at": "2026-03-30T00:00:01Z",
                "collected_fields": ["customer_requested_human"],
                "still_needed_fields": [],
            },
            {
                "case_id": "case_explicit_add_car_lane",
                "formal_submitted_at": "2026-03-30T00:00:02Z",
                "service_lane": "add_car",
                "collected_fields": [],
                "still_needed_fields": [],
            },
        ]
    }
    store.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))

    repo = ServiceRecordReadRepository()
    rows = repo.list_formally_submitted_add_car()

    assert len(rows) == 2
    by_id = {r.case_id: r for r in rows}
    assert by_id["case_addcar_1"].customer_name == "Alice"
    assert by_id["case_addcar_1"].quote_ready_status == "almost_ready"
    assert by_id["case_explicit_add_car_lane"].service_lane == "add_car"
