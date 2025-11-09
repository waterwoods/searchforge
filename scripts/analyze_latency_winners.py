#!/usr/bin/env python3
"""
analyze_latency_winners.py - P95 Latency Winners Analysis
==========================================================
Analyzes latency grid results and generates winners_latency.json
with parameter→p95 curves and recommendations.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import statistics


def load_job_metrics(job_id: str, runs_dir: Path = Path("/app/.runs")) -> Dict[str, Any]:
    """Load metrics.json for a job."""
    metrics_path = runs_dir / job_id / "metrics.json"
    if not metrics_path.exists():
        return {}
    
    try:
        with open(metrics_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {metrics_path}: {e}", file=sys.stderr)
        return {}


def analyze_parameter_impact(experiments: List[Dict]) -> Dict[str, Any]:
    """Analyze the impact of each parameter on p95 latency."""
    analysis = {}
    
    # Group by dataset type
    for dataset_type in ['gold', 'hard']:
        dataset_exps = [e for e in experiments if e['dataset_type'] == dataset_type]
        if not dataset_exps:
            continue
        
        analysis[dataset_type] = {}
        
        # EfSearch impact
        ef_impact = {}
        for ef in sorted(set(e['ef_search'] for e in dataset_exps)):
            ef_exps = [e for e in dataset_exps if e['ef_search'] == ef]
            ef_impact[ef] = {
                'avg_p95_ms': statistics.mean(e['p95_ms'] for e in ef_exps),
                'avg_recall': statistics.mean(e['recall_at_10'] for e in ef_exps),
                'count': len(ef_exps)
            }
        analysis[dataset_type]['ef_search'] = ef_impact
        
        # Concurrency impact
        conc_impact = {}
        for conc in sorted(set(e['concurrency'] for e in dataset_exps)):
            conc_exps = [e for e in dataset_exps if e['concurrency'] == conc]
            conc_impact[conc] = {
                'avg_p95_ms': statistics.mean(e['p95_ms'] for e in conc_exps),
                'avg_recall': statistics.mean(e['recall_at_10'] for e in conc_exps),
                'count': len(conc_exps)
            }
        analysis[dataset_type]['concurrency'] = conc_impact
        
        # Warmup impact
        warmup_impact = {}
        for warm in sorted(set(e['warm_cache'] for e in dataset_exps)):
            warm_exps = [e for e in dataset_exps if e['warm_cache'] == warm]
            warmup_impact[warm] = {
                'avg_p95_ms': statistics.mean(e['p95_ms'] for e in warm_exps),
                'count': len(warm_exps)
            }
        analysis[dataset_type]['warm_cache'] = warmup_impact
    
    return analysis


def find_best_configs(experiments: List[Dict]) -> Dict[str, Any]:
    """Find best configurations for different criteria."""
    recommendations = {}
    
    # Tier 1: Speed-optimized (lowest p95, recall > 0.85)
    speed_configs = [e for e in experiments if e['recall_at_10'] > 0.85]
    if speed_configs:
        best_speed = min(speed_configs, key=lambda x: x['p95_ms'])
        recommendations['speed_optimized'] = {
            'tier': 1,
            'description': 'Lowest latency with recall > 0.85',
            'config': {
                'ef_search': best_speed['ef_search'],
                'concurrency': best_speed['concurrency'],
                'warm_cache': best_speed['warm_cache']
            },
            'expected_performance': {
                'p95_ms': best_speed['p95_ms'],
                'recall_at_10': best_speed['recall_at_10']
            }
        }
    
    # Tier 2: Balanced (p95 < 1000ms, recall > 0.90)
    balanced_configs = [e for e in experiments if e['recall_at_10'] > 0.90 and e['p95_ms'] < 1000]
    if balanced_configs:
        # Score: minimize (p95_ms + (1 - recall) * 10000)
        best_balanced = min(balanced_configs, key=lambda x: x['p95_ms'] + (1 - x['recall_at_10']) * 10000)
        recommendations['balanced'] = {
            'tier': 2,
            'description': 'P95 < 1000ms with recall > 0.90 (RECOMMENDED)',
            'config': {
                'ef_search': best_balanced['ef_search'],
                'concurrency': best_balanced['concurrency'],
                'warm_cache': best_balanced['warm_cache']
            },
            'expected_performance': {
                'p95_ms': best_balanced['p95_ms'],
                'recall_at_10': best_balanced['recall_at_10']
            },
            'is_default': True
        }
    
    # Tier 3: Quality-optimized (best recall)
    if experiments:
        best_quality = max(experiments, key=lambda x: x['recall_at_10'])
        recommendations['quality_optimized'] = {
            'tier': 3,
            'description': 'Highest recall',
            'config': {
                'ef_search': best_quality['ef_search'],
                'concurrency': best_quality['concurrency'],
                'warm_cache': best_quality['warm_cache']
            },
            'expected_performance': {
                'p95_ms': best_quality['p95_ms'],
                'recall_at_10': best_quality['recall_at_10']
            }
        }
    
    return recommendations


def generate_summary_text(results: Dict[str, Any]) -> str:
    """Generate human-readable summary text."""
    experiments = results['experiments']
    winners = results['winners']
    analysis = results['parameter_analysis']
    recommendations = results['recommendations']
    
    lines = []
    lines.append("=" * 80)
    lines.append("P95 LATENCY OPTIMIZATION SUMMARY")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total experiments: {len(experiments)}")
    lines.append(f"Winners (p95 < 1000ms, recall > 0.90): {len(winners)}")
    lines.append("")
    
    # Parameter impact analysis
    for dataset_type in ['gold', 'hard']:
        if dataset_type not in analysis:
            continue
        
        lines.append(f"{'='*80}")
        lines.append(f"Dataset: {dataset_type.upper()}")
        lines.append(f"{'='*80}")
        lines.append("")
        
        # EfSearch impact
        lines.append("efSearch Impact:")
        for ef, metrics in sorted(analysis[dataset_type]['ef_search'].items()):
            lines.append(f"  efSearch={ef:3d}: avg_p95={metrics['avg_p95_ms']:6.0f}ms, avg_recall={metrics['avg_recall']:.3f}")
        lines.append("")
        
        # Concurrency impact
        lines.append("Concurrency Impact:")
        for conc, metrics in sorted(analysis[dataset_type]['concurrency'].items()):
            lines.append(f"  concurrency={conc:2d}: avg_p95={metrics['avg_p95_ms']:6.0f}ms, avg_recall={metrics['avg_recall']:.3f}")
        lines.append("")
        
        # Warmup impact
        lines.append("Warmup Impact:")
        for warm, metrics in sorted(analysis[dataset_type]['warm_cache'].items()):
            lines.append(f"  warm_cache={warm:3d}: avg_p95={metrics['avg_p95_ms']:6.0f}ms")
        lines.append("")
    
    # Recommendations
    lines.append("=" * 80)
    lines.append("RECOMMENDED CONFIGURATIONS")
    lines.append("=" * 80)
    lines.append("")
    
    for tier_name, rec in recommendations.items():
        lines.append(f"Tier {rec['tier']}: {rec['description']}")
        config = rec['config']
        perf = rec['expected_performance']
        lines.append(f"  efSearch={config['ef_search']}, concurrency={config['concurrency']}, warm_cache={config['warm_cache']}")
        lines.append(f"  Expected: p95={perf['p95_ms']:.0f}ms, recall={perf['recall_at_10']:.3f}")
        if rec.get('is_default'):
            lines.append("  ⭐ DEFAULT RECOMMENDATION")
        lines.append("")
    
    # Default strategy
    lines.append("=" * 80)
    lines.append("DEFAULT STRATEGY")
    lines.append("=" * 80)
    lines.append("")
    
    if 'balanced' in recommendations:
        rec = recommendations['balanced']
        lines.append("Recommended default configuration:")
        lines.append(f"  efSearch={rec['config']['ef_search']}")
        lines.append(f"  concurrency={rec['config']['concurrency']}")
        lines.append(f"  warm_cache={rec['config']['warm_cache']}")
        lines.append("  top_k=10, mmr=false")
        lines.append("")
        lines.append("Expected performance:")
        lines.append(f"  P95 latency: {rec['expected_performance']['p95_ms']:.0f}ms (<1000ms ✓)")
        lines.append(f"  Recall@10: {rec['expected_performance']['recall_at_10']:.3f} (>0.90 ✓)")
    else:
        lines.append("⚠️  No configurations meet p95 < 1000ms with recall > 0.90")
        lines.append("Consider:")
        lines.append("  - Increasing efSearch beyond 96")
        lines.append("  - Optimizing Qdrant HNSW index")
        lines.append("  - Adding more warmup queries")
    
    lines.append("")
    lines.append("=" * 80)
    
    return '\n'.join(lines)


def main():
    """Main analysis function."""
    # Read job entries from stdin (passed from bash script)
    job_entries = [line.strip() for line in sys.stdin if line.strip()]
    
    if not job_entries:
        print("Error: No job entries provided", file=sys.stderr)
        sys.exit(1)
    
    # Parse experiments and load metrics
    experiments = []
    for job_entry in job_entries:
        parts = job_entry.split(':')
        if len(parts) < 6:
            continue
        
        job_id, name, dataset_type, ef_search, concurrency, warm_cache = parts
        
        # Load metrics from job
        metrics = load_job_metrics(job_id)
        if not metrics:
            print(f"Warning: No metrics for {job_id}", file=sys.stderr)
            continue
        
        # Extract metrics
        overall = metrics.get('metrics', {})
        recall = overall.get('recall_at_10', 0)
        p95 = overall.get('p95_ms', 0)
        p50 = overall.get('median_ms', 0)
        
        # Extract latency breakdown
        breakdown = metrics.get('latency_breakdown_ms', {})
        
        experiment = {
            'job_id': job_id,
            'name': name,
            'dataset_type': dataset_type,
            'ef_search': int(ef_search),
            'concurrency': int(concurrency),
            'warm_cache': int(warm_cache),
            'recall_at_10': recall,
            'p95_ms': p95,
            'p50_ms': p50,
            'search_ms': breakdown.get('search', 0),
            'serialize_ms': breakdown.get('serialize', 0),
            'cache_hit_rate': breakdown.get('cache_hit_rate', 0),
            'winner': p95 < 1000 and recall > 0.90
        }
        
        experiments.append(experiment)
        print(f"✓ {name}: recall={recall:.3f}, p95={p95:.0f}ms", file=sys.stderr)
    
    # Filter winners
    winners = [e for e in experiments if e['winner']]
    
    # Analyze parameter impact
    parameter_analysis = analyze_parameter_impact(experiments)
    
    # Find best configurations
    recommendations = find_best_configs(experiments)
    
    # Build results
    results = {
        'experiments': experiments,
        'winners': winners,
        'total_experiments': len(experiments),
        'total_winners': len(winners),
        'target_p95_ms': 1000,
        'min_recall': 0.90,
        'parameter_analysis': parameter_analysis,
        'recommendations': recommendations
    }
    
    # Save results
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    
    # Save full results
    with open(reports_dir / 'latency_grid_all.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save winners only
    with open(reports_dir / 'winners_latency.json', 'w') as f:
        json.dump({
            'winners': winners,
            'total_winners': len(winners),
            'target_p95_ms': 1000,
            'min_recall': 0.90,
            'recommendations': recommendations
        }, f, indent=2)
    
    # Generate and save summary text
    summary_text = generate_summary_text(results)
    with open(reports_dir / 'latency_grid_summary.txt', 'w') as f:
        f.write(summary_text)
    
    # Print summary to stderr
    print("\n" + summary_text, file=sys.stderr)
    
    # Print success message to stderr
    print(f"\n🏆 Found {len(winners)} winning configurations", file=sys.stderr)
    print(f"📊 Results saved to:", file=sys.stderr)
    print(f"   - reports/latency_grid_all.json", file=sys.stderr)
    print(f"   - reports/winners_latency.json", file=sys.stderr)
    print(f"   - reports/latency_grid_summary.txt", file=sys.stderr)


if __name__ == '__main__':
    main()

