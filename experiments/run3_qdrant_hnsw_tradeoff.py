#!/usr/bin/env python3
"""
Run3 - Qdrant HNSW Tradeoff Test (V2 Final Corrected)

This script tests Qdrant service performance with different HNSW ef parameters with critical corrections:
- V2: Only creates collection ONCE, tests all ef values in a loop
- Scientific reproducibility: Each ef value is tested 3 times independently
- Proper warmup: Per-level warmup with current ef value
- Dedicated collection: Creates, populates, tests, and cleans up collection
- Pre-flight check: Verify Qdrant collection configuration matches manifest.json
- HNSW enabled: Use hnsw_ef parameter with exact=False
- gRPC enabled: Use prefer_grpc=True for better performance

Key Features:
- Loads standardized dataset and SLA constants from manifest.json
- Creates dedicated collection "beir_fiqa_1706_benchmark"
- Uploads vectors and payloads from .npy files
- Tests HNSW ef values: [16, 32, 64, 128, 256, 512]
- Each ef value: 3 repeat runs with proper warmup
- Generates evidence pack with mean/std metrics and visualization
- Cleans up collection automatically on exit
"""

import json
import logging
import os
import pathlib
import platform
import random
import statistics
import time
from typing import Dict, List, Tuple, Optional

import numpy as np
from beir.retrieval.evaluation import EvaluateRetrieval
from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams, Distance, VectorParams, PointStruct

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

# V2 CORRECTION: HNSW ef values to test with repeat runs
HNSW_EF_TO_TEST = [16, 32, 64, 128, 256, 512]
REPEAT_RUNS = 3

# Qdrant connection settings
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

# Dedicated collection name for benchmark
COLLECTION_NAME = "beir_fiqa_1706_benchmark"

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
    """Find the most recent dataset directory in reports/dataset_prepared."""
    if not DATASET_PREPARED_DIR.exists():
        raise FileNotFoundError(
            f"Dataset prepared directory not found: {DATASET_PREPARED_DIR}"
        )
    
    dataset_dirs = [
        d for d in DATASET_PREPARED_DIR.iterdir()
        if d.is_dir() and d.name.startswith("fiqa_")
    ]
    
    if not dataset_dirs:
        raise FileNotFoundError(
            f"No dataset directories found in {DATASET_PREPARED_DIR}"
        )
    
    dataset_dir = sorted(dataset_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    logger.info(f"Using dataset directory: {dataset_dir}")
    return dataset_dir


def load_manifest(dataset_dir: pathlib.Path) -> Tuple[Dict, Dict]:
    """Load manifest.json and extract dataset paths and SLA defaults."""
    manifest_path = dataset_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    logger.info(f"Loaded manifest from {manifest_path}")
    
    sla_defaults = manifest.get("sla_defaults", {})
    if not isinstance(sla_defaults, dict):
        sla_defaults = {}
    
    final_sla = FALLBACK_SLA.copy()
    final_sla.update(sla_defaults)
    
    logger.info(f"SLA defaults from manifest: top_k={final_sla['top_k']}, "
                f"warmup_queries={final_sla['warmup_queries']}, "
                f"random_seed={final_sla['random_seed']}")
    
    return manifest, final_sla


def initialize_qdrant_client() -> QdrantClient:
    """Initialize Qdrant client with gRPC enabled."""
    logger.info(f"Initializing Qdrant client: host={QDRANT_HOST}, port={QDRANT_PORT}, prefer_grpc=True")
    client = QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        prefer_grpc=True
    )
    
    try:
        collections = client.get_collections()
        logger.info(f"Connected to Qdrant. Available collections: {[c.name for c in collections.collections]}")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Qdrant: {e}")
    
    return client


def create_and_populate_collection(
    client: QdrantClient,
    collection_name: str,
    dataset_dir: pathlib.Path,
    manifest: Dict
) -> None:
    """Create and populate dedicated collection."""
    logger.info("=" * 80)
    logger.info("Creating and Populating Collection")
    logger.info("=" * 80)
    
    # Delete collection if it exists
    try:
        collections = client.get_collections()
        existing_collections = [c.name for c in collections.collections]
        if collection_name in existing_collections:
            logger.info(f"Deleting existing collection '{collection_name}' for clean start...")
            client.delete_collection(collection_name=collection_name)
            logger.info(f"Collection '{collection_name}' deleted successfully")
    except Exception as e:
        logger.warning(f"Error checking/deleting collection: {e}")
    
    # Get configuration from manifest
    dimension = manifest.get("models", {}).get("primary", {}).get("dimension", 0)
    if dimension == 0:
        raise ValueError("Could not determine vector dimension from manifest")
    
    logger.info(f"Vector dimension: {dimension}")
    logger.info(f"Distance metric: Cosine")
    
    # Create collection
    logger.info(f"Creating collection '{collection_name}'...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=dimension,
            distance=Distance.COSINE
        )
    )
    logger.info(f"Collection '{collection_name}' created successfully")
    
    # Load document embeddings
    doc_emb_path = dataset_dir / manifest["output_files"]["primary_embeddings"]
    if not doc_emb_path.exists():
        raise FileNotFoundError(f"Document embeddings not found: {doc_emb_path}")
    
    doc_embeddings = np.load(doc_emb_path)
    logger.info(f"Loaded document embeddings: shape={doc_embeddings.shape}")
    
    doc_embeddings = np.ascontiguousarray(doc_embeddings, dtype=np.float32)
    
    # Normalize embeddings
    logger.info("L2 normalizing document vectors...")
    norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    doc_embeddings = doc_embeddings / norms
    
    # Load document IDs
    corpus_path = dataset_dir / "processed_corpus.jsonl"
    doc_ids = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                doc_ids.append(data["doc_id"])
    
    logger.info(f"Loaded {len(doc_ids)} document IDs from corpus")
    
    # Upload vectors in batches
    batch_size = 100
    total_points = len(doc_ids)
    total_batches = (total_points + batch_size - 1) // batch_size
    
    logger.info(f"Uploading {total_points} points in {total_batches} batches of {batch_size}...")
    
    for i in range(0, total_points, batch_size):
        batch_end = min(i + batch_size, total_points)
        batch_doc_ids = doc_ids[i:batch_end]
        batch_embeddings = doc_embeddings[i:batch_end]
        
        points = []
        for j, (doc_id, embedding) in enumerate(zip(batch_doc_ids, batch_embeddings)):
            points.append(
                PointStruct(
                    id=i + j,
                    vector=embedding.tolist(),
                    payload={"doc_id": doc_id}
                )
            )
        
        # Upload batch
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        batch_num = (i // batch_size) + 1
        logger.info(f"Uploaded batch {batch_num}/{total_batches} ({len(points)} points)")
    
    logger.info(f"Collection '{collection_name}' populated successfully with {total_points} points")


def preflight_check(client: QdrantClient, collection_name: str, manifest: Dict) -> None:
    """Verify Qdrant collection configuration matches manifest."""
    logger.info("=" * 80)
    logger.info("Pre-flight Check: Verifying Qdrant Configuration")
    logger.info("=" * 80)
    
    try:
        collection_info = client.get_collection(collection_name)
        actual_count = collection_info.points_count
        actual_dim = collection_info.config.params.vectors.size
        actual_distance = collection_info.config.params.vectors.distance.name
        
        expected_count = manifest.get("subset_corpus_count", 0)
        expected_dim = manifest.get("models", {}).get("primary", {}).get("dimension", 0)
        
        logger.info("Expected (from manifest):")
        logger.info(f"  Corpus count: {expected_count}")
        logger.info(f"  Dimension: {expected_dim}")
        logger.info(f"  Distance: Cosine")
        
        logger.info("Actual (from Qdrant):")
        logger.info(f"  Vectors count: {actual_count}")
        logger.info(f"  Dimension: {actual_dim}")
        logger.info(f"  Distance: {actual_distance}")
        
        if actual_count != expected_count:
            logger.warning(f"Count mismatch: expected {expected_count}, got {actual_count}")
        if actual_dim != expected_dim:
            raise ValueError(f"Dimension mismatch: expected {expected_dim}, got {actual_dim}")
        if actual_distance != "COSINE":
            raise ValueError(f"Distance mismatch: expected COSINE, got {actual_distance}")
        
        logger.info("=" * 80)
        logger.info("Pre-flight Check: PASSED ✓")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"Pre-flight check failed: {e}")
        raise


