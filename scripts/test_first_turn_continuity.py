#!/usr/bin/env python3
"""
Regression test: First-turn must NOT force handoff_ready (MULTI_TURN_CONTINUITY_GUARDRAIL).

Runs against the triage module directly (no server required).
Usage: PYTHONPATH=. python3 scripts/test_first_turn_continuity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_conversation


def test_first_turn_continuity() -> int:
    """First message with incomplete info must return handoff_ready=False."""
    cases = [
        ("加车", "add-car: vague"),
        ("想加一辆新车", "add-car: vague"),
        ("付款失败了", "payment: no proof"),
        ("还缺什么材料", "missing-doc: vague"),
    ]
    failed = 0
    for text, label in cases:
        result = triage_conversation(text, [])
        ho = result.get("handoff_ready")
        if ho is True:
            print(f"FAIL {label}: handoff_ready=True (expected False for first turn)")
            failed += 1
        else:
            print(f"PASS {label}: handoff_ready={ho}")
    return 0 if failed == 0 else 1


def test_first_turn_full_info_handoff() -> int:
    """Add-car with full info on first turn may hand off (MATURE_INTAKE_SKELETON).
    Requires vehicle + zip + (delivery or driver) per 80% completion spec."""
    text = "客户要加一台2021 Tesla Model Y，90210，下周提车，问今天能不能先出报价"
    result = triage_conversation(text, [])
    ho = result.get("handoff_ready")
    if ho is not True:
        print(f"FAIL add-car full info: handoff_ready={ho} (expected True)")
        return 1
    print("PASS add-car full info: handoff_ready=True")
    return 0


if __name__ == "__main__":
    sys.exit(test_first_turn_continuity() or test_first_turn_full_info_handoff())
