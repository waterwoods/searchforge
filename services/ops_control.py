"""
Ops Control Router for app_main.

Provides endpoints for control flow shaping and routing management:
- GET /ops/control/status
- POST/GET /ops/flags
- POST /ops/control/policy
- GET /ops/decisions
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any, Optional
import logging

from services.plugins.control import get_control_plugin
from services.plugins.routing import get_routing_plugin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ops", tags=["control"])


# ============================================================================
# CONTROL ENDPOINTS
# ============================================================================

@router.get("/control/status")
async def get_control_status():
    """
    Get control system status.
    
    Returns:
        Current policy, enabled signals/actuators, and parameters
    """
    try:
        control = get_control_plugin()
        routing = get_routing_plugin()
        
        return {
            "ok": True,
            "control": control.get_status(),
            "routing": routing.get_status()
        }
    
    except Exception as e:
        logger.error(f"Error getting control status: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@router.post("/flags")
async def set_flags(request: Request):
    """
    Set feature flags for control and routing.
    
    Body:
    {
        "control": {
            "signals": ["p95", "queue_depth"],
            "actuators": ["concurrency", "batch_size"],
            "policy": "aimd"
        },
        "routing": {
            "enabled": true,
            "policy": "rules",
            "faiss": true
        }
    }
    
    Returns:
        Changes applied
    """
    try:
        body = await request.json()
        
        results = {}
        
        # Update control flags
        if "control" in body:
            control = get_control_plugin()
            results["control"] = await control.set_flags(body["control"])
        
        # Update routing flags
        if "routing" in body:
            routing = get_routing_plugin()
            results["routing"] = await routing.set_flags(body["routing"])
        
        return {
            "ok": True,
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error setting flags: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@router.get("/flags")
async def get_flags():
    """
    Get current feature flags.
    
    Returns:
        Current control and routing flags
    """
    try:
        control = get_control_plugin()
        routing = get_routing_plugin()
        
        return {
            "ok": True,
            "control": {
                "enabled_signals": list(control.enabled_signals),
                "enabled_actuators": list(control.enabled_actuators),
                "policy": control.active_policy
            },
            "routing": {
                "enabled": routing.enabled,
                "policy": routing.policy,
                "faiss_healthy": routing.router.faiss_healthy
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting flags: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@router.post("/control/policy")
async def set_control_policy(request: Request):
    """
    Switch control policy (aimd <-> pid).
    
    Body:
    {
        "policy": "aimd" | "pid"
    }
    
    Returns:
        Policy switch result
    """
    try:
        body = await request.json()
        policy_name = body.get("policy")
        
        if not policy_name:
            return {
                "ok": False,
                "error": "policy name required"
            }
        
        control = get_control_plugin()
        result = await control.set_policy(policy_name)
        
        return result
    
    except Exception as e:
        logger.error(f"Error setting policy: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@router.get("/decisions")
async def get_decisions(limit: int = 200):
    """
    Get recent control decisions.
    
    Query params:
        limit: Max decisions to return (default 200)
    
    Returns:
        Last N decisions with why->do->result
    """
    try:
        control = get_control_plugin()
        decisions = control.get_decisions(limit=limit)
        
        return {
            "ok": True,
            "count": len(decisions),
            "decisions": decisions
        }
    
    except Exception as e:
        logger.error(f"Error getting decisions: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


# ============================================================================
# ROUTING ENDPOINTS
# ============================================================================

@router.post("/routing/route")
async def route_query(request: Request):
    """
    Get routing decision for a query.
    
    Body:
    {
        "topk": 10,
        "has_filter": false
    }
    
    Returns:
        Routing decision (faiss or qdrant)
    """
    try:
        body = await request.json()
        topk = body.get("topk", 10)
        has_filter = body.get("has_filter", False)
        
        routing = get_routing_plugin()
        decision = await routing.route(topk, has_filter)
        
        return {
            "ok": True,
            **decision
        }
    
    except Exception as e:
        logger.error(f"Error routing query: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@router.get("/routing/cost")
async def get_routing_cost(topk: int = 10):
    """
    Get cost comparison for routing.
    
    Query params:
        topk: Number of results
    
    Returns:
        Cost comparison between FAISS and Qdrant
    """
    try:
        routing = get_routing_plugin()
        comparison = routing.get_cost_comparison(topk)
        
        return {
            "ok": True,
            **comparison
        }
    
    except Exception as e:
        logger.error(f"Error getting cost comparison: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


# ============================================================================
# CONTROL LOOP MANAGEMENT
# ============================================================================

@router.post("/control/start")
async def start_control_loop():
    """
    Start the control loop.
    
    Returns:
        Start result
    """
    try:
        control = get_control_plugin()
        await control.start_control_loop()
        
        return {
            "ok": True,
            "status": "control_loop_started"
        }
    
    except Exception as e:
        logger.error(f"Error starting control loop: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@router.post("/control/stop")
async def stop_control_loop():
    """
    Stop the control loop.
    
    Returns:
        Stop result
    """
    try:
        control = get_control_plugin()
        await control.stop_control_loop()
        
        return {
            "ok": True,
            "status": "control_loop_stopped"
        }
    
    except Exception as e:
        logger.error(f"Error stopping control loop: {e}")
        return {
            "ok": False,
            "error": str(e)
        }

