"""
search_service.py - Search Service Logic
========================================
Pure business logic for search operations.
No client creation - uses clients.py singletons.
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# ========================================
# Constants (configurable via env)
# ========================================

# Collection mapping
COLLECTION_MAP = {
    "fiqa": "beir_fiqa_full_ta",
    "beir_fiqa_full_ta": "beir_fiqa_full_ta"
}


# ========================================
# Core Search Logic
# ========================================

def do_search(
    query: str,
    top_k: int,
    collection: str,
    routing_flags: dict,
    faiss_engine: Optional[Any],
    faiss_ready: bool,
    faiss_enabled: bool,
    lab_headers: Optional[Dict[str, str]] = None
) -> Tuple[Dict[str, Any], str, bool]:
    """
    Execute search with unified routing (FAISS/Qdrant/Milvus).
    
    Args:
        query: Search query string
        top_k: Number of results to return
        collection: Collection name
        routing_flags: Dict with 'enabled', 'mode', 'manual_backend' keys
        faiss_engine: FAISS engine instance (or None)
        faiss_ready: Whether FAISS is ready
        faiss_enabled: Whether FAISS is enabled
        lab_headers: Optional lab experiment headers (X-Lab-Exp, X-Lab-Phase, X-TopK)
        
    Returns:
        Tuple of (results_dict, route_used, fallback_occurred)
        
    Raises:
        Exception: On critical errors (will be caught by route handler)
    """
    from services.fiqa_api.clients import (
        get_encoder_model, 
        get_qdrant_client, 
        get_redis_client,
        ensure_qdrant_connection
    )
    
    # Ensure Qdrant connection is healthy before proceeding
    if not ensure_qdrant_connection():
        logger.warning("[SEARCH] Qdrant connection unhealthy, search may fail")
    
    start_time = time.time()
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
                
                # Format results
                for doc_id, score in faiss_results:
                    results.append({
                        "id": doc_id,
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
            query_vector = encoder.encode(query).tolist()
            
            # Search Qdrant
            qdrant_results = client.search(
                collection_name=actual_collection,
                query_vector=query_vector,
                limit=top_k
            )
            
            # Format results
            for r in qdrant_results:
                payload = r.payload or {}
                doc_id = payload.get("doc_id", str(r.id))
                results.append({
                    "id": doc_id,
                    "text": payload.get("text", "")[:200],
                    "title": payload.get("title", "Unknown"),
                    "score": float(r.score) if hasattr(r, 'score') else 0.0
                })
            
            route_used = "qdrant"
    
    latency_ms = (time.time() - start_time) * 1000
    
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
    
    return {
        "ok": True,
        "results": results,
        "latency_ms": latency_ms,
        "route": route_used,
        "fallback": fallback,
        "doc_ids": [r["id"] for r in results]
    }, route_used, fallback


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

