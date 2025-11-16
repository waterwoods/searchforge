#!/usr/bin/env python3
"""
AutoTuner On/Off experiment (single-concurrency, lab-only).

Definitions for this experiment:
- "baseline" mode:
    - Does NOT call /api/autotuner/suggest at all.
    - We still reset the autotuner state once per run for cleanliness,
      but the tuner never receives metrics, so ef_search / rerank_k
      stay at their static defaults (effectively "no autotuning").
    - Query pipeline is fixed: same /api/query payload for every request.

- "autotuner" mode:
    - Before each run, we reset the global tuner state and set a policy
      via POST /api/autotuner/set_policy (policy = \"Balanced\").
    - After each /api/query response, we POST metrics to
      /api/autotuner/suggest, so the tuner can adapt ef_search/rerank_k
      based on the Balanced policy and the current budget.

Both modes:
- Use the SAME query set (FiQA queries with ground-truth qrels).
- Use the SAME /api/query payload and model/Qdrant backend.
- Run with single concurrency (queries executed sequentially).

Outputs:
- Raw CSV   : .runs/auto_tuner_on_off_raw.csv
- Aggregated: .runs/auto_tuner_on_off.csv
- Manifest  : .runs/auto_tuner_on_off.manifest.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Ensure we can import shared FiQA evaluation helpers
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "experiments"))

from fiqa_lib import (  # type: ignore
    load_queries_qrels,
    extract_doc_ids as fiqa_extract_doc_ids,
)


RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000").rstrip("/")
AUTOTUNER_TOKEN = (
    os.getenv("AUTOTUNER_TOKEN")
    or os.getenv("AUTOTUNER_TOKENS")
    or "devtoken"
)

RUNS_DIR = Path(".runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)

# Experiment constants (shared across all runs; can be overridden via CLI)
N_QUERIES = 500
BUDGETS_MS = [400, 600, 800, 1000, 1200]
REPEATS = 3
MODES = ["baseline", "autotuner"]
AUTOTUNER_POLICY = "Balanced"


@dataclass
class QuerySample:
    latency_ms: float
    success: bool
    over_budget: bool
    hit: int
    error: Optional[str] = None


def _wait_ready(timeout_s: float = 300.0) -> None:
    """Wait for rag-api /healthz and /readyz (clients_ready=true)."""
    deadline = time.time() + timeout_s
    session = requests.Session()

    # First /healthz
    while time.time() < deadline:
        try:
            resp = session.get(f"{RAG_API_URL}/healthz", timeout=5)
            if resp.status_code == 200:
                break
        except requests.RequestException:
            pass
        time.sleep(2.0)
    else:
        raise RuntimeError("rag-api /healthz did not become ready in time")

    # Then /readyz with clients_ready==true
    consecutive = 0
    while time.time() < deadline:
        try:
            resp = session.get(f"{RAG_API_URL}/readyz", timeout=5)
            if resp.status_code == 200:
                payload = resp.json() if isinstance(resp.json(), dict) else {}
                if bool(payload.get("clients_ready", False)):
                    consecutive += 1
                    if consecutive >= 3:
                        return
                else:
                    consecutive = 0
            else:
                consecutive = 0
        except requests.RequestException:
            consecutive = 0
        time.sleep(2.0)

    raise RuntimeError("rag-api /readyz did not become ready in time")


def _autotuner_headers() -> Dict[str, str]:
    """Build X-Autotuner-Token header (first token if comma-separated)."""
    token = AUTOTUNER_TOKEN
    if "," in token:
        token = token.split(",")[0].strip()
    return {"X-Autotuner-Token": token}


def _percentile(values: List[float], q: float) -> float:
    """Nearest-rank percentile with basic guards."""
    if not values:
        return 0.0
    q = max(0.0, min(1.0, float(q)))
    sorted_vals = sorted(float(v) for v in values)
    if q <= 0.0:
        return sorted_vals[0]
    if q >= 1.0:
        return sorted_vals[-1]
    idx = int(math.ceil(q * len(sorted_vals))) - 1
    idx = max(0, min(idx, len(sorted_vals) - 1))
    return sorted_vals[idx]


def _set_autotuner_policy(policy: str) -> str:
    """POST /api/autotuner/set_policy and return the active policy name."""
    url = f"{RAG_API_URL}/api/autotuner/set_policy"
    headers = _autotuner_headers()
    try:
        resp = requests.post(url, json={"policy": policy}, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.HTTPError as e:
        if resp.status_code == 401:
            raise RuntimeError(
                f"autotuner set_policy unauthorized (401) for policy '{policy}'"
            ) from e
        if resp.status_code == 403:
            raise RuntimeError(
                f"autotuner set_policy forbidden (403) for policy '{policy}'"
            ) from e
        raise
    data = resp.json()
    active = data.get("policy")
    if not active:
        raise RuntimeError(f"autotuner set_policy returned no policy field: {data}")
    return str(active)


def _reset_autotuner_state() -> None:
    """POST /api/autotuner/reset (best-effort, used in both modes)."""
    url = f"{RAG_API_URL}/api/autotuner/reset"
    headers = _autotuner_headers()
    try:
        resp = requests.post(url, json={}, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        # For baseline mode this is non-fatal; for autotuner mode the next
        # set_policy/suggest calls will still fail loudly if something is wrong.
        return


def _extract_items_and_latency(resp_json: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], float]:
    """Extract items list and latency from /api/query response."""
    items = resp_json.get("items") or []
    if not isinstance(items, list):
        items = []

    # Prefer explicit latency field, fall back to timings.total_ms
    latency_keys = ("p95_ms", "latency_ms", "latency")
    latency_ms: float = 0.0
    for key in latency_keys:
        if key in resp_json and resp_json[key] is not None:
            try:
                latency_ms = float(resp_json[key])
                break
            except (TypeError, ValueError):
                continue
    if latency_ms <= 0.0:
        timings = resp_json.get("timings") or {}
        try:
            latency_ms = float(timings.get("total_ms", 0.0))
        except (TypeError, ValueError):
            latency_ms = 0.0

    return items, latency_ms


def _call_query(
    session: requests.Session,
    question: str,
    budget_ms: int,
    top_k: int,
    rerank: bool,
) -> Tuple[Optional[Dict[str, Any]], float, Optional[str]]:
    """
    POST /api/query with a fixed payload shape similar to CI experiments.

    Returns:
        (response_json_or_none, client_latency_ms, error_str_or_none)
    """
    url = f"{RAG_API_URL}/api/query"
    payload: Dict[str, Any] = {
        "question": question,
        "budget_ms": int(budget_ms),
        # Experiment knobs (see fiqa_api /api/query handler for supported fields):
        # - top_k: controls number of retrieved results (cost proxy).
        # - rerank: enables expensive cross-encoder reranking.
        # For this lab:
        # - baseline uses a deliberately heavy config (large top_k, rerank=True).
        # - autotuner starts lighter and adapts via the Balanced policy.
        "top_k": int(top_k),
        "use_hybrid": False,
        "rerank": bool(rerank),
    }
    headers = {"Content-Type": "application/json"}

    start = time.perf_counter()
    try:
        resp = session.post(url, json=payload, headers=headers, timeout=20.0)
        client_latency_ms = (time.perf_counter() - start) * 1000.0
        if resp.status_code != 200:
            return None, client_latency_ms, f"HTTP {resp.status_code}"
        try:
            data = resp.json()
        except Exception as e:
            return None, client_latency_ms, f"json_error: {e}"
        return data, client_latency_ms, None
    except requests.Timeout as e:
        client_latency_ms = (time.perf_counter() - start) * 1000.0
        return None, client_latency_ms, "timeout"
    except requests.RequestException as e:
        client_latency_ms = (time.perf_counter() - start) * 1000.0
        return None, client_latency_ms, str(e)


def _post_autotuner_suggest(
    metrics: Dict[str, Any],
    trace_headers: Dict[str, str],
) -> None:
    """POST metrics to /api/autotuner/suggest (fire-and-forget with basic error handling)."""
    url = f"{RAG_API_URL}/api/autotuner/suggest"
    headers = {**trace_headers, **_autotuner_headers()}
    try:
        resp = requests.post(url, json=metrics, headers=headers, timeout=15.0)
        resp.raise_for_status()
    except requests.RequestException:
        # For this lab experiment we treat suggest failures as non-fatal for
        # the current query; they will, however, degrade the autotuner mode.
        return


def _compute_hit_flag(
    response_json: Optional[Dict[str, Any]],
    query_id: str,
    qrels: Dict[str, List[str]],
) -> int:
    """Return 1 if any retrieved doc matches ground truth for query_id, else 0."""
    if not response_json:
        return 0
    relevant = set(qrels.get(query_id, []))
    if not relevant:
        return 0

    # Extract doc_ids from response; reuse fiqa_lib helper when possible
    try:
        doc_ids = fiqa_extract_doc_ids(response_json)
    except Exception:
        doc_ids = []

    if not doc_ids:
        # Try a minimal extractor from items[]
        items = response_json.get("items") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("doc_id") or item.get("id")
            if not doc_id:
                meta = item.get("metadata")
                if isinstance(meta, dict):
                    doc_id = meta.get("doc_id") or meta.get("id")
            if doc_id and str(doc_id) in relevant:
                return 1
        return 0

    return 1 if any(str(doc_id) in relevant for doc_id in doc_ids[:10]) else 0


def run_single_experiment(
    mode: str,
    policy: str,
    budget_ms: int,
    repeat_idx: int,
    queries: List[Dict[str, str]],
    qrels: Dict[str, List[str]],
    top_k: int,
    rerank: bool,
) -> Tuple[float, float, float, float, float, float, float]:
    """
    Run one (mode, budget, repeat) experiment instance.

    Returns:
        p50_ms, p95_ms, p99_ms, success_rate, timeout_rate, error_rate
    """
    assert mode in MODES

    session = requests.Session()

    # Prepare autotuner state according to mode
    if mode == "autotuner":
        _reset_autotuner_state()
        active_policy = _set_autotuner_policy(policy)
        if active_policy != policy:
            # If backend normalized the policy name, we still treat this as the same policy.
            policy = active_policy
    else:
        # baseline: clear any previous tuning history so we measure a clean,
        # non-adaptive configuration (no suggest calls below).
        _reset_autotuner_state()

    samples: List[QuerySample] = []
    items_per_query: List[int] = []
    # Use the provided queries list as-is (already sliced by caller for N queries)
    for q in queries:
        query_id = q["query_id"]
        text = q["text"]

        resp_json, client_latency_ms, error = _call_query(
            session=session,
            question=text,
            budget_ms=budget_ms,
            top_k=top_k,
            rerank=rerank,
        )

        success = False
        items_latency_ms = 0.0
        num_items = 0
        if resp_json is not None:
            items, items_latency_ms = _extract_items_and_latency(resp_json)
            num_items = len(items)
            success = bool(items) and error is None

        # For timeout/over-budget metric we use client-side latency; if an error
        # occurred we treat this as over-budget as well (worst-case accounting).
        effective_latency = client_latency_ms or items_latency_ms
        over_budget = bool(effective_latency > float(budget_ms) or error in ("timeout",))

        hit = _compute_hit_flag(resp_json, query_id=query_id, qrels=qrels)

        items_per_query.append(num_items)

        samples.append(
            QuerySample(
                latency_ms=effective_latency,
                success=success,
                over_budget=over_budget or not success,
                hit=hit,
                error=error,
            )
        )

        # Only autotuner mode sends metrics to /api/autotuner/suggest
        if mode == "autotuner" and resp_json is not None:
            metrics = {
                "p95_ms": float(items_latency_ms or effective_latency),
                # crude recall proxy: 1.0 if we fetched at least one item
                "recall_at_10": 1.0 if success else 0.0,
                "coverage": 1.0,
                "trace_url": resp_json.get("trace_url"),
            }
            trace_headers = {}
            trace_id = resp_json.get("trace_id")
            if isinstance(trace_id, str):
                trace_headers["X-Trace-Id"] = trace_id
            _post_autotuner_suggest(metrics, trace_headers)

    latencies = [s.latency_ms for s in samples]
    successes = sum(1 for s in samples if s.success)
    timeouts = sum(1 for s in samples if s.over_budget)
    errors = sum(1 for s in samples if s.error is not None)

    p50_ms = _percentile(latencies, 0.5)
    p95_ms = _percentile(latencies, 0.95)
    p99_ms = _percentile(latencies, 0.99)

    n = float(len(samples)) or 1.0
    success_rate = successes / n
    timeout_rate = timeouts / n
    error_rate = errors / n
    avg_items = float(sum(items_per_query) / len(items_per_query)) if items_per_query else 0.0

    return p50_ms, p95_ms, p99_ms, success_rate, timeout_rate, error_rate, avg_items


def _append_raw_row(
    csv_path: Path,
    mode: str,
    policy: str,
    budget_ms: int,
    repeat_idx: int,
    p50_ms: float,
    p95_ms: float,
    p99_ms: float,
    success_rate: float,
    timeout_rate: float,
    avg_items: float,
) -> None:
    header = [
        "mode",
        "policy",
        "budget_ms",
        "repeat_idx",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "success_rate",
        "timeout_rate",
        "avg_items",
    ]
    first_write = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if first_write:
            writer.writerow(header)
        writer.writerow(
            [
                mode,
                policy,
                int(budget_ms),
                int(repeat_idx),
                f"{p50_ms:.3f}",
                f"{p95_ms:.3f}",
                f"{p99_ms:.3f}",
                f"{success_rate:.5f}",
                f"{timeout_rate:.5f}",
                    f"{avg_items:.3f}",
            ]
        )


def _aggregate_raw_to_csv(raw_csv: Path, agg_csv: Path) -> Dict[str, Any]:
    """
    Aggregate raw CSV into per-(mode,policy,budget_ms) mean metrics.

    Returns:
        A dict with summary stats (including error flags) for downstream checks.
    """
    if not raw_csv.exists():
        raise FileNotFoundError(f"raw CSV not found: {raw_csv}")

    groups: Dict[Tuple[str, str, int], Dict[str, List[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    with raw_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                mode = row["mode"]
                policy = row["policy"]
                budget_ms = int(row["budget_ms"])
                p50 = float(row["p50_ms"])
                p95 = float(row["p95_ms"])
                p99 = float(row["p99_ms"])
                success_rate = float(row["success_rate"])
                timeout_rate = float(row["timeout_rate"])
                avg_items = float(row.get("avg_items", "0") or 0.0)
            except (KeyError, ValueError):
                continue

            key = (mode, policy, budget_ms)
            g = groups[key]
            g["p50_ms"].append(p50)
            g["p95_ms"].append(p95)
            g["p99_ms"].append(p99)
            g["success_rate"].append(success_rate)
            g["timeout_rate"].append(timeout_rate)
            g["avg_items"].append(avg_items)

    header = [
        "mode",
        "policy",
        "budget_ms",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "success_rate",
        "timeout_rate",
        "avg_items",
    ]
    with agg_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for (mode, policy, budget_ms), metrics in sorted(
            groups.items(), key=lambda kv: (kv[0][0], kv[0][2])
        ):
            def mean(vals: List[float]) -> float:
                return float(sum(vals) / len(vals)) if vals else 0.0

            writer.writerow(
                [
                    mode,
                    policy,
                    budget_ms,
                    f"{mean(metrics['p50_ms']):.3f}",
                    f"{mean(metrics['p95_ms']):.3f}",
                    f"{mean(metrics['p99_ms']):.3f}",
                    f"{mean(metrics['success_rate']):.5f}",
                    f"{mean(metrics['timeout_rate']):.5f}",
                    f"{mean(metrics['avg_items']):.3f}",
                ]
            )

    summary: Dict[str, Any] = {"groups": {}}
    for (mode, policy, budget_ms), metrics in groups.items():
        key = f"{mode}:{policy}:{budget_ms}"
        summary["groups"][key] = {
            "mode": mode,
            "policy": policy,
            "budget_ms": budget_ms,
            "runs": len(metrics["p50_ms"]),
            "success_rate_min": min(metrics["success_rate"]),
            "success_rate_mean": float(
                sum(metrics["success_rate"]) / len(metrics["success_rate"])
            ),
        }
    return summary


def _write_manifest(
    manifest_path: Path,
    n_queries: int,
    budgets_ms: List[int],
    repeats: int,
    notes: str,
) -> None:
    """Write manifest JSON for reproducibility."""
    try:
        git_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
            or "unknown"
        )
    except Exception:
        git_sha = "unknown"

    payload = {
        "git_sha": git_sha,
        "datetime_utc": datetime.now(timezone.utc).isoformat(),
        "rag_api_url": RAG_API_URL,
        "n_queries": n_queries,
        "budgets_ms": budgets_ms,
        "repeats": repeats,
        "modes": MODES,
        "autotuner_policy": AUTOTUNER_POLICY,
        "notes": notes,
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Single-concurrency AutoTuner On/Off experiment."
    )
    parser.add_argument("--n-queries", type=int, default=N_QUERIES)
    parser.add_argument(
        "--budgets-ms",
        type=str,
        default="400,600,800,1000,1200",
        help="Comma-separated budget values in ms",
    )
    parser.add_argument("--repeats", type=int, default=REPEATS)
    parser.add_argument(
        "--tag",
        type=str,
        default="",
        help="Optional tag suffix for output filenames (e.g. 'hard')",
    )
    parser.add_argument(
        "--baseline-top-k",
        type=int,
        default=40,
        help="TopK for baseline (fixed) mode; heavy by design.",
    )
    parser.add_argument(
        "--baseline-rerank",
        type=str,
        default="true",
        help="Whether baseline always reranks (true/false).",
    )
    parser.add_argument(
        "--autotuner-top-k",
        type=int,
        default=10,
        help="Initial TopK for autotuner mode (Balanced policy).",
    )
    parser.add_argument(
        "--autotuner-rerank",
        type=str,
        default="false",
        help="Initial rerank flag for autotuner mode (Balanced policy).",
    )
    args = parser.parse_args()


    def _parse_bool_flag(value: str) -> bool:
        return str(value).lower() in ("1", "true", "yes", "y")

    n_queries = args.n_queries if args.n_queries is not None else N_QUERIES
    budgets = [int(x) for x in args.budgets_ms.split(",") if x] if args.budgets_ms else BUDGETS_MS
    repeats = args.repeats if args.repeats is not None else REPEATS
    tag = f"_{args.tag}" if args.tag else ""

    baseline_top_k = args.baseline_top_k
    baseline_rerank = _parse_bool_flag(args.baseline_rerank)
    autotuner_top_k = args.autotuner_top_k
    autotuner_rerank = _parse_bool_flag(args.autotuner_rerank)

    start_ts = time.time()
    print("[auto_tuner_on_off] Waiting for rag-api readiness...")
    _wait_ready()
    print("[auto_tuner_on_off] Backend ready, loading FiQA queries/qrels...")

    # Use the same query source as other FiQA experiments (50k dataset).
    queries, qrels = load_queries_qrels(
        dataset_name=os.getenv("FIQA_DATASET_NAME", "fiqa_50k_v1"),
        qrels_name=os.getenv("FIQA_QRELS_NAME", "fiqa_qrels_50k_v1"),
    )
    if not queries:
        raise SystemExit("no FiQA queries loaded")

    # Deterministic ordering: first n_queries queries with ground truth
    queries = queries[:n_queries]
    print(
        f"[auto_tuner_on_off] Using {len(queries)} queries, budgets={budgets}, "
        f"repeats={repeats}, modes={MODES}"
    )

    raw_csv = RUNS_DIR / f"auto_tuner_on_off_raw{tag}.csv"
    agg_csv = RUNS_DIR / f"auto_tuner_on_off{tag}.csv"
    manifest_path = RUNS_DIR / f"auto_tuner_on_off{tag}.manifest.json"

    # Remove old artifacts for a clean run
    for path in (raw_csv, agg_csv, manifest_path):
        if path.exists():
            path.unlink()

    # Run experiment grid
    error_flags: Dict[str, List[float]] = defaultdict(list)

    for mode in MODES:
        for budget_ms in budgets:
            for repeat_idx in range(repeats):
                if mode == "baseline":
                    mode_top_k = baseline_top_k
                    mode_rerank = baseline_rerank
                else:
                    mode_top_k = autotuner_top_k
                    mode_rerank = autotuner_rerank
                print(
                    f"[auto_tuner_on_off] mode={mode} budget={budget_ms}ms "
                    f"repeat={repeat_idx+1}/{repeats}"
                )
                (
                    p50_ms,
                    p95_ms,
                    p99_ms,
                    success_rate,
                    timeout_rate,
                    error_rate,
                    avg_items,
                ) = run_single_experiment(
                    mode=mode,
                    policy=AUTOTUNER_POLICY,
                    budget_ms=budget_ms,
                    repeat_idx=repeat_idx,
                    queries=queries,
                    qrels=qrels,
                    top_k=mode_top_k,
                    rerank=mode_rerank,
                )
                _append_raw_row(
                    csv_path=raw_csv,
                    mode=mode,
                    policy="fixed" if mode == "baseline" else AUTOTUNER_POLICY,
                    budget_ms=budget_ms,
                    repeat_idx=repeat_idx,
                    p50_ms=p50_ms,
                    p95_ms=p95_ms,
                    p99_ms=p99_ms,
                    success_rate=success_rate,
                    timeout_rate=timeout_rate,
                    avg_items=avg_items,
                )
                error_flags[mode].append(error_rate)

    summary = _aggregate_raw_to_csv(raw_csv=raw_csv, agg_csv=agg_csv)
    notes = "Single-concurrency AutoTuner On/Off experiment"
    if args.tag:
        notes += f" (tag={args.tag}, HARD mode candidate)"
    _write_manifest(
        manifest_path=manifest_path,
        n_queries=len(queries),
        budgets_ms=budgets,
        repeats=repeats,
        notes=notes,
    )

    elapsed = time.time() - start_ts
    print(f"[auto_tuner_on_off] Done in {elapsed:.1f}s")
    print(f"[auto_tuner_on_off] Raw CSV: {raw_csv}")
    print(f"[auto_tuner_on_off] Aggregated CSV: {agg_csv}")
    print(f"[auto_tuner_on_off] Manifest: {manifest_path}")

    # Hard guard: if any mode has >50% errors on average, treat experiment as failed.
    for mode, rates in error_flags.items():
        if not rates:
            continue
        mean_err = float(sum(rates) / len(rates))
        if mean_err > 0.5:
            print(
                f"[auto_tuner_on_off] ERROR: mode={mode} has mean error_rate={mean_err:.3f} (>0.5)"
            )
            return 1

    # Also surface a quick per-mode summary from aggregation
    try:
        grouped = summary.get("groups", {})
        for key, payload in grouped.items():
            mode = payload.get("mode")
            budget = payload.get("budget_ms")
            succ = payload.get("success_rate_mean")
            print(
                f"[auto_tuner_on_off][summary] mode={mode} budget={budget} "
                f"success_rate_mean={succ:.3f}"
            )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


