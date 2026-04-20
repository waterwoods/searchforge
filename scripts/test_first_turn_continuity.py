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


def test_first_turn_add_car_relative_delivery_not_handoff() -> int:
    """PILOT_CONTRACT_ADD_CAR_V1 §2.4: relative-only pickup (e.g. 下周) does not satisfy delivery_date.

    First turn must not report quote/handoff complete when delivery truth is still relative-only,
    even if year/make/zip are present."""
    text = "客户要加一台2021 Tesla Model Y，90210，下周提车，问今天能不能先出报价"
    result = triage_conversation(text, [])
    ho = result.get("handoff_ready")
    collected = result.get("collected_fields") or []
    if ho is True:
        print("FAIL add-car relative delivery: handoff_ready=True (expected False per pilot contract)")
        return 1
    if "delivery_date" in collected:
        print("FAIL add-car relative delivery: delivery_date collected without absolute calendar date")
        return 1
    if result.get("quote_ready_status") == "quote_ready":
        print("FAIL add-car relative delivery: quote_ready_status=quote_ready with relative-only delivery")
        return 1
    print("PASS add-car relative delivery: no premature handoff / no false delivery_date truth")
    return 0


def test_first_turn_add_car_contract_complete_may_handoff() -> int:
    """First turn may hand off only when pilot quote truth is complete (VIN+zip+delivery+driver)."""
    text = (
        "Add car: VIN is 1HGCM82633A123456, garaging ZIP 90210, pick up 04/25/2026, "
        "I am the primary driver."
    )
    result = triage_conversation(text, [])
    ho = result.get("handoff_ready")
    if ho is not True:
        print(f"FAIL add-car contract-complete EN: handoff_ready={ho} (expected True)")
        return 1
    collected = result.get("collected_fields") or []
    if "vin" not in collected:
        print(f"FAIL add-car contract-complete EN: vin missing from collected_fields: {collected!r}")
        return 1
    print("PASS add-car contract-complete EN: handoff_ready=True with VIN collected")
    return 0


if __name__ == "__main__":
    sys.exit(
        test_first_turn_continuity()
        or test_first_turn_add_car_relative_delivery_not_handoff()
        or test_first_turn_add_car_contract_complete_may_handoff()
    )
