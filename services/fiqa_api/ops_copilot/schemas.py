"""
schemas.py - Ops Copilot Data Models
=====================================
Pydantic models for ops copilot request/response.

These models define the data structures for system health checks,
safety upgrades, and strategy lab scenarios.
"""

from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, Field


# ========================================
# Health Band Enum
# ========================================

HealthBand = Literal["healthy", "warning", "degraded", "critical"]


# ========================================
# System Snapshot Model
# ========================================

class SystemSnapshot(BaseModel):
    """System snapshot model capturing current system metrics."""
    service_name: str = Field(..., description="Service name, e.g., 'api-gateway'")
    environment: Literal["prod", "staging", "dev"] = Field(..., description="Environment")
    cpu_pct: float = Field(..., ge=0, le=100, description="CPU usage percentage (0-100)")
    mem_pct: float = Field(..., ge=0, le=100, description="Memory usage percentage (0-100)")
    p95_latency_ms: float = Field(..., ge=0, description="P95 latency in milliseconds")
    error_rate: float = Field(..., ge=0, le=1, description="Error rate (0-1)")
    qps: float = Field(..., ge=0, description="Queries per second")
    disk_pct: float = Field(..., ge=0, le=100, description="Disk usage percentage (0-100)")
    timestamp: datetime = Field(..., description="Timestamp when snapshot was taken")
    region: Optional[str] = Field(None, description="Region identifier, e.g., 'us-east-1'")
    tags: Dict[str, str] = Field(default_factory=dict, description="Additional metadata tags")


# ========================================
# Health Check Result Model
# ========================================

class SystemHealthCheckResult(BaseModel):
    """System health check result with band, score, and risk flags."""
    band: HealthBand = Field(..., description="Health band classification")
    score: float = Field(..., ge=0, le=100, description="Health score (0-100)")
    risk_flags: List[str] = Field(
        default_factory=list,
        description="List of risk flag identifiers, e.g., ['high_cpu', 'high_latency', 'high_error_rate']"
    )
    hard_block: bool = Field(
        default=False,
        description="Whether this system should be blocked from deployment (hard block)"
    )
    soft_warning: bool = Field(
        default=False,
        description="Whether this system needs caution (soft warning)"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Per-metric assessments, e.g., {'cpu': {'value': 85.0, 'status': 'critical'}}"
    )


# ========================================
# Safety Upgrade Models
# ========================================

class SaferConfigSuggestion(BaseModel):
    """A single safety upgrade suggestion with structured config changes."""
    id: str = Field(..., description="Unique suggestion identifier")
    title: str = Field(..., description="Short human-facing title, e.g., 'Reduce QPS by 20% and add 1 replica'")
    description: str = Field(..., description="More verbose explanation")
    config_changes: Dict[str, Any] = Field(
        ...,
        description="Structured config changes, e.g., {'qps_limit': 0.8, 'replicas': +1}"
    )
    estimated_result: Optional[SystemHealthCheckResult] = Field(
        None,
        description="Estimated health check result after applying this suggestion"
    )


# ========================================
# Strategy Lab Models
# ========================================

class SystemStrategyScenario(BaseModel):
    """单个方案实验结果 (Single scenario experiment result)."""
    id: str = Field(..., description="Unique scenario identifier, e.g., 'lower_qps_20', 'add_replica'")
    title: str = Field(..., description="User-facing name, e.g., 'Lower QPS by 20%'")
    description: str = Field(..., description="Brief description of the scenario")
    snapshot_after_change: SystemSnapshot = Field(..., description="System snapshot after applying this scenario")
    health_result: SystemHealthCheckResult = Field(..., description="Health check result for this scenario")


class SystemStrategyLabResult(BaseModel):
    """方案实验室的整体输出 (Strategy lab overall output)."""
    baseline_snapshot: SystemSnapshot = Field(..., description="Baseline system snapshot")
    baseline_health: SystemHealthCheckResult = Field(..., description="Baseline health check result")
    scenarios: List[SystemStrategyScenario] = Field(
        default_factory=list,
        description="List of scenario results"
    )


# ========================================
# RAG Snippet Model
# ========================================

