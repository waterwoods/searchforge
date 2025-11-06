"""
LabOps Agent V2 Endpoints
=========================
REST API for Agent V2 operations.

Endpoints:
- POST /ops/agent/run?v=2&dry=<true|false> - Run agent once
- GET  /ops/agent/summary?v=2 - Get last V2 summary

Schema:
  Run response:
    {
      "ok": bool,
      "mode": "dry" | "live",
      "verdict": "pass" | "edge" | "fail" | "error" | "blocked",
      "timestamp": str
    }
  
  Summary response:
    {
      "ok": bool,
      "delta_p95_pct": float,
      "delta_qps_pct": float,
      "error_rate_pct": float,
      "bullets": list[str],
      "generated_at": str
    }
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

# Import V2 agent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.labops.v2.agent_runner_v2 import LabOpsAgentV2, load_config


# Create router (no prefix - will be added in app_main.py)
router = APIRouter(tags=["agent_v2"])


# Global state for last run
_last_v2_run: Optional[Dict[str, Any]] = None
_last_v2_summary: Optional[Dict[str, Any]] = None
_agent_lock = asyncio.Lock()


class AgentRunRequest(BaseModel):
    """Request model for agent run (optional, can use query params)."""
    config_path: Optional[str] = "agents/labops/plan/plan_combo.yaml"
    auto_apply: bool = False


def _safe_parse_summary() -> Dict[str, Any]:
    """
    Parse last V2 summary from file.
    Gracefully degrade if file missing or malformed.
    
    NEVER raises exceptions - always returns valid dict with defaults.
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        summary_path = project_root / "reports" / "LABOPS_AGENT_V2_SUMMARY.txt"
        
        # File not found - return soft-fail with helpful message
        if not summary_path.exists():
            return {
                "ok": False,
                "error": "no_report",
                "message": "No report generated yet",
                "delta_p95_pct": 0.0,
                "delta_qps_pct": 0.0,
                "error_rate_pct": 0.0,
                "bullets": ["尚未生成报告 - Agent未运行或首次启动"],
                "generated_at": None,
                "mode": "rules"
            }
        
        # Read and parse summary file
        text = summary_path.read_text()
        
        # Empty file guard
        if not text or len(text.strip()) == 0:
            return {
                "ok": False,
                "error": "empty_report",
                "message": "Report file is empty",
                "delta_p95_pct": 0.0,
                "delta_qps_pct": 0.0,
                "error_rate_pct": 0.0,
                "bullets": ["报告文件为空"],
                "generated_at": None,
                "mode": "rules"
            }
        
        # Extract metrics (simple regex-free parsing)
        lines = text.split('\n')
        
        delta_p95 = 0.0
        delta_qps = 0.0
        error_rate = 0.0
        bullets = []
        generated_at = None
        
        for i, line in enumerate(lines):
            # Extract timestamp
            if line.startswith("Timestamp:"):
                try:
                    generated_at = line.split(":", 1)[1].strip()
                except (IndexError, AttributeError):
                    pass
            
            # Extract metrics with safe parsing
            if line.startswith("ΔP95:"):
                try:
                    val_str = line.split(":", 1)[1].strip().replace("%", "").replace("+", "")
                    delta_p95 = float(val_str) if val_str else 0.0
                except (ValueError, IndexError, AttributeError):
                    delta_p95 = 0.0
            
            if line.startswith("ΔQPS:"):
                try:
                    val_str = line.split(":", 1)[1].strip().replace("%", "").replace("+", "")
                    delta_qps = float(val_str) if val_str else 0.0
                except (ValueError, IndexError, AttributeError):
                    delta_qps = 0.0
            
            if line.startswith("Error Rate:"):
                try:
                    val_str = line.split(":", 1)[1].strip().replace("%", "")
                    error_rate = float(val_str) if val_str else 0.0
                except (ValueError, IndexError, AttributeError):
                    error_rate = 0.0
            
            # Extract bullets (lines starting with •)
            if line.strip().startswith("•"):
                try:
                    bullet = line.strip()[1:].strip()  # Remove bullet char
                    if bullet:  # Only add non-empty bullets
                        bullets.append(bullet)
                except (IndexError, AttributeError):
                    pass
        
        # No data guard - if all metrics are 0 and no bullets
        if delta_p95 == 0.0 and delta_qps == 0.0 and error_rate == 0.0 and not bullets:
            bullets.append("暂无数据 - 等待实验结果")
        
        return {
            "ok": True,
            "delta_p95_pct": delta_p95,
            "delta_qps_pct": delta_qps,
            "error_rate_pct": error_rate,
            "bullets": bullets if bullets else ["实验已完成，详情见报告"],
            "generated_at": generated_at or datetime.now().isoformat(),
            "mode": "rules"
        }
    
    except Exception as e:
        # Catch-all fallback - should never reach here but defensive
        error_type = type(e).__name__
        return {
            "ok": False,
            "error": "parse_failed",
            "message": f"{error_type}: {str(e)[:100]}",
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "bullets": [f"解析失败: {error_type}"],
            "generated_at": None,
            "mode": "error"
        }


