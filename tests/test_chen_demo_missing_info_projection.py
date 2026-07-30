"""Chen Demo trust polish — Brief facts must not appear as Request More gaps.

Regression: 陈明 (chen_camry) submits accident basics; checklist/Brief share one
presence SSOT from case known_facts. Supplied facts are not「仍缺信息」.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_case_brief
from services.fiqa_api.inbox_triage.p20_missing_information import (
    FACT_STATUS_MISSING,
    FACT_STATUS_SUPPLIED_UNCONFIRMED,
    derive_missing_information_checklist,
    merge_fact_records,
    seed_fact_records_from_case,
)


# Current Chen Ming scenario — accident facts as Mini Program would stamp them.
CHEN_MING_KNOWN_FACTS = {
    "accident_description": "在停车场倒车时轻碰右侧护栏，无人受伤。",
    "accident_datetime": "2026-07-18T10:00:00Z",
    "accident_location": "San Jose 停车场",
    "injury_status": "no",
    "anyone_injured": "no",
    "primary_vehicle_summary": "2020 Toyota Camry",
    "qa_label": "演示·陈明",
}

_ACCIDENT_KEYS = (
    "accident_description",
    "accident_datetime",
    "accident_location",
    "injury_status",
)


def test_chen_ming_supplied_facts_are_not_checklist_gaps():
    case = {
        "case_id": "case_chen_ming_demo",
        "customer_name": "陈明",
        "demo_name": "chen_known_customer_demo",
        "service_lane": "claim",
        "known_facts": dict(CHEN_MING_KNOWN_FACTS),
        "case_attachments": [],
        "claim_timeline": [],
    }
    checklist = derive_missing_information_checklist(None, case=case)
    by_key = {row["field_key"]: row for row in checklist}

    for key in _ACCIDENT_KEYS:
        row = by_key[key]
        assert row["status"] == FACT_STATUS_SUPPLIED_UNCONFIRMED, key
        assert row["is_gap"] is False, key
        assert row["value"], key
        # Presentation: Chinese labels on broker path (no English field titles).
        assert "Accident" not in row["label"]
        assert "Anyone injured" not in row["label"]

    must_have_gaps = [
        row
        for row in checklist
        if row.get("business_class") == "must_have" and row.get("is_gap")
    ]
    assert must_have_gaps == []


def test_chen_ming_stale_missing_aggregate_yields_to_case_known_facts():
    """Aggregate seeded empty before customer patch must not contradict Brief."""
    case = {
        "case_id": "case_chen_ming_demo",
        "customer_name": "陈明",
        "demo_name": "chen_known_customer_demo",
        "service_lane": "claim",
        "known_facts": dict(CHEN_MING_KNOWN_FACTS),
        "case_attachments": [],
        "claim_timeline": [],
    }
    stale = seed_fact_records_from_case({"known_facts": {}})
    for key in _ACCIDENT_KEYS:
        assert stale[key]["status"] == FACT_STATUS_MISSING

    merged = merge_fact_records(stale, case=case)
    for key in _ACCIDENT_KEYS:
        assert merged[key]["status"] == FACT_STATUS_SUPPLIED_UNCONFIRMED, key
        assert merged[key]["value"]

    checklist = derive_missing_information_checklist(stale, case=case)
    gaps = {
        row["field_key"]
        for row in checklist
        if row.get("business_class") == "must_have" and row.get("is_gap")
    }
    assert gaps == set()


def test_chen_ming_brief_missing_excludes_submitted_accident_facts():
    case = {
        "case_id": "case_chen_ming_demo",
        "customer_name": "陈明",
        "demo_name": "chen_known_customer_demo",
        "service_lane": "claim",
        "known_facts": dict(CHEN_MING_KNOWN_FACTS),
        "case_attachments": [],
        "claim_timeline": [],
        "risk_flags": [],
    }
    brief = build_claim_case_brief(case)
    key_facts = brief["key_facts"]
    assert key_facts["accident_datetime"]
    assert key_facts["accident_location"] == "San Jose 停车场"
    assert key_facts["injury_status"] == "no"
    assert key_facts["accident_description"]

    missing_keys = {item["key"] for item in brief["missing_info"]}
    for key in _ACCIDENT_KEYS:
        assert key not in missing_keys, f"{key} must not appear under 仍缺信息"
