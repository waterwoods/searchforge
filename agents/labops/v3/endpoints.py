"""
LabOps Agent V3 Endpoints
=========================
REST API for Agent V3 operations with LLM explanations and code navigation.

Endpoints:
- POST /api/agent/run?v=3&dry=<true|false> - Run agent V3 once
- GET  /api/agent/summary?v=3 - Get last V3 summary
- GET  /api/agent/history?v=3&n=10 - Get last N V3 runs

Schema:
  Run response:
    {
      "ok": bool,
      "mode": "dry" | "live",
      "verdict": "pass" | "edge" | "fail" | "error" | "blocked",
      "explainer_mode": "llm" | "rules" | "fallback",
      "timestamp": str
    }
  
  Summary response:
    {
      "ok": bool,
      "delta_p95_pct": float,
      "delta_qps_pct": float,
      "error_rate_pct": float,
      "bullets": list[str],  # ≤6 bullets
      "code_nav": list[dict],  # Code locations with {file, line, context}
      "explainer_mode": "llm" | "rules" | "fallback",
      "generated_at": str
    }
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

# Import V3 agent
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.labops.v3.runner_v3 import LabOpsAgentV3, load_config


# Create router (no prefix - will be added in app_main.py)
router = APIRouter(tags=["agent_v3"])


# Global state for last run
_last_v3_run: Optional[Dict[str, Any]] = None
_last_v3_summary: Optional[Dict[str, Any]] = None
_agent_lock = asyncio.Lock()


class AgentV3RunRequest(BaseModel):
    """Request model for V3 agent run (optional)."""
    config_path: Optional[str] = "agents/labops/plan/plan_combo.yaml"
    auto_apply: bool = False


def _safe_parse_summary_v3() -> Dict[str, Any]:
    """
    Parse last V3 summary from file.
    Gracefully degrade if file missing.
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        summary_path = project_root / "reports" / "LABOPS_AGENT_V3_SUMMARY.txt"
        
        if not summary_path.exists():
            return {
                "ok": False,
                "error": "no_report",
                "message": "No V3 report generated yet",
                "delta_p95_pct": 0.0,
                "delta_qps_pct": 0.0,
                "error_rate_pct": 0.0,
                "bullets": ["尚未生成 V3 报告"],
                "code_nav": [],
                "explainer_mode": "unknown",
                "generated_at": None
            }
        
        # Parse summary file
        text = summary_path.read_text()
        lines = text.split('\n')
        
        delta_p95 = 0.0
        delta_qps = 0.0
        error_rate = 0.0
        bullets = []
        code_nav = []
        explainer_mode = "unknown"
        generated_at = None
        
        # Parse sections
        in_explanation = False
        in_code_nav = False
        
        for i, line in enumerate(lines):
            # Extract timestamp
            if line.startswith("Timestamp:"):
                generated_at = line.split(":", 1)[1].strip()
            
            # Extract explainer mode
            if line.startswith("Explainer:"):
                explainer_mode = line.split(":", 1)[1].strip().lower()
            
            # Extract metrics
            if line.startswith("ΔP95:"):
                try:
                    val_str = line.split(":")[1].strip().replace("%", "").replace("+", "")
                    delta_p95 = float(val_str)
                except:
                    pass
            
            if line.startswith("ΔQPS:"):
                try:
                    val_str = line.split(":")[1].strip().replace("%", "").replace("+", "")
                    delta_qps = float(val_str)
                except:
                    pass
            
            if line.startswith("Error Rate:"):
                try:
                    val_str = line.split(":")[1].strip().replace("%", "")
                    error_rate = float(val_str)
                except:
                    pass
            
            # Start of explanation section
            if "EXPLANATION" in line:
                in_explanation = True
                in_code_nav = False
                continue
            
            # Start of code nav section
            if "CODE LOCATIONS" in line:
                in_explanation = False
                in_code_nav = True
                continue
            
            # End of sections
            if line.startswith("="):
                in_explanation = False
                in_code_nav = False
            
            # Extract bullets (lines starting with •)
            if in_explanation and line.strip().startswith("•"):
                bullet = line.strip()[1:].strip()
                bullets.append(bullet)
            
            # Extract code locations
            if in_code_nav and line.strip() and line.strip()[0].isdigit():
                # Format: "1. [context] file:line"
                try:
                    # Parse: "1. [判断逻辑] agents/labops/policies/decision.py:45"
                    parts = line.split("]", 1)
                    if len(parts) == 2:
                        context_part = parts[0].split("[", 1)
                        if len(context_part) == 2:
                            context = context_part[1].strip()
                            file_line = parts[1].strip()
                            
                            if ":" in file_line:
                                file_path, line_num_str = file_line.rsplit(":", 1)
                                line_num = int(line_num_str) if line_num_str.isdigit() else 0
                                
                                code_nav.append({
                                    "context": context,
                                    "file": file_path.strip(),
                                    "line": line_num
                                })
                except:
                    pass
        
        return {
            "ok": True,
            "delta_p95_pct": delta_p95,
            "delta_qps_pct": delta_qps,
            "error_rate_pct": error_rate,
            "bullets": bullets if bullets else ["实验已完成（V3），详情见报告"],
            "code_nav": code_nav,
            "explainer_mode": explainer_mode,
            "generated_at": generated_at or datetime.now().isoformat()
        }
    
    except Exception as e:
        # Fallback template
        return {
            "ok": False,
            "error": "parse_failed",
            "message": str(e),
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "bullets": [f"V3 解析失败: {str(e)[:50]}"],
            "code_nav": [],
            "explainer_mode": "error",
            "generated_at": None
        }


@router.post("/run")
async def run_agent_v3(
    v: int = Query(3, description="API version (must be 3 for V3)"),
    dry: bool = Query(True, description="Dry run mode"),
    config_path: str = Query("agents/labops/plan/plan_combo.yaml", description="Config path")
) -> Dict[str, Any]:
    """
    Run Agent V3 once (LLM explainer + code nav).
    
    Query params:
    - v: API version (must be 3 for V3, or 2 for V2)
    - dry: Dry run mode (default: true)
    - config_path: Path to config file
    
    Returns:
        {
          "ok": bool,
          "mode": "dry" | "live",
          "verdict": str,
          "explainer_mode": "llm" | "rules" | "fallback",
          "timestamp": str,
          "message": str (optional)
        }
    """
    # Version guard - V3 only handles v=3
    # v=2 is handled by V2 endpoints
    if v not in [2, 3]:
        return {
            "ok": False,
            "error": "invalid_version",
            "message": f"v={v} not supported, use v=2 or v=3"
        }
    
    # If v=2, delegate to V2 (will be handled by V2 router)
    # This endpoint only handles v=3
    if v != 3:
        return {
            "ok": False,
            "error": "wrong_endpoint",
            "message": f"Use v=2 endpoint for Agent V2, this is V3"
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
                    "explainer_mode": "n/a",
                    "timestamp": datetime.now().isoformat()
                }
            
            config = load_config(cfg_path)
            
            # Run agent V3 in thread pool (blocking operation)
            def _run_sync():
                agent = LabOpsAgentV3(config, dry_run=dry, auto_apply=False)
                return agent.run()
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _run_sync)
            
            # Extract verdict and explainer mode
            verdict = "error"
            explainer_mode = "unknown"
            
            if result.get("ok"):
                judgment = result.get("judgment", {})
                decision = judgment.get("decision", {})
                verdict = decision.get("verdict", "unknown")
            elif result.get("phase") == "health_gate":
                verdict = "blocked"
            
            explanation = result.get("explanation", {})
            explainer_mode = explanation.get("mode", "unknown")
            
            # Store last run
            global _last_v3_run
            _last_v3_run = result
            
            return {
                "ok": result.get("ok", False),
                "mode": "dry" if dry else "live",
                "verdict": verdict,
                "explainer_mode": explainer_mode,
                "timestamp": datetime.now().isoformat(),
                "message": f"Agent V3 run completed ({verdict}, {explainer_mode} mode)"
            }
        
        except Exception as e:
            # V3: Never 500, return safe default
            return {
                "ok": False,
                "error": "agent_exception",
                "message": str(e)[:200],
                "mode": "dry" if dry else "live",
                "verdict": "error",
                "explainer_mode": "error",
                "timestamp": datetime.now().isoformat()
            }


@router.get("/summary")
async def get_agent_v3_summary(
    v: int = Query(3, description="API version (must be 3 for V3)")
) -> Dict[str, Any]:
    """
    Get last V3 agent summary with LLM bullets and code navigation.
    
    Returns:
        {
          "ok": bool,
          "delta_p95_pct": float,
          "delta_qps_pct": float,
          "error_rate_pct": float,
          "bullets": list[str],  # ≤6 bullets
          "code_nav": list[dict],  # Code locations
          "explainer_mode": "llm" | "rules" | "fallback",
          "generated_at": str
        }
    """
    # Version guard
    if v not in [2, 3]:
        return {
            "ok": False,
            "error": "invalid_version",
            "message": f"v={v} not supported, use v=2 or v=3",
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "bullets": ["Invalid version"],
            "code_nav": [],
            "explainer_mode": "error",
            "generated_at": None
        }
    
    # Handle V3 only
    if v != 3:
        return {
            "ok": False,
            "error": "wrong_endpoint",
            "message": f"Use v=2 endpoint for V2, this is V3",
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "bullets": ["Wrong version"],
            "code_nav": [],
            "explainer_mode": "error",
            "generated_at": None
        }
    
    try:
        # Parse summary from file
        summary = _safe_parse_summary_v3()
        return summary
    
    except Exception as e:
        # V3: Fallback
        return {
            "ok": False,
            "error": "summary_failed",
            "message": str(e)[:200],
            "delta_p95_pct": 0.0,
            "delta_qps_pct": 0.0,
            "error_rate_pct": 0.0,
            "bullets": [f"V3 获取总结失败: {str(e)[:50]}"],
            "code_nav": [],
            "explainer_mode": "error",
            "generated_at": None
        }


@router.get("/history")
async def get_agent_v3_history(
    v: int = Query(3, description="API version (must be 3 for V3)"),
    n: int = Query(10, description="Number of recent runs")
) -> Dict[str, Any]:
    """
    Get last N runs from history_v3.jsonl.
    
    Returns:
        {
          "ok": bool,
          "runs": list[dict],
          "count": int
        }
    """
    # Version guard
    if v not in [2, 3]:
        return {
            "ok": False,
            "error": "invalid_version",
            "message": f"v={v} not supported, use v=2 or v=3",
            "runs": [],
            "count": 0
        }
    
    # Handle V3 only
    if v != 3:
        return {
            "ok": False,
            "error": "wrong_endpoint",
            "message": f"Use v=2 endpoint for V2, this is V3",
            "runs": [],
            "count": 0
        }
    
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        history_path = project_root / "agents" / "labops" / "state" / "history_v3.jsonl"
        
        if not history_path.exists():
            return {
                "ok": True,
                "runs": [],
                "count": 0,
                "message": "No V3 history yet"
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

