"""
ops_copilot.py - Ops Copilot Route Handler
===========================================
Handles /api/ops-copilot/system-health endpoint for system health checks.
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from services.fiqa_api.ops_copilot.schemas import (
    SystemSnapshot,
    SystemHealthAgentResponse,
)
from services.fiqa_api.ops_copilot.graphs.system_health_graph import (
    run_system_health_graph,
)
from services.fiqa_api.ops_copilot.input_validation import validate_system_snapshot
from services.fiqa_api.observability.security_events import log_security_event

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter()


# ========================================
# Route Handler
# ========================================

@router.post("/ops-copilot/system-health", response_model=SystemHealthAgentResponse)
async def system_health_endpoint(
    snapshot: SystemSnapshot,
    request: Request,
) -> SystemHealthAgentResponse:
    """
    System Health Agent: check system health, suggest safety upgrades, and explain results.
    
    This endpoint:
    1. Takes a SystemSnapshot with current system metrics
    2. Runs health check to compute band, score, and risk flags
    3. If degraded/critical, generates safety upgrade suggestions
    4. Runs strategy lab to explore alternative scenarios
    5. Generates LLM narrative to explain results in SRE-friendly language
    6. Returns structured response with all results
    
    Request body:
        SystemSnapshot with:
            - service_name: str - Service name, e.g., 'search-api'
            - environment: str - Environment: 'prod', 'staging', or 'dev'
            - cpu_pct: float - CPU usage percentage (0-100)
            - mem_pct: float - Memory usage percentage (0-100)
            - p95_latency_ms: float - P95 latency in milliseconds
            - error_rate: float - Error rate (0-1)
            - qps: float - Queries per second
            - disk_pct: float - Disk usage percentage (0-100)
            - timestamp: datetime - Timestamp when snapshot was taken
            - region: str (optional) - Region identifier
            - tags: dict (optional) - Additional metadata tags
    
    Returns:
        SystemHealthAgentResponse with:
            - snapshot: Input snapshot
            - health_result: SystemHealthCheckResult with band, score, risk_flags
            - safety_suggestions: List of SaferConfigSuggestion (if degraded/critical)
            - strategy_lab: SystemStrategyLabResult with alternative scenarios
            - narrative: SRE-friendly narrative explanation
            - recommended_actions: List of recommended actions
            - agent_steps: Step-by-step execution log
            - llm_usage: LLM usage metadata
    
    Example request:
        {
            "service_name": "search-api",
            "environment": "prod",
            "cpu_pct": 82.0,
            "mem_pct": 78.0,
            "p95_latency_ms": 650.0,
            "error_rate": 0.03,
            "qps": 1200.0,
            "disk_pct": 88.0,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    """
    # Get request_id from request state or generate new one
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = uuid.uuid4().hex
    
    # Input validation with security logging
    validation_errors = validate_system_snapshot(snapshot)
    if validation_errors:
        log_security_event(
            event_type="input_validation_failed",
            request_id=request_id,
            context={
                "service_name": "ops_copilot",
                "endpoint": "system_health_endpoint",
                "errors": validation_errors,
                "service_name_input": snapshot.service_name,
                "environment": snapshot.environment,
            },
        )
        raise HTTPException(
            status_code=400,
            detail={"errors": validation_errors}
        )
    
    try:
        logger.info(
            f"level=INFO endpoint=system_health_endpoint "
            f"service_name={snapshot.service_name} "
            f"environment={snapshot.environment} "
            f"request_id={request_id}"
        )
        
        # Run the LangGraph workflow
        result = run_system_health_graph(snapshot, request_id=request_id)
        
        logger.info(
            f"level=INFO endpoint=system_health_endpoint status=success "
            f"band={result['health_result'].band} "
            f"score={result['health_result'].score:.1f} "
            f"suggestions_count={len(result.get('safety_suggestions', []))} "
            f"request_id={request_id}"
        )
        
        # Convert to response model
        return SystemHealthAgentResponse(
            snapshot=result["snapshot"],
            health_result=result["health_result"],
            safety_suggestions=result.get("safety_suggestions", []),
            strategy_lab=result.get("strategy_lab"),
            narrative=result.get("narrative"),
            recommended_actions=result.get("recommended_actions", []),
            agent_steps=result.get("agent_steps", []),
            llm_usage=result.get("llm_usage"),
        )
    except ValueError as ve:
        # Input validation errors
        logger.warning(
            f"level=WARN endpoint=system_health_endpoint status=VALIDATION_ERROR error='{str(ve)}'",
            exc_info=True
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Unexpected errors - log full traceback for debugging
        logger.exception(
            f"level=ERROR endpoint=system_health_endpoint status=ERROR "
            f"error_type={type(e).__name__} error='{str(e)}'"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )

