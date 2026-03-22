#!/usr/bin/env python3
"""
Broker Trial Stress Simulations — realistic broker/customer behavior.

Runs broker_trial_stress_simulations.json for hardening sprint.
Usage: PYTHONPATH=. python3 scripts/run_broker_trial_stress_simulations.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.fiqa_api.inbox_triage.triage import triage_conversation


def load_simulations() -> list[dict]:
    path = Path(__file__).resolve().parent.parent / "configs" / "broker_trial_stress_simulations.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("simulations", [])


WEAK_BROKER_NEXT_STEP_PATTERNS = (
    "continue processing",
    "follow up as needed",
    "review and act on",
)


def run_single(sim: dict) -> dict:
    sid = sim.get("id", "?")
    turns = [t for t in sim.get("turns", []) if (t.get("role") or "").strip().lower() == "customer"]
    conv: list[dict] = []
    results = {"id": sid, "name": sim.get("name", ""), "notes": [], "pass": True}
    handoff_at: int | None = None
    last_result: dict | None = None

    for i, t in enumerate(turns):
        text = (t.get("text") or "").strip()
        if not text:
            continue
        r = triage_conversation(text, conv)
        last_result = r
        cat = r.get("issue_category", "")
        handoff = r.get("handoff_ready", False)
        if handoff and handoff_at is None:
            handoff_at = i + 1

        # Check expectations
        if sim.get("expected_no_handoff_turn1") and i == 0 and handoff:
            results["notes"].append("Should NOT hand off turn 1 for vague message")
            results["pass"] = False
        if sim.get("expected_category") and i == 0 and cat != sim["expected_category"]:
            results["notes"].append(f"Expected category {sim['expected_category']}, got {cat}")
            results["pass"] = False
        if sim.get("expected_category_turn2") and i == 1 and cat != sim["expected_category_turn2"]:
            results["notes"].append(f"Turn 2 expected {sim['expected_category_turn2']}, got {cat}")
            results["pass"] = False
        exp_handoff = sim.get("expected_handoff_after_turn")
        if exp_handoff is not None and handoff_at is not None and handoff_at != exp_handoff:
            results["notes"].append(f"Handoff at turn {handoff_at}, expected {exp_handoff}")
            results["pass"] = False
        if exp_handoff is not None and handoff_at is None and i + 1 >= exp_handoff:
            results["notes"].append(f"Expected handoff by turn {exp_handoff}, but no handoff yet")
            results["pass"] = False

        conv.append({"role": "customer", "text": text})
        conv.append({"role": "system", "text": r.get("client_reply_draft", "")})

    # WORKBENCH_HANDOFF_PROFESSIONALIZATION: validate handoff quality when applicable
    if last_result and handoff_at is not None:
        bns = (last_result.get("broker_next_step") or "").lower()
        for weak in WEAK_BROKER_NEXT_STEP_PATTERNS:
            if weak in bns:
                results["notes"].append(f"broker_next_step too vague (contains '{weak}')")
                results["pass"] = False
        for kw in sim.get("expected_broker_next_step_contains", []):
            if kw.lower() not in bns:
                results["notes"].append(f"broker_next_step should contain '{kw}'")
                results["pass"] = False
        exp_qrs = sim.get("expected_quote_ready_status")
        if exp_qrs and last_result.get("quote_ready_status") != exp_qrs:
            results["notes"].append(f"Expected quote_ready_status={exp_qrs}, got {last_result.get('quote_ready_status')}")
            results["pass"] = False

    return results


def main() -> int:
    sims = load_simulations()
    print(f"Running {len(sims)} broker trial stress simulations...\n")
    failed = 0
    for sim in sims:
        r = run_single(sim)
        status = "PASS" if r["pass"] else "FAIL"
        if not r["pass"]:
            failed += 1
        print(f"[{status}] {r['id']} {r['name']}")
        for n in r.get("notes", []):
            print(f"       └ {n}")
    print(f"\n--- {len(sims) - failed}/{len(sims)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
