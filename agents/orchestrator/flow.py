from __future__ import annotations

import json
import hashlib
import logging
import subprocess
import tempfile
import threading
import time
import uuid
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

from tools.ab_test import run_ab
from tools.draw_pareto import render_pareto_chart
from tools.fetch_metrics import (
    MetricsAggregationError,
    aggregate_metrics,
    write_fail_topn_csv,
)
from tools.run_eval import (
    HealthCheckError,
    RunEvalError,
    RunEvalResult,
    RunnerTimeoutError,
    check_backend_health,
    run_grid_task,
    run_smoke,
)
from agents.orchestrator import memory, planner, reflection
from agents.orchestrator.config_loader import get_orchestrator_config
from agents.orchestrator.fingerprint import compute_fingerprints
from agents.orchestrator.sla import verify_sla
from observe.logging import EventLogger

logger = logging.getLogger(__name__)

RUN_ID_PREFIX = "orch"
PIPELINE_STAGES: List[str] = ["SMOKE", "GRID", "AB", "SELECT", "PUBLISH"]


class DatasetBlockError(RuntimeError):
    """Raised when dataset is disabled or not in whitelist."""
    def __init__(self, message: str, code: str = "DATASET_BLOCK", payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.payload = payload or {}


class AlignmentBlockError(RuntimeError):
    """Raised when alignment check fails."""
    def __init__(self, message: str, code: str = "ALIGNMENT_BLOCK", payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.payload = payload or {}


def _default_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _apply_host_alias(url: str, aliases: Dict[str, str]) -> str:
    """Apply host alias mapping to URL."""
    if not url:
        return url
    parsed = urlparse(url)
    alias = aliases.get(parsed.hostname)
    if alias:
        netloc = alias if parsed.port is None else f"{alias}:{parsed.port}"
        parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)
    return url


@dataclass
class ExperimentPlan:
    """Configuration for a full orchestrated experiment run."""

    dataset: str
    sample_size: int
    search_space: Dict[str, Any]
    budget: Dict[str, Any] = field(default_factory=dict)
    concurrency: Optional[int] = None
    baseline_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ExperimentPlan":
        """Construct an ExperimentPlan from an API payload."""
        if "dataset" not in payload:
            raise ValueError("`dataset` is required in ExperimentPlan")
        if "sample_size" not in payload:
            raise ValueError("`sample_size` is required in ExperimentPlan")
        if "search_space" not in payload:
            raise ValueError("`search_space` is required in ExperimentPlan")

        return cls(
            dataset=str(payload["dataset"]),
            sample_size=int(payload["sample_size"]),
            search_space=dict(payload["search_space"]),
            budget=dict(payload.get("budget") or {}),
            concurrency=(
                int(payload["concurrency"]) if payload.get("concurrency") else None
            ),
            baseline_id=str(payload["baseline_id"])
            if payload.get("baseline_id")
            else None,
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-serializable dictionary."""
        return json.loads(json.dumps(asdict(self)))


@dataclass
class ExperimentReport:
    """Summary artifact returned once the orchestrator completes."""

    run_id: str
    status: str
    created_at: str = field(default_factory=_default_timestamp)
    artifacts: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))


class OrchestratorFlow:
    """Entry point for experiment orchestration phases."""

    def __init__(
        self,
        logger: Optional[EventLogger] = None,
        run_memory: Optional[memory.RunMemory] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.config = config or get_orchestrator_config()
        reports_dir = Path(self.config.get("reports_dir", "reports")).resolve()

        if logger is None:
            events_dir = reports_dir / "events"
            events_dir.mkdir(parents=True, exist_ok=True)
            logger = EventLogger(base_dir=events_dir)

        if run_memory is None:
            memory_dir = reports_dir / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            run_memory = memory.RunMemory(base_dir=memory_dir)

        self.logger = logger
        self.memory = run_memory
        self.reports_dir = reports_dir
        self._policies_cache: Optional[Dict[str, Any]] = None

        run_cfg = self.config.get("run", {})
        concurrency_limit = int(run_cfg.get("concurrency_limit", 2))
        queue_size = int(run_cfg.get("queue_size", 10))
        
        self._executor = ThreadPoolExecutor(max_workers=concurrency_limit)
        self._futures: Dict[str, Future] = {}
        self._futures_lock = threading.Lock()
        self._queue: deque = deque(maxlen=queue_size)
        self._queue_lock = threading.Lock()
        self._run_metadata: Dict[str, Dict[str, Any]] = {}  # run_id -> {started_at, finished_at, fingerprints, ...}
        self._metadata_lock = threading.Lock()

    def _build_error_payload(self, exc: Exception) -> Dict[str, Any]:
        payload = {
            "type": getattr(exc, "error_type", exc.__class__.__name__),
            "msg": str(exc),
        }
        hint = getattr(exc, "hint", None)
        if hint:
            payload["hint"] = hint
        details = getattr(exc, "details", None)
        if details:
            payload["details"] = details
        return payload

    def _log_stage_failure(
        self,
        run_id: str,
        stage: str,
        exc: Exception,
        duration_ms: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload: Dict[str, Any] = {"stage": stage}
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        if extra:
            payload.update(extra)
        payload["error"] = self._build_error_payload(exc)
        self.logger.log_stage_event(run_id, stage=stage, status="failed", payload=payload)

    def _run_reflection(
        self,
        run_id: str,
        stage: str,
        kpis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run reflection after a stage completes.
        
        Args:
            run_id: Run ID
            stage: Stage name
            kpis: Key performance indicators (metrics, duration_ms, etc.)
        
        Returns:
            Reflection summary dict
        """
        # Get SLA verification
        metrics = kpis.get("metrics", {})
        sla_policy_path = self.config.get("sla_policy_path")
        sla_result = verify_sla(metrics, sla_policy_path)
        
        # Get LLM config
        llm_cfg = self.config.get("llm", {})
        
        # Get cumulative spent cost from memory
        memory_record = self.memory.get(run_id)
        spent_cost = 0.0
        if memory_record:
            spent_cost = float(memory_record.metadata.get("reflection_spent_cost", 0.0))
        
        # Log REFLECT_STARTED
        self.logger.log_event(
            run_id,
            "REFLECT_STARTED",
            {
                "stage": stage.upper(),
                "timestamp": _default_timestamp(),
            },
        )
        
        # Call reflection.summarize() with spent_cost
        reflection_result = reflection.summarize(
            stage=stage,
            kpis=kpis,
            sla=sla_result,
            llm_cfg=llm_cfg,
            spent_cost=spent_cost,
        )
        
        # Update spent cost
        new_cost = reflection_result.get("cost_usd", 0.0)
        spent_cost += new_cost
        
        # Write reflection files (full and lite)
        run_dir = self.reports_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        stage_upper = stage.upper()
        
        # Write full reflection file
        reflection_file = run_dir / f"reflection_{stage_upper}.md"
        with reflection_file.open("w", encoding="utf-8") as fp:
            fp.write(reflection_result.get("rationale_md", ""))
        
        # Write lite reflection file
        reflection_lite_file = run_dir / f"reflection_{stage_upper}_lite.md"
        with reflection_lite_file.open("w", encoding="utf-8") as fp:
            fp.write(reflection_result.get("rationale_md_lite", ""))
        
        # Prepare event payload (exclude sensitive data)
        event_payload = {
            "stage": stage_upper,
            "model": reflection_result.get("model", "rule-engine"),
            "tokens": reflection_result.get("tokens", 0),
            "cost_usd": reflection_result.get("cost_usd", 0.0),
            "confidence": reflection_result.get("confidence", 0.5),
            "cache_hit": reflection_result.get("cache_hit", False),
            "blocked": reflection_result.get("blocked", False),
            "elapsed_ms": reflection_result.get("elapsed_ms", 0),
            "timestamp": _default_timestamp(),
        }
        
        # Add prompt_hash if present (for LLM calls)
        if "prompt_hash" in reflection_result:
            event_payload["prompt_hash"] = reflection_result["prompt_hash"]
        
        # Log REFLECT_DONE
        self.logger.log_event(
            run_id,
            "REFLECT_DONE",
            event_payload,
        )
        
        # Store reflection result in memory for retrieval
        if memory_record:
            existing_reflections = memory_record.metadata.get("reflections", {})
        else:
            existing_reflections = {}
        
        existing_reflections[stage_upper] = {
            "next_actions": reflection_result.get("next_actions", []),
        }
        
        self.memory.update_metadata(
            run_id,
            {
                "reflections": existing_reflections,
                "reflection_spent_cost": spent_cost,
            },
        )
        
        return reflection_result

    def start(self, plan: ExperimentPlan, *, dry_run: Optional[bool] = None, commit: bool = False) -> Dict[str, Any]:
        """Start an experiment run with fingerprinting, idempotency, and dry-run support."""
        run_cfg = self.config.get("run", {})
        if dry_run is None:
            # If commit=False, force dry_run=True; if commit=True, dry_run=False unless config says otherwise
            if not commit:
                dry_run = True
            else:
                dry_run = bool(run_cfg.get("dry_run_default", False))
        
        # Validate and inject dataset/queries_path/qrels_path from policy if needed
        datasets_cfg = self.config.get("datasets", {})
        qrels_map = datasets_cfg.get("qrels_map", {})
        queries_map = datasets_cfg.get("queries_map", {})
        
        # If policy is specified, inject dataset/queries_path/qrels_path from policy
        policy_id = plan.baseline_id or self.config.get("baseline_policy")
        if policy_id:
            try:
                policy = self._load_policy_config(policy_id)
                # Inject from policy if not explicitly provided
                if not plan.metadata.get("dataset") and policy.get("dataset"):
                    plan.metadata["dataset"] = policy["dataset"]
                if not plan.metadata.get("queries_path") and policy.get("queries_path"):
                    plan.metadata["queries_path"] = policy["queries_path"]
                if not plan.metadata.get("qrels_path") and policy.get("qrels_path"):
                    plan.metadata["qrels_path"] = policy["qrels_path"]
            except Exception as e:
                logger.warning(f"Failed to load policy {policy_id}: {e}")
        
        # Validate three-piece consistency: dataset, queries_path, qrels_path
        plan_dataset = plan.metadata.get("dataset") or plan.dataset
        plan_queries_path = plan.metadata.get("queries_path")
        plan_qrels_path = plan.metadata.get("qrels_path")
        
        # Try to get from config maps if not in plan
        if not plan_queries_path:
            plan_queries_path = queries_map.get(plan_dataset)
        if not plan_qrels_path:
            plan_qrels_path = qrels_map.get(plan_dataset)
        
        # Validate all three are present
        if not plan_dataset:
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            self.logger.log_event(
                run_id=run_id,
                event_type="ALIGNMENT_BLOCK",
                payload={
                    "hint": "dataset is required. Provide it explicitly or via policy.",
                    "timestamp": _default_timestamp(),
                },
            )
            raise RuntimeError("ALIGNMENT_BLOCK: dataset is required")
        
        if not plan_queries_path:
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            self.logger.log_event(
                run_id=run_id,
                event_type="ALIGNMENT_BLOCK",
                payload={
                    "dataset": plan_dataset,
                    "hint": f"queries_path is required for dataset '{plan_dataset}'. Provide it explicitly, via policy, or ensure it's in config.datasets.queries_map",
                    "timestamp": _default_timestamp(),
                },
            )
            raise RuntimeError(f"ALIGNMENT_BLOCK: queries_path is required for dataset '{plan_dataset}'")
        
        if not plan_qrels_path:
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            self.logger.log_event(
                run_id=run_id,
                event_type="ALIGNMENT_BLOCK",
                payload={
                    "dataset": plan_dataset,
                    "hint": f"qrels_path is required for dataset '{plan_dataset}'. Provide it explicitly, via policy, or ensure it's in config.datasets.qrels_map",
                    "timestamp": _default_timestamp(),
                },
            )
            raise RuntimeError(f"ALIGNMENT_BLOCK: qrels_path is required for dataset '{plan_dataset}'")
        
        # Store validated paths in plan metadata
        plan.metadata["dataset"] = plan_dataset
        plan.metadata["queries_path"] = plan_queries_path
        plan.metadata["qrels_path"] = plan_qrels_path
        
        # Compute fingerprints
        fingerprints = compute_fingerprints(plan, self.config)
        fingerprint_key = f"{fingerprints['data_fingerprint']}:{fingerprints['code_commit']}:{fingerprints['policy_hash']}:{fingerprints['args_hash']}"
        
        # Check idempotency: same fingerprint already running or completed
        existing_run_id = self._find_existing_run(fingerprint_key)
        if existing_run_id:
            return {"run_id": existing_run_id, "idempotent": True, "dry_run": False}
        
        # Dataset validation (whitelist/disabled check)
        whitelist = datasets_cfg.get("whitelist", [])
        disabled = datasets_cfg.get("disabled", [])
        
        if plan.dataset in disabled:
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            payload = {
                "dataset": plan.dataset,
                "hint": f"Dataset '{plan.dataset}' is disabled. Use one of: {', '.join(whitelist)}",
                "timestamp": _default_timestamp(),
            }
            self.logger.log_event(
                run_id=run_id,
                event_type="DATASET_BLOCK",
                payload=payload,
            )
            raise DatasetBlockError(
                f"Dataset '{plan.dataset}' is disabled",
                code="DATASET_BLOCK",
                payload=payload,
            )
        
        if whitelist and plan.dataset not in whitelist:
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            payload = {
                "dataset": plan.dataset,
                "hint": f"Dataset '{plan.dataset}' not in whitelist. Use one of: {', '.join(whitelist)}",
                "timestamp": _default_timestamp(),
            }
            self.logger.log_event(
                run_id=run_id,
                event_type="DATASET_BLOCK",
                payload=payload,
            )
            raise DatasetBlockError(
                f"Dataset '{plan.dataset}' not in whitelist",
                code="DATASET_BLOCK",
                payload=payload,
            )
        
        # Alignment check: verify qrels doc_ids are 100% present in collection
        # Use validated qrels_path from plan.metadata
        qrels_path = plan.metadata.get("qrels_path")
        if not qrels_path:
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            payload = {
                "dataset": plan.dataset,
                "hint": f"qrels_path is required for dataset '{plan.dataset}'. Ensure it's in config.datasets.qrels_map or provided via policy.",
                "timestamp": _default_timestamp(),
            }
            self.logger.log_event(
                run_id=run_id,
                event_type="ALIGNMENT_BLOCK",
                payload=payload,
            )
            raise AlignmentBlockError(
                f"qrels_path is required for dataset '{plan.dataset}'",
                code="ALIGNMENT_BLOCK",
                payload=payload,
            )
        
        # Resolve qrels path relative to repo root
        repo_root = Path(__file__).resolve().parent.parent.parent
        qrels_full_path = repo_root / qrels_path if not Path(qrels_path).is_absolute() else Path(qrels_path)
        
        if not qrels_full_path.exists():
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            payload = {
                "dataset": plan.dataset,
                "qrels": str(qrels_path),
                "hint": f"Qrels file not found: {qrels_full_path}",
                "timestamp": _default_timestamp(),
            }
            self.logger.log_event(
                run_id=run_id,
                event_type="ALIGNMENT_BLOCK",
                payload=payload,
            )
            raise AlignmentBlockError(
                f"Qrels file not found: {qrels_path}",
                code="ALIGNMENT_BLOCK",
                payload=payload,
            )
        
        # Get Qdrant host from config with alias resolution
        base_url = self.config.get("base_url", "http://localhost:8000")
        host_aliases = self.config.get("host_aliases", {})
        alias_base = _apply_host_alias(base_url, host_aliases)
        
        # Extract Qdrant host from base_url (assume Qdrant is on port 6333)
        # Try to find Qdrant host from allowed_hosts or use default
        # In Docker, prefer container name; fallback to localhost
        qdrant_host = "http://127.0.0.1:6333"  # Default Qdrant port
        allowed_hosts = self.config.get("allowed_hosts", [])
        
        # Prefer container name if available (for Docker environments)
        container_host = None
        for host in allowed_hosts:
            if "searchforge-qdrant" in str(host) and ":6333" in str(host):
                container_host = f"http://{host}" if not host.startswith("http") else host
                break
        
        # If container host found, use it; otherwise check for localhost:6333
        if container_host:
            qdrant_host = container_host
        else:
            for host in allowed_hosts:
                if ":6333" in str(host):
                    qdrant_host = f"http://{host}" if not host.startswith("http") else host
                    break
        
        # Apply alias to Qdrant host
        qdrant_host = _apply_host_alias(qdrant_host, host_aliases)
        
        # Call alignment auditor as subprocess
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_json:
                tmp_json_path = tmp_json.name
            
            cmd = [
                "python", "-m", "tools.eval.id_alignment_auditor",
                "--host", qdrant_host,
                "--collection", plan.dataset,
                "--qrels", str(qrels_full_path),
                "--json-out", tmp_json_path,
            ]
            
            logger.info(f"Running alignment check: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            # Load alignment result from JSON file
            alignment_result = {}
            if Path(tmp_json_path).exists():
                try:
                    with open(tmp_json_path, 'r', encoding='utf-8') as f:
                        alignment_result = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load alignment result JSON: {e}")
                finally:
                    Path(tmp_json_path).unlink(missing_ok=True)
            
            # Check if subprocess failed or alignment check failed
            if result.returncode != 0:
                run_id = generate_run_id()
                self.logger.initialize(run_id)
                payload = {
                    "dataset": plan.dataset,
                    "collection": plan.dataset,
                    "qrels": str(qrels_path),
                    "checked": alignment_result.get("checked", 0),
                    "found": alignment_result.get("found", 0),
                    "mismatch": alignment_result.get("mismatch", 0),
                    "mismatch_rate": alignment_result.get("mismatch_rate", 1.0),
                    "hint": f"Alignment check failed (exit code {result.returncode}). Verify qrels file and collection alignment.",
                    "stderr": result.stderr[:500] if result.stderr else None,
                    "timestamp": _default_timestamp(),
                }
                self.logger.log_event(
                    run_id=run_id,
                    event_type="ALIGNMENT_BLOCK",
                    payload=payload,
                )
                raise AlignmentBlockError(
                    f"Alignment check failed: {result.stderr[:200] if result.stderr else 'unknown error'}",
                    code="ALIGNMENT_BLOCK",
                    payload=payload,
                )
            
            mismatch_rate = alignment_result.get("mismatch_rate", 1.0)
            
            if mismatch_rate > 0:
                run_id = generate_run_id()
                self.logger.initialize(run_id)
                payload = {
                    "dataset": plan.dataset,
                    "collection": plan.dataset,
                    "qrels": str(qrels_path),
                    "checked": alignment_result.get("checked", 0),
                    "found": alignment_result.get("found", 0),
                    "mismatch": alignment_result.get("mismatch", 0),
                    "mismatch_rate": mismatch_rate,
                    "hint": "qrels doc_id must be 100% present in collection; verify you are using fiqa_qrels_hard_50k_v1.tsv (numeric ids).",
                    "timestamp": _default_timestamp(),
                }
                self.logger.log_event(
                    run_id=run_id,
                    event_type="ALIGNMENT_BLOCK",
                    payload=payload,
                )
                raise AlignmentBlockError(
                    f"Alignment check failed: {alignment_result.get('mismatch', 0)}/{alignment_result.get('checked', 0)} "
                    f"qrels doc_ids not found in collection '{plan.dataset}'",
                    code="ALIGNMENT_BLOCK",
                    payload=payload,
                )
            
            # Store alignment info in plan metadata
            plan.metadata["alignment"] = {
                "checked": alignment_result.get("checked", 0),
                "found": alignment_result.get("found", 0),
                "mismatch": alignment_result.get("mismatch", 0),
                "mismatch_rate": mismatch_rate,
            }
        except AlignmentBlockError:
            # Re-raise alignment block errors
            raise
        except subprocess.TimeoutExpired:
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            payload = {
                "dataset": plan.dataset,
                "collection": plan.dataset,
                "qrels": str(qrels_path),
                "hint": "Alignment check timed out after 5 minutes",
                "timestamp": _default_timestamp(),
            }
            self.logger.log_event(
                run_id=run_id,
                event_type="ALIGNMENT_BLOCK",
                payload=payload,
            )
            raise AlignmentBlockError(
                "Alignment check timed out",
                code="ALIGNMENT_BLOCK",
                payload=payload,
            )
        except Exception as e:
            # If alignment check fails due to technical issues, log and block
            logger.error(f"Alignment check failed: {e}", exc_info=True)
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            payload = {
                "dataset": plan.dataset,
                "collection": plan.dataset,
                "qrels": str(qrels_path),
                "hint": f"Alignment check failed due to technical error: {str(e)[:200]}",
                "timestamp": _default_timestamp(),
            }
            self.logger.log_event(
                run_id=run_id,
                event_type="ALIGNMENT_BLOCK",
                payload=payload,
            )
            raise AlignmentBlockError(
                f"Alignment check failed: {str(e)}",
                code="ALIGNMENT_BLOCK",
                payload=payload,
            )
        
        # Budget check
        budget_error = self._check_budget(plan)
        if budget_error:
            run_id = generate_run_id()
            self.logger.initialize(run_id)
            self.logger.log_event(
                run_id=run_id,
                event_type="BUDGET_BLOCK",
                payload={
                    "error": budget_error,
                    "hint": "调整预算限制或减少并发/样本量",
                    "timestamp": _default_timestamp(),
                },
            )
            raise RuntimeError(f"Budget check failed: {budget_error}")
        
        run_id = generate_run_id()
        started_at = _default_timestamp()
        
        self.logger.initialize(run_id)
        
        # Store metadata
        with self._metadata_lock:
            self._run_metadata[run_id] = {
                "started_at": started_at,
                "fingerprints": fingerprints,
                "fingerprint_key": fingerprint_key,
                "dry_run": dry_run,
            }
        
        if dry_run and not commit:
            # Dry-run: only plan and validate
            return self._dry_run_plan(run_id, plan, fingerprints, started_at)
        
        # Actual execution
        datasets_cfg = self.config.get("datasets", {})
        qrels_map = datasets_cfg.get("qrels_map", {})
        queries_map = datasets_cfg.get("queries_map", {})
        
        # Use validated paths from plan.metadata
        plan_dataset = plan.metadata.get("dataset", plan.dataset)
        qrels_path = plan.metadata.get("qrels_path") or qrels_map.get(plan_dataset)
        queries_path = plan.metadata.get("queries_path") or queries_map.get(plan_dataset)
        
        self.logger.log_event(
            run_id=run_id,
            event_type="RUN_STARTED",
            payload={
                "dataset": plan_dataset,
                "qrels_path": qrels_path,
                "queries_path": queries_path,
                "id_normalization": "digits-only/no-leading-zero",
                "sample_size": plan.sample_size,
                "baseline_id": plan.baseline_id,
                "fingerprints": fingerprints,
                "timestamp": started_at,
            },
        )
        
        self.memory.register_plan(run_id, {**plan.to_dict(), "fingerprints": fingerprints})
        
        # Queue management
        with self._queue_lock:
            queue_pos = len(self._queue)
            if len(self._queue) >= self._queue.maxlen:
                raise RuntimeError(f"Queue full (max {self._queue.maxlen})")
            self._queue.append(run_id)
        
        with self._futures_lock:
            future = self._executor.submit(self._run_pipeline_with_cleanup, run_id, plan, queue_pos)
            self._futures[run_id] = future
        
        return {"run_id": run_id, "idempotent": False, "dry_run": False, "queue_pos": queue_pos}

    def get_status(self, run_id: str, detail: str = "lite") -> Dict[str, Any]:
        events = self.logger.read_events(run_id, limit=None)
        if not events:
            raise KeyError(run_id)

        stage = "PENDING"
        latest_metrics: Dict[str, Any] = {}
        status = "running"
        started_at = None
        finished_at = None

        for event in reversed(events):
            event_type = event.get("event_type", "")
            payload = event.get("payload") or {}
            created_at = event.get("created_at")
            
            if "metrics" in payload and not latest_metrics:
                latest_metrics = payload["metrics"]  # type: ignore[assignment]
            if event_type.endswith("_FAILED") or event_type == "RUN_FAILED":
                stage = payload.get("stage", stage)
                status = "failed"
                if not finished_at:
                    finished_at = created_at
                break
            if event_type == "RUN_COMPLETED":
                status = "completed"
                stage = payload.get("stage", PIPELINE_STAGES[-1])
                if not finished_at:
                    finished_at = created_at
                continue
            if event_type == "RUN_STARTED":
                if not started_at:
                    started_at = created_at
            if event_type.endswith("_DONE"):
                stage = payload.get("stage", stage)
                if status not in {"failed", "completed"}:
                    status = "running"
                break
            if event_type.endswith("_STARTED") or event_type.endswith("_START"):
                stage = payload.get("stage", stage)
                status = "running"

        stage = stage or "SMOKE"
        stage_upper = stage.upper()
        stage_index = PIPELINE_STAGES.index(stage_upper) if stage_upper in PIPELINE_STAGES else -1
        completed = stage_index + 1 if stage_index >= 0 and status in {"completed", "running"} else 0
        progress = {
            "current_stage": stage_upper,
            "completed": completed,
            "total": len(PIPELINE_STAGES),
            "status": status,
        }
        
        # Get metadata
        with self._metadata_lock:
            metadata = self._run_metadata.get(run_id, {})
            if not started_at:
                started_at = metadata.get("started_at")
            if not finished_at and status in {"completed", "failed"}:
                finished_at = metadata.get("finished_at")
        
        # Calculate queue position
        queue_pos = None
        with self._queue_lock:
            try:
                queue_pos = list(self._queue).index(run_id)
            except ValueError:
                pass
        
        # Collect reflections from REFLECT_DONE events
        reflections = []
        for event in events:
            event_type = event.get("event_type", "")
            if event_type == "REFLECT_DONE":
                payload = event.get("payload") or {}
                reflection_entry = {
                    "stage": payload.get("stage", ""),
                    "model": payload.get("model", "rule-engine"),
                    "tokens": payload.get("tokens", 0),
                    "cost_usd": payload.get("cost_usd", 0.0),
                    "confidence": payload.get("confidence", 0.5),
                    "cache_hit": payload.get("cache_hit", False),
                    "blocked": payload.get("blocked", False),
                    "elapsed_ms": payload.get("elapsed_ms", 0),
                    "created_at": event.get("created_at"),
                }
                # Add prompt_hash if present
                if "prompt_hash" in payload:
                    reflection_entry["prompt_hash"] = payload["prompt_hash"]
                
                # Load rationale_md from reflection file (full or lite based on detail)
                run_dir = self.reports_dir / run_id
                stage_name = payload.get("stage", "").upper()
                
                if detail == "full":
                    reflection_file = run_dir / f"reflection_{stage_name}.md"
                else:
                    reflection_file = run_dir / f"reflection_{stage_name}_lite.md"
                
                if reflection_file.exists():
                    try:
                        with reflection_file.open("r", encoding="utf-8") as fp:
                            rationale_md = fp.read()
                            reflection_entry["rationale_md"] = rationale_md
                    except Exception:
                        reflection_entry["rationale_md"] = ""
                else:
                    # Fallback: try full version if lite doesn't exist
                    if detail == "lite":
                        fallback_file = run_dir / f"reflection_{stage_name}.md"
                        if fallback_file.exists():
                            try:
                                with fallback_file.open("r", encoding="utf-8") as fp:
                                    rationale_md = fp.read()
                                    # Sanitize and shorten for lite
                                    from agents.orchestrator.reflection import sanitize_and_shorten
                                    reflection_entry["rationale_md"] = sanitize_and_shorten(rationale_md)
                            except Exception:
                                reflection_entry["rationale_md"] = ""
                        else:
                            reflection_entry["rationale_md"] = ""
                    else:
                        reflection_entry["rationale_md"] = ""
                
                # Load next_actions from memory
                try:
                    memory_record = self.memory.get(run_id)
                    if memory_record:
                        reflections_data = memory_record.metadata.get("reflections", {})
                        stage_reflection = reflections_data.get(stage_name, {})
                        reflection_entry["next_actions"] = stage_reflection.get("next_actions", [])
                    else:
                        reflection_entry["next_actions"] = []
                except Exception:
                    reflection_entry["next_actions"] = []
                
                reflections.append(reflection_entry)
        
        recent_events = events[-10:]
        result = {
            "run_id": run_id,
            "stage": stage_upper,
            "status": status,
            "progress": progress,
            "latest_metrics": latest_metrics,
            "recent_events": recent_events,
            "reflections": reflections,
        }
        if queue_pos is not None:
            result["queue_pos"] = queue_pos
        if started_at:
            result["started_at"] = started_at
        if finished_at:
            result["finished_at"] = finished_at
        return result

    def _find_existing_run(self, fingerprint_key: str) -> Optional[str]:
        """Find existing run with same fingerprint that is running or completed."""
        # Check running runs
        with self._futures_lock:
            for run_id, future in self._futures.items():
                if not future.done():
                    with self._metadata_lock:
                        if self._run_metadata.get(run_id, {}).get("fingerprint_key") == fingerprint_key:
                            return run_id
        
        # Check completed runs by scanning memory
        try:
            memory_dir = self.reports_dir / "memory"
            if memory_dir.exists():
                for run_file in memory_dir.glob("*.json"):
                    try:
                        with run_file.open("r", encoding="utf-8") as fp:
                            data = json.load(fp)
                            if isinstance(data, list) and len(data) > 0:
                                plan_data = data[0].get("plan", {})
                                stored_fp = plan_data.get("fingerprints", {})
                                stored_key = f"{stored_fp.get('data_fingerprint')}:{stored_fp.get('code_commit')}:{stored_fp.get('policy_hash')}:{stored_fp.get('args_hash')}"
                                if stored_key == fingerprint_key:
                                    return run_file.stem
                    except Exception:
                        continue
        except Exception:
            pass
        
        return None

    def _check_budget(self, plan: ExperimentPlan) -> Optional[str]:
        """Check budget constraints. Returns error message if violated, None otherwise."""
        budget_cfg = self.config.get("budget", {})
        
        # Check concurrent runs
        max_concurrent = budget_cfg.get("max_concurrent_runs")
        if max_concurrent is not None:
            with self._futures_lock:
                running_count = sum(1 for f in self._futures.values() if not f.done())
                if running_count >= max_concurrent:
                    return f"Max concurrent runs ({max_concurrent}) exceeded (current: {running_count})"
        
        # Check tokens/cost (placeholder - would need actual cost estimation)
        max_tokens = budget_cfg.get("max_tokens")
        max_cost = budget_cfg.get("max_cost_usd")
        if max_tokens is not None or max_cost is not None:
            # Estimate: sample_size * avg_tokens_per_query * stages
            estimated_tokens = plan.sample_size * 1000 * 3  # rough estimate
            if max_tokens is not None and estimated_tokens > max_tokens:
                return f"Estimated tokens ({estimated_tokens}) exceeds limit ({max_tokens})"
            estimated_cost = estimated_tokens * 0.0001  # rough $/token estimate
            if max_cost is not None and estimated_cost > max_cost:
                return f"Estimated cost (${estimated_cost:.2f}) exceeds limit (${max_cost:.2f})"
        
        return None

    def _dry_run_plan(self, run_id: str, plan: ExperimentPlan, fingerprints: Dict[str, str], started_at: str) -> Dict[str, Any]:
        """Generate dry-run plan without executing."""
        try:
            # Health check
            check_backend_health(self.config)
        except HealthCheckError as exc:
            self.logger.log_event(
                run_id=run_id,
                event_type="DRY_RUN_HEALTH_FAIL",
                payload={
                    "error": self._build_error_payload(exc),
                    "timestamp": started_at,
                },
            )
            raise
        
        # Generate grid plan
        grid_batches = planner.make_grid(plan, self.config)
        total_tasks = sum(len(batch.tasks) for batch in grid_batches)
        
        # Estimate duration (rough: 2s per task)
        estimated_duration_s = total_tasks * 2 + 10  # smoke + grid + ab overhead
        
        plan_summary = {
            "batches": len(grid_batches),
            "total_tasks": total_tasks,
            "estimated_duration_s": estimated_duration_s,
            "stages": ["SMOKE", "GRID", "AB", "SELECT", "PUBLISH"],
        }
        
        self.logger.log_event(
            run_id=run_id,
            event_type="DRY_RUN_PLAN",
            payload={
                "fingerprints": fingerprints,
                "plan": plan_summary,
                "timestamp": started_at,
            },
        )
        
        return {
            "run_id": run_id,
            "dry_run": True,
            "plan": plan_summary,
            "fingerprints": fingerprints,
            "message": "Use commit=true to execute",
        }

    def _run_pipeline_with_cleanup(self, run_id: str, plan: ExperimentPlan, queue_pos: int) -> None:
        """Run pipeline with queue cleanup."""
        try:
            self._run_pipeline(run_id, plan)
        finally:
            # Remove from queue
            with self._queue_lock:
                try:
                    self._queue.remove(run_id)
                except ValueError:
                    pass
            
            # Update finished_at
            with self._metadata_lock:
                if run_id in self._run_metadata:
                    self._run_metadata[run_id]["finished_at"] = _default_timestamp()
            
            # Cleanup future
            with self._futures_lock:
                self._futures.pop(run_id, None)

    def _run_pipeline(self, run_id: str, plan: ExperimentPlan) -> None:
        current_stage = "SMOKE"
        try:
            self._run_smoke(run_id, plan)
            current_stage = "GRID"
            grid_summary = self._run_grid(run_id, plan)
            decision = grid_summary.get("decision") or {}
            if decision.get("action") == "early_stop":
                self.logger.log_event(
                    run_id,
                    "RUN_COMPLETED",
                    {
                        "stage": "GRID",
                        "timestamp": _default_timestamp(),
                        "reason": "Reflection requested early stop after grid stage",
                    },
                )
                self.memory.update_metadata(
                    run_id,
                    {
                        "status": "completed",
                        "grid_decision": decision,
                    },
                )
                return
            current_stage = "AB"
            ab_summary = self._run_ab(run_id, plan, grid_summary)
            current_stage = "SELECT"
            winner = self._select_winner(run_id, plan, grid_summary)
            current_stage = "PUBLISH"
            publish_summary = self._publish_winner(run_id, plan, grid_summary, ab_summary, winner)
            self.logger.log_event(
                run_id,
                "RUN_COMPLETED",
                {
                    "stage": "PUBLISH",
                    "timestamp": _default_timestamp(),
                    "artifacts": publish_summary.get("artifacts", {}),
                },
            )
            self.memory.update_metadata(
                run_id,
                {
                    "status": "completed",
                    "ab": ab_summary,
                    "winner": winner,
                    "artifacts": publish_summary.get("artifacts", {}),
                },
            )
        except Exception as exc:  # pylint: disable=broad-except
            error_payload = self._build_error_payload(exc)
            self.logger.log_event(
                run_id,
                "RUN_FAILED",
                {
                    "stage": current_stage,
                    "error": error_payload,
                    "timestamp": _default_timestamp(),
                },
            )
            self.memory.update_metadata(
                run_id,
                {"status": "failed", "error": str(exc), "failed_stage": current_stage},
            )
        finally:
            with self._futures_lock:
                self._futures.pop(run_id, None)

    def _run_smoke(self, run_id: str, plan: ExperimentPlan) -> RunEvalResult:
        stage = "SMOKE"
        self.logger.log_stage_event(
            run_id,
            stage=stage,
            status="started",
            payload={"stage": stage, "timestamp": _default_timestamp()},
        )
        started_at = time.monotonic()
        try:
            check_backend_health(self.config)
        except HealthCheckError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            error_payload = self._build_error_payload(exc)
            self.logger.log_event(
                run_id,
                "HEALTH_FAIL",
                {
                    "stage": stage,
                    "timestamp": _default_timestamp(),
                    "duration_ms": duration_ms,
                    "error": error_payload,
                },
            )
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise

        try:
            result = run_smoke(plan, self.config)
            metrics_summary = aggregate_metrics(result.metrics_path)
            duration_ms = int((time.monotonic() - started_at) * 1000)
            payload = {
                "stage": stage,
                "duration_ms": duration_ms,
                "job_id": result.job_id,
                "metrics": metrics_summary,
            }
            self.memory.update_metadata(
                run_id,
                {"smoke": {"job_id": result.job_id, "metrics": metrics_summary}},
            )
            self.logger.log_stage_event(run_id, stage=stage, status="done", payload=payload)
            
            # Run reflection after stage completes
            kpis = {
                "metrics": metrics_summary,
                "duration_ms": duration_ms,
            }
            self._run_reflection(run_id, stage, kpis)
            
            return result
        except RunnerTimeoutError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            error_payload = self._build_error_payload(exc)
            self.logger.log_event(
                run_id,
                "RUNNER_TIMEOUT",
                {
                    "stage": stage,
                    "timestamp": _default_timestamp(),
                    "duration_ms": duration_ms,
                    "error": error_payload,
                },
            )
            self.memory.update_metadata(run_id, {"smoke": {"status": "failed", "error": str(exc)}})
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise
        except RunEvalError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self.memory.update_metadata(run_id, {"smoke": {"status": "failed", "error": str(exc)}})
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise
        except Exception as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self.memory.update_metadata(run_id, {"smoke": {"status": "failed", "error": str(exc)}})
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise

    def _run_grid(self, run_id: str, plan: ExperimentPlan) -> Dict[str, Any]:
        stage = "GRID"
        self.logger.log_stage_event(
            run_id,
            stage=stage,
            status="started",
            payload={"stage": stage, "timestamp": _default_timestamp()},
        )
        started_at = time.monotonic()

        try:
            check_backend_health(self.config)
        except HealthCheckError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            error_payload = self._build_error_payload(exc)
            self.logger.log_event(
                run_id,
                "HEALTH_FAIL",
                {
                    "stage": stage,
                    "timestamp": _default_timestamp(),
                    "duration_ms": duration_ms,
                    "error": error_payload,
                },
            )
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise

        try:
            grid_batches = planner.make_grid(plan, self.config)
            batch_results: List[Dict[str, Any]] = []
            metrics_paths: List[Path] = []

            for batch in grid_batches:
                batch_payload = {
                    "stage": stage,
                    "batch_id": batch.batch_id,
                    "concurrency": batch.concurrency,
                    "task_count": len(batch.tasks),
                    "timestamp": _default_timestamp(),
                }
                self.logger.log_event(run_id, "GRID_BATCH_STARTED", batch_payload)

                for task in batch.tasks:
                    task_payload = {
                        "stage": stage,
                        "batch_id": batch.batch_id,
                        "config_id": task.config_id,
                        "parameters": task.parameters,
                    }
                    try:
                        result = run_grid_task(task.parameters, self.config)
                        metrics_summary = aggregate_metrics(result.metrics_path)
                        task_entry = {
                            "config_id": task.config_id,
                            "status": "ok",
                            "metrics": metrics_summary,
                            "job_id": result.job_id,
                            "metrics_path": str(result.metrics_path),
                            "parameters": task.parameters,
                        }
                        metrics_paths.append(result.metrics_path)
                        self.logger.log_event(
                            run_id,
                            "GRID_TASK_DONE",
                            {
                                **task_payload,
                                "status": "ok",
                                "job_id": result.job_id,
                                "metrics": metrics_summary,
                            },
                        )
                    except RunnerTimeoutError as exc:
                        error_payload = self._build_error_payload(exc)
                        elapsed_ms = int((time.monotonic() - started_at) * 1000)
                        self.logger.log_event(
                            run_id,
                            "RUNNER_TIMEOUT",
                            {
                                **task_payload,
                                "stage": stage,
                                "duration_ms": elapsed_ms,
                                "error": error_payload,
                            },
                        )
                        raise
                    except HealthCheckError as exc:
                        error_payload = self._build_error_payload(exc)
                        elapsed_ms = int((time.monotonic() - started_at) * 1000)
                        self.logger.log_event(
                            run_id,
                            "HEALTH_FAIL",
                            {
                                **task_payload,
                                "stage": stage,
                                "duration_ms": elapsed_ms,
                                "error": error_payload,
                            },
                        )
                        raise
                    except (RunEvalError, MetricsAggregationError) as exc:
                        task_entry = {
                            "config_id": task.config_id,
                            "status": "error",
                            "error": str(exc),
                            "metrics": {},
                            "parameters": task.parameters,
                        }
                        self.logger.log_event(
                            run_id,
                            "GRID_TASK_FAILED",
                            {**task_payload, "status": "error", "error": str(exc)},
                        )
                    batch_results.append(task_entry)

                self.logger.log_event(
                    run_id,
                    "GRID_BATCH_DONE",
                    {
                        "stage": stage,
                        "batch_id": batch.batch_id,
                        "completed_tasks": len(batch.tasks),
                        "timestamp": _default_timestamp(),
                    },
                )

            duration_ms = int((time.monotonic() - started_at) * 1000)
            try:
                aggregate = aggregate_metrics([Path(path) for path in metrics_paths]) if metrics_paths else {}
            except MetricsAggregationError:
                aggregate = {}

            reflection_input = {
                "run_id": run_id,
                "stage": stage,
                "results": batch_results,
                "metrics": aggregate,
                "thresholds": self.config.get("reflection", {}),
            }
            decision = reflection.post_phase_reflect(reflection_input, logger=self.logger)

            payload = {
                "stage": stage,
                "duration_ms": duration_ms,
                "metrics": aggregate,
                "decision": decision,
                "task_results": batch_results,
            }
            self.memory.update_metadata(
                run_id,
                {
                    "grid": {
                        "aggregated_metrics": aggregate,
                        "tasks": batch_results,
                        "decision": decision,
                    }
                },
            )
            self.logger.log_stage_event(run_id, stage=stage, status="done", payload=payload)
            
            # Run reflection after stage completes
            kpis = {
                "metrics": aggregate,
                "duration_ms": duration_ms,
            }
            self._run_reflection(run_id, stage, kpis)
            
            return {
                "decision": decision,
                "aggregate": aggregate,
                "tasks": batch_results,
                "metrics_paths": [str(path) for path in metrics_paths],
            }
        except RunnerTimeoutError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise
        except RunEvalError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise
        except Exception as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise

    def _load_policy_config(self, policy_id: Optional[str]) -> Dict[str, Any]:
        policy_name = policy_id or self.config.get("baseline_policy")
        if not policy_name:
            raise ValueError("Baseline policy id is not configured.")
        if self._policies_cache is None:
            policies_path = Path(self.config.get("policies_path", "configs/policies.json")).resolve()
            with policies_path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
            self._policies_cache = data.get("policies") or {}
        policy = self._policies_cache.get(policy_name)
        if not policy:
            raise ValueError(f"Policy `{policy_name}` not found in policies configuration.")
        return dict(policy)

    @staticmethod
    def _rank_configs(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ranked: List[Dict[str, Any]] = []
        for item in tasks:
            if item.get("status") != "ok":
                continue
            metrics = item.get("metrics") or {}
            parameters = item.get("parameters") or {}
            ranked.append(
                {
                    "config_id": item.get("config_id"),
                    "metrics": metrics,
                    "parameters": parameters,
                    "job_id": item.get("job_id"),
                }
            )
        ranked.sort(
            key=lambda entry: (
                -float(entry["metrics"].get("recall_at_10", 0.0)),
                float(entry["metrics"].get("p95_ms", float("inf"))),
                float(entry["metrics"].get("cost", float("inf"))),
            )
        )
        return ranked

    def _relative_to_reports(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.reports_dir))
        except ValueError:
            return str(path)

    def _run_ab(
        self,
        run_id: str,
        plan: ExperimentPlan,
        grid_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        stage = "AB"
        self.logger.log_stage_event(
            run_id,
            stage=stage,
            status="started",
            payload={"stage": stage, "timestamp": _default_timestamp()},
        )
        started_at = time.monotonic()

        ranked = self._rank_configs(grid_summary.get("tasks", []))
        if not ranked:
            raise RuntimeError("No successful grid configurations available for A/B stage.")

        ab_cfg = self.config.get("ab") or {}
        sample_n = int(ab_cfg.get("sample", plan.sample_size))
        baseline_config = self._load_policy_config(plan.baseline_id)
        baseline_policy = plan.baseline_id or self.config.get("baseline_policy")

        challenger = ranked[0]
        challenger_cfg = dict(challenger["parameters"])
        challenger_cfg["run_id"] = run_id

        ab_config = dict(self.config)
        ab_config["run_id"] = run_id

        try:
            check_backend_health(self.config)
        except HealthCheckError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            error_payload = self._build_error_payload(exc)
            self.logger.log_event(
                run_id,
                "HEALTH_FAIL",
                {
                    "stage": stage,
                    "timestamp": _default_timestamp(),
                    "duration_ms": duration_ms,
                    "error": error_payload,
                },
            )
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise

        try:
            result = run_ab(baseline_config, challenger_cfg, sample_n, ab_config)
            duration_ms = int((time.monotonic() - started_at) * 1000)
            chart_path = Path(result["chart_path"])
            csv_path = Path(result["csv_path"])
            result_record = {
                "diff_table": result.get("diff_table"),
                "baseline_metrics": result.get("baseline_metrics"),
                "challenger_metrics": result.get("challenger_metrics"),
                "baseline_job_id": result.get("baseline_job_id"),
                "challenger_job_id": result.get("challenger_job_id"),
                "chart_path": str(chart_path),
                "csv_path": str(csv_path),
            }
            payload = {
                "stage": stage,
                "duration_ms": duration_ms,
                "candidate_config_id": challenger["config_id"],
                "baseline_policy": baseline_policy,
                "diff_table": result["diff_table"],
                "chart": self._relative_to_reports(chart_path),
                "csv": self._relative_to_reports(csv_path),
            }
            self.memory.update_metadata(
                run_id,
                {
                    "ab": {
                        "baseline_policy": baseline_policy,
                        "candidate": challenger,
                        "result": result_record,
                    }
                },
            )
            self.logger.log_stage_event(run_id, stage=stage, status="done", payload=payload)
            return {
                "baseline_policy": baseline_policy,
                "candidate": challenger,
                "result": result_record,
            }
        except RunnerTimeoutError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            error_payload = self._build_error_payload(exc)
            self.logger.log_event(
                run_id,
                "RUNNER_TIMEOUT",
                {
                    "stage": stage,
                    "timestamp": _default_timestamp(),
                    "duration_ms": duration_ms,
                    "error": error_payload,
                },
            )
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise
        except RunEvalError as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise
        except Exception as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self._log_stage_failure(run_id, stage, exc, duration_ms)
            raise

    def _select_winner(
        self,
        run_id: str,
        plan: ExperimentPlan,
        grid_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        stage = "SELECT"
        self.logger.log_stage_event(
            run_id,
            stage=stage,
            status="started",
            payload={"stage": stage, "timestamp": _default_timestamp()},
        )
        ranked = self._rank_configs(grid_summary.get("tasks", []))
        if not ranked:
            raise RuntimeError("No successful configurations available for selection.")

        winner = ranked[0]
        payload = {
            "stage": stage,
            "timestamp": _default_timestamp(),
            "config_id": winner["config_id"],
            "metrics": winner["metrics"],
        }
        self.memory.update_metadata(
            run_id,
            {
                "winner": {
                    "config_id": winner["config_id"],
                    "metrics": winner["metrics"],
                    "parameters": winner["parameters"],
                    "job_id": winner.get("job_id"),
                }
            },
        )
        self.logger.log_stage_event(run_id, stage=stage, status="done", payload=payload)
        
        # Run reflection after stage completes
        kpis = {
            "metrics": winner["metrics"],
            "duration_ms": 0,  # SELECT is typically instant
        }
        self._run_reflection(run_id, stage, kpis)
        
        return winner

    def _publish_winner(
        self,
        run_id: str,
        plan: ExperimentPlan,
        grid_summary: Dict[str, Any],
        ab_summary: Dict[str, Any],
        winner: Dict[str, Any],
    ) -> Dict[str, Any]:
        stage = "PUBLISH"
        self.logger.log_stage_event(
            run_id,
            stage=stage,
            status="started",
            payload={"stage": stage, "timestamp": _default_timestamp()},
        )

        run_dir = self.reports_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        winners_json_path = run_dir / "winners.json"
        winners_md_path = run_dir / "winners.md"
        pareto_path = run_dir / "pareto.png"
        fail_topn_path = run_dir / "failTopN.csv"

        rows = []
        for item in grid_summary.get("tasks", []):
            if item.get("status") != "ok":
                continue
            metrics = item.get("metrics") or {}
            rows.append(
                {
                    "config_id": item.get("config_id"),
                    "recall_at_10": float(metrics.get("recall_at_10", 0.0)),
                    "p95_ms": float(metrics.get("p95_ms", 0.0)),
                    "cost": float(metrics.get("cost", 0.0)),
                }
            )
        if rows:
            render_pareto_chart(rows, pareto_path)
        write_fail_topn_csv(grid_summary.get("tasks", []), fail_topn_path, top_n=10)

        ab_result = ab_summary.get("result") or {}
        ab_chart_rel = self._relative_to_reports(Path(ab_result.get("chart_path", pareto_path)))
        ab_csv_rel = self._relative_to_reports(Path(ab_result.get("csv_path", fail_topn_path)))
        ab_result_serializable = {
            "diff_table": ab_result.get("diff_table"),
            "baseline_metrics": ab_result.get("baseline_metrics"),
            "challenger_metrics": ab_result.get("challenger_metrics"),
            "baseline_job_id": ab_result.get("baseline_job_id"),
            "challenger_job_id": ab_result.get("challenger_job_id"),
            "chart_path": ab_chart_rel,
            "csv_path": ab_csv_rel,
        }

        # Get fingerprints from metadata
        with self._metadata_lock:
            fingerprints = self._run_metadata.get(run_id, {}).get("fingerprints", {})
        
        # Get validated paths from plan metadata
        plan_dataset = plan.metadata.get("dataset", plan.dataset)
        qrels_path = plan.metadata.get("qrels_path")
        queries_path = plan.metadata.get("queries_path")
        alignment_info = plan.metadata.get("alignment", {})
        
        winners_payload = {
            "run_id": run_id,
            "generated_at": _default_timestamp(),
            "dataset": plan_dataset,
            "queries_path": queries_path,
            "qrels_path": qrels_path,
            "id_normalization": "digits-only/no-leading-zero",
            "alignment": alignment_info,
            "fingerprints": fingerprints,
            "winner": winner,
            "ab": ab_result_serializable,
            "grid_decision": grid_summary.get("decision") or {},
        }
        with winners_json_path.open("w", encoding="utf-8") as fp:
            json.dump(winners_payload, fp, indent=2, ensure_ascii=False)

        metrics = winner["metrics"]
        md_lines = [
            f"# Winner Summary — {run_id}",
            "",
            f"- **Config ID**: `{winner['config_id']}`",
            f"- **Dataset**: `{plan.dataset}`",
            f"- **Recall@10**: {metrics.get('recall_at_10', 0.0):.4f}",
            f"- **P95 ms**: {metrics.get('p95_ms', 0.0):.2f}",
            f"- **Cost**: {metrics.get('cost', 0.0):.4f}",
            "",
            "## Parameters",
        ]
        for key, value in sorted((winner.get("parameters") or {}).items()):
            md_lines.append(f"- {key}: {value}")
        md_lines.append("")
        with winners_md_path.open("w", encoding="utf-8") as fp:
            fp.write("\n".join(md_lines))

        winners_final_path = Path(self.config.get("winners_source", self.reports_dir / "winners.final.json")).resolve()
        winners_final_path.parent.mkdir(parents=True, exist_ok=True)
        if winners_final_path.exists():
            with winners_final_path.open("r", encoding="utf-8") as fp:
                existing_doc = json.load(fp)
            if isinstance(existing_doc, dict):
                final_entries = existing_doc.setdefault("entries", [])
                winners_document = existing_doc
            elif isinstance(existing_doc, list):
                final_entries = existing_doc
                winners_document = final_entries
            else:
                final_entries = []
                winners_document = final_entries
        else:
            final_entries = []
            winners_document = final_entries
        record_hash = hashlib.sha256(
            json.dumps(
                {
                    "config_id": winner["config_id"],
                    "parameters": winner["parameters"],
                    "metrics": winner["metrics"],
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        # Get validated paths from plan metadata
        plan_dataset = plan.metadata.get("dataset", plan.dataset)
        qrels_path = plan.metadata.get("qrels_path")
        queries_path = plan.metadata.get("queries_path")
        alignment_info = plan.metadata.get("alignment", {})
        
        final_entries.append(
            {
                "run_id": run_id,
                "timestamp": _default_timestamp(),
                "dataset": plan_dataset,
                "queries_path": queries_path,
                "qrels_path": qrels_path,
                "id_normalization": "digits-only/no-leading-zero",
                "alignment": alignment_info,
                "fingerprints": fingerprints,
                "winner": winner,
                "ab_diff": ab_result.get("diff_table", {}),
                "grid_decision": grid_summary.get("decision") or {},
                "hash": record_hash,
            }
        )
        with winners_final_path.open("w", encoding="utf-8") as fp:
            json.dump(winners_document, fp, indent=2, ensure_ascii=False)

        artifacts = {
            "winners_json": self._relative_to_reports(winners_json_path),
            "winners_md": self._relative_to_reports(winners_md_path),
            "pareto_png": self._relative_to_reports(pareto_path),
            "ab_diff_png": ab_chart_rel,
            "ab_diff_csv": ab_csv_rel,
            "fail_topn_csv": self._relative_to_reports(fail_topn_path),
            "events_jsonl": self._relative_to_reports(self.reports_dir / "events" / f"{run_id}.jsonl"),
            "winners_final_json": self._relative_to_reports(winners_final_path),
        }

        self.logger.log_stage_event(
            run_id,
            stage=stage,
            status="done",
            payload={
                "stage": stage,
                "timestamp": _default_timestamp(),
                "artifacts": artifacts,
            },
        )
        
        # Run reflection after stage completes
        kpis = {
            "metrics": winner["metrics"],
            "duration_ms": 0,  # PUBLISH is typically fast
        }
        self._run_reflection(run_id, stage, kpis)
        
        return {"artifacts": artifacts}

    def get_report_artifacts(self, run_id: str) -> Dict[str, Any]:
        """Get report artifacts with SLA verification."""
        run_dir = self.reports_dir / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run directory not found: {run_dir}")
        
        artifacts: Dict[str, str] = {}
        
        winners_json_path = run_dir / "winners.json"
        if winners_json_path.exists():
            artifacts["winners_json"] = self._relative_to_reports(winners_json_path)
            # Load metrics for SLA check
            try:
                with winners_json_path.open("r", encoding="utf-8") as fp:
                    winners_data = json.load(fp)
                    winner_metrics = winners_data.get("winner", {}).get("metrics", {})
                    sla_policy_path = self.config.get("sla_policy_path")
                    sla_verdict = verify_sla(winner_metrics, sla_policy_path)
                    return {
                        "artifacts": artifacts,
                        "sla_verdict": sla_verdict["verdict"],
                        "sla_checks": sla_verdict.get("checks", []),
                    }
            except Exception:
                pass
        
        # Fallback: try to get metrics from events
        events = self.logger.read_events(run_id, limit=100)
        latest_metrics = {}
        for event in reversed(events):
            payload = event.get("payload", {})
            if "metrics" in payload:
                latest_metrics = payload["metrics"]
                break
        
        sla_policy_path = self.config.get("sla_policy_path")
        sla_verdict = verify_sla(latest_metrics, sla_policy_path)
        
        # Standard artifact paths
        artifacts.update({
            "winners_md": self._relative_to_reports(run_dir / "winners.md"),
            "pareto_png": self._relative_to_reports(run_dir / "pareto.png"),
            "ab_diff_png": self._relative_to_reports(run_dir / "ab_diff.png"),
            "fail_topn_csv": self._relative_to_reports(run_dir / "failTopN.csv"),
            "events_jsonl": self._relative_to_reports(self.reports_dir / "events" / f"{run_id}.jsonl"),
        })
        
        return {
            "artifacts": artifacts,
            "sla_verdict": sla_verdict["verdict"],
            "sla_checks": sla_verdict.get("checks", []),
        }


def generate_run_id() -> str:
    uid = uuid.uuid4().hex[:12]
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{RUN_ID_PREFIX}-{timestamp}-{uid}"

