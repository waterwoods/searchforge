#!/usr/bin/env python3
"""
Run fixed-sample A/B evaluation for all bandit arms and emit CSV/MD summaries.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional

import io_utils
import reward


def _apply_policy(base: str, arm: str) -> None:
    cmd = [
        sys.executable,
        "scripts/bandit/apply.py",
        "--arm",
        arm,
        "--base",
        base,
    ]
    subprocess.run(cmd, check=True)


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


def _assert_headers(base: str, cfg: Mapping[str, object]) -> None:
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
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
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


def _run_runner(
    note: str,
    cfg: Mapping[str, object],
    sample: int,
    seed: int,
    concurrency: int,
    repeats: int,
    warm_cache: int,
    base: str,
) -> Path:
    runs_dir = Path(os.environ.get("RUNS_DIR", ".runs"))
    runs_dir.mkdir(exist_ok=True, parents=True)
    before = {entry.name for entry in runs_dir.glob("*") if entry.is_dir()}

    _warm_cache(base, warm_cache)

    cmd = [
        sys.executable,
        "-m",
        "experiments.fiqa_suite_runner",
        "--job-note",
        note,
        "--collection",
        str(cfg.get("collection", "")),
        "--dataset-name",
        str(cfg.get("collection", "")),
        "--qrels-name",
        "fiqa_qrels_50k_v1",
        "--sample",
        str(sample),
        "--top_k",
        str(cfg.get("top_k", 10)),
        "--seed",
        str(seed),
        "--concurrency",
        str(concurrency),
        "--repeats",
        str(repeats),
    ]

    if bool(cfg.get("mmr", False)):
        cmd.append("--mmr")
    mmr_lambda = cfg.get("mmr_lambda")
    if mmr_lambda is not None:
        cmd.extend(["--mmr-lambda", str(mmr_lambda)])
    ef_search = cfg.get("ef_search")
    if ef_search is not None:
        cmd.extend(["--ef-search", str(ef_search)])

    subprocess.run(cmd, check=True)

    after = {entry.name for entry in runs_dir.glob("*") if entry.is_dir()}
    created = sorted(after - before)
    if not created:
        raise RuntimeError("runner did not produce a metrics directory")
    metrics_path = runs_dir / created[-1] / "metrics.json"
    if not metrics_path.exists():
        raise RuntimeError(f"metrics.json missing at {metrics_path}")

    with metrics_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    data.setdefault("metrics", {})["count"] = int(sample)
    config_block = data.setdefault("config", {})
    config_block["sample"] = int(sample)
    config_block["concurrency"] = int(concurrency)
    config_block["warm_cache"] = int(warm_cache)
    metrics_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    return metrics_path


def _extract_metrics(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    metrics = data.get("metrics", {})
    return {
        "policy": (data.get("policy") or {}).get("name", "unknown"),
        "p95_ms": float(metrics.get("p95_ms", 0.0)),
        "recall_at_10": float(metrics.get("recall_at_10", 0.0)),
        "path": str(path),
        "job_id": data.get("job_id"),
        "error_rate": float(metrics.get("error_rate", 0.0)),
        "cost_per_query": float(metrics.get("cost_per_query", 0.0)),
        "count": float(metrics.get("count", 0.0)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixed-sample A/B evaluation across bandit arms.")
    env_sample = int(os.environ.get("SAMPLE", os.environ.get("AB_SAMPLE", "200")))
    env_seed = int(os.environ.get("SEED", os.environ.get("AB_SEED", "20251107")))
    env_concurrency = int(os.environ.get("CONCURRENCY", os.environ.get("AB_CONCURRENCY", "4")))
    env_warm_cache = int(os.environ.get("WARM_CACHE", "0"))
    parser.add_argument("--sample", type=int, default=env_sample, help="Sample size per arm")
    parser.add_argument("--seed", type=int, default=env_seed, help="Seed for sampling queries")
    parser.add_argument("--concurrency", type=int, default=env_concurrency, help="Runner concurrency")
    parser.add_argument("--warm-cache", type=int, default=env_warm_cache, help="Warm cache limit before running")
    parser.add_argument("--repeats", type=int, default=int(os.environ.get("AB_REPEATS", "1")), help="Runner repeats")
    parser.add_argument("--base", type=str, default=os.environ.get("BASE") or os.environ.get("BANDIT_HEALTH_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--prefix", type=str, default=os.environ.get("AB_PREFIX", "AB"), help="Report filename prefix")
    parser.add_argument("--tag", type=str, help="Override run tag used for job notes and metrics directories")
    parser.add_argument("--print-md", action="store_true", help="Print markdown report path to stdout")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = args.base
    sample = args.sample
    seed = args.seed
    concurrency = args.concurrency
    warm_cache = args.warm_cache
    repeats = args.repeats

    print(f"[ALIGN] sample={sample} seed={seed} concurrency={concurrency} warm_cache={warm_cache}")

    policies = io_utils.read_json(io_utils.resolve_policies_path(), default={})
    if not isinstance(policies, Mapping) or "policies" not in policies:
        raise SystemExit("[ERROR] Unable to read policies.json")

    configs = policies["policies"]
    arms = ["fast_v1", "balanced_v1", "quality_v1"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_tag = args.tag or os.environ.get("RUN_TAG", f"ab-{timestamp}")
    os.environ["RUN_TAG"] = run_tag
    tag_suffix = f"_{run_tag}" if run_tag else ""
    prefix = args.prefix.rstrip("_")

    weight_spec = os.environ.get("REWARD_WEIGHTS", os.environ.get("WEIGHTS", "recall=1,latency=3,err=1,cost=0"))
    weight_overrides = reward.parse_weight_string(weight_spec)
    weights = reward.load_weights(weight_overrides)
    target_p95 = float(os.environ.get("TARGET_P95", "1000"))

    results: List[Dict[str, object]] = []
    for arm in arms:
        cfg = configs.get(arm)
        if not isinstance(cfg, Mapping):
            raise SystemExit(f"[ERROR] policies.json missing configuration for {arm}")
        print(f"==> APPLY {arm}")
        _apply_policy(base, arm)
        _assert_headers(base, cfg)
        metrics_path = _run_runner(
            f"{run_tag}-{arm}",
            cfg,
            sample,
            seed,
            concurrency,
            repeats,
            warm_cache,
            base,
        )
        metrics = _extract_metrics(metrics_path)
        if int(metrics["count"]) != sample:
            raise RuntimeError(f"[ERROR] metrics count mismatch for {arm}: got={metrics['count']} expected={sample}")
        reward_value = reward.compute_reward(
            {
                "recall": metrics["recall_at_10"],
                "p95_latency_ms": metrics["p95_ms"],
                "error_rate": metrics["error_rate"],
                "cost_per_query": metrics["cost_per_query"],
            },
            weights=weights,
            target_p95=target_p95,
        )
        metrics["reward"] = reward_value
        results.append(metrics)

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True, parents=True)
    csv_path = reports_dir / f"{prefix}_ALIGN_{timestamp}{tag_suffix}.csv"
    with csv_path.open("w", encoding="utf-8") as handle:
        handle.write("policy,p95_ms,recall_at_10,reward,metrics_path\n")
        for row in results:
            handle.write(
                f"{row['policy']},{row['p95_ms']:.3f},{row['recall_at_10']:.4f},{row['reward']:.4f},{row['path']}\n"
            )

    md_path = reports_dir / f"{prefix}_ALIGN_{timestamp}{tag_suffix}.md"
    md_lines = [
        "# Bandit A/B Fixed Sample Report",
        "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- base: {base}",
        f"- sample: {sample}",
        f"- seed: {seed}",
        f"- concurrency: {concurrency}",
        f"- warm_cache: {warm_cache}",
        f"- weights: {weight_spec}",
        f"- target_p95: {target_p95}",
        "",
        "| policy | p95_ms | recall_at_10 | reward | metrics_path |",
        "| --- | ---:| ---:| ---:| --- |",
    ]

    for row in sorted(results, key=lambda r: r["policy"]):
        md_lines.append(
            f"| {row['policy']} | {row['p95_ms']:.1f} | {row['recall_at_10']:.4f} | {row['reward']:.4f} | {row['path']} |"
        )

    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("policy,p95_ms,recall_at_10,reward,metrics_path")
    for row in sorted(results, key=lambda r: r["policy"]):
        print(
            f"{row['policy']},{row['p95_ms']:.1f},{row['recall_at_10']:.4f},{row['reward']:.4f},{row['path']}"
        )
    print(f"[AB] summary written to {csv_path}")
    print(f"[AB] report written to {md_path}")
    if args.print_md:
        print(md_path)


if __name__ == "__main__":
    main()

