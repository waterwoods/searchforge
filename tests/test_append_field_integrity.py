"""P16 append integrity: additive memory on follow-up append."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from services.fiqa_api.inbox_triage.case_store import (
    _merge_append_field_lists,
    append_follow_up_message,
    save_case,
)
from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append


def _use_temp_case_store(monkeypatch, tmp_path: Path) -> None:
    case_file = tmp_path / "cases.json"
    case_file.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(case_file))
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)


def test_merge_append_field_lists_preserves_prior_collected() -> None:
    existing = {
        "collected_fields": ["vin", "zip", "delivery_date", "primary_driver"],
        "still_needed_fields": ["name", "phone"],
    }
    triage = {
        "collected_fields": ["vin", "zip", "primary_driver", "phone"],
        "still_needed_fields": ["delivery_date", "name"],
    }
    coll, still = _merge_append_field_lists(existing, triage)
    coll_l = [x.lower() for x in coll]
    still_l = [x.lower() for x in still]
    assert "delivery_date" in coll_l
    assert "delivery_date" not in still_l
    assert "phone" in coll_l


def test_merge_append_field_lists_honors_correction_invalidation() -> None:
    existing = {"collected_fields": ["zip", "delivery_date"], "still_needed_fields": []}
    triage = {
        "collected_fields": ["zip"],
        "still_needed_fields": ["delivery_date"],
        "add_car_merge": {
            "correction_turn": True,
            "invalidated_slots": ["delivery_date"],
        },
    }
    coll, still = _merge_append_field_lists(existing, triage)
    assert "delivery_date" not in [x.lower() for x in coll]
    assert "delivery_date" in [x.lower() for x in still]


def test_append_follow_up_ac05_name_phone_preserves_delivery(monkeypatch, tmp_path) -> None:
    _use_temp_case_store(monkeypatch, tmp_path)
    turns: list[dict[str, str]] = []
    msgs = [
        "I bought a 2024 Tesla Model Y and want to add it to my policy.",
        "I already sent the insurance card photo by WeChat.",
        "VIN 7SAYGDEE5PA123456\nZIP 90024\nDelivery date next Wednesday\nI am the primary driver",
    ]
    for msg in msgs:
        triage_conversation(msg, turns)
        turns.append({"role": "customer", "text": msg})
    source = "\n".join(f"[{'客户' if t['role'] == 'customer' else '系统'}] {t['text']}" for t in turns)
    formal = triage_conversation(
        msgs[-1],
        turns,
        reply_truth_context={"formal_submit_this_turn": True},
    )
    case = save_case(source, formal, service_lane="add_car")

    # Simulate triage regression (missing persisted_collected_fields in reply_truth_context).
    append_triage = triage_for_append(
        source,
        "Name: Li Hua\nPhone: 949-555-1234",
        reply_truth_context={"formal_submitted_at": "2026-06-06T12:00:00Z"},
    )
    buggy = dict(append_triage)
    buggy["collected_fields"] = [
        x for x in (append_triage.get("collected_fields") or []) if x != "delivery_date"
    ]
    buggy["still_needed_fields"] = list(buggy.get("still_needed_fields") or []) + ["delivery_date"]
    buggy["office_broker_next_step"] = "联系客户补齐提车日期、姓名、电话，然后出报价"

    updated = append_follow_up_message(case["case_id"], "Name: Li Hua\nPhone: 949-555-1234", buggy)
    assert updated is not None
    coll = [x.lower() for x in (updated.get("collected_fields") or [])]
    still = [x.lower() for x in (updated.get("still_needed_fields") or [])]
    assert "delivery_date" in coll
    assert "vin" in coll
    assert "zip" in coll
    assert "primary_driver" in coll
    assert "name" in coll
    assert "phone" in coll
    assert "delivery_date" not in still
    office = updated.get("office_broker_next_step") or ""
    assert "提车日期" not in office
