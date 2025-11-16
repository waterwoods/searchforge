#!/usr/bin/env python3
"""
Go Proxy On/Off Concurrency/QPS Experiment.

Compares:
  - baseline: client → rag-api (/api/query) → GPU → Qdrant
  - proxy   : client → retrieval-proxy (/v1/search) → Qdrant (proxy may bypass GPU)

For each (mode, concurrency):
  - Sends N_REQUESTS_PER_RUN logical requests (overlapped at higher concurrency).
  - Measures p50/p95/p99 latency, QPS, error_rate, timeout_rate.

Outputs:
  - Raw CSV      : .runs/go_proxy_on_off_raw.csv
  - Aggregated   : .runs/go_proxy_on_off.csv
  - Manifest JSON: .runs/go_proxy_on_off.manifest.json
"""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import queue
import threading

try:
    import requests
except ImportError:
    print("ERROR: Missing dependency: requests. Install with: pip install requests")
    sys.exit(1)


# Base URLs (env-overridable)
RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000").rstrip("/")
# For the Go proxy, prefer explicit RETRIEVAL_PROXY_URL, then PROXY_URL, then the
# default host mapping from docker-compose (7070).
RETRIEVAL_PROXY_URL = (
    os.getenv("RETRIEVAL_PROXY_URL")
    or os.getenv("PROXY_URL")
    or "http://localhost:7070"
)
RETRIEVAL_PROXY_URL = RETRIEVAL_PROXY_URL.rstrip("/")

