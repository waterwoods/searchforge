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

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature flags
FEATURE_BANDIT_ROUTING = os.getenv('FEATURE_BANDIT_ROUTING', 'off').lower() == 'on'

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

# Initialize routing components
if FEATURE_BANDIT_ROUTING:
    bandit_api = BanditRAGAPI()
else:
    bandit_api = None

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
            # Use standard routing (placeholder implementation)
            logger.warning("Standard routing not implemented - returning mock response")
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
            "standard_routing": not FEATURE_BANDIT_ROUTING
        },
        routing_method="bandit" if FEATURE_BANDIT_ROUTING else "standard",
        collections=["amazon_electronics_100k", "amazon_reviews_hybrid"]
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