def load_queries_dev(dataset_dir: pathlib.Path) -> Tuple[List[str], Dict[str, str]]:
    """Load dev queries."""
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
    """Load dev qrels in BEIR format."""
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


def load_all_query_ids(dataset_dir: pathlib.Path, manifest: Dict) -> List[str]:
    """Load all query IDs from queries_subset file."""
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
    """Align query vectors to match dev set query order."""
    logger.info("Aligning query vectors with dev set...")
    
    all_query_ids = load_all_query_ids(dataset_dir, manifest)
    
    if len(all_query_ids) != len(all_query_embeddings):
        raise ValueError(
            f"Query ID count ({len(all_query_ids)}) doesn't match "
            f"embedding count ({len(all_query_embeddings)})"
        )
    
    query_id_to_idx = {qid: idx for idx, qid in enumerate(all_query_ids)}
    
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
        raise ValueError(f"Could not align {len(missing_ids)} query vectors")
    
    aligned_array = np.vstack(aligned_embeddings)
    logger.info(f"Aligned {len(aligned_embeddings)} query vectors: shape={aligned_array.shape}")
    
    return aligned_array


def normalize_query_vectors(query_embeddings: np.ndarray) -> np.ndarray:
    """Normalize all query vectors using L2 normalization."""
    logger.info("L2 normalizing all query vectors...")
    
    query_embeddings = np.ascontiguousarray(query_embeddings, dtype=np.float32)
    
    norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    query_embeddings = query_embeddings / norms
    
    logger.info(f"Normalized {len(query_embeddings)} query vectors: shape={query_embeddings.shape}, dtype={query_embeddings.dtype}")
    return query_embeddings


def run_level_warmup(
    client: QdrantClient,
    collection_name: str,
    normalized_query_vectors: np.ndarray,
    query_ids: List[str],
    ef_value: int,
    top_k: int,
    warmup_queries: int
):
    """
    Perform warmup using current ef value.
    
    Args:
        client: Qdrant client
        collection_name: Collection name
        normalized_query_vectors: Pre-normalized query vectors (N x D)
        query_ids: List of query IDs
        ef_value: HNSW ef parameter
        top_k: Number of top results to retrieve
        warmup_queries: Number of warmup queries to execute
    """
    num_queries = len(query_ids)
    num_warmup = min(warmup_queries, num_queries)
    
    logger.info(f"Per-level warmup: {num_warmup} queries with ef={ef_value}")
    
    for i in range(num_warmup):
        try:
            query_vec = normalized_query_vectors[i:i+1][0].tolist()
            
            search_params = SearchParams(
                hnsw_ef=ef_value,
                exact=False
            )
            
            _ = client.search(
                collection_name=collection_name,
                query_vector=query_vec,
                limit=top_k,
                search_params=search_params,
                with_payload=False,
                with_vectors=False
            )
        except Exception as e:
            logger.warning(f"Warmup query {i} failed: {e}")
    
    logger.info(f"Warmup completed: {num_warmup} queries")


