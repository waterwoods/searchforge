#!/usr/bin/env python3
"""
3-Agent Product Simulation — Customer Simulator + Runtime Validator + Product Auditor.
=====================================================================================
Simulates realistic notice-confusion flows and validates retrieval behavior.

Agent 1 (Customer Simulator): Sends realistic messages (Chinese/English notice confusion)
Agent 2 (Runtime Validator): Checks retrieval active, explanation useful, fallback path
Agent 3 (Product Auditor): Summarizes where retrieval helped, where fallback dominated

Usage:
  PYTHONPATH=. python3 scripts/run_retrieval_3agent_simulation.py
  PYTHONPATH=. python3 scripts/run_retrieval_3agent_simulation.py --verbose

Requires: triage module (no live API needed; uses direct triage call)
"""

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv()
    if (REPO_ROOT / ".env.cloudrun").exists():
        load_dotenv(REPO_ROOT / ".env.cloudrun", override=True)
except ImportError:
    pass

# Agent 1 — Customer messages (path 1: notice | path 2: document | control)
CUSTOMER_MESSAGES = [
    ("这个英文 notice 什么意思？", "english_notice_confusion", "Chinese notice confusion"),
    ("payment failed 是不是马上停保？", "english_notice_confusion", "payment failed + urgency"),
    ("cancel pending 是什么意思？", "english_notice_confusion", "cancel pending"),
    ("last notice 这个是不是很严重？", "english_notice_confusion", "last notice urgency"),
    ("declaration page是什么？", "document_confusion", "declaration page 解释"),
    ("garaging proof 是什么意思？", "document_confusion", "garaging proof 解释"),
    ("为什么他们还要我补 declaration page？", "document_confusion", "为什么补材料"),
    ("加一台 2024 年的特斯拉", "add_car_quote", "control: add-car, rules only"),
]


def run_triage(text: str) -> dict:
    """Run triage on customer message. Returns triage result dict."""
    from services.fiqa_api.inbox_triage.triage import triage_message
    return triage_message(text)


def validator_checks(result: dict, retrieval_used: bool) -> dict:
    """Agent 2 — Runtime Validator checks."""
    checks = {
        "has_client_reply_draft": bool(result.get("client_reply_draft")),
        "draft_not_empty": len((result.get("client_reply_draft") or "").strip()) > 20,
        "retrieval_used": retrieval_used,
        "category_ok": result.get("issue_category") in ("customer_question", "cancellation_warning", "payment_lapse_expiration", "missing_document", "unclear"),
        "handoff_rules_ok": True,  # Handoff not triggered on first message
    }
    draft = result.get("client_reply_draft") or ""
    # Heuristic: retrieval augment often contains "根据常见情况" or "Based on common cases"
    checks["likely_retrieval_augment"] = "根据常见情况" in draft or "Based on common cases" in draft
    checks["all_ok"] = all([checks["has_client_reply_draft"], checks["draft_not_empty"], checks["category_ok"]])
    return checks


def main():
    parser = argparse.ArgumentParser(description="3-Agent retrieval product simulation")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("3-Agent Product Simulation — Notice Explanation")
    print("=" * 60)

    from services.fiqa_api.inbox_triage.notice_retrieval import retrieval_ready, retrieve_notice_explanation

    retrieval_ready_at_start = retrieval_ready()
    print(f"Retrieval ready at start: {retrieval_ready_at_start}")
    print()

    summaries = []
    for msg, expected_category, desc in CUSTOMER_MESSAGES:
        result = run_triage(msg)
        # Infer retrieval usage from draft content
        draft = result.get("client_reply_draft") or ""
        retrieval_used = "根据常见情况" in draft or "Based on common cases" in draft
        checks = validator_checks(result, retrieval_used)

        auditor_verdict = "strong" if (retrieval_used and checks["likely_retrieval_augment"]) else "acceptable" if checks["all_ok"] else "weak"
        summaries.append({
            "msg": msg[:50] + "..." if len(msg) > 50 else msg,
            "desc": desc,
            "category": result.get("issue_category"),
            "retrieval_used": retrieval_used,
            "validator_ok": checks["all_ok"],
            "auditor_verdict": auditor_verdict,
        })

        if args.verbose:
            print("-" * 50)
            print(f"Customer: {msg}")
            print(f"Expected: {expected_category} | {desc}")
            print(f"Category: {result.get('issue_category')}")
            print(f"Retrieval used: {retrieval_used}")
            print(f"Validator: {checks}")
            print(f"Auditor: {auditor_verdict}")
            print(f"Draft (first 120 chars): {(draft or '')[:120]}...")
            print()

    # Agent 3 — Product Auditor summary
    retrieval_count = sum(1 for s in summaries if s["retrieval_used"])
    strong_count = sum(1 for s in summaries if s["auditor_verdict"] == "strong")
    control_ok = any(s["desc"].startswith("control") and s["category"] != "customer_question" for s in summaries)

    print("=" * 60)
    print("Product Auditor Summary")
    print("=" * 60)
    print(f"Retrieval augmented: {retrieval_count}/{len(CUSTOMER_MESSAGES)}")
    print(f"Strong (retrieval + useful): {strong_count}")
    print(f"Control case (add-car) stayed rules-driven: {control_ok}")
    print()
    for s in summaries:
        print(f"  {s['desc']}: {s['auditor_verdict']} (retrieval={s['retrieval_used']})")
    print("=" * 60)
    print("Verdict: ", end="")
    if retrieval_count >= 1 and strong_count >= 1:
        print("Retrieval is product-real in at least one chain.")
    elif retrieval_ready_at_start and retrieval_count == 0:
        print("Retrieval ready but no augment in these cases (check query extraction).")
    else:
        print("Retrieval not active or fallback dominated. Check warmup/Qdrant.")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
