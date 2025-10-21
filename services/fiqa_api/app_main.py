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

# Validate OPENAI_API_KEY early
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ Missing OPENAI_API_KEY. Please check your .env file.")

# Log successful key loading (show first 6 chars only for security)
print(f"✅ OPENAI_API_KEY loaded: {OPENAI_API_KEY[:6]}**** (length={len(OPENAI_API_KEY)})")

# ========================================
# FastAPI and Other Imports
# ========================================
from fastapi import FastAPI, Request, Response, Header, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

# OpenAI client for LLM summarization (code_lookup)
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    _openai_available = True
    print(f"✅ OpenAI client initialized successfully with model: {os.getenv('CODE_LOOKUP_LLM_MODEL', 'gpt-4o-mini')}")
except Exception as e:
    _openai_client = None
    _openai_available = False
    logging.warning(f"⚠️  OpenAI client unavailable: {e}")

# LLM configuration for code_lookup
LLM_MODEL = os.getenv("CODE_LOOKUP_LLM_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_MS = int(os.getenv("CODE_LOOKUP_LLM_TIMEOUT_MS", "8000"))

# Qdrant and embedding model for code_lookup (initialize globally at startup)
_qdrant_client = None
_embedding_model = None
_code_lookup_clients_available = False

try:
    from qdrant_client import QdrantClient
    from sentence_transformers import SentenceTransformer
    
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME", "searchforge_codebase")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    
    logging.info(f"Initializing Qdrant client at {QDRANT_URL}...")
    _qdrant_client = QdrantClient(url=QDRANT_URL, timeout=60)
    
    # Verify collection exists
    collection_info = _qdrant_client.get_collection(collection_name=QDRANT_COLLECTION)
    logging.info(f"Connected to Qdrant collection '{QDRANT_COLLECTION}' with {collection_info.points_count} points")
    
    logging.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
    _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    logging.info(f"Embedding model loaded successfully")
    
    _code_lookup_clients_available = True
except Exception as e:
    logging.error(f"Failed to initialize Qdrant/embedding clients for code_lookup: {e}")
    _qdrant_client = None
    _embedding_model = None
    _code_lookup_clients_available = False

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
from services.routers.ops_lab import router as ops_lab_router, labops_router

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
# FastAPI Application
# ========================================

app = FastAPI(
    title="SearchForge Main",
    description="Clean entry point with Force Override, Guardrails, and Watchdog",
    version="1.0.0"
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

# Mount with /api prefix (primary)
app.include_router(create_api_router(ops_router, "/api"))
app.include_router(create_api_router(ops_control_router, "/api/control"))
app.include_router(create_api_router(black_swan_router, "/api/black_swan"))
app.include_router(create_api_router(metrics_router, "/api"))
app.include_router(create_api_router(quiet_experiment_router, "/api"))
app.include_router(create_api_router(ops_lab_router, "/api/lab"))
app.include_router(create_api_router(labops_router, "/api/labops"))

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
# Search Endpoint with FAISS Routing
# ========================================

class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    top_k: int = 10
    collection: str = "fiqa"
    rerank: bool = False


@app.post("/search")
async def search(request: SearchRequest, response: Response, x_lab_exp: str = Header(None), x_lab_phase: str = Header(None), x_topk: str = Header(None)):
    """
    Search endpoint with unified routing (FAISS/Qdrant/Milvus).
    
    Routes queries between FAISS, Qdrant, and Milvus based on routing flags and query characteristics.
    
    Lab experiment headers:
    - X-Lab-Exp: Experiment ID for metrics collection
    - X-Lab-Phase: Phase identifier (A/B)
    - X-TopK: Top-K value for the request
    """
    import numpy as np
    from backend_core.routing_policy import Router
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    
    # ✅ Import unified router for Milvus support
    try:
        from engines.factory import get_router
        unified_router_available = True
    except ImportError:
        logger.warning("[ROUTING] Unified router not available, using legacy routing")
        unified_router_available = False
    
    start_time = time.time()
    route_used = "qdrant"  # Default
    fallback = False
    
    # Map collection name (fiqa -> beir_fiqa_full_ta)
    collection_map = {
        "fiqa": "beir_fiqa_full_ta",
        "beir_fiqa_full_ta": "beir_fiqa_full_ta"
    }
    actual_collection = collection_map.get(request.collection, request.collection)
    
    try:
        # Get routing flags
        flags = app.state.routing_flags
        enabled = flags.get("enabled", True)
        mode = flags.get("mode", "rules")
        manual_backend = flags.get("manual_backend")
        
        # ✅ Use unified router if available (supports Milvus)
        if unified_router_available and os.getenv("VECTOR_BACKEND", "faiss") == "milvus":
            logger.info(f"[ROUTING] Using unified router with VECTOR_BACKEND=milvus")
            unified_router = get_router()
            
            # Search using unified router
            search_results, debug_info = unified_router.search(
                query=request.query,
                collection_name=actual_collection,
                top_k=request.top_k,
                force_backend=manual_backend,
                trace_id=None,
                with_fallback=True
            )
            
            route_used = debug_info.get("routed_to", "unknown")
            logger.info(f"[ROUTING] Router decision: {route_used}, results: {len(search_results)}")
            
            # Format results
            results = []
            for r in search_results:
                results.append({
                    "id": r.get("id", "unknown"),
                    "text": r.get("text", ""),
                    "score": float(r.get("score", 0.0))
                })
        
        else:
            # Legacy routing (FAISS/Qdrant only)
            # Determine routing decision
            should_use_faiss = False
            
            if manual_backend:
                # Manual override
                should_use_faiss = (manual_backend == "faiss")
                route_used = manual_backend
            elif enabled and app.state.faiss_ready and app.state.faiss_enabled:
                # Use Router to decide
                router = Router(policy=mode, topk_threshold=32)
                has_filter = False  # Could extract from request if needed
                
                decision = router.route(
                    query={"topk": request.top_k, "has_filter": has_filter},
                    faiss_load=0.0,  # Could track actual load
                    qdrant_load=0.0
                )
                
                should_use_faiss = (decision["backend"] == "faiss")
                route_used = decision["backend"]
            
            # Execute search
            results = []
            
            if should_use_faiss and app.state.faiss_ready and app.state.faiss_enabled:
                # Use FAISS
                try:
                    # Encode query
                    encoder_model = os.getenv("ENCODER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
                    encoder = SentenceTransformer(encoder_model)
                    query_vector = encoder.encode(request.query)
                    
                    # Search FAISS
                    faiss_results = app.state.faiss_engine.search(query_vector, topk=request.top_k)
                    
                    # Format results
                    for doc_id, score in faiss_results:
                        results.append({
                            "id": doc_id,
                            "text": f"Document {doc_id}",  # Could load full text from Qdrant if needed
                            "score": float(score)
                        })
                    
                    route_used = "faiss"
                    
                except Exception as e:
                    logger.warning(f"[ROUTING] FAISS search failed, falling back to Qdrant: {e}")
                    fallback = True
                    should_use_faiss = False
            
            if not should_use_faiss or fallback:
                # Use Qdrant
                qdrant_host = os.getenv("QDRANT_HOST", "localhost")
                qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
                
                client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=10)
                
                # Encode query
                encoder_model = os.getenv("ENCODER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
                encoder = SentenceTransformer(encoder_model)
                query_vector = encoder.encode(request.query).tolist()
                
                # Search Qdrant
                qdrant_results = client.search(
                    collection_name=actual_collection,
                    query_vector=query_vector,
                    limit=request.top_k
                )
                
                # Format results
                for r in qdrant_results:
                    payload = r.payload or {}
                    doc_id = payload.get("doc_id", str(r.id))
                    results.append({
                        "id": doc_id,
                        "text": payload.get("text", "")[:200],
                        "title": payload.get("title", "Unknown"),
                        "score": float(r.score) if hasattr(r, 'score') else 0.0
                    })
                
                route_used = "qdrant"
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Set route header
        response.headers["X-Search-Route"] = route_used
        
        # ✅ Lab experiment metrics collection hook
        if x_lab_exp:
            try:
                import redis
                from datetime import datetime
                redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                
                # Record to Redis: lab:exp:<id>:raw
                metric_data = {
                    "ts": start_time,
                    "latency_ms": latency_ms,
                    "ok": True,
                    "route": route_used,
                    "phase": x_lab_phase or "unknown",
                    "topk": int(x_topk) if x_topk else request.top_k,
                    "fallback": fallback
                }
                
                # ✅ Extended TTL for long-running tests (default 24h)
                lab_ttl = int(os.getenv("LAB_REDIS_TTL", "86400"))  # 24 hours
                raw_key = f"lab:exp:{x_lab_exp}:raw"
                
                redis_client.rpush(raw_key, json.dumps(metric_data))
                redis_client.expire(raw_key, lab_ttl)  # Refresh TTL on each write (keep-alive)
                
                # Every 5 seconds, trigger aggregation (simple implementation)
                # Note: For production, use a background task
                bucket_ts = int(start_time / 5) * 5
                redis_client.sadd(f"lab:exp:{x_lab_exp}:buckets", bucket_ts)
                
            except Exception as e:
                # Non-critical: Log but don't fail the request
                logger.debug(f"[LAB] Failed to record metric: {e}")
        
        return {
            "ok": True,
            "results": results,
            "latency_ms": latency_ms,
            "route": route_used,
            "fallback": fallback,
            "doc_ids": [r["id"] for r in results]
        }
        
    except Exception as e:
        logger.error(f"[SEARCH] Error: {e}")
        latency_ms = (time.time() - start_time) * 1000
        
        # Set route header even on error
        response.headers["X-Search-Route"] = route_used
        
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "latency_ms": latency_ms,
                "route": route_used
            }
        )


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
# Agent Code Lookup API
# ========================================

class CodeLookupRequest(BaseModel):
    """Request model for code lookup."""
    message: str


class CodeFile(BaseModel):
    """Individual code file result."""
    path: str
    language: str
    start_line: int
    end_line: int
    snippet: str
    why_relevant: str


class CodeLookupResponse(BaseModel):
    """Response model for code lookup."""
    agent: str
    intent: str
    query: str
    summary_md: str
    files: List[CodeFile]


@app.post("/api/agent/code_lookup", response_model=CodeLookupResponse)
async def code_lookup(request: CodeLookupRequest):
    """
    Search codebase using Qdrant vector search with LLM summarization.
    
    This endpoint provides semantic code search powered by Qdrant vector database.
    It embeds the user's query, searches for similar code snippets, and uses
    GPT-4o mini to generate a concise summary and select the most relevant files.
    
    Args:
        request: CodeLookupRequest with message field
        
    Returns:
        CodeLookupResponse with LLM-generated summary and top files
        
    Environment:
        OPENAI_API_KEY: Required for LLM summarization
        CODE_LOOKUP_LLM_MODEL: LLM model (default: gpt-4o-mini)
        CODE_LOOKUP_LLM_TIMEOUT_MS: Timeout in ms (default: 8000)
        
    Example:
        POST /api/agent/code_lookup
        {
            "message": "embedding code"
        }
    """
    # Check if Qdrant and embedding clients are initialized
    if not _code_lookup_clients_available or _qdrant_client is None or _embedding_model is None:
        raise HTTPException(
            status_code=503,
            detail="Code lookup service unavailable. Qdrant or embedding model failed to initialize."
        )
    
    try:
        # Configuration
        QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME", "searchforge_codebase")
        MAX_RESULTS = 5
        MIN_SIMILARITY = 0.4
        
        # Embed the query with error handling
        try:
            query_vector = _embedding_model.encode(request.message).tolist()
        except Exception as e:
            logger.error(f"[CODE_LOOKUP] Failed to embed query: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate query embedding: {str(e)}"
            )
        
        # Search Qdrant with error handling
        try:
            search_results = _qdrant_client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=MAX_RESULTS
            )
        except Exception as e:
            logger.error(f"[CODE_LOOKUP] Qdrant search failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Vector search failed: {str(e)}"
            )
        
        # Handle no results
        if not search_results:
            return CodeLookupResponse(
                agent="sf_agent_qdrant_llm_v0.2",
                intent="code_lookup",
                query=request.message,
                summary_md="没有找到相关代码片段。",
                files=[]
            )
        
        # Filter by similarity threshold
        filtered_results = [r for r in search_results if r.score >= MIN_SIMILARITY]
        
        if not filtered_results:
            return CodeLookupResponse(
                agent="sf_agent_qdrant_llm_v0.2",
                intent="code_lookup",
                query=request.message,
                summary_md="没有找到足够相关的代码片段。搜索结果相似度太低。",
                files=[]
            )
        
        # ========================================
        # LLM Summarization (with fallback)
        # ========================================
        
        def _clip_text(text: str, max_len: int = 400) -> str:
            """Clip text to max length and remove null characters."""
            text = text.replace("\u0000", "")
            return (text[:max_len] + "…") if len(text) > max_len else text
        
        # Prepare top-3 snippets for LLM
        top_snippets = []
        for result in filtered_results[:3]:
            payload = result.payload
            top_snippets.append({
                "path": payload.get("file_path") or payload.get("path") or "unknown",
                "snippet": _clip_text(payload.get("text") or payload.get("content") or ""),
                "score": float(result.score)
            })
        
        # Try LLM summarization
        llm_success = False
        files_output = []
        summary_md = ""
        
        if _openai_available and _openai_client:
            try:
                # System prompt for LLM
                system_prompt = (
                    "You are SearchForge Code Assistant.\n"
                    "You will ONLY return a valid JSON object with exactly these keys:\n"
                    "  summary_md: string (markdown),\n"
                    "  files: array of {path, snippet, why_relevant}\n"
                    "Rules:\n"
                    "- Base your answer ONLY on provided snippets.\n"
                    "- Select 1~2 most relevant files; add brief why_relevant.\n"
                    "- Keep summary concise and cite files in markdown.\n"
                    "- No extra keys. No code fences. Strict JSON.\n"
                )
                
                # User prompt with query and snippets
                user_prompt_data = {
                    "query": request.message,
                    "snippets": top_snippets
                }
                
                # Call OpenAI with strict JSON mode
                response = _openai_client.chat.completions.create(
                    model=LLM_MODEL,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=512,
                    timeout=LLM_TIMEOUT_MS / 1000.0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(user_prompt_data, ensure_ascii=False)}
                    ]
                )
                
                # Parse LLM response
                content = response.choices[0].message.content
                llm_data = json.loads(content)
                
                # Validate JSON shape
                if not isinstance(llm_data, dict) or "summary_md" not in llm_data or "files" not in llm_data:
                    raise ValueError("Invalid JSON shape from LLM")
                
                # Extract summary and files
                summary_md = llm_data["summary_md"]
                
                # Build files from LLM selection (limit to 3)
                for file_item in llm_data["files"][:3]:
                    # Find original result to get full metadata
                    matched_result = None
                    for result in filtered_results:
                        if result.payload.get("file_path") == file_item.get("path"):
                            matched_result = result
                            break
                    
                    if matched_result:
                        payload = matched_result.payload
                        files_output.append(CodeFile(
                            path=file_item.get("path", "unknown"),
                            language=payload.get("language", "python"),
                            start_line=payload.get("chunk_index", 0) * 50,
                            end_line=(payload.get("chunk_index", 0) + 1) * 50,
                            snippet=_clip_text(file_item.get("snippet", "")),
                            why_relevant=file_item.get("why_relevant", "Selected by LLM")
                        ))
                    else:
                        # Fallback if path not found in original results
                        files_output.append(CodeFile(
                            path=file_item.get("path", "unknown"),
                            language="python",
                            start_line=0,
                            end_line=50,
                            snippet=_clip_text(file_item.get("snippet", "")),
                            why_relevant=file_item.get("why_relevant", "Selected by LLM")
                        ))
                
                llm_success = True
                logger.info(f"[CODE_LOOKUP] LLM summarization successful for query: {request.message[:50]}")
                
            except Exception as e:
                logger.warning(f"[CODE_LOOKUP] LLM summarization failed, falling back to raw results: {e}")
                llm_success = False
        
        # ========================================
        # Fallback: Raw Top-K if LLM fails
        # ========================================
        
        if not llm_success:
            # Build fallback response from raw Qdrant results
            files_output = []
            for result in filtered_results[:3]:
                payload = result.payload
                files_output.append(CodeFile(
                    path=payload.get("file_path", "unknown"),
                    language=payload.get("language", "python"),
                    start_line=payload.get("chunk_index", 0) * 50,
                    end_line=(payload.get("chunk_index", 0) + 1) * 50,
                    snippet=_clip_text(payload.get("text", "")[:500]),
                    why_relevant=f"Top-K by vector search (score: {result.score:.2f})"
                ))
            
            # Generate simple markdown summary
            summary_md = f"LLM 不可用，展示前 {len(files_output)} 条原始匹配结果。\n\n"
            summary_md += "\n".join([f"- **{f.path}** (相似度: {filtered_results[i].score:.2f})" 
                                     for i, f in enumerate(files_output)])
        
        # Return final response
        return CodeLookupResponse(
            agent="sf_agent_qdrant_llm_v0.2",
            intent="code_lookup",
            query=request.message,
            summary_md=summary_md,
            files=files_output
        )
        
    except HTTPException:
        # Re-raise HTTPExceptions from inner handlers
        raise
    except Exception as e:
        logger.error(f"[CODE_LOOKUP] Unexpected error: {e}")
        # Raise 500 for unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during code lookup: {str(e)}"
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


