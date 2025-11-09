"""
SLA verification utilities for experiment reports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def verify_sla(metrics: Dict[str, Any], sla_policy_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify SLA compliance based on metrics.
    
    Returns:
        {"verdict": "pass"|"warn"|"fail", "checks": [...]}
    """
    if sla_policy_path is None:
        return {"verdict": "pass", "checks": [], "reason": "No SLA policy configured"}
    
    policy_path = Path(sla_policy_path)
    if not policy_path.exists():
        return {"verdict": "pass", "checks": [], "reason": "SLA policy file not found"}
    
    try:
        with policy_path.open("r", encoding="utf-8") as fp:
            policy = yaml.safe_load(fp) or {}
    except Exception:
        return {"verdict": "warn", "checks": [], "reason": "Failed to load SLA policy"}
    
    checks = []
    verdict = "pass"
    
    # Check recall threshold
    recall_threshold = policy.get("recall_at_10_min", 0.0)
    recall = float(metrics.get("recall_at_10", 0.0))
    if recall < recall_threshold:
        checks.append({
            "metric": "recall_at_10",
            "value": recall,
            "threshold": recall_threshold,
            "status": "fail",
        })
        verdict = "fail"
    elif recall < recall_threshold * 1.1:  # Within 10% of threshold
        checks.append({
            "metric": "recall_at_10",
            "value": recall,
            "threshold": recall_threshold,
            "status": "warn",
        })
        if verdict == "pass":
            verdict = "warn"
    
    # Check latency threshold
    p95_max_ms = policy.get("p95_ms_max", float("inf"))
    p95_ms = float(metrics.get("p95_ms", 0.0))
    if p95_ms > p95_max_ms:
        checks.append({
            "metric": "p95_ms",
            "value": p95_ms,
            "threshold": p95_max_ms,
            "status": "fail",
        })
        verdict = "fail"
    elif p95_ms > p95_max_ms * 0.9:  # Within 10% of threshold
        checks.append({
            "metric": "p95_ms",
            "value": p95_ms,
            "threshold": p95_max_ms,
            "status": "warn",
        })
        if verdict == "pass":
            verdict = "warn"
    
    # Check cost threshold
    cost_max = policy.get("cost_max", float("inf"))
    cost = float(metrics.get("cost", 0.0))
    if cost > cost_max:
        checks.append({
            "metric": "cost",
            "value": cost,
            "threshold": cost_max,
            "status": "fail",
        })
        verdict = "fail"
    
    return {
        "verdict": verdict,
        "checks": checks,
    }

