"""
react_planner.py - ReAct Planner for Ops Copilot
=================================================
Minimal ReAct-style planner that uses LLM to decide which tools to call.

This module implements a simple ReAct loop (max 3 steps) where:
1. Step 1: Always run health_check if not provided
2. Steps 2-3: LLM decides next tool (safety_upgrade, strategy_lab, or finish)

All logic gracefully degrades to deterministic flow if LLM fails.
"""

import logging
import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from services.fiqa_api.ops_copilot.schemas import (
    SystemSnapshot,
    SystemHealthCheckResult,
    SaferConfigSuggestion,
    SystemStrategyLabResult,
)
from services.fiqa_api.ops_copilot.tools import (
    TOOL_REGISTRY,
    tool_system_health_check,
    tool_safety_upgrade,
    tool_strategy_lab,
)
from services.fiqa_api.utils.llm_client import is_llm_generation_enabled
from services.fiqa_api.clients import get_openai_client

logger = logging.getLogger("ops_copilot")


def run_react_planner(
    snapshot: SystemSnapshot,
    existing_health: Optional[SystemHealthCheckResult] = None,
    max_steps: int = 3,
) -> Tuple[SystemHealthCheckResult, List[SaferConfigSuggestion], Optional[SystemStrategyLabResult], List[Dict[str, Any]]]:
    """
    Run ReAct planner to decide which tools to call.
    
    Args:
        snapshot: SystemSnapshot instance
        existing_health: Optional existing health result (if None, will call health_check)
        max_steps: Maximum number of steps (default: 3)
    
    Returns:
        Tuple of:
        - health_result: Final SystemHealthCheckResult
        - safety_suggestions: List of SaferConfigSuggestion (from last safety_upgrade call)
        - strategy_lab: SystemStrategyLabResult or None (from last strategy_lab call)
        - planner_trace: List of step dicts for observability
    """
    planner_trace: List[Dict[str, Any]] = []
    health_result: Optional[SystemHealthCheckResult] = existing_health
    safety_suggestions: List[SaferConfigSuggestion] = []
    strategy_lab: Optional[SystemStrategyLabResult] = None
    
    # Step 1: Always run health_check if not provided
    if health_result is None:
        try:
            health_result = tool_system_health_check(snapshot)
            planner_trace.append({
                "step": 1,
                "tool": "health_check",
                "reason": "initial_health_check",
                "observation_summary": f"band={health_result.band}, score={health_result.score:.1f}, risk_flags={health_result.risk_flags}",
            })
            logger.info(f"[REACT_PLANNER] Step 1: health_check -> band={health_result.band}, score={health_result.score:.1f}")
        except Exception as e:
            logger.error(f"[REACT_PLANNER] Step 1 failed: {e}")
            # Fallback: return empty results
            fallback_health = SystemHealthCheckResult(
                band="healthy",
                score=85.0,
                risk_flags=[],
                hard_block=False,
                soft_warning=False,
                details={},
            )
            return fallback_health, [], None, planner_trace
    
    # Steps 2-3: LLM decides next tool
    for step_num in range(2, max_steps + 1):
        # Check if we should stop early
        if health_result.band == "healthy":
            # Healthy system: don't allow safety_upgrade, but can still run strategy_lab
            # If we already have strategy_lab, finish
            if strategy_lab is not None:
                planner_trace.append({
                    "step": step_num,
                    "tool": "finish",
                    "reason": "system_healthy_and_strategy_lab_complete",
                    "observation_summary": "No further actions needed",
                })
                break
        
        # Call LLM to decide next tool
        try:
            next_tool_decision = _call_llm_for_tool_decision(
                snapshot=snapshot,
                health_result=health_result,
                safety_suggestions=safety_suggestions,
                strategy_lab=strategy_lab,
                step_num=step_num,
            )
            
            if next_tool_decision is None:
                # LLM call failed - graceful degradation: run deterministic flow
                logger.warning(f"[REACT_PLANNER] Step {step_num}: LLM failed, falling back to deterministic flow")
                health_result, safety_suggestions, strategy_lab = _run_deterministic_fallback(
                    snapshot, health_result
                )
                planner_trace.append({
                    "step": step_num,
                    "tool": "fallback",
                    "reason": "llm_failed_using_deterministic_flow",
                    "observation_summary": "LLM unavailable, used deterministic tool sequence",
                })
                break
            
            tool_name = next_tool_decision.get("tool")
            reason = next_tool_decision.get("reason", "")
            
            if tool_name == "finish":
                planner_trace.append({
                    "step": step_num,
                    "tool": "finish",
                    "reason": reason,
                    "observation_summary": "Planner decided to finish",
                })
                break
            
            # Validate tool name
            if tool_name not in TOOL_REGISTRY:
                logger.warning(f"[REACT_PLANNER] Step {step_num}: Invalid tool '{tool_name}', finishing")
                planner_trace.append({
                    "step": step_num,
                    "tool": "finish",
                    "reason": f"invalid_tool_{tool_name}",
                    "observation_summary": f"Invalid tool name: {tool_name}",
                })
                break
            
            # Safety check: don't allow safety_upgrade if healthy
            if tool_name == "safety_upgrade" and health_result.band == "healthy":
                logger.info(f"[REACT_PLANNER] Step {step_num}: Blocked safety_upgrade for healthy system")
                planner_trace.append({
                    "step": step_num,
                    "tool": "finish",
                    "reason": "safety_upgrade_blocked_for_healthy_system",
                    "observation_summary": "System is healthy, safety_upgrade not needed",
                })
                break
            
            # Execute tool
            try:
                observation = _execute_tool(tool_name, snapshot, health_result)
                
                # Update state based on tool result
                if tool_name == "safety_upgrade":
                    safety_suggestions = observation
                elif tool_name == "strategy_lab":
                    strategy_lab = observation
                
                planner_trace.append({
                    "step": step_num,
                    "tool": tool_name,
                    "reason": reason,
                    "observation_summary": _summarize_observation(tool_name, observation),
                })
                logger.info(f"[REACT_PLANNER] Step {step_num}: {tool_name} -> {_summarize_observation(tool_name, observation)}")
                
            except Exception as tool_error:
                logger.error(f"[REACT_PLANNER] Step {step_num}: Tool {tool_name} failed: {tool_error}")
                planner_trace.append({
                    "step": step_num,
                    "tool": tool_name,
                    "reason": reason,
                    "observation_summary": f"Tool execution failed: {str(tool_error)}",
                })
                # Continue to next step (don't break on tool error)
                continue
        
        except Exception as e:
            logger.error(f"[REACT_PLANNER] Step {step_num} failed: {e}", exc_info=True)
            # Fallback to deterministic flow
            health_result, safety_suggestions, strategy_lab = _run_deterministic_fallback(
                snapshot, health_result
            )
            planner_trace.append({
                "step": step_num,
                "tool": "fallback",
                "reason": f"exception_{type(e).__name__}",
                "observation_summary": f"Exception occurred, used deterministic flow",
            })
            break
    
    # Post-processing: ensure strategy_lab is run for degraded/critical systems
    if health_result.band in ("critical", "degraded") and strategy_lab is None:
        try:
            strategy_lab = tool_strategy_lab(snapshot, health_result)
            logger.info(f"[REACT_PLANNER] Post-processing: ran strategy_lab for {health_result.band} system")
        except Exception as e:
            logger.warning(f"[REACT_PLANNER] Post-processing strategy_lab failed: {e}")
    
    return health_result, safety_suggestions, strategy_lab, planner_trace


