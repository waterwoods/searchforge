"""
ops_runtime.py - Ops Copilot Runtime Logic
==========================================
Rule-based system health checks, safety upgrades, and strategy lab for ops/infra scenarios.

This module provides:
1. System health check with rule-based thresholds
2. Safety upgrade suggestions (config changes to improve health)
3. Strategy lab for what-if scenario analysis

No LLM calls, no HTTP - pure Python rule-based logic.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import uuid
import json

from services.fiqa_api.observability.langsmith_tracing import maybe_traceable
from services.fiqa_api.ops_copilot.schemas import (
    HealthBand,
    SystemSnapshot,
    SystemHealthCheckResult,
    SaferConfigSuggestion,
    SystemStrategyScenario,
    SystemStrategyLabResult,
    SystemContextSnapshot,
    HealthAnalystOutput,
    RemediationPlannerOutput,
    ExplainerOutput,
    RagSnippet,
    OpsAction,
    OpsActionPlan,
)

logger = logging.getLogger("ops_copilot")
audit_logger = logging.getLogger("ops_copilot.audit")

# ========================================
# Tool-level Guardrails
# ========================================

# Sensitive tools metadata - defines which tools are "dangerous" and require guardrails
# This structure allows us to define policies for tools that could modify production data
# Currently, all tools are read-only (suggestions only), but this provides a foundation
# for future tools that could actually execute config changes.
SENSITIVE_TOOLS = {
    "apply_config_change": {
        "allowed_in_envs": ["staging"],  # Only allow in staging (not prod)
        "dry_run_only": True,  # Currently all tools are dry-run only
        "description": "Apply configuration changes to system (not yet implemented)",
    },
    "trigger_emergency_rollback": {
        "allowed_in_envs": [],  # Not allowed in any environment (safety)
        "dry_run_only": True,
        "description": "Trigger emergency rollback (not yet implemented)",
    },
    # Add more sensitive tools here as they are implemented
}


class ToolGuardrailException(Exception):
    """
    Exception raised when a tool call is blocked by guardrails.
    
    This exception should be caught and handled gracefully - it indicates
    that the tool was blocked for safety reasons, not due to an error.
    """
    pass


def guard_tool_call(
    tool_name: str,
    request_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Guard a tool call - check if it's allowed based on SENSITIVE_TOOLS rules.
    
    This function implements tool-level guardrails. Currently, all "real modification"
    tools are blocked (they can only suggest, not execute). Future tools that actually
    modify production data must pass through this guard.
    
    Args:
        tool_name: Name of the tool being called
        request_id: Optional request ID for logging
        context: Optional context dict (e.g., {"environment": "prod", "service": "api-gateway"})
    
    Raises:
        ToolGuardrailException: If the tool call is blocked
    
    Example:
        try:
            guard_tool_call("apply_config_change", request_id=req_id, context={"environment": "prod"})
            # Tool is allowed - proceed with execution
        except ToolGuardrailException:
            # Tool was blocked - return suggestion-only response
            return {"suggestion": "...", "blocked": True}
    """
    from services.fiqa_api.observability.security_events import log_security_event
    
    # Check if tool is in sensitive tools list
    if tool_name not in SENSITIVE_TOOLS:
        # Not a sensitive tool - allow by default
        return
    
    tool_config = SENSITIVE_TOOLS[tool_name]
    
    # Extract environment from context (if provided)
    environment = None
    if context:
        environment = context.get("environment")
    
    # Check if tool is dry-run only
    if tool_config.get("dry_run_only", False):
        # All tools are currently dry-run only (suggestions only, no execution)
        # Log the tool call but don't block (we're in suggestion mode)
        log_security_event(
            event_type="tool_call_blocked",
            request_id=request_id,
            context={
                "tool": tool_name,
                "reason": "dry_run_only_mode",
                "environment": environment,
                **(context or {}),
            },
        )
        # Don't raise exception - in dry-run mode, we allow the call but log it
        return
    
    # Check environment restrictions
    allowed_envs = tool_config.get("allowed_in_envs", [])
    if environment and allowed_envs:
        if environment not in allowed_envs:
            # Tool not allowed in this environment
            log_security_event(
                event_type="tool_call_blocked",
                request_id=request_id,
                context={
                    "tool": tool_name,
                    "reason": f"not_allowed_in_env_{environment}",
                    "allowed_envs": allowed_envs,
                    "environment": environment,
                    **(context or {}),
                },
            )
            raise ToolGuardrailException(
                f"Tool '{tool_name}' is not allowed in environment '{environment}'. "
                f"Allowed environments: {allowed_envs}"
            )
    
    # Tool passed all checks - allow it
    return


# ========================================
# Module-level Thresholds
# ========================================

# CPU thresholds
CPU_WARN = 70.0
CPU_CRITICAL = 90.0

# Memory thresholds
MEM_WARN = 75.0
MEM_CRITICAL = 90.0

# Latency thresholds (milliseconds)
LATENCY_WARN = 300.0
LATENCY_CRITICAL = 800.0

# Error rate thresholds (0-1)
ERROR_WARN = 0.01  # 1%
ERROR_CRITICAL = 0.05  # 5%

# Disk thresholds
DISK_WARN = 75.0
DISK_CRITICAL = 90.0

# QPS thresholds (for context, not directly used in health band)
QPS_HIGH = 1000.0


# ========================================
# Helper Functions
# ========================================

def _compute_health_band(snapshot: SystemSnapshot) -> Tuple[HealthBand, List[str]]:
    """
    Compute health band and risk flags based on simple rules.
    
    Args:
        snapshot: SystemSnapshot instance
    
    Returns:
        Tuple of (health_band, risk_flags)
    """
    risk_flags: List[str] = []
    critical_count = 0
    warning_count = 0
    
    # Check CPU
    if snapshot.cpu_pct >= CPU_CRITICAL:
        risk_flags.append("high_cpu")
        critical_count += 1
    elif snapshot.cpu_pct >= CPU_WARN:
        risk_flags.append("high_cpu")
        warning_count += 1
    
    # Check Memory
    if snapshot.mem_pct >= MEM_CRITICAL:
        risk_flags.append("high_memory")
        critical_count += 1
    elif snapshot.mem_pct >= MEM_WARN:
        risk_flags.append("high_memory")
        warning_count += 1
    
    # Check Latency
    if snapshot.p95_latency_ms >= LATENCY_CRITICAL:
        risk_flags.append("high_latency")
        critical_count += 1
    elif snapshot.p95_latency_ms >= LATENCY_WARN:
        risk_flags.append("high_latency")
        warning_count += 1
    
    # Check Error Rate
    if snapshot.error_rate >= ERROR_CRITICAL:
        risk_flags.append("high_error_rate")
        critical_count += 1
    elif snapshot.error_rate >= ERROR_WARN:
        risk_flags.append("high_error_rate")
        warning_count += 1
    
    # Check Disk
    if snapshot.disk_pct >= DISK_CRITICAL:
        risk_flags.append("disk_near_full")
        critical_count += 1
    elif snapshot.disk_pct >= DISK_WARN:
        risk_flags.append("disk_near_full")
        warning_count += 1
    
    # Determine health band
    if critical_count > 0:
        band: HealthBand = "critical"
    elif warning_count >= 2:
        band = "degraded"
    elif warning_count == 1:
        band = "warning"
    else:
        band = "healthy"
    
    return band, risk_flags


def _compute_health_score(snapshot: SystemSnapshot, risk_flags: List[str], band: HealthBand) -> float:
    """
    Compute a numeric health score (0-100) based on metrics and risk flags.
    
    Args:
        snapshot: SystemSnapshot instance
        risk_flags: List of risk flag identifiers
        band: Health band classification
    
    Returns:
        Health score (0-100)
    """
    # Start from 85 (baseline good score)
    score = 85.0
    
    # Subtract points for each risk
    if "high_cpu" in risk_flags:
        if snapshot.cpu_pct >= CPU_CRITICAL:
            score -= 30
        else:
            score -= 10
    
    if "high_memory" in risk_flags:
        if snapshot.mem_pct >= MEM_CRITICAL:
            score -= 25
        else:
            score -= 8
    
    if "high_latency" in risk_flags:
        if snapshot.p95_latency_ms >= LATENCY_CRITICAL:
            score -= 20
        else:
            score -= 10
    
    if "high_error_rate" in risk_flags:
        if snapshot.error_rate >= ERROR_CRITICAL:
            score -= 40
        else:
            score -= 15
    
    if "disk_near_full" in risk_flags:
        if snapshot.disk_pct >= DISK_CRITICAL:
            score -= 25
        else:
            score -= 8
    
    # Clamp to 0-100
    score = max(0.0, min(100.0, score))
    
    return score


def _build_per_metric_details(snapshot: SystemSnapshot) -> Dict[str, Any]:
    """
    Build per-metric assessment details.
    
    Args:
        snapshot: SystemSnapshot instance
    
    Returns:
        Dictionary with per-metric assessments
    """
    details: Dict[str, Any] = {}
    
    # CPU assessment
    if snapshot.cpu_pct >= CPU_CRITICAL:
        cpu_status = "critical"
    elif snapshot.cpu_pct >= CPU_WARN:
        cpu_status = "warn"
    else:
        cpu_status = "ok"
    details["cpu"] = {"value": snapshot.cpu_pct, "status": cpu_status}
    
    # Memory assessment
    if snapshot.mem_pct >= MEM_CRITICAL:
        mem_status = "critical"
    elif snapshot.mem_pct >= MEM_WARN:
        mem_status = "warn"
    else:
        mem_status = "ok"
    details["memory"] = {"value": snapshot.mem_pct, "status": mem_status}
    
    # Latency assessment
    if snapshot.p95_latency_ms >= LATENCY_CRITICAL:
        latency_status = "critical"
    elif snapshot.p95_latency_ms >= LATENCY_WARN:
        latency_status = "warn"
    else:
        latency_status = "ok"
    details["latency"] = {"value": snapshot.p95_latency_ms, "status": latency_status}
    
    # Error rate assessment
    if snapshot.error_rate >= ERROR_CRITICAL:
        error_status = "critical"
    elif snapshot.error_rate >= ERROR_WARN:
        error_status = "warn"
    else:
        error_status = "ok"
    details["error_rate"] = {"value": snapshot.error_rate, "status": error_status}
    
    # Disk assessment
    if snapshot.disk_pct >= DISK_CRITICAL:
        disk_status = "critical"
    elif snapshot.disk_pct >= DISK_WARN:
        disk_status = "warn"
    else:
        disk_status = "ok"
    details["disk"] = {"value": snapshot.disk_pct, "status": disk_status}
    
    # QPS (informational)
    details["qps"] = {"value": snapshot.qps, "status": "info"}
    
    return details


# ========================================
# Main Health Check Function
# ========================================

def run_system_health_check(snapshot: SystemSnapshot) -> SystemHealthCheckResult:
    """
    Run a system health check based on the snapshot.
    
    Args:
        snapshot: SystemSnapshot instance
    
    Returns:
        SystemHealthCheckResult with band, score, risk flags, and details
    """
    # Compute health band and risk flags
    band, risk_flags = _compute_health_band(snapshot)
    
    # Compute health score
    score = _compute_health_score(snapshot, risk_flags, band)
    
    # Determine hard_block and soft_warning
    hard_block = (
        band == "critical" or
        "high_error_rate" in risk_flags or
        "disk_near_full" in risk_flags
    )
    
    soft_warning = (
        band == "degraded" or
        (band == "warning" and len(risk_flags) > 0)
    )
    
    # Build per-metric details
    details = _build_per_metric_details(snapshot)
    
    return SystemHealthCheckResult(
        band=band,
        score=score,
        risk_flags=risk_flags,
        hard_block=hard_block,
        soft_warning=soft_warning,
        details=details,
    )


# ========================================
# Safety Upgrade Function
# ========================================

def run_safety_upgrade_for_system(snapshot: SystemSnapshot) -> List[SaferConfigSuggestion]:
    """
    Generate safety upgrade suggestions for a system snapshot.
    
    If the system is healthy, returns empty list.
    Otherwise, proposes 2-3 simple config suggestions based on rule-based heuristics.
    
    Args:
        snapshot: SystemSnapshot instance
    
    Returns:
        List of SaferConfigSuggestion instances
    """
    # Run baseline health check
    baseline_health = run_system_health_check(snapshot)
    
    # If healthy, return empty list
    if baseline_health.band == "healthy":
        return []
    
    suggestions: List[SaferConfigSuggestion] = []
    
    # Suggestion 1: Reduce QPS by 20% and add 1 replica
    # This helps with CPU, memory, and latency
    if "high_cpu" in baseline_health.risk_flags or "high_latency" in baseline_health.risk_flags:
        try:
            new_qps = snapshot.qps * 0.8
            # Estimate: reducing QPS by 20% should reduce CPU by ~15-20% and latency by ~10-15%
            estimated_cpu = max(0, snapshot.cpu_pct * 0.85)
            estimated_mem = max(0, snapshot.mem_pct * 0.85)
            estimated_latency = max(50, snapshot.p95_latency_ms * 0.90)
            
            snapshot_after = SystemSnapshot(
                service_name=snapshot.service_name,
                environment=snapshot.environment,
                cpu_pct=estimated_cpu,
                mem_pct=estimated_mem,
                p95_latency_ms=estimated_latency,
                error_rate=snapshot.error_rate * 0.95,  # Slight improvement
                qps=new_qps,
                disk_pct=snapshot.disk_pct,
                timestamp=snapshot.timestamp,
                region=snapshot.region,
                tags=snapshot.tags,
            )
            
            estimated_result = run_system_health_check(snapshot_after)
            
            suggestions.append(SaferConfigSuggestion(
                id="reduce_qps_20_add_replica",
                title="Reduce QPS by 20% and add 1 replica",
                description=(
                    f"Reduce QPS from {snapshot.qps:.0f} to {new_qps:.0f} and add 1 replica. "
                    f"This should reduce CPU load and improve latency."
                ),
                config_changes={
                    "qps_limit": new_qps,
                    "replicas": "+1",
                    "estimated_cpu_reduction_pct": 15,
                },
                estimated_result=estimated_result,
            ))
        except Exception as e:
            logger.warning(f"[SAFETY_UPGRADE] Failed to generate reduce_qps_20_add_replica suggestion: {e}")
    
    # Suggestion 2: Switch to conservative timeout and reduce max QPS
    # This helps with latency and error rate
    if "high_latency" in baseline_health.risk_flags or "high_error_rate" in baseline_health.risk_flags:
        try:
            new_qps = snapshot.qps * 0.75  # More aggressive reduction
            new_timeout_ms = snapshot.p95_latency_ms * 1.5  # Increase timeout budget
            # Estimate: more aggressive QPS reduction should help more
            estimated_cpu = max(0, snapshot.cpu_pct * 0.80)
            estimated_latency = max(50, snapshot.p95_latency_ms * 0.85)
            estimated_error_rate = max(0, snapshot.error_rate * 0.70)  # Better error handling
            
            snapshot_after = SystemSnapshot(
                service_name=snapshot.service_name,
                environment=snapshot.environment,
                cpu_pct=estimated_cpu,
                mem_pct=snapshot.mem_pct * 0.90,
                p95_latency_ms=estimated_latency,
                error_rate=estimated_error_rate,
                qps=new_qps,
                disk_pct=snapshot.disk_pct,
                timestamp=snapshot.timestamp,
                region=snapshot.region,
                tags=snapshot.tags,
            )
            
            estimated_result = run_system_health_check(snapshot_after)
            
            suggestions.append(SaferConfigSuggestion(
                id="switch_to_conservative_timeout",
                title="Switch to conservative timeout and reduce max QPS by 25%",
                description=(
                    f"Reduce QPS from {snapshot.qps:.0f} to {new_qps:.0f} and increase timeout to {new_timeout_ms:.0f}ms. "
                    f"This should reduce latency and error rate."
                ),
                config_changes={
                    "qps_limit": new_qps,
                    "timeout_ms": new_timeout_ms,
                    "estimated_latency_reduction_pct": 15,
                    "estimated_error_reduction_pct": 30,
                },
                estimated_result=estimated_result,
            ))
        except Exception as e:
            logger.warning(f"[SAFETY_UPGRADE] Failed to generate switch_to_conservative_timeout suggestion: {e}")
    
    # Suggestion 3: Add more replicas and scale horizontally
    # This helps with CPU, memory, and overall load
    if "high_cpu" in baseline_health.risk_flags or "high_memory" in baseline_health.risk_flags:
        try:
            # Estimate: adding 2 replicas should reduce CPU/mem per instance by ~40-50%
            estimated_cpu = max(0, snapshot.cpu_pct * 0.60)
            estimated_mem = max(0, snapshot.mem_pct * 0.60)
            estimated_latency = max(50, snapshot.p95_latency_ms * 0.85)
            
            snapshot_after = SystemSnapshot(
                service_name=snapshot.service_name,
                environment=snapshot.environment,
                cpu_pct=estimated_cpu,
                mem_pct=estimated_mem,
                p95_latency_ms=estimated_latency,
                error_rate=snapshot.error_rate * 0.90,
                qps=snapshot.qps,  # Same QPS, but distributed across more replicas
                disk_pct=snapshot.disk_pct,
                timestamp=snapshot.timestamp,
                region=snapshot.region,
                tags=snapshot.tags,
            )
            
            estimated_result = run_system_health_check(snapshot_after)
            
            suggestions.append(SaferConfigSuggestion(
                id="add_replicas_scale_horizontal",
                title="Add 2 replicas and scale horizontally",
                description=(
                    f"Add 2 replicas to distribute load. "
                    f"This should reduce CPU and memory usage per instance by ~40%."
                ),
                config_changes={
                    "replicas": "+2",
                    "estimated_cpu_reduction_pct": 40,
                    "estimated_mem_reduction_pct": 40,
                },
                estimated_result=estimated_result,
            ))
        except Exception as e:
            logger.warning(f"[SAFETY_UPGRADE] Failed to generate add_replicas_scale_horizontal suggestion: {e}")
    
    # Limit to 3 suggestions
    return suggestions[:3]


# ========================================
# Strategy Lab Function
# ========================================

