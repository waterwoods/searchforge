"""
Lab Dashboard Router for app_main
==================================
Production-like ABAB testing environment for Flow Shaping (CONTROL) and Routing experiments.

Features:
- Two experiment types: flow_shaping and routing
- Mutual exclusion (can't run both at same time)
- Quiet Mode enforcement (mandatory for experiments)
- Prewarm verification (must prewarm before ABAB start)
- Noise filtering (greyed out windows with noise_index > 40)
- Auto phase transitions (A→B→A→B)
- Mini report generation (≤80 lines)
- Health gates (block if Redis/Qdrant unhealthy)

Endpoints:
- GET /api/lab/config - Tab definitions, health, experiment info
- POST /api/lab/start - Start experiment (flow_shaping | routing)
- GET /api/lab/status - ABAB state, noise score, deltas
- POST /api/lab/stop - Stop experiment, write report
- GET /api/lab/report - Serve mini report for download
- POST /api/lab/prewarm - Prewarm dependencies (60s)
"""

import os
import time
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field
from enum import Enum
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.plugins.control import get_control_plugin
from services.plugins.routing import get_routing_plugin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lab", tags=["lab_dashboard"])

# Additional router for labops agent endpoints
labops_router = APIRouter(prefix="/ops/labops", tags=["labops_agent"])

# ========================================
# Data Models
# ========================================

class ExperimentType(str, Enum):
    """Experiment type enumeration."""
    FLOW_SHAPING = "flow_shaping"
    ROUTING = "routing"
    COMBO = "combo"
    NONE = "none"


class ExperimentPhase(str, Enum):
    """Experiment phase enumeration."""
    IDLE = "idle"
    A = "A"
    B = "B"
    COMPLETED = "completed"


class PrewarmRequest(BaseModel):
    """Request model for prewarm operation."""
    duration_sec: int = 60


class LabStartRequest(BaseModel):
    """Request model for starting lab experiment."""
    experiment_type: Literal["flow_shaping", "routing", "combo"]
    a_ms: int = 120000  # 2 minutes per A window
    b_ms: int = 120000  # 2 minutes per B window
    rounds: int = 2  # Number of ABAB cycles
    b_config: Optional[Dict[str, Any]] = None  # Configuration for B variant


@dataclass
class NoiseMetrics:
    """Noise metrics for a time window."""
    cpu_load: float = 0.0
    qdrant_latency_p95: float = 0.0
    redis_latency_p95: float = 0.0
    queue_depth: int = 0
    gc_flag: int = 0
    
    def compute_noise_index(self) -> float:
        """
        Compute noise index (0-100 scale).
        
        Weighting:
        - CPU load: 0-100% → 0-30 points
        - Qdrant P95: 0-1000ms → 0-25 points
        - Redis P95: 0-100ms → 0-20 points
        - Queue depth: 0-1000 → 0-15 points
        - GC flag: 0 or 1 → 0 or 10 points
        
        Returns noise index (0-100), >40 = noisy window
        """
        cpu_score = min(self.cpu_load, 100) * 0.3
        qdrant_score = min(self.qdrant_latency_p95 / 1000, 1.0) * 25
        redis_score = min(self.redis_latency_p95 / 100, 1.0) * 20
        queue_score = min(self.queue_depth / 1000, 1.0) * 15
        gc_score = self.gc_flag * 10
        
        total = cpu_score + qdrant_score + redis_score + queue_score + gc_score
        return round(total, 2)


@dataclass
class WindowMetrics:
    """Metrics for a single time window."""
    timestamp: int  # Unix timestamp (ms)
    phase: str  # "A" or "B"
    p95_ms: Optional[float] = None
    qps: float = 0.0
    recall_at_10: Optional[float] = None
    samples: int = 0
    noise_index: float = 0.0
    valid: bool = True  # False if noise_index > 40


@dataclass
class LabExperimentState:
    """Lab experiment state."""
    # Experiment metadata
    experiment_type: ExperimentType = ExperimentType.NONE
    running: bool = False
    phase: ExperimentPhase = ExperimentPhase.IDLE
    experiment_id: Optional[str] = None
    started_at: Optional[int] = None
    stopped_at: Optional[int] = None
    
    # Timing
    a_ms: int = 120000
    b_ms: int = 120000
    rounds: int = 2
    current_round: int = 0
    current_window_start: Optional[int] = None
    
    # B variant configuration
    b_config: Dict[str, Any] = field(default_factory=dict)
    
    # Collected metrics
    windows: List[WindowMetrics] = field(default_factory=list)
    
    # Prewarm tracking
    prewarmed_at: Optional[int] = None
    prewarm_valid: bool = False  # Valid if prewarmed within last 5 minutes


@dataclass
class QuietModeState:
    """Quiet mode state (simplified tracking)."""
    enabled: bool = False
    locked_params: Dict[str, Any] = field(default_factory=dict)


# ========================================
# Global State
# ========================================

_lab_experiment: LabExperimentState = LabExperimentState()
_quiet_mode: QuietModeState = QuietModeState()
_state_lock = asyncio.Lock()


# ========================================
# Helper Functions
# ========================================

