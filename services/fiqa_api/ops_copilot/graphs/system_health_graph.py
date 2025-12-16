"""
system_health_graph.py - System Health LangGraph Workflow
==========================================================
LangGraph workflow for system health checks with safety upgrades and strategy lab.
"""

import logging
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

from langgraph.graph import StateGraph, END

from services.fiqa_api.observability.langsmith_tracing import maybe_traceable

from services.fiqa_api.ops_copilot.schemas import (
    SystemSnapshot,
    SystemHealthCheckResult,
    SaferConfigSuggestion,
    SystemStrategyLabResult,
    SystemContextSnapshot,
    RagSnippet,
    OpsActionPlan,
)
from services.fiqa_api.ops_copilot.ops_runtime import (
    run_system_health_check,
    run_safety_upgrade_for_system,
    run_system_strategy_lab,
    _generate_system_health_narrative,
    fetch_rag_context_for_system,
    build_ops_action_plan,
    validate_ops_action_plan,
    log_ops_action_plan,
)
from services.fiqa_api.ops_copilot.react_planner import run_react_planner
from services.fiqa_api.ops_copilot.semantic_tools import (
    query_logs,
    get_runbook,
    summarize_recent_incidents,
)
from services.fiqa_api.mortgage.schemas import AgentStep

logger = logging.getLogger("ops_copilot")


class SystemHealthGraphState(TypedDict, total=False):
    """LangGraph state for system health workflow."""

    # Input
    snapshot: SystemSnapshot

    # Intermediate results
    health_result: Optional[SystemHealthCheckResult]
    safety_suggestions: Optional[List[SaferConfigSuggestion]]
    strategy_lab: Optional[SystemStrategyLabResult]
    context: Optional[SystemContextSnapshot]
    rag_snippets: Optional[List[RagSnippet]]
    action_plan: Optional[OpsActionPlan]

    # LLM output
    narrative: Optional[str]
    recommended_actions: Optional[List[str]]
    llm_usage: Optional[Dict[str, Any]]

    # Metadata / observability
    agent_steps: List[AgentStep]
    request_id: Optional[str]


def _health_check_node(state: SystemHealthGraphState) -> Dict[str, Any]:
    """
    Node: run the core system health check and gather semantic context.
    
    Acts as HealthAnalyst agent: classify band, compute score, populate context.
    """
    snapshot = state["snapshot"]
    request_id = state.get("request_id")
    step_start_time = datetime.utcnow()

    try:
        # Acts as HealthAnalyst agent: classify band, compute score, populate context
        health_result = run_system_health_check(snapshot)
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000

        # Structured logging
        logger.info(
            f"event=ops_node_complete node=health_check "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"band={health_result.band} "
            f"score={health_result.score:.1f} "
            f"risk_flags={','.join(health_result.risk_flags) if health_result.risk_flags else 'none'} "
            f"service_name={snapshot.service_name}"
        )

        # Build semantic context based on health status
        context = None
        try:
            # Always query logs and incidents
            log_summary = query_logs(snapshot.service_name, window_minutes=15, max_samples=5)
            incident_summary = summarize_recent_incidents(snapshot.service_name, window_days=30, max_items=5)
            
            # Query runbook if degraded/critical
            runbook = None
            if health_result.band in ("degraded", "critical") and health_result.risk_flags:
                # Map risk flags to symptoms
                symptom = health_result.risk_flags[0]  # Use first risk flag as symptom
                runbook = get_runbook(snapshot.service_name, symptom)
            
            # Fetch RAG context from ops knowledge base
            # This provides additional context from runbooks/incidents/configs/lessons
            # Note: fetch_rag_context_for_system handles graceful degradation internally
            rag_snippets = fetch_rag_context_for_system(
                snapshot=snapshot,
                health_result=health_result,
                top_n=3,  # Limit to 3 snippets to avoid prompt bloat
            )
            
            # Build context snapshot (including RAG snippets)
            context = SystemContextSnapshot(
                log_summary=log_summary,
                runbook=runbook,
                incident_summary=incident_summary,
                rag_snippets=rag_snippets,
            )
            
            logger.info(
                f"event=ops_semantic_tools_complete "
                f"request_id={request_id or 'unknown'} "
                f"service_name={snapshot.service_name} "
                f"log_error_count={log_summary.error_count if log_summary else 0} "
                f"runbook_fetched={runbook is not None} "
                f"incident_count={incident_summary.total_incidents if incident_summary else 0} "
                f"rag_snippets_count={len(rag_snippets)}"
            )
        except Exception as ctx_error:
            logger.warning(f"[SYSTEM_HEALTH_GRAPH] Failed to build semantic context: {ctx_error}")
            # Continue without context (graceful degradation)
            context = None
        
        # Also store rag_snippets separately in state for easy access
        # (though they're also in context.rag_snippets)
        rag_snippets_for_state = context.rag_snippets if context else []

        # Build key metrics summary for agent step
        key_metrics = {
            "band": health_result.band,
            "score": health_result.score,
            "risk_flags_count": len(health_result.risk_flags),
            "hard_block": health_result.hard_block,
            "context_available": context is not None,
        }

        agent_steps = state.get("agent_steps", [])
        
        # Add RAG retrieval result to agent steps for observability
        rag_count = len(rag_snippets_for_state)
        key_metrics["rag_snippets_count"] = rag_count
        
        agent_steps.append(
            AgentStep(
                step_id="health_check",
                step_name="System Health Check (HealthAnalyst agent)",
                status="completed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={
                    "service_name": snapshot.service_name,
                    "environment": snapshot.environment,
                    "agent_role": "health_analyst",
                },
                outputs=key_metrics,
            )
        )
        
        # Add a note about RAG retrieval in agent steps if snippets were found
        if rag_count > 0:
            agent_steps.append(
                AgentStep(
                    step_id="rag_retrieval",
                    step_name="RAG Knowledge Retrieval",
                    status="completed",
                    timestamp=datetime.utcnow().isoformat(),
                    duration_ms=0,  # RAG retrieval is included in health_check duration
                    inputs={
                        "service_name": snapshot.service_name,
                        "symptom": health_result.risk_flags[0] if health_result and health_result.risk_flags else None,
                    },
                    outputs={"snippets_retrieved": rag_count},
                )
            )

        return {
            "health_result": health_result,
            "context": context,
            "rag_snippets": rag_snippets_for_state,
            "agent_steps": agent_steps,
        }
    except Exception as e:
        logger.exception(f"[SYSTEM_HEALTH_GRAPH] health_check_node failed: {e}")
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
        request_id = state.get("request_id")
        logger.error(
            f"event=ops_node_failed node=health_check "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"error={str(e)}"
        )
        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="health_check",
                step_name="System Health Check",
                status="failed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={"service_name": snapshot.service_name, "environment": snapshot.environment},
                error=str(e),
            )
        )
        # Re-raise to stop graph execution
        raise


def _need_safety_upgrade_router(state: SystemHealthGraphState) -> str:
    """
    Router to decide whether to run safety upgrade.
    
    Returns:
        "need_upgrade" if band is "degraded" or "critical"
        "skip_upgrade" otherwise
    """
    health_result = state.get("health_result")
    if not health_result:
        return "skip_upgrade"
    
    band = health_result.band
    if band in ("degraded", "critical"):
        return "need_upgrade"
    return "skip_upgrade"


