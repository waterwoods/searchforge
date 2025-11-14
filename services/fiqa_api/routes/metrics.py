"""
Metrics Routes
==============
API routes for metrics data (trilines, observability URLs, etc.)
"""
import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.fiqa_api.settings import RUNS_PATH, REPO_ROOT

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


@router.get("/trilines", response_model=TrilinesResponse)
async def get_trilines():
    """
    Read .runs/real_large_trilines.csv and return JSON.
    
    Returns:
        {
            "points": [{"budget": 200, "t": 12.79, "p95_ms": 12.79, "recall10": 1.0, "cost_1k_usd": 0.06}, ...],
            "budgets": [200, 400, 800, ...],
            "updated_at": "2024-01-01T00:00:00Z"
        }
    """
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

