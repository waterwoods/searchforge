"""
AutoTuner Router
================
FastAPI endpoints for AutoTuner control and status.

Endpoints:
- GET /api/autotuner/status - Get current tuner status
- POST /api/autotuner/start - Start tuning job
- POST /api/autotuner/stop - Stop tuning job
- GET /api/autotuner/recommendations - Get tuning recommendations
"""

import sys
import time
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to path
project_root = Path(__file__).parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/autotuner", tags=["AutoTuner"])


# ========================================
# Pydantic Models
# ========================================

class AutoTunerStatus(BaseModel):
    """AutoTuner status response model."""
    ok: bool
    job_id: str
    status: str = Field(..., description="Tuning status: 'idle', 'running', 'completed', 'error'")
    current_params: Dict[str, Any] = Field(default_factory=dict)
    progress: Optional[int] = Field(None, description="Progress 0-100")
    last_update: str = Field(..., description="ISO timestamp of last update")


class EstimatedImpact(BaseModel):
    """Estimated impact of parameter change."""
    delta_p95_ms: Optional[float] = None
    delta_recall_pct: Optional[float] = None


class AutoTunerRecommendation(BaseModel):
    """AutoTuner recommendation model."""
    params: Dict[str, Any]
    estimated_impact: EstimatedImpact
    reason: str
    timestamp: str


class ApiAutoTunerRecommendationsResponse(BaseModel):
    """AutoTuner recommendations response."""
    ok: bool
    job_id: str
    recommendations: List[AutoTunerRecommendation]


class StartJobResponse(BaseModel):
    """Start job response."""
    ok: bool
    job_id: str


class StopJobResponse(BaseModel):
    """Stop job response."""
    ok: bool


# ========================================
# Helper Functions
# ========================================

def get_autotuner_instances():
    """
    Get global AutoTuner instances from rag_api.
    
    Returns:
        Tuple of (autotuner, state) or (None, None) if not available
    """
    try:
        # Import from services/rag_api/app.py
        sys.path.insert(0, str(project_root / "services" / "rag_api"))
        from app import get_global_autotuner
        
        autotuner, state = get_global_autotuner()
        if autotuner is None or state is None:
            logger.warning("⚠️ AutoTuner not initialized")
            return None, None
        
        return autotuner, state
        
    except Exception as e:
        logger.error(f"❌ Failed to get AutoTuner instances: {e}")
        return None, None


def generate_job_id() -> str:
    """Generate a unique job ID."""
    timestamp = int(time.time())
    return f"tuner_job_{timestamp}_{str(uuid.uuid4())[:8]}"


# ========================================
# Endpoints
# ========================================

@router.get("/status", response_model=AutoTunerStatus)
async def get_status():
    """
    Get current AutoTuner status.
    
    Returns:
        AutoTunerStatus with current state and parameters
    """
    try:
        autotuner, state = get_autotuner_instances()
        
        if autotuner is None or state is None:
            raise HTTPException(
                status_code=503,
                detail="AutoTuner not available or not initialized"
            )
        
        # Generate job ID based on tuning state
        if state.is_tuning:
            job_id = f"tuner_job_{int(state.last_tuning_time)}"
        else:
            job_id = "idle"
        
        # Determine status
        if state.is_tuning:
            status = "running"
        else:
            status = "idle"
        
        # Get current parameters
        current_params = state.get_current_params()
        
        # Calculate progress (simplified - could be enhanced)
        progress = None
        if state.is_tuning and state.tuning_count > 0:
            # Simple progress based on tuning iterations
            progress = min(100, state.tuning_count * 10)
        
        # Last update timestamp
        last_update = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        
        return AutoTunerStatus(
            ok=True,
            job_id=job_id,
            status=status,
            current_params=current_params,
            progress=progress,
            last_update=last_update
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting AutoTuner status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AutoTuner status: {str(e)}"
        )


