#!/usr/bin/env python3
"""
FIQA RAG Benchmark Script
=========================

Single-entry benchmark script for RAG system evaluation on FIQA 10k dataset.

Usage:
    # Quick sanity run (50 queries)
    python scripts/fiqa_rag_benchmark.py --split test --limit 50

    # Full test set with custom k values
    python scripts/fiqa_rag_benchmark.py --split test --k 5,10,20

    # Train set with RAG mode (includes answer generation)
    python scripts/fiqa_rag_benchmark.py --split train --mode rag

Prerequisites:
    - Qdrant running: `docker compose up -d`
    - FIQA data seeded: `make seed-fiqa` (or equivalent)
    - Collection `fiqa_10k_v1` must exist in Qdrant

Output:
    - Run file: `{out_dir}/run.jsonl` (query_id, query_text, doc_ids, scores, latency_ms)
    - Metrics report: `{out_dir}/metrics.json` (Recall@k, MRR@k, nDCG@k, latency stats)
    - Console: Summary table with key metrics
"""

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from experiments.fiqa_lib import load_queries_qrels, normalize_doc_id
    from modules.search.vector_search import VectorSearch
    from tools.eval.recall_eval_dedup import calculate_recall_at_k
    from experiments.metrics import calculate_ndcg_at_k, calculate_mrr
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)

# Try to import RAG components (optional, for RAG mode)
try:
    from services.fiqa_api.services.search_core import perform_search
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("RAG mode not available (search_core not importable). Only retrieval mode will work.")


def find_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    # Fallback: assume we're in project root
    return Path(__file__).resolve().parent.parent


def load_qrels_for_split(split: str, repo_root: Path) -> Dict[str, List[str]]:
    """
    Load qrels for the specified split.
    
    Supports both v1 format (single file) and legacy format (split-specific files).
    """
    # Try v1 format first (no splits, single file)
    v1_qrels_path = repo_root / "data" / "fiqa_v1" / "fiqa_qrels_10k_v1.jsonl"
    if v1_qrels_path.exists():
        logger.info(f"Loading qrels from v1 format: {v1_qrels_path}")
        from experiments.fiqa_lib import load_fiqa_qrels_jsonl
        qrels = load_fiqa_qrels_jsonl(v1_qrels_path)
        # If split is not 'test', we still use the same file (v1 doesn't have splits)
        if split != "test":
            logger.warning(f"v1 format doesn't support splits. Using all qrels for split '{split}'")
        return qrels
    
    # Try v1 TREC format
    v1_trec_path = repo_root / "data" / "fiqa_v1" / "fiqa_qrels_10k_v1.trec"
    if v1_trec_path.exists():
        logger.info(f"Loading qrels from v1 TREC format: {v1_trec_path}")
        from experiments.fiqa_lib import load_fiqa_qrels_trec
        qrels = load_fiqa_qrels_trec(v1_trec_path)
        if split != "test":
            logger.warning(f"v1 format doesn't support splits. Using all qrels for split '{split}'")
        return qrels
    
    # Fallback to legacy format with splits
    legacy_qrels_path = repo_root / "data" / "fiqa" / "qrels" / f"{split}.tsv"
    if legacy_qrels_path.exists():
        logger.info(f"Loading qrels from legacy format: {legacy_qrels_path}")
        from experiments.fiqa_lib import load_fiqa_qrels
        qrels = load_fiqa_qrels(legacy_qrels_path)
        return qrels
    
    raise FileNotFoundError(
        f"Qrels file not found for split '{split}'. Tried:\n"
        f"  - {v1_qrels_path}\n"
        f"  - {v1_trec_path}\n"
        f"  - {legacy_qrels_path}\n"
        f"\nHint: Run `make seed-fiqa` to seed FIQA data."
    )


def check_qdrant_connection(collection_name: str = "fiqa_10k_v1") -> bool:
    """Check if Qdrant is running and collection exists."""
    try:
        searcher = VectorSearch()
        collections = searcher.list_collections()
        if collection_name not in collections:
            logger.error(
                f"Collection '{collection_name}' not found in Qdrant.\n"
                f"Available collections: {collections}\n"
                f"\nHint: Run `make seed-fiqa` to seed the FIQA collection."
            )
            return False
        logger.info(f"✅ Qdrant connection OK. Collection '{collection_name}' found.")
        return True
    except Exception as e:
        logger.error(
            f"Failed to connect to Qdrant: {e}\n"
            f"\nHint: Make sure Qdrant is running: `docker compose up -d`"
        )
        return False


def run_retrieval_query(
    query_text: str,
    collection_name: str,
    top_k: int,
    searcher: VectorSearch
) -> Tuple[List[str], List[float], float]:
    """
    Run a single retrieval query.
    
    Returns:
        (doc_ids, scores, latency_ms)
    """
    start_time = time.perf_counter()
    try:
        results = searcher.vector_search(
            query=query_text,
            collection_name=collection_name,
            top_n=top_k
        )
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        doc_ids = []
        scores = []
        for result in results:
            # Extract doc_id from document metadata (which contains the payload)
            metadata = result.document.metadata if hasattr(result.document, 'metadata') else {}
            doc_id = metadata.get("doc_id") or metadata.get("id") or str(result.document.id)
            score = result.score
            doc_ids.append(str(doc_id))
            scores.append(float(score))
        
        return doc_ids, scores, latency_ms
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"Retrieval failed for query '{query_text[:50]}...': {e}")
        return [], [], latency_ms


