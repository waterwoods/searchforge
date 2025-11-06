#!/usr/bin/env python3
"""
Run2 - Qdrant Service Baseline Test (V3 Self-Contained)

This script tests Qdrant service performance under concurrent load with critical corrections:
- Self-contained: Creates, populates, tests, and cleans up a dedicated collection
- Pre-flight check: Verify Qdrant collection configuration matches manifest.json
- Exact search enforcement: Force exact (brute-force) retrieval for fair comparison with FAISS
- gRPC enabled: Use prefer_grpc=True to reduce serialization overhead
- Per-level warmup with ThreadPoolExecutor
- Combined latency data from all runs for CDF plots
- Robust error handling
- Automatic cleanup: Deletes collection in finally block

Key Features:
- Loads standardized dataset and SLA constants from manifest.json
- Creates dedicated collection "beir_fiqa_1706_benchmark"
- Uploads vectors and payloads from .npy files
- Uses ThreadPoolExecutor to simulate concurrent queries [1, 4, 8, 16]
- Generates evidence pack with mean/std metrics and three graphs
- Evaluates retrieval quality once (using first run at concurrency=1)
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
from concurrent.futures import ThreadPoolExecutor, as_completed
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

CONCURRENCY_LEVELS = [1, 4, 8, 16]
REPEAT_RUNS = 3

# Qdrant connection settings
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

# CRITICAL CORRECTION #1: Dedicated collection name for benchmark
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


def initialize_qdrant_client() -> QdrantClient:
    """
    Initialize Qdrant client with gRPC enabled.
    
    CRITICAL CORRECTION #3: Enable gRPC for better performance.
    
    Returns:
        QdrantClient: Initialized client
    """
    logger.info(f"Initializing Qdrant client: host={QDRANT_HOST}, port={QDRANT_PORT}, prefer_grpc=True")
    client = QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        prefer_grpc=True  # CRITICAL CORRECTION #3: Enable gRPC
    )
    
    # Test connection
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
    """
    CRITICAL CORRECTION #1: Create and populate dedicated collection.
    
    Steps:
    1. Delete collection if it exists (clean start)
    2. Create collection with correct configuration
    3. Load document vectors and doc_ids from .npy files
    4. Upload vectors and payloads in batches
    
    Args:
        client: Qdrant client
        collection_name: Collection name
        dataset_dir: Dataset directory path
        manifest: Manifest data
    """
    logger.info("=" * 80)
    logger.info("Creating and Populating Collection")
    logger.info("=" * 80)
    
    # Step 1: Delete collection if it exists
    try:
        collections = client.get_collections()
        existing_collections = [c.name for c in collections.collections]
        if collection_name in existing_collections:
            logger.info(f"Deleting existing collection '{collection_name}' for clean start...")
            client.delete_collection(collection_name=collection_name)
            logger.info(f"Collection '{collection_name}' deleted successfully")
    except Exception as e:
        logger.warning(f"Error checking/deleting collection: {e}")
    
    # Step 2: Get configuration from manifest
    dimension = manifest.get("models", {}).get("primary", {}).get("dimension", 0)
    if dimension == 0:
        raise ValueError("Could not determine vector dimension from manifest")
    
    logger.info(f"Vector dimension: {dimension}")
    logger.info(f"Distance metric: Cosine")
    
    # Step 3: Create collection
    logger.info(f"Creating collection '{collection_name}'...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=dimension,
            distance=Distance.COSINE
        )
    )
    logger.info(f"Collection '{collection_name}' created successfully")
    
    # Step 4: Load document embeddings
    doc_emb_path = dataset_dir / manifest["output_files"]["primary_embeddings"]
    if not doc_emb_path.exists():
        raise FileNotFoundError(f"Document embeddings not found: {doc_emb_path}")
    
    doc_embeddings = np.load(doc_emb_path)
    logger.info(f"Loaded document embeddings: shape={doc_embeddings.shape}")
    
    # Ensure C contiguous and float32
    doc_embeddings = np.ascontiguousarray(doc_embeddings, dtype=np.float32)
    
    # Normalize embeddings for cosine similarity
    logger.info("L2 normalizing document vectors...")
    norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # Avoid division by zero
    doc_embeddings = doc_embeddings / norms
    
    # Step 5: Load corpus and build doc_id mapping
    corpus_path = dataset_dir / "processed_corpus.jsonl"
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")
    
    doc_ids = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for row_idx, line in enumerate(f):
            if line.strip():
                data = json.loads(line)
                doc_id = data["doc_id"]
                doc_ids.append(doc_id)
    
    logger.info(f"Loaded {len(doc_ids)} document IDs from corpus")
    
    if len(doc_ids) != len(doc_embeddings):
        raise ValueError(
            f"Document ID count ({len(doc_ids)}) doesn't match "
            f"embedding count ({len(doc_embeddings)})"
        )
    
    # Step 6: Upload vectors and payloads in batches
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
            point = PointStruct(
                id=i + j,  # Use row index as point ID
                vector=embedding.tolist(),
                payload={
                    "doc_id": doc_id
                }
            )
            points.append(point)
        
        # Upload batch
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        batch_num = (i // batch_size) + 1
        logger.info(f"Uploaded batch {batch_num}/{total_batches} ({len(points)} points)")
    
    logger.info(f"Collection '{collection_name}' populated successfully with {total_points} points")
    logger.info("=" * 80)


def preflight_check(client: QdrantClient, collection_name: str, manifest: Dict) -> None:
    """
    CRITICAL CORRECTION #2: Pre-flight check AFTER data upload.
    
    Args:
        client: Qdrant client
        collection_name: Collection name
        manifest: Manifest data
        
    Raises:
        AssertionError: If any configuration mismatch is detected
    """
    logger.info("=" * 80)
    logger.info("Pre-flight Check: Verifying Qdrant Configuration")
    logger.info("=" * 80)
    
    try:
        collection_info = client.get_collection(collection_name)
    except Exception as e:
        raise RuntimeError(f"Failed to get collection info: {e}")
    
    # Extract expected values from manifest
    expected_corpus_count = manifest.get("subset_corpus_count", 0)
    expected_dimension = manifest.get("models", {}).get("primary", {}).get("dimension", 0)
    
    # Get actual values from Qdrant
    actual_vectors_count = collection_info.points_count
    actual_dimension = collection_info.config.params.vectors.size
    actual_distance = collection_info.config.params.vectors.distance.name
    
    logger.info(f"Expected (from manifest):")
    logger.info(f"  Corpus count: {expected_corpus_count}")
    logger.info(f"  Dimension: {expected_dimension}")
    logger.info(f"  Distance: Cosine")
    logger.info(f"Actual (from Qdrant):")
    logger.info(f"  Vectors count: {actual_vectors_count}")
    logger.info(f"  Dimension: {actual_dimension}")
    logger.info(f"  Distance: {actual_distance}")
    
    # CRITICAL CORRECTION #2: Assertions with clear error messages
    if actual_vectors_count != expected_corpus_count:
        error_msg = (
            f"CRITICAL MISMATCH: Vector count mismatch!\n"
            f"  Expected (manifest): {expected_corpus_count}\n"
            f"  Actual (Qdrant): {actual_vectors_count}\n"
            f"This indicates dataset inconsistency. Experiment aborted."
        )
        logger.error(error_msg)
        raise AssertionError(error_msg)
    
    if actual_dimension != expected_dimension:
        error_msg = (
            f"CRITICAL MISMATCH: Vector dimension mismatch!\n"
            f"  Expected (manifest): {expected_dimension}\n"
            f"  Actual (Qdrant): {actual_dimension}\n"
            f"This indicates embedding model mismatch. Experiment aborted."
        )
        logger.error(error_msg)
        raise AssertionError(error_msg)
    
    if actual_distance.lower() != "cosine":
        error_msg = (
            f"CRITICAL MISMATCH: Distance metric mismatch!\n"
            f"  Expected: Cosine\n"
            f"  Actual: {actual_distance}\n"
            f"This indicates distance metric mismatch. Experiment aborted."
        )
        logger.error(error_msg)
        raise AssertionError(error_msg)
    
    logger.info("=" * 80)
    logger.info("Pre-flight Check: PASSED ✓")
    logger.info("=" * 80)


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
        np.ndarray: Normalized query embeddings (C contiguous, float32)
    """
    logger.info("L2 normalizing all query vectors...")
    
    # CRITICAL: Ensure C contiguous and float32
    query_embeddings = np.ascontiguousarray(query_embeddings, dtype=np.float32)
    
    # Normalize in-place
    norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # Avoid division by zero
    query_embeddings = query_embeddings / norms
    
    logger.info(f"Normalized {len(query_embeddings)} query vectors: shape={query_embeddings.shape}, dtype={query_embeddings.dtype}")
    return query_embeddings