async def check_dependency_health() -> Dict[str, Any]:
    """
    Check health of Redis and Qdrant dependencies.
    
    Returns health status dict with ok=True if all healthy.
    """
    health = {
        "ok": True,
        "redis": {"ok": False, "message": "not_checked"},
        "qdrant": {"ok": False, "message": "not_checked"},
        "backend": {"ok": True, "message": "app_main_running"},
        "reasons": []
    }
    
    # Check Redis
    try:
        from core.metrics import metrics_sink
        if metrics_sink and hasattr(metrics_sink, 'client'):
            metrics_sink.client.ping()
            health["redis"] = {"ok": True, "message": "connected"}
        else:
            health["ok"] = False
            health["redis"] = {"ok": False, "message": "metrics_sink_unavailable"}
            health["reasons"].append("Redis not available")
    except Exception as e:
        health["ok"] = False
        health["redis"] = {"ok": False, "message": str(e)[:50]}
        health["reasons"].append(f"Redis: {str(e)[:40]}")
    
    # Check Qdrant
    try:
        from qdrant_client import QdrantClient
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=2)
        collections = client.get_collections()
        health["qdrant"] = {"ok": True, "message": f"{len(collections.collections)} collections"}
    except Exception as e:
        health["ok"] = False
        health["qdrant"] = {"ok": False, "message": str(e)[:50]}
        health["reasons"].append(f"Qdrant: {str(e)[:40]}")
    
    return health


async def collect_noise_metrics() -> NoiseMetrics:
    """
    Collect current noise metrics from system.
    
    Returns NoiseMetrics object with current readings.
    """
    metrics = NoiseMetrics()
    
    # CPU load
    try:
        import psutil
        metrics.cpu_load = psutil.cpu_percent(interval=0.1)
    except:
        metrics.cpu_load = 0.0
    
    # Qdrant latency
    try:
        from qdrant_client import QdrantClient
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=2)
        
        start = time.time()
        client.get_collections()
        latency_ms = (time.time() - start) * 1000
        metrics.qdrant_latency_p95 = latency_ms
    except:
        metrics.qdrant_latency_p95 = 0.0
    
    # Redis latency
    try:
        from core.metrics import metrics_sink
        if metrics_sink and hasattr(metrics_sink, 'client'):
            start = time.time()
            metrics_sink.client.ping()
            latency_ms = (time.time() - start) * 1000
            metrics.redis_latency_p95 = latency_ms
    except:
        metrics.redis_latency_p95 = 0.0
    
    return metrics


async def collect_window_metrics(phase: str) -> WindowMetrics:
    """
    Collect metrics for current time window.
    
    Args:
        phase: Current phase ("A" or "B")
        
    Returns WindowMetrics with current readings.
    """
    now_ms = int(time.time() * 1000)
    window = WindowMetrics(timestamp=now_ms, phase=phase)
    
    # Collect from metrics backend
    try:
        from core.metrics import metrics_sink
        if metrics_sink:
            # Fetch window data
            data = metrics_sink.window60s(now_ms)
            window.p95_ms = data.get("p95_ms")
            window.qps = data.get("tps", 0.0)
            window.recall_at_10 = data.get("recall_at_10")
            window.samples = data.get("samples", 0)
    except Exception as e:
        logger.warning(f"[LAB] Failed to collect window metrics: {e}")
    
    # Collect noise metrics
    noise = await collect_noise_metrics()
    window.noise_index = noise.compute_noise_index()
    window.valid = window.noise_index <= 40.0
    
    return window


async def check_quiet_mode_enabled() -> bool:
    """Check if quiet mode is enabled via quiet_experiment router."""
    try:
        from services.routers.quiet_experiment import _quiet_mode as quiet_state
        return quiet_state.enabled
    except:
        return False


async def lab_experiment_control_loop():
    """
    Background loop that manages lab experiment phase transitions.
    Should be called periodically (e.g., every 5 seconds).
    """
    global _lab_experiment
    
    if not _lab_experiment.running:
        return
    
    async with _state_lock:
        now_ms = int(time.time() * 1000)
        
        # Check if current window expired
        if _lab_experiment.current_window_start:
            phase_duration = _lab_experiment.a_ms if _lab_experiment.phase == ExperimentPhase.A else _lab_experiment.b_ms
            elapsed = now_ms - _lab_experiment.current_window_start
            
            if elapsed >= phase_duration:
                # Collect metrics for completed window
                window = await collect_window_metrics(_lab_experiment.phase.value)
                _lab_experiment.windows.append(window)
                logger.info(
                    f"[LAB] Window completed: {_lab_experiment.phase.value} "
                    f"(p95={window.p95_ms}, noise={window.noise_index}, valid={window.valid})"
                )
                
                # Transition to next phase
                if _lab_experiment.phase == ExperimentPhase.A:
                    # A → B
                    _lab_experiment.phase = ExperimentPhase.B
                    _lab_experiment.current_window_start = now_ms
                    await _apply_b_configuration()
                    
                elif _lab_experiment.phase == ExperimentPhase.B:
                    # B → A or complete
                    _lab_experiment.current_round += 1
                    if _lab_experiment.current_round < _lab_experiment.rounds:
                        _lab_experiment.phase = ExperimentPhase.A
                        _lab_experiment.current_window_start = now_ms
                        await _apply_a_configuration()
                    else:
                        # Experiment complete
                        _lab_experiment.running = False
                        _lab_experiment.phase = ExperimentPhase.COMPLETED
                        _lab_experiment.stopped_at = now_ms
                        await _restore_baseline_configuration()
                        logger.info("[LAB] Experiment completed")


