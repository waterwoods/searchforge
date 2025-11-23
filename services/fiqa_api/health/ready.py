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
    
    Core dependencies (required for readiness):
    - embedding_model: Embedding model must be initialized
    - qdrant_connected: Qdrant connection must be healthy
    - gpu_client_connected: GPU worker connection (if GPU worker is configured)
    
    Optional dependencies (reported but do not block readiness):
    - redis_connected: Redis connection (optional)
    - openai: OpenAI client (optional)
    
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
    
    clients_status = get_clients_status()
    
    # Add connection health to status
    clients_status["qdrant_connected"] = qdrant_ok
    clients_status["redis_connected"] = redis_ok
    
    # Check GPU client status if available
    gpu_client_connected = None
    try:
        from services.fiqa_api.gpu_worker_client import get_gpu_pool
        gpu_pool = get_gpu_pool()
        if gpu_pool is not None:
            # Check if at least one GPU worker instance is healthy
            gpu_client_connected = any(instance.healthy for instance in gpu_pool.instances)
            clients_status["gpu_client_connected"] = gpu_client_connected
        else:
            # GPU worker not configured - not required
            clients_status["gpu_client_connected"] = None
    except Exception as e:
        logger.debug(f"[READYZ] GPU client check failed: {e}")
        clients_status["gpu_client_connected"] = False
        gpu_client_connected = False
    
    # Define core dependencies (required for readiness)
    core_keys = [
        "embedding_model",
        "qdrant_connected",
    ]
    
    # Add GPU client to core if it's configured (not None)
    if clients_status.get("gpu_client_connected") is not None:
        core_keys.append("gpu_client_connected")
    
    # Compute core readiness based on core dependencies only
    core_ready = all(clients_status.get(k) for k in core_keys)
    
    # Log warnings for optional dependency failures (non-blocking)
    optional_keys = ["redis_connected", "openai"]
    for k in optional_keys:
        if not clients_status.get(k, True):
            logger.warning(f"[READYZ] Optional dependency not ready: {k}")
    
    # Set readiness based on core dependencies only
    clients_ready = core_ready
    ok = core_ready
    status = "ready" if core_ready else "not_ready"
    
    return {
        "ok": ok,
        "status": status,
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
    Includes embedding_ready status check.
    
    Returns:
        {"ok": true, "version": "v11", "status": "healthy", "embedding_ready": bool, "service": str, "timestamp": str}
    """
    from services.fiqa_api.clients import check_embedding_ready
    
    # Lightweight probe for embedding backend
    embedding_ready = check_embedding_ready()
    
    return {
        "ok": True,
        "version": "v11",
        "status": "healthy",
        "embedding_ready": embedding_ready,
        "service": "app_main",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

