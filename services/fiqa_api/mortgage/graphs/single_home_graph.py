# services/fiqa_api/mortgage/graphs/single_home_graph.py

import json
import logging
from typing import TypedDict, Optional, List, Dict, Any

from langgraph.graph import StateGraph, END

from services.fiqa_api.mortgage.schemas import (
    SingleHomeAgentRequest,
    SingleHomeAgentResponse,
    StressCheckRequest,
    StressCheckResponse,
    SafetyUpgradeResult,
    AgentStep,
    MortgageProgramPreview,
    StrategyLabResult,
)
from services.fiqa_api.mortgage.nl_to_stress_request import (
    PartialStressRequest,
    NLToStressRequestOutput,
)
from services.fiqa_api.mortgage.mortgage_agent_runtime import (
    run_stress_check,
    run_safety_upgrade_flow,
    _generate_single_home_narrative,
)
from services.fiqa_api.utils.llm_client import is_llm_generation_enabled

logger = logging.getLogger(__name__)


class SingleHomeGraphState(TypedDict, total=False):
    """LangGraph state for single-home workflow."""

    # 输入
    request: SingleHomeAgentRequest
    stress_request: StressCheckRequest

    # NLU fields (for natural language entry)
    user_text: Optional[str]
    partial_request: Optional[PartialStressRequest]
    missing_required_fields: Optional[List[str]]
    nl_intent_type: Optional[str]

    # 中间结果
    stress_result: Optional[StressCheckResponse]
    safety_upgrade: Optional[SafetyUpgradeResult]
    mortgage_programs: Optional[List[Dict[str, Any]]]
    mortgage_programs_preview: Optional[List[MortgageProgramPreview]]
    strategy_lab: Optional[StrategyLabResult]

    # LLM 输出
    borrower_narrative: Optional[str]
    recommended_actions: Optional[List[str]]
    llm_usage: Optional[Dict[str, Any]]

    # 元数据 / 观测
    agent_steps: List[AgentStep]
    errors: List[str]


def _nl_to_stress_request_node(state: SingleHomeGraphState) -> Dict[str, Any]:
    """Node: extract mortgage fields from natural language using NLU."""
    from services.fiqa_api.mortgage.nl_to_stress_request import nl_to_stress_request
    
    user_text = state.get("user_text")
    if not user_text:
        # If no user_text, just return state unchanged
        return {}
    
    result: NLToStressRequestOutput = nl_to_stress_request(
        user_text=user_text,
        conversation_history=None
    )
    
    return {
        "partial_request": result.partial_request,
        "missing_required_fields": result.missing_required_fields,
        "nl_intent_type": result.intent_type,
    }


def _need_more_info_router(state: SingleHomeGraphState) -> str:
    """
    Router to decide whether we have enough info to run a stress check.
    
    Returns:
        "have_enough_info" if all required fields are present
        "need_more_info" if any required fields are missing
    """
    missing = state.get("missing_required_fields") or []
    partial_request = state.get("partial_request")
    
    if len(missing) == 0 and partial_request is not None:
        return "have_enough_info"
    else:
        return "need_more_info"


def _stress_check_node(state: SingleHomeGraphState) -> Dict[str, Any]:
    """Node: run the core stress check tool."""
    stress_req = state["stress_request"]

    stress_result = run_stress_check(stress_req)

    # 将 stress_result 自带的 agent_steps 合并进 state.agent_steps
    steps: List[AgentStep] = []
    if "agent_steps" in state and state["agent_steps"]:
        steps.extend(state["agent_steps"])
    if getattr(stress_result, "agent_steps", None):
        steps.extend(stress_result.agent_steps)

    return {
        "stress_result": stress_result,
        "agent_steps": steps,
    }


def _need_safety_upgrade_router(state: SingleHomeGraphState) -> str:
    """
    Conditional router:
    - tight / high_risk → 'need_upgrade'
    - 其他（loose / ok / None）→ 'skip_upgrade'
    """
    stress = state.get("stress_result")
    band = getattr(stress, "stress_band", None)
    if band in ("tight", "high_risk"):
        return "need_upgrade"
    return "skip_upgrade"


def _safety_upgrade_node(state: SingleHomeGraphState) -> Dict[str, Any]:
    """Node: run the safety upgrade flow if stress is tight / high_risk."""
    stress_req = state["stress_request"]
    safety_upgrade = run_safety_upgrade_flow(stress_req, max_candidates=5)

    # 注意：safety_upgrade 内部已经重新跑了一次 stress_check，用于对比
    return {"safety_upgrade": safety_upgrade}