@router.post("/run")
async def run_agent_v2(
    v: int = Query(2, description="API version (must be 2)"),
    dry: bool = Query(True, description="Dry run mode"),
    config_path: str = Query("agents/labops/plan/plan_combo.yaml", description="Config path")
) -> Dict[str, Any]:
    """
    Run Agent V2 once.
    
    Query params:
    - v: API version (must be 2)
    - dry: Dry run mode (default: true)
    - config_path: Path to config file
    
    Returns:
        {
          "ok": bool,
          "mode": "dry" | "live",
          "verdict": str,
          "timestamp": str,
          "message": str (optional)
        }
    """
    # Version guard
    if v != 2:
        return {
            "ok": False,
            "error": "invalid_version",
            "message": f"v={v} not supported, use v=2"
        }
    
    # Mutual exclusion lock
    async with _agent_lock:
        try:
            # Load config
            project_root = Path(__file__).parent.parent.parent.parent
            cfg_path = project_root / config_path
            
            if not cfg_path.exists():
                return {
                    "ok": False,
                    "error": "config_not_found",
                    "message": f"Config not found: {config_path}",
                    "mode": "dry" if dry else "live",
                    "verdict": "error",
                    "timestamp": datetime.now().isoformat()
                }
            
            config = load_config(cfg_path)
            
            # Run agent in thread pool (blocking operation)
            def _run_sync():
                agent = LabOpsAgentV2(config, dry_run=dry, auto_apply=False)
                return agent.run()
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _run_sync)
            
            # Extract verdict
            verdict = "error"
            if result.get("ok"):
                judgment = result.get("judgment", {})
                decision = judgment.get("decision", {})
                verdict = decision.get("verdict", "unknown")
            elif result.get("phase") == "health_gate":
                verdict = "blocked"
            
            # Store last run
            global _last_v2_run
            _last_v2_run = result
            
            return {
                "ok": result.get("ok", False),
                "mode": "dry" if dry else "live",
                "verdict": verdict,
                "timestamp": datetime.now().isoformat(),
                "message": f"Agent V2 run completed ({verdict})"
            }
        
        except Exception as e:
            # V2: Never 500, return safe default
            return {
                "ok": False,
                "error": "agent_exception",
                "message": str(e)[:200],
                "mode": "dry" if dry else "live",
                "verdict": "error",
                "timestamp": datetime.now().isoformat()
            }


@router.get("/summary")
async def get_agent_v2_summary(
    v: int = Query(2, description="API version (must be 2)")
) -> Dict[str, Any]:
    """
    Get last V2 agent summary.
    
    NEVER raises HTTPException. Always returns 200 with JSON.
    
    Returns:
        {
          "ok": bool,
          "delta_p95_pct": float,
          "delta_qps_pct": float,
          "error_rate_pct": float,
          "bullets": list[str],
          "generated_at": str,
          "mode": str  # "rules" or "error"
        }
    """
    try:
        # Version guard
        if v != 2:
            return {
                "ok": False,
                "error": "invalid_version",
                "message": f"v={v} not supported, use v=2",
                "delta_p95_pct": 0.0,
                "delta_qps_pct": 0.0,
                "error_rate_pct": 0.0,
                "bullets": ["Invalid version"],
                "generated_at": None,
                "mode": "error"
            }
        
        # Parse summary from file (already has internal try/except)
        summary = _safe_parse_summary()
        
        # Ensure all required fields exist with defaults
        return {
            "ok": summary.get("ok", False),
            "delta_p95_pct": summary.get("delta_p95_pct", 0.0),
            "delta_qps_pct": summary.get("delta_qps_pct", 0.0),
            "error_rate_pct": summary.get("error_rate_pct", 0.0),
            "bullets": summary.get("bullets", ["暂无数据"]),
            "generated_at": summary.get("generated_at"),
            "mode": summary.get("mode", "rules"),
            "error": summary.get("error")  # Optional error field
        }
    
    except Exception as e:
        # Soft-fail: NEVER raise 500, always return 200 + JSON
        error_type = type(e).__name__
        return {
            "ok": False,
            "error": "v2_summary_soft_fail",
            "message": f"{error_type}: {str(e)[:150]}",
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "bullets": [f"v2 summary soft-fail: {error_type}"],
            "generated_at": None,
            "mode": "error"
        }


@router.get("/history")
async def get_agent_v2_history(
    v: int = Query(2, description="API version (must be 2)"),
    n: int = Query(5, description="Number of recent runs")
) -> Dict[str, Any]:
    """
    Get last N runs from history_v2.jsonl.
    
    Returns:
        {
          "ok": bool,
          "runs": list[dict],
          "count": int
        }
    """
    # Version guard
    if v != 2:
        return {
            "ok": False,
            "error": "invalid_version",
            "message": f"v={v} not supported, use v=2",
            "runs": [],
            "count": 0
        }
    
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        history_path = project_root / "agents" / "labops" / "state" / "history_v2.jsonl"
        
        if not history_path.exists():
            return {
                "ok": True,
                "runs": [],
                "count": 0,
                "message": "No history yet"
            }
        
        # Read last N lines
        with open(history_path, 'r') as f:
            lines = f.readlines()
        
        # Parse JSON lines (last N)
        runs = []
        for line in lines[-n:]:
            try:
                runs.append(json.loads(line))
            except:
                pass
        
        return {
            "ok": True,
            "runs": runs,
            "count": len(runs)
        }
    
    except Exception as e:
        return {
            "ok": False,
            "error": "history_failed",
            "message": str(e)[:200],
            "runs": [],
            "count": 0
        }

