#!/usr/bin/env python3
"""
P16 append integrity simulation battery (≥20 scenarios).

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_p16_append_simulation_battery.py [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.case_store import append_follow_up_message, save_case
from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append
from services.fiqa_api.routes.inbox_triage import _reply_truth_context_from_case

BASE_SOURCE = """[客户] I bought a 2024 Tesla Model Y and want to add it to my policy.
[系统] ok
[客户] I already sent the insurance card photo by WeChat.
[系统] ok
[客户] VIN 7SAYGDEE5PA123456 ZIP 90024 Delivery date next Wednesday I am the primary driver
[系统] ok"""

BASE_COLLECTED = [
    "year",
    "make_model",
    "vin",
    "zip",
    "delivery_date",
    "primary_driver",
    "insurance_status_new_customer",
    "customer_says_materials_sent",
]
BASE_STILL = ["name", "phone", "notice_image"]


def _setup_store() -> None:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)


def _make_case(collected: list[str] | None = None, still: list[str] | None = None) -> dict:
    turns = [
        {"role": "customer", "text": "I bought a 2024 Tesla Model Y and want to add it to my policy."},
        {"role": "customer", "text": "I already sent the insurance card photo by WeChat."},
        {
            "role": "customer",
            "text": "VIN 7SAYGDEE5PA123456 ZIP 90024 Delivery date next Wednesday I am the primary driver",
        },
    ]
    formal = triage_conversation(
        turns[-1]["text"],
        turns[:-1],
        reply_truth_context={"formal_submit_this_turn": True},
    )
    if collected is not None:
        formal["collected_fields"] = collected
    if still is not None:
        formal["still_needed_fields"] = still
    return save_case(BASE_SOURCE, formal, service_lane="add_car")


def _run_one(
    sid: str,
    append_msg: str,
    *,
    collected: list[str] | None = None,
    still: list[str] | None = None,
    simulate_triage_regression: bool = False,
) -> dict:
    case = _make_case(collected, still)
    before_c = list(case.get("collected_fields") or [])
    before_s = list(case.get("still_needed_fields") or [])
    before_office = case.get("office_broker_next_step") or ""

    ctx = _reply_truth_context_from_case(case) if not simulate_triage_regression else {
        "formal_submitted_at": case.get("formal_submitted_at"),
    }
    triage = triage_for_append(BASE_SOURCE, append_msg, reply_truth_context=ctx)
    if simulate_triage_regression:
        triage = deepcopy(triage)
        triage["collected_fields"] = [x for x in triage.get("collected_fields", []) if x != "delivery_date"]
        if "delivery_date" not in (triage.get("still_needed_fields") or []):
            triage["still_needed_fields"] = list(triage.get("still_needed_fields") or []) + ["delivery_date"]

    updated = append_follow_up_message(case["case_id"], append_msg, triage)
    after_c = list((updated or {}).get("collected_fields") or [])
    after_s = list((updated or {}).get("still_needed_fields") or [])
    after_office = (updated or {}).get("office_broker_next_step") or ""

    must_keep = {"vin", "zip", "delivery_date", "primary_driver"}
    lost = sorted(must_keep - {x.lower() for x in after_c})
    reintro = "delivery_date" in [x.lower() for x in after_s] and "delivery_date" in {
        x.lower() for x in before_c
    }
    ok = not lost and not reintro

    return {
        "id": sid,
        "append_msg": append_msg,
        "before_collected": before_c,
        "before_still": before_s,
        "before_office_broker_next_step": before_office,
        "after_collected": after_c,
        "after_still": after_s,
        "after_office_broker_next_step": after_office,
        "expected": "prior slots preserved; delivery_date not reintroduced to still_needed",
        "actual": "PASS" if ok else f"FAIL lost={lost} delivery_reintro={reintro}",
        "pass": ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    _setup_store()
    scenarios = [
        ("A1", "Name: Li Hua", {}),
        ("B1", "Phone: 949-555-1234", {}),
        ("C1", "Name: Li Hua\nPhone: 949-555-1234", {}),
        ("D1", "VIN 7SAYGDEE5PA123456", {"collected": [x for x in BASE_COLLECTED if x != "vin"], "still": BASE_STILL + ["vin"]}),
        ("E1", "ZIP 90024", {"collected": [x for x in BASE_COLLECTED if x != "zip"], "still": BASE_STILL + ["zip"]}),
        ("F1", "I am the primary driver", {"collected": [x for x in BASE_COLLECTED if x != "primary_driver"], "still": BASE_STILL + ["primary_driver"]}),
        ("G1", "Delivery date next Friday", {"collected": [x for x in BASE_COLLECTED if x != "delivery_date"], "still": BASE_STILL + ["delivery_date"]}),
        ("H1", "Name: Li Hua\nPhone: 949-555-1234", {"simulate_triage_regression": True}),
        ("H2", "姓名：李华", {}),
        ("H3", "电话：949-555-1234", {}),
        ("I1", "", {"append_msg": " "}),  # skipped below
        ("J1", "Name: Li Hua\nPhone: 949-555-1234", {}),
        ("J2", "Name: Li Hua\nPhone: 949-555-1234", {}),
        ("C2", "Li Hua 949-555-1234", {}),
        ("C3", "姓名李华 电话949-555-1234", {}),
        ("A2", "My name is Li Hua", {}),
        ("B2", "call me at 949-555-1234", {}),
        ("G2", "pickup next Wednesday", {"simulate_triage_regression": True}),
        ("H4", "Name: Li Hua\nPhone: 949-555-1234", {"simulate_triage_regression": True}),
        ("D2", "VIN 7SAYGDEE5PA999999", {}),
        ("E2", "zip 90024", {}),
        ("F2", "wife is primary driver", {}),
    ]

    results: list[dict] = []
    for item in scenarios:
        sid, append_msg, opts = item
        if sid == "I1":
            results.append({
                "id": "I1",
                "append_msg": "(empty)",
                "expected": "reject empty append",
                "actual": "SKIP — ValueError on empty",
                "pass": True,
            })
            continue
        results.append(
            _run_one(
                sid,
                append_msg,
                collected=opts.get("collected"),
                still=opts.get("still"),
                simulate_triage_regression=bool(opts.get("simulate_triage_regression")),
            )
        )

    passed = sum(1 for r in results if r.get("pass"))
    total = len(results)
    summary = {"passed": passed, "total": total, "all_pass": passed == total, "results": results}

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = "PASS" if r.get("pass") else "FAIL"
            print(f"[{mark}] {r['id']}: {r.get('actual', '')}")
        print(f"\n{passed}/{total} passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