def _build_mortgage_programs_preview(programs: List[Dict[str, Any]]) -> List[MortgageProgramPreview]:
    """Build lightweight preview list from full program data (top 2-3 only)."""
    previews: List[MortgageProgramPreview] = []
    for prog in programs[:3]:
        previews.append(
            MortgageProgramPreview(
                program_id=prog.get("id") or prog.get("program_id") or "unknown",
                name=prog.get("name", "Mortgage assistance program"),
                state=prog.get("state"),
                max_dti=prog.get("max_dti"),
                summary=prog.get("short_description") or prog.get("description"),
                tags=prog.get("tags") or [],
            )
        )
    return previews


def _mortgage_programs_node(state: SingleHomeGraphState) -> Dict[str, Any]:
    """Node: fetch mortgage programs when stress is tight / high risk."""
    stress_result = state.get("stress_result")
    if not stress_result:
        return {}

    if getattr(stress_result, "stress_band", None) not in ("tight", "high_risk"):
        return {}

    try:
        # Import the search_mortgage_programs function directly from the server file
        # This avoids namespace conflicts with the mcp package
        import sys
        import importlib.util
        from pathlib import Path
        
        # Find the server.py file
        server_file = Path("/app/mcp/mortgage_programs_server/server.py")
        if not server_file.exists():
            # Try relative path as fallback
            server_file = Path(__file__).parent.parent.parent.parent.parent / "mcp" / "mortgage_programs_server" / "server.py"
        
        if not server_file.exists():
            logger.warning("[SINGLE_HOME_GRAPH] mortgage_programs_node unavailable: server.py not found at %s", server_file)
            return {}
        
        # Load the module directly from file
        spec = importlib.util.spec_from_file_location("mortgage_programs_server", server_file)
        if spec is None or spec.loader is None:
            logger.warning("[SINGLE_HOME_GRAPH] mortgage_programs_node unavailable: could not load spec from %s", server_file)
            return {}
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        search_mortgage_programs = module.search_mortgage_programs
        logger.debug("[SINGLE_HOME_GRAPH] Successfully loaded mortgage_programs_server from %s", server_file)
    except Exception as e:
        logger.warning("[SINGLE_HOME_GRAPH] mortgage_programs_node unavailable: failed to load module - %s", e, exc_info=True)
        return {}

    stress_req = state.get("stress_request")
    # Get zip_code and state from stress_request or home_snapshot
    zip_code = None
    location_state = None
    
    # Try to get zip_code from stress_request first
    if getattr(stress_req, "zip_code", None):
        zip_code = stress_req.zip_code
    # Fall back to home_snapshot if available
    elif stress_result and hasattr(stress_result, "home_snapshot"):
        home_snapshot = stress_result.home_snapshot or {}
        if isinstance(home_snapshot, dict):
            zip_code = home_snapshot.get("zip_code")
    
    # Get state
    if getattr(stress_req, "state", None):
        location_state = stress_req.state
    elif state.get("request") and getattr(state["request"], "stress_request", None):
        location_state = getattr(state["request"].stress_request, "state", None)
    # Fall back to home_snapshot
    elif stress_result and hasattr(stress_result, "home_snapshot"):
        home_snapshot = stress_result.home_snapshot or {}
        if isinstance(home_snapshot, dict):
            location_state = location_state or home_snapshot.get("state")
    
    # If no zip_code, cannot call MCP
    if not zip_code:
        logger.warning("[SINGLE_HOME_GRAPH] mortgage_programs_node skipped: no zip_code available")
        return {}
    
    # Record step start
    from datetime import datetime
    step_start_time = datetime.utcnow()
    
    try:
        # MCP function returns JSON string, need to parse it
        programs_json = search_mortgage_programs(
            zip_code=zip_code,
            state=location_state,
            current_dti=getattr(stress_result, "dti_ratio", None),
            profile_tags=[],
        )
        # Parse JSON string to list of dicts
        programs = json.loads(programs_json) if isinstance(programs_json, str) else programs_json
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[SINGLE_HOME_GRAPH] mortgage_programs search failed: %s", exc, exc_info=True)
        # Record failed step
        step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
        agent_steps: List[AgentStep] = state.get("agent_steps", [])
        agent_steps.append(
            AgentStep(
                step_id="mortgage_programs_mcp",
                step_name="Mortgage programs lookup (MCP Server)",
                status="failed",
                timestamp=step_start_time.isoformat(),
                duration_ms=step_duration,
                inputs={"zip_code": zip_code, "state": location_state},
                error=str(exc),
            )
        )
        return {"agent_steps": agent_steps}

    if not programs:
        # MCP was called but returned no results - still mark as checked
        hit_count = 0
        normalized: List[Dict[str, Any]] = []
    else:
        hit_count = len(programs)
        normalized: List[Dict[str, Any]] = []
        # Take top 3 programs
        for program in programs[:3]:
            if isinstance(program, dict):
                normalized.append(program)
            elif hasattr(program, "model_dump"):
                normalized.append(program.model_dump())
            else:
                # Fallback: convert to dict if possible
                normalized.append(program)

    # Record successful step
    step_duration = (datetime.utcnow() - step_start_time).total_seconds() * 1000
    agent_steps: List[AgentStep] = state.get("agent_steps", [])
    agent_steps.append(
        AgentStep(
            step_id="mortgage_programs_mcp",
            step_name="Mortgage programs lookup (MCP Server)",
            status="completed",
            timestamp=step_start_time.isoformat(),
            duration_ms=step_duration,
            inputs={"zip_code": zip_code, "state": location_state},
            outputs={"hit_count": hit_count, "programs_count": len(normalized)},
        )
    )

    # Build preview from normalized programs (top 2-3)
    previews = _build_mortgage_programs_preview(normalized) if normalized else []

    # Update safety_upgrade to mark MCP call
    result: Dict[str, Any] = {
        "mortgage_programs": normalized,
        "mortgage_programs_preview": previews,
        "agent_steps": agent_steps,
    }
    
    safety_upgrade = state.get("safety_upgrade")
    if safety_upgrade:
        # Update existing safety_upgrade with MCP info
        result["safety_upgrade"] = SafetyUpgradeResult(
            baseline_band=safety_upgrade.baseline_band,
            baseline_dti=safety_upgrade.baseline_dti,
            baseline_total_payment=safety_upgrade.baseline_total_payment,
            baseline_zip_code=safety_upgrade.baseline_zip_code,
            baseline_state=safety_upgrade.baseline_state,
            baseline_is_tight_or_worse=safety_upgrade.baseline_is_tight_or_worse,
            safer_homes=safety_upgrade.safer_homes,
            primary_suggestion=safety_upgrade.primary_suggestion,
            alternative_suggestions=safety_upgrade.alternative_suggestions,
            mortgage_programs_checked=True,
            mortgage_programs_hit_count=hit_count,
        )
    else:
        # safety_upgrade doesn't exist yet (shouldn't happen but defensive)
        # Create a minimal one to mark MCP was called
        result["safety_upgrade"] = SafetyUpgradeResult(
            baseline_is_tight_or_worse=True,
            mortgage_programs_checked=True,
            mortgage_programs_hit_count=hit_count,
        )
    
    return result


