"""
experiment.py - Experiment Job Routes
======================================
REST API routes for running experiment jobs (fiqa-fast, tune-fast, etc).
"""

import logging
import re
import uuid
import subprocess
import sys
import os
import time
import threading
import collections
from typing import List, Optional, Dict, Any
from queue import Full
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
import json
from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.fiqa_api.job_runner import get_job_manager, Job
from services.fiqa_api.models import ExperimentConfig, ExperimentGroupConfig
from services.fiqa_api.models.diff_models import DiffMetrics, DiffResponse, DiffMeta
from services.fiqa_api.utils.gitinfo import get_git_sha
from services.fiqa_api.preset_manager import get_preset_manager
from services.fiqa_api.clients import get_qdrant_client

logger = logging.getLogger(__name__)

# ========================================
# Simplified Non-Blocking Job Runner
# ========================================

_EXEC = ThreadPoolExecutor(max_workers=int(os.getenv("RUNNER_WORKERS", "2")))
_JOBS: Dict[str, Dict[str, Any]] = {}  # {job_id: {"status": "QUEUED|RUNNING|SUCCEEDED|FAILED", "rc": int|None, "started": ts, "ended": ts|None, "log": path}}
_LOCK = threading.Lock()
_RUNS_DIR = Path(os.getenv("RUNS_DIR", "/app/.runs"))
_RUNS_DIR.mkdir(parents=True, exist_ok=True)

# ========================================
# Job History Registry
# ========================================

class JobMeta(BaseModel):
    """Job metadata for history tracking."""
    job_id: str
    status: str  # QUEUED, RUNNING, SUCCEEDED, FAILED
    created_at: str  # ISO format timestamp
    finished_at: Optional[str] = None  # ISO format timestamp
    return_code: Optional[int] = None
    params: Dict[str, Any] = {}  # sample, repeats, fast_mode, config_file
    cmd: Optional[List[str]] = None

# In-memory registry
_JOB_REGISTRY: Dict[str, JobMeta] = {}  # {job_id: JobMeta}
_HISTORY: collections.deque = collections.deque(maxlen=500)  # Most recent 500 jobs

def _save_job_meta(meta: JobMeta):
    """Persist job metadata to disk."""
    meta_file = _RUNS_DIR / f"{meta.job_id}.json"
    try:
        _RUNS_DIR.mkdir(parents=True, exist_ok=True)
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta.model_dump(), f, indent=2, ensure_ascii=False)
        logger.info(f"[HISTORY] saved meta: {meta_file} status={meta.status}")
    except Exception as e:
        logger.error(f"Failed to save job meta for {meta.job_id}: {e}", exc_info=True)

def _load_job_meta(job_id: str) -> Optional[JobMeta]:
    """Load job metadata from disk."""
    meta_file = _RUNS_DIR / f"{job_id}.json"
    if not meta_file.exists():
        return None
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return JobMeta(**data)
    except Exception as e:
        logger.error(f"Failed to load job meta for {job_id}: {e}", exc_info=True)
        return None


def enqueue_run(config_file: Optional[str], overrides: dict | None = None) -> str:
    """Enqueue a non-blocking run and return job_id immediately."""
    job_id = uuid.uuid4().hex[:12]
    log_path = _RUNS_DIR / f"{job_id}.log"
    
    # Build command for metadata
    # 以模块方式运行，确保包导入正常：python -m experiments.fiqa_suite_runner
    cmd = [sys.executable, "-u", "-m", "experiments.fiqa_suite_runner"]
    base_url = os.getenv("BASE", "http://localhost:8000")
    cmd += ["--base", base_url]
    if config_file:
        root = Path(__file__).resolve().parents[3]
        if not str(config_file).startswith("/"):
            cfg = (root / config_file).resolve()
        else:
            cfg = Path(config_file).resolve()
        cmd += ["--config-file", str(cfg)]
    if overrides:
        if "sample" in overrides and overrides["sample"] is not None:
            cmd += ["--sample", str(overrides["sample"])]
        if "repeats" in overrides and overrides["repeats"] is not None:
            cmd += ["--repeats", str(overrides["repeats"])]
        if "fast_mode" in overrides and overrides["fast_mode"]:
            cmd += ["--fast"]
        if "top_k" in overrides and overrides["top_k"] is not None:
            cmd += ["--top_k", str(overrides["top_k"])]
        if "dataset_name" in overrides and overrides["dataset_name"]:
            cmd += ["--dataset-name", str(overrides["dataset_name"])]
            logger.info("[ENQUEUE] Adding --dataset-name %s", overrides["dataset_name"])
        else:
            logger.warning("[ENQUEUE] No dataset_name in overrides!")
        if "qrels_name" in overrides and overrides["qrels_name"]:
            # If use_hard is True, don't pass qrels_name (runner will use HARD_QRELS_MAP)
            if not overrides.get("use_hard", False):
                cmd += ["--qrels-name", str(overrides["qrels_name"])]
                logger.info("[ENQUEUE] Adding --qrels-name %s", overrides["qrels_name"])
            else:
                logger.info("[ENQUEUE] Skipping --qrels-name (use_hard=True, runner will use HARD_QRELS_MAP)")
        else:
            logger.warning("[ENQUEUE] No qrels_name in overrides!")
        if "top_k" in overrides and overrides["top_k"] is not None:
            cmd += ["--top_k", str(overrides["top_k"])]
            logger.info("[ENQUEUE] Adding --top_k %s", overrides["top_k"])
        if "use_hard" in overrides and overrides["use_hard"]:
            cmd += ["--use-hard"]
            logger.info("[ENQUEUE] Adding --use-hard flag")
            # Note: env["USE_HARD"] will be set in _run_job function
        if "ef_search" in overrides and overrides["ef_search"] is not None:
            cmd += ["--ef-search", str(overrides["ef_search"])]
            logger.info("[ENQUEUE] Adding --ef-search %s", overrides["ef_search"])
        if "mmr" in overrides and overrides["mmr"]:
            cmd += ["--mmr"]
            logger.info("[ENQUEUE] Adding --mmr flag")
        if "mmr_lambda" in overrides and overrides["mmr_lambda"] is not None:
            cmd += ["--mmr-lambda", str(overrides["mmr_lambda"])]
            logger.info("[ENQUEUE] Adding --mmr-lambda %s", overrides["mmr_lambda"])
    
    # Create JobMeta with full parameter set (before logging)
    params = {
        "sample": overrides.get("sample") if overrides else None,
        "repeats": overrides.get("repeats") if overrides else None,
        "fast_mode": overrides.get("fast_mode") if overrides else False,
        "config_file": config_file,
        "dataset_name": overrides.get("dataset_name") if overrides else None,
        "qrels_name": overrides.get("qrels_name") if overrides else None,
        "top_k": overrides.get("top_k") if overrides else None,
        "use_hybrid": overrides.get("use_hybrid") if overrides else None,
        "rerank": overrides.get("rerank") if overrides else None,
        "collection": overrides.get("collection") if overrides else None,
        "use_hard": overrides.get("use_hard", False) if overrides else False,
    }
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    # Log payload and command for debugging
    logger.info("[PAYLOAD] %s", json.dumps(params, indent=2))
    logger.info("[CMD] %s  [CWD=/app]", " ".join(cmd))
    
    created_at = datetime.now().isoformat()
    meta = JobMeta(
        job_id=job_id,
        status="QUEUED",
        created_at=created_at,
        params=params,
        cmd=cmd
    )
    
    with _LOCK:
        _JOBS[job_id] = {
            "status": "QUEUED",
            "rc": None,
            "started": time.time(),
            "ended": None,
            "log": str(log_path)
        }
        _JOB_REGISTRY[job_id] = meta
        _HISTORY.append(meta)
        logger.info(f"[HISTORY] enqueued job {job_id} into registry (count={len(_JOB_REGISTRY)})")
    
    # Persist to disk immediately
    _save_job_meta(meta)
    
    _EXEC.submit(_run_job, job_id, config_file, overrides or {}, str(log_path))
    return job_id