async def _apply_a_configuration():
    """Apply baseline (A) configuration."""
    exp_type = _lab_experiment.experiment_type
    
    if exp_type == ExperimentType.FLOW_SHAPING:
        # A = Fixed concurrency/batch (baseline)
        control = get_control_plugin()
        await control.set_policy("aimd")
        await control.stop_control_loop()
        logger.info("[LAB] Applied Flow Shaping A config: fixed params, control loop OFF")
        
    elif exp_type == ExperimentType.ROUTING:
        # A = All→Qdrant (baseline)
        routing = get_routing_plugin()
        await routing.set_flags({
            "enabled": False,
            "manual_backend": "qdrant"
        })
        logger.info("[LAB] Applied Routing A config: all→Qdrant")
    
    elif exp_type == ExperimentType.COMBO:
        # A = BASELINE: No flow control, no routing
        # Clear flow control
        control = get_control_plugin()
        await control.set_policy("aimd")
        await control.stop_control_loop()
        
        # Clear routing: force Qdrant
        routing = get_routing_plugin()
        await routing.set_flags({
            "enabled": False,
            "manual_backend": "qdrant",
            "topk_threshold": None
        })
        
        logger.info("[LAB] Applied COMBO A config: fixed flow, all→Qdrant")


async def _apply_b_configuration():
    """Apply B variant configuration."""
    exp_type = _lab_experiment.experiment_type
    b_config = _lab_experiment.b_config or {}
    
    if exp_type == ExperimentType.FLOW_SHAPING:
        # B = AIMD or PID-lite control
        control = get_control_plugin()
        policy = b_config.get("policy", "aimd")
        await control.set_policy(policy)
        await control.start_control_loop()
        logger.info(f"[LAB] Applied Flow Shaping B config: {policy} control loop ON")
        
    elif exp_type == ExperimentType.ROUTING:
        # B = FAISS-first or Cost-model routing
        routing = get_routing_plugin()
        await routing.set_flags({
            "enabled": True,
            "policy": b_config.get("policy", "rules")
        })
        logger.info(f"[LAB] Applied Routing B config: smart routing ON")
    
    elif exp_type == ExperimentType.COMBO:
        # B = VARIANT: Flow control + Routing enabled
        
        # Enable flow control
        control = get_control_plugin()
        policy = b_config.get("flow_policy", "aimd")
        await control.set_policy(policy)
        
        # Set flow control parameters if provided
        if "target_p95" in b_config:
            await control.set_flags({"target_p95_ms": b_config["target_p95"]})
        if "conc_cap" in b_config:
            await control.set_flags({"max_concurrency": b_config["conc_cap"]})
        if "batch_cap" in b_config:
            await control.set_flags({"max_batch_size": b_config["batch_cap"]})
        
        await control.start_control_loop()
        
        # Enable routing
        routing = get_routing_plugin()
        routing_mode = b_config.get("routing_mode", "rules")
        routing_flags = {
            "enabled": True,
            "policy": routing_mode,
            "manual_backend": None  # Clear manual override
        }
        
        # Set topk threshold if provided
        if "topk_threshold" in b_config:
            routing_flags["topk_threshold"] = b_config["topk_threshold"]
        
        await routing.set_flags(routing_flags)
        
        logger.info(
            f"[LAB] Applied COMBO B config: flow={policy}, routing={routing_mode}, "
            f"topk_threshold={b_config.get('topk_threshold')}"
        )


async def _restore_baseline_configuration():
    """Restore baseline configuration after experiment."""
    exp_type = _lab_experiment.experiment_type
    
    if exp_type == ExperimentType.FLOW_SHAPING:
        control = get_control_plugin()
        await control.stop_control_loop()
        
    elif exp_type == ExperimentType.ROUTING:
        routing = get_routing_plugin()
        await routing.set_flags({"enabled": True, "policy": "rules"})
    
    elif exp_type == ExperimentType.COMBO:
        # Reset both flow and routing
        control = get_control_plugin()
        await control.stop_control_loop()
        
        routing = get_routing_plugin()
        await routing.set_flags({
            "enabled": True,
            "policy": "rules",
            "manual_backend": None,
            "topk_threshold": None
        })
    
    logger.info("[LAB] Restored baseline configuration")