@router.post("/start", response_model=StartJobResponse)
async def start_tuning():
    """
    Start a new tuning job.
    
    Returns:
        StartJobResponse with job_id
    """
    try:
        autotuner, state = get_autotuner_instances()
        
        if autotuner is None or state is None:
            raise HTTPException(
                status_code=503,
                detail="AutoTuner not available or not initialized"
            )
        
        # Check if already running
        if state.is_tuning:
            logger.warning("⚠️ Tuning job already running")
            job_id = f"tuner_job_{int(state.last_tuning_time)}"
            return StartJobResponse(ok=True, job_id=job_id)
        
        # Start tuning
        state.start_tuning()
        job_id = f"tuner_job_{int(state.last_tuning_time)}"
        
        logger.info(f"✅ Started tuning job: {job_id}")
        
        return StartJobResponse(ok=True, job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting tuning job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start tuning job: {str(e)}"
        )


@router.post("/stop", response_model=StopJobResponse)
async def stop_tuning():
    """
    Stop the current tuning job.
    
    Returns:
        StopJobResponse
    """
    try:
        autotuner, state = get_autotuner_instances()
        
        if autotuner is None or state is None:
            raise HTTPException(
                status_code=503,
                detail="AutoTuner not available or not initialized"
            )
        
        # Check if tuning is running
        if not state.is_tuning:
            logger.warning("⚠️ No tuning job is running")
            return StopJobResponse(ok=True)
        
        # Stop tuning
        state.stop_tuning()
        
        logger.info("✅ Stopped tuning job")
        
        return StopJobResponse(ok=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error stopping tuning job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop tuning job: {str(e)}"
        )


@router.get("/recommendations", response_model=ApiAutoTunerRecommendationsResponse)
async def get_recommendations():
    """
    Get AutoTuner recommendations.
    
    For now, returns mock recommendations. Can be enhanced to return
    real recommendations from the AutoTuner's decision history.
    
    Returns:
        ApiAutoTunerRecommendationsResponse with recommendations list
    """
    try:
        autotuner, state = get_autotuner_instances()
        
        if autotuner is None or state is None:
            raise HTTPException(
                status_code=503,
                detail="AutoTuner not available or not initialized"
            )
        
        # Generate job ID
        job_id = "mock_job" if not state.is_tuning else f"tuner_job_{int(state.last_tuning_time)}"
        
        # Get current params to generate contextual recommendations
        current_params = state.get_current_params()
        current_ef = current_params.get("ef_search", 128)
        current_rerank = current_params.get("rerank_k", 200)
        
        # Create mock recommendations based on current state
        # These are simplified recommendations for initial integration
        recommendations = []
        
        # Recommendation 1: Increase ef_search for better recall
        if current_ef < 200:
            recommendations.append(
                AutoTunerRecommendation(
                    params={
                        "ef_search": min(current_ef + 32, 256),
                        "rerank_k": current_rerank
                    },
                    estimated_impact=EstimatedImpact(
                        delta_p95_ms=15.0,
                        delta_recall_pct=2.5
                    ),
                    reason="low_recall_with_latency_margin",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
                )
            )
        
        # Recommendation 2: Decrease ef_search for lower latency
        if current_ef > 96:
            recommendations.append(
                AutoTunerRecommendation(
                    params={
                        "ef_search": max(current_ef - 32, 64),
                        "rerank_k": current_rerank
                    },
                    estimated_impact=EstimatedImpact(
                        delta_p95_ms=-20.0,
                        delta_recall_pct=-1.5
                    ),
                    reason="high_latency_with_recall_redundancy",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
                )
            )
        
        # If no recommendations, provide a balanced option
        if not recommendations:
            recommendations.append(
                AutoTunerRecommendation(
                    params={
                        "ef_search": 128,
                        "rerank_k": 200
                    },
                    estimated_impact=EstimatedImpact(
                        delta_p95_ms=0.0,
                        delta_recall_pct=0.0
                    ),
                    reason="balanced_baseline",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
                )
            )
        
        logger.info(f"✅ Generated {len(recommendations)} recommendations")
        
        return ApiAutoTunerRecommendationsResponse(
            ok=True,
            job_id=job_id,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )


