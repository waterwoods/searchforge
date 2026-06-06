"""
ready.py - Lightweight Readiness Check
======================================
Fast readiness check for Kubernetes liveness/readiness probes.
Returns immediately based on startup initialization status.

For detailed diagnostics, use health/diagnose.py (future implementation).
"""

import os
import time
import asyncio
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Demo mode flag - makes embedding_model optional for retrieval-only mode
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")


def _vectors_optional_for_intake() -> bool:
    """Qdrant/embedding optional when demo cloud or paid-pilot intake-core readiness."""

    if DEMO_MODE:
        return True
    try:
        from services.fiqa_api.deployment_profile import intake_core_readiness_enabled

        return intake_core_readiness_enabled()
    except Exception:
        return False

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
    Intake readiness (paid pilot): prefer ``intake_path_ready`` over top-level ``ok``.

    When ``UNIFIED_INTAKE_INTAKE_CORE_READINESS=1`` (with product-only) or ``DEMO_MODE``,
    Qdrant/embedding are optional — inbox triage still runs. Legacy full-stack mode treats
    vectors as required. Do not confuse with ``GET /ready`` (RAG/vector legacy gate).
    
    This is designed for Kubernetes probes and should complete in <30ms.
    Performs lightweight connection health checks with auto-reconnect.
    
    Core dependencies (required for readiness):
    - qdrant_connected: Qdrant connection must be healthy
    - embedding_model: Embedding model must be initialized (optional if DEMO_MODE=true)
    - gpu_client_connected: GPU worker connection (if GPU worker is configured)
    
    Optional dependencies (reported but do not block readiness):
    - redis_connected: Redis connection (optional)
    - openai: OpenAI client (optional)
    - embedding_model: In DEMO_MODE, embedding model is optional (retrieval-only mode)
    
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
    
    vectors_optional = _vectors_optional_for_intake()

    # Define core dependencies (required for readiness)
    core_keys = []
    # Qdrant: required for RAG/search; optional for intake-core (triage is rule-based/LLM)
    if not vectors_optional:
        core_keys.append("qdrant_connected")
    elif not qdrant_ok:
        logger.info("[READYZ] Intake-core: qdrant not connected (inbox triage does not require Qdrant)")

    if not vectors_optional:
        core_keys.append("embedding_model")
    elif not clients_status.get("embedding_model", False):
        logger.info("[READYZ] Intake-core: embedding_model not ready (retrieval optional)")
    
    if not vectors_optional and clients_status.get("gpu_client_connected") is not None:
        core_keys.append("gpu_client_connected")
    
    # Compute core readiness based on core dependencies only
    core_ready = all(clients_status.get(k) for k in core_keys)
    
    # Log warnings for optional dependency failures (non-blocking)
    optional_keys = ["redis_connected", "openai"]
    if vectors_optional:
        optional_keys.append("embedding_model")
    
    for k in optional_keys:
        if not clients_status.get(k, True):
            logger.warning(f"[READYZ] Optional dependency not ready: {k}")
    
    # Set readiness based on core dependencies only
    clients_ready = core_ready
    ok = core_ready
    status = "ready" if core_ready else "not_ready"

    intake_path_ready = vectors_optional and (len(core_keys) == 0 or core_ready)
    if vectors_optional and not ok and len(core_keys) == 0:
        ok = True
        clients_ready = True
        status = "ready"
        intake_path_ready = True

    try:
        from services.fiqa_api.deployment_profile import runtime_service_display_name

        service_label = runtime_service_display_name()
    except Exception:
        service_label = "app_main"

    payload = {
        "ok": ok,
        "status": status,
        "clients_ready": clients_ready,
        "clients": clients_status,
        "service": service_label,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if vectors_optional:
        if DEMO_MODE:
            payload["demo_mode"] = True
        try:
            from services.fiqa_api.deployment_profile import intake_core_readiness_enabled

            if intake_core_readiness_enabled():
                payload["intake_core_readiness"] = True
        except Exception:
            pass
        payload["readiness_mode"] = "intake_core"
        payload["intake_path_ready"] = intake_path_ready
    else:
        payload["readiness_mode"] = "full_stack"
    return payload


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