def _run_job(job_id: str, config_file: Optional[str], overrides: dict, log_path: str):
    """Background job execution function."""
    root = Path("/app")  # Explicitly set to /app
    # 以模块方式运行，确保包导入正常：python -m experiments.fiqa_suite_runner
    cmd = [sys.executable, "-u", "-m", "experiments.fiqa_suite_runner"]
    
    # Set base URL to localhost:8000 (container's internal port)
    # This ensures the experiment script can connect to the API service
    base_url = os.getenv("BASE", "http://localhost:8000")
    cmd += ["--base", base_url]
    
    # Add config file if provided
    if config_file:
        # Resolve config file path
        if not str(config_file).startswith("/"):
            cfg = (root / config_file).resolve()
        else:
            cfg = Path(config_file).resolve()
        cmd += ["--config-file", str(cfg)]
    if overrides:
        # Convert overrides dict to CLI arguments
        if "sample" in overrides and overrides["sample"] is not None:
            cmd += ["--sample", str(overrides["sample"])]
        if "repeats" in overrides and overrides["repeats"] is not None:
            cmd += ["--repeats", str(overrides["repeats"])]
        if "fast_mode" in overrides and overrides["fast_mode"]:
            cmd += ["--fast"]
        if "top_k" in overrides and overrides["top_k"] is not None:
            cmd += ["--top_k", str(overrides["top_k"])]
        if "dataset_name" in overrides and overrides["dataset_name"]:
            cmd += ["--dataset-name", str(overrides["dataset_name"])]
        if "qrels_name" in overrides and overrides["qrels_name"]:
            # If use_hard is True, don't pass qrels_name (runner will use HARD_QRELS_MAP)
            if not overrides.get("use_hard", False):
                cmd += ["--qrels-name", str(overrides["qrels_name"])]
        if "top_k" in overrides and overrides["top_k"] is not None:
            cmd += ["--top_k", str(overrides["top_k"])]
        if "use_hard" in overrides and overrides["use_hard"]:
            cmd += ["--use-hard"]
        if "mmr" in overrides and overrides["mmr"]:
            cmd += ["--mmr"]
        if "mmr_lambda" in overrides and overrides["mmr_lambda"] is not None:
            cmd += ["--mmr-lambda", str(overrides["mmr_lambda"])]
    
    with _LOCK:
        _JOBS[job_id]["status"] = "RUNNING"
        # Update JobMeta status
        if job_id in _JOB_REGISTRY:
            _JOB_REGISTRY[job_id].status = "RUNNING"
            logger.info(f"[HISTORY] job {job_id} status updated to RUNNING")
            _save_job_meta(_JOB_REGISTRY[job_id])
    
    # Set environment variable for BASE as well (experiment script checks this)
    env = os.environ.copy()
    env["BASE"] = base_url
    env["JOB_ID"] = job_id  # Pass job_id to runner for metrics.json writing
    if overrides.get("use_hard", False):
        env["USE_HARD"] = "true"
    
    proc = subprocess.Popen(
        cmd,
        cwd="/app",  # Explicitly set working directory to /app
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    with open(log_path, "w", encoding="utf-8", errors="ignore") as lf:
        lf.write(f"[CMD] {' '.join(cmd)}  [CWD=/app]\n")
        lf.flush()
        if proc.stdout:
            for line in proc.stdout:
                lf.write(line)
                lf.flush()
    
    rc = proc.wait()
    
    finished_at = datetime.now().isoformat()
    final_status = "SUCCEEDED" if rc == 0 else "FAILED"
    
    # Job completion fallback: try to write metrics.json if missing (regardless of status)
    try:
        _write_metrics_json_if_missing(job_id, note=f"job finished with status={final_status} without runner metrics")
    except Exception as e:
        logger.warning(f"Failed to write fallback metrics.json for job {job_id}: {e}", exc_info=True)
    
    with _LOCK:
        _JOBS[job_id]["rc"] = rc
        _JOBS[job_id]["ended"] = time.time()
        _JOBS[job_id]["status"] = final_status
        
        # Update JobMeta
        if job_id in _JOB_REGISTRY:
            meta = _JOB_REGISTRY[job_id]
            meta.status = final_status
            meta.finished_at = finished_at
            meta.return_code = rc
            # Persist updated meta
            logger.info(f"[HISTORY] job {job_id} status updated to {final_status}")
            _save_job_meta(meta)


def _write_metrics_json_if_missing(job_id: str, note: str = ""):
    """
    API fallback: only write metrics.json if file is missing or source is not "runner".
    
    Args:
        job_id: Job ID
        note: Optional note about why fallback was used
    """
    out_dir = Path("/app/.runs") / job_id
    out_file = out_dir / "metrics.json"
    
    if out_file.exists():
        # Check if source is "runner" - if so, skip fallback
        try:
            with open(out_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                if existing.get("source") == "runner":
                    print(f"[API][METRICS] skip fallback, runner metrics exist: {out_file}")
                    return
        except Exception as e:
            print(f"[API][METRICS] error reading existing metrics.json: {e}, will overwrite")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "source": "api-fallback",  # <- 明确兜底
        "job_id": job_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": note or "runner did not produce metrics.json",
        "metrics": {
            "recall_at_10": 0.0,
            "ndcg_at_10": 0.0,
            "mrr": 0.0,
            "p95_ms": 0.0,
            "qps": 0.0
        },
        "config": {}
    }
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    print(f"[API][METRICS] wrote fallback {out_file}")


def _write_metrics_json(job_id: str, overrides: dict, log_path: str) -> None:
    """
    DEPRECATED: Use _write_metrics_json_if_missing instead.
    This function is kept for backward compatibility but should not be used.
    """
    # Legacy function - now just calls fallback
    _write_metrics_json_if_missing(job_id, note="legacy fallback")


def _get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status."""
    with _LOCK:
        return _JOBS.get(job_id, None)


def _get_job_log_tail(job_id: str, n: int = 200) -> Optional[Dict[str, Any]]:
    """Get log tail for a job."""
    # First try new registry system
    with _LOCK:
        # Check _JOBS first (contains log path)
        meta = _JOBS.get(job_id)
        if meta:
            p = Path(meta["log"])
            if p.exists():
                lines = p.read_text(errors="ignore").splitlines()[-n:]
                return {"lines": lines}
        
        # Check _JOB_REGISTRY
        if job_id in _JOB_REGISTRY:
            # Log path should be in _RUNS_DIR
            log_path = _RUNS_DIR / f"{job_id}.log"
            if log_path.exists():
                lines = log_path.read_text(errors="ignore").splitlines()[-n:]
                return {"lines": lines}
    
    # Try loading from disk metadata
    meta = _load_job_meta(job_id)
    if meta:
        log_path = _RUNS_DIR / f"{job_id}.log"
        if log_path.exists():
            lines = log_path.read_text(errors="ignore").splitlines()[-n:]
            return {"lines": lines}
    
    # Fallback: try standard log path
    log_path = _RUNS_DIR / f"{job_id}.log"
    if log_path.exists():
        lines = log_path.read_text(errors="ignore").splitlines()[-n:]
        return {"lines": lines}
    
    # Return empty if not found
    return {"lines": []}

# ========================================
# Router Setup
# ========================================

router = APIRouter()


# ========================================
# Command Mapping
# ========================================

CMD_MAP = {
    "fiqa-fast": [
        "bash", "-lc",
        "python -u experiments/fiqa_suite_runner.py --groups baseline rrf gated --top_k 50 --fast"
    ],
    "tune-fast": [
        "bash", "-lc",
        "python -u experiments/fiqa_tuner.py --fast"
    ]
}


# ========================================
# Request/Response Models
# ========================================

class RunKind(str, Enum):
    """Supported experiment job kinds."""
    fiqa_fast = "fiqa-fast"
    tune_fast = "tune-fast"


class RunOverrides(BaseModel):
    """Optional parameter overrides for a run request."""
    model_config = ConfigDict(extra='ignore')
    sample: int = 200
    repeats: int = 1
    fast_mode: bool = False
    top_k: Optional[int] = None
    rerank: Optional[bool] = None
    rerank_top_k: Optional[int] = Field(default=None, description="Rerank top K")
    dataset_name: Optional[str] = None
    qrels_name: Optional[str] = None
    use_hybrid: Optional[bool] = None
    rrf_k: Optional[int] = None
    collection: Optional[str] = None
    use_hard: Optional[bool] = False  # Use hard query subset
    ef_search: Optional[int] = None  # Qdrant HNSW ef parameter
    mmr: Optional[bool] = None  # MMR diversification
    mmr_lambda: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="MMR lambda parameter")


class RunRequest(BaseModel):
    """Request model for running an experiment (V9/V10 compatible)."""
    # Relax: ignore unknown fields to avoid 422 on extra keys
    model_config = ConfigDict(extra='ignore')
    
    # Simple controls (top-level defaults)
    sample: int = 200
    repeats: int = 1
    fast_mode: bool = False
    
    # Optional config source hints
    config_file: Optional[str] = Field(default=None, description="Optional config file path. If not provided, uses pure CLI args.")
    overrides: Optional[RunOverrides] = None
    
    # Dataset selection (top-level for convenience)
    dataset_name: Optional[str] = None
    qrels_name: Optional[str] = None
    top_k: Optional[int] = None
    use_hybrid: Optional[bool] = None
    rerank: Optional[bool] = None
    collection: Optional[str] = None
    use_hard: Optional[bool] = False  # Use hard query subset
    ef_search: Optional[int] = None  # Qdrant HNSW ef parameter
    
    # V9 legacy fields
    kind: Optional[RunKind] = None
    
    # V10 fields
    config: Optional[ExperimentConfig] = None
    preset_name: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_v10(self):
        """Validation: allow V9, V10, or simple top-level defaults without failing."""
        if self.kind is not None:
            if self.config is not None or self.preset_name is not None:
                raise ValueError("Cannot mix V9 'kind' with V10 'config' or 'preset_name'")
        # If neither kind/config/preset provided, we will fallback to a default preset in the handler
        return self


class RunResponse(BaseModel):
    """Response model for run endpoint."""
    job_id: str
    status: str
    position: Optional[int] = None


class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    job_id: str
    status: str
    return_code: Optional[int] = None
    queued_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    progress_hint: Optional[str] = None
    last_update_at: Optional[str] = None


class LogResponse(BaseModel):
    """Response model for logs endpoint."""
    job_id: str
    tail: List[str]


class CancelResponse(BaseModel):
    """Response model for cancel endpoint."""
    job_id: str
    status: str


class QueueResponse(BaseModel):
    """Response model for queue endpoint."""
    queued: List[str]
    running: List[str]
    queue_size: int


class JobsListResponse(BaseModel):
    """Response model for jobs list endpoint."""
    jobs: List[dict]
    total: int


class JobDetailResponse(BaseModel):
    """Response model for job detail endpoint."""
    job_id: str
    status: str
    cmd: List[str]
    return_code: Optional[int] = None
    queued_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    progress_hint: Optional[str] = None
    pid: Optional[int] = None
    artifacts: Optional[dict] = None
    config: Optional[dict] = None  # V10: Optional experiment config
    params: Optional[dict] = None  # Job parameters (dataset_name, qrels_name, etc.)
    metrics: Optional[dict] = None  # Metrics from metrics.json (overall, hard, latency_breakdown_ms, config)
    last_update_at: Optional[str] = None


# ========================================
# Helper Functions
# ========================================

def _get_versioned_presets() -> Dict[str, Any]:
    """
    Get versioned presets (shared between list_presets endpoint and run endpoint).
    
    Loads presets from configs/presets_v10.json if available and merges with hardcoded presets.
    
    Returns:
        Dictionary with version and presets list
    """
    # Try to load from configs/presets_v10.json
    presets_v10_path = Path("/app/configs/presets_v10.json")
    loaded_presets = []
    
    if presets_v10_path.exists():
        try:
            with open(presets_v10_path, 'r', encoding='utf-8') as f:
                presets_v10_data = json.load(f)
                presets_list = presets_v10_data.get("presets", [])
                
                # Convert presets_v10 format to versioned format
                for preset in presets_list:
                    # Map preset fields to ExperimentConfig format
                    config_dict = {
                        "dataset_name": preset.get("dataset_name"),
                        "qrels_name": preset.get("qrels_name"),
                        "qdrant_collection": preset.get("collection"),
                        "top_k": preset.get("top_k", 20),
                        "repeats": 1,
                        "warmup": 5,
                        "concurrency": 16,
                        "sample": 200,
                        "fast_mode": False,
                    }
                    
                    # Handle MMR and rerank
                    groups = []
                    if preset.get("mmr") is not False and preset.get("mmr") is not None:
                        # MMR enabled
                        groups.append({
                            "name": f"MMR={preset.get('mmr')}",
                            "use_hybrid": False,
                            "rerank": False,
                            "description": f"MMR diversity (lambda={preset.get('mmr')})"
                        })
                    elif preset.get("rerank"):
                        # Rerank enabled
                        groups.append({
                            "name": "Baseline + Rerank",
                            "use_hybrid": False,
                            "rerank": True,
                            "rerank_top_k": preset.get("rerank_top_k", 10),
                            "description": "Vector search with rerank"
                        })
                    else:
                        # Baseline
                        groups.append({
                            "name": "Baseline",
                            "use_hybrid": False,
                            "rerank": False,
                            "description": "Pure vector search baseline"
                        })
                    
                    config_dict["groups"] = groups
                    
                    # Generate a clean preset name for API use
                    preset_name = preset.get("name", "unknown")
                    clean_name = preset_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").replace("=", "_").replace(":", "")
                    # Remove multiple underscores
                    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
                    
                    loaded_presets.append({
                        "label": preset_name,
                        "name": clean_name,
                        "config": config_dict
                    })
                    
                logger.info(f"Loaded {len(loaded_presets)} presets from configs/presets_v10.json")
        except Exception as e:
            logger.warning(f"Failed to load presets_v10.json: {e}", exc_info=True)
    
    # Hardcoded presets (existing)
    hardcoded_presets = [
            {
                "label": "FIQA Baseline (10k)",
                "name": "fiqa_baseline_10k",
                "config": {
                    "dataset_name": "fiqa_10k_v1",
                    "qrels_name": "fiqa_qrels_10k_v1",
                    "qdrant_collection": "fiqa_10k_v1",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": False,
                    "fast_rrf_k": 40,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "Baseline",
                            "use_hybrid": False,
                            "rerank": False,
                            "rerank_top_k": 10,
                            "description": "Pure vector search baseline"
                        }
                    ]
                }
            },
            {
                "label": "FIQA Fast - Baseline (10k)",
                "name": "fiqa_fast_baseline_10k",
                "config": {
                    "dataset_name": "fiqa_10k_v1",
                    "qrels_name": "fiqa_qrels_10k_v1",
                    "qdrant_collection": "fiqa_10k_v1",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": True,
                    "fast_rrf_k": 40,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "Baseline",
                            "use_hybrid": False,
                            "rerank": False,
                            "rerank_top_k": 10,
                            "description": "Pure vector search baseline"
                        }
                    ]
                }
            },
            {
                "label": "FIQA Fast - Rerank (10k)",
                "name": "fiqa_fast_rerank_10k",
                "config": {
                    "dataset_name": "fiqa_10k_v1",
                    "qrels_name": "fiqa_qrels_10k_v1",
                    "qdrant_collection": "fiqa_10k_v1",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": True,
                    "fast_rrf_k": 40,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "Baseline + Rerank",
                            "use_hybrid": False,
                            "rerank": True,
                            "rerank_top_k": 10,
                            "description": "Vector search with rerank (10k)"
                        }
                    ]
                }
            },
            {
                "label": "FIQA Fast - Baseline (50k)",
                "name": "fiqa_fast_baseline_50k",
                "config": {
                    "dataset_name": "fiqa_50k_v1",
                    "qrels_name": "fiqa_qrels_50k_v1",
                    "qdrant_collection": "fiqa_50k_v1",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": True,
                    "fast_rrf_k": 40,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "Baseline",
                            "use_hybrid": False,
                            "rerank": False,
                            "rerank_top_k": 10,
                            "description": "Pure vector search baseline (50k)"
                        }
                    ]
                }
            },
            {
                "label": "FIQA Fast - Rerank (50k)",
                "name": "fiqa_fast_rerank_50k",
                "config": {
                    "dataset_name": "fiqa_50k_v1",
                    "qrels_name": "fiqa_qrels_50k_v1",
                    "qdrant_collection": "fiqa_50k_v1",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": True,
                    "fast_rrf_k": 40,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "Baseline + Rerank",
                            "use_hybrid": False,
                            "rerank": True,
                            "rerank_top_k": 10,
                            "description": "Vector search with rerank (50k)"
                        }
                    ]
                }
            },
            {
                "label": "FIQA 50k + RRF",
                "name": "fiqa_50k_rrf",
                "config": {
                    "dataset_name": "fiqa_50k_v1",
                    "qrels_name": "fiqa_qrels_50k_v1",
                    "qdrant_collection": "fiqa_50k_v1",
                    "data_dir": "experiments/data/fiqa",
                    "top_k": 40,
                    "repeats": 1,
                    "warmup": 5,
                    "concurrency": 16,
                    "sample": 200,
                    "fast_mode": True,
                    "fast_rrf_k": 60,
                    "fast_topk": 40,
                    "fast_rerank_topk": 10,
                    "groups": [
                        {
                            "name": "+RRF",
                            "use_hybrid": True,
                            "rrf_k": 60,
                            "rerank": False,
                            "rerank_top_k": 10,
                            "description": "Hybrid RRF (BM25 + vector fusion) - 50k"
                        }
                    ]
                }
            }
        ]
    
    # Merge presets: loaded from file first, then hardcoded (avoid duplicates by name)
    seen_names = set()
    merged_presets = []
    
    # Add loaded presets first
    for preset in loaded_presets:
        preset_name = preset.get("name", "")
        if preset_name and preset_name not in seen_names:
            merged_presets.append(preset)
            seen_names.add(preset_name)
    
    # Add hardcoded presets (skip if name already exists)
    for preset in hardcoded_presets:
        preset_name = preset.get("name", "")
        if preset_name and preset_name not in seen_names:
            merged_presets.append(preset)
            seen_names.add(preset_name)
    
    return {
        "version": 10 if loaded_presets else 3,
        "presets": merged_presets
    }


def _check_collection_exists(collection_name: str) -> tuple:
    """
    Check if a Qdrant collection exists.
    
    Args:
        collection_name: Collection name to check
        
    Returns:
        (exists: bool, hint: Optional[str])
        If collection doesn't exist, hint contains command to create it.
    """
    try:
        client = get_qdrant_client()
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name in collection_names:
            return True, None
        else:
            # Generate hint based on collection name
            if "50k" in collection_name:
                hint = "Run: make fiqa-v1-50k"
            else:
                hint = f"Collection {collection_name} not found. Please create it first."
            return False, hint
    except Exception as e:
        logger.error(f"Failed to check collection {collection_name}: {e}", exc_info=True)
        # If we can't check, don't block - assume it might exist
        return True, None


# ========================================
# Route Handlers
# ========================================

@router.post("/run", status_code=202, summary="Run an experiment job", description="Submit an experiment (non-blocking, returns 202 immediately).")
async def run_experiment(request: RunRequest):
    """
    Submit an experiment job (non-blocking, returns 202 immediately).
    
    Request body:
        config_file: Optional config file path. If not provided, uses pure CLI args (no --config-file).
        sample, repeats, fast_mode: Top-level parameters (used if config_file not provided).
        overrides: Optional parameter overrides with defaults (sample=200, repeats=1, fast_mode=False)
        
    Returns:
        202 Accepted with job_id and status URLs
    """
    try:
        # If config_file not provided, use None to run with pure CLI args (no --config-file)
        cfg = request.config_file
        # Merge precedence: top-level fields override overrides for dataset/qrels (bug fix)
        if request.overrides:
            # If overrides provided, use them (they already have defaults)
            overrides_dict = request.overrides.model_dump()
            # Top-level dataset_name/qrels_name take precedence (for API compatibility)
            if hasattr(request, 'dataset_name') and request.dataset_name:
                overrides_dict['dataset_name'] = request.dataset_name
            if hasattr(request, 'qrels_name') and request.qrels_name:
                overrides_dict['qrels_name'] = request.qrels_name
            # top_k can come from either place
            if hasattr(request, 'top_k') and request.top_k and 'top_k' not in overrides_dict:
                overrides_dict['top_k'] = request.top_k
        else:
            # Otherwise, use top-level fields with defaults
            overrides_dict = RunOverrides(
                sample=request.sample,
                repeats=request.repeats,
                fast_mode=request.fast_mode,
                dataset_name=getattr(request, 'dataset_name', None),
                qrels_name=getattr(request, 'qrels_name', None),
                top_k=getattr(request, 'top_k', None),
                use_hard=getattr(request, 'use_hard', False),
                ef_search=getattr(request, 'ef_search', None),
            ).model_dump()
            # Remove None values (but keep False values for use_hard)
            overrides_dict = {k: v for k, v in overrides_dict.items() if v is not None or k == 'use_hard'}
        logger.info("[RUN] Request dataset_name=%s, qrels_name=%s, top_k=%s, fast_mode=%s", 
                   getattr(request, 'dataset_name', None), 
                   getattr(request, 'qrels_name', None),
                   getattr(request, 'top_k', None),
                   getattr(request, 'fast_mode', False))
        logger.info("[RUN] overrides=%s", json.dumps(overrides_dict, indent=2))
        job_id = enqueue_run(cfg, overrides_dict)
        
        return {
            "ok": True,
            "status": "QUEUED",
            "job_id": job_id,
            "poll": f"/api/experiment/status/{job_id}",
            "logs": f"/api/experiment/logs/{job_id}"
        }
    except Exception as e:
        logger.error(f"Run experiment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}")
async def get_status_simple(job_id: str):
    """Get job status."""
    meta = _get_job_status(job_id)
    if not meta:
        # Return FAILED instead of unknown when job not found (registry might have been reloaded)
        return {
            "ok": True, 
            "job": {
                "job_id": job_id, 
                "status": "FAILED", 
                "error": "job not found in registry (may have been lost after container restart)"
            }
        }
    return {"ok": True, "job": meta}


@router.get("/logs/{job_id}")
async def get_logs_simple(job_id: str, tail: int = Query(200, ge=1, le=1000)):
    """Get log tail for a job."""
    data = _get_job_log_tail(job_id, tail)
    if data is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return data


@router.get("/debug/registry")
async def debug_registry():
    """
    Debug endpoint to check registry and history counts.
    
    Returns:
        Dictionary with registry stats for debugging
    """
    with _LOCK:
        registry_count = len(_JOB_REGISTRY)
        history_count = len(_HISTORY)
        
        # Count by status
        status_counts = {}
        for meta in _JOB_REGISTRY.values():
            status_counts[meta.status] = status_counts.get(meta.status, 0) + 1
        
        # Get recent job IDs
        recent_jobs = list(_JOB_REGISTRY.keys())[:10]
        
        return {
            "registry_count": registry_count,
            "history_count": history_count,
            "status_counts": status_counts,
            "recent_job_ids": recent_jobs,
            "runs_dir": str(_RUNS_DIR),
            "disk_files": len(list(_RUNS_DIR.glob("*.json"))) if _RUNS_DIR.exists() else 0
        }


@router.get("/history")
async def get_history(limit: int = Query(50, ge=1, le=500)):
    """
    Get experiment job history.
    
    Returns:
        List of job metadata sorted by created_at (descending)
        Includes QUEUED, RUNNING, SUCCEEDED, FAILED states.
    """
    # Collect jobs from in-memory registry
    all_jobs: List[JobMeta] = []
    
    with _LOCK:
        # Add all jobs from registry (includes QUEUED and RUNNING)
        all_jobs.extend(_JOB_REGISTRY.values())
        logger.debug(f"[HISTORY] loaded {len(_JOB_REGISTRY)} jobs from registry")
    
    # Load any additional jobs from disk that aren't in memory
    try:
        for meta_file in _RUNS_DIR.glob("*.json"):
            job_id = meta_file.stem
            # Skip if already in registry or if it's a log file pattern
            if job_id.endswith(".log"):
                continue
            if job_id not in _JOB_REGISTRY:
                meta = _load_job_meta(job_id)
                if meta:
                    all_jobs.append(meta)
        logger.debug(f"[HISTORY] loaded additional {len([j for j in all_jobs if j.job_id not in _JOB_REGISTRY])} jobs from disk")
    except Exception as e:
        logger.error(f"Error loading job metas from disk: {e}", exc_info=True)
    
    # Sort by created_at descending (most recent first)
    all_jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply limit
    result = all_jobs[:limit]
    
    # Log summary for debugging
    status_counts = {}
    for job in result:
        status_counts[job.status] = status_counts.get(job.status, 0) + 1
    logger.info(f"[HISTORY] returning {len(result)} jobs (limit={limit}): {status_counts}")
    
    # Return as list of dicts (includes all states: QUEUED, RUNNING, SUCCEEDED, FAILED)
    return [meta.model_dump() for meta in result]


@router.post("/cancel/{job_id}", response_model=CancelResponse)
async def cancel_job(job_id: str):
    """
    Cancel a running job.
    
    Path parameters:
        job_id: Job ID to cancel
        
    Returns:
        Cancellation status
        
    Raises:
        400: Invalid job_id format
        404: Job not found
        409: Job cannot be cancelled
    """
    # V8.1: Security patch - validate job_id format to prevent path traversal
    if not re.match(r'^[a-zA-Z0-9_-]{1,200}$', job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    
    try:
        manager = get_job_manager()
        result = manager.cancel(job_id)
        return CancelResponse(**result)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Cancel job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue", response_model=QueueResponse)
async def get_queue():
    """
    Get current queue status.
    
    Returns:
        Queue status with queued and running job IDs
    """
    manager = get_job_manager()
    status = manager.get_queue_status()
    return QueueResponse(**status)


@router.get("/jobs", response_model=JobsListResponse)
async def list_jobs(limit: int = Query(100, ge=1, le=500)):
    """
    List all jobs in reverse chronological order.
    
    Query parameters:
        limit: Maximum number of jobs to return (default: 100, max: 500)
        
    Returns:
        List of all jobs with metadata
    """
    manager = get_job_manager()
    jobs = manager.list_all_jobs(limit=limit)
    return JobsListResponse(jobs=jobs, total=len(jobs))


@router.get("/job/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(job_id: str):
    """
    Get detailed information for a specific job.
    
    Path parameters:
        job_id: Job ID
        
    Returns:
        Complete job details including artifacts
        
    Raises:
        400: Invalid job_id format
        404: Job not found
    """
    # V8.1: Security patch - validate job_id format to prevent path traversal
    if not re.match(r'^[a-zA-Z0-9_-]{1,200}$', job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    
    # Try to load metrics.json from run directory
    metrics = None
    metrics_path = _RUNS_DIR / job_id / "metrics.json"
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metrics.json for {job_id}: {e}")
    
    # First try new registry system
    with _LOCK:
        if job_id in _JOB_REGISTRY:
            meta = _JOB_REGISTRY[job_id]
            # Convert JobMeta to JobDetailResponse format
            return JobDetailResponse(
                job_id=meta.job_id,
                status=meta.status,
                cmd=meta.cmd or [],
                return_code=meta.return_code,
                queued_at=meta.created_at,
                started_at=meta.created_at if meta.status != "QUEUED" else None,
                finished_at=meta.finished_at,
                progress_hint=None,
                pid=None,
                artifacts=None,
                config=meta.params if meta.params else None,
                params=meta.params if meta.params else None,  # Also expose as params for frontend compatibility
                metrics=metrics,
                last_update_at=meta.finished_at or meta.created_at
            )
    
    # Try loading from disk
    meta = _load_job_meta(job_id)
    if meta:
        return JobDetailResponse(
            job_id=meta.job_id,
            status=meta.status,
            cmd=meta.cmd or [],
            return_code=meta.return_code,
            queued_at=meta.created_at,
            started_at=meta.created_at if meta.status != "QUEUED" else None,
            finished_at=meta.finished_at,
            progress_hint=None,
            pid=None,
            artifacts=None,
            config=meta.params if meta.params else None,
            params=meta.params if meta.params else None,  # Also expose as params for frontend compatibility
            metrics=metrics,
            last_update_at=meta.finished_at or meta.created_at
        )
    
    # Fallback to old JobManager system
    try:
        manager = get_job_manager()
        job = manager.get_job_detail(job_id)
        
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return JobDetailResponse(**job)
    except Exception as e:
        logger.warning(f"JobManager lookup failed for {job_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


# ========================================
# V10 Preset API Routes
# ========================================

@router.get("/presets")
async def list_presets():
    """
    V11: List all available presets with versioned response.
    
    Returns:
        Versioned preset list:
        {
            "version": 2,
            "presets": [
                {
                    "label": "FIQA Fast - Baseline (10k)",
                    "name": "fiqa_fast_baseline_10k",
                    "config": {...}
                },
                ...
            ]
        }
    """
    return _get_versioned_presets()


@router.get("/run/schema")
async def get_run_schema():
    """Return the run request schema and example payloads."""
    example_a = {
        "sample": 5,
        "repeats": 1,
        "fast_mode": True
    }
    example_b = {
        "config_file": "configs/fiqa_suite.yaml",
        "overrides": {"sample": 5, "repeats": 1, "fast_mode": True}
    }
    return {
        "schema": RunRequest.model_json_schema(),
        "examples": {"A": example_a, "B": example_b}
    }


@router.get("/presets/{preset_name}")
async def get_preset(preset_name: str):
    """
    Get a preset configuration by name.
    
    Path parameters:
        preset_name: Preset name
        
    Returns:
        Preset configuration
        
    Raises:
        404: Preset not found
    """
    preset_manager = get_preset_manager()
    config = preset_manager.get_preset(preset_name)
    
    if config is None:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    
    return {"name": preset_name, "config": config.model_dump()}


@router.post("/presets")
async def create_preset(
    preset_name: str,
    config: ExperimentConfig,
    description: str = ""
):
    """
    Create or update a preset.
    
    Query parameters:
        preset_name: Preset name
        description: Optional description
        
    Request body:
        config: Experiment configuration
        
    Returns:
        Success status
    """
    preset_manager = get_preset_manager()
    success = preset_manager.save_preset(preset_name, config, description)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save preset")
    
    return {"ok": True, "name": preset_name}


@router.delete("/presets/{preset_name}")
async def delete_preset(preset_name: str):
    """
    Delete a preset.
    
    Path parameters:
        preset_name: Preset name
        
    Returns:
        Success status
        
    Raises:
        404: Preset not found
    """
    preset_manager = get_preset_manager()
    success = preset_manager.delete_preset(preset_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    
    return {"ok": True, "name": preset_name}


# ========================================
# V11 Rerun API
# ========================================

class RerunRequest(BaseModel):
    """Request model for rerun endpoint."""
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameter overrides (top_k, repeats, fast_mode, bm25_k, rerank, rerank_topk, rerank_top_k, sample)")


class RerunResponse(BaseModel):
    """Response model for rerun endpoint."""
    job_id: str
    status_url: str


@router.post("/rerun/{job_id}", response_model=RerunResponse)
async def rerun_job(job_id: str, request: RerunRequest):
    """
    V11: Rerun a completed job with optional parameter overrides.
    
    Path parameters:
        job_id: Original job ID to rerun
        
    Request body:
        overrides: Optional dict with allowed keys: {top_k, repeats, fast_mode, bm25_k, rerank_topk, sample}
        
    Returns:
        New job_id and status_url
        
    Raises:
        400: Invalid job_id format or invalid overrides
        404: Job not found
        409: Job cannot be rerun or queue is full
    """
    # V8.1: Security patch - validate job_id format
    if not re.match(r'^[a-zA-Z0-9_-]{1,200}$', job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id format")
    
    try:
        manager = get_job_manager()
        
        # Validate overrides if provided
        overrides = request.overrides
        if overrides:
            # Normalize legacy key to canonical before validation
            if "rerank_topk" in overrides and "rerank_top_k" not in overrides:
                overrides["rerank_top_k"] = overrides["rerank_topk"]
                del overrides["rerank_topk"]

            # One-time audit log of raw overrides
            try:
                logger.info(f"[OVR-AUDIT] raw_overrides={json.dumps(overrides, ensure_ascii=False)}")
            except Exception:
                logger.info(f"[OVR-AUDIT] raw_overrides={overrides}")

            allowed_keys = {"top_k", "repeats", "fast_mode", "bm25_k", "rerank", "rerank_top_k", "sample"}
            invalid_keys = set(overrides.keys()) - allowed_keys
            if invalid_keys:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid override keys: {invalid_keys}. Allowed: {allowed_keys}"
                )
            
            # Validate types
            if "top_k" in overrides and not isinstance(overrides["top_k"], int):
                raise HTTPException(status_code=400, detail="top_k must be an integer")
            if "repeats" in overrides and not isinstance(overrides["repeats"], int):
                raise HTTPException(status_code=400, detail="repeats must be an integer")
            if "fast_mode" in overrides and not isinstance(overrides["fast_mode"], bool):
                raise HTTPException(status_code=400, detail="fast_mode must be a boolean")
            if "bm25_k" in overrides and not isinstance(overrides["bm25_k"], int):
                raise HTTPException(status_code=400, detail="bm25_k must be an integer")
            if "rerank" in overrides and not isinstance(overrides["rerank"], bool):
                raise HTTPException(status_code=400, detail="rerank must be a boolean")
            if "rerank_top_k" in overrides and not isinstance(overrides["rerank_top_k"], int):
                raise HTTPException(status_code=400, detail="rerank_top_k must be an integer")
            if "sample" in overrides and not isinstance(overrides["sample"], int):
                raise HTTPException(status_code=400, detail="sample must be an integer")
        
        # V11: Check collection existence before rerunning
        # Load original config to check collection
        job_detail = manager.get_job_detail(job_id)
        if job_detail and job_detail.get("config"):
            original_config = job_detail["config"]
            collection_name = original_config.get("qdrant_collection")
            if collection_name:
                exists, hint = _check_collection_exists(collection_name)
                if not exists:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "collection_missing",
                            "collection": collection_name,
                            "hint": hint
                        }
                    )
        
        # Rerun the job
        new_job = manager.rerun(job_id, overrides=overrides)
        
        # Get base URL from environment or use default
        import os
        base_url = os.getenv("FIQA_API_BASE", "http://localhost:8011")
        status_url = f"{base_url}/api/experiment/status/{new_job.job_id}"
        
        return RerunResponse(
            job_id=new_job.job_id,
            status_url=status_url
        )
        
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Full:
        raise HTTPException(status_code=409, detail="队列已满，请稍后再试")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rerun job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# V11 Diff API
# ========================================

@router.get("/diff", response_model=DiffResponse)
async def diff_jobs(
    A: str = Query(..., description="Job ID A"),
    B: str = Query(..., description="Job ID B")
):
    """
    V11: Compare two completed jobs (A/B comparison) with readiness and compatibility checks.
    
    Query parameters:
        A: Job ID A
        B: Job ID B
        
    Returns:
        DiffResponse with metrics for both jobs and parameter differences
        
    Raises:
        400: Invalid job_id format
        404: Job not found
        409: Job not ready (in progress or missing metrics)
        422: Incompatible context (dataset/version/index/units mismatch)
    """
    # Validate job_id formats
    if not re.match(r'^[a-zA-Z0-9_-]{1,200}$', A):
        raise HTTPException(status_code=400, detail="Invalid job_id A format")
    if not re.match(r'^[a-zA-Z0-9_-]{1,200}$', B):
        raise HTTPException(status_code=400, detail="Invalid job_id B format")
    
    try:
        manager = get_job_manager()
        
        # Load job details from JobManager
        def _load_job(job_id: str) -> Optional[Dict]:
            """Load job from JobManager."""
            job = manager.get_job_detail(job_id)
            # get_job_detail already returns a dict, not a Job object
            return job if job else None
        
        # Load metrics from file
        def _load_metrics(job_id: str) -> Optional[Dict]:
            """Load metrics.json for a job."""
            base_dir = Path(manager.base_dir)
            job_dir = base_dir / "jobs" / job_id
            metrics_file = job_dir / "metrics.json"
            
            if not metrics_file.exists():
                return None
            
            from services.fiqa_api.utils.fs import read_json
            metrics = read_json(str(metrics_file), {})
            return metrics if metrics else None
        
        # Load config from file
        def _load_config(job_id: str) -> Dict:
            """Load config.json for a job (or from job detail)."""
            base_dir = Path(manager.base_dir)
            job_dir = base_dir / "jobs" / job_id
            config_file = job_dir / "config.json"
            
            from services.fiqa_api.utils.fs import read_json
            if config_file.exists():
                config = read_json(str(config_file), {})
                if config:
                    return config
            
            # Fallback to config from job detail
            job = manager.get_job_detail(job_id)
            if job and job.get("config"):
                return job["config"]
            
            return {}
        
        # Load both jobs
        job_a = _load_job(A)
        job_b = _load_job(B)
        
        # 404: Job not found
        if job_a is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "job_not_found", "missing": A}
            )
        if job_b is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "job_not_found", "missing": B}
            )
        
        # get_job_detail returns a dict directly, not a Job object
        # No need to call .to_dict() again
        # 409: Job not ready - check status
        # Only SUCCEEDED jobs can be diffed; FAILED jobs should return 409
        status_a = job_a.get("status", "")
        status_b = job_b.get("status", "")
        
        # Only SUCCEEDED is considered ready for diff
        if status_a != "SUCCEEDED":
            if status_a == "FAILED":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "job_failed",
                        "job_id": A,
                        "status": status_a,
                        "reason": "Failed jobs cannot be compared"
                    }
                )
            else:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "job_in_progress",
                        "job_id": A,
                        "status": status_a
                    }
                )
        
        if status_b != "SUCCEEDED":
            if status_b == "FAILED":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "job_failed",
                        "job_id": B,
                        "status": status_b,
                        "reason": "Failed jobs cannot be compared"
                    }
                )
            else:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "job_in_progress",
                        "job_id": B,
                        "status": status_b
                    }
                )
        
        # 409: Check for missing metrics
        met_a = _load_metrics(A)
        met_b = _load_metrics(B)
        
        if met_a is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "metrics_missing",
                    "job_id": A
                }
            )
        
        if met_b is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "metrics_missing",
                    "job_id": B
                }
            )
        
        # Load configs
        cfg_a = _load_config(A) or {}
        cfg_b = _load_config(B) or {}
        
        # 422: Compatibility check - check for mismatches
        mismatch = {}
        
        # Dataset name check
        if cfg_a.get("dataset_name") != cfg_b.get("dataset_name"):
            mismatch["dataset_name"] = [
                cfg_a.get("dataset_name"),
                cfg_b.get("dataset_name")
            ]
        
        # Schema version check
        if cfg_a.get("schema_version") != cfg_b.get("schema_version"):
            mismatch["schema_version"] = [
                cfg_a.get("schema_version"),
                cfg_b.get("schema_version")
            ]
        
        # Optional consistency checks (index/embedding fingerprint)
        for k in ["index_fingerprint", "embedding_model", "embedding_version"]:
            va = cfg_a.get(k)
            vb = cfg_b.get(k)
            if va and vb and va != vb:
                mismatch[k] = [va, vb]
        
        # Units consistency check (from metrics)
        units_a = met_a.get("units") or {}
        units_b = met_b.get("units") or {}
        if units_a and units_b and units_a != units_b:
            mismatch["units"] = [units_a, units_b]
        
        # Raise 422 if any mismatches found
        if mismatch:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "incompatible_context",
                    "mismatch": mismatch
                }
            )
        
        # Extract required metrics
        def extract_metrics(metrics: Dict) -> DiffMetrics:
            """Extract metrics into DiffMetrics model."""
            return DiffMetrics(
                recall_at_10=metrics.get("recall_at_10", 0.0),
                p95_ms=metrics.get("p95_ms", 0.0),
                cost_per_query=metrics.get("cost_per_query", 0.0)
            )
        
        metrics_a_obj = extract_metrics(met_a)
        metrics_b_obj = extract_metrics(met_b)
        
        # Compute parameter differences (only keys with different values)
        # Format: {"top_k": [a, b], "fast_mode": [a, b]}
        param_diff = {}
        all_keys = set(cfg_a.keys()) | set(cfg_b.keys())
        for key in all_keys:
            val_a = cfg_a.get(key)
            val_b = cfg_b.get(key)
            if val_a != val_b:
                param_diff[key] = [val_a, val_b]
        
        # Get git SHA using robust utility
        git_sha, git_sha_source = get_git_sha()
        
        # Get created_at from job queued_at (separate for A and B)
        created_at_a = job_a.get("queued_at") or job_a.get("started_at") or datetime.now().isoformat()
        created_at_b = job_b.get("queued_at") or job_b.get("started_at") or datetime.now().isoformat()
        
        # Build meta (use values from compatible configs)
        dataset_name = cfg_a.get("dataset_name") or cfg_b.get("dataset_name") or "unknown"
        schema_version = cfg_a.get("schema_version") or cfg_b.get("schema_version") or 11
        
        meta = DiffMeta(
            dataset_name=dataset_name,
            schema_version=schema_version,
            git_sha=git_sha,
            git_sha_source=git_sha_source,
            created_at={"A": created_at_a, "B": created_at_b}
        )
        
        return DiffResponse(
            metrics={"A": metrics_a_obj, "B": metrics_b_obj},
            params_diff=param_diff,
            meta=meta
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diff jobs error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Runner Self-Check Endpoint
# ========================================

@router.get("/runner_check")
async def runner_check():
    """
    Runner self-check endpoint to verify Python interpreter, working directory, and script existence.
    
    Returns:
        {
            "python": sys.executable path,
            "cwd": current working directory,
            "experiments_root": EXPERIMENTS_ROOT env var value,
            "script_path": absolute path to fiqa_suite_runner.py,
            "script_exists": bool indicating if fiqa_suite_runner.py exists
        }
    """
    # Build absolute paths same way as job_runner
    experiments_root = os.getenv("EXPERIMENTS_ROOT")
    if experiments_root:
        root = Path(experiments_root).resolve()
    else:
        root = Path(__file__).resolve().parents[3] / "experiments"
        root = root.resolve()
    
    script_path = root / "fiqa_suite_runner.py"
    
    return {
        "python": sys.executable,
        "cwd": os.getcwd(),
        "experiments_root": experiments_root,
        "script_path": str(script_path.resolve()),
        "script_exists": script_path.exists()
    }



# dev-reload-132054
