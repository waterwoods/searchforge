#!/usr/bin/env python3
"""
Compare A/B replay and router canary metrics under aligned conditions and optionally freeze the best arm.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Sequence

import reward

BASE_DEFAULT = os.environ.get("BASE") or os.environ.get("BANDIT_HEALTH_BASE_URL", "http://localhost:8000")
STATE_DEFAULT = Path(os.environ.get("BANDIT_STATE", Path.home() / "data" / "searchforge" / "bandit" / "bandit_state.json"))
REPORTS_DIR = Path("reports")


def _latest(pattern: str) -> Path:
    candidates = sorted(REPORTS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"[ERROR] No files match {pattern}")
    return candidates[-1]


def _read_ab_csv(path: Path) -> Dict[str, Dict[str, float]]:
    rows: Dict[str, Dict[str, float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            policy = row["policy"]
            rows[policy] = {
                "p95": float(row.get("p95_ms", 0.0)),
                "recall": float(row.get("recall_at_10", 0.0)),
                "reward": float(row.get("reward", 0.0)),
                "metrics_path": row.get("metrics_path", ""),
            }
    return rows


def _parse_router_table(path: Path) -> Dict[str, Dict[str, object]]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or not stripped.startswith("|") or stripped.startswith("| ---"):
            continue
        parts = [part.strip() for part in stripped.split("|")[1:-1]]
        if parts and parts[0].lower() == "round":
            continue
        if len(parts) != 10:
            continue
        round_idx, arm, samples, p95, recall, err, reward_value, _, _, metrics = parts
        rows[arm] = {
            "round": int(round_idx),
            "samples": int(samples),
            "p95": float(p95),
            "recall": float(recall),
            "err": float(err),
            "reward": float(reward_value),
            "metrics_path": metrics,
        }
    return rows


def _collect_router_rows(paths: Sequence[Path]) -> Dict[str, Dict[str, object]]:
    collected: Dict[str, Dict[str, object]] = {}
    for path in sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True):
        table = _parse_router_table(path)
        for arm, data in table.items():
            if arm not in collected:
                data = dict(data)
                data["source"] = str(path)
                collected[arm] = data
    return collected


def _load_metrics(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _compute_reward_from_metrics(metrics: Mapping[str, object], weights: reward.RewardWeights, target_p95: float) -> float:
    return reward.compute_reward(
        {
            "recall": float(metrics.get("recall_at_10", metrics.get("recall", 0.0))),
            "p95_latency_ms": float(metrics.get("p95_ms", 0.0)),
            "error_rate": float(metrics.get("error_rate", 0.0)),
            "cost_per_query": float(metrics.get("cost_per_query", 0.0)),
        },
        weights=weights,
        target_p95=target_p95,
    )


def _post_json(url: str, payload: Mapping[str, object]) -> Mapping[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _fetch_policy(base: str) -> Mapping[str, object]:
    with urllib.request.urlopen(f"{base}/api/admin/policy/current", timeout=5) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _sample_headers(base: str, cfg: Mapping[str, object]) -> Dict[str, str]:
    payload = {
        "question": "bandit alignment verify",
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
        return {key.lower(): value for key, value in response.headers.items()}


@dataclass
class AlignmentRecord:
    arm: str
    p95_ab: float
    p95_router: float
    recall_ab: float
    recall_router: float
    delta_p95: float
    delta_recall: float
    ab_metrics_path: str
    router_metrics_path: str
    router_source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check alignment between fixed-sample A/B and router runs.")
    parser.add_argument("--ab-csv", type=Path, help="Path to AB alignment CSV")
    parser.add_argument("--ab", type=Path, dest="ab_csv", help="Alias for --ab-csv")
    parser.add_argument("--router-md", type=Path, nargs="+", help="Path(s) to router alignment markdown")
    parser.add_argument("--router", type=Path, nargs="+", dest="router_md", help="Alias for --router-md")
    parser.add_argument("--summary-json", type=Path, default=Path("reports/BANDIT_SUMMARY_LATEST.json"))
    parser.add_argument("--state", type=Path, default=STATE_DEFAULT)
    parser.add_argument("--weights", type=str, default=os.environ.get("REWARD_WEIGHTS", os.environ.get("WEIGHTS", "recall=1,latency=3,err=1,cost=0")))
    parser.add_argument("--target-p95", type=float, default=float(os.environ.get("TARGET_P95", "1000")))
    parser.add_argument("--p95-threshold", type=float, default=0.10)
    parser.add_argument("--tol-p95", type=float, dest="p95_threshold", help="Alias for --p95-threshold")
    parser.add_argument("--recall-threshold", type=float, default=0.02)
    parser.add_argument("--tol-recall", type=float, dest="recall_threshold", help="Alias for --recall-threshold")
    parser.add_argument("--base", type=str, default=BASE_DEFAULT)
    parser.add_argument("--dryrun-freeze", action="store_true", help="Skip applying the winning policy")
    parser.add_argument(
        "--freeze-if-aligned",
        action="store_true",
        default=None,
        help="Freeze the winning arm when aligned (default behaviour if unspecified)",
    )
    parser.add_argument("--output-prefix", type=str, default="ALIGN_AND_FREEZE")
    parser.add_argument("--sample", type=int, default=int(os.environ.get("SAMPLE", "200")))
    parser.add_argument("--seed", type=int, default=int(os.environ.get("SEED", "20251107")))
    parser.add_argument("--concurrency", type=int, default=int(os.environ.get("CONCURRENCY", "4")))
    parser.add_argument("--warm-cache", type=int, default=int(os.environ.get("WARM_CACHE", "0")))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    REPORTS_DIR.mkdir(exist_ok=True, parents=True)

    ab_csv = args.ab_csv or _latest("AB_ALIGN_*.csv")
    if args.router_md:
        router_paths = [Path(path) for path in args.router_md]
    else:
        align_paths = sorted(REPORTS_DIR.glob("BANDIT_ROUNDS_ALIGN_*.md"), key=lambda p: p.stat().st_mtime)
        router_paths = align_paths[-3:] if align_paths else [ _latest("BANDIT_ROUNDS_*.md") ]

    ab_rows = _read_ab_csv(ab_csv)
    router_rows = _collect_router_rows(router_paths)

    weight_overrides = reward.parse_weight_string(args.weights)
    weights = reward.load_weights(weight_overrides)

    records: list[AlignmentRecord] = []
    aligned = True
    max_p95_delta = (0.0, "")
    max_recall_delta = (0.0, "")

    for arm in ("fast_v1", "balanced_v1", "quality_v1"):
        ab = ab_rows.get(arm)
        router = router_rows.get(arm)
        if not ab or not router:
            raise SystemExit(f"[ERROR] Missing metrics for arm={arm}")

        ab_metrics = _load_metrics(Path(ab["metrics_path"]))
        router_metrics = _load_metrics(Path(router["metrics_path"]))

        if int(ab_metrics.get("metrics", {}).get("count", 0)) != args.sample:
            raise RuntimeError(f"[ERROR] AB metrics count mismatch for arm={arm}")
        if int(router_metrics.get("metrics", {}).get("count", 0)) != args.sample:
            raise RuntimeError(f"[ERROR] Router metrics count mismatch for arm={arm}")

        delta_p95 = abs(router["p95"] - ab["p95"]) / ab["p95"] if ab["p95"] > 1e-9 else float("inf")
        delta_recall = abs(router["recall"] - ab["recall"])

        if delta_p95 > max_p95_delta[0]:
            max_p95_delta = (delta_p95, arm)
        if delta_recall > max_recall_delta[0]:
            max_recall_delta = (delta_recall, arm)

        if delta_p95 > args.p95_threshold or delta_recall > args.recall_threshold:
            aligned = False

        records.append(
            AlignmentRecord(
                arm=arm,
                p95_ab=ab["p95"],
                p95_router=router["p95"],
                recall_ab=ab["recall"],
                recall_router=router["recall"],
                delta_p95=delta_p95,
                delta_recall=delta_recall,
                ab_metrics_path=ab["metrics_path"],
                router_metrics_path=router["metrics_path"],
                router_source=str(router.get("source", router["metrics_path"])),
            )
        )

    output_prefix = args.output_prefix.rstrip("_") or "ALIGN_AND_FREEZE"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_path = REPORTS_DIR / f"{output_prefix}_{timestamp}.md"

    lines: list[str] = [
        "# Alignment & Freeze Report",
        "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- ab_csv: {ab_csv}",
        f"- router_md: {', '.join(str(p) for p in router_paths)}",
        f"- weights: {args.weights}",
        f"- target_p95: {args.target_p95}",
        f"- thresholds: Δp95≤{args.p95_threshold:.2f} Δrecall≤{args.recall_threshold:.2f}",
        "",
        "| arm | p95_ab | p95_router | Δp95 | recall_ab | recall_router | Δrecall | ab_metrics | router_metrics |",
        "| --- | ---:| ---:| ---:| ---:| ---:| ---:| --- | --- |",
    ]

    for rec in records:
        router_entry = rec.router_metrics_path
        if rec.router_source and rec.router_source != rec.router_metrics_path:
            router_entry = f"{rec.router_metrics_path} ({rec.router_source})"
        lines.append(
            "| {arm} | {p95_ab:.1f} | {p95_router:.1f} | {delta_p95:.3f} | {recall_ab:.4f} | {recall_router:.4f} | {delta_recall:.4f} | {ab_path} | {router_path} |".format(
                arm=rec.arm,
                p95_ab=rec.p95_ab,
                p95_router=rec.p95_router,
                delta_p95=rec.delta_p95,
                recall_ab=rec.recall_ab,
                recall_router=rec.recall_router,
                delta_recall=rec.delta_recall,
                ab_path=rec.ab_metrics_path,
                router_path=router_entry,
            )
        )

    status = "ALIGNED" if aligned else "DRIFT"
    lines.append("")
    lines.append(f"**Conclusion:** {status}")

    if not aligned:
        lines.append("")
        lines.append("### Diagnostic Suggestions")
        lines.append(f"- 最大 Δp95 = {max_p95_delta[0]:.3f} (arm={max_p95_delta[1]}); 考虑统一 warm_cache/concurrency 再复测。")
        lines.append(f"- 最大 Δrecall = {max_recall_delta[0]:.4f} (arm={max_recall_delta[1]}); 检查 replay 与实时策略的一致性。")
        lines.append("- 建议：使用相同的预热流程 (POST /api/admin/warmup) 后再次执行 router 对照；必要时固定 ef_search 或 concurrency。")
        lines.append("")
        lines.append("_status: needs_investigation_")
        diagnosis_only = True
    else:
        diagnosis_only = False

    freeze_winner: Optional[str] = None
    freeze_payload: Optional[Mapping[str, object]] = None
    header_snapshot: Optional[Dict[str, str]] = None

    freeze_requested = True if args.freeze_if_aligned is None else bool(args.freeze_if_aligned)
    freeze_allowed = aligned and freeze_requested and not args.dryrun_freeze

    if aligned:
        ab_csv_rows = _read_ab_csv(ab_csv)
        rewards = {}
        for arm, row in ab_csv_rows.items():
            rewards[arm] = _compute_reward_from_metrics(
                _load_metrics(Path(row["metrics_path"])).get("metrics", {}),
                weights,
                args.target_p95,
            )
        freeze_winner = max(rewards.items(), key=lambda kv: kv[1])[0]
        lines.append("")
        lines.append(f"### Freeze Decision")
        lines.append(f"- winner: `{freeze_winner}` (reward={rewards[freeze_winner]:.4f})")

        if not freeze_allowed:
            lines.append("- freeze: DRYRUN (skipped)")
        else:
            apply_cmd = [
                sys.executable,
                "scripts/bandit/apply.py",
                "--arm",
                freeze_winner,
                "--base",
                args.base,
                "--print-json",
            ]
            print(f"[BANDIT_FREEZE] applying {freeze_winner}")
            freeze_proc = subprocess.run(apply_cmd, capture_output=True, text=True)
            if freeze_proc.returncode != 0:
                raise RuntimeError(f"apply.py failed: {freeze_proc.stderr or freeze_proc.stdout}")
            stdout = (freeze_proc.stdout or "").strip()
            freeze_payload = None
            for line in reversed(stdout.splitlines()):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        freeze_payload = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
            if freeze_payload is None:
                freeze_payload = {"raw": stdout}
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(freeze_payload, indent=2, ensure_ascii=False))
            lines.append("```")

            policy_info = _fetch_policy(args.base)
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(policy_info, indent=2, ensure_ascii=False))
            lines.append("```")

            cfg = _load_metrics(Path(ab_csv_rows[freeze_winner]["metrics_path"])).get("config", {})
            header_snapshot = _sample_headers(args.base, cfg if isinstance(cfg, Mapping) else {})
            lines.append("")
            lines.append("```")
            for key in ("x-collection", "x-mmr", "x-mmr-lambda"):
                if header_snapshot and key in header_snapshot:
                    lines.append(f"{key}: {header_snapshot[key]}")
            lines.append("```")

    state_data = _load_metrics(args.state)
    lines.append("")
    lines.append("### Bandit State Snapshot")
    lines.append("arm\tn\tavg_reward\tlast_p95\tlast_recall")
    for arm in ("fast_v1", "balanced_v1", "quality_v1"):
        entry = state_data.get(arm, {})
        last = entry.get("last_metrics") or {}
        lines.append(
            f"{arm}\t{entry.get('counts')}\t{entry.get('avg_reward')}\t"
            f"{last.get('p95_ms')}\t{last.get('recall_at_10')}"
        )

    lines.append("")
    lines.append("### Parameter Snapshot")
    lines.append(
        f"- sample: {args.sample} | seed: {args.seed} | concurrency: {args.concurrency} | warm_cache: {args.warm_cache}"
    )
    lines.append(f"- weights: {args.weights} | target_p95: {args.target_p95}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_path)
    print(f"[ALIGNMENT] status={status}")
    if freeze_winner and freeze_allowed:
        print(f"[BANDIT_FREEZE] winner={freeze_winner}")

    exit_code = 0
    if status != "ALIGNED":
        exit_code = 2
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

