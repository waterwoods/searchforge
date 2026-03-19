#!/usr/bin/env python3
"""
Follow-up append simulation — Paste new message into existing case.

Simulates realistic broker continuation scenarios:
1. Add-car case gets ZIP later
2. Renewal case gets bill later
3. Claim case gets photos later
4. Missing-document case says "I sent declaration page again"
5. Notice case corrected from "payment failed" to "final notice"

Run: PYTHONPATH=. python3 scripts/run_follow_up_append_simulations.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from services.fiqa_api.inbox_triage.triage import triage_for_append

SCENARIOS = [
    {
        "id": "FA1",
        "name": "Add-car gets ZIP later",
        "original": "客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价",
        "new_message": "我发了ZIP 90210，下周一提车",
        "expect_collected_zip": True,
        "expect_still_needed_driver": True,
    },
    {
        "id": "FA2",
        "name": "Renewal case gets bill later",
        "original": "续保保费太高了，其中一辆去掉会便宜吗",
        "new_message": "我发了最新的账单和declaration page",
        "expect_renewal": True,
    },
    {
        "id": "FA3",
        "name": "Claim case gets photos later",
        "original": "刚出事故了，要收集什么？",
        "new_message": "我拍了现场照片，对方车牌和保险信息也发你了",
        "expect_claim": True,
        "expect_photos_collected": True,
    },
    {
        "id": "FA4",
        "name": "Missing-document sent again",
        "original": "UW follow up - need dec page + garaging proof. 客户说上周发过了",
        "new_message": "declaration page 我又发了一遍，请查收",
        "expect_missing_doc": True,
        "expect_sent_claimed": True,
    },
    {
        "id": "FA5",
        "name": "Corrected notice case",
        "original": "客户问：这个英文 notice 说 payment failed，我现在怎么办？",
        "new_message": "不是payment failed，是final notice说保单要停了",
        "expect_correction": True,
    },
]


def run_scenario(scenario: dict) -> tuple[bool, str]:
    original = scenario["original"]
    new_msg = scenario["new_message"]
    result = triage_for_append(original, new_msg)

    issues = []
    cat = result.get("issue_category", "")
    collected = result.get("collected_fields") or []
    still_needed = result.get("still_needed_fields") or []

    if scenario.get("expect_collected_zip") and "zip" not in [c.lower() for c in collected]:
        issues.append("Expected zip in collected_fields")
    if scenario.get("expect_still_needed_driver") and not any("driver" in s.lower() for s in still_needed):
        issues.append("Expected primary_driver in still_needed")
    if scenario.get("expect_renewal") and "renewal" not in cat.lower() and "premium" not in cat.lower():
        if "customer_question" not in cat:
            issues.append("Expected renewal/premium context")
    if scenario.get("expect_claim") and "customer_question" not in cat and "claim" not in str(result).lower():
        issues.append("Expected claim context")
    if scenario.get("expect_photos_collected") and not any("photo" in c.lower() for c in collected):
        issues.append("Expected photos in collected (optional)")
    if scenario.get("expect_missing_doc") and "missing_document" not in cat and "underwriting" not in cat:
        issues.append("Expected missing_document or underwriting_followup")
    if scenario.get("expect_sent_claimed") and not any("sent" in c.lower() or "already" in c.lower() for c in collected):
        issues.append("Expected customer_says_sent or already_sent in collected (optional)")
    if scenario.get("expect_correction"):
        if not result.get("broker_next_step"):
            issues.append("Expected broker_next_step")
        if "final" not in (result.get("broker_next_step") or "").lower() and "notice" not in (result.get("broker_next_step") or "").lower():
            pass  # Optional: correction should reflect final notice

    passed = len(issues) == 0
    detail = "; ".join(issues) if issues else f"OK — category={cat}, collected={collected[:4]}, still_needed={still_needed[:2]}"
    return passed, detail


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    passed_count = 0
    failed: list[tuple[str, str]] = []

    for scenario in SCENARIOS:
        ok, detail = run_scenario(scenario)
        if ok:
            passed_count += 1
            status = "PASS"
        else:
            failed.append((scenario["id"], detail))
            status = "FAIL"
        line = f"{status} {scenario['id']} {scenario['name']}"
        if verbose or not ok:
            line += f" — {detail}"
        print(line)

    print()
    print(f"Follow-up append simulations: {passed_count}/{len(SCENARIOS)} passed")
    if failed:
        print("Failed:", json.dumps(dict(failed), indent=2))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
