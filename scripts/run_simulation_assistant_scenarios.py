#!/usr/bin/env python3
"""
Run Simulation Assistant scenarios through triage for bug harvest.

Usage:
  PYTHONPATH=. python3 scripts/run_simulation_assistant_scenarios.py
  PYTHONPATH=. python3 scripts/run_simulation_assistant_scenarios.py --verbose
  PYTHONPATH=. python3 scripts/run_simulation_assistant_scenarios.py --single SIM9

Output: Per-scenario pass/fail, system replies, handoff timing, bug harvest notes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_conversation


def load_scenarios() -> list[dict]:
    config_path = Path(__file__).resolve().parent.parent / "configs" / "simulation_assistant_scenarios.json"
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("scenarios", [])


def run_scenario(scenario: dict, verbose: bool = False) -> dict:
    """Run one scenario and return results for bug harvest."""
    sid = scenario.get("id", "?")
    flow_type = scenario.get("flow_type", "")
    turns = scenario.get("turns", [])
    customer_turns = [t for t in turns if (t.get("role") or "").strip().lower() == "customer"]
    expected_handoff = scenario.get("expected_handoff_after_turn", 2)

    results = {
        "id": sid,
        "flow_type": flow_type,
        "title": scenario.get("title", ""),
        "notes": [],
        "system_replies": [],
        "handoff_ready_at_turn": None,
        "eval_tag": "unknown",
        "bug_harvest": [],
    }

    conversation_turns: list[dict[str, str]] = []

    for i, cust_turn in enumerate(customer_turns):
        text = (cust_turn.get("text") or "").strip()
        if not text:
            continue

        result = triage_conversation(text, conversation_turns)
        sys_reply = result.get("client_reply_draft", "")
        handoff = result.get("handoff_ready", False)

        results["system_replies"].append(sys_reply)

        if handoff and results["handoff_ready_at_turn"] is None:
            results["handoff_ready_at_turn"] = i + 1

        # Build conversation for next turn
        conversation_turns.append({"role": "customer", "text": text})
        conversation_turns.append({"role": "system", "text": sys_reply})

    # Bug harvest heuristics
    first_reply = (results["system_replies"] or [""])[0] if results["system_replies"] else ""
    first_lower = first_reply.lower()

    # Anti-patterns
    if "please provide more context" in first_lower or "这段内容还不够完整" in first_reply:
        if flow_type in ("add_car", "notice_cancellation", "missing_document", "claim", "renewal_premium"):
            results["bug_harvest"].append("First reply too generic for clear intent")
    if "thank you for reaching out" in first_lower or "feel free to ask" in first_lower:
        results["bug_harvest"].append("Robotic/formulaic first reply")

    # Handoff timing
    actual = results["handoff_ready_at_turn"]
    if actual is None:
        if len(customer_turns) >= expected_handoff:
            results["bug_harvest"].append("No handoff after expected turns")
    elif actual != expected_handoff:
        results["bug_harvest"].append(f"Handoff at turn {actual}, expected {expected_handoff}")

    # Turn-2 flow pollution: did second reply ask for wrong field?
    if len(results["system_replies"]) >= 2:
        second_reply = results["system_replies"][1]
        # If handoff happened, second reply should be handoff message
        if results["handoff_ready_at_turn"] != 2 and expected_handoff == 2:
            results["bug_harvest"].append("Turn 2 did not hand off when expected")

    # Eval tag
    if not results["bug_harvest"]:
        results["eval_tag"] = "Normal"
    elif any("too generic" in b for b in results["bug_harvest"]) or any("No handoff" in b for b in results["bug_harvest"]):
        results["eval_tag"] = "Off-flow / suspicious"
    else:
        results["eval_tag"] = "Needs review"

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Simulation Assistant scenarios for bug harvest")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full replies")
    parser.add_argument("--single", type=str, help="Run only scenario ID (e.g. SIM9)")
    args = parser.parse_args()

    scenarios = load_scenarios()
    if args.single:
        scenarios = [s for s in scenarios if s.get("id") == args.single]
        if not scenarios:
            print(f"No scenario with id {args.single}")
            return 1

    print(f"Running {len(scenarios)} Simulation Assistant scenarios...\n", flush=True)
    normal = 0
    needs_review = 0
    off_flow = 0

    for scenario in scenarios:
        result = run_scenario(scenario, verbose=args.verbose)
        tag = result["eval_tag"]
        if tag == "Normal":
            normal += 1
        elif tag == "Needs review":
            needs_review += 1
        else:
            off_flow += 1

        status = "PASS" if tag == "Normal" else "REVIEW" if tag == "Needs review" else "OFF-FLOW"
        print(f"[{status}] {result['id']} {result.get('title', '')} ({result.get('flow_type', '')})", flush=True)
        if result.get("bug_harvest"):
            for b in result["bug_harvest"]:
                print(f"       └ {b}")
        if args.verbose:
            for i, reply in enumerate(result.get("system_replies", [])):
                print(f"       Turn {i+1} system: {reply[:100]}...")
            print(f"       Handoff at turn: {result.get('handoff_ready_at_turn')}")
        print()

    print("---")
    print(f"Normal: {normal} | Needs review: {needs_review} | Off-flow: {off_flow}")
    return 0 if off_flow == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