def run_system_strategy_lab(snapshot: SystemSnapshot) -> SystemStrategyLabResult:
    """
    Run strategy lab analysis: generate alternative scenarios and compare health results.
    
    Args:
        snapshot: Baseline SystemSnapshot instance
    
    Returns:
        SystemStrategyLabResult with baseline and scenario comparisons
    """
    # Run baseline health check
    baseline_health = run_system_health_check(snapshot)
    
    scenarios: List[SystemStrategyScenario] = []
    
    # Scenario 1: Lower QPS by 20%
    try:
        new_qps = snapshot.qps * 0.8
        estimated_cpu = max(0, snapshot.cpu_pct * 0.85)
        estimated_mem = max(0, snapshot.mem_pct * 0.85)
        estimated_latency = max(50, snapshot.p95_latency_ms * 0.90)
        
        snapshot_after = SystemSnapshot(
            service_name=snapshot.service_name,
            environment=snapshot.environment,
            cpu_pct=estimated_cpu,
            mem_pct=estimated_mem,
            p95_latency_ms=estimated_latency,
            error_rate=snapshot.error_rate * 0.95,
            qps=new_qps,
            disk_pct=snapshot.disk_pct,
            timestamp=snapshot.timestamp,
            region=snapshot.region,
            tags=snapshot.tags,
        )
        
        health_result = run_system_health_check(snapshot_after)
        
        scenarios.append(SystemStrategyScenario(
            id="scenario_lower_qps_20",
            title="Lower QPS by 20%",
            description=f"Reduce QPS from {snapshot.qps:.0f} to {new_qps:.0f}",
            snapshot_after_change=snapshot_after,
            health_result=health_result,
        ))
    except Exception as e:
        logger.warning(f"[STRATEGY_LAB] Failed to generate scenario_lower_qps_20: {e}")
    
    # Scenario 2: Add replica (distribute load)
    try:
        # Estimate: adding 1 replica should reduce CPU/mem per instance by ~30-40%
        estimated_cpu = max(0, snapshot.cpu_pct * 0.70)
        estimated_mem = max(0, snapshot.mem_pct * 0.70)
        estimated_latency = max(50, snapshot.p95_latency_ms * 0.85)
        
        snapshot_after = SystemSnapshot(
            service_name=snapshot.service_name,
            environment=snapshot.environment,
            cpu_pct=estimated_cpu,
            mem_pct=estimated_mem,
            p95_latency_ms=estimated_latency,
            error_rate=snapshot.error_rate * 0.90,
            qps=snapshot.qps,  # Same QPS, distributed
            disk_pct=snapshot.disk_pct,
            timestamp=snapshot.timestamp,
            region=snapshot.region,
            tags=snapshot.tags,
        )
        
        health_result = run_system_health_check(snapshot_after)
        
        scenarios.append(SystemStrategyScenario(
            id="scenario_add_replica",
            title="Add 1 replica",
            description="Add 1 replica to distribute load across more instances",
            snapshot_after_change=snapshot_after,
            health_result=health_result,
        ))
    except Exception as e:
        logger.warning(f"[STRATEGY_LAB] Failed to generate scenario_add_replica: {e}")
    
    # Scenario 3: Reduce error rate (assuming fix)
    try:
        # Assume error rate drops by 50% and slight QPS improvement
        estimated_error_rate = snapshot.error_rate * 0.5
        estimated_cpu = max(0, snapshot.cpu_pct * 0.95)  # Slight improvement
        estimated_latency = max(50, snapshot.p95_latency_ms * 0.95)  # Slight improvement
        
        snapshot_after = SystemSnapshot(
            service_name=snapshot.service_name,
            environment=snapshot.environment,
            cpu_pct=estimated_cpu,
            mem_pct=snapshot.mem_pct,
            p95_latency_ms=estimated_latency,
            error_rate=estimated_error_rate,
            qps=snapshot.qps * 0.95,  # Slight QPS drop due to better error handling
            disk_pct=snapshot.disk_pct,
            timestamp=snapshot.timestamp,
            region=snapshot.region,
            tags=snapshot.tags,
        )
        
        health_result = run_system_health_check(snapshot_after)
        
        scenarios.append(SystemStrategyScenario(
            id="scenario_reduce_error_rate_assuming_fix",
            title="Reduce error rate by 50% (assuming fix)",
            description=f"Reduce error rate from {snapshot.error_rate:.3f} to {estimated_error_rate:.3f}",
            snapshot_after_change=snapshot_after,
            health_result=health_result,
        ))
    except Exception as e:
        logger.warning(f"[STRATEGY_LAB] Failed to generate scenario_reduce_error_rate_assuming_fix: {e}")
    
    # Sort scenarios by health score (higher score = better)
    scenarios.sort(key=lambda s: s.health_result.score, reverse=True)
    
    # Limit to 3 scenarios
    scenarios = scenarios[:3]
    
    return SystemStrategyLabResult(
        baseline_snapshot=snapshot,
        baseline_health=baseline_health,
        scenarios=scenarios,
    )


# ========================================
# RAG Context Fetching
# ========================================

def fetch_rag_context_for_system(
    snapshot: SystemSnapshot,
    health_result: Optional[SystemHealthCheckResult] = None,
    top_n: int = 3,
) -> List[RagSnippet]:
    """
    Fetch RAG context from ops knowledge base for a given system snapshot.
    
    This function:
    1. Constructs a query from service_name and health signals (risk_flags)
    2. Calls retrieve_ops_knowledge() to perform vector search
    3. Converts results to RagSnippet objects
    4. Returns top N snippets (default: 3)
    
    Args:
        snapshot: SystemSnapshot instance (provides service_name)
        health_result: Optional SystemHealthCheckResult (provides risk_flags for symptom)
        top_n: Number of snippets to return (default: 3)
    
    Returns:
        List of RagSnippet objects (empty list if retrieval fails or no index available)
    
    Graceful degradation:
        - If vector search fails, returns empty list (does not raise)
        - If no index available, returns empty list
        - If no results found, returns empty list
    
    Example:
        >>> snapshot = SystemSnapshot(...)
        >>> health_result = run_system_health_check(snapshot)
        >>> rag_snippets = fetch_rag_context_for_system(snapshot, health_result, top_n=3)
        >>> print(f"Retrieved {len(rag_snippets)} RAG snippets")
    """
    try:
        from services.fiqa_api.ops_copilot.ops_rag_retriever import retrieve_ops_knowledge
        
        # Extract symptom from risk_flags if available
        symptom = None
        if health_result and health_result.risk_flags:
            # Use the first risk flag as symptom (e.g., "high_cpu", "high_error_rate")
            # This maps to how runbooks are indexed in the knowledge base
            symptom = health_result.risk_flags[0]
        
        # Construct query: service_name + symptom (if available)
        # The retrieve_ops_knowledge function will combine them into a query string
        service_name = snapshot.service_name
        
        # Call vector search
        # Note: retrieve_ops_knowledge already handles graceful degradation internally
        raw_results = retrieve_ops_knowledge(
            service_name=service_name,
            symptom=symptom,
            top_k=top_n,
        )
        
        # Convert raw results to RagSnippet objects
        rag_snippets = []
        for result in raw_results:
            try:
                snippet = RagSnippet(
                    text=result.get("text", ""),
                    source_file=result.get("source_file", "unknown"),
                    service_hint=result.get("service_hint"),
                    symptom_hint=result.get("symptom_hint"),
                    score=result.get("score", 0.0),
                )
                rag_snippets.append(snippet)
            except Exception as e:
                # Skip invalid results (shouldn't happen, but be defensive)
                logger.warning(f"[RAG] Failed to convert result to RagSnippet: {e}")
                continue
        
        logger.info(
            f"[RAG] Retrieved {len(rag_snippets)} snippets for service={service_name}, "
            f"symptom={symptom}, top_n={top_n}"
        )
        
        return rag_snippets
        
    except Exception as e:
        # Graceful degradation: log warning but don't raise
        logger.warning(f"[RAG] Failed to fetch RAG context: {e}")
        return []


# ========================================
# Multi-Agent Functions
# ========================================

def run_health_analyst_agent(
    snapshot: SystemSnapshot,
    request_id: Optional[str] = None,
) -> HealthAnalystOutput:
    """
    Health Analyst Agent: Analyze system health and gather diagnostic context.
    
    This agent is responsible for:
    - Running the core health check (band, score, risk flags)
    - Loading operational context from semantic tools (logs, runbooks, incidents)
    - Generating human-friendly analysis notes about the health status
    
    Args:
        snapshot: SystemSnapshot instance
        request_id: Optional request ID for tracing
    
    Returns:
        HealthAnalystOutput with health result, context, and analysis notes
    """
    # Run core health check
    health_result = run_system_health_check(snapshot)
    
    # Load semantic context based on health status
    context = None
    try:
        from services.fiqa_api.ops_copilot.semantic_tools import (
            query_logs,
            get_runbook,
            summarize_recent_incidents,
        )
        
        # Always query logs and incidents
        log_summary = query_logs(snapshot.service_name, window_minutes=15, max_samples=5)
        incident_summary = summarize_recent_incidents(snapshot.service_name, window_days=30, max_items=5)
        
        # Query runbook if degraded/critical
        runbook = None
        if health_result.band in ("degraded", "critical") and health_result.risk_flags:
            # Map risk flags to symptoms
            symptom = health_result.risk_flags[0]  # Use first risk flag as symptom
            runbook = get_runbook(snapshot.service_name, symptom)
        
        # Build context snapshot
        context = SystemContextSnapshot(
            log_summary=log_summary,
            runbook=runbook,
            incident_summary=incident_summary,
        )
    except Exception as ctx_error:
        logger.warning(f"[HEALTH_ANALYST] Failed to load semantic context: {ctx_error}")
        context = None
    
    # Generate analysis notes based on health status and risk flags
    analysis_notes = []
    
    if health_result.band in ("degraded", "critical"):
        # Note about overall health
        analysis_notes.append(
            f"System is {health_result.band} with score {health_result.score:.1f} - immediate attention required"
        )
        
        # Note about co-occurring metrics (possible retry storm or cascading failure)
        if "high_cpu" in health_result.risk_flags and "high_error_rate" in health_result.risk_flags:
            analysis_notes.append(
                "CPU and error rate both elevated - may indicate retry storm or cascading failures"
            )
        elif "high_latency" in health_result.risk_flags and "high_error_rate" in health_result.risk_flags:
            analysis_notes.append(
                "Latency and error rate both elevated - possible downstream service degradation"
            )
        
        # Note about disk pressure
        if "disk_near_full" in health_result.risk_flags:
            analysis_notes.append(
                f"Disk usage at {snapshot.disk_pct:.0f}% - risk of service failure if disk fills completely"
            )
        
        # Note about context availability
        if context:
            if context.log_summary and context.log_summary.error_count > 10:
                analysis_notes.append(
                    f"Logs show {context.log_summary.error_count} errors in last {context.log_summary.window_minutes} minutes"
                )
            if context.incident_summary and context.incident_summary.critical_count > 0:
                analysis_notes.append(
                    f"Historical context: {context.incident_summary.critical_count} critical incidents in last {context.incident_summary.window_days} days"
                )
    
    elif health_result.band == "warning":
        analysis_notes.append(
            f"System has minor warnings (score {health_result.score:.1f}) - monitor closely"
        )
    
    else:  # healthy
        analysis_notes.append(
            f"System is healthy with score {health_result.score:.1f} - all metrics within normal range"
        )
    
    return HealthAnalystOutput(
        health_result=health_result,
        context=context,
        analysis_notes=analysis_notes,
    )


def run_remediation_planner_agent(
    snapshot: SystemSnapshot,
    health_output: HealthAnalystOutput,
    request_id: Optional[str] = None,
) -> RemediationPlannerOutput:
    """
    Remediation Planner Agent: Generate remediation strategies and what-if scenarios.
    
    This agent is responsible for:
    - Generating safety upgrade suggestions if system is degraded/critical
    - Running strategy lab analysis to explore alternative scenarios
    - Providing planning notes about recommended actions
    
    Args:
        snapshot: SystemSnapshot instance (needed for safety upgrades and strategy lab)
        health_output: HealthAnalystOutput from health analyst agent
        request_id: Optional request ID for tracing
    
    Returns:
        RemediationPlannerOutput with safety suggestions, strategy lab results, and planning notes
    """
    health_result = health_output.health_result
    
    # Generate safety suggestions if degraded/critical
    safety_suggestions = []
    if health_result.band in ("degraded", "critical"):
        try:
            safety_suggestions = run_safety_upgrade_for_system(snapshot)
        except Exception as e:
            logger.warning(f"[REMEDIATION_PLANNER] Failed to generate safety suggestions: {e}")
    
    # Always run strategy lab
    strategy_lab = None
    try:
        strategy_lab = run_system_strategy_lab(snapshot)
    except Exception as e:
        logger.warning(f"[REMEDIATION_PLANNER] Failed to run strategy lab: {e}")
    
    # Generate planning notes
    plan_notes = []
    
    if safety_suggestions:
        # Find best safety suggestion (first one with highest estimated score)
        best_suggestion = max(
            safety_suggestions,
            key=lambda s: s.estimated_result.score if s.estimated_result else 0.0,
            default=None
        )
        if best_suggestion and best_suggestion.estimated_result:
            plan_notes.append(
                f"Safety suggestion '{best_suggestion.title}' improves score from "
                f"{health_result.score:.1f} → {best_suggestion.estimated_result.score:.1f}"
            )
    
    if strategy_lab and strategy_lab.scenarios:
        baseline_score = strategy_lab.baseline_health.score
        best_scenario = strategy_lab.scenarios[0]  # Already sorted by score
        score_delta = best_scenario.health_result.score - baseline_score
        
        if score_delta > 0:
            plan_notes.append(
                f"Scenario '{best_scenario.title}' improves score from "
                f"{baseline_score:.1f} → {best_scenario.health_result.score:.1f}, recommend executing it first"
            )
        else:
            plan_notes.append(
                f"All scenarios evaluated - best option is '{best_scenario.title}' with score {best_scenario.health_result.score:.1f}"
            )
    
    if health_result.band in ("degraded", "critical"):
        if "high_cpu" in health_result.risk_flags or "high_memory" in health_result.risk_flags:
            plan_notes.append("Priority action: Add replicas to distribute load (horizontal scaling preferred over QPS reduction)")
        elif "high_error_rate" in health_result.risk_flags:
            plan_notes.append("Priority action: Investigate error root cause before scaling (may be logic bug, not capacity)")
    
    return RemediationPlannerOutput(
        safety_suggestions=safety_suggestions,
        strategy_lab=strategy_lab,
        plan_notes=plan_notes,
    )


# ========================================
# Action Planning Function (Plan / Act Separation)
# ========================================

def build_ops_action_plan(
    service_name: str,
    health_result: SystemHealthCheckResult,
    safety_suggestions: Optional[List[SaferConfigSuggestion]] = None,
    strategy_lab: Optional[SystemStrategyLabResult] = None,
) -> OpsActionPlan:
    """
    Build a structured OpsActionPlan from safety suggestions and strategy lab scenarios.
    
    PLAN ONLY - never ACT.
    This function only generates structured action plans. It never executes any real operations,
    never calls any external APIs (Kubernetes, Cloud Run, database config changes, etc.).
    
    Maps the best 1-3 suggestions/scenarios into OpsAction objects.
    
    Args:
        service_name: Service name (e.g., 'api-gateway')
        health_result: SystemHealthCheckResult with band, score, hard_block
        safety_suggestions: Optional list of safety upgrade suggestions (0-3 items)
        strategy_lab: Optional SystemStrategyLabResult with scenarios
    
    Returns:
        OpsActionPlan with structured actions (0-5 actions)
    """
    # Initialize plan
    plan = OpsActionPlan(
        service_name=service_name,
        band=health_result.band,
        hard_block=health_result.hard_block,
        generated_at=datetime.utcnow(),
        actions=[],
        notes=[],
    )
    
    actions: List[OpsAction] = []
    baseline_score = health_result.score
    
    # Convert safety_suggestions to OpsAction (0-2 actions)
    if safety_suggestions:
        for suggestion in safety_suggestions[:2]:  # Limit to top 2
            try:
                # Determine action_type from config_changes
                action_type = "reduce_qps"  # Default
                config_changes = suggestion.config_changes or {}
                
                if "replicas" in str(config_changes):
                    if "qps_limit" in str(config_changes) or "qps" in str(config_changes).lower():
                        action_type = "reduce_qps"  # Both QPS reduction and replica addition
                    else:
                        action_type = "add_replica"
                elif "qps_limit" in str(config_changes) or "qps" in str(config_changes).lower():
                    action_type = "reduce_qps"
                elif "timeout" in str(config_changes).lower():
                    action_type = "adjust_timeout"
                elif "retry" in str(config_changes).lower():
                    action_type = "tune_retry_policy"
                elif "error" in str(config_changes).lower():
                    action_type = "reduce_error_rate"
                
                # Determine severity
                if health_result.hard_block or health_result.band == "critical":
                    severity = "critical"
                elif health_result.band == "degraded":
                    severity = "warning"
                else:
                    severity = "info"
                
                # Extract estimated scores
                estimated_before = baseline_score
                estimated_after = None
                if suggestion.estimated_result:
                    estimated_after = suggestion.estimated_result.score
                
                # Calculate estimated_delta
                estimated_delta = None
                if estimated_after is not None and estimated_before is not None:
                    estimated_delta = estimated_after - estimated_before
                
                # Build reason from risk_flags and brief explanation
                risk_flags_str = " + ".join(health_result.risk_flags[:3]) if health_result.risk_flags else "no_risk_flags"
                if action_type == "reduce_qps":
                    reason = f"{risk_flags_str} — reduce QPS to relieve upstream pressure"
                elif action_type == "add_replica":
                    reason = f"{risk_flags_str} — add replica to distribute load"
                elif action_type == "adjust_timeout":
                    reason = f"{risk_flags_str} — adjust timeout to handle latency spikes"
                elif action_type == "reduce_error_rate":
                    reason = f"{risk_flags_str} — reduce error rate through improved error handling"
                elif action_type == "tune_retry_policy":
                    reason = f"{risk_flags_str} — tune retry policy to avoid retry storms"
                else:
                    reason = f"{risk_flags_str} — {action_type} to improve system health"
                
                # Build summary
                summary = suggestion.title or f"{action_type} for {service_name}"
                
                action = OpsAction(
                    action_id=uuid.uuid4().hex,
                    action_type=action_type,
                    target_service=service_name,
                    severity=severity,
                    summary=summary,
                    details=suggestion.description,
                    estimated_before_score=estimated_before,
                    estimated_after_score=estimated_after,
                    estimated_delta=estimated_delta,
                    reason=reason,
                    require_human_approval=True,  # Always require approval for safety
                    source="safety_suggestions",
                )
                actions.append(action)
            except Exception as e:
                logger.warning(f"[ACTION_PLANNER] Failed to convert safety suggestion to OpsAction: {e}")
                continue
        
        # Add note about safety suggestions
        if actions:
            safety_actions = [a for a in actions if a.source == "safety_suggestions"]
            if safety_actions:
                best_safety = max(safety_actions, key=lambda a: a.estimated_after_score or 0.0, default=None)
                if best_safety and best_safety.estimated_after_score is not None:
                    plan.notes.append(
                        f"Selected {len(safety_actions)} action(s) from safety_suggestions "
                        f"improving score from {best_safety.estimated_before_score:.1f} to {best_safety.estimated_after_score:.1f}."
                    )
    
    # Convert strategy_lab scenarios to OpsAction (0-2 actions)
    if strategy_lab and strategy_lab.scenarios:
        baseline_health_score = strategy_lab.baseline_health.score
        
        # Only select scenarios that improve score
        improved_scenarios = [
            s for s in strategy_lab.scenarios
            if s.health_result.score > baseline_health_score
        ]
        
        # Limit to top 2 improved scenarios
        for scenario in improved_scenarios[:2]:
            try:
                # Determine action_type from scenario title/description
                action_type = "reduce_qps"  # Default
                title_lower = scenario.title.lower()
                
                if "replica" in title_lower or "add" in title_lower:
                    action_type = "add_replica"
                elif "qps" in title_lower or "lower" in title_lower:
                    action_type = "reduce_qps"
                elif "error" in title_lower:
                    action_type = "reduce_error_rate"
                elif "timeout" in title_lower:
                    action_type = "adjust_timeout"
                elif "retry" in title_lower:
                    action_type = "tune_retry_policy"
                
                # Determine severity
                if health_result.hard_block or health_result.band == "critical":
                    severity = "critical"
                elif health_result.band == "degraded":
                    severity = "warning"
                else:
                    severity = "info"
                
                # Extract scores
                estimated_before = baseline_health_score
                estimated_after = scenario.health_result.score
                
                # Calculate estimated_delta
                estimated_delta = estimated_after - estimated_before if estimated_after is not None and estimated_before is not None else None
                
                # Build reason from risk_flags and brief explanation
                risk_flags_str = " + ".join(health_result.risk_flags[:3]) if health_result.risk_flags else "no_risk_flags"
                if action_type == "reduce_qps":
                    reason = f"{risk_flags_str} — reduce QPS to relieve upstream pressure"
                elif action_type == "add_replica":
                    reason = f"{risk_flags_str} — add replica to distribute load"
                elif action_type == "adjust_timeout":
                    reason = f"{risk_flags_str} — adjust timeout to handle latency spikes"
                elif action_type == "reduce_error_rate":
                    reason = f"{risk_flags_str} — reduce error rate through improved error handling"
                elif action_type == "tune_retry_policy":
                    reason = f"{risk_flags_str} — tune retry policy to avoid retry storms"
                else:
                    reason = f"{risk_flags_str} — {action_type} to improve system health"
                
                # Build summary
                summary = scenario.title or f"{action_type} for {service_name}"
                
                action = OpsAction(
                    action_id=uuid.uuid4().hex,
                    action_type=action_type,
                    target_service=service_name,
                    severity=severity,
                    summary=summary,
                    details=scenario.description,
                    estimated_before_score=estimated_before,
                    estimated_after_score=estimated_after,
                    estimated_delta=estimated_delta,
                    reason=reason,
                    require_human_approval=True,  # Always require approval for safety
                    source="strategy_lab",
                )
                actions.append(action)
            except Exception as e:
                logger.warning(f"[ACTION_PLANNER] Failed to convert strategy scenario to OpsAction: {e}")
                continue
        
        # Add note about strategy lab
        strategy_actions = [a for a in actions if a.source == "strategy_lab"]
        if strategy_actions:
            best_strategy = max(strategy_actions, key=lambda a: a.estimated_after_score or 0.0, default=None)
            if best_strategy and best_strategy.estimated_after_score is not None:
                plan.notes.append(
                    f"Selected {len(strategy_actions)} action(s) from strategy_lab scenarios "
                    f"improving score from {best_strategy.estimated_before_score:.1f} to {best_strategy.estimated_after_score:.1f}."
                )
    
    # Limit total actions to 5
    plan.actions = actions[:5]
    
    # If no actions, add a note
    if not plan.actions:
        plan.notes.append("No actions recommended - system is healthy or no improvements found.")
    
    return plan


