"""
job_runner.py - Job Manager and Runner
======================================
Singleton job controller with queue, worker thread, and subprocess management.
"""

import os
import sys
import time
import uuid
import signal
import logging
import threading
import subprocess
import json
import re
import copy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Literal, Deque, Any
from queue import Queue, Full, Empty
from threading import RLock
from collections import deque

import requests

from services.fiqa_api.utils.fs import (
    ensure_dir,
    read_json,
    write_json_atomic,
    write_text_file
)

logger = logging.getLogger(__name__)


# ========================================
# Utility Functions
# ========================================

def find_repo_root(start: Path) -> Path:
    """
    Find repository root by searching upward for pyproject.toml.
    
    Args:
        start: Starting path to search from
        
    Returns:
        Path to repository root, or start if not found (fallback)
    """
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "pyproject.toml").exists():
            return cand
    return start  # 兜底


# ========================================
# Job Status and Model
# ========================================

JobStatus = Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "ABORTED"]


class Job:
    """Job model (V9/V10 compatible)."""
    def __init__(
        self,
        job_id: str,
        status: JobStatus,
        cmd: List[str],
        return_code: Optional[int] = None,
        queued_at: Optional[str] = None,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
        progress_hint: Optional[str] = None,
        pid: Optional[int] = None,
        artifacts: Optional[Dict] = None,
        config: Optional[Dict] = None  # V10: Optional experiment config
    ):
        self.job_id = job_id
        self.status = status
        self.cmd = cmd
        self.return_code = return_code
        self.queued_at = queued_at or datetime.now().isoformat()
        self.started_at = started_at
        self.finished_at = finished_at
        self.progress_hint = progress_hint
        self.pid = pid
        self.artifacts = artifacts
        self.config = config  # V10
        self.last_update_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert job to dictionary."""
        result = {
            "job_id": self.job_id,
            "status": self.status,
            "cmd": self.cmd,
            "return_code": self.return_code,
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress_hint": self.progress_hint,
            "pid": self.pid,
            "artifacts": self.artifacts,
            "last_update_at": self.last_update_at
        }
        # V10: Include config if present
        if self.config is not None:
            result["config"] = self.config
        return result
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create job from dictionary (V9/V10 compatible)."""
        return cls(
            job_id=data["job_id"],
            status=data["status"],
            cmd=data["cmd"],
            return_code=data.get("return_code"),
            queued_at=data.get("queued_at"),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            progress_hint=data.get("progress_hint"),
            pid=data.get("pid"),
            artifacts=data.get("artifacts"),
            config=data.get("config")  # V10: Load config if present
        )


# ========================================
# Job Manager Singleton
# ========================================

