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
import json
import logging
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

# ========================================
# Environment Variables Loading (MUST BE FIRST)
# ========================================
from dotenv import load_dotenv

# Load .env file before any other initialization
load_dotenv()

# ✅ OPENAI_API_KEY is optional - code_lookup will fall back to raw results if missing
# Configure logging first before any logging calls
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    logger.info(f"✅ OPENAI_API_KEY loaded: {OPENAI_API_KEY[:6]}**** (length={len(OPENAI_API_KEY)})")
else:
    logger.warning("⚠️  OPENAI_API_KEY not set - code_lookup will use fallback mode")

# ========================================
# FastAPI and Other Imports
# ========================================
from fastapi import FastAPI, Request, Response, Header, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

# ✅ Module-level heavy resource initialization moved to clients.py singleton pattern
# Resources are now initialized lazily via lifespan event

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

# Import existing routers
from services.api.ops_routes import router as ops_router
from services.routers.metrics import router as metrics_router
from services.routers.black_swan_async import router as black_swan_router
from services.routers.ops_control import router as ops_control_router
from services.routers.quiet_experiment import router as quiet_experiment_router
from services.routers.ops_lab import router as ops_lab_router, labops_router
from services.routers.autotuner_router import router as autotuner_router

# ✅ Import new refactored routers
from services.fiqa_api.routes.search import router as search_router
from services.fiqa_api.routes.agent_code_lookup import router as code_lookup_router
from services.fiqa_api.health.ready import router as health_router

# Logging already configured above

# ========================================
# Application Configuration
# ========================================

# Load configuration from environment
MAIN_PORT = settings.get_env_int("MAIN_PORT", 8011)
API_ENTRY = settings.get_env("API_ENTRY", "main")
# ✅ Include common Vite development ports (5173, 5174) for frontend CORS
CORS_ORIGINS = settings.get_env("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:5174").split(",")

# Force override configuration
force_config = settings.get_force_override_config()
FORCE_OVERRIDE = force_config["enabled"]
HARD_CAP_ENABLED = force_config["hard_cap_enabled"]

# Shadow traffic configuration
shadow_config = get_shadow_config()
SHADOW_PCT = shadow_config["percentage"]