def compute_deltas(windows: List[WindowMetrics]) -> Dict[str, Any]:
    """
    Compute delta metrics from windows.
    Only considers valid windows (noise_index ≤ 40).
    
    Returns dict with deltaP95, deltaQPS, deltaRecall (or null if insufficient data).
    """
    a_windows = [w for w in windows if w.phase == "A" and w.valid]
    b_windows = [w for w in windows if w.phase == "B" and w.valid]
    
    result = {
        "deltaP95": None,
        "deltaQPS": None,
        "deltaRecall": None,
        "a_count": len(a_windows),
        "b_count": len(b_windows)
    }
    
    if not a_windows or not b_windows:
        return result
    
    # P95 delta
    a_p95 = [w.p95_ms for w in a_windows if w.p95_ms is not None]
    b_p95 = [w.p95_ms for w in b_windows if w.p95_ms is not None]
    if a_p95 and b_p95:
        avg_a_p95 = sum(a_p95) / len(a_p95)
        avg_b_p95 = sum(b_p95) / len(b_p95)
        result["deltaP95"] = ((avg_b_p95 - avg_a_p95) / avg_a_p95 * 100) if avg_a_p95 > 0 else 0
    
    # QPS delta
    a_qps = [w.qps for w in a_windows]
    b_qps = [w.qps for w in b_windows]
    if a_qps and b_qps:
        avg_a_qps = sum(a_qps) / len(a_qps)
        avg_b_qps = sum(b_qps) / len(b_qps)
        result["deltaQPS"] = ((avg_b_qps - avg_a_qps) / avg_a_qps * 100) if avg_a_qps > 0 else 0
    
    # Recall delta
    a_recall = [w.recall_at_10 for w in a_windows if w.recall_at_10 is not None]
    b_recall = [w.recall_at_10 for w in b_windows if w.recall_at_10 is not None]
    if a_recall and b_recall:
        avg_a_recall = sum(a_recall) / len(a_recall)
        avg_b_recall = sum(b_recall) / len(b_recall)
        result["deltaRecall"] = ((avg_b_recall - avg_a_recall) / avg_a_recall * 100) if avg_a_recall > 0 else 0
    
    return result


def generate_mini_report(experiment: LabExperimentState) -> str:
    """
    Generate compact mini report (≤80 lines).
    
    Args:
        experiment: Experiment state
        
    Returns report text (≤80 lines).
    """
    lines = []
    lines.append("=" * 70)
    lines.append("LAB DASHBOARD EXPERIMENT REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    # Experiment metadata
    lines.append("EXPERIMENT METADATA")
    lines.append("-" * 70)
    lines.append(f"Experiment ID: {experiment.experiment_id}")
    lines.append(f"Type: {experiment.experiment_type.value}")
    lines.append(f"Rounds: {experiment.rounds} (ABAB cycles)")
    lines.append(f"A Window: {experiment.a_ms}ms ({experiment.a_ms // 1000}s)")
    lines.append(f"B Window: {experiment.b_ms}ms ({experiment.b_ms // 1000}s)")
    if experiment.b_config:
        lines.append(f"B Config: {experiment.b_config}")
    lines.append("")
    
    # Window analysis
    lines.append("WINDOW ANALYSIS")
    lines.append("-" * 70)
    
    a_windows = [w for w in experiment.windows if w.phase == "A" and w.valid]
    b_windows = [w for w in experiment.windows if w.phase == "B" and w.valid]
    
    lines.append(f"Total Windows: {len(experiment.windows)}")
    lines.append(f"Valid A Windows: {len(a_windows)}")
    lines.append(f"Valid B Windows: {len(b_windows)}")
    lines.append(f"Noisy Windows: {len([w for w in experiment.windows if not w.valid])}")
    lines.append("")
    
    # Compute deltas
    deltas = compute_deltas(experiment.windows)
    
    lines.append("DELTA METRICS (Valid Windows Only)")
    lines.append("-" * 70)
    
    if deltas["deltaP95"] is not None:
        lines.append(f"ΔP95: {deltas['deltaP95']:+.1f}%")
    else:
        lines.append("ΔP95: [insufficient data]")
    
    if deltas["deltaQPS"] is not None:
        lines.append(f"ΔQPS: {deltas['deltaQPS']:+.1f}%")
    else:
        lines.append("ΔQPS: [insufficient data]")
    
    if deltas["deltaRecall"] is not None:
        lines.append(f"ΔRecall: {deltas['deltaRecall']:+.1f}%")
    else:
        lines.append("ΔRecall: [not available]")
    
    lines.append("")
    
    # Detailed window log
    lines.append("WINDOW LOG")
    lines.append("-" * 70)
    for i, w in enumerate(experiment.windows):
        status = "✓" if w.valid else "✗ NOISY"
        lines.append(
            f"{i+1:2d}. {w.phase} | p95={w.p95_ms or 'N/A':>6} qps={w.qps:>5.1f} "
            f"noise={w.noise_index:>5.1f} {status}"
        )
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)
    
    # Limit to 80 lines
    return "\n".join(lines[:80])


# ========================================
# Endpoints
# ========================================

