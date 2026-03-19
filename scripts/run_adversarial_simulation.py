#!/usr/bin/env python3
"""
Run adversarial real-user scenarios against the triage engine.

Usage:
  PYTHONPATH=. python3 scripts/run_adversarial_simulation.py
  PYTHONPATH=. python3 scripts/run_adversarial_simulation.py --verbose
  PYTHONPATH=. python3 scripts/run_adversarial_simulation.py --flow add_car

Output: Per-scenario category, draft preview, and pass/weak judgment.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_message

CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "adversarial_real_user_scenarios.json"

# Flow-specific expectations: category and draft must contain one of these
FLOW_EXPECTATIONS = {
    "add_car": {
        "expected_categories": ["customer_question"],
        "draft_contains_any": ["报价", "quote", "VIN", "车型", "year", "model", "发我", "send"],
        "anti_patterns": ["这段内容还不够完整", "please provide more context"],
    },
    "renewal_premium": {
        "expected_categories": ["customer_question"],
        "draft_contains_any": ["保费", "premium", "policy", "bill", "账单", "发我", "send"],
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
        "draft_contains_any": ["发我", "核对", "declaration", "garaging", "驾照", "send"],
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


def run_scenario(scenario: dict, flow_id: str, verbose: bool) -> dict:
    text = scenario.get("text", "")
    result = triage_message(text)
    cat = (result.get("issue_category") or "").strip().lower()
    draft = result.get("client_reply_draft") or ""
    expectations = FLOW_EXPECTATIONS.get(flow_id, {})

    errors = []
    exp_cats = expectations.get("expected_categories", [])
    if exp_cats and cat not in exp_cats:
        errors.append(f"category: got '{cat}' expected one of {exp_cats}")

    draft_phrases = expectations.get("draft_contains_any", [])
    if draft_phrases and not _draft_contains_expected(draft, draft_phrases):
        errors.append(f"draft missing expected phrase (one of {draft_phrases[:4]}...)")

    if _draft_has_anti_pattern(draft, expectations.get("anti_patterns", [])):
        errors.append("generic fallback / anti-pattern")

    classification = "strong" if not errors else "weak"
    return {
        "id": scenario.get("id", "?"),
        "flow": flow_id,
        "text": text[:70] + ("..." if len(text) > 70 else ""),
        "style": scenario.get("style", ""),
        "category": cat,
        "urgency": result.get("urgency"),
        "draft_preview": draft[:120] + ("..." if len(draft) > 120 else ""),
        "errors": errors,
        "classification": classification,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run adversarial real-user simulation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full output")
    parser.add_argument("--flow", type=str, help="Run only this flow (e.g. add_car)")
    args = parser.parse_args()

    if not CONFIG_PATH.exists():
        print(f"ERROR: Config not found: {CONFIG_PATH}", file=sys.stderr)
        return 1

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    flows = data.get("flows", [])
    if args.flow:
        flows = [f for f in flows if f.get("id") == args.flow]
        if not flows:
            print(f"No flow with id '{args.flow}'")
            return 1

    total_strong = 0
    total_weak = 0
    flow_results = []

    for flow in flows:
        flow_id = flow.get("id", "?")
        flow_name = flow.get("name", "")
        scenarios = flow.get("scenarios", [])
        strong = 0
        weak = 0
        scenario_results = []

        for s in scenarios:
            r = run_scenario(s, flow_id, args.verbose)
            scenario_results.append(r)
            if r["classification"] == "strong":
                strong += 1
                total_strong += 1
            else:
                weak += 1
                total_weak += 1

        flow_results.append({
            "flow": flow_id,
            "name": flow_name,
            "strong": strong,
            "weak": weak,
            "total": len(scenarios),
            "scenarios": scenario_results,
        })

        status = "PASS" if weak == 0 else "GAPS"
        print(f"[{status}] {flow_id} {flow_name}: {strong}/{len(scenarios)} strong")
        for r in scenario_results:
            if r["classification"] == "weak":
                print(f"       └ {r['id']} ({r['style']}): {'; '.join(r['errors'])}")
                if args.verbose:
                    print(f"          text: {r['text']}")
                    print(f"          got: {r['category']} | draft: {r['draft_preview']}")
        print()

    print("---")
    print(f"Total: {total_strong} strong, {total_weak} weak across {sum(f['total'] for f in flow_results)} scenarios")
    return 0 if total_weak == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
