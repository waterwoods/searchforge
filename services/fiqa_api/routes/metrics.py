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
from typing import List, Dict, Any, Optional, Union
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


class DemoSummaryResponse(BaseModel):
    dataset: Union[str, Dict[str, Any]]  # Can be string or dict for safe default
    kpis: Dict[str, Optional[float]]  # Allow None for missing metrics
    timestamp: str
    message: Optional[str] = None  # Optional guidance message


@router.get("/demo-summary", response_model=DemoSummaryResponse)
async def get_demo_summary():
    """
    Get demo summary from benchmark results for Metrics Hub demo mode.
    
    Reads results/fiqa_bench/demo_summary.json (preferred) or results/fiqa_bench/metrics.json (fallback).
    Returns normalized schema with KPIs: recall@5, recall@10, mrr@5, ndcg@10, avg_latency_ms, p95_latency_ms.
    
    Returns:
        {
            "dataset": "fiqa_10k_v1",
            "kpis": {
                "recall@5": 1.0,
                "recall@10": 0.975,
                "mrr@5": 1.0,
                "ndcg@10": 0.9824,
                "avg_latency_ms": 44.86,
                "p95_latency_ms": 70.0
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    Raises:
        404: If neither demo_summary.json nor metrics.json exists
        500: If file read/parse fails
    """
    # Try demo_summary.json first, then fallback to metrics.json
    results_dir = REPO_ROOT / "results" / "fiqa_bench"
    demo_summary_path = results_dir / "demo_summary.json"
    metrics_path = results_dir / "metrics.json"
    
    data_file = None
    data = None
    
    # Prefer demo_summary.json
    if demo_summary_path.exists():
        data_file = demo_summary_path
        try:
            with open(demo_summary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded demo_summary.json from {demo_summary_path}")
        except Exception as e:
            logger.warning(f"Failed to read demo_summary.json: {e}, trying metrics.json")
            data_file = None
            data = None
    
    # Fallback to metrics.json
    if data_file is None and metrics_path.exists():
        data_file = metrics_path
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded metrics.json from {metrics_path}")
        except Exception as e:
            logger.error(f"Failed to read metrics.json: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read metrics file: {str(e)}"
            )
    
    # If no artifacts found, return safe default demo payload (never 404)
    if data_file is None or data is None:
        logger.warning(f"Demo summary artifacts not found at {results_dir}, returning safe default")
        from datetime import datetime
        return {
            "dataset": {
                "name": "FIQA 10k",
                "split": "test",
                "queries": 0,
                "collection": "fiqa_10k_v1"
            },
            "kpis": {
                "Recall@5": None,
                "Recall@10": None,
                "MRR@5": None,
                "nDCG@10": None,
                "avg_latency_ms": None,
                "p95_latency_ms": None
            },
            "message": "No benchmark artifacts found. Run: python scripts/fiqa_rag_benchmark.py --split test --limit 50",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    # Normalize schema
    try:
        # Extract dataset name
        dataset = data.get("dataset", "fiqa_10k_v1")
        
        # Extract metrics from nested structure
        metrics = data.get("metrics", {})
        counts = data.get("counts", {})
        
        # Build normalized KPIs
        kpis: Dict[str, float] = {}
        
        # Recall metrics
        if "Recall@5" in metrics:
            kpis["recall@5"] = float(metrics["Recall@5"])
        elif "recall@5" in metrics:
            kpis["recall@5"] = float(metrics["recall@5"])
        
        if "Recall@10" in metrics:
            kpis["recall@10"] = float(metrics["Recall@10"])
        elif "recall@10" in metrics:
            kpis["recall@10"] = float(metrics["recall@10"])
        
        # MRR metrics
        if "MRR@5" in metrics:
            kpis["mrr@5"] = float(metrics["MRR@5"])
        elif "mrr@5" in metrics:
            kpis["mrr@5"] = float(metrics["mrr@5"])
        
        # nDCG metrics
        if "nDCG@10" in metrics:
            kpis["ndcg@10"] = float(metrics["nDCG@10"])
        elif "ndcg@10" in metrics:
            kpis["ndcg@10"] = float(metrics["ndcg@10"])
        
        # Latency metrics
        if "avg_latency_ms" in counts:
            kpis["avg_latency_ms"] = float(counts["avg_latency_ms"])
        elif "avg_latency_ms" in data:
            kpis["avg_latency_ms"] = float(data["avg_latency_ms"])
        
        if "p95_latency_ms" in counts:
            kpis["p95_latency_ms"] = float(counts["p95_latency_ms"])
        elif "p95_latency_ms" in data:
            kpis["p95_latency_ms"] = float(data["p95_latency_ms"])
        
        # Get timestamp from file mtime or use current time
        if data_file:
            timestamp = datetime.fromtimestamp(data_file.stat().st_mtime).isoformat() + "Z"
        else:
            timestamp = datetime.utcnow().isoformat() + "Z"
        
        return DemoSummaryResponse(
            dataset=dataset,
            kpis=kpis,
            timestamp=timestamp,
            message=None
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Failed to normalize demo summary data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to normalize demo summary: {str(e)}"
        )


class AutoInsuranceEvalResponse(BaseModel):
    collection: str
    total_queries: int
    avg_hit_at_5: float
    pct_queries_with_3_plus_relevant: float
    avg_latency_ms: float
    passed: bool
    timestamp: str
    message: Optional[str] = None
    language_breakdown: Optional[Dict[str, Any]] = None


@router.get("/auto-insurance-eval", response_model=AutoInsuranceEvalResponse)
async def get_auto_insurance_eval():
    """
    Get latest auto insurance RAG evaluation metrics.
    
    Reads results/auto_insurance/EVAL_REPORT.json and returns aggregate metrics.
    Returns safe defaults if file is missing (never 404).
    
    Returns:
        {
            "collection": "auto_insurance_v2_clean",
            "total_queries": 20,
            "avg_hit_at_5": 0.75,
            "pct_queries_with_3_plus_relevant": 85.0,
            "avg_latency_ms": 45.2,
            "passed": true,
            "timestamp": "2024-01-01T00:00:00Z",
            "message": null,
            "language_breakdown": {...}
        }
    """
    eval_report_path = REPO_ROOT / "results" / "auto_insurance" / "EVAL_REPORT.json"
    
    if not eval_report_path.exists():
        logger.warning(f"Auto insurance eval report not found at {eval_report_path}")
        return AutoInsuranceEvalResponse(
            collection="auto_insurance_v2_clean",
            total_queries=0,
            avg_hit_at_5=0.0,
            pct_queries_with_3_plus_relevant=0.0,
            avg_latency_ms=0.0,
            passed=False,
            timestamp=datetime.utcnow().isoformat() + "Z",
            message="No evaluation report found. Run: ./scripts/run_auto_insurance_refresh.sh",
            language_breakdown=None
        )
    
    try:
        with open(eval_report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract metrics
        return AutoInsuranceEvalResponse(
            collection=data.get("collection", "auto_insurance_v2_clean"),
            total_queries=data.get("total_queries", 0),
            avg_hit_at_5=float(data.get("avg_hit_at_5", 0.0)),
            pct_queries_with_3_plus_relevant=float(data.get("pct_queries_with_3_plus_relevant", 0.0)),
            avg_latency_ms=float(data.get("avg_latency_ms", 0.0)),
            passed=bool(data.get("passed", False)),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            message=None,
            language_breakdown=data.get("language_breakdown")
        )
    except Exception as e:
        logger.error(f"Failed to read auto insurance eval report: {e}", exc_info=True)
        return AutoInsuranceEvalResponse(
            collection="auto_insurance_v2_clean",
            total_queries=0,
            avg_hit_at_5=0.0,
            pct_queries_with_3_plus_relevant=0.0,
            avg_latency_ms=0.0,
            passed=False,
            timestamp=datetime.utcnow().isoformat() + "Z",
            message=f"Failed to read evaluation report: {str(e)}",
            language_breakdown=None
        )

