from __future__ import annotations

from services.fiqa_api.inbox_triage.service_record_consistency import compare_snapshot_with_pg
from services.fiqa_api.inbox_triage.service_record_read import ServiceRecordSnapshot


def test_compare_snapshot_with_pg_detects_missing_row():
    snap = ServiceRecordSnapshot(
        case_id="case_1",
        formal_submitted_at="2026-03-30T00:00:00Z",
        customer_name="Alice",
        customer_phone="4155550101",
        lifecycle_status="handoff_pending",
        quote_ready_status="almost_ready",
        still_needed_fields=["delivery_date"],
        collected_fields=["year", "make_model", "zip"],
    )
    assert compare_snapshot_with_pg(snap, None) == ["missing_postgres_row"]


def test_compare_snapshot_with_pg_detects_aligned_and_mismatch_fields():
    snap = ServiceRecordSnapshot(
        case_id="case_2",
        formal_submitted_at="2026-03-30T00:00:00Z",
        customer_name="Alice",
        customer_phone="4155550101",
        lifecycle_status="handoff_pending",
        quote_ready_status="almost_ready",
        still_needed_fields=["delivery_date"],
        collected_fields=["year", "make_model", "zip"],
    )

    aligned = {
        "record_id": "case_2",
        "customer_name": "Alice",
        "customer_phone": "4155550101",
        "lifecycle_status": "handoff_pending",
        "quote_readiness": "almost_ready",
        "extra": {"formal_submitted_at": "2026-03-30T00:00:00Z"},
        "structured_payload": {"still_needed_fields": ["delivery_date"]},
    }
    assert compare_snapshot_with_pg(snap, aligned) == []

    broken = {
        **aligned,
        "customer_phone": "999",
        "quote_readiness": "need_more",
        "structured_payload": {"still_needed_fields": ["zip"]},
    }
    mismatches = compare_snapshot_with_pg(snap, broken)
    assert "customer_phone" in mismatches
    assert "quote_ready_status" in mismatches
    assert "still_needed_fields" in mismatches


def test_compare_snapshot_with_pg_service_lane_when_json_has_lane():
    snap = ServiceRecordSnapshot(
        case_id="case_3",
        formal_submitted_at="2026-03-30T00:00:00Z",
        customer_name="Alice",
        customer_phone="4155550101",
        lifecycle_status="handoff_pending",
        quote_ready_status="almost_ready",
        still_needed_fields=["delivery_date"],
        collected_fields=["year", "make_model", "zip"],
        service_lane="add_car",
    )
    base = {
        "record_id": "case_3",
        "customer_name": "Alice",
        "customer_phone": "4155550101",
        "lifecycle_status": "handoff_pending",
        "quote_readiness": "almost_ready",
        "extra": {"formal_submitted_at": "2026-03-30T00:00:00Z"},
        "structured_payload": {
            "still_needed_fields": ["delivery_date"],
            "service_lane": "add_car",
        },
    }
    assert compare_snapshot_with_pg(snap, base) == []

    missing_lane = {**base, "structured_payload": {"still_needed_fields": ["delivery_date"]}}
    assert "service_lane" in compare_snapshot_with_pg(snap, missing_lane)
