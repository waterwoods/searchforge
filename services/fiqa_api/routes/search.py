"""
search.py - Search Route Handler
=================================
Handles /search endpoint with parameter validation and error mapping.
Core logic delegated to services/search_core.py.
"""

import logging
import uuid
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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
# Request/Response Models
# ========================================

class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    top_k: int = 10
    collection: str = "fiqa"
    rerank: bool = False


def _item_to_result(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = item.get("payload") if isinstance(item, dict) else {}
    if not isinstance(payload, dict):
        payload = {}
    doc_id = payload.get("doc_id") or item.get("id") or payload.get("id") or "unknown"
    result: Dict[str, Any] = {
        "id": doc_id,
        "score": item.get("score", 0.0),
        "title": payload.get("title") or item.get("title", ""),
        "text": payload.get("text") or item.get("text", ""),
    }
    if payload:
        result["payload"] = payload
    return result


# ========================================
# Route Handler
# ========================================

@router.post("/search")
async def search(
    request: SearchRequest,
    response: Response,
    raw_request: Request,
    x_lab_exp: Optional[str] = Header(None),
    x_lab_phase: Optional[str] = Header(None),
    x_topk: Optional[str] = Header(None),
    x_trace_id: Optional[str] = Header(None),
):
    """
    Search endpoint with unified routing (FAISS/Qdrant/Milvus).
    
    Routes queries between FAISS, Qdrant, and Milvus based on routing flags and query characteristics.
    
    Lab experiment headers:
    - X-Lab-Exp: Experiment ID for metrics collection
    - X-Lab-Phase: Phase identifier (A/B)
    - X-TopK: Top-K value for the request
    
    Returns:
        Search results with latency and routing info
    """
    # Performance tracking
    start = time.perf_counter()
    trace_id_candidate = (x_trace_id or "").strip()
    trace_id = trace_id_candidate or str(uuid.uuid4())
    response.headers["X-Trace-Id"] = trace_id
    raw_request.state.trace_id = trace_id
    obs_ctx = {"trace_id": trace_id, "job_id": trace_id}
    raw_request.state.obs_ctx = obs_ctx
    
    if USE_RETRIEVAL_PROXY:
        items, timings, degraded, trace_url = proxy_search(
            query=request.query,
            k=request.top_k,
            budget_ms=PROXY_DEFAULT_BUDGET_MS,
            trace_id=trace_id,
        )
        latency_ms = timings.get("total_ms")
        if latency_ms is None:
            latency_ms = (time.perf_counter() - start) * 1000
        latency_ms = float(latency_ms)
        route_used = timings.get("route") or "retrieval_proxy"
        ret_code = timings.get("ret_code") or "OK"
        results = [_item_to_result(item) for item in items]
        payload: Dict[str, Any] = {
            "ok": True,
            "results": results,
            "latency_ms": latency_ms,
            "route": route_used,
            "fallback": degraded,
            "doc_ids": [res["id"] for res in results],
            "timings": timings,
            "ret_code": ret_code,
            "degraded": degraded,
            "trace_url": trace_url,
        }
        response.headers["X-Search-Route"] = route_used
        response.headers["X-Proxy-RetCode"] = ret_code
        response.headers["X-Proxy-Cache-Hit"] = "true" if timings.get("cache_hit") else "false"
        if trace_url:
            response.headers["X-Langfuse-Trace-Url"] = trace_url
        elapsed = latency_ms
        logger.info(
            "level=INFO trace_id=%s route=%s ret_code=%s cache_hit=%s latency_ms=%.1f",
            trace_id,
            route_used,
            ret_code,
            timings.get("cache_hit"),
            elapsed,
        )
        try:
            raw_request.state.trace_url = trace_url or obs.build_obs_url(trace_id)
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=raw_request.state.trace_url,
                metrics=timings,
                decision=route_used,
            )
        except Exception:
            pass
        return payload
    
    # Workaround: Get app state from global app instance
    # This is a temporary solution - proper DI should be used
    try:
        from services.fiqa_api.app_main import app
        routing_flags = app.state.routing_flags
        faiss_engine = app.state.faiss_engine
        faiss_ready = app.state.faiss_ready
        faiss_enabled = app.state.faiss_enabled
    except Exception as e:
        logger.error(f"[SEARCH] Failed to access app state: {e}")
        # Fallback defaults
        routing_flags = {"enabled": True, "mode": "rules"}
        faiss_engine = None
        faiss_ready = False
        faiss_enabled = False
    
    try:
        # Prepare lab headers dict
        lab_headers = None
        if x_lab_exp:
            lab_headers = {
                "x_lab_exp": x_lab_exp,
                "x_lab_phase": x_lab_phase,
                "x_topk": x_topk
            }
        
        # Call service layer
        result = perform_search(
            query=request.query,
            top_k=request.top_k,
            collection=request.collection,
            routing_flags=routing_flags,
            faiss_engine=faiss_engine,
            faiss_ready=faiss_ready,
            faiss_enabled=faiss_enabled,
            lab_headers=lab_headers,
            obs_ctx=obs_ctx,
        )
        
        # Set response headers (preserve original behavior)
        response.headers["X-Search-Route"] = result.get("route", "unknown")
        
        # Log performance
        elapsed = (time.perf_counter() - start) * 1000
        logger.info("level=INFO trace_id=%s route=%s latency_ms=%.1f", trace_id, result.get("route", "unknown"), elapsed)
        
        try:
            trace_url = result.get("trace_url") or obs.build_obs_url(trace_id)
            raw_request.state.trace_url = trace_url
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=trace_url,
                metrics=result.get("timings") or {},
                decision=result.get("route", "legacy"),
            )
        except Exception:
            pass
        return result
        
    except Exception as e:
        logger.error(f"[SEARCH] Error: {e}")
        
        # Log performance even on error
        elapsed = (time.perf_counter() - start) * 1000
        logger.error("level=ERROR trace_id=%s latency_ms=%.1f status=ERROR", trace_id, elapsed)
        try:
            trace_url = obs.build_obs_url(trace_id)
            raw_request.state.trace_url = trace_url
            obs.finalize_root(
                job_id=trace_id,
                trace_id=trace_id,
                trace_url=trace_url,
                decision="error",
            )
        except Exception:
            pass
        
        # Set route header even on error
        response.headers["X-Search-Route"] = "error"
        
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "latency_ms": 0,
                "route": "error"
            }
        )

