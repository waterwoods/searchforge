"""
jd_analysis_graph.py - Flow 1: JD Analysis + Fit Assessment LangGraph

This is Flow 1: JD interpretation + fit assessment (single analysis loop) LangGraph implementation.
Reuses existing modules (jd_interpreter.py, job_fit_analyzer.py) to provide a minimal usable analysis flow.

[改动标记 - Step 2]
- 新增 node_attach_evidence 节点（证据对齐/反幻觉）
- 更新流程顺序：check_constraints → interpret_jd → lifecycle_reflection → spotlight_story → evidence_align → analyze_fit
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END

from services.fiqa_api.jobhunter.schemas import JDAnalysisState, JobJDInput, JobJDSummary, GraphStep
from services.fiqa_api.jobhunter.jd_interpreter import interpret_job_jd
from services.fiqa_api.jobhunter.job_fit_analyzer import analyze_job_fit, JobFitSummary
from services.fiqa_api.jobhunter.jd_constraints import check_basic_constraints
from services.fiqa_api.jobhunter.jd_story_reflection import (
    node_lifecycle_reflection as _node_lifecycle_reflection,
    node_spotlight_story as _node_spotlight_story,
)
from services.fiqa_api.jobhunter.jd_evidence_align import attach_evidence_snippets
from services.fiqa_api.jobhunter.jd_core_signals import run_core_signals
from services.fiqa_api.telemetry.langsmith_config import (
    is_langsmith_enabled,
    default_langsmith_run_config,
)
from services.fiqa_api.jobhunter.sqlite_cache import (
    init_db,
    compute_jd_hash,
    get_cached_analysis,
    save_analysis,
)

logger = logging.getLogger(__name__)


def _create_graph_step(
    node_name: str,
    status: str,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    duration_ms: Optional[float] = None,
    extra_info: Optional[Dict[str, Any]] = None,
) -> GraphStep:
    """
    Helper function to create a graph step.
    
    Args:
        node_name: Name of the node (e.g., "check_constraints")
        status: Step status ("pending", "in_progress", "completed", "failed", "skipped")
        started_at: ISO timestamp when step started
        finished_at: ISO timestamp when step finished
        duration_ms: Optional duration in milliseconds
        extra_info: Optional extra information dict
    
    Returns:
        GraphStep instance
    """
    return GraphStep(
        name=node_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        extra_info=extra_info,
    )


def node_check_constraints(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Check constraints
    
    Calls check_basic_constraints to identify hard blocks and soft flags
    (work mode, location restrictions, travel requirements) and writes
    the result to state["constraints"].
    """
    node_name = "check_constraints"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    try:
        jd_input = state.get("jd_input")
        if not jd_input:
            raise ValueError("Missing jd_input in state")
        
        candidate_profile = state.get("candidate_profile")
        profile_id = state.get("profile_id")
        
        # Ensure jd_input is JobJDInput type
        if isinstance(jd_input, dict):
            jd_input = JobJDInput(**jd_input)
        elif not isinstance(jd_input, JobJDInput):
            jd_input = JobJDInput.model_validate(jd_input)
        
        # Call constraint checking (with profile_id for mismatch detection)
        logger.info("Checking constraints...")
        constraints = check_basic_constraints(jd_input, candidate_profile=candidate_profile, profile_id=profile_id)
        
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Record completed step (reducer will append this to existing list)
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        
        # [Quick Filter] Propagate skip_deep_analysis flag to state
        return {
            "constraints": constraints,
            "skip_deep_analysis": constraints.skip_deep_analysis,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Record failed step (reducer will append this to existing list)
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        
        return {
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }


def node_interpret_jd(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Interpret JD
    
    Calls interpret_job_jd to interpret the JD and writes the result to state["jd_summary"].
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True to avoid heavy LLM calls.
    """
    node_name = "interpret_jd"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping interpret_jd: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        
        # Create a minimal jd_summary for compatibility (CLI and UI expect it)
        jd_input = state.get("jd_input")
        if isinstance(jd_input, dict):
            jd_input = JobJDInput(**jd_input)
        elif not isinstance(jd_input, JobJDInput):
            jd_input = JobJDInput.model_validate(jd_input)
        
        minimal_summary = JobJDSummary(
            job_id=jd_input.job_id,
            company=jd_input.company,
            title=jd_input.title,
            location=jd_input.location,
            gold_points=[],
            silver_points=[],
            bronze_points=[],
            core_skills=[],
            nice_to_have_skills=[],
            risks_or_red_flags=["Profile/JD mismatch: role type does not align with candidate profile"],
            recommendation="SKIP",
            reasoning_summary="Quick filter: This role appears to be primarily a sales/financial-advisory position, which does not align with the selected profile.",
            evidence_snippets=[],
        )
        
        return {
            "jd_summary": minimal_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    
    try:
        jd_input = state.get("jd_input")
        if not jd_input:
            raise ValueError("Missing jd_input in state")
        
        candidate_profile = state.get("candidate_profile")
        
        # Ensure jd_input is JobJDInput type
        # LangGraph may serialize objects as dict, need to convert back
        if isinstance(jd_input, dict):
            jd_input = JobJDInput(**jd_input)
        elif not isinstance(jd_input, JobJDInput):
            # If not JobJDInput and not dict, try to convert
            jd_input = JobJDInput.model_validate(jd_input)
        
        # Set candidate_profile (if provided)
        if candidate_profile:
            jd_input.candidate_profile = candidate_profile
        
        # Call JD interpretation
        logger.info("Interpreting JD...")
        jd_summary = interpret_job_jd(jd_input, client=None)
        
        # Check if interpret_job_jd returned None (should not happen, but handle gracefully)
        if jd_summary is None:
            logger.error("interpret_job_jd returned None, creating fallback summary")
            jd_summary = JobJDSummary(
                job_id=jd_input.job_id,
                company=jd_input.company,
                title=jd_input.title,
                location=jd_input.location,
                gold_points=[],
                silver_points=[],
                bronze_points=[],
                core_skills=[],
                nice_to_have_skills=[],
                risks_or_red_flags=[],
                recommendation="MAYBE",
                reasoning_summary="JD interpretation returned None (internal error)",
                evidence_snippets=[],
            )
        
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Record completed step (reducer will append this to existing list)
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        
        return {
            "jd_summary": jd_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        logger.error(f"Failed to interpret JD in node: {e}", exc_info=True)
        
        # Record failed step (reducer will append this to existing list)
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        
        # Create a minimal fallback jd_summary so the graph can continue
        # This matches the fallback behavior in interpret_job_jd
        minimal_summary = JobJDSummary(
            job_id=jd_input.job_id,
            company=jd_input.company,
            title=jd_input.title,
            location=jd_input.location,
            gold_points=[],
            silver_points=[],
            bronze_points=[],
            core_skills=[],
            nice_to_have_skills=[],
            risks_or_red_flags=[],
            recommendation="MAYBE",
            reasoning_summary=f"Analysis failed: {str(e)[:200]}",
            evidence_snippets=[],
        )
        
        return {
            "jd_summary": minimal_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }


def node_attach_evidence(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Attach Evidence Snippets (Step 2)
    
    Attaches evidence snippets from JD text to spotlight stories to reduce hallucinations.
    Reads jd_input.description and jd_summary, calls attach_evidence_snippets(),
    and updates jd_summary with evidence_snippets for each spotlight story.
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True.
    """
    node_name = "evidence_align"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping evidence_align: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append
    
    try:
        jd_input = state.get("jd_input")
        jd_summary = state.get("jd_summary")
        
        if not jd_input or not jd_summary:
            logger.warning("Missing jd_input or jd_summary, skipping evidence attachment")
            finished_at = datetime.utcnow().isoformat()
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            new_step = _create_graph_step(
                node_name, "completed",
                started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
                extra_info={"skipped": "Missing jd_input or jd_summary"}
            )
            return {"graph_steps": [new_step]}  # Return only new step, reducer will append
        
        # Ensure types
        if isinstance(jd_input, dict):
            jd_input = JobJDInput(**jd_input)
        elif not isinstance(jd_input, JobJDInput):
            jd_input = JobJDInput.model_validate(jd_input)
        
        if isinstance(jd_summary, dict):
            jd_summary = JobJDSummary(**jd_summary)
        elif not isinstance(jd_summary, JobJDSummary):
            jd_summary = JobJDSummary.model_validate(jd_summary)
        
        # Skip if no spotlight stories
        if not jd_summary.spotlight_stories:
            logger.debug("No spotlight stories found, skipping evidence attachment")
            finished_at = datetime.utcnow().isoformat()
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            new_step = _create_graph_step(
                node_name, "completed",
                started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
                extra_info={"skipped": "No spotlight stories"}
            )
            return {"graph_steps": [new_step]}  # Return only new step, reducer will append
        
        # Attach evidence snippets
        logger.info("Attaching evidence snippets to spotlight stories...")
        updated_summary = attach_evidence_snippets(
            jd_text=jd_input.description,
            summary=jd_summary,
        )
        
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        
        return {
            "jd_summary": updated_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def node_analyze_fit(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Analyze fit
    
    If candidate_profile and jd_summary are not None, calls analyze_job_fit to perform fit analysis.
    
    [Quick Filter] If skip_deep_analysis=True, returns early with low match score (1/10) and SKIP recommendation.
    """
    node_name = "analyze_fit"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    try:
        jd_summary = state.get("jd_summary")
        candidate_profile = state.get("candidate_profile")
        profile_id = state.get("profile_id")
        skip_deep_analysis = state.get("skip_deep_analysis", False)
        constraints = state.get("constraints")
        
        fit_summary = None
        
        # [Quick Filter] If skip_deep_analysis is True, return early with low score
        if skip_deep_analysis:
            logger.info("Quick filter active: returning low match score (1/10) due to profile mismatch")
            
            # Build reasoning from profile_mismatch_reasons
            reasons = []
            if constraints and hasattr(constraints, "profile_mismatch_reasons"):
                reasons = constraints.profile_mismatch_reasons or []
            
            # Create a minimal fit summary with SKIP recommendation
            # The route handler will set match_score=1 and category="C" for SKIP when skip_deep_analysis=True
            # The route handler will also build reasoning_summary from constraints.profile_mismatch_reasons
            fit_summary = JobFitSummary(
                recommendation_for_candidate="SKIP",
                strengths=[],
                gaps=reasons if reasons else ["Quick role filter detected this is a sales/financial advisor role, not a data engineering position, so deep analysis was skipped."],
                action_items=[],
            )
            
        elif candidate_profile and jd_summary:
            logger.info("Analyzing job fit...")
            fit_summary = analyze_job_fit(jd_summary, candidate_profile, profile_id=profile_id)
        else:
            logger.debug("Skipping fit analysis: missing candidate_profile or jd_summary")
        
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"fit_analyzed": fit_summary is not None}
        )
        
        return {
            "fit_summary": fit_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def node_lifecycle_reflection(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Wrapper for lifecycle_reflection node with step tracking.
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True.
    """
    node_name = "lifecycle_reflection"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping lifecycle_reflection: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append
    
    try:
        result = _node_lifecycle_reflection(state)
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        # Add new step to result (reducer will append)
        result["graph_steps"] = [new_step]
        return result
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def node_spotlight_story(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Wrapper for spotlight_story node with step tracking.
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True.
    """
    node_name = "spotlight_story"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping spotlight_story: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append
    
    try:
        result = _node_spotlight_story(state)
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms
        )
        # Add new step to result (reducer will append)
        result["graph_steps"] = [new_step]
        return result
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def node_core_signals(state: JDAnalysisState) -> Dict[str, Any]:
    """
    Node: Core Signals Extraction
    
    Extracts 2-3 core themes from lifecycle + spotlight stories + evidence.
    Updates state.core_signals and state.jd_summary.core_signals/core_narrative.
    
    [Quick Filter] Short-circuits if skip_deep_analysis=True.
    """
    node_name = "core_signals"
    started_at = datetime.utcnow().isoformat()
    start_time = time.perf_counter()
    
    # [Quick Filter] Short-circuit if skip_deep_analysis is True
    if state.get("skip_deep_analysis"):
        logger.info("Skipping core_signals: skip_deep_analysis=True (quick filter active)")
        finished_at = datetime.utcnow().isoformat()
        duration_ms = 0.0  # SKIPPED nodes don't need duration
        new_step = _create_graph_step(
            node_name, "skipped",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"skipped": "Quick filter: profile mismatch detected"}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append
    
    try:
        new_state = run_core_signals(state)
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Extract updated fields from new_state
        core_signals = new_state.get("core_signals", [])
        jd_summary = new_state.get("jd_summary")
        
        new_step = _create_graph_step(
            node_name, "completed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"signals_count": len(core_signals) if core_signals else 0}
        )
        
        return {
            "core_signals": core_signals,
            "jd_summary": jd_summary,
            "graph_steps": [new_step],  # Return only new step, reducer will append
        }
    except Exception as e:
        finished_at = datetime.utcnow().isoformat()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        new_step = _create_graph_step(
            node_name, "failed",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            extra_info={"error": str(e)[:200]}
        )
        return {"graph_steps": [new_step]}  # Return only new step, reducer will append


def build_jd_analysis_graph() -> StateGraph:
    """
    Build LangGraph for JD interpretation + fit analysis.
    
    Flow: check_constraints -> interpret_jd -> lifecycle_reflection -> spotlight_story -> core_signals -> evidence_align -> analyze_fit
    
    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(JDAnalysisState)
    
    # Add nodes
    graph.add_node("check_constraints", node_check_constraints)
    graph.add_node("interpret_jd", node_interpret_jd)
    graph.add_node("lifecycle_reflection", node_lifecycle_reflection)
    graph.add_node("spotlight_story", node_spotlight_story)
    graph.add_node("core_signals", node_core_signals)  # [Core Signals] 新增核心信号提取节点
    graph.add_node("evidence_align", node_attach_evidence)  # [Step 2] 新增证据对齐节点
    graph.add_node("analyze_fit", node_analyze_fit)
    
    # Set entry point
    graph.set_entry_point("check_constraints")
    
    # Add edges: linear flow (updated for Core Signals)
    graph.add_edge("check_constraints", "interpret_jd")
    graph.add_edge("interpret_jd", "lifecycle_reflection")
    graph.add_edge("lifecycle_reflection", "spotlight_story")
    graph.add_edge("spotlight_story", "core_signals")  # [Core Signals] 添加核心信号提取步骤
    graph.add_edge("core_signals", "evidence_align")  # [Core Signals] 更新流程顺序
    graph.add_edge("evidence_align", "analyze_fit")
    graph.add_edge("analyze_fit", END)
    
    return graph


def run_jd_analysis(
    jd_input: JobJDInput,
    candidate_profile: str | None = None,
    profile_id: str | None = None,
    job_url: str | None = None,
    job_title: str | None = None,
) -> Dict[str, Any]:
    """
    Helper function to run JD interpretation + fit analysis with caching support.
    
    This function:
    1. Checks cache before running analysis
    2. Runs LangGraph analysis if cache miss
    3. Saves result to cache after analysis
    
    Args:
        jd_input: JobJDInput instance
        candidate_profile: Optional candidate profile text
        profile_id: Optional profile identifier (e.g., "data_engineer_gcp", "llm_agent")
        job_url: Optional job posting URL (for cache storage)
        job_title: Optional job title (for cache storage, defaults to jd_input.title)
    
    Returns:
        Completed JDAnalysisState (as dict) with graph_steps populated
    """
    # ========================================
    # Cache Integration: Check cache before analysis
    # ========================================
    user_id = "local_demo_user"  # Simple constant for now
    full_jd_text = jd_input.description  # Use the full JD text for hashing
    cached_result = None
    cache_hit = False
    
    # Only check cache if we have valid JD text and profile_id
    if full_jd_text and profile_id:
        try:
            # Initialize DB (idempotent)
            init_db()
            
            # Compute hash for cache key
            jd_hash = compute_jd_hash(full_jd_text)
            
            # Try to get cached analysis
            cached_result = get_cached_analysis(
                user_id=user_id,
                profile_id=profile_id,
                jd_hash=jd_hash,
            )
            
            if cached_result:
                cache_hit = True
                logger.info(f"Cache HIT for job: {jd_input.title or 'Untitled'} (profile_id={profile_id}, jd_hash={jd_hash[:8]}...)")
            else:
                logger.info(f"Cache MISS for job: {jd_input.title or 'Untitled'} (profile_id={profile_id}, jd_hash={jd_hash[:8]}...)")
        except Exception as e:
            # Graceful degradation: if cache fails, continue with normal analysis
            logger.warning(f"Cache lookup failed: {e}, continuing with normal analysis")
    
    # If cache hit, use cached result; otherwise run analysis
    if cache_hit and cached_result:
        # Reconstruct result dict from cached analysis
        # cached_result should be the analysis_result dict saved by save_analysis
        result = cached_result
        logger.info("Using cached analysis result")
    else:
        # Run JD analysis graph
        logger.info(f"Running JD analysis for job: {jd_input.title or 'Untitled'} at {jd_input.company or 'Unknown'}")
        
        graph = build_jd_analysis_graph().compile()
        
        initial_state: JDAnalysisState = {
            "jd_input": jd_input,
            "candidate_profile": candidate_profile,
            "profile_id": profile_id,
            "graph_steps": [],  # Initialize graph_steps list
            "skip_deep_analysis": False,  # [Quick Filter] Initialize skip flag
        }
        
        if is_langsmith_enabled():
            config = default_langsmith_run_config("jobhunter_jd_analysis")
            result = graph.invoke(initial_state, config=config)
        else:
            result = graph.invoke(initial_state)
        
        # Ensure graph_steps is in result (convert GraphStep objects to dicts)
        # LangGraph merges state updates, so graph_steps should be accumulated from all nodes
        if "graph_steps" in result and result["graph_steps"]:
            # Convert GraphStep objects to dicts for JSON serialization
            graph_steps_list = []
            for step in result["graph_steps"]:
                if hasattr(step, "model_dump"):
                    graph_steps_list.append(step.model_dump())
                elif isinstance(step, dict):
                    graph_steps_list.append(step)
                else:
                    # Fallback: try to convert to dict
                    try:
                        graph_steps_list.append({
                            "name": getattr(step, "name", ""),
                            "status": getattr(step, "status", ""),
                            "started_at": getattr(step, "started_at", None),
                            "finished_at": getattr(step, "finished_at", None),
                            "duration_ms": getattr(step, "duration_ms", None),
                            "extra_info": getattr(step, "extra_info", None),
                        })
                    except Exception as e:
                        logger.warning(f"Failed to convert graph step to dict: {e}")
                        continue
            result["graph_steps"] = graph_steps_list
            logger.info(f"Collected {len(graph_steps_list)} graph steps")
        else:
            logger.warning("No graph_steps found in result")
            result["graph_steps"] = []
        
        # ========================================
        # Cache Integration: Save result after analysis
        # ========================================
        if full_jd_text and profile_id and not cache_hit:
            try:
                jd_hash = compute_jd_hash(full_jd_text)
                job_url_final = job_url or ""
                job_title_final = job_title or jd_input.title or ""
                
                # Prepare analysis_result dict with COMPLETE analysis results
                # Include all fields: jd_summary, fit_summary, constraints, lifecycle, spotlight_stories, core_signals, graph_steps
                # TODO: cache full analysis_json here - saving complete analysis result including Core Signals, Lifecycle, Story, etc.
                analysis_result = {
                    "jd_summary": result.get("jd_summary"),
                    "fit_summary": result.get("fit_summary"),
                    "constraints": result.get("constraints"),
                    "lifecycle": result.get("lifecycle"),
                    "spotlight_stories": result.get("spotlight_stories"),
                    "core_signals": result.get("core_signals"),
                    "graph_steps": result.get("graph_steps", []),
                }
                
                # Convert Pydantic models to dicts if needed (for JSON serialization)
                def convert_to_dict(obj):
                    """Helper to convert Pydantic models to dicts."""
                    if obj is None:
                        return None
                    if hasattr(obj, "model_dump"):
                        return obj.model_dump()
                    if isinstance(obj, list):
                        return [convert_to_dict(item) for item in obj]
                    if isinstance(obj, dict):
                        return {k: convert_to_dict(v) for k, v in obj.items()}
                    return obj
                
                # Convert all Pydantic models to dicts
                analysis_result["jd_summary"] = convert_to_dict(analysis_result["jd_summary"])
                analysis_result["fit_summary"] = convert_to_dict(analysis_result["fit_summary"])
                analysis_result["constraints"] = convert_to_dict(analysis_result["constraints"])
                analysis_result["lifecycle"] = convert_to_dict(analysis_result["lifecycle"])
                analysis_result["spotlight_stories"] = convert_to_dict(analysis_result["spotlight_stories"])
                analysis_result["core_signals"] = convert_to_dict(analysis_result["core_signals"])
                
                save_analysis(
                    user_id=user_id,
                    profile_id=profile_id,
                    job_url=job_url_final,
                    job_title=job_title_final,
                    jd_hash=jd_hash,
                    raw_text=full_jd_text,
                    analysis=analysis_result,
                )
                logger.info(f"Cached complete analysis result (profile_id={profile_id}, jd_hash={jd_hash[:8]}...)")
            except Exception as e:
                # Graceful degradation: if save fails, log warning but don't fail the request
                logger.warning(f"Failed to save analysis to cache: {e}")
    
    return result


if __name__ == "__main__":
    # 简单的 smoke test
    import sys
    from pathlib import Path
    
    # 添加项目根路径
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # 创建一个假的 JD 输入用于测试
    from services.fiqa_api.jobhunter.schemas import JobJDInput
    
    test_jd = JobJDInput(
        job_id="test_123",
        company="Test Company",
        title="Senior Engineer",
        location="Remote",
        description="We are looking for a senior engineer with experience in Python, GCP, and LLM systems.",
    )
    
    print("Testing Flow 1: JD Analysis Graph")
    print("=" * 60)
    
    result = run_jd_analysis(test_jd)
    
    print("\nResults:")
    print(f"- JD Summary: {result.get('jd_summary') is not None}")
    print(f"- Fit Summary: {result.get('fit_summary') is not None}")
    
    if result.get("jd_summary"):
        summary = result["jd_summary"]
        print(f"\nRecommendation: {summary.recommendation}")
        print(f"Gold points: {len(summary.gold_points)}")
        print(f"Core skills: {summary.core_skills}")