"""
steward.py - Steward Review Endpoint
====================================
Minimal MVP for steward review summaries and suggestions.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from pydantic import BaseModel

from services.fiqa_api.utils.env_loader import get_llm_conf
from services.fiqa_api.utils.llm_client import LLMDisabled, reflect_with_llm
from services.fiqa_api.utils.metrics_loader import (
    extract_metrics_from_manifest,
    load_baseline,
    load_manifest,
    merge_metrics,
    parse_metrics_from_log,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["steward"])


_LAST_REFLECTION_META: Dict[str, Any] = {"reflection_source": "rules", "llm": None}


@router.get("/debug/llm-env")
def debug_llm_env():
    llm = get_llm_conf()
    sanitized = {k: v for k, v in llm.items() if k != "api_key"}
    return sanitized


@router.get("/debug/which")
def debug_last_reflection():
    return _LAST_REFLECTION_META

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ARTIFACTS_ROOT = _PROJECT_ROOT / "artifacts"
_REVIEWS_ROOT = _ARTIFACTS_ROOT / "reviews"

_HEX_JOB_PATTERN = re.compile(r"^[a-fA-F0-9]{8,16}$")

_COST_TOKEN_HIGH_THRESHOLD = float(os.getenv("STEWARD_COST_TOKENS_HIGH", "12000"))
_P95_LATENCY_THRESHOLD_MS = float(os.getenv("STEWARD_P95_THRESHOLD_MS", "1200"))
_P95_RECALL_LATENCY_CAP_MS = float(os.getenv("STEWARD_RECALL_LATENCY_CAP_MS", "1500"))
_ERR_RATE_THRESHOLD = float(os.getenv("STEWARD_ERR_RATE_THRESHOLD", "0.01"))

_DEFAULT_LLM_MAX_TOKENS = 256
_DEFAULT_INPUT_COST_PERK = 0.15
_DEFAULT_OUTPUT_COST_PERK = 0.60
_DEFAULT_BUDGET_USD = 0.01


class StewardApplyRequest(BaseModel):
    job_id: str
    preset: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None


class BaselineRequest(BaseModel):
    job_id: str


@router.get("/review")
async def get_steward_review(
    job_id: str = Query(..., description="Experiment job identifier"),
    suggest: int = Query(0, description="Enable suggestion generation (1=true)"),
) -> Dict[str, Any]:
    """
    Retrieve steward review for a given job_id.

    Returns summary metrics, reflection bullets, and heuristic suggestions.
    Persists the review to artifacts/reviews/<job_id>.review.json.
    """
    if not job_id or not _HEX_JOB_PATTERN.fullmatch(job_id):
        raise HTTPException(status_code=404, detail="invalid_job_id")

    suggest_flag = bool(suggest)

    manifest_data, manifest_path = load_manifest(job_id)
    manifest_metrics = extract_metrics_from_manifest(manifest_data or {})

    baseline_data, baseline_path = load_baseline()
    baseline_metrics = extract_metrics_from_manifest(baseline_data or {})

    needs_metrics_fallback = any(
        manifest_metrics.get(key) is None for key in ("p95_ms", "err_rate", "recall_at_10", "cost_tokens")
    )

    job_status: Optional[Dict[str, Any]] = None
    status_note: Optional[str] = None
    if manifest_data is None or needs_metrics_fallback:
        job_status, status_note = await _fetch_job_status(job_id)

    log_fallback_used = False
    if needs_metrics_fallback:
        log_text = await _fetch_job_log(job_id)
        log_metrics = parse_metrics_from_log(log_text or "")
        merged_metrics = merge_metrics(manifest_metrics, log_metrics)
        if merged_metrics != manifest_metrics:
            log_fallback_used = True
        manifest_metrics = merged_metrics

    normalized_metrics = _normalize_metrics(manifest_metrics)
    summary = _build_summary(manifest_data, job_status)
    for key, value in normalized_metrics.items():
        summary[key] = value

    poll_path = f"/api/experiment/status/{job_id}"
    logs_path = f"/api/experiment/logs/{job_id}"
    job_status_payload: Dict[str, Any] = dict(job_status or {})
    job_status_payload.setdefault("poll", poll_path)
    job_status_payload.setdefault("logs", logs_path)
    summary_meta = {
        "source": str(manifest_path) if manifest_path else None,
        "job_status": job_status_payload,
        "status_note": status_note,
        "baseline_path": baseline_path,
    }
    if log_fallback_used:
        summary_meta["metrics_fallback"] = "log"

    baseline_summary = _normalize_metrics(baseline_metrics)
    summary_meta["deltas"] = _compute_deltas(summary, baseline_summary)

    suggestion = _build_suggestion(summary, baseline_summary, suggest_flag)

    reflection = _build_rule_based_reflection(summary, suggestion, baseline_summary, summary_meta)
    meta: Dict[str, Any] = {"reflection_source": "rules", "llm": None, "job_status": job_status_payload}

    llm_conf = get_llm_conf()
    can_llm = bool(llm_conf["key_present"] and llm_conf["model"] and llm_conf["budget_usd"] > 0)

    if can_llm:
        try:
            llm_result = await _run_in_threadpool(
                reflect_with_llm,
                llm_conf,
                summary,
                suggestion,
                baseline_summary,
                llm_conf.get("max_tokens", _DEFAULT_LLM_MAX_TOKENS),
            )
            points = llm_result.get("points") if isinstance(llm_result, dict) else None
            if points:
                reflection = points
                meta = {
                    "reflection_source": "llm",
                    "llm": {
                        "model": llm_conf["model"],
                        "tokens_in": llm_result.get("tokens_in"),
                        "tokens_out": llm_result.get("tokens_out"),
                        "cost_usd_est": llm_result.get("cost_usd_est"),
                    },
                    "job_status": job_status_payload,
                }
        except LLMDisabled:
            pass
        except Exception as exc:
            logger.warning("[STEWARD] LLM reflection failed, falling back: %s", exc)

    global _LAST_REFLECTION_META
    _LAST_REFLECTION_META = meta

    payload: Dict[str, Any] = {
        "job_id": job_id,
        "summary": summary,
        "summary_meta": summary_meta,
        "reflection": reflection,
        "suggestion": suggestion,
        "meta": meta,
        "baseline": baseline_summary,
    }

    compact = _format_compact_summary(summary)
    if compact:
        payload["summary_compact"] = compact

    _persist_review(job_id, payload)

    return payload


@router.post("/apply")
async def apply_steward_changes(request: StewardApplyRequest) -> Dict[str, Any]:
    job_id = request.job_id.strip()
    if not job_id or not _HEX_JOB_PATTERN.fullmatch(job_id):
        raise HTTPException(status_code=400, detail="invalid_job_id")

    preset = request.preset
    changes = request.changes or {}
    if not isinstance(changes, dict):
        changes = {}

    overrides = {k: v for k, v in changes.items()}

    if not overrides:
        preset = preset or "smoke-fast"
        overrides = {"warmup": 100}

    run_payload: Dict[str, Any] = {
        "overrides": overrides,
        "source_job_id": job_id,
    }
    if preset is not None:
        run_payload["preset"] = preset

    base_url = os.getenv("STEWARD_INTERNAL_BASE", os.getenv("BASE", "http://localhost:8000"))
    run_url = f"{base_url.rstrip('/')}/api/experiment/run"

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(run_url, json=run_payload)
    except httpx.HTTPError as exc:
        logger.error("[STEWARD] Failed to trigger apply for %s: %s", job_id, exc)
        raise HTTPException(status_code=502, detail="experiment_unreachable") from exc

    if response.status_code not in (200, 202):
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        logger.error("[STEWARD] Experiment run rejected (%s): %s", response.status_code, error_detail)
        raise HTTPException(status_code=response.status_code, detail="experiment_rejected")

    try:
        run_response = response.json()
    except ValueError as exc:
        logger.error("[STEWARD] Experiment run returned invalid JSON: %s", exc)
        raise HTTPException(status_code=502, detail="experiment_invalid_response") from exc

    new_job_id = run_response.get("job_id") or run_response.get("jobId")
    if not isinstance(new_job_id, str) or not new_job_id:
        logger.error("[STEWARD] Experiment run missing job_id: %s", run_response)
        raise HTTPException(status_code=502, detail="experiment_missing_job_id")

    poll_path = run_response.get("poll") or f"/api/experiment/status/{new_job_id}"
    logs_path = run_response.get("logs") or f"/api/experiment/logs/{new_job_id}"

    started_at = None
    job_status, _ = await _fetch_job_status(new_job_id)
    if job_status:
        started_at = job_status.get("started")

    return {
        "job_id": new_job_id,
        "poll": poll_path,
        "logs": logs_path,
        "started_at": started_at,
        "preset": preset,
        "overrides": overrides,
        "source_job_id": job_id,
    }


@router.get("/baseline")
async def get_steward_baseline() -> Dict[str, Any]:
    baseline_data, baseline_path = load_baseline()
    if baseline_data is None:
        raise HTTPException(status_code=404, detail="baseline_not_found")
    metrics = _normalize_metrics(extract_metrics_from_manifest(baseline_data or {}))
    return {
        "path": baseline_path,
        "metrics": metrics,
        "manifest": baseline_data,
    }


@router.post("/baseline")
async def set_steward_baseline(request: BaselineRequest) -> Dict[str, Any]:
    job_id = request.job_id.strip()
    if not job_id or not _HEX_JOB_PATTERN.fullmatch(job_id):
        raise HTTPException(status_code=400, detail="invalid_job_id")

    manifest_data, manifest_path = load_manifest(job_id)
    manifest_metrics = extract_metrics_from_manifest(manifest_data or {})

    combined_metrics = dict(manifest_metrics)
    if any(combined_metrics.get(key) is None for key in ("p95_ms", "err_rate", "recall_at_10", "cost_tokens")):
        log_text = await _fetch_job_log(job_id)
        log_metrics = parse_metrics_from_log(log_text or "")
        combined_metrics = merge_metrics(combined_metrics, log_metrics)

    normalized_metrics = _normalize_metrics(combined_metrics)
    if all(value is None for value in normalized_metrics.values()):
        raise HTTPException(status_code=404, detail="metrics_not_found")

    baseline_payload: Dict[str, Any] = {}
    if isinstance(manifest_data, dict):
        baseline_payload = json.loads(json.dumps(manifest_data))

    baseline_payload["job_id"] = job_id
    baseline_payload.setdefault("status", (manifest_data or {}).get("status", "SUCCEEDED"))
    baseline_payload["source_manifest"] = manifest_path
    baseline_payload["updated_at"] = time.time()

    summary_block = baseline_payload.get("summary")
    if not isinstance(summary_block, dict):
        summary_block = {}
    for key, value in normalized_metrics.items():
        if value is not None:
            summary_block[key] = value
    baseline_payload["summary"] = summary_block
    baseline_payload["metrics"] = summary_block.copy()

    project_root = Path(__file__).resolve().parents[3]
    baseline_dir = project_root / "artifacts" / "sla"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = baseline_dir / "baseline.json"
    with open(baseline_path, "w", encoding="utf-8") as handle:
        json.dump(baseline_payload, handle, indent=2, ensure_ascii=False)

    return {
        "path": str(baseline_path),
        "job_id": job_id,
        "metrics": normalized_metrics,
        "source_manifest": manifest_path,
    }


async def _fetch_job_status(job_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    base_url = os.getenv("STEWARD_INTERNAL_BASE", os.getenv("BASE", "http://localhost:8000"))
    url = f"{base_url.rstrip('/')}/api/experiment/status/{job_id}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return None, "job_not_found"
            response.raise_for_status()
            data = response.json()
            job = data.get("job")
            if isinstance(job, dict):
                return job, None
            return None, "unexpected_status_shape"
    except httpx.HTTPError as exc:
        logger.warning("[STEWARD] Failed to fetch status for %s: %s", job_id, exc)
        return None, f"http_error:{exc.__class__.__name__}"


async def _fetch_job_log(job_id: str, tail: int = 400) -> Optional[str]:
    base_url = os.getenv("STEWARD_INTERNAL_BASE", os.getenv("BASE", "http://localhost:8000"))
    url = f"{base_url.rstrip('/')}/api/experiment/logs/{job_id}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(url, params={"tail": tail})
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                lines = data.get("lines")
                if isinstance(lines, list):
                    return "\n".join(line for line in lines if isinstance(line, str))
    except httpx.HTTPError as exc:
        logger.debug("[STEWARD] Failed to fetch logs for %s: %s", job_id, exc)
    except Exception as exc:  # pragma: no cover
        logger.debug("[STEWARD] Unexpected log fetch error for %s: %s", job_id, exc)
    return None


def _build_summary(
    manifest: Optional[Dict[str, Any]],
    job_status: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    sources: List[Dict[str, Any]] = []
    if manifest:
        sources.append(manifest)
        for key in ("metrics", "summary", "results", "telemetry", "metrics_summary"):
            nested = manifest.get(key) if isinstance(manifest, dict) else None
            if isinstance(nested, dict):
                sources.append(nested)

        if isinstance(manifest.get("metrics"), list):
            for entry in manifest["metrics"]:
                if isinstance(entry, dict):
                    sources.append(entry)

    summary = {
        "p95_ms": _extract_first_numeric(sources, ("p95_ms", "latency_p95_ms", "p95", "latency_p95")),
        "err_rate": _extract_first_numeric(
            sources, ("err_rate", "error_rate", "errors_pct", "err_pct"), scale=0.01 if _detect_percentage(sources, "err_pct") else 1.0
        ),
        "recall_at_10": _extract_first_numeric(
            sources, ("recall_at_10", "recall@10", "recall10", "recall")
        ),
        "cost_tokens": _extract_first_numeric(
            sources, ("cost_tokens", "tokens", "total_tokens", "token_cost")
        ),
    }

    if job_status:
        summary["status"] = job_status.get("status")
        summary["started_at"] = job_status.get("started")
        summary["finished_at"] = job_status.get("ended")

    return summary


def _normalize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {"p95_ms": None, "err_rate": None, "recall_at_10": None, "cost_tokens": None}
    for key in normalized:
        value = metrics.get(key)
        if value is None:
            normalized[key] = None
            continue
        try:
            if key == "cost_tokens":
                normalized[key] = int(float(value))
            else:
                numeric = float(value)
                if key == "p95_ms" and numeric <= 0:
                    normalized[key] = None
                else:
                    normalized[key] = numeric
        except (TypeError, ValueError):
            normalized[key] = None
    return normalized


def _compute_deltas(summary: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Optional[float]]:
    deltas: Dict[str, Optional[float]] = {}
    for key in ("p95_ms", "err_rate", "recall_at_10", "cost_tokens"):
        current = summary.get(key)
        base = baseline.get(key) if baseline else None
        if isinstance(current, (int, float)) and isinstance(base, (int, float)):
            deltas[key] = float(current) - float(base)
        else:
            deltas[key] = None
    return deltas


def _detect_percentage(sources: Iterable[Dict[str, Any]], target_key: str) -> bool:
    for source in sources:
        if target_key in source:
            value = source.get(target_key)
            if isinstance(value, (int, float)) and value > 1:
                return True
    return False


def _extract_first_numeric(
    sources: Iterable[Dict[str, Any]],
    keys: Tuple[str, ...],
    scale: float = 1.0,
) -> Optional[float]:
    for source in sources:
        for key in keys:
            if key in source:
                value = source[key]
                if isinstance(value, (int, float)):
                    return float(value) * scale
                if isinstance(value, str):
                    try:
                        cleaned = value.strip().rstrip("%")
                        parsed = float(cleaned)
                        if value.endswith("%"):
                            return parsed / 100.0
                        return parsed * scale
                    except ValueError:
                        continue
    return None


def _build_suggestion(
    summary: Dict[str, Any],
    baseline: Optional[Dict[str, Any]],
    suggest_flag: bool,
) -> Dict[str, Any]:
    changes: Dict[str, Any] = {}
    effects: List[str] = []
    risks: List[str] = []

    if not suggest_flag:
        return {
            "policy": "balanced",
            "changes": changes,
            "expected_effect": "No changes requested",
            "risk": "none",
        }

    p95_ms = summary.get("p95_ms")
    recall_at_10 = summary.get("recall_at_10")
    err_rate = summary.get("err_rate")
    cost_tokens = summary.get("cost_tokens")
    baseline_recall = baseline.get("recall_at_10") if baseline else None

    if isinstance(p95_ms, (int, float)) and p95_ms > _P95_LATENCY_THRESHOLD_MS:
        changes.update({"ef_search": 32, "concurrency": 4, "warmup": 100})
        effects.append(f"Targets lower P95 latency ({p95_ms:.0f}ms → <{_P95_LATENCY_THRESHOLD_MS:.0f}ms)")
        risks.append("May increase load during warmup")

    if (
        isinstance(recall_at_10, (int, float))
        and isinstance(baseline_recall, (int, float))
        and recall_at_10 < baseline_recall
        and (not isinstance(p95_ms, (int, float)) or p95_ms <= _P95_RECALL_LATENCY_CAP_MS)
    ):
        changes.update({"top_k": 30, "mmr_lambda": 0.5})
        effects.append("Improves recall towards SLA baseline")
        risks.append("Potential latency increase from higher top_k")

    if isinstance(err_rate, (int, float)) and err_rate > _ERR_RATE_THRESHOLD:
        changes.update({"rollback": True})
        effects.append("Reduces exposure by rolling back")
        risks.append("Rollbacks pause ongoing experiments")

    if isinstance(cost_tokens, (int, float)) and cost_tokens > _COST_TOKEN_HIGH_THRESHOLD:
        changes.update({"ctx_len": "reduce", "rerank": False})
        effects.append("Caps token spend per query")
        risks.append("Context reduction could hurt answer quality")

    if not changes:
        effects.append("No automatic changes recommended")
        risks.append("Maintain current configuration until new data lands")

    expected_effect = "; ".join(dict.fromkeys(effects)) if effects else "None"
    risk = "; ".join(dict.fromkeys(risks)) if risks else "low"

    return {
        "policy": "balanced",
        "changes": changes,
        "expected_effect": expected_effect,
        "risk": risk,
    }


async def _run_in_threadpool(func, *args, **kwargs):
    import functools
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


def _build_rule_based_reflection(
    summary: Dict[str, Any],
    suggestion: Dict[str, Any],
    baseline: Optional[Dict[str, Any]],
    summary_meta: Dict[str, Any],
) -> List[str]:
    bullets: List[str] = []

    p95 = summary.get("p95_ms")
    if isinstance(p95, (int, float)):
        bullets.append(f"P95 latency sits at {p95:.0f} ms (threshold {_P95_LATENCY_THRESHOLD_MS:.0f} ms).")
    else:
        bullets.append("Latency p95 not reported; monitor next run.")

    err_rate = summary.get("err_rate")
    if isinstance(err_rate, (int, float)):
        bullets.append(f"Error rate {err_rate:.2%} (limit {_ERR_RATE_THRESHOLD:.2%}).")
    else:
        bullets.append("Error rate unavailable; verify logging pipeline.")

    recall = summary.get("recall_at_10")
    base_recall = baseline.get("recall_at_10") if baseline else None
    if isinstance(recall, (int, float)) and isinstance(base_recall, (int, float)):
        delta = recall - base_recall
        bullets.append(f"Recall@10 delta vs baseline: {delta:+.3f}.")
    elif isinstance(recall, (int, float)):
        bullets.append(f"Recall@10 observed at {recall:.3f}.")
    else:
        bullets.append("Recall@10 missing; schedule validation sweep.")

    cost_tokens = summary.get("cost_tokens")
    if isinstance(cost_tokens, (int, float)):
        bullets.append(f"Token spend per run: {cost_tokens:.0f} (cap {_COST_TOKEN_HIGH_THRESHOLD:.0f}).")

    changes = suggestion.get("changes", {}) if suggestion else {}
    if changes:
        bullets.append(f"Recommended change set: {', '.join(changes.keys())}.")
    elif summary_meta.get("status_note") == "job_not_found":
        bullets.append("Job not found; verify job_id or retention window.")
    else:
        bullets.append("No immediate mitigations recommended.")

    return bullets[:5]


def _format_compact_summary(summary: Dict[str, Any]) -> Optional[str]:
    parts: List[str] = []
    p95 = summary.get("p95_ms")
    if isinstance(p95, (int, float)):
        parts.append(f"P95 {p95:.0f}ms")
    err_rate = summary.get("err_rate")
    if isinstance(err_rate, (int, float)):
        parts.append(f"Err {err_rate:.2%}")
    recall = summary.get("recall_at_10")
    if isinstance(recall, (int, float)):
        parts.append(f"Recall {recall:.3f}")
    cost_tokens = summary.get("cost_tokens")
    if isinstance(cost_tokens, (int, float)):
        parts.append(f"Tokens {cost_tokens:.0f}")
    status = summary.get("status")
    if status:
        parts.append(f"Status {status}")
    return " · ".join(parts) if parts else None


def _persist_review(job_id: str, payload: Dict[str, Any]) -> None:
    try:
        _REVIEWS_ROOT.mkdir(parents=True, exist_ok=True)
        review_path = _REVIEWS_ROOT / f"{job_id}.review.json"
        with review_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
    except Exception as exc:
        logger.warning("[STEWARD] Failed to persist review for %s: %s", job_id, exc)

