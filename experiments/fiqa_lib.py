#!/usr/bin/env python3
"""
FiQA Evaluation Library - Shared Evaluation Functions

This module provides shared evaluation utilities used by both
fiqa_suite_runner.py and fiqa_tuner.py for consistent evaluation.
"""

import json
import logging
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


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class QueryResult:
    """Result from a single query."""
    latency_ms: float
    recall_at_10: float
    rerank_triggered: bool = False
    error: Optional[str] = None


# ============================================================================
# Data Loading Functions
# ============================================================================

def load_fiqa_queries(queries_path: Path) -> List[Dict[str, str]]:
    """
    Load FiQA queries from JSONL file.
    
    Args:
        queries_path: Path to queries.jsonl file
        
    Returns:
        List of {"query_id": str, "text": str} dictionaries
    """
    queries = []
    with open(queries_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                queries.append({
                    "query_id": data.get("_id", ""),
                    "text": data.get("text", "")
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
                        if query_id not in qrels:
                            qrels[query_id] = []
                        qrels[query_id].append(doc_id)
    
    logger.info(f"Loaded qrels for {len(qrels)} queries from {qrels_path}")
    return qrels


def load_queries_qrels(
    data_dir: str = "experiments/data/fiqa",
    sample: Optional[int] = None,
    seed: int = 42
) -> Tuple[List[Dict[str, str]], Dict[str, List[str]]]:
    """
    Load queries and qrels, optionally sampling queries.
    
    Args:
        data_dir: Directory containing queries.jsonl and qrels/test.tsv
        sample: If provided, randomly sample N queries (None = all)
        seed: Random seed for sampling
        
    Returns:
        Tuple of (queries list, qrels dict)
    """
    data_path = Path(data_dir)
    queries_file = data_path / "queries.jsonl"
    qrels_file = data_path / "qrels" / "test.tsv"
    
    if not queries_file.exists():
        raise FileNotFoundError(f"Queries file not found: {queries_file}")
    
    if not qrels_file.exists():
        raise FileNotFoundError(f"Qrels file not found: {qrels_file}")
    
    queries = load_fiqa_queries(queries_file)
    qrels = load_fiqa_qrels(qrels_file)
    
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
    Calculate Recall@10 metric.
    
    Args:
        retrieved_docs: List of retrieved document IDs
        relevant_docs: List of relevant document IDs
        
    Returns:
        Recall@10 value (0.0-1.0)
    """
    if not relevant_docs:
        return 0.0
    
    # Normalize doc IDs for comparison
    retrieved_set = {str(doc_id).strip() for doc_id in retrieved_docs[:10]}
    relevant_set = {str(doc_id).strip() for doc_id in relevant_docs}
    
    # Calculate hits
    hits = len(retrieved_set & relevant_set)
    
    # Recall@10 = hits / min(10, |relevant|)
    return hits / min(10, len(relevant_docs))


def extract_doc_ids(response: Dict) -> List[str]:
    """
    Extract document IDs from API response.
    
    Args:
        response: API response JSON
        
    Returns:
        List of document IDs
    """
    sources = response.get("sources", [])
    return [src.get("doc_id", "") for src in sources if src.get("doc_id")]


def call_query_api(
    base_url: str,
    query: str,
    top_k: int,
    config: Dict,
    timeout: Optional[float] = None
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
        
    Returns:
        Tuple of (response_json, latency_ms, error_message)
    """
    # Get timeout from environment variable if not provided
    if timeout is None:
        timeout = float(os.getenv("CLIENT_TIMEOUT_S", "10.0"))
    
    url = f"{base_url}/api/query"
    payload = {
        "question": query,
        "top_k": top_k,
        "use_hybrid": config.get("use_hybrid", False),
        "rerank": config.get("rerank", False)
    }
    
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
    
    for attempt in range(max_retries + 1):
        start_time = time.perf_counter()
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
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
    timeout: Optional[float] = None
) -> QueryResult:
    """
    Run a single query and return metrics.
    
    Returns:
        QueryResult with latency, recall, and rerank status
    """
    response, latency_ms, error = call_query_api(
        base_url=base_url,
        query=query_item["text"],
        top_k=top_k,
        config=config,
        timeout=timeout
    )
    
    if error:
        return QueryResult(latency_ms=latency_ms, recall_at_10=0.0, rerank_triggered=False, error=error)
    
    retrieved_docs = extract_doc_ids(response)
    relevant_docs = qrels.get(query_item["query_id"], [])
    recall = calculate_recall_at_10(retrieved_docs, relevant_docs)
    
    # Extract rerank trigger status from response
    rerank_triggered = response.get("reranker_triggered", False) or \
                       response.get("metrics", {}).get("rerank_triggered", False)
    
    return QueryResult(
        latency_ms=latency_ms,
        recall_at_10=recall,
        rerank_triggered=rerank_triggered,
        error=None
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
    warmup: int = 5
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
    all_latencies = []
    all_recalls = []
    rerank_triggers = []
    total_queries = 0
    failed_queries = 0
    
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
                timeout=timeout_s
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
                executor.submit(run_single_query, base_url, q, qrels, top_k, cfg, timeout_s): q
                for q in repeat_queries
            }
            
            completed = 0
            for future in as_completed(futures):
                total_queries += 1
                completed += 1
                
                result = future.result()
                
                if result.error:
                    logger.warning(f"Query failed: {result.error}")
                    failed_queries += 1
                    continue
                
                all_latencies.append(result.latency_ms)
                all_recalls.append(result.recall_at_10)
                rerank_triggers.append(result.rerank_triggered)
                
                if completed % 100 == 0:
                    logger.info(f"  Processed {completed}/{len(repeat_queries)} queries")
    
    # Calculate aggregated metrics
    if not all_latencies:
        logger.error("No successful queries!")
        return {
            "p95_ms": 0.0,
            "mean_latency_ms": 0.0,
            "qps": 0.0,
            "recall_at_10": 0.0,
            "rerank_trigger_rate": 0.0,
            "total_queries": total_queries,
            "failed_queries": failed_queries
        }
    
    # Calculate p95 latency
    sorted_latencies = sorted(all_latencies)
    p95_index = int(0.95 * len(sorted_latencies))
    p95_ms = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]
    
    # Calculate QPS
    mean_latency = statistics.mean(all_latencies)
    qps = 1000.0 / mean_latency if mean_latency > 0 else 0.0
    
    # Calculate rerank trigger rate
    rerank_trigger_rate = sum(rerank_triggers) / len(rerank_triggers) if rerank_triggers else 0.0
    
    return {
        "p95_ms": p95_ms,
        "mean_latency_ms": mean_latency,
        "qps": qps,
        "recall_at_10": statistics.mean(all_recalls),
        "rerank_trigger_rate": rerank_trigger_rate,
        "total_queries": total_queries,
        "failed_queries": failed_queries
    }


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