class JobManager:
    """Singleton job manager with queue and worker."""
    
    _instance: Optional['JobManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Configuration
        self.base_dir = os.getenv("RAGLAB_DIR", "/tmp/raglab")
        self.queue_maxsize = 10
        # Build absolute path to repository root
        # Path(__file__).parents[2] = searchforge root (fiqa_api -> services -> searchforge)
        self.project_root = Path(__file__).resolve().parents[2]
        
        # State
        self.queue = Queue(maxsize=self.queue_maxsize)
        self.state: Dict[str, Job] = {}
        self.tail_cache: Dict[str, Deque[str]] = {}
        self.lock = RLock()
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Directories
        self.logs_dir = Path(self.base_dir) / "logs"
        self.pids_dir = Path(self.base_dir) / "pids"
        self.jobs_file = Path(self.base_dir) / "jobs.json"
        self.jobs_lock_path = str(self.jobs_file) + ".lock"  # V11: Lock path for jobs.json
        
        # Initialize
        self._setup_directories()
        self._load_persisted_jobs()
        self._start_worker()
        
        self._initialized = True
        logger.info(f"JobManager initialized (base_dir={self.base_dir})")
    
    def _setup_directories(self):
        """Create necessary directories."""
        ensure_dir(str(self.logs_dir))
        ensure_dir(str(self.pids_dir))
    
    def _get_job_dir(self, job_id: str) -> Path:
        """
        Get directory path for a job (for storing config.json, etc.).
        
        Args:
            job_id: Job ID
            
        Returns:
            Path to job directory
        """
        return Path(self.base_dir) / "jobs" / job_id
    
    def _get_git_sha(self) -> str:
        """
        Get current git SHA for reproducibility.
        
        Returns:
            Git SHA (first 8 chars) or "unknown"
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]
        except Exception as e:
            logger.warning(f"Failed to get git SHA: {e}")
        return "unknown"
    
    def _parse_metrics_from_output(self, lines: List[str]) -> Dict[str, Any]:
        """
        V11: Parse metrics from job output lines.
        
        Looks for common metrics patterns in the output.
        
        Args:
            lines: List of output lines from subprocess
            
        Returns:
            Metrics dict with recall_at_10, p95_ms, qps, etc.
        """
        metrics = {}
        
        # Try to extract common metrics from output
        for line in lines:
            # Look for recall metrics
            if "recall" in line.lower() and "@10" in line:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)', line)
                    if match:
                        metrics["recall_at_10"] = float(match.group(1))
                except:
                    pass
            
            # Look for p95/p99 latency
            if "p95" in line.lower() or "95th" in line.lower():
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*ms', line, re.IGNORECASE)
                    if match:
                        metrics["p95_ms"] = float(match.group(1))
                except:
                    pass
            
            # Look for QPS
            if "qps" in line.lower() or "queries/sec" in line.lower():
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)', line)
                    if match:
                        metrics["qps"] = float(match.group(1))
                except:
                    pass
        
        return metrics
    
    def _write_job_metrics(self, job_id: str, artifacts: Optional[Dict], config: Dict[str, Any]) -> None:
        """
        V11: Write metrics.json atomically after job completion.
        
        Args:
            job_id: Job ID
            artifacts: Artifacts dict from job output (may contain metrics or yaml_report path)
            config: Job config for cost estimation
        """
        import yaml
        from services.fiqa_api.cost import estimate_cost
        
        job_dir = self._get_job_dir(job_id)
        metrics_file = job_dir / "metrics.json"
        
        # Extract metrics from artifacts or use defaults
        metrics = {}
        if artifacts:
            metrics.update(artifacts)
        
        # Try to extract metrics from YAML report if artifacts only contain paths
        if artifacts and "yaml_report" in artifacts and not any(k in metrics for k in ["recall_at_10", "p95_ms", "qps"]):
            try:
                yaml_path = Path(artifacts["yaml_report"])
                # Make path relative to project root
                if not yaml_path.is_absolute():
                    yaml_path = self.project_root / yaml_path
                
                if yaml_path.exists():
                    with open(yaml_path, 'r') as f:
                        yaml_data = yaml.safe_load(f)
                    
                    # Extract metrics from first configuration in YAML
                    configurations = yaml_data.get("configurations", [])
                    if configurations and "metrics" in configurations[0]:
                        yaml_metrics = configurations[0]["metrics"]
                        # Convert nested format {p95_ms: {mean: X}} to flat format {p95_ms: X}
                        metrics["p95_ms"] = yaml_metrics.get("p95_ms", {}).get("mean", 0.0)
                        metrics["qps"] = yaml_metrics.get("qps", {}).get("mean", 0.0)
                        metrics["recall_at_10"] = yaml_metrics.get("recall_at_10", {}).get("mean", 0.0)
                        logger.info(f"V11: Extracted metrics from YAML: recall={metrics.get('recall_at_10', 0.0):.4f}, p95={metrics.get('p95_ms', 0.0):.1f}ms, qps={metrics.get('qps', 0.0):.2f}")
            except Exception as e:
                logger.warning(f"V11: Failed to extract metrics from YAML report: {e}")
        
        # Ensure required fields exist
        metrics.setdefault("recall_at_10", 0.0)
        metrics.setdefault("p95_ms", 0.0)
        metrics.setdefault("qps", 0.0)
        
        # Calculate cost per query
        cost_per_query = estimate_cost(metrics, config)
        metrics["cost_per_query"] = cost_per_query
        
        # Set schema version
        metrics["schema_version"] = 11
        metrics["job_id"] = job_id
        
        # Write atomically
        write_json_atomic(str(metrics_file), metrics)
        logger.info(f"V11: Wrote metrics.json for job {job_id} (cost_per_query={cost_per_query:.6f})")
    
    def _get_default_v10_config(self) -> Dict:
        """
        V10.6/V10.7: Get safe default ExperimentConfig for V9 job migration.
        
        Returns:
            ExperimentConfig as dictionary with safe defaults
        """
        # Use ExperimentConfig Pydantic defaults - safe and valid
        from services.fiqa_api.models.experiment_models import ExperimentConfig
        
        # Create with all defaults from Pydantic model
        default_config = ExperimentConfig()
        return default_config.model_dump()
    
    def _sanitize_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        V11: Normalize experiment config for safety & reproducibility.
        
        - groups: if missing/empty -> [{"name": "baseline", ...}]
        - sample: if None -> 0
        - schema_version: always set to 11
        - dataset_name/qrels_name/qdrant_collection: default to fiqa_10k_v1 if missing
        - Ensure no None fields (remove them)
        
        Args:
            cfg: Config dictionary to sanitize (may be modified in-place)
            
        Returns:
            Sanitized cfg (may be the same object)
        """
        if cfg is None:
            return cfg  # V10.7 已保证默认不为 None，这里留作防御
        
        # Map legacy rerank_topk -> rerank_top_k (canonical)
        if cfg is not None and isinstance(cfg, dict):
            if "rerank_topk" in cfg and "rerank_top_k" not in cfg:
                cfg["rerank_top_k"] = cfg.get("rerank_topk")
                del cfg["rerank_topk"]

        # V11: Set schema_version
        cfg["schema_version"] = 11
        
        # V11: Default dataset/qrels/collection fields if missing
        if not cfg.get("dataset_name"):
            cfg["dataset_name"] = "fiqa_10k_v1"
        if not cfg.get("qrels_name"):
            cfg["qrels_name"] = "fiqa_qrels_10k_v1"
        if not cfg.get("qdrant_collection"):
            cfg["qdrant_collection"] = "fiqa_10k_v1"
        
        # 1) groups 兜底 - 如果缺失或为空列表，设置为 ["baseline"]
        groups = cfg.get("groups")
        if not groups:  # None 或 空列表
            from services.fiqa_api.models.experiment_models import ExperimentGroupConfig
            baseline_group = ExperimentGroupConfig(name="baseline")
            cfg["groups"] = [baseline_group.model_dump()]
        
        # 2) sample 去空 - 如果为 None，设置为 0
        if cfg.get("sample") is None:
            cfg["sample"] = 0
        
        # 3) fast_mode 默认值 - 如果缺失，默认为 False
        if "fast_mode" not in cfg:
            cfg["fast_mode"] = False
        
        # Defaults for rerank keys at top-level for suite convenience
        if "rerank" not in cfg:
            cfg["rerank"] = False
        if "rerank_top_k" not in cfg:
            cfg["rerank_top_k"] = 10

        # V11: Remove None fields to ensure config completeness (except schema_version)
        # Note: We create a new dict here to avoid modifying the original while iterating
        sanitized = {k: v for k, v in cfg.items() if v is not None or k == "schema_version"}
        # schema_version should never be None, but ensure it's set
        sanitized["schema_version"] = 11
        
        # Ensure fast_mode is present (default to False if somehow missing)
        if "fast_mode" not in sanitized:
            sanitized["fast_mode"] = False
        
        return sanitized
    
    def _load_persisted_jobs(self):
        """Load jobs from persistence and clean up stale processes."""
        jobs_data = read_json(str(self.jobs_file), {})
        
        needs_persistence = False
        
        for job_data in jobs_data.get("jobs", []):
            job_id = job_data.get("job_id", "unknown")
            
            # V10.7: Real V9->V10 lazy migration - use safe default config
            if "config" not in job_data:
                # This is a V9 job - assign safe default config (never None)
                default_config = self._get_default_v10_config()
                # Sanitize the default config
                default_config = self._sanitize_config(default_config)
                job_data["config"] = default_config
                needs_persistence = True
                
                # Save config.json to job directory
                try:
                    job_dir = self._get_job_dir(job_id)
                    job_dir.mkdir(parents=True, exist_ok=True)
                    config_file = job_dir / "config.json"
                    
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(default_config, f, indent=2, ensure_ascii=False)
                    
                    logger.info(
                        f"V10.7: Migrated V9 job {job_id} -> default config, saved to {config_file}"
                    )
                except Exception as e:
                    logger.error(f"V10.7: Failed to save config.json for job {job_id}: {e}", exc_info=True)
                    # Continue anyway - config is already set in job_data
            
            # V10.7: Sanitize config (groups/sample normalization)
            if "config" in job_data and job_data["config"]:
                before_cfg = job_data.get("config")
                # Create a deep copy for sanitization to compare changes
                cfg_copy = copy.deepcopy(before_cfg) if isinstance(before_cfg, dict) else before_cfg
                after_cfg = self._sanitize_config(cfg_copy)
                # Compare by JSON serialization to handle nested dicts properly
                if json.dumps(before_cfg, sort_keys=True) != json.dumps(after_cfg, sort_keys=True):
                    job_data["config"] = after_cfg
                    needs_persistence = True
                    logger.info(f"V10.7: Sanitized config for job {job_id} (groups/sample normalization)")
                    
                    # Update config.json in job directory if it exists
                    try:
                        job_dir = self._get_job_dir(job_id)
                        config_file = job_dir / "config.json"
                        if config_file.exists():
                            with open(config_file, 'w', encoding='utf-8') as f:
                                json.dump(after_cfg, f, indent=2, ensure_ascii=False)
                            logger.info(f"V10.7: Updated config.json for job {job_id}")
                    except Exception as e:
                        logger.warning(f"V10.7: Failed to update config.json for job {job_id}: {e}")
            
            job = Job.from_dict(job_data)
            
            # Check if job is still RUNNING
            if job.status == "RUNNING" and job.pid:
                # Check if process still exists
                if not self._is_process_running(job.pid):
                    logger.warning(f"Marking job {job.job_id} as ABORTED (process not found)")
                    job.status = "ABORTED"
                    job.finished_at = datetime.now().isoformat()
                    # Update job_data to reflect status change
                    job_data["status"] = "ABORTED"
                    job_data["finished_at"] = job.finished_at
                    needs_persistence = True
                else:
                    # Process still running, but we don't track it actively anymore
                    logger.warning(f"Job {job.job_id} was RUNNING but orphaned, marking as ABORTED")
                    job.status = "ABORTED"
                    job.finished_at = datetime.now().isoformat()
                    # Update job_data to reflect status change
                    job_data["status"] = "ABORTED"
                    job_data["finished_at"] = job.finished_at
                    needs_persistence = True
            
            # Clean up stale PID file
            pid_file = self.pids_dir / f"{job.job_id}.pid"
            if pid_file.exists() and job.status != "RUNNING":
                try:
                    pid_file.unlink()
                except:
                    pass
            
            # Don't reload QUEUED jobs on restart (they are lost)
            if job.status == "QUEUED":
                continue
            
            self.state[job.job_id] = job
            self.tail_cache[job.job_id] = deque(maxlen=1000)
        
        # V9.0/V10.7: Persist zombie job cleanup and V9->V10 migrations
        if needs_persistence:
            try:
                # Use read-modify-write with lock to avoid overwriting concurrent updates
                from services.fiqa_api.utils.locks import file_lock
                
                with file_lock(self.jobs_lock_path):
                    # Re-read latest state (may have been updated by another process)
                    latest_jobs_data = read_json(str(self.jobs_file), {})
                    latest_jobs_dict = {j.get("job_id"): j for j in latest_jobs_data.get("jobs", [])}
                    
                    # Merge: use migrated jobs_data as base, but preserve any new jobs from latest
                    merged_jobs = []
                    migrated_job_ids = {j.get("job_id") for j in jobs_data.get("jobs", [])}
                    
                    # Add migrated/updated jobs
                    for job in jobs_data.get("jobs", []):
                        merged_jobs.append(job)
                    
                    # Add any jobs from latest that weren't in our migration (from other processes)
                    for job_id, job_data in latest_jobs_dict.items():
                        if job_id not in migrated_job_ids:
                            merged_jobs.append(job_data)
                    
                    final_jobs_data = {
                        "jobs": merged_jobs,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    # Write atomically (lock is held)
                    write_json_atomic(str(self.jobs_file), final_jobs_data)
                    logger.info(f"V10.7: Atomically updated jobs.json with migrated configs")
            except Exception as e:
                logger.error(f"V10.7: Failed to atomically persist jobs.json: {e}", exc_info=True)
                # Fallback to existing persist method
                self._persist_state()
        
        logger.info(f"Loaded {len(self.state)} persisted jobs")
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if process is still running."""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False
    
    def _parse_artifacts_from_output(self, lines: List[str]) -> Optional[Dict]:
        """
        V6: Parse ARTIFACTS_JSON from subprocess output with security validation.
        
        Args:
            lines: List of output lines from subprocess
            
        Returns:
            Artifacts dict if found and validated, None otherwise
        """
        try:
            # Search for [ARTIFACTS_JSON] marker
            for line in lines:
                if '[ARTIFACTS_JSON]' in line:
                    # Extract JSON part after the marker
                    marker_start = line.find('[ARTIFACTS_JSON]') + len('[ARTIFACTS_JSON]')
                    json_str = line[marker_start:].strip()
                    
                    # Parse JSON
                    artifacts = json.loads(json_str)
                    
                    # V6: Security validation - sanitize all paths
                    return self._sanitize_artifacts(artifacts)
            
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse ARTIFACTS_JSON: {e}")
            return None
    
    def _sanitize_artifacts(self, artifacts: Dict) -> Optional[Dict]:
        """
        V6: Sanitize artifact paths to prevent path traversal.
        
        Args:
            artifacts: Raw artifacts dict from subprocess
            
        Returns:
            Sanitized artifacts dict, or None if validation fails
        """
        try:
            # Define safe base directories
            safe_bases = [
                Path("reports"),
                Path("experiments")
            ]
            
            sanitized = {}
            
            # Validate and sanitize each path field
            for key, value in artifacts.items():
                if key.endswith('_path') or key.endswith('_report') or key.endswith('_plot') or key == 'report_dir':
                    if value is None:
                        sanitized[key] = None
                        continue
                    
                    # Convert to Path and resolve
                    path = Path(value).resolve()
                    
                    # Check if path is within any safe base
                    is_safe = False
                    for base in safe_bases:
                        try:
                            base_resolved = (self.project_root / base).resolve()
                            path.relative_to(base_resolved)
                            is_safe = True
                            break
                        except ValueError:
                            continue
                    
                    if not is_safe:
                        logger.warning(f"V6: Rejecting unsafe artifact path: {path}")
                        return None
                    
                    # Store relative path from project root
                    sanitized[key] = str(path.relative_to(self.project_root))
                else:
                    # Non-path fields pass through
                    sanitized[key] = value
            
            return sanitized
        except Exception as e:
            logger.error(f"V6: Failed to sanitize artifacts: {e}")
            return None
    
    def _start_worker(self):
        """Start worker thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Worker thread started")
    
    def _check_health(self) -> bool:
        """Check backend health before accepting jobs."""
        try:
            # Use direct client check instead of HTTP to avoid connection issues
            from services.fiqa_api.clients import get_qdrant_client, ensure_qdrant_connection
            
            client = get_qdrant_client()
            if client is None:
                logger.error("Qdrant client not initialized")
                return False
            
            # Quick health check
            return ensure_qdrant_connection()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def run(self, job_id: str, cmd: List[str], config: Optional[Dict] = None) -> Dict:
        """
        Submit a job to the queue.
        
        Args:
            job_id: Unique job ID
            cmd: Command to execute
            config: Optional V10 experiment config
            
        Returns:
            Dict with job_id, status, position
            
        Raises:
            Full: If queue is full
            RuntimeError: If health check fails
        """
        # Check health
        if not self._check_health():
            raise RuntimeError("依赖未就绪: backend health check failed")
        
        # Check queue capacity
        if self.queue.full():
            raise Full("Queue is full")
        
        # V10.7: Sanitize config before creating job
        if config is not None:
            config = self._sanitize_config(copy.deepcopy(config))
        
        # Create job
        job = Job(job_id=job_id, status="QUEUED", cmd=cmd, config=config)
        
        with self.lock:
            self.state[job_id] = job
            self.tail_cache[job_id] = deque(maxlen=1000)
            self._persist_state()
        
        # Enqueue
        try:
            position = self.queue.qsize() + 1  # Approximate position
            self.queue.put(job, block=False)
            logger.info(f"Job {job_id} queued (position={position})")
            return {
                "job_id": job_id,
                "status": "QUEUED",
                "position": position
            }
        except Full:
            # Clean up state
            with self.lock:
                self.state.pop(job_id, None)
                self.tail_cache.pop(job_id, None)
            raise
    
    def _worker_loop(self):
        """Main worker loop: process jobs from queue."""
        logger.info("Worker loop started")
        
        while self.running:
            try:
                # Get job from queue
                job = self.queue.get(timeout=1)
                
                # Check if job should run
                with self.lock:
                    if job.job_id not in self.state:
                        # Job was removed, skip
                        continue
                
                logger.info(f"Worker starting job {job.job_id}")
                
                # Update status
                with self.lock:
                    job.status = "RUNNING"
                    job.started_at = datetime.now().isoformat()
                    self._persist_state()
                
                # Run subprocess
                self._spawn_subprocess(job)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
    
    def _spawn_subprocess(self, job: Job):
        """Spawn subprocess and manage logs."""
        log_file = self.logs_dir / f"{job.job_id}.log"
        pid_file = self.pids_dir / f"{job.job_id}.pid"
        
        # Log spawn cwd for debugging
        logger.info(f"spawn cwd={self.project_root}")
        
        try:
            # Build absolute paths
            # Use EXPERIMENTS_ROOT env var if set, otherwise fallback to repo root / experiments
            experiments_root = os.getenv("EXPERIMENTS_ROOT")
            if experiments_root:
                root = Path(experiments_root).resolve()
            else:
                root = Path(__file__).resolve().parents[2] / "experiments"
                root = root.resolve()
            
            cwd_str = str(Path(__file__).resolve().parents[2])
            
            # V10: Build command if job has config (config-driven mode)
            cmd_to_execute = job.cmd
            config_file = None
            
            if job.config and not job.cmd:
                # V10 mode: Write config.json and build command with --config-file
                # V10.7: Defensive sanitization before writing config.json
                sanitized_config = self._sanitize_config(copy.deepcopy(job.config))
                logger.info(
                    f"RUN.config fast_mode={sanitized_config.get('fast_mode')} "
                    f"sample={sanitized_config.get('sample')} "
                    f"repeats={sanitized_config.get('repeats')} "
                    f"preset={sanitized_config.get('preset_name', 'N/A')}"
                )
                config_file = self.logs_dir / f"{job.job_id}_config.json"
                write_json_atomic(str(config_file), sanitized_config)
                logger.info(f"V10: Wrote sanitized config to {config_file}")
                
                # Also write to job directory for persistence
                job_dir = self._get_job_dir(job.job_id)
                job_dir.mkdir(parents=True, exist_ok=True)
                job_config_file = job_dir / "config.json"
                write_json_atomic(str(job_config_file), sanitized_config)
                logger.info(f"V10: Wrote config to job directory: {job_config_file}")
                
                # Build command with --config-file
                # Use sys.executable to use the same Python interpreter as the current process
                # This ensures the subprocess uses the same environment (venv, dependencies, etc.)
                script = str((root / "fiqa_suite_runner.py").resolve())
                cfg = str(Path(config_file).resolve())
                cmd_to_execute = [
                    sys.executable, "-u", script, "--config-file", cfg
                ]
            
            # Spawn process with process group (Unix) or new console (Windows)
            # Ensure subprocess inherits current process environment to avoid poetry/shell issues
            env = os.environ.copy()
            
            if os.name == 'posix':
                # Unix/Linux/macOS: use setsid to create new process group
                process = subprocess.Popen(
                    cmd_to_execute,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=os.setsid,
                    cwd=cwd_str,
                    env=env
                )
            else:
                # Windows: use CREATE_NEW_PROCESS_GROUP
                process = subprocess.Popen(
                    cmd_to_execute,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    cwd=cwd_str,
                    env=env
                )
            
            job.pid = process.pid
            
            # Write PID file
            write_text_file(str(pid_file), str(job.pid))
            
            with self.lock:
                self._persist_state()
            
            logger.info(f"Job {job.job_id} started (pid={job.pid})")
            
            # Tail log lines and capture for post-completion scan
            log_lines = []
            all_captured_lines = []  # V6: Capture all lines for artifact parsing
            for line in process.stdout:
                line = line.rstrip('\n')
                log_lines.append(line)
                all_captured_lines.append(line)
                
                # Update cache
                with self.lock:
                    if job.job_id in self.tail_cache:
                        self.tail_cache[job.job_id].append(line)
                
                # Write to file periodically
                if len(log_lines) % 100 == 0:
                    with open(log_file, 'a') as f:
                        f.write('\n'.join(log_lines) + '\n')
                    log_lines = []
            
            # Write remaining lines
            if log_lines:
                with open(log_file, 'a') as f:
                    f.write('\n'.join(log_lines) + '\n')
            
            # Wait for completion
            return_code = process.wait()
            
            # V6: Post-completion security scan for ARTIFACTS_JSON
            artifacts = None
            if return_code == 0:
                artifacts = self._parse_artifacts_from_output(all_captured_lines)
            
            # V11: Write metrics.json on completion (if job succeeded)
            if return_code == 0 and job.config:
                try:
                    self._write_job_metrics(job.job_id, artifacts, job.config)
                except Exception as e:
                    logger.error(f"V11: Failed to write metrics.json for job {job.job_id}: {e}", exc_info=True)
            
            # Update status
            with self.lock:
                job.return_code = return_code
                job.finished_at = datetime.now().isoformat()
                job.status = "SUCCEEDED" if return_code == 0 else "FAILED"
                job.artifacts = artifacts
                self._persist_state()
            
            logger.info(f"Job {job.job_id} finished (return_code={return_code})")
            
            # On failure, log detailed error information
            if return_code != 0:
                error_info = {
                    "command": cmd_to_execute,
                    "cwd": cwd_str,
                    "return_code": return_code,
                    "first_50_lines": all_captured_lines[:50],
                    "last_50_lines": all_captured_lines[-50:] if len(all_captured_lines) > 50 else all_captured_lines
                }
                logger.error(
                    f"Job {job.job_id} failed:\n"
                    f"Command: {cmd_to_execute}\n"
                    f"CWD: {cwd_str}\n"
                    f"Return code: {return_code}\n"
                    f"First 50 lines:\n" + "\n".join(error_info["first_50_lines"]) + "\n"
                    f"Last 50 lines:\n" + "\n".join(error_info["last_50_lines"])
                )
            
        except Exception as e:
            # Extract command and cwd from context if available
            cmd_str = str(cmd_to_execute) if 'cmd_to_execute' in locals() else "unknown"
            cwd_str_local = cwd_str if 'cwd_str' in locals() else str(self.project_root)
            all_lines = all_captured_lines if 'all_captured_lines' in locals() else []
            
            error_info = {
                "command": cmd_str,
                "cwd": cwd_str_local,
                "exception": str(e),
                "first_50_lines": all_lines[:50],
                "last_50_lines": all_lines[-50:] if len(all_lines) > 50 else all_lines
            }
            
            logger.error(
                f"Subprocess error for job {job.job_id}: {e}\n"
                f"Command: {cmd_str}\n"
                f"CWD: {cwd_str_local}\n"
                f"First 50 lines:\n" + "\n".join(error_info["first_50_lines"]) + "\n"
                f"Last 50 lines:\n" + "\n".join(error_info["last_50_lines"]),
                exc_info=True
            )
            with self.lock:
                job.return_code = -1
                job.finished_at = datetime.now().isoformat()
                job.status = "FAILED"
                job.progress_hint = f"{str(e)} | Command: {cmd_str} | CWD: {cwd_str_local}"
                self._persist_state()
        
        finally:
            # Clean up PID file
            if pid_file.exists():
                try:
                    pid_file.unlink()
                except:
                    pass
            
            # V10: Clean up config file if it exists
            if config_file and config_file.exists():
                try:
                    config_file.unlink()
                    logger.info(f"V10: Cleaned up config file {config_file}")
                except:
                    pass
    
    def cancel(self, job_id: str) -> Dict:
        """
        Cancel a running job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            Dict with job_id and status
            
        Raises:
            KeyError: If job not found
            ValueError: If job cannot be cancelled
        """
        with self.lock:
            if job_id not in self.state:
                raise KeyError(f"Job {job_id} not found")
            
            job = self.state[job_id]
            
            # Check if cancellable
            if job.status not in ["QUEUED", "RUNNING"]:
                raise ValueError(f"Job {job_id} is {job.status}, cannot cancel")
            
            # If QUEUED, remove from queue and mark as cancelled
            if job.status == "QUEUED":
                job.status = "CANCELLED"
                job.finished_at = datetime.now().isoformat()
                self._persist_state()
                return {"job_id": job_id, "status": "CANCELLED"}
            
            # If RUNNING, kill process
            if job.pid and self._is_process_running(job.pid):
                try:
                    if os.name == 'posix':
                        # Unix/Linux/macOS: use process groups
                        pgid = os.getpgid(job.pid)
                        os.killpg(pgid, signal.SIGTERM)
                        logger.info(f"Sent SIGTERM to job {job_id} (pgid={pgid})")
                        
                        # Wait up to 5 seconds
                        time.sleep(5)
                        
                        # Check if still running
                        if self._is_process_running(job.pid):
                            logger.warning(f"Job {job_id} didn't exit, sending SIGKILL")
                            os.killpg(pgid, signal.SIGKILL)
                    else:
                        # Windows: send SIGTERM then SIGKILL
                        os.kill(job.pid, signal.SIGTERM)
                        time.sleep(2)
                        if self._is_process_running(job.pid):
                            os.kill(job.pid, signal.SIGKILL)
                
                except Exception as e:
                    logger.error(f"Error killing job {job_id}: {e}")
            
            # Update status
            job.status = "CANCELLED"
            job.finished_at = datetime.now().isoformat()
            self._persist_state()
            
            return {"job_id": job_id, "status": "CANCELLED"}
    
    def get_status(self, job_id: str) -> Optional[Job]:
        """Get job status."""
        with self.lock:
            return self.state.get(job_id)
    
    def get_logs(self, job_id: str, tail: int = 200) -> List[str]:
        """Get log tail for a job."""
        with self.lock:
            if job_id not in self.tail_cache:
                return []
            
            deque_obj = self.tail_cache[job_id]
            lines = list(deque_obj)[-tail:]
            return lines
    
    def _persist_state(self):
        """
        Persist state to disk with file lock protecting read-modify-write cycle.
        
        This ensures concurrent writes don't cause last-write-wins data loss:
        1. Acquire lock
        2. Read latest jobs.json
        3. Merge current state with persisted state
        4. Write atomically with fsync
        5. Release lock
        """
        try:
            from services.fiqa_api.utils.locks import file_lock
            
            with file_lock(self.jobs_lock_path):
                # Read latest persisted state (may have updates from other processes)
                persisted_jobs = read_json(str(self.jobs_file), {})
                persisted_jobs_dict = {j.get("job_id"): j for j in persisted_jobs.get("jobs", [])}
                
                # Build current state
                current_jobs_dict = {job.job_id: job.to_dict() for job in self.state.values()}
                
                # Merge: current state takes precedence (in-memory is authoritative for active jobs)
                # But preserve jobs that exist in persisted but not in memory (edge case)
                merged_jobs = list(current_jobs_dict.values())
                
                # Add persisted jobs that aren't in current state (e.g., from another process)
                for job_id, job_data in persisted_jobs_dict.items():
                    if job_id not in current_jobs_dict:
                        # Only keep if it's a terminal state (not QUEUED/RUNNING which might be stale)
                        if job_data.get("status") in ["SUCCEEDED", "FAILED", "CANCELLED", "ABORTED"]:
                            merged_jobs.append(job_data)
                
                # Prepare final jobs data
                jobs_data = {
                    "jobs": merged_jobs,
                    "updated_at": datetime.now().isoformat()
                }
                
                # Write atomically (lock is held, so no race condition)
                write_json_atomic(str(self.jobs_file), jobs_data)
        except Exception as e:
            logger.error(f"Failed to persist state: {e}")
    
    def get_queue_status(self) -> Dict:
        """Get current queue and running jobs status."""
        with self.lock:
            queued = [j.job_id for j in self.state.values() if j.status == "QUEUED"]
            running = [j.job_id for j in self.state.values() if j.status == "RUNNING"]
            return {
                "queued": queued,
                "running": running,
                "queue_size": self.queue.qsize()
            }
    
    def list_all_jobs(self, limit: int = 100) -> List[Dict]:
        """
        Get all jobs in reverse chronological order.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dictionaries
        """
        with self.lock:
            jobs = sorted(
                self.state.values(),
                key=lambda j: j.last_update_at,
                reverse=True
            )
            return [job.to_dict() for job in jobs[:limit]]
    
    def get_job_detail(self, job_id: str) -> Optional[Dict]:
        """
        Get detailed job information.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job dictionary with full details, or None if not found
        """
        with self.lock:
            job = self.state.get(job_id)
            if job is None:
                return None
            return job.to_dict()
    
    def rerun(self, job_id: str, overrides: Dict[str, Any] | None = None) -> Job:
        """
        V11: Rerun a completed job with optional parameter overrides.
        
        Args:
            job_id: Original job ID to rerun
            overrides: Optional dict with allowed overrides: {top_k, repeats, fast_mode}
            
        Returns:
            New Job instance queued for execution
            
        Raises:
            KeyError: If original job not found
            ValueError: If original job hasn't completed or invalid overrides
        """
        with self.lock:
            original_job = self.state.get(job_id)
            if original_job is None:
                raise KeyError(f"Job {job_id} not found")
            
            # Only allow rerunning completed jobs
            if original_job.status not in ["SUCCEEDED", "FAILED"]:
                raise ValueError(f"Job {job_id} is {original_job.status}, only SUCCEEDED/FAILED jobs can be rerun")
        
        # Read original config.json
        job_dir = self._get_job_dir(job_id)
        config_file = job_dir / "config.json"
        if not config_file.exists():
            raise ValueError(f"Original job {job_id} has no config.json")
        
        original_config = read_json(str(config_file), {})
        if not original_config:
            raise ValueError(f"Original job {job_id} config.json is empty")
        
        # Get git_sha (try from config, or get current)
        git_sha = original_config.get("git_sha") or self._get_git_sha()
        
        # Create new config with overrides
        # Merge order: defaults → preset (original_config) → overrides (APPLIED FIRST to get final fast_mode) → fast caps (only if final fast_mode==True)
        # Note: Overrides are applied first to determine final fast_mode, then caps are applied based on final fast_mode
        new_config = copy.deepcopy(original_config)
        
        # Step 1: Apply overrides FIRST (frontend wins) - this determines final fast_mode
        if overrides:
            # Normalize legacy rerank_topk -> rerank_top_k
            if "rerank_topk" in overrides and "rerank_top_k" not in overrides:
                overrides = {**overrides, "rerank_top_k": overrides["rerank_topk"]}
                overrides.pop("rerank_topk", None)

            allowed_keys = {"top_k", "repeats", "fast_mode", "rerank", "rerank_top_k", "sample", "bm25_k"}
            for key, value in overrides.items():
                if key not in allowed_keys:
                    raise ValueError(f"Override key '{key}' not allowed. Allowed: {allowed_keys}")
                new_config[key] = value
                # Apply to first group if group-level param
                if key == "rerank" and "groups" in new_config and isinstance(new_config["groups"], list) and len(new_config["groups"]) > 0:
                    new_config["groups"][0]["rerank"] = value
                if key == "rerank_top_k" and "groups" in new_config and isinstance(new_config["groups"], list) and len(new_config["groups"]) > 0:
                    new_config["groups"][0]["rerank_top_k"] = value
        
        # Step 2: Apply fast caps ONLY if final fast_mode is True (after overrides)
        fast_mode_value = new_config.get("fast_mode", False)
        
        # Apply fast caps only when fast_mode==True
        if fast_mode_value:
            # Cap RRF k for hybrid groups
            if "groups" in new_config and isinstance(new_config["groups"], list):
                for group in new_config["groups"]:
                    if isinstance(group, dict) and group.get("use_hybrid") and "rrf_k" in group:
                        FAST_RRF_K = 40
                        group["rrf_k"] = min(int(group.get("rrf_k", 60)), FAST_RRF_K)
                    if isinstance(group, dict) and group.get("rerank") and "rerank_top_k" in group:
                        FAST_RERANK_TOPK = 10
                        group["rerank_top_k"] = min(int(group.get("rerank_top_k", 20)), FAST_RERANK_TOPK)
            # Cap top-level rerank_top_k if present
            if "rerank_top_k" in new_config:
                FAST_RERANK_TOPK = 10
                new_config["rerank_top_k"] = min(int(new_config["rerank_top_k"]), FAST_RERANK_TOPK)
        
        # Sanitize config (sets schema_version=11, removes None fields)
        new_config = self._sanitize_config(new_config)

        # One-time audit logs for override precedence (subset of key params)
        try:
            audit_subset = {
                "top_k": new_config.get("top_k"),
                "rrf_k": new_config.get("groups", [{}])[0].get("rrf_k") if new_config.get("groups") else None,
                "rerank": new_config.get("rerank") or (new_config.get("groups", [{}])[0].get("rerank") if new_config.get("groups") else None),
                "rerank_top_k": new_config.get("rerank_top_k") or (new_config.get("groups", [{}])[0].get("rerank_top_k") if new_config.get("groups") else None),
                "fast_mode": new_config.get("fast_mode"),
            }
            logger.info(f"[OVR-AUDIT] raw_overrides={json.dumps(overrides, ensure_ascii=False) if overrides else None}")
            logger.info(f"[OVR-AUDIT] final_config={json.dumps(audit_subset, ensure_ascii=False)}")
        except Exception:
            pass
        
        # Set git_sha in config
        new_config["git_sha"] = git_sha
        
        # Generate new job_id
        new_job_id = str(uuid.uuid4())
        new_job_dir = self._get_job_dir(new_job_id)
        new_job_dir.mkdir(parents=True, exist_ok=True)
        
        # Write config.json to logs/ (temporary, for --config-file)
        temp_config_file = self.logs_dir / f"{new_job_id}_config.json"
        write_json_atomic(str(temp_config_file), new_config)
        
        # Also write to job directory for persistence
        job_config_file = new_job_dir / "config.json"
        write_json_atomic(str(job_config_file), new_config)
        
        # Create new job (empty cmd, JobRunner will build it from config)
        new_job = Job(
            job_id=new_job_id,
            status="QUEUED",
            cmd=[],  # Empty, will be built from config
            config=new_config
        )
        
        # Persist state atomically
        with self.lock:
            self.state[new_job_id] = new_job
            self.tail_cache[new_job_id] = deque(maxlen=1000)
            self._persist_state()
        
        # Enqueue job
        try:
            self.queue.put(new_job, block=False)
            logger.info(f"V11: Rerun job {new_job_id} created from {job_id} (overrides={overrides})")
            return new_job
        except Full:
            # Clean up state if queue is full
            with self.lock:
                self.state.pop(new_job_id, None)
                self.tail_cache.pop(new_job_id, None)
                self._persist_state()
            raise Full("Queue is full")


# ========================================
# Singleton Access
# ========================================

def get_job_manager() -> JobManager:
    """Get JobManager singleton instance."""
    return JobManager()

