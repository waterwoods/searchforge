import argparse, json, time, statistics, csv, itertools, yaml
from pathlib import Path
from modules.search.search_pipeline import SearchPipeline

def recall_at_k(relevants, retrieved_ids, k=10):
    s = set(relevants)
    hit = sum(1 for x in retrieved_ids[:k] if x in s)
    return hit / min(k, len(s) if len(s)>0 else k)

def extract_doc_id_from_result(result):
    """Extract doc_id from search result, prioritizing payload doc_id over document.id"""
    if hasattr(result, 'document') and hasattr(result.document, 'metadata'):
        # Try payload doc_id first
        doc_id = result.document.metadata.get("doc_id")
        if doc_id is not None:
            return str(doc_id)
    
    # Fallback to document.id
    if hasattr(result, 'document') and hasattr(result.document, 'id'):
        return str(result.document.id)
    
    # Fallback to result.id (legacy)
    if hasattr(result, 'id'):
        return str(result.id)
    
    return None

def get_candidate_coverage(pipe, query, gold_doc_ids, max_candidate_k):
    """Get candidate coverage by running retrieval without reranking"""
    # Create a config for maximum candidate retrieval without reranking
    candidate_config = {
        "retriever": {
            "type": "vector",
            "top_k": max_candidate_k
        },
        "reranker": None  # Disable reranking for coverage check
    }
    
    # Temporarily disable reranker for coverage check
    original_reranker = pipe.reranker
    pipe.reranker = None
    
    try:
        # Get maximum candidates
        results = pipe.search(query, collection_name="demo_5k")
        
        # Extract doc_ids from candidates
        candidate_doc_ids = []
        for result in results:
            doc_id = extract_doc_id_from_result(result)
            if doc_id:
                candidate_doc_ids.append(doc_id)
        
        # Calculate coverage
        gold_set = set(str(doc_id) for doc_id in gold_doc_ids)
        candidate_set = set(candidate_doc_ids)
        coverage_hits = len(gold_set.intersection(candidate_set))
        coverage_total = len(gold_set)
        
        return coverage_hits, coverage_total, candidate_doc_ids
        
    finally:
        # Restore original reranker
        pipe.reranker = original_reranker

def run_single_config(mode, cfg, queries, k=10, verbose=False, max_candidate_k=200):
    """Run evaluation with a single configuration"""
    pipe = SearchPipeline(cfg)
    recs, lat = [], []
    detailed_results = []
    
    for q, rel_ids in queries:
        # 1. Get candidate coverage first (without reranking)
        coverage_hits, coverage_total, candidate_doc_ids = get_candidate_coverage(pipe, q, rel_ids, max_candidate_k)
        
        # 2. Run full pipeline with timing (from vector retrieval to final results)
        t0 = time.perf_counter()
        results = pipe.search(q, collection_name="demo_5k")
        t1 = time.perf_counter()
        
        # 3. Extract document IDs using unified method (prioritize payload doc_id)
        ids = []
        for result in results:
            doc_id = extract_doc_id_from_result(result)
            if doc_id:
                ids.append(doc_id)
        
        latency_ms = (t1 - t0) * 1000
        
        # 4. Convert gold IDs to strings for consistent comparison
        gold_ids_str = [str(doc_id) for doc_id in rel_ids]
        
        # 5. Calculate recall using string doc_ids
        recall = recall_at_k(gold_ids_str, ids, k)
        
        recs.append(recall)
        lat.append(latency_ms)
        
        # 6. Calculate hits and misses using string doc_ids
        hits = [doc_id for doc_id in ids[:k] if doc_id in gold_ids_str]
        misses = [doc_id for doc_id in gold_ids_str if doc_id not in ids[:k]]
        
        detailed_result = {
            "query": q,
            "hits": hits,
            "misses": misses,
            "candidate_k": len(results),
            "rerank_k": min(k, len(results)),
            "alpha": cfg.get("retriever", {}).get("alpha", "N/A"),
            "latency_ms": round(latency_ms, 1),
            "recall": round(recall, 3),
            "coverage_hits": coverage_hits,
            "coverage_total": coverage_total
        }
        detailed_results.append(detailed_result)
        
        # 7. Print per-query results in requested format
        if verbose:
            print(f"COVER {coverage_hits}/{coverage_total}, Recall@10={recall:.3f}, hits={hits[:5]}{'...' if len(hits) > 5 else ''}, misses={misses[:5]}{'...' if len(misses) > 5 else ''}")
    
    # 8. Calculate overall statistics
    p50_ms = round(statistics.median(lat), 1)
    p95_ms = round(statistics.quantiles(lat, n=20)[-1], 1) if len(lat) >= 20 else round(sorted(lat)[int(0.95 * len(lat)) - 1], 1)
    recall_macro = round(sum(recs) / len(recs), 3)
    recall_micro = round(sum(recs), 3)  # 总命中数
    
    return {
        "mode": mode,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "recall@10_macro": recall_macro,
        "recall@10_micro": recall_micro,
        "n": len(queries),
        "detailed_results": detailed_results
    }

