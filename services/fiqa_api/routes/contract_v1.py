from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from services.fiqa_api.job_runner import get_job_manager
from services.fiqa_api.utils.metrics_loader import (
    extract_metrics_from_manifest,
    load_baseline,
    load_manifest,
    merge_metrics,
    parse_metrics_from_log,
)
from services.fiqa_api.settings import RUNS_PATH

logger = logging.getLogger(__name__)

JOB_ID_PATTERN = re.compile(r"^[a-f0-9]{6,}$")
UPSTREAM_TIMEOUT_SECONDS = 6.0
LOG_TAIL_DEFAULT = 200
LOG_TAIL_MAX = 1000
LOG_TAIL_MIN = 1
LOG_FALLBACK_LINES = 400
RUNS_DIR = RUNS_PATH


class ContractApiError(Exception):
    def __init__(self, status_code: int, code: str, detail: Optional[str] = None):
        super().__init__(detail or code)
        self.status_code = status_code
        self.code = code
        self.detail = detail


class ReviewSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    p95_ms: Optional[float] = None
    err_rate: Optional[float] = None
    recall_at_10: Optional[float] = None
    cost_tokens: Optional[int] = None


class ReviewBaseline(BaseModel):
    model_config = ConfigDict(extra="allow")

    summary: ReviewSummary
    source: Optional[str] = None


class ReviewMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    poll: str
    logs: str
    manifest_path: Optional[str] = None
    baseline_path: Optional[str] = None
    suggest_enabled: Optional[bool] = None
    job_status: Optional[Dict[str, Any]] = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    summary: ReviewSummary
    baseline: Optional[ReviewBaseline] = None
    meta: Optional[ReviewMeta] = None


class ApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., pattern=JOB_ID_PATTERN.pattern)
    preset: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None


class ApplyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    poll: str
    logs: str
    started_at: Optional[float] = None
    preset: Optional[str] = None
    overrides: Optional[Dict[str, Any]] = None
    source_job_id: str


class StatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: str
    rc: Optional[int] = None
    started: Optional[float] = None
    ended: Optional[float] = None
    poll: str
    logs: str


class LogsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    tail: Optional[str] = None
    lines: Optional[int] = None


router = APIRouter(prefix="/api/v1/experiment", tags=["experiment-contract"])


def _json_error(status_code: int, code: str, detail: Optional[str] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": code, "code": code, "detail": detail},
    )


