#!/usr/bin/env python3
"""
Run0 - FAISS Pure Algorithm Baseline (Cosine Similarity) - V3

This script establishes a pure, network-overhead-free, metrically correct 
algorithm performance baseline using FAISS.

V3 Corrections:
- Fixed timing boundaries (normalize before loops, time only search)
- Standardized three plots (CDF, quality metrics, Pareto point)
- Unified SLA constants from manifest.json
- Enhanced reproducibility (random seeds, filtered evaluation)
- Complete metrics and raw evidence (QPS, JSONL latencies, metrics.json)

Features:
- Loads standardized dataset and SLA constants from manifest.json
- Ensures strict alignment between query vectors and dev set queries
- Builds FAISS index with cosine similarity (L2 normalization + inner product)
- Correctly maps IDs and formats results for BEIR evaluation
- Follows warmup, cold/hot start benchmarking protocol with strict timing
- Generates complete engineering evidence pack
"""

import json
import logging
import pathlib
import platform
import random
import statistics
import time
from typing import Dict, List, Tuple, Optional

import faiss
import numpy as np
from beir.retrieval.evaluation import EvaluateRetrieval

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration Constants
# ============================================================================

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
REPORTS_DIR = SCRIPT_DIR.parent / "reports"
DATASET_PREPARED_DIR = REPORTS_DIR / "dataset_prepared"

# Fallback SLA values (will be overridden from manifest if available)
FALLBACK_SLA = {
    "top_k": 100,
    "warmup_queries": 10,
    "random_seed": 2025
}


# ============================================================================
# Helper Functions
# ============================================================================

