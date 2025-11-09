#!/usr/bin/env python3
"""
Generate a consolidated bandit summary report combining state, router rounds, and A/B results.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable

import io_utils
import reward


def _latest(path_glob: str) -> Path | None:
    files = sorted(Path(".").glob(path_glob))
    return files[-1] if files else None


def _load_state() -> Mapping[str, Mapping[str, object]]:
    raw = io_utils.read_json(io_utils.resolve_state_path(), default={})
    if not isinstance(raw, Mapping):
        raise SystemExit("[ERROR] bandit_state.json is malformed")
    return raw  # type: ignore[return-value]


def _load_rounds(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_ab_csv(path: Path) -> Dict[str, Dict[str, float]]:
    rows: Dict[str, Dict[str, float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            policy = row["policy"]
            rows[policy] = {
                "p95_ms": float(row["p95_ms"]),
                "recall_at_10": float(row["recall_at_10"]),
                "metrics_path": row["metrics_path"],
            }
    return rows


def _parse_weights() -> Mapping[str, float]:
    spec = os.environ.get("WEIGHTS", "recall=1,latency=3,err=1,cost=0")
    return reward.parse_weight_string(spec)


def _target_p95() -> float:
    return float(os.environ.get("TARGET_P95", "1000"))


def _compute_reward_from_ab(ab_row: Mapping[str, float]) -> float:
    metrics = {
        "recall": ab_row.get("recall_at_10", 0.0),
        "p95_latency_ms": ab_row.get("p95_ms", 0.0),
        "error_rate": ab_row.get("error_rate", 0.0),
        "cost_per_query": ab_row.get("cost_per_query", 0.0),
    }
    overrides = _parse_weights()
    weights = reward.load_weights(overrides)
    return reward.compute_reward(metrics, weights=weights, target_p95=_target_p95())


def _latest_metrics_reward(
    arm: str,
    *,
    runs_dir: Path,
    weights: reward.RewardWeights,
    target_p95: float,
) -> tuple[float | None, float | None, Path | None]:
    if not runs_dir.exists():
        return None, None, None

    candidate_paths = sorted(
        runs_dir.glob("*/metrics.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )

    for metrics_path in candidate_paths:
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        policy = payload.get("policy")
        policy_name = None
        if isinstance(policy, Mapping):
            name = policy.get("name")
            if isinstance(name, str):
                policy_name = name

        if not policy_name:
            job_note = payload.get("job_note")
            if isinstance(job_note, str) and ":" in job_note:
                _, _, tail = job_note.partition(":")
                policy_name = tail.strip()

        if policy_name != arm:
            continue

        metrics_block = payload.get("metrics", {})
        if not isinstance(metrics_block, Mapping):
            continue

        recall = float(
            metrics_block.get("recall_at_10", metrics_block.get("recall", 0.0)) or 0.0
        )
        p95 = float(
            metrics_block.get(
                "p95_latency_ms",
                metrics_block.get("p95_ms", metrics_block.get("p95", 0.0)),
            )
            or 0.0
        )
        err = float(metrics_block.get("error_rate", metrics_block.get("err_rate", 0.0)) or 0.0)
        cost = float(metrics_block.get("cost_per_query", metrics_block.get("cost", 0.0)) or 0.0)

        reward_value = reward.compute_reward(
            {
                "recall": recall,
                "p95_latency_ms": p95,
                "error_rate": err,
                "cost_per_query": cost,
            },
            weights=weights,
            target_p95=target_p95 or p95 or 1.0,
        )
        return reward_value, p95, metrics_path

    return None, None, None


def _within_tolerance(strength: float, measured: float, pct: float = 0.10) -> bool:
    denom = abs(strength) if abs(strength) > 1e-6 else 1.0
    return abs(measured - strength) / denom <= pct


def _reward_from_last_metrics(
    entry: Mapping[str, object],
    *,
    weights: reward.RewardWeights,
    target_p95: float,
) -> tuple[float | None, float | None]:
    last_metrics = entry.get("last_metrics")
    if not isinstance(last_metrics, Mapping):
        return None, None
    recall = float(last_metrics.get("recall_at_10", last_metrics.get("recall", 0.0)) or 0.0)
    p95 = float(last_metrics.get("p95_ms", last_metrics.get("p95_latency_ms", 0.0)) or 0.0)
    err = float(last_metrics.get("error_rate", 0.0) or 0.0)
    cost = float(last_metrics.get("cost", last_metrics.get("cost_per_query", 0.0)) or 0.0)
    reward_value = reward.compute_reward(
        {
            "recall": recall,
            "p95_latency_ms": p95,
            "error_rate": err,
            "cost_per_query": cost,
        },
        weights=weights,
        target_p95=target_p95 or p95 or 1.0,
    )
    return reward_value, p95


def _git_status() -> str:
    status = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, check=False)
    diffstat = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True, check=False)
    return f"```\n{status.stdout.strip()}\n```\n\n```\n{diffstat.stdout.strip()}\n```"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a consolidated bandit summary report.")
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Emit structured summary JSON to stdout (markdown report is still produced).",
    )
    args = parser.parse_args()

    state = _load_state()
    latest_rounds = _latest("reports/BANDIT_ROUNDS_*.md")
    latest_ab = _latest("reports/AB_*.csv")

    if not latest_rounds or not latest_ab:
        raise SystemExit("[ERROR] Missing BANDIT_ROUNDS or AB CSV report; run router and A/B first.")

    ab_data = _load_ab_csv(latest_ab)

    table1_lines = ["| arm | n | avg_reward | last_p95 | last_recall | streak |", "| --- | ---:| ---:| ---:| ---:| ---:|"]
    comparison_lines = ["| arm | ab_p95 | ab_recall | calc_reward | avg_reward | consistent | metrics_path |",
                        "| --- | ---:| ---:| ---:| ---:| --- | --- |"]
    drift_lines = [
        "| arm | instant_reward | state_avg | abs_delta | status | metrics |",
        "| --- | ---:| ---:| ---:| --- | --- |",
    ]

    best_arm = None
    best_reward = -float("inf")
    runs_dir = Path(os.environ.get("RUNS_DIR", ".runs")).expanduser()
    weight_overrides = _parse_weights()
    weights_obj = reward.load_weights(weight_overrides)
    target_p95 = _target_p95()
    state_records: list[dict[str, object]] = []
    drift_records: list[dict[str, object]] = []
    ab_records: list[dict[str, object]] = []

    for arm in ["fast_v1", "balanced_v1", "quality_v1"]:
        entry = state.get(arm, {})
        counts = entry.get("counts", 0)
        avg_reward = float(entry.get("avg_reward", 0.0) or 0.0)
        last_p95 = entry.get("last_p95", 0.0)
        last_recall = entry.get("last_recall", 0.0)
        streak = entry.get("streak", 0)
        table1_lines.append(
            f"| {arm} | {counts} | {avg_reward:.4f} | {float(last_p95 or 0.0):.1f} | {float(last_recall or 0.0):.3f} | {streak} |"
        )
        state_records.append(
            {
                "arm": arm,
                "counts": counts,
                "avg_reward": avg_reward,
                "last_p95": float(last_p95 or 0.0),
                "last_recall": float(last_recall or 0.0),
                "streak": streak,
            }
        )
        if avg_reward > best_reward:
            best_reward = avg_reward
            best_arm = arm

        ab_row = ab_data.get(arm)

        metrics_label: str | None = None
        instant_reward, _ = _reward_from_last_metrics(
            entry,
            weights=weights_obj,
            target_p95=target_p95,
        )
        metrics_path: Path | None = None
        if instant_reward is None:
            instant_reward, _, metrics_path = _latest_metrics_reward(
                arm,
                runs_dir=runs_dir,
                weights=weights_obj,
                target_p95=target_p95,
            )
        else:
            metrics_label = "state.last_metrics"

        if instant_reward is None:
            drift_lines.append(
                f"| {arm} | n/a | {avg_reward:.4f} | n/a | missing | - |"
            )
            drift_records.append(
                {
                    "arm": arm,
                    "instant_reward": None,
                    "state_avg": avg_reward,
                    "abs_delta": None,
                    "status": "missing",
                    "metrics_path": None,
                }
            )
        else:
            delta = abs(instant_reward - avg_reward)
            status = "OK" if delta <= 0.1 else "DRIFT"
            drift_lines.append(
                f"| {arm} | {instant_reward:.4f} | {avg_reward:.4f} | {delta:.4f} | {status} | {metrics_path if metrics_label is None else metrics_label} |"
            )
            drift_records.append(
                {
                    "arm": arm,
                    "instant_reward": instant_reward,
                    "state_avg": avg_reward,
                    "abs_delta": delta,
                    "status": status,
                    "metrics_path": metrics_label if metrics_label else str(metrics_path),
                }
            )

        if ab_row:
            calc_reward = _compute_reward_from_ab(ab_row)
            consistent = _within_tolerance(avg_reward, calc_reward)
            status = "yes" if consistent else "no"
            comparison_lines.append(
                f"| {arm} | {ab_row['p95_ms']:.1f} | {ab_row['recall_at_10']:.4f} | {calc_reward:.4f} | {avg_reward:.4f} | {status} | {ab_row['metrics_path']} |"
            )
            ab_records.append(
                {
                    "arm": arm,
                    "ab_p95": ab_row["p95_ms"],
                    "ab_recall": ab_row["recall_at_10"],
                    "calc_reward": calc_reward,
                    "state_avg": avg_reward,
                    "consistent": status == "yes",
                    "metrics_path": ab_row["metrics_path"],
                }
            )
        else:
            comparison_lines.append(
                f"| {arm} | n/a | n/a | n/a | {avg_reward:.4f} | missing | - |"
            )
            ab_records.append(
                {
                    "arm": arm,
                    "ab_p95": None,
                    "ab_recall": None,
                    "calc_reward": None,
                    "state_avg": avg_reward,
                    "consistent": False,
                    "metrics_path": None,
                }
            )

    conclusion_lines = []
    if best_arm:
        conclusion_lines.append(f"- 建议冻结 `{best_arm}`：当前 avg_reward={best_reward:.4f} 领先其他臂。")
    under_sampled = [arm for arm, entry in state.items() if (entry.get("counts") or 0) < 200]
    if under_sampled:
        conclusion_lines.append(f"- `{', '.join(under_sampled)}` 样本仍偏少，后续可提高 EPS 或增大批量。")
    inconsistent = [line for line in comparison_lines[2:] if "| no |" in line or "missing" in line]
    if inconsistent:
        conclusion_lines.append("- A/B 与路由 reward 存在偏差，请检查缓存/并发或样本方差。")
    else:
        conclusion_lines.append("- A/B 与路由 reward 在 ±10% 内，相互验证通过。")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_path = Path("reports") / f"BANDIT_SUMMARY_{timestamp}.md"
    content = [
        "# Bandit Summary Report",
        "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- state_path: {io_utils.resolve_state_path()}",
        f"- rounds_report: {latest_rounds}",
        f"- ab_report: {latest_ab}",
        "",
        "## State Overview",
        *table1_lines,
        "",
        "## 漂移自检",
        *drift_lines,
        "",
        "## A/B Comparison",
        *comparison_lines,
        "",
        "## Conclusion",
        *conclusion_lines,
        "",
        "## File Changes",
        _git_status(),
    ]

    out_path.write_text("\n".join(content) + "\n", encoding="utf-8")

    summary_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_path": str(io_utils.resolve_state_path()),
        "rounds_report": str(latest_rounds),
        "ab_report": str(latest_ab),
        "best_arm": best_arm,
        "best_reward": best_reward,
        "state": state_records,
        "drift": drift_records,
        "ab_comparison": ab_records,
        "conclusion": conclusion_lines,
        "markdown_path": str(out_path),
    }

    if args.print_json:
        print(json.dumps(summary_payload, indent=2, ensure_ascii=False))
    else:
        print(out_path)


if __name__ == "__main__":
    main()

