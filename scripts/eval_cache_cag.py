#!/usr/bin/env python3
"""
Synthetic evaluation script for Cache-Augmented Generation (CAG).

Generates synthetic workload with repeats to validate cache hit rates and latency improvements.
"""
import time
import random
import json
import numpy as np
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.rag.contracts import CacheConfig, CacheStats
from modules.rag.cache import CAGCache


def stub_embedder(text: str) -> np.ndarray:
    """Stub embedder for semantic policy testing."""
    # Use hash to get consistent but varied vectors
    hash_val = hash(text) % 1000
    vec = np.array([hash_val / 1000.0, (1000 - hash_val) / 1000.0, 0.5])
    return vec / np.linalg.norm(vec)


def simulate_retrieval(query: str) -> tuple[Any, float]:
    """Simulate retrieval with realistic latency."""
    # Base latency ~80ms ± 10ms
    retrieval_ms = random.gauss(80, 10)
    # Simulate result
    result = f"Answer for: {query}"
    return result, max(10, retrieval_ms)  # Ensure positive


def simulate_rerank(result: Any) -> float:
    """Simulate reranking with realistic latency."""
    # Rerank latency ~40ms ± 10ms
    rerank_ms = random.gauss(40, 10)
    return max(5, rerank_ms)  # Ensure positive


def generate_queries(n_queries: int, repeat_rate: float = 0.3) -> List[str]:
    """Generate query workload with repeats.
    
    Args:
        n_queries: Total number of queries to generate
        repeat_rate: Fraction of queries that are repeats
        
    Returns:
        List of query strings
    """
    # Generate base queries
    n_unique = int(n_queries * (1 - repeat_rate))
    base_queries = [f"query about topic {i}" for i in range(n_unique)]
    
    # Add repeats
    queries = base_queries.copy()
    n_repeats = n_queries - n_unique
    for _ in range(n_repeats):
        queries.append(random.choice(base_queries))
    
    # Shuffle to mix repeats throughout
    random.shuffle(queries)
    return queries