def validate_ops_action_plan(
    plan: OpsActionPlan,
    health_result: SystemHealthCheckResult,
) -> OpsActionPlan:
    """
    Validate OpsActionPlan with high-risk guardrails.
    
    This function applies safety guardrails to action plans:
    - Blocks dangerous action types in critical/high-risk scenarios
    - Sets require_human_approval=True for all actions in critical scenarios
    - Removes unknown action types and logs them
    - Updates statistics (num_actions_blocked, num_actions_require_human)
    
    Args:
        plan: OpsActionPlan to validate
        health_result: SystemHealthCheckResult for context
    
    Returns:
        Validated OpsActionPlan (may have actions removed or modified)
    """
    # Define dangerous action types (for future extension)
    # Currently we don't have these action types, but we reserve the check for future safety
    DANGEROUS_ACTION_TYPES = [
        "scale_up_traffic",
        "shift_traffic_to_single_region",
        "disable_circuit_breaker",
        "remove_rate_limiting",
    ]
    
    # Define known valid action types
    VALID_ACTION_TYPES = [
        "reduce_qps",
        "add_replica",
        "reduce_error_rate",
        "adjust_timeout",
        "tune_retry_policy",
        "other",
    ]
    
    # Check if we're in a high-risk scenario
    is_critical = health_result.band == "critical"
    has_high_error_rate = "high_error_rate" in health_result.risk_flags
    has_disk_near_full = "disk_near_full" in health_result.risk_flags
    is_high_risk = is_critical or has_high_error_rate or has_disk_near_full
    
    # Initialize counters
    num_actions_blocked = 0
    num_actions_require_human = 0
    
    # Validate each action
    validated_actions = []
    blocked_action_types = []
    unknown_action_types = []
    
    for action in plan.actions:
        # Check for unknown action types
        if action.action_type not in VALID_ACTION_TYPES:
            unknown_action_types.append(action.action_type)
            num_actions_blocked += 1
            continue
        
        # Check for dangerous action types in high-risk scenarios
        if is_high_risk and action.action_type in DANGEROUS_ACTION_TYPES:
            blocked_action_types.append(action.action_type)
            num_actions_blocked += 1
            continue
        
        # In high-risk scenarios, ensure require_human_approval=True
        if is_high_risk:
            action.require_human_approval = True
            num_actions_require_human += 1
        elif action.require_human_approval:
            num_actions_require_human += 1
        
        validated_actions.append(action)
    
    # Update plan with validated actions
    plan.actions = validated_actions
    plan.num_actions_blocked = num_actions_blocked
    plan.num_actions_require_human = num_actions_require_human
    
    # Add notes about blocked/unknown actions
    if blocked_action_types:
        plan.notes.append(
            f"Guardrail: Blocked {len(blocked_action_types)} dangerous action(s) in high-risk scenario: {', '.join(blocked_action_types)}"
        )
    
    if unknown_action_types:
        plan.notes.append(
            f"Guardrail: Removed {len(unknown_action_types)} action(s) with unknown action_type: {', '.join(unknown_action_types)}"
        )
    
    if is_high_risk and num_actions_require_human > 0:
        plan.notes.append(
            f"Guardrail: All {num_actions_require_human} action(s) require human approval due to critical/high-risk scenario"
        )
    
    logger.info(
        f"[ACTION_PLANNER_VALIDATION] Validated plan: "
        f"actions={len(validated_actions)}, blocked={num_actions_blocked}, "
        f"require_human={num_actions_require_human}, is_high_risk={is_high_risk}"
    )
    
    return plan


def log_ops_action_plan(
    plan: OpsActionPlan,
    health_result: SystemHealthCheckResult,
    request_id: Optional[str] = None,
) -> None:
    """
    Audit log for OpsActionPlan.
    
    只负责记录日志,不做任何业务修改。
    只在 degraded / critical 场景,且有 action 时记录。
    """
    try:
        # 只记录降级/严重场景
        if plan.band not in ("degraded", "critical"):
            return
        if not plan.actions:
            return
        
        # 基本信息
        log_data = {
            "event": "ops_action_plan_audit",
            "request_id": request_id,
            "service_name": plan.service_name,
            "band": plan.band,
            "score": health_result.score,
            "hard_block": plan.hard_block,
            "num_actions": len(plan.actions),
            "num_actions_blocked": plan.num_actions_blocked,
            "num_actions_require_human": plan.num_actions_require_human,
            "risk_flags": health_result.risk_flags,
            "generated_at": plan.generated_at.isoformat() if plan.generated_at else None,
            "notes": plan.notes,
            "actions": [],
        }
        
        # 每个 action 的摘要（不要太长,方便日志查看）
        for action in plan.actions:
            log_data["actions"].append(
                {
                    "action_id": action.action_id,
                    "action_type": action.action_type,
                    "severity": action.severity,
                    "target_service": action.target_service,
                    "require_human_approval": action.require_human_approval,
                    "estimated_before_score": action.estimated_before_score,
                    "estimated_after_score": action.estimated_after_score,
                    "estimated_delta": action.estimated_delta,
                    "source": action.source,
                    "summary": action.summary,
                    "reason": action.reason,
                }
            )
        
        # 结构化日志（JSON 一行）
        audit_logger.info("[OPS_ACTION_PLAN_AUDIT] %s", json.dumps(log_data))
    except Exception as e:
        # 审计失败不能影响主流程
        logger.warning(
            "Failed to audit log OpsActionPlan: %s (request_id=%s)", e, request_id
        )


