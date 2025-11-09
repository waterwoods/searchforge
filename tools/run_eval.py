"""
Execution helpers for orchestrator-triggered evaluations.

The smoke evaluation wrapper is responsible for invoking the existing FiQA
suite runner with sensible defaults, while enforcing timeout, retry and rate
limiting guarantees as mandated by the orchestrator contract.
"""

from __future__ import annotations

import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urljoin, urlparse, urlunparse

import requests

logger = logging.getLogger(__name__)


class RunEvalError(RuntimeError):
    """Raised when an evaluation job cannot be completed successfully."""

    def __init__(
        self,
        message: str,
        *,
        error_type: Optional[str] = None,
        hint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type or self.__class__.__name__
        self.hint = hint
        self.details = details or {}


class HealthCheckError(RunEvalError):
    """Raised when backend health checks fail."""


class RunnerTimeoutError(RunEvalError):
    """Raised when the runner exceeds the configured timeout."""


@dataclass(frozen=True)
class RunEvalResult:
    job_id: str
    metrics_path: Path
    summary: Dict[str, Any]


class _RateLimiter:
    def __init__(self, rate_per_sec: float) -> None:
        self.min_interval = 0.0
        if rate_per_sec and rate_per_sec > 0:
            self.min_interval = 1.0 / rate_per_sec
        self._lock = threading.Lock()
        self._last_at = 0.0

    def acquire(self) -> None:
        if self.min_interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            wait_for = self.min_interval - (now - self._last_at)
            if wait_for > 0:
                time.sleep(wait_for)
            self._last_at = time.monotonic()

    def __enter__(self) -> "_RateLimiter":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        return None


class _SemaphoreGuard:
    def __init__(self, semaphore: threading.Semaphore) -> None:
        self._semaphore = semaphore

    def __enter__(self) -> "_SemaphoreGuard":
        self._semaphore.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._semaphore.release()


_rate_limiters: Dict[str, _RateLimiter] = {}
_rate_limiters_lock = threading.Lock()
_semaphores: Dict[int, threading.BoundedSemaphore] = {}
_semaphores_lock = threading.Lock()


def _get_rate_limiter(key: str, rate_per_sec: float) -> _RateLimiter:
    with _rate_limiters_lock:
        limiter = _rate_limiters.get(key)
        if limiter is None or limiter.min_interval != (1.0 / rate_per_sec if rate_per_sec else 0.0):
            limiter = _RateLimiter(rate_per_sec)
            _rate_limiters[key] = limiter
    return limiter


def _get_semaphore(limit: int) -> threading.BoundedSemaphore:
    limit = max(1, int(limit))
    with _semaphores_lock:
        semaphore = _semaphores.get(limit)
        if semaphore is None:
            semaphore = threading.BoundedSemaphore(limit)
            _semaphores[limit] = semaphore
    return semaphore


def _validate_host(url: str, allowed_hosts: Mapping[str, Any]) -> None:
    parsed = urlparse(url)
    netloc = parsed.netloc
    if not netloc:
        raise RunEvalError(f"Invalid base URL: {url}")
    host_with_port = netloc.lower()
    allowed = {str(host).lower() for host in allowed_hosts}
    if host_with_port not in allowed:
        raise RunEvalError(f"Host `{host_with_port}` not in allowed list: {sorted(allowed)}")


def _ensure_metrics_exists(metrics_path: Path) -> Dict[str, Any]:
    if not metrics_path.exists():
        raise RunEvalError(f"metrics.json not found at {metrics_path}")
    with metrics_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _create_job_id(prefix: str = "smoke") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _build_runner_command(
    cfg: Mapping[str, Any],
    *,
    dataset: str,
    sample: int,
    top_k: int,
    concurrency: int,
    mmr: bool,
    mmr_lambda: float,
    ef_search: Optional[int],
    extra_args: Optional[Dict[str, Any]] = None,
    qrels_path: Optional[str] = None,
    queries_path: Optional[str] = None,
) -> list[str]:
    runner_cmd = cfg.get("runner_cmd", "python -m experiments.fiqa_suite_runner")
    cmd = shlex.split(runner_cmd)
    if cmd:
        resolved = shutil.which(cmd[0])
        if resolved:
            cmd[0] = resolved
        elif cmd[0] in {"python", "python3"}:
            cmd[0] = sys.executable
    effective_base = _effective_base_url(cfg)
    cmd.extend(
        [
            "--base",
            effective_base,
            "--collection",
            dataset,
            "--sample",
            str(sample),
            "--top_k",
            str(top_k),
            "--concurrency",
            str(concurrency),
        ]
    )
    # Always add qrels and queries paths if provided
    if qrels_path:
        cmd.extend(["--qrels", qrels_path])
    if queries_path:
        cmd.extend(["--queries", queries_path])
    if ef_search is not None:
        cmd.extend(["--ef-search", str(ef_search)])
    if mmr:
        cmd.append("--mmr")
        cmd.extend(["--mmr-lambda", str(mmr_lambda)])
    if extra_args:
        for key, value in extra_args.items():
            if value is None:
                continue
            if key in {"use_hybrid", "warm_cache"}:
                # Unsupported by fiqa_suite_runner CLI; skip gracefully.
                continue
            flag = f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    cmd.append(flag)
            else:
                cmd.extend([flag, str(value)])
    return cmd


def _plan_value(plan: Any, key: str, default: Any = None) -> Any:
    if isinstance(plan, Mapping):
        return plan.get(key, default)
    return getattr(plan, key, default)


def _effective_base_url(cfg: Mapping[str, Any]) -> str:
    base_url = str(cfg.get("base_url") or "")
    if not base_url:
        return base_url
    aliases = cfg.get("host_aliases") or {}
    parsed = urlparse(base_url)
    alias = aliases.get(parsed.hostname or "")
    if alias:
        netloc = alias
        if parsed.port:
            netloc = f"{alias}:{parsed.port}"
        parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)
    return base_url


