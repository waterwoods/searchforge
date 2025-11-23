"""
kv_experiment.py - KV/Streaming Experiment API Route

HTTP API endpoint for running KV-cache and streaming performance experiments.
Provides a frontend-friendly interface to compare 4 modes:
- baseline: use_kv_cache=false, stream=false
- kv_only: use_kv_cache=true, stream=false
- stream_only: use_kv_cache=false, stream=true
- kv_and_stream: use_kv_cache=true, stream=true
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.fiqa_api.services.kv_experiment_service import run_kv_experiment_for_all_modes

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================================
# Request/Response Models
# ========================================

class KvExperimentRequest(BaseModel):
    """Request model for KV experiment endpoint."""
    question: str = Field(..., description="User's question")
    collection: Optional[str] = Field(
        default="airbnb_la_demo",
        description="Collection name (default: airbnb_la_demo)"
    )
    profile_name: Optional[str] = Field(
        default="airbnb_la_location_first",
        description="Search profile name (default: airbnb_la_location_first)"
    )
    runs_per_mode: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of runs per mode (default: 3, max: 10)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filters: price_max, min_bedrooms, neighbourhood, room_type"
    )


class ModeMetrics(BaseModel):
    """Metrics for a single experiment mode."""
    num_runs: int
    p50_ms: float
    p95_ms: float
    p50_first_token_ms: float
    p95_first_token_ms: float
    avg_total_tokens: float
    avg_cost_usd: float
    stream_enabled: bool
    kv_enabled: bool
    kv_hit_rate: float
    stream_error_rate: float


class KvExperimentResponse(BaseModel):
    """Response model for KV experiment endpoint."""
    ok: bool
    question: str
    collection: str
    profile_name: Optional[str]
    modes: Dict[str, ModeMetrics]
    raw_samples: Optional[list] = None
    error: Optional[str] = None


# ========================================
# Route Handler
# ========================================

@router.post("/api/kv-experiment/run", response_model=KvExperimentResponse)
async def run_kv_experiment(request: KvExperimentRequest):
    """
    Run KV/Streaming experiment for all 4 modes.
    
    This endpoint runs the same query multiple times (runs_per_mode) for each of 4 modes:
    - baseline: use_kv_cache=false, stream=false
    - kv_only: use_kv_cache=true, stream=false
    - stream_only: use_kv_cache=false, stream=true
    - kv_and_stream: use_kv_cache=true, stream=true
    
    For KV modes (kv_only, kv_and_stream), a fixed session_id is used across runs
    to allow KV-cache hits on subsequent runs.
    
    Request body:
        question: str - User's question
        collection: str - Collection name (default: "airbnb_la_demo")
        profile_name: str - Profile name (default: "airbnb_la_location_first")
        runs_per_mode: int - Number of runs per mode (default: 3, max: 10)
        filters: dict - Optional filters (price_max, min_bedrooms, neighbourhood, room_type)
    
    Returns:
        {
            "ok": bool,
            "question": str,
            "collection": str,
            "profile_name": str,
            "modes": {
                "baseline": {...},
                "kv_only": {...},
                "stream_only": {...},
                "kv_and_stream": {...},
            },
            "raw_samples": [...] (optional, limited to first 3 per mode)
        }
    
    Example request:
        {
            "question": "Find a 2 bedroom place in West LA under $200 per night",
            "collection": "airbnb_la_demo",
            "profile_name": "airbnb_la_location_first",
            "runs_per_mode": 3,
            "filters": {
                "price_max": 200,
                "min_bedrooms": 2,
                "neighbourhood": "Long Beach",
                "room_type": "Entire home/apt"
            }
        }
    """
    try:
        result = await run_kv_experiment_for_all_modes(
            question=request.question,
            collection=request.collection or "airbnb_la_demo",
            profile_name=request.profile_name or "airbnb_la_location_first",
            runs_per_mode=request.runs_per_mode,
            filters=request.filters,
        )
        
        # Convert modes dict to ModeMetrics objects
        modes_metrics = {}
        for mode_name, mode_data in result.get("modes", {}).items():
            modes_metrics[mode_name] = ModeMetrics(**mode_data)
        
        return KvExperimentResponse(
            ok=result.get("ok", False),
            question=result.get("question", request.question),
            collection=result.get("collection", request.collection or "airbnb_la_demo"),
            profile_name=result.get("profile_name", request.profile_name),
            modes=modes_metrics,
            raw_samples=result.get("raw_samples"),
            error=result.get("error"),
        )
        
    except Exception as e:
        logger.error(f"KV experiment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Experiment failed: {str(e)}"
        )