def run_explainer_agent(
    snapshot: SystemSnapshot,
    health_output: HealthAnalystOutput,
    plan_output: RemediationPlannerOutput,
    request_id: Optional[str] = None,
) -> ExplainerOutput:
    """
    Explainer Agent: Generate human-friendly explanations and recommendations.
    
    This agent is responsible for:
    - Generating SRE-friendly narrative via LLM (or fallback if LLM disabled)
    - Extracting actionable recommendations for ops teams
    - Tracking LLM usage metadata
    
    Args:
        snapshot: SystemSnapshot instance (for LLM context)
        health_output: HealthAnalystOutput from health analyst agent
        plan_output: RemediationPlannerOutput from remediation planner agent
        request_id: Optional request ID for tracing
    
    Returns:
        ExplainerOutput with narrative, recommended actions, and LLM usage metadata
    """
    health_result = health_output.health_result
    context = health_output.context
    safety_suggestions = plan_output.safety_suggestions
    strategy_lab = plan_output.strategy_lab
    
    # Generate narrative via LLM or fallback
    try:
        narrative, recommended_actions, llm_usage = _generate_system_health_narrative(
            health_result=health_result,
            strategy_lab=strategy_lab,
            safety_suggestions=safety_suggestions,
            snapshot=snapshot,
            context=context,
            request_id=request_id,
        )
    except Exception as e:
        logger.warning(f"[EXPLAINER] Failed to generate narrative: {e}")
        # Fallback to simple explanation
        narrative = f"Service is {health_result.band} with score {health_result.score:.1f}."
        recommended_actions = ["Review system metrics and health trends"]
        llm_usage = {"llm_enabled": False, "error": str(e)}
    
    # Apply output guardrails to ensure narrative is sufficiently urgent for critical cases
    narrative, recommended_actions = apply_ops_output_guardrails(
        health_result=health_result,
        narrative=narrative,
        recommended_actions=recommended_actions,
        request_id=request_id,
    )
    
    return ExplainerOutput(
        narrative=narrative,
        recommended_actions=recommended_actions,
        llm_usage=llm_usage,
    )


# ========================================
# LLM Explanation Helper
# ========================================