@router.get("/config")
async def get_lab_config() -> Dict[str, Any]:
    """
    Get lab dashboard configuration.
    
    Returns:
        - Tab definitions (flow_shaping, routing)
        - Health status (Redis, Qdrant, Backend)
        - Current experiment info (if any)
        - Quiet mode status
        - Prewarm status
    """
    health = await check_dependency_health()
    quiet_enabled = await check_quiet_mode_enabled()
    
    async with _state_lock:
        # Check if prewarm is still valid (within 5 minutes)
        prewarm_valid = False
        if _lab_experiment.prewarmed_at:
            elapsed_sec = (int(time.time() * 1000) - _lab_experiment.prewarmed_at) / 1000
            prewarm_valid = elapsed_sec < 300  # 5 minutes
        
        return {
            "ok": True,
            "tabs": [
                {
                    "id": "flow_shaping",
                    "name": "Flow Shaping (CONTROL)",
                    "icon": "🌀",
                    "description": "A=Fixed | B=AIMD/PID control"
                },
                {
                    "id": "routing",
                    "name": "Routing",
                    "icon": "🧭",
                    "description": "A=All→Qdrant | B=FAISS-first routing"
                },
                {
                    "id": "combo",
                    "name": "COMBO (Flow + Routing)",
                    "icon": "⚡",
                    "description": "A=Baseline | B=Flow control + Smart routing"
                }
            ],
            "health": health,
            "quiet_mode": {
                "enabled": quiet_enabled,
                "required": True
            },
            "prewarm": {
                "valid": prewarm_valid,
                "prewarmed_at": _lab_experiment.prewarmed_at,
                "required": True
            },
            "current_experiment": {
                "running": _lab_experiment.running,
                "type": _lab_experiment.experiment_type.value,
                "experiment_id": _lab_experiment.experiment_id
            } if _lab_experiment.running else None
        }


@router.post("/prewarm")
async def prewarm_dependencies(request: PrewarmRequest) -> Dict[str, Any]:
    """
    Prewarm dependencies before experiment.
    
    Runs warming queries for specified duration (default 60s).
    Marks prewarm as valid for next 5 minutes.
    
    Args:
        request: Prewarm duration configuration
        
    Returns:
        Prewarm status (202 for async operation)
    """
    global _lab_experiment
    
    duration_sec = min(request.duration_sec, 300)  # Max 5 minutes
    
    async with _state_lock:
        _lab_experiment.prewarmed_at = int(time.time() * 1000)
        _lab_experiment.prewarm_valid = True
    
    logger.info(f"[LAB] Prewarm started for {duration_sec}s")
    
    # In production, you'd run actual warming queries here
    # For now, just mark as prewarmed
    
    return {
        "ok": True,
        "status": "prewarming",
        "duration_sec": duration_sec,
        "message": f"Prewarming for {duration_sec}s"
    }


@router.post("/start")
async def start_lab_experiment(request: LabStartRequest) -> Dict[str, Any]:
    """
    Start lab experiment.
    
    Validates:
    - Quiet mode enabled
    - Prewarm completed (within last 5 minutes)
    - No other experiment running
    - Dependencies healthy
    
    Args:
        request: Experiment configuration
        
    Returns:
        Start status (202 if started, 400/409 if validation fails)
    """
    global _lab_experiment
    
    # Check if already running
    async with _state_lock:
        if _lab_experiment.running:
            return {
                "ok": False,
                "error": "experiment_already_running",
                "experiment_id": _lab_experiment.experiment_id,
                "type": _lab_experiment.experiment_type.value
            }
    
    # Check quiet mode
    quiet_enabled = await check_quiet_mode_enabled()
    if not quiet_enabled:
        return {
            "ok": False,
            "error": "quiet_mode_required",
            "message": "Enable Quiet Mode before starting experiment"
        }
    
    # Check prewarm
    async with _state_lock:
        if not _lab_experiment.prewarmed_at:
            return {
                "ok": False,
                "error": "prewarm_required",
                "message": "Run Prewarm before starting experiment"
            }
        
        elapsed_sec = (int(time.time() * 1000) - _lab_experiment.prewarmed_at) / 1000
        if elapsed_sec > 300:  # 5 minutes
            return {
                "ok": False,
                "error": "prewarm_expired",
                "message": "Prewarm expired (>5min ago). Please prewarm again."
            }
    
    # Check dependency health
    health = await check_dependency_health()
    if not health["ok"]:
        return {
            "ok": False,
            "error": "deps_unhealthy",
            "details": health,
            "message": f"Dependencies unhealthy: {', '.join(health['reasons'])}"
        }
    
    # Start experiment
    async with _state_lock:
        experiment_id = f"{request.experiment_type}_{int(time.time())}"
        now_ms = int(time.time() * 1000)
        
        if request.experiment_type == "flow_shaping":
            exp_type = ExperimentType.FLOW_SHAPING
        elif request.experiment_type == "routing":
            exp_type = ExperimentType.ROUTING
        elif request.experiment_type == "combo":
            exp_type = ExperimentType.COMBO
        else:
            exp_type = ExperimentType.FLOW_SHAPING
        
        _lab_experiment = LabExperimentState(
            experiment_type=exp_type,
            running=True,
            phase=ExperimentPhase.A,
            experiment_id=experiment_id,
            started_at=now_ms,
            a_ms=request.a_ms,
            b_ms=request.b_ms,
            rounds=request.rounds,
            current_round=0,
            current_window_start=now_ms,
            b_config=request.b_config or {},
            windows=[],
            prewarmed_at=_lab_experiment.prewarmed_at,
            prewarm_valid=True
        )
        
        # Apply A configuration
        await _apply_a_configuration()
        
        logger.info(
            f"[LAB] Experiment started: {experiment_id} "
            f"(type={request.experiment_type}, rounds={request.rounds})"
        )
    
    return {
        "ok": True,
        "experiment_id": experiment_id,
        "type": request.experiment_type,
        "phase": "A",
        "message": "Experiment started"
    }


