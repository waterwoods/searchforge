#!/usr/bin/env python3
"""
State / Field Accuracy Audit — Sprint helper
Runs targeted scenarios to check follow_up_type, collected_fields, still_needed_fields.
Usage: LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_message

# Audit cases: (turns, last_msg, expected_follow_up_type, expected_collected_contains, expected_still_needed_contains)
AUDIT_CASES = [
    # 1. Cancellation / payment risk
    {
        "id": "C1",
        "flow": "cancellation",
        "turns": [
            {"role": "customer", "text": "payment failed 是不是要停保"},
            {"role": "system", "text": "把最新通知或付款截图发我"},
            {"role": "customer", "text": "我昨天付了，截图发你"},
        ],
        "expected_follow_up": "already_sent",
        "expected_collected": [],  # No cancellation structured fields yet
        "note": "Payment risk T3: customer says sent screenshot",
    },
    {
        "id": "C2",
        "flow": "cancellation",
        "turns": [
            {"role": "customer", "text": "客户问 payment failed 什么意思"},
            {"role": "system", "text": "..."},
            {"role": "customer", "text": "我昨天已经换了新卡，需要再发什么给你吗"},
        ],
        "expected_follow_up": "clarification_question",  # "what to send" not "already sent"
        "expected_collected": [],
        "note": "MT6: 'need to send what?' should be clarification, NOT already_sent",
    },
    # 2. Missing document
    {
        "id": "M1",
        "flow": "missing_document",
        "turns": [
            {"role": "customer", "text": "UW need dec page + garaging proof. 客户说上周发过了"},
            {"role": "system", "text": "..."},
            {"role": "customer", "text": "declaration page 发你了，garaging 是什么意思"},
        ],
        "expected_follow_up": "clarification_question",
        "expected_collected": ["requested_garaging_proof", "customer_says_sent_declaration_page"],  # no customer_says_sent_garaging (clarification)
        "note": "SIM2: dec sent + garaging clarification",
    },
    {
        "id": "M2",
        "flow": "missing_document",
        "turns": [
            {"role": "customer", "text": "他们要我补 declaration page 和 garaging proof"},
            {"role": "system", "text": "..."},
            {"role": "customer", "text": "declaration page 发你了，garaging 还没弄"},
        ],
        "expected_follow_up": "already_sent",  # "发你了" = I sent; 好的收到了 is correct
        "expected_collected": ["requested_declaration_page", "requested_garaging_proof", "customer_says_sent_declaration_page"],
        "expected_still_needed": ["garaging_proof"],
        "note": "Dec sent, garaging not yet",
    },
    # 3. Add-car
    {
        "id": "A1",
        "flow": "add_car",
        "turns": [
            {"role": "customer", "text": "我买了台宝马X5，想问下保费多少钱"},
            {"role": "system", "text": "..."},
            {"role": "customer", "text": "2024年的，zip 90210，下周提车"},
        ],
        "expected_follow_up": "new_info",
        "expected_collected": ["year", "make_model", "zip", "delivery_date"],
        "note": "Add-car T2: year, zip, delivery",
    },
    # 4. Claim
    {
        "id": "CL1",
        "flow": "claim",
        "turns": [
            {"role": "customer", "text": "刚出事故了，要收集什么？"},
            {"role": "system", "text": "..."},
            {"role": "customer", "text": "拍了照片，对方保险也记了，发你微信"},
        ],
        "expected_follow_up": "already_sent",
        "expected_collected": ["accident_reported", "photos", "other_driver_info"],
        "note": "Claim T2: photos + other driver sent",
    },
    # 5. Renewal
    {
        "id": "R1",
        "flow": "renewal",
        "turns": [
            {"role": "customer", "text": "保费太高了，能不能便宜一点"},
            {"role": "system", "text": "..."},
            {"role": "customer", "text": "续保通知和账单我发你微信了"},
        ],
        "expected_follow_up": "already_sent",
        "expected_collected": ["premium_concern", "policy_bill_sent"],
        "note": "Renewal T2: bill sent",
    },
    # 6. Package 2.0: broker_next_step verify/confirm when client says sent
    {
        "id": "P2-M1",
        "flow": "missing_document",
        "turns": [
            {"role": "customer", "text": "dec page 和 garaging 要补，客户说上周发了"},
            {"role": "system", "text": "..."},
            {"role": "customer", "text": "dec page 又发了一次，garaging 也发了"},
        ],
        "expected_follow_up": "already_sent",
        "expected_broker_next_step_contains": ["verify", "carrier"],
        "note": "Package 2.0: broker_next_step must tell broker to verify with carrier",
    },
    {
        "id": "P2-C1",
        "flow": "cancellation",
        "turns": [
            {"role": "customer", "text": "payment failed 是不是今天要处理"},
            {"role": "system", "text": "..."},
            {"role": "customer", "text": "我昨天付了，截图发你"},
        ],
        "expected_follow_up": "already_sent",
        "expected_broker_next_step_contains": ["confirm", "carrier"],
        "note": "Package 2.0: broker_next_step must tell broker to confirm payment with carrier",
    },
]


def run_audit():
    print("State / Field Accuracy Audit\n" + "=" * 50)
    passed = 0
    failed = 0
    for c in AUDIT_CASES:
        turns = c["turns"]
        last_msg = turns[-1]["text"] if turns else ""
        conv = [t for t in turns[:-1] if t["role"] == "customer"]
        # Build conversation_turns (exclude last customer - triage_conversation adds it)
        conversation_turns = []
        for t in turns[:-1]:
            conversation_turns.append({"role": t["role"], "text": t["text"]})

        result = triage_conversation(last_msg, conversation_turns)
        got_follow_up = result.get("follow_up_type", "")
        got_collected = result.get("collected_fields") or []
        got_still_needed = result.get("still_needed_fields") or []

        exp_follow = c.get("expected_follow_up")
        exp_collected = c.get("expected_collected") or []
        exp_still = c.get("expected_still_needed") or []
        exp_broker_contains = c.get("expected_broker_next_step_contains") or []

        errs = []
        if exp_follow and got_follow_up != exp_follow:
            errs.append(f"follow_up_type: got '{got_follow_up}' expected '{exp_follow}'")
        for req in exp_collected:
            if req not in got_collected:
                errs.append(f"collected missing '{req}' (got {got_collected})")
        for req in exp_still:
            if req not in got_still_needed:
                errs.append(f"still_needed missing '{req}' (got {got_still_needed})")
        broker_next = (result.get("broker_next_step") or "").lower()
        for req in exp_broker_contains:
            if req.lower() not in broker_next:
                errs.append(f"broker_next_step must contain '{req}' (got: {broker_next[:80]}...)")

        ok = len(errs) == 0
        if ok:
            passed += 1
            print(f"[PASS] {c['id']} {c['flow']}: follow_up={got_follow_up} collected={got_collected[:5]}...")
        else:
            failed += 1
            print(f"[FAIL] {c['id']} {c['flow']}: {errs}")
            print(f"       Note: {c.get('note','')}")

    print(f"\nResult: {passed}/{passed+failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_audit())