def run_rag_query(
    query_text: str,
    collection_name: str,
    top_k: int
) -> Tuple[List[str], List[float], float]:
    """
    Run a single RAG query (retrieval + answer generation).
    
    Returns:
        (doc_ids, scores, latency_ms)
    """
    if not RAG_AVAILABLE:
        raise RuntimeError("RAG mode not available. search_core module not importable.")
    
    start_time = time.perf_counter()
    try:
        # Call perform_search directly (retrieval only for now)
        # Note: Full RAG with answer generation would require LLM setup
        result = perform_search(
            query=query_text,
            top_k=top_k,
            collection=collection_name
        )
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        if not result.get("ok", False):
            logger.warning(f"RAG query returned error: {result.get('error', 'unknown')}")
            return [], [], latency_ms
        
        results = result.get("results", [])
        doc_ids = []
        scores = []
        for item in results:
            doc_id = item.get("id") or item.get("doc_id")
            score = item.get("score", 0.0)
            if doc_id:
                doc_ids.append(str(doc_id))
                scores.append(float(score))
        
        return doc_ids, scores, latency_ms
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"RAG query failed for '{query_text[:50]}...': {e}")
        return [], [], latency_ms


def compute_metrics(
    run_results: List[Dict[str, Any]],
    qrels: Dict[str, List[str]],
    k_values: List[int]
) -> Dict[str, Any]:
    """
    Compute evaluation metrics for all queries.
    
    Returns:
        Dict with metrics for each k value
    """
    metrics = {}
    
    for k in k_values:
        recalls = []
        mrr_scores = []
        ndcg_scores = []
        
        for run in run_results:
            query_id = run["query_id"]
            retrieved_doc_ids = run.get("doc_ids", [])
            relevant_doc_ids = qrels.get(query_id, [])
            
            if not relevant_doc_ids:
                continue  # Skip queries without ground truth
            
            # Doc IDs are already normalized in run_results
            retrieved_normalized = retrieved_doc_ids
            relevant_normalized = [normalize_doc_id(d) for d in relevant_doc_ids]
            relevant_set = {d for d in relevant_normalized if d}
            
            # Calculate Recall@k
            recall = calculate_recall_at_k(
                retrieved_doc_ids=retrieved_normalized[:k],
                relevant_doc_ids=relevant_set,
                k=k
            )
            recalls.append(recall)
            
            # Calculate MRR (uses all retrieved, not just top k)
            mrr = calculate_mrr(
                retrieved_docs=retrieved_normalized,
                relevant_docs=list(relevant_set)
            )
            mrr_scores.append(mrr)
            
            # Calculate nDCG@k
            ndcg = calculate_ndcg_at_k(
                retrieved_docs=retrieved_normalized[:k],
                relevant_docs=list(relevant_set),
                k=k
            )
            ndcg_scores.append(ndcg)
        
        metrics[f"Recall@{k}"] = sum(recalls) / len(recalls) if recalls else 0.0
        metrics[f"MRR@{k}"] = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
        metrics[f"nDCG@{k}"] = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
    
    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="FIQA RAG Benchmark - Evaluate retrieval/RAG system on FIQA 10k dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test"],
        default="test",
        help="Dataset split to use (default: test)"
    )
    parser.add_argument(
        "--k",
        type=str,
        default="5,10,20",
        help="Comma-separated k values for evaluation (default: 5,10,20)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of queries for quick runs (default: None = all queries)"
    )
    parser.add_argument(
        "--mode",
        choices=["retrieval", "rag"],
        default="retrieval",
        help="Evaluation mode: retrieval (vector search only) or rag (with answer generation) (default: retrieval)"
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="results/fiqa_bench",
        help="Output directory for run file and metrics (default: results/fiqa_bench)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic ordering (default: 42)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="fiqa_10k_v1",
        help="Qdrant collection name (default: fiqa_10k_v1)"
    )
    
    args = parser.parse_args()
    
    # Parse k values
    k_values = [int(k.strip()) for k in args.k.split(",")]
    max_k = max(k_values)
    
    # Set random seed
    random.seed(args.seed)
    
    # Find repo root
    repo_root = find_repo_root()
    logger.info(f"Repository root: {repo_root}")
    
    # Check Qdrant connection
    if not check_qdrant_connection(args.collection):
        sys.exit(1)
    
    # Load queries and qrels
    logger.info(f"Loading queries and qrels for split '{args.split}'...")
    
    # v1 format doesn't support splits, so only use it for test split
    use_v1_format = (args.split == "test")
    
    if use_v1_format:
        try:
            # Try v1 format first (only for test split)
            queries, qrels = load_queries_qrels(
                dataset_name="fiqa_10k_v1",
                qrels_name="fiqa_qrels_10k_v1",
                sample=args.limit,
                seed=args.seed
            )
            logger.info(f"Loaded {len(queries)} queries using v1 format")
        except (FileNotFoundError, Exception) as e:
            logger.warning(f"v1 format failed: {e}. Trying legacy format...")
            use_v1_format = False
    
    if not use_v1_format:
        # Use legacy format (supports train/dev/test splits)
        try:
            qrels = load_qrels_for_split(args.split, repo_root)
            # Load queries from legacy path
            queries_file = repo_root / "data" / "fiqa" / "queries.jsonl"
            if not queries_file.exists():
                raise FileNotFoundError(f"Queries file not found: {queries_file}")
            
            from experiments.fiqa_lib import load_fiqa_queries
            queries = load_fiqa_queries(queries_file)
            
            # Filter to queries with qrels
            queries = [q for q in queries if q["query_id"] in qrels]
            
            # Sample if requested
            if args.limit and len(queries) > args.limit:
                random.seed(args.seed)
                queries = random.sample(queries, args.limit)
            
            logger.info(f"Loaded {len(queries)} queries using legacy format (split={args.split})")
        except Exception as e2:
            logger.error(f"Failed to load queries/qrels: {e2}")
            sys.exit(1)
    
    if not queries:
        logger.error("No queries loaded. Exiting.")
        sys.exit(1)
    
    # Initialize searcher
    searcher = VectorSearch()
    
    # Run queries
    logger.info(f"Running {len(queries)} queries in {args.mode} mode (top_k={max_k})...")
    run_results = []
    failures = 0
    latencies = []
    
    for i, query in enumerate(queries, 1):
        query_id = query["query_id"]
        query_text = query.get("text", "") or query.get("query", "")
        
        if not query_text:
            logger.warning(f"Query {query_id} has no text, skipping")
            failures += 1
            continue
        
        if args.mode == "retrieval":
            doc_ids, scores, latency_ms = run_retrieval_query(
                query_text, args.collection, max_k, searcher
            )
        else:  # RAG mode
            doc_ids, scores, latency_ms = run_rag_query(
                query_text, args.collection, max_k
            )
        
        # Normalize doc IDs for consistency
        normalized_doc_ids = [normalize_doc_id(d) for d in doc_ids if normalize_doc_id(d)]
        
        if not normalized_doc_ids:
            failures += 1
        
        latencies.append(latency_ms)
        
        run_results.append({
            "query_id": query_id,
            "query_text": query_text,
            "doc_ids": normalized_doc_ids,
            "scores": scores[:len(normalized_doc_ids)],  # Match length after normalization
            "latency_ms": latency_ms
        })
        
        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(queries)} queries processed")
    
    logger.info(f"Completed {len(run_results)} queries ({failures} failures)")
    
    # Compute metrics
    logger.info("Computing evaluation metrics...")
    metrics = compute_metrics(run_results, qrels, k_values)
    
    # Calculate latency statistics
    if latencies:
        latencies_sorted = sorted(latencies)
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = latencies_sorted[int(len(latencies) * 0.95)] if latencies else 0.0
    else:
        avg_latency = 0.0
        p95_latency = 0.0
    
    # Count total docs retrieved
    total_docs = sum(len(r["doc_ids"]) for r in run_results)
    
    # Build final report
    report = {
        "dataset": "fiqa_10k_v1",
        "split": args.split,
        "mode": args.mode,
        "k_values": k_values,
        "metrics": metrics,
        "counts": {
            "num_queries": len(queries),
            "num_docs_retrieved": total_docs,
            "failures": failures,
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2)
        },
        "config": {
            "collection": args.collection,
            "seed": args.seed,
            "limit": args.limit
        }
    }
    
    # Write run file
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    run_file = out_dir / "run.jsonl"
    logger.info(f"Writing run file to {run_file}...")
    with open(run_file, 'w', encoding='utf-8') as f:
        for run in run_results:
            f.write(json.dumps(run, ensure_ascii=False) + "\n")
    
    # Write metrics report
    metrics_file = out_dir / "metrics.json"
    logger.info(f"Writing metrics report to {metrics_file}...")
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary table
    print("\n" + "="*80)
    print("FIQA RAG Benchmark Results")
    print("="*80)
    print(f"Dataset: {report['dataset']} ({report['split']} split)")
    print(f"Mode: {report['mode']}")
    print(f"Queries: {report['counts']['num_queries']}")
    print(f"Failures: {report['counts']['failures']}")
    print(f"Avg Latency: {report['counts']['avg_latency_ms']:.2f} ms")
    print(f"P95 Latency: {report['counts']['p95_latency_ms']:.2f} ms")
    print("\nMetrics:")
    print("-" * 80)
    for k in k_values:
        print(f"  k={k:2d}:  Recall@{k}={metrics[f'Recall@{k}']:.4f}  "
              f"MRR@{k}={metrics[f'MRR@{k}']:.4f}  "
              f"nDCG@{k}={metrics[f'nDCG@{k}']:.4f}")
    print("="*80)
    print(f"\nRun file: {run_file}")
    print(f"Metrics: {metrics_file}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
