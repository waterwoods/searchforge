#!/usr/bin/env python3
"""
Run2b - Qdrant Service Batch Query Optimization Test (V2 Corrected)

This script tests Qdrant service batch query performance with critical corrections:
- V2: Tests multiple batch sizes [16, 32, 64, 128] with 3 repeat runs each
- Scientific reproducibility: Each batch size is tested 3 times independently
- Proper warmup: First batch is used for warmup before timing starts
- Dedicated collection: Creates, populates, tests, and cleans up collection
- Pre-flight check: Verify Qdrant collection configuration matches manifest.json
- Exact search enforcement: Force exact (brute-force) retrieval
- gRPC enabled: Use prefer_grpc=True for better performance

Key Features:
- Loads standardized dataset and SLA constants from manifest.json
- Creates dedicated collection "beir_fiqa_1706_benchmark"
- Uploads vectors and payloads from .npy files
- Tests batch sizes: 16, 32, 64, 128
- Each batch size: 3 repeat runs with proper warmup
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
from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams, Distance, VectorParams, PointStruct, SearchRequest

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

# V2 CORRECTION: Multiple batch sizes with repeat runs
BATCH_SIZES_TO_TEST = [16, 32, 64, 128]
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
# Helper Functions (reused from run2)
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
# Batch Query Testing Functions
# ============================================================================

def split_queries_into_batches(
    query_vectors: np.ndarray,
    query_ids: List[str],
    batch_size: int,
    top_k: int
) -> List[List[SearchRequest]]:
    """
    Split queries into batches of SearchRequest objects.
    
    Args:
        query_vectors: Query embedding vectors (N x D)
        query_ids: Query IDs
        batch_size: Number of queries per batch
        top_k: Top K results per query
    
    Returns:
        List of batches, where each batch is a list of SearchRequest objects
    """
    list_of_batches = []
    total_queries = len(query_vectors)
    
    for i in range(0, total_queries, batch_size):
        batch_end = min(i + batch_size, total_queries)
        batch_vectors = query_vectors[i:batch_end]
        
        batch_requests = []
        for vector in batch_vectors:
            batch_requests.append(
                SearchRequest(
                    vector=vector.tolist(),
                    limit=top_k,
                    params=SearchParams(exact=True)  # Force exact search
                )
            )
        
        list_of_batches.append(batch_requests)
    
    logger.info(f"Split {total_queries} queries into {len(list_of_batches)} batches of size ~{batch_size}")
    return list_of_batches


def test_batch_size(
    client: QdrantClient,
    collection_name: str,
    list_of_batches: List[List[SearchRequest]],
    repeat_runs: int
) -> Dict:
    """
    Test a specific batch size with multiple repeat runs.
    
    Args:
        client: Qdrant client
        collection_name: Collection name
        list_of_batches: List of batches (each batch is a list of SearchRequest)
        repeat_runs: Number of repeat runs
    
    Returns:
        Dictionary with mean/std of job_time and effective_qps
    """
    job_times = []
    qps_runs = []
    error_messages = []
    error_count = 0
    
    # V2 CORRECTION: Extract first batch for warmup
    first_batch = list_of_batches[0] if list_of_batches else []
    
    # Calculate total queries from actual batches (MICROTUNE #1: don't hardcode)
    total_queries_processed = sum(len(b) for b in list_of_batches)
    
    for run_num in range(repeat_runs):
        # V2 CORRECTION: Batch warmup (first batch, not timed)
        if first_batch:
            logger.debug(f"Run {run_num + 1}/{repeat_runs}: Warming up with first batch...")
            try:
                client.search_batch(
                    collection_name=collection_name,
                    requests=first_batch,
                    timeout=30  # MICROTUNE #3: timeout protection
                )
            except Exception as e:
                logger.warning(f"Warmup batch failed: {e}")
        
        # Start timing
        total_start_time = time.perf_counter()
        
        # Run all batches (including first batch again)
        for batch in list_of_batches:
            try:
                client.search_batch(
                    collection_name=collection_name,
                    requests=batch,
                    timeout=30  # MICROTUNE #3: timeout protection
                )
            except Exception as e:  # MICROTUNE #2: robust error handling
                error_count += 1
                error_msg = f"Batch query failed in run {run_num + 1}: {e}"
                error_messages.append(error_msg)
                logger.error(error_msg)
                # Don't raise - collect errors and continue
        
        # End timing
        total_end_time = time.perf_counter()
        
        # Record single run results (MICROTUNE #1: use total_queries_processed)
        total_job_time_sec = total_end_time - total_start_time
        effective_qps = total_queries_processed / total_job_time_sec
        
        job_times.append(total_job_time_sec)
        qps_runs.append(effective_qps)
        
        logger.info(f"Run {run_num + 1}/{repeat_runs}: "
                   f"Total time = {total_job_time_sec:.4f}s, "
                   f"Effective QPS = {effective_qps:.2f}")
    
    # Compute mean/std
    qps_mean = statistics.mean(qps_runs)
    qps_std = statistics.stdev(qps_runs) if repeat_runs > 1 else 0.0
    
    job_time_mean = statistics.mean(job_times)
    job_time_std = statistics.stdev(job_times) if repeat_runs > 1 else 0.0
    
    return {
        "total_job_time_mean_sec": job_time_mean,
        "total_job_time_std_sec": job_time_std,
        "effective_qps_mean": qps_mean,
        "effective_qps_std": qps_std,
        "raw_job_times": job_times,
        "raw_qps_runs": qps_runs,
        "error_count": error_count,  # MICROTUNE #2: error tracking
        "error_messages": error_messages[:10] if error_messages else []  # Limit to first 10
    }


# ============================================================================
# Visualization Functions
# ============================================================================

def generate_batch_size_vs_qps_plot(
    output_dir: pathlib.Path,
    results_by_batch_size: Dict[int, Dict]
):
    """
    Generate bar chart: batch_size vs effective_qps_mean with error bars.
    
    Args:
        output_dir: Output directory
        results_by_batch_size: Results dictionary keyed by batch size
    """
    try:
        import matplotlib.pyplot as plt
        
        logger.info("Generating batch_size_vs_qps.png...")
        
        batch_sizes = sorted(results_by_batch_size.keys())
        qps_means = [results_by_batch_size[bs]["effective_qps_mean"] for bs in batch_sizes]
        qps_stds = [results_by_batch_size[bs]["effective_qps_std"] for bs in batch_sizes]
        
        plt.figure(figsize=(12, 8))
        
        # Create bar chart with error bars
        bars = plt.bar(
            [str(bs) for bs in batch_sizes],
            qps_means,
            yerr=qps_stds,
            capsize=5,
            alpha=0.7,
            color='#2E86AB',
            edgecolor='black',
            linewidth=1.5
        )
        
        # Add value labels on bars
        for i, (bar, mean, std) in enumerate(zip(bars, qps_means, qps_stds)):
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2,
                height + std + max(qps_means) * 0.02,
                f'{mean:.1f}±{std:.1f}',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )
        
        plt.xlabel('Batch Size', fontsize=14, fontweight='bold')
        plt.ylabel('Effective QPS (Queries Per Second)', fontsize=14, fontweight='bold')
        plt.title('Batch Size vs Effective QPS', fontsize=16, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        # Set tick label font size
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        
        plt.tight_layout()
        
        plot_path = output_dir / "batch_size_vs_qps.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved: {plot_path}")
        
    except ImportError:
        logger.warning("matplotlib not available, skipping batch_size_vs_qps plot")
    except Exception as e:
        logger.error(f"Error generating batch_size_vs_qps plot: {e}", exc_info=True)


# ============================================================================
# Evidence Pack Generation
# ============================================================================

def generate_evidence_pack(
    output_dir: pathlib.Path,
    results_by_batch_size: Dict[int, Dict],
    manifest: Dict,
    sla_defaults: Dict,
    collection_name: str
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
        "experiment_name": "Run2b - Qdrant Service Batch Query Optimization (V2 Corrected)",
        "version": "V2_Corrected",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "critical_corrections": {
            "v2_corrected": True,
            "multiple_batch_sizes": True,
            "repeat_runs": 3,
            "batch_warmup": True,
            "self_contained": True,
            "preflight_check": True,
            "exact_search_enforced": True,
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
            "retrieval_backend": "qdrant_service_batch",
            "qdrant_host": QDRANT_HOST,
            "qdrant_port": QDRANT_PORT,
            "collection_name": collection_name,
            "search_parameters": {
                "exact": True,
                "with_payload": False,
                "with_vectors": False
            },
            "distance_metric": "Cosine",
            "normalized": True,
            "batch_sizes_tested": BATCH_SIZES_TO_TEST,
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
        "batch_results": {}
    }
    
    # Add batch results
    for batch_size in sorted(results_by_batch_size.keys()):
        results = results_by_batch_size[batch_size]
        batch_result_dict = {
            "total_job_time_mean_sec": round(results["total_job_time_mean_sec"], 4),
            "total_job_time_std_sec": round(results["total_job_time_std_sec"], 4),
            "effective_qps_mean": round(results["effective_qps_mean"], 2),
            "effective_qps_std": round(results["effective_qps_std"], 2)
        }
        
        # MICROTUNE #2: Add error info if present
        if results.get("error_count", 0) > 0:
            batch_result_dict["error_count"] = results["error_count"]
            batch_result_dict["error_messages"] = results.get("error_messages", [])
        
        report["batch_results"][str(batch_size)] = batch_result_dict
    
    # MICROTUNE #4: Add best_batch_size (highest effective_qps_mean)
    best_batch_size = None
    best_qps = 0
    for batch_size, results in results_by_batch_size.items():
        qps_mean = results.get("effective_qps_mean", 0)
        if qps_mean > best_qps:
            best_qps = qps_mean
            best_batch_size = batch_size
    
    report["summary"] = {
        "best_batch_size": best_batch_size,
        "best_effective_qps": round(best_qps, 2) if best_batch_size else None
    }
    
    # Save report
    if yaml:
        yaml_path = output_dir / "run2b_qdrant_batch.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved YAML report: {yaml_path}")
    else:
        json_path = output_dir / "run2b_qdrant_batch.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved JSON report (yaml not available): {json_path}")
    
    # Generate plot
    generate_batch_size_vs_qps_plot(output_dir, results_by_batch_size)
    
    logger.info("Evidence pack generation completed")


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Run2b - Qdrant Service Batch Query Optimization (V2 Corrected)")
    logger.info("=" * 80)
    logger.info(f"Collection name: {COLLECTION_NAME}")
    logger.info(f"gRPC enabled: True")
    logger.info(f"Exact search enforced: True")
    logger.info(f"Batch sizes to test: {BATCH_SIZES_TO_TEST}")
    logger.info(f"Repeat runs per batch size: {REPEAT_RUNS}")
    logger.info(f"Batch warmup: ENABLED")
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
        
        # 2. Initialize Qdrant client
        logger.info("Initializing Qdrant client...")
        client = initialize_qdrant_client()
        
        # 3. Create and populate collection
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
        total_queries = len(query_ids)
        
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
        
        # 7. V2 CORRECTION: Main loop - test multiple batch sizes
        logger.info("=" * 80)
        logger.info("Starting Batch Size Benchmarks")
        logger.info("=" * 80)
        
        results_by_batch_size = {}
        
        for batch_size in BATCH_SIZES_TO_TEST:
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"Testing Batch Size: {batch_size}")
            logger.info("=" * 80)
            
            # Split queries into batches
            list_of_batches = split_queries_into_batches(
                normalized_query_vectors,
                query_ids,
                batch_size,
                top_k
            )
            
            # Test this batch size
            results = test_batch_size(
                client,
                COLLECTION_NAME,
                list_of_batches,
                REPEAT_RUNS
            )
            
            # Store results
            results_by_batch_size[batch_size] = results
            
            logger.info("")
            logger.info(f"Batch Size {batch_size} Summary:")
            logger.info(f"  Total job time: {results['total_job_time_mean_sec']:.4f} ± {results['total_job_time_std_sec']:.4f} sec")
            logger.info(f"  Effective QPS: {results['effective_qps_mean']:.2f} ± {results['effective_qps_std']:.2f}")
        
        # 8. Generate evidence pack
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = REPORTS_DIR / "run2b_qdrant_batch" / timestamp
        
        generate_evidence_pack(
            output_dir,
            results_by_batch_size,
            manifest,
            sla_defaults,
            COLLECTION_NAME
        )
        
        # MICROTUNE #4: Print best batch size summary
        best_batch_size = None
        best_qps = 0
        for batch_size, results in results_by_batch_size.items():
            qps_mean = results.get("effective_qps_mean", 0)
            if qps_mean > best_qps:
                best_qps = qps_mean
                best_batch_size = batch_size
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("Summary: Best Batch Size")
        logger.info("=" * 80)
        logger.info(f"Best batch size: {best_batch_size}")
        logger.info(f"Best effective QPS: {best_qps:.2f}")
        logger.info("=" * 80)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("Run2b V2 Corrected Completed Successfully!")
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

