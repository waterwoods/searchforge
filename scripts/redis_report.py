#!/usr/bin/env python3
"""
redis_report.py - Compute metrics from Redis lab experiment data

Usage:
    python redis_report.py <exp_id> [--warmup 20]
"""

import sys
import json
import redis
import numpy as np
from collections import defaultdict

def compute_metrics(exp_id: str, warmup_sec: int = 20):
    """
    Read lab:exp:<id>:raw, filter warmup, compute metrics.
    
    Returns dict with:
    - p95_a, p95_b: P95 latencies
    - delta_p95_pct: % difference
    - err_pct: error percentage
    - qps_a, qps_b: queries per second
    - route_share: {milvus, faiss, qdrant} percentages
    - samples_a, samples_b: sample counts
    """
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    raw_key = f"lab:exp:{exp_id}:raw"
    
    # Read all metrics
    raw_data = r.lrange(raw_key, 0, -1)
    if not raw_data:
        return {
            "ok": False,
            "error": "no_data",
            "p95_a": 0, "p95_b": 0, "delta_p95_pct": 0,
            "err_pct": 0, "qps_a": 0, "qps_b": 0,
            "route_share": {"milvus": 0, "faiss": 0, "qdrant": 0},
            "samples_a": 0, "samples_b": 0
        }
    
    # Parse and filter warmup
    metrics = [json.loads(m) for m in raw_data]
    start_ts = min(m["ts"] for m in metrics)
    filtered = [m for m in metrics if m["ts"] >= start_ts + warmup_sec]
    
    if not filtered:
        return {"ok": False, "error": "no_data_after_warmup"}
    
    # Split by phase
    phase_a = [m for m in filtered if m.get("phase") == "A"]
    phase_b = [m for m in filtered if m.get("phase") == "B"]
    
    # Compute P95
    def p95(data):
        if not data:
            return 0
        latencies = [m["latency_ms"] for m in data if m.get("ok")]
        return np.percentile(latencies, 95) if latencies else 0
    
    p95_a = p95(phase_a)
    p95_b = p95(phase_b)
    delta_p95_pct = ((p95_b - p95_a) / p95_a * 100) if p95_a > 0 else 0
    
    # Error rate
    total = len(filtered)
    errors = sum(1 for m in filtered if not m.get("ok", True))
    err_pct = (errors / total * 100) if total > 0 else 0
    
    # QPS (time range)
    end_ts = max(m["ts"] for m in filtered)
    duration = end_ts - (start_ts + warmup_sec)
    qps_a = len(phase_a) / duration if duration > 0 else 0
    qps_b = len(phase_b) / duration if duration > 0 else 0
    
    # Route share
    routes = defaultdict(int)
    for m in filtered:
        route = m.get("route", "unknown")
        routes[route] += 1
    
    route_total = sum(routes.values())
    route_share = {
        "milvus": routes.get("milvus", 0) / route_total * 100 if route_total > 0 else 0,
        "faiss": routes.get("faiss", 0) / route_total * 100 if route_total > 0 else 0,
        "qdrant": routes.get("qdrant", 0) / route_total * 100 if route_total > 0 else 0
    }
    
    return {
        "ok": True,
        "p95_a": round(p95_a, 2),
        "p95_b": round(p95_b, 2),
        "delta_p95_pct": round(delta_p95_pct, 2),
        "err_pct": round(err_pct, 2),
        "qps_a": round(qps_a, 2),
        "qps_b": round(qps_b, 2),
        "route_share": {k: round(v, 1) for k, v in route_share.items()},
        "samples_a": len(phase_a),
        "samples_b": len(phase_b)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python redis_report.py <exp_id> [--warmup 20]")
        sys.exit(1)
    
    exp_id = sys.argv[1]
    warmup = 20
    if "--warmup" in sys.argv:
        idx = sys.argv.index("--warmup")
        warmup = int(sys.argv[idx + 1])
    
    result = compute_metrics(exp_id, warmup)
    print(json.dumps(result, indent=2))