def test_ef_value(
    client: QdrantClient,
    collection_name: str,
    normalized_query_vectors: np.ndarray,
    query_ids: List[str],
    doc_ids: List[str],
    ef_value: int,
    top_k: int,
    warmup_queries: int,
    repeat_runs: int,
    qrels: Dict[str, Dict[str, int]]
) -> Dict:
    """
    Test a specific ef value with multiple repeat runs.
    
    Returns:
        Dictionary with mean/std of metrics
    """
    all_latencies = []
    all_recall_scores = []
    recall_by_run = []
    
    for run_num in range(repeat_runs):
        logger.info(f"Run {run_num + 1}/{repeat_runs} for ef={ef_value}")
        
        # Warmup with current ef value
        run_level_warmup(
            client,
            collection_name,
            normalized_query_vectors,
            query_ids,
            ef_value,
            top_k,
            warmup_queries
        )
        
        # Run benchmark
        latencies = []
        retrieval_results = {}
        total_time_start = time.perf_counter()
        
        for query_idx in range(len(query_ids)):
            try:
                query_vec = normalized_query_vectors[query_idx:query_idx+1][0].tolist()
                
                search_params = SearchParams(
                    hnsw_ef=ef_value,
                    exact=False
                )
                
                start_time = time.perf_counter()
                results = client.search(
                    collection_name=collection_name,
                    query_vector=query_vec,
                    limit=top_k,
                    search_params=search_params,
                    with_payload=False,
                    with_vectors=False
                )
                end_time = time.perf_counter()
                
                latency_ms = (end_time - start_time) * 1000.0
                latencies.append(latency_ms)
                
                # Store results for quality evaluation
                query_id = query_ids[query_idx]
                doc_scores = {}
                for result in results:
                    point_id = result.id
                    score = float(result.score)
                    # Map point ID (row index) to doc_id
                    if 0 <= point_id < len(doc_ids):
                        doc_id = doc_ids[point_id]
                        doc_scores[doc_id] = score
                    else:
                        doc_scores[f"doc_{point_id}"] = score
                retrieval_results[query_id] = doc_scores
                
            except Exception as e:
                logger.warning(f"Query {query_idx} failed: {e}")
        
        total_time_end = time.perf_counter()
        total_time_sec = total_time_end - total_time_start
        
        # Calculate QPS for this run
        num_queries = len(latencies)
        qps = num_queries / total_time_sec if total_time_sec > 0 else 0.0
        
        logger.info(f"Run {run_num + 1} for ef={ef_value}: {num_queries} queries, {total_time_sec:.4f}s, QPS={qps:.2f}")
        
        # Evaluate quality
        quality_metrics, _ = evaluate_retrieval_quality(qrels, retrieval_results, k=10)
        recall_score = quality_metrics.get("Recall@10", 0.0)
        recall_by_run.append(recall_score)
        
        # Accumulate latencies
        all_latencies.extend(latencies)
    
    # Calculate mean/std metrics
    if all_latencies:
        sorted_latencies = sorted(all_latencies)
        n = len(sorted_latencies)
        
        mean_lat = statistics.mean(all_latencies)
        p95 = sorted_latencies[int(n * 0.95)]
        recall_mean = statistics.mean(recall_by_run)
        recall_std = statistics.stdev(recall_by_run) if len(recall_by_run) > 1 else 0.0
        
        # Calculate QPS from accumulated latencies
        total_queries_processed = len(all_latencies)
        avg_latency_sec = mean_lat / 1000.0
        avg_qps = total_queries_processed / (total_queries_processed * avg_latency_sec) if avg_latency_sec > 0 else 0.0
        
        # Better QPS calculation
        num_queries = len(query_ids)
        total_time_estimate = mean_lat * num_queries / 1000.0  # seconds
        avg_qps = num_queries / total_time_estimate if total_time_estimate > 0 else 0.0
        
    else:
        mean_lat = p95 = recall_mean = recall_std = avg_qps = 0.0
    
    return {
        "mean_latency_ms": mean_lat,
        "p95_latency_ms": p95,
        "recall_at_10_mean": recall_mean,
        "recall_at_10_std": recall_std,
        "qps_mean": avg_qps,
        "all_latencies": all_latencies
    }