RUNS_DIR = Path(".runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)


# Experiment constants
MODES: List[str] = ["baseline", "proxy"]
CONCURRENCIES: List[int] = [1, 4, 8, 16, 32]
N_REQUESTS_PER_RUN: int = 200
REPEATS: int = 3
BUDGET_MS: int = 70
TIMEOUT_SEC: float = 2.0


# Simple fixed FIQA-style question list (cycled as needed)
QUESTIONS: List[str] = [
    "what is ETF?",
    "how do index funds work?",
    "what is the difference between stocks and bonds?",
    "how does compound interest work?",
    "what is a mutual fund?",
    "how can I diversify my portfolio?",
    "what is risk tolerance in investing?",
    "how do dividend payments work?",
    "what are exchange-traded funds?",
    "what is an options contract?",
    "how does dollar-cost averaging work?",
    "what is market volatility?",
    "how do interest rates affect stock prices?",
    "what is portfolio rebalancing?",
    "how do I start investing with a small amount of money?",
    "what is an expense ratio?",
    "how do capital gains taxes work on investments?",
    "what is the difference between active and passive investing?",
    "how do credit scores impact loan interest rates?",
    "what is inflation and how does it affect savings?",
]


@dataclass
class Sample:
    latency_ms: float
    success: bool
    timeout: bool
    error: Optional[str]


def _do_request_baseline(session: requests.Session, question: str) -> Tuple[Optional[Sample], Optional[str]]:
    """
    POST to rag-api /api/query with a fixed payload shape.
    This path exercises: client → rag-api → GPU worker → Qdrant.
    """
    url = f"{RAG_API_URL}/api/query"
    payload: Dict[str, Any] = {
        "question": question,
        "budget_ms": BUDGET_MS,
        "top_k": 10,
        "rerank": False,
        "use_hybrid": False,
    }
    headers = {"Content-Type": "application/json"}

    start = time.perf_counter()
    try:
        resp = session.post(url, json=payload, headers=headers, timeout=TIMEOUT_SEC)
        latency_ms = (time.perf_counter() - start) * 1000.0
    except requests.Timeout:
        latency_ms = (time.perf_counter() - start) * 1000.0
        sample = Sample(latency_ms=latency_ms, success=False, timeout=True, error="timeout")
        return sample, "timeout"
    except requests.RequestException as exc:
        latency_ms = (time.perf_counter() - start) * 1000.0
        err_str = f"request_error: {exc}"
        sample = Sample(latency_ms=latency_ms, success=False, timeout=False, error=err_str)
        return sample, err_str

    if resp.status_code != 200:
        err_str = f"HTTP {resp.status_code}"
        sample = Sample(latency_ms=latency_ms, success=False, timeout=False, error=err_str)
        return sample, err_str

    try:
        data = resp.json()
    except Exception as exc:  # pragma: no cover - defensive
        err_str = f"json_error: {exc}"
        sample = Sample(latency_ms=latency_ms, success=False, timeout=False, error=err_str)
        return sample, err_str

    # Treat any 200 + parseable body as success for this throughput/latency lab
    sample = Sample(latency_ms=latency_ms, success=True, timeout=False, error=None)
    return sample, None


def _do_request_proxy(session: requests.Session, question: str) -> Tuple[Optional[Sample], Optional[str]]:
    """
    GET retrieval-proxy /v1/search with equivalent logical query/budget.

    Note: As of this lab, the Go proxy may directly query Qdrant without GPU;
    this is acceptable – the focus here is concurrency and QPS behavior.
    """
    url = f"{RETRIEVAL_PROXY_URL}/v1/search"
    params = {
        "q": question,
        "k": 10,
        "budget_ms": BUDGET_MS,
    }

    start = time.perf_counter()
    try:
        resp = session.get(url, params=params, timeout=TIMEOUT_SEC)
        latency_ms = (time.perf_counter() - start) * 1000.0
    except requests.Timeout:
        latency_ms = (time.perf_counter() - start) * 1000.0
        sample = Sample(latency_ms=latency_ms, success=False, timeout=True, error="timeout")
        return sample, "timeout"
    except requests.RequestException as exc:
        latency_ms = (time.perf_counter() - start) * 1000.0
        err_str = f"request_error: {exc}"
        sample = Sample(latency_ms=latency_ms, success=False, timeout=False, error=err_str)
        return sample, err_str

    if resp.status_code != 200:
        err_str = f"HTTP {resp.status_code}"
        sample = Sample(latency_ms=latency_ms, success=False, timeout=False, error=err_str)
        return sample, err_str

    try:
        _ = resp.json()
    except Exception as exc:  # pragma: no cover - defensive
        err_str = f"json_error: {exc}"
        sample = Sample(latency_ms=latency_ms, success=False, timeout=False, error=err_str)
        return sample, err_str

    sample = Sample(latency_ms=latency_ms, success=True, timeout=False, error=None)
    return sample, None


def run_one_mode_concurrency(
    mode: str,
    concurrency: int,
    n_requests: int,
    questions: List[str],
) -> Tuple[List[Sample], float]:
    """
    Run a single (mode, concurrency) experiment instance using a thread pool.
    Returns:
        (samples, wall_clock_seconds)
    """
    assert mode in MODES

    samples: List[Sample] = []
    errors: List[str] = []
    samples_lock = threading.Lock()
    errors_lock = threading.Lock()

    work_q: "queue.Queue[Optional[str]]" = queue.Queue()
    for i in range(n_requests):
        q_text = questions[i % len(questions)]
        work_q.put(q_text)
    for _ in range(concurrency):
        work_q.put(None)  # Sentinel

    def worker() -> None:
        with requests.Session() as session:
            while True:
                q_text = work_q.get()
                if q_text is None:
                    break
                if mode == "baseline":
                    sample, err = _do_request_baseline(session, q_text)
                else:
                    sample, err = _do_request_proxy(session, q_text)
                if sample is not None:
                    with samples_lock:
                        samples.append(sample)
                if err:
                    with errors_lock:
                        errors.append(err)

    threads: List[threading.Thread] = []
    start = time.perf_counter()
    for _ in range(concurrency):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    end = time.perf_counter()

    wall_s = end - start
    return samples, wall_s


def summarize_samples(samples: List[Sample], wall_s: float) -> Dict[str, float]:
    if not samples:
        return {
            "p50_ms": math.nan,
            "p95_ms": math.nan,
            "p99_ms": math.nan,
            "qps": 0.0,
            "error_rate": 1.0,
            "timeout_rate": 1.0,
        }

    latencies = [s.latency_ms for s in samples if s.success]
    if not latencies:
        latencies = [s.latency_ms for s in samples]

    lat_sorted = sorted(latencies)

    def pct(p: float) -> float:
        # nearest-rank percentile
        if not lat_sorted:
            return math.nan
        p = max(0.0, min(1.0, float(p)))
        if p <= 0.0:
            return float(lat_sorted[0])
        if p >= 1.0:
            return float(lat_sorted[-1])
        idx = int(math.ceil(p * len(lat_sorted))) - 1
        idx = max(0, min(idx, len(lat_sorted) - 1))
        return float(lat_sorted[idx])

    p50 = statistics.median(lat_sorted)
    p95 = pct(0.95)
    p99 = pct(0.99)

    n = len(samples)
    error_rate = sum(1 for s in samples if not s.success and not s.timeout) / float(n)
    timeout_rate = sum(1 for s in samples if s.timeout) / float(n)
    qps = float(len(samples)) / wall_s if wall_s > 0 else 0.0

    return {
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "qps": qps,
        "error_rate": error_rate,
        "timeout_rate": timeout_rate,
    }


def _append_raw_row(
    csv_path: Path,
    mode: str,
    concurrency: int,
    run_idx: int,
    req_count: int,
    wall_s: float,
    metrics: Dict[str, float],
) -> None:
    header = [
        "mode",
        "concurrency",
        "run_idx",
        "req_count",
        "wall_s",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "qps",
        "error_rate",
        "timeout_rate",
    ]
    first_write = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if first_write:
            writer.writerow(header)
        writer.writerow(
            [
                mode,
                int(concurrency),
                int(run_idx),
                int(req_count),
                f"{wall_s:.6f}",
                f"{metrics['p50_ms']:.3f}",
                f"{metrics['p95_ms']:.3f}",
                f"{metrics['p99_ms']:.3f}",
                f"{metrics['qps']:.3f}",
                f"{metrics['error_rate']:.5f}",
                f"{metrics['timeout_rate']:.5f}",
            ]
        )


def _aggregate_raw_to_csv(raw_csv: Path, agg_csv: Path) -> None:
    """
    Aggregate raw CSV into per-(mode, concurrency) mean metrics over REPEATS.
    """
    if not raw_csv.exists():
        raise FileNotFoundError(f"raw CSV not found: {raw_csv}")

    groups: Dict[Tuple[str, int], Dict[str, List[float]]] = {}

    with raw_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                mode = row["mode"]
                concurrency = int(row["concurrency"])
                p50 = float(row["p50_ms"])
                p95 = float(row["p95_ms"])
                p99 = float(row["p99_ms"])
                qps = float(row["qps"])
                err = float(row["error_rate"])
                to = float(row["timeout_rate"])
            except (KeyError, ValueError):
                continue

            key = (mode, concurrency)
            if key not in groups:
                groups[key] = {
                    "p50_ms": [],
                    "p95_ms": [],
                    "p99_ms": [],
                    "qps": [],
                    "error_rate": [],
                    "timeout_rate": [],
                }
            g = groups[key]
            g["p50_ms"].append(p50)
            g["p95_ms"].append(p95)
            g["p99_ms"].append(p99)
            g["qps"].append(qps)
            g["error_rate"].append(err)
            g["timeout_rate"].append(to)

    header = [
        "mode",
        "concurrency",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "qps",
        "error_rate",
        "timeout_rate",
    ]
    with agg_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for (mode, concurrency), metrics in sorted(
            groups.items(), key=lambda kv: (kv[0][0], kv[0][1])
        ):

            def mean(vals: List[float]) -> float:
                return float(sum(vals) / len(vals)) if vals else 0.0

            writer.writerow(
                [
                    mode,
                    concurrency,
                    f"{mean(metrics['p50_ms']):.3f}",
                    f"{mean(metrics['p95_ms']):.3f}",
                    f"{mean(metrics['p99_ms']):.3f}",
                    f"{mean(metrics['qps']):.3f}",
                    f"{mean(metrics['error_rate']):.5f}",
                    f"{mean(metrics['timeout_rate']):.5f}",
                ]
            )


def _write_manifest(manifest_path: Path) -> None:
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
        "retrieval_proxy_url": RETRIEVAL_PROXY_URL,
        "modes": MODES,
        "concurrencies": CONCURRENCIES,
        "n_requests_per_run": N_REQUESTS_PER_RUN,
        "repeats": REPEATS,
        "budget_ms": BUDGET_MS,
        "timeout_sec": TIMEOUT_SEC,
        "notes": "Concurrency & QPS experiment: rag-api vs Go retrieval proxy, no autotuner.",
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    raw_csv = RUNS_DIR / "go_proxy_on_off_raw.csv"
    agg_csv = RUNS_DIR / "go_proxy_on_off.csv"
    manifest_path = RUNS_DIR / "go_proxy_on_off.manifest.json"

    # Clean previous artifacts
    for path in (raw_csv, agg_csv, manifest_path):
        if path.exists():
            path.unlink()

    total_start = time.time()
    print(
        f"[go_proxy_on_off] Starting experiment with modes={MODES}, "
        f"concurrencies={CONCURRENCIES}, n_requests_per_run={N_REQUESTS_PER_RUN}, "
        f"repeats={REPEATS}, budget_ms={BUDGET_MS}, timeout_sec={TIMEOUT_SEC}"
    )
    print(f"[go_proxy_on_off] RAG_API_URL={RAG_API_URL} RETRIEVAL_PROXY_URL={RETRIEVAL_PROXY_URL}")

    for mode in MODES:
        for concurrency in CONCURRENCIES:
            for run_idx in range(REPEATS):
                print(
                    f"[go_proxy_on_off] mode={mode} concurrency={concurrency} "
                    f"run={run_idx + 1}/{REPEATS}"
                )
                samples, wall_s = run_one_mode_concurrency(
                    mode=mode,
                    concurrency=concurrency,
                    n_requests=N_REQUESTS_PER_RUN,
                    questions=QUESTIONS,
                )
                metrics = summarize_samples(samples, wall_s)
                _append_raw_row(
                    csv_path=raw_csv,
                    mode=mode,
                    concurrency=concurrency,
                    run_idx=run_idx,
                    req_count=len(samples),
                    wall_s=wall_s,
                    metrics=metrics,
                )

    _aggregate_raw_to_csv(raw_csv=raw_csv, agg_csv=agg_csv)
    _write_manifest(manifest_path=manifest_path)

    elapsed = time.time() - total_start
    print(f"[go_proxy_on_off] Done in {elapsed:.1f}s")
    print(f"[go_proxy_on_off] Raw CSV: {raw_csv}")
    print(f"[go_proxy_on_off] Aggregated CSV: {agg_csv}")
    print(f"[go_proxy_on_off] Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


