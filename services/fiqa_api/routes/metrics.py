"""
Metrics Routes
==============
API routes for metrics data (trilines, observability URLs, etc.)
"""
import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Response, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.fiqa_api.settings import RUNS_PATH, REPO_ROOT
from services.fiqa_api.cost import load_pricing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class TrilinesPoint(BaseModel):
    budget: float
    t: float  # p95_ms
    p95_ms: float
    recall10: float  # recall_or_success_rate
    cost_1k_usd: float


class TrilinesResponse(BaseModel):
    points: List[TrilinesPoint]
    budgets: List[float]
    updated_at: str


class KPIResponse(BaseModel):
    success_rate: float
    p95_down: bool
    bounds_ok: bool
    stable_detune: bool
    budgets: List[float]
    updated_at: str
    cost_enabled: bool


@router.get("/trilines", response_model=TrilinesResponse)
async def get_trilines(mode: str = Query(default="full", description="Data mode: 'full' or 'fast'")):
    """
    Read .runs/real_large_trilines.csv (or real_fast_trilines.csv for mode=fast) and return JSON.
    
    Args:
        mode: Data mode - "full" for full CI (2000×15) or "fast" for fast CI (200×5)
    
    Returns:
        {
            "points": [{"budget": 200, "t": 12.79, "p95_ms": 12.79, "recall10": 1.0, "cost_1k_usd": 0.06}, ...],
            "budgets": [200, 400, 800, ...],
            "updated_at": "2024-01-01T00:00:00Z"
        }
    """
    if mode == "fast":
        csv_path = RUNS_PATH / "real_fast_trilines.csv"
    else:
        csv_path = RUNS_PATH / "real_large_trilines.csv"
    
    if not csv_path.exists():
        logger.warning(f"Trilines CSV not found at {csv_path}")
        return JSONResponse(
            status_code=200,
            content={
                "points": [],
                "budgets": [],
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    try:
        points: List[TrilinesPoint] = []
        budgets: List[float] = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    budget = float(row.get('budget_ms', 0))
                    p95_ms = float(row.get('p95_ms', 0))
                    recall10 = float(row.get('recall_or_success_rate', 0))
                    cost_1k_usd = float(row.get('cost_per_1k_usd', 0))
                    policy = row.get('policy', 'Balanced')  # Default to Balanced if not present
                    
                    point = TrilinesPoint(
                        budget=budget,
                        t=p95_ms,  # t is same as p95_ms
                        p95_ms=p95_ms,
                        recall10=recall10,
                        cost_1k_usd=cost_1k_usd
                    )
                    points.append(point)
                    if budget not in budgets:
                        budgets.append(budget)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row: {row}, error: {e}")
                    continue
        
        # Sort budgets
        budgets.sort()
        
        # Get file modification time
        updated_at = datetime.fromtimestamp(csv_path.stat().st_mtime).isoformat() + "Z"
        
        return TrilinesResponse(
            points=points,
            budgets=budgets,
            updated_at=updated_at
        )
    except Exception as e:
        logger.error(f"Error reading trilines CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read trilines data: {str(e)}")


@router.get("/kpi", response_model=KPIResponse)
async def get_kpi(mode: str = Query(default="full", description="Data mode: 'full' or 'fast'")):
    """
    Read .runs/e2e_report.json & .runs/pareto.json (or pareto_fast.json for mode=fast) and return KPI metrics.
    
    Args:
        mode: Data mode - "full" for full CI (2000×15) or "fast" for fast CI (200×5)
            Note: e2e_report.json is always read from full CI for both modes.
    
    Returns:
        {
            "success_rate": 0.95,
            "p95_down": true,
            "bounds_ok": true,
            "stable_detune": true,
            "budgets": [200, 400, 800, 1000, 1200],
            "updated_at": "2024-01-01T00:00:00Z",
            "cost_enabled": true
        }
    """
    e2e_path = RUNS_PATH / "e2e_report.json"
    if mode == "fast":
        pareto_path = RUNS_PATH / "pareto_fast.json"
    else:
        pareto_path = RUNS_PATH / "pareto.json"
    
    # Default values
    success_rate = 0.0
    p95_down = False
    bounds_ok = False
    stable_detune = False
    budgets: List[float] = []
    updated_at_times: List[float] = []
    
    # Read e2e_report.json
    e2e_data: Optional[Dict[str, Any]] = None
    if e2e_path.exists():
        try:
            with open(e2e_path, 'r', encoding='utf-8') as f:
                e2e_data = json.load(f)
            updated_at_times.append(e2e_path.stat().st_mtime)
        except Exception as e:
            logger.warning(f"Failed to read e2e_report.json: {e}")
    
    # Read pareto.json
    pareto_data: Optional[Dict[str, Any]] = None
    if pareto_path.exists():
        try:
            with open(pareto_path, 'r', encoding='utf-8') as f:
                pareto_data = json.load(f)
            updated_at_times.append(pareto_path.stat().st_mtime)
        except Exception as e:
            logger.warning(f"Failed to read pareto.json: {e}")
    
    # Extract values from pareto.json
    if pareto_data:
        if isinstance(pareto_data, dict):
            success_rate = float(pareto_data.get("success_rate", 0.0))
            p95_down = bool(pareto_data.get("p95_down", False))
            bounds_ok = bool(pareto_data.get("bounds_ok", False))
            stable_detune = bool(pareto_data.get("stable_detune", False))
            budgets_raw = pareto_data.get("budgets", [])
            if isinstance(budgets_raw, list):
                budgets = [float(b) for b in budgets_raw if isinstance(b, (int, float))]
        elif isinstance(pareto_data, list):
            # Legacy format: list of records
            # Extract from first entry or aggregate
            if pareto_data:
                first_entry = pareto_data[0] if isinstance(pareto_data[0], dict) else {}
                success_rate = float(first_entry.get("success_rate", 0.0))
                p95_down = bool(first_entry.get("p95_down", False))
                bounds_ok = True  # Default for legacy format
                stable_detune = True  # Default for legacy format
    
    # Calculate updated_at from latest mtime
    if updated_at_times:
        updated_at = datetime.fromtimestamp(max(updated_at_times)).isoformat() + "Z"
    else:
        updated_at = datetime.utcnow().isoformat() + "Z"
    
    # Check if cost is enabled using unified pricing parser
    _, _, cost_enabled, _ = load_pricing()
    
    return KPIResponse(
        success_rate=success_rate,
        p95_down=p95_down,
        bounds_ok=bounds_ok,
        stable_detune=stable_detune,
        budgets=budgets,
        updated_at=updated_at,
        cost_enabled=cost_enabled
    )


@router.get("/obs/url")
async def get_obs_url():
    """
    Get latest Langfuse URL.
    Returns 204 if URL is not available.
    """
    # Try to get Langfuse URL from environment or config
    langfuse_url = os.getenv("LANGFUSE_URL") or os.getenv("LANGFUSE_PUBLIC_URL")
    
    if not langfuse_url:
        # Return 204 No Content if URL is not available
        return Response(status_code=204)
    
    return {"url": langfuse_url}


@router.get("/obs/last")
async def get_obs_last(limit: int = Query(default=10, ge=1, le=100)):
    """
    Get last N trace URLs from .runs/obs_url.txt (latest first).
    Returns 204 if file is missing or empty.
    """
    obs_file = RUNS_PATH / "obs_url.txt"
    
    if not obs_file.exists():
        return Response(status_code=204)
    
    try:
        # Read all lines
        lines = obs_file.read_text(encoding="utf-8").splitlines()
        # Reverse to get latest first, filter non-empty, slice by limit
        urls = [line.strip() for line in reversed(lines) if line.strip()][:limit]
        
        if not urls:
            return Response(status_code=204)
        
        # Get file modification time
        updated_at = datetime.fromtimestamp(obs_file.stat().st_mtime).isoformat() + "Z"
        
        return {"urls": urls, "updated_at": updated_at}
    except Exception as e:
        logger.error(f"Error reading obs_url.txt: {e}", exc_info=True)
        return Response(status_code=204)