def _safety_upgrade_node(state: SystemHealthGraphState) -> Dict[str, Any]:
    """
    Node: run safety upgrade suggestions if health is degraded/critical.
    
    Acts as RemediationPlanner agent: generate safer configs.
    """
    snapshot = state["snapshot"]
    request_id = state.get("request_id")
    health_result = state.get("health_result")
    step_start_time = datetime.utcnow()

    try:
        # Acts as RemediationPlanner agent: generate safer configs
        safety_suggestions = run_safety_upgrade_for_system(snapshot)
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000

        # Structured logging
        band_str = health_result.band if health_result else 'unknown'
        score_val = health_result.score if health_result else 0.0
        logger.info(
            f"event=ops_node_complete node=safety_upgrade "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"band={band_str} "
            f"score={score_val:.1f} "
            f"safety_upgrade_ran=true "
            f"suggestions_count={len(safety_suggestions)}"
        )

        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="safety_upgrade",
                step_name="Safety Upgrade Suggestions (RemediationPlanner agent)",
                status="completed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={
                    "service_name": snapshot.service_name,
                    "agent_role": "remediation_planner",
                },
                outputs={"suggestions_count": len(safety_suggestions)},
            )
        )

        return {
            "safety_suggestions": safety_suggestions,
            "agent_steps": agent_steps,
        }
    except Exception as e:
        logger.warning(f"[SYSTEM_HEALTH_GRAPH] safety_upgrade_node failed: {e}", exc_info=True)
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
        request_id = state.get("request_id")
        logger.error(
            f"event=ops_node_failed node=safety_upgrade "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"error={str(e)}"
        )
        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="safety_upgrade",
                step_name="Safety Upgrade Suggestions",
                status="failed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={"service_name": snapshot.service_name},
                error=str(e),
            )
        )
        # Return empty suggestions on error (graceful degradation)
        return {
            "safety_suggestions": [],
            "agent_steps": agent_steps,
        }


def _strategy_lab_node(state: SystemHealthGraphState) -> Dict[str, Any]:
    """
    Node: run strategy lab to explore alternative scenarios.
    
    Acts as RemediationPlanner agent: generate what-if scenarios.
    """
    snapshot = state["snapshot"]
    request_id = state.get("request_id")
    health_result = state.get("health_result")
    step_start_time = datetime.utcnow()

    try:
        # Acts as RemediationPlanner agent: generate what-if scenarios
        strategy_lab = run_system_strategy_lab(snapshot)
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000

        # Count improved scenarios (scenarios with higher score than baseline)
        baseline_score = strategy_lab.baseline_health.score if strategy_lab else 0.0
        improved_count = 0
        if strategy_lab:
            for scenario in strategy_lab.scenarios:
                if scenario.health_result.score > baseline_score:
                    improved_count += 1

        # Structured logging
        band_str = health_result.band if health_result else 'unknown'
        score_val = health_result.score if health_result else 0.0
        scenarios_count = len(strategy_lab.scenarios) if strategy_lab else 0
        logger.info(
            f"event=ops_node_complete node=strategy_lab "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"band={band_str} "
            f"score={score_val:.1f} "
            f"strategy_improved={improved_count} "
            f"scenarios_count={scenarios_count}"
        )

        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="strategy_lab",
                step_name="Strategy Lab Analysis (RemediationPlanner agent)",
                status="completed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={
                    "service_name": snapshot.service_name,
                    "agent_role": "remediation_planner",
                },
                outputs={"scenarios_count": len(strategy_lab.scenarios)},
            )
        )

        return {
            "strategy_lab": strategy_lab,
            "agent_steps": agent_steps,
        }
    except Exception as e:
        logger.warning(f"[SYSTEM_HEALTH_GRAPH] strategy_lab_node failed: {e}", exc_info=True)
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
        request_id = state.get("request_id")
        logger.error(
            f"event=ops_node_failed node=strategy_lab "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"error={str(e)}"
        )
        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="strategy_lab",
                step_name="Strategy Lab Analysis",
                status="failed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={"service_name": snapshot.service_name},
                error=str(e),
            )
        )
        # Return None strategy_lab on error (graceful degradation)
        return {
            "strategy_lab": None,
            "agent_steps": agent_steps,
        }


