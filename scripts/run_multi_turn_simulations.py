#!/usr/bin/env python3
"""
Run multi-turn customer intake simulations against the triage engine.

Usage:
  PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py
  PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py --verbose
  PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py --single MT1

Output: Per-scenario pass/fail, system replies, handoff timing, and classification.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_message, triage_conversation


def load_simulations() -> dict:
    config_path = Path(__file__).resolve().parent.parent / "configs" / "customer_entry_multi_turn_simulations.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def run_single_simulation(sim: dict, verbose: bool = False) -> dict:
    """Run one multi-turn simulation and return results."""
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
        "final_urgency": None,
        "final_broker_next_step": None,
        "final_client_draft": None,
        "conversation_summary": None,
        "classification": "unknown",
        "notes": [],
    }

    conversation_turns: list[dict[str, str]] = []

    for i, cust_turn in enumerate(customer_turns):
        text = (cust_turn.get("text") or "").strip()
        if not text:
            continue

        # Triage with full conversation context
        result = triage_conversation(text, conversation_turns)

        sys_reply = result.get("client_reply_draft", "")
        handoff = result.get("handoff_ready", False)

        results["turn_results"].append({
            "turn": i + 1,
            "customer_text": text[:80] + ("..." if len(text) > 80 else ""),
            "system_reply": sys_reply[:120] + ("..." if len(sys_reply) > 120 else ""),
            "handoff_ready": handoff,
            "category": result.get("issue_category"),
            "urgency": result.get("urgency"),
        })
        results["system_replies"].append(sys_reply)

        if handoff and results["handoff_ready_at_turn"] is None:
            results["handoff_ready_at_turn"] = i + 1
            results["final_category"] = result.get("issue_category")
            results["final_urgency"] = result.get("urgency")
            results["final_broker_next_step"] = result.get("broker_next_step")
            results["final_client_draft"] = result.get("client_reply_draft")
            results["conversation_summary"] = result.get("conversation_summary")

        # Build conversation for next turn
        conversation_turns.append({"role": "customer", "text": text})
        conversation_turns.append({"role": "system", "text": sys_reply})

    # Classify result
    _classify_simulation_result(results, sim)

    return results


def _classify_simulation_result(results: dict, sim: dict) -> None:
    """Set classification: strong, acceptable_with_friction, weak."""
    notes = results.get("notes", [])

    # Check first reply quality
    first_reply = (results.get("system_replies") or [""])[0] if results.get("system_replies") else ""
    first_lower = first_reply.lower()

    # Anti-patterns
    if "please provide more context" in first_lower or "这段内容还不够完整" in first_reply:
        if sim.get("category") in ("add_car_quote", "payment_failed_cancellation_risk", "english_notice_confusion"):
            notes.append("First reply too generic for clear intent")
    if "thank you for reaching out" in first_lower or "feel free to ask" in first_lower:
        notes.append("Robotic/formulaic first reply")

    # Second turn: did system use the new info?
    if len(results.get("system_replies", [])) >= 2:
        second_reply = results["system_replies"][1]
        # After 2nd customer message, we hand off - draft becomes handoff message
        if results.get("handoff_ready_at_turn") == 2:
            # Check if broker_next_step reflects collected context
            bns = (results.get("final_broker_next_step") or "").lower()
            # Good: broker guidance mentions concrete items
            if "year" in bns or "zip" in bns or "delivery" in bns or "screenshot" in bns or "notice" in bns:
                pass  # OK
            elif "review" in bns and "context" not in bns:
                pass  # OK
        # If we handed off, second system reply is handoff message (办公室会尽快处理)
        # That's expected - no need to check for "ignores new details" there

    # Handoff timing
    expected = sim.get("expected_handoff_after_turn", 2)
    actual = results.get("handoff_ready_at_turn")
    if actual is not None and expected is not None and actual != expected:
        notes.append(f"Handoff at turn {actual}, expected {expected}")

    # Category sanity
    cat = results.get("final_category", "")
    sim_cat = sim.get("category", "")
    cat_map = {
        "add_car_quote": "customer_question",
        "remove_car_policy_change": "customer_question",
        "premium_review": "customer_question",
        "payment_failed_cancellation_risk": "payment_lapse_expiration",
        "english_notice_confusion": "customer_question",
        "missing_document": "missing_document",
        "dmv_sr22_help": "customer_question",
        "claim_intake": "customer_question",
        "add_driver": "customer_question",
        "billing_clarification": "customer_question",
        "talk_to_agent": "customer_requested_human",
    }
    expected_cat = cat_map.get(sim_cat, "customer_question")
    if expected_cat == "payment_lapse_expiration" and cat not in ("payment_lapse_expiration", "cancellation_warning"):
        notes.append(f"Expected payment/cancellation category, got {cat}")
    elif expected_cat == "missing_document" and cat not in ("missing_document", "customer_question"):
        # Document confusion (garaging proof 是什么意思) routes to customer_question
        notes.append(f"Expected missing_document or customer_question, got {cat}")
    elif expected_cat == "customer_requested_human" and cat != "customer_requested_human":
        notes.append(f"Expected customer_requested_human, got {cat}")

    results["notes"] = notes

    # Final classification
    if not notes:
        results["classification"] = "strong"
    elif len(notes) <= 2 and not any("too generic" in n for n in notes):
        results["classification"] = "acceptable_with_friction"
    else:
        results["classification"] = "weak"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run multi-turn intake simulations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full replies")
    parser.add_argument("--single", type=str, help="Run only simulation ID (e.g. MT1)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of simulations (0=all)")
    args = parser.parse_args()

    data = load_simulations()
    sims = data.get("simulations", [])
    if args.limit:
        sims = sims[: args.limit]
    if args.single:
        sims = [s for s in sims if s.get("id") == args.single]
        if not sims:
            print(f"No simulation with id {args.single}")
            return 1

    print(f"Running {len(sims)} multi-turn simulations...\n", flush=True)
    strong = 0
    acceptable = 0
    weak = 0

    for sim in sims:
        result = run_single_simulation(sim, verbose=args.verbose)
        c = result.get("classification", "unknown")
        if c == "strong":
            strong += 1
        elif c == "acceptable_with_friction":
            acceptable += 1
        else:
            weak += 1

        status = "PASS" if c == "strong" else "FRICTION" if c == "acceptable_with_friction" else "WEAK"
        print(f"[{status}] {result['id']} {result.get('name', '')} ({result.get('category', '')})", flush=True)
        if result.get("notes"):
            for n in result["notes"]:
                print(f"       └ {n}")
        if args.verbose:
            for i, tr in enumerate(result.get("turn_results", [])):
                print(f"       Turn {tr['turn']}: customer: {tr['customer_text']}")
                print(f"               system:  {tr['system_reply']}")
                print(f"               handoff: {tr['handoff_ready']}")
            print(f"       Final: category={result.get('final_category')} urgency={result.get('final_urgency')}")
            print(f"       broker_next_step: {(result.get('final_broker_next_step') or '')[:100]}...")
        print()

    print("---")
    print(f"Strong: {strong} | Acceptable with friction: {acceptable} | Weak: {weak}")
    return 0 if weak == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
