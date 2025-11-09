#!/usr/bin/env python3
"""
Normalize historical bandit state against a new reward configuration.

This migration script replays the most recent metrics snapshots for each arm,
computes rewards via the existing `reward.py` helper (respecting the provided
weight specification and target P95), and rewrites the state file with a fresh
EMA while preserving counts.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence
from collections.abc import Mapping, MutableMapping

import io_utils


DEFAULT_WEIGHTS = "recall=1,latency=3,err=1,cost=0"
DEFAULT_TARGET_P95 = 1000.0
DEFAULT_ALPHA = 0.3
DEFAULT_WINDOW = 10


@dataclass(frozen=True)
class RewardSample:
    reward: float
    recall: float
    p95: float
    err: float
    cost: float
    samples: int
    metrics_path: Path
    captured_at: datetime


def _resolve_state_path(arg: str | None) -> Path:
    if arg:
        path = Path(arg).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return io_utils.resolve_state_path()


def _parse_metrics(path: Path) -> tuple[str | None, RewardSample | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None, None

    policy_name = None
    policy = payload.get("policy")
    if isinstance(policy, Mapping):
        name = policy.get("name")
        if isinstance(name, str):
            policy_name = name

    job_note = payload.get("job_note")
    if not policy_name and isinstance(job_note, str) and ":" in job_note:
        _, _, tail = job_note.partition(":")
        policy_name = tail.strip()

    metrics = payload.get("metrics", {})
    if not isinstance(metrics, Mapping):
        return policy_name, None

    recall = float(metrics.get("recall_at_10", metrics.get("recall", 0.0)) or 0.0)
    p95 = float(
        metrics.get(
            "p95_latency_ms",
            metrics.get("p95_ms", metrics.get("p95", 0.0)),
        )
        or 0.0
    )
    err = float(metrics.get("error_rate", metrics.get("err_rate", 0.0)) or 0.0)
    cost = float(metrics.get("cost_per_query", metrics.get("cost", 0.0)) or 0.0)
    sample_count = metrics.get("count")
    if sample_count is None:
        config = payload.get("config")
        if isinstance(config, Mapping):
            sample_count = config.get("sample")
    try:
        samples = int(sample_count or 0)
    except (TypeError, ValueError):
        samples = 0

    timestamp_raw = payload.get("ts") or payload.get("timestamp")
    if isinstance(timestamp_raw, str):
        try:
            captured_at = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
        except ValueError:
            captured_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    else:
        captured_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

    sample = RewardSample(
        reward=float("nan"),  # placeholder, filled later
        recall=recall,
        p95=p95,
        err=err,
        cost=cost,
        samples=samples,
        metrics_path=path,
        captured_at=captured_at,
    )
    return policy_name, sample


def _collect_recent_metrics(
    arms: Iterable[str],
    runs_dir: Path,
    window: int,
) -> dict[str, list[RewardSample]]:
    per_arm: dict[str, list[RewardSample]] = {arm: [] for arm in arms}
    if window <= 0:
        return per_arm
    if not runs_dir.exists():
        return per_arm

    metric_paths = sorted(
        runs_dir.glob("*/metrics.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )

    for metrics_path in metric_paths:
        arm_name, sample = _parse_metrics(metrics_path)
        if arm_name is None or sample is None:
            continue
        if arm_name not in per_arm:
            continue
        bucket = per_arm[arm_name]
        if len(bucket) >= window:
            continue
        bucket.append(sample)

        if all(len(samples) >= window for samples in per_arm.values()):
            break

    # restore chronological order (oldest first) for EMA
    for arm, samples in per_arm.items():
        samples.sort(key=lambda item: item.captured_at)
    return per_arm


def _invoke_reward_cli(
    reward_script: Path,
    sample: RewardSample,
    *,
    weights: str,
    target_p95: float,
) -> float:
    cmd = [
        sys.executable,
        str(reward_script),
        "--metrics",
        str(sample.metrics_path),
        "--weights",
        weights,
        "--target-p95",
        str(target_p95),
        "--dryrun",
        "--print-json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"reward.py failed for {sample.metrics_path}: {proc.stderr or proc.stdout}"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Unable to parse reward output for {sample.metrics_path}: {exc}"
        ) from exc
    reward_value = float(payload.get("reward", 0.0))
    return reward_value


def _ema(alpha: float, rewards: Sequence[float]) -> float | None:
    if not rewards:
        return None
    avg = rewards[0]
    for value in rewards[1:]:
        avg = alpha * value + (1.0 - alpha) * avg
    return avg


def _update_entry(
    entry: MutableMapping[str, object],
    *,
    ema_reward: float | None,
    latest_sample: RewardSample | None,
    latest_reward: float | None,
    reset_only: bool,
) -> None:
    if reset_only:
        entry["avg_reward"] = 0.0
        entry["last_reward"] = 0.0
        entry["last_p95"] = 0.0
        entry["last_recall"] = 0.0
        entry["last_err"] = 0.0
        entry["last_metrics"] = {
            "p95_ms": 0.0,
            "recall_at_10": 0.0,
            "error_rate": 0.0,
            "cost": 0.0,
            "samples": 0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        entry["streak"] = 0
        entry["last_updated"] = datetime.now(timezone.utc).isoformat()
        return

    if ema_reward is not None:
        entry["avg_reward"] = ema_reward
    if latest_reward is not None:
        entry["last_reward"] = latest_reward
    if latest_sample is not None:
        entry["last_p95"] = latest_sample.p95
        entry["last_recall"] = latest_sample.recall
        entry["last_err"] = latest_sample.err
        entry["last_metrics"] = {
            "p95_ms": latest_sample.p95,
            "recall_at_10": latest_sample.recall,
            "error_rate": latest_sample.err,
            "cost": latest_sample.cost,
            "samples": latest_sample.samples,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    entry["streak"] = 0
    entry["last_updated"] = datetime.now(timezone.utc).isoformat()


def migrate_state(
    *,
    state_path: Path,
    runs_dir: Path,
    weights: str,
    target_p95: float,
    alpha: float,
    window: int,
    reset_window: int | None,
    dryrun: bool,
    emit_report: bool,
    print_diff: bool,
) -> None:
    raw_state = io_utils.read_json(state_path, default={})
    if not isinstance(raw_state, MutableMapping):
        raise SystemExit("[ERROR] state file is not a JSON object")

    arms = [
        arm
        for arm in raw_state.keys()
        if arm != "meta" and isinstance(raw_state.get(arm), Mapping)
    ]
    if not arms:
        raise SystemExit("[ERROR] no arms found in state file")

    reward_script = Path(__file__).resolve().parent / "reward.py"
    metrics_window = reset_window if reset_window is not None else window
    per_arm_samples = _collect_recent_metrics(arms, runs_dir, metrics_window)

    before_snapshot: dict[str, float | None] = {}
    diffs: list[str] = []

    for arm in arms:
        entry_obj = raw_state.get(arm)
        if not isinstance(entry_obj, MutableMapping):
            continue
        before_snapshot[arm] = (
            float(entry_obj.get("avg_reward")) if isinstance(entry_obj.get("avg_reward"), (int, float)) else None
        )
        samples = per_arm_samples.get(arm, [])
        if not samples:
            if reset_window == 0:
                _update_entry(
                    entry_obj,
                    ema_reward=None,
                    latest_sample=None,
                    latest_reward=None,
                    reset_only=True,
                )
                if print_diff:
                    diffs.append(f"* {arm}: reset to zero (no recent samples)")
            else:
                diffs.append(f"* {arm}: no metrics found -> skipped")
            continue

        computed_rewards: list[float] = []
        for idx, sample in enumerate(samples):
            reward_value = _invoke_reward_cli(
                reward_script,
                sample,
                weights=weights,
                target_p95=target_p95,
            )
            samples[idx] = RewardSample(
                reward=reward_value,
                recall=sample.recall,
                p95=sample.p95,
                err=sample.err,
                cost=sample.cost,
                samples=sample.samples,
                metrics_path=sample.metrics_path,
                captured_at=sample.captured_at,
            )
            computed_rewards.append(reward_value)

        ema_value = _ema(alpha, computed_rewards)
        latest_sample = samples[-1] if samples else None
        latest_reward = computed_rewards[-1] if computed_rewards else None

        prev_avg = entry_obj.get("avg_reward")
        prev_avg_float = float(prev_avg) if isinstance(prev_avg, (int, float)) else None
        _update_entry(
            entry_obj,
            ema_reward=ema_value,
            latest_sample=latest_sample,
            latest_reward=latest_reward,
            reset_only=False,
        )

        if print_diff:
            if ema_value is None:
                diffs.append(f"* {arm}: EMA unavailable (no rewards)")
            elif prev_avg_float is None:
                diffs.append(f"* {arm}: avg_reward -> {ema_value:.4f} (initialized)")
            else:
                delta = ema_value - prev_avg_float
                sign = "+" if delta >= 0 else ""
                diffs.append(
                    f"* {arm}: {prev_avg_float:.4f} -> {ema_value:.4f} (Δ{sign}{delta:.4f})"
                )

    meta = {
        "weights": weights,
        "target_p95": target_p95,
        "alpha": alpha,
        "window": metrics_window,
        "reset_window": reset_window,
        "migrated_at": datetime.now(timezone.utc).isoformat(),
    }
    raw_state["meta"] = meta

    if print_diff and diffs:
        print("\n".join(diffs))

    if dryrun:
        print("[STATE-MIGRATE] dryrun=1 -> no changes written")
        return

    io_utils.write_json(state_path, raw_state)
    print(f"[STATE-MIGRATE] state updated: {state_path}")

    if emit_report:
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        report_path = reports_dir / f"BANDIT_MIGRATE_{timestamp}.md"
        table_lines = [
            "# Bandit State Migration",
            "",
            f"- migrated_at: {meta['migrated_at']}",
            f"- state_path: {state_path}",
            f"- weights: {weights}",
            f"- target_p95: {target_p95}",
            "",
            "| arm | before_avg | after_avg | delta | status |",
            "| --- | ---:| ---:| ---:| --- |",
        ]
        for arm in arms:
            after_entry = raw_state.get(arm, {})
            after_avg = None
            if isinstance(after_entry, Mapping):
                value = after_entry.get("avg_reward")
                after_avg = float(value) if isinstance(value, (int, float)) else None
            before_avg = before_snapshot.get(arm)
            delta = None
            if after_avg is not None and before_avg is not None:
                delta = after_avg - before_avg
            status = "aligned" if delta is None or abs(delta) <= 0.1 else "drift"
            table_lines.append(
                f"| {arm} | "
                f"{'n/a' if before_avg is None else f'{before_avg:.4f}'} | "
                f"{'n/a' if after_avg is None else f'{after_avg:.4f}'} | "
                f"{'n/a' if delta is None else f'{delta:+.4f}'} | "
                f"{status} |"
            )

        report_path.write_text("\n".join(table_lines) + "\n", encoding="utf-8")
        print(f"[STATE-MIGRATE] report -> {report_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bandit reward state migration utility")
    parser.add_argument(
        "--state",
        type=str,
        help="Path to bandit_state.json (defaults to BANDIT_STATE env or ~/.data/searchforge/...)",  # noqa: E501
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path(".runs"),
        help="Directory containing per-run metrics.json files",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=os.environ.get("REWARD_WEIGHTS", DEFAULT_WEIGHTS),
        help="Reward weight overrides in recall=1,latency=3,... format",
    )
    parser.add_argument(
        "--target-p95",
        type=float,
        default=float(os.environ.get("TARGET_P95", DEFAULT_TARGET_P95)),
        help="Target p95 latency used for reward normalization",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=float(os.environ.get("ALPHA", DEFAULT_ALPHA)),
        help="EMA smoothing factor (0-1)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=int(os.environ.get("MIGRATE_WINDOW", DEFAULT_WINDOW)),
        help="Number of most recent metrics.json files per arm to replay",
    )
    parser.add_argument(
        "--reset-window",
        type=int,
        nargs="?",
        const=0,
        help="Reset avg_reward/last_metrics using up to N recent samples (omit N to zero out)",
    )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--apply",
        action="store_true",
        help="Persist the migrated state and emit a migration report",
    )
    action_group.add_argument(
        "--dryrun",
        action="store_true",
        help="Only print results without persisting the state file",
    )
    parser.add_argument(
        "--print-diff",
        action="store_true",
        help="Print avg_reward migration diff per arm",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state_path = _resolve_state_path(args.state)
    runs_dir = args.runs_dir.expanduser().resolve()
    if args.reset_window is not None and args.reset_window < 0:
        raise SystemExit("--reset-window must be >= 0")
    migrate_state(
        state_path=state_path,
        runs_dir=runs_dir,
        weights=args.weights,
        target_p95=args.target_p95,
        alpha=args.alpha,
        window=max(args.window, 1),
        reset_window=args.reset_window,
        dryrun=not args.apply,
        emit_report=args.apply,
        print_diff=args.print_diff,
    )


if __name__ == "__main__":
    main()


