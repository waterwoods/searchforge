#!/usr/bin/env python3
"""
Analyze Chunking Experiment Results

This script analyzes the results from run_chunk_experiments.py and produces:
1. reports/winners_chunk.json - Winners analysis
2. Pareto chart (quality vs latency)
3. Bar charts (index size, build time)
4. Recommendations report

Usage:
    python experiments/analyze_chunk_results.py --input reports/chunk_experiments_*.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_results(input_path: Path) -> Dict[str, Any]:
    """Load experiment results from JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)


def calculate_quality_score(recall: float, ndcg: float) -> float:
    """
    Calculate composite quality score.
    
    Score = 0.6 * Recall@10 + 0.4 * nDCG@10
    """
    return 0.6 * recall + 0.4 * ndcg


def find_pareto_frontier(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find Pareto frontier (quality vs latency).
    
    A point is on the Pareto frontier if no other point has both
    better quality and better (lower) latency.
    """
    pareto = []
    
    for candidate in results:
        candidate_quality = calculate_quality_score(
            candidate['recall_at_10'],
            candidate['ndcg_at_10']
        )
        candidate_latency = candidate['p95_ms']
        
        is_dominated = False
        
        for other in results:
            if other == candidate:
                continue
            
            other_quality = calculate_quality_score(
                other['recall_at_10'],
                other['ndcg_at_10']
            )
            other_latency = other['p95_ms']
            
            # Check if other dominates candidate
            if other_quality >= candidate_quality and other_latency <= candidate_latency:
                if other_quality > candidate_quality or other_latency < candidate_latency:
                    is_dominated = True
                    break
        
        if not is_dominated:
            pareto.append(candidate)
    
    # Sort by latency
    pareto.sort(key=lambda x: x['p95_ms'])
    return pareto


def categorize_winners(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categorize winners into three tiers:
    - Fast: Best latency with acceptable quality (quality >= 0.7 * best_quality)
    - Balanced: Best quality/latency tradeoff (Pareto frontier, middle)
    - High-Quality: Best quality, regardless of latency
    """
    if not results:
        return {}
    
    # Calculate quality scores
    for result in results:
        result['quality_score'] = calculate_quality_score(
            result['recall_at_10'],
            result['ndcg_at_10']
        )
    
    # Find best quality
    best_quality_result = max(results, key=lambda x: x['quality_score'])
    best_quality = best_quality_result['quality_score']
    
    # Find fast tier (best latency with quality >= 0.7 * best_quality)
    acceptable_quality = 0.7 * best_quality
    fast_candidates = [
        r for r in results
        if r['quality_score'] >= acceptable_quality
    ]
    fast_winner = min(fast_candidates, key=lambda x: x['p95_ms']) if fast_candidates else None
    
    # Find high-quality tier (best quality)
    high_quality_winner = best_quality_result
    
    # Find balanced tier (Pareto frontier, middle point)
    pareto = find_pareto_frontier(results)
    if pareto:
        mid_idx = len(pareto) // 2
        balanced_winner = pareto[mid_idx]
    else:
        balanced_winner = None
    
    return {
        'fast': fast_winner,
        'balanced': balanced_winner,
        'high_quality': high_quality_winner,
        'pareto_frontier': pareto
    }


def generate_pareto_chart(
    results: List[Dict[str, Any]],
    pareto: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """Generate Pareto chart (quality vs latency)."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Calculate quality scores
    for r in results:
        r['quality_score'] = calculate_quality_score(
            r['recall_at_10'],
            r['ndcg_at_10']
        )
    
    # Group by collection
    collections = {}
    for r in results:
        col = r['collection']
        if col not in collections:
            collections[col] = []
        collections[col].append(r)
    
    # Color map
    colors = {
        'fiqa_para_50k': 'blue',
        'fiqa_sent_50k': 'green',
        'fiqa_win256_o64_50k': 'red'
    }
    
    markers = {
        'fiqa_para_50k': 'o',
        'fiqa_sent_50k': 's',
        'fiqa_win256_o64_50k': '^'
    }
    
    labels_map = {
        'fiqa_para_50k': 'Paragraph',
        'fiqa_sent_50k': 'Sentence',
        'fiqa_win256_o64_50k': 'Sliding Window'
    }
    
    # Plot all points
    for col_name, col_results in collections.items():
        latencies = [r['p95_ms'] for r in col_results]
        qualities = [r['quality_score'] for r in col_results]
        
        ax.scatter(
            latencies,
            qualities,
            color=colors.get(col_name, 'gray'),
            marker=markers.get(col_name, 'o'),
            label=labels_map.get(col_name, col_name),
            alpha=0.6,
            s=100
        )
    
    # Plot Pareto frontier
    if pareto:
        pareto_latencies = [r['p95_ms'] for r in pareto]
        pareto_qualities = [r['quality_score'] for r in pareto]
        
        ax.plot(
            pareto_latencies,
            pareto_qualities,
            'k--',
            linewidth=2,
            alpha=0.5,
            label='Pareto Frontier'
        )
    
    ax.set_xlabel('p95 Latency (ms)', fontsize=12)
    ax.set_ylabel('Quality Score (0.6*Recall@10 + 0.4*nDCG@10)', fontsize=12)
    ax.set_title('Chunking Strategy Comparison: Quality vs Latency', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Pareto chart saved to {output_path}")


def generate_bar_charts(
    results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """Generate bar charts for index size and build time."""
    # Group by collection (take average across configs)
    collection_stats = {}
    
    for r in results:
        col = r['collection']
        if col not in collection_stats:
            collection_stats[col] = {
                'build_times': [],
                'index_sizes': [],
                'chunks_per_doc': r.get('chunks_per_doc', 0)
            }
        
        collection_stats[col]['build_times'].append(r.get('build_time_sec', 0))
        collection_stats[col]['index_sizes'].append(r.get('index_size_mb', 0))
    
    # Calculate averages
    collections = []
    build_times = []
    index_sizes = []
    chunks_per_doc = []
    
    labels_map = {
        'fiqa_para_50k': 'Paragraph',
        'fiqa_sent_50k': 'Sentence',
        'fiqa_win256_o64_50k': 'Window'
    }
    
    for col_name in sorted(collection_stats.keys()):
        stats = collection_stats[col_name]
        collections.append(labels_map.get(col_name, col_name))
        build_times.append(np.mean(stats['build_times']))
        index_sizes.append(np.mean(stats['index_sizes']))
        chunks_per_doc.append(stats['chunks_per_doc'])
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Build time chart
    x = np.arange(len(collections))
    width = 0.6
    
    bars1 = ax1.bar(x, build_times, width, color=['blue', 'green', 'red'], alpha=0.7)
    ax1.set_xlabel('Chunking Strategy', fontsize=12)
    ax1.set_ylabel('Build Time (seconds)', fontsize=12)
    ax1.set_title('Index Build Time', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(collections)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s',
                ha='center', va='bottom', fontsize=10)
    
    # Index size chart
    bars2 = ax2.bar(x, index_sizes, width, color=['blue', 'green', 'red'], alpha=0.7)
    ax2.set_xlabel('Chunking Strategy', fontsize=12)
    ax2.set_ylabel('Index Size (MB)', fontsize=12)
    ax2.set_title('Index Storage Size', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(collections)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, cpd in zip(bars2, chunks_per_doc):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}MB\n({cpd:.1f} chunks/doc)',
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Bar charts saved to {output_path}")


def generate_recommendations(
    winners: Dict[str, Any],
    output_path: Path
) -> str:
    """Generate recommendations report."""
    lines = []
    
    lines.append("="*60)
    lines.append("CHUNKING STRATEGY RECOMMENDATIONS")
    lines.append("="*60)
    lines.append("")
    
    # Fast tier
    if winners.get('fast'):
        fast = winners['fast']
        lines.append("🚀 FAST TIER (省时)")
        lines.append("-" * 40)
        lines.append(f"Collection: {fast['collection']}")
        lines.append(f"Strategy: {fast['chunking_strategy']}")
        lines.append(f"Config: top_k={fast['top_k']}, MMR={'on' if fast['mmr'] else 'off'}")
        lines.append(f"Recall@10: {fast['recall_at_10']:.4f}")
        lines.append(f"nDCG@10: {fast['ndcg_at_10']:.4f}")
        lines.append(f"p95 Latency: {fast['p95_ms']:.2f} ms")
        lines.append(f"Quality Score: {fast['quality_score']:.4f}")
        lines.append("")
        lines.append("When to use:")
        lines.append("  - Latency is critical (< 100ms required)")
        lines.append("  - Acceptable quality tradeoff")
        lines.append("  - High QPS workloads")
        lines.append("")
    
    # Balanced tier
    if winners.get('balanced'):
        balanced = winners['balanced']
        lines.append("⚖️  BALANCED TIER (均衡)")
        lines.append("-" * 40)
        lines.append(f"Collection: {balanced['collection']}")
        lines.append(f"Strategy: {balanced['chunking_strategy']}")
        lines.append(f"Config: top_k={balanced['top_k']}, MMR={'on' if balanced['mmr'] else 'off'}")
        lines.append(f"Recall@10: {balanced['recall_at_10']:.4f}")
        lines.append(f"nDCG@10: {balanced['ndcg_at_10']:.4f}")
        lines.append(f"p95 Latency: {balanced['p95_ms']:.2f} ms")
        lines.append(f"Quality Score: {balanced['quality_score']:.4f}")
        lines.append("")
        lines.append("When to use:")
        lines.append("  - Good balance of quality and speed")
        lines.append("  - Production default recommendation")
        lines.append("  - Most common use cases")
        lines.append("")
    
    # High-quality tier
    if winners.get('high_quality'):
        hq = winners['high_quality']
        lines.append("🏆 HIGH-QUALITY TIER (高质)")
        lines.append("-" * 40)
        lines.append(f"Collection: {hq['collection']}")
        lines.append(f"Strategy: {hq['chunking_strategy']}")
        lines.append(f"Config: top_k={hq['top_k']}, MMR={'on' if hq['mmr'] else 'off'}")
        lines.append(f"Recall@10: {hq['recall_at_10']:.4f}")
        lines.append(f"nDCG@10: {hq['ndcg_at_10']:.4f}")
        lines.append(f"p95 Latency: {hq['p95_ms']:.2f} ms")
        lines.append(f"Quality Score: {hq['quality_score']:.4f}")
        lines.append("")
        lines.append("When to use:")
        lines.append("  - Quality is paramount")
        lines.append("  - Latency not critical")
        lines.append("  - Research/analysis workloads")
        lines.append("")
    
    # Strategy-specific recommendations
    lines.append("="*60)
    lines.append("STRATEGY-SPECIFIC RECOMMENDATIONS")
    lines.append("="*60)
    lines.append("")
    
    lines.append("📄 PARAGRAPH CHUNKING")
    lines.append("  Pros: Natural semantic boundaries, human-readable")
    lines.append("  Cons: Variable chunk sizes, may miss sentence-level details")
    lines.append("  Best for: Document Q&A, long-form content")
    lines.append("")
    
    lines.append("📝 SENTENCE CHUNKING")
    lines.append("  Pros: Fine-grained matching, consistent sizes")
    lines.append("  Cons: More chunks = more storage/compute")
    lines.append("  Best for: Precise retrieval, short answers")
    lines.append("")
    
    lines.append("🪟 SLIDING WINDOW CHUNKING")
    lines.append("  Pros: No information loss, overlap ensures coverage")
    lines.append("  Cons: Highest storage, potential redundancy")
    lines.append("  Best for: Dense information, no clear boundaries")
    lines.append("")
    
    report_text = "\n".join(lines)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"✅ Recommendations report saved to {output_path}")
    
    return report_text


def main():
    parser = argparse.ArgumentParser(
        description="Analyze chunking experiment results"
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to experiment results JSON file'
    )
    
    args = parser.parse_args()
    
    repo_root = find_repo_root()
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    # Load results
    print(f"Loading results from {input_path}...")
    data = load_results(input_path)
    results = data.get('results', [])
    
    if not results:
        print("❌ No results found in input file")
        sys.exit(1)
    
    print(f"Loaded {len(results)} experiment results")
    
    # Categorize winners
    print("\nAnalyzing results...")
    winners = categorize_winners(results)
    
    # Create output directory
    reports_dir = repo_root / 'reports'
    charts_dir = reports_dir / 'chunk_charts'
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate winners JSON
    winners_path = reports_dir / 'winners_chunk.json'
    winners_data = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source_file': str(input_path),
        'fast': winners.get('fast'),
        'balanced': winners.get('balanced'),
        'high_quality': winners.get('high_quality'),
        'pareto_frontier': winners.get('pareto_frontier', [])
    }
    
    with open(winners_path, 'w', encoding='utf-8') as f:
        json.dump(winners_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Winners JSON saved to {winners_path}")
    
    # Generate Pareto chart
    pareto_chart_path = charts_dir / 'pareto_quality_latency.png'
    generate_pareto_chart(
        results,
        winners.get('pareto_frontier', []),
        pareto_chart_path
    )
    
    # Generate bar charts
    bar_charts_path = charts_dir / 'index_metrics.png'
    generate_bar_charts(results, bar_charts_path)
    
    # Generate recommendations
    recommendations_path = reports_dir / 'chunk_recommendations.txt'
    report_text = generate_recommendations(winners, recommendations_path)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Winners JSON: {winners_path}")
    print(f"Pareto chart: {pareto_chart_path}")
    print(f"Bar charts: {bar_charts_path}")
    print(f"Recommendations: {recommendations_path}")
    print(f"\n{report_text}")


if __name__ == '__main__':
    main()

