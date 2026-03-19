#!/usr/bin/env python3
"""
Broker Daily-Use End-to-End Simulation.

Simulates a realistic broker workday with mixed cases:
- queue scan → choose first → open → assess → reopen → append → see what changed → continue → next case

Run: PYTHONPATH=. python3 scripts/run_daily_use_simulation.py
      PYTHONPATH=. python3 scripts/run_daily_use_simulation.py --verbose
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from services.fiqa_api.inbox_triage.case_store import (
    add_case_note,
    append_follow_up_message,
    get_case_by_id,
    list_recent_cases,
    save_case,
    update_case_follow_up,
    update_case_status,
)
from services.fiqa_api.inbox_triage.triage import triage_for_append, triage_message

# Realistic mixed day: 8 cases covering add-car, renewal, claim, missing-doc, appended, reopened
DAILY_USE_SEEDS = [
    {
        "id": "D1",
        "label": "Add-car (ready to quote)",
        "text": "客户要加一台2021 Tesla Model Y，下周提车，ZIP 90210，问今天能不能先出报价",
        "status": "reviewing",
        "waiting_on": "broker",
        "next_contact_by_offset": 0,
        "note": "Same-day quote if driver details come back.",
    },
    {
        "id": "D2",
        "label": "Renewal (bill now)",
        "text": "续保保费太高了，其中一辆去掉会便宜吗，我发了最新的账单",
        "status": "reviewing",
        "waiting_on": "broker",
        "next_contact_by_offset": 0,
        "note": "Bill received; confirm which vehicle to remove.",
    },
    {
        "id": "D3",
        "label": "Claim (just got photos)",
        "text": "刚出事故了，要收集什么？",
        "status": "reviewing",
        "waiting_on": "broker",
        "next_contact_by_offset": 0,
        "note": "First-response claim; guide client.",
        "append_later": "我拍了现场照片，对方车牌和保险信息也发你了",
    },
    {
        "id": "D4",
        "label": "Missing-doc (sent again)",
        "text": "UW follow up - need dec page + garaging proof. 客户说上周发过了",
        "status": "waiting_client",
        "waiting_on": "client",
        "next_contact_by_offset": 1,
        "note": "Client said they can resend tomorrow.",
        "append_later": "declaration page 我又发了一遍，请查收",
    },
    {
        "id": "D5",
        "label": "Add-car (got ZIP later)",
        "text": "客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价",
        "status": "reviewing",
        "waiting_on": "broker",
        "next_contact_by_offset": 0,
        "note": "Waiting on ZIP and driver.",
        "append_later": "我发了ZIP 90210，下周一提车",
    },
    {
        "id": "D6",
        "label": "Cancellation risk (overdue)",
        "text": "Notice: Policy will be cancelled in 7 days due to non-payment. Last notice.",
        "status": "reviewing",
        "waiting_on": "broker",
        "next_contact_by_offset": -1,  # overdue
        "note": "Same-day action; confirm balance due.",
    },
    {
        "id": "D7",
        "label": "Premium review (parked)",
        "text": "客户说这个月保费太高了，能不能看看怎么降一点",
        "status": "waiting_client",
        "waiting_on": "client",
        "next_contact_by_offset": 3,
        "note": "Waiting on latest bill.",
    },
    {
        "id": "D8",
        "label": "DMV / SR-22 (due tomorrow)",
        "text": "DMV信说要 SR-22 proof 才能 clear suspension，这个要带什么？",
        "status": "reviewing",
        "waiting_on": "broker",
        "next_contact_by_offset": 1,
        "note": "Confirm DMV wants SR-22 filing proof.",
    },
]


def iso_date(offset_days: int) -> str:
    today = datetime.now(timezone.utc).date()
    return (today + timedelta(days=offset_days)).isoformat()


def run_daily_use_simulation(verbose: bool = False) -> tuple[int, int, list[str]]:
    """Build mixed queue, simulate broker workflow, return (passed, total, friction_notes)."""
    store_path = REPO_ROOT / "data" / "unified_intake_cases.json"
    orig_path = os.environ.get("UNIFIED_INTAKE_CASES_PATH", "")
    try:
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(store_path)
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(json.dumps({"cases": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        created: list[dict] = []
        for seed in DAILY_USE_SEEDS:
            result = triage_message(seed["text"])
            case = save_case(seed["text"], result)
            case = update_case_status(case["case_id"], seed["status"]) or case
            case = update_case_follow_up(
                case["case_id"],
                seed["waiting_on"],
                iso_date(seed["next_contact_by_offset"]),
            ) or case
            case = add_case_note(case["case_id"], seed["note"]) or case
            created.append({**case, "_seed": seed})

        # Append follow-ups for D3, D4, D5
        for c in created:
            seed = c.get("_seed", {})
            if not seed.get("append_later"):
                continue
            triage_result = triage_for_append(c["source_text"], seed["append_later"])
            updated = append_follow_up_message(c["case_id"], seed["append_later"], triage_result)
            if updated:
                c.update(updated)

        # Simulate broker workflow checks
        friction: list[str] = []
        cases = list_recent_cases(limit=12)

        # 1. Queue scan — can broker choose first?
        action_cases = [x for x in cases if x.get("waiting_on") == "broker" or x.get("urgency") in ("critical", "high")]
        if not action_cases and cases:
            friction.append("Queue: No clear 'action now' cases surfaced; broker may not know what to open first")
        if verbose and action_cases:
            print(f"  Queue: {len(action_cases)} cases need attention now")

        # 2. Reopen — does Resume here / last update appear?
        for c in cases[:3]:
            has_note = bool(c.get("case_notes"))
            has_activity = bool(c.get("case_activity"))
            if not has_note and not has_activity:
                friction.append(f"Reopen: Case {c.get('case_id', '?')[:12]} has no note/activity for Resume here")
            if c.get("case_activity", [{}])[0].get("activity_type") == "follow_up_added":
                if "Customer follow-up added" not in str(c.get("case_activity", [{}])[0].get("message", "")):
                    friction.append("Append: activity message should mention Customer follow-up added")

        # 3. Append — does triage refresh correctly?
        appended = [c for c in cases if any(a.get("activity_type") == "follow_up_added" for a in c.get("case_activity") or [])]
        for c in appended:
            if not c.get("broker_next_step"):
                friction.append("Append: broker_next_step missing after append")
            if not c.get("updated_at"):
                friction.append("Append: updated_at should be set")

        # 4. Due-state — overdue / due today visible?
        overdue = [c for c in cases if c.get("next_contact_by") and (c.get("next_contact_by", "") < iso_date(0))]
        if overdue and verbose:
            print(f"  Due-state: {len(overdue)} overdue cases")

        return len(friction), len(DAILY_USE_SEEDS) + 3, friction
    finally:
        if orig_path:
            os.environ["UNIFIED_INTAKE_CASES_PATH"] = orig_path
        else:
            os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    friction_count, total, friction = run_daily_use_simulation(verbose)
    passed = friction_count == 0
    print(f"\nDaily-use simulation: {'PASS' if passed else 'FRICTION'}")
    print(f"  Cases: {len(DAILY_USE_SEEDS)} seeded, 3 appended")
    if friction:
        print("  Friction notes:")
        for f in friction:
            print(f"    - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
