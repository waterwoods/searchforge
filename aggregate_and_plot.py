#!/usr/bin/env python3
"""
Aggregate metrics and generate plots for Gold + Hard experiments.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import statistics

# Try to import matplotlib, fallback to host rendering
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: matplotlib not available, plots will be generated on host", file=sys.stderr)

def load_metrics_from_file(runs_dir: Path, job_id: str) -> Optional[Dict]:
    """Load metrics.json for a job."""
    metrics_file = runs_dir / job_id / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def collect_jobs(runs_dir: Path, job_ids: List[str]) -> List[Dict]:
    """Collect metrics for all jobs."""
    all_items = []
    
    for job_id in job_ids:
        metrics = load_metrics_from_file(runs_dir, job_id)
        if not metrics:
            continue
        
        # Extract metrics (support both new and old format)
        if "metrics" in metrics:
            metrics_data = metrics.get("metrics", {})
            config = metrics.get("config", {})
            source = metrics.get("source", "unknown")
            dataset = metrics.get("dataset") or config.get("dataset")
            qrels_name = metrics.get("qrels_name") or config.get("qrels")
        else:
            metrics_data = metrics.get("overall", {})
            config = metrics.get("config", {})
            source = "legacy"
            dataset = config.get("dataset")
            qrels_name = config.get("qrels")
        
        # Determine if this is gold or hard
        dataset_tag = "hard" if "hard" in (qrels_name or "").lower() else "gold"
        
        item = {
            "job_id": job_id,
            "dataset_tag": dataset_tag,
            "top_k": config.get("top_k"),
            "fast_mode": config.get("fast_mode", False),
            "mmr": config.get("mmr"),
            "recall_at_1": metrics_data.get("recall_at_1", 0.0),
            "recall_at_3": metrics_data.get("recall_at_3", 0.0),
            "recall_at_10": metrics_data.get("recall_at_10", 0.0),
            "precision_at_10": metrics_data.get("precision_at_10", 0.0),
            "ndcg_at_10": metrics_data.get("ndcg_at_10", 0.0),
            "mrr": metrics_data.get("mrr", 0.0),
            "p95_ms": metrics_data.get("p95_ms", 0.0),
            "qps": metrics_data.get("qps", 0.0),
            "cost_per_query": metrics_data.get("cost_per_query", 0.0),
            "source": source,
            "status": "SUCCEEDED"
        }
        all_items.append(item)
    
    return all_items

def find_winners(all_items: List[Dict], dataset_tag: str) -> Dict:
    """Find winners for a dataset tag."""
    filtered = [x for x in all_items if x.get("dataset_tag") == dataset_tag and x.get("recall_at_10", 0) > 0]
    
    if not filtered:
        return {"quality": {}, "latency": {}, "balanced": {}}
    
    # Quality: highest recall@10, then lowest p95
    best_quality = max(filtered, key=lambda x: (x.get("recall_at_10", 0), -x.get("p95_ms", 1e9)))
    
    # Latency: lowest p95, then highest recall@10
    latency_candidates = [x for x in filtered if x.get("p95_ms", 1e9) > 0]
    best_latency = min(latency_candidates, key=lambda x: (x.get("p95_ms", 1e9), -x.get("recall_at_10", 0))) if latency_candidates else best_quality
    
    # Balanced: maximize (recall@10 - 0.0005 * p95_ms)
    balanced = max(filtered, key=lambda x: (x.get("recall_at_10", 0)) - 0.0005 * (x.get("p95_ms", 0)))
    
    return {
        "quality": best_quality,
        "latency": best_latency,
        "balanced": balanced
    }

def plot_pareto(all_items: List[Dict], dataset_tag: str, output_path: Path):
    """Generate Pareto plot (Recall@10 vs p95_ms)."""
    if not MATPLOTLIB_AVAILABLE:
        print(f"SKIP: Plot for {dataset_tag} (matplotlib not available)")
        return
    
    filtered = [x for x in all_items if x.get("dataset_tag") == dataset_tag]
    if not filtered:
        return
    
    recalls = [x.get("recall_at_10", 0) for x in filtered]
    p95s = [x.get("p95_ms", 0) for x in filtered]
    labels = [f"k={x.get('top_k')},f={x.get('fast_mode')}" for x in filtered]
    
    plt.figure(figsize=(10, 6))
    plt.scatter(p95s, recalls, s=200, alpha=0.7)
    
    # Annotate points
    for i, (p95, recall, label) in enumerate(zip(p95s, recalls, labels)):
        plt.annotate(label, (p95, recall), xytext=(5, 5), textcoords='offset points', fontsize=9)
    
    plt.xlabel('P95 Latency (ms)', fontsize=12)
    plt.ylabel('Recall@10', fontsize=12)
    plt.title(f'Pareto Front: Recall@10 vs P95 Latency ({dataset_tag.upper()})', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved plot: {output_path}")

def generate_summary_md(all_items: List[Dict], output_path: Path):
    """Generate summary markdown with comparison table."""
    lines = [
        "# Gold vs Hard Experiment Summary",
        "",
        "## Metrics Comparison Table",
        "",
        "| Dataset | Top-K | Fast | MMR | R@1 | R@3 | R@10 | P@10 | nDCG@10 | MRR | P95 (ms) | Cost/Req |",
        "|---------|-------|------|-----|-----|-----|------|------|---------|-----|----------|----------|"
    ]
    
    # Sort by dataset_tag, then top_k, then fast_mode
    sorted_items = sorted(all_items, key=lambda x: (
        x.get("dataset_tag", ""),
        x.get("top_k", 0),
        x.get("fast_mode", False)
    ))
    
    for item in sorted_items:
        lines.append(
            f"| {item.get('dataset_tag', '?')} | {item.get('top_k', '?')} | {item.get('fast_mode', False)} | "
            f"{item.get('mmr') or 'off'} | {item.get('recall_at_1', 0):.4f} | {item.get('recall_at_3', 0):.4f} | "
            f"{item.get('recall_at_10', 0):.4f} | {item.get('precision_at_10', 0):.4f} | "
            f"{item.get('ndcg_at_10', 0):.4f} | {item.get('mrr', 0):.4f} | {item.get('p95_ms', 0):.1f} | "
            f"{item.get('cost_per_query', 0):.6f} |"
        )
    
    # Find largest differences
    gold_items = [x for x in all_items if x.get("dataset_tag") == "gold"]
    hard_items = [x for x in all_items if x.get("dataset_tag") == "hard"]
    
    if gold_items and hard_items:
        lines.extend([
            "",
            "## Key Differences",
            ""
        ])
        
        # Compare average metrics
        def avg_metric(items, key):
            return statistics.mean([x.get(key, 0) for x in items]) if items else 0
        
        gold_avg_r10 = avg_metric(gold_items, "recall_at_10")
        hard_avg_r10 = avg_metric(hard_items, "recall_at_10")
        gold_avg_p95 = avg_metric(gold_items, "p95_ms")
        hard_avg_p95 = avg_metric(hard_items, "p95_ms")
        
        lines.extend([
            f"- **Recall@10**: Gold avg={gold_avg_r10:.4f}, Hard avg={hard_avg_r10:.4f}, "
            f"Δ={hard_avg_r10 - gold_avg_r10:.4f}",
            f"- **P95 Latency**: Gold avg={gold_avg_p95:.1f}ms, Hard avg={hard_avg_p95:.1f}ms, "
            f"Δ={hard_avg_p95 - gold_avg_p95:.1f}ms",
        ])
        
        # Find configuration with largest difference
        if len(gold_items) == len(hard_items):
            max_diff_idx = 0
            max_diff_val = 0
            for i, (g, h) in enumerate(zip(gold_items, hard_items)):
                diff = abs(g.get("recall_at_10", 0) - h.get("recall_at_10", 0))
                if diff > max_diff_val:
                    max_diff_val = diff
                    max_diff_idx = i
            if max_diff_idx < len(gold_items):
                g = gold_items[max_diff_idx]
                h = hard_items[max_diff_idx]
                lines.append(
                    f"- **Largest difference** at top_k={g.get('top_k')}, fast={g.get('fast_mode')}: "
                    f"R@10 Δ={abs(g.get('recall_at_10', 0) - h.get('recall_at_10', 0)):.4f}"
                )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"✅ Saved summary: {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Aggregate metrics and generate plots")
    parser.add_argument("--runs-dir", default="/app/.runs", help="Runs directory")
    parser.add_argument("--jobs-file", default="reports/jobs_gold_hard.list", help="Jobs file")
    parser.add_argument("--out-dir", default="reports", help="Output directory")
    args = parser.parse_args()
    
    runs_dir = Path(args.runs_dir)
    jobs_file = Path(args.jobs_file)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load job IDs
    if jobs_file.exists():
        job_ids = jobs_file.read_text().strip().split()
    else:
        # Fallback: scan runs directory
        job_ids = [d.name for d in runs_dir.iterdir() if d.is_dir() and (d / "metrics.json").exists()]
    
    print(f"Collecting metrics for {len(job_ids)} jobs...")
    all_items = collect_jobs(runs_dir, job_ids)
    print(f"Loaded {len(all_items)} jobs with metrics")
    
    # Generate winners for gold and hard
    gold_winners = find_winners(all_items, "gold")
    hard_winners = find_winners(all_items, "hard")
    
    # Save winners
    with open(out_dir / "winners_gold.json", 'w', encoding='utf-8') as f:
        json.dump({"winners": gold_winners, "all": [x for x in all_items if x.get("dataset_tag") == "gold"]}, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {out_dir / 'winners_gold.json'}")
    
    with open(out_dir / "winners_hard.json", 'w', encoding='utf-8') as f:
        json.dump({"winners": hard_winners, "all": [x for x in all_items if x.get("dataset_tag") == "hard"]}, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {out_dir / 'winners_hard.json'}")
    
    # Generate plots
    plot_pareto(all_items, "gold", out_dir / "pareto_gold.png")
    plot_pareto(all_items, "hard", out_dir / "pareto_hard.png")
    
    # Generate summary
    generate_summary_md(all_items, out_dir / "summary_gold_vs_hard.md")
    
    print(f"\n✅ Aggregation complete. Outputs in: {out_dir}")

if __name__ == "__main__":
    main()