def evaluate_retrieval_quality(
    qrels: Dict[str, Dict[str, int]],
    retrieval_results: Dict[str, Dict[str, float]],
    k: int = 10
) -> Tuple[Dict[str, float], int]:
    """
    Evaluate retrieval quality using BEIR EvaluateRetrieval.
    
    Only evaluate queries with qrels (consistent with Run0/Run1/Run2).
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
    
    # Evaluate using standard evaluate method
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
    
    return {
        f"Recall@{k}": recall_at_k,
        f"nDCG@{k}": ndcg_at_k,
        f"MRR@{k}": mrr_at_k
    }, eval_queries_count


def get_environment_info() -> Dict:
    """Get system environment information."""
    try:
        import qdrant_client
        qdrant_version = getattr(qdrant_client, '__version__', 'unknown')
    except:
        qdrant_version = 'unknown'
    
    return {
        "cpu_info": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "ram_total_gb": 0,  # Would need psutil for accurate measurement
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "qdrant_version": qdrant_version
    }


# ============================================================================
# Visualization Functions
# ============================================================================

def generate_quality_vs_latency_plot(
    output_dir: pathlib.Path,
    results_by_ef: Dict[int, Dict]
):
    """
    Generate quality vs latency tradeoff plot (ace visualization).
    
    Args:
        output_dir: Output directory
        results_by_ef: Results dictionary keyed by ef value
    """
    try:
        import matplotlib.pyplot as plt
        
        logger.info("Generating quality_vs_latency_tradeoff.png...")
        
        ef_values = sorted(results_by_ef.keys())
        p95_latencies = [results_by_ef[ef]["p95_latency_ms"] for ef in ef_values]
        recalls = [results_by_ef[ef]["recall_at_10_mean"] for ef in ef_values]
        
        plt.figure(figsize=(12, 8))
        
        # Create scatter plot with ef labels
        scatter = plt.scatter(
            p95_latencies,
            recalls,
            s=200,
            alpha=0.7,
            c=range(len(ef_values)),
            cmap='viridis',
            edgecolors='black',
            linewidths=2,
            zorder=3
        )
        
        # Add ef value labels
        for i, (ef, x, y) in enumerate(zip(ef_values, p95_latencies, recalls)):
            plt.annotate(
                f'ef={ef}',
                xy=(x, y),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=10,
                fontweight='bold'
            )
        
        plt.xlabel('P95 Latency (ms)', fontsize=14, fontweight='bold')
        plt.ylabel('Recall@10', fontsize=14, fontweight='bold')
        plt.title('HNSW Tradeoff: Quality vs Latency', fontsize=16, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.colorbar(scatter, label='ef Value Index')
        
        # Set tick label font size
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        
        plt.tight_layout()
        
        plot_path = output_dir / "quality_vs_latency_tradeoff.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved: {plot_path}")
        
    except ImportError:
        logger.warning("matplotlib not available, skipping quality_vs_latency plot")
    except Exception as e:
        logger.error(f"Error generating quality_vs_latency plot: {e}", exc_info=True)


# ============================================================================
# Evidence Pack Generation
# ============================================================================

def generate_evidence_pack(
    output_dir: pathlib.Path,
    results_by_ef: Dict[int, Dict],
    manifest: Dict,
    sla_defaults: Dict,
    collection_name: str,
    eval_queries_count: int
):
    """Generate complete engineering evidence pack."""
    logger.info("Generating evidence pack...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get environment info
    env_info = get_environment_info()
    
    # Try to import yaml
    try:
        import yaml
    except ImportError:
        logger.warning("yaml not available, will save as JSON instead")
        yaml = None
    
    # Build report
    report = {
        "experiment_name": "Run3 - Qdrant HNSW Tradeoff (V2 Corrected)",
        "version": "V2_Corrected",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "critical_corrections": {
            "v2_corrected": True,
            "single_collection": True,
            "repeat_runs": REPEAT_RUNS,
            "per_level_warmup": True,
            "self_contained": True,
            "preflight_check": True,
            "hnsw_enabled": True,
            "grpc_enabled": True,
            "automatic_cleanup": True
        },
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
            "retrieval_backend": "qdrant_service_grpc_hnsw",
            "qdrant_host": QDRANT_HOST,
            "qdrant_port": QDRANT_PORT,
            "collection_name": collection_name,
            "search_parameters": {
                "exact": False,
                "hnsw_ef": "varied",
                "with_payload": False,
                "with_vectors": False
            },
            "distance_metric": "Cosine",
            "normalized": True,
            "ef_values_tested": HNSW_EF_TO_TEST,
            "repeat_runs": REPEAT_RUNS
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
            "qdrant_version": env_info["qdrant_version"]
        },
        "ef_results": {}
    }
    
    # Add ef results
    for ef_value in sorted(results_by_ef.keys()):
        results = results_by_ef[ef_value]
        ef_result_dict = {
            "p95_latency_ms": round(results["p95_latency_ms"], 4),
            "mean_latency_ms": round(results["mean_latency_ms"], 4),
            "qps_mean": round(results["qps_mean"], 2),
            "recall_at_10_mean": round(results["recall_at_10_mean"], 4),
            "recall_at_10_std": round(results["recall_at_10_std"], 4)
        }
        
        report["ef_results"][str(ef_value)] = ef_result_dict
    
    report["evaluation"] = {
        "eval_queries_count": eval_queries_count,
        "note": "Only queries with qrels were evaluated (consistent with Run0/Run1/Run2)"
    }
    
    # Find best ef value (highest recall)
    best_ef = None
    best_recall = 0
    for ef_value, results in results_by_ef.items():
        recall_mean = results.get("recall_at_10_mean", 0)
        if recall_mean > best_recall:
            best_recall = recall_mean
            best_ef = ef_value
    
    report["summary"] = {
        "best_ef": best_ef,
        "best_recall": round(best_recall, 4) if best_ef else None
    }
    
    # Save report
    if yaml:
        yaml_path = output_dir / "run3_qdrant_hnsw_tradeoff.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved YAML report: {yaml_path}")
    else:
        json_path = output_dir / "run3_qdrant_hnsw_tradeoff.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved JSON report (yaml not available): {json_path}")
    
    # Generate plot
    generate_quality_vs_latency_plot(output_dir, results_by_ef)
    
    logger.info("Evidence pack generation completed")


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Run3 - Qdrant HNSW Tradeoff (V2 Corrected)")
    logger.info("=" * 80)
    logger.info(f"Collection name: {COLLECTION_NAME}")
    logger.info(f"gRPC enabled: True")
    logger.info(f"HNSW enabled: True (with ef parameter)")
    logger.info(f"ef values to test: {HNSW_EF_TO_TEST}")
    logger.info(f"Repeat runs per ef value: {REPEAT_RUNS}")
    logger.info(f"Per-level warmup: ENABLED")
    logger.info(f"Automatic cleanup: ENABLED")
    logger.info("=" * 80)
    
    client = None
    
    try:
        # 1. Find and load dataset
        dataset_dir = find_dataset_directory()
        manifest, sla_defaults = load_manifest(dataset_dir)
        
        # Set random seeds
        random_seed = sla_defaults["random_seed"]
        random.seed(random_seed)
        np.random.seed(random_seed)
        logger.info(f"Set random seed: {random_seed}")
        
        # Get SLA parameters
        top_k = sla_defaults["top_k"]
        warmup_queries = sla_defaults["warmup_queries"]
        
        # 2. Initialize Qdrant client
        logger.info("Initializing Qdrant client...")
        client = initialize_qdrant_client()
        
        # 3. V2 CORRECTION: Create and populate collection ONCE
        create_and_populate_collection(
            client,
            COLLECTION_NAME,
            dataset_dir,
            manifest
        )
        
        # 4. Pre-flight check
        preflight_check(client, COLLECTION_NAME, manifest)
        
        # 5. Load data
        logger.info("Loading data...")
        query_ids, queries_dict = load_queries_dev(dataset_dir)
        qrels = load_qrels_dev(dataset_dir)
        
        # Load corpus for doc_id mapping
        corpus_path = dataset_dir / "processed_corpus.jsonl"
        doc_ids = []
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    doc_ids.append(data["doc_id"])
        
        # 6. Load and normalize query embeddings
        logger.info("Loading embeddings...")
        all_query_embeddings = np.load(dataset_dir / manifest["output_files"]["primary_query_embeddings"])
        
        logger.info("Aligning query vectors...")
        query_embeddings = align_query_vectors(
            query_ids,
            queries_dict,
            all_query_embeddings,
            dataset_dir,
            manifest
        )
        
        logger.info("Normalizing query vectors...")
        normalized_query_vectors = normalize_query_vectors(query_embeddings)
        
        # 7. V2 CORRECTION: Main loop - test multiple ef values
        logger.info("=" * 80)
        logger.info("Starting HNSW ef Parameter Benchmarks")
        logger.info("=" * 80)
        
        results_by_ef = {}
        eval_queries_count = 0
        
        for ef_value in HNSW_EF_TO_TEST:
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"Testing ef Value: {ef_value}")
            logger.info("=" * 80)
            
            # Test this ef value
            results = test_ef_value(
                client,
                COLLECTION_NAME,
                normalized_query_vectors,
                query_ids,
                doc_ids,
                ef_value,
                top_k,
                warmup_queries,
                REPEAT_RUNS,
                qrels
            )
            
            # Store results
            results_by_ef[ef_value] = results
            
            logger.info("")
            logger.info(f"ef={ef_value} Summary:")
            logger.info(f"  P95 latency: {results['p95_latency_ms']:.4f} ms")
            logger.info(f"  Mean latency: {results['mean_latency_ms']:.4f} ms")
            logger.info(f"  QPS: {results['qps_mean']:.2f}")
            logger.info(f"  Recall@10: {results['recall_at_10_mean']:.4f} ± {results['recall_at_10_std']:.4f}")
        
        # 8. Generate evidence pack
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = REPORTS_DIR / "run3_qdrant_hnsw_tradeoff" / timestamp
        
        # Get eval_queries_count (count queries with qrels)
        eval_queries_count = len([qid for qid, rels in qrels.items() if len(rels) > 0])
        
        generate_evidence_pack(
            output_dir,
            results_by_ef,
            manifest,
            sla_defaults,
            COLLECTION_NAME,
            eval_queries_count
        )
        
        # Print best ef summary
        best_ef = None
        best_recall = 0
        for ef_value, results in results_by_ef.items():
            recall_mean = results.get("recall_at_10_mean", 0)
            if recall_mean > best_recall:
                best_recall = recall_mean
                best_ef = ef_value
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("Summary: Best ef Value")
        logger.info("=" * 80)
        logger.info(f"Best ef: {best_ef}")
        logger.info(f"Best Recall@10: {best_recall:.4f}")
        logger.info("=" * 80)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("Run3 V2 Corrected Completed Successfully!")
        logger.info(f"Output directory: {output_dir}")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise
    
    finally:
        # Cleanup: Delete collection
        if client:
            try:
                logger.info("")
                logger.info("=" * 80)
                logger.info("Cleaning up: Deleting collection...")
                logger.info("=" * 80)
                client.delete_collection(collection_name=COLLECTION_NAME)
                logger.info(f"Collection '{COLLECTION_NAME}' deleted successfully")
            except Exception as e:
                logger.warning(f"Failed to delete collection '{COLLECTION_NAME}': {e}")


if __name__ == "__main__":
    main()

