"""
tools.py - Ops Copilot Standard Tools Layer
===========================================
Standard tool functions for ReAct/Planner Agent integration.

This module provides a standardized tool layer that wraps the core runtime functions
for use by ReAct/Planner agents and LLM tool-calling. Each tool has:
- Clear name and description (for LLM/Planner)
- Explicit input/output types (Pydantic/TypedDict)
- Usage guidelines (when to use / not to use)
"""

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass

from services.fiqa_api.ops_copilot.schemas import (
    SystemSnapshot,
    SystemHealthCheckResult,
    SystemStrategyLabResult,
    SaferConfigSuggestion,
)
from services.fiqa_api.ops_copilot.ops_runtime import (
    run_system_health_check,
    run_safety_upgrade_for_system,
    run_system_strategy_lab,
)


# ========================================
# Tool Definition
# ========================================

@dataclass
class OpsTool:
    """
    Tool definition for Ops Copilot tools.
    
    This dataclass represents a single tool that can be used by ReAct/Planner agents.
    """
    name: str
    description: str
    callable: Callable
    allowed_in_bands: Optional[List[str]] = None
    """List of health bands where this tool is allowed (e.g., ['degraded', 'critical']).
    If None, tool is allowed in all bands."""


# ========================================
# Core Tool Functions
# ========================================

def tool_system_health_check(snapshot: SystemSnapshot) -> SystemHealthCheckResult:
    """
    Run a system health check based on the snapshot.
    
    This tool analyzes system metrics (CPU, memory, latency, error rate, disk, QPS)
    and returns a health assessment with band classification, score, and risk flags.
    
    Args:
        snapshot: SystemSnapshot instance with current system metrics
    
    Returns:
        SystemHealthCheckResult with:
        - band: Health band classification (healthy/warning/degraded/critical)
        - score: Numeric health score (0-100)
        - risk_flags: List of risk identifiers (e.g., ['high_cpu', 'high_latency'])
        - hard_block: Whether system should be blocked from deployment
        - soft_warning: Whether system needs caution
        - details: Per-metric assessments
    
    When to use:
        - Always use this as the first step to assess system health
        - Use before running safety_upgrade or strategy_lab
        - Use to validate health status before making decisions
    
    When NOT to use:
        - Don't use if you already have a recent health_result
        - Don't use for historical analysis (use snapshot timestamp instead)
    """
    return run_system_health_check(snapshot)


def tool_safety_upgrade(
    snapshot: SystemSnapshot,
    health_result: SystemHealthCheckResult,
) -> List[SaferConfigSuggestion]:
    """
    Generate safety upgrade suggestions for a degraded or critical system.
    
    This tool proposes 2-3 config change suggestions (e.g., reduce QPS, add replicas)
    that could improve system health. Each suggestion includes estimated health impact.
    
    Args:
        snapshot: SystemSnapshot instance (baseline metrics)
        health_result: SystemHealthCheckResult from health_check (used to determine if suggestions are needed)
    
    Returns:
        List of SaferConfigSuggestion (0-3 items):
        - id: Unique suggestion identifier
        - title: Human-facing title (e.g., "Reduce QPS by 20% and add 1 replica")
        - description: Detailed explanation
        - config_changes: Structured config changes dict
        - estimated_result: Estimated health result after applying suggestion
    
    When to use:
        - Use when health_result.band is 'degraded' or 'critical'
        - Use when you need actionable remediation suggestions
        - Use before strategy_lab to get quick safety improvements
    
    When NOT to use:
        - Don't use if health_result.band is 'healthy' (returns empty list)
        - Don't use if you only need what-if scenarios (use strategy_lab instead)
        - Don't use without first running health_check
    
    Note:
        The health_result parameter is used for early return optimization (if healthy, skip).
        The underlying runtime function will still run its own health check internally.
    """
    # Early return optimization: if system is healthy, skip suggestions
    if health_result.band == "healthy":
        return []
    
    # Call runtime function (it will run health check internally, but we use health_result for early return)
    return run_safety_upgrade_for_system(snapshot)


def tool_strategy_lab(
    snapshot: SystemSnapshot,
    health_result: SystemHealthCheckResult,
) -> SystemStrategyLabResult:
    """
    Run strategy lab analysis: generate alternative scenarios and compare health results.
    
    This tool explores what-if scenarios (e.g., lower QPS, add replicas, reduce error rate)
    and compares their estimated health outcomes against the baseline.
    
    Args:
        snapshot: SystemSnapshot instance (baseline metrics)
        health_result: SystemHealthCheckResult from health_check (baseline health, used for context)
    
    Returns:
        SystemStrategyLabResult with:
        - baseline_snapshot: Original system snapshot
        - baseline_health: Baseline health check result
        - scenarios: List of SystemStrategyScenario (0-3 items), sorted by health score
    
    When to use:
        - Use when you need to explore multiple remediation options
        - Use to compare different strategies before making decisions
        - Use after health_check to understand improvement potential
        - Use for both healthy and degraded systems (always returns scenarios)
    
    When NOT to use:
        - Don't use if you only need quick safety suggestions (use safety_upgrade instead)
        - Don't use without first running health_check
    
    Note:
        The health_result parameter is provided for context/validation.
        The underlying runtime function will still run its own health check internally.
    """
    return run_system_strategy_lab(snapshot)


# ========================================
# Tool Registry
# ========================================

TOOL_REGISTRY: Dict[str, OpsTool] = {
    "health_check": OpsTool(
        name="health_check",
        description=(
            "Run a system health check based on system metrics snapshot. "
            "Returns health band (healthy/warning/degraded/critical), score, risk flags, "
            "and per-metric assessments. Always use this as the first step."
        ),
        callable=tool_system_health_check,
        allowed_in_bands=None,  # Allowed in all bands
    ),
    "safety_upgrade": OpsTool(
        name="safety_upgrade",
        description=(
            "Generate safety upgrade suggestions for degraded or critical systems. "
            "Proposes 2-3 config changes (e.g., reduce QPS, add replicas) with estimated health impact. "
            "Returns empty list if system is healthy. Use after health_check when system is degraded/critical."
        ),
        callable=tool_safety_upgrade,
        allowed_in_bands=["degraded", "critical", "warning"],  # Only for non-healthy systems
    ),
    "strategy_lab": OpsTool(
        name="strategy_lab",
        description=(
            "Run strategy lab analysis: explore what-if scenarios and compare health outcomes. "
            "Generates 0-3 alternative scenarios (e.g., lower QPS, add replicas) and compares "
            "their estimated health results against baseline. Use after health_check to explore options."
        ),
        callable=tool_strategy_lab,
        allowed_in_bands=None,  # Allowed in all bands (useful for healthy systems too)
    ),
}


__all__ = [
    "OpsTool",
    "tool_system_health_check",
    "tool_safety_upgrade",
    "tool_strategy_lab",
    "TOOL_REGISTRY",
]

