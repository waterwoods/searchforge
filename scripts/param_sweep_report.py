#!/usr/bin/env python3
"""
Parameter Sweep Report Generator

Generates effect-vs-performance analysis by sweeping candidate_k and rerank_k parameters.
Creates CSV metrics and visualization charts for embedding into HTML reports.

# Quick run example:
# python scripts/param_sweep_report.py \
#   --config configs/demo_rerank_5k.yaml \
#   --collection demo_5k \
#   --queries "fast usb c cable charging" "wireless charger" "usb c hub" \
#   --candidate-grid 100,200,400 \
#   --rerank-grid 20,50,80 \
#   --output-dir reports/rerank_html/sweep
"""

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.search.search_pipeline import SearchPipeline
from modules.types import Document, ScoredDocument


def normalize_tokens(text: str) -> List[str]:
    """Extract normalized tokens from text."""
    return re.findall(r"[a-z0-9]+", text.lower())


def is_relevant_document(doc_text: str, query: str) -> bool:
    """Check if document is relevant based on token overlap."""
    doc_tokens = set(normalize_tokens(doc_text))
    query_tokens = set(normalize_tokens(query))
    
    # At least 2 tokens must match
    overlap = len(doc_tokens & query_tokens)
    return overlap >= 2


def calculate_recall_at_10(results: List[ScoredDocument], query: str) -> float:
    """Calculate Recall@10 based on token overlap relevance."""
    if len(results) < 10:
        return 0.0
    
    top_10 = results[:10]
    relevant_count = sum(1 for result in top_10 if is_relevant_document(result.document.text, query))
    return relevant_count / len(top_10)


def run_single_trial(
    query: str, 
    candidates: List[Tuple[str, float, str]], 
    rerank_k: int
) -> Dict[str, Any]:
    """Run a single trial and return metrics."""
    try:
        # Get base top-1 document ID
        base_top1_id = candidates[0][0] if candidates else None
        
        # Time the reranking process
        start_time = time.perf_counter()
        
        # Apply reranking
        docs = [Document(id=doc_id, text=text, metadata={}) for doc_id, _, text in candidates]
        from modules.rerankers.simple_ce import CrossEncoderReranker
        reranker = CrossEncoderReranker()
        reranked_results = reranker.rerank(query, docs, top_k=rerank_k)
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        # Get reranked top-1 document ID
        reranked_top1_id = reranked_results[0].document.id if reranked_results else None
        
        # Calculate metrics
        top1_changed = (base_top1_id != reranked_top1_id)
        recall_at10 = calculate_recall_at_10(reranked_results, query)
        
        return {
            "latency_ms": latency_ms,
            "top1_changed": 1.0 if top1_changed else 0.0,
            "recall_at10": recall_at10
        }
        
    except Exception as e:
        print(f"    Error in trial: {e}")
        return {"latency_ms": np.nan, "top1_changed": 0.0, "recall_at10": 0.0}


def search_without_rerank(pipeline: SearchPipeline, query: str, collection_name: str, candidate_k: int) -> List[ScoredDocument]:
    """Search with reranker disabled to get base similarity scores."""
    # Temporarily disable reranker
    original_reranker = pipeline.reranker
    pipeline.reranker = None
    
    # Update retriever config to get more candidates
    original_top_k = pipeline.config.get("retriever", {}).get("top_k", 20)
    pipeline.config["retriever"]["top_k"] = candidate_k
    
    try:
        results = pipeline.search(query, collection_name)
        return results
    finally:
        # Restore original settings
        pipeline.reranker = original_reranker
        pipeline.config["retriever"]["top_k"] = original_top_k


