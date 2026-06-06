"""
app_main.py - Unified Intake API entry (SearchForge lab stack when product-only off)
==================================================================================
Composed entry point with plugins, middlewares, and read-only routes.

Paid pilot / broker SaaS: set ``UNIFIED_INTAKE_PRODUCT_ONLY=1`` (see ``deployment_profile.py``).

Default port: 8000 (configurable via MAIN_PORT)
Prefix: /v3 (optional, for path-based routing)

Features:
- Force Override plugin integration
- Guardrails & Watchdog (minimal no-op implementations)
- Shadow traffic capability (default 0%)
- Health & readiness checks
- Read-only ops/metrics routes
- CORS & request ID middleware

This is the main entry point. Old entry points (app.py, app_v2.py) have been moved to _deprecated/.
"""
# [health] inspected

# ========================================
# Environment Variables Loading (MUST BE FIRST - BEFORE ANY IMPORTS)
# ========================================
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env.cloudrun first, then fall back to .env
# This MUST happen before any project imports that might import translation.py
env_cloudrun = Path(".env.cloudrun")
if env_cloudrun.exists():
    load_dotenv(env_cloudrun, override=False)
load_dotenv(override=False)

# Log environment loading for debugging
print("[env] loaded .env.cloudrun, TRANSLATION_ENABLED=", os.getenv("TRANSLATION_ENABLED"))

# Now safe to import other modules
import sys
import time
import json
import logging
import uuid
import signal
from typing import Optional, List, Dict, Any

# ✅ OPENAI_API_KEY is optional - code_lookup will fall back to raw results if missing
# Configure logging first before any logging calls
API_LOG_LEVEL = os.getenv("API_LOG_LEVEL", "info")
LOG_LEVEL = getattr(logging, API_LOG_LEVEL.upper(), logging.INFO)

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
try:
    PORT = int(os.getenv("PORT", "8000"))
except ValueError:
    PORT = 8000

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    logger.info(f"✅ OPENAI_API_KEY loaded: {OPENAI_API_KEY[:6]}**** (length={len(OPENAI_API_KEY)})")
else:
    logger.warning("⚠️  OPENAI_API_KEY not set - code_lookup will use fallback mode")

# ========================================
# FastAPI and Other Imports
# ========================================
from fastapi import FastAPI, Request, Response, Header, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import asyncio

from services.fiqa_api.settings import RUNS_PATH, ARTIFACTS_PATH, REPO_ROOT

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

ARTIFACTS_DIR = ARTIFACTS_PATH

# Import unified settings and plugins
from services.core import settings
from services.core.shadow import get_shadow_config
from services.plugins.force_override import get_status as get_force_status
from services.plugins.guardrails import get_status as get_guardrails_status
from services.plugins.watchdog import get_status as get_watchdog_status

# Import existing routers
from services.api.ops_routes import router as ops_router
from services.routers.metrics import router as metrics_router
from services.fiqa_api.routes.metrics import router as fiqa_metrics_router
from services.routers.black_swan_async import router as black_swan_router
from services.routers.ops_control import router as ops_control_router
from services.routers.quiet_experiment import router as quiet_experiment_router
from services.routers.ops_lab import router as ops_lab_router, labops_router
from services.routers.autotuner_router import router as autotuner_router

# ✅ Import new refactored routers
from services.fiqa_api.routes.search import router as search_router
from services.fiqa_api.routes.query import router as query_router
from services.fiqa_api.routes.kv_experiment import router as kv_experiment_router
from services.fiqa_api.routes.debug import router as debug_router
from services.fiqa_api.routes.agent_code_lookup import router as code_lookup_router
from services.fiqa_api.routes.code_graph import router as code_graph_router
from services.fiqa_api.routes.best import router as best_router
from services.fiqa_api.routes.health import router as qdrant_health_router
from services.fiqa_api.routes.contract_v1 import router as contract_router
from services.fiqa_api.routes.experiment import router as experiment_router
from services.fiqa_api.routes.steward import router as steward_router
from services.fiqa_api.routes.qdrant_info import router as qdrant_info_router
from services.fiqa_api.routes.mortgage_agent import router as mortgage_agent_router
from services.fiqa_api.routes.ops_copilot import router as ops_copilot_router
from services.fiqa_api.routes.ecommerce_agent import router as ecommerce_agent_router
from services.fiqa_api.routes.jobhunter import router as jobhunter_router
from services.fiqa_api.routes.inbox_triage import router as inbox_triage_router
from services.fiqa_api.routes.analytics_dashboard import router as analytics_dashboard_router
from services.fiqa_api.routes.health_monitor import router as health_monitor_router
try:
    from routes.graph_run import router as graph_router