def run_experiment(name: str, cache: Any, queries: List[str]) -> Dict[str, Any]:
    """Run experiment with given cache configuration.
    
    Args:
        name: Experiment name
        cache: CAGCache instance or None for cache-off
        queries: List of queries to process
        
    Returns:
        Results dictionary
    """
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")
    
    latencies = []
    
    for i, query in enumerate(queries):
        start = time.perf_counter()
        
        # Check cache
        cached = None
        if cache:
            cached = cache.get(query)
        
        if cached:
            # Cache hit - skip retrieval/rerank
            answer = cached["answer"]
            total_ms = (time.perf_counter() - start) * 1000
            # Track saved latency
            if cache:
                saved_ms = 120.0  # Estimate of retrieval + rerank
                cache.stats.saved_latency_ms += saved_ms
        else:
            # Cache miss or no cache - run full pipeline
            answer, retrieval_ms = simulate_retrieval(query)
            rerank_ms = simulate_rerank(answer)
            
            # Simulate processing time
            time.sleep((retrieval_ms + rerank_ms) / 1000.0)
            
            total_ms = (time.perf_counter() - start) * 1000
            
            # Write back to cache
            if cache:
                cache.put(query, answer, {"cost_ms": total_ms})
        
        latencies.append(total_ms)
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i+1}/{len(queries)} queries...")
    
    # Calculate statistics
    latencies_arr = np.array(latencies)
    mean_latency = np.mean(latencies_arr)
    p50_latency = np.percentile(latencies_arr, 50)
    p95_latency = np.percentile(latencies_arr, 95)
    p99_latency = np.percentile(latencies_arr, 99)
    
    results = {
        "name": name,
        "n_queries": len(queries),
        "mean_latency_ms": round(mean_latency, 2),
        "p50_latency_ms": round(p50_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "p99_latency_ms": round(p99_latency, 2),
    }
    
    # Add cache stats if available
    if cache:
        stats = cache.get_stats().as_dict()
        results.update({
            "cache_hit_rate": round(stats["hit_rate"], 3),
            "cache_hits": stats["hits"],
            "cache_misses": stats["misses"],
            "cache_evictions": stats["evictions"],
            "cache_expired": stats["expired"],
            "saved_latency_ms": round(stats["saved_latency_ms"], 2)
        })
    else:
        results.update({
            "cache_hit_rate": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_evictions": 0,
            "cache_expired": 0,
            "saved_latency_ms": 0.0
        })
    
    return results


def print_results_table(results_list: List[Dict[str, Any]]):
    """Print results in a formatted table."""
    print(f"\n{'='*100}")
    print("CACHE EVALUATION RESULTS")
    print(f"{'='*100}")
    
    # Header
    print(f"{'Config':<25} {'Hit Rate':<12} {'Mean (ms)':<12} {'P95 (ms)':<12} {'Saved (ms)':<12} {'Evict/Exp':<12}")
    print(f"{'-'*100}")
    
    # Rows
    for r in results_list:
        name = r["name"][:24]
        hit_rate = f"{r['cache_hit_rate']:.3f}"
        mean = f"{r['mean_latency_ms']:.1f}"
        p95 = f"{r['p95_latency_ms']:.1f}"
        saved = f"{r['saved_latency_ms']:.1f}"
        evict_exp = f"{r['cache_evictions']}/{r['cache_expired']}"
        
        print(f"{name:<25} {hit_rate:<12} {mean:<12} {p95:<12} {saved:<12} {evict_exp:<12}")
    
    print(f"{'='*100}\n")


def print_chinese_summary(results_list: List[Dict[str, Any]]):
    """Print Chinese summary of results."""
    baseline = results_list[0]  # Cache off
    
    print(f"\n{'='*60}")
    print("📊 缓存评估总结 (Cache Evaluation Summary)")
    print(f"{'='*60}\n")
    
    for r in results_list[1:]:  # Skip baseline
        hit_rate = r['cache_hit_rate']
        p95_improvement = ((baseline['p95_latency_ms'] - r['p95_latency_ms']) / baseline['p95_latency_ms']) * 100
        mean_improvement = ((baseline['mean_latency_ms'] - r['mean_latency_ms']) / baseline['mean_latency_ms']) * 100
        
        print(f"配置: {r['name']}")
        print(f"  ✓ 命中率: {hit_rate:.1%}")
        print(f"  ✓ P95延迟改善: {p95_improvement:.1f}%")
        print(f"  ✓ 平均延迟改善: {mean_improvement:.1f}%")
        print(f"  ✓ 节省总延迟: {r['saved_latency_ms']:.1f}ms")
        print()
    
    print(f"{'='*60}\n")


def main():
    """Main evaluation function."""
    print("Cache-Augmented Generation (CAG) Evaluation")
    print("=" * 60)
    
    # Configuration
    n_queries = 200
    repeat_rate = 0.30
    random.seed(42)
    np.random.seed(42)
    
    print(f"Configuration:")
    print(f"  - Total queries: {n_queries}")
    print(f"  - Repeat rate: {repeat_rate:.0%}")
    print(f"  - Unique queries: ~{int(n_queries * (1 - repeat_rate))}")
    print(f"  - Repeated queries: ~{int(n_queries * repeat_rate)}")
    
    # Generate workload
    print(f"\nGenerating query workload...")
    queries = generate_queries(n_queries, repeat_rate)
    print(f"Generated {len(queries)} queries")
    
    # Run experiments
    results_list = []
    
    # 1. Cache off (baseline)
    results_list.append(run_experiment("Cache OFF (baseline)", None, queries))
    
    # 2. Cache exact policy
    cache_exact = CAGCache(CacheConfig(
        policy="exact",
        ttl_sec=600,
        capacity=10_000,
        normalize=False
    ))
    results_list.append(run_experiment("Cache EXACT (ttl=600s)", cache_exact, queries))
    
    # 3. Cache normalized policy
    cache_normalized = CAGCache(CacheConfig(
        policy="normalized",
        ttl_sec=600,
        capacity=10_000,
        normalize=True
    ))
    results_list.append(run_experiment("Cache NORMALIZED (ttl=600s)", cache_normalized, queries))
    
    # 4. Cache semantic policy
    cache_semantic = CAGCache(CacheConfig(
        policy="semantic",
        ttl_sec=600,
        capacity=10_000,
        fuzzy_threshold=0.85,
        embedder=stub_embedder
    ))
    results_list.append(run_experiment("Cache SEMANTIC (θ=0.85)", cache_semantic, queries))
    
    # Print results
    print_results_table(results_list)
    
    # Print Chinese summary
    print_chinese_summary(results_list)
    
    # Save results to JSON
    output_dir = Path("reports/rag")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "cache_eval.json"
    
    with open(output_file, "w") as f:
        json.dump({
            "config": {
                "n_queries": n_queries,
                "repeat_rate": repeat_rate
            },
            "results": results_list
        }, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    
    # Print conclusion
    print("\n✅ Evaluation complete!")
    baseline = results_list[0]
    best = max(results_list[1:], key=lambda x: x['cache_hit_rate'])
    print(f"Best configuration: {best['name']}")
    print(f"  - Hit rate: {best['cache_hit_rate']:.1%}")
    print(f"  - P95 improvement: {((baseline['p95_latency_ms'] - best['p95_latency_ms']) / baseline['p95_latency_ms']) * 100:.1f}%")


if __name__ == "__main__":
    main()

