"""
A/B testing utilities invoked by the orchestrator flow.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tools.fetch_metrics import aggregate_metrics
from tools.run_eval import RunEvalResult, run_ab_task


def _metric_diff(baseline: Dict[str, float], candidate: Dict[str, float]) -> Dict[str, float]:
    keys = ("recall_at_10", "p95_ms", "cost")
    return {
        key: float(candidate.get(key, 0.0)) - float(baseline.get(key, 0.0))
        for key in keys
    }


def _render_chart(
    baseline_metrics: Dict[str, float],
    challenger_metrics: Dict[str, float],
    output_path: Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    labels = ["Recall@10", "P95 ms", "Cost"]
    baseline_values = [
        baseline_metrics.get("recall_at_10", 0.0),
        baseline_metrics.get("p95_ms", 0.0),
        baseline_metrics.get("cost", 0.0),
    ]
    challenger_values = [
        challenger_metrics.get("recall_at_10", 0.0),
        challenger_metrics.get("p95_ms", 0.0),
        challenger_metrics.get("cost", 0.0),
    ]

    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([i - 0.2 for i in x], baseline_values, width=0.4, label="Baseline")
    ax.bar([i + 0.2 for i in x], challenger_values, width=0.4, label="Challenger")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_title("A/B Comparison")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def _write_diff_csv(
    baseline_metrics: Dict[str, float],
    challenger_metrics: Dict[str, float],
    diff_table: Dict[str, float],
    csv_path: Path,
) -> Path:
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["metric", "baseline", "challenger", "delta"])
        for key in ("recall_at_10", "p95_ms", "cost"):
            writer.writerow(
                [
                    key,
                    baseline_metrics.get(key, 0.0),
                    challenger_metrics.get(key, 0.0),
                    diff_table.get(key, 0.0),
                ]
            )
    return csv_path


def _prepare_parameters(
    config: Dict[str, Any],
    sample_n: int,
    ab_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    dataset = config.get("dataset") or config.get("collection")
    if not dataset:
        raise ValueError("A/B configuration must include `dataset` or `collection`.")

    mmr_flag = bool(config.get("mmr", False))
    mmr_lambda = config.get("mmr_lambda", 0.0 if not mmr_flag else 0.3)
    if mmr_lambda is None:
        mmr_lambda = 0.0

    extra_args: Dict[str, Any] = {}
    for key in ("rerank", "use_hybrid", "fast_mode", "use_hard"):
        if key in config:
            extra_args[key] = config[key]

    if ab_cfg.get("warm_cache"):
        extra_args["warm_cache"] = ab_cfg.get("warm_cache")

    params: Dict[str, Any] = {
        "dataset": dataset,
        "sample": sample_n,
        "top_k": config.get("top_k"),
        "mmr": mmr_flag,
        "mmr_lambda": mmr_lambda,
        "ef_search": config.get("ef_search"),
        "concurrency": config.get("concurrency") or ab_cfg.get("concurrency", 1),
    }
    if params["top_k"] is None or params["ef_search"] is None:
        raise ValueError("A/B configuration must include `top_k` and `ef_search`.")
    if extra_args:
        params["extra_args"] = extra_args
    return params


def run_ab(
    baseline_cfg: Dict[str, Any],
    challenger_cfg: Dict[str, Any],
    sample_n: int,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute an A/B comparison between baseline and challenger configurations.
    """
    ab_cfg = cfg.get("ab") or {}
    reports_dir = Path(cfg.get("reports_dir", "reports")).resolve()
    run_id = cfg.get("run_id") or challenger_cfg.get("run_id") or baseline_cfg.get("run_id") or "ab"
    output_dir = reports_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_params = _prepare_parameters(baseline_cfg, sample_n, ab_cfg)
    challenger_params = _prepare_parameters(challenger_cfg, sample_n, ab_cfg)

    baseline_result: RunEvalResult = run_ab_task(baseline_params, cfg)
    challenger_result: RunEvalResult = run_ab_task(challenger_params, cfg)

    baseline_metrics = aggregate_metrics(baseline_result.metrics_path)
    challenger_metrics = aggregate_metrics(challenger_result.metrics_path)
    diff_table = _metric_diff(baseline_metrics, challenger_metrics)

    chart_path = _render_chart(
        baseline_metrics,
        challenger_metrics,
        output_dir / "ab_diff.png",
    )
    csv_path = _write_diff_csv(
        baseline_metrics,
        challenger_metrics,
        diff_table,
        output_dir / "ab_diff.csv",
    )

    return {
        "diff_table": diff_table,
        "chart_path": chart_path,
        "csv_path": csv_path,
        "baseline_metrics": baseline_metrics,
        "challenger_metrics": challenger_metrics,
        "baseline_job_id": baseline_result.job_id,
        "challenger_job_id": challenger_result.job_id,
    }
