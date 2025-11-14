#!/usr/bin/env python3
"""
FiQA Evaluation Library - Shared Evaluation Functions

This module provides shared evaluation utilities used by both
fiqa_suite_runner.py and fiqa_tuner.py for consistent evaluation.
"""

import json
import logging
import math
import os
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_doc_id(x) -> Optional[str]:
    """Normalize document identifier strings."""
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    if s.lower().startswith("doc:"):
        s = s[4:]
    return s.lower()


def extract_doc_ids(resp: Dict) -> List[str]:
    """Extract normalized document IDs from common response payload shapes."""
    if not isinstance(resp, dict):
        return []

    cands: List[Optional[str]] = []
    list_paths = [
        ("sources",),
        ("results",),
        ("hits",),
        ("docs",),
    ]

    for path in list_paths:
        cur = resp
        ok = True
        for key in path:
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break
        if not ok or not isinstance(cur, list):
            continue
        for item in cur:
            if not isinstance(item, dict):
                continue
            value = None
            for candidate_key in ("doc_id", "id", "document_id", "_id"):
                if candidate_key in item:
                    value = item[candidate_key]
                    break
                metadata = item.get("metadata")
                if isinstance(metadata, dict) and candidate_key in metadata:
                    value = metadata[candidate_key]
                    break
            cands.append(normalize_doc_id(value))

    doc_ids_field = resp.get("doc_ids")
    if isinstance(doc_ids_field, list):
        cands.extend(normalize_doc_id(x) for x in doc_ids_field)

    deduped: List[str] = []
    for candidate in cands:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class QueryResult:
    """Result from a single query."""
    latency_ms: float
    hit: int
    recall_at_10: float
    rerank_triggered: bool = False
    tokens_used: int = 0
    error: Optional[str] = None
def percentile(values: List[float], q: float) -> Optional[float]:
    """
    Compute percentile using nearest-rank method (ceil).

    Args:
        values: Iterable of numeric values.
        q: Quantile in [0,1].

    Returns:
        Percentile value as float or None when unavailable.
    """
    if not values:
        return None
    if q <= 0:
        return float(min(values))
    if q >= 1:
        return float(max(values))
    vals = sorted(values)
    idx = max(0, int(math.ceil(q * len(vals))) - 1)
    idx = min(idx, len(vals) - 1)
    return float(vals[idx])


def extract_total_tokens(resp_json: Dict[str, object]) -> int:
    """Extract total tokens from common response structures."""
    if not isinstance(resp_json, dict):
        return 0

    def _safe_int(value) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _coerce_total(container: Optional[Dict[str, object]]) -> Optional[int]:
        if not isinstance(container, dict):
            return None
        total = _safe_int(container.get("total_tokens"))
        if total is not None:
            return total
        input_tokens = _safe_int(container.get("input_tokens") or container.get("prompt_tokens"))
        output_tokens = _safe_int(container.get("output_tokens") or container.get("completion_tokens"))
        if input_tokens is not None or output_tokens is not None:
            return (input_tokens or 0) + (output_tokens or 0)
        token_usage = container.get("token_usage")
        if isinstance(token_usage, dict):
            total = _safe_int(token_usage.get("total"))
            if total is not None:
                return total
            return _coerce_total(token_usage)
        return None

    containers: List[Dict[str, object]] = []

    usage = resp_json.get("usage")
    if isinstance(usage, dict):
        containers.append(usage)

    meta = resp_json.get("meta")
    if isinstance(meta, dict):
        containers.append(meta)
        token_usage = meta.get("token_usage")
        if isinstance(token_usage, dict):
            containers.append(token_usage)

    observability_metrics = resp_json.get("observability_metrics")
    if isinstance(observability_metrics, dict):
        containers.append(observability_metrics)

    token_usage_root = resp_json.get("token_usage")
    if isinstance(token_usage_root, dict):
        containers.append(token_usage_root)

    metrics = resp_json.get("metrics")
    if isinstance(metrics, dict):
        metrics_token_usage = metrics.get("token_usage")
        if isinstance(metrics_token_usage, dict):
            containers.append(metrics_token_usage)

    rerank = resp_json.get("rerank")
    if isinstance(rerank, dict):
        rerank_usage = rerank.get("usage")
        if isinstance(rerank_usage, dict):
            containers.append(rerank_usage)

    for container in containers:
        total = _coerce_total(container)
        if total is not None:
            return max(0, total)

    return 0


