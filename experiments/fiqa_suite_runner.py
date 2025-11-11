#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from experiments.fiqa_lib import (
    evaluate_config,
    load_queries_qrels,
    percentile,
)

logger = logging.getLogger("fiqa_suite_runner")


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    if not config_path:
        return {}
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(text) or {}
    return json.loads(text)


def coerce_positive(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v <= 0:
        return None
    return v


def write_summary(job_id: str, summary: Dict[str, Any]) -> Path:
    artifacts_root = Path(__file__).resolve().parents[1] / "artifacts"
    job_dir = artifacts_root / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    summary_path = job_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    return summary_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="FiQA suite runner (minimal)")
    parser.add_argument("--base", dest="base_url", default="http://localhost:8000", help="Base API URL")
    parser.add_argument("--config-file", dest="config_file", default=None, help="Optional config JSON/YAML")
    parser.add_argument("--sample", type=int, default=100, help="Number of queries to sample")
    parser.add_argument("--repeats", type=int, default=1, help="Number of evaluation repeats")
    parser.add_argument("--top_k", type=int, default=10, help="Top-K to request")
    parser.add_argument("--concurrency", type=int, default=8, help="Concurrent query workers")
    parser.add_argument("--timeout", type=float, default=15.0, help="Request timeout (seconds)")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup queries")
    parser.add_argument("--dataset-name", default=None, help="Dataset name (fiqa_v1)")
    parser.add_argument("--qrels-name", default=None, help="Qrels name (fiqa_qrels_v1)")
    parser.add_argument("--data-dir", default=None, help="Legacy data directory fallback")
    parser.add_argument("--collection", default=None, help="Optional collection override")
    parser.add_argument("--fast", action="store_true", help="Fast mode (reduced warmup/sample)")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    config = load_config(args.config_file)

    sample = max(5, args.sample or 100)
    warmup = max(0, args.warmup)
    repeats = max(1, args.repeats)
    concurrency = max(1, args.concurrency)

    if args.fast:
        sample = min(sample, 50)
        warmup = min(warmup, 2)
        repeats = min(repeats, 1)
        concurrency = min(concurrency, 8)

    queries, qrels = load_queries_qrels(
        data_dir=args.data_dir,
        dataset_name=args.dataset_name,
        qrels_name=args.qrels_name,
        sample=sample,
    )
    if not queries:
        logger.error("No queries loaded. Check dataset configuration.")
        return 1

    metrics = evaluate_config(
        config,
        base_url=args.base_url.rstrip("/"),
        queries=queries,
        qrels=qrels,
        top_k=args.top_k,
        concurrency=concurrency,
        repeats=repeats,
        timeout_s=args.timeout,
        warmup=warmup,
        collection=args.collection,
        return_details=True,
    )

    latencies = metrics.pop("latencies_ms", [])

    p95_ms = coerce_positive(metrics.get("p95_ms"))
    if p95_ms is None:
        p95_ms = coerce_positive(percentile(latencies, 0.95))

    total_queries = int(metrics.get("total_queries") or len(latencies))
    failed_queries = int(metrics.get("failed_queries") or 0)
    hit_count = int(metrics.get("hit_count") or 0)

    err_rate = metrics.get("err_rate")
    if err_rate is not None:
        try:
            err_rate = max(0.0, min(1.0, float(err_rate)))
        except (TypeError, ValueError):
            err_rate = None
    elif total_queries > 0:
        err_rate = failed_queries / total_queries

    recall_at_10 = metrics.get("recall_at_10")
    if recall_at_10 is not None:
        try:
            recall_at_10 = max(0.0, min(1.0, float(recall_at_10)))
        except (TypeError, ValueError):
            recall_at_10 = None
    elif total_queries > 0:
        recall_at_10 = hit_count / total_queries

    cost_tokens = metrics.get("cost_tokens")
    try:
        cost_tokens = int(cost_tokens) if cost_tokens is not None else 0
    except (TypeError, ValueError):
        cost_tokens = 0

    summary = {
        "p95_ms": p95_ms,
        "err_rate": err_rate,
        "recall_at_10": recall_at_10,
        "cost_tokens": cost_tokens,
        "total": total_queries,
        "hits": hit_count,
        "errors": failed_queries,
    }

    job_id = os.environ.get("JOB_ID") or ""
    if not job_id:
        job_id = f"local-{int(time.time())}"
    summary_path = write_summary(job_id, summary)
    logger.info(f"Wrote summary metrics to {summary_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

