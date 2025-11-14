"""Lightweight AutoTuner API backed by the global singleton."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from services.fiqa_api import obs
from services.fiqa_api.autotuner_global import (
    clear_autotuner_state,
    get_global_autotuner,
    get_state_summary as get_global_state_summary,
    persist_state_snapshot,
    reset_global_autotuner,
    set_policy as set_global_policy,
)

router = APIRouter(prefix="/api/autotuner", tags=["autotuner"])


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
    if not trace_url:
        return
    try:
        runs_dir = Path(".runs")
        runs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        with (runs_dir / "obs_url.txt").open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} {trace_url.strip()}\n")
    except OSError:
        pass


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
async def autotuner_reset() -> Dict[str, Any]:
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
async def autotuner_set_policy(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="invalid_payload")
    policy_name = body.get("policy")
    if not policy_name:
        raise HTTPException(status_code=400, detail="policy_required")
    try:
        tuner, state = set_global_policy(policy_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    persist_state_snapshot(tuner, state)
    return {"ok": True, "policy": getattr(tuner, "policy_name", policy_name)}