def check_backend_health(cfg: Mapping[str, Any]) -> None:
    base_url = str(cfg.get("base_url") or "").rstrip("/")
    if not base_url:
        raise HealthCheckError(
            "base_url is not configured.",
            hint="在 orchestrator 配置中设置 base_url 指向真实 API。",
        )

    effective_base = _effective_base_url(cfg).rstrip("/")
    endpoints = cfg.get("health_endpoints") or []
    timeout_s = float(cfg.get("health_timeout_s", 10.0))
    session = requests.Session()

    for endpoint in endpoints:
        if not endpoint:
            continue
        url = urljoin(f"{effective_base or base_url}/", endpoint.lstrip("/"))
        started = time.time()
        try:
            response = session.get(url, timeout=timeout_s)
        except requests.RequestException as exc:
            hint = "确认后端 API 正在运行且网络连通。"
            if isinstance(exc, requests.exceptions.ConnectionError):
                hint = "检查主机名解析与网络连通性（例如 /etc/hosts 或 DNS 设置）。"
            raise HealthCheckError(
                f"Health check request to {url} failed: {exc}",
                hint=hint,
                details={
                    "url": url,
                    "timeout_s": timeout_s,
                    "original_base": base_url,
                    "error": repr(exc),
                },
            ) from exc

        if response.status_code >= 400:
            raise HealthCheckError(
                f"Health check {url} returned status {response.status_code}",
                hint="检查服务日志或健康接口响应，确认后端状态。",
                details={
                    "url": url,
                    "status_code": response.status_code,
                    "elapsed_ms": int((time.time() - started) * 1000),
                    "response": response.text[:500],
                },
            )


def _mock_run(
    parameters: Mapping[str, Any],
    cfg: Mapping[str, Any],
    job_prefix: str,
) -> RunEvalResult:
    runs_dir = Path(cfg.get("runs_dir", ".runs")).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)

    job_id = _create_job_id(f"{job_prefix}-mock")
    metrics_path = runs_dir / job_id / "metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    sample_size = int(parameters.get("sample") or 50)
    top_k = int(parameters.get("top_k") or 10)
    recall = min(0.99, 0.4 + 0.02 * top_k)
    p95_ms = float(80 + 3 * top_k)
    cost = float(0.001 * top_k)

    payload = {
        "job_id": job_id,
        "status": "ok",
        "metrics": {
            "recall_at_10": recall,
            "p95_ms": p95_ms,
            "cost_per_query": cost,
            "count": sample_size,
        },
        "latency_breakdown_ms": {"search": p95_ms / 2.0},
        "config": parameters,
    }
    with metrics_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2)

    summary = {
        "job_id": job_id,
        "status": "ok",
        "metrics": payload["metrics"],
        "latency_breakdown_ms": payload["latency_breakdown_ms"],
    }
    return RunEvalResult(job_id=job_id, metrics_path=metrics_path, summary=summary)


def _execute_runner(
    command: list[str],
    *,
    cfg: Mapping[str, Any],
    dataset: str,
    job_prefix: str,
    sample: int,
    timeout_s: float,
    max_retries: int,
    backoff_s: float,
    rate_per_sec: float,
    concurrency_limit: int,
    runner_timeout: float,
) -> RunEvalResult:
    base_url = str(cfg.get("base_url"))
    effective_base_url = _effective_base_url(cfg)
    allowed_hosts = cfg.get("allowed_hosts") or []
    _validate_host(base_url, allowed_hosts)
    if effective_base_url and effective_base_url != base_url:
        _validate_host(effective_base_url, allowed_hosts)

    runs_dir = Path(cfg.get("runs_dir", ".runs")).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)

    job_id = _create_job_id(job_prefix)
    metrics_path = runs_dir / job_id / "metrics.json"

    env = os.environ.copy()
    env.update(
        {
            "RUNS_DIR": str(runs_dir),
            "JOB_ID": job_id,
            "BASE": effective_base_url or base_url,
        }
    )

    limiter = _get_rate_limiter(job_prefix, rate_per_sec)
    semaphore = _get_semaphore(concurrency_limit)

    attempt = 0
    command_summary = " ".join(command[:8])
    while True:
        with _SemaphoreGuard(semaphore), limiter:
            try:
                logger.info(
                    "Starting %s evaluation job_id=%s dataset=%s sample=%d attempt=%d",
                    job_prefix,
                    job_id,
                    dataset,
                    sample,
                    attempt + 1,
                )
                subprocess.run(
                    command,
                    check=True,
                    timeout=runner_timeout,
                    env=env,
                )
                data = _ensure_metrics_exists(metrics_path)
                summary = {
                    "job_id": data.get("job_id", job_id),
                    "status": data.get("status", "unknown"),
                    "metrics": data.get("metrics", {}),
                    "latency_breakdown_ms": data.get("latency_breakdown_ms", {}),
                }
                return RunEvalResult(
                    job_id=summary["job_id"],
                    metrics_path=metrics_path,
                    summary=summary,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                attempt += 1
                if attempt >= max_retries:
                    if isinstance(exc, subprocess.TimeoutExpired):
                        raise RunnerTimeoutError(
                            f"{job_prefix} runner timed out after {runner_timeout} seconds.",
                            details={
                                "command": command_summary,
                                "timeout_s": runner_timeout,
                                "runs_dir": str(runs_dir),
                                "attempt": attempt,
                                "stage_timeout_s": timeout_s,
                            },
                            hint="检查后端运行状态或调高 runner_timeout_s。",
                        ) from exc
                    raise RunEvalError(
                        f"{job_prefix} evaluation failed after {max_retries} attempts: {exc}",
                        details={
                            "command": command_summary,
                            "exit_code": getattr(exc, "returncode", None),
                            "runs_dir": str(runs_dir),
                            "attempt": attempt,
                            "stage_timeout_s": timeout_s,
                        },
                        hint="查看 runner 输出与后端日志。",
                    ) from exc
                logger.warning(
                    "%s evaluation failed (attempt %d/%d): %s",
                    job_prefix,
                    attempt,
                    max_retries,
                    exc,
                )
                time.sleep(backoff_s * (2 ** (attempt - 1)))
            except FileNotFoundError as exc:
                raise RunEvalError(
                    "Runner executable not found.",
                    hint="确认 runner_cmd 指向可执行命令（例如 python/poetry 环境）。",
                    details={"command": command_summary},
                ) from exc


def _resolve_section_cfg(cfg: Mapping[str, Any], section: str) -> Mapping[str, Any]:
    section_cfg = cfg.get(section)
    if isinstance(section_cfg, Mapping):
        return section_cfg
    return {}


def _resolve_timeout(
    section_cfg: Mapping[str, Any],
    fallback_cfg: Mapping[str, Any],
    key: str,
    default: float,
) -> float:
    if key in section_cfg:
        return float(section_cfg[key])
    if key in fallback_cfg:
        return float(fallback_cfg[key])
    return default


def _run_parameterized_job(
    parameters: Mapping[str, Any],
    cfg: Mapping[str, Any],
    *,
    job_prefix: str,
    section: str,
) -> RunEvalResult:
    section_cfg = _resolve_section_cfg(cfg, section)
    fallback_cfg = _resolve_section_cfg(cfg, "smoke")

    dataset = str(parameters.get("dataset") or section_cfg.get("dataset", ""))
    if not dataset:
        raise RunEvalError(f"{job_prefix.capitalize()} evaluation requires a dataset name.")

    sample = int(parameters.get("sample") or section_cfg.get("sample") or 100)
    top_k = int(parameters.get("top_k") or section_cfg.get("top_k") or 10)
    concurrency = int(parameters.get("concurrency") or section_cfg.get("concurrency") or 1)
    mmr_flag = bool(parameters.get("mmr", section_cfg.get("mmr", False)))
    mmr_lambda = float(parameters.get("mmr_lambda", section_cfg.get("mmr_lambda", 0.3)))
    ef_search = parameters.get("ef_search") or section_cfg.get("ef_search")

    timeout_s = _resolve_timeout(section_cfg, fallback_cfg, "timeout_s", 1800.0)
    max_retries = max(1, int(_resolve_timeout(section_cfg, fallback_cfg, "max_retries", 1)))
    backoff_s = _resolve_timeout(section_cfg, fallback_cfg, "backoff_s", 2.0)
    rate_per_sec = _resolve_timeout(section_cfg, fallback_cfg, "rate_limit_per_sec", 0.0)

    if cfg.get("mock_runner"):
        return _mock_run(parameters, cfg, job_prefix)
    check_backend_health(cfg)

    extra_args = parameters.get("extra_args") or section_cfg.get("extra_args")
    
    # Get qrels and queries paths from config datasets maps
    datasets_cfg = cfg.get("datasets", {})
    qrels_map = datasets_cfg.get("qrels_map", {})
    queries_map = datasets_cfg.get("queries_map", {})
    qrels_path = qrels_map.get(dataset)
    queries_path = queries_map.get(dataset)

    # Default paths if not in map
    if not qrels_path:
        qrels_path = "experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv"
    if not queries_path:
        queries_path = "experiments/data/fiqa/fiqa_hard_50k.jsonl"

    command = _build_runner_command(
        cfg=cfg,
        dataset=dataset,
        sample=sample,
        top_k=top_k,
        concurrency=concurrency,
        mmr=mmr_flag,
        mmr_lambda=mmr_lambda,
        ef_search=int(ef_search) if ef_search is not None else None,
        extra_args=extra_args,
        qrels_path=qrels_path,
        queries_path=queries_path,
    )
    runner_timeout = float(cfg.get("runner_timeout_s", timeout_s))
    return _execute_runner(
        command,
        cfg=cfg,
        dataset=dataset,
        job_prefix=job_prefix,
        sample=sample,
        timeout_s=min(timeout_s, runner_timeout),
        max_retries=max_retries,
        backoff_s=backoff_s,
        rate_per_sec=rate_per_sec,
        concurrency_limit=concurrency,
        runner_timeout=runner_timeout,
    )


def run_smoke(plan: Mapping[str, Any], cfg: Mapping[str, Any]) -> RunEvalResult:
    dataset = _plan_value(plan, "dataset")
    if not dataset:
        raise RunEvalError("Smoke evaluation requires a dataset name.")

    smoke_cfg = _resolve_section_cfg(cfg, "smoke")
    parameters = {
        "dataset": dataset,
        "sample": smoke_cfg.get("sample", _plan_value(plan, "sample_size", 50)),
        "top_k": smoke_cfg.get("top_k", 10),
        "mmr": smoke_cfg.get("mmr", False),
        "mmr_lambda": smoke_cfg.get("mmr_lambda", 0.3),
        "concurrency": smoke_cfg.get("concurrency", 4),
    }
    return _run_parameterized_job(parameters, cfg, job_prefix="smoke", section="smoke")


def run_grid_task(task_params: Mapping[str, Any], cfg: Mapping[str, Any]) -> RunEvalResult:
    if task_params.get("ef_search") is None:
        raise RunEvalError("Grid task requires ef_search parameter.")
    return _run_parameterized_job(task_params, cfg, job_prefix="grid", section="grid")


def run_ab_task(task_params: Mapping[str, Any], cfg: Mapping[str, Any]) -> RunEvalResult:
    return _run_parameterized_job(task_params, cfg, job_prefix="ab", section="ab")

