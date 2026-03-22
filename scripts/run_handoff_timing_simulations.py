#!/usr/bin/env python3
"""
Handoff Timing Audit — run simulations focused on handoff timing.

Tests: customer-not-finished-yet, correction-after-handoff, mixed-intent,
vague, talk-to-agent, add-car+driver, premium+remove-vehicle.

Usage: PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py
       PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py --verbose
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_conversation


def load_simulations() -> list[dict]:
    path = Path(__file__).resolve().parent.parent / "configs" / "handoff_timing_simulations.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("simulations", [])


def run_single(sim: dict, verbose: bool = False) -> dict:
    sid = sim.get("id", "?")
    turns = [t for t in sim.get("turns", []) if (t.get("role") or "").strip().lower() == "customer"]
    conv: list[dict] = []
    results = {
        "id": sid,
        "name": sim.get("name", ""),
        "category": sim.get("category", ""),
        "notes": [],
        "pass": True,
        "handoff_at": None,
        "turn_results": [],
        "final_broker_next_step": None,
        "final_summary": None,
    }

    for i, t in enumerate(turns):
        text = (t.get("text") or "").strip()
        if not text:
            continue
        r = triage_conversation(text, conv)
        cat = r.get("issue_category", "")
        handoff = r.get("handoff_ready", False)
        if handoff and results["handoff_at"] is None:
            results["handoff_at"] = i + 1
            results["final_broker_next_step"] = r.get("broker_next_step")
            results["final_summary"] = r.get("conversation_summary")

        results["turn_results"].append({
            "turn": i + 1,
            "customer": text[:60] + ("..." if len(text) > 60 else ""),
            "handoff": handoff,
            "category": cat,
        })

        # Check expectations
        if sim.get("expected_no_handoff_turn1") and i == 0 and handoff:
            results["notes"].append("Should NOT hand off turn 1 (vague/mixed)")
            results["pass"] = False
        if sim.get("expected_no_handoff_turn2") and i == 1 and handoff:
            results["notes"].append("Should NOT hand off turn 2 (T3 adds key info)")
            results["pass"] = False
        if sim.get("expected_category") and i == 0 and cat != sim["expected_category"]:
            results["notes"].append(f"Expected category {sim['expected_category']}, got {cat}")
            results["pass"] = False
        exp = sim.get("expected_handoff_after_turn")
        if exp is not None and results["handoff_at"] is not None and results["handoff_at"] != exp:
            results["notes"].append(f"Handoff at turn {results['handoff_at']}, expected {exp}")
            results["pass"] = False
        if exp is not None and results["handoff_at"] is None and i + 1 >= exp:
            results["notes"].append(f"Expected handoff by turn {exp}, but no handoff yet")
            results["pass"] = False

        conv.append({"role": "customer", "text": text})
        conv.append({"role": "system", "text": r.get("client_reply_draft", "")})

    return results


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    sims = load_simulations()
    print(f"Running {len(sims)} handoff timing simulations...\n")
    failed = 0
    for sim in sims:
        r = run_single(sim, verbose=args.verbose)
        if not r["pass"]:
            failed += 1
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{status}] {r['id']} {r['name']} (handoff@{r['handoff_at']})")
        for n in r.get("notes", []):
            print(f"       └ {n}")
        if args.verbose:
            for tr in r.get("turn_results", []):
                print(f"       T{tr['turn']}: {tr['customer'][:50]}... handoff={tr['handoff']}")
            if r.get("final_broker_next_step"):
                print(f"       broker_next_step: {r['final_broker_next_step'][:80]}...")
        print()

    print(f"\n--- {len(sims) - failed}/{len(sims)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