def _call_llm_for_tool_decision(
    snapshot: SystemSnapshot,
    health_result: SystemHealthCheckResult,
    safety_suggestions: List[SaferConfigSuggestion],
    strategy_lab: Optional[SystemStrategyLabResult],
    step_num: int,
) -> Optional[Dict[str, Any]]:
    """
    Call LLM to decide which tool to use next.
    
    Returns:
        Dict with {"tool": "...", "reason": "..."} or None if LLM fails
    """
    # Check if LLM is enabled
    if not is_llm_generation_enabled():
        return None
    
    # Get OpenAI client
    openai_client = get_openai_client()
    if openai_client is None:
        return None
    
    # Build prompt
    system_prompt = (
        "You are an ops copilot planner. Decide which tool to use next or finish.\n"
        "Available tools: health_check, safety_upgrade, strategy_lab, finish\n"
        "Rules:\n"
        "- If system is healthy, do NOT use safety_upgrade\n"
        "- If system is degraded/critical, consider safety_upgrade or strategy_lab\n"
        "Output ONLY valid JSON: {\"tool\": \"tool_name\", \"reason\": \"brief reason\"}\n"
        "Do not include any other text."
    )
    
    user_prompt_parts = [
        f"Current system health:",
        f"  band: {health_result.band}",
        f"  score: {health_result.score:.1f}",
        f"  risk_flags: {', '.join(health_result.risk_flags) if health_result.risk_flags else 'none'}",
    ]
    
    if safety_suggestions:
        user_prompt_parts.append(f"\nSafety suggestions already generated: {len(safety_suggestions)} items")
    
    if strategy_lab:
        user_prompt_parts.append(f"\nStrategy lab already completed: {len(strategy_lab.scenarios)} scenarios")
    
    user_prompt_parts.append(f"\nStep {step_num}: Which tool should we use next?")
    user_prompt = "\n".join(user_prompt_parts)
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=100,
            response_format={"type": "json_object"},
            timeout=10.0,
        )
        
        content = ""
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content or ""
        
        # Parse JSON
        try:
            decision = json.loads(content) if content else {}
            tool = decision.get("tool")
            reason = decision.get("reason", "")
            
            # Validate tool name
            if tool not in ["health_check", "safety_upgrade", "strategy_lab", "finish"]:
                logger.warning(f"[REACT_PLANNER] LLM returned invalid tool: {tool}")
                return None
            
            return {"tool": tool, "reason": reason}
        
        except json.JSONDecodeError as e:
            logger.warning(f"[REACT_PLANNER] Failed to parse LLM JSON: {e}, content: {content[:200]}")
            return None
    
    except Exception as e:
        logger.warning(f"[REACT_PLANNER] LLM call failed: {e}")
        return None


