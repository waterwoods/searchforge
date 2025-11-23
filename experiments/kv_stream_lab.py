#!/usr/bin/env python3
"""
KV-cache / Streaming 实验模块

这个脚本用于评测 KV-cache 和 Streaming 对 RAG 系统性能的影响。

Modes:
- baseline: use_kv_cache=False, stream=False
- kv_only: use_kv_cache=True, stream=False
- stream_only: use_kv_cache=False, stream=True
- kv_and_stream: use_kv_cache=True, stream=True
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# Ensure we can import shared FiQA helpers
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "experiments"))

from fiqa_lib import (  # type: ignore
    load_queries_qrels,
    extract_total_tokens,
)

RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000").rstrip("/")

# FIQA collection name for /api/query
FIQA_COLLECTION = os.getenv("FIQA_COLLECTION", "fiqa_para_50k")

# Mode configurations
MODES = {
    "baseline": dict(use_kv_cache=False, stream=False),
    "kv_only": dict(use_kv_cache=True, stream=False),
    "stream_only": dict(use_kv_cache=False, stream=True),
    "kv_and_stream": dict(use_kv_cache=True, stream=True),
}

# Fixed experiment parameters (to prevent "fake fast" results)
EXPERIMENT_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 512,
}


def _percentile(values: List[float], q: float) -> float:
    """Nearest-rank percentile with simple guards."""
    if not values:
        return 0.0
    q = max(0.0, min(1.0, float(q)))
    vals = sorted(float(v) for v in values)
    if q <= 0.0:
        return vals[0]
    if q >= 1.0:
        return vals[-1]
    idx = int((len(vals) * q + 0.999999)) - 1
    idx = max(0, min(idx, len(vals) - 1))
    return vals[idx]


@dataclass
class RequestMetrics:
    """Single request metrics."""
    latency_ms: float
    first_token_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    kv_enabled: bool
    kv_hit: bool
    stream_enabled: bool
    stream_error: bool
    error: Optional[str] = None


def _call_query(
    session: requests.Session,
    question: str,
    *,
    use_kv_cache: bool = False,
    session_id: Optional[str] = None,
    stream: bool = False,
    top_k: int = 10,
    collection: Optional[str] = None,
    timeout: float = 20.0,
) -> Tuple[Optional[Dict[str, Any]], RequestMetrics]:
    """
    Call /api/query endpoint with KV-cache and streaming options.

    Returns:
        (response_json_or_none, RequestMetrics)
    """
    url = f"{RAG_API_URL}/api/query"
    payload: Dict[str, Any] = {
        "question": question,
        "top_k": int(top_k),
        "use_hybrid": False,
        "rerank": False,
        "collection": collection or FIQA_COLLECTION,
        "use_kv_cache": bool(use_kv_cache),
        "session_id": session_id,
        "stream": bool(stream),
        "generate_answer": True,  # Explicitly enable LLM generation for experiments
    }
    headers = {"Content-Type": "application/json"}

    start_time = time.perf_counter()
    first_token_time: Optional[float] = None
    stream_error = False
    error: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None

    try:
        if stream:
            # Streaming request
            resp = session.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
                stream=True,
            )
            if resp.status_code != 200:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                error = f"HTTP {resp.status_code}"
                metrics = RequestMetrics(
                    latency_ms=latency_ms,
                    first_token_ms=latency_ms,  # Fallback: same as latency
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    kv_enabled=use_kv_cache,
                    kv_hit=False,
                    stream_enabled=True,
                    stream_error=True,
                    error=error,
                )
                return None, metrics

            # Read streaming response using SSE format
            # Format: "data: {payload}\n\n" ... "data: [DONE]\n\n"
            chunks = []
            try:
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    
                    # Parse SSE format: "data: {payload}"
                    if line.startswith("data: "):
                        payload = line[6:].strip()  # Remove "data: " prefix
                        
                        # Record first token time
                        if first_token_time is None and payload and payload != "[DONE]":
                            first_token_time = time.perf_counter()
                        
                        # Check for done marker
                        if payload == "[DONE]":
                            break
                        
                        # Accumulate payload (could be text chunk or JSON)
                        if payload:
                            chunks.append(payload)
            except Exception as e:
                stream_error = True
                error = f"stream_parse_error: {str(e)}"
                logger.warning(f"Stream parsing error: {e}")

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            first_token_ms = (
                (first_token_time - start_time) * 1000.0
                if first_token_time
                else latency_ms
            )

            # For streaming, we don't get structured JSON response
            # Create a minimal response structure with accumulated text
            full_text = "".join(chunks)
            response_data = {"answer": full_text}
        else:
            # Non-streaming request
            resp = session.post(url, json=payload, headers=headers, timeout=timeout)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            if resp.status_code != 200:
                error = f"HTTP {resp.status_code}"
                metrics = RequestMetrics(
                    latency_ms=latency_ms,
                    first_token_ms=latency_ms,  # For non-streaming, same as latency
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    kv_enabled=use_kv_cache,
                    kv_hit=False,
                    stream_enabled=False,
                    stream_error=False,
                    error=error,
                )
                return None, metrics

            try:
                response_data = resp.json()
            except Exception as exc:
                error = f"json_error: {exc}"
                metrics = RequestMetrics(
                    latency_ms=latency_ms,
                    first_token_ms=latency_ms,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    cost_usd=0.0,
                    kv_enabled=use_kv_cache,
                    kv_hit=False,
                    stream_enabled=False,
                    stream_error=False,
                    error=error,
                )
                return None, metrics

            # For non-streaming, first_token_ms equals latency_ms
            first_token_ms = latency_ms

    except requests.Timeout:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        error = "timeout"
        metrics = RequestMetrics(
            latency_ms=latency_ms,
            first_token_ms=latency_ms,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0.0,
            kv_enabled=use_kv_cache,
            kv_hit=False,
            stream_enabled=stream,
            stream_error=True if stream else False,
            error=error,
        )
        return None, metrics
    except requests.RequestException as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        error = str(exc)
        metrics = RequestMetrics(
            latency_ms=latency_ms,
            first_token_ms=latency_ms,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0.0,
            kv_enabled=use_kv_cache,
            kv_hit=False,
            stream_enabled=stream,
            stream_error=True if stream else False,
            error=error,
        )
        return None, metrics

    # Extract tokens and KV metrics from response
    total_tokens = extract_total_tokens(response_data) if response_data else 0
    # Extract input_tokens and output_tokens from metrics if available
    metrics_data = response_data.get("metrics", {}) if response_data else {}
    llm_usage = metrics_data.get("llm_usage", {})
    input_tokens = llm_usage.get("prompt_tokens", 0) if llm_usage else 0
    output_tokens = llm_usage.get("completion_tokens", 0) if llm_usage else 0
    if total_tokens == 0 and input_tokens + output_tokens > 0:
        total_tokens = input_tokens + output_tokens
    
    # Extract KV metrics
    kv_enabled_actual = metrics_data.get("kv_enabled", use_kv_cache)
    kv_hit = metrics_data.get("kv_hit", False)

    # Calculate cost from usage if available, otherwise estimate
    cost_usd = 0.0
    if llm_usage and "cost_usd_est" in llm_usage:
        cost_usd_est_val = llm_usage.get("cost_usd_est")
        if cost_usd_est_val is not None:
            cost_usd = float(cost_usd_est_val)
    elif total_tokens > 0:
        # Fallback: estimate cost
        price_per_1k = float(os.getenv("MODEL_PRICE_PER_1K", "0.002"))
        cost_usd = (total_tokens / 1000.0) * price_per_1k

    metrics = RequestMetrics(
        latency_ms=latency_ms,
        first_token_ms=first_token_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        kv_enabled=kv_enabled_actual,
        kv_hit=kv_hit,
        stream_enabled=stream,
        stream_error=stream_error,
        error=None,
    )

    return response_data, metrics


def run_experiment(
    mode: str,
    queries: List[Dict[str, str]],
    concurrency: int = 16,
    warmup: int = 20,
    turns_per_session: int = 1,
) -> List[RequestMetrics]:
    """
    Run experiment for a given mode.

    Args:
        mode: One of "baseline", "kv_only", "stream_only", "kv_and_stream"
        queries: List of query dictionaries with "query_id" and "text"
        concurrency: Number of concurrent requests
        warmup: Number of warmup requests (not included in results)
        turns_per_session: Number of turns per session for KV-cache testing (default: 1)

    Returns:
        List of RequestMetrics for each query
    """
    if mode not in MODES:
        raise ValueError(f"Invalid mode: {mode}. Must be one of {list(MODES.keys())}")

    config = MODES[mode]
    use_kv_cache = config["use_kv_cache"]
    stream = config["stream"]

    session = requests.Session()
    results: List[RequestMetrics] = []

    # Warmup phase
    if warmup > 0:
        print(f"[{mode}] Warming up with {warmup} requests...")
        for i in range(warmup):
            query = queries[i % len(queries)]
            _, _ = _call_query(
                session=session,
                question=query["text"],
                use_kv_cache=use_kv_cache,
                session_id=None,  # No session for warmup
                stream=stream,
            )

    # Main experiment phase
    print(f"[{mode}] Running {len(queries)} queries with concurrency={concurrency}...")
    
    # For KV-cache modes, group queries into sessions
    if use_kv_cache and turns_per_session > 1:
        # Group queries into sessions: each session gets turns_per_session queries
        query_groups = []
        for i in range(0, len(queries), turns_per_session):
            group = queries[i:i + turns_per_session]
            query_groups.append((f"kv-lab-{i // turns_per_session}", group))
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for session_id, group_queries in query_groups:
                for turn_idx, q in enumerate(group_queries):
                    futures.append(executor.submit(
                        _call_query,
                        session=session,
                        question=q["text"],
                        use_kv_cache=use_kv_cache,
                        session_id=session_id,
                        stream=stream,
                    ))
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                _, metrics = future.result()
                results.append(metrics)
                
                if completed % 10 == 0:
                    print(f"  [{mode}] Completed {completed}/{len(queries)} queries")
    else:
        # Single-turn mode (no session grouping)
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(
                    _call_query,
                    session=session,
                    question=q["text"],
                    use_kv_cache=use_kv_cache,
                    session_id=None,  # No session for single-turn
                    stream=stream,
                ): q
                for q in queries
            }

            completed = 0
            for future in as_completed(futures):
                completed += 1
                _, metrics = future.result()
                results.append(metrics)

                if completed % 10 == 0:
                    print(f"  [{mode}] Completed {completed}/{len(queries)} queries")

    return results


@dataclass
class Summary:
    """Aggregated summary statistics."""
    mode: str
    num_queries: int
    p50_ms: float
    p95_ms: float
    p50_first_token_ms: float
    p95_first_token_ms: float
    avg_input_tokens: float
    avg_output_tokens: float
    avg_total_tokens: float
    avg_cost_usd: float
    stream_error_rate: float
    kv_enabled: bool
    kv_hit_rate: float
    stream_enabled: bool


def collect_stats(records: List[RequestMetrics]) -> Summary:
    """
    Aggregate metrics from request records.

    Args:
        records: List of RequestMetrics

    Returns:
        Summary with aggregated statistics
    """
    if not records:
        raise ValueError("No records to aggregate")

    mode = "unknown"
    kv_enabled = records[0].kv_enabled if records else False
    stream_enabled = records[0].stream_enabled if records else False

    latencies = [r.latency_ms for r in records]
    first_token_times = [r.first_token_ms for r in records]
    input_tokens = [r.input_tokens for r in records]
    output_tokens = [r.output_tokens for r in records]
    total_tokens = [r.total_tokens for r in records]
    costs = [r.cost_usd for r in records]

    stream_requests = [r for r in records if r.stream_enabled]
    stream_errors = sum(1 for r in stream_requests if r.stream_error)
    stream_error_rate = (
        (stream_errors / len(stream_requests)) if stream_requests else 0.0
    )
    
    # Calculate KV hit rate
    kv_enabled_requests = [r for r in records if r.kv_enabled]
    kv_hits = sum(1 for r in kv_enabled_requests if r.kv_hit)
    kv_hit_rate = (
        (kv_hits / len(kv_enabled_requests)) if kv_enabled_requests else 0.0
    )

    return Summary(
        mode=mode,
        num_queries=len(records),
        p50_ms=_percentile(latencies, 0.5),
        p95_ms=_percentile(latencies, 0.95),
        p50_first_token_ms=_percentile(first_token_times, 0.5),
        p95_first_token_ms=_percentile(first_token_times, 0.95),
        avg_input_tokens=sum(input_tokens) / len(input_tokens) if input_tokens else 0.0,
        avg_output_tokens=sum(output_tokens) / len(output_tokens) if output_tokens else 0.0,
        avg_total_tokens=sum(total_tokens) / len(total_tokens) if total_tokens else 0.0,
        avg_cost_usd=sum(costs) / len(costs) if costs else 0.0,
        stream_error_rate=stream_error_rate,
        kv_enabled=kv_enabled,
        kv_hit_rate=kv_hit_rate,
        stream_enabled=stream_enabled,
    )


def write_csv(output_path: Path, summaries: List[Summary]) -> None:
    """Write summary statistics to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "mode",
        "num_queries",
        "p50_ms",
        "p95_ms",
        "p50_first_token_ms",
        "p95_first_token_ms",
        "avg_total_tokens",
        "avg_cost_usd",
        "stream_error_rate",
        "kv_enabled",
        "kv_hit_rate",
        "stream_enabled",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            row = asdict(summary)
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def print_summary_table(summaries: List[Summary]) -> None:
    """Print a formatted summary table."""
    print("\n" + "=" * 100)
    print("Summary Statistics")
    print("=" * 100)
    print(
        f"{'Mode':<20} {'P50(ms)':<12} {'P95(ms)':<12} {'P50-FT(ms)':<14} {'P95-FT(ms)':<14} "
        f"{'Avg Tokens':<12} {'Avg Cost($)':<12} {'Stream Err%':<12} {'KV':<6} {'KV Hit%':<10} {'Stream':<8}"
    )
    print("-" * 110)

    for s in summaries:
        print(
            f"{s.mode:<20} {s.p50_ms:<12.1f} {s.p95_ms:<12.1f} {s.p50_first_token_ms:<14.1f} "
            f"{s.p95_first_token_ms:<14.1f} {s.avg_total_tokens:<12.1f} {s.avg_cost_usd:<12.4f} "
            f"{s.stream_error_rate*100:<12.2f} {str(s.kv_enabled):<6} {s.kv_hit_rate*100:<10.2f} {str(s.stream_enabled):<8}"
        )

    print("=" * 100 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="KV-cache / Streaming 实验模块"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=list(MODES.keys()) + ["all"],
        default="baseline",
        help="Experiment mode: baseline, kv_only, stream_only, kv_and_stream, or all",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="fiqa_50k_v1",
        help="Dataset name (default: fiqa_50k_v1)",
    )
    parser.add_argument(
        "--num-queries",
        type=int,
        default=50,
        help="Number of queries to evaluate (default: 50)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=16,
        help="Number of concurrent requests (default: 16)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=20,
        help="Number of warmup requests (default: 20)",
    )
    parser.add_argument(
        "--turns-per-session",
        type=int,
        default=1,
        help="Number of turns per session for KV-cache testing (default: 1, set to 2+ for multi-turn)",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=None,
        help="Output CSV path (default: reports/kv_stream/results_{dataset}_{timestamp}.csv)",
    )

    args = parser.parse_args()

    # Load queries
    dataset_name = args.dataset
    qrels_name = os.getenv("FIQA_QRELS_NAME", f"fiqa_qrels_{dataset_name.replace('fiqa_', '')}")
    queries, qrels = load_queries_qrels(
        dataset_name=dataset_name,
        qrels_name=qrels_name,
    )

    if not queries:
        print("ERROR: No queries loaded")
        return 1

    # Take first N queries
    queries_subset = queries[: max(0, int(args.num_queries))]
    print(f"Loaded {len(queries_subset)} queries from {dataset_name}")

    # Determine which modes to run
    if args.mode == "all":
        modes_to_run = list(MODES.keys())
    else:
        modes_to_run = [args.mode]

    # Run experiments
    all_summaries: List[Summary] = []

    for mode in modes_to_run:
        print(f"\n{'='*80}")
        print(f"Running experiment: {mode}")
        print(f"{'='*80}")

        try:
            results = run_experiment(
                mode=mode,
                queries=queries_subset,
                concurrency=args.concurrency,
                warmup=args.warmup,
                turns_per_session=args.turns_per_session,
            )

            summary = collect_stats(results)
            summary.mode = mode
            all_summaries.append(summary)

        except Exception as e:
            print(f"ERROR in mode {mode}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Write CSV
    if args.output_csv:
        output_path = Path(args.output_csv)
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = Path(f"reports/kv_stream/results_{dataset_name}_{timestamp}.csv")

    write_csv(output_path, all_summaries)
    print(f"\nResults written to: {output_path}")

    # Print summary table
    print_summary_table(all_summaries)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

