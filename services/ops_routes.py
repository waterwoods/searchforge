"""
Operations Routes
=================
Operational endpoints for system introspection and control.

Endpoints:
- GET /ops/force_status - Get force override status with precedence trace
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from services.plugins.force_override import resolve, get_status, ForceStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ops", tags=["operations"])


@router.get("/force_status", response_model=ForceStatus)
async def get_force_status(
    planned: Optional[str] = Query(
        None,
        description="JSON-encoded planned parameters (e.g., '{\"num_candidates\":100}')"
    )
) -> ForceStatus:
    """
    Get force override status with full precedence trace.
    
    This endpoint shows:
    - Current force override configuration
    - How parameters flow through the precedence chain
    - What would be the effective parameters for a given input
    
    Args:
        planned: Optional JSON string of planned parameters
        
    Returns:
        ForceStatus with precedence chain and effective parameters
        
    Examples:
        GET /ops/force_status
        GET /ops/force_status?planned={"num_candidates":100,"rerank_topk":50}
    """
    # Parse planned parameters
    planned_params = {}
    if planned:
        try:
            planned_params = json.loads(planned)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in 'planned' parameter: {e}"
            )
    
    # Get defaults from environment (optional)
    defaults = {
        "num_candidates": 50,
        "rerank_topk": 6,
        "qps": 60
    }
    
    # Resolve through precedence chain
    status = resolve(planned_params, context="ops_force_status", defaults=defaults)
    
    logger.info(
        f"[OPS] Force status requested with planned={planned_params}, "
        f"effective={status.effective_params}"
    )
    
    return status


@router.get("/force_config")
async def get_force_config() -> dict:
    """
    Get current force override configuration (without precedence trace).
    
    Returns:
        Dictionary with current configuration
    """
    config = get_status()
    logger.debug(f"[OPS] Force config requested: {config}")
    return config


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint for ops routes.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "ops_routes",
        "endpoints": [
            "/ops/force_status",
            "/ops/force_config",
            "/ops/health",
            "/ops/verify",
            "/ops/decisions"
        ]
    }


@router.get("/verify")
async def verify_system() -> dict:
    """
    Quick verification endpoint for system health and configuration sync.
    
    This endpoint provides a fast health check showing:
    - Force override environment configuration
    - Hard cap environment configuration  
    - Plugin status (Force Override, Guardrails, Watchdog)
    - Shadow traffic configuration
    - Frontend sync readiness
    
    Returns:
        System verification status
    """
    from services.core.shadow import get_shadow_config
    from services.plugins.guardrails import get_status as get_guardrails_status
    from services.plugins.watchdog import get_status as get_watchdog_status
    from services.core.settings import get_recall_config
    
    force_config = get_status()
    shadow_config = get_shadow_config()
    guardrails_status = get_guardrails_status()
    watchdog_status = get_watchdog_status()
    recall_config = get_recall_config()
    
    import os
    
    # Get Black Swan async status (now properly async)
    black_swan_status = {}
    try:
        from services.black_swan.state import get_state
        state_mgr = get_state()
        
        # Properly await the async call
        state = await state_mgr.get_state()
        
        if state:
            black_swan_status = {
                "enabled": True,
                "available": True,
                "phase": state.phase.value if hasattr(state.phase, 'value') else state.phase,
                "progress": state.progress,
                "run_id": state.run_id
            }
        else:
            black_swan_status = {
                "enabled": True,
                "available": True,
                "phase": "idle",
                "progress": 0
            }
    except ImportError:
        black_swan_status = {
            "enabled": False,
            "available": False,
            "error": "Module not available"
        }
    except Exception as e:
        black_swan_status = {
            "enabled": True,
            "available": False,
            "error": f"State check failed: {str(e)}"
        }
    
    # Probe Qdrant connectivity
    qdrant_status = {"ok": False, "error": "not_checked"}
    try:
        from qdrant_client import QdrantClient
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=2)
        collections = client.get_collections()
        qdrant_status = {
            "ok": True,
            "host": qdrant_host,
            "port": qdrant_port,
            "collections": len(collections.collections)
        }
    except Exception as e:
        qdrant_status = {
            "ok": False,
            "error": "qdrant_unreachable",
            "message": str(e)[:100]
        }
    
    # Probe Redis connectivity
    redis_status = {"ok": False, "error": "not_checked"}
    try:
        from core.metrics import metrics_sink
        if metrics_sink and hasattr(metrics_sink, 'client'):
            metrics_sink.client.ping()
            redis_status = {
                "ok": True,
                "backend": "redis",
                "connected": True
            }
        else:
            redis_status = {
                "ok": False,
                "error": "redis_unavailable",
                "message": "Metrics sink not configured"
            }
    except ImportError as e:
        redis_status = {
            "ok": False,
            "error": "redis_unreachable",
            "message": "Core metrics module not available - using memory mode"
        }
    except Exception as e:
        redis_status = {
            "ok": False,
            "error": "redis_unreachable",
            "message": str(e)[:100]
        }
    
    # Determine storage backend
    storage_backend = "redis" if redis_status["ok"] else "memory"
    
    return {
        "ok": True,
        "service": "app_main",
        "version": "1.0.0",
        "port": int(os.getenv("MAIN_PORT", "8011")),
        "proxy_to_v2": False,  # CRITICAL: No longer proxying to app_v2
        "data_sources": {
            "qdrant": qdrant_status,
            "redis": redis_status
        },
        "plugins": {
            "black_swan_async": {
                "enabled": True,
                "storage": storage_backend
            },
            "tuner": {
                "enabled": True,
                "mode": "stub"
            }
        },
        "endpoints": {
            "black_swan": ["status", "config", "run", "report", "stop"],
            "tuner": ["enabled", "toggle"]
        },
        "env_force_override": force_config["force_override"],
        "env_hard_cap": force_config["hard_cap_enabled"],
        "shadow": {
            "enabled": shadow_config["enabled"],
            "pct": shadow_config["percentage"],
            "status": shadow_config["status"]
        },
        "plugins": {
            "force_override": {
                "enabled": force_config["force_override"],
                "status": "ok"
            },
            "guardrails": {
                "mode": guardrails_status["mode"],
                "status": guardrails_status["status"]
            },
            "watchdog": {
                "mode": watchdog_status["mode"],
                "status": watchdog_status["status"]
            }
        },
        "black_swan_async": black_swan_status,
        "plugin_status": "ok",
        "frontend_sync": "ready",
        "active_params": force_config["active_params"],
        "hard_cap_limits": force_config["hard_cap_limits"],
        "recall": {
            "enabled": recall_config["enabled"],
            "sample_rate": recall_config["sample_rate"]
        }
    }


@router.get("/decisions")
async def get_decisions(limit: int = 20) -> dict:
    """
    AutoTuner decision log endpoint.
    
    Returns decision history from AutoTuner. Currently returns empty
    as AutoTuner is not integrated in app_main yet.
    
    Args:
        limit: Maximum number of decisions to return (default 20)
        
    Returns:
        Decision log with schema
    """
    return {
        "ok": True,
        "decisions": [],
        "schema": {
            "decision": {
                "ts": "int (unix timestamp)",
                "action": "str (e.g., 'increase_k', 'decrease_k')",
                "reason": "str (reason for decision)",
                "params_before": "dict",
                "params_after": "dict",
                "metrics": "dict (p95, recall, etc.)"
            }
        },
        "count": 0,
        "limit": limit,
        "note": "AutoTuner not integrated in app_main yet - returns empty list"
    }

