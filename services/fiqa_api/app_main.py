"""
app_main.py - Clean Entry Point for SearchForge Main API
==========================================================
Composed entry point with plugins, middlewares, and read-only routes.

Default port: 8011 (configurable via MAIN_PORT)
Prefix: /v3 (optional, for path-based routing)

Features:
- Force Override plugin integration
- Guardrails & Watchdog (minimal no-op implementations)
- Shadow traffic capability (default 0%)
- Health & readiness checks
- Read-only ops/metrics routes
- CORS & request ID middleware

DO NOT modify app_v2.py - this is an additive entry point.
"""

import os
import sys
import time
import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Add parent directories to path for imports
project_root = Path(__file__).parent.parent.parent.resolve()
# Ensure project root is at the front of sys.path for core.metrics import
if str(project_root) in sys.path:
    sys.path.remove(str(project_root))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import unified settings and plugins
from services.core import settings
from services.core.shadow import get_shadow_config
from services.plugins.force_override import get_status as get_force_status
from services.plugins.guardrails import get_status as get_guardrails_status
from services.plugins.watchdog import get_status as get_watchdog_status

# Import routers
from services.api.ops_routes import router as ops_router
from services.routers.metrics import router as metrics_router
from services.routers.black_swan_async import router as black_swan_router
from services.routers.ops_control import router as ops_control_router
from services.routers.quiet_experiment import router as quiet_experiment_router
from services.routers.ops_lab import router as ops_lab_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ========================================
# Application Configuration
# ========================================

# Load configuration from environment
MAIN_PORT = settings.get_env_int("MAIN_PORT", 8011)
API_ENTRY = settings.get_env("API_ENTRY", "main")
CORS_ORIGINS = settings.get_env("CORS_ORIGINS", "http://localhost:3000").split(",")

# Force override configuration
force_config = settings.get_force_override_config()
FORCE_OVERRIDE = force_config["enabled"]
HARD_CAP_ENABLED = force_config["hard_cap_enabled"]

# Shadow traffic configuration
shadow_config = get_shadow_config()
SHADOW_PCT = shadow_config["percentage"]

# ========================================
# FastAPI Application
# ========================================

app = FastAPI(
    title="SearchForge Main",
    description="Clean entry point with Force Override, Guardrails, and Watchdog",
    version="1.0.0"
)

# ========================================
# Middlewares
# ========================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests for tracing."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # Log response
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"→ {response.status_code} ({duration_ms:.2f}ms)"
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"→ ERROR ({duration_ms:.2f}ms): {e}"
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": str(e),
                    "request_id": request_id
                }
            )


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler for unhandled exceptions."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(f"[{request_id}] Unhandled exception: {e}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": "Internal server error",
                    "detail": str(e),
                    "request_id": request_id
                }
            )


# Add middlewares in order
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ========================================
# Health & Readiness Endpoints
# ========================================

