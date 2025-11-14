from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestrators.steward_graph import app
from services.fiqa_api import obs
logger = logging.getLogger(__name__)



router = APIRouter()


class StewardRunRequest(BaseModel):
    job_id: str


class StewardRunResponse(BaseModel):
    job_id: str
    resume: bool = False
    plan: Optional[str] = None
    dryrun_status: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    decision: Optional[str] = None
    baseline_path: Optional[str] = None
    thresholds: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    obs_url: str = ""
    trace_id: Optional[str] = None


@router.post("/run", response_model=StewardRunResponse)
async def run_steward_graph(request: StewardRunRequest) -> Dict[str, Any]:
    resume = False
    try:
        state_snapshot = app.get_state(config={"configurable": {"thread_id": request.job_id}})
        if state_snapshot and getattr(state_snapshot, "values", None):
            resume = True
    except AttributeError:
        logger.debug("LangGraph app does not expose get_state values attribute")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to inspect steward graph state for job %s: %s", request.job_id, exc)

    trace = obs.trace_start(
        request.job_id,
        name="steward.run",
        input=obs.redact({"job_id": request.job_id, "resume": resume}),
        metadata={"job_id": request.job_id},
        force_sample=True,
    )
    ctx_key = f"steward:{request.job_id}"
    trace_identifier = request.job_id
    if trace:
        trace_identifier = getattr(trace, "id", None) or getattr(trace, "trace_id", None) or request.job_id
    obs_ctx = {
        "job_id": request.job_id,
        "trace_id": trace_identifier,
    }
    if trace:
        obs_ctx["trace"] = trace
        obs_ctx["root"] = trace
    obs.register_ctx(ctx_key, obs_ctx)
    obs_ctx_state_value = ctx_key

    try:
        state = app.invoke(
            {
                "job_id": request.job_id,
                "resume": resume,
                "obs_ctx": obs_ctx_state_value,
                "obs_url": "",
            },
            config={"configurable": {"thread_id": request.job_id}},
        )
    except Exception as exc:
        obs.trace_end(trace, output=obs.redact({"decision": "", "errors": [str(exc)]}))
        obs.unregister_ctx(ctx_key)
        raise HTTPException(status_code=500, detail=f"Failed to run steward graph: {exc}") from exc

    response: Dict[str, Any] = {
        "job_id": request.job_id,
        "resume": bool(state.get("resume") or resume),
        "plan": state.get("plan"),
        "dryrun_status": state.get("dryrun_status"),
        "metrics": state.get("metrics"),
        "decision": state.get("decision"),
        "baseline_path": state.get("baseline_path"),
        "thresholds": state.get("thresholds"),
        "errors": state.get("errors", []),
    }

    scores: Dict[str, float] = {}
    try:
        metrics = state.get("metrics") if isinstance(state, dict) else None
        if isinstance(metrics, dict):
            if metrics.get("p95_ms") is not None:
                scores["p95_ms"] = metrics["p95_ms"]
            if metrics.get("recall@10") is not None:
                scores["recall@10"] = metrics["recall@10"]
            if metrics.get("err_rate") is not None:
                scores["err_rate"] = metrics["err_rate"]
    except Exception:
        pass

    metrics_payload = state.get("metrics") if isinstance(state, dict) else None
    finalize_ctx = obs.get_registered_ctx(ctx_key) or {}
    finalize_ctx.setdefault("job_id", request.job_id)
    finalize_ctx.setdefault("trace_id", trace_identifier)

    finalize_meta = None
    if isinstance(metrics_payload, dict):
        finalize_meta = {
            "p95_ms": metrics_payload.get("p95_ms"),
            "recall@10": metrics_payload.get("recall@10"),
            "err_rate": metrics_payload.get("err_rate"),
            "delta_recall": metrics_payload.get("delta_recall"),
        }

    finalize_error: Optional[HTTPException] = None
    try:
        obs.finalize_root(finalize_ctx, meta=finalize_meta)
    except HTTPException as exc:
        finalize_error = exc

    obs_url = finalize_ctx.get("obs_url", "")
    if isinstance(state, dict):
        state["obs_url"] = obs_url
    response["obs_url"] = obs_url
    response["trace_id"] = finalize_ctx.get("trace_id", trace_identifier)
    if isinstance(state, dict):
        state["trace_id"] = response["trace_id"]

    obs.trace_end(
        trace,
        output=obs.redact(response),
        scores=scores,
    )
    obs.unregister_ctx(ctx_key)

    if finalize_error:
        raise finalize_error

    return response

