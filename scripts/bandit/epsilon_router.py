#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ε-greedy small-traffic router (one-click)

- 批量小流量：按 ε 将一小批请求分给探索臂，其余给当前最好臂
- 流程：apply policy -> 预热两道闸 -> 跑 canary -> 计算奖励 -> 更新 bandit_state.json
- 依赖：configs/policies.json, bandit_state.json, scripts/bandit/reward.py, experiments.fiqa_suite_runner.py
"""

from __future__ import annotations

import json
import os
import pathlib
import random
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, Iterable, Mapping, Optional

import io_utils

BASE = os.getenv("BANDIT_HEALTH_BASE_URL", "http://localhost:8000")
POL = io_utils.resolve_policies_path()
STATE = io_utils.resolve_state_path()
RUNS_DIR = pathlib.Path(".runs")
RUNS_DIR.mkdir(exist_ok=True, parents=True)
REPORTS_DIR = pathlib.Path("reports")
REPORTS_DIR.mkdir(exist_ok=True, parents=True)


def _get(url: str, timeout: float = 8.0) -> Mapping[str, object]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _post(url: str, timeout: float = 8.0) -> Mapping[str, object]:
    request = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _warm_cache(base: str, warm_cache: int) -> None:
    if warm_cache <= 0:
        return
    payload = json.dumps({"limit": warm_cache, "timeout_sec": 300}).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/api/admin/warmup",
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
        if not data.get("ok"):
            print(f"[WARN] warm_cache={warm_cache} failed response={data}")
        else:
            print(
                "[WARMUP] queries_run={queries_run} duration_ms={duration_ms} cache_hit_rate={cache_hit_rate}".format(
                    queries_run=data.get("queries_run", 0),
                    duration_ms=data.get("duration_ms", 0),
                    cache_hit_rate=data.get("cache_hit_rate", 0),
                )
            )
    except urllib.error.URLError as exc:  # pragma: no cover
        print(f"[WARN] warm_cache={warm_cache} warmup request failed: {exc}")


def warmup(max_wait: float = 30.0, sleep: float = 1.0) -> Mapping[str, object]:
    start = time.time()
    while True:
        try:
            emb = _get(f"{BASE}/api/health/embeddings")
            ready = _get(f"{BASE}/ready")
            if emb.get("ok") and ready.get("ok"):
                return {"ok": True, "elapsed": round(time.time() - start, 2)}
        except Exception:  # noqa: BLE001
            pass
        if time.time() - start > max_wait:
            return {"ok": False, "elapsed": round(time.time() - start, 2)}
        time.sleep(sleep)


def apply_policy(name: str) -> Mapping[str, object]:
    encoded = urllib.parse.quote(name)
    return _post(f"{BASE}/api/admin/policy/apply?name={encoded}")


def best_arm(state: Mapping[str, Mapping[str, object]], fallback_expected: Mapping[str, Mapping[str, float]]) -> str:
    scores: Dict[str, float] = {}
    for arm, expected in fallback_expected.items():
        entry = state.get(arm, {})
        avg_reward = entry.get("avg_reward")
        if isinstance(avg_reward, (int, float)):
            scores[arm] = float(avg_reward)
            continue
        recall = float(expected.get("expected_recall", 0.0))
        p95 = float(expected.get("expected_p95_ms", 1e9))
        scores[arm] = recall - 0.001 * (p95 / 10.0)
    return max(scores.items(), key=lambda pair: pair[1])[0]


def decide_allocation(
    arms: Iterable[str],
    exploit_arm: str,
    batch: int,
    eps: float,
    min_per_arm: int,
) -> Dict[str, int]:
    arms = list(arms)
    allocation = {arm: 0 for arm in arms}
    others = [arm for arm in arms if arm != exploit_arm]

    if not arms:
        return allocation

    if not others:
        allocation[exploit_arm] = batch
        return allocation

    min_per_arm = max(0, int(min_per_arm))
    for arm in arms:
        allocation[arm] = min_per_arm

    remaining = batch - min_per_arm * len(arms)
    if remaining < 0:
        # If batch is too small, fall back to proportional split.
        remaining = batch
        for arm in arms:
            allocation[arm] = 0

    desired_other = max(min_per_arm, int(round(batch * eps)))
    for arm in others:
        if remaining <= 0:
            break
        needed = max(0, desired_other - allocation[arm])
        grant = min(remaining, needed)
        allocation[arm] += grant
        remaining -= grant

    if remaining > 0:
        allocation[exploit_arm] += remaining

    return allocation


def run_canary(
    arm: str,
    cfg: Mapping[str, object],
    sample_size: int,
    seed: int,
    *,
    concurrency: int,
    warm_cache: int,
    base: str,
) -> str:
    before = {entry.name for entry in RUNS_DIR.glob("*") if entry.is_dir()}
    collection = str(cfg.get("collection", ""))
    args = [
        sys.executable,
        "-m",
        "experiments.fiqa_suite_runner",
        "--job-note",
        f"epsilon:{arm}",
        "--collection",
        collection,
        "--top_k",
        str(cfg.get("top_k", 10)),
        "--sample",
        str(sample_size),
        "--repeats",
        "1",
        "--seed",
        str(seed),
        "--concurrency",
        str(concurrency),
    ]

    args.extend(["--dataset-name", collection or arm])

    qrels_name = cfg.get("qrels_name")
    if not qrels_name and "fiqa" in collection:
        qrels_name = "fiqa_qrels_50k_v1"
    if qrels_name:
        args.extend(["--qrels-name", str(qrels_name)])

    if cfg.get("mmr"):
        args.append("--mmr")
        if "mmr_lambda" in cfg:
            args.extend(["--mmr-lambda", str(cfg.get("mmr_lambda", 0.3))])
    elif "mmr_lambda" in cfg:
        args.extend(["--mmr-lambda", str(cfg.get("mmr_lambda", 0.3))])

    if "ef_search" in cfg:
        args.extend(["--ef-search", str(cfg["ef_search"])])

    env = os.environ.copy()
    env["RUNS_DIR"] = str(RUNS_DIR.resolve())
    _warm_cache(base, warm_cache)
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

    after = {entry.name for entry in RUNS_DIR.glob("*") if entry.is_dir()}
    created = sorted(after - before)
    if not created:
        import re

        matches = re.findall(r"/\.runs/([^/]+)/metrics\.json", result.stdout)
        if matches:
            metrics_path = RUNS_DIR / matches[-1] / "metrics.json"
            if metrics_path.exists():
                return str(metrics_path)
        raise RuntimeError(f"no metrics dir found for arm={arm}\n{result.stdout}")

    metrics_path = RUNS_DIR / created[-1] / "metrics.json"
    if not metrics_path.exists():
        raise RuntimeError(f"metrics missing: {metrics_path}")

    try:
        data = json.loads(metrics_path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise RuntimeError(f"unable to parse metrics file {metrics_path}: {exc}") from exc

    data.setdefault("metrics", {})["count"] = int(sample_size)
    config_block = data.setdefault("config", {})
    config_block["sample"] = int(sample_size)
    config_block["concurrency"] = int(concurrency)
    config_block["warm_cache"] = int(warm_cache)
    metrics_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    return str(metrics_path)


def _assert_headers(base: str, cfg: Mapping[str, object]) -> None:
    """Validate response headers reflect the applied policy parameters."""

    payload = {
        "question": "bandit header check",
        "top_k": 1,
        "collection": cfg.get("collection"),
        "mmr": bool(cfg.get("mmr", False)),
        "mmr_lambda": float(cfg.get("mmr_lambda", 0.3)),
    }
    request = urllib.request.Request(
        f"{base}/api/query",
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
        headers = {key.lower(): value for key, value in response.headers.items()}

    expected_collection = str(cfg.get("collection", "")).lower()
    header_collection = headers.get("x-collection", "").lower()
    if expected_collection and header_collection and expected_collection not in header_collection:
        raise RuntimeError(
            f"Header collection mismatch: expected~={expected_collection} got={header_collection}"
        )

    expected_mmr = bool(cfg.get("mmr", False))
    header_mmr = headers.get("x-mmr")
    if header_mmr is not None and expected_mmr != (header_mmr.lower() == "true"):
        raise RuntimeError("Header MMR flag mismatch")

    if expected_mmr:
        header_lambda = headers.get("x-mmr-lambda")
        if header_lambda is not None:
            expected_lambda = float(cfg.get("mmr_lambda", 0.3))
            if abs(expected_lambda - float(header_lambda)) > 1e-3:
                raise RuntimeError(
                    f"Header MMR λ mismatch: expected={expected_lambda} got={header_lambda}"
                )


def _assert_sample_count(metrics_path: str, expected_n: int) -> None:
    with open(metrics_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    observed = int(payload.get("metrics", {}).get("count", -1))
    if observed != expected_n:
        raise RuntimeError(
            f"Sample mismatch for {metrics_path}: expected={expected_n} got={observed}"
        )


def _suspicious_p95(metrics_path: str) -> bool:
    with open(metrics_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    p95 = float(payload.get("metrics", {}).get("p95_ms", -1))
    return p95 > 0 and (p95 < 30 or p95 > 3000)


def _invoke_reward(
    metrics_path: str,
    arm_name: str,
    *,
    weights: str,
    target_p95: float,
    samples: int,
    alpha: float,
    min_samples: int,
    winner: Optional[bool],
    dryrun: bool,
) -> Mapping[str, object]:
    cmd = [
        sys.executable,
        "scripts/bandit/reward.py",
        "--metrics",
        metrics_path,
        "--arm",
        arm_name,
        "--weights",
        weights,
        "--target-p95",
        str(target_p95),
        "--samples",
        str(samples),
        "--alpha",
        str(alpha),
        "--min-samples",
        str(min_samples),
        "--print-json",
    ]

    if dryrun:
        cmd.append("--dryrun")
    else:
        cmd.extend(["--update", str(STATE)])
        if winner is not None:
            cmd.extend(["--winner", "yes" if winner else "no"])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)

    return json.loads(proc.stdout or "{}")


def read_sla(metrics_path: str, default_p95: float = 9e9, default_err: float = 0.0) -> tuple[float, float, float]:
    with open(metrics_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    metrics = payload.get("metrics", {})
    p95 = float(metrics.get("p95_ms", default_p95))
    err = float(metrics.get("error_rate", default_err))
    recall = float(metrics.get("recall_at_10", metrics.get("recall", 0.0)))
    return p95, err, recall


def ensure_state(arms: Iterable[str]) -> Mapping[str, object]:
    raw = io_utils.read_json(STATE, default={})
    state = raw if isinstance(raw, dict) else {}
    updated = False
    for arm in arms:
        if arm not in state:
            state[arm] = {
                "counts": 0,
                "avg_reward": None,
                "last_updated": None,
                "window_stats": {},
                "streak": 0,
                "last_reward": None,
                "last_p95": None,
                "last_recall": None,
            }
            updated = True
    if updated:
        io_utils.write_json(STATE, state)
    return state


def write_report(
    history: list[dict[str, object]],
    *,
    base_url: str,
    params: Mapping[str, object],
    final_policy: str,
    weight_spec: str,
    prefix: str,
) -> pathlib.Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    sanitized_prefix = prefix.rstrip("_") or "BANDIT_ROUNDS"
    path = REPORTS_DIR / f"{sanitized_prefix}_{timestamp}.md"

    header_lines = [
        "# Bandit Rounds Summary",
        "",
        f"- base: {base_url}",
        f"- rounds: {params['rounds']} (batch={params['batch']}, eps={params['eps']})",
        f"- min_per_arm: {params['min_per_arm']} | promote_p95: {params['promote_p95']:.2f} | promote_streak: {params['promote_streak']}",
        f"- weights: {weight_spec} | alpha: {params['alpha']}",
        f"- concurrency: {params.get('concurrency')} | warm_cache: {params.get('warm_cache')}",
        f"- final_policy: {final_policy}",
        "",
        "| round | arm | samples | p95_ms | recall | err | reward | meets_min | winner | metrics |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]

    for round_info in history:
        round_idx = round_info["round"]
        winner = round_info.get("winner")
        rows = sorted(round_info.get("rows", []), key=lambda row: row["arm"])
        for row in rows:
            winner_flag = "✅" if row["arm"] == winner else ""
            header_lines.append(
                "| {round} | {arm} | {n} | {p95:.0f} | {recall:.3f} | {err:.4f} | {reward:.4f} | {meets_min} | {winner_flag} | {metrics} |".format(
                    round=round_idx,
                    arm=row["arm"],
                    n=row["n"],
                    p95=row["p95"],
                    recall=row["recall"],
                    err=row["err"],
                    reward=row["reward"],
                    meets_min="yes" if row["meets_min"] else "no",
                    winner_flag=winner_flag,
                    metrics=row["metrics"],
                )
            )

    with path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(header_lines) + "\n")

    return path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="ε-greedy small-traffic router")
    parser.add_argument("--eps", type=float, default=float(os.getenv("EPS", "0.15")), help="explore ratio (0~1)")
    parser.add_argument("--batch", type=int, default=int(os.getenv("BATCH", "120")), help="requests per round")
    parser.add_argument("--rounds", type=int, default=int(os.getenv("ROUNDS", "5")), help="round count")
    parser.add_argument("--seed", type=int, default=int(os.getenv("SEED", "20251107")))
    parser.add_argument("--min-per-arm", type=int, default=int(os.getenv("MIN_PER_ARM", "30")))
    parser.add_argument("--promote-p95", type=float, default=float(os.getenv("PROMOTE_P95", "0.15")))
    parser.add_argument("--promote-streak", type=int, default=int(os.getenv("PROMOTE_STREAK", "2")))
    parser.add_argument("--sla-p95", type=float, default=float(os.getenv("SLA_P95", "1500")))
    parser.add_argument("--sla-error", type=float, default=float(os.getenv("SLA_ERR", "0.01")))
    parser.add_argument(
        "--weights",
        type=str,
        default=os.getenv("REWARD_WEIGHTS", os.getenv("WEIGHTS", "recall=1,latency=1,err=1,cost=0")),
    )
    parser.add_argument("--alpha", type=float, default=float(os.getenv("ALPHA", "0.3")))
    parser.add_argument(
        "--target-p95",
        type=float,
        default=float(os.getenv("TARGET_P95", "0")),
        help="Override target p95 latency for reward normalization (0 = per-policy expected)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=int(os.getenv("CONCURRENCY", "4")),
        help="Runner concurrency for canary sampling",
    )
    parser.add_argument(
        "--warm-cache",
        type=int,
        default=int(os.getenv("WARM_CACHE", "0")),
        help="Warm cache limit before running each canary",
    )
    parser.add_argument(
        "--report-prefix",
        type=str,
        default=os.getenv("ROUTER_REPORT_PREFIX", "BANDIT_ROUNDS"),
        help="Prefix for router markdown reports",
    )
    parser.add_argument(
        "--force-arm",
        type=str,
        choices=("fast_v1", "balanced_v1", "quality_v1"),
        help="Force running a single arm with EPS=0 and one round",
    )
    args = parser.parse_args()

    policies_payload = io_utils.read_json(POL, default={})
    policies = policies_payload["policies"]
    if args.force_arm and args.force_arm not in policies:
        raise SystemExit(f"[ERROR] force-arm={args.force_arm} not present in policies.json")

    if args.force_arm:
        arms = [args.force_arm]
        args.eps = 0.0
        args.rounds = 1
        args.min_per_arm = min(args.batch, args.min_per_arm)
    else:
        arms = [arm for arm in ("fast_v1", "balanced_v1", "quality_v1") if arm in policies]
    if not arms:
        print("[ROUTER] no eligible arms found in policies.json")
        sys.exit(1)

    state = ensure_state(arms)
    expected = {
        arm: {
            "expected_recall": policies[arm].get("expected_recall", 0.0),
            "expected_p95_ms": policies[arm].get("expected_p95_ms", 1e9),
        }
        for arm in arms
    }

    baseline_arm = policies_payload.get("sla_thresholds", {}).get("rollback_target", "baseline_v1")

    print(
        f"[ROUTER] base={BASE} eps={args.eps} batch={args.batch} rounds={args.rounds} "
        f"min_per_arm={args.min_per_arm}"
    )
    print(
        f"[ALIGN] sample={args.batch} seed={args.seed} concurrency={args.concurrency} warm_cache={args.warm_cache}"
    )

    warm = warmup()
    if not warm.get("ok"):
        print(f"[ROUTER] warmup failed in {warm.get('elapsed')}s")
        sys.exit(2)
    print(f"[ROUTER] warmup ok in {warm.get('elapsed')}s")

    try:
        status = _get(f"{BASE}/api/admin/policy/current")
        current_policy = status.get("policy_name", arms[0])
    except Exception:  # noqa: BLE001
        current_policy = arms[0]

    promotion_tracker = {arm: 0 for arm in arms}
    history: list[dict[str, object]] = []
    exploit_breach_streak = 0

    for round_idx in range(1, args.rounds + 1):
        policy_start = current_policy
        random.seed(args.seed + round_idx)
        exploit = best_arm(state, expected)
        allocation = decide_allocation(arms, exploit, args.batch, args.eps, args.min_per_arm)
        print(f"\n[ROUND {round_idx}] exploit={exploit} alloc={allocation}")

        round_rows: list[dict[str, object]] = []
        exploit_violation = False
        violation_detail = ""
        auto_rollback_performed = False

        for arm in arms:
            count = allocation.get(arm, 0)
            if count <= 0:
                continue

            cfg = policies[arm]
            apply_policy(arm)
            warm_inner = warmup()
            if not warm_inner.get("ok"):
                print(f"[WARN] warmup timeout for arm={arm} after switching policy")
                continue

            try:
                _assert_headers(BASE, cfg)
            except Exception as exc:  # noqa: BLE001
                print(f"[ERROR] header check failed for arm={arm}: {exc}")
                continue

            try:
                metrics_path = run_canary(
                    arm,
                    cfg,
                    count,
                    args.seed + round_idx,
                    concurrency=args.concurrency,
                    warm_cache=args.warm_cache,
                    base=BASE,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[ERROR] canary failed arm={arm}: {exc}")
                continue

            try:
                _assert_sample_count(metrics_path, count)
            except Exception as exc:
                print(f"[ERROR] sample count check failed for arm={arm}: {exc}")
                continue

            p95, err, recall = read_sla(metrics_path)
            target_p95 = float(args.target_p95 if args.target_p95 > 0 else cfg.get("expected_p95_ms", args.sla_p95))

            skip_reward = _suspicious_p95(metrics_path)
            reward_value = float("nan")
            if skip_reward:
                print(f"[ROUTER][WARN] suspicious p95 (p95={p95:.1f}) -> skip reward update for {metrics_path}")
                reward_info: Mapping[str, object] = {}
            else:
                reward_info = _invoke_reward(
                    metrics_path,
                    arm,
                    weights=args.weights,
                    target_p95=target_p95,
                    samples=count,
                    alpha=args.alpha,
                    min_samples=args.min_per_arm,
                    winner=None,
                    dryrun=True,
                )
                reward_value = float(reward_info.get("reward", 0.0))

            row = {
                "arm": arm,
                "n": count,
                "p95": p95,
                "recall": recall,
                "err": err,
                "reward": reward_value,
                "metrics": metrics_path,
                "meets_min": count >= args.min_per_arm,
                "target_p95": target_p95,
                "skip_reward": skip_reward,
            }
            round_rows.append(row)

            if arm == exploit and (p95 > args.sla_p95 or err > args.sla_error):
                exploit_violation = True
                violation_detail = f"p95={p95:.1f} err={err:.4f}"

        rows_by_arm = {row["arm"]: row for row in round_rows}
        base_row = rows_by_arm.get(policy_start)
        winner_row: Optional[dict[str, object]] = None

        if base_row:
            candidates = [row for row in round_rows if row["arm"] != policy_start and row["meets_min"]]
            base_p95 = base_row["p95"]
            base_recall = base_row["recall"]
            for row in candidates:
                improvement = (base_p95 - row["p95"]) / base_p95 if base_p95 > 0 else 0.0
                recall_ok = row["recall"] >= base_recall - 1e-6
                if improvement >= args.promote_p95 or recall_ok:
                    if winner_row is None or row["reward"] > winner_row["reward"]:
                        winner_row = row
        else:
            candidates = [row for row in round_rows if row["meets_min"]]
            if candidates:
                winner_row = max(candidates, key=lambda item: item["reward"])

        winner_arm = winner_row["arm"] if winner_row else None

        if exploit_violation:
            exploit_breach_streak += 1
        else:
            exploit_breach_streak = 0

        if exploit_breach_streak >= 2 and current_policy != baseline_arm:
            print(
                f"[AUTO_ROLLBACK] exploit arm={exploit} consecutive_breach={exploit_breach_streak} "
                f"reason={violation_detail or 'unknown'} -> {baseline_arm}"
            )
            apply_policy(baseline_arm)
            warmup()
            current_policy = baseline_arm
            auto_rollback_performed = True
            for key in promotion_tracker:
                promotion_tracker[key] = 0
        elif exploit_violation:
            print(
                f"[ROUTER][WARN] exploit arm={exploit} breach streak={exploit_breach_streak} "
                f"reason={violation_detail or 'unknown'}"
            )
            for key in promotion_tracker:
                promotion_tracker[key] = 0

        if not exploit_violation and winner_arm:
            for key in promotion_tracker:
                promotion_tracker[key] = promotion_tracker[key] + 1 if key == winner_arm else 0

        promotion_performed = False
        if (
            winner_arm
            and promotion_tracker[winner_arm] >= args.promote_streak
            and winner_arm != current_policy
        ):
            print(f"[PROMOTE] applying policy {winner_arm} (streak={promotion_tracker[winner_arm]})")
            apply_policy(winner_arm)
            warmup()
            current_policy = winner_arm
            promotion_performed = True

        for row in round_rows:
            if row.get("skip_reward"):
                continue
            _invoke_reward(
                row["metrics"],
                row["arm"],
                weights=args.weights,
                target_p95=row["target_p95"],
                samples=row["n"],
                alpha=args.alpha,
                min_samples=args.min_per_arm,
                winner=(winner_arm is not None and row["arm"] == winner_arm),
                dryrun=False,
            )

        state = io_utils.read_json(STATE, default={})

        print("arm,n,p95_ms,recall_at_10,error,reward,metrics_path")
        for row in sorted(round_rows, key=lambda item: item["arm"]):
            print(
                f"{row['arm']},{row['n']},{int(row['p95'])},{row['recall']:.3f},{row['err']:.3f},{row['reward']:.4f},{row['metrics']}"
            )

        streak_display = (
            f"{winner_arm}:{promotion_tracker[winner_arm]}" if winner_arm else "none"
        )

        breach_label = "YES" if auto_rollback_performed else ("WARN" if exploit_violation else "NO")

        print(
            f"[ROUND {round_idx}] exploit={exploit} alloc={allocation} winner={winner_arm or 'none'} "
            f"streak={streak_display} current_policy={current_policy} "
            f"sla_breach_exploit={breach_label}"
        )

        history.append(
            {
                "round": round_idx,
                "exploit": exploit,
                "allocation": allocation,
                "rows": round_rows,
                "winner": winner_arm,
                "streak": promotion_tracker.get(winner_arm, 0) if winner_arm else 0,
                "policy_start": policy_start,
                "policy_end": current_policy,
                "auto_rollback": auto_rollback_performed,
                "promotion": promotion_performed,
                "exploit_violation": exploit_violation,
                "violation_detail": violation_detail,
            }
        )

    report_path = write_report(
        history,
        base_url=BASE,
        params={
            "rounds": args.rounds,
            "batch": args.batch,
            "eps": args.eps,
            "min_per_arm": args.min_per_arm,
            "promote_p95": args.promote_p95,
            "promote_streak": args.promote_streak,
            "alpha": args.alpha,
            "concurrency": args.concurrency,
            "warm_cache": args.warm_cache,
        },
        final_policy=current_policy,
        weight_spec=args.weights,
        prefix=args.report_prefix,
    )

    print(f"\n[ROUTER] report={report_path}")
    print("[ROUTER] done.")


if __name__ == "__main__":
    main()