def _action_planner_node(state: SystemHealthGraphState) -> Dict[str, Any]:
    """
    Node: build structured OpsActionPlan from safety suggestions and strategy lab.
    
    PLAN ONLY - never ACT.
    This node only generates structured action plans. It never executes any real operations,
    never calls any external APIs (Kubernetes, Cloud Run, database config changes, etc.).
    
    Acts as Action Planner: convert suggestions/scenarios into structured OpsActionPlan.
    """
    snapshot = state.get("snapshot")
    health_result = state.get("health_result")
    safety_suggestions = state.get("safety_suggestions")
    strategy_lab = state.get("strategy_lab")
    request_id = state.get("request_id")
    step_start_time = datetime.utcnow()

    try:
        # PLAN ONLY: Build structured action plan
        # This function is pure - no external I/O, no API calls, only data transformation
        action_plan = build_ops_action_plan(
            service_name=snapshot.service_name if snapshot else "unknown",
            health_result=health_result,
            safety_suggestions=safety_suggestions,
            strategy_lab=strategy_lab,
        )
        
        # Validate action plan with guardrails
        action_plan = validate_ops_action_plan(action_plan, health_result)
        
        # 审计日志：只记录 degraded / critical 的 plan
        log_ops_action_plan(action_plan, health_result, request_id=request_id)
        
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000

        # Structured logging
        band_str = health_result.band if health_result else 'unknown'
        score_val = health_result.score if health_result else 0.0
        actions_count = len(action_plan.actions) if action_plan else 0
        logger.info(
            f"event=ops_node_complete node=action_planner "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"band={band_str} "
            f"score={score_val:.1f} "
            f"actions_count={actions_count} "
            f"hard_block={action_plan.hard_block if action_plan else False} "
            f"num_actions_blocked={action_plan.num_actions_blocked} "
            f"num_actions_require_human={action_plan.num_actions_require_human}"
        )

        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="action_planner",
                step_name="Ops Action Planner (plan only, no execution)",
                status="completed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={
                    "service_name": snapshot.service_name if snapshot else "unknown",
                    "agent_role": "action_planner",
                },
                outputs={
                    "num_actions": len(action_plan.actions),
                    "hard_block": action_plan.hard_block,
                    "num_actions_blocked": action_plan.num_actions_blocked,
                    "num_actions_require_human": action_plan.num_actions_require_human,
                },
            )
        )
        
        # Add validation step record
        agent_steps.append(
            AgentStep(
                step_id="action_planner_validation",
                step_name="OpsActionPlan built & validated",
                status="completed",
                timestamp=datetime.utcnow().isoformat(),
                duration_ms=0,  # Validation is included in action_planner duration
                inputs={},
                outputs={
                    "num_actions": len(action_plan.actions),
                    "num_actions_blocked": action_plan.num_actions_blocked,
                    "num_actions_require_human": action_plan.num_actions_require_human,
                },
            )
        )

        return {
            "action_plan": action_plan,
            "agent_steps": agent_steps,
        }
    except Exception as e:
        logger.warning(f"[SYSTEM_HEALTH_GRAPH] action_planner_node failed: {e}", exc_info=True)
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
        request_id = state.get("request_id")
        logger.error(
            f"event=ops_node_failed node=action_planner "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"error={str(e)}"
        )
        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="action_planner",
                step_name="Ops Action Planner",
                status="failed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={"service_name": snapshot.service_name if snapshot else "unknown"},
                error=str(e),
            )
        )
        # Return empty plan on error (graceful degradation)
        from services.fiqa_api.ops_copilot.schemas import OpsActionPlan
        empty_plan = OpsActionPlan(
            service_name=snapshot.service_name if snapshot else "unknown",
            band=health_result.band if health_result else None,
            hard_block=health_result.hard_block if health_result else None,
            generated_at=datetime.utcnow(),
            actions=[],
            notes=["Action planning failed - see error logs"],
        )
        return {
            "action_plan": empty_plan,
            "agent_steps": agent_steps,
        }


