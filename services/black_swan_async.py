"""
Black Swan Async - API Router

FastAPI router for Black Swan async endpoints.
Provides endpoints for starting, monitoring, and retrieving test results.

Endpoints:
- POST /ops/black_swan - Start test run
- GET /ops/black_swan/status - Get current status
- GET /ops/black_swan/report - Get final report
- POST /ops/black_swan/stop - Stop current run
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import Black Swan modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from black_swan.models import RunConfig, RunMode, Phase
from black_swan.state import get_state
from black_swan.runner import BlackSwanRunner
from black_swan.reporter import get_reporter
from black_swan.storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ops", tags=["black_swan_async"])


# Request models
class StartRequest(BaseModel):
    """Request to start Black Swan test."""
    mode: str = Field(default="B", description="Test mode (A/B/C)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Optional parameter overrides")


# Global runner tracking
_current_runner: Optional[BlackSwanRunner] = None
_runner_lock = asyncio.Lock()


async def _run_test_background(config: RunConfig, run_id: Optional[str]) -> None:
    """Run test in background task."""
    global _current_runner
    runner = None
    
    try:
        # Note: config.mode is a string (due to use_enum_values=True in Pydantic)
        mode_str = config.mode if isinstance(config.mode, str) else config.mode.value
        logger.info(f"[BS:API] Background task starting (mode={mode_str})")
        
        # Create runner with explicit target URL
        target_url = "http://localhost:8080/search"  # FIQA endpoint (app.py)
        runner = BlackSwanRunner(config=config, target_url=target_url)
        
        async with _runner_lock:
            _current_runner = runner
        
        logger.info(f"[BS:API] Runner created, starting execution...")
        
        # Run test
        actual_run_id = await runner.run()
        logger.info(f"[BS:API] Test execution completed with run_id={actual_run_id}")
        
        # Generate report
        state = await runner.state.get_state()
        reporter = get_reporter()
        
        if state and state.phase == Phase.COMPLETE:
            report = reporter.build_report(
                state=state,
                config=config,
                phase_metrics=runner.phase_metrics
            )
            
            # Save report
            await reporter.save_report(report)
            logger.info(f"[BS:API] Test completed successfully: run_id={actual_run_id}")
        else:
            logger.warning(f"[BS:API] Test did not complete successfully: run_id={actual_run_id}, phase={state.phase.value if state else 'unknown'}")
    
    except Exception as e:
        logger.exception(f"[BS:API] Background test failed: {e}")
        
        # Mark state as failed if runner was created
        if runner and hasattr(runner, 'state') and runner.state:
            try:
                await runner.state.fail(error=f"Background task failed: {str(e)}")
            except Exception as state_err:
                logger.error(f"[BS:API] Failed to mark state as failed: {state_err}")
    
    finally:
        # Always clear current runner, even on exception
        async with _runner_lock:
            _current_runner = None
        logger.info(f"[BS:API] Background task cleanup completed")


@router.post("/black_swan")
async def start_black_swan(
    request: StartRequest
) -> JSONResponse:
    """
    Start Black Swan test run.
    
    Args:
        request: Start request with mode and optional params
        
    Returns:
        JSON response with run_id and status
    """
    try:
        # Check if run already in progress
        state_mgr = get_state()
        current_state = await state_mgr.get_state()
        
        if current_state and current_state.phase not in [Phase.COMPLETE, Phase.ERROR, Phase.CANCELED]:
            return JSONResponse(
                status_code=409,
                content={
                    "ok": False,
                    "error": "run_already_in_progress",
                    "message": f"Run {current_state.run_id} already in progress (phase: {current_state.phase.value})",
                    "run_id": current_state.run_id
                }
            )
        
        # Validate mode
        try:
            mode = RunMode(request.mode.upper())
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "invalid_mode",
                    "message": f"Invalid mode '{request.mode}'. Must be A, B, or C"
                }
            )
        
        # Build config from request
        config = RunConfig(mode=mode, **request.params)
        
        # Start test in background using asyncio.create_task
        # This ensures the task runs on the current event loop immediately
        asyncio.create_task(_run_test_background(config, None))
        logger.info(f"[BS:API] Background task scheduled for mode {mode.value}")
        
        # Return immediately with starting status
        storage = get_storage()
        memory_mode = not storage.is_available()
        
        return JSONResponse(
            status_code=202,
            content={
                "ok": True,
                "run_id": "starting",  # Placeholder - actual run_id will be in status endpoint
                "mode": mode.value,
                "status": "starting",
                "message": f"Black Swan test starting (mode {mode.value}) - poll /status for run_id",
                "memory_mode": memory_mode
            }
        )
    
    except Exception as e:
        logger.exception(f"[BS:API] Failed to start test: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "start_failed",
                "message": str(e)
            }
        )


@router.get("/black_swan/config")
async def get_config() -> JSONResponse:
    """
    Get Black Swan test configuration and defaults.
    
    Returns:
        JSON response with available modes, default parameters, and system info
    """
    try:
        # Get storage status
        storage = get_storage()
        storage_available = storage.is_available()
        
        # Get current state if available
        state_mgr = get_state()
        current_state = await state_mgr.get_state()
        current_config = await state_mgr.get_config() if current_state else None
        
        return JSONResponse(
            content={
                "ok": True,
                "storage": {
                    "backend": "redis" if storage_available else "memory",
                    "available": storage_available,
                    "degraded": not storage_available
                },
                "modes": {
                    "A": {
                        "name": "Mode A - Basic Load",
                        "description": "Simple load test with steady QPS",
                        "default_qps": 100,
                        "phases": ["warmup", "baseline", "trip", "recovery"]
                    },
                    "B": {
                        "name": "Mode B - Progressive Load",
                        "description": "Progressive load increase with ramp-up",
                        "default_qps": 150,
                        "phases": ["warmup", "baseline", "trip", "recovery"]
                    },
                    "C": {
                        "name": "Mode C - Spike Test",
                        "description": "Sudden spike test with high QPS burst",
                        "default_qps": 200,
                        "phases": ["warmup", "baseline", "trip", "recovery"]
                    }
                },
                "defaults": {
                    "mode": "B",
                    "qps": 100,
                    "duration_sec": 60,
                    "warmup_sec": 10,
                    "recovery_sec": 20,
                    "unique_queries": False,
                    "guardrails_enabled": True,
                    "watchdog_enabled": True,
                    "p95_threshold_ms": 1000
                },
                "current_run": {
                    "active": current_state is not None and current_state.phase.value not in ["complete", "error", "canceled"] if current_state else False,
                    "run_id": current_state.run_id if current_state else None,
                    "phase": current_state.phase.value if current_state and hasattr(current_state.phase, 'value') else None,
                    "config": current_config.dict() if current_config else None
                },
                "endpoints": {
                    "start": "POST /ops/black_swan",
                    "status": "GET /ops/black_swan/status",
                    "report": "GET /ops/black_swan/report",
                    "stop": "POST /ops/black_swan/stop",
                    "config": "GET /ops/black_swan/config"
                }
            }
        )
    
    except Exception as e:
        logger.exception(f"[BS:API] Failed to get config: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "config_failed",
                "message": str(e)
            }
        )


@router.get("/black_swan/status")
async def get_status() -> JSONResponse:
    """
    Get current Black Swan test status.
    
    Returns:
        JSON response with current state, metrics, progress, etc.
    """
    try:
        state_mgr = get_state()
        state = await state_mgr.get_state()
        
        if state is None:
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "phase": "idle",
                    "progress": 0,
                    "message": "No test run found - system idle"
                }
            )
        
        # Build status response (compatible with v2 format)
        return JSONResponse(
            content={
                "ok": True,
                "run_id": state.run_id,
                "mode": state.mode.value if hasattr(state.mode, 'value') else state.mode,
                "phase": state.phase.value if hasattr(state.phase, 'value') else state.phase,
                "progress": state.progress,
                "eta_sec": state.eta_sec,
                "message": state.message,
                
                # Metrics
                "metrics": {
                    "count": state.metrics.count,
                    "qps": state.metrics.qps,
                    "p50_ms": state.metrics.p50_ms,
                    "p95_ms": state.metrics.p95_ms,
                    "p99_ms": state.metrics.p99_ms,
                    "max_ms": state.metrics.max_ms,
                    "error_rate": state.metrics.error_rate,
                    "errors": state.metrics.errors
                },
                
                # Guardrails
                "guardrail_state": {
                    "enabled": state.guardrail_state.enabled,
                    "violated": state.guardrail_state.violated,
                    "violations": state.guardrail_state.violations,
                    "p95_threshold_ms": state.guardrail_state.p95_threshold_ms
                },
                
                # Watchdog
                "watchdog_state": {
                    "enabled": state.watchdog_state.enabled,
                    "triggered": state.watchdog_state.triggered,
                    "reason": state.watchdog_state.reason
                },
                
                # Precedence chain
                "precedence_chain": state.precedence_chain,
                
                # Timing
                "started_at": state.started_at,
                "updated_at": state.updated_at,
                "ended_at": state.ended_at,
                
                # Error (if any)
                "error": state.error
            }
        )
    
    except Exception as e:
        logger.exception(f"[BS:API] Failed to get status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "status_failed",
                "message": str(e)
            }
        )


@router.get("/black_swan/report")
async def get_report() -> JSONResponse:
    """
    Get final Black Swan test report.
    
    Returns:
        JSON response with complete test report
    """
    try:
        # Try to get report from Redis first
        storage = get_storage()
        report = storage.load_report()
        
        if report:
            return JSONResponse(
                content={
                    "ok": True,
                    "source": "redis",
                    "report": report
                }
            )
        
        # If not in Redis, check current state
        state_mgr = get_state()
        state = await state_mgr.get_state()
        
        if state is None:
            return JSONResponse(
                status_code=404,
                content={
                    "ok": False,
                    "error": "no_report_found",
                    "message": "No test report available"
                }
            )
        
        # If run is complete but no report, generate it
        if state.phase == Phase.COMPLETE:
            config = await state_mgr.get_config()
            
            # Get runner to access phase metrics
            async with _runner_lock:
                if _current_runner:
                    reporter = get_reporter()
                    report = reporter.build_report(
                        state=state,
                        config=config,
                        phase_metrics=_current_runner.phase_metrics
                    )
                    
                    # Save to Redis
                    await reporter.save_report(report)
                    
                    return JSONResponse(
                        content={
                            "ok": True,
                            "source": "generated",
                            "report": report
                        }
                    )
        
        # Run in progress or no report available
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error": "report_not_ready",
                "message": f"Report not ready (current phase: {state.phase.value})"
            }
        )
    
    except Exception as e:
        logger.exception(f"[BS:API] Failed to get report: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "report_failed",
                "message": str(e)
            }
        )


@router.post("/black_swan/stop")
async def stop_black_swan() -> JSONResponse:
    """
    Stop current Black Swan test run.
    
    Returns:
        JSON response with confirmation
    """
    try:
        # Get current runner
        async with _runner_lock:
            if _current_runner is None:
                return JSONResponse(
                    status_code=404,
                    content={
                        "ok": False,
                        "error": "no_run_in_progress",
                        "message": "No test run in progress"
                    }
                )
            
            # Stop runner
            await _current_runner.stop()
            run_id = _current_runner.run_id
        
        return JSONResponse(
            content={
                "ok": True,
                "message": f"Black Swan test {run_id} stopped",
                "run_id": run_id
            }
        )
    
    except Exception as e:
        logger.exception(f"[BS:API] Failed to stop test: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "stop_failed",
                "message": str(e)
            }
        )