def run_parameter_sweep(
    config_path: str,
    collection_name: str,
    queries: List[str],
    candidate_grid: List[int],
    rerank_grid: List[int],
    output_dir: Path,
    trials: int = 3
) -> None:
    """Run parameter sweep and generate metrics."""
    
    # Load pipeline configuration
    try:
        pipeline = SearchPipeline.from_config(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    # Override collection if provided
    if collection_name:
        pipeline.config["collection_name"] = collection_name
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Running parameter sweep...")
    print(f"Queries: {queries}")
    print(f"Candidate grid: {candidate_grid}")
    print(f"Rerank grid: {rerank_grid}")
    print(f"Trials per point: {trials}")
    
    # Pre-fetch candidates for consistency
    max_candidate_k = max(candidate_grid)
    print(f"\nPre-fetching candidates (max candidate_k={max_candidate_k})...")
    
    candidate_cache = {}
    for query in queries:
        print(f"  Fetching candidates for: {query}")
        base_results = search_without_rerank(pipeline, query, collection_name, max_candidate_k)
        if not base_results:
            print(f"    Warning: No results for query '{query}'")
            candidate_cache[query] = []
            continue
        
        # Cache candidates with (doc_id, score, text) tuples, sorted by score desc
        candidates = []
        for result in base_results:
            doc_id = result.document.id
            score = float(result.score)
            text = result.document.text
            candidates.append((doc_id, score, text))
        
        # Sort by score descending for deterministic prefix cuts
        candidates.sort(key=lambda x: x[1], reverse=True)
        candidate_cache[query] = candidates
        print(f"    Cached {len(candidates)} candidates")
    
    # Run sweep with multiple trials
    all_metrics = []
    
    for candidate_k in candidate_grid:
        for rerank_k in rerank_grid:
            print(f"\nTesting candidate_k={candidate_k}, rerank_k={rerank_k}")
            
            # Collect all trial results across all queries
            all_latencies = []
            all_top1_changes = []
            all_recalls = []
            
            for query in queries:
                print(f"  Query: {query}")
                
                # Get cached candidates for this query
                full_candidates = candidate_cache[query]
                if not full_candidates:
                    print(f"    Skipping - no cached candidates")
                    continue
                
                # Take prefix for this candidate_k
                candidates = full_candidates[:candidate_k]
                if len(candidates) < rerank_k:
                    print(f"    Warning: Only {len(candidates)} candidates available for rerank_k={rerank_k}")
                
                # Run multiple trials
                query_latencies = []
                query_top1_changes = []
                query_recalls = []
                
                for trial in range(trials):
                    print(f"    Trial {trial + 1}/{trials}")
                    trial_result = run_single_trial(query, candidates, rerank_k)
                    
                    if not np.isnan(trial_result["latency_ms"]):
                        query_latencies.append(trial_result["latency_ms"])
                    query_top1_changes.append(trial_result["top1_changed"])
                    query_recalls.append(trial_result["recall_at10"])
                
                # Add to global aggregates
                all_latencies.extend(query_latencies)
                all_top1_changes.extend(query_top1_changes)
                all_recalls.extend(query_recalls)
            
            # Calculate aggregate metrics across all queries and trials
            if all_latencies:
                p50_ms = float(np.percentile(all_latencies, 50))
                p95_ms = float(np.percentile(all_latencies, 95))
                p99_ms = float(np.percentile(all_latencies, 99))
            else:
                p50_ms = p95_ms = p99_ms = np.nan
            
            top1_rate = float(np.mean(all_top1_changes)) if all_top1_changes else 0.0
            recall_at10 = float(np.mean(all_recalls)) if all_recalls else 0.0
            
            all_metrics.append({
                "candidate_k": candidate_k,
                "rerank_k": rerank_k,
                "p50_ms": round(p50_ms, 2) if not np.isnan(p50_ms) else np.nan,
                "p95_ms": round(p95_ms, 2) if not np.isnan(p95_ms) else np.nan,
                "p99_ms": round(p99_ms, 2) if not np.isnan(p99_ms) else np.nan,
                "top1_rate": round(top1_rate, 3),
                "recall_at10": round(recall_at10, 3),
                "queries": len(queries)
            })
            
            print(f"  Results: P50={p50_ms:.1f}ms, P95={p95_ms:.1f}ms, P99={p99_ms:.1f}ms")
            print(f"           Top1_rate={top1_rate:.3f}, Recall@10={recall_at10:.3f}")
    
    # Save CSV with new columns
    csv_path = output_dir / "sweep_metrics.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_k", "rerank_k", "p50_ms", "p95_ms", "p99_ms", "top1_rate", "recall_at10", "queries"])
        writer.writeheader()
        writer.writerows(all_metrics)
    
    print(f"\nSaved metrics to {csv_path}")
    
    # Generate charts with error bars
    generate_charts_with_error_bars(all_metrics, output_dir)
    
    print(f"Parameter sweep completed! Results saved to {output_dir}")


