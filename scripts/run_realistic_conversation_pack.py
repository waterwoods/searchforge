#!/usr/bin/env python3
"""
Run realistic conversation simulation pack against the triage engine.

Usage:
  PYTHONPATH=. python3 scripts/run_realistic_conversation_pack.py
  PYTHONPATH=. python3 scripts/run_realistic_conversation_pack.py --verbose
  PYTHONPATH=. python3 scripts/run_realistic_conversation_pack.py --single RC-S1

Output: Per-scenario pass/weak, category, draft preview, and failure reasons.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_message, triage_conversation

CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "realistic_conversation_simulation_pack.json"


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
    if not draft or not patterns:
        return False
    lowered = draft.lower()
    return any(p in draft or p.lower() in lowered for p in patterns)


def run_single_turn(s: dict, verbose: bool) -> dict:
    text = s.get("input", "")
    result = triage_message(text)
    cat = (result.get("issue_category") or "").strip().lower()
    urg = (result.get("urgency") or "").strip().lower()
    draft = result.get("client_reply_draft") or ""

    expected_cat = (s.get("expected_category") or "").strip().lower()
    expected_urg = (s.get("expected_urgency") or "").strip().lower()
    expected_phrases = s.get("expected_draft_contains_any") or []
    anti_patterns = s.get("anti_patterns") or []

    errors = []
    if expected_cat and cat != expected_cat:
        errors.append(f"category: got '{cat}' expected '{expected_cat}'")
    if expected_urg and urg != expected_urg:
        errors.append(f"urgency: got '{urg}' expected '{expected_urg}'")
    if expected_phrases and not _draft_contains_expected(draft, expected_phrases):
        errors.append(f"draft missing expected phrase (one of {expected_phrases[:4]}...)")
    if _draft_has_anti_pattern(draft, anti_patterns):
        errors.append("generic fallback / anti-pattern")

    classification = "strong" if not errors else "weak"
    return {
        "id": s.get("id", "?"),
        "style": s.get("style", ""),
        "text": text[:70] + ("..." if len(text) > 70 else ""),
        "category": cat,
        "urgency": urg,
        "draft_preview": draft[:120] + ("..." if len(draft) > 120 else ""),
        "errors": errors,
        "classification": classification,
        "business_goal": s.get("business_goal", ""),
        "why_matters": s.get("why_matters", ""),
    }


def run_multi_turn(sim: dict, verbose: bool) -> dict:
    sim_id = sim.get("id", "?")
    turns = sim.get("turns", [])
    customer_turns = [t for t in turns if (t.get("role") or "").strip().lower() == "customer"]

    results = {
        "id": sim_id,
        "category": sim.get("category", ""),
        "name": sim.get("name", ""),
        "turn_results": [],
        "handoff_ready_at_turn": None,
        "final_category": None,
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
            "system_reply": sys_reply[:100] + ("..." if len(sys_reply) > 100 else ""),
            "handoff_ready": handoff,
            "category": result.get("issue_category"),
        })

        if handoff and results["handoff_ready_at_turn"] is None:
            results["handoff_ready_at_turn"] = i + 1
            results["final_category"] = result.get("issue_category")
            results["conversation_summary"] = result.get("conversation_summary")

        conversation_turns.append({"role": "customer", "text": text})
        conversation_turns.append({"role": "system", "text": sys_reply})

    expected = sim.get("expected_handoff_after_turn")
    actual = results.get("handoff_ready_at_turn")
    if expected and actual and actual != expected:
        results["notes"].append(f"Handoff at turn {actual}, expected {expected}")

    first_reply = (results["turn_results"][0]["system_reply"] if results["turn_results"] else "") or ""
    if "please provide more context" in first_reply.lower() or "这段内容还不够完整" in first_reply:
        results["notes"].append("First reply too generic for clear intent")

    if not results["notes"]:
        results["classification"] = "strong"
    elif len(results["notes"]) <= 2:
        results["classification"] = "acceptable_with_friction"
    else:
        results["classification"] = "weak"

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run realistic conversation simulation pack")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full output")
    parser.add_argument("--single", type=str, help="Run only scenario with this ID (e.g. RC-S1)")
    args = parser.parse_args()

    if not CONFIG_PATH.exists():
        print(f"ERROR: Config not found: {CONFIG_PATH}", file=sys.stderr)
        return 1

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    single_turn = data.get("single_turn", [])
    multi_turn = data.get("multi_turn", [])

    if args.single:
        single_turn = [s for s in single_turn if s.get("id") == args.single]
        multi_turn = [s for s in multi_turn if s.get("id") == args.single]
        if not single_turn and not multi_turn:
            print(f"No scenario with id '{args.single}'")
            return 1

    total_strong = 0
    total_weak = 0
    total_acceptable = 0
    failures = []

    print("=== Realistic Conversation Pack (Single-Turn) ===\n", flush=True)
    for s in single_turn:
        r = run_single_turn(s, args.verbose)
        if r["classification"] == "strong":
            total_strong += 1
        else:
            total_weak += 1
            failures.append(r)

        status = "PASS" if r["classification"] == "strong" else "WEAK"
        print(f"[{status}] {r['id']} ({r.get('style', '')[:40]}): {r['text'][:50]}...")
        if r["errors"]:
            for e in r["errors"]:
                print(f"       └ {e}")
        if args.verbose:
            print(f"       category={r['category']} draft={r['draft_preview'][:80]}...")
            print(f"       business_goal={r.get('business_goal')} why_matters={r.get('why_matters')}")
    print()

    print("=== Realistic Conversation Pack (Multi-Turn) ===\n", flush=True)
    for sim in multi_turn:
        r = run_multi_turn(sim, args.verbose)
        if r["classification"] == "strong":
            total_strong += 1
        elif r["classification"] == "acceptable_with_friction":
            total_acceptable += 1
        else:
            total_weak += 1
            failures.append(r)

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
    if failures:
        print("\nFailures (for fix-now queue):")
        for f in failures:
            print(f"  {f.get('id')}: {f.get('errors', f.get('notes', []))}")
    return 0 if total_weak == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