async def _safe_call(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except ContractApiError as exc:
        return _json_error(exc.status_code, exc.code, exc.detail)
    except httpx.TimeoutException as exc:
        return _json_error(408, "upstream_timeout", str(exc))
    except httpx.HTTPError as exc:
        logger.error("Upstream experiment call failed: %s", exc)
        return _json_error(502, "experiment_unreachable", str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected contract v1 error: %s", exc)
        return _json_error(502, "experiment_unreachable", str(exc))


@dataclass
class _StatusData:
    status: Optional[str] = None
    rc: Optional[int] = None
    started: Optional[float] = None
    ended: Optional[float] = None
    log_path: Optional[str] = None

    def to_payload(self, job_id: str) -> StatusResponse:
        poll_link = f"/api/experiment/status/{job_id}"
        logs_link = f"/api/experiment/logs/{job_id}"
        return StatusResponse(
            job_id=job_id,
            status=self.status or "UNKNOWN",
            rc=self.rc,
            started=self.started,
            ended=self.ended,
            poll=poll_link,
            logs=logs_link,
        )


def _validate_job_id(raw_job_id: str) -> str:
    if not raw_job_id or not JOB_ID_PATTERN.fullmatch(raw_job_id):
        raise ContractApiError(400, "invalid_job_id", "job_id must match ^[a-f0-9]{6,}$")
    return raw_job_id


def _iso_to_epoch(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(value).timestamp()
    except Exception:
        return None


def _load_meta_file(job_id: str) -> Optional[Dict[str, Any]]:
    meta_path = RUNS_DIR / f"{job_id}.json"
    if not meta_path.exists():
        return None
    try:
        with meta_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Failed to read meta file for %s: %s", job_id, exc)
        return None


def _resolve_status(job_id: str, allow_missing: bool = False) -> Tuple[Optional[_StatusData], Optional[Dict[str, Any]]]:
    manager = get_job_manager()
    status_data = _StatusData()

    job_obj = manager.get_status(job_id)
    if job_obj is not None:
        status_data.status = getattr(job_obj, "status", None)
        status_data.rc = getattr(job_obj, "return_code", None)
        status_data.started = _iso_to_epoch(getattr(job_obj, "started_at", None))
        status_data.ended = _iso_to_epoch(getattr(job_obj, "finished_at", None))

    job_detail = manager.get_job_detail(job_id)
    if job_detail:
        status_data.status = status_data.status or job_detail.get("status")
        status_data.rc = status_data.rc if status_data.rc is not None else job_detail.get("return_code")
        status_data.started = status_data.started or _iso_to_epoch(job_detail.get("started_at"))
        status_data.ended = status_data.ended or _iso_to_epoch(job_detail.get("finished_at"))

    meta_file = _load_meta_file(job_id)
    if meta_file:
        status_data.status = status_data.status or meta_file.get("status")
        if status_data.rc is None and isinstance(meta_file.get("return_code"), int):
            status_data.rc = meta_file["return_code"]
        status_data.started = status_data.started or _iso_to_epoch(meta_file.get("started"))
        status_data.ended = status_data.ended or _iso_to_epoch(meta_file.get("ended"))
        if isinstance(meta_file.get("log"), str):
            status_data.log_path = meta_file["log"]

    default_log_path = RUNS_DIR / f"{job_id}.log"
    if default_log_path.exists():
        status_data.log_path = status_data.log_path or str(default_log_path)

    if not any([status_data.status, status_data.rc, status_data.started, status_data.ended]) and not status_data.log_path:
        if allow_missing:
            return None, meta_file
        raise ContractApiError(404, "not_found", f"job_id {job_id} not found")

    return status_data, meta_file


def _normalize_summary(metrics: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    normalized: Dict[str, Optional[Any]] = {
        "p95_ms": None,
        "err_rate": None,
        "recall_at_10": None,
        "cost_tokens": None,
    }

    if metrics is None:
        return normalized

    for key in ("p95_ms", "err_rate", "recall_at_10"):
        value = metrics.get(key)
        if value is None:
            normalized[key] = None
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            normalized[key] = None
            continue
        if key == "p95_ms" and numeric <= 0:
            normalized[key] = None
        else:
            normalized[key] = numeric

    cost_value = metrics.get("cost_tokens")
    if cost_value is not None:
        try:
            normalized["cost_tokens"] = int(float(cost_value))
        except (TypeError, ValueError):
            normalized["cost_tokens"] = None

    return normalized


def _merge_status_for_meta(status: Optional[_StatusData]) -> Optional[Dict[str, Any]]:
    if status is None:
        return None
    return {
        "status": status.status,
        "rc": status.rc,
        "started": status.started,
        "ended": status.ended,
    }


def _get_log_lines(job_id: str, tail: int, status: Optional[_StatusData]) -> Tuple[list[str], Optional[str]]:
    manager = get_job_manager()
    lines: list[str] = []
    try:
        lines = manager.get_logs(job_id, tail) or []
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Failed to fetch logs via manager for %s: %s", job_id, exc)

    log_path = status.log_path if status else None
    candidate_path = Path(log_path) if log_path else RUNS_DIR / f"{job_id}.log"
    if (not lines or len(lines) < tail) and candidate_path.exists():
        try:
            with candidate_path.open("r", encoding="utf-8", errors="ignore") as handle:
                file_lines = handle.read().splitlines()
                lines = file_lines[-tail:] if tail else file_lines
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Failed to read log file for %s: %s", job_id, exc)

    filtered_lines = [line for line in lines if isinstance(line, str)]
    return filtered_lines, str(candidate_path) if candidate_path.exists() else None


async def status_handler(job_id: str) -> StatusResponse:
    job_id = _validate_job_id(job_id)
    status_data, _ = _resolve_status(job_id)
    return status_data.to_payload(job_id)


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    return await _safe_call(status_handler, job_id)


async def logs_handler(job_id: str, tail: int) -> LogsResponse:
    job_id = _validate_job_id(job_id)
    if tail < LOG_TAIL_MIN or tail > LOG_TAIL_MAX:
        raise ContractApiError(400, "invalid_tail", f"tail must be between {LOG_TAIL_MIN} and {LOG_TAIL_MAX}")
    status_data, _ = _resolve_status(job_id)
    lines, _ = _get_log_lines(job_id, tail, status_data)
    tail_text = "\n".join(lines) if lines else None
    return LogsResponse(job_id=job_id, tail=tail_text, lines=len(lines) if lines else 0)


@router.get("/logs/{job_id}", response_model=LogsResponse)
async def get_logs(job_id: str, tail: int = Query(LOG_TAIL_DEFAULT)) -> LogsResponse:
    return await _safe_call(logs_handler, job_id, tail)


async def review_handler(job_id: str, suggest: int) -> ReviewResponse:
    job_id = _validate_job_id(job_id)
    bool_suggest = bool(suggest)

    status_data, _ = _resolve_status(job_id, allow_missing=True)

    manifest, manifest_path = load_manifest(job_id)
    manifest_metrics = extract_metrics_from_manifest(manifest or {})

    requires_log_fallback = any(
        manifest_metrics.get(key) is None for key in ("p95_ms", "err_rate", "recall_at_10", "cost_tokens")
    )

    baseline_manifest, baseline_path = load_baseline()
    baseline_summary = _normalize_summary(extract_metrics_from_manifest(baseline_manifest or {}))

    if requires_log_fallback:
        lines, _ = _get_log_lines(job_id, LOG_FALLBACK_LINES, status_data)
        if lines:
            fallback_metrics = parse_metrics_from_log("\n".join(lines))
            manifest_metrics = merge_metrics(manifest_metrics, fallback_metrics)

    summary = _normalize_summary(manifest_metrics)

    baseline_payload = None
    if baseline_manifest or any(value is not None for value in baseline_summary.values()):
        baseline_payload = ReviewBaseline(
            summary=ReviewSummary(**baseline_summary),
            source=baseline_path,
        )

    meta = ReviewMeta(
        poll=f"/api/experiment/status/{job_id}",
        logs=f"/api/experiment/logs/{job_id}",
        manifest_path=manifest_path,
        baseline_path=baseline_path,
        suggest_enabled=bool_suggest,
        job_status=_merge_status_for_meta(status_data),
    )

    return ReviewResponse(
        job_id=job_id,
        summary=ReviewSummary(**summary),
        baseline=baseline_payload,
        meta=meta,
    )


@router.get("/review", response_model=ReviewResponse)
async def get_review(job_id: str = Query(...), suggest: int = Query(0)) -> ReviewResponse:
    return await _safe_call(review_handler, job_id, suggest)


async def apply_handler(request: ApplyRequest) -> ApplyResponse:
    job_id = _validate_job_id(request.job_id)

    payload: Dict[str, Any] = {
        "source_job_id": job_id,
    }

    overrides = request.changes or {}
    payload["overrides"] = overrides
    if request.preset is not None:
        payload["preset"] = request.preset

    base_url = os.getenv("EXPERIMENT_INTERNAL_BASE", os.getenv("BASE", "http://localhost:8000")).rstrip("/")
    run_url = f"{base_url}/api/experiment/run"

    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT_SECONDS) as client:
            response = await client.post(run_url, json=payload, headers={"content-type": "application/json"})
    except httpx.TimeoutException as exc:
        raise ContractApiError(408, "upstream_timeout", str(exc)) from exc
    except httpx.HTTPError as exc:
        raise ContractApiError(502, "experiment_unreachable", str(exc)) from exc

    if response.status_code >= 400:
        try:
            detail_payload = response.json()
            detail_text = json.dumps(detail_payload)
        except Exception:
            detail_payload = None
            detail_text = response.text

        code_map = {
            400: "invalid_job_id",
            404: "not_found",
            408: "upstream_timeout",
            429: "rate_limited",
            503: "busy",
        }
        mapped_code = code_map.get(response.status_code, "experiment_unreachable")
        status_code = response.status_code if mapped_code != "experiment_unreachable" else 502
        raise ContractApiError(status_code, mapped_code, detail_text or detail_payload)

    try:
        payload_data = response.json()
    except ValueError as exc:
        raise ContractApiError(502, "experiment_unreachable", f"Invalid JSON from experiment runner: {exc}") from exc

    new_job_id = payload_data.get("job_id") or payload_data.get("jobId")
    if not isinstance(new_job_id, str) or not new_job_id:
        raise ContractApiError(502, "experiment_unreachable", "experiment runner response missing job_id")

    status_lookup, _ = _resolve_status(new_job_id, allow_missing=True)

    return ApplyResponse(
        job_id=new_job_id,
        poll=payload_data.get("poll") or f"/api/experiment/status/{new_job_id}",
        logs=payload_data.get("logs") or f"/api/experiment/logs/{new_job_id}",
        started_at=status_lookup.started if status_lookup else None,
        preset=request.preset,
        overrides=overrides or None,
        source_job_id=job_id,
    )


@router.post("/apply", response_model=ApplyResponse)
async def post_apply(apply_request: ApplyRequest) -> ApplyResponse:
    return await _safe_call(apply_handler, apply_request)


__all__ = [
    "router",
    "ContractApiError",
    "ApplyRequest",
    "ApplyResponse",
    "LogsResponse",
    "ReviewResponse",
    "StatusResponse",
    "apply_handler",
    "logs_handler",
    "review_handler",
    "status_handler",
]

