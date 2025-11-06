#!/usr/bin/env python3
"""
RAG API Service with optional bandit routing.
Main service that can be configured to use bandit routing or standard routing.
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
import time, statistics
from collections import deque
from fastapi import Request, APIRouter

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature flags
FEATURE_BANDIT_ROUTING = os.getenv('FEATURE_BANDIT_ROUTING', 'off').lower() == 'on'

# Observability and chaos configuration
CHAOS_LAT_MS = int(os.getenv('CHAOS_LAT_MS', '0'))
CHAOS_BURST_EVERY = int(os.getenv('CHAOS_BURST_EVERY', '40'))
CE_CACHE_SIZE = int(os.getenv('CE_CACHE_SIZE', '0'))
FORCE_CE_ON = os.getenv('FORCE_CE_ON', '1') == '1'
FORCE_HYBRID_ON = os.getenv('FORCE_HYBRID_ON', '1') == '1'
CANDIDATE_K_STEP = os.getenv('CANDIDATE_K_STEP', '100,200,400')
RERANK_K = int(os.getenv('RERANK_K', '50'))
TUNER_ENABLED = os.getenv('TUNER_ENABLED', '1') == '1'
TUNER_SAMPLE_SEC = int(os.getenv('TUNER_SAMPLE_SEC', '5'))
TUNER_COOLDOWN_SEC = int(os.getenv('TUNER_COOLDOWN_SEC', '10'))
SLO_P95_MS = float(os.getenv('SLO_P95_MS', '1200'))
SLO_RECALL_AT10 = float(os.getenv('SLO_RECALL_AT10', '0.30'))

# Import routing modules based on feature flags
BanditRAGAPI = None
BanditSearchRequest = None
BanditSearchResult = None
BanditAnalytics = None
MultiArmedBandit = None

if FEATURE_BANDIT_ROUTING:
    try:
        from modules.routing.bandit_router import (
            BanditRAGAPI, BanditSearchRequest, BanditSearchResult,
            BanditAnalytics, MultiArmedBandit
        )
        logger.info("✅ Bandit routing enabled")
    except ImportError as e:
        logger.error(f"❌ Failed to import bandit router: {e}")
        FEATURE_BANDIT_ROUTING = False
else:
    logger.info("📏 Using standard routing")

# Initialize FastAPI app
app = FastAPI(
    title="RAG API Service",
    description="Retrieval-Augmented Generation API with optional bandit routing",
    version="1.0.0"
)

# --- SLA / latency sampling (opt-in) ---
SLA_WINDOW_SEC = int(os.getenv("SLA_WINDOW_SEC", "120"))
SLA_MAX_SAMPLES = int(os.getenv("SLA_MAX_SAMPLES", "5000"))
SLA_ENABLED = os.getenv("RAG_API_SLA_SAMPLING", "on").lower() in ("1","true","on","yes")

_latency_samples = deque()  # (timestamp_sec, latency_ms)

def _gc_old_samples(now_sec: float):
    threshold = now_sec - SLA_WINDOW_SEC
    while _latency_samples and _latency_samples[0][0] < threshold:
        _latency_samples.popleft()

def _percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * (p/100.0)
    f = int(k)
    c = min(f + 1, len(values)-1)
    if f == c:
        return float(values[f])
    return float(values[f] + (values[c] - values[f]) * (k - f))

# Admin router
admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.get("/sla_status")
def sla_status():
    now = time.time()
    _gc_old_samples(now)
    lat = [ms for _, ms in _latency_samples]
    p95 = _percentile(lat, 95)
    p99 = _percentile(lat, 99)
    return {
        "enabled": SLA_ENABLED,
        "window_sec": SLA_WINDOW_SEC,
        "samples": len(lat),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
    }

app.include_router(admin_router)

@app.middleware("http")
async def sla_latency_middleware(request: Request, call_next):
    if not SLA_ENABLED:
        return await call_next(request)

    t0 = time.perf_counter()
    response = await call_next(request)
    t1 = time.perf_counter()

    latency_ms = (t1 - t0) * 1000.0
    now = time.time()
    _latency_samples.append((now, latency_ms))
    # bound memory
    if len(_latency_samples) > SLA_MAX_SAMPLES:
        _latency_samples.popleft()
    _gc_old_samples(now)
    return response

# Initialize routing components
if FEATURE_BANDIT_ROUTING:
    bandit_api = BanditRAGAPI()
else:
    bandit_api = None

# Initialize global AutoTuner instance
global_autotuner = None
global_autotuner_state = None

def get_global_autotuner():
    """Get or create global AutoTuner instance."""
    global global_autotuner, global_autotuner_state
    
    if global_autotuner is None:
        try:
            from modules.autotune.controller import AutoTuner
            from modules.autotune.state import TuningState
            
            # Initialize AutoTuner with proper parameters
            global_autotuner = AutoTuner(
                engine="hnsw",  # Changed from "ivf" to "hnsw"
                policy="Balanced",
                target_p95_ms=250.0,  # Updated for demo
                target_recall=0.8,    # Updated for demo
                hnsw_ef_range=(64, 256),  # Demo range
                step_up=32,           # Demo step sizes
                step_down=16
            )
            global_autotuner_state = TuningState()
            logger.info("✅ Global AutoTuner initialized")
            
        except ImportError as e:
            logger.warning(f"⚠️ AutoTuner not available: {e}")
            return None, None
    
    return global_autotuner, global_autotuner_state

# Request/Response models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    algorithm: Optional[str] = None
    enable_bm25: bool = False
    force_route: Optional[str] = None
    ab_test_mode: bool = False

class SearchResult(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    route_metrics: Dict[str, Any]
    routing_method: str
    objective_score: Optional[float] = None
    constraint_violations: Optional[List[str]] = None

class HealthResponse(BaseModel):
    status: str
    features: Dict[str, bool]
    routing_method: str
    collections: List[str]

@app.post("/search", response_model=SearchResult)
async def search(request: SearchRequest):
    """Main search endpoint with configurable routing."""
    try:
        if FEATURE_BANDIT_ROUTING and bandit_api:
            # Use bandit routing
            bandit_request = BanditSearchRequest(
                query=request.query,
                top_k=request.top_k,
                algorithm=request.algorithm or "ucb",
                enable_bm25=request.enable_bm25,
                force_route=request.force_route,
                ab_test_mode=request.ab_test_mode
            )
            
            bandit_result = bandit_api.search_with_bandit_routing(bandit_request)
            
            return SearchResult(
                query=bandit_result.query,
                results=bandit_result.results,
                route_metrics=bandit_result.route_metrics,
                routing_method="bandit",
                objective_score=bandit_result.objective_score,
                constraint_violations=bandit_result.constraint_violations
            )
        else:
            # Use standard routing - implement actual search
            try:
                # Import search pipeline
                from modules.search.search_pipeline import search_with_explain
                
                # Get collection name from request or use default
                collection_name = "amazon_electronics_100k"  # Default collection
                
                # Get global AutoTuner instance and parameters
                autotuner, autotuner_state = get_global_autotuner()
                autotuner_params = None
                
                if autotuner and autotuner_state:
                    # Get current AutoTuner parameters
                    current_params = autotuner_state.get_current_params()
                    if current_params:
                        # Map AutoTuner parameters to HNSW parameters
                        # Both nprobe and ef_search will be mapped to hnsw_ef
                        autotuner_params = {
                            'nprobe': current_params.get('nprobe'),
                            'ef_search': current_params.get('ef_search')
                        }
                
                # Perform search using the search pipeline with AutoTuner parameters
                search_results = search_with_explain(
                    query=request.query,
                    collection_name=collection_name,
                    reranker_name=request.algorithm or "llm",
                    explainer_name="simple",
                    top_n=request.top_k,
                    autotuner_params=autotuner_params
                )
                
                # Calculate metrics
                latency_ms = 50.0  # Placeholder latency
                recall_at_10 = min(1.0, len(search_results) / 10.0)
                cost_per_query = 0.01  # Placeholder cost
                
                return SearchResult(
                    query=request.query,
                    results=search_results,
                    route_metrics={
                        "route": "standard",
                        "routing_method": "standard",
                        "latency_ms": latency_ms,
                        "recall_at_10": recall_at_10,
                        "cost_per_query": cost_per_query
                    },
                    routing_method="standard"
                )
                
            except Exception as e:
                logger.error(f"Standard routing error: {e}")
                # Return empty results on error
                return SearchResult(
                    query=request.query,
                    results=[],
                    route_metrics={
                        "route": "standard",
                        "routing_method": "standard",
                        "latency_ms": 0.0,
                        "recall_at_10": 0.0,
                        "cost_per_query": 0.0
                    },
                    routing_method="standard"
                )
            
    except Exception as e:
        logger.error(f"Error processing search request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/bandit", response_model=BanditAnalytics)
async def get_bandit_analytics():
    """Get bandit analytics (only available when bandit routing is enabled)."""
    if not FEATURE_BANDIT_ROUTING or not bandit_api:
        raise HTTPException(status_code=404, detail="Bandit routing not enabled")
    
    return bandit_api.get_bandit_analytics()

@app.get("/analytics/arms")
async def get_arm_statistics():
    """Get arm statistics (only available when bandit routing is enabled)."""
    if not FEATURE_BANDIT_ROUTING or not bandit_api:
        raise HTTPException(status_code=404, detail="Bandit routing not enabled")
    
    return bandit_api.bandit.get_arm_statistics()

@app.post("/bandit/reset")
async def reset_bandit():
    """Reset bandit statistics (only available when bandit routing is enabled)."""
    if not FEATURE_BANDIT_ROUTING or not bandit_api:
        raise HTTPException(status_code=404, detail="Bandit routing not enabled")
    
    bandit_api.bandit = MultiArmedBandit(bandit_api.bandit.algorithm)
    bandit_api.query_history.clear()
    bandit_api.objective_scores.clear()
    return {"message": "Bandit reset successfully"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with feature status."""
    return HealthResponse(
        status="healthy",
        features={
            "bandit_routing": FEATURE_BANDIT_ROUTING,
            "standard_routing": not FEATURE_BANDIT_ROUTING,
            "chaos_enabled": CHAOS_LAT_MS > 0,
            "ce_cache_enabled": CE_CACHE_SIZE > 0,
            "force_ce_on": FORCE_CE_ON,
            "force_hybrid_on": FORCE_HYBRID_ON,
            "tuner_enabled": TUNER_ENABLED
        },
        routing_method="bandit" if FEATURE_BANDIT_ROUTING else "standard",
        collections=["amazon_electronics_100k", "amazon_reviews_hybrid"]
    )

@app.get("/config")
async def get_config():
    """Get current configuration values."""
    return {
        "chaos_lat_ms": CHAOS_LAT_MS,
        "chaos_burst_every": CHAOS_BURST_EVERY,
        "ce_cache_size": CE_CACHE_SIZE,
        "force_ce_on": FORCE_CE_ON,
        "force_hybrid_on": FORCE_HYBRID_ON,
        "candidate_k_step": CANDIDATE_K_STEP,
        "rerank_k": RERANK_K,
        "tuner_enabled": TUNER_ENABLED,
        "tuner_sample_sec": TUNER_SAMPLE_SEC,
        "tuner_cooldown_sec": TUNER_COOLDOWN_SEC,
        "slo_p95_ms": SLO_P95_MS,
        "slo_recall_at10": SLO_RECALL_AT10
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
