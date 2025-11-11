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

    obs_url = obs.build_obs_url(request.job_id)

    trace = obs.trace_start(
        request.job_id,
        name="steward.run",
        input=obs.redact({"job_id": request.job_id, "resume": resume}),
        metadata={"job_id": request.job_id},
        force_sample=True,
    )
    obs_ctx = {"trace": trace, "trace_id": request.job_id} if trace else {}

    try:
        state = app.invoke(
            {
                "job_id": request.job_id,
                "resume": resume,
                "obs_ctx": obs_ctx,
                "obs_url": obs_url,
            },
            config={"configurable": {"thread_id": request.job_id}},
        )
    except Exception as exc:
        obs.trace_end(trace, output=obs.redact({"decision": "", "errors": [str(exc)]}))
        raise HTTPException(status_code=500, detail=f"Failed to run steward graph: {exc}") from exc

    response = {
        "job_id": request.job_id,
        "resume": bool(state.get("resume") or resume),
        "plan": state.get("plan"),
        "dryrun_status": state.get("dryrun_status"),
        "metrics": state.get("metrics"),
        "decision": state.get("decision"),
        "baseline_path": state.get("baseline_path"),
        "thresholds": state.get("thresholds"),
        "errors": state.get("errors", []),
        "obs_url": obs_url,
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

    obs.trace_end(
        trace,
        output=obs.redact(response),
        scores=scores,
    )

    return response

