from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestrators.steward_graph import app
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

    try:
        state = app.invoke(
            {"job_id": request.job_id, "resume": resume},
            config={"configurable": {"thread_id": request.job_id}},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to run steward graph: {exc}") from exc

    return {
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

