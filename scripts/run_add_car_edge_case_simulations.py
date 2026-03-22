#!/usr/bin/env python3
"""
Run Add-Car edge-case simulations (ACE* ids) from customer_entry_multi_turn_simulations.json.

Usage:
  PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py
  PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py --verbose
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "run_multi_turn_simulations",
    Path(__file__).resolve().parent / "run_multi_turn_simulations.py",
)
_mts = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mts)
run_single_simulation = _mts.run_single_simulation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ACE* Add-Car edge-case simulations")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    config_path = Path(__file__).resolve().parent.parent / "configs" / "customer_entry_multi_turn_simulations.json"
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    sims = [s for s in data.get("simulations", []) if str(s.get("id", "")).startswith("ACE")]

    if not sims:
        print("No ACE* simulations found.")
        return 1

    print(f"Running {len(sims)} Add-Car edge-case simulations...\n", flush=True)
    strong = acceptable = weak = 0
    for sim in sorted(sims, key=lambda x: x.get("id", "")):
        result = run_single_simulation(sim, verbose=args.verbose)
        c = result.get("classification", "unknown")
        if c == "strong":
            strong += 1
        elif c == "acceptable_with_friction":
            acceptable += 1
        else:
            weak += 1
        status = "PASS" if c == "strong" else "FRICTION" if c == "acceptable_with_friction" else "WEAK"
        print(f"[{status}] {result['id']} {result.get('name', '')}", flush=True)
        if result.get("notes"):
            for n in result["notes"]:
                print(f"       └ {n}")
        if args.verbose:
            for tr in result.get("turn_results", []):
                print(f"       Turn {tr['turn']}: {tr['customer_text']}")
                print(f"               → handoff={tr['handoff_ready']} cat={tr['category']}")
        print()
    print("---")
    print(f"Strong: {strong} | Acceptable: {acceptable} | Weak: {weak}")
    return 0 if weak == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
