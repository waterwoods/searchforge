#!/usr/bin/env python3
"""
Run expression robustness simulations against the triage engine.

Same-intent variants should produce consistent category, urgency, and draft quality.
Usage:
  PYTHONPATH=. python3 scripts/run_expression_robustness.py
  PYTHONPATH=. python3 scripts/run_expression_robustness.py --verbose
  PYTHONPATH=. python3 scripts/run_expression_robustness.py --intent add_car_quote

Output: Per-variant pass/fail, classification consistency, draft quality.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_message

CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "expression_robustness_cases.json"


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _draft_contains_expected_phrase(draft: str, phrases: list[str]) -> bool:
    if not draft or not phrases:
        return False
    lowered = (draft or "").lower()
    for phrase in phrases:
        if any("\u4e00" <= ch <= "\u9fff" for ch in phrase):
            if phrase in draft:
                return True
        elif phrase.lower() in lowered:
            return True
    return False


def run_variant(variant: dict, intent: dict, verbose: bool) -> dict:
    """Run one variant and return result with classification."""
    text = variant.get("text", "")
    result = triage_message(text)
    got_cat = (result.get("issue_category") or "").strip().lower()
    expected_cat = (intent.get("expected_category") or "customer_question").strip().lower()
    expected_phrases = intent.get("expected_draft_contains_any") or []
    draft = result.get("client_reply_draft") or ""

    errors = []
    if got_cat != expected_cat:
        errors.append(f"category: got '{got_cat}' expected '{expected_cat}'")
    if expected_phrases and not _draft_contains_expected_phrase(draft, expected_phrases):
        errors.append(f"draft missing expected phrase (one of {expected_phrases})")

    # Anti-pattern: generic fallback for clear intent
    if "please provide more context" in draft.lower() or "这段内容还不够完整" in draft:
        if intent.get("id") in ("add_car_quote", "payment_failed_cancellation_risk", "english_notice_confusion"):
            errors.append("generic fallback for clear intent")

    classification = "strong" if not errors else "weak"
    return {
        "variant_id": variant.get("id", "?"),
        "text": text[:80] + ("..." if len(text) > 80 else ""),
        "style": variant.get("style", ""),
        "got_category": got_cat,
        "expected_category": expected_cat,
        "draft_preview": draft[:100] + ("..." if len(draft) > 100 else ""),
        "errors": errors,
        "classification": classification,
        "result": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run expression robustness simulations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full output")
    parser.add_argument("--intent", type=str, help="Run only this intent (e.g. add_car_quote)")
    args = parser.parse_args()

    if not CONFIG_PATH.exists():
        print(f"ERROR: Config not found: {CONFIG_PATH}", file=sys.stderr)
        return 1

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    intents = data.get("intents", [])
    if args.intent:
        intents = [i for i in intents if i.get("id") == args.intent]
        if not intents:
            print(f"No intent with id '{args.intent}'")
            return 1

    total_strong = 0
    total_weak = 0
    intent_results = []

    for intent in intents:
        intent_id = intent.get("id", "?")
        intent_name = intent.get("name", "")
        variants = intent.get("variants", [])
        strong = 0
        weak = 0
        variant_results = []

        for v in variants:
            r = run_variant(v, intent, verbose=args.verbose)
            variant_results.append(r)
            if r["classification"] == "strong":
                strong += 1
                total_strong += 1
            else:
                weak += 1
                total_weak += 1

        intent_results.append({
            "intent": intent_id,
            "name": intent_name,
            "strong": strong,
            "weak": weak,
            "total": len(variants),
            "variants": variant_results,
        })

        status = "PASS" if weak == 0 else "GAPS"
        print(f"[{status}] {intent_id} {intent_name}: {strong}/{len(variants)} strong")
        for r in variant_results:
            if r["classification"] == "weak":
                print(f"       └ {r['variant_id']} ({r['style']}): {'; '.join(r['errors'])}")
                if args.verbose:
                    print(f"          text: {r['text']}")
                    print(f"          got: {r['got_category']} | draft: {r['draft_preview']}")
        print()

    print("---")
    print(f"Total: {total_strong} strong, {total_weak} weak across {sum(len(i['variants']) for i in intent_results)} variants")
    return 0 if total_weak == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
