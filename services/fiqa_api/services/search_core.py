"""
search_core.py - Core Search Logic (Reusable Service Layer)
===========================================================
Pure business logic for search operations, extracted from route handlers.
This module provides a reusable `perform_search` function that can be called
by multiple endpoints (e.g., /search and /api/query).

No HTTP concerns - pure business logic only.
Uses clients.py singletons for all external dependencies.
"""

import os
import time
import json
import logging
import math
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# ========================================
# Constants (configurable via env)
# ========================================

# Collection mapping
COLLECTION_MAP = {
    "fiqa": "beir_fiqa_full_ta",
    "beir_fiqa_full_ta": "beir_fiqa_full_ta",
    "fiqa_10k_v1": "fiqa_10k_v1",
    "fiqa_50k_v1": "fiqa_50k_v1",
    # Support dataset_name format
    "fiqa_10k": "fiqa_10k_v1",
    "fiqa_50k": "fiqa_50k_v1",
}

# Default candidate sizes for hybrid search
DENSE_K_DEFAULT = int(os.getenv("DENSE_K_DEFAULT", "60"))
BM25_K_DEFAULT = int(os.getenv("BM25_K_DEFAULT", "60"))

# ========================================
# Rerank Trigger Statistics (Module-level)
# ========================================

class TriggerStats:
    """Module-level rerank trigger statistics."""
    def __init__(self):
        self.total = 0
        self.triggered = 0
    
    def get_rate(self) -> float:
        """Get current trigger rate."""
        return self.triggered / max(self.total, 1)

_trigger_stats = TriggerStats()


# ========================================
# Helper Functions
# ========================================

def ensure_1d_float32(vec):
    """
    Normalize embedding vector to 1D float32 list.
    
    Handles:
    - list[float]: Direct list of floats
    - list[list[float]]: Nested list (e.g., from batch encode)
    - numpy array: Any shape numpy array
    
    Args:
        vec: Input vector (may be nested list or numpy array)
        
    Returns:
        1D list of float32 values
        
    Raises:
        ValueError: If vector is None or empty
    """
    if vec is None:
        raise ValueError("Vector is None")
    
    # Handle nested lists (e.g., from batch encode returning list[list[float]])
    if isinstance(vec, list) and len(vec) > 0 and isinstance(vec[0], list):
        vec = vec[0]
    
    # Convert to numpy array and ensure float32
    arr = np.asarray(vec, dtype=np.float32)
    
    # Flatten to 1D
    arr = arr.reshape(-1)
    
    # Convert back to list
    return arr.tolist()

def canonical_doc_id(hit: Dict[str, Any]) -> str:
    """
    Extract and normalize document ID from a search hit.
    Unifies dense hits (id field) and BM25 hits (doc_id field) to string.
    
    Args:
        hit: Search hit dictionary from dense or sparse search
        
    Returns:
        Normalized document ID as string
    """
    # Try common ID fields in order of preference
    doc_id = hit.get("id") or hit.get("doc_id") or hit.get("_id", "unknown")
    
    # Ensure string type for consistent comparison
    return str(doc_id)