def _execute_tool(
    tool_name: str,
    snapshot: SystemSnapshot,
    health_result: SystemHealthCheckResult,
) -> Any:
    """
    Execute a tool by name.
    
    Returns:
        Tool result (varies by tool)
    """
    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        raise ValueError(f"Tool '{tool_name}' not found in registry")
    
    if tool_name == "health_check":
        return tool.callable(snapshot)
    elif tool_name == "safety_upgrade":
        return tool.callable(snapshot, health_result)
    elif tool_name == "strategy_lab":
        return tool.callable(snapshot, health_result)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def _summarize_observation(tool_name: str, observation: Any) -> str:
    """Summarize tool observation for logging."""
    if tool_name == "health_check":
        if isinstance(observation, SystemHealthCheckResult):
            return f"band={observation.band}, score={observation.score:.1f}"
    elif tool_name == "safety_upgrade":
        if isinstance(observation, list):
            return f"{len(observation)} suggestions"
    elif tool_name == "strategy_lab":
        if isinstance(observation, SystemStrategyLabResult):
            return f"{len(observation.scenarios)} scenarios"
    return str(observation)[:100]


def _run_deterministic_fallback(
    snapshot: SystemSnapshot,
    health_result: SystemHealthCheckResult,
) -> Tuple[SystemHealthCheckResult, List[SaferConfigSuggestion], Optional[SystemStrategyLabResult]]:
    """
    Fallback to deterministic tool sequence when LLM fails.
    
    Flow: health_check (already done) -> safety_upgrade (if degraded/critical) -> strategy_lab
    """
    safety_suggestions: List[SaferConfigSuggestion] = []
    strategy_lab: Optional[SystemStrategyLabResult] = None
    
    # Run safety_upgrade if degraded/critical
    if health_result.band in ("degraded", "critical"):
        try:
            safety_suggestions = tool_safety_upgrade(snapshot, health_result)
        except Exception as e:
            logger.warning(f"[REACT_PLANNER] Fallback safety_upgrade failed: {e}")
    
    # Always run strategy_lab
    try:
        strategy_lab = tool_strategy_lab(snapshot, health_result)
    except Exception as e:
        logger.warning(f"[REACT_PLANNER] Fallback strategy_lab failed: {e}")
    
    return health_result, safety_suggestions, strategy_lab

