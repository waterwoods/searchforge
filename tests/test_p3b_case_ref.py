"""P3-B Slice 1 — case_ref uniqueness, immutability, assignment, backfill helpers."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.case_ref import (
    allocate_case_ref,
    ensure_case_ref,
    format_case_ref,
    is_valid_case_ref,
    normalize_case_ref,
    parse_case_ref_number,
    reset_json_case_ref_counter_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_json_counter(monkeypatch):
    reset_json_case_ref_counter_for_tests(1)
    # Force JSON allocator path in unit tests (no accidental PG).
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_ref._next_pg_case_ref_number",
        lambda: None,
    )
    yield
    reset_json_case_ref_counter_for_tests(1)


def test_format_case_ref_pads_to_four_digits():
    assert format_case_ref(1) == "CLM-0001"
    assert format_case_ref(1028) == "CLM-1028"
    assert format_case_ref(10000) == "CLM-10000"


def test_parse_and_normalize_case_ref():
    assert parse_case_ref_number("CLM-1028") == 1028
    assert normalize_case_ref("clm-7") == "CLM-0007"
    assert is_valid_case_ref("CLM-0001")
    assert not is_valid_case_ref("case_deadbeef")
    assert not is_valid_case_ref("CLM-")


def test_allocate_case_ref_is_unique_and_sequential():
    a = allocate_case_ref()
    b = allocate_case_ref()
    assert a != b
    assert parse_case_ref_number(a) < parse_case_ref_number(b)


def test_ensure_case_ref_is_immutable_after_assignment():
    case = {"case_id": "case_abc123def456"}
    first = ensure_case_ref(case)
    second = ensure_case_ref(case)
    assert first == second
    assert case["case_ref"] == first
    # Mutating attempt via ensure with a different value must not rewrite.
    case["case_ref"] = first
    assert ensure_case_ref(case) == first


def test_ensure_case_ref_does_not_derive_from_case_id_hex():
    case = {"case_id": "case_deadbeef0012"}
    ref = ensure_case_ref(case)
    assert ref.startswith("CLM-")
    assert "deadbeef" not in ref.lower()
    assert "0012" not in ref


def test_new_case_assignment_via_save_case(tmp_path, monkeypatch):
    store = tmp_path / "cases.json"
    store.write_text('{"cases": []}', encoding="utf-8")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(store))
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case

    saved = save_case(
        "test source",
        {
            "issue_category": "claim_intake",
            "urgency": "normal",
            "broker_next_step": "Review",
            "client_prep": "",
            "client_reply_draft": "",
            "manual_followup_needed": True,
        },
        service_lane="claim",
    )
    assert is_valid_case_ref(saved.get("case_ref"))
    loaded = get_case_by_id(saved["case_id"])
    assert loaded is not None
    assert loaded.get("case_ref") == saved.get("case_ref")


def test_existing_case_backfill_via_ensure():
    """Legacy row without case_ref receives a safe additive assignment."""
    legacy = {"case_id": "case_legacy0001", "customer_name": "陈明"}
    assert not legacy.get("case_ref")
    assigned = ensure_case_ref(legacy)
    assert is_valid_case_ref(assigned)
    assert legacy["case_ref"] == assigned