def run_level_warmup(
    client: QdrantClient,
    collection_name: str,
    normalized_query_vectors: np.ndarray,
    query_ids: List[str],
    concurrency_level: int,
    top_k: int,
    warmup_queries: int
):
    """
    Perform warmup using ThreadPoolExecutor at the specified concurrency level.
    
    CRITICAL CORRECTION #3: Per-level warmup with ThreadPoolExecutor.
    
    Args:
        client: Qdrant client
        collection_name: Collection name
        normalized_query_vectors: Pre-normalized query vectors (N x D)
        query_ids: List of query IDs
        concurrency_level: Number of concurrent threads for warmup
        top_k: Number of top results to retrieve
        warmup_queries: Number of warmup queries to execute
    """
    num_queries = len(query_ids)
    num_warmup = min(warmup_queries, num_queries)
    
    logger.info(f"Per-level warmup: {num_warmup} queries with concurrency={concurrency_level}")
    
    def warmup_task(query_idx: int):
        """Warmup task function."""
        try:
            query_vec = normalized_query_vectors[query_idx:query_idx+1][0].tolist()
            
            # CRITICAL CORRECTION #3: Use exact search for warmup too
            search_params = SearchParams(
                exact=True,  # Force exact (brute-force) retrieval
                hnsw_ef=None  # Disable HNSW
            )
            
            _ = client.search(
                collection_name=collection_name,
                query_vector=query_vec,
                limit=top_k,
                search_params=search_params,
                with_payload=False,  # CRITICAL CORRECTION #3: Optimization
                with_vectors=False  # CRITICAL CORRECTION #3: Optimization
            )
            return query_idx
        except Exception as e:
            logger.warning(f"Warmup query {query_idx} failed: {e}")
            return None
    
    # Execute warmup with ThreadPoolExecutor at current concurrency level
    with ThreadPoolExecutor(max_workers=concurrency_level) as executor:
        futures = [executor.submit(warmup_task, i) for i in range(num_warmup)]
        for future in as_completed(futures):
            result = future.result()
            if result is None:
                logger.warning(f"Warmup query {result} completed with error")
    
    logger.info(f"Warmup completed: {num_warmup} queries")