except Exception as exc:  # pragma: no cover - optional dependency
    graph_router = None
    logger.warning("Failed to import routes.graph_run (steward graph disabled): %s", exc)
from services.fiqa_api.health.ready import router as health_router
from services.fiqa_api.deployment_profile import (
    intake_schema_epoch,
    is_unified_intake_product_only,
    log_deployment_profile_banner,
    operator_runtime_hints,
    platform_inline_route_leak_count,
    runtime_service_display_name,
)
from services.fiqa_api.security.request_identity import IntakeClientAssertionMiddleware, intake_tenant_truth
from services.fiqa_api.security.support_export_gate import support_export_auth_posture_dict
from services.fiqa_api.security.case_office_access import office_ownership_posture_dict
from services.fiqa_api.security.intake_api_gate import (
    IntakeApiPerimeterMiddleware,
    intake_api_auth_posture_dict,
    intake_api_secret_configured,
)
from services.fiqa_api.security.minimal_signed_broker_token import (
    MinimalBrokerTokenMiddleware,
    minimal_broker_token_posture_dict,
)
from services.fiqa_api.security.pilot_intake_middleware import (
    IntakeOfficeExpectationHintMiddleware,
    TriagePostRateLimitMiddleware,
)
from services.fiqa_api.security.token_scope_posture import token_scope_registry_dict

# Import NetworkX engine (graph file loaded for platform-only inline routes)
from engines.networkx_engine import NetworkXEngine

# Logging already configured above

# ========================================
# Application Configuration
# ========================================

# Load configuration from environment
# Cloud Run sets PORT env var, so we respect it if set, otherwise use MAIN_PORT
_PORT_ENV = os.getenv("PORT")
if _PORT_ENV:
    try:
        MAIN_PORT = int(_PORT_ENV)
    except ValueError:
        MAIN_PORT = settings.get_env_int("MAIN_PORT", 8000)
else:
    MAIN_PORT = settings.get_env_int("MAIN_PORT", 8000)
API_ENTRY = settings.get_env("API_ENTRY", "main")

def _parse_origins(env_val: str) -> list[str]:
    return [s.strip() for s in (env_val or "").split(",") if s.strip()]

# CORS configuration: support both ALLOWED_ORIGINS (Cloud Run) and legacy CORS_ORIGINS
_ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS")
if _ALLOWED_ORIGINS_ENV:
    # New env var for Cloud Run deployment
    CORS_ORIGINS = _parse_origins(_ALLOWED_ORIGINS_ENV)
    ALLOW_ALL_CORS = "*" in CORS_ORIGINS or _ALLOWED_ORIGINS_ENV.strip() == "*"
else:
    # Legacy env vars for backward compatibility
    ALLOW_ALL_CORS = os.getenv("ALLOW_ALL_CORS", "1") in ("1", "true", "True", "yes")
    CORS_ORIGINS = _parse_origins(os.getenv("CORS_ORIGINS", ""))

# Force override configuration
force_config = settings.get_force_override_config()
FORCE_OVERRIDE = force_config["enabled"]
HARD_CAP_ENABLED = force_config["hard_cap_enabled"]

# Shadow traffic configuration
shadow_config = get_shadow_config()
SHADOW_PCT = shadow_config["percentage"]

# ========================================
# Startup Hardening Controls
# ========================================

# Fast startup mode avoids hard-failing on slow external deps
FAST_STARTUP = os.getenv("FAST_STARTUP", "1") == "1"
# Time budget per init step (seconds)
try:
    INIT_TIMEOUT_SEC = float(os.getenv("INIT_TIMEOUT_SEC", "3"))
except Exception:
    INIT_TIMEOUT_SEC = 3.0

# Global readiness state
_READINESS: bool = False
_PHASE: str = "starting"

async def _run_with_timeout(name: str, coro):
    """Run an async init step with timeout; warn and continue on timeout/error."""
    global _PHASE
    try:
        await asyncio.wait_for(coro, timeout=INIT_TIMEOUT_SEC)
        logger.info(f"[STARTUP] {name}: OK")
        return True
    except Exception as e:
        logger.warning(f"[STARTUP] {name}: DEFERRED ({type(e).__name__}: {e})")
        _PHASE = "degraded"
        return False

# ========================================
# NetworkX Graph Engine Initialization (for code graph analysis)
# ========================================

graph_engine: NetworkXEngine = None

# Instantiate NetworkXEngine at module import with explicit graph path
try:
    _current_dir = Path(__file__).parent
    _graph_path = _current_dir.parent.parent / "codegraph.v1.json"
    if _graph_path.exists():
        graph_engine = NetworkXEngine(str(_graph_path))
        logger.info(f"[GRAPH_ENGINE] Initialized NetworkX engine from {_graph_path}")
    else:
        logger.warning(f"[GRAPH_ENGINE] Graph file not found at {_graph_path}")
except Exception as e:
    logger.warning(f"[GRAPH_ENGINE] Failed to initialize NetworkX engine: {e}")
    graph_engine = None

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
    logger.info("%s — starting", runtime_service_display_name())
    logger.info("=" * 60)
    try:
        from services.fiqa_api.db.service_record_settings import unified_intake_case_persistence_report

        _ui_posture = unified_intake_case_persistence_report()
        logger.info(
            "[STARTUP] unified_intake_case_persistence_mode=%s (db=%s prod=%s pg_primary=%s dual=%s json_writes=%s)",
            _ui_posture.get("unified_intake_case_persistence_mode"),
            _ui_posture.get("has_service_record_database_url"),
            _ui_posture.get("is_production_mode"),
            _ui_posture.get("postgres_case_persistence_primary"),
            _ui_posture.get("dual_write"),
            _ui_posture.get("json_case_writes"),
        )
    except Exception as _e:
        logger.debug("[STARTUP] unified intake persistence report skipped: %s", _e)
    
    from services.fiqa_api.clients import initialize_clients, start_embedding_warmup
    from services.fiqa_api.search import initialize_bm25

    global _READINESS, _PHASE
    _PHASE = "starting"
    
    # Initialize GPU worker pool (if WORKER_URLS is set and dependencies available)
    try:
        from services.fiqa_api.gpu_worker_client import initialize_gpu_pool
        gpu_pool = initialize_gpu_pool()
        if gpu_pool:
            logger.info("[STARTUP] GPU worker pool initialized, waiting for readiness...")
            # Wait for GPU workers to be ready (non-blocking, will degrade if timeout)
            async def _wait_gpu_ready():
                try:
                    ready = await gpu_pool.wait_ready(timeout=300.0, consecutive=3)
                    if ready:
                        logger.info("[STARTUP] GPU workers ready")
                    else:
                        logger.warning("[STARTUP] GPU workers not ready, degraded mode")
                except Exception as e:
                    logger.warning(f"[STARTUP] GPU worker wait failed: {e}, degraded mode")
            
            # Start in background (don't block startup)
            try:
                asyncio.get_running_loop().create_task(_wait_gpu_ready())
            except RuntimeError:
                pass
        else:
            logger.info("[STARTUP] GPU worker disabled (no WORKER_URLS)")
    except (ImportError, RuntimeError) as e:
        logger.info(f"[STARTUP] GPU worker client not available: {e}. Continuing without GPU worker.")
    
    # Start background embedding warmup (non-blocking)
    start_embedding_warmup()

    async def _init_clients():
        # Wrap sync function in thread to avoid blocking loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: initialize_clients(skip_openai=(OPENAI_API_KEY is None)))

    async def _init_bm25():
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, initialize_bm25)

    async def _do_startup():
        clients_ok = await _run_with_timeout("clients", _init_clients())
        bm25_ok = await _run_with_timeout("bm25", _init_bm25())
        if clients_ok and bm25_ok:
            _READINESS = True
            _PHASE = "ready"
        else:
            _READINESS = False

    # Schedule startup tasks without blocking server accept loop
    try:
        asyncio.get_running_loop().create_task(_do_startup())
    except RuntimeError:
        # Fallback if no loop (should not happen under uvicorn)
        pass
    
    # Periodic readiness check: promote phase to "ready" when EMBED_READY and vector client are ready
    async def _check_readiness_periodic():
        """Periodic check to promote phase to 'ready' when conditions are met."""
        global _READINESS, _PHASE
        while True:
            await asyncio.sleep(2)  # Check every 2 seconds
            try:
                from services.fiqa_api.clients import EMBED_READY, ensure_qdrant_connection
                
                # Check if embedding is ready and vector client is reachable
                if EMBED_READY:
                    vector_ok = ensure_qdrant_connection()
                    if vector_ok and _PHASE != "ready":
                        _READINESS = True
                        _PHASE = "ready"
                        logger.info(f"[READY] Phase promoted to 'ready' (EMBED_READY=True, vector_ok=True)")
            except Exception as e:
                logger.debug(f"[READY] Periodic check error (non-critical): {e}")
    
    # Start periodic readiness check
    try:
        asyncio.get_running_loop().create_task(_check_readiness_periodic())
    except RuntimeError:
        pass
    
    # Ensure runtime directories exist on first startup
    for label, path in (("runs", RUNS_PATH), ("artifacts", ARTIFACTS_PATH)):
        try:
            existed = path.exists()
            path.mkdir(parents=True, exist_ok=True)
            status = "ready" if existed else "created"
            logger.info("[STARTUP] %s directory %s at %s", label.upper(), status, path.resolve())
        except Exception as exc:
            logger.warning(f"[STARTUP] Failed to ensure {label} dir {path}: {exc}")

    logger.info(f"[PATHS] runs_dir={RUNS_PATH.resolve()} artifacts_dir={ARTIFACTS_PATH.resolve()}")
    
    # [health] init_health_db - Initialize health monitoring database
    try:
        from services.fiqa_api.health.health_db import init_health_db
        init_health_db()
        logger.info("[STARTUP] Health monitoring database initialized")
    except Exception as e:
        logger.warning(f"[STARTUP] Failed to initialize health monitoring database: {e}")

    logger.info(f"Port: {MAIN_PORT}")
    logger.info(f"API Entry: {API_ENTRY}")
    logger.info(f"CORS Origins: {CORS_ORIGINS}")
    logger.info(f"Force Override: {FORCE_OVERRIDE}")
    logger.info(f"Hard Cap Enabled: {HARD_CAP_ENABLED}")
    logger.info(f"Shadow Traffic: {SHADOW_PCT}%")
    
    logger.info("=" * 60)
    logger.info("Ready to accept requests")
    logger.info("=" * 60)
    
    # Immediately yield to let server start accepting requests
    yield
    
    # Shutdown: cleanup if needed
    logger.info("Shutting down...")


