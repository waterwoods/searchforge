#!/usr/bin/env python3
"""
Verify speed routing — which turns use fast path vs LLM.

Run with LLM_GENERATION_ENABLED=1 to see actual routing.
Run with LLM_GENERATION_ENABLED=0 to see triage_path=rule (no fast path when LLM disabled).

Usage:
  LLM_GENERATION_ENABLED=1 PYTHONPATH=. python3 scripts/verify_speed_routing.py
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/verify_speed_routing.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_conversation

# Cases: (conversation_turns, last_msg, expect_fast_when_llm_on)
ROUTING_CASES = [
    # Turn 1 lightweight: payment confusion (short, clear) → fast
    ([], "客户问 payment failed 什么意思", True),
    # Turn 1 lightweight: cancellation
    ([], "Notice: Policy will be cancelled in 7 days due to non-payment.", True),
    # Turn 1 lightweight: add-car short
    ([], "我买了台2024宝马X5，zip 90210", True),
    # Turn 1: mixed/unclear → LLM (expect_fast=False)
    ([], "Important - Action Required [generic marketing footer]", False),
    # Turn 2 already_sent: fast
    (
        [{"role": "customer", "text": "payment failed 是不是要停保"}, {"role": "system", "text": "把截图发我"}],
        "我发了截图在微信",
        True,
    ),
    # Turn 2 clarification: fast
    (
        [{"role": "customer", "text": "UW need dec page"}, {"role": "system", "text": "..."}],
        "garaging proof 是什么意思",
        True,
    ),
    # Turn 2 add-car field: fast
    (
        [{"role": "customer", "text": "我买了台宝马X5"}, {"role": "system", "text": "..."}],
        "2024年的，zip 90210，下周提车",
        True,
    ),
    # Turn 2 "这些够了吗": fast (clarification)
    (
        [{"role": "customer", "text": "2024年的"}, {"role": "system", "text": "zip发我"}],
        "90210，下周提车。这些够了吗？",
        True,
    ),
    # Turn 2 correction: fast
    (
        [{"role": "customer", "text": "payment failed"}, {"role": "system", "text": "..."}],
        "我其实已经付了",
        True,
    ),
]


def main() -> int:
    llm_enabled = os.getenv("LLM_GENERATION_ENABLED", "0").lower() in ("1", "true", "yes", "on")
    print(f"LLM_GENERATION_ENABLED={'1' if llm_enabled else '0'}")
    print("=" * 60)

    for i, (conv_turns, last_msg, expect_fast) in enumerate(ROUTING_CASES):
        result = triage_conversation(last_msg, conv_turns)
        path = result.get("triage_path", "?")
        got_fast = path == "fast"

        # When LLM disabled, path is always "rule" — skip expect check
        if not llm_enabled:
            status = "OK"
        else:
            status = "OK" if got_fast == expect_fast else "MISMATCH"

        print(f"[{status}] {i + 1}. last_msg: {last_msg[:55]}{'...' if len(last_msg) > 55 else ''}")
        print(f"       triage_path={path} (expect fast={expect_fast} when LLM on)")
    print("=" * 60)
    print("Done. When LLM=1, Turn 1 lightweight + turn 2+ simple → triage_path=fast.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
