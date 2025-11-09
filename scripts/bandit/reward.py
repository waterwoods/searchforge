#!/usr/bin/env python3
"""Bandit reward utilities.

This module provides a minimal reward calculation that combines recall, latency,
error, and cost metrics into a single scalar. Weight defaults can be overridden
via environment variables.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, MutableMapping, Optional, Sequence

import io_utils


DEFAULT_WEIGHTS = {
    "wq": 1.0,  # recall weight
    "wl": 0.7,  # latency (p95) penalty weight
    "we": 1.2,  # error rate penalty weight
    "wc": 0.3,  # cost penalty weight
}


WEIGHT_ENV_MAP = {
    "wq": "BANDIT_WEIGHT_RECALL",
    "wl": "BANDIT_WEIGHT_LATENCY",
    "we": "BANDIT_WEIGHT_ERROR",
    "wc": "BANDIT_WEIGHT_COST",
}

WEIGHT_ALIAS = {
    "recall": "wq",
    "latency": "wl",
    "error": "we",
    "cost": "wc",
}


@dataclass(frozen=True)
class RewardWeights:
    recall: float
    latency: float
    error: float
    cost: float


def parse_weight_string(spec: Optional[str]) -> Mapping[str, float]:
    overrides: dict[str, float] = {}
    if not spec:
        return overrides
    for part in spec.split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        alias = WEIGHT_ALIAS.get(key.strip().lower())
        if not alias:
            continue
        try:
            overrides[alias] = float(value.strip())
        except ValueError:
            continue
    return overrides


def load_weights(overrides: Optional[Mapping[str, float]] = None) -> RewardWeights:
    """Load reward weights from the environment with optional overrides."""

    overrides = overrides or {}

    def _fetch(key: str) -> float:
        if key in overrides:
            return overrides[key]
        env = WEIGHT_ENV_MAP[key]
        default = DEFAULT_WEIGHTS[key]
        raw = os.getenv(env)
        if raw is None:
            return default
        try:
            return float(raw)
        except ValueError:
            return default

    return RewardWeights(
        recall=_fetch("wq"),
        latency=_fetch("wl"),
        error=_fetch("we"),
        cost=_fetch("wc"),
    )


def compute_reward(
    metrics: Mapping[str, float],
    weights: Optional[RewardWeights] = None,
    *,
    target_p95: Optional[float] = None,
) -> float:
    """Compute the scalar reward using simple, explainable normalization."""

    weights = weights or load_weights()

    recall_norm = max(0.0, min(float(metrics.get("recall", 0.0)), 1.0))

    p95_value = float(metrics.get("p95_latency_ms", 0.0))
    target = max(float(target_p95 or p95_value or 1.0), 1e-6)
    p95_norm = max(0.0, min(p95_value / target, 2.0))

    error_norm = max(0.0, float(metrics.get("error_rate", 0.0)))
    cost_norm = max(0.0, float(metrics.get("cost_per_query", 0.0)))

    reward = (
        weights.recall * recall_norm
        - weights.latency * p95_norm
        - weights.error * error_norm
        - weights.cost * cost_norm
    )
    return reward


def _flatten_candidates(payload: Mapping[str, object]) -> Sequence[tuple[str, object]]:
    stack = [payload]
    results: list[tuple[str, object]] = []
    while stack:
        current = stack.pop()
        if isinstance(current, Mapping):
            for key, value in current.items():
                results.append((str(key), value))
                if isinstance(value, Mapping):
                    stack.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, Mapping):
                            stack.append(item)
    return results


def _find_metric(payload: Mapping[str, object], synonyms: Sequence[str]) -> Optional[float]:
    synonyms = [s.lower() for s in synonyms]
    for key, value in _flatten_candidates(payload):
        key_lower = key.lower()
        if all(term in key_lower for term in synonyms):
            if isinstance(value, (int, float)):
                return float(value)
    return None


def _resolve_arm(payload: Mapping[str, object], override: Optional[str]) -> str:
    if override:
        return override

    policy = payload.get("policy")
    if isinstance(policy, Mapping):
        name = policy.get("name")
        if isinstance(name, str):
            return name

    for key, value in _flatten_candidates(payload):
        key_lower = key.lower()
        if key_lower in {"arm", "policy", "policy_name", "strategy", "config"} and isinstance(
            value, str
        ):
            return value
    raise ValueError("Unable to infer arm name from metrics; provide --arm")


def _extract_window_stats(payload: Mapping[str, object]) -> Mapping[str, Mapping[str, float]]:
    for key, value in _flatten_candidates(payload):
        if key.lower() == "window_stats" and isinstance(value, Mapping):
            return value  # type: ignore[return-value]
    return {}


def _load_metrics(path: Path) -> Mapping[str, object]:
    data = json.loads(path.read_text())
    if isinstance(data, Mapping):
        return data
    raise ValueError(f"Metrics file {path} does not contain a JSON object")


def _update_state(
    state_path: Path,
    arm: str,
    reward: float,
    *,
    samples: int,
    alpha: float,
    min_samples: int,
    winner: Optional[bool],
    stats: Mapping[str, float],
    window_stats: Optional[Mapping[str, Mapping[str, float]]],
    last_metrics: Mapping[str, object],
) -> Mapping[str, object]:
    raw_state = io_utils.read_json(state_path, default={})
    if not isinstance(raw_state, MutableMapping):
        raw_state = {}
    state: MutableMapping[str, MutableMapping[str, object]] = raw_state  # type: ignore[assignment]

    entry = state.setdefault(
        arm,
        {
            "counts": 0,
            "avg_reward": None,
            "last_updated": None,
            "window_stats": {},
            "streak": 0,
            "last_reward": None,
            "last_p95": None,
            "last_recall": None,
        },
    )

    effective_samples = max(int(samples), 1)
    min_samples = max(int(min_samples), 1)
    alpha = max(0.0, min(float(alpha), 1.0))

    entry["counts"] = int(entry.get("counts") or 0) + effective_samples

    prev_avg = entry.get("avg_reward")
    if prev_avg is None:
        new_avg = reward
    else:
        weight = alpha * min(1.0, effective_samples / float(min_samples))
        new_avg = (1.0 - weight) * float(prev_avg) + weight * reward

    entry["avg_reward"] = new_avg
    entry["last_updated"] = datetime.now(timezone.utc).isoformat()
    entry["last_reward"] = reward
    entry["last_p95"] = stats.get("p95_latency_ms")
    entry["last_recall"] = stats.get("recall")
    entry["last_err"] = stats.get("error_rate")

    if winner is not None:
        entry["streak"] = (int(entry.get("streak") or 0) + 1) if winner else 0

    if window_stats:
        entry["window_stats"] = window_stats
    entry["last_metrics"] = dict(last_metrics)

    io_utils.write_json(state_path, state)
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute bandit reward and optionally update state.")
    parser.add_argument("--metrics", required=True, type=Path, help="Path to metrics JSON file")
    parser.add_argument(
        "--update",
        type=Path,
        default=io_utils.resolve_state_path(),
        help="Path to bandit_state.json to update",
    )
    parser.add_argument("--arm", help="Override arm/policy name for the metrics")
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print the computed reward payload as JSON instead of plain text",
    )
    parser.add_argument(
        "--weights",
        type=str,
        help="Override reward weights in the form recall=1.0,latency=0.7,error=1.2,cost=0.3",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Skip updating state even if --update is supplied; outputs reward only",
    )
    parser.add_argument("--target-p95", type=float, help="Target p95 latency for normalization")
    parser.add_argument("--sla-p95", type=float, help="Fallback SLA p95 latency")
    parser.add_argument("--samples", type=int, default=0, help="Sample count associated with the metrics")
    parser.add_argument(
        "--alpha",
        type=float,
        default=float(os.getenv("BANDIT_ALPHA", "0.3")),
        help="EMA smoothing factor for reward averaging",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=30,
        help="Minimum sample threshold for full EMA weighting",
    )
    parser.add_argument(
        "--winner",
        type=str,
        choices={"yes", "no"},
        help="Flag indicating whether this arm is the winner for streak tracking",
    )

    args = parser.parse_args()
    payload = _load_metrics(args.metrics)

    metrics_section = payload.get("metrics") if isinstance(payload, Mapping) else None
    metrics_root = metrics_section if isinstance(metrics_section, Mapping) else payload

    recall = _find_metric(metrics_root, ["recall"]) or 0.0
    latency = _find_metric(metrics_root, ["p95", "latency"])
    if latency is None or latency == 0.0:
        latency = _find_metric(metrics_root, ["p95_ms"])
    latency = latency or 0.0
    error = _find_metric(metrics_root, ["error", "rate"]) or 0.0
    cost = _find_metric(metrics_root, ["cost"]) or 0.0

    window_stats = _extract_window_stats(payload)

    weight_overrides = parse_weight_string(args.weights)
    weights = load_weights(weight_overrides)

    target_p95 = args.target_p95 or args.sla_p95 or latency or 1.0

    reward = compute_reward(
        {
            "recall": recall,
            "p95_latency_ms": latency,
            "error_rate": error,
            "cost_per_query": cost,
        },
        weights=weights,
        target_p95=target_p95,
    )

    arm = _resolve_arm(payload, args.arm)

    result = {
        "arm": arm,
        "reward": reward,
        "target_p95": target_p95,
        "metrics": {
            "recall": recall,
            "p95_latency_ms": latency,
            "error_rate": error,
            "cost_per_query": cost,
        },
    }

    last_metrics_payload = {
        "p95_ms": latency,
        "recall_at_10": recall,
        "error_rate": error,
        "cost": cost,
        "samples": int(args.samples),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result["last_metrics"] = last_metrics_payload

    state_entry: Optional[Mapping[str, object]] = None

    if args.update and not args.dryrun:
        state_entry = _update_state(
            args.update,
            arm,
            reward,
            samples=args.samples,
            alpha=args.alpha,
            min_samples=args.min_samples,
            winner=(None if args.winner is None else args.winner == "yes"),
            stats={
                "recall": recall,
                "p95_latency_ms": latency,
                "error_rate": error,
                "cost_per_query": cost,
            },
            window_stats=window_stats,
            last_metrics=last_metrics_payload,
        )
        result["state_path"] = str(args.update)
    elif args.update and args.dryrun:
        result["state_path"] = str(args.update)

    if isinstance(state_entry, Mapping):
        result["state_entry"] = {
            "counts": state_entry.get("counts"),
            "avg_reward": state_entry.get("avg_reward"),
            "last_metrics": state_entry.get("last_metrics"),
        }

    if args.print_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"arm={arm} reward={reward:.4f}")


if __name__ == "__main__":
    main()


__all__ = ["RewardWeights", "load_weights", "compute_reward"]


