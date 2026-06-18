#!/usr/bin/env python3
"""
P16 Office Workbench visibility simulation (≥20 queue scenarios).

Mirrors ui/src/features/intake/utils/intakePure.ts workbench scoring after P16 fix.

Usage:
  PYTHONPATH=. python3 scripts/run_p16_office_visibility_simulation.py [--json]
"""
from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent

RECENT_FORMAL_SUBMISSION_VISIBILITY_BOOST = 165
FOUNDER_DEMO_SEED_WORKBENCH_PENALTY = 300

FOUNDER_DEMO_SEED_TEXTS = [
    "Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？",
    "UW follow up - need dec page + garaging proof. 客户说上周发过了",
    "客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价",
    "客户说这个月保费太高了，能不能看看怎么降一点",
    "DMV信说要 SR-22 proof 才能 clear suspension，这个要带什么？",
    "AutoPay failed again, please update card to avoid interruption in coverage",
    "客户卖掉旧车了，想把2014 Honda Accord从保单拿掉",
    "客户问：这个英文 notice 说 payment failed，我现在怎么办？",
    "客户发来carrier email，说 declaration page missing，他问这个什么意思",
    "保险公司说我的保单7天后要cancel",
    "刚出事故了，要收集什么？",
    "续保保费太高了，其中一辆去掉会便宜吗",
]