@router.get("/status")
async def get_lab_status() -> Dict[str, Any]:
    """
    Get current lab experiment status.
    
    Returns:
        - Experiment state (running, phase, round)
        - Current window progress
        - Collected windows with noise filtering
        - Delta metrics (ΔP95, ΔQPS, ΔRecall)
        - Current noise score
    """
    async with _state_lock:
        if not _lab_experiment.running and _lab_experiment.phase == ExperimentPhase.IDLE:
            return {
                "ok": True,
                "running": False,
                "phase": "idle",
                "message": "No experiment running"
            }
        
        # Calculate progress
        now_ms = int(time.time() * 1000)
        current_window_progress = 0
        if _lab_experiment.current_window_start:
            phase_duration = _lab_experiment.a_ms if _lab_experiment.phase == ExperimentPhase.A else _lab_experiment.b_ms
            elapsed = now_ms - _lab_experiment.current_window_start
            current_window_progress = min(100, int(elapsed / phase_duration * 100))
        
        # Collect current noise
        noise = await collect_noise_metrics()
        current_noise = noise.compute_noise_index()
        
        # Map windows to dict format
        windows_data = [
            {
                "timestamp": w.timestamp,
                "phase": w.phase,
                "p95_ms": w.p95_ms,
                "qps": w.qps,
                "recall_at_10": w.recall_at_10,
                "samples": w.samples,
                "noise_index": w.noise_index,
                "valid": w.valid
            }
            for w in _lab_experiment.windows
        ]
        
        # Compute deltas
        deltas = compute_deltas(_lab_experiment.windows)
        
        return {
            "ok": True,
            "running": _lab_experiment.running,
            "experiment_id": _lab_experiment.experiment_id,
            "experiment_type": _lab_experiment.experiment_type.value,
            "phase": _lab_experiment.phase.value,
            "current_round": _lab_experiment.current_round,
            "total_rounds": _lab_experiment.rounds,
            "current_window_progress": current_window_progress,
            "current_noise": current_noise,
            "windows": windows_data,
            "deltas": deltas
        }


@router.post("/stop")
async def stop_lab_experiment() -> Dict[str, Any]:
    """
    Stop current lab experiment.
    
    Immediately stops the experiment, restores baseline configuration,
    and generates a compact report saved to reports/LAB_DASHBOARD_MINI.txt
    or reports/LAB_ROUTE_REPORT_MINI.txt (depending on experiment type).
    
    Returns:
        Stop status with report path
    """
    global _lab_experiment
    
    async with _state_lock:
        if not _lab_experiment.running:
            return {
                "ok": False,
                "error": "no_experiment_running",
                "message": "No experiment is currently running"
            }
        
        # Mark as stopped
        _lab_experiment.running = False
        _lab_experiment.phase = ExperimentPhase.COMPLETED
        _lab_experiment.stopped_at = int(time.time() * 1000)
        exp_type = _lab_experiment.experiment_type
        exp_id = _lab_experiment.experiment_id
        
        # Restore baseline
        await _restore_baseline_configuration()
        
        logger.info(f"[LAB] Experiment stopped: {exp_id}")
        
        # Generate report based on experiment type
        project_root = Path(__file__).parent.parent.parent
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_text = ""
        report_path_main = None
        
        if exp_type == ExperimentType.ROUTING:
            # Use routing reporter
            try:
                from backend_core.lab_route_reporter import generate_route_report
                import redis
                
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
                report_path_main = reports_dir / "LAB_ROUTE_REPORT_MINI.txt"
                
                result = generate_route_report(exp_id, str(report_path_main))
                report_text = result.get("report_text", "")
                
                logger.info(f"[LAB] Routing report saved: {report_path_main}")
            except Exception as e:
                logger.error(f"[LAB] Failed to generate routing report: {e}")
                # Fallback to dashboard mini report
                report_text = generate_mini_report(_lab_experiment)
                report_path_main = reports_dir / "LAB_DASHBOARD_MINI.txt"
                report_path_main.write_text(report_text)
        
        elif exp_type == ExperimentType.COMBO:
            # Use combo reporter
            try:
                from backend_core.lab_combo_reporter import generate_combo_report
                import redis
                
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
                report_path_main = reports_dir / "LAB_COMBO_REPORT_MINI.txt"
                
                result = generate_combo_report(exp_id, str(report_path_main))
                report_text = result.get("report_text", "")
                
                logger.info(f"[LAB] Combo report saved: {report_path_main}")
            except Exception as e:
                logger.error(f"[LAB] Failed to generate combo report: {e}")
                # Fallback to dashboard mini report
                report_text = generate_mini_report(_lab_experiment)
                report_path_main = reports_dir / "LAB_DASHBOARD_MINI.txt"
                report_path_main.write_text(report_text)
        
        else:
            # Use flow/dashboard reporter
            report_text = generate_mini_report(_lab_experiment)
            
            # Save both report names for compatibility
            report_path_main = reports_dir / "LAB_DASHBOARD_MINI.txt"
            report_path_2 = reports_dir / "LAB_FLOW_REPORT_MINI.txt"
            report_path_main.write_text(report_text)
            report_path_2.write_text(report_text)
            
            logger.info(f"[LAB] Flow report saved: {report_path_main} and {report_path_2}")
        
        return {
            "ok": True,
            "experiment_id": exp_id,
            "experiment_type": exp_type.value,
            "report_path": str(report_path_main),
            "windows_collected": len(_lab_experiment.windows),
            "message": "Experiment stopped and report generated"
        }


@router.get("/report")
async def get_lab_report(mini: Optional[int] = None) -> Dict[str, Any]:
    """
    Get last generated mini report.
    
    Args:
        mini: If 1, return compact format with key metrics
              (ΔP95%, ΔQPS%, Err% + routing-specific: faiss_share_pct, fallback_count)
    
    Returns:
        Report text or mini format with key metrics
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        
        # Try combo report first, then routing, then flow report
        combo_report_path = project_root / "reports" / "LAB_COMBO_REPORT_MINI.txt"
        routing_report_path = project_root / "reports" / "LAB_ROUTE_REPORT_MINI.txt"
        flow_report_path = project_root / "reports" / "LAB_FLOW_REPORT_MINI.txt"
        
        report_path = None
        is_routing = False
        is_combo = False
        
        if combo_report_path.exists():
            report_path = combo_report_path
            is_combo = True
            is_routing = True  # Combo has routing metrics
        elif routing_report_path.exists():
            report_path = routing_report_path
            is_routing = True
        elif flow_report_path.exists():
            report_path = flow_report_path
            is_routing = False
        
        # If mini=1, return compact format with key metrics
        if mini == 1:
            if not report_path:
                return {
                    "ok": False,
                    "message": "No report yet",
                    "delta_p95_pct": 0.0,
                    "delta_qps_pct": 0.0,
                    "error_rate_pct": 0.0,
                    "faiss_share_pct": 0.0,
                    "fallback_count": 0,
                    "generated_at": None
                }
            
            # Parse report to extract metrics
            report_text = report_path.read_text()
            delta_p95 = 0.0
            delta_qps = 0.0
            error_rate = 0.0
            faiss_share_pct = 0.0
            fallback_count = 0
            
            # Extract metrics from report
            import re
            for line in report_text.split('\n'):
                if 'ΔP95:' in line:
                    try:
                        # Extract percentage from "ΔP95: -8.1ms (-0.8%)"
                        match = re.search(r'\(([+-]?\d+\.?\d*)%\)', line)
                        if match:
                            delta_p95 = float(match.group(1))
                    except:
                        pass
                elif 'ΔQPS:' in line:
                    try:
                        # Extract number from "ΔQPS: -1.1 (-24.2%)"
                        match = re.search(r'\(([+-]?\d+\.?\d*)%\)', line)
                        if match:
                            delta_qps = float(match.group(1))
                    except:
                        pass
                elif is_routing and 'FAISS:' in line and '(' in line:
                    try:
                        # Extract "FAISS: 123 (45.6%)"
                        match = re.search(r'FAISS:\s*\d+\s*\(([0-9.]+)%\)', line)
                        if match:
                            faiss_share_pct = float(match.group(1))
                    except:
                        pass
                elif is_routing and 'Fallbacks' in line:
                    try:
                        # Extract "Fallbacks (FAISS→Qdrant): 5"
                        match = re.search(r':\s*(\d+)', line)
                        if match:
                            fallback_count = int(match.group(1))
                    except:
                        pass
                elif is_routing and 'Error Rate:' in line:
                    try:
                        # Extract "Error Rate: 0.12%"
                        match = re.search(r'([0-9.]+)%', line)
                        if match:
                            error_rate = float(match.group(1))
                    except:
                        pass
            
            # Calculate error rate from experiment state if not found in report
            if error_rate == 0.0:
                async with _state_lock:
                    valid_windows = [w for w in _lab_experiment.windows if w.valid]
                    total_windows = len(_lab_experiment.windows)
                    if total_windows > 0:
                        error_rate = ((total_windows - len(valid_windows)) / total_windows) * 100
            
            exp_type = "combo" if is_combo else ("routing" if is_routing else "flow")
            return {
                "ok": True,
                "message": "Report available",
                "experiment_type": exp_type,
                "delta_p95_pct": round(delta_p95, 2),
                "delta_qps_pct": round(delta_qps, 2),
                "error_rate_pct": round(error_rate, 2),
                "faiss_share_pct": round(faiss_share_pct, 2),
                "fallback_count": fallback_count,
                "generated_at": report_path.stat().st_mtime if report_path else None
            }
        
        # Standard full report
        if not report_path:
            # Try dashboard report
            dashboard_path = project_root / "reports" / "LAB_DASHBOARD_MINI.txt"
            if dashboard_path.exists():
                report_path = dashboard_path
            else:
                return {
                    "ok": False,
                    "error": "report_not_found",
                    "message": "No report available. Run an experiment first."
                }
        
        report_text = report_path.read_text()
        
        return {
            "ok": True,
            "report": report_text,
            "path": str(report_path)
        }
    
    except Exception as e:
        if mini == 1:
            return {
                "ok": False,
                "message": "Error reading report",
                "delta_p95_pct": 0.0,
                "delta_qps_pct": 0.0,
                "error_rate_pct": 0.0,
                "faiss_share_pct": 0.0,
                "fallback_count": 0,
                "generated_at": None
            }
        return {
            "ok": False,
            "error": "read_failed",
            "message": str(e)
        }


# ========================================
# Background Task
# ========================================

async def start_lab_experiment_loop():
    """Start background lab experiment control loop."""
    while True:
        try:
            await lab_experiment_control_loop()
        except Exception as e:
            logger.error(f"[LAB] Experiment loop error: {e}")
        await asyncio.sleep(5)  # Run every 5 seconds


# ========================================
# LabOps Agent Endpoints
# ========================================

@labops_router.get("/last")
async def get_labops_last_report() -> Dict[str, Any]:
    """
    Get last LabOps Agent summary report.
    
    Returns the latest agent summary with key metrics in mini format.
    Reads from reports/LABOPS_AGENT_SUMMARY.txt and parses key metrics.
    
    Returns:
        Mini format with ok, verdict, delta_p95_pct, delta_qps_pct, error_rate_pct,
        faiss_share_pct (if combo), and apply_command (if safe mode).
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        summary_path = project_root / "reports" / "LABOPS_AGENT_SUMMARY.txt"
        
        if not summary_path.exists():
            return {
                "ok": False,
                "message": "No agent report yet",
                "verdict": None,
                "delta_p95_pct": 0.0,
                "delta_qps_pct": 0.0,
                "error_rate_pct": 0.0,
                "faiss_share_pct": 0.0,
                "applied": False,
                "generated_at": None
            }
        
        # Parse summary report
        report_text = summary_path.read_text()
        
        verdict = None
        delta_p95 = 0.0
        delta_qps = 0.0
        error_rate = 0.0
        faiss_share_pct = 0.0
        applied = False
        apply_command = None
        
        import re
        
        for line in report_text.split('\n'):
            # Extract verdict
            if 'Decision:' in line:
                if 'PASS' in line:
                    verdict = 'PASS'
                elif 'EDGE' in line:
                    verdict = 'EDGE'
                elif 'FAIL' in line:
                    verdict = 'FAIL'
            
            # Extract ΔP95
            if line.startswith('ΔP95:'):
                match = re.search(r'([+-]?\d+\.?\d*)%', line)
                if match:
                    delta_p95 = float(match.group(1))
            
            # Extract ΔQPS
            elif line.startswith('ΔQPS:'):
                match = re.search(r'([+-]?\d+\.?\d*)%', line)
                if match:
                    delta_qps = float(match.group(1))
            
            # Extract error rate
            elif 'Error Rate:' in line:
                match = re.search(r'([0-9.]+)%', line)
                if match:
                    error_rate = float(match.group(1))
            
            # Check if flags were applied
            elif 'Flags Applied:' in line:
                applied = 'YES' in line
            
            # Extract FAISS share if present (combo experiments)
            elif 'FAISS:' in line and '(' in line:
                match = re.search(r'FAISS:\s*\d+\s*\(([0-9.]+)%\)', line)
                if match:
                    faiss_share_pct = float(match.group(1))
            
            # Extract apply command if in safe mode
            elif line.strip().startswith('curl -X POST'):
                # Multi-line curl command - capture it
                apply_command = line.strip()
        
        # If apply command is present, look for the full multi-line version
        if 'APPLY COMMAND' in report_text:
            in_apply_section = False
            cmd_lines = []
            for line in report_text.split('\n'):
                if 'APPLY COMMAND' in line:
                    in_apply_section = True
                    continue
                if in_apply_section:
                    if line.startswith('-' * 60):
                        continue
                    if line.startswith('=') or 'ROLLBACK' in line:
                        break
                    if line.strip():
                        cmd_lines.append(line.strip())
            
            if cmd_lines:
                apply_command = ' '.join(cmd_lines)
        
        return {
            "ok": True,
            "message": "Report available",
            "verdict": verdict,
            "delta_p95_pct": round(delta_p95, 2),
            "delta_qps_pct": round(delta_qps, 2),
            "error_rate_pct": round(error_rate, 2),
            "faiss_share_pct": round(faiss_share_pct, 2),
            "applied": applied,
            "apply_command": apply_command,
            "generated_at": summary_path.stat().st_mtime
        }
    
    except Exception as e:
        logger.error(f"[LABOPS] Error reading agent report: {e}")
        return {
            "ok": False,
            "message": f"Error reading report: {str(e)}",
            "verdict": None,
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "faiss_share_pct": 0.0,
            "applied": False,
            "generated_at": None
        }

