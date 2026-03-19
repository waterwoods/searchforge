#!/usr/bin/env python3
"""
Targeted qualitative test for the 3 critical entry scenarios.
Usage: PYTHONPATH=. python3 scripts/test_three_critical_entry_scenarios.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_message, triage_conversation

# Scenario 1 — Payment problem
PAYMENT_INPUTS = [
    "付款有问题",
    "payment failed，现在怎么办？",
    "他说 payment failed，现在怎么办",
    "Payment failed",
    "这个英文 notice 说 payment failed，我现在怎么办？",
]

# Scenario 2 — Quote problem
QUOTE_INPUTS = [
    "我才买了一个2026年的丰田花冠，大约半年的保费是多少？",
    "宝马x5，多少钱",
    "刚提一台X5，报价能看下吗",
    "新车保险多少",
    "I bought a new BMW X5, how much is insurance?",
]

# Scenario 3 — Missing-doc / already-sent
MISSING_DOC_INPUTS = [
    "我上周已经发过了，怎么还在追材料？",
    "UW要dec page，我发过了",
    "发你了",
    "declaration page 我上周就发了，怎么还在追？",
    "客户说dec page发过了，carrier还说要",
    "need declaration page and garaging proof, client says she already sent",
]

def run():
    print("=" * 60)
    print("THREE CRITICAL ENTRY SCENARIOS — Qualitative Test")
    print("=" * 60)

    print("\n### Scenario 1 — Payment problem ###\n")
    for inp in PAYMENT_INPUTS:
        r = triage_message(inp)
        cat = r.get("issue_category", "")
        draft = r.get("client_reply_draft", "")
        print(f"Input: {inp[:60]}...")
        print(f"  Category: {cat}")
        print(f"  Draft: {draft[:120]}...")
        bad = "内容不够完整" in draft or "please provide more context" in draft.lower()
        print(f"  Blocklist check: {'FAIL' if bad else 'OK'}")
        print()

    print("\n### Scenario 2 — Quote problem ###\n")
    for inp in QUOTE_INPUTS:
        r = triage_message(inp)
        cat = r.get("issue_category", "")
        draft = r.get("client_reply_draft", "")
        print(f"Input: {inp[:60]}...")
        print(f"  Category: {cat}")
        print(f"  Draft: {draft[:120]}...")
        bad = "内容不够完整" in draft or "please provide more context" in draft.lower()
        print(f"  Blocklist check: {'FAIL' if bad else 'OK'}")
        print()

    print("\n### Scenario 3 — Missing-doc / already-sent ###\n")
    for inp in MISSING_DOC_INPUTS:
        r = triage_message(inp)
        cat = r.get("issue_category", "")
        draft = r.get("client_reply_draft", "")
        print(f"Input: {inp[:60]}...")
        print(f"  Category: {cat}")
        print(f"  Draft: {draft[:120]}...")
        has_ack = any(m in draft for m in ["发过", "发过了", "sent", "already sent", "您说"])
        print(f"  Acknowledgment check: {'OK' if has_ack or '发' in draft else 'WARN'}")
        print()

    # Multi-turn: MT29 (declaration page 我上周就发了，怎么还在追)
    print("\n### Multi-turn: MT29 (missing-doc frustrated) ###\n")
    t1_text = "declaration page 我上周就发了，怎么还在追？"
    r1 = triage_conversation(t1_text, [])
    turns = [{"role": "customer", "text": t1_text}, {"role": "system", "text": r1.get("client_reply_draft", "")}]
    r2 = triage_conversation("刚又发了一次，你帮我对一下", turns)
    print(f"Turn 1 input: {t1_text}")
    print(f"  Turn 1 draft: {r1.get('client_reply_draft', '')[:120]}...")
    print(f"Turn 2 input: 刚又发了一次，你帮我对一下")
    print(f"  Turn 2 draft: {r2.get('client_reply_draft', '')[:150]}...")
    print(f"  Handoff: {r2.get('handoff_ready')}")
    print()

if __name__ == "__main__":
    run()