app = FastAPI(
    title=runtime_service_display_name(),
    description=(
        "Unified Intake broker SaaS (inbox triage, cases, workbench) when "
        "UNIFIED_INTAKE_PRODUCT_ONLY=1; legacy SearchForge lab/RAG surface otherwise."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


def _install_signal_handlers():
    """Register basic signal handlers for graceful shutdown logging."""
    def _wrap_handler(sig: int, previous):
        sig_name = signal.Signals(sig).name

        def handler(signum, frame):
            logger.info(f"[SHUTDOWN] Received signal {sig_name}; shutting down gracefully.")
            if callable(previous):
                previous(signum, frame)
        return handler

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            previous_handler = signal.getsignal(sig)
            signal.signal(sig, _wrap_handler(sig, previous_handler))
        except Exception as exc:
            logger.debug(f"Failed to install signal handler for {sig}: {exc}")


_install_signal_handlers()

# ========================================
# Static Files Mount (Reports Directory)
# ========================================

# Mount reports/ directory as static files for artifact serving
# Note: project_root is already defined above (line 67)
# Try multiple possible locations for reports directory
reports_dirs: list[Path] = []
reports_env = os.getenv("REPORTS_DIR")
if reports_env:
    reports_dirs.append(Path(reports_env).resolve())
reports_dirs.extend([
    project_root / "reports",
    project_root / "services" / "fiqa_api" / "reports",
])
reports_dir = None
for dir_candidate in reports_dirs:
    if dir_candidate.exists():
        reports_dir = dir_candidate
        break

if reports_dir:
    app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")
    logger.info(f"✓ Reports directory mounted at /reports from {reports_dir}")
else:
    logger.warning(f"⚠ Reports directory not found in any of: {reports_dirs}")

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
        except HTTPException:
            # Re-raise HTTPException so FastAPI can handle it properly
            raise
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
# Starlette: later add_middleware wraps outward and runs first on inbound.
# Register inner intake middleware first (first add_middleware = innermost).
# Inbound: RequestID → IntakeApiPerimeter → IntakeClientAssertion → MinimalBrokerToken →
# office-expectation header → triage POST rate limit → routes (CORS wraps outside these).
app.add_middleware(TriagePostRateLimitMiddleware)
app.add_middleware(IntakeOfficeExpectationHintMiddleware)
app.add_middleware(MinimalBrokerTokenMiddleware)
app.add_middleware(IntakeClientAssertionMiddleware)
app.add_middleware(IntakeApiPerimeterMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS middleware configuration
# For local dev: ALLOWED_ORIGINS="*" or ALLOW_ALL_CORS=1 (allows all origins)
# For production (Cloud Run): Set ALLOWED_ORIGINS to specific frontend URL(s), e.g.:
#   ALLOWED_ORIGINS="https://your-demo.vercel.app,https://your-demo.netlify.app"
# Legacy env vars (CORS_ORIGINS, ALLOW_ALL_CORS) are still supported for backward compatibility
# Expose custom response headers for frontend
EXPOSE_HEADERS = [
    "X-Embed-Model", "X-Backend", "X-Top-K", "X-Mode", "X-Hybrid", "X-Rerank",
    "X-Dataset", "X-Qrels", "X-Collection", "X-Search-MS", "X-Rerank-MS", "X-Total-MS",
    "X-Dim", "X-Trace-Id", "X-Request-ID",
    "X-Unified-Intake-Office-Expectation",
]
_cors_allow_origins = ["*"] if ALLOW_ALL_CORS else CORS_ORIGINS
_cors_allow_credentials = False if ALLOW_ALL_CORS else True
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins,
    allow_credentials=_cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=EXPOSE_HEADERS
)

# ========================================
# Health & Readiness Endpoints
# ✅ Moved to health/ready.py for lightweight checks
# Will be mounted via router below
# ========================================


# ========================================
# Root Endpoint
# ========================================

@app.get("/version")
async def get_version():
    """Get version information including git commit SHA."""
    from services.fiqa_api.utils.gitinfo import get_git_sha

    sha, source = get_git_sha()
    return {
        "commit": sha,
        "source": source,
        "service": runtime_service_display_name(),
        "deployment_profile": (
            "unified_intake_product_only"
            if is_unified_intake_product_only()
            else "platform_full"
        ),
    }

@app.get("/healthz")
async def healthz():
    """
    Lightweight health check endpoint for Cloud Run.
    
    Returns:
        JSON with status, service name, version, and timestamp.
        No external dependencies or database calls.
        Always returns 200 if service is running.
    """
    from services.fiqa_api.utils.gitinfo import get_git_sha
    from datetime import datetime
    
    sha, source = get_git_sha()
    version = sha if sha != "unknown" else os.getenv("GIT_SHA", "unknown")
    return {
        "status": "ok",
        "service": runtime_service_display_name(),
        "version": version,
        "time": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    if is_unified_intake_product_only():
        from services.fiqa_api.utils.gitinfo import get_git_sha

        sha, source = get_git_sha()
        return {
            "service": runtime_service_display_name(),
            "deployment_profile": "unified_intake_product_only",
            "version": "1.0.0",
            "status": "operational",
            "git": {"commit": sha, "source": source},
            "note": (
                "Unified Intake paid-pilot surface. Lab/RAG/tuner routes are not mounted. "
                "Use /health/live for liveness and /readyz for intake readiness (not /ready)."
            ),
            "endpoints": {
                "version": "/version",
                "liveness": "/health/live",
                "health_json": "/healthz",
                "health_cloud_run": "/api/healthz",
                "readiness": "/readyz",
                "health_detailed": "/health",
                "vector_ready_legacy": "/ready",
                "qdrant": "/api/health/qdrant",
                "inbox": "/api/inbox/*",
                "analytics_dashboard": "GET /api/analytics/dashboard",
                "support_manifest": "GET /api/inbox/support/deployment-manifest",
            },
        }
    return {
        "service": "SearchForge Main API (lab/dev)",
        "deployment_profile": "platform_full",
        "version": "1.0.0",
        "status": "operational",
        "note": (
            "OPTIONAL lab/RAG surface (platform_full). Set UNIFIED_INTAKE_PRODUCT_ONLY=1 for "
            "Unified Intake SaaS / paid pilot. /ready requires vectors; intake uses /readyz."
        ),
        "endpoints": {
            "liveness": "/health/live",
            "health": "/healthz",
            "health_cloud_run": "/api/healthz",
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
            },
            "code_graph": {
                "full_graph": "GET /api/codemap/full_graph",
                "stats": "GET /api/codemap/stats"
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
app.include_router(qdrant_health_router, tags=["Health"])  # /api/health/qdrant
app.include_router(qdrant_info_router)  # /api/qdrant/version.tag

# Lightweight health endpoints
@app.get("/health/live")
async def health_live():
    """Liveness probe."""
    return {"ok": True}


@app.get("/api/healthz")
async def api_healthz_cloud_run_safe():
    """
    Liveness alias for environments where top-level /healthz never reaches the app.

    Google Cloud Run's HTTP frontend returns its own HTML 404 for ``GET /healthz`` before
    the request is forwarded to the container (verified 2026-03; see sprint docs). Paths such
    as ``/health/live``, ``/readyz``, and this ``/api/healthz`` route reach the service
    normally. Use ``/health/live`` as the canonical liveness URL; this endpoint exists so
    deploy scripts and tools that insist on the name *healthz* can probe a stable path.
    """
    return await health_live()


@app.get("/health/ready")
async def health_ready():
    """Readiness probe that ensures critical routes and artifacts directory exist."""
    paths = [getattr(route, "path", "") for route in app.router.routes]
    if is_unified_intake_product_only():
        routes_loaded = any(p.startswith("/api/inbox") for p in paths)
    else:
        routes_loaded = any(p.startswith("/api/v1/experiment") for p in paths)
    artifacts_ok = ARTIFACTS_DIR.exists()
    if routes_loaded and artifacts_ok:
        return {"ok": True, "artifacts_dir": str(ARTIFACTS_DIR)}

    return JSONResponse(
        status_code=503,
        content={
            "ok": False,
            "detail": {
                "routes_loaded": routes_loaded,
                "artifacts_dir_exists": artifacts_ok
            }
        },
    )


# Health and readiness endpoints (hardened semantics)
@app.get("/health")
async def health(request: Request):
    """Health endpoint: returns phase based on EMBED_READY and vector client."""
    global _PHASE
    try:
        from services.fiqa_api.clients import EMBED_READY, ensure_qdrant_connection
        
        # Check readiness: EMBED_READY and vector client must be OK
        if EMBED_READY:
            vector_ok = ensure_qdrant_connection()
            if vector_ok and _PHASE != "ready":
                _PHASE = "ready"
        elif _PHASE == "ready":
            # If EMBED_READY becomes False, demote to degraded
            _PHASE = "degraded"
    except Exception as e:
        logger.debug(f"[HEALTH] Check error (non-critical): {e}")

    try:
        from services.fiqa_api.db.service_record_settings import unified_intake_case_persistence_report

        _persist = unified_intake_case_persistence_report()
    except Exception:
        _persist = {"unified_intake_case_persistence_mode": "UNKNOWN"}

    return {
        "ok": True,
        "phase": _PHASE,
        "unified_intake_case_persistence": _persist,
        "deployment_profile": {
            "unified_intake_product_only": is_unified_intake_product_only(),
            "platform_inline_route_leak_count": platform_inline_route_leak_count(),
            "intake_schema_epoch": intake_schema_epoch(),
            "auth_posture": support_export_auth_posture_dict(),
            "intake_perimeter": intake_api_auth_posture_dict(),
            "office_ownership": office_ownership_posture_dict(),
            "tenant_truth": intake_tenant_truth(request).as_dict(),
            "operator_runtime_hints": operator_runtime_hints(),
            "token_scope_registry": token_scope_registry_dict(),
            "minimal_broker_token": minimal_broker_token_posture_dict(),
        },
    }

@app.get("/ready")
async def ready():
    """
    Legacy full-stack readiness (Qdrant + embedding required).

    Paid-pilot intake operators should use ``GET /readyz`` (``intake_path_ready``) instead.
    """
    global _READINESS, _PHASE
    legacy_note = None
    if is_unified_intake_product_only():
        legacy_note = (
            "deprecated_for_intake_use_readyz_v1: /ready is legacy RAG/vector gate; "
            "broker intake uses /readyz (intake_path_ready)."
        )
    try:
        from services.fiqa_api.clients import EMBED_READY, ensure_qdrant_connection
        
        # Check readiness: EMBED_READY and vector client must be OK
        if EMBED_READY:
            vector_ok = ensure_qdrant_connection()
            if vector_ok:
                _READINESS = True
                if _PHASE != "ready":
                    _PHASE = "ready"
                body: dict = {"ok": True, "phase": _PHASE}
                if legacy_note:
                    body["operator_note"] = legacy_note
                return body
        
        # Not ready
        _READINESS = False
        if _PHASE == "ready":
            _PHASE = "degraded"
        detail: dict = {"ok": False, "phase": _PHASE}
        if legacy_note:
            detail["operator_note"] = legacy_note
        raise HTTPException(status_code=503, detail=detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"[READY] Check error: {e}")
        _READINESS = False
        detail = {"ok": False, "phase": _PHASE, "error": str(e)}
        if legacy_note:
            detail["operator_note"] = legacy_note
        raise HTTPException(status_code=503, detail=detail)

# Unified Intake product core + founder analytics (always mounted)
app.include_router(inbox_triage_router)  # /api/inbox/*
app.include_router(analytics_dashboard_router)  # /api/analytics/dashboard

if not is_unified_intake_product_only():
    app.include_router(debug_router)  # /debug/trace
    app.include_router(search_router)  # /search
    app.include_router(contract_router)
    app.include_router(query_router, prefix="/api")  # /api/query
    app.include_router(kv_experiment_router)  # /api/kv-experiment/run
    app.include_router(mortgage_agent_router, prefix="/api")  # /api/mortgage-agent/run
    app.include_router(ops_copilot_router, prefix="/api")  # /api/ops-copilot/system-health
    app.include_router(ecommerce_agent_router, prefix="/api")  # /api/ecommerce-agent/run
    app.include_router(jobhunter_router, prefix="/api")  # /api/jobhunter/analyze
    app.include_router(health_monitor_router)  # /api/vitals/ingest, /api/vitals/latest
    app.include_router(code_lookup_router)  # /api/agent/code_lookup
    app.include_router(code_graph_router)  # /api/codemap/*
    app.include_router(best_router)  # /api/best
    app.include_router(experiment_router, prefix="/api/experiment", tags=["experiment"])  # /api/experiment/*
    app.include_router(experiment_router, prefix="/orchestrate", tags=["orchestrate"])
    app.include_router(steward_router, prefix="/api/steward", tags=["steward"])
    if graph_router is not None:
        app.include_router(graph_router, prefix="/api/steward", tags=["steward-graph"])

    # Mount existing routers with /api prefix (primary)
    app.include_router(create_api_router(ops_router, "/api"))
    app.include_router(create_api_router(ops_control_router, "/api/control"))
    app.include_router(create_api_router(black_swan_router, "/api/black_swan"))
    app.include_router(create_api_router(metrics_router, "/api"))
    # Mount fiqa_api metrics router (trilines, kpi endpoints)
    app.include_router(fiqa_metrics_router)  # Already has /api/metrics prefix
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
        config_path: str = Query("agents/labops/plan/plan_combo.yaml"),
    ):
        """Unified agent run endpoint - routes to v2 or v3 based on version parameter."""
        if v == 2:
            return await agent_v2.run_agent_v2(v=v, dry=dry, config_path=config_path)
        if v == 3:
            return await agent_v3.run_agent_v3(v=v, dry=dry, config_path=config_path)
        return {"ok": False, "error": "invalid_version", "message": f"v={v} not supported, use v=2 or v=3"}

    @app.get("/api/agent/summary")
    async def agent_summary_unified(v: int = Query(2, description="Agent version (2 or 3)")):
        """Unified agent summary endpoint - routes to v2 or v3 based on version parameter."""
        if v == 2:
            return await agent_v2.get_agent_v2_summary(v=v)
        if v == 3:
            return await agent_v3.get_agent_v3_summary(v=v)
        return {
            "ok": False,
            "error": "invalid_version",
            "message": f"v={v} not supported, use v=2 or v=3",
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "bullets": [f"Invalid version: {v}"],
            "generated_at": None,
        }

    @app.get("/api/agent/history")
    async def agent_history_unified(
        v: int = Query(2, description="Agent version (2 or 3)"),
        n: int = Query(5, description="Number of recent runs"),
    ):
        """Unified agent history endpoint - routes to v2 or v3 based on version parameter."""
        if v == 2:
            return await agent_v2.get_agent_v2_history(v=v, n=n)
        if v == 3:
            return await agent_v3.get_agent_v3_history(v=v, n=n)
        return {"ok": False, "error": "invalid_version", "message": f"v={v} not supported, use v=2 or v=3"}

log_deployment_profile_banner(logger)

try:
    from services.fiqa_api.db.service_record_settings import is_production_mode
    from services.fiqa_api.security.support_export_gate import support_export_secret_configured

    if is_production_mode() and not support_export_secret_configured():
        logger.warning(
            "[OPERATIONAL_RISK] Production-like runtime (ENV=prod or UNIFIED_INTAKE_DB_PRIMARY_WRITES) "
            "but UNIFIED_INTAKE_SUPPORT_API_KEY is unset: GET /api/inbox/support/* is anonymously reachable "
            "when exposed to the internet. Set UNIFIED_INTAKE_SUPPORT_API_KEY for operator-only access."
        )
except Exception as exc:
    logger.debug("[STARTUP] production/support posture check skipped: %s", exc)

try:
    sk = (os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    if sk and len(sk) < 24:
        logger.warning(
            "[OPERATIONAL_RISK] UNIFIED_INTAKE_SUPPORT_API_KEY is shorter than 24 characters — "
            "prefer a long random operator secret (this is not enforced; attacks still require network access)."
        )
except Exception as exc:
    logger.debug("[STARTUP] support key length check skipped: %s", exc)

try:
    from services.fiqa_api.db.service_record_settings import is_production_mode

    if is_production_mode() and not intake_api_secret_configured():
        logger.warning(
            "[OPERATIONAL_RISK] Production-like runtime but UNIFIED_INTAKE_INTAKE_API_KEY is unset: "
            "GET/POST /api/inbox/* (except support export + WeChat callback) is anonymously reachable "
            "when exposed to the internet. Set UNIFIED_INTAKE_INTAKE_API_KEY for a coarse intake perimeter."
        )
except Exception as exc:
    logger.debug("[STARTUP] intake perimeter check skipped: %s", exc)

try:
    from services.fiqa_api.db.service_record_settings import (
        db_primary_writes_enabled,
        is_production_mode,
        service_record_database_url,
    )

    if is_production_mode() and not is_unified_intake_product_only():
        logger.warning(
            "[OPERATIONAL_RISK] Production-like runtime but UNIFIED_INTAKE_PRODUCT_ONLY is off: "
            "platform-full API surface is mounted. Set UNIFIED_INTAKE_PRODUCT_ONLY=1 for sellable pilot."
        )
    if is_production_mode() and service_record_database_url() and not db_primary_writes_enabled():
        logger.warning(
            "[OPERATIONAL_RISK] Production-like runtime with DATABASE_URL set but "
            "UNIFIED_INTAKE_DB_PRIMARY_WRITES is off: case truth may still be JSON-primary. "
            "Set UNIFIED_INTAKE_DB_PRIMARY_WRITES=1 and UNIFIED_INTAKE_JSON_CASE_WRITES=0."
        )
except Exception as exc:
    logger.debug("[STARTUP] product-only / PG-primary posture check skipped: %s", exc)

if not is_unified_intake_product_only():
    from services.fiqa_api.platform_inline_routes import register_platform_inline_routes

    register_platform_inline_routes(app, graph_engine=graph_engine)

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
        # Exclude API/static paths from SPA. Do not use prefix "health" alone — it matches
        # "healthz" and would incorrectly send /healthz through this handler if it were ever
        # matched before the real route (see health endpoint sprint docs).
        if full_path in ("healthz", "readyz") or full_path.startswith(
            ("api/", "ops/", "docs", "openapi.json", "health/", "reports/")
        ):
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
    
    MAIN_PORT = int(os.getenv("MAIN_PORT", "8000"))
    logger.info(f"Starting app_main on port {MAIN_PORT}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=MAIN_PORT,
        reload=False,
        log_level="info"
    )