@app.get("/healthz")
async def health_check():
    """
    Fast health check - returns immediately.
    
    Returns:
        Health status with basic info
    """
    return {
        "ok": True,
        "status": "healthy",
        "service": "app_main",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


@app.get("/readyz")
async def readiness_check():
    """
    Readiness check - verifies plugins are initialized.
    
    Returns:
        Readiness status with plugin information
    """
    # Check plugin status
    force_status = get_force_status()
    guardrails_status = get_guardrails_status()
    watchdog_status = get_watchdog_status()
    shadow_config = get_shadow_config()
    
    # Check Redis/Storage status (with direct probe)
    storage_status = {"backend": "unavailable", "degraded": False}
    redis_ok = False
    try:
        from core.metrics import metrics_sink
        if metrics_sink and hasattr(metrics_sink, 'client'):
            metrics_sink.client.ping()
            redis_ok = True
            storage_status = {"backend": "redis", "degraded": False, "connected": True}
        else:
            from services.black_swan.storage import get_storage
            storage = get_storage()
            if storage.is_available():
                storage_status = {"backend": "redis", "degraded": False}
            else:
                storage_status = {"backend": "memory", "degraded": True}
    except Exception as e:
        storage_status = {"backend": "unavailable", "degraded": True, "error": str(e)}
    
    # Check Qdrant connectivity
    qdrant_status = {"ok": False, "error": "not_probed"}
    try:
        from qdrant_client import QdrantClient
        import os
        qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
        qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
        client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=2)
        collections = client.get_collections()
        qdrant_status = {
            "ok": True,
            "host": qdrant_host,
            "port": qdrant_port,
            "collections": len(collections.collections)
        }
    except Exception as e:
        qdrant_status = {"ok": False, "error": "qdrant_unreachable", "message": str(e)[:80]}
    
    # Check Black Swan runner status
    black_swan_status = {"ready": False, "idle": True}
    try:
        from services.black_swan.state import get_state
        from services.routers.black_swan_async import _current_runner, _runner_lock
        
        state_mgr = get_state()
        state = await state_mgr.get_state()
        
        async with _runner_lock:
            runner_active = _current_runner is not None
        
        if state:
            black_swan_status = {
                "ready": True,
                "idle": state.phase.value in ["complete", "error", "canceled"] if hasattr(state.phase, 'value') else True,
                "phase": state.phase.value if hasattr(state.phase, 'value') else str(state.phase)
            }
        else:
            black_swan_status = {"ready": True, "idle": True}
    except Exception as e:
        black_swan_status = {"ready": False, "error": str(e)}
    
    # Determine overall readiness (degraded mode is still ready)
    degraded = storage_status.get("degraded", False)
    ready = True  # All plugins are no-op or functional
    
    return {
        "ok": ready,
        "status": "ready" if ready else "not_ready",
        "degraded": degraded,
        "service": "app_main",
        "data_sources": {
            "qdrant": qdrant_status,
            "redis": storage_status
        },
        "plugins": {
            "force_override": {
                "enabled": force_status["force_override"],
                "status": "ok"
            },
            "hard_cap": {
                "enabled": force_status["hard_cap_enabled"],
                "status": "ok"
            },
            "guardrails": {
                "mode": guardrails_status["mode"],
                "status": guardrails_status["status"]
            },
            "watchdog": {
                "mode": watchdog_status["mode"],
                "status": watchdog_status["status"]
            },
            "shadow_traffic": {
                "enabled": shadow_config["enabled"],
                "percentage": shadow_config["percentage"],
                "status": shadow_config["status"]
            }
        },
        "storage": storage_status,
        "black_swan": black_swan_status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


# ========================================
# Root Endpoint
# ========================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "SearchForge Main API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/healthz",
            "readiness": "/readyz",
            "ops": "/ops/*",
            "force_status": "/ops/force_status",
            "verify": "/ops/verify",
            "summary": "/ops/summary",
            "control": {
                "status": "GET /ops/control/status",
                "flags": "GET/POST /ops/flags",
                "policy": "POST /ops/control/policy",
                "decisions": "GET /ops/decisions",
                "start": "POST /ops/control/start",
                "stop": "POST /ops/control/stop"
            },
            "routing": {
                "route": "POST /ops/routing/route",
                "cost": "GET /ops/routing/cost"
            },
            "black_swan": {
                "config": "GET /ops/black_swan/config",
                "start": "POST /ops/black_swan",
                "status": "GET /ops/black_swan/status",
                "report": "GET /ops/black_swan/report",
                "stop": "POST /ops/black_swan/stop"
            },
            "quiet_experiment": {
                "quiet_mode": "POST /ops/quiet_mode",
                "quiet_status": "GET /ops/quiet_mode/status",
                "start": "POST /ops/experiment/start",
                "status": "GET /ops/experiment/status",
                "stop": "POST /ops/experiment/stop"
            }
        },
        "config": {
            "force_override": FORCE_OVERRIDE,
            "hard_cap_enabled": HARD_CAP_ENABLED,
            "shadow_traffic_pct": SHADOW_PCT,
            "api_entry": API_ENTRY,
            "port": MAIN_PORT
        }
    }