class RagSnippet(BaseModel):
    """
    A single RAG snippet retrieved from the ops knowledge base.
    
    This represents a relevant knowledge chunk from runbooks, incidents,
    configs, or lessons_learned that can be used to enhance LLM explanations.
    """
    text: str = Field(..., description="Snippet text content (chunk from knowledge base)")
    source_file: str = Field(..., description="Source markdown file (e.g., 'runbooks.md', 'incidents.md')")
    service_hint: Optional[str] = Field(
        None,
        description="Service hint extracted from chunk metadata (e.g., 'payment-service')"
    )
    symptom_hint: Optional[str] = Field(
        None,
        description="Symptom hint extracted from chunk metadata (e.g., 'high_error_rate')"
    )
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score from vector search (0-1)")


# ========================================
# Semantic Tools Context Model
# ========================================

class SystemContextSnapshot(BaseModel):
    """
    Context snapshot from semantic tools (logs, runbooks, incidents).
    
    This model aggregates operational context that helps the LLM
    provide better explanations and recommendations.
    """
    log_summary: Optional[Any] = Field(
        None,
        description="Log summary from query_logs() (LogSummary instance)"
    )
    runbook: Optional[Any] = Field(
        None,
        description="Runbook entry from get_runbook() (RunbookEntry instance)"
    )
    incident_summary: Optional[Any] = Field(
        None,
        description="Incident summary from summarize_recent_incidents() (IncidentSummary instance)"
    )
    rag_snippets: List[RagSnippet] = Field(
        default_factory=list,
        description="RAG snippets from ops knowledge base (vector search results)"
    )


# ========================================
# Multi-Agent Output Models
# ========================================

class HealthAnalystOutput(BaseModel):
    """
    Output from Health Analyst Agent.
    
    This agent is responsible for analyzing system health status,
    identifying risk flags, and providing initial diagnostic context.
    """
    health_result: SystemHealthCheckResult = Field(..., description="System health check result")
    context: Optional[SystemContextSnapshot] = Field(
        None,
        description="Operational context from semantic tools (logs, runbooks, incidents)"
    )
    analysis_notes: List[str] = Field(
        default_factory=list,
        description="Human-friendly analysis notes, e.g., 'CPU and error rate both elevated - possible retry storm'"
    )


class RemediationPlannerOutput(BaseModel):
    """
    Output from Remediation Planner Agent.
    
    This agent is responsible for generating remediation strategies,
    including safety suggestions and what-if scenario analysis.
    """
    safety_suggestions: List[SaferConfigSuggestion] = Field(
        default_factory=list,
        description="Safety upgrade suggestions (empty if system is healthy)"
    )
    strategy_lab: Optional[SystemStrategyLabResult] = Field(
        None,
        description="Strategy lab analysis with alternative scenarios"
    )
    plan_notes: List[str] = Field(
        default_factory=list,
        description="Human-friendly planning notes, e.g., 'Scenario X improves score from 34 → 52, recommend executing it first'"
    )


class ExplainerOutput(BaseModel):
    """
    Output from Explainer Agent.
    
    This agent is responsible for generating human-friendly explanations
    and actionable recommendations for SRE/ops teams.
    """
    narrative: Optional[str] = Field(
        None,
        description="SRE-friendly narrative explanation (2-3 sentences)"
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="List of recommended actions (1-3 items)"
    )
    llm_usage: Optional[Dict[str, Any]] = Field(
        None,
        description="LLM usage metadata (tokens, cost, etc.)"
    )


# ========================================
# Ops Action Models (Plan / Act Separation)
# ========================================

