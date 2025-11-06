"""
metrics.py - Extended Evaluation Metrics
========================================
Implements Recall@1/3/10, nDCG@10, MRR, and hard subset evaluation.
"""
import logging
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


def _dedup_by_doc_id(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """De-duplicate hits by doc_id, keeping first occurrence."""
    seen = set()
    out = []
    for h in hits:
        doc_id = h.get("doc_id") or h.get("id") or (h.get("payload", {}) if isinstance(h.get("payload"), dict) else {}).get("doc_id")
        if doc_id is None:
            continue
        doc_id_str = str(doc_id).strip()
        if doc_id_str in seen:
            continue
        seen.add(doc_id_str)
        out.append(h)
    return out


def topk_after_dedup(hits: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
    """Get top K hits after de-duplication by doc_id."""
    return _dedup_by_doc_id(hits)[:k]


def calculate_recall_at_k(retrieved_docs: List[str], relevant_docs: List[str], k: int) -> float:
    """
    Calculate Recall@K metric (with de-duplication).
    
    Args:
        retrieved_docs: List of retrieved document IDs (top K, already deduplicated)
        relevant_docs: List of relevant document IDs
        k: K value (1, 3, 10, etc.)
        
    Returns:
        Recall@K value (0.0-1.0)
    """
    if not relevant_docs:
        return 0.0
    
    # Normalize doc IDs for comparison
    retrieved_set = {str(doc_id).strip() for doc_id in retrieved_docs[:k]}
    relevant_set = {str(doc_id).strip() for doc_id in relevant_docs}
    
    # Calculate hits
    hits = len(retrieved_set & relevant_set)
    
    # Recall@K = hits / min(K, |relevant|)
    return hits / min(k, len(relevant_docs))


def calculate_ndcg_at_k(retrieved_docs: List[str], relevant_docs: List[str], k: int) -> float:
    """
    Calculate nDCG@K (Normalized Discounted Cumulative Gain).
    
    Args:
        retrieved_docs: List of retrieved document IDs in order (already deduplicated)
        relevant_docs: List of relevant document IDs (unordered)
        k: K value (typically 10)
        
    Returns:
        nDCG@K value (0.0-1.0)
    """
    if not relevant_docs:
        return 0.0
    
    # Normalize doc IDs
    relevant_set = {str(doc_id).strip() for doc_id in relevant_docs}
    retrieved_subset = [str(doc_id).strip() for doc_id in retrieved_docs[:k]]
    
    # Calculate DCG
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_subset):
        if doc_id in relevant_set:
            # Relevance score = 1 for relevant docs
            rel = 1.0
            # Position is i+1 (1-indexed)
            dcg += rel / np.log2(i + 2)  # log2(i+2) because position is i+1, and log2(1) = 0
    
    # Calculate IDCG (Ideal DCG)
    # IDCG is the DCG for perfect ranking (all relevant docs first)
    num_relevant = len(relevant_set)
    idcg = 0.0
    for i in range(min(k, num_relevant)):
        idcg += 1.0 / np.log2(i + 2)
    
    # nDCG = DCG / IDCG
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def calculate_mrr(retrieved_docs: List[str], relevant_docs: List[str]) -> float:
    """
    Calculate MRR (Mean Reciprocal Rank).
    
    For a single query, RR = 1/rank of first relevant doc, or 0 if none found.
    
    Args:
        retrieved_docs: List of retrieved document IDs in order
        relevant_docs: List of relevant document IDs
        
    Returns:
        RR value for this query (0.0-1.0)
    """
    if not relevant_docs:
        return 0.0
    
    # Normalize doc IDs
    relevant_set = {str(doc_id).strip() for doc_id in relevant_docs}
    
    # Find rank of first relevant document (1-indexed)
    for rank, doc_id in enumerate(retrieved_docs, start=1):
        if str(doc_id).strip() in relevant_set:
            return 1.0 / rank
    
    return 0.0


def calculate_all_metrics(
    retrieved_docs: List[str],
    relevant_docs: List[str]
) -> Dict[str, float]:
    """
    Calculate all metrics for a single query.
    
    Returns:
        Dict with recall_at_1, recall_at_3, recall_at_10, ndcg_at_10, mrr
    """
    return {
        "recall_at_1": calculate_recall_at_k(retrieved_docs, relevant_docs, 1),
        "recall_at_3": calculate_recall_at_k(retrieved_docs, relevant_docs, 3),
        "recall_at_10": calculate_recall_at_k(retrieved_docs, relevant_docs, 10),
        "ndcg_at_10": calculate_ndcg_at_k(retrieved_docs, relevant_docs, 10),
        "mrr": calculate_mrr(retrieved_docs, relevant_docs)
    }


def identify_hard_subset(
    queries: List[Dict],
    qrels: Dict[str, List[str]],
    method: str = "bm25_low_score",
    bm25_threshold: float = 0.1
) -> List[bool]:
    """
    Identify hard queries based on different criteria.
    
    Args:
        queries: List of query dicts with 'query_id' and 'text'
        qrels: Qrels dict mapping query_id to relevant doc IDs
        method: Method to identify hard queries:
            - "bm25_low_score": BM25 top1 score < threshold
            - "long_query": Query length > 75th percentile
        bm25_threshold: Threshold for BM25 score method
        
    Returns:
        List of booleans indicating if each query is hard
    """
    hard_flags = []
    
    if method == "bm25_low_score":
        # Method a: BM25 top1 score < threshold
        try:
            from services.fiqa_api.search.bm25 import bm25_search, is_bm25_ready
            if not is_bm25_ready():
                logger.warning("[METRICS] BM25 not ready, skipping hard subset identification")
                return [False] * len(queries)
            
            for query_item in queries:
                query_text = query_item.get("text", "")
                query_id = query_item.get("_id") or query_item.get("query_id", "")
                
                # Run BM25 search
                bm25_results = bm25_search(query_text, top_k=1)
                if bm25_results and len(bm25_results) > 0:
                    top1_score = bm25_results[0].get("score", 1.0)
                    is_hard = top1_score < bm25_threshold
                else:
                    # No BM25 results - consider hard
                    is_hard = True
                
                hard_flags.append(is_hard)
        except Exception as e:
            logger.warning(f"[METRICS] Failed to identify hard subset via BM25: {e}")
            return [False] * len(queries)
    
    elif method == "long_query":
        # Method b: Query length > 75th percentile
        query_lengths = [len(q.get("text", "")) for q in queries]
        if query_lengths:
            percentile_75 = np.percentile(query_lengths, 75)
            hard_flags = [len(q.get("text", "")) > percentile_75 for q in queries]
        else:
            hard_flags = [False] * len(queries)
    else:
        # Default: no hard subset
        hard_flags = [False] * len(queries)
    
    return hard_flags


def aggregate_metrics(
    all_results: List[Dict[str, float]],
    hard_flags: Optional[List[bool]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Aggregate metrics across all queries.
    
    Args:
        all_results: List of metric dicts (one per query)
        hard_flags: Optional list of booleans indicating hard queries
        
    Returns:
        Dict with 'overall' and optionally 'hard' metrics
    """
    if not all_results:
        return {"overall": {}}
    
    # Aggregate overall metrics
    overall = {
        "recall_at_1": np.mean([r.get("recall_at_1", 0) for r in all_results]),
        "recall_at_3": np.mean([r.get("recall_at_3", 0) for r in all_results]),
        "recall_at_10": np.mean([r.get("recall_at_10", 0) for r in all_results]),
        "ndcg_at_10": np.mean([r.get("ndcg_at_10", 0) for r in all_results]),
        "mrr": np.mean([r.get("mrr", 0) for r in all_results])
    }
    
    result = {"overall": overall}
    
    # Aggregate hard subset metrics if provided
    if hard_flags and len(hard_flags) == len(all_results):
        hard_results = [r for r, is_hard in zip(all_results, hard_flags) if is_hard]
        if hard_results:
            result["hard"] = {
                "recall_at_1": np.mean([r.get("recall_at_1", 0) for r in hard_results]),
                "recall_at_3": np.mean([r.get("recall_at_3", 0) for r in hard_results]),
                "recall_at_10": np.mean([r.get("recall_at_10", 0) for r in hard_results]),
                "ndcg_at_10": np.mean([r.get("ndcg_at_10", 0) for r in hard_results]),
                "mrr": np.mean([r.get("mrr", 0) for r in hard_results]),
                "count": len(hard_results)
            }
    
    return result