def _strategy_lab_node(state: SingleHomeGraphState) -> Dict[str, Any]:
    """Optional node: run strategy lab to explore a few alternative plans."""
    from services.fiqa_api.mortgage.mortgage_agent_runtime import run_strategy_lab
    
    stress_request = state.get("stress_request")
    if not stress_request:
        return {}

    try:
        lab_result = run_strategy_lab(
            req=stress_request,
            max_scenarios=3,
        )
        logger.info(
            f"[SINGLE_HOME_GRAPH] Strategy lab completed: "
            f"baseline_band={lab_result.baseline_stress_band}, "
            f"scenarios_count={len(lab_result.scenarios)}"
        )
        return {"strategy_lab": lab_result}
    except Exception as e:
        logger.warning(
            f"[SINGLE_HOME_GRAPH] strategy_lab failed: {e}",
            exc_info=True
        )
        return {}


def _llm_explanation_node(state: SingleHomeGraphState) -> Dict[str, Any]:
    """Node: generate borrower narrative + recommended actions via LLM."""
    if not is_llm_generation_enabled():
        return {}

    stress_result = state.get("stress_result")
    request = state.get("request")
    safety_upgrade = state.get("safety_upgrade")
    mortgage_programs = state.get("mortgage_programs")

    user_message = request.user_message if request and request.user_message else None

    narrative, actions, usage = _generate_single_home_narrative(
        stress_result=stress_result,
        user_message=user_message,
        safety_upgrade=safety_upgrade,
        mortgage_programs=mortgage_programs,
        approval_score=stress_result.approval_score if stress_result else None,
        risk_assessment=stress_result.risk_assessment if stress_result else None,
    )

    return {
        "borrower_narrative": narrative,
        "recommended_actions": actions,
        "llm_usage": usage,
    }


_graph = None


def _build_single_home_graph() -> StateGraph:
    """
    Build and compile the LangGraph for the single-home workflow.

    Flow:
    entry → stress_check → (router)
        - need_upgrade → safety_upgrade → mortgage_programs → strategy_lab → llm_explanation → END
        - skip_upgrade → strategy_lab → llm_explanation → END
    """
    global _graph
    if _graph is not None:
        return _graph

    graph = StateGraph(SingleHomeGraphState)

    graph.add_node("stress_check", _stress_check_node)
    graph.add_node("safety_upgrade", _safety_upgrade_node)
    graph.add_node("mortgage_programs", _mortgage_programs_node)
    graph.add_node("strategy_lab", _strategy_lab_node)
    graph.add_node("llm_explanation", _llm_explanation_node)

    graph.set_entry_point("stress_check")

    graph.add_conditional_edges(
        "stress_check",
        _need_safety_upgrade_router,
        {
            "need_upgrade": "safety_upgrade",
            "skip_upgrade": "strategy_lab",
        },
    )

    graph.add_edge("safety_upgrade", "mortgage_programs")
    graph.add_edge("mortgage_programs", "strategy_lab")
    graph.add_edge("strategy_lab", "llm_explanation")
    graph.add_edge("llm_explanation", END)

    _graph = graph.compile()
    return _graph


def run_single_home_graph(
    request: SingleHomeAgentRequest,
    *,
    config: Optional[Dict[str, Any]] = None,
) -> SingleHomeAgentResponse:
    """
    Public entry: run the single-home workflow via LangGraph.

    This is a drop-in alternative to run_single_home_agent:
    same input type, same output type, just with LangGraph orchestrating
    stress_check → safety_upgrade → llm_explanation.
    """
    graph = _build_single_home_graph()

    initial_state: SingleHomeGraphState = {
        "request": request,
        "stress_request": request.stress_request,
        "stress_result": None,
        "safety_upgrade": None,
        "mortgage_programs": None,
        "mortgage_programs_preview": None,
        "strategy_lab": None,
        "borrower_narrative": None,
        "recommended_actions": None,
        "llm_usage": None,
        "agent_steps": [],
        "errors": [],
    }

    final_state = graph.invoke(initial_state, config=config)

    # stress_result should always be set by stress_check_node
    stress_result = final_state.get("stress_result")
    if stress_result is None:
        raise ValueError("stress_result is None after graph execution - this should not happen")

    # Merge graph-level agent_steps into stress_result.agent_steps
    graph_agent_steps = final_state.get("agent_steps", [])
    if graph_agent_steps:
        # Merge with existing agent_steps from stress_result
        existing_steps = getattr(stress_result, "agent_steps", []) or []
        all_steps = list(existing_steps)
        
        # Add graph-level steps (like MCP) that aren't already in stress_result
        existing_step_ids = {step.step_id for step in existing_steps}
        for step in graph_agent_steps:
            if step.step_id not in existing_step_ids:
                all_steps.append(step)
        
        # Update stress_result with merged agent_steps
        # Use model_dump(exclude={'agent_steps'}) to avoid duplicate argument
        result_dict = stress_result.model_dump()
        result_dict["agent_steps"] = all_steps
        stress_result = StressCheckResponse(**result_dict)

    return SingleHomeAgentResponse(
        stress_result=stress_result,
        borrower_narrative=final_state.get("borrower_narrative"),
        recommended_actions=final_state.get("recommended_actions"),
        llm_usage=final_state.get("llm_usage"),
        safety_upgrade=final_state.get("safety_upgrade"),
        mortgage_programs_preview=final_state.get("mortgage_programs_preview"),
        risk_assessment=stress_result.risk_assessment if stress_result else None,  # Copy from stress_result for convenience
        strategy_lab=final_state.get("strategy_lab"),
    )

