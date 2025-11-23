"""Lightweight AutoTuner API backed by the global singleton."""

from __future__ import annotations

import collections
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, status

from services.fiqa_api import obs
from services.fiqa_api.autotuner_global import (
    clear_autotuner_state,
    get_global_autotuner,
    get_state_summary as get_global_state_summary,
    persist_state_snapshot,
    reset_global_autotuner,
    set_policy as set_global_policy,
)
from services.fiqa_api.obs import append_trace

router = APIRouter(prefix="/api/autotuner", tags=["autotuner"])

# Authentication
_AUTOTUNER_TOKENS = [
    token.strip()
    for token in os.getenv("AUTOTUNER_TOKENS", "").split(",")
    if token.strip()
]

# Rate limiting: sliding window per token/IP (default: 12 requests per 60s)
_AUTOTUNER_RPS = int(os.getenv("AUTOTUNER_RPS", "12"))
_RATE_LIMIT_WINDOW = 60.0  # seconds
_rate_limit_store: Dict[str, collections.deque] = {}
_rate_limit_lock = collections.defaultdict(lambda: collections.deque())


def _check_auth(request: Request) -> None:
    """Check authentication token from X-Autotuner-Token header."""
    if not _AUTOTUNER_TOKENS:
        # No tokens configured, allow all requests
        return
    
    token = request.headers.get("X-Autotuner-Token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Autotuner-Token header"
        )
    
    if token not in _AUTOTUNER_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )


def _check_rate_limit(request: Request) -> None:
    """Check rate limit using sliding window (per token or IP)."""
    if _AUTOTUNER_RPS <= 0:
        return
    
    # Use token if available, otherwise use IP
    token = request.headers.get("X-Autotuner-Token")
    identifier = token or request.client.host if request.client else "unknown"
    
    now = time.time()
    window = _rate_limit_lock[identifier]
    
    # Remove entries outside the window
    while window and window[0] < now - _RATE_LIMIT_WINDOW:
        window.popleft()
    
    # Check if limit exceeded
    if len(window) >= _AUTOTUNER_RPS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {_AUTOTUNER_RPS} requests per {_RATE_LIMIT_WINDOW}s"
        )
    
    # Record this request
    window.append(now)


def _ensure_global():
    tuner, state = get_global_autotuner()
    if tuner is None or state is None:
        raise HTTPException(status_code=503, detail="autotuner_unavailable")
    return tuner, state


def _serialize_state(tuner, state) -> Dict[str, Any]:
    params = state.get_current_params()
    params.update(state.get_convergence_status())
    history = list(getattr(state, "parameter_history", []))
    return {
        "params": params,
        "history_len": len(history),
        "parameter_history": history,
        "metrics": state.get_smoothed_metrics(),
        "policy": getattr(tuner, "policy_name", getattr(getattr(tuner, "policy", None), "name", None)),
    }


def _append_obs_line(trace_url: str) -> None:
    """Append trace URL using rolling trace utility."""
    append_trace(trace_url, limit=200)


@router.get("/status")
async def autotuner_status(request: Request) -> Dict[str, Any]:
    tuner, state = _ensure_global()
    trace_id = request.headers.get("X-Trace-Id")
    if trace_id:
        obs.persist_trace_id(trace_id)
        trace_url = obs.build_obs_url(trace_id)
        if trace_url:
            obs.persist_obs_url(trace_url)
            _append_obs_line(trace_url)
    payload = _serialize_state(tuner, state)
    summary = get_global_state_summary()
    payload["history_len"] = summary["history_len"]
    payload["last_params"] = summary["last_params"]
    payload["state_file_mtime"] = summary["file_mtime"]
    payload["ok"] = True
    return payload


@router.post("/suggest")
async def autotuner_suggest(request: Request, body: Dict[str, Any]) -> Dict[str, Any]:
    _check_auth(request)
    _check_rate_limit(request)
    tuner, state = _ensure_global()

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="invalid_metrics_payload")

    trace_id = request.headers.get("X-Trace-Id") or body.get("trace_id")
    if trace_id:
        obs.persist_trace_id(trace_id)

    try:
        next_params = tuner.suggest(body)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    trace_url = body.get("trace_url") or obs.build_obs_url(trace_id)
    finalized_url = trace_url
    try:  # best-effort finalize
        result = obs.finalize_root(trace_id=trace_id, trace_url=trace_url)
        if isinstance(result, dict):
            finalized_url = result.get("trace_url") or finalized_url
    except Exception:  # pragma: no cover - defensive
        pass

    if finalized_url:
        _append_obs_line(finalized_url)

    payload = {
        "ok": True,
        "next_params": next_params,
    }
    payload.update(_serialize_state(tuner, state))
    persist_state_snapshot(tuner, state)
    summary = get_global_state_summary()
    payload["history_len"] = summary["history_len"]
    payload["last_params"] = summary["last_params"]
    payload["state_file_mtime"] = summary["file_mtime"]
    return payload


@router.get("/state")
async def autotuner_state() -> Dict[str, Any]:
    summary = get_global_state_summary()
    summary["ok"] = True
    return summary


@router.post("/reset")
async def autotuner_reset(request: Request) -> Dict[str, Any]:
    _check_auth(request)
    _check_rate_limit(request)
    clear_autotuner_state()
    tuner, state = reset_global_autotuner(clear_file=False)
    payload = _serialize_state(tuner, state)
    summary = get_global_state_summary()
    payload["history_len"] = summary["history_len"]
    payload["last_params"] = summary["last_params"]
    payload["state_file_mtime"] = summary["file_mtime"]
    payload["ok"] = True
    return payload


@router.post("/set_policy")
async def autotuner_set_policy(request: Request) -> Dict[str, Any]:
    """
    Set autotuner policy.
    
    Allowed policies: LatencyFirst, RecallFirst, Balanced
    
    Body:
        {"policy": "LatencyFirst" | "RecallFirst" | "Balanced"}
    """
    _check_auth(request)
    _check_rate_limit(request)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json")
    policy_name = (body.get("policy") or "").strip()
    if not policy_name:
        raise HTTPException(status_code=400, detail="policy_required")
    
    # Validate policy name (only allow the three preset policies)
    allowed_policies = {"LatencyFirst", "RecallFirst", "Balanced"}
    if policy_name not in allowed_policies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy '{policy_name}'. Allowed: {', '.join(sorted(allowed_policies))}"
        )
    
    try:
        tuner, state = set_global_policy(policy_name)
        persist_state_snapshot(tuner, state)
    except HTTPException:
        raise
    except Exception as e:
        # 避免 500 泄漏：记录日志，但返回 400 以便 CI 明确失败原因
        logging.getLogger(__name__).exception("set_policy failed")
        raise HTTPException(status_code=400, detail="set_policy_failed")
    return {"ok": True, "policy": getattr(tuner, "policy_name", policy_name)}