def _llm_explanation_node(state: SystemHealthGraphState) -> Dict[str, Any]:
    """
    Node: generate SRE-friendly narrative via LLM.
    
    Acts as Explainer agent: generate narrative and recommended actions.
    """
    snapshot = state.get("snapshot")
    health_result = state.get("health_result")
    strategy_lab = state.get("strategy_lab")
    safety_suggestions = state.get("safety_suggestions", [])
    context = state.get("context")
    action_plan = state.get("action_plan")
    request_id = state.get("request_id")

    step_start_time = datetime.utcnow()

    try:
        # Acts as Explainer agent: generate narrative and recommended actions
        # Pass action_plan to LLM explanation layer
        narrative, recommended_actions, llm_usage = _generate_system_health_narrative(
            health_result=health_result,
            strategy_lab=strategy_lab,
            safety_suggestions=safety_suggestions,
            snapshot=snapshot,
            context=context,
            action_plan=action_plan,
            request_id=request_id,
        )
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000

        # Extract fallback flag from llm_usage
        fallback_used = not llm_usage.get("llm_enabled", False) if llm_usage else True
        model = llm_usage.get("model", "none") if llm_usage else "none"
        band_str = health_result.band if health_result else 'unknown'
        score_val = health_result.score if health_result else 0.0
        has_context = context is not None
        
        # Extract context details for logging
        log_error_count = 0
        if context and hasattr(context, 'log_summary') and context.log_summary:
            log_error_count = context.log_summary.error_count

        # Structured logging
        logger.info(
            f"event=ops_node_complete node=llm_explanation "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"band={band_str} "
            f"score={score_val:.1f} "
            f"llm_fallback_used={fallback_used} "
            f"model={model} "
            f"has_context={has_context} "
            f"log_error_count={log_error_count}"
        )

        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="llm_explanation",
                step_name="LLM Explanation (Explainer agent)",
                status="completed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={
                    "llm_enabled": llm_usage.get("llm_enabled", False) if llm_usage else False,
                    "agent_role": "explainer",
                },
                outputs={
                    "narrative_length": len(narrative) if narrative else 0,
                    "actions_count": len(recommended_actions) if recommended_actions else 0,
                },
            )
        )

        return {
            "narrative": narrative,
            "recommended_actions": recommended_actions or [],
            "llm_usage": llm_usage,
            "agent_steps": agent_steps,
        }
    except Exception as e:
        logger.warning(f"[SYSTEM_HEALTH_GRAPH] llm_explanation_node failed: {e}", exc_info=True)
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
        request_id = state.get("request_id")
        logger.error(
            f"event=ops_node_failed node=llm_explanation "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"error={str(e)}"
        )
        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="llm_explanation",
                step_name="LLM Explanation",
                status="failed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                error=str(e),
            )
        )
        # Fallback to simple deterministic narrative
        fallback_narrative = f"Service {health_result.band if health_result else 'unknown'} status. "
        if health_result:
            fallback_narrative += f"Health score: {health_result.score:.1f}. "
            if health_result.risk_flags:
                fallback_narrative += f"Key risks: {', '.join(health_result.risk_flags[:3])}. "
        if strategy_lab and strategy_lab.scenarios:
            fallback_narrative += f"Strategy lab found {len(strategy_lab.scenarios)} improved scenarios."
        
        fallback_actions = []
        if health_result and health_result.band in ("degraded", "critical"):
            fallback_actions.append("Review system metrics and consider scaling or optimization")
        if safety_suggestions:
            fallback_actions.append("Review safety upgrade suggestions")

        return {
            "narrative": fallback_narrative,
            "recommended_actions": fallback_actions,
            "llm_usage": {"llm_enabled": False, "error": str(e)},
            "agent_steps": agent_steps,
        }


_graph = None