def rrf_fuse(
    dense_results: List[Dict[str, Any]],
    sparse_results: List[Dict[str, Any]],
    k: int = 60,
    top_k: int = 10
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Fuse dense and sparse results using Reciprocal Rank Fusion.
    Performs doc_id deduplication and stable sorting.
    
    Args:
        dense_results: List of {"id": str, "score": float} from vector search
        sparse_results: List of {"doc_id": str, "score": float} from BM25
        k: RRF k parameter (default: 60)
        top_k: Number of results to return
        
    Returns:
        Tuple of (fused results list, fusion metrics dict with fusion_overlap and rrf_candidates)
    """
    # Normalize doc IDs using canonical_doc_id
    dense_doc_ids = set()
    dense_id_to_result = {}
    dense_id_to_rank = {}
    
    for rank, result in enumerate(dense_results[:top_k*2], start=1):
        doc_id = canonical_doc_id(result)
        if doc_id not in dense_doc_ids:
            dense_doc_ids.add(doc_id)
            dense_id_to_result[doc_id] = result
            dense_id_to_rank[doc_id] = rank
    
    sparse_doc_ids = set()
    sparse_id_to_result = {}
    sparse_id_to_rank = {}
    
    for rank, result in enumerate(sparse_results[:top_k*2], start=1):
        doc_id = canonical_doc_id(result)
        if doc_id not in sparse_doc_ids:
            sparse_doc_ids.add(doc_id)
            sparse_id_to_result[doc_id] = result
            sparse_id_to_rank[doc_id] = rank
    
    # Calculate fusion overlap (documents appearing in both lists)
    fusion_overlap = len(dense_doc_ids & sparse_doc_ids)
    
    # Build RRF score map: doc_id -> (rrf_score, dense_rank, bm25_rank)
    rrf_scores = {}
    all_doc_ids = dense_doc_ids | sparse_doc_ids
    
    for doc_id in all_doc_ids:
        dense_score = 1.0 / (k + dense_id_to_rank[doc_id]) if doc_id in dense_id_to_rank else 0.0
        sparse_score = 1.0 / (k + sparse_id_to_rank[doc_id]) if doc_id in sparse_id_to_rank else 0.0
        combined_score = dense_score + sparse_score
        
        # Store with stable sort keys: (rrf_score, dense_rank, bm25_rank)
        # Use large rank values for missing items to ensure stable ordering
        dense_rank = dense_id_to_rank.get(doc_id, 999999)
        bm25_rank = sparse_id_to_rank.get(doc_id, 999999)
        
        rrf_scores[doc_id] = (combined_score, dense_rank, bm25_rank)
    
    # Stable sort: primary by RRF score (desc), then by dense_rank (asc), then by bm25_rank (asc)
    sorted_docs = sorted(
        rrf_scores.items(),
        key=lambda x: (-x[1][0], x[1][1], x[1][2])  # Negative for descending score
    )[:top_k]
    
    # Build result list (merge back original metadata)
    results = []
    for doc_id, (score, _, _) in sorted_docs:
        # Prefer dense result metadata, fallback to sparse
        result_item = None
        if doc_id in dense_id_to_result:
            dense_r = dense_id_to_result[doc_id]
            result_item = {
                "id": doc_id,
                "text": dense_r.get("text", ""),
                "title": dense_r.get("title", ""),
                "score": float(score)
            }
        elif doc_id in sparse_id_to_result:
            sparse_r = sparse_id_to_result[doc_id]
            result_item = {
                "id": doc_id,
                "text": sparse_r.get("text", ""),
                "title": sparse_r.get("title", ""),
                "score": float(score)
            }
        
        if not result_item:
            result_item = {"id": doc_id, "text": "", "score": float(score)}
        
        results.append(result_item)
    
    # Return results and metrics
    metrics = {
        "fusion_overlap": fusion_overlap,
        "rrf_candidates": len(sorted_docs)
    }
    
    return results, metrics


def calculate_margin(results: List[Dict[str, Any]]) -> float:
    """
    Calculate score margin between top-1 and top-2 results.
    
    Args:
        results: List of results with "score" field
        
    Returns:
        Margin value (top1_score - top2_score), or 1.0 if < 2 results
    """
    if len(results) < 2:
        return 1.0
    
    scores = [r.get("score", 0.0) for r in results[:2]]
    return max(0.0, scores[0] - scores[1])


# ========================================
# Core Search Function (Reusable)
# ========================================

def perform_search(
    query: str,
    top_k: int = 10,
    collection: str = "fiqa",
    routing_flags: Optional[Dict[str, Any]] = None,
    faiss_engine: Optional[Any] = None,
    faiss_ready: bool = False,
    faiss_enabled: bool = False,
    lab_headers: Optional[Dict[str, str]] = None,
    use_hybrid: bool = False,
    rrf_k: int = 60,
    rerank: bool = False,
    rerank_top_k: int = 20,
    rerank_if_margin_below: Optional[float] = None,
    max_rerank_trigger_rate: float = 0.25,
    rerank_budget_ms: int = 25
) -> Dict[str, Any]:
    """
    Execute search with unified routing (FAISS/Qdrant/Milvus).
    
    This is the core search logic extracted from route handlers.
    Can be called by multiple endpoints without duplication.
    
    Args:
        query: Search query string
        top_k: Number of results to return (default: 10)
        collection: Collection name (default: "fiqa")
        routing_flags: Dict with 'enabled', 'mode', 'manual_backend' keys (default: None)
        faiss_engine: FAISS engine instance (or None)
        faiss_ready: Whether FAISS is ready (default: False)
        faiss_enabled: Whether FAISS is enabled (default: False)
        lab_headers: Optional lab experiment headers (default: None)
        
    Returns:
        Dict with:
            - ok: bool
            - results: List[Dict] with id, text, score, (optional title)
            - latency_ms: float
            - route: str (backend used)
            - fallback: bool (whether fallback occurred)
            - doc_ids: List[str] (extracted IDs)
        
    Raises:
        Exception: On critical errors (will be caught by route handler)
    """
    from services.fiqa_api.clients import (
        get_encoder_model, 
        get_qdrant_client, 
        get_redis_client,
        ensure_qdrant_connection
    )
    
    # Default routing flags
    if routing_flags is None:
        routing_flags = {"enabled": True, "mode": "rules"}
    
    # Ensure Qdrant connection is healthy before proceeding
    if not ensure_qdrant_connection():
        logger.warning("[SEARCH] Qdrant connection unhealthy, search may fail")
    
    start_time = time.perf_counter()
    t_vec_search = None
    t_rerank = None
    t_serialize = None
    route_used = "qdrant"  # Default
    fallback = False
    
    # Map collection name
    actual_collection = COLLECTION_MAP.get(collection, collection)
    
    # Get routing flags
    enabled = routing_flags.get("enabled", True)
    mode = routing_flags.get("mode", "rules")
    manual_backend = routing_flags.get("manual_backend")
    
    # ✅ Use unified router if available (supports Milvus)
    unified_router_available = False
    try:
        from engines.factory import get_router
        unified_router_available = True
    except ImportError:
        logger.debug("[SEARCH] Unified router not available, using legacy routing")
    
    if unified_router_available and os.getenv("VECTOR_BACKEND", "faiss") == "milvus":
        logger.info(f"[SEARCH] Using unified router with VECTOR_BACKEND=milvus")
        unified_router = get_router()
        
        # Search using unified router
        search_results, debug_info = unified_router.search(
            query=query,
            collection_name=actual_collection,
            top_k=top_k,
            force_backend=manual_backend,
            trace_id=None,
            with_fallback=True
        )
        
        route_used = debug_info.get("routed_to", "unknown")
        logger.info(f"[SEARCH] Router decision: {route_used}, results: {len(search_results)}")
        
        # Format results
        results = []
        for r in search_results:
            results.append({
                "id": r.get("id", "unknown"),
                "text": r.get("text", ""),
                "score": float(r.get("score", 0.0))
            })
    
    else:
        # Legacy routing (FAISS/Qdrant only)
        should_use_faiss = False
        
        if manual_backend:
            # Manual override
            should_use_faiss = (manual_backend == "faiss")
            route_used = manual_backend
        elif enabled and faiss_ready and faiss_enabled:
            # Use Router to decide
            from backend_core.routing_policy import Router
            router = Router(policy=mode, topk_threshold=32)
            has_filter = False  # Could extract from request if needed
            
            decision = router.route(
                query={"topk": top_k, "has_filter": has_filter},
                faiss_load=0.0,  # Could track actual load
                qdrant_load=0.0
            )
            
            should_use_faiss = (decision["backend"] == "faiss")
            route_used = decision["backend"]
        
        # Execute search
        results = []
        
        if should_use_faiss and faiss_ready and faiss_enabled:
            # Use FAISS
            try:
                # Get encoder singleton
                encoder = get_encoder_model()
                query_vector = encoder.encode(query)
                
                # Search FAISS
                faiss_results = faiss_engine.search(query_vector, topk=top_k)
                
                # Format results (ensure doc_id is string)
                for doc_id, score in faiss_results:
                    results.append({
                        "id": str(doc_id),
                        "text": f"Document {doc_id}",  # Could load full text from Qdrant if needed
                        "score": float(score)
                    })
                
                route_used = "faiss"
                
            except Exception as e:
                logger.warning(f"[SEARCH] FAISS search failed, falling back to Qdrant: {e}")
                fallback = True
                should_use_faiss = False
        
        if not should_use_faiss or fallback:
            # Use Qdrant
            client = get_qdrant_client()
            encoder = get_encoder_model()
            if encoder is None:
                # Fallback to embedder if encoder is None
                from services.fiqa_api.clients import get_embedder
                embedder = get_embedder()
                if embedder is None:
                    raise RuntimeError("Encoder model not available")
                # Use embedder: encode([query]) returns numpy array of shape (1, dim)
                raw_vector = embedder.encode([query])[0]
            else:
                # Check if encoder is FastEmbedder (has encode method that takes list)
                # or SentenceTransformer (has encode method that takes string)
                try:
                    # Try encode([query]) first (for FastEmbedder)
                    raw_vector = encoder.encode([query])[0]
                except (TypeError, AttributeError):
                    # Fallback to encode(query) (for SentenceTransformer)
                    raw_vector = encoder.encode(query)
            
            # Normalize to 1D float32 list
            query_vector = ensure_1d_float32(raw_vector)
            
            # Verify dimension matches collection
            try:
                collection_info = client.get_collection(actual_collection)
                expected_dim = collection_info.config.params.vectors.size
                if len(query_vector) != int(expected_dim):
                    raise ValueError(f"embedding_dim_mismatch: got {len(query_vector)} expected {expected_dim}")
            except Exception as dim_error:
                if "embedding_dim_mismatch" in str(dim_error):
                    raise
                # Non-fatal: continue if dimension check fails
            
            # Search Qdrant
            qdrant_results = client.search(
                collection_name=actual_collection,
                query_vector=query_vector,  # Ensure it's 1D, NOT [query_vector]
                limit=top_k
            )
            
            # Format results (ensure doc_id is string)
            for r in qdrant_results:
                payload = r.payload or {}
                doc_id = str(payload.get("doc_id", r.id))
                results.append({
                    "id": doc_id,
                    "text": payload.get("text", "")[:200],
                    "title": payload.get("title", "Unknown"),
                    "score": float(r.score) if hasattr(r, 'score') else 0.0
                })
            
            route_used = "qdrant"
    
    # Record vector search completion time
    t_vec_search = time.perf_counter()
    
    # ========================================
    # Hybrid RRF Fusion (if enabled)
    # ========================================
    dense_results = results
    hybrid_fusion_info = None
    fusion_metrics = {}
    
    if use_hybrid:
        try:
            from services.fiqa_api.search import bm25_search, is_bm25_ready
            
            if is_bm25_ready():
                # Calculate candidate sizes for parallel search
                dense_k = max(top_k, DENSE_K_DEFAULT)
                bm25_k = max(top_k, BM25_K_DEFAULT)
                
                # Concurrent execution of dense and sparse search
                def _dense_search_hybrid():
                    """Helper to retrieve dense results (already computed, return as-is)."""
                    return dense_results
                
                def _bm25_search_hybrid():
                    """Helper to execute BM25 search."""
                    return bm25_search(query, top_k=bm25_k)
                
                # Execute dense and BM25 searches in parallel
                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_dense = executor.submit(_dense_search_hybrid)
                    future_bm25 = executor.submit(_bm25_search_hybrid)
                    dense_hits = future_dense.result()
                    sparse_hits = future_bm25.result()
                
                if sparse_hits:
                    # Apply smaller fusion window (limit k, then take top_k)
                    k = max(1, min(rrf_k or 60, 100))
                    fused, fusion_metrics = rrf_fuse(dense_hits, sparse_hits, k=k, top_k=top_k)
                    results = fused[:top_k]  # Ensure exactly top_k results
                    
                    hybrid_fusion_info = {
                        "enabled": True,
                        "method": "rrf",
                        "k": k
                    }
                    logger.info(f"[SEARCH] Hybrid RRF fusion (concurrent): {len(dense_hits)} dense + {len(sparse_hits)} sparse -> {len(results)} results, overlap={fusion_metrics.get('fusion_overlap', 0)}")
                else:
                    logger.warning("[SEARCH] BM25 returned no results, falling back to dense-only")
                    hybrid_fusion_info = {"enabled": False, "reason": "no_sparse_results"}
                    fusion_metrics = {"fusion_overlap": 0, "rrf_candidates": 0}
            else:
                logger.warning("[SEARCH] BM25 not ready, falling back to dense-only")
                hybrid_fusion_info = {"enabled": False, "reason": "bm25_not_ready"}
                fusion_metrics = {"fusion_overlap": 0, "rrf_candidates": 0}
        except Exception as e:
            logger.error(f"[SEARCH] Hybrid fusion failed: {e}, falling back to dense-only")
            results = dense_results
            hybrid_fusion_info = {"enabled": False, "reason": "error"}
            fusion_metrics = {"fusion_overlap": 0, "rrf_candidates": 0}
    else:
        hybrid_fusion_info = {"enabled": False}
        fusion_metrics = {"fusion_overlap": 0, "rrf_candidates": 0}
    
    # ========================================
    # Gated Reranking (if enabled)
    # ========================================
    reranker_info = None
    reranker_triggered = False
    rerank_timeout = False
    
    if rerank and len(results) >= 2:
        # Update trigger stats
        _trigger_stats.total += 1
        
        # Calculate margin
        margin = calculate_margin(results)
        
        # Check trigger conditions
        trigger_condition = (
            (rerank_if_margin_below is None or margin < rerank_if_margin_below)
            and _trigger_stats.get_rate() < max_rerank_trigger_rate
        )
        
        reranker_triggered = trigger_condition
        
        if reranker_triggered:
            _trigger_stats.triggered += 1
            logger.info(f"[RERANK] Triggered: margin={margin:.4f}, rate={_trigger_stats.get_rate():.2%}")
            
            # Attempt reranking with timeout protection
            rerank_start = time.time()
            try:
                # Import reranker function
                try:
                    from modules.rag.reranker_lite import rerank_passages
                    
                    # Extract texts for reranking
                    candidate_texts = [r.get("text", "") for r in results[:rerank_top_k]]
                    
                    # Call reranker with timeout (using threading in a sync context)
                    # Note: Since perform_search is sync, we'll use a simple timeout mechanism
                    import threading
                    
                    rerank_result = None
                    rerank_error = None
                    
                    def _rerank_worker():
                        nonlocal rerank_result, rerank_error
                        try:
                            rerank_result = rerank_passages(
                                query=query,
                                passages=candidate_texts,
                                top_k=min(top_k, len(candidate_texts)),
                                timeout_ms=rerank_budget_ms
                            )
                        except Exception as e:
                            rerank_error = e
                    
                    # Run reranker in a thread with timeout
                    thread = threading.Thread(target=_rerank_worker)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout=(rerank_budget_ms / 1000.0) + 0.1)  # Add small buffer
                    
                    if thread.is_alive():
                        # Thread still running - timeout occurred
                        rerank_timeout = True
                        logger.warning(f"[RERANK] Timeout after {rerank_budget_ms}ms budget, keeping original order")
                        reranker_info = {
                            "enabled": True,
                            "triggered": True,
                            "margin": round(margin, 4),
                            "trigger_rate": round(_trigger_stats.get_rate(), 4),
                            "budget_ms": rerank_budget_ms,
                            "elapsed_ms": (time.time() - rerank_start) * 1000,
                            "timeout": True
                        }
                    elif rerank_error:
                        # Reranker raised an exception
                        rerank_timeout = True
                        logger.warning(f"[RERANK] Error during reranking: {rerank_error}, keeping original order")
                        reranker_info = {
                            "enabled": True,
                            "triggered": True,
                            "margin": round(margin, 4),
                            "trigger_rate": round(_trigger_stats.get_rate(), 4),
                            "budget_ms": rerank_budget_ms,
                            "elapsed_ms": (time.time() - rerank_start) * 1000,
                            "timeout": True,
                            "error": str(rerank_error)
                        }
                    elif rerank_result:
                        # Reranking succeeded
                        reranked_texts, rerank_latency_ms, rerank_model = rerank_result
                        
                        # Map reranked texts back to original results by matching text content
                        # Create a mapping from text to original result
                        text_to_result = {}
                        for r in results[:rerank_top_k]:
                            text_key = r.get("text", "")[:200]  # Use first 200 chars as key
                            if text_key not in text_to_result:
                                text_to_result[text_key] = r
                        
                        # Reorder results based on reranked text order
                        reranked_results = []
                        reranked_texts_set = set()
                        for reranked_text in reranked_texts:
                            text_key = reranked_text[:200] if isinstance(reranked_text, str) else str(reranked_text)[:200]
                            if text_key in text_to_result:
                                reranked_results.append(text_to_result[text_key])
                                reranked_texts_set.add(text_key)
                        
                        # Add any remaining results that weren't reranked (shouldn't happen, but safety)
                        for r in results[:rerank_top_k]:
                            text_key = r.get("text", "")[:200]
                            if text_key not in reranked_texts_set:
                                reranked_results.append(r)
                        
                        # Replace original results with reranked order, keeping tail intact
                        results = reranked_results + results[rerank_top_k:]
                        
                        reranker_info = {
                            "enabled": True,
                            "triggered": True,
                            "margin": round(margin, 4),
                            "trigger_rate": round(_trigger_stats.get_rate(), 4),
                            "budget_ms": rerank_budget_ms,
                            "elapsed_ms": rerank_latency_ms,
                            "timeout": False
                        }
                        logger.info(f"[RERANK] Completed in {rerank_latency_ms:.1f}ms, reordered {len(reranked_results)} results")
                    else:
                        # Unexpected case
                        rerank_timeout = True
                        reranker_info = {
                            "enabled": True,
                            "triggered": True,
                            "margin": round(margin, 4),
                            "trigger_rate": round(_trigger_stats.get_rate(), 4),
                            "budget_ms": rerank_budget_ms,
                            "elapsed_ms": (time.time() - rerank_start) * 1000,
                            "timeout": True
                        }
                        
                except ImportError:
                    # Reranker module not available - mock behavior
                    rerank_timeout = False
                    reranker_info = {
                        "enabled": True,
                        "triggered": True,
                        "margin": round(margin, 4),
                        "trigger_rate": round(_trigger_stats.get_rate(), 4),
                        "budget_ms": rerank_budget_ms,
                        "elapsed_ms": 0.0,
                        "timeout": False
                    }
                    logger.info("[RERANK] Reranker module not available, using mock")
                    
            except Exception as e:
                # Catch-all for any reranking errors
                rerank_timeout = True
                logger.warning(f"[RERANK] Unexpected error: {e}, keeping original order")
                reranker_info = {
                    "enabled": True,
                    "triggered": True,
                    "margin": round(margin, 4),
                    "trigger_rate": round(_trigger_stats.get_rate(), 4),
                    "budget_ms": rerank_budget_ms,
                    "elapsed_ms": (time.time() - rerank_start) * 1000,
                    "timeout": True,
                    "error": str(e)
                }
        else:
            reranker_info = {
                "enabled": True,
                "triggered": False,
                "margin": round(margin, 4),
                "trigger_rate": round(_trigger_stats.get_rate(), 4),
                "budget_ms": rerank_budget_ms,
                "elapsed_ms": 0.0,
                "timeout": False
            }
            logger.debug(f"[RERANK] Not triggered: margin={margin:.4f}, rate={_trigger_stats.get_rate():.2%}")
    else:
        reranker_info = {"enabled": False, "triggered": False, "timeout": False}
    
    # Record rerank completion time
    if reranker_info.get("enabled") and reranker_info.get("triggered"):
        t_rerank = time.perf_counter()
    else:
        t_rerank = t_vec_search  # No rerank, reuse vec_search time
    
    # Record serialize start (just before building response)
    t_serialize_start = time.perf_counter()
    
    latency_ms = (time.perf_counter() - start_time) * 1000
    latency_search_ms = (t_vec_search - start_time) * 1000 if t_vec_search else latency_ms
    latency_rerank_ms = (t_rerank - t_vec_search) * 1000 if (t_rerank and t_vec_search) else 0.0
    latency_serialize_ms = (time.perf_counter() - t_serialize_start) * 1000
    
    # ✅ Lab experiment metrics collection (if enabled)
    if lab_headers and lab_headers.get("x_lab_exp"):
        _record_lab_metrics(
            lab_headers=lab_headers,
            start_time=start_time,
            latency_ms=latency_ms,
            route_used=route_used,
            fallback=fallback,
            top_k=top_k
        )
    
    # Build response with enhanced metrics
    response = {
        "ok": True,
        "results": results,
        "latency_ms": latency_ms,
        "latency_search_ms": latency_search_ms,
        "latency_rerank_ms": latency_rerank_ms,
        "latency_serialize_ms": latency_serialize_ms,
        "route": route_used,
        "fallback": fallback,
        "doc_ids": [r["id"] for r in results]
    }
    
    # Add enhanced metrics if hybrid or rerank was configured
    if hybrid_fusion_info or reranker_info:
        response["metrics_details"] = {}
        if hybrid_fusion_info:
            response["metrics_details"]["fusion"] = hybrid_fusion_info
        if reranker_info:
            response["metrics_details"]["rerank"] = reranker_info
    
    # Add per-request observability metrics (for /api/query endpoint)
    response["observability_metrics"] = {
        "fusion_overlap": fusion_metrics.get("fusion_overlap", 0),
        "rrf_candidates": fusion_metrics.get("rrf_candidates", len(results) if not use_hybrid else 0),
        "rerank_triggered": reranker_triggered,
        "rerank_timeout": rerank_timeout
    }
    
    return response


def _record_lab_metrics(
    lab_headers: Dict[str, str],
    start_time: float,
    latency_ms: float,
    route_used: str,
    fallback: bool,
    top_k: int
):
    """
    Record lab experiment metrics to Redis (non-critical).
    
    Args:
        lab_headers: Dict with x_lab_exp, x_lab_phase, x_topk keys
        start_time: Request start timestamp
        latency_ms: Request latency in milliseconds
        route_used: Backend route used
        fallback: Whether fallback occurred
        top_k: Top-K value
    """
    try:
        from services.fiqa_api.clients import get_redis_client, ensure_redis_connection
        
        # Ensure Redis connection is healthy
        if not ensure_redis_connection():
            logger.debug("[LAB] Redis connection unhealthy, skipping metrics recording")
            return
        
        redis_client = get_redis_client()
        x_lab_exp = lab_headers.get("x_lab_exp")
        x_lab_phase = lab_headers.get("x_lab_phase")
        x_topk = lab_headers.get("x_topk")
        
        # Record to Redis: lab:exp:<id>:raw
        metric_data = {
            "ts": start_time,
            "latency_ms": latency_ms,
            "ok": True,
            "route": route_used,
            "phase": x_lab_phase or "unknown",
            "topk": int(x_topk) if x_topk else top_k,
            "fallback": fallback
        }
        
        # ✅ Extended TTL for long-running tests (default 24h)
        lab_ttl = int(os.getenv("LAB_REDIS_TTL", "86400"))  # 24 hours
        raw_key = f"lab:exp:{x_lab_exp}:raw"
        
        redis_client.rpush(raw_key, json.dumps(metric_data))
        redis_client.expire(raw_key, lab_ttl)  # Refresh TTL on each write
        
        # Every 5 seconds, trigger aggregation
        bucket_ts = int(start_time / 5) * 5
        redis_client.sadd(f"lab:exp:{x_lab_exp}:buckets", bucket_ts)
        
    except Exception as e:
        # Non-critical: Log but don't fail the request
        logger.debug(f"[SEARCH] Failed to record lab metric: {e}")

