#!/usr/bin/env python3
"""
Run Chunking Experiments

This script runs experiments on three chunking collections:
- fiqa_para_50k
- fiqa_sent_50k
- fiqa_win256_o64_50k

Configuration grid:
- Top-K: [10, 20]
- MMR: [off, λ=0.3]

Metrics recorded:
- Recall@10
- nDCG@10
- p95 latency (ms)
- Index size (MB)
- Build time (sec)

Usage:
    python experiments/run_chunk_experiments.py --api-url http://andy-wsl:8000
"""

import argparse
import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Local imports
from fiqa_lib import (
    load_queries_qrels,
    evaluate_config
)


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_collection_metadata(config_dir: Path, collection_name: str) -> Dict[str, Any]:
    """Load collection metadata from configs/collection_tags/*.json"""
    metadata_path = config_dir / f"{collection_name}.json"
    
    if not metadata_path.exists():
        return {
            'collection_name': collection_name,
            'build_time_sec': 0,
            'index_size_mb': 0,
            'chunking_strategy': 'unknown'
        }
    
    with open(metadata_path, 'r') as f:
        return json.load(f)


def run_experiment(
    api_url: str,
    collection_name: str,
    top_k: int,
    mmr: bool,
    mmr_lambda: float,
    queries: List[Dict[str, str]],
    qrels: Dict[str, List[str]],
    concurrency: int = 16,
    repeats: int = 1,
    timeout_s: float = 15.0,
    warmup: int = 5
) -> Dict[str, Any]:
    """
    Run a single experiment configuration.
    
    Returns:
        Dictionary with experiment results
    """
    config = {
        'use_hybrid': False,
        'rerank': False,
        'mmr': mmr,
        'mmr_lambda': mmr_lambda
    }
    
    print(f"\n  Running: collection={collection_name}, top_k={top_k}, mmr={mmr}, lambda={mmr_lambda}")
    
    metrics = evaluate_config(
        config,
        base_url=api_url,
        queries=queries,
        qrels=qrels,
        top_k=top_k,
        concurrency=concurrency,
        repeats=repeats,
        timeout_s=timeout_s,
        warmup=warmup,
        collection=collection_name
    )
    
    result = {
        'collection': collection_name,
        'top_k': top_k,
        'mmr': mmr,
        'mmr_lambda': mmr_lambda if mmr else None,
        'recall_at_10': metrics.get('recall_at_10', 0.0),
        'ndcg_at_10': metrics.get('ndcg_at_10', 0.0),
        'p95_ms': metrics.get('p95_ms', 0.0),
        'mean_latency_ms': metrics.get('mean_latency_ms', 0.0),
        'total_queries': metrics.get('total_queries', 0),
        'failed_queries': metrics.get('failed_queries', 0)
    }
    
    print(f"    Recall@10: {result['recall_at_10']:.4f}")
    print(f"    nDCG@10: {result['ndcg_at_10']:.4f}")
    print(f"    p95 latency: {result['p95_ms']:.2f} ms")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run chunking experiments"
    )
    parser.add_argument(
        '--api-url',
        type=str,
        required=True,
        help='API base URL (e.g., http://andy-wsl:8000)'
    )
    parser.add_argument(
        '--dataset-name',
        type=str,
        default='fiqa_50k_v1',
        help='Dataset name for loading queries/qrels (default: fiqa_50k_v1)'
    )
    parser.add_argument(
        '--qrels-name',
        type=str,
        default='fiqa_qrels_50k_v1',
        help='Qrels name (default: fiqa_qrels_50k_v1)'
    )
    parser.add_argument(
        '--sample-queries',
        type=int,
        default=None,
        help='Sample N queries for faster testing (default: all queries)'
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=16,
        help='Concurrency level (default: 16)'
    )
    parser.add_argument(
        '--repeats',
        type=int,
        default=1,
        help='Number of repeats (default: 1)'
    )
    parser.add_argument(
        '--warmup',
        type=int,
        default=5,
        help='Warmup queries (default: 5)'
    )
    
    args = parser.parse_args()
    
    repo_root = find_repo_root()
    config_dir = repo_root / 'configs' / 'collection_tags'
    reports_dir = repo_root / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Load queries and qrels
    print(f"Loading queries and qrels...")
    print(f"  Dataset: {args.dataset_name}")
    print(f"  Qrels: {args.qrels_name}")
    
    queries, qrels = load_queries_qrels(
        dataset_name=args.dataset_name,
        qrels_name=args.qrels_name,
        sample=args.sample_queries
    )
    
    print(f"Loaded {len(queries)} queries with ground truth")
    
    # Define collections
    collections = [
        'fiqa_para_50k',
        'fiqa_sent_50k',
        'fiqa_win256_o64_50k'
    ]
    
    # Define experiment grid
    top_k_values = [10, 20]
    mmr_configs = [
        {'mmr': False, 'lambda': None},
        {'mmr': True, 'lambda': 0.3}
    ]
    
    # Run all experiments
    all_results = []
    
    print(f"\n{'='*60}")
    print(f"RUNNING EXPERIMENTS")
    print(f"{'='*60}")
    print(f"Collections: {len(collections)}")
    print(f"Top-K values: {top_k_values}")
    print(f"MMR configs: {len(mmr_configs)}")
    print(f"Total experiments: {len(collections) * len(top_k_values) * len(mmr_configs)}")
    print(f"{'='*60}\n")
    
    experiment_count = 0
    total_experiments = len(collections) * len(top_k_values) * len(mmr_configs)
    
    for collection_name in collections:
        print(f"\n{'#'*60}")
        print(f"# Collection: {collection_name}")
        print(f"{'#'*60}")
        
        # Load collection metadata
        metadata = load_collection_metadata(config_dir, collection_name)
        
        for top_k in top_k_values:
            for mmr_config in mmr_configs:
                experiment_count += 1
                print(f"\nExperiment {experiment_count}/{total_experiments}")
                
                try:
                    result = run_experiment(
                        api_url=args.api_url,
                        collection_name=collection_name,
                        top_k=top_k,
                        mmr=mmr_config['mmr'],
                        mmr_lambda=mmr_config['lambda'] or 0.3,
                        queries=queries,
                        qrels=qrels,
                        concurrency=args.concurrency,
                        repeats=args.repeats,
                        warmup=args.warmup
                    )
                    
                    # Add metadata
                    result['build_time_sec'] = metadata.get('build_time_sec', 0)
                    result['index_size_mb'] = metadata.get('index_size_mb', 0)
                    result['chunking_strategy'] = metadata.get('chunking_strategy', 'unknown')
                    result['chunks_per_doc'] = metadata.get('chunks_per_doc', 0)
                    
                    all_results.append(result)
                    
                except Exception as e:
                    print(f"❌ Error in experiment: {e}")
                    continue
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_path = reports_dir / f'chunk_experiments_{timestamp}.json'
    
    results_data = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'config': {
            'api_url': args.api_url,
            'dataset_name': args.dataset_name,
            'qrels_name': args.qrels_name,
            'num_queries': len(queries),
            'concurrency': args.concurrency,
            'repeats': args.repeats,
            'warmup': args.warmup
        },
        'results': all_results
    }
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"EXPERIMENTS COMPLETE")
    print(f"{'='*60}")
    print(f"Total experiments: {len(all_results)}")
    print(f"Results saved to: {results_path}")
    
    # Generate summary
    print(f"\nBest performers by metric:")
    
    if all_results:
        # Best Recall@10
        best_recall = max(all_results, key=lambda x: x['recall_at_10'])
        print(f"\nBest Recall@10: {best_recall['recall_at_10']:.4f}")
        print(f"  Collection: {best_recall['collection']}")
        print(f"  Config: top_k={best_recall['top_k']}, mmr={best_recall['mmr']}")
        
        # Best nDCG@10
        best_ndcg = max(all_results, key=lambda x: x['ndcg_at_10'])
        print(f"\nBest nDCG@10: {best_ndcg['ndcg_at_10']:.4f}")
        print(f"  Collection: {best_ndcg['collection']}")
        print(f"  Config: top_k={best_ndcg['top_k']}, mmr={best_ndcg['mmr']}")
        
        # Best latency (lowest p95)
        best_latency = min(all_results, key=lambda x: x['p95_ms'])
        print(f"\nBest Latency: {best_latency['p95_ms']:.2f} ms")
        print(f"  Collection: {best_latency['collection']}")
        print(f"  Config: top_k={best_latency['top_k']}, mmr={best_latency['mmr']}")
        print(f"  Recall@10: {best_latency['recall_at_10']:.4f}")
    
    print(f"\nNext step: python experiments/analyze_chunk_results.py --input {results_path}")
    
    return results_path


if __name__ == '__main__':
    main()