def generate_charts_with_error_bars(metrics: List[Dict[str, Any]], output_dir: Path) -> None:
    """Generate visualization charts with error bars."""
    
    # Prepare data for plotting
    candidate_values = sorted(set(m["candidate_k"] for m in metrics))
    rerank_values = sorted(set(m["rerank_k"] for m in metrics))
    
    # Create figure with subplots
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Effect vs Performance Analysis (P95 with P50-P99 band)', fontsize=16)
    
    # Plot 1: P95 Latency vs Rerank K with error bands
    ax1 = axes[0]
    for candidate_k in candidate_values:
        candidate_data = [m for m in metrics if m["candidate_k"] == candidate_k]
        rerank_vals = [m["rerank_k"] for m in candidate_data]
        p50_vals = [m["p50_ms"] for m in candidate_data]
        p95_vals = [m["p95_ms"] for m in candidate_data]
        p99_vals = [m["p99_ms"] for m in candidate_data]
        
        # Plot P95 line
        ax1.plot(rerank_vals, p95_vals, marker='o', label=f'candidate_k={candidate_k}', linewidth=2)
        # Fill between P50 and P99 for error band
        ax1.fill_between(rerank_vals, p50_vals, p99_vals, alpha=0.25)
    
    ax1.set_xlabel('Rerank K')
    ax1.set_ylabel('Latency (ms)')
    ax1.set_title('Latency vs Rerank K (P95 with P50-P99 band)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Top-1 Change Rate vs Rerank K
    ax2 = axes[1]
    for candidate_k in candidate_values:
        candidate_data = [m for m in metrics if m["candidate_k"] == candidate_k]
        rerank_vals = [m["rerank_k"] for m in candidate_data]
        top1_vals = [m["top1_rate"] * 100 for m in candidate_data]  # Convert to percentage
        
        ax2.plot(rerank_vals, top1_vals, marker='o', label=f'candidate_k={candidate_k}')
    
    ax2.set_xlabel('Rerank K')
    ax2.set_ylabel('Top-1 Changed (%)')
    ax2.set_title('Effect vs Rerank K')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Recall@10 vs Rerank K
    ax3 = axes[2]
    for candidate_k in candidate_values:
        candidate_data = [m for m in metrics if m["candidate_k"] == candidate_k]
        rerank_vals = [m["rerank_k"] for m in candidate_data]
        recall_vals = [m["recall_at10"] * 100 for m in candidate_data]  # Convert to percentage
        
        ax3.plot(rerank_vals, recall_vals, marker='o', label=f'candidate_k={candidate_k}')
    
    ax3.set_xlabel('Rerank K')
    ax3.set_ylabel('Recall@10 (%)')
    ax3.set_title('Quality vs Rerank K')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Save combined chart
    combined_path = output_dir / "sweep_combined.png"
    plt.tight_layout()
    plt.savefig(combined_path, dpi=160, bbox_inches='tight')
    plt.close()
    
    # Save individual charts
    for i, (ax, title) in enumerate(zip(axes, ['p95_vs_rerankk', 'top1_vs_rerankk', 'recall_vs_rerankk'])):
        fig_single, ax_single = plt.subplots(figsize=(8, 6))
        
        # Recreate the plot for individual chart
        for candidate_k in candidate_values:
            candidate_data = [m for m in metrics if m["candidate_k"] == candidate_k]
            rerank_vals = [m["rerank_k"] for m in candidate_data]
            
            if i == 0:  # P95 chart with error bands
                p50_vals = [m["p50_ms"] for m in candidate_data]
                p95_vals = [m["p95_ms"] for m in candidate_data]
                p99_vals = [m["p99_ms"] for m in candidate_data]
                ylabel = 'Latency (ms)'
                
                # Plot P95 line
                ax_single.plot(rerank_vals, p95_vals, marker='o', label=f'candidate_k={candidate_k}', linewidth=2)
                # Fill between P50 and P99 for error band
                ax_single.fill_between(rerank_vals, p50_vals, p99_vals, alpha=0.25)
            elif i == 1:  # Top-1 chart
                vals = [m["top1_rate"] * 100 for m in candidate_data]
                ylabel = 'Top-1 Changed (%)'
                ax_single.plot(rerank_vals, vals, marker='o', label=f'candidate_k={candidate_k}')
            else:  # Recall chart
                vals = [m["recall_at10"] * 100 for m in candidate_data]
                ylabel = 'Recall@10 (%)'
                ax_single.plot(rerank_vals, vals, marker='o', label=f'candidate_k={candidate_k}')
        
        ax_single.set_xlabel('Rerank K')
        ax_single.set_ylabel(ylabel)
        ax_single.set_title(title.replace('_', ' ').title())
        ax_single.legend()
        ax_single.grid(True, alpha=0.3)
        
        individual_path = output_dir / f"{title}.png"
        plt.savefig(individual_path, dpi=160, bbox_inches='tight')
        plt.close()
    
    print(f"Generated charts: {output_dir}/sweep_combined.png")
    print(f"Generated individual charts: p95_vs_rerankk.png, top1_vs_rerankk.png, recall_vs_rerankk.png")


def main():
    parser = argparse.ArgumentParser(description='Generate parameter sweep report')
    parser.add_argument('--config', required=True, help='Path to YAML config file')
    parser.add_argument('--collection', required=True, help='Collection name to search')
    parser.add_argument('--queries', nargs='+', required=True, help='Queries to test')
    parser.add_argument('--candidate-grid', required=True, help='Comma-separated candidate_k values')
    parser.add_argument('--rerank-grid', required=True, help='Comma-separated rerank_k values')
    parser.add_argument('--output-dir', required=True, help='Output directory for results')
    parser.add_argument('--trials', type=int, default=3, help='Number of trials per grid point to measure p50/p95/p99')
    
    args = parser.parse_args()
    
    # Parse grid values
    candidate_grid = [int(x.strip()) for x in args.candidate_grid.split(',')]
    rerank_grid = [int(x.strip()) for x in args.rerank_grid.split(',')]
    
    # Create output directory
    output_dir = Path(args.output_dir)
    
    # Run parameter sweep
    run_parameter_sweep(
        config_path=args.config,
        collection_name=args.collection,
        queries=args.queries,
        candidate_grid=candidate_grid,
        rerank_grid=rerank_grid,
        output_dir=output_dir,
        trials=args.trials
    )


if __name__ == "__main__":
    main()