# ========================================
# FastAPI Application with Lifespan
# ========================================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI.
    Initializes singleton clients at startup.
    """
    # Startup: Initialize all clients
    logger.info("=" * 60)
    logger.info("SearchForge Main API - Starting Up")
    logger.info("=" * 60)
    
    from services.fiqa_api.clients import initialize_clients
    
    try:
        status = initialize_clients(skip_openai=(OPENAI_API_KEY is None))
        logger.info(f"✅ Clients initialized: {status}")
        
        if not status.get("embedding_model") or not status.get("qdrant"):
            logger.warning("⚠️  Some core clients failed to initialize - service may be degraded")
        
    except Exception as e:
        logger.error(f"❌ Client initialization failed: {e}")
    
    logger.info(f"Port: {MAIN_PORT}")
    logger.info(f"API Entry: {API_ENTRY}")
    logger.info(f"CORS Origins: {CORS_ORIGINS}")
    logger.info(f"Force Override: {FORCE_OVERRIDE}")
    logger.info(f"Hard Cap Enabled: {HARD_CAP_ENABLED}")
    logger.info(f"Shadow Traffic: {SHADOW_PCT}%")
    
    logger.info("=" * 60)
    logger.info("Ready to accept requests")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown: cleanup if needed
    logger.info("Shutting down...")


app = FastAPI(
    title="SearchForge Main",
    description="Clean entry point with Force Override, Guardrails, and Watchdog",
    version="1.0.0",
    lifespan=lifespan
)

# ========================================
# Application State (FAISS & Routing)
# ========================================

# Routing configuration state
app.state.routing_flags = {
    "enabled": True,
    "mode": "rules"  # or "cost"
}

# FAISS engine state
# ✅ Respect DISABLE_FAISS environment variable
faiss_disabled_env = os.getenv("DISABLE_FAISS", "false").lower() == "true"
app.state.faiss_engine = None
app.state.faiss_ready = False
app.state.faiss_enabled = not faiss_disabled_env  # Runtime control flag

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
    
    # Track if we've already logged deprecation warning
    _deprecation_warned = False
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        
        # Check for deprecated /ops routes and warn once
        if request.url.path.startswith("/ops/") and not LoggingMiddleware._deprecation_warned:
            logger.warning(
                f"[DEPRECATION] /ops/* routes are deprecated and will be removed soon. "
                f"Please migrate to /api/* endpoints. Called: {request.url.path}"
            )
            LoggingMiddleware._deprecation_warned = True
        
        try:
            response = await call_next(request)
            
            # Add deprecation header for /ops routes
            if request.url.path.startswith("/ops/"):
                response.headers["X-API-Deprecation"] = "This endpoint is deprecated. Please use /api/ instead."
            
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


class DeprecatedOpsMiddleware(BaseHTTPMiddleware):
    """Return 410 Gone for all /ops/* endpoints."""
    
    async def dispatch(self, request: Request, call_next):
        # Check if request path starts with /ops/
        if request.url.path.startswith("/ops/"):
            # Map to equivalent /api path
            api_path = request.url.path.replace("/ops/", "/api/", 1)
            
            return JSONResponse(
                status_code=410,
                content={
                    "ok": False,
                    "reason": "ops endpoints removed, use /api/*",
                    "deprecated_path": request.url.path,
                    "use_instead": api_path
                },
                headers={
                    "X-Deprecated": "ops-removed",
                    "Location": api_path
                }
            )
        
        return await call_next(request)


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
app.add_middleware(DeprecatedOpsMiddleware)  # Return 410 for /ops/* before routing
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS middleware - allow any localhost/127.0.0.1 origin with any port
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ========================================
# Health & Readiness Endpoints
# ✅ Moved to health/ready.py for lightweight checks
# Will be mounted via router below
# ========================================


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
        "note": "All API endpoints use /api prefix. Legacy /ops prefix has been removed (returns 410 Gone).",
        "endpoints": {
            "health": "/healthz",
            "readiness": "/readyz",
            "api": "/api/*",
            "force_status": "/api/force_status",
            "verify": "/api/verify",
            "summary": "/api/summary",
            "control": {
                "status": "GET /api/control/status",
                "flags": "GET/POST /api/flags",
                "policy": "POST /api/control/policy",
                "decisions": "GET /api/decisions",
                "start": "POST /api/control/start",
                "stop": "POST /api/control/stop"
            },
            "routing": {
                "route": "POST /api/routing/route",
                "cost": "GET /api/routing/cost"
            },
            "black_swan": {
                "config": "GET /api/black_swan/config",
                "start": "POST /api/black_swan",
                "status": "GET /api/black_swan/status",
                "report": "GET /api/black_swan/report",
                "stop": "POST /api/black_swan/stop"
            },
            "quiet_experiment": {
                "quiet_mode": "POST /api/quiet_mode",
                "quiet_status": "GET /api/quiet_mode/status",
                "start": "POST /api/experiment/start",
                "status": "GET /api/experiment/status",
                "stop": "POST /api/experiment/stop"
            },
            "agent_v2": {
                "run": "POST /api/agent/run?v=2&dry=<bool>",
                "summary": "GET /api/agent/summary?v=2",
                "history": "GET /api/agent/history?v=2"
            },
            "autotuner": {
                "status": "GET /api/autotuner/status",
                "start": "POST /api/autotuner/start",
                "stop": "POST /api/autotuner/stop",
                "recommendations": "GET /api/autotuner/recommendations"
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

# Mount all routers with both /api and /ops prefixes for compatibility
# Primary prefix: /api (used by frontend proxy)
# Legacy prefix: /ops (for backward compatibility)

from fastapi import APIRouter

def mount_with_dual_prefix(main_app: FastAPI, router: APIRouter, api_prefix: str, ops_prefix: str = None):
    """Mount a router with both /api and /ops prefixes"""
    # Mount with /api prefix (primary)
    api_router = APIRouter()
    api_router.include_router(router)
    # Replace /ops prefix with /api in the router
    if hasattr(router, 'prefix') and router.prefix:
        original_prefix = router.prefix
        new_prefix = original_prefix.replace('/ops', api_prefix, 1)
        api_router.prefix = new_prefix
    else:
        api_router.prefix = api_prefix
    main_app.include_router(api_router)
    
    # Mount with /ops prefix (legacy compatibility)
    main_app.include_router(router)

# However, for simplicity, we'll just include routers twice with modified prefixes
# First, include with /api prefix
def create_api_router(base_router: APIRouter, new_prefix: str) -> APIRouter:
    """Create a new router with modified prefix"""
    from copy import deepcopy
    # Create new router with modified prefix
    new_router = APIRouter(
        prefix=new_prefix,
        tags=base_router.tags if hasattr(base_router, 'tags') else []
    )
    # Copy all routes from base router
    for route in base_router.routes:
        new_router.routes.append(route)
    return new_router

# ✅ Mount refactored lightweight routers first
app.include_router(health_router)  # /healthz, /readyz
app.include_router(search_router)  # /search
app.include_router(code_lookup_router)  # /api/agent/code_lookup

# Mount existing routers with /api prefix (primary)
app.include_router(create_api_router(ops_router, "/api"))
app.include_router(create_api_router(ops_control_router, "/api/control"))
app.include_router(create_api_router(black_swan_router, "/api/black_swan"))
app.include_router(create_api_router(metrics_router, "/api"))
app.include_router(create_api_router(quiet_experiment_router, "/api"))
app.include_router(create_api_router(ops_lab_router, "/api/lab"))
app.include_router(create_api_router(labops_router, "/api/labops"))

# Mount AutoTuner router (already has /api/autotuner prefix)
app.include_router(autotuner_router)

# LabOps Agent V2/V3 routes - Unified /api/agent endpoint with version routing
from agents.labops.v2 import endpoints as agent_v2
from agents.labops.v3 import endpoints as agent_v3

@app.post("/api/agent/run")
async def agent_run_unified(
    v: int = Query(2, description="Agent version (2 or 3)"),
    dry: bool = Query(True, description="Dry run mode"),
    config_path: str = Query("agents/labops/plan/plan_combo.yaml")
):
    """Unified agent run endpoint - routes to v2 or v3 based on version parameter."""
    if v == 2:
        return await agent_v2.run_agent_v2(v=v, dry=dry, config_path=config_path)
    elif v == 3:
        return await agent_v3.run_agent_v3(v=v, dry=dry, config_path=config_path)
    else:
        return {"ok": False, "error": "invalid_version", "message": f"v={v} not supported, use v=2 or v=3"}

@app.get("/api/agent/summary")
async def agent_summary_unified(v: int = Query(2, description="Agent version (2 or 3)")):
    """Unified agent summary endpoint - routes to v2 or v3 based on version parameter."""
    if v == 2:
        return await agent_v2.get_agent_v2_summary(v=v)
    elif v == 3:
        return await agent_v3.get_agent_v3_summary(v=v)
    else:
        return {
            "ok": False,
            "error": "invalid_version",
            "message": f"v={v} not supported, use v=2 or v=3",
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "bullets": [f"Invalid version: {v}"],
            "generated_at": None
        }

@app.get("/api/agent/history")
async def agent_history_unified(
    v: int = Query(2, description="Agent version (2 or 3)"),
    n: int = Query(5, description="Number of recent runs")
):
    """Unified agent history endpoint - routes to v2 or v3 based on version parameter."""
    if v == 2:
        return await agent_v2.get_agent_v2_history(v=v, n=n)
    elif v == 3:
        return await agent_v3.get_agent_v3_history(v=v, n=n)
    else:
        return {"ok": False, "error": "invalid_version", "message": f"v={v} not supported, use v=2 or v=3"}

# /ops prefix removed - all traffic should use /api
# Legacy /ops routes will return 410 Gone (see catch-all handler below)

# ========================================
# Lab Report Endpoint (API prefix)
# ========================================

@app.get("/api/lab/report")
async def get_lab_report_api(mini: Optional[int] = 0, exp_id: Optional[str] = None):
    """
    Get lab experiment report (unified /api endpoint).
    
    Query params:
    - mini: If 1, return mini metrics (default: 0)
    - exp_id: Experiment ID (default: latest)
    
    Returns:
        Report data with metrics
    """
    try:
        from backend_core.lab_combo_reporter import generate_mini, get_latest_experiment_id
        
        # Determine experiment ID
        experiment_id = exp_id or get_latest_experiment_id()
        
        if not experiment_id:
            return {
                "ok": False,
                "message": "No experiment data found",
                "delta_p95_pct": 0.0,
                "delta_qps_pct": 0.0,
                "error_rate_pct": 0.0,
                "faiss_share_pct": 0.0,
                "milvus_share_pct": 0.0,
                "qdrant_share_pct": 0.0,
                "generated_at": time.time()
            }
        
        # Generate report
        text_report, json_metrics = generate_mini(experiment_id)
        
        if mini == 1:
            # Return mini JSON metrics
            return json_metrics
        else:
            # Return full text report
            return {
                "ok": json_metrics.get('ok', False),
                "report": text_report,
                "metrics": json_metrics
            }
    
    except Exception as e:
        logger.error(f"[LAB_REPORT] Failed to generate report: {e}")
        return {
            "ok": False,
            "message": f"Report generation failed: {str(e)}",
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "faiss_share_pct": 0.0,
            "milvus_share_pct": 0.0,
            "qdrant_share_pct": 0.0,
            "generated_at": time.time()
        }


@app.get("/api/metrics/mini")
async def get_mini_metrics(exp_id: str, window_sec: int = 120):
    """
    Get mini metrics for an experiment from Redis.
    
    Query params:
    - exp_id: Experiment ID
    - window_sec: Time window in seconds (default: 120)
    
    Returns:
        JSON with p95, qps, err_pct, route_share, samples
    """
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        raw_key = f"lab:exp:{exp_id}:raw"
        
        # Read raw data
        raw_data = r.lrange(raw_key, 0, -1)
        if not raw_data:
            return {
                "ok": False,
                "error": "no_data",
                "p95": 0, "qps": 0, "err_pct": 0,
                "route_share": {"milvus": 0, "faiss": 0, "qdrant": 0},
                "samples": 0
            }
        
        # Parse and filter by window
        metrics = [json.loads(m) for m in raw_data]
        now = time.time()
        windowed = [m for m in metrics if now - m["ts"] <= window_sec]
        
        if not windowed:
            return {"ok": False, "error": "no_data_in_window"}
        
        # Compute metrics
        import numpy as np
        from collections import defaultdict
        
        latencies = [m["latency_ms"] for m in windowed if m.get("ok")]
        p95 = float(np.percentile(latencies, 95)) if latencies else 0
        
        errors = sum(1 for m in windowed if not m.get("ok", True))
        err_pct = (errors / len(windowed) * 100) if windowed else 0
        
        duration = max(m["ts"] for m in windowed) - min(m["ts"] for m in windowed)
        qps = len(windowed) / duration if duration > 0 else 0
        
        routes = defaultdict(int)
        for m in windowed:
            routes[m.get("route", "unknown")] += 1
        
        route_total = sum(routes.values())
        route_share = {
            "milvus": routes["milvus"] / route_total * 100 if route_total > 0 else 0,
            "faiss": routes["faiss"] / route_total * 100 if route_total > 0 else 0,
            "qdrant": routes["qdrant"] / route_total * 100 if route_total > 0 else 0
        }
        
        return {
            "ok": True,
            "p95": round(p95, 2),
            "qps": round(qps, 2),
            "err_pct": round(err_pct, 2),
            "route_share": {k: round(v, 1) for k, v in route_share.items()},
            "samples": len(windowed)
        }
        
    except Exception as e:
        logger.error(f"[MINI_METRICS] Error: {e}")
        return {"ok": False, "error": str(e)}


@app.post("/api/lab/snapshot")
async def create_snapshot(request: Request):
    """
    Create a snapshot of current system state.
    
    Saves:
    - Selected environment variables
    - Git SHA (if available)
    - Timestamp
    
    Returns:
        Snapshot path
    """
    try:
        import subprocess
        
        # Get git SHA
        git_sha = "unknown"
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                git_sha = result.stdout.strip()[:8]
        except:
            pass
        
        # Request body (optional metadata)
        body = {}
        try:
            body = await request.json()
        except:
            pass
        
        # Selected safe environment variables
        safe_env = {
            "MAIN_PORT": os.getenv("MAIN_PORT", "8011"),
            "QDRANT_HOST": os.getenv("QDRANT_HOST", "localhost"),
            "QDRANT_PORT": os.getenv("QDRANT_PORT", "6333"),
            "LAB_REDIS_TTL": os.getenv("LAB_REDIS_TTL", "86400"),
            "DISABLE_FAISS": os.getenv("DISABLE_FAISS", "false"),
            "VECTOR_BACKEND": os.getenv("VECTOR_BACKEND", "faiss")
        }
        
        # Build snapshot
        ts = int(time.time())
        snapshot = {
            "timestamp": ts,
            "timestamp_human": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts)),
            "git_sha": git_sha,
            "env": safe_env,
            "flags": app.state.routing_flags,
            "trigger": body.get("trigger", "manual"),
            "exp_id": body.get("exp_id", "unknown")
        }
        
        # Write to reports/_snapshots/
        project_root = Path(__file__).parent.parent.parent
        snapshots_dir = project_root / "reports" / "_snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_file = snapshots_dir / f"{ts}_snapshot.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)
        
        logger.info(f"[SNAPSHOT] Created: {snapshot_file}")
        
        return {
            "ok": True,
            "path": str(snapshot_file),
            "timestamp": ts
        }
        
    except Exception as e:
        logger.error(f"[SNAPSHOT] Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


# ========================================
# Routing Flags Endpoint
# ========================================

@app.post("/api/routing/flags")
async def set_routing_flags(flags: dict):
    """
    Set routing configuration flags.
    
    Flags:
    - enabled: bool - Enable/disable smart routing
    - mode: str - Routing mode ("rules" or "cost")
    - manual_backend: str - Force backend ("qdrant", "faiss", "milvus")
    - faiss_enabled: bool - Enable/disable FAISS backend (runtime control)
    
    Returns:
        Status dict
    """
    try:
        # Update routing flags
        if "enabled" in flags:
            app.state.routing_flags["enabled"] = bool(flags["enabled"])
        if "mode" in flags:
            app.state.routing_flags["mode"] = str(flags["mode"])
        if "policy" in flags:
            # Accept "policy" as alias for "mode"
            app.state.routing_flags["mode"] = str(flags["policy"])
        if "manual_backend" in flags:
            if flags["manual_backend"] is None:
                # Clear manual override
                app.state.routing_flags.pop("manual_backend", None)
            else:
                app.state.routing_flags["manual_backend"] = str(flags["manual_backend"])
        
        # ✅ Runtime FAISS enable/disable control
        if "faiss_enabled" in flags:
            app.state.faiss_enabled = bool(flags["faiss_enabled"])
            logger.info(f"[FAISS] Runtime control: enabled={app.state.faiss_enabled}")
        
        logger.info(f"[ROUTING] Flags updated: {app.state.routing_flags}")
        
        return {
            "ok": True,
            "flags": app.state.routing_flags,
            "faiss_enabled": app.state.faiss_enabled
        }
    except Exception as e:
        logger.error(f"[ROUTING] Failed to set flags: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@app.get("/api/routing/status")
async def get_routing_status():
    """
    Get routing status.
    
    Returns:
        Routing status with FAISS and config info
    """
    return {
        "ok": True,
        "flags": app.state.routing_flags,
        "faiss": {
            "enabled": app.state.faiss_enabled,
            "ready": app.state.faiss_ready,
            "engine": app.state.faiss_engine.get_status() if app.state.faiss_engine else None
        }
    }



# ========================================
# Graph Mermaid API
# ========================================

@app.get("/api/graph/mermaid")
async def get_mermaid_graph(requestId: str = Query(..., description="Request ID to retrieve graph data")):
    """
    Transform raw graph data into a ready-to-render Mermaid.js string.
    
    This endpoint retrieves stored graph data (edges_json and files) for a given requestId
    and transforms it into a Mermaid.js graph syntax string with node details.
    
    Args:
        requestId: Request ID to retrieve stored graph data
        
    Returns:
        JSON response with mermaidText and nodeDetails
        
    Raises:
        HTTPException: 404 if requestId is invalid or data not found
        HTTPException: 422 if requestId is missing or empty
    """
    # Input validation
    if not requestId or not requestId.strip():
        raise HTTPException(
            status_code=422,
            detail="Request ID is invalid or has expired."
        )
    
    # Check cache first (optional Redis caching)
    cache_key = f"mermaid_graph:{requestId}"
    cached_result = None
    
    try:
        # Try to get from Redis cache if available
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        cached_data = redis_client.get(cache_key)
        if cached_data:
            import json
            cached_result = json.loads(cached_data)
            logger.info(f"[MERMAID_GRAPH] Cache hit for requestId {requestId}")
            return cached_result
    except Exception as e:
        logger.warning(f"[MERMAID_GRAPH] Cache check failed: {e}")
        # Continue without cache
    
    try:
        # Retrieve data from Qdrant using requestId
        from services.fiqa_api.clients import get_qdrant_client, ensure_qdrant_connection
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Ensure Qdrant connection is healthy
        if not ensure_qdrant_connection():
            raise HTTPException(
                status_code=503,
                detail="Qdrant connection unavailable"
            )
        
        qdrant_client = get_qdrant_client()
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "searchforge_codebase")
        
        # For now, since the current system doesn't store requestId in Qdrant,
        # we'll return mock data for demonstration purposes
        # TODO: Implement proper requestId-based data retrieval when the storage mechanism is updated
        
        logger.info(f"[MERMAID_GRAPH] Using mock data for requestId {requestId}")
        
        # Mock data for demonstration
        mock_edges_json = [
            {"src": "main.py::start", "dst": "controller.py::init", "type": "calls"},
            {"src": "controller.py::init", "dst": "config.py::load_settings", "type": "calls"},
            {"src": "controller.py::init", "dst": "database.py::connect", "type": "calls"},
            {"src": "config.py::load_settings", "dst": "settings.py::get_config", "type": "calls"},
            {"src": "database.py::connect", "dst": "models.py::User", "type": "imports"},
            {"src": "models.py::User", "dst": "auth.py::authenticate", "type": "calls"},
            {"src": "auth.py::authenticate", "dst": "utils.py::hash_password", "type": "calls"},
            {"src": "utils.py::hash_password", "dst": "crypto.py::sha256", "type": "calls"},
        ]
        
        mock_files = [
            {
                "path": "main.py",
                "snippet": "def start():\n    controller.init()\n    print('Application started')",
                "language": "python"
            },
            {
                "path": "controller.py", 
                "snippet": "def init():\n    config.load_settings()\n    database.connect()",
                "language": "python"
            },
            {
                "path": "config.py",
                "snippet": "def load_settings():\n    settings.get_config()\n    return True",
                "language": "python"
            }
        ]
        
        edges_json = mock_edges_json
        files = mock_files
        
        # Transform the data using the helper function
        result = convert_edges_to_mermaid_data(edges_json, files)
        
        # Store result in cache (optional Redis caching)
        try:
            import redis
            import json
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            # Cache for 15 minutes (900 seconds)
            redis_client.setex(cache_key, 900, json.dumps(result))
            logger.info(f"[MERMAID_GRAPH] Cached result for requestId {requestId}")
        except Exception as e:
            logger.warning(f"[MERMAID_GRAPH] Cache storage failed: {e}")
            # Continue without caching
        
        return result
        
    except Exception as e:
        logger.error(f"[MERMAID_GRAPH] Error processing requestId {requestId}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


def convert_edges_to_mermaid_data(edges_json: list, files: list) -> dict:
    """
    Convert edges_json and files data into Mermaid.js graph format.
    
    Args:
        edges_json: List of edge data with src, dst, type keys
        files: List of file data with path, snippet, language keys
        
    Returns:
        Dict with mermaidText and nodeDetails keys
    """
    # Security limits to prevent DoS
    MAX_NODES = 200
    MAX_EDGES = 500
    
    # Validate input limits
    if len(edges_json) > MAX_EDGES:
        raise ValueError(f"Too many edges: {len(edges_json)} > {MAX_EDGES}")
    
    # Extract all unique nodes from edges
    nodes = set()
    for edge in edges_json:
        if isinstance(edge, dict) and 'src' in edge and 'dst' in edge:
            nodes.add(edge['src'])
            nodes.add(edge['dst'])
    
    if len(nodes) > MAX_NODES:
        raise ValueError(f"Too many nodes: {len(nodes)} > {MAX_NODES}")
    
    # Build Mermaid.js graph syntax
    mermaid_lines = ["graph TD"]
    
    # Add nodes with proper escaping
    for node in sorted(nodes):
        # Escape special characters for Mermaid
        escaped_node = _escape_mermaid_identifier(node)
        # Create a short label for display
        label = _create_node_label(node)
        mermaid_lines.append(f'    {escaped_node}["{label}"]')
    
    # Add edges with proper escaping
    for edge in edges_json:
        if isinstance(edge, dict) and 'src' in edge and 'dst' in edge:
            src = _escape_mermaid_identifier(edge['src'])
            dst = _escape_mermaid_identifier(edge['dst'])
            edge_type = edge.get('type', 'calls')
            
            # Choose arrow style based on edge type
            if edge_type == 'calls':
                arrow = "-->"
            elif edge_type == 'imports':
                arrow = "-.->"
            else:
                arrow = "-->"
            
            mermaid_lines.append(f'    {src} {arrow} {dst}')
    
    # Add click callbacks for each node
    click_lines = []
    for node in sorted(nodes):
        escaped_node = _escape_mermaid_identifier(node)
        # Escape the node ID for JavaScript
        js_safe_node_id = node.replace('"', '\\"').replace("'", "\\'")
        click_lines.append(f'    click {escaped_node} call handleNodeClick("{js_safe_node_id}")')
    
    # Combine all lines
    all_lines = mermaid_lines + click_lines
    mermaid_text = ";\n".join(all_lines) + ";"
    
    # Build node details map
    node_details = {}
    for node in nodes:
        # Find corresponding file data
        file_data = _find_file_for_node(node, files)
        
        node_details[node] = {
            "code": _escape_html(file_data.get('snippet', '')) if file_data else '',
            "filePath": _escape_html(file_data.get('path', '')) if file_data else ''
        }
    
    return {
        "mermaidText": mermaid_text,
        "nodeDetails": node_details
    }


def _escape_mermaid_identifier(identifier: str) -> str:
    """Escape special characters in Mermaid identifiers."""
    # Replace problematic characters with underscores
    escaped = identifier.replace('::', '_').replace(':', '_').replace('.', '_')
    escaped = escaped.replace(' ', '_').replace('-', '_')
    # Remove any remaining special characters
    import re
    escaped = re.sub(r'[^a-zA-Z0-9_]', '_', escaped)
    return escaped


def _create_node_label(node: str) -> str:
    """Create a short, readable label for a node."""
    # Extract the function/class name from the node
    if '::' in node:
        return node.split('::')[-1]
    elif '.' in node:
        return node.split('.')[-1]
    else:
        return node.split('/')[-1] if '/' in node else node


def _find_file_for_node(node: str, files: list) -> dict:
    """Find the file data that corresponds to a node."""
    for file_data in files:
        file_path = file_data.get('path', '')
        if file_path in node or node in file_path:
            return file_data
    return {}


def _escape_html(text: str) -> str:
    """Escape HTML/JavaScript characters to prevent XSS."""
    if not text:
        return ''
    
    # Replace HTML/JS special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    text = text.replace('/', '&#x2F;')
    
    return text


# ========================================
# Embeddings API
# ========================================

class EmbeddingRequest(BaseModel):
    """Embedding request model."""
    chunks: List[Dict[str, Any]]
    batch_size: int = 64
    max_tokens: int = 512
    normalize: bool = True
    backend: Optional[str] = None  # Force backend: milvus, qdrant, or none


@app.post("/api/embeddings/encode")
async def encode_embeddings(request: EmbeddingRequest, response: Response):
    """
    Encode chunks to embeddings and optionally store in vector database.
    
    Request body:
        chunks: List of dicts with doc_id, chunk_id, text
        batch_size: Batch size for encoding (default: 64)
        max_tokens: Max tokens per text (default: 512)
        normalize: Normalize vectors (default: true)
        backend: Force backend (milvus, qdrant, none) or use VECTOR_BACKEND env
    
    Response:
        ok: bool
        count: int (number of chunks processed)
        dim: int (vector dimension)
        model: str (model name used)
        backend: str (backend used: milvus, qdrant, or none)
    
    Headers:
        X-Embed-Model: Model name used
        X-Embed-Dim: Vector dimension
    """
    start_time = time.time()
    
    try:
        from modules.embedding import embed_chunks
        from modules.embedding.sinks import auto_upsert
        
        # Validate input
        if not request.chunks:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "empty_chunks",
                    "message": "No chunks provided"
                }
            )
        
        # Validate chunk schema
        for i, chunk in enumerate(request.chunks):
            if not all(key in chunk for key in ["doc_id", "chunk_id", "text"]):
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "error": "invalid_chunk",
                        "message": f"Chunk {i} missing required fields (doc_id, chunk_id, text)"
                    }
                )
        
        # Embed chunks
        logger.info(f"[EMBEDDINGS] Processing {len(request.chunks)} chunks")
        embedded_items = embed_chunks(
            request.chunks,
            batch_size=request.batch_size,
            max_tokens=request.max_tokens,
            normalize=request.normalize
        )
        
        # Get model and dimension info
        model = embedded_items[0]["model"] if embedded_items else "unknown"
        dim = embedded_items[0]["dim"] if embedded_items else 0
        
        # Upsert to vector database (if configured)
        upsert_result = auto_upsert(
            embedded_items,
            collection="sf_chunks",
            backend=request.backend
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Set response headers
        response.headers["X-Embed-Model"] = model
        response.headers["X-Embed-Dim"] = str(dim)
        
        logger.info(
            f"[EMBEDDINGS] Encoded {len(embedded_items)} chunks in {latency_ms:.2f}ms, "
            f"backend: {upsert_result['backend']}"
        )
        
        return {
            "ok": True,
            "count": len(embedded_items),
            "dim": dim,
            "model": model,
            "backend": upsert_result["backend"],
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"[EMBEDDINGS] Error: {e}")
        
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "latency_ms": latency_ms
            }
        )



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

@app.post("/api/demo/generate-traffic")
async def generate_demo_traffic(high_qps: bool = False, duration: int = 60):
    """
    Generate demo traffic for monitoring and testing.
    
    Args:
        high_qps: If True, use high QPS mode (20 QPS vs 10 QPS)
        duration: Duration in seconds (default: 60)
    
    This endpoint triggers the demo_monitor.sh script to generate test traffic.
    """
    try:
        import subprocess
        import asyncio
        
        logger.info(f"[DEMO] Starting traffic generation (high_qps={high_qps})...")
        
        # Choose script based on QPS mode
        script_path = "/Users/nanxinli/Documents/dev/searchforge/scripts/demo_monitor_configurable.sh"
        
        if high_qps:
            mode = f"高QPS模式 (20 QPS, {duration}秒)"
            # Pass duration and QPS as arguments to the script
            process = await asyncio.create_subprocess_exec(
                "bash", script_path, str(duration), "20",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            mode = f"标准模式 (10 QPS, {duration}秒)"
            # Pass duration and QPS as arguments to the script
            process = await asyncio.create_subprocess_exec(
                "bash", script_path, str(duration), "10",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        
        # Don't wait for completion, let it run in background
        logger.info(f"[DEMO] Traffic generation started in background ({mode})")
        
        return {
            "status": "started",
            "message": f"Demo traffic generation started ({mode})",
            "mode": mode,
            "pid": process.pid
        }
        
    except Exception as e:
        logger.error(f"[DEMO] Failed to start traffic generation: {e}")
        return {
            "status": "error", 
            "message": f"Failed to start traffic generation: {str(e)}"
        }

@app.post("/api/lab/prewarm")
async def prewarm_faiss():
    """
    Prewarm FAISS engine with hot vectors from Qdrant.
    
    Loads a subset of vectors into FAISS for fast in-memory search.
    """
    try:
        logger.info("[FAISS] Starting prewarm...")
        
        # Import FAISS engine
        from services.search.faiss_engine import FaissEngine
        import numpy as np
        from qdrant_client import QdrantClient
        
        # Connect to Qdrant
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        collection_name = os.getenv("COLLECTION_NAME", "fiqa")
        
        client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=10)
        
        # Get collection info
        collection_info = client.get_collection(collection_name)
        vector_size = collection_info.config.params.vectors.size
        total_points = collection_info.points_count
        
        # Fetch a subset of vectors (50k max for speed)
        fetch_limit = min(50000, total_points)
        logger.info(f"[FAISS] Fetching {fetch_limit} vectors from Qdrant (total: {total_points})")
        
        # Scroll through points
        points, _ = client.scroll(
            collection_name=collection_name,
            limit=fetch_limit,
            with_vectors=True
        )
        
        if not points:
            return {
                "ok": False,
                "error": "no_points_found",
                "message": "No points found in Qdrant collection"
            }
        
        # Extract vectors and IDs
        embeddings = []
        ids = []
        for point in points:
            embeddings.append(point.vector)
            # Extract doc_id from payload or use point id
            doc_id = point.payload.get("doc_id", str(point.id)) if point.payload else str(point.id)
            ids.append(doc_id)
        
        embeddings = np.array(embeddings, dtype='float32')
        ids = np.array(ids)
        
        # Initialize and load FAISS
        engine = FaissEngine(dim=vector_size)
        engine.load(embeddings, ids)
        
        # Store in app state
        app.state.faiss_engine = engine
        app.state.faiss_ready = True
        
        logger.info(f"[FAISS] Prewarm complete: {len(ids)} vectors loaded")
        
        return {
            "ok": True,
            "vectors_loaded": len(ids),
            "dimension": vector_size,
            "status": engine.get_status()
        }
        
    except Exception as e:
        logger.error(f"[FAISS] Prewarm failed: {e}")
        return {
            "ok": False,
            "error": str(e)
        }



# ========================================
# Static Files Mount (Frontend)
# ========================================

# Mount frontend static files with SPA fallback
frontend_dist = project_root / "frontend" / "dist"
if frontend_dist.exists():
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    # SPA fallback - serve index.html for all routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Skip API routes
        if full_path.startswith(("api/", "ops/", "docs", "openapi.json", "health", "readyz", "reports/")):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # Serve index.html for all other routes (SPA fallback)
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            raise HTTPException(status_code=404, detail="Frontend not found")
    
    logger.info(f"✓ Frontend mounted with SPA fallback (from {frontend_dist})")
else:
    logger.warning(f"⚠ Frontend dist not found at {frontend_dist}")

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

