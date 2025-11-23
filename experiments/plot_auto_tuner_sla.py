#!/usr/bin/env python3
"""
plot_auto_tuner_sla.py - Visualize AutoTuner vs heavy baseline under tight SLA.

Reads:
- .runs/auto_tuner_on_off_sla.csv

Produces:
- .runs/auto_tuner_on_off_sla.png
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt


def _load_sla_csv(csv_path: Path) -> Tuple[List[int], Dict[str, Dict[int, Dict[str, float]]]]:
    """
    Load SLA CSV and return budgets + metrics grouped by mode.

    Returns:
        budgets: sorted unique budget_ms values (ints)
        data: {mode: {budget_ms: {"p95_ms": float, "timeout_rate": float}}}
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"SLA CSV not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise RuntimeError(f"SLA CSV is empty: {csv_path}")

    data: Dict[str, Dict[int, Dict[str, float]]] = {}
    budgets_set = set()

    for row in rows:
        try:
            mode = row["mode"]
            budget_ms = int(row["budget_ms"])
            p95_ms = float(row["p95_ms"])
            timeout_rate = float(row["timeout_rate"])
        except (KeyError, ValueError) as e:
            # Skip malformed rows
            continue

        budgets_set.add(budget_ms)
        data.setdefault(mode, {})[budget_ms] = {
            "p95_ms": p95_ms,
            "timeout_rate": timeout_rate,
        }

    budgets = sorted(budgets_set)
    if not budgets:
        raise RuntimeError(f"No valid budget rows found in {csv_path}")

    return budgets, data


def _extract_series(
    budgets: List[int],
    data: Dict[str, Dict[int, Dict[str, float]]],
    mode: str,
    metric: str,
) -> List[float]:
    """Extract a metric series for a given mode across budgets (fills missing with 0)."""
    mode_data = data.get(mode, {})
    series: List[float] = []
    for b in budgets:
        val = mode_data.get(b, {}).get(metric, 0.0)
        series.append(float(val))
    return series


def plot_auto_tuner_sla(csv_path: Path, output_path: Path) -> None:
    budgets, data = _load_sla_csv(csv_path)

    # Prepare series
    baseline_p95 = _extract_series(budgets, data, mode="baseline", metric="p95_ms")
    autotuner_p95 = _extract_series(budgets, data, mode="autotuner", metric="p95_ms")

    baseline_timeout_pct = [
        v * 100.0 for v in _extract_series(budgets, data, mode="baseline", metric="timeout_rate")
    ]
    autotuner_timeout_pct = [
        v * 100.0 for v in _extract_series(budgets, data, mode="autotuner", metric="timeout_rate")
    ]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    # Top subplot: p95 vs budget
    ax1.plot(
        budgets,
        baseline_p95,
        color="orange",
        marker="o",
        label="Baseline (TopK=40, rerank=on)",
    )
    ax1.plot(
        budgets,
        autotuner_p95,
        color="C0",
        marker="o",
        label="Autotuner (Balanced)",
    )
    # SLA reference line (p95 target ~70ms)
    ax1.axhline(
        70,
        color="red",
        linestyle="--",
        alpha=0.5,
        label="SLA p95=70ms",
    )
    ax1.set_ylabel("p95 latency (ms)")
    ax1.set_title("AutoTuner vs Heavy Baseline – p95 under tight budgets")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Bottom subplot: timeout_rate vs budget
    ax2.plot(
        budgets,
        baseline_timeout_pct,
        color="orange",
        marker="o",
        label="Baseline (TopK=40, rerank=on)",
    )
    ax2.plot(
        budgets,
        autotuner_timeout_pct,
        color="C0",
        marker="o",
        label="Autotuner (Balanced)",
    )
    ax2.set_ylabel("Timeout rate (%)")
    ax2.set_xlabel("Budget (ms)")
    ax2.set_title("Timeout rate under tight SLA")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    print(f"[PLOT] Saved AutoTuner SLA figure to {output_path}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    runs_dir = repo_root / ".runs"
    csv_path = runs_dir / "auto_tuner_on_off_sla.csv"
    png_path = runs_dir / "auto_tuner_on_off_sla.png"

    try:
        plot_auto_tuner_sla(csv_path, png_path)
    except FileNotFoundError as e:
        print(f"[PLOT] ERROR: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"[PLOT] ERROR: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


