"""
query.py - Query Route Handler (Frontend API)
==============================================
Handles /api/query endpoint with frontend-friendly request/response format.
Core logic delegated to services/search_core.py.
"""

import logging
import uuid
import time
import asyncio
import json
import os
from datetime import datetime
from typing import Optional

# Collection name mapping (dataset_name -> collection_name)
COLLECTION_MAP = {
    "fiqa_10k_v1": "fiqa_10k_v1",
    "fiqa_50k_v1": "fiqa_50k_v1",
    "fiqa_para_50k": "fiqa_para_50k",
    "fiqa_sent_50k": "fiqa_sent_50k",
    "fiqa_win256_o64_50k": "fiqa_win256_o64_50k",
}


from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.fiqa_api.services.search_core import perform_search

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter()


# ========================================
# Constants
# ========================================

DEFAULT_TOP_K = 20
MAX_TOP_K = 100
QUERY_TIMEOUT_SEC = float(os.getenv("QUERY_TIMEOUT_S", "45.0"))
RRF_K_DEFAULT = int(os.getenv("RRF_K_DEFAULT", "60"))
RERANK_TOPK_DEFAULT = int(os.getenv("RERANK_TOPK_DEFAULT", "20"))
EXPECTED_QDRANT_DIM = 384  # Dimension for all-MiniLM-L6-v2 and bge-small-en-v1.5


# ========================================
# Helper Functions
# ========================================

def get_default_metrics() -> dict:
    """Return default metrics structure with all required keys."""
    return {
        "qps": 0,
        "p95_ms": 0,
        "recall_at_10": 0,
        "total": 0
    }


# ========================================
# Request/Response Models
# ========================================

class QueryRequest(BaseModel):
    """Query request model (frontend format)."""
    question: str
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K, description=f"Number of results (default: {DEFAULT_TOP_K}, max: {MAX_TOP_K})")
    collection: Optional[str] = Field(default="fiqa", description="Collection name (e.g., 'fiqa', 'fiqa_50k_v1', 'fiqa_10k_v1')")
    rerank: bool = Field(default=False, description="Whether to rerank results")
    use_hybrid: bool = Field(default=False, description="Whether to use hybrid retrieval (BM25 + vector fusion)")
    rrf_k: Optional[int] = Field(default=None, ge=1, le=100, description="RRF reciprocal rank fusion k parameter")
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=100, description="Number of candidates to rerank")
    rerank_if_margin_below: Optional[float] = Field(default=0.12, ge=0.0, le=1.0, description="Margin threshold for gated reranking")
    max_rerank_trigger_rate: float = Field(default=0.25, ge=0.0, le=1.0, description="Max rerank trigger rate")
    rerank_budget_ms: int = Field(default=25, ge=1, le=1000, description="Rerank budget in milliseconds")
    ef_search: Optional[int] = Field(default=None, ge=16, le=512, description="Qdrant HNSW ef parameter for search")
    mmr: bool = Field(default=False, description="Whether to use MMR (Maximum Marginal Relevance) diversification")
    mmr_lambda: float = Field(default=0.3, ge=0.0, le=1.0, description="MMR lambda parameter (0=max diversity, 1=max relevance)")


# ========================================
# Route Handler
# ========================================

