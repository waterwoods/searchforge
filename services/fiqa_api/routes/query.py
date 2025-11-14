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
from typing import Any, Dict, Optional

# Collection name mapping (dataset_name -> collection_name)
COLLECTION_MAP = {
    "fiqa": "fiqa_50k_v1",
    "fiqa_10k_v1": "fiqa_10k_v1",
    "fiqa_50k_v1": "fiqa_50k_v1",
    "fiqa_para_50k": "fiqa_para_50k",
    "fiqa_sent_50k": "fiqa_sent_50k",
    "fiqa_win256_o64_50k": "fiqa_win256_o64_50k",
}


from fastapi import APIRouter, Header, HTTPException, Request, Response, Query as FastAPIQuery
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, root_validator

try:
    from clients.retrieval_proxy_client import (
        DEFAULT_BUDGET_MS as PROXY_DEFAULT_BUDGET_MS,
        USE_PROXY as USE_RETRIEVAL_PROXY,
        search as proxy_search,
    )
except ModuleNotFoundError:  # pragma: no cover - container fallback
    PROXY_DEFAULT_BUDGET_MS = 400
    USE_RETRIEVAL_PROXY = False

    def proxy_search(*args, **kwargs):
        raise RuntimeError("retrieval proxy client unavailable")

from services.fiqa_api import obs
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