@app.on_event("startup")
async def startup_event():
    """Log startup configuration."""
    logger.info("=" * 60)
    logger.info("SearchForge Main API - Starting Up")
    logger.info("=" * 60)
    logger.info(f"✅ Environment loaded from .env file")
    logger.info(f"✅ OPENAI_API_KEY: {OPENAI_API_KEY[:6]}**** (length={len(OPENAI_API_KEY)})")
    logger.info(f"✅ OpenAI Client: {'Available' if _openai_available else 'Unavailable'}")
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
    
    # Initialize control plugin (TEMPORARILY DISABLED FOR DEBUGGING)
    logger.info("⚠️ Background tasks temporarily disabled for debugging")
    # try:
    #     from services.plugins.control import get_control_plugin
    #     control = get_control_plugin()
    #     await control.start_control_loop()
    #     logger.info("Control plugin initialized and started")
    # except Exception as e:
    #     logger.warning(f"Control plugin initialization failed: {e}")
    
    # Start quiet experiment background loop (TEMPORARILY DISABLED)
    # try:
    #     from services.routers.quiet_experiment import start_experiment_loop
    #     import asyncio
    #     asyncio.create_task(start_experiment_loop())
    #     logger.info("Quiet experiment loop started")
    # except Exception as e:
    #     logger.warning(f"Quiet experiment loop initialization failed: {e}")
    
    # Start lab experiment background loop (TEMPORARILY DISABLED)
    # try:
    #     from services.routers.ops_lab import start_lab_experiment_loop
    #     import asyncio
    #     asyncio.create_task(start_lab_experiment_loop())
    #     logger.info("Lab experiment loop started")
    # except Exception as e:
    #     logger.warning(f"Lab experiment loop initialization failed: {e}")
    
    # Auto-prewarm FAISS on startup (background task)
    # ✅ TEMPORARILY DISABLED FOR STABILITY - TODO: Fix and re-enable later
    # ✅ Skip if DISABLE_FAISS=true or PREWARM_FAISS=false
    # import asyncio  # ✅ Import asyncio for create_task
    # disable_faiss = os.getenv("DISABLE_FAISS", "false").lower() == "true"
    # prewarm_faiss_enabled = os.getenv("PREWARM_FAISS", "true").lower() == "true"
    # 
    # if not disable_faiss and prewarm_faiss_enabled:
    #     async def auto_prewarm():
    #         await asyncio.sleep(5)  # Wait for app to be fully ready
    #         try:
    #             logger.info("[FAISS] Auto-prewarming in background...")
    #             await prewarm_faiss()
    #         except Exception as e:
    #             logger.warning(f"[FAISS] Auto-prewarm failed (non-critical): {e}")
    #     
    #     asyncio.create_task(auto_prewarm())
    # else:
    #     if disable_faiss:
    #         logger.info("[FAISS] Prewarm skipped: DISABLE_FAISS=true")
    #     else:
    #         logger.info("[FAISS] Prewarm skipped: PREWARM_FAISS=false")
    
    logger.info("⚠️ FAISS prewarm temporarily disabled for stability")
    
    logger.info("=" * 60)
    logger.info("Ready to accept requests")
    logger.info("=" * 60)


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

