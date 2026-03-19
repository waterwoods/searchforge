#!/usr/bin/env python3
"""
Answer Alignment Audit — Targeted example runner

Runs the sprint's targeted examples and prints:
- What the user asked
- What the system answered
- Answer alignment classification
- Failure mode hints

Usage:
  PYTHONPATH=. python3 scripts/audit_answer_alignment.py
  PYTHONPATH=. python3 scripts/audit_answer_alignment.py --verbose
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_message, triage_conversation


# Sprint's targeted examples: (input, expected_direct_answer?, category_hint)
TARGETED_EXAMPLES = [
    # A. Direct answer expected
    ("这个英文 notice 说 payment failed，我现在怎么办？", True, "payment_failed_what_to_do"),
    ("宝马x5，多少钱？", True, "add_car_price"),
    ("刚撞了，对方跑了，我现在先干嘛？", True, "claim_first_step"),
    ("我上周已经发过了，怎么还在追材料？", True, "already_sent_chase"),
    # B. Mixed ask
    ("payment failed 怎么办，另外 dec page 我上周发过了", True, "mixed_payment_and_doc"),
    ("我刚买了车，怎么保？大概要多少钱？", True, "mixed_add_car"),
    # C. Clarification follow-up (multi-turn)
    ("garaging proof 是什么意思？要发什么？", True, "document_clarification"),
    ("这些够了吗？", True, "enough_check"),
    ("我其实已经付了", True, "correction_already_paid"),
]


def run_single_turn(text: str) -> dict:
    return triage_message(text)


def run_multi_turn_example(turns: list[tuple[str, str]]) -> list[dict]:
    """turns = [(customer, expected_system_reply_hint), ...]"""
    results = []
    conversation_turns = []
    for cust_text, _ in turns:
        result = triage_conversation(cust_text, conversation_turns)
        results.append(result)
        conversation_turns.append({"role": "customer", "text": cust_text})
        conversation_turns.append({"role": "system", "text": result.get("client_reply_draft", "")})
    return results


def classify_alignment(user_ask: str, draft: str, expected_direct: bool) -> str:
    """Heuristic: answered_well | partially_answered | mostly_missed | wrong_direction"""
    draft_lower = (draft or "").lower()
    # Anti-patterns
    if "请提供更多信息" in draft or "please provide more context" in draft_lower:
        return "mostly_missed"
    if "这段内容还不够完整" in draft:
        return "mostly_missed"
    if "thank you for reaching out" in draft_lower or "feel free to ask" in draft_lower:
        return "mostly_missed"
    # Direct answer markers
    has_urgency = any(m in draft for m in ["今天", "尽快", "urgent", "today", "最关键"])
    has_what_to_do = any(m in draft for m in ["发我", "发你", "send", "把", "发"])
    has_explanation = any(m in draft for m in ["什么意思", "是", "证明", "proof", "帮你看"])
    has_ack = any(m in draft for m in ["好的", "Got it", "可以"])
    if expected_direct and (has_urgency or has_what_to_do or has_explanation or has_ack):
        if has_urgency or has_what_to_do:
            return "answered_well"
        return "partially_answered"
    if expected_direct and not (has_urgency or has_what_to_do or has_explanation):
        return "mostly_missed"
    return "partially_answered"


def main() -> int:
    ap = argparse.ArgumentParser(description="Answer Alignment Audit")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    print("=" * 60)
    print("Answer Alignment Audit — Targeted Examples")
    print("=" * 60)

    for text, expected_direct, hint in TARGETED_EXAMPLES:
        result = run_single_turn(text)
        draft = result.get("client_reply_draft", "")
        cat = result.get("issue_category", "")
        alignment = classify_alignment(text, draft, expected_direct)
        print(f"\n--- {hint} ---")
        print(f"User asked: {text[:80]}...")
        print(f"Category: {cat}")
        print(f"Draft: {draft[:120]}...")
        print(f"Alignment: {alignment}")
        if args.verbose:
            print(f"broker_next_step: {result.get('broker_next_step', '')[:80]}...")

    # Multi-turn: SIM1 Turn 3 (clarification)
    print("\n" + "=" * 60)
    print("Multi-turn: SIM1 Turn 3 — 其实付了，最要紧做什么")
    print("=" * 60)
    sim1_turns = [
        ("这个英文 notice 说 payment failed，我现在怎么办？", ""),
        ("我发了截图在微信", ""),
        ("其实已经付了，但是账单上还显示due，是不是搞错了？那我现在最要紧做什么？", ""),
    ]
    conv = []
    for i, (cust, _) in enumerate(sim1_turns):
        r = triage_conversation(cust, conv)
        conv.append({"role": "customer", "text": cust})
        conv.append({"role": "system", "text": r.get("client_reply_draft", "")})
        print(f"\nTurn {i+1} customer: {cust[:60]}...")
        print(f"Turn {i+1} draft: {r.get('client_reply_draft', '')[:100]}...")
        print(f"handoff_ready: {r.get('handoff_ready')}, follow_up_type: {r.get('follow_up_type')}")

    # SIM2 Turn 3: garaging proof 是什么意思
    print("\n" + "=" * 60)
    print("Multi-turn: SIM2 Turn 3 — garaging proof 是什么意思")
    print("=" * 60)
    sim2_turns = [
        ("UW follow up - need dec page + garaging proof. 上周发过了", ""),
        ("declaration page 他又发了一次，garaging proof 还没弄", ""),
        ("garaging proof 是什么意思？要发什么？", ""),
    ]
    conv2 = []
    for i, (cust, _) in enumerate(sim2_turns):
        r = triage_conversation(cust, conv2)
        conv2.append({"role": "customer", "text": cust})
        conv2.append({"role": "system", "text": r.get("client_reply_draft", "")})
        print(f"\nTurn {i+1} customer: {cust[:60]}...")
        print(f"Turn {i+1} draft: {r.get('client_reply_draft', '')[:120]}...")
        print(f"handoff_ready: {r.get('handoff_ready')}, follow_up_type: {r.get('follow_up_type')}")

    print("\n" + "=" * 60)
    print("Audit complete.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
