from typing import Any, Dict, Optional
import os
import time

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, validator

from agents.orchestrator.flow import ExperimentPlan, OrchestratorFlow
from agents.orchestrator.config_loader import get_orchestrator_config


router = APIRouter()
_orchestrator_flow = OrchestratorFlow()


class ExperimentPlanRequest(BaseModel):
    # Support both old format (dataset, sample_size, search_space) and new format (preset, collection, overrides)
    dataset: Optional[str] = None
    sample_size: Optional[int] = None
    search_space: Optional[Dict[str, Any]] = None
    budget: Optional[Dict[str, Any]] = None
    concurrency: Optional[int] = None
    baseline_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # New format: preset and collection
    preset: Optional[str] = None
    collection: Optional[str] = None
    overrides: Optional[Dict[str, Any]] = None

    @validator("dataset")
    def _dataset_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value:
            raise ValueError("dataset must be a non-empty string")
        return value

    @validator("sample_size")
    def _sample_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("sample_size must be positive")
        return value


@router.post("/run")
def orchestrate_run(
    body: ExperimentPlanRequest,
    commit: bool = Query(False, description="Commit to execute (default: false, dry-run)"),
) -> Dict[str, Any]:
    try:
        # Convert preset/collection format to ExperimentPlan format
        payload = body.dict(exclude_none=True)
        
        # If using preset/collection format, convert to ExperimentPlan format
        if payload.get("preset") or payload.get("collection"):
            config = get_orchestrator_config()
            collection = payload.get("collection") or (config.get("collections") or ["fiqa_para_50k"])[0]
            preset = payload.get("preset", "smoke")
            overrides = payload.get("overrides") or {}
            
            # Get smoke config defaults
            smoke_cfg = config.get("smoke", {})
            grid_cfg = config.get("grid", {})
            
            # Build search_space from overrides and defaults
            search_space = {}
            if "top_k" in overrides:
                search_space["top_k"] = [overrides["top_k"]]
            elif grid_cfg.get("top_k"):
                search_space["top_k"] = grid_cfg["top_k"]
            else:
                search_space["top_k"] = [smoke_cfg.get("top_k", 10)]
            
            if "mmr" in overrides:
                search_space["mmr"] = [overrides["mmr"]]
            elif grid_cfg.get("mmr"):
                search_space["mmr"] = grid_cfg["mmr"]
            else:
                search_space["mmr"] = [smoke_cfg.get("mmr", False)]
            
            if "ef_search" in overrides:
                search_space["ef_search"] = [overrides["ef_search"]]
            elif grid_cfg.get("ef_search"):
                search_space["ef_search"] = grid_cfg["ef_search"]
            
            # Build plan payload
            plan_payload = {
                "dataset": collection,
                "sample_size": overrides.get("sample", smoke_cfg.get("sample", 50)),
                "search_space": search_space,
                "budget": config.get("budget", {}),
                "concurrency": overrides.get("concurrency", smoke_cfg.get("concurrency")),
                "baseline_id": config.get("baseline_policy"),
                "metadata": {"preset": preset, "collection": collection, **overrides}
            }
        else:
            # Use existing format
            if not payload.get("dataset"):
                raise ValueError("Either (preset/collection) or (dataset/sample_size/search_space) must be provided")
            if not payload.get("sample_size"):
                raise ValueError("sample_size is required")
            if not payload.get("search_space"):
                raise ValueError("search_space is required")
            plan_payload = payload
        
        plan = ExperimentPlan.from_dict(plan_payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = _orchestrator_flow.start(plan, commit=commit)
    return result


@router.get("/status")
def orchestrate_status(run_id: str = Query(..., description="Unique orchestrator run_id")) -> Dict[str, Any]:
    try:
        return _orchestrator_flow.get_status(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"run_id `{run_id}` not found") from exc


@router.get("/report")
def orchestrate_report(run_id: str = Query(..., description="Unique orchestrator run_id")) -> Dict[str, Any]:
    try:
        artifacts = _orchestrator_flow.get_report_artifacts(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"run_id `{run_id}` not found or incomplete") from None
    return {"run_id": run_id, **artifacts}

