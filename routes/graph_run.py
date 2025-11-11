from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestrators.steward_graph import app


router = APIRouter()


class StewardRunRequest(BaseModel):
    job_id: str


class StewardRunResponse(BaseModel):
    job_id: str
    plan: Optional[str] = None
    dryrun_status: Optional[str] = None
    errors: List[str] = []


@router.post("/run", response_model=StewardRunResponse)
async def run_steward_graph(request: StewardRunRequest) -> Dict[str, Any]:
    try:
        state = app.invoke(
            {"job_id": request.job_id},
            config={"configurable": {"thread_id": request.job_id}},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to run steward graph: {exc}") from exc

    return {
        "job_id": request.job_id,
        "plan": state.get("plan"),
        "dryrun_status": state.get("dryrun_status"),
        "errors": state.get("errors", []),
    }

