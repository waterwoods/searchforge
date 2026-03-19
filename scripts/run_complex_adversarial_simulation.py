#!/usr/bin/env python3
"""
Run complex adversarial simulations: mixed-intent and long-context / memory-shift.

Usage:
  PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py
  PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py --verbose
  PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py --pack mixed_intent
  PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py --pack long_context

Output: Per-scenario category, draft preview, pass/weak judgment, and failure classification.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_message, triage_conversation

MIXED_INTENT_PATH = Path(__file__).resolve().parent.parent / "configs" / "mixed_intent_scenarios.json"
LONG_CONTEXT_PATH = Path(__file__).resolve().parent.parent / "configs" / "long_context_memory_shift_simulations.json"

# Flow expectations for mixed-intent: at least primary intent should be recognized
MIXED_INTENT_EXPECTATIONS = {
    "add_car": {
        "expected_categories": ["customer_question"],
        "draft_contains_any": ["报价", "quote", "VIN", "车型", "year", "model", "发我", "send", "garaging"],
        "anti_patterns": ["这段内容还不够完整", "please provide more context"],
    },
    "renewal_premium": {
        "expected_categories": ["customer_question", "payment_lapse_expiration", "missing_document"],
        "draft_contains_any": ["保费", "premium", "policy", "bill", "账单", "付款", "发我", "send", "核对"],
        "anti_patterns": ["这段内容还不够完整", "please provide more context"],
    },
    "claim_intake": {
        "expected_categories": ["customer_question"],
        "draft_contains_any": ["事故", "accident", "照片", "photos", "发我", "send", "报案"],
        "anti_patterns": ["这段内容还不够完整", "please provide more context"],
    },
    "notice_payment": {
        "expected_categories": ["customer_question", "payment_lapse_expiration", "cancellation_warning"],
        "draft_contains_any": ["付款", "payment", "通知", "notice", "发我", "send", "今天"],
        "anti_patterns": ["这段内容还不够完整", "please provide more context"],
    },
    "document_chase": {
        "expected_categories": ["customer_question", "missing_document"],
        "draft_contains_any": ["发我", "核对", "declaration", "garaging", "驾照", "send", "报价"],
        "anti_patterns": ["这段内容还不够完整", "please provide more context"],
    },
}


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _draft_contains_expected(draft: str, phrases: list[str]) -> bool:
    if not draft or not phrases:
        return False
    lowered = draft.lower()
    for phrase in phrases:
        if any("\u4e00" <= ch <= "\u9fff" for ch in phrase):
            if phrase in draft:
                return True
        elif phrase.lower() in lowered:
            return True
    return False


def _draft_has_anti_pattern(draft: str, patterns: list[str]) -> bool:
    if not draft:
        return False
    lowered = draft.lower()
    return any(p in draft or p.lower() in lowered for p in patterns)


def run_mixed_intent_scenario(scenario: dict, flow_id: str, verbose: bool) -> dict:
    text = scenario.get("text", "")
    result = triage_message(text)
    cat = (result.get("issue_category") or "").strip().lower()
    draft = result.get("client_reply_draft") or ""
    expectations = MIXED_INTENT_EXPECTATIONS.get(flow_id, {})

    errors = []
    exp_cats = expectations.get("expected_categories", [])
    if exp_cats and cat not in exp_cats:
        errors.append(f"category: got '{cat}' expected one of {exp_cats}")

    draft_phrases = expectations.get("draft_contains_any", [])
    if draft_phrases and not _draft_contains_expected(draft, draft_phrases):
        errors.append(f"draft missing expected phrase (one of {draft_phrases[:4]}...)")

    if _draft_has_anti_pattern(draft, expectations.get("anti_patterns", [])):
        errors.append("generic fallback / anti-pattern")

    # Check if secondary intent was addressed (weaker check)
    secondary = scenario.get("secondary_intent", "")
    secondary_lost = False
    if secondary and "document" in secondary:
        doc_addressed = any(
            m in draft for m in ["garaging", "declaration", "核对", "材料", "发过", "check on my side"]
        )
        if (("garaging" in text.lower() or "dec page" in text.lower()) and not doc_addressed):
            secondary_lost = True
    if secondary_lost:
        errors.append("secondary intent (document) not addressed")

    classification = "strong" if not errors else "weak"
    return {
        "id": scenario.get("id", "?"),
        "flow": flow_id,
        "text": text[:80] + ("..." if len(text) > 80 else ""),
        "style": scenario.get("style", ""),
        "primary_intent": scenario.get("primary_intent", ""),
        "secondary_intent": secondary,
        "category": cat,
        "urgency": result.get("urgency"),
        "draft_preview": draft[:140] + ("..." if len(draft) > 140 else ""),
        "errors": errors,
        "classification": classification,
    }


def run_long_context_simulation(sim: dict, verbose: bool) -> dict:
    sim_id = sim.get("id", "?")
    turns = sim.get("turns", [])
    customer_turns = [t for t in turns if (t.get("role") or "").strip().lower() == "customer"]

    results = {
        "id": sim_id,
        "category": sim.get("category", ""),
        "name": sim.get("name", ""),
        "turn_results": [],
        "system_replies": [],
        "handoff_ready_at_turn": None,
        "final_category": None,
        "final_broker_next_step": None,
        "conversation_summary": None,
        "classification": "unknown",
        "notes": [],
    }

    conversation_turns: list[dict[str, str]] = []

    for i, cust_turn in enumerate(customer_turns):
        text = (cust_turn.get("text") or "").strip()
        if not text:
            continue

        result = triage_conversation(text, conversation_turns)
        sys_reply = result.get("client_reply_draft", "")
        handoff = result.get("handoff_ready", False)

        results["turn_results"].append({
            "turn": i + 1,
            "customer_text": text[:80] + ("..." if len(text) > 80 else ""),
            "system_reply": sys_reply[:120] + ("..." if len(sys_reply) > 120 else ""),
            "handoff_ready": handoff,
            "category": result.get("issue_category"),
        })
        results["system_replies"].append(sys_reply)

        if handoff and results["handoff_ready_at_turn"] is None:
            results["handoff_ready_at_turn"] = i + 1
            results["final_category"] = result.get("issue_category")
            results["final_broker_next_step"] = result.get("broker_next_step")
            results["conversation_summary"] = result.get("conversation_summary")

        conversation_turns.append({"role": "customer", "text": text})
        conversation_turns.append({"role": "system", "text": sys_reply})

    # Classify: did we preserve context? did we hand off reasonably?
    expected = sim.get("expected_handoff_after_turn")
    actual = results.get("handoff_ready_at_turn")
    if expected and actual and actual != expected:
        results["notes"].append(f"Handoff at turn {actual}, expected {expected}")

    # Check if first reply was generic for clear intent
    first_reply = (results.get("system_replies") or [""])[0] if results.get("system_replies") else ""
    if "please provide more context" in first_reply.lower() or "这段内容还不够完整" in first_reply:
        results["notes"].append("First reply too generic for clear intent")

    # Check if summary preserves correction / "already sent" context (only when we have a summary)
    summary = results.get("conversation_summary") or ""
    customer_joined = " ".join(cust.get("text", "") for cust in customer_turns)
    if summary:
        if "又发" in customer_joined and "resent" not in summary.lower() and "sent" not in summary.lower():
            results["notes"].append("Summary may not preserve 'already sent' context")
        # Correction: "不是这个", "不是 payment", "不是续保" (exclude 是不是)
        has_correction = any(
            p in customer_joined for p in ["不是这个", "不是 payment", "不是续保", "不是 payment failed"]
        )
        if has_correction and "correct" not in summary.lower() and "clarified" not in summary.lower():
            results["notes"].append("Summary may not preserve correction")

    if not results["notes"]:
        results["classification"] = "strong"
    elif len(results["notes"]) <= 2:
        results["classification"] = "acceptable_with_friction"
    else:
        results["classification"] = "weak"

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run complex adversarial simulations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full output")
    parser.add_argument("--pack", type=str, choices=["mixed_intent", "long_context", "all"], default="all")
    args = parser.parse_args()

    total_strong = 0
    total_weak = 0
    total_acceptable = 0
    all_results = []

    # Mixed-intent pack
    if args.pack in ("mixed_intent", "all") and MIXED_INTENT_PATH.exists():
        print("=== Mixed-Intent Pack ===\n", flush=True)
        data = json.loads(MIXED_INTENT_PATH.read_text(encoding="utf-8"))
        for flow in data.get("flows", []):
            flow_id = flow.get("id", "?")
            flow_name = flow.get("name", "")
            for s in flow.get("scenarios", []):
                r = run_mixed_intent_scenario(s, flow_id, args.verbose)
                all_results.append(("mixed", r))
                if r["classification"] == "strong":
                    total_strong += 1
                else:
                    total_weak += 1
                status = "PASS" if r["classification"] == "strong" else "WEAK"
                print(f"[{status}] {r['id']} {flow_id}: {r['text'][:50]}...")
                if r["errors"]:
                    for e in r["errors"]:
                        print(f"       └ {e}")
                if args.verbose:
                    print(f"       category={r['category']} draft={r['draft_preview'][:80]}...")
        print()

    # Long-context pack
    if args.pack in ("long_context", "all") and LONG_CONTEXT_PATH.exists():
        print("=== Long-Context / Memory-Shift Pack ===\n", flush=True)
        data = json.loads(LONG_CONTEXT_PATH.read_text(encoding="utf-8"))
        for sim in data.get("simulations", []):
            r = run_long_context_simulation(sim, args.verbose)
            all_results.append(("long_context", r))
            if r["classification"] == "strong":
                total_strong += 1
            elif r["classification"] == "acceptable_with_friction":
                total_acceptable += 1
            else:
                total_weak += 1
            status = "PASS" if r["classification"] == "strong" else "FRICTION" if r["classification"] == "acceptable_with_friction" else "WEAK"
            print(f"[{status}] {r['id']} {r.get('name', '')} ({r.get('category', '')})")
            if r.get("notes"):
                for n in r["notes"]:
                    print(f"       └ {n}")
            if args.verbose:
                for tr in r.get("turn_results", []):
                    print(f"       Turn {tr['turn']}: {tr['customer_text']} -> handoff={tr['handoff_ready']}")
        print()

    total = total_strong + total_acceptable + total_weak
    print("---")
    print(f"Strong: {total_strong} | Acceptable: {total_acceptable} | Weak: {total_weak} | Total: {total}")
    return 0 if total_weak == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