@router.post("/query")
async def query(request: QueryRequest, response: Response):
    """
    Query endpoint with frontend-friendly format.
    
    Maps frontend `question` → core `query`, calls search_core.perform_search,
    and adapts response to frontend format with trace_id, sources, etc.
    
    Includes model consistency checks and embedding model header.
    
    Request body:
        question: str - User's question
        top_k: int - Number of results (default: 20, max: 100)
        rerank: bool - Whether to rerank results (default: False)
    
    Returns:
        {
            "ok": true,
            "trace_id": "uuid",
            "question": "string",
            "answer": "string",  # Empty for now
            "latency_ms": float,
            "route": "string",
            "params": {"top_k": int, "rerank": bool},
            "sources": [...],  # Mapped from search results
            "metrics": {...},  # Structured metrics object
            "reranker_triggered": false,
            "ts": "ISO8601 timestamp"
        }
    
    Response headers:
        X-Trace-Id: Request trace ID for correlation
    """
    # Performance tracking
    start = time.perf_counter()
    
    # Generate trace_id
    trace_id = str(uuid.uuid4())
    
    # Set trace_id in response headers for correlation
    response.headers["X-Trace-Id"] = trace_id
    
    try:
        # Check embedding readiness (cold-start warmup)
        from services.fiqa_api.clients import EMBED_READY, EmbeddingUnreadyError, get_embedder
        if not EMBED_READY:
            logger.warning(f"level=WARN trace_id={trace_id} status=EMBEDDING_WARMING msg='Embedding model not ready'")
            response.headers["Retry-After"] = "10"
            raise HTTPException(
                status_code=503,
                detail={"ok": False, "error": "embedding_warming"}
            )
        
        # Get embedding metadata for headers
        embedder = None
        embed_model = "unknown"
        embed_backend = os.getenv("EMBEDDING_BACKEND", "UNKNOWN")
        embed_dim = None
        try:
            embedder = get_embedder()
            embed_model = getattr(embedder, "model_name", os.getenv("SBERT_MODEL", "unknown"))
            embed_dim = getattr(embedder, "dim", None)
        except Exception as e:
            logger.warning(f"level=WARN trace_id={trace_id} status=EMBED_INFO_FAILED msg='Could not get embedder info: {e}'")
        
        # Model consistency check
        expected_model = os.getenv("EXPECTED_EMBED_MODEL")
        if expected_model:
            try:
                if embed_model and embed_model != expected_model:
                    logger.error(f"level=ERROR trace_id={trace_id} status=MODEL_MISMATCH expected={expected_model} got={embed_model}")
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "ok": False,
                            "error": "embed_model_mismatch",
                            "expected": expected_model,
                            "got": embed_model
                        }
                    )
                # Set model header
                response.headers["X-Embed-Model"] = embed_model or "unknown"
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"level=WARN trace_id={trace_id} status=MODEL_CHECK_FAILED msg='Could not verify model: {e}'")
                # Non-fatal: continue with query
        else:
            # Set header anyway
            response.headers["X-Embed-Model"] = embed_model
        
        # Clean and validate input
        cleaned_question = request.question.strip() if request.question else ""
        if not cleaned_question:
            logger.warning(f"level=WARN trace_id={trace_id} status=INVALID_INPUT msg='Empty question provided'")
            raise HTTPException(
                status_code=400,
                detail="question cannot be empty"
            )
        
        # Get collection name and map to actual collection
        collection_name = request.collection if request.collection else "fiqa"
        actual_collection = COLLECTION_MAP.get(collection_name, collection_name)
        
        # Check Qdrant collection dimension
        try:
            from services.fiqa_api.clients import get_qdrant_client
            qdrant_client = get_qdrant_client()
            collection_info = qdrant_client.get_collection(actual_collection)
            # Get dimension from collection config
            if hasattr(collection_info.config.params.vectors, 'size'):
                qdrant_dim = collection_info.config.params.vectors.size
            elif hasattr(collection_info.config.params, 'vectors') and isinstance(collection_info.config.params.vectors, dict):
                qdrant_dim = collection_info.config.params.vectors.get('size')
            else:
                # Fallback: try to get from config
                qdrant_dim = getattr(collection_info.config.params.vectors, 'size', None)
            
            if qdrant_dim is not None and qdrant_dim != EXPECTED_QDRANT_DIM:
                logger.error(f"level=ERROR trace_id={trace_id} status=DIM_MISMATCH qdrant_dim={qdrant_dim} expected={EXPECTED_QDRANT_DIM}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "ok": False,
                        "error": "dim_mismatch",
                        "qdrant_dim": qdrant_dim,
                        "expected": EXPECTED_QDRANT_DIM
                    }
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"level=WARN trace_id={trace_id} status=DIM_CHECK_FAILED msg='Could not verify Qdrant dimension: {e}'")
            # Non-fatal: continue with query
        
        # Get app state from global app instance
        try:
            from services.fiqa_api.app_main import app
            routing_flags = app.state.routing_flags
            faiss_engine = app.state.faiss_engine
            faiss_ready = app.state.faiss_ready
            faiss_enabled = app.state.faiss_enabled
        except Exception as e:
            logger.error(f"level=ERROR trace_id={trace_id} status=APP_STATE_ERROR error='{str(e)}'")
            # Fallback defaults
            routing_flags = {"enabled": True, "mode": "rules"}
            faiss_engine = None
            faiss_ready = False
            faiss_enabled = False
        
        # Apply parameter bounds protection with defaults
        rrf_k = max(1, min(request.rrf_k if request.rrf_k is not None else RRF_K_DEFAULT, 100))
        rerank_top_k = max(1, min(request.rerank_top_k if request.rerank_top_k is not None else RERANK_TOPK_DEFAULT, request.top_k))
        
        # Call core search logic with timeout
        try:
            search_result = await asyncio.wait_for(
                asyncio.to_thread(
                    perform_search,
                    query=cleaned_question,
                    top_k=request.top_k,
                    collection=collection_name,
                    routing_flags=routing_flags,
                    faiss_engine=faiss_engine,
                    faiss_ready=faiss_ready,
                    faiss_enabled=faiss_enabled,
                    lab_headers=None,
                    use_hybrid=request.use_hybrid,
                    rrf_k=rrf_k,
                    rerank=request.rerank,
                    rerank_top_k=rerank_top_k,
                    rerank_if_margin_below=request.rerank_if_margin_below,
                    max_rerank_trigger_rate=request.max_rerank_trigger_rate,
                    rerank_budget_ms=request.rerank_budget_ms,
                    ef_search=request.ef_search,
                    mmr=request.mmr,
                    mmr_lambda=request.mmr_lambda
                ),
                timeout=QUERY_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"level=ERROR trace_id={trace_id} status=TIMEOUT route='unknown' latency_ms={elapsed:.1f} timeout_sec={QUERY_TIMEOUT_SEC}")
            raise HTTPException(
                status_code=504,
                detail=f"Query timeout after {QUERY_TIMEOUT_SEC}s"
            )
        except ValueError as ve:
            # Handle dimension mismatch or other ValueError from search_core
            elapsed = (time.perf_counter() - start) * 1000
            error_msg = str(ve)
            if "embedding_dim_mismatch" in error_msg:
                logger.error(f"level=ERROR trace_id={trace_id} status=DIM_MISMATCH latency_ms={elapsed:.1f} error='{error_msg}'")
                raise HTTPException(
                    status_code=400,
                    detail={"ok": False, "error": "embedding_dim_mismatch", "detail": error_msg}
                )
            else:
                logger.error(f"level=ERROR trace_id={trace_id} status=VALIDATION_ERROR latency_ms={elapsed:.1f} error='{error_msg}'")
                raise HTTPException(
                    status_code=400,
                    detail={"ok": False, "error": "validation_error", "detail": error_msg}
                )
        
        # Map search results to frontend sources format
        sources = []
        for result in search_result.get("results", []):
            sources.append({
                "doc_id": result.get("id", "unknown"),
                "title": result.get("title", ""),
                "url": "",  # Empty for now
                "score": result.get("score", 0.0)
            })
        
        # Extract timing information
        elapsed = (time.perf_counter() - start) * 1000
        route_used = search_result.get('route', 'unknown')
        latency_search_ms = search_result.get('latency_search_ms', elapsed)
        latency_rerank_ms = search_result.get('latency_rerank_ms', 0.0)
        latency_serialize_ms = search_result.get('latency_serialize_ms', 0.0)
        
        # Set response headers with metadata
        response.headers["X-Embed-Model"] = embed_model
        response.headers["X-Backend"] = embed_backend
        response.headers["X-Top-K"] = str(request.top_k)
        response.headers["X-Mode"] = "fast" if hasattr(request, 'fast_mode') and getattr(request, 'fast_mode', False) else "normal"
        response.headers["X-Hybrid"] = "true" if request.use_hybrid else "false"
        response.headers["X-Rerank"] = "true" if request.rerank else "false"
        response.headers["X-MMR"] = "true" if request.mmr else "false"
        response.headers["X-MMR-Lambda"] = f"{request.mmr_lambda:.2f}"
        response.headers["X-Dataset"] = request.collection or "fiqa"
        response.headers["X-Qrels"] = "unknown"  # Will be set from experiment params if available
        response.headers["X-Collection"] = actual_collection
        response.headers["X-Search-MS"] = f"{float(latency_search_ms):.1f}"
        response.headers["X-Rerank-MS"] = f"{float(latency_rerank_ms):.1f}"
        response.headers["X-Total-MS"] = f"{float(elapsed):.1f}"
        if embed_dim:
            response.headers["X-Dim"] = str(embed_dim)
        
        # Log success with structured JSON
        log_metadata = {
            "trace_id": trace_id,
            "status": "SUCCESS",
            "route": route_used,
            "latency_total_ms": round(elapsed, 1),
            "latency_search_ms": round(latency_search_ms, 1),
            "latency_rerank_ms": round(latency_rerank_ms, 1),
            "latency_serialize_ms": round(latency_serialize_ms, 1),
            "top_k": request.top_k,
            "hybrid": request.use_hybrid,
            "rerank": request.rerank,
            "collection": actual_collection,
            "embed_model": embed_model,
            "backend": embed_backend,
            "dim": embed_dim
        }
        logger.info(f"level=INFO {json.dumps(log_metadata)}")
        
        # Extract metrics from search result
        metrics_details = search_result.get("metrics_details", {})
        observability_metrics = search_result.get("observability_metrics", {})
        reranker_triggered = metrics_details.get("rerank", {}).get("triggered", False) or observability_metrics.get("rerank_triggered", False)
        
        # Build base metrics
        base_metrics = get_default_metrics()
        
        # Add fusion and rerank info if available
        if metrics_details.get("fusion"):
            base_metrics["fusion"] = metrics_details["fusion"]
        if metrics_details.get("rerank"):
            base_metrics["rerank"] = metrics_details["rerank"]
        
        # Add per-request observability metrics
        base_metrics["fusion_overlap"] = observability_metrics.get("fusion_overlap", 0)
        base_metrics["rrf_candidates"] = observability_metrics.get("rrf_candidates", 0)
        base_metrics["rerank_triggered"] = observability_metrics.get("rerank_triggered", False)
        base_metrics["rerank_timeout"] = observability_metrics.get("rerank_timeout", False)
        
        # Return frontend-friendly response with all required fields
        return {
            "ok": True,
            "trace_id": trace_id,
            "question": cleaned_question,
            "answer": "",  # Empty for now
            "latency_ms": elapsed,
            "route": route_used,
            "params": {
                "top_k": request.top_k,
                "rerank": request.rerank,
                "use_hybrid": request.use_hybrid,
                "rrf_k": request.rrf_k if request.use_hybrid else None
            },
            "sources": sources,
            "metrics": base_metrics,
            "reranker_triggered": reranker_triggered,
            "ts": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions (4xx/5xx) - FastAPI will handle status code
        elapsed = (time.perf_counter() - start) * 1000
        logger.warning(f"level=WARN trace_id={trace_id} status=HTTP_{http_ex.status_code} latency_ms={elapsed:.1f} error='{http_ex.detail}'")
        raise
    except Exception as e:
        # Log error with structured fields
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(f"level=ERROR trace_id={trace_id} status=ERROR route='error' latency_ms={elapsed:.1f} error_type={type(e).__name__} error='{str(e)}'")
        
        # Return error response with all required fields and proper status code
        return JSONResponse(
            status_code=500,
            headers={"X-Trace-Id": trace_id},  # Also set in headers
            content={
                "ok": False,
                "trace_id": trace_id,
                "question": cleaned_question if 'cleaned_question' in locals() else "",
                "answer": "",
                "error": str(e),
                "latency_ms": elapsed,
                "route": "error",
                "params": {
                    "top_k": request.top_k if request else 0,
                    "rerank": request.rerank if request else False
                },
                "sources": [],
                "metrics": get_default_metrics(),  # Structured metrics even in error
                "reranker_triggered": False,
                "ts": datetime.utcnow().isoformat() + "Z"
            }
        )