class OpsAction(BaseModel):
    """
    A single structured action plan item.
    
    This represents a planned action that could be taken to improve system health.
    All actions are PLAN-ONLY - they are never executed by the LLM or planning layer.
    Execution must go through a separate, whitelisted safe_apply service with GuardRails.
    """
    action_id: str = Field(
        ...,
        description="Unique action identifier (generated with uuid4().hex)"
    )
    action_type: Literal[
        "reduce_qps",
        "add_replica",
        "reduce_error_rate",
        "adjust_timeout",
        "tune_retry_policy",
        "other",
    ] = Field(
        ...,
        description="Type of action to be taken"
    )
    target_service: str = Field(
        ...,
        description="Target service name (e.g., 'api-gateway')"
    )
    severity: Literal["info", "warning", "critical"] = Field(
        ...,
        description="Severity level of this action"
    )
    summary: str = Field(
        ...,
        description="One-sentence summary of the action (e.g., 'Reduce QPS by 20% and add 1 replica')"
    )
    details: Optional[str] = Field(
        None,
        description="Longer description (optional)"
    )
    estimated_before_score: Optional[float] = Field(
        None,
        description="Estimated health score before applying this action"
    )
    estimated_after_score: Optional[float] = Field(
        None,
        description="Estimated health score after applying this action"
    )
    estimated_delta: Optional[float] = Field(
        None,
        description="Estimated score change (after - before)"
    )
    reason: str = Field(
        ...,
        description="Reason for this action (combines risk_flags and brief explanation, e.g., 'high_error_rate + high_latency — reduce QPS to relieve upstream pressure')"
    )
    require_human_approval: bool = Field(
        default=True,
        description="Whether this action requires human approval before execution"
    )
    source: Literal["safety_suggestions", "strategy_lab"] = Field(
        ...,
        description="Source of this action (safety_suggestions or strategy_lab)"
    )


class OpsActionPlan(BaseModel):
    """
    Structured action plan for a service.
    
    This represents a complete plan of actions that could be taken to improve system health.
    The plan is PLAN-ONLY - it contains no execution results, only planned actions.
    
    All actions in this plan must go through a separate safe_apply service with GuardRails
    before any real changes are made to production systems.
    """
    service_name: str = Field(
        ...,
        description="Service name (e.g., 'api-gateway')"
    )
    band: Optional[HealthBand] = Field(
        None,
        description="Health band from health_result.band"
    )
    hard_block: Optional[bool] = Field(
        None,
        description="Whether this system has hard_block flag"
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp when this plan was generated"
    )
    actions: List[OpsAction] = Field(
        default_factory=list,
        description="List of planned actions (0-5 actions)"
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Human-friendly notes about the plan (e.g., 'Selected 2 actions from safety_suggestions improving score from 34.0 to 52.0')"
    )
    num_actions_blocked: int = Field(
        default=0,
        description="Number of actions blocked by guardrails (for audit/eval purposes)"
    )
    num_actions_require_human: int = Field(
        default=0,
        description="Number of actions requiring human approval (for audit/eval purposes)"
    )


# ========================================
# Agent Response Model
# ========================================

class SystemHealthAgentResponse(BaseModel):
    """Complete response from system health agent workflow."""
    snapshot: SystemSnapshot = Field(..., description="Input system snapshot")
    health_result: SystemHealthCheckResult = Field(..., description="System health check result")
    safety_suggestions: List[SaferConfigSuggestion] = Field(
        default_factory=list,
        description="Safety upgrade suggestions (only populated if health is degraded/critical)"
    )
    strategy_lab: Optional[SystemStrategyLabResult] = Field(
        None,
        description="Strategy lab analysis with alternative scenarios"
    )
    narrative: Optional[str] = Field(
        None,
        description="SRE-friendly narrative explanation (2-3 sentences)"
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="List of recommended actions (1-3 items)"
    )
    agent_steps: List[Any] = Field(
        default_factory=list,
        description="Step-by-step execution log (AgentStep instances)"
    )
    llm_usage: Optional[Dict[str, Any]] = Field(
        None,
        description="LLM usage metadata (tokens, cost, etc.)"
    )
    context: Optional[SystemContextSnapshot] = Field(
        None,
        description="Operational context from semantic tools (logs, runbooks, incidents)"
    )


__all__ = [
    "HealthBand",
    "SystemSnapshot",
    "SystemHealthCheckResult",
    "SaferConfigSuggestion",
    "SystemStrategyScenario",
    "SystemStrategyLabResult",
    "RagSnippet",
    "SystemContextSnapshot",
    "HealthAnalystOutput",
    "RemediationPlannerOutput",
    "ExplainerOutput",
    "SystemHealthAgentResponse",
    "OpsAction",
    "OpsActionPlan",
]