def _build_system_health_graph() -> StateGraph:
    """
    Build and compile the LangGraph for the system health workflow.
    
    Flow:
    entry → health_check → router →
        ├─ need_upgrade → safety_upgrade → strategy_lab → llm_explanation → END
        └─ skip_upgrade → strategy_lab → llm_explanation → END
    """
    global _graph
    if _graph is not None:
        return _graph

    graph = StateGraph(SystemHealthGraphState)

    graph.add_node("health_check", _health_check_node)
    graph.add_node("safety_upgrade", _safety_upgrade_node)
    graph.add_node("strategy_lab", _strategy_lab_node)
    graph.add_node("action_planner", _action_planner_node)
    graph.add_node("llm_explanation", _llm_explanation_node)

    graph.set_entry_point("health_check")

    graph.add_conditional_edges(
        "health_check",
        _need_safety_upgrade_router,
        {
            "need_upgrade": "safety_upgrade",
            "skip_upgrade": "strategy_lab",
        },
    )

    graph.add_edge("safety_upgrade", "strategy_lab")
    graph.add_edge("strategy_lab", "action_planner")
    graph.add_edge("action_planner", "llm_explanation")
    graph.add_edge("llm_explanation", END)

    _graph = graph.compile()
    return _graph


@maybe_traceable(name="system_health_graph_run")
def run_system_health_graph(
    snapshot: SystemSnapshot,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Public entry: run the system health workflow via LangGraph.
    
    Args:
        snapshot: SystemSnapshot instance
        request_id: Optional request ID for tracing
    
    Returns:
        Dictionary with all results (can be converted to SystemHealthAgentResponse)
    """
    graph = _build_system_health_graph()

    initial_state: SystemHealthGraphState = {
        "snapshot": snapshot,
        "health_result": None,
        "safety_suggestions": None,
        "strategy_lab": None,
        "context": None,
        "rag_snippets": None,
        "action_plan": None,
        "narrative": None,
        "recommended_actions": None,
        "llm_usage": None,
        "agent_steps": [],
        "request_id": request_id,
    }

    final_state = graph.invoke(initial_state)

    # health_result should always be set by health_check_node
    health_result = final_state.get("health_result")
    if health_result is None:
        raise ValueError("health_result is None after graph execution - this should not happen")

    return {
        "snapshot": snapshot,
        "health_result": health_result,
        "safety_suggestions": final_state.get("safety_suggestions", []),
        "strategy_lab": final_state.get("strategy_lab"),
        "context": final_state.get("context"),
        "action_plan": final_state.get("action_plan"),
        "narrative": final_state.get("narrative"),
        "recommended_actions": final_state.get("recommended_actions", []),
        "agent_steps": final_state.get("agent_steps", []),
        "llm_usage": final_state.get("llm_usage"),
    }


def _react_planner_node(state: SystemHealthGraphState) -> Dict[str, Any]:
    """
    Node: run ReAct planner to decide which tools to call.
    
    This node uses LLM to decide tool sequence, but gracefully falls back
    to deterministic flow if LLM fails.
    """
    snapshot = state["snapshot"]
    request_id = state.get("request_id")
    existing_health = state.get("health_result")
    step_start_time = datetime.utcnow()
    
    try:
        # Call ReAct planner
        health_result, safety_suggestions, strategy_lab, planner_trace = run_react_planner(
            snapshot=snapshot,
            existing_health=existing_health,
            max_steps=3,
        )
        
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
        
        # Log planner execution
        logger.info(
            f"event=ops_node_complete node=react_planner "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"band={health_result.band} "
            f"score={health_result.score:.1f} "
            f"steps={len(planner_trace)} "
            f"safety_suggestions={len(safety_suggestions)} "
            f"strategy_lab_scenarios={len(strategy_lab.scenarios) if strategy_lab else 0}"
        )
        
        # Convert planner_trace to agent_steps
        agent_steps = state.get("agent_steps", [])
        for step_info in planner_trace:
            agent_steps.append(
                AgentStep(
                    step_id=f"react_planner_step_{step_info['step']}",
                    step_name=f"ReAct Planner Step {step_info['step']}: {step_info['tool']}",
                    status="completed",
                    timestamp=step_start_time.isoformat(),
                    duration_ms=0,  # Duration is tracked at planner level
                    inputs={
                        "tool": step_info["tool"],
                        "reason": step_info.get("reason", ""),
                    },
                    outputs={
                        "observation_summary": step_info.get("observation_summary", ""),
                    },
                )
            )
        
        return {
            "health_result": health_result,
            "safety_suggestions": safety_suggestions,
            "strategy_lab": strategy_lab,
            "agent_steps": agent_steps,
        }
    
    except Exception as e:
        logger.exception(f"[SYSTEM_HEALTH_GRAPH] react_planner_node failed: {e}")
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
        request_id = state.get("request_id")
        logger.error(
            f"event=ops_node_failed node=react_planner "
            f"request_id={request_id or 'unknown'} "
            f"latency_ms={step_duration:.1f} "
            f"error={str(e)}"
        )
        agent_steps = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="react_planner",
                step_name="ReAct Planner",
                status="failed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={"service_name": snapshot.service_name},
                error=str(e),
            )
        )
        # Fallback: run basic health check
        try:
            health_result = run_system_health_check(snapshot)
            return {
                "health_result": health_result,
                "safety_suggestions": [],
                "strategy_lab": None,
                "agent_steps": agent_steps,
            }
        except Exception as fallback_error:
            logger.error(f"[SYSTEM_HEALTH_GRAPH] Fallback health check failed: {fallback_error}")
            raise


_graph_with_planner = None


@maybe_traceable(name="system_health_graph_with_planner_run")
def run_system_health_graph_with_planner(
    snapshot: SystemSnapshot,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Public entry: run the system health workflow with ReAct planner via LangGraph.
    
    This is a parallel version to run_system_health_graph() that uses ReAct planner
    to decide tool sequence instead of deterministic flow.
    
    Flow: entry → react_planner → action_planner → llm_explanation → END
    
    Args:
        snapshot: SystemSnapshot instance
        request_id: Optional request ID for tracing
    
    Returns:
        Dictionary with all results (same structure as run_system_health_graph)
    """
    # Build graph (with caching)
    global _graph_with_planner
    if _graph_with_planner is None:
        graph = StateGraph(SystemHealthGraphState)
        graph.add_node("react_planner", _react_planner_node)
        graph.add_node("action_planner", _action_planner_node)
        graph.add_node("llm_explanation", _llm_explanation_node)
        graph.set_entry_point("react_planner")
        graph.add_edge("react_planner", "action_planner")
        graph.add_edge("action_planner", "llm_explanation")
        graph.add_edge("llm_explanation", END)
        _graph_with_planner = graph.compile()
    
    graph = _graph_with_planner
    
    initial_state: SystemHealthGraphState = {
        "snapshot": snapshot,
        "health_result": None,
        "safety_suggestions": None,
        "strategy_lab": None,
        "context": None,
        "rag_snippets": None,
        "action_plan": None,
        "narrative": None,
        "recommended_actions": None,
        "llm_usage": None,
        "agent_steps": [],
        "request_id": request_id,
    }
    
    final_state = graph.invoke(initial_state)
    
    # health_result should always be set by react_planner_node
    health_result = final_state.get("health_result")
    if health_result is None:
        raise ValueError("health_result is None after graph execution - this should not happen")
    
    return {
        "snapshot": snapshot,
        "health_result": health_result,
        "safety_suggestions": final_state.get("safety_suggestions", []),
        "strategy_lab": final_state.get("strategy_lab"),
        "context": final_state.get("context"),
        "action_plan": final_state.get("action_plan"),
        "narrative": final_state.get("narrative"),
        "recommended_actions": final_state.get("recommended_actions", []),
        "agent_steps": final_state.get("agent_steps", []),
        "llm_usage": final_state.get("llm_usage"),
    }