def find_dataset_directory() -> pathlib.Path:
    """
    Find the most recent dataset directory in reports/dataset_prepared.
    
    Returns:
        pathlib.Path: Path to dataset directory
    """
    if not DATASET_PREPARED_DIR.exists():
        raise FileNotFoundError(
            f"Dataset prepared directory not found: {DATASET_PREPARED_DIR}"
        )
    
    # Find subdirectories matching fiqa_* pattern
    dataset_dirs = [
        d for d in DATASET_PREPARED_DIR.iterdir()
        if d.is_dir() and d.name.startswith("fiqa_")
    ]
    
    if not dataset_dirs:
        raise FileNotFoundError(
            f"No dataset directories found in {DATASET_PREPARED_DIR}"
        )
    
    # Return the most recent one (by modification time)
    dataset_dir = sorted(dataset_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    logger.info(f"Using dataset directory: {dataset_dir}")
    return dataset_dir


def load_manifest(dataset_dir: pathlib.Path) -> Tuple[Dict, Dict]:
    """
    Load manifest.json and extract dataset paths and SLA defaults.
    
    Args:
        dataset_dir: Path to dataset directory
        
    Returns:
        Tuple of (manifest data, sla_defaults dict)
    """
    manifest_path = dataset_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    logger.info(f"Loaded manifest from {manifest_path}")
    
    # Extract SLA defaults from manifest
    sla_defaults = manifest.get("sla_defaults", {})
    if not isinstance(sla_defaults, dict):
        sla_defaults = {}
    
    # Merge with fallbacks for missing values
    final_sla = FALLBACK_SLA.copy()
    final_sla.update(sla_defaults)
    
    logger.info(f"SLA defaults from manifest: top_k={final_sla['top_k']}, "
                f"warmup_queries={final_sla['warmup_queries']}, "
                f"random_seed={final_sla['random_seed']}")
    
    return manifest, final_sla


def load_queries_dev(dataset_dir: pathlib.Path) -> Tuple[List[str], Dict[str, str]]:
    """
    Load dev queries and create query_id -> text mapping.
    
    Args:
        dataset_dir: Path to dataset directory
        
    Returns:
        Tuple of (query_ids list in order, query_id -> text mapping)
    """
    queries_path = dataset_dir / "queries_dev.jsonl"
    if not queries_path.exists():
        raise FileNotFoundError(f"Queries file not found: {queries_path}")
    
    query_ids = []
    queries_dict = {}
    
    with open(queries_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                query_id = data["query_id"]
                query_text = data["text"]
                query_ids.append(query_id)
                queries_dict[query_id] = query_text
    
    logger.info(f"Loaded {len(query_ids)} dev queries from {queries_path}")
    return query_ids, queries_dict


def load_qrels_dev(dataset_dir: pathlib.Path) -> Dict[str, Dict[str, int]]:
    """
    Load dev qrels in BEIR format.
    
    Args:
        dataset_dir: Path to dataset directory
        
    Returns:
        Dict[str, Dict[str, int]]: {query_id: {doc_id: relevance_score}}
    """
    qrels_path = dataset_dir / "qrels_dev.tsv"
    if not qrels_path.exists():
        raise FileNotFoundError(f"Qrels file not found: {qrels_path}")
    
    qrels = {}
    
    with open(qrels_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num == 1:  # Skip header
                continue
            if line.strip():
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    query_id, doc_id, score = parts[0], parts[1], int(parts[2])
                    if query_id not in qrels:
                        qrels[query_id] = {}
                    if score > 0:  # Only include positive relevance
                        qrels[query_id][doc_id] = score
    
    logger.info(f"Loaded qrels for {len(qrels)} queries from {qrels_path}")
    return qrels


def load_corpus_and_build_id_map(dataset_dir: pathlib.Path) -> Tuple[List[Dict], List[str]]:
    """
    Load processed corpus and build row_idx -> doc_id mapping.
    
    Args:
        dataset_dir: Path to dataset directory
        
    Returns:
        Tuple of (corpus data list, id_map: row_idx -> doc_id)
    """
    corpus_path = dataset_dir / "processed_corpus.jsonl"
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")
    
    corpus_data = []
    id_map = []  # row_idx -> doc_id
    
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for row_idx, line in enumerate(f):
            if line.strip():
                data = json.loads(line)
                doc_id = data["doc_id"]
                corpus_data.append(data)
                id_map.append(doc_id)
    
    logger.info(f"Loaded {len(corpus_data)} documents from {corpus_path}")
    logger.info(f"Built ID map: {len(id_map)} entries")
    return corpus_data, id_map


def load_embeddings(dataset_dir: pathlib.Path, manifest: Dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load document and query embeddings.
    
    Args:
        dataset_dir: Path to dataset directory
        manifest: Manifest data
        
    Returns:
        Tuple of (doc_embeddings, query_embeddings)
    """
    # Load document embeddings
    doc_emb_path = dataset_dir / manifest["output_files"]["primary_embeddings"]
    if not doc_emb_path.exists():
        raise FileNotFoundError(f"Document embeddings not found: {doc_emb_path}")
    
    doc_embeddings = np.load(doc_emb_path)
    logger.info(f"Loaded document embeddings: shape={doc_embeddings.shape}")
    
    # Load query embeddings
    query_emb_path = dataset_dir / manifest["output_files"]["primary_query_embeddings"]
    if not query_emb_path.exists():
        raise FileNotFoundError(f"Query embeddings not found: {query_emb_path}")
    
    query_embeddings = np.load(query_emb_path)
    logger.info(f"Loaded query embeddings: shape={query_embeddings.shape}")
    
    return doc_embeddings, query_embeddings


def load_all_query_ids(dataset_dir: pathlib.Path, manifest: Dict) -> List[str]:
    """
    Load all query IDs from queries_subset file to determine embedding order.
    
    Args:
        dataset_dir: Path to dataset directory
        manifest: Manifest data
        
    Returns:
        List[str]: Query IDs in the same order as embeddings
    """
    subset_queries_path = dataset_dir / manifest["output_files"]["queries_subset"]
    if not subset_queries_path.exists():
        raise FileNotFoundError(f"Queries subset file not found: {subset_queries_path}")
    
    all_query_ids = []
    with open(subset_queries_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                all_query_ids.append(data["query_id"])
    
    logger.info(f"Loaded {len(all_query_ids)} query IDs from subset file")
    return all_query_ids


def align_query_vectors(
    query_ids: List[str],
    queries_dict: Dict[str, str],
    all_query_embeddings: np.ndarray,
    dataset_dir: pathlib.Path,
    manifest: Dict
) -> np.ndarray:
    """
    Align query vectors to match dev set query order.
    
    The query embeddings are stored in the same order as queries_subset.jsonl.
    We need to map dev query IDs to their positions in the full query list.
    
    Args:
        query_ids: List of dev query IDs in desired order
        queries_dict: Mapping of query_id -> text (for validation)
        all_query_embeddings: Full query embeddings array (ordered by queries_subset)
        dataset_dir: Path to dataset directory
        manifest: Manifest data
        
    Returns:
        np.ndarray: Aligned query embeddings for dev set
    """
    logger.info("Aligning query vectors with dev set...")
    
    # Load all query IDs to determine embedding order
    all_query_ids = load_all_query_ids(dataset_dir, manifest)
    
    if len(all_query_ids) != len(all_query_embeddings):
        raise ValueError(
            f"Query ID count ({len(all_query_ids)}) doesn't match "
            f"embedding count ({len(all_query_embeddings)})"
        )
    
    # Build mapping from query_id to embedding index
    query_id_to_idx = {qid: idx for idx, qid in enumerate(all_query_ids)}
    
    # Extract embeddings for dev queries in the correct order
    aligned_embeddings = []
    missing_ids = []
    
    for query_id in query_ids:
        if query_id in query_id_to_idx:
            idx = query_id_to_idx[query_id]
            aligned_embeddings.append(all_query_embeddings[idx])
        else:
            missing_ids.append(query_id)
    
    if missing_ids:
        logger.error(f"Missing {len(missing_ids)} query IDs in embeddings")
        logger.error(f"First few missing: {missing_ids[:5]}")
        raise ValueError(f"Could not align {len(missing_ids)} query vectors")
    
    aligned_array = np.vstack(aligned_embeddings)
    logger.info(f"Aligned {len(aligned_embeddings)} query vectors: shape={aligned_array.shape}")
    
    return aligned_array


def normalize_query_vectors(query_embeddings: np.ndarray) -> np.ndarray:
    """
    Normalize all query vectors using L2 normalization.
    
    Args:
        query_embeddings: Query embeddings array (N x D)
        
    Returns:
        np.ndarray: Normalized query embeddings
    """
    logger.info("L2 normalizing all query vectors...")
    
    # Convert to float32
    query_embeddings = query_embeddings.astype(np.float32)
    
    # Normalize in-place
    faiss.normalize_L2(query_embeddings)
    
    logger.info(f"Normalized {len(query_embeddings)} query vectors")
    return query_embeddings


def build_faiss_index(doc_embeddings: np.ndarray) -> faiss.Index:
    """
    Build FAISS index with cosine similarity (L2 normalization + inner product).
    
    Args:
        doc_embeddings: Document embeddings array (N x D)
        
    Returns:
        faiss.Index: Built FAISS index
    """
    logger.info("Building FAISS index...")
    
    # Get dimension
    dimension = doc_embeddings.shape[1]
    logger.info(f"Embedding dimension: {dimension}")
    
    # Convert to float32 (required by FAISS)
    doc_embeddings = doc_embeddings.astype(np.float32)
    
    # L2 normalize document vectors
    logger.info("L2 normalizing document vectors...")
    faiss.normalize_L2(doc_embeddings)
    
    # Create inner product index (for cosine similarity on normalized vectors)
    index = faiss.IndexFlatIP(dimension)
    logger.info(f"Created FAISS IndexFlatIP with dimension {dimension}")
    
    # Add vectors to index
    logger.info(f"Adding {len(doc_embeddings)} vectors to index...")
    index.add(doc_embeddings)
    
    logger.info(f"Index built successfully. Total vectors: {index.ntotal}")
    return index


def benchmark_search(
    index: faiss.Index,
    normalized_query_embeddings: np.ndarray,
    query_ids: List[str],
    id_map: List[str],
    top_k: int,
    warmup_queries: int
) -> Tuple[List[float], List[float], Dict[str, Dict[str, float]], float]:
    """
    Perform warmup, cold start, and hot start benchmarking.
    
    V3 Correction: All query vectors are normalized BEFORE the loops.
    Timing ONLY wraps index.search().
    ID mapping and result formatting happen AFTER timing loops.
    
    Args:
        index: FAISS index
        normalized_query_embeddings: Pre-normalized query embeddings array
        query_ids: List of query IDs
        id_map: Row index -> doc_id mapping
        top_k: Number of top results to retrieve
        warmup_queries: Number of warmup queries
        
    Returns:
        Tuple of (cold_latencies, hot_latencies, retrieval_results, hot_total_time_sec)
    """
    logger.info("=" * 80)
    logger.info("Starting Benchmark Protocol")
    logger.info("=" * 80)
    
    num_queries = len(query_ids)
    logger.info(f"Total queries: {num_queries}")
    logger.info(f"Warmup queries: {warmup_queries}")
    logger.info(f"Top-K: {top_k}")
    logger.info("Note: Query vectors are pre-normalized. Timing only wraps index.search().")
    
    # Initialize results
    cold_latencies = []
    hot_latencies = []
    cold_search_results = []  # Store (distances, indices) for later processing
    hot_total_time_start = None
    hot_total_time_end = None
    
    # ========================================================================
    # Warmup Phase
    # ========================================================================
    logger.info("-" * 80)
    logger.info("Phase 1: Warmup")
    logger.info("-" * 80)
    
    for i in range(min(warmup_queries, num_queries)):
        query_vec = normalized_query_embeddings[i:i+1]  # Already normalized
        
        # Perform search (no timing)
        _ = index.search(query_vec, top_k)
        
        if (i + 1) % 10 == 0:
            logger.info(f"Warmup: {i + 1}/{warmup_queries}")
    
    logger.info(f"Warmup completed: {warmup_queries} queries")
    
    # ========================================================================
    # Cold Start Phase - TIMING ONLY index.search()
    # ========================================================================
    logger.info("-" * 80)
    logger.info("Phase 2: Cold Start Benchmark (timing only index.search())")
    logger.info("-" * 80)
    
    for i in range(num_queries):
        query_vec = normalized_query_embeddings[i:i+1]  # Already normalized
        
        # Time ONLY the search call
        start_time = time.perf_counter()
        distances, indices = index.search(query_vec, top_k)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000.0
        cold_latencies.append(latency_ms)
        cold_search_results.append((distances, indices))
        
        if (i + 1) % 50 == 0:
            logger.info(f"Cold start: {i + 1}/{num_queries}")
    
    logger.info(f"Cold start completed: {num_queries} queries")
    
    # ========================================================================
    # Hot Start Phase - TIMING ONLY index.search()
    # ========================================================================
    logger.info("-" * 80)
    logger.info("Phase 3: Hot Start Benchmark (timing only index.search())")
    logger.info("-" * 80)
    
    hot_total_time_start = time.perf_counter()
    
    for i in range(num_queries):
        query_vec = normalized_query_embeddings[i:i+1]  # Already normalized
        
        # Time ONLY the search call
        start_time = time.perf_counter()
        distances, indices = index.search(query_vec, top_k)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000.0
        hot_latencies.append(latency_ms)
        
        if (i + 1) % 50 == 0:
            logger.info(f"Hot start: {i + 1}/{num_queries}")
    
    hot_total_time_end = time.perf_counter()
    hot_total_time_sec = hot_total_time_end - hot_total_time_start
    
    logger.info(f"Hot start completed: {num_queries} queries")
    logger.info(f"Hot start total time: {hot_total_time_sec:.3f} seconds")
    
    # ========================================================================
    # Post-processing: ID Mapping and Result Formatting (OUTSIDE timing loops)
    # ========================================================================
    logger.info("-" * 80)
    logger.info("Post-processing: ID mapping and result formatting")
    logger.info("-" * 80)
    
    retrieval_results = {}
    for i, (distances, indices) in enumerate(cold_search_results):
        query_id = query_ids[i]
        
        # Map row indices to doc_ids
        doc_scores = {}
        for j in range(len(indices[0])):
            row_idx = int(indices[0][j])
            doc_id = id_map[row_idx]
            score = float(distances[0][j])
            doc_scores[doc_id] = score
        
        retrieval_results[query_id] = doc_scores
    
    logger.info("=" * 80)
    logger.info("Benchmark Protocol Completed")
    logger.info("=" * 80)
    
    return cold_latencies, hot_latencies, retrieval_results, hot_total_time_sec


def evaluate_retrieval_quality(
    qrels: Dict[str, Dict[str, int]],
    retrieval_results: Dict[str, Dict[str, float]],
    k: int = 10
) -> Tuple[Dict[str, float], int]:
    """
    Evaluate retrieval quality using BEIR EvaluateRetrieval.
    
    V3 Correction: Only evaluate queries that have at least one relevant document in qrels.
    
    Args:
        qrels: Ground truth qrels
        retrieval_results: Retrieval results {query_id: {doc_id: score}}
        k: Top-K for evaluation
        
    Returns:
        Tuple of (metrics dict, number of queries used for evaluation)
    """
    logger.info("Evaluating retrieval quality...")
    
    # Filter: only queries with qrels
    filtered_qrels = {qid: rels for qid, rels in qrels.items() if len(rels) > 0}
    filtered_results = {qid: results for qid, results in retrieval_results.items() 
                       if qid in filtered_qrels}
    
    eval_queries_count = len(filtered_qrels)
    logger.info(f"Evaluating {eval_queries_count} queries (with qrels) out of "
                f"{len(retrieval_results)} total queries")
    
    if eval_queries_count == 0:
        logger.warning("No queries with qrels found for evaluation")
        return {
            f"Recall@{k}": 0.0,
            f"nDCG@{k}": 0.0,
            f"MRR@{k}": 0.0
        }, 0
    
    evaluator = EvaluateRetrieval()
    
    # Evaluate using standard evaluate method (returns tuple of dicts)
    # BEIR returns: (ndcg_dict, map_dict, recall_dict, precision_dict)
    ndcg_dict, map_dict, recall_dict, precision_dict = evaluator.evaluate(filtered_qrels, filtered_results, [k])
    
    # Extract metrics
    recall_at_k = recall_dict.get(f"Recall@{k}", 0.0)
    ndcg_at_k = ndcg_dict.get(f"NDCG@{k}", 0.0)
    
    # Calculate MRR manually
    mrr_scores = []
    for query_id in filtered_qrels.keys():
        if query_id not in filtered_results:
            continue
        relevant_docs = set(filtered_qrels[query_id].keys())
        result_docs = list(filtered_results[query_id].keys())
        
        # Find rank of first relevant document
        for rank, doc_id in enumerate(result_docs[:k], start=1):
            if doc_id in relevant_docs:
                mrr_scores.append(1.0 / rank)
                break
        else:
            mrr_scores.append(0.0)
    
    mrr_at_k = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    
    logger.info(f"Retrieval Quality Metrics (@{k}):")
    logger.info(f"  Recall@{k}: {recall_at_k:.4f}")
    logger.info(f"  nDCG@{k}: {ndcg_at_k:.4f}")
    logger.info(f"  MRR@{k}: {mrr_at_k:.4f}")
    logger.info(f"  Eval queries used: {eval_queries_count}")
    
    return {
        f"Recall@{k}": recall_at_k,
        f"nDCG@{k}": ndcg_at_k,
        f"MRR@{k}": mrr_at_k
    }, eval_queries_count


def calculate_percentiles(latencies: List[float]) -> Dict[str, float]:
    """Calculate p50, p95, p99 percentiles."""
    if not latencies:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    return {
        "p50": sorted_latencies[int(n * 0.50)],
        "p95": sorted_latencies[int(n * 0.95)],
        "p99": sorted_latencies[int(n * 0.99)]
    }


def get_environment_info() -> Dict:
    """Get environment information for the report."""
    import sys
    try:
        import psutil
        cpu_count = psutil.cpu_count(logical=True)
        ram_total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except ImportError:
        cpu_count = "unknown"
        ram_total_gb = "unknown"
    
    try:
        import faiss
        faiss_version = getattr(faiss, "__version__", "unknown")
    except:
        faiss_version = "unknown"
    
    return {
        "cpu_info": platform.processor() or platform.machine(),
        "cpu_count": cpu_count,
        "ram_total_gb": ram_total_gb,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "faiss_version": faiss_version
    }


def generate_three_plots(
    output_dir: pathlib.Path,
    cold_latencies: List[float],
    hot_latencies: List[float],
    quality_metrics: Dict[str, float],
    hot_p95_ms: float
):
    """
    Generate the three standard plots required by V3.
    
    1. latency_cdf.png: CDF curves for cold and hot start
    2. quality_metrics.png: Bar chart of Recall@10, nDCG@10, MRR@10
    3. pareto_point.png: Single scatter point (hot_p95_ms, Recall@10)
    
    Args:
        output_dir: Output directory
        cold_latencies: Cold start latency list
        hot_latencies: Hot start latency list
        quality_metrics: Dictionary with quality metrics (Recall@10, nDCG@10, MRR@10)
        hot_p95_ms: Hot run P95 latency in milliseconds
    """
    try:
        import matplotlib.pyplot as plt
        
        logger.info("Generating three standard plots...")
        
        # Extract quality metrics with explicit error handling
        recall_at_10 = quality_metrics.get('Recall@10', 0.0)
        ndcg_at_10 = quality_metrics.get('nDCG@10', 0.0)
        mrr_at_10 = quality_metrics.get('MRR@10', 0.0)
        
        logger.info(f"Plotting with values: Recall@10={recall_at_10:.4f}, "
                   f"nDCG@10={ndcg_at_10:.4f}, MRR@10={mrr_at_10:.4f}, "
                   f"hot_p95_ms={hot_p95_ms:.4f}")
        
        # Plot 1: Latency CDF
        sorted_cold = sorted(cold_latencies)
        sorted_hot = sorted(hot_latencies)
        y_cold = np.arange(1, len(sorted_cold) + 1) / len(sorted_cold)
        y_hot = np.arange(1, len(sorted_hot) + 1) / len(sorted_hot)
        
        plt.figure(figsize=(8, 6))
        plt.plot(sorted_cold, y_cold, label='Cold Start', color='blue', linewidth=2)
        plt.plot(sorted_hot, y_hot, label='Hot Start', color='red', linewidth=2)
        plt.xlabel('Latency (ms)', fontsize=12)
        plt.ylabel('Cumulative Probability', fontsize=12)
        plt.title('Latency CDF', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        cdf_path = output_dir / "latency_cdf.png"
        plt.savefig(cdf_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {cdf_path}")
        
        # Plot 2: Quality Metrics Bar Chart
        metrics_names = ['Recall@10', 'nDCG@10', 'MRR@10']
        metrics_values = [recall_at_10, ndcg_at_10, mrr_at_10]
        
        # Validate values are not zero/empty
        if not metrics_values or all(v == 0.0 for v in metrics_values):
            logger.warning("All quality metrics are zero, plotting may be incorrect")
        
        plt.figure(figsize=(8, 6))
        bars = plt.bar(metrics_names, metrics_values, color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.7)
        plt.ylabel('Score', fontsize=12)
        plt.title('Retrieval Quality Metrics', fontsize=14, fontweight='bold')
        y_max = max(metrics_values) * 1.1 if metrics_values and max(metrics_values) > 0 else 1.0
        plt.ylim(0, y_max)
        
        # Add value labels on bars
        for bar, value in zip(bars, metrics_values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + y_max * 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontsize=10)
        
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        quality_path = output_dir / "quality_metrics.png"
        plt.savefig(quality_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {quality_path}")
        
        # Plot 3: Pareto Point
        # Ensure we're using the exact values passed to the function
        plt.figure(figsize=(8, 6))
        plt.scatter([hot_p95_ms], [recall_at_10], s=200, color='red', 
                   marker='o', edgecolors='black', linewidths=2, zorder=3)
        plt.xlabel('Hot Run P95 Latency (ms)', fontsize=12)
        plt.ylabel('Recall@10', fontsize=12)
        plt.title('Pareto Point: Performance vs Quality', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        # Set axis limits to show the point clearly
        plt.xlim(max(0, hot_p95_ms * 0.8), hot_p95_ms * 1.2)
        plt.ylim(max(0, recall_at_10 * 0.8), min(1.0, recall_at_10 * 1.2))
        
        # Add annotation
        plt.annotate(f'({hot_p95_ms:.4f}, {recall_at_10:.4f})',
                    xy=(hot_p95_ms, recall_at_10),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=10, ha='left')
        
        plt.tight_layout()
        pareto_path = output_dir / "pareto_point.png"
        plt.savefig(pareto_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {pareto_path}")
        
    except ImportError:
        logger.warning("matplotlib not available, skipping plots")
    except Exception as e:
        logger.error(f"Error generating plots: {e}", exc_info=True)
        raise


def generate_evidence_pack(
    output_dir: pathlib.Path,
    cold_latencies: List[float],
    hot_latencies: List[float],
    retrieval_results: Dict[str, Dict[str, float]],
    quality_metrics: Dict[str, float],
    eval_queries_count: int,
    manifest: Dict,
    sla_defaults: Dict,
    qps_hot: float
):
    """
    Generate complete engineering evidence pack with V3 corrections.
    
    Args:
        output_dir: Output directory
        cold_latencies: Cold start latencies
        hot_latencies: Hot start latencies
        retrieval_results: Retrieval results
        quality_metrics: Quality evaluation metrics
        eval_queries_count: Number of queries used for evaluation
        manifest: Manifest data
        sla_defaults: SLA defaults used
        qps_hot: QPS calculated from hot run
    """
    logger.info("Generating evidence pack...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save raw evidence files (JSONL format for latencies)
    logger.info("Saving raw evidence files...")
    
    # Save latencies as JSONL (one latency per line)
    cold_lat_path = output_dir / "latencies_cold.jsonl"
    with open(cold_lat_path, 'w') as f:
        for latency_ms in cold_latencies:
            f.write(json.dumps({"latency_ms": latency_ms}) + '\n')
    logger.info(f"Saved cold latencies (JSONL): {cold_lat_path}")
    
    hot_lat_path = output_dir / "latencies_hot.jsonl"
    with open(hot_lat_path, 'w') as f:
        for latency_ms in hot_latencies:
            f.write(json.dumps({"latency_ms": latency_ms}) + '\n')
    logger.info(f"Saved hot latencies (JSONL): {hot_lat_path}")
    
    # Save retrieval results
    results_path = output_dir / "results_dev.json"
    with open(results_path, 'w') as f:
        json.dump(retrieval_results, f, indent=2)
    logger.info(f"Saved retrieval results: {results_path}")
    
    # Calculate performance metrics
    cold_stats = calculate_percentiles(cold_latencies)
    hot_stats = calculate_percentiles(hot_latencies)
    
    cold_mean = statistics.mean(cold_latencies) if cold_latencies else 0.0
    hot_mean = statistics.mean(hot_latencies) if hot_latencies else 0.0
    
    # Get environment info
    env_info = get_environment_info()
    
    # Generate metrics.json
    metrics_data = {
        "performance": {
            "cold_start": {
                "mean_ms": round(cold_mean, 3),
                "p50_ms": round(cold_stats["p50"], 3),
                "p95_ms": round(cold_stats["p95"], 3),
                "p99_ms": round(cold_stats["p99"], 3),
                "total_queries": len(cold_latencies)
            },
            "hot_start": {
                "mean_ms": round(hot_mean, 3),
                "p50_ms": round(hot_stats["p50"], 3),
                "p95_ms": round(hot_stats["p95"], 3),
                "p99_ms": round(hot_stats["p99"], 3),
                "total_queries": len(hot_latencies),
                "qps_hot_single_thread": round(qps_hot, 3)
            }
        },
        "quality": quality_metrics,
        "evaluation": {
            "eval_queries_count": eval_queries_count,
            "total_queries": len(retrieval_results)
        }
    }
    
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    logger.info(f"Saved metrics: {metrics_path}")
    
    # Generate YAML report
    yaml_path = output_dir / "baseline_faiss_pure.yaml"
    report = {
        "experiment_name": "Run0 - FAISS Pure Algorithm Baseline (Cosine)",
        "version": "V3",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset": {
            "source": manifest.get("source_dataset", "unknown"),
            "corpus_count": manifest.get("subset_corpus_count", 0),
            "dev_queries_count": manifest.get("data_split", {}).get("dev_queries_count", 0),
            "embedding_model": manifest.get("models", {}).get("primary", {}).get("name", "unknown"),
            "embedding_dimension": manifest.get("models", {}).get("primary", {}).get("dimension", 0)
        },
        "sla_defaults": {
            "top_k": sla_defaults["top_k"],
            "warmup_queries": sla_defaults["warmup_queries"],
            "random_seed": sla_defaults["random_seed"]
        },
        "parameters": {
            "retrieval_tool": "faiss-cpu",
            "faiss_index_type": "IndexFlatIP",
            "distance_metric": "Cosine Similarity (via normalized L2 + IP)",
            "top_k": sla_defaults["top_k"]
        },
        "hardware": {
            "cpu_info": env_info["cpu_info"],
            "cpu_count": env_info["cpu_count"],
            "ram_total_gb": env_info["ram_total_gb"],
            "platform": env_info["platform"]
        },
        "software": {
            "python_version": env_info["python_version"],
            "numpy_version": env_info["numpy_version"],
            "faiss_version": env_info["faiss_version"]
        },
        "results": {
            "performance": {
                "cold_start": {
                    "mean_ms": round(cold_mean, 3),
                    "p50_ms": round(cold_stats["p50"], 3),
                    "p95_ms": round(cold_stats["p95"], 3),
                    "p99_ms": round(cold_stats["p99"], 3),
                    "total_queries": len(cold_latencies)
                },
                "hot_start": {
                    "mean_ms": round(hot_mean, 3),
                    "p50_ms": round(hot_stats["p50"], 3),
                    "p95_ms": round(hot_stats["p95"], 3),
                    "p99_ms": round(hot_stats["p99"], 3),
                    "total_queries": len(hot_latencies),
                    "qps_hot_single_thread": round(qps_hot, 3)
                }
            },
            "quality": quality_metrics,
            "evaluation": {
                "eval_queries_count": eval_queries_count,
                "total_queries": len(retrieval_results)
            }
        },
        "raw_evidence_files": {
            "cold_latencies": "latencies_cold.jsonl",
            "hot_latencies": "latencies_hot.jsonl",
            "retrieval_results": "results_dev.json",
            "metrics": "metrics.json"
        }
    }
    
    # Save as YAML or JSON
    try:
        import yaml
        with open(yaml_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved YAML report: {yaml_path}")
    except ImportError:
        # Fallback to JSON if yaml not available
        json_path = output_dir / "baseline_faiss_pure.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved JSON report (yaml not available): {json_path}")
    
    # Generate three standard plots
    generate_three_plots(
        output_dir,
        cold_latencies,
        hot_latencies,
        quality_metrics,
        hot_stats["p95"]
    )
    
    logger.info("Evidence pack generation completed")


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Run0 - FAISS Pure Algorithm Baseline (V3)")
    logger.info("=" * 80)
    
    try:
        # 1. Find and load dataset
        dataset_dir = find_dataset_directory()
        manifest, sla_defaults = load_manifest(dataset_dir)
        
        # Set random seeds for reproducibility (V3 correction)
        random_seed = sla_defaults["random_seed"]
        random.seed(random_seed)
        np.random.seed(random_seed)
        logger.info(f"Set random seed: {random_seed}")
        
        # Get SLA parameters
        top_k = sla_defaults["top_k"]
        warmup_queries = sla_defaults["warmup_queries"]
        
        # 2. Load data
        logger.info("Loading data...")
        query_ids, queries_dict = load_queries_dev(dataset_dir)
        qrels = load_qrels_dev(dataset_dir)
        corpus_data, id_map = load_corpus_and_build_id_map(dataset_dir)
        
        # 3. Load embeddings
        logger.info("Loading embeddings...")
        doc_embeddings, all_query_embeddings = load_embeddings(dataset_dir, manifest)
        
        # 4. Align query vectors
        logger.info("Aligning query vectors...")
        query_embeddings = align_query_vectors(
            query_ids,
            queries_dict,
            all_query_embeddings,
            dataset_dir,
            manifest
        )
        
        # 5. Normalize query vectors BEFORE benchmarking (V3 correction)
        logger.info("Normalizing query vectors (before benchmarking)...")
        normalized_query_embeddings = normalize_query_vectors(query_embeddings)
        
        # 6. Build FAISS index
        logger.info("Building FAISS index...")
        index = build_faiss_index(doc_embeddings)
        
        # 7. Benchmark (with strict timing boundaries)
        logger.info("Running benchmark with strict timing boundaries...")
        cold_latencies, hot_latencies, retrieval_results, hot_total_time_sec = benchmark_search(
            index,
            normalized_query_embeddings,
            query_ids,
            id_map,
            top_k,
            warmup_queries
        )
        
        # Calculate QPS (V3 correction)
        num_queries = len(hot_latencies)
        qps_hot = num_queries / hot_total_time_sec if hot_total_time_sec > 0 else 0.0
        logger.info(f"Hot run QPS: {qps_hot:.2f} queries/second")
        
        # 8. Evaluate quality (filtered to queries with qrels)
        logger.info("Evaluating retrieval quality (queries with qrels only)...")
        quality_metrics, eval_queries_count = evaluate_retrieval_quality(
            qrels, retrieval_results, k=10
        )
        
        # 9. Generate evidence pack
        output_dir = REPORTS_DIR / "run0_faiss_pure" / time.strftime("%Y%m%d_%H%M%S")
        generate_evidence_pack(
            output_dir,
            cold_latencies,
            hot_latencies,
            retrieval_results,
            quality_metrics,
            eval_queries_count,
            manifest,
            sla_defaults,
            qps_hot
        )
        
        logger.info("=" * 80)
        logger.info("Run0 V3 Completed Successfully!")
        logger.info(f"Output directory: {output_dir}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