def run_concurrent_benchmark(
    client: QdrantClient,
    collection_name: str,
    normalized_query_vectors: np.ndarray,
    query_ids: List[str],
    concurrency_level: int,
    top_k: int,
    doc_ids: Optional[List[str]] = None
) -> Tuple[List[float], Dict[str, Dict[str, float]], float, List[str]]:
    """
    Run concurrent benchmark for a single concurrency level.
    
    CRITICAL CORRECTION #3: Force exact search for fair comparison with FAISS.
    CRITICAL CORRECTION #3: Optimize with with_payload=False, with_vectors=False.
    
    Args:
        client: Qdrant client
        collection_name: Collection name
        normalized_query_vectors: Pre-normalized query vectors (N x D)
        query_ids: List of query IDs
        concurrency_level: Number of concurrent threads
        top_k: Number of top results to retrieve
        
    Returns:
        Tuple of (latencies list, retrieval_results dict, total_time_sec, error_list)
    """
    num_queries = len(query_ids)
    
    # Main benchmark phase
    latencies = []
    retrieval_results = {}
    errors = []
    total_time_start = time.perf_counter()
    
    def search_task(query_idx: int) -> Tuple[int, Optional[float], Optional[List], Optional[str]]:
        """
        Task function for concurrent execution with error handling.
        
        CRITICAL CORRECTION #3: Force exact search.
        CRITICAL CORRECTION #3: Optimize with with_payload=False, with_vectors=False.
        """
        try:
            query_vec = normalized_query_vectors[query_idx:query_idx+1][0].tolist()
            
            # CRITICAL CORRECTION #3: Force exact (brute-force) retrieval
            search_params = SearchParams(
                exact=True,  # Force exact (brute-force) retrieval
                hnsw_ef=None  # Disable HNSW
            )
            
            # Time ONLY the search call
            start_time = time.perf_counter()
            results = client.search(
                collection_name=collection_name,
                query_vector=query_vec,
                limit=top_k,
                search_params=search_params,
                with_payload=False,  # CRITICAL CORRECTION #3: Optimization
                with_vectors=False  # CRITICAL CORRECTION #3: Optimization
            )
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000.0
            
            return query_idx, latency_ms, results, None
        except Exception as e:
            error_msg = f"Query {query_idx} failed: {str(e)}"
            logger.error(error_msg)
            return query_idx, None, None, error_msg
    
    # Execute concurrent searches
    with ThreadPoolExecutor(max_workers=concurrency_level) as executor:
        futures = [executor.submit(search_task, i) for i in range(num_queries)]
        
        for future in as_completed(futures):
            query_idx, latency_ms, search_results, error_msg = future.result()
            
            if error_msg is not None:
                errors.append(error_msg)
                continue
            
            if latency_ms is not None and search_results is not None:
                latencies.append(latency_ms)
                
                # Store results for quality evaluation
                # Map point IDs (row indices) to doc_ids
                query_id = query_ids[query_idx]
                doc_scores = {}
                for result in search_results:
                    point_id = result.id
                    score = float(result.score)
                    # Map point ID (row index) to doc_id
                    if doc_ids is not None and 0 <= point_id < len(doc_ids):
                        doc_id = doc_ids[point_id]
                        doc_scores[doc_id] = score
                    else:
                        # Fallback: store as placeholder
                        doc_scores[f"doc_{point_id}"] = score
                retrieval_results[query_id] = doc_scores
    
    total_time_end = time.perf_counter()
    total_time_sec = total_time_end - total_time_start
    
    return latencies, retrieval_results, total_time_sec, errors


