#!/usr/bin/env python3
"""
collect_metrics.py - Collect Metrics and Generate winners.json
==============================================================
Reads metrics.json from each job and generates reports/winners.json with quality/latency/balanced winners.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Default paths (support both container and remote execution)
import os
RUNS_DIR = Path(os.getenv("RUNS_DIR", "/app/.runs"))
if not RUNS_DIR.exists():
    # Try relative path
    RUNS_DIR = Path(".runs")
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "/app/reports"))
if not REPORTS_DIR.exists():
    # Try relative path
    REPORTS_DIR = Path("reports")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def load_metrics_from_file(job_id: str) -> Optional[Dict]:
    """Load metrics.json from run directory."""
    metrics_path = RUNS_DIR / job_id / "metrics.json"
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"WARNING: Failed to load metrics.json for {job_id}: {e}", file=sys.stderr)
    return None


def load_metrics_from_api(job_id: str) -> Optional[Dict]:
    """Load metrics from API detail endpoint (fallback)."""
    try:
        import urllib.request
        url = f"{API_BASE}/api/experiment/detail/{job_id}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            return data.get("metrics")
    except Exception as e:
        print(f"WARNING: Failed to load metrics from API for {job_id}: {e}", file=sys.stderr)
        return None


def collect_all_jobs() -> List[Dict]:
    """Collect metrics from all jobs."""
    all_items = []
    
    # Scan run directory for job IDs
    if not RUNS_DIR.exists():
        print(f"WARNING: Run directory not found: {RUNS_DIR}", file=sys.stderr)
        return all_items
    
    # Get all job directories
    for job_dir in RUNS_DIR.iterdir():
        if not job_dir.is_dir():
            continue
        
        job_id = job_dir.name
        
        # Try to load metrics.json
        metrics = load_metrics_from_file(job_id)
        
        if not metrics:
            # Fallback: try API
            metrics = load_metrics_from_api(job_id)
        
        if metrics:
            # Extract key metrics
            overall = metrics.get("overall", {})
            config = metrics.get("config", {})
            
            item = {
                "job_id": job_id,
                "top_k": config.get("top_k"),
                "fast_mode": config.get("fast_mode", False),
                "dataset_name": config.get("dataset"),
                "qrels_name": config.get("qrels"),
                "collection": config.get("collection"),
                "use_hybrid": config.get("use_hybrid", False),
                "rerank": config.get("rerank", False),
                "recall_at_10": overall.get("recall_at_10", 0.0),
                "p95_ms": overall.get("p95_ms", 0.0),
                "qps": overall.get("qps", 0.0),
                "status": "SUCCEEDED"  # Assume succeeded if metrics exist
            }
            all_items.append(item)
    
    return all_items


def find_winners(all_items: List[Dict]) -> Dict:
    """Find winners: quality, latency, balanced."""
    if not all_items:
        return {
            "quality": {},
            "latency": {},
            "balanced": {}
        }
    
    # Filter succeeded items
    succeeded = [x for x in all_items if x.get("status") == "SUCCEEDED" and x.get("recall_at_10", 0) > 0]
    
    if not succeeded:
        return {
            "quality": all_items[0] if all_items else {},
            "latency": all_items[0] if all_items else {},
            "balanced": all_items[0] if all_items else {}
        }
    
    # Quality winner: highest recall@10
    best_quality = max(succeeded, key=lambda x: x.get("recall_at_10", 0))
    
    # Latency winner: lowest p95_ms
    latency_candidates = [x for x in succeeded if x.get("p95_ms", 1e9) > 0]
    best_latency = min(latency_candidates, key=lambda x: x.get("p95_ms", 1e9)) if latency_candidates else best_quality
    
    # Balanced winner: maximize (recall@10 - 0.0005 * p95_ms)
    balanced = max(succeeded, key=lambda x: (x.get("recall_at_10", 0)) - 0.0005 * (x.get("p95_ms", 0)))
    
    return {
        "quality": best_quality,
        "latency": best_latency,
        "balanced": balanced
    }


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Collect metrics and generate winners.json")
    parser.add_argument("--runs-dir", help="Runs directory path (default: /app/.runs or .runs)")
    parser.add_argument("--out", default="reports/winners.json", help="Output winners.json path")
    args = parser.parse_args()
    
    # Override RUNS_DIR if provided
    global RUNS_DIR
    if args.runs_dir:
        RUNS_DIR = Path(args.runs_dir)
    
    print("Collecting metrics from all jobs...")
    print(f"Using RUNS_DIR: {RUNS_DIR}")
    all_items = collect_all_jobs()
    
    print(f"Found {len(all_items)} jobs with metrics")
    
    if not all_items:
        print("WARNING: No jobs with metrics found!", file=sys.stderr)
        # Create empty winners.json
        winners = {
            "winners": {
                "quality": {},
                "latency": {},
                "balanced": {}
            },
            "all": []
        }
    else:
        winners_data = find_winners(all_items)
        winners = {
            "winners": winners_data,
            "all": all_items
        }
    
    # Write winners.json
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    winners_path = Path(args.out)
    winners_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(winners_path, 'w', encoding='utf-8') as f:
        json.dump(winners, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Winners written to: {winners_path}")
    
    # Print summary
    if winners["winners"]["quality"]:
        q = winners["winners"]["quality"]
        print(f"\nBest Quality: {q['job_id']} - Recall@10={q.get('recall_at_10', 0):.4f}, P95={q.get('p95_ms', 0):.1f}ms")
    
    if winners["winners"]["latency"]:
        l = winners["winners"]["latency"]
        print(f"Best Latency: {l['job_id']} - Recall@10={l.get('recall_at_10', 0):.4f}, P95={l.get('p95_ms', 0):.1f}ms")
    
    if winners["winners"]["balanced"]:
        b = winners["winners"]["balanced"]
        print(f"Best Balanced: {b['job_id']} - Recall@10={b.get('recall_at_10', 0):.4f}, P95={b.get('p95_ms', 0):.1f}ms")
    
    sys.exit(0)


if __name__ == "__main__":
    main()

