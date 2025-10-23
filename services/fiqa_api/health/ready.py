"""
ready.py - Lightweight Readiness Check
======================================
Fast readiness check for Kubernetes liveness/readiness probes.
Returns immediately based on startup initialization status.

For detailed diagnostics, use health/diagnose.py (future implementation).
"""

import time
import asyncio
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter()


# ========================================
# Lightweight Readiness Check
# ========================================

@router.get("/readyz")
async def readiness_check():
    """
    Fast readiness check - returns immediately based on client initialization status.
    
    This is designed for Kubernetes probes and should complete in <30ms.
    Performs lightweight connection health checks with auto-reconnect.
    
    Returns:
        {"ok": true/false, "clients_ready": bool, "service": str, "timestamp": str}
    """
    from services.fiqa_api.clients import (
        are_clients_ready, 
        get_clients_status,
        ensure_qdrant_connection,
        ensure_redis_connection
    )
    
    start_time = time.perf_counter()
    
    # Run connection checks concurrently with timeout
    try:
        # Run both checks in parallel with 2s timeout each
        qdrant_ok, redis_ok = await asyncio.gather(
            asyncio.wait_for(
                asyncio.to_thread(ensure_qdrant_connection),
                timeout=2.0
            ),
            asyncio.wait_for(
                asyncio.to_thread(ensure_redis_connection),
                timeout=2.0
            ),
            return_exceptions=False
        )
    except asyncio.TimeoutError:
        logger.warning("[READYZ] Connection check timed out")
        qdrant_ok = False
        redis_ok = False
    except Exception as e:
        logger.error(f"[READYZ] Connection check failed: {e}")
        qdrant_ok = False
        redis_ok = False
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(f"[READYZ] Total latency: {elapsed_ms:.2f}ms")
    
    clients_ready = are_clients_ready() and qdrant_ok and redis_ok
    clients_status = get_clients_status()
    
    # Add connection health to status
    clients_status["qdrant_connected"] = qdrant_ok
    clients_status["redis_connected"] = redis_ok
    
    return {
        "ok": clients_ready,
        "status": "ready" if clients_ready else "not_ready",
        "clients_ready": clients_ready,
        "clients": clients_status,
        "service": "app_main",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


@router.get("/healthz")
async def health_check():
    """
    Fast health check - returns immediately.
    Always returns 200 if the service is running.
    
    Returns:
        {"ok": true, "status": "healthy", "service": str, "timestamp": str}
    """
    return {
        "ok": True,
        "status": "healthy",
        "service": "app_main",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