def _norm_source(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def _iso_recent(hours_ago: float = 1.0) -> str:
    t = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return t.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _iso_old() -> str:
    t = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return t.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _follow_up_due_tag(next_contact_by: str | None) -> str | None:
    raw = (next_contact_by or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return None
    due = datetime.strptime(raw, "%Y-%m-%d").date()
    today = datetime.now().date()
    if due < today:
        return "overdue"
    if due == today:
        return "due_today"
    return None


def _attention(case: dict[str, Any]) -> tuple[str, str]:
    due = _follow_up_due_tag(case.get("next_contact_by"))
    if case.get("case_status") == "done":
        return "tracking", "done"
    if due == "overdue":
        return "action", "overdue"
    if due == "due_today":
        return "action", "due_today"
    if case.get("waiting_on") == "broker":
        return "action", "wait_broker"
    if case.get("manual_followup_needed") and case.get("urgency") in ("critical", "high"):
        return "action", "urgent_manual"
    if case.get("manual_followup_needed"):
        return "action", "manual_followup"
    if case.get("waiting_on") not in (None, "", "none"):
        return "tracking", "wait_external"
    if case.get("case_status") == "reviewing":
        return "tracking", "reviewing"
    return "tracking", "parked"


def _within_24h(iso: str | None) -> bool:
    if not iso:
        return False
    try:
        t = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return False
    return (datetime.now(timezone.utc) - t).total_seconds() <= 24 * 3600


def _recent_boost(case: dict[str, Any]) -> int:
    if case.get("workbench_test"):
        return 0
    ls = (case.get("lifecycle_status") or "").strip()
    if ls not in ("handed_off", "office_followup"):
        return 0
    if not _within_24h(case.get("formal_submitted_at")):
        return 0
    return RECENT_FORMAL_SUBMISSION_VISIBILITY_BOOST


def _demo_penalty(case: dict[str, Any]) -> int:
    if case.get("workbench_test"):
        return 0
    norm = _norm_source(case.get("source_text") or "")
    if not norm:
        return 0
    for seed in FOUNDER_DEMO_SEED_TEXTS:
        if _norm_source(seed) == norm:
            return FOUNDER_DEMO_SEED_WORKBENCH_PENALTY
    return 0


def workbench_score(case: dict[str, Any]) -> int:
    section, kind = _attention(case)
    base = 100 if section == "action" else 0
    if kind == "overdue":
        base += 70
    elif kind == "due_today":
        base += 60
    elif kind == "wait_broker":
        base += 50
    elif kind == "urgent_manual":
        base += 40
    elif kind == "manual_followup":
        base += 25
    urgency = (case.get("urgency") or "low").lower()
    bonus = {"critical": 20, "high": 15, "medium": 8}.get(urgency, 0)
    done_pen = 100 if case.get("case_status") == "done" else 0
    return base + bonus - done_pen + _recent_boost(case) - _demo_penalty(case)


def order_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        cases,
        key=lambda c: (workbench_score(c), c.get("updated_at") or ""),
        reverse=True,
    )


def _today_iso() -> str:
    return datetime.now().date().isoformat()


def _tomorrow_iso() -> str:
    return (datetime.now().date() + timedelta(days=1)).isoformat()


def build_scenarios() -> list[dict[str, Any]]:
    recent = _iso_recent(0.5)
    old = _iso_old()
    today = _today_iso()
    tomorrow = _tomorrow_iso()
    scenarios: list[dict[str, Any]] = []

    def add(sid: str, case: dict[str, Any], *, updated_hours_ago: float = 0.5):
        c = {"scenario_id": sid, **case}
        c.setdefault("updated_at", _iso_recent(updated_hours_ago))
        scenarios.append({"id": sid, "case": c})

    # 10 add-car cases (recent formal submits should rank near top vs demo noise)
    for i in range(1, 6):
        add(
            f"AC-TESLA-{i}",
            {
                "case_id": f"case_tesla_submit_{i}",
                "source_text": f"[客户] 买了2024 Tesla Model Y 想加保 VIN batch{i}",
                "primary_vehicle_summary": "2024 Tesla Model Y",
                "lifecycle_status": "handed_off",
                "formal_submitted_at": recent,
                "urgency": "medium",
                "waiting_on": "none",
                "case_status": "reviewing",
                "still_needed_fields": ["name", "phone"] if i % 2 else [],
                "issue_category": "customer_question",
            },
            updated_hours_ago=0.5 + i * 0.01,
        )
    for i in range(1, 6):
        add(
            f"AC-HONDA-{i}",
            {
                "case_id": f"case_honda_submit_{i}",
                "source_text": f"[客户] 2025 Honda Civic 加车 邮编91765 batch{i}",
                "primary_vehicle_summary": "2025 Honda Civic",
                "lifecycle_status": "handed_off",
                "formal_submitted_at": recent,
                "urgency": "medium",
                "waiting_on": "none",
                "case_status": "reviewing",
                "still_needed_fields": ["zip"] if i == 1 else [],
            },
            updated_hours_ago=0.6 + i * 0.01,
        )

    # Representative certified case shape — newest among recent add-car submits
    add(
        "AC-CERTIFIED-EA74",
        {
            "case_id": "case_ea74d66fa3ba",
            "source_text": "[客户] 2024 Tesla Model Y 正式提交加车",
            "primary_vehicle_summary": "2024 Tesla Model Y",
            "lifecycle_status": "handed_off",
            "formal_submitted_at": recent,
            "urgency": "medium",
            "waiting_on": "none",
            "case_status": "reviewing",
            "still_needed_fields": ["phone"],
        },
        updated_hours_ago=0.01,
    )

    # 5 cancellation / lapse cases — must stay above fresh add-car when due today + broker wait
    for i, urgency in enumerate(["critical", "high", "high", "medium", "critical"], start=1):
        add(
            f"CANCEL-{i}",
            {
                "case_id": f"case_cancel_{i}",
                "source_text": f"Carrier cancellation notice real case {i}",
                "lifecycle_status": "office_followup",
                "formal_submitted_at": old,
                "urgency": urgency,
                "waiting_on": "broker",
                "next_contact_by": today,
                "case_status": "reviewing",
                "issue_category": "cancellation_warning",
                "manual_followup_needed": True,
            },
        )

    # 5 payment-failed cases
    for i in range(1, 6):
        add(
            f"PAY-FAIL-{i}",
            {
                "case_id": f"case_pay_fail_{i}",
                "source_text": f"AutoPay failed real customer message {i}",
                "lifecycle_status": "handed_off",
                "formal_submitted_at": old,
                "urgency": "high" if i <= 2 else "medium",
                "waiting_on": "broker",
                "next_contact_by": today if i <= 3 else tomorrow,
                "case_status": "reviewing",
                "issue_category": "payment_lapse_expiration",
            },
        )

    # Missing-doc + old formal submit (no boost)
    add(
        "MISSING-DOC",
        {
            "case_id": "case_missing_doc",
            "source_text": "UW need dec page customer says sent last week",
            "lifecycle_status": "handed_off",
            "formal_submitted_at": old,
            "urgency": "medium",
            "waiting_on": "client",
            "next_contact_by": tomorrow,
            "case_status": "waiting_client",
            "issue_category": "missing_document",
        },
    )

    # Founder demo seeds (noise)
    for i, seed in enumerate(FOUNDER_DEMO_SEED_TEXTS[:6], start=1):
        add(
            f"DEMO-SEED-{i}",
            {
                "case_id": f"case_demo_seed_{i}",
                "source_text": seed,
                "lifecycle_status": "handed_off" if i == 3 else "office_followup",
                "formal_submitted_at": old,
                "urgency": "high" if i in (1, 3, 6) else "medium",
                "waiting_on": "broker" if i != 2 else "client",
                "next_contact_by": today if i in (1, 3, 5, 6) else tomorrow,
                "case_status": "reviewing" if i != 2 else "waiting_client",
            },
        )

    return scenarios


def evaluate(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    queue_cases = [deepcopy(s["case"]) for s in scenarios]
    ordered = order_cases(queue_cases)
    rank_by_id = {c["case_id"]: idx + 1 for idx, c in enumerate(ordered)}
    demo_ranks = [
        rank_by_id[c["case_id"]]
        for c in ordered
        if str(c.get("case_id", "")).startswith("case_demo_seed_")
    ]
    best_demo_rank = min(demo_ranks) if demo_ranks else 999
    results: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    for spec in scenarios:
        cid = spec["case"]["case_id"]
        rank = rank_by_id[cid]
        score = workbench_score(spec["case"])
        checks: list[str] = []
        ok = True
        sid = spec["id"]

        # Recent formal add-car: must beat founder demo noise and land on first screen in mixed queue
        ls = spec["case"].get("lifecycle_status")
        if (
            sid.startswith("AC-")
            and _within_24h(spec["case"].get("formal_submitted_at"))
            and ls in ("handed_off", "office_followup")
        ):
            if rank >= best_demo_rank:
                ok = False
                checks.append(f"rank {rank} not above demo noise (best demo rank {best_demo_rank})")
            if sid == "AC-CERTIFIED-EA74" and rank > 8:
                ok = False
                checks.append(f"certified case rank {rank} outside first visible screen (max 8)")

        # Critical/high same-day cancellation stays above fresh add-car
        if sid.startswith("CANCEL-") and spec["case"].get("urgency") in ("critical", "high"):
            ac_best = min(
                rank_by_id[c["case_id"]]
                for c in ordered
                if c["case_id"].startswith("case_tesla_submit_") or c["case_id"] == "case_ea74d66fa3ba"
            )
            if rank > ac_best:
                ok = False
                checks.append(f"urgent cancellation rank {rank} below recent add-car rank {ac_best}")

        # Payment-failed due today + high stays above fresh add-car
        if sid.startswith("PAY-FAIL-") and spec["case"].get("urgency") == "high":
            if spec["case"].get("next_contact_by") == _today_iso():
                ac_best = min(
                    rank_by_id[c["case_id"]]
                    for c in ordered
                    if c["case_id"].startswith("case_tesla_submit_") or c["case_id"] == "case_ea74d66fa3ba"
                )
                if rank > ac_best:
                    ok = False
                    checks.append(f"high payment-fail rank {rank} below recent add-car rank {ac_best}")

        # Demo seeds must stay below all recent formal add-car submits
        if sid.startswith("DEMO-SEED-"):
            ac_best = min(
                rank_by_id[c["case_id"]]
                for c in ordered
                if c["case_id"].startswith("case_tesla_submit_")
                or c["case_id"].startswith("case_honda_submit_")
                or c["case_id"] == "case_ea74d66fa3ba"
            )
            if rank < ac_best:
                ok = False
                checks.append(f"demo seed rank {rank} above recent add-car rank {ac_best}")

        if ok:
            passed += 1
        else:
            failed += 1
        results.append(
            {
                "scenario_id": sid,
                "case_id": cid,
                "rank": rank,
                "score": score,
                "pass": ok,
                "checks": checks,
            }
        )

    total = passed + failed
    rate = (passed / total * 100) if total else 0.0
    certified = rate >= 95.0
    ea_rank = rank_by_id.get("case_ea74d66fa3ba")
    return {
        "total_scenarios": total,
        "passed": passed,
        "failed": failed,
        "pass_rate_pct": round(rate, 2),
        "certified": certified,
        "case_ea74d66fa3ba_rank": ea_rank,
        "top_5_case_ids": [c["case_id"] for c in ordered[:5]],
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate(build_scenarios())
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"P16 Office Visibility Simulation: {report['passed']}/{report['total_scenarios']} passed ({report['pass_rate_pct']}%)")
        print(f"Certified (≥95%): {'YES' if report['certified'] else 'NO'}")
        print(f"case_ea74d66fa3ba rank: {report['case_ea74d66fa3ba_rank']}")
        print(f"Top 5: {', '.join(report['top_5_case_ids'])}")
        if not report["certified"]:
            print("\nFailures:")
            for row in report["results"]:
                if not row["pass"]:
                    print(f"  - {row['scenario_id']}: {', '.join(row['checks'])}")
    out_path = REPO / "docs" / "trial" / ".p16_office_visibility_simulation.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if report["certified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
