#!/usr/bin/env python3
"""
Bandit arm selector (UCB1 / epsilon-greedy).

Reads bandit_state.json and configs/policies.json, then emits a JSON payload
describing which arm to pick next together with reasoning metadata.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Mapping, Tuple

import io_utils


def _arm_list(policies: Mapping[str, object]) -> Iterable[str]:
    data = policies.get("policies")
    if not isinstance(data, Mapping):
        raise SystemExit("[ERROR] policies.json missing 'policies' mapping")
    return [arm for arm in ("fast_v1", "balanced_v1", "quality_v1") if arm in data]


def _counts_and_rewards(
    state_data: Mapping[str, object],
    arms: Iterable[str],
) -> Tuple[Dict[str, int], Dict[str, float]]:
    counts: Dict[str, int] = {}
    rewards: Dict[str, float] = {}
    for arm in arms:
        entry = state_data.get(arm, {})
        if not isinstance(entry, Mapping):
            entry = {}
        counts[arm] = int(entry.get("counts", 0) or 0)
        rewards[arm] = float(entry.get("avg_reward", 0.0) or 0.0)
    return counts, rewards


def _pick_under_sampled(arms: Iterable[str], counts: Mapping[str, int], min_samples: int) -> str | None:
    under = [arm for arm in arms if counts.get(arm, 0) < min_samples]
    if not under:
        return None
    under.sort(key=lambda arm: (counts.get(arm, 0), arm))
    return under[0]


def _ucb1_select(
    arms: Iterable[str],
    counts: Mapping[str, int],
    rewards: Mapping[str, float],
) -> Tuple[str, Dict[str, float]]:
    total = sum(max(counts.get(arm, 0), 0) for arm in arms)
    indices: Dict[str, float] = {}
    best_arm = None
    best_index = -float("inf")
    for arm in arms:
        n_i = counts.get(arm, 0)
        if n_i <= 0 or total == 0:
            index = float("inf")
        else:
            bonus = math.sqrt(2.0 * math.log(total) / n_i)
            index = rewards.get(arm, 0.0) + bonus
        indices[arm] = index
        if index > best_index:
            best_index = index
            best_arm = arm
    assert best_arm is not None
    return best_arm, indices


def _epsilon_select(
    arms: Iterable[str],
    counts: Mapping[str, int],
    rewards: Mapping[str, float],
    eps: float,
) -> Tuple[str, Dict[str, float], float]:
    eps = max(0.0, min(eps, 1.0))
    rnd = random.random()
    if rnd < eps:
        picked = random.choice(list(arms))
    else:
        picked = max(arms, key=lambda arm: (rewards.get(arm, 0.0), -counts.get(arm, 0)))
    indices = {arm: rewards.get(arm, 0.0) for arm in arms}
    return picked, indices, rnd


def main() -> None:
    parser = argparse.ArgumentParser(description="Bandit arm selector")
    parser.add_argument("--algo", choices={"ucb1", "epsilon"}, default="ucb1")
    parser.add_argument("--eps", type=float, default=0.10, help="exploration rate for epsilon-greedy")
    parser.add_argument("--eps-decay", type=float, default=0.98, help="display only; no state mutation")
    parser.add_argument("--min-samples", type=int, default=15, help="minimum samples before inclusion in main selection")
    parser.add_argument("--state", type=Path, default=io_utils.resolve_state_path())
    parser.add_argument("--policies", type=Path, default=io_utils.resolve_policies_path())
    parser.add_argument("--print-json", action="store_true", help="emit selection as compact JSON")
    parser.add_argument("--seed", type=int, help="optional RNG seed for epsilon exploration")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    policies_data = io_utils.read_json(args.policies, default={})
    if not isinstance(policies_data, Mapping) or "policies" not in policies_data:
        raise SystemExit(f"[ERROR] invalid policies file: {args.policies}")
    state_data = io_utils.read_json(args.state, default={})
    if not isinstance(state_data, Mapping):
        raise SystemExit(f"[ERROR] invalid state file: {args.state}")

    arms = list(_arm_list(policies_data))
    if not arms:
        raise SystemExit("[ERROR] policies.json missing required arms (fast_v1/balanced_v1/quality_v1)")

    counts, rewards = _counts_and_rewards(state_data, arms)

    min_sample_choice = _pick_under_sampled(arms, counts, args.min_samples)

    reason: Dict[str, object] = {
        "counts": counts,
        "eps": args.eps,
        "eps_after_decay": round(args.eps * args.eps_decay, 6),
    }

    if min_sample_choice is not None:
        picked = min_sample_choice
        reason["kind"] = "min_sample_round_robin"
        reason["indices"] = {arm: rewards.get(arm, 0.0) for arm in arms}
    elif args.algo == "ucb1":
        picked, indices = _ucb1_select(arms, counts, rewards)
        reason["indices"] = indices
        reason["N"] = sum(counts.values())
    else:
        picked, indices, rnd = _epsilon_select(arms, counts, rewards, args.eps)
        reason["indices"] = indices
        reason["roll"] = rnd

    payload = {
        "picked": picked,
        "algo": args.algo,
        "reason": reason,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    if args.print_json:
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        if exc.code not in (0, 1, 2):
            raise