def _item_to_source(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = item.get("payload") if isinstance(item, dict) else {}
    if not isinstance(payload, dict):
        payload = {}
    doc_id = payload.get("doc_id") or item.get("id") or payload.get("id") or "unknown"
    title = payload.get("title") or item.get("title", "")
    url = payload.get("url") or ""
    score = item.get("score", 0.0)
    return {
        "doc_id": doc_id,
        "title": title,
        "url": url,
        "score": score,
    }


# ========================================
# Request/Response Models
# ========================================

class QueryRequest(BaseModel):
    """Query request model (frontend format)."""
    question: str = Field(..., alias="question")
    budget_ms: Optional[int] = Field(default=None, alias="budget_ms")
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K, description=f"Number of results (default: {DEFAULT_TOP_K}, max: {MAX_TOP_K})")
    collection: Optional[str] = Field(default="fiqa", description="Collection name (e.g., 'fiqa', 'fiqa_50k_v1', 'fiqa_10k_v1')")
    rerank: bool = Field(default=False, description="Whether to rerank results")
    use_hybrid: bool = Field(default=False, description="Whether to use hybrid retrieval (BM25 + vector fusion)")
    rrf_k: Optional[int] = Field(default=None, ge=1, le=100, description="RRF reciprocal rank fusion k parameter")
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=100, description="Number of candidates to rerank")
    rerank_if_margin_below: Optional[float] = Field(default=0.12, ge=0.0, le=1.0, description="Margin threshold for gated reranking")
    max_rerank_trigger_rate: float = Field(default=0.25, ge=0.0, le=1.0, description="Max rerank trigger rate")
    rerank_budget_ms: int = Field(default=25, ge=1, le=1000, description="Rerank budget in milliseconds")

    @root_validator(pre=True)
    def _alias_q(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "question" not in values:
            alias_val = values.pop("q", None)
            if alias_val:
                values["question"] = alias_val
        if "budget_ms" not in values and "budget" in values:
            values["budget_ms"] = values.get("budget")
        return values

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


# ========================================
# Route Handler
# ========================================

async def _execute_query(
    request_model: QueryRequest,
    response: Response,
    raw_request: Request,
    x_trace_id: Optional[str] = None,
):
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
    request = request_model
    # Performance tracking
    start = time.perf_counter()
    
    # Generate or reuse trace_id
    trace_id_candidate = (x_trace_id or "").strip()
    trace_id = trace_id_candidate or str(uuid.uuid4())
    
    # Set trace_id in response headers for correlation
    response.headers["X-Trace-Id"] = trace_id
    raw_request.state.trace_id = trace_id
    obs_ctx = {"trace_id": trace_id, "job_id": trace_id}
    raw_request.state.obs_ctx = obs_ctx
    
    cleaned_question = request.question.strip() if request.question else ""
    if not cleaned_question:
        logger.warning(f"level=WARN trace_id={trace_id} status=INVALID_INPUT msg='Empty question provided'")
        raise HTTPException(
            status_code=400,
            detail="question cannot be empty"
        )
    
    collection_name = request.collection if request.collection else "fiqa"
    actual_collection = COLLECTION_MAP.get(collection_name, collection_name)
    
    if USE_RETRIEVAL_PROXY:
        try:
            proxy_budget = request.budget_ms if request.budget_ms is not None else PROXY_DEFAULT_BUDGET_MS
            items, timings, degraded, trace_url = proxy_search(
                query=cleaned_question,
                k=request.top_k,
                budget_ms=proxy_budget,
                trace_id=trace_id,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "level=WARN trace_id=%s status=PROXY_FALLBACK error='%s'",
                trace_id,
                exc,
            )
        else:
            latency_ms = timings.get("total_ms")
            if latency_ms is None:
                latency_ms = (time.perf_counter() - start) * 1000
            latency_ms = float(latency_ms)
            ret_code = timings.get("ret_code") or "OK"
            route_used = timings.get("route") or "retrieval_proxy"
            cache_hit = bool(timings.get("cache_hit"))
            per_source = timings.get("per_source_ms") or {}
            response.headers["X-Backend"] = route_used
            response.headers["X-Top-K"] = str(request.top_k)
            response.headers["X-Mode"] = "fast" if getattr(request, "fast_mode", False) else "normal"
            response.headers["X-Hybrid"] = "true" if request.use_hybrid else "false"
            response.headers["X-Rerank"] = "true" if request.rerank else "false"
            response.headers["X-Dataset"] = collection_name
            response.headers["X-Qrels"] = "unknown"
            response.headers["X-Collection"] = actual_collection
            response.headers["X-Search-MS"] = f"{latency_ms:.1f}"
            response.headers["X-Rerank-MS"] = "0.0"
            response.headers["X-Total-MS"] = f"{latency_ms:.1f}"
            response.headers["X-Embed-Model"] = "retrieval-proxy"
            response.headers["X-Proxy-RetCode"] = ret_code
            if per_source:
                response.headers["X-Proxy-Sources"] = json.dumps(per_source)
            if trace_url:
                response.headers["X-Langfuse-Trace-Url"] = trace_url
            sources = [_item_to_source(item) for item in items]
            base_metrics = get_default_metrics()
            base_metrics["total"] = len(sources)
            base_metrics["proxy_ret_code"] = ret_code
            base_metrics["proxy_cache_hit"] = cache_hit
            base_metrics["proxy_degraded"] = degraded
            observability_metrics = {
                "fusion_overlap": 0,
                "rrf_candidates": 0,
                "rerank_triggered": False,
                "rerank_timeout": False,
                "proxy_cache_hit": cache_hit,
                "proxy_degraded": degraded,
            }
            log_payload = {
                "trace_id": trace_id,
                "status": "SUCCESS",
                "route": route_used,
                "latency_total_ms": round(latency_ms, 1),
                "top_k": request.top_k,
                "hybrid": request.use_hybrid,
                "rerank": request.rerank,
                "ret_code": ret_code,
                "cache_hit": cache_hit,
                "degraded": degraded,
            }
            logger.info("level=INFO %s", json.dumps(log_payload))
            try:
                obs.finalize_root(
                    job_id=trace_id,
                    trace_id=trace_id,
                    trace_url=trace_url or "",
                    metrics=base_metrics,
                    decision=route_used,
                )
                if trace_url:
                    raw_request.state.trace_url = trace_url
            except Exception:
                pass
            return {
                "ok": True,
                "trace_id": trace_id,
                "question": cleaned_question,
                "answer": "",
                "latency_ms": latency_ms,
                "route": route_used,
                "params": {
                    "top_k": request.top_k,
                    "rerank": request.rerank,
                    "use_hybrid": request.use_hybrid,
                    "rrf_k": request.rrf_k if request.use_hybrid else None,
                },
                "sources": sources,
                "items": sources,
                "metrics": base_metrics,
                "observability_metrics": observability_metrics,
                "reranker_triggered": False,
                "degraded": bool(degraded),
                "budget_ms": request.budget_ms,
                "ts": datetime.utcnow().isoformat() + "Z",
            }
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
                    obs_ctx=obs_ctx,
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
        payload = {
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
                "rrf_k": request.rrf_k if request.use_hybrid else None,
            },
            "sources": sources,
            "items": sources,
            "metrics": base_metrics,
            "reranker_triggered": reranker_triggered,
            "degraded": bool(search_result.get("fallback", False)),
            "budget_ms": request.budget_ms,
            "ts": datetime.utcnow().isoformat() + "Z",
        }
        try:
            trace_url = search_result.get("trace_url") or obs.build_obs_url(trace_id)
            raw_request.state.trace_url = trace_url
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=trace_url,
                metrics=base_metrics,
                decision=route_used,
            )
        except Exception:
            pass
        return payload
        
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions (4xx/5xx) - FastAPI will handle status code
        elapsed = (time.perf_counter() - start) * 1000
        logger.warning(f"level=WARN trace_id={trace_id} status=HTTP_{http_ex.status_code} latency_ms={elapsed:.1f} error='{http_ex.detail}'")
        try:
            trace_url = obs.build_obs_url(trace_id)
            raw_request.state.trace_url = trace_url
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=trace_url,
                decision=f"HTTP_{http_ex.status_code}",
            )
        except Exception:
            pass
        raise
    except Exception as e:
        # Log error with structured fields
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(f"level=ERROR trace_id={trace_id} status=ERROR route='error' latency_ms={elapsed:.1f} error_type={type(e).__name__} error='{str(e)}'")
        
        error_text = str(e)
        not_found_markers = (
            "StatusCode.NOT_FOUND",
            "doesn't exist",
            "Collection",
            "NOT_FOUND",
        )
        if any(marker in error_text for marker in not_found_markers):
            message = f"Collection '{actual_collection}' not found in Qdrant. Run `make seed-fiqa` to seed demo vectors."
            friendly_payload = {
                "ok": False,
                "ret_code": "DATASET_MISSING",
                "trace_id": trace_id,
                "question": cleaned_question if "cleaned_question" in locals() else "",
                "answer": "",
                "message": message,
                "latency_ms": elapsed,
                "route": "dataset_missing",
                "params": {
                    "top_k": request.top_k if request else 0,
                    "rerank": request.rerank if request else False,
                    "use_hybrid": request.use_hybrid if request else False,
                },
                "sources": [],
                "items": [],
                "metrics": get_default_metrics(),
                "reranker_triggered": False,
                "ts": datetime.utcnow().isoformat() + "Z",
            }
            try:
                trace_url = obs.build_obs_url(trace_id)
                raw_request.state.trace_url = trace_url
                obs.finalize_root(
                    job_id=trace_id,
                    trace_id=trace_id,
                    trace_url=trace_url,
                    decision="dataset_missing",
                )
            except Exception:
                pass
            return JSONResponse(
                status_code=200,
                headers={"X-Trace-Id": trace_id},
                content=friendly_payload,
            )
        
        try:
            trace_url = obs.build_obs_url(trace_id)
            raw_request.state.trace_url = trace_url
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=trace_url,
                decision="exception",
            )
        except Exception:
            pass
        
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
                "items": [],
                "metrics": get_default_metrics(),  # Structured metrics even in error
                "reranker_triggered": False,
                "degraded": False,
                "budget_ms": request.budget_ms if request else None,
                "ts": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.post("/query")
async def query(
    request: QueryRequest,
    response: Response,
    raw_request: Request,
    x_trace_id: Optional[str] = Header(None),
):
    return await _execute_query(request, response, raw_request, x_trace_id)


@router.get("/query")
async def query_get(
    raw_request: Request,
    response: Response,
    q: Optional[str] = FastAPIQuery(None),
    budget_ms: Optional[int] = FastAPIQuery(None),
    x_trace_id: Optional[str] = Header(None),
):
    payload = QueryRequest(q=q, budget_ms=budget_ms)
    return await _execute_query(payload, response, raw_request, x_trace_id)