@maybe_traceable(name="ops_llm_explanation")
def _generate_system_health_narrative(
    health_result: Optional[SystemHealthCheckResult],
    strategy_lab: Optional[SystemStrategyLabResult],
    safety_suggestions: Optional[List[SaferConfigSuggestion]],
    snapshot: Optional[SystemSnapshot] = None,
    context: Optional[Any] = None,
    action_plan: Optional[OpsActionPlan] = None,
    request_id: Optional[str] = None,
) -> Tuple[str, List[str], Dict[str, Any]]:
    """
    Generate SRE-friendly narrative from structured system health results.
    
    Args:
        health_result: SystemHealthCheckResult instance
        strategy_lab: Optional SystemStrategyLabResult
        safety_suggestions: Optional list of SaferConfigSuggestion
        snapshot: Optional SystemSnapshot for additional context
        context: Optional SystemContextSnapshot with logs/runbooks/incidents
        request_id: Optional request ID for tracing
    
    Returns:
        Tuple of (narrative, recommended_actions, llm_usage)
        - narrative: 2-3 short sentences for SRE/Infra engineer
        - recommended_actions: List of 1-3 action strings
        - llm_usage: Dict with usage metadata or {"llm_enabled": False}
    """
    from services.fiqa_api.utils.llm_client import is_llm_generation_enabled
    from services.fiqa_api.clients import get_openai_client
    from services.fiqa_api.utils.env_loader import get_llm_conf
    from services.fiqa_api.ops_copilot.memory import load_system_memory
    import json
    import os
    import time
    
    # Track start time for latency
    llm_start_time = time.time()
    
    # Check if LLM generation is enabled
    if not is_llm_generation_enabled():
        logger.info(
            f"event=ops_llm_explanation "
            f"request_id={request_id or 'unknown'} "
            f"model=none "
            f"success=false "
            f"fallback_used=true "
            f"latency_ms=0.0 "
            f"reason=llm_disabled"
        )
        return _build_fallback_narrative(health_result, strategy_lab, safety_suggestions, snapshot, context, action_plan)
    
    # Get OpenAI client
    openai_client = get_openai_client()
    if openai_client is None:
        logger.info(
            f"event=ops_llm_explanation "
            f"request_id={request_id or 'unknown'} "
            f"model=none "
            f"success=false "
            f"fallback_used=true "
            f"latency_ms=0.0 "
            f"reason=client_unavailable"
        )
        return _build_fallback_narrative(health_result, strategy_lab, safety_suggestions, snapshot, context, action_plan)
    
    # Get LLM configuration
    try:
        llm_conf = get_llm_conf()
        model = llm_conf.get("model", "gpt-4o-mini")
        max_tokens = llm_conf.get("max_tokens", 512)
        input_per_mtok = llm_conf.get("input_per_mtok")
        output_per_mtok = llm_conf.get("output_per_mtok")
    except Exception as e:
        logger.warning(f"[OPS_COPILOT_LLM] Failed to load LLM config: {e}")
        llm_latency_ms = (time.time() - llm_start_time) * 1000
        logger.info(
            f"event=ops_llm_explanation "
            f"request_id={request_id or 'unknown'} "
            f"model=none "
            f"success=false "
            f"fallback_used=true "
            f"latency_ms={llm_latency_ms:.1f} "
            f"reason=config_error"
        )
        return _build_fallback_narrative(health_result, strategy_lab, safety_suggestions, snapshot, context, action_plan)
    
    # Use mini-4o (gpt-4o-mini) as specified
    model = "gpt-4o-mini"
    
    # Load system memory (knowledge base)
    system_memory = None
    if snapshot:
        try:
            system_memory = load_system_memory(
                service_name=snapshot.service_name,
                env=snapshot.environment,
                region=snapshot.region,
                max_snippets_per_category=2,
                max_snippet_length=400,
            )
            logger.debug(
                f"[OPS_COPILOT_LLM] Loaded system memory: "
                f"incidents={len(system_memory.get('incidents', []))}, "
                f"runbooks={len(system_memory.get('runbooks', []))}, "
                f"configs={len(system_memory.get('configs', []))}, "
                f"lessons={len(system_memory.get('lessons', []))}"
            )
        except Exception as mem_error:
            logger.warning(f"[OPS_COPILOT_LLM] Failed to load system memory: {mem_error}")
            system_memory = None
    
    try:
        # Build system prompt
        system_prompt = (
            "You are an SRE/Infrastructure engineer assistant. "
            "Your job is to explain system health check results in clear, concise language. "
            "Output JSON only with 'narrative' and 'recommended_actions' fields. "
            "Keep narrative to 2-3 short sentences. Keep recommended_actions to 1-3 actionable items."
        )
        
        # Build user prompt with structured data
        user_prompt_parts = []
        user_prompt_parts.append("System Health Check Results:")
        
        if snapshot:
            user_prompt_parts.append(f"  service_name: {snapshot.service_name}")
            user_prompt_parts.append(f"  environment: {snapshot.environment}")
        
        if health_result:
            user_prompt_parts.append(f"  band: {health_result.band}")
            user_prompt_parts.append(f"  score: {health_result.score:.1f}")
            user_prompt_parts.append(f"  risk_flags: {', '.join(health_result.risk_flags) if health_result.risk_flags else 'none'}")
            user_prompt_parts.append(f"  hard_block: {health_result.hard_block}")
            user_prompt_parts.append(f"  soft_warning: {health_result.soft_warning}")
            
            # Add per-metric details
            if health_result.details:
                user_prompt_parts.append("  metrics:")
                for metric_name, metric_data in health_result.details.items():
                    if isinstance(metric_data, dict):
                        value = metric_data.get("value")
                        status = metric_data.get("status")
                        if value is not None and status:
                            user_prompt_parts.append(f"    {metric_name}: {value} ({status})")
        
        # Add strategy lab info
        if strategy_lab:
            user_prompt_parts.append("")
            user_prompt_parts.append("Strategy Lab Results:")
            user_prompt_parts.append(f"  baseline_band: {strategy_lab.baseline_health.band}")
            user_prompt_parts.append(f"  baseline_score: {strategy_lab.baseline_health.score:.1f}")
            if strategy_lab.scenarios:
                best_scenario = strategy_lab.scenarios[0]  # Already sorted by score
                user_prompt_parts.append(f"  best_scenario: {best_scenario.title}")
                user_prompt_parts.append(f"  best_scenario_band: {best_scenario.health_result.band}")
                user_prompt_parts.append(f"  best_scenario_score: {best_scenario.health_result.score:.1f}")
        
        # Add safety suggestions
        if safety_suggestions:
            user_prompt_parts.append("")
            user_prompt_parts.append("Safety Upgrade Suggestions:")
            for idx, suggestion in enumerate(safety_suggestions[:3], 1):
                user_prompt_parts.append(f"  {idx}. {suggestion.title}")
                if suggestion.estimated_result:
                    user_prompt_parts.append(f"     Estimated band: {suggestion.estimated_result.band}")
                    user_prompt_parts.append(f"     Estimated score: {suggestion.estimated_result.score:.1f}")
        
        # Add proposed actions from OpsActionPlan (plan only, not executed)
        if action_plan and action_plan.actions:
            user_prompt_parts.append("")
            user_prompt_parts.append("# Proposed Actions (plan only, require human approval for critical actions)")
            user_prompt_parts.append("The planner has generated the following structured actions:")
            user_prompt_parts.append("These are PLAN-ONLY suggestions - they are NOT executed by this system.")
            user_prompt_parts.append("Execution must go through a separate safe_apply service with GuardRails and human approval.")
            user_prompt_parts.append("")
            for idx, action in enumerate(action_plan.actions, 1):
                # Build action info with severity and require_human_approval
                approval_status = "[requires human approval]" if action.require_human_approval else "[auto-approved]"
                action_info = f"  {idx}) action_type={action.action_type}, severity={action.severity} {approval_status}, summary=\"{action.summary}\""
                if action.estimated_before_score is not None and action.estimated_after_score is not None:
                    action_info += f", estimated_score: {action.estimated_before_score:.1f} -> {action.estimated_after_score:.1f}"
                if action.estimated_delta is not None:
                    action_info += f" (delta: {action.estimated_delta:+.1f})"
                user_prompt_parts.append(action_info)
                if action.reason:
                    user_prompt_parts.append(f"     Reason: {action.reason}")
                if action.details:
                    user_prompt_parts.append(f"     Details: {action.details[:100]}...")
            user_prompt_parts.append("")
            user_prompt_parts.append("When generating your narrative, please reference these planned actions and explain them.")
            user_prompt_parts.append("You can prioritize them, but remember: these are suggestions only, not executed changes.")
            user_prompt_parts.append("For critical actions or actions marked as 'requires human approval', emphasize that human SRE review is required before execution.")
        
        # Add context from semantic tools
        if context:
            # Log summary
            log_summary = getattr(context, 'log_summary', None)
            if log_summary:
                user_prompt_parts.append("")
                user_prompt_parts.append("Recent Logs (last 15 minutes):")
                user_prompt_parts.append(f"  Total lines: {log_summary.total_lines}")
                user_prompt_parts.append(f"  Errors: {log_summary.error_count}, Warnings: {log_summary.warn_count}")
                if log_summary.sample_entries:
                    user_prompt_parts.append(f"  Sample errors/warnings:")
                    for entry in log_summary.sample_entries[:3]:
                        if entry.level in ("ERROR", "WARN"):
                            user_prompt_parts.append(f"    [{entry.level}] {entry.message[:80]}")
            
            # Runbook
            runbook = getattr(context, 'runbook', None)
            if runbook:
                user_prompt_parts.append("")
                user_prompt_parts.append("Runbook Guidance:")
                user_prompt_parts.append(f"  Title: {runbook.title}")
                user_prompt_parts.append(f"  Summary: {runbook.summary}")
                if runbook.steps:
                    user_prompt_parts.append(f"  Key steps:")
                    for step in runbook.steps[:2]:  # Show first 2 steps
                        user_prompt_parts.append(f"    {step.order}. {step.action}")
            
            # Incident summary
            incident_summary = getattr(context, 'incident_summary', None)
            if incident_summary:
                user_prompt_parts.append("")
                user_prompt_parts.append("Recent Incidents (last 30 days):")
                user_prompt_parts.append(f"  Total: {incident_summary.total_incidents}, Critical: {incident_summary.critical_count}, High: {incident_summary.high_count}")
                if incident_summary.recent_incidents:
                    user_prompt_parts.append(f"  Most recent:")
                    recent = incident_summary.recent_incidents[0]
                    user_prompt_parts.append(f"    [{recent.severity.upper()}] {recent.summary[:80]}")
        
        # Add system memory (knowledge base) snippets
        if system_memory:
            has_memory = any(len(snippets) > 0 for snippets in system_memory.values())
            if has_memory:
                user_prompt_parts.append("")
                user_prompt_parts.append("# Historical Context (from system memory):")
                
                # Recent incidents
                if system_memory.get("incidents"):
                    user_prompt_parts.append("")
                    user_prompt_parts.append("Past incidents:")
                    for i, snippet in enumerate(system_memory["incidents"][:2], 1):
                        # Truncate snippet for prompt (first 200 chars)
                        snippet_short = snippet[:200] + "..." if len(snippet) > 200 else snippet
                        user_prompt_parts.append(f"  {i}. {snippet_short}")
                
                # Known runbooks
                if system_memory.get("runbooks"):
                    user_prompt_parts.append("")
                    user_prompt_parts.append("Known runbooks:")
                    for i, snippet in enumerate(system_memory["runbooks"][:2], 1):
                        snippet_short = snippet[:200] + "..." if len(snippet) > 200 else snippet
                        user_prompt_parts.append(f"  {i}. {snippet_short}")
                
                # Risky configs
                if system_memory.get("configs"):
                    user_prompt_parts.append("")
                    user_prompt_parts.append("Known risky configs:")
                    for i, snippet in enumerate(system_memory["configs"][:2], 1):
                        snippet_short = snippet[:200] + "..." if len(snippet) > 200 else snippet
                        user_prompt_parts.append(f"  {i}. {snippet_short}")
                
                # Lessons learned
                if system_memory.get("lessons"):
                    user_prompt_parts.append("")
                    user_prompt_parts.append("Lessons learned:")
                    for i, snippet in enumerate(system_memory["lessons"][:2], 1):
                        snippet_short = snippet[:200] + "..." if len(snippet) > 200 else snippet
                        user_prompt_parts.append(f"  {i}. {snippet_short}")
        
        # Add RAG knowledge from ops knowledge base
        # This provides vector-search-based context from runbooks/incidents/configs/lessons
        # The RAG snippets are retrieved based on service_name + symptom (risk_flag)
        rag_snippets = []
        if context and hasattr(context, 'rag_snippets'):
            rag_snippets = context.rag_snippets or []
        
        if rag_snippets:
            user_prompt_parts.append("")
            user_prompt_parts.append("# RAG knowledge from ops knowledge base:")
            user_prompt_parts.append("")
            user_prompt_parts.append("The following knowledge snippets were retrieved from the ops knowledge base")
            user_prompt_parts.append("using vector search. When generating your narrative and recommendations,")
            user_prompt_parts.append("please reference the source_file when applicable (e.g., 'According to runbooks.md...').")
            user_prompt_parts.append("")
            
            for i, snippet in enumerate(rag_snippets, 1):
                # Truncate text to 200-300 chars for prompt (to avoid bloat)
                text_preview = snippet.text[:250] + "..." if len(snippet.text) > 250 else snippet.text
                source_file = snippet.source_file
                score = snippet.score
                
                # Format: [source=filename, score=0.XX] text preview
                user_prompt_parts.append(f"- [source={source_file}, score={score:.2f}] {text_preview}")
        
        # If no RAG snippets but we have context, mention it's empty (for transparency)
        elif context and hasattr(context, 'rag_snippets'):
            # RAG was attempted but returned no results - don't add anything to prompt
            # (graceful degradation - system works fine without RAG)
            pass
        
        user_prompt_parts.append("")
        user_prompt_parts.append(
            "Please provide:\n"
            "1. narrative: 2-3 short sentences explaining the system health status, key metrics, and any improvements found.\n"
            "   If you reference knowledge from the RAG snippets above, mention the source_file (e.g., 'According to runbooks.md...').\n"
            "2. recommended_actions: 1-3 actionable items for the SRE team (e.g., 'Scale horizontally by adding 2 replicas', 'Review error rate spike at 14:00 UTC')."
        )
        
        user_prompt = "\n".join(user_prompt_parts)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        # Call LLM with timeout (15-20s as specified)
        timeout_seconds = 20.0
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                timeout=timeout_seconds,
            )
        except Exception as timeout_error:
            llm_latency_ms = (time.time() - llm_start_time) * 1000
            logger.warning(f"[OPS_COPILOT_LLM] LLM call timed out or failed: {timeout_error}", exc_info=True)
            logger.info(
                f"event=ops_llm_explanation "
                f"request_id={request_id or 'unknown'} "
                f"model={model} "
                f"success=false "
                f"fallback_used=true "
                f"latency_ms={llm_latency_ms:.1f} "
                f"reason=timeout_or_error"
            )
            return _build_fallback_narrative(health_result, strategy_lab, safety_suggestions, snapshot, context, action_plan)
        
        # Extract content
        content = ""
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content or ""
        
        # Parse JSON with safe fallback
        try:
            llm_data = json.loads(content) if content else {}
        except json.JSONDecodeError as e:
            llm_latency_ms = (time.time() - llm_start_time) * 1000
            logger.warning(f"[OPS_COPILOT_LLM] Failed to parse LLM JSON response: {e}, content: {content[:200]}")
            logger.info(
                f"event=ops_llm_explanation "
                f"request_id={request_id or 'unknown'} "
                f"model={model} "
                f"success=false "
                f"fallback_used=true "
                f"latency_ms={llm_latency_ms:.1f} "
                f"reason=parse_error"
            )
            return _build_fallback_narrative(health_result, strategy_lab, safety_suggestions, snapshot, context, action_plan)
        
        # Extract narrative and recommended_actions
        narrative = llm_data.get("narrative", "")
        recommended_actions_raw = llm_data.get("recommended_actions", [])
        
        # Normalize recommended_actions to list of strings
        if isinstance(recommended_actions_raw, str):
            recommended_actions = [recommended_actions_raw]
        elif isinstance(recommended_actions_raw, list):
            recommended_actions = [str(item) for item in recommended_actions_raw if item]
        else:
            recommended_actions = []
        
        # Limit to 3 actions
        recommended_actions = recommended_actions[:3]
        
        # Extract usage
        usage_obj = getattr(response, "usage", None)
        tokens_in = getattr(usage_obj, "prompt_tokens", None) if usage_obj else None
        tokens_out = getattr(usage_obj, "completion_tokens", None) if usage_obj else None
        tokens_total = getattr(usage_obj, "total_tokens", None) if usage_obj else None
        
        # Estimate cost
        cost_usd_est = None
        if tokens_in is not None and tokens_out is not None:
            if input_per_mtok is not None and output_per_mtok is not None:
                cost_usd_est = (
                    (tokens_in / 1_000_000.0) * input_per_mtok +
                    (tokens_out / 1_000_000.0) * output_per_mtok
                )
        
        # Build usage dict
        usage_dict = {
            "llm_enabled": True,
            "prompt_tokens": tokens_in,
            "completion_tokens": tokens_out,
            "total_tokens": tokens_total,
            "cost_usd_est": cost_usd_est,
            "model": model,
        }
        
        # Structured logging for LLM explanation
        llm_latency_ms = (time.time() - llm_start_time) * 1000
        logger.info(
            f"event=ops_llm_explanation "
            f"request_id={request_id or 'unknown'} "
            f"model={model} "
            f"success=true "
            f"fallback_used=false "
            f"latency_ms={llm_latency_ms:.1f} "
            f"tokens={tokens_total} "
            f"cost_usd_est={cost_usd_est or 0.0:.6f}"
        )
        
        return narrative, recommended_actions, usage_dict
        
    except Exception as e:
        llm_latency_ms = (time.time() - llm_start_time) * 1000
        logger.exception("[OPS_COPILOT_LLM_ERROR] Failed to generate LLM explanation")
        logger.info(
            f"event=ops_llm_explanation "
            f"request_id={request_id or 'unknown'} "
            f"model={model if 'model' in locals() else 'none'} "
            f"success=false "
            f"fallback_used=true "
            f"latency_ms={llm_latency_ms:.1f} "
            f"reason=exception"
        )
        return _build_fallback_narrative(health_result, strategy_lab, safety_suggestions, snapshot, context, action_plan)


