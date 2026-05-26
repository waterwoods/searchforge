#!/usr/bin/env python3
"""
Regression runner for ADD_CAR_HIGH_ROI_EXTRACTION_GUARD_FIX.

Usage:
  LLM_GENERATION_ENABLED=false PYTHONPATH=. python3 scripts/run_add_car_high_roi_regression.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("LLM_GENERATION_ENABLED", "false")

from services.fiqa_api.inbox_triage.triage import (  # noqa: E402
    _derive_follow_up_type,
    triage_conversation,
)

PACK = ROOT / "docs" / "sprints" / "archive" / "add_car_sprints" / "ADD_CAR_HIGH_ROI_EXTRACTION_GUARD_FIX" / "regression_scenarios.json"


def main() -> int:
    if not PACK.exists():
        print(f"ERROR: missing {PACK}", file=sys.stderr)
        return 1
    data = json.loads(PACK.read_text(encoding="utf-8"))
    failed = 0
    passed = 0

    for c in data.get("follow_up_cases", []):
        msg = c.get("message") or ""
        exp = c.get("expected_follow_up_type")
        got = _derive_follow_up_type(msg)
        ok = got == exp
        if ok:
            passed += 1
            print(f"[PASS] {c.get('id')} follow_up_type={got}")
        else:
            failed += 1
            print(f"[FAIL] {c.get('id')} message={msg!r} got={got!r} expected={exp!r}")

    for c in data.get("add_car_field_cases", []):
        conv: list[dict[str, str]] = []
        for pm in c.get("prior_customer_messages") or []:
            conv.append({"role": "customer", "text": pm})
            conv.append({"role": "system", "text": "…"})
        last = (c.get("last_customer_message") or "").strip()
        result = triage_conversation(last, conv)
        collected = list(result.get("collected_fields") or [])
        expect = c.get("expect_collected_contains") or []
        missing = [x for x in expect if x not in collected]
        if not missing:
            passed += 1
            print(f"[PASS] {c.get('id')} {c.get('name')} collected has {expect}")
        else:
            failed += 1
            print(
                f"[FAIL] {c.get('id')} {c.get('name')} missing {missing} "
                f"(got {collected}) follow_up={result.get('follow_up_type')}"
            )

    print(f"\nHigh-ROI regression: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
