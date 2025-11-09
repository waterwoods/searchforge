"""
Pareto front visualization utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _pareto_front(rows: Iterable[Mapping[str, float]]) -> List[int]:
    rows = list(rows)
    if not rows:
        return []
    indices = list(range(len(rows)))
    sorted_indices = sorted(indices, key=lambda idx: (-rows[idx]["recall_at_10"], rows[idx]["p95_ms"]))
    pareto: List[int] = []
    best_latency = float("inf")
    for idx in sorted_indices:
        latency = rows[idx]["p95_ms"]
        if latency <= best_latency:
            pareto.append(idx)
            best_latency = latency
    return pareto


def render_pareto_chart(rows: Iterable[Mapping[str, float]], output_path: Path) -> Path:
    """
    Render pareto scatter plot and save as PNG.

    Args:
        rows: iterable of dicts containing `config_id`, `recall_at_10`, `p95_ms`, `cost`.
        output_path: target PNG path.
    """
    row_list = list(rows)
    if not row_list:
        raise ValueError("Pareto chart requires at least one row.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pareto_indices = _pareto_front(row_list)

    fig, ax = plt.subplots(figsize=(6, 4))
    recalls = [row["recall_at_10"] for row in row_list]
    latencies = [row["p95_ms"] for row in row_list]
    costs = [row.get("cost", 0.0) for row in row_list]
    labels = [row.get("config_id", f"cfg-{idx}") for idx, row in enumerate(row_list)]

    scatter = ax.scatter(latencies, recalls, c=costs, cmap="viridis", s=60, edgecolors="black")
    ax.set_xlabel("P95 Latency (ms)")
    ax.set_ylabel("Recall@10")
    ax.set_title("Quality vs Latency Pareto")
    plt.colorbar(scatter, ax=ax, label="Cost")

    for idx, label in enumerate(labels):
        ax.annotate(label, (latencies[idx], recalls[idx]), textcoords="offset points", xytext=(5, 5), fontsize=8)

    pareto_points = [row_list[idx] for idx in pareto_indices]
    pareto_latencies = [row["p95_ms"] for row in pareto_points]
    pareto_recalls = [row["recall_at_10"] for row in pareto_points]
    ax.plot(pareto_latencies, pareto_recalls, linestyle="--", color="red", linewidth=1.2, label="Pareto front")
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path