def _build_fallback_narrative(
    health_result: Optional[SystemHealthCheckResult],
    strategy_lab: Optional[SystemStrategyLabResult],
    safety_suggestions: Optional[List[SaferConfigSuggestion]],
    snapshot: Optional[SystemSnapshot] = None,
    context: Optional[Any] = None,
    action_plan: Optional[OpsActionPlan] = None,
) -> Tuple[str, List[str], Dict[str, Any]]:
    """
    Build deterministic fallback narrative when LLM is disabled or fails.
    
    Returns:
        Tuple of (narrative, recommended_actions, llm_usage)
    """
    narrative_parts = []
    
    if health_result:
        narrative_parts.append(f"Service is {health_result.band} with score {health_result.score:.1f}.")
        if health_result.risk_flags:
            narrative_parts.append(f"Key risks: {', '.join(health_result.risk_flags[:3])}.")
    else:
        narrative_parts.append("Service health status unknown.")
    
    if strategy_lab and strategy_lab.scenarios:
        narrative_parts.append(f"Strategy lab found {len(strategy_lab.scenarios)} improved scenarios.")
    
    # Add context hints if available
    if context:
        log_summary = getattr(context, 'log_summary', None)
        if log_summary and log_summary.error_count > 10:
            narrative_parts.append(f"Logs show {log_summary.error_count} errors in last 15 min.")
        
        incident_summary = getattr(context, 'incident_summary', None)
        if incident_summary and incident_summary.critical_count > 0:
            narrative_parts.append(f"{incident_summary.critical_count} critical incidents in last 30 days.")
    
    narrative = " ".join(narrative_parts) if narrative_parts else "System health check completed."
    
    recommended_actions = []
    if health_result and health_result.band in ("degraded", "critical"):
        recommended_actions.append("Review system metrics and consider scaling or optimization")
    if safety_suggestions:
        recommended_actions.append("Review safety upgrade suggestions")
    if not recommended_actions:
        recommended_actions.append("Monitor system metrics and review health trends")
    
    # Limit to 2 actions for fallback
    recommended_actions = recommended_actions[:2]
    
    llm_usage = {"llm_enabled": False}
    
    return narrative, recommended_actions, llm_usage


def apply_ops_output_guardrails(
    health_result: SystemHealthCheckResult,
    narrative: Optional[str],
    recommended_actions: Optional[List[str]],
    request_id: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """
    Apply output guardrails to ensure narrative and recommendations are urgent enough for critical cases.
    
    This function checks if the LLM-generated narrative is sufficiently urgent when the system is critical.
    If the narrative is too calm (lacks urgency language), it appends urgent language.
    If recommended_actions don't include emergency actions, it adds them.
    
    This ensures that even if the LLM generates overly calm text, we have rule-based safety nets.
    
    Args:
        health_result: SystemHealthCheckResult instance (source of truth for health assessment)
        narrative: Optional narrative text from LLM (may be None if LLM disabled)
        recommended_actions: Optional list of recommended actions from LLM
        request_id: Optional request ID for security logging
    
    Returns:
        Tuple of (narrative, recommended_actions) - potentially adjusted with guardrail content
    """
    from services.fiqa_api.observability.security_events import log_security_event
    
    # Initialize defaults
    if narrative is None:
        narrative = ""
    if recommended_actions is None:
        recommended_actions = []
    
    narrative_adjusted = False
    actions_adjusted = False
    
    # Check health status
    band = health_result.band
    hard_block = health_result.hard_block
    soft_warning = health_result.soft_warning
    
    # Critical cases or hard_block: narrative MUST contain urgent language
    if hard_block or band == "critical":
        urgent_keywords = [
            "立即", "immediately", "立刻", "urgent", "紧急", "emergency",
            "严重", "serious", "critical", "严重问题", "critical issue",
            "需要立即", "immediate action", "立即处理", "take immediate action",
        ]
        
        narrative_lower = narrative.lower()
        has_urgent_language = any(kw.lower() in narrative_lower for kw in urgent_keywords)
        
        if not has_urgent_language:
            # Narrative lacks sufficient urgency - prepend urgent language
            urgent_prefix = "⚠️ **CRITICAL**: "
            narrative = urgent_prefix + narrative
            narrative_adjusted = True
        
        # Check recommended_actions for emergency actions
        emergency_keywords = [
            "降流量", "reduce traffic", "增加副本", "add replicas", "扩容", "scale",
            "触发应急", "trigger emergency", "runbook", "应急", "emergency",
            "立即", "immediately", "立刻", "urgent",
        ]
        
        actions_text = " ".join(recommended_actions).lower()
        has_emergency_action = any(kw.lower() in actions_text for kw in emergency_keywords)
        
        if not has_emergency_action or len(recommended_actions) == 0:
            # Add a standard emergency action
            emergency_action = "立即降低流量或增加副本数量，触发应急runbook"
            recommended_actions = [emergency_action] + recommended_actions
            actions_adjusted = True
        
        # Log security event if we adjusted
        if narrative_adjusted or actions_adjusted:
            log_security_event(
                event_type="narrative_guardrail_adjusted",
                request_id=request_id,
                context={
                    "service_name": "ops_copilot",
                    "reason": "hard_block_or_critical_without_urgency",
                    "band": band,
                    "hard_block": hard_block,
                    "narrative_adjusted": narrative_adjusted,
                    "actions_adjusted": actions_adjusted,
                },
            )
    
    # Degraded cases: narrative should mention priority
    elif band == "degraded":
        priority_keywords = [
            "尽快", "as soon as possible", "优先", "priority", "需要关注", "needs attention",
            "尽快处理", "address soon", "需要尽快", "needs to be addressed",
        ]
        
        narrative_lower = narrative.lower()
        has_priority_language = any(kw.lower() in narrative_lower for kw in priority_keywords)
        
        if not has_priority_language and narrative:
            # Add priority note
            priority_suffix = "\n\n💡 提示：系统已降级，建议优先排查并修复。"
            narrative = narrative + priority_suffix
            narrative_adjusted = True
    
    # Ensure narrative is not empty (fallback)
    if not narrative.strip():
        narrative = f"Service health status: {band} (score: {health_result.score:.1f})."
    
    # Ensure we have at least one action (fallback)
    if not recommended_actions:
        recommended_actions = ["Review system metrics and consider remediation actions"]
    
    # Limit to 3 actions max
    recommended_actions = recommended_actions[:3]
    
    return narrative, recommended_actions


# ========================================
# Tool Layer Imports (for ReAct/Planner)
# ========================================
# These imports expose the standard tool functions for use by ReAct/Planner agents.
# The existing runtime functions (run_system_health_check, etc.) remain unchanged.
# This is a lightweight reference - no changes to existing code paths.

from services.fiqa_api.ops_copilot.tools import (
    tool_system_health_check,
    tool_safety_upgrade,
    tool_strategy_lab,
    TOOL_REGISTRY,
)