def load_config_with_overrides(config_path, overrides):
    """Load config and apply overrides"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply overrides
    for key, value in overrides.items():
        if key == "alpha":
            config["retriever"]["alpha"] = value
        elif key == "candidate_k":
            config["retriever"]["vector_top_k"] = value
            config["retriever"]["bm25_top_k"] = value
        elif key == "rerank_k":
            config["rerank_k"] = value
            if "reranker" in config:
                config["reranker"]["top_k"] = value
    
    return config

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="data/goldset.jsonl")
    ap.add_argument("--vector_cfg", default="configs/demo_vector_5k.yaml")
    ap.add_argument("--hybrid_cfg", default="configs/demo_hybrid_5k.yaml")
    ap.add_argument("--alpha-grid", default="0.4,0.6,0.8", help="Comma-separated alpha values for hybrid search")
    ap.add_argument("--candidate-grid", default="100,200", help="Comma-separated candidate_k values")
    ap.add_argument("--rerank-k", type=int, default=50, help="Number of docs to rerank")
    ap.add_argument("--output-csv", default="reports/quality/sweep_metrics.csv", help="Output CSV file for sweep results")
    ap.add_argument("--verbose", action="store_true", help="Print detailed per-query results")
    ap.add_argument("--show-first", type=int, default=2, help="Number of queries to show in detailed breakdown")
    args = ap.parse_args()

    # Load queries
    queries = []
    with open(args.gold) as f:
        for line in f:
            r = json.loads(line)
            queries.append((r["query"], r["relevant_ids"]))

    print(f"Loaded {len(queries)} queries from {args.gold}")
    
    # Parse grid parameters
    alpha_values = [float(x.strip()) for x in args.alpha_grid.split(",")]
    candidate_values = [int(x.strip()) for x in args.candidate_grid.split(",")]
    
    # Create output directory
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    
    # Store results for CSV output
    sweep_results = []
    
    # Get max candidate k for coverage check
    max_candidate_k = max(candidate_values)
    
    # 1. Vector-only baseline (no alpha parameter)
    print("\n=== Vector-only baseline ===")
    vector_config = load_config_with_overrides(args.vector_cfg, {"candidate_k": candidate_values[0], "rerank_k": args.rerank_k})
    vector_result = run_single_config("vector", vector_config, queries, k=10, verbose=args.verbose, max_candidate_k=max_candidate_k)
    sweep_results.append({
        "setting": "vector_only",
        "alpha": "N/A",
        "candidate_k": candidate_values[0],
        "rerank_k": args.rerank_k,
        "p50_ms": vector_result["p50_ms"],
        "p95_ms": vector_result["p95_ms"],
        "recall@10_macro": vector_result["recall@10_macro"],
        "recall@10_micro": vector_result["recall@10_micro"]
    })
    print(f"Overall: macro/micro Recall@10={vector_result['recall@10_macro']}/{vector_result['recall@10_micro']}, p50/p95={vector_result['p50_ms']}/{vector_result['p95_ms']}ms")
    
    # 2. Hybrid search with parameter sweep
    print("\n=== Hybrid search parameter sweep ===")
    for alpha, candidate_k in itertools.product(alpha_values, candidate_values):
        setting_name = f"hybrid_alpha{alpha}_k{candidate_k}"
        print(f"\nTesting {setting_name}...")
        
        hybrid_config = load_config_with_overrides(args.hybrid_cfg, {
            "alpha": alpha, 
            "candidate_k": candidate_k, 
            "rerank_k": args.rerank_k
        })
        
        hybrid_result = run_single_config(setting_name, hybrid_config, queries, k=10, verbose=args.verbose, max_candidate_k=max_candidate_k)
        
        sweep_results.append({
            "setting": setting_name,
            "alpha": alpha,
            "candidate_k": candidate_k,
            "rerank_k": args.rerank_k,
            "p50_ms": hybrid_result["p50_ms"],
            "p95_ms": hybrid_result["p95_ms"],
            "recall@10_macro": hybrid_result["recall@10_macro"],
            "recall@10_micro": hybrid_result["recall@10_micro"]
        })
        
        print(f"Overall: macro/micro Recall@10={hybrid_result['recall@10_macro']}/{hybrid_result['recall@10_micro']}, p50/p95={hybrid_result['p50_ms']}/{hybrid_result['p95_ms']}ms")
    
    # 3. Write results to CSV
    with open(args.output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["setting", "alpha", "candidate_k", "rerank_k", "p50_ms", "p95_ms", "recall@10_macro", "recall@10_micro"])
        writer.writeheader()
        writer.writerows(sweep_results)
    
    print(f"\nSweep results written to {args.output_csv}")
    
    # 4. Find and print best settings
    best_by_recall = max(sweep_results, key=lambda x: x["recall@10_macro"])
    best_by_p95 = min(sweep_results, key=lambda x: x["p95_ms"])
    
    print(f"\nBest by recall@10: {best_by_recall['setting']} (recall={best_by_recall['recall@10_macro']}, p95={best_by_recall['p95_ms']}ms)")
    print(f"Best by p95 latency: {best_by_p95['setting']} (p95={best_by_p95['p95_ms']}ms, recall={best_by_p95['recall@10_macro']})")
    
    # 5. Print detailed per-query breakdown for first N queries
    if sweep_results:
        print(f"\n=== Per-query breakdown (first {args.show_first} queries) ===")
        # Use vector result for detailed breakdown
        for i, detail in enumerate(vector_result["detailed_results"][:args.show_first]):
            print(f"Query {i+1}: {detail['query']}")
            print(f"  COVER {detail['coverage_hits']}/{detail['coverage_total']}, Recall@10={detail['recall']}, hits={detail['hits'][:5]}{'...' if len(detail['hits']) > 5 else ''}, misses={detail['misses'][:5]}{'...' if len(detail['misses']) > 5 else ''}")
            print()

if __name__ == "__main__":
    main()