# ============================================================================
# Data Loading Functions
# ============================================================================

def load_fiqa_queries(queries_path: Path) -> List[Dict[str, str]]:
    """
    Load FiQA queries from JSONL file or plain txt file.
    
    Args:
        queries_path: Path to queries.jsonl or fiqa_queries.txt file
        
    Returns:
        List of {"query_id": str, "text": str} dictionaries
    """
    queries = []
    
    # Handle plain txt files
    if queries_path.suffix == ".txt":
        with open(queries_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                text = line.strip()
                if text:
                    queries.append({
                        "query_id": str(idx),
                        "text": text
                    })
    else:
        # Handle JSONL files
        with open(queries_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())
                    qid = data.get("_id") or data.get("id") or data.get("query_id", "")
                    text = data.get("text", "")
                    if qid and text:
                        queries.append({
                            "query_id": qid,
                            "text": text
                        })
    
    logger.info(f"Loaded {len(queries)} queries from {queries_path}")
    return queries


def load_fiqa_qrels(qrels_path: Path) -> Dict[str, List[str]]:
    """
    Load FiQA qrels (ground truth) from TSV file.
    
    Args:
        qrels_path: Path to test.tsv qrels file
        
    Returns:
        Dict mapping query_id to list of relevant doc_ids
    """
    qrels = {}
    with open(qrels_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0:  # Skip header
                continue
            if line.strip():
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    query_id, doc_id, score = parts[0], parts[1], parts[2]
                    if int(score) > 0:  # Only relevant docs
                        normalized = normalize_doc_id(doc_id)
                        if not normalized:
                            continue
                        if query_id not in qrels:
                            qrels[query_id] = []
                        qrels[query_id].append(normalized)
    
    logger.info(f"Loaded qrels for {len(qrels)} queries from {qrels_path}")
    return qrels


def load_fiqa_qrels_trec(qrels_path: Path) -> Dict[str, List[str]]:
    """
    Load FiQA qrels (ground truth) from TREC format file.
    
    TREC format: query_id Q0 doc_id relevance_score run_id
    
    Args:
        qrels_path: Path to .trec qrels file
        
    Returns:
        Dict mapping query_id to list of relevant doc_ids
    """
    qrels = {}
    with open(qrels_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 4:
                    query_id = parts[0]
                    doc_id = parts[2]
                    score = int(parts[3])
                    if score > 0:  # Only relevant docs
                        normalized = normalize_doc_id(doc_id)
                        if not normalized:
                            continue
                        if query_id not in qrels:
                            qrels[query_id] = []
                        qrels[query_id].append(normalized)
    
    logger.info(f"Loaded qrels for {len(qrels)} queries from {qrels_path}")
    return qrels


def load_fiqa_qrels_jsonl(qrels_path: Path) -> Dict[str, List[str]]:
    """
    Load FiQA qrels (ground truth) from JSONL format file.
    
    JSONL format: {"query_id": "...", "relevant_doc_ids": ["...", "..."]}
    
    Args:
        qrels_path: Path to .jsonl qrels file
        
    Returns:
        Dict mapping query_id to list of relevant doc_ids
    """
    qrels = {}
    with open(qrels_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                query_id = data.get("query_id", "")
                doc_ids = data.get("relevant_doc_ids", [])
                if query_id and doc_ids:
                    normalized_ids = [
                        normalize_doc_id(doc_id) for doc_id in doc_ids
                    ]
                    qrels[query_id] = [doc_id for doc_id in normalized_ids if doc_id]
    
    logger.info(f"Loaded qrels for {len(qrels)} queries from {qrels_path}")
    return qrels


def load_queries_qrels(
    data_dir: Optional[str] = None,
    dataset_name: Optional[str] = None,
    qrels_name: Optional[str] = None,
    sample: Optional[int] = None,
    seed: int = 42
) -> Tuple[List[Dict[str, str]], Dict[str, List[str]]]:
    """
    Load queries and qrels, optionally sampling queries.
    
    Query lookup order (v1 format if dataset_name provided):
    1. data/fiqa_v1/{dataset_name}/queries.jsonl
    2. data/fiqa_v1/fiqa_queries_v1.jsonl (shared fallback)
    3. experiments/data/fiqa/queries.jsonl (legacy)
    4. data/fiqa/fiqa_queries.txt (on-the-fly convert)
    
    Falls back to old path format if dataset_name/qrels_name are not provided:
    - queries: {data_dir}/queries.jsonl
    - qrels: {data_dir}/qrels/test.tsv
    
    Args:
        data_dir: Directory containing queries.jsonl and qrels/test.tsv (fallback only)
        dataset_name: Dataset name for v1 path format (e.g., "fiqa_10k_v1")
        qrels_name: Qrels name for v1 path format (e.g., "fiqa_qrels_10k_v1")
        sample: If provided, randomly sample N queries (None = all)
        seed: Random seed for sampling
        
    Returns:
        Tuple of (queries list, qrels dict)
    """
    # Find repo root
    repo_root = Path(__file__).resolve()
    original_file = repo_root
    while repo_root != repo_root.parent:
        if (repo_root / "pyproject.toml").exists() or (repo_root / ".git").exists():
            break
        parent = repo_root.parent
        if parent == repo_root:  # Reached filesystem root
            break
        repo_root = parent
    
    # If we reached root and didn't find markers, try common locations
    if repo_root == Path("/"):
        # Check if we're in /app (common in Docker containers)
        if (Path("/app") / "experiments").exists():
            repo_root = Path("/app")
        elif (original_file.parent.parent.parent / "experiments").exists():
            # Go up from experiments/fiqa_lib.py -> experiments -> parent
            repo_root = original_file.parent.parent.parent
    
    # Use new v1 frozen path format if dataset_name/qrels_name are provided
    if dataset_name and qrels_name:
        # Query lookup order for v1
        queries_candidates = [
            repo_root / "data" / "fiqa_v1" / dataset_name / "queries.jsonl",
            repo_root / "data" / "fiqa_v1" / "fiqa_queries_v1.jsonl",
            repo_root / "experiments" / "data" / "fiqa" / "queries.jsonl",  # Legacy path (exists)
            repo_root / "data" / "fiqa" / "queries.jsonl",  # Alternative legacy path
            repo_root / "data" / "fiqa_queries.txt",
        ]
        
        queries_file = None
        for candidate in queries_candidates:
            if candidate.exists():
                queries_file = candidate
                break
        
        if queries_file is None:
            raise FileNotFoundError(
                f"Queries file not found. Tried:\n" +
                "\n".join([f"  - {c}" for c in queries_candidates])
            )
        
        # Log which path is used
        if queries_file == queries_candidates[0]:
            logger.info(f"✅ Using v1 queries: {queries_file}")
        else:
            logger.info(f"⚠️  Fallback to legacy queries: {queries_file}")
        
        # Try JSONL first, then TREC (both formats supported)
        qrels_candidates = [
            repo_root / "data" / "fiqa_v1" / f"{qrels_name}.jsonl",
            repo_root / "data" / "fiqa_v1" / f"{qrels_name}.trec",
            repo_root / "experiments" / "data" / "fiqa" / "qrels" / "test.tsv",  # Legacy path
        ]
        qrels_file = None
        for candidate in qrels_candidates:
            if candidate.exists():
                qrels_file = candidate
                break
        
        if qrels_file is None:
            # Fallback: try without extension (will check in loop below)
            qrels_file = repo_root / "data" / "fiqa_v1" / qrels_name
        
        corpus_file = repo_root / "data" / "fiqa_v1" / dataset_name / "corpus.jsonl"
    else:
        # Fallback to old path format
        if data_dir is None:
            data_dir = "experiments/data/fiqa"
        data_path = Path(data_dir)
        queries_file = data_path / "queries.jsonl"
        qrels_file = data_path / "qrels" / "test.tsv"
        corpus_file = None  # Not used in old format
        
        if not queries_file.exists():
            raise FileNotFoundError(f"Queries file not found: {queries_file}")
    
    # Handle qrels file discovery if extension wasn't specified
    if not qrels_file.exists():
        # Try common extensions
        for ext in ['.jsonl', '.trec', '.tsv']:
            candidate = Path(str(qrels_file) + ext)
            if candidate.exists():
                qrels_file = candidate
                break
    
    if not qrels_file.exists():
        raise FileNotFoundError(f"Qrels file not found: {qrels_file}")
    
    queries = load_fiqa_queries(queries_file)
    
    # Load qrels based on file extension
    if qrels_file.suffix == '.jsonl':
        qrels = load_fiqa_qrels_jsonl(qrels_file)
    elif qrels_file.suffix == '.trec':
        qrels = load_fiqa_qrels_trec(qrels_file)
    else:
        qrels = load_fiqa_qrels(qrels_file)  # TSV format
    
    # Normalize qrels doc IDs (dedupe while preserving order)
    for qid, docs in list(qrels.items()):
        seen_docs = set()
        normalized_list: List[str] = []
        for doc_id in docs:
            normalized = normalize_doc_id(doc_id)
            if normalized and normalized not in seen_docs:
                seen_docs.add(normalized)
                normalized_list.append(normalized)
        if normalized_list:
            qrels[qid] = normalized_list
        else:
            qrels.pop(qid, None)

    # Filter queries to only those with ground truth
    queries = [q for q in queries if q["query_id"] in qrels]
    total_with_gt = len(queries)
    logger.info(f"Found {total_with_gt} queries with ground truth")
    
    # Sample queries if requested
    if sample and sample > 0:
        if total_with_gt > sample:
            random.seed(seed)
            queries = random.sample(queries, sample)
            logger.info(f"Sampled {sample} queries from {total_with_gt} total (seed={seed})")
        else:
            logger.info(f"Sample size ({sample}) >= total queries ({total_with_gt}), using all queries")
    
    logger.info(f"Using {len(queries)} queries for evaluation")
    return queries, qrels


# ============================================================================
# Evaluation Functions
# ============================================================================

def calculate_recall_at_10(retrieved_docs: List[str], relevant_docs: List[str]) -> float:
    """
    Calculate Recall@10 metric (legacy function, delegates to metrics module).
    
    Args:
        retrieved_docs: List of retrieved document IDs
        relevant_docs: List of relevant document IDs
        
    Returns:
        Recall@10 value (0.0-1.0)
    """
    from experiments.metrics import calculate_recall_at_k
    return calculate_recall_at_k(retrieved_docs, relevant_docs, 10)


def extract_doc_ids(response: Dict) -> List[str]:
    """
    Extract document IDs from API response.
    
    Args:
        response: API response JSON
        
    Returns:
        List of document IDs
    """
    sources = response.get("sources") or response.get("results") or []
    doc_ids: List[str] = []
    seen = set()
    for item in sources:
        if not isinstance(item, dict):
            continue
        doc_id = item.get("doc_id") or item.get("id")
        if not doc_id and isinstance(item.get("metadata"), dict):
            metadata = item["metadata"]
            doc_id = metadata.get("doc_id") or metadata.get("id")
        if doc_id:
            doc_str = str(doc_id)
            if doc_str not in seen:
                seen.add(doc_str)
                doc_ids.append(doc_str)
    return doc_ids


def call_query_api(
    base_url: str,
    query: str,
    top_k: int,
    config: Dict,
    timeout: Optional[float] = None,
    collection: Optional[str] = None
) -> Tuple[Dict, float, Optional[str]]:
    """
    Call /api/query endpoint with specified configuration.
    Includes light retry for timeout/ECONNRESET errors (max 1 retry, 200ms backoff).
    
    Args:
        base_url: Base API URL
        query: Search query text
        top_k: Number of results
        config: Experiment configuration dictionary
        timeout: Request timeout in seconds
        collection: Collection name (e.g., 'fiqa_50k_v1', 'fiqa_10k_v1')
        
    Returns:
        Tuple of (response_json, latency_ms, error_message)
    """
    # Get timeout from environment variable if not provided
    if timeout is None:
        timeout = float(os.getenv("CLIENT_TIMEOUT_S", "20.0"))
    
    url = f"{base_url}/api/query"
    payload = {
        "question": query,
        "top_k": top_k,
        "use_hybrid": config.get("use_hybrid", False),
        "rerank": config.get("rerank", False)
    }
    
    # Add collection parameter if provided (important for dataset_name support)
    if collection:
        payload["collection"] = collection
    
    # Add optional parameters if they exist
    if config.get("use_hybrid"):
        payload["rrf_k"] = config.get("rrf_k", 60)
    
    if config.get("rerank"):
        payload["rerank_top_k"] = config.get("rerank_top_k", 20)
        if config.get("rerank_if_margin_below") is not None:
            payload["rerank_if_margin_below"] = config.get("rerank_if_margin_below")
        payload["max_rerank_trigger_rate"] = config.get("max_rerank_trigger_rate", 0.25)
        payload["rerank_budget_ms"] = config.get("rerank_budget_ms", 25)
    
    max_retries = 1
    backoff_ms = 200
    
    headers = {"Content-Type": "application/json"}
    trace_header = os.getenv("TRACE_ID") or os.getenv("JOB_ID")
    if trace_header:
        headers["X-Trace-Id"] = trace_header

    for attempt in range(max_retries + 1):
        start_time = time.perf_counter()
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers=headers,
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            if response.status_code != 200:
                return None, latency_ms, f"HTTP {response.status_code}: {response.text}"
            
            result = response.json()
            return result, latency_ms, None
            
        except requests.exceptions.Timeout:
            latency_ms = (time.perf_counter() - start_time) * 1000
            if attempt < max_retries:
                time.sleep(backoff_ms / 1000.0)
                continue
            return None, latency_ms, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            error_str = str(e)
            # Check for ECONNRESET or broken pipe
            if "ECONNRESET" in error_str or "Broken pipe" in error_str or "Connection reset" in error_str:
                if attempt < max_retries:
                    time.sleep(backoff_ms / 1000.0)
                    continue
            return None, latency_ms, str(e)
        except requests.exceptions.RequestException as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return None, latency_ms, str(e)
    
    # Should not reach here, but just in case
    return None, 0.0, "Max retries exceeded"


def run_single_query(
    base_url: str,
    query_item: Dict,
    qrels: Dict[str, List[str]],
    top_k: int,
    config: Dict,
    timeout: Optional[float] = None,
    collection: Optional[str] = None
) -> QueryResult:
    """
    Run a single query and return metrics.
    
    Returns:
        QueryResult with latency, recall, and rerank status.
        Extended metrics (recall@1/3/10, ndcg@10, mrr) are stored in result.metrics dict.
    """
    response, latency_ms, error = call_query_api(
        base_url=base_url,
        query=query_item["text"],
        top_k=top_k,
        config=config,
        timeout=timeout,
        collection=collection
    )
    if error:
        return QueryResult(
            latency_ms=latency_ms,
            hit=0,
            recall_at_10=0.0,
            rerank_triggered=False,
            tokens_used=0,
            error=error,
        )

    if not isinstance(response, dict):
        return QueryResult(
            latency_ms=latency_ms,
            hit=0,
            recall_at_10=0.0,
            rerank_triggered=False,
            tokens_used=0,
            error="invalid_response_shape",
        )

    tokens_used = extract_total_tokens(response)
    rerank_triggered = response.get("reranker_triggered", False) or \
        response.get("metrics", {}).get("rerank_triggered", False)

    retrieved_docs = extract_doc_ids(response)
    if not retrieved_docs:
        return QueryResult(
            latency_ms=latency_ms,
            hit=0,
            recall_at_10=0.0,
            rerank_triggered=rerank_triggered,
            tokens_used=tokens_used,
            error="empty_results",
        )

    relevant_docs = set(qrels.get(query_item["query_id"], []))
    hit = 0
    if relevant_docs:
        if any(doc_id in relevant_docs for doc_id in retrieved_docs[:top_k]):
            hit = 1

    recall = float(hit)

    return QueryResult(
        latency_ms=latency_ms,
        hit=hit,
        recall_at_10=recall,
        rerank_triggered=rerank_triggered,
        tokens_used=tokens_used,
        error=None,
    )


def evaluate_config(
    cfg: dict,
    *,
    base_url: str,
    queries: List[Dict[str, str]],
    qrels: Dict[str, List[str]],
    top_k: int,
    concurrency: int = 16,
    repeats: int = 1,
    timeout_s: float = 15.0,
    warmup: int = 5,
    collection: Optional[str] = None,
    return_details: bool = False,
) -> dict:
    """
    Evaluate a single configuration and return aggregated metrics.
    
    Args:
        cfg: Configuration dictionary (use_hybrid, rerank, etc.)
        base_url: Base API URL
        queries: List of query dictionaries
        qrels: Ground truth qrels
        top_k: Top-K parameter
        concurrency: Thread pool size
        repeats: Number of evaluation repeats
        timeout_s: Request timeout in seconds
        warmup: Number of warmup queries
        collection: Collection name (e.g., 'fiqa_50k_v1', 'fiqa_10k_v1')
        
    Returns:
        Dictionary with metrics:
            - p95_ms: 95th percentile latency
            - mean_latency_ms: Mean latency
            - qps: Queries per second
            - recall_at_10: Mean Recall@10
            - rerank_trigger_rate: Fraction of queries that triggered rerank
            - total_queries: Total queries executed
            - failed_queries: Number of failed queries
    """
    all_latencies: List[float] = []
    rerank_triggers: List[bool] = []
    token_counts: List[int] = []
    total_queries = 0
    failed_queries = 0
    hit_count = 0
    tokens_sum = 0
    
    # Run warmup (sequential)
    if warmup > 0:
        logger.info(f"Warming up with {warmup} queries...")
        for i in range(warmup):
            query = queries[i % len(queries)]
            _, _, error = call_query_api(
                base_url=base_url,
                query=query["text"],
                top_k=top_k,
                config=cfg,
                timeout=timeout_s,
                collection=collection
            )
            if error:
                logger.warning(f"Warmup query {i+1} failed: {error}")
    
    # Run experiment repeats with concurrency
    for repeat in range(repeats):
        logger.info(f"Repeat {repeat + 1}/{repeats}...")
        
        # Create expanded query list for this repeat
        repeat_queries = queries * 1  # Single pass through all queries
        
        # Execute queries in parallel
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(run_single_query, base_url, q, qrels, top_k, cfg, timeout_s, collection): q
                for q in repeat_queries
            }
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                total_queries += 1
                
                result = future.result()
                all_latencies.append(float(result.latency_ms))
                tokens_sum += result.tokens_used or 0
                token_counts.append(result.tokens_used or 0)
                
                if result.error:
                    logger.warning(f"Query failed: {result.error}")
                    failed_queries += 1
                else:
                    hit_count += result.hit
                    rerank_triggers.append(result.rerank_triggered)
                
                if completed % 100 == 0:
                    logger.info(f"  Processed {completed}/{len(repeat_queries)} queries")
    
    # Calculate aggregated metrics
    if not all_latencies:
        logger.error("No successful queries!")
        result = {
            "p95_ms": None,
            "mean_latency_ms": None,
            "qps": None,
            "recall_at_10": None,
            "err_rate": None,
            "rerank_trigger_rate": None,
            "total_queries": total_queries,
            "failed_queries": failed_queries,
            "hit_count": hit_count,
            "cost_tokens": 0,
        }
        if return_details:
            result["latencies_ms"] = []
            result["token_counts"] = []
        return result
    
    # Calculate p95 latency (ensure float ms)
    p95_ms = percentile(all_latencies, 0.95)
    
    # Calculate QPS
    mean_latency = statistics.mean(all_latencies) if all_latencies else None
    qps = float(1000.0 / mean_latency) if mean_latency and mean_latency > 0 else None
    
    # Calculate rerank trigger rate
    rerank_trigger_rate = float(sum(rerank_triggers) / len(rerank_triggers)) if rerank_triggers else None
    recall_at_10 = (hit_count / total_queries) if total_queries else None
    err_rate = (failed_queries / total_queries) if total_queries else None
    
    result = {
        "p95_ms": p95_ms,
        "mean_latency_ms": mean_latency,
        "qps": qps,
        "recall_at_10": recall_at_10,
        "err_rate": err_rate,
        "rerank_trigger_rate": rerank_trigger_rate,
        "total_queries": total_queries,
        "failed_queries": failed_queries,
        "hit_count": hit_count,
        "cost_tokens": tokens_sum,
    }
    if return_details:
        result["latencies_ms"] = list(all_latencies)
        result["token_counts"] = list(token_counts)
    return result


def objective(metrics: dict) -> float:
    """
    Calculate objective score from metrics.
    
    Score formula:
        score = recall_at_10 - 0.2*(p95_ms/1000.0) - 0.1*rerank_trigger_rate
    
    Args:
        metrics: Dictionary with recall_at_10, p95_ms, rerank_trigger_rate
        
    Returns:
        Objective score (higher is better)
    """
    recall = metrics.get("recall_at_10", 0.0)
    p95_ms = metrics.get("p95_ms", 0.0)
    rerank_trigger_rate = metrics.get("rerank_trigger_rate", 0.0)
    
    score = recall - 0.2 * (p95_ms / 1000.0) - 0.1 * rerank_trigger_rate
    return score


def put_best_to_api(best_cfg: dict, base_url: str) -> bool:
    """
    PUT best configuration to /api/best endpoint with deep merge.
    
    Args:
        best_cfg: Configuration dictionary (use_hybrid, rerank, etc.)
        base_url: Base API URL
        
    Returns:
        True if successful, False otherwise
    """
    url = f"{base_url}/api/best"
    
    # Map config to API format (deep merge structure)
    pipeline_config = {
        "hybrid": best_cfg.get("use_hybrid", False)
    }
    
    # Add rrf_k if hybrid is enabled
    if pipeline_config["hybrid"]:
        pipeline_config["rrf_k"] = best_cfg.get("rrf_k", 60)
    
    # Add gated_rerank if rerank is enabled
    if best_cfg.get("rerank", False):
        pipeline_config["gated_rerank"] = {
            "top_k": best_cfg.get("rerank_top_k", 20),
            "margin": best_cfg.get("rerank_if_margin_below", 0.12),
            "trigger_rate_cap": best_cfg.get("max_rerank_trigger_rate", 0.25),
            "budget_ms": best_cfg.get("rerank_budget_ms", 25)
        }
    
    # Build payload with metrics if available
    payload = {
        "pipeline": pipeline_config
    }
    
    # Add metrics if provided in best_cfg
    if "metrics" in best_cfg:
        payload["metrics"] = best_cfg["metrics"]
    
    try:
        response = requests.put(url, json=payload, timeout=10)
        if response.status_code in [200, 201]:
            logger.info(f"Successfully updated /api/best")
            return True
        else:
            logger.warning(f"Failed to update /api/best: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error updating /api/best: {e}")
        return False

