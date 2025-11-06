"""
search.py - Search Route Handler
=================================
Handles /search endpoint with parameter validation and error mapping.
Core logic delegated to services/search_core.py.
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Response, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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


# ========================================
# Route Handler
# ========================================

@router.post("/search")
async def search(
    request: SearchRequest,
    response: Response,
    x_lab_exp: Optional[str] = Header(None),
    x_lab_phase: Optional[str] = Header(None),
    x_topk: Optional[str] = Header(None)
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
            lab_headers=lab_headers
        )
        
        # Set response headers (preserve original behavior)
        response.headers["X-Search-Route"] = result.get("route", "unknown")
        
        # Log performance
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[Perf] /search took {elapsed:.1f} ms")
        
        return result
        
    except Exception as e:
        logger.error(f"[SEARCH] Error: {e}")
        
        # Log performance even on error
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[Perf] /search took {elapsed:.1f} ms (error)")
        
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