def map_results_to_doc_ids(
    retrieval_results: Dict[str, Dict[str, float]],
    doc_ids: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Map retrieval results from point IDs to doc_ids.
    
    Args:
        retrieval_results: Results with point IDs as keys
        doc_ids: List of doc_ids indexed by row
        
    Returns:
        Dict with doc_id mappings
    """
    mapped_results = {}
    
    for query_id, scores in retrieval_results.items():
        mapped_scores = {}
        for point_id_str, score in scores.items():
            # Extract point ID from "doc_{point_id}" format
            if point_id_str.startswith("doc_"):
                point_id = int(point_id_str[4:])
                if 0 <= point_id < len(doc_ids):
                    doc_id = doc_ids[point_id]
                    mapped_scores[doc_id] = score
        mapped_results[query_id] = mapped_scores
    
    return mapped_results


def evaluate_retrieval_quality(
    qrels: Dict[str, Dict[str, int]],
    retrieval_results: Dict[str, Dict[str, float]],
    k: int = 10
) -> Tuple[Dict[str, float], int]:
    """
    Evaluate retrieval quality using BEIR EvaluateRetrieval.
    
    Only evaluate queries with qrels (consistent with Run0/Run1).
    
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
        from qdrant_client import QdrantClient
        qdrant_version = getattr(QdrantClient, "__version__", "unknown")
    except:
        qdrant_version = "unknown"
    
    return {
        "cpu_info": platform.processor() or platform.machine(),
        "cpu_count": cpu_count,
        "ram_total_gb": ram_total_gb,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "qdrant_version": qdrant_version
    }


def generate_latency_cdf_concurrency(
    output_dir: pathlib.Path,
    results_by_concurrency: Dict[int, Dict]
):
    """
    Generate CDF plot for multiple concurrency levels.
    
    Combine latency data from ALL runs, not just last run.
    
    Args:
        output_dir: Output directory
        results_by_concurrency: Results dictionary keyed by concurrency level
    """
    try:
        import matplotlib.pyplot as plt
        
        logger.info("Generating latency CDF plot for concurrency levels...")
        
        plt.figure(figsize=(10, 6))
        
        for level in sorted(results_by_concurrency.keys()):
            # Get combined latencies from ALL runs
            results = results_by_concurrency[level]
            all_latencies = results.get("all_runs_latencies", [])
            
            if all_latencies:
                # Use combined latency data from all runs
                sorted_lat = sorted(all_latencies)
                y = np.arange(1, len(sorted_lat) + 1) / len(sorted_lat)
                plt.plot(sorted_lat, y, label=f'Concurrency={level}', linewidth=2)
            else:
                # Fallback: use percentile approximation if no raw data
                p50_mean = results.get("p50_mean_ms", 0)
                p95_mean = results.get("p95_mean_ms", 0)
                p99_mean = results.get("p99_mean_ms", 0)
                latencies = [p50_mean * 0.8, p50_mean, p95_mean, p99_mean, p99_mean * 1.2]
                sorted_lat = sorted(latencies)
                y = np.arange(1, len(sorted_lat) + 1) / len(sorted_lat)
                plt.plot(sorted_lat, y, label=f'Concurrency={level}', linewidth=2, marker='o', markersize=4)
        
        plt.xlabel('Latency (ms)', fontsize=12)
        plt.ylabel('Cumulative Probability', fontsize=12)
        plt.title('Latency CDF by Concurrency Level', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        cdf_path = output_dir / "latency_cdf_concurrency.png"
        plt.savefig(cdf_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {cdf_path}")
        
    except ImportError:
        logger.warning("matplotlib not available, skipping CDF plot")
    except Exception as e:
        logger.error(f"Error generating CDF plot: {e}", exc_info=True)


def generate_qps_vs_latency(
    output_dir: pathlib.Path,
    results_by_concurrency: Dict[int, Dict]
):
    """
    Generate QPS vs Latency scatter plot.
    
    Args:
        output_dir: Output directory
        results_by_concurrency: Results dictionary keyed by concurrency level
    """
    try:
        import matplotlib.pyplot as plt
        
        logger.info("Generating QPS vs Latency plot...")
        
        qps_values = []
        p95_latencies = []
        labels = []
        
        for level in sorted(results_by_concurrency.keys()):
            results = results_by_concurrency[level]
            qps_mean = results.get("qps_mean", 0)
            p95_mean_ms = results.get("p95_mean_ms", 0)
            
            qps_values.append(qps_mean)
            p95_latencies.append(p95_mean_ms)
            labels.append(str(level))
        
        plt.figure(figsize=(10, 6))
        plt.scatter(p95_latencies, qps_values, s=200, alpha=0.7, edgecolors='black', linewidths=2)
        
        # Add labels
        for i, label in enumerate(labels):
            plt.annotate(f'C={label}', (p95_latencies[i], qps_values[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=10)
        
        plt.xlabel('P95 Latency (ms)', fontsize=12)
        plt.ylabel('QPS (Queries Per Second)', fontsize=12)
        plt.title('QPS vs P95 Latency by Concurrency Level', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        qps_path = output_dir / "qps_vs_latency.png"
        plt.savefig(qps_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved: {qps_path}")
        
    except ImportError:
        logger.warning("matplotlib not available, skipping QPS vs Latency plot")
    except Exception as e:
        logger.error(f"Error generating QPS vs Latency plot: {e}", exc_info=True)


def generate_quality_metrics_plot(
    output_dir: pathlib.Path,
    quality_metrics: Dict[str, float]
):
    """
    Generate quality metrics bar chart.
    
    Args:
        output_dir: Output directory
        quality_metrics: Quality metrics dictionary
    """
    try:
        import matplotlib.pyplot as plt
        
        logger.info("Generating quality metrics plot...")
        
        recall_at_10 = quality_metrics.get('Recall@10', 0.0)
        ndcg_at_10 = quality_metrics.get('nDCG@10', 0.0)
        mrr_at_10 = quality_metrics.get('MRR@10', 0.0)
        
        metrics_names = ['Recall@10', 'nDCG@10', 'MRR@10']
        metrics_values = [recall_at_10, ndcg_at_10, mrr_at_10]
        
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
        
    except ImportError:
        logger.warning("matplotlib not available, skipping quality metrics plot")
    except Exception as e:
        logger.error(f"Error generating quality metrics plot: {e}", exc_info=True)


def generate_evidence_pack(
    output_dir: pathlib.Path,
    results_by_concurrency: Dict[int, Dict],
    quality_metrics: Dict[str, float],
    eval_queries_count: int,
    manifest: Dict,
    sla_defaults: Dict,
    collection_name: str
):
    """
    Generate complete engineering evidence pack.
    
    Args:
        output_dir: Output directory
        results_by_concurrency: Results dictionary keyed by concurrency level
        quality_metrics: Quality evaluation metrics
        eval_queries_count: Number of queries used for evaluation
        manifest: Manifest data
        sla_defaults: SLA defaults used
        collection_name: Qdrant collection name
    """
    logger.info("Generating evidence pack...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get environment info
    env_info = get_environment_info()
    
    # Generate YAML report
    try:
        import yaml
    except ImportError:
        logger.warning("yaml not available, will save as JSON instead")
        yaml = None
    
    report = {
        "experiment_name": "Run2 - Qdrant Service Baseline (Exact Search, Self-Contained)",
        "version": "V3_SelfContained",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "critical_corrections": {
            "self_contained": True,
            "preflight_check": True,
            "exact_search_enforced": True,
            "grpc_enabled": True,
            "per_level_warmup": True,
            "combined_latency_data": True,
            "error_handling": True,
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
            "retrieval_backend": "qdrant_service_grpc",
            "qdrant_host": QDRANT_HOST,
            "qdrant_port": QDRANT_PORT,
            "collection_name": collection_name,
            "search_parameters": {
                "exact": True,
                "hnsw_ef": None,
                "with_payload": False,
                "with_vectors": False
            },
            "distance_metric": "Cosine",
            "normalized": True,
            "concurrency_levels": CONCURRENCY_LEVELS,
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
        "quality_metrics": quality_metrics,
        "concurrency_results": {}
    }
    
    # Add concurrency results
    for level in sorted(results_by_concurrency.keys()):
        results = results_by_concurrency[level]
        # Determine status based on errors
        status = "degraded" if results.get("error_count", 0) > 0 else "normal"
        
        # Create result dict with all metadata
        result_dict = {
            "status": status,
            "error_count": results.get("error_count", 0),
            "qps_mean": round(results.get("qps_mean", 0), 2),
            "qps_std": round(results.get("qps_std", 0), 2),
            "p50_mean_ms": round(results.get("p50_mean_ms", 0), 4),
            "p50_std_ms": round(results.get("p50_std_ms", 0), 4),
            "p95_mean_ms": round(results.get("p95_mean_ms", 0), 4),
            "p95_std_ms": round(results.get("p95_std_ms", 0), 4),
            "p99_mean_ms": round(results.get("p99_mean_ms", 0), 4),
            "p99_std_ms": round(results.get("p99_std_ms", 0), 4),
            "mean_mean_ms": round(results.get("mean_mean_ms", 0), 4),
            "mean_std_ms": round(results.get("mean_std_ms", 0), 4)
        }
        
        # Add error messages if any
        if results.get("error_count", 0) > 0:
            result_dict["error_messages"] = results.get("error_messages", [])[:10]  # Limit to first 10
        
        report["concurrency_results"][str(level)] = result_dict
    
    report["evaluation"] = {
        "eval_queries_count": eval_queries_count,
        "note": "Only queries with qrels were evaluated (consistent with Run0/Run1)"
    }
    
    # Save report
    if yaml:
        yaml_path = output_dir / "run2_qdrant_service_exact.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved YAML report: {yaml_path}")
    else:
        json_path = output_dir / "run2_qdrant_service_exact.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved JSON report (yaml not available): {json_path}")
    
    # Generate three plots
    generate_latency_cdf_concurrency(output_dir, results_by_concurrency)
    generate_qps_vs_latency(output_dir, results_by_concurrency)
    generate_quality_metrics_plot(output_dir, quality_metrics)
    
    logger.info("Evidence pack generation completed")


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Run2 - Qdrant Service Baseline Test (V3 Self-Contained)")
    logger.info("=" * 80)
    logger.info(f"Collection name: {COLLECTION_NAME}")
    logger.info(f"gRPC enabled: True")
    logger.info(f"Exact search enforced: True")
    logger.info(f"Repeat runs per concurrency level: {REPEAT_RUNS}")
    logger.info(f"Per-level warmup: ENABLED")
    logger.info(f"Error handling: ENABLED")
    logger.info(f"Automatic cleanup: ENABLED")
    logger.info("=" * 80)
    
    client = None
    
    try:
        # 1. Find and load dataset
        dataset_dir = find_dataset_directory()
        manifest, sla_defaults = load_manifest(dataset_dir)
        
        # Set random seeds for reproducibility
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
        
        # 3. CRITICAL CORRECTION #1: Create and populate collection
        create_and_populate_collection(
            client,
            COLLECTION_NAME,
            dataset_dir,
            manifest
        )
        
        # 4. CRITICAL CORRECTION #2: Pre-flight check AFTER data upload
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
        
        # 6. Load embeddings
        logger.info("Loading embeddings...")
        all_query_embeddings = np.load(dataset_dir / manifest["output_files"]["primary_query_embeddings"])
        
        # 7. Align query vectors
        logger.info("Aligning query vectors...")
        query_embeddings = align_query_vectors(
            query_ids,
            queries_dict,
            all_query_embeddings,
            dataset_dir,
            manifest
        )
        
        # 8. Normalize query vectors (CRITICAL: ensure C contiguous and float32)
        logger.info("Normalizing query vectors (ensuring C contiguous and float32)...")
        normalized_query_vectors = normalize_query_vectors(query_embeddings)
        
        # 9. Run concurrency benchmarks
        logger.info("=" * 80)
        logger.info("Starting Concurrency Benchmarks")
        logger.info("=" * 80)
        
        results_by_concurrency = {}
        quality_metrics = None
        eval_queries_count = 0
        
        for concurrency_level in CONCURRENCY_LEVELS:
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Testing Concurrency Level: {concurrency_level}")
            logger.info(f"{'=' * 80}")
            
            # Store results for this concurrency level
            level_qps_runs = []
            level_p50_runs = []
            level_p95_runs = []
            level_p99_runs = []
            level_mean_runs = []
            all_runs_latencies = []  # Store ALL latencies for CDF
            all_errors = []  # Store all errors for this concurrency level
            
            # Repeat runs for stability
            for run_num in range(REPEAT_RUNS):
                logger.info(f"\n--- Run {run_num + 1}/{REPEAT_RUNS} ---")
                
                # CRITICAL CORRECTION #3: Per-level warmup BEFORE each run
                run_level_warmup(
                    client,
                    COLLECTION_NAME,
                    normalized_query_vectors,
                    query_ids,
                    concurrency_level,
                    top_k,
                    warmup_queries
                )
                
                # Run concurrent benchmark
                latencies, retrieval_results, total_time_sec, errors = run_concurrent_benchmark(
                    client,
                    COLLECTION_NAME,
                    normalized_query_vectors,
                    query_ids,
                    concurrency_level,
                    top_k,
                    doc_ids=doc_ids  # Pass doc_ids for mapping
                )
                
                # Combine latencies from all runs
                all_runs_latencies.extend(latencies)
                all_errors.extend(errors)
                
                # Calculate metrics for this run
                if latencies:
                    percentiles = calculate_percentiles(latencies)
                    mean_latency = statistics.mean(latencies)
                    num_queries = len(latencies)
                    qps = num_queries / total_time_sec if total_time_sec > 0 else 0.0
                    
                    level_qps_runs.append(qps)
                    level_p50_runs.append(percentiles["p50"])
                    level_p95_runs.append(percentiles["p95"])
                    level_p99_runs.append(percentiles["p99"])
                    level_mean_runs.append(mean_latency)
                    
                    logger.info(f"Run {run_num + 1}: QPS={qps:.2f}, P95={percentiles['p95']:.4f}ms, Mean={mean_latency:.4f}ms")
                else:
                    logger.warning(f"Run {run_num + 1}: No successful queries")
                
                # Report errors if any
                if errors:
                    logger.warning(f"Run {run_num + 1}: {len(errors)} errors occurred")
                    for error in errors[:5]:  # Show first 5 errors
                        logger.warning(f"  - {error}")
                
                # Evaluate quality only once (first run of concurrency=1)
                if concurrency_level == 1 and run_num == 0 and quality_metrics is None:
                    logger.info("\nEvaluating retrieval quality (first run, concurrency=1)...")
                    # Results already have doc_ids mapped (passed doc_ids parameter)
                    quality_metrics, eval_queries_count = evaluate_retrieval_quality(
                        qrels, retrieval_results, k=10
                    )
            
            # Calculate mean and std for this concurrency level
            if level_qps_runs:
                qps_mean = statistics.mean(level_qps_runs)
                qps_std = statistics.stdev(level_qps_runs) if len(level_qps_runs) > 1 else 0.0
                
                p50_mean = statistics.mean(level_p50_runs)
                p50_std = statistics.stdev(level_p50_runs) if len(level_p50_runs) > 1 else 0.0
                
                p95_mean = statistics.mean(level_p95_runs)
                p95_std = statistics.stdev(level_p95_runs) if len(level_p95_runs) > 1 else 0.0
                
                p99_mean = statistics.mean(level_p99_runs)
                p99_std = statistics.stdev(level_p99_runs) if len(level_p99_runs) > 1 else 0.0
                
                mean_mean = statistics.mean(level_mean_runs)
                mean_std = statistics.stdev(level_mean_runs) if len(level_mean_runs) > 1 else 0.0
            else:
                # All runs failed
                logger.error(f"All runs failed for concurrency level {concurrency_level}")
                qps_mean = qps_std = p50_mean = p50_std = p95_mean = p95_std = p99_mean = p99_std = mean_mean = mean_std = 0.0
            
            # Store results
            results_by_concurrency[concurrency_level] = {
                "qps_mean": qps_mean,
                "qps_std": qps_std,
                "p50_mean_ms": p50_mean,
                "p50_std_ms": p50_std,
                "p95_mean_ms": p95_mean,
                "p95_std_ms": p95_std,
                "p99_mean_ms": p99_mean,
                "p99_std_ms": p99_std,
                "mean_mean_ms": mean_mean,
                "mean_std_ms": mean_std,
                "all_runs_latencies": all_runs_latencies,  # Store combined latencies
                "error_count": len(all_errors),
                "error_messages": all_errors[:20]  # Store up to 20 error messages
            }
            
            logger.info(f"\nConcurrency Level {concurrency_level} Summary:")
            logger.info(f"  QPS: {qps_mean:.2f} ± {qps_std:.2f}")
            logger.info(f"  P50: {p50_mean:.4f} ± {p50_std:.4f} ms")
            logger.info(f"  P95: {p95_mean:.4f} ± {p95_std:.4f} ms")
            logger.info(f"  P99: {p99_mean:.4f} ± {p99_std:.4f} ms")
            logger.info(f"  Mean: {mean_mean:.4f} ± {mean_std:.4f} ms")
            if all_errors:
                logger.warning(f"  Errors: {len(all_errors)} occurred")
        
        # 10. Generate evidence pack
        output_dir = REPORTS_DIR / "run2_qdrant_service_exact" / time.strftime("%Y%m%d_%H%M%S")
        generate_evidence_pack(
            output_dir,
            results_by_concurrency,
            quality_metrics or {},
            eval_queries_count,
            manifest,
            sla_defaults,
            COLLECTION_NAME
        )
        
        logger.info("=" * 80)
        logger.info("Run2 V3 Self-Contained Completed Successfully!")
        logger.info(f"Output directory: {output_dir}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise
    finally:
        # CRITICAL CORRECTION #5: Cleanup collection in finally block
        if client is not None:
            try:
                logger.info("=" * 80)
                logger.info("Cleaning up: Deleting collection...")
                logger.info("=" * 80)
                client.delete_collection(collection_name=COLLECTION_NAME)
                logger.info(f"Collection '{COLLECTION_NAME}' deleted successfully")
            except Exception as e:
                logger.warning(f"Failed to delete collection '{COLLECTION_NAME}': {e}")
                logger.warning("Collection may need to be manually deleted")


if __name__ == "__main__":
    main()
