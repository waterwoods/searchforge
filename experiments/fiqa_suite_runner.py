#!/usr/bin/env python3
"""
FiQA Suite Runner - Experiment Runner for FiQA Evaluation Suite

This script runs experiments and writes metrics.json as the authoritative source.
"""

import argparse
import json
import logging
import os
import random
import statistics
import time
from pathlib import Path
from typing import Dict, List, Optional

from experiments.fiqa_lib import (
    load_queries_qrels,
    evaluate_config,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RUNNER_VERSION = "v2.0.0"

# Hard queries and qrels mapping
HARD_QUERIES_MAP = {
    "fiqa_50k_v1": "experiments/data/fiqa/fiqa_hard_50k.jsonl",
    "fiqa_10k_v1": "experiments/data/fiqa/fiqa_hard_10k.jsonl",
}

HARD_QRELS_MAP = {
    "fiqa_50k_v1": "experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv",
    "fiqa_10k_v1": "experiments/data/fiqa/fiqa_qrels_hard_10k_v1.tsv",
}


def _ensure_dir(p: Path):
    """Ensure directory exists."""
    p.mkdir(parents=True, exist_ok=True)


def _write_metrics_json_runner(
    job_id: str,
    metrics: dict,
    config: dict,
    latency_ms: dict,
    *,
    status: str = "ok",
    err: Optional[str] = None,
    job_note: Optional[str] = None,
):
    """
    Authoritative metrics writer. Called when evaluation finishes (success or failure).
    
    Args:
        job_id: Job ID
        metrics: Dictionary with all metrics (recall_at_1/3/10, ndcg_at_10, mrr, precision_at_10, qps, cost_per_query)
        config: Configuration dictionary
        latency_ms: Dictionary with p95_ms and other latency metrics
        status: Status string ("ok" for success, "error" for failure)
        err: Error message if status is not "ok"
    """
    job = job_id or os.getenv("JOB_ID") or time.strftime("%Y%m%d_%H%M%S")

    base_dir = os.getenv("RUNS_DIR", "/app/.runs")
    out_dir = Path(base_dir) / job

    try:
        _ensure_dir(out_dir)
    except PermissionError:
        fallback = os.getenv("RUNS_FALLBACK_DIR")
        if fallback is None:
            fallback = str(Path.cwd() / ".runs")
        out_dir = Path(fallback) / job
        _ensure_dir(out_dir)
    
    # Try to get current policy from admin API
    policy_info = None
    try:
        import requests
        base_url = os.getenv("BASE", "http://localhost:8000")
        resp = requests.get(f"{base_url}/api/admin/policy/current", timeout=5)
        if resp.status_code == 200:
            policy_info = resp.json()
            logger.info(f"[RUNNER] Current policy: {policy_info.get('policy_name')}")
    except Exception as e:
        logger.warning(f"[RUNNER] Could not fetch policy info: {e}")
    
    payload = {
        "schema_version": 2,
        "source": "runner",  # <- 唯一真相
        "runner_version": RUNNER_VERSION,
        "job_id": job,
        "status": status,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": config.get("dataset_name"),
        "qrels_name": config.get("qrels_name"),
        "metrics": {
            "recall_at_1": float(metrics.get("recall_at_1", 0.0)),
            "recall_at_3": float(metrics.get("recall_at_3", 0.0)),
            "recall_at_10": float(metrics.get("recall_at_10", 0.0)),
            "precision_at_10": float(metrics.get("precision_at_10", 0.0)),
            "ndcg_at_10": float(metrics.get("ndcg_at_10", 0.0)),
            "mrr": float(metrics.get("mrr", 0.0)),
            "p95_ms": float(latency_ms.get("p95_ms", 0.0)),
            "median_ms": float(latency_ms.get("median_ms", 0.0)),
            "qps": float(metrics.get("qps", 0.0)),
            "cost_per_query": float(metrics.get("cost_per_query", 0.0)),
        },
        "latency_breakdown_ms": {
            "search": float(latency_ms.get("search_ms", 0.0)),
            "serialize": float(latency_ms.get("serialize_ms", 0.0)),
            "cache_hit_rate": float(latency_ms.get("cache_hit_rate", 0.0)),
        },
        "config": {
            "dataset": config.get("dataset_name"),
            "qrels": config.get("qrels_name"),
            "top_k": config.get("top_k"),
            "fast_mode": bool(config.get("fast_mode", False)),
            "rerank": bool(config.get("rerank", False)),
            "mmr": bool(config.get("mmr", False)),
            "mmr_lambda": float(config.get("mmr_lambda", 0.3)),
            "use_hard": config.get("use_hard", False),
            "overrides": {
                "top_k": config.get("top_k"),
                "use_hard": config.get("use_hard", False),
                "fast_mode": bool(config.get("fast_mode", False)),
                "ef_search": config.get("ef_search"),
                "mmr": bool(config.get("mmr", False)),
                "mmr_lambda": float(config.get("mmr_lambda", 0.3)),
            }
        }
    }

    if job_note:
        payload["job_note"] = job_note
    
    # Add policy info if available
    if policy_info:
        payload["policy"] = {
            "name": policy_info.get("policy_name", "unknown"),
            "applied_at": policy_info.get("applied_at"),
            "source": policy_info.get("source", "unknown")
        }
    
    if err:
        payload["error"] = str(err)
    
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    print(f"[RUNNER][METRICS] wrote {out_dir / 'metrics.json'} (status={status})")


def calculate_all_metrics(eval_results: dict, latencies: List[float]) -> dict:
    """
    Calculate all metrics from evaluation results.
    
    Args:
        eval_results: Dictionary from evaluate_config
        latencies: List of latency values in milliseconds
        
    Returns:
        Dictionary with all metrics
    """
    # Extract basic metrics from eval_results
    recall_at_10 = float(eval_results.get("recall_at_10", 0.0))
    qps = float(eval_results.get("qps", 0.0))
    
    # Calculate p95 and median latency
    if latencies:
        sorted_latencies = sorted(latencies)
        p95_index = int(0.95 * len(sorted_latencies))
        p95_ms = float(sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1])
        median_ms = float(sorted_latencies[len(sorted_latencies) // 2])
    else:
        p95_ms = float(eval_results.get("p95_ms", 0.0))
        median_ms = float(eval_results.get("median_ms", 0.0))
    
    # For now, set ndcg and mrr to 0 if not available
    # These can be enhanced later if needed
    ndcg_at_10 = float(eval_results.get("ndcg_at_10", 0.0))
    mrr = float(eval_results.get("mrr", 0.0))
    
    return {
        "recall_at_10": recall_at_10,
        "ndcg_at_10": ndcg_at_10,
        "mrr": mrr,
        "qps": qps,
    }


def wait_for_health(base: str, tries: int = 30, sleep_s: int = 2) -> None:
    """
    Wait for backend health check to pass.
    
    Args:
        base: Base API URL
        tries: Number of retry attempts
        sleep_s: Sleep time between attempts (seconds)
        
    Raises:
        RuntimeError: If health check fails after all retries
    """
    import requests
    
    url = f"{base}/api/health/qdrant"
    logger.info(f"Waiting for backend health at {url}...")
    
    for attempt in range(1, tries + 1):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("http_ok") and data.get("grpc_ok"):
                    logger.info(f"✅ Backend health OK (attempt {attempt}/{tries})")
                    return
                else:
                    logger.warning(f"Health check not ready: http_ok={data.get('http_ok')}, grpc_ok={data.get('grpc_ok')}")
            else:
                logger.warning(f"Health check returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Health check attempt {attempt}/{tries} failed: {e}")
        
        if attempt < tries:
            time.sleep(sleep_s)
    
    raise RuntimeError(f"后端未就绪: health check failed after {tries} attempts")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FiQA Suite Runner - Experiment Runner for FiQA Evaluation Suite"
    )
    parser.add_argument(
        "--base",
        type=str,
        default="http://localhost:8000",
        help="Base API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--config-file",
        type=str,
        default=None,
        help="Optional config file path (YAML format)"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Sample N queries (default: all)"
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of repeats (default: 1)"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=None,
        help="Top-K parameter"
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default=None,
        help="Dataset name (e.g., fiqa_50k_v1)"
    )
    parser.add_argument(
        "--qrels",
        type=str,
        required=True,
        help="Path to qrels TSV file (required)"
    )
    parser.add_argument(
        "--queries",
        type=str,
        required=True,
        help="Path to queries JSONL file (required)"
    )
    parser.add_argument(
        "--qrels-name",
        type=str,
        default=None,
        help="Qrels name (e.g., fiqa_qrels_50k_v1)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="experiments/data/fiqa",
        help="Data directory (default: experiments/data/fiqa)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Request timeout in seconds (default: 15.0)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=16,
        help="Thread pool size (default: 16)"
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=5,
        help="Number of warmup queries (default: 5)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Collection override (alias for dataset name)"
    )
    parser.add_argument(
        "--use-hard",
        action="store_true",
        help="Use hard query subset"
    )
    parser.add_argument(
        "--ef-search",
        type=int,
        default=None,
        help="Qdrant HNSW ef parameter for search"
    )
    parser.add_argument(
        "--mmr",
        action="store_true",
        help="Enable MMR (Maximum Marginal Relevance) diversification"
    )
    parser.add_argument(
        "--mmr-lambda",
        type=float,
        default=0.3,
        help="MMR lambda parameter (0=max diversity, 1=max relevance, default: 0.3)"
    )
    parser.add_argument(
        "--job-note",
        type=str,
        default=None,
        help="Optional note to attach to metrics outputs"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling queries (default: 42)"
    )
    
    args = parser.parse_args()
    
    # Allow --collection to act as alias for dataset name
    if args.collection and not args.dataset_name:
        args.dataset_name = args.collection

    # Handle BASE environment variable override
    base_url = os.getenv("BASE", args.base)
    
    # Get job_id from environment
    job_id = os.getenv("JOB_ID")
    if not job_id:
        job_id = time.strftime("%Y%m%d_%H%M%S")
        logger.warning(f"No JOB_ID in environment, using generated: {job_id}")
    
    logger.info("="*80)
    logger.info("FiQA Suite Runner")
    logger.info("="*80)
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Dataset: {args.dataset_name}")
    logger.info(f"Qrels: {args.qrels_name}")
    logger.info(f"Top-K: {args.top_k}")
    logger.info(f"Fast Mode: {args.fast}")
    logger.info(f"Sample: {args.sample}")
    logger.info(f"Seed: {args.seed}")
    if args.job_note:
        logger.info(f"Job Note: {args.job_note}")
    logger.info("="*80)
    
    # Wait for backend health
    try:
        wait_for_health(base_url)
    except RuntimeError as e:
        logger.error(f"Health check failed: {e}")
        return 1
    
    # Load queries and qrels
    try:
        # Use explicitly provided --qrels and --queries (required, no fallback)
        repo_root = Path("/app") if Path("/app").exists() else Path(__file__).resolve().parent.parent
        
        if not args.qrels or not args.queries:
            raise ValueError("Both --qrels and --queries are required")
        
        # Direct qrels and queries file paths provided (required)
        qrels_file = repo_root / args.qrels if not Path(args.qrels).is_absolute() else Path(args.qrels)
        queries_file = repo_root / args.queries if not Path(args.queries).is_absolute() else Path(args.queries)
        
        if not qrels_file.exists():
            raise FileNotFoundError(f"Qrels file not found: {qrels_file}")
        if not queries_file.exists():
            raise FileNotFoundError(f"Queries file not found: {queries_file}")
        
        # Load qrels and queries explicitly (do NOT fall back to defaults)
        from experiments.fiqa_lib import load_fiqa_qrels, load_fiqa_queries
        qrels = load_fiqa_qrels(qrels_file)
        queries = load_fiqa_queries(queries_file)
        logger.info(f"✅ Loaded qrels from: {qrels_file} ({len(qrels)} query-doc pairs)")
        logger.info(f"✅ Loaded queries from: {queries_file} ({len(queries)} queries)")
        
        # Robust sampling: if sample is provided and valid, slice queries
        if args.sample and isinstance(args.sample, int) and args.sample > 0:
            if len(queries) > args.sample:
                random.seed(args.seed)
                queries = random.sample(queries, args.sample)
                logger.info(f"Sampled {len(queries)} queries (requested {args.sample}, seed={args.seed})")
        
    except Exception as e:
        logger.error(f"Failed to load queries/qrels: {e}", exc_info=True)
        return 1
    
    # Determine top_k
    top_k = args.top_k if args.top_k is not None else (30 if args.fast else 50)
    
    # Build configuration
    use_hard = args.use_hard or os.getenv("USE_HARD", "false").lower() == "true"
    config = {
        "use_hybrid": False,
        "rerank": False,
        "dataset_name": args.dataset_name,
        "qrels_name": args.qrels_name if not use_hard else HARD_QRELS_MAP.get(args.dataset_name, args.qrels_name),
        "top_k": top_k,
        "fast_mode": args.fast,
        "use_hard": use_hard,
        "mmr": args.mmr,
        "mmr_lambda": args.mmr_lambda,
    }
    
    # Add ef_search if provided
    if args.ef_search is not None:
        config["ef_search"] = args.ef_search
        logger.info(f"ef_search: {args.ef_search}")
    
    # Log MMR settings if enabled
    if args.mmr:
        logger.info(f"MMR enabled: λ={args.mmr_lambda}")
    
    # Determine collection name
    collection = args.dataset_name if args.dataset_name else None
    
    # Run evaluation
    status = "ok"
    error_msg = None
    metrics = {
        "recall_at_1": 0.0,
        "recall_at_3": 0.0,
        "recall_at_10": 0.0,
        "precision_at_10": 0.0,
        "ndcg_at_10": 0.0,
        "mrr": 0.0,
        "qps": 0.0,
        "cost_per_query": 0.0,
    }
    latency_ms = {"p95_ms": 0.0}
    
    try:
        logger.info("Starting evaluation...")
        eval_results = evaluate_config(
            cfg=config,
            base_url=base_url,
            queries=queries,
            qrels=qrels,
            top_k=top_k,
            concurrency=args.concurrency,
            repeats=args.repeats,
            timeout_s=args.timeout,
            warmup=args.warmup,
            collection=collection
        )
        
        logger.info(f"Evaluation complete:")
        logger.info(f"  Recall@10: {eval_results.get('recall_at_10', 0.0):.4f}")
        logger.info(f"  P95 (ms): {eval_results.get('p95_ms', 0.0):.1f}")
        logger.info(f"  Median (ms): {eval_results.get('median_ms', 0.0):.1f}")
        logger.info(f"  QPS: {eval_results.get('qps', 0.0):.2f}")
        
        # Extract metrics and latency from eval_results
        latency_ms = {
            "p95_ms": eval_results.get("p95_ms", 0.0),
        }
        
        metrics = {
            "recall_at_1": eval_results.get("recall_at_1", 0.0),
            "recall_at_3": eval_results.get("recall_at_3", 0.0),
            "recall_at_10": eval_results.get("recall_at_10", 0.0),
            "precision_at_10": eval_results.get("precision_at_10", 0.0),
            "ndcg_at_10": eval_results.get("ndcg_at_10", 0.0),
            "mrr": eval_results.get("mrr", 0.0),
            "qps": eval_results.get("qps", 0.0),
            "cost_per_query": eval_results.get("cost_per_query", 0.0),
        }
        
        status = "ok"
        
        logger.info("="*80)
        logger.info("Experiment complete!")
        logger.info("="*80)
        
        return_code = 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        status = "error"
        error_msg = str(e)
        return_code = 1
    
    finally:
        # Always write metrics.json (success or failure)
        _write_metrics_json_runner(
            job_id,
            metrics,
            config,
            latency_ms,
            status=status,
            err=error_msg,
            job_note=args.job_note,
        )
    
    return return_code


if __name__ == "__main__":
    import sys
    sys.exit(main())

