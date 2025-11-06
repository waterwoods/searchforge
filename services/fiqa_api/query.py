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
import os
from datetime import datetime
from typing import Optional

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
EXPECTED_QDRANT_DIM = 384  # Dimension for BAAI/bge-small-en-v1.5


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
    rerank: bool = Field(default=False, description="Whether to rerank results")
    use_hybrid: bool = Field(default=False, description="Whether to use hybrid retrieval (BM25 + vector fusion)")
    rrf_k: Optional[int] = Field(default=None, ge=1, le=100, description="RRF reciprocal rank fusion k parameter")
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=100, description="Number of candidates to rerank")
    rerank_if_margin_below: Optional[float] = Field(default=0.12, ge=0.0, le=1.0, description="Margin threshold for gated reranking")
    max_rerank_trigger_rate: float = Field(default=0.25, ge=0.0, le=1.0, description="Max rerank trigger rate")
    rerank_budget_ms: int = Field(default=25, ge=1, le=1000, description="Rerank budget in milliseconds")


# ========================================
# Route Handler
# ========================================

@router.post("/query")
async def query(request: QueryRequest, response: Response):
    """
    Query endpoint with frontend-friendly format.
    
    Maps frontend `question` → core `query`, calls search_core.perform_search,
    and adapts response to frontend format with trace_id, sources, etc.
    
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
        from services.fiqa_api.clients import EMBED_READY, EmbeddingUnreadyError
        if not EMBED_READY:
            logger.warning(f"level=WARN trace_id={trace_id} status=EMBEDDING_WARMING msg='Embedding model not ready'")
            response.headers["Retry-After"] = "10"
            raise HTTPException(
                status_code=503,
                detail={"ok": False, "error": "embedding_warming"}
            )
        
        # Clean and validate input
        cleaned_question = request.question.strip() if request.question else ""
        if not cleaned_question:
            logger.warning(f"level=WARN trace_id={trace_id} status=INVALID_INPUT msg='Empty question provided'")
            raise HTTPException(
                status_code=400,
                detail="question cannot be empty"
            )
        
        # Check Qdrant collection dimension
        try:
            from services.fiqa_api.clients import get_qdrant_client
            from services.fiqa_api.services.search_core import COLLECTION_MAP
            qdrant_client = get_qdrant_client()
            # Map collection name (same as search_core does)
            actual_collection = COLLECTION_MAP.get("fiqa", "beir_fiqa_full_ta")
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
                    collection="fiqa",
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
                    rerank_budget_ms=request.rerank_budget_ms
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
        
        # Log success with structured fields
        elapsed = (time.perf_counter() - start) * 1000
        route_used = search_result.get('route', 'unknown')
        logger.info(f"level=INFO trace_id={trace_id} status=SUCCESS route={route_used} latency_ms={elapsed:.1f} top_k={request.top_k}")
        
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