# ========================================
# Mount Routers
# ========================================

# Ops routes (force_status, verify, decisions, etc.)
app.include_router(ops_router)

# Ops control routes (control flow shaping and routing)
app.include_router(ops_control_router)

# Black Swan async routes (new async implementation - mount before metrics to take precedence)
app.include_router(black_swan_router)

# Metrics routes (summary, qdrant, qa, etc.)
app.include_router(metrics_router)

# Quiet mode & ABAB experiment routes
app.include_router(quiet_experiment_router)

# Lab Dashboard routes (ABAB testing for flow shaping & routing)
app.include_router(ops_lab_router)

# ========================================
# Tuner Endpoints (Stub Implementation)
# ========================================

# In-memory tuner state (stub)
_tuner_enabled = False

@app.get("/tuner/enabled")
async def get_tuner_enabled():
    """
    Get tuner enabled status (stub implementation).
    
    Returns:
        Tuner enabled status with stub data
    """
    global _tuner_enabled
    return {
        "ok": True,
        "enabled": _tuner_enabled,
        "mode": "stub",
        "message": "Tuner stub implementation"
    }


@app.post("/tuner/toggle")
async def toggle_tuner():
    """
    Toggle tuner status (stub implementation).
    
    Returns:
        Toggle result with updated status
    """
    global _tuner_enabled
    _tuner_enabled = not _tuner_enabled
    return {
        "ok": True,
        "enabled": _tuner_enabled,
        "message": f"Tuner {'enabled' if _tuner_enabled else 'disabled'} (stub)"
    }

# ========================================
# Startup Event
# ========================================

@app.on_event("startup")
async def startup_event():
    """Log startup configuration."""
    logger.info("=" * 60)
    logger.info("SearchForge Main API - Starting Up")
    logger.info("=" * 60)
    logger.info(f"Port: {MAIN_PORT}")
    logger.info(f"API Entry: {API_ENTRY}")
    logger.info(f"CORS Origins: {CORS_ORIGINS}")
    logger.info(f"Force Override: {FORCE_OVERRIDE}")
    logger.info(f"Hard Cap Enabled: {HARD_CAP_ENABLED}")
    logger.info(f"Shadow Traffic: {SHADOW_PCT}%")
    
    # Log precedence chain preview (first 3 items)
    force_status = get_force_status()
    if force_status["force_override"]:
        logger.info(f"Force Params: {force_status['active_params']}")
    if force_status["hard_cap_enabled"]:
        logger.info(f"Hard Cap Limits: {force_status['hard_cap_limits']}")
    
    # Initialize control plugin
    try:
        from services.plugins.control import get_control_plugin
        control = get_control_plugin()
        await control.start_control_loop()
        logger.info("Control plugin initialized and started")
    except Exception as e:
        logger.warning(f"Control plugin initialization failed: {e}")
    
    # Start quiet experiment background loop
    try:
        from services.routers.quiet_experiment import start_experiment_loop
        import asyncio
        asyncio.create_task(start_experiment_loop())
        logger.info("Quiet experiment loop started")
    except Exception as e:
        logger.warning(f"Quiet experiment loop initialization failed: {e}")
    
    # Start lab experiment background loop
    try:
        from services.routers.ops_lab import start_lab_experiment_loop
        import asyncio
        asyncio.create_task(start_lab_experiment_loop())
        logger.info("Lab experiment loop started")
    except Exception as e:
        logger.warning(f"Lab experiment loop initialization failed: {e}")
    
    logger.info("=" * 60)
    logger.info("Ready to accept requests")
    logger.info("=" * 60)


# ========================================
# Main Entry Point
# ========================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting app_main on port {MAIN_PORT}")
    
    uvicorn.run(
        "app_main:app",
        host="0.0.0.0",
        port=MAIN_PORT,
        reload=False,
        log_level="info"
    )

