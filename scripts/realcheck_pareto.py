#!/usr/bin/env python3
"""Aggregate large-run autotuner results into Pareto summary."""

import argparse
import json
import statistics as st
from pathlib import Path
from typing import Any, Dict, List

from realcheck_large import aggregate_paired, _parse_budgets_arg

RUNS_DIR = Path(".runs")


def load_scenarios():
    scenarios = []
    for path in sorted(RUNS_DIR.glob("real_large_*.json")):
        name = path.name
        if name in {"real_large_report.json", "real_large_last_run.json", "pareto.json"}:
            continue
        if not (
            name.startswith("real_large_proxy_")
            or name.startswith("real_large_paired_")
        ):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_file"] = name
            scenarios.append(data)
        except Exception:
            continue
    return scenarios


def _legacy_main():
    scenarios = load_scenarios()
    if not scenarios:
        print("No real_large_*.json files found in .runs/")
        return 1
    pareto = []
    for entry in scenarios:
        record = {
            "mode": entry.get("mode"),
            "budget_ms": entry.get("budget_ms"),
            "success_rate": entry.get("success_rate"),
            "file": entry.get("_file"),
        }
        if entry.get("mode") == "paired" or str(entry.get("_file", "")).startswith("real_large_paired_"):
            record.update({
                "p95_on": entry.get("p95_on"),
                "p95_off": entry.get("p95_off"),
                "paired_median_delta_ms": entry.get("paired_median_delta_ms"),
                "paired_improve": entry.get("paired_improve"),
            })
        else:
            record.update({
                "recall": entry.get("recall_at_10"),
                "p95_ms": entry.get("p95_ms"),
                "p99_ms": entry.get("p99_ms"),
                "cost_ms": entry.get("latency_mean"),
            })
        pareto.append(record)

    bounds_ok = all(bool(entry.get("bounds_ok", True)) for entry in scenarios)
    stable_detune = all(bool(entry.get("stable_detune", True)) for entry in scenarios)

    paired_entries = [
        entry for entry in scenarios if entry.get("mode") == "paired" or str(entry.get("_file", "")).startswith("real_large_paired_")
    ]
    proxy_entries = [
        entry for entry in scenarios if str(entry.get("_file", "")).startswith("real_large_proxy_")
    ]

    def _paired_condition(entry: Dict[str, Any]) -> bool:
        cond = bool(entry.get("p95_down"))
        delta = entry.get("paired_median_delta_ms")
        if isinstance(delta, (int, float)):
            cond = cond or delta < 0
        p95_on = entry.get("p95_on")
        p95_off = entry.get("p95_off")
        if isinstance(p95_on, (int, float)) and isinstance(p95_off, (int, float)):
            cond = cond or (float(p95_on) < float(p95_off))
        return cond

    if paired_entries:
        paired_conditions = [_paired_condition(entry) for entry in paired_entries]
        p95_down = all(paired_conditions)
        deltas = [float(entry["paired_median_delta_ms"]) for entry in paired_entries if isinstance(entry.get("paired_median_delta_ms"), (int, float))]
        paired_median_delta = st.median(deltas) if deltas else None
        paired_improve_all = all(bool(entry.get("paired_improve")) for entry in paired_entries)
        paired_ok = p95_down and (paired_median_delta is None or paired_median_delta < 0)
    else:
        p95_down = all(bool(entry.get("p95_down")) for entry in proxy_entries) if proxy_entries else True
        paired_median_delta = None
        paired_improve_all = None
        paired_ok = p95_down

    report = {
        "ok": bounds_ok and stable_detune and paired_ok,
        "bounds_ok": bounds_ok,
        "stable_detune": stable_detune,
        "p95_down": p95_down,
        "paired_median_delta_ms": paired_median_delta,
        "paired_improve": paired_improve_all,
        "scenarios": [entry.get("_file") for entry in scenarios],
    }

    (RUNS_DIR / "pareto.json").write_text(json.dumps(pareto, indent=2), encoding="utf-8")
    (RUNS_DIR / "real_large_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PARETO PASS" if report["ok"] else "PARETO FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pareto aggregation utilities.")
    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Aggregate paired run outputs across default budgets (400,800,1200).",
    )
    parser.add_argument(
        "--budgets",
        type=str,
        default="200,400,800,1000,1200",
        help="Comma or space separated budgets used when aggregating paired results.",
    )
    args = parser.parse_args()

    if args.aggregate:
        budgets_override = _parse_budgets_arg(args.budgets)
        budgets = budgets_override or [200, 400, 800, 1000, 1200]
        raise SystemExit(aggregate_paired(budgets))

    raise SystemExit(_legacy_main())
