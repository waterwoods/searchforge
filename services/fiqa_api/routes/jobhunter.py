"""
jobhunter.py - JobHunter Agent Route Handler
=============================================
Handles /api/jobhunter/* endpoints for job description analysis and career coaching.
"""
# [health] inspected

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum

from services.fiqa_api.jobhunter.graphs.jd_analysis_graph import (
    run_jd_analysis,
    generate_quick_view_cn,
    generate_quick_view_from_raw,
    run_jd_quick_analysis,
    calculate_auto_skip,
)
from services.fiqa_api.jobhunter.graphs.jd_chat_graph import run_jd_chat_turn
from services.fiqa_api.jobhunter.jd_interpreter import batch_analyze_jd_clips, DEFAULT_MODEL
from services.fiqa_api.jobhunter.sqlite_cache import (
    list_cached_analyses,
    get_cached_analysis_by_id,
    get_user_resume,
    upsert_user_resume,
    upsert_job_application,
    get_job_application_by_cache_id,
    list_job_applications,
    delete_job_application,
    get_quick_view_for_cache_id,
    save_quick_view_for_cache_id,
    update_quick_view_cn,
    update_analysis_json,
    update_auto_skip_flags,
    get_cache_id_by_hash,
    compute_jd_hash,
)
from services.fiqa_api.jobhunter.schemas import (
    JobJDInput,
    JobJDSummary,
    JobHunterChatRequest,
    JobHunterChatResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
)
from services.fiqa_api.jobhunter.job_fit_analyzer import JobFitSummary
from services.fiqa_api.jobhunter.profile_loader import (
    load_candidate_profile,
    get_default_profile_path,
    get_profile_path_for_mode,
)
from services.fiqa_api.clients import get_openai_client

logger = logging.getLogger(__name__)

# ========================================
# Constants
# ========================================

# Temporary user_id constant (TODO: replace with real auth user id)
DEMO_USER_ID = "andy_local"

# ========================================
# Router Setup
# ========================================

router = APIRouter()

# ========================================
# Request/Response Models
# ========================================

class JDAnalyzeRequest(BaseModel):
    """Request model for JD analysis endpoint."""
    jd_input: dict = Field(..., description="JobJDInput fields: description (required), title, company, location, job_id")
    use_default_profile: bool = Field(False, description="Whether to use default candidate profile for fit analysis")
    profile_mode: Optional[str] = Field(
        default=None,
        description="Which candidate profile to use. e.g. 'agent' or 'data_eng'. If omitted, defaults to original agent profile."
    )


class JDAnalysisResponse(BaseModel):
    """Response model for JD analysis endpoint."""
    ok: bool
    jd_summary: Optional[dict] = None
    fit_summary: Optional[dict] = None
    constraints: Optional[dict] = None
    graph_steps: Optional[List[dict]] = None  # [Engineering View] Graph execution steps for debugging
    cn_fast_read: Optional[str] = None  # Optional Chinese fast-read summary generated from structured analysis
    error: Optional[str] = None


class CachedJDItem(BaseModel):
    """Single cached JD analysis item for list view."""
    id: int = Field(..., description="Cache record ID (primary key, used for detail API lookup)")
    job_url: str
    job_title: str
    match_score: Optional[float] = None
    category: Optional[str] = None
    recommendation: Optional[str] = None
    last_analyzed_at: Optional[str] = None
    auto_skip: bool = Field(default=False, description="Whether this job should be auto-skipped (Lv0 filter)")
    auto_skip_reasons: Optional[list[str]] = Field(default=None, description="List of reasons for auto-skip")


class CachedJDListResponse(BaseModel):
    """Response model for cached JD list endpoint."""
    items: List[CachedJDItem]
    total: int


class CachedJDDetail(BaseModel):
    """Detailed cached JD analysis item with full analysis results."""
    id: int = Field(..., description="Cache record ID (primary key)")
    profile_id: str = Field(..., description="Profile identifier (e.g., 'data_engineer_gcp')")
    job_url: Optional[str] = Field(None, description="Job posting URL")
    job_title: Optional[str] = Field(None, description="Job title")
    raw_text: Optional[str] = Field(None, description="Original JD text (for deep analysis trigger)")
    analysis: Dict[str, Any] = Field(..., description="Complete analysis JSON (includes core_signals, lifecycle, spotlight_stories, constraints, graph_steps, etc.)")
    created_at: Optional[str] = Field(None, description="ISO timestamp when record was created")
    updated_at: Optional[str] = Field(None, description="ISO timestamp when record was last updated")


class ResumePayload(BaseModel):
    """Request model for saving user resume."""
    profile_id: str = Field(..., description="Profile identifier (e.g., 'data_engineer_gcp')")
    resume_text: str = Field(..., description="Resume text content")


class ResumeResponse(BaseModel):
    """Response model for resume endpoints."""
    ok: bool
    profile_id: str
    resume_text: Optional[str] = None
    error: Optional[str] = None


class QuickViewRequest(BaseModel):
    """Request model for quick view endpoint."""
    cache_id: int


class QuickViewResponse(BaseModel):
    """Response model for quick view endpoint."""
    cache_id: int
    quick_view_cn: Optional[str] = None  # Legacy field: single string summary
    quick_view: Optional[Dict[str, Any]] = None  # New field: structured quick view (cn_overview, responsibilities, requirements, red_flags)
    error: Optional[str] = None


class AnalyzeCachedRequest(BaseModel):
    """Request model for analyze_cached endpoint."""
    cache_id: int = Field(..., description="JD analysis cache ID (from jd_analysis_cache.id)")
    profile_id: str = Field(..., description="Profile identifier (e.g., 'data_engineer_gcp')")


class AnalyzeCachedResponse(BaseModel):
    """Response model for analyze_cached endpoint."""
    cache_id: int
    ok: bool
    error: Optional[str] = None


class ApplicationStatus(str, Enum):
    """Application status enum."""
    planned = "planned"
    applied = "applied"
    interviewing = "interviewing"
    offer = "offer"
    rejected = "rejected"
    skipped = "skipped"


class JobApplicationUpsertRequest(BaseModel):
    """Request model for upserting job application."""
    profile_id: str = Field(..., description="Profile identifier (e.g., 'data_engineer_gcp')")
    cache_id: int = Field(..., description="JD analysis cache ID (from jd_analysis_cache.id)")
    status: ApplicationStatus = Field(..., description="Application status")
    notes: Optional[str] = Field(None, description="Optional notes")


class JobApplicationItem(BaseModel):
    """Single job application item."""
    id: int = Field(..., description="Application record ID")
    profile_id: str = Field(..., description="Profile identifier")
    cache_id: Optional[int] = Field(None, description="JD analysis cache ID")
    job_url: Optional[str] = Field(None, description="Job posting URL")
    job_title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    status: ApplicationStatus = Field(..., description="Application status")
    first_seen_at: Optional[str] = Field(None, description="ISO timestamp when first seen")
    applied_at: Optional[str] = Field(None, description="ISO timestamp when applied")
    last_updated_at: Optional[str] = Field(None, description="ISO timestamp when last updated")
    notes: Optional[str] = Field(None, description="Optional notes")


class JobApplicationListResponse(BaseModel):
    """Response model for listing job applications."""
    items: List[JobApplicationItem]
    total: int


ChatRole = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    """Single chat message in conversation."""
    role: ChatRole
    content: str


class CareerChatRequest(BaseModel):
    """Request model for career coach chat endpoint."""
    profile_id: str = Field(..., description="Profile identifier (e.g., 'data_engineer_gcp')")
    cache_id: int = Field(..., description="JD analysis cache ID (from jd_analysis_cache.id)")
    topic: Literal["resume_opt", "gap_analysis", "tech_question"] = Field(
        ..., description="Chat topic: 'resume_opt' for resume optimization, 'gap_analysis' for gap analysis, 'tech_question' for technical questions"
    )
    messages: List[ChatMessage] = Field(..., description="Conversation history, last one is user question")


class CareerChatResponse(BaseModel):
    """Response model for career coach chat endpoint."""
    ok: bool
    answer: str
    topic: str
    error: Optional[str] = None


class ResumeRefinementStep(str, Enum):
    """Resume refinement conversation step."""
    analyze_resume = "analyze_resume"  # Step 1: Request resume
    identify_optimization = "identify_optimization"  # Step 2: Cross-reference JD and resume
    provide_suggestions = "provide_suggestions"  # Step 3: Personalized suggestions
    offer_fine_tuning = "offer_fine_tuning"  # Step 4: Further review option
    summary_next_steps = "summary_next_steps"  # Step 5: Summary and next steps


class ResumeRefinementRequest(BaseModel):
    """Request model for resume refinement endpoint."""
    profile_id: str = Field(..., description="Profile identifier (e.g., 'data_engineer_gcp')")
    cache_id: int = Field(..., description="JD analysis cache ID (from jd_analysis_cache.id)")
    current_step: Optional[ResumeRefinementStep] = Field(
        None,
        description="Current step in the refinement flow. If None, starts from Step 1."
    )
    messages: List[ChatMessage] = Field(..., description="Conversation history, last one is user message")
    resume_text: Optional[str] = Field(
        None,
        description="Current resume text (optional, will be loaded from profile if not provided)"
    )


class ResumeRefinementResponse(BaseModel):
    """Response model for resume refinement endpoint."""
    ok: bool
    answer: str
    current_step: ResumeRefinementStep
    next_step: Optional[ResumeRefinementStep] = None
    is_complete: bool = Field(False, description="Whether the refinement flow is complete")
    suggestions: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured suggestions (only in provide_suggestions step)"
    )
    error: Optional[str] = None


# ========================================
# Route Handlers
# ========================================

@router.post("/jobhunter/analyze", response_model=JDAnalysisResponse)
async def analyze_jd(request: JDAnalyzeRequest) -> JDAnalysisResponse:
    """
    Analyze a job description and provide fit assessment.
    
    This endpoint:
    1. Interprets the job description (extracts gold/silver/bronze points, skills, risks)
    2. Analyzes how well it fits the candidate profile (if provided)
    
    Request body:
        jd_input: dict with fields:
            - description: str (required) - Full job description text
            - title: str (optional) - Job title
            - company: str (optional) - Company name
            - location: str (optional) - Job location
            - job_id: str (optional) - Job ID
        use_default_profile: bool (optional, default: false) - Use default candidate profile
    
    Returns:
        JDAnalysisResponse with:
            - ok: bool - Success status
            - jd_summary: dict - Job description summary (gold/silver/bronze points, skills, recommendation)
            - fit_summary: dict - Job fit analysis (strengths, gaps, recommendation, match_score, category)
            - error: str (optional) - Error message if ok=False
    
    Example request:
        {
            "jd_input": {
                "description": "We are looking for a senior engineer...",
                "title": "Senior Software Engineer",
                "company": "Anthropic",
                "location": "San Francisco, CA"
            },
            "use_default_profile": true
        }
    """
    try:
        # Parse jd_input into JobJDInput
        jd_input_data = request.jd_input
        
        # Extract candidate profile if needed
        candidate_profile = None
        profile_id = None
        if request.use_default_profile or request.profile_mode:
            try:
                # Priority: profile_mode takes precedence over use_default_profile
                if request.profile_mode:
                    profile_path = get_profile_path_for_mode(request.profile_mode)
                    candidate_profile = load_candidate_profile(profile_path)
                    # Map profile_mode to profile_id for fit analysis rules
                    if request.profile_mode == "data_eng":
                        profile_id = "data_engineer_gcp"
                    elif request.profile_mode == "agent":
                        profile_id = "llm_agent"
                else:
                    # Legacy behavior: use default profile (assumes agent profile)
                    candidate_profile = load_candidate_profile()
                    profile_id = "llm_agent"
            except Exception as e:
                logger.warning(f"Failed to load profile: {e}, continuing without profile")
        
        # Create JobJDInput
        jd_input = JobJDInput(
            description=jd_input_data.get("description", ""),
            title=jd_input_data.get("title"),
            company=jd_input_data.get("company"),
            location=jd_input_data.get("location"),
            job_id=jd_input_data.get("job_id"),
            candidate_profile=candidate_profile,
        )
        
        if not jd_input.description:
            raise ValueError("Job description is required")
        
        # Run JD analysis graph (with built-in cache support)
        # Cache logic is now in run_jd_analysis function
        logger.info(f"Running JD analysis for job: {jd_input.title or 'Untitled'} at {jd_input.company or 'Unknown'}")
        job_url = jd_input_data.get("job_url")  # Extract job_url from request if available
        job_title = jd_input_data.get("title") or jd_input.title  # Use title from request or jd_input
        result = run_jd_analysis(
            jd_input,
            candidate_profile=candidate_profile,
            profile_id=profile_id,
            job_url=job_url,
            job_title=job_title,
        )
        
        # Extract results
        jd_summary = result.get("jd_summary")
        fit_summary = result.get("fit_summary")
        constraints = result.get("constraints")
        graph_steps = result.get("graph_steps")  # [Engineering View] Graph execution steps
        
        # Convert to dict for response
        # Handle both Pydantic models (from LangGraph) and dicts (from cache)
        jd_summary_dict = None
        if jd_summary:
            if isinstance(jd_summary, dict):
                jd_summary_dict = jd_summary
            elif hasattr(jd_summary, "model_dump"):
                jd_summary_dict = jd_summary.model_dump()
            else:
                # Fallback: try to convert to dict
                jd_summary_dict = dict(jd_summary) if jd_summary else None
        
        constraints_dict = None
        if constraints:
            if isinstance(constraints, dict):
                constraints_dict = constraints
            elif hasattr(constraints, "model_dump"):
                constraints_dict = constraints.model_dump()
            else:
                constraints_dict = dict(constraints) if constraints else None
        
        fit_summary_dict = None
        if fit_summary:
            # Convert JobFitSummary to dict and add match_score/category for frontend compatibility
            if isinstance(fit_summary, dict):
                fit_dict = fit_summary.copy()
            elif hasattr(fit_summary, "model_dump"):
                fit_dict = fit_summary.model_dump()
            else:
                fit_dict = dict(fit_summary) if fit_summary else {}
            
            # [Quick Filter] Check if skip_deep_analysis is True (from constraints)
            skip_deep_analysis = False
            if constraints:
                if isinstance(constraints, dict):
                    skip_deep_analysis = constraints.get("skip_deep_analysis", False)
                elif hasattr(constraints, "skip_deep_analysis"):
                    skip_deep_analysis = constraints.skip_deep_analysis
            
            # [Quick Filter] If skip_deep_analysis is True, set match_score=1 and category="C"
            if skip_deep_analysis:
                match_score = 1
                category = "C"
            else:
                # Calculate match_score (1-10) based on strengths vs gaps
                # Simple heuristic: more strengths = higher score, more gaps = lower score
                # Handle both dict (from cache) and Pydantic model (from LangGraph)
                if isinstance(fit_summary, dict):
                    strengths = fit_summary.get("strengths", [])
                    gaps = fit_summary.get("gaps", [])
                    recommendation = fit_summary.get("recommendation_for_candidate", "SKIP")
                else:
                    strengths = fit_summary.strengths if hasattr(fit_summary, "strengths") else []
                    gaps = fit_summary.gaps if hasattr(fit_summary, "gaps") else []
                    recommendation = fit_summary.recommendation_for_candidate if hasattr(fit_summary, "recommendation_for_candidate") else "SKIP"
                
                strengths_count = len(strengths)
                gaps_count = len(gaps)
                
                # Base score from recommendation
                if recommendation == "APPLY":
                    base_score = 8
                elif recommendation == "MAYBE":
                    base_score = 5
                else:  # SKIP
                    base_score = 3
                
                # Adjust based on strengths/gaps ratio
                if strengths_count > 0 or gaps_count > 0:
                    ratio = strengths_count / max(strengths_count + gaps_count, 1)
                    match_score = int(base_score + (ratio - 0.5) * 4)  # Scale to 1-10
                    match_score = max(1, min(10, match_score))  # Clamp to 1-10
                else:
                    match_score = base_score
                
                # Map recommendation to category
                if recommendation == "APPLY":
                    category = "A"
                elif recommendation == "MAYBE":
                    category = "B"
                else:  # SKIP
                    category = "C"
            
            # Get recommendation if not already set
            if "recommendation" not in fit_dict and "recommendation_for_candidate" not in fit_dict:
                if isinstance(fit_summary, dict):
                    recommendation = fit_dict.get("recommendation") or fit_dict.get("recommendation_for_candidate", "SKIP")
                else:
                    recommendation = fit_summary.recommendation_for_candidate if hasattr(fit_summary, "recommendation_for_candidate") else "SKIP"
            else:
                recommendation = fit_dict.get("recommendation") or fit_dict.get("recommendation_for_candidate", "SKIP")
            
            # Add fields expected by frontend (only if not already present, e.g., from cache)
            if "match_score" not in fit_dict:
                fit_dict["match_score"] = match_score
            if "category" not in fit_dict:
                fit_dict["category"] = category
            if "recommendation" not in fit_dict:
                fit_dict["recommendation"] = recommendation
            
            # [Quick Filter] Build reasoning_summary from profile_mismatch_reasons if skip_deep_analysis
            if skip_deep_analysis and constraints:
                reasons = []
                if isinstance(constraints, dict):
                    reasons = constraints.get("profile_mismatch_reasons", []) or []
                elif hasattr(constraints, "profile_mismatch_reasons"):
                    reasons = constraints.profile_mismatch_reasons or []
                
                if reasons:
                    summary_reason = (
                        "This role appears to be primarily a sales/financial-advisory position, "
                        "which does not align with the selected profile."
                    )
                    summary_reason += " " + " ".join(reasons)
                    fit_dict["reasoning_summary"] = summary_reason
                else:
                    fit_dict["reasoning_summary"] = (
                        "This role appears to be primarily a sales/financial-advisory position, "
                        "which does not align with the selected profile."
                    )
            elif jd_summary:
                # Safely extract reasoning_summary from jd_summary if available
                if isinstance(jd_summary, dict):
                    fit_dict["reasoning_summary"] = jd_summary.get("reasoning_summary", "")
                elif hasattr(jd_summary, "reasoning_summary"):
                    fit_dict["reasoning_summary"] = jd_summary.reasoning_summary
                else:
                    fit_dict["reasoning_summary"] = ""
            elif fit_summary:
                # Check if fit_summary has reasoning_summary attribute (from quick filter)
                if isinstance(fit_summary, dict):
                    fit_dict["reasoning_summary"] = fit_summary.get("reasoning_summary", "")
                elif hasattr(fit_summary, "reasoning_summary"):
                    fit_dict["reasoning_summary"] = fit_summary.reasoning_summary
                else:
                    fit_dict["reasoning_summary"] = ""
            else:
                fit_dict["reasoning_summary"] = ""
            
            fit_summary_dict = fit_dict
        
        # Convert graph_steps to list of dicts (already dicts from run_jd_analysis)
        graph_steps_list = None
        if graph_steps:
            # Ensure graph_steps is a list
            if isinstance(graph_steps, list):
                graph_steps_list = graph_steps
            else:
                logger.warning(f"graph_steps is not a list: {type(graph_steps)}")
                graph_steps_list = []
        else:
            logger.debug("No graph_steps in result")
            graph_steps_list = []
        
        # Log debug info about core_signals
        if jd_summary_dict and "core_signals" in jd_summary_dict:
            logger.info(f"jd_summary contains core_signals: {len(jd_summary_dict.get('core_signals', []))} signals")
        else:
            logger.debug("jd_summary does not contain core_signals or jd_summary_dict is None")
        
        return JDAnalysisResponse(
            ok=True,
            jd_summary=jd_summary_dict,
            fit_summary=fit_summary_dict,
            constraints=constraints_dict,
            graph_steps=graph_steps_list,  # [Engineering View] Graph execution steps
            cn_fast_read=result.get("cn_fast_read"),
        )
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        return JDAnalysisResponse(
            ok=False,
            error=str(e),
        )
    except Exception as e:
        logger.exception(f"Error analyzing JD: {e}")
        return JDAnalysisResponse(
            ok=False,
            error=f"Internal server error: {str(e)}",
        )


@router.post("/jobhunter/chat", response_model=JobHunterChatResponse)
async def chat_with_jobhunter(request: JobHunterChatRequest) -> JobHunterChatResponse:
    """
    Chat with the JobHunter career coach about a job description.
    
    This endpoint provides multi-turn conversational support based on JD analysis
    and fit assessment. Users can ask questions about the job, their fit, resume
    improvements, interview preparation, etc.
    
    Request body:
        jd_summary: JobJDSummary - Job description summary from Flow1 (required)
        fit_summary: JobFitSummary (optional) - Job fit analysis result
        messages: List[ChatMessage] - Chat history, last one is user question
        use_default_profile: bool (default: true) - Use default candidate profile
        profile_text: str (optional) - Custom candidate profile text
    
    Returns:
        JobHunterChatResponse with:
            - reply: str - Assistant's reply
            - messages: List[ChatMessage] - Updated complete chat history
    
    Example request:
        {
            "jd_summary": { ... },
            "fit_summary": { ... },
            "messages": [
                {"role": "user", "content": "这个工作适不适合我？"}
            ],
            "use_default_profile": true
        }
    """
    try:
        # Validate that we have messages
        if not request.messages:
            raise ValueError("Messages list cannot be empty")
        
        # Validate that last message is from user
        last_msg = request.messages[-1]
        if last_msg.role != "user":
            raise ValueError("Last message in history must be from user")
        
        # Ensure jd_summary is a JobJDSummary object (it should be from Pydantic, but double-check)
        jd_summary_obj = request.jd_summary
        if isinstance(jd_summary_obj, dict):
            jd_summary_obj = JobJDSummary(**jd_summary_obj)
        
        # Load profile
        profile_text: Optional[str] = request.profile_text
        if not profile_text and (request.use_default_profile or request.profile_mode):
            try:
                # Priority: profile_mode takes precedence over use_default_profile
                if request.profile_mode:
                    profile_path = get_profile_path_for_mode(request.profile_mode)
                    profile_text = load_candidate_profile(profile_path)
                else:
                    # Legacy behavior: use default profile
                    profile_path = get_default_profile_path()
                    profile_text = load_candidate_profile(profile_path)
            except Exception as e:
                logger.warning(f"Failed to load profile: {e}, continuing without profile")
                profile_text = None
        
        # Convert fit_summary dict to JobFitSummary if needed
        fit_summary_obj = request.fit_summary
        if fit_summary_obj is not None and isinstance(fit_summary_obj, dict):
            # Try to reconstruct JobFitSummary from dict
            try:
                fit_summary_obj = JobFitSummary(**fit_summary_obj)
            except Exception as e:
                logger.warning(f"Failed to parse fit_summary: {e}, using as-is")
        
        # Call LangGraph flow (run in thread pool since it's synchronous)
        new_messages = await asyncio.to_thread(
            run_jd_chat_turn,
            jd_summary_obj,
            fit_summary_obj,
            request.messages,
            profile_text,
        )
        
        # Extract reply from last message (should be assistant)
        reply = new_messages[-1].content if new_messages else "抱歉，无法生成回答。"
        
        return JobHunterChatResponse(
            reply=reply,
            messages=new_messages,
        )
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/jobhunter/cache", response_model=CachedJDListResponse)
async def get_cached_analyses(
    profile_id: Optional[str] = Query(None, description="Filter by profile ID (e.g., 'data_engineer_gcp')"),
    limit: int = Query(20, ge=1, le=200, description="Maximum number of results to return"),
    order: Literal["asc", "desc"] = Query("desc", description="Sort order by last_analyzed_at ('desc' for newest first)"),
) -> CachedJDListResponse:
    """
    Get list of cached JD analysis results.
    
    This endpoint returns previously analyzed job descriptions from the cache,
    allowing frontend to display a "Top Jobs" list without re-running LLM analysis.
    
    Query parameters:
        profile_id: Optional profile identifier to filter by (e.g., 'data_engineer_gcp', 'llm_agent')
        limit: Maximum number of results (1-200, default: 20)
        order: Sort order ('desc' for newest first, 'asc' for oldest first, default: 'desc')
    
    Returns:
        CachedJDListResponse with:
            - items: List[CachedJDItem] - List of cached JD analyses
            - total: int - Total number of items returned
    
    Each CachedJDItem contains:
        - job_url: str - Job posting URL
        - job_title: str - Job title
        - match_score: Optional[float] - Match score (1-10)
        - category: Optional[str] - Category ('A', 'B', or 'C')
        - recommendation: Optional[str] - Recommendation ('APPLY', 'MAYBE', or 'SKIP')
        - last_analyzed_at: Optional[str] - ISO timestamp when analysis was last updated
    
    Example request:
        GET /api/jobhunter/cache?profile_id=data_engineer_gcp&limit=10&order=desc
    
    Example curl:
        curl "http://localhost:8000/api/jobhunter/cache?profile_id=data_engineer_gcp&limit=10"
    """
    try:
        # Use fixed user_id for now (will be replaced with real user authentication later)
        # Note: Use DEMO_USER_ID to match existing data in database
        user_id = DEMO_USER_ID
        
        # Call list_cached_analyses function
        results = list_cached_analyses(
            user_id=user_id,
            profile_id=profile_id,
            limit=limit,
            order=order,
        )
        
        # Convert results to CachedJDItem list
        items = []
        for result in results:
            # Safely extract fields from analysis dict
            analysis = result.get("analysis", {})
            fit_summary = analysis.get("fit_summary", {})
            constraints = analysis.get("constraints", {})
            
            # Check if skip_deep_analysis is True (from constraints)
            skip_deep_analysis = False
            if isinstance(constraints, dict):
                skip_deep_analysis = constraints.get("skip_deep_analysis", False)
            
            # Calculate match_score and category (same logic as in analyze_jd endpoint)
            match_score = None
            category = None
            recommendation = None
            
            if isinstance(fit_summary, dict):
                # Extract recommendation first
                recommendation = fit_summary.get("recommendation") or fit_summary.get("recommendation_for_candidate", "SKIP")
                
                # If skip_deep_analysis is True, set match_score=1 and category="C"
                if skip_deep_analysis:
                    match_score = 1
                    category = "C"
                else:
                    # Calculate match_score (1-10) based on strengths vs gaps
                    strengths = fit_summary.get("strengths", [])
                    gaps = fit_summary.get("gaps", [])
                    
                    strengths_count = len(strengths)
                    gaps_count = len(gaps)
                    
                    # Base score from recommendation
                    if recommendation == "APPLY":
                        base_score = 8
                    elif recommendation == "MAYBE":
                        base_score = 5
                    else:  # SKIP
                        base_score = 3
                    
                    # Adjust based on strengths/gaps ratio
                    if strengths_count > 0 or gaps_count > 0:
                        ratio = strengths_count / max(strengths_count + gaps_count, 1)
                        match_score = int(base_score + (ratio - 0.5) * 4)  # Scale to 1-10
                        match_score = max(1, min(10, match_score))  # Clamp to 1-10
                    else:
                        match_score = base_score
                    
                    # Map recommendation to category
                    if recommendation == "APPLY":
                        category = "A"
                    elif recommendation == "MAYBE":
                        category = "B"
                    else:  # SKIP
                        category = "C"
            
            # Get id, job_url and job_title from result
            cache_id = result.get("id")
            job_url = result.get("job_url") or ""
            job_title = result.get("job_title") or ""
            last_analyzed_at = result.get("last_analyzed_at")
            auto_skip = result.get("auto_skip", False)
            auto_skip_reasons = result.get("auto_skip_reasons")
            
            item = CachedJDItem(
                id=cache_id,
                job_url=job_url,
                job_title=job_title,
                match_score=match_score,
                category=category,
                recommendation=recommendation,
                last_analyzed_at=last_analyzed_at,
                auto_skip=auto_skip,
                auto_skip_reasons=auto_skip_reasons,
            )
            items.append(item)
        
        logger.info(f"Returned {len(items)} cached analyses for user_id={user_id}, profile_id={profile_id}")
        
        return CachedJDListResponse(
            items=items,
            total=len(items),
        )
        
    except Exception as e:
        logger.exception(f"Error listing cached analyses: {e}")
        # Return empty list on error (graceful degradation)
        return CachedJDListResponse(
            items=[],
            total=0,
        )


@router.get("/jobhunter/cache/{cache_id}", response_model=CachedJDDetail)
async def get_cached_analysis_detail(cache_id: int) -> CachedJDDetail:
    """
    Get detailed cached JD analysis by cache ID.
    
    This endpoint returns the complete analysis result for a single cached JD,
    including full analysis_json with core_signals, lifecycle, spotlight_stories,
    constraints, graph_steps, etc.
    
    Path parameters:
        cache_id: int - Cache record ID (primary key from jd_analysis_cache table)
    
    Returns:
        CachedJDDetail with:
            - id: int - Cache record ID
            - profile_id: str - Profile identifier
            - job_url: Optional[str] - Job posting URL
            - job_title: Optional[str] - Job title
            - analysis: dict - Complete analysis JSON (includes all fields from analysis_json)
            - created_at: Optional[str] - ISO timestamp when record was created
            - updated_at: Optional[str] - ISO timestamp when record was last updated
    
    Raises:
        HTTPException 404: If cache item not found
    
    Example request:
        GET /api/jobhunter/cache/123
    
    Example curl:
        curl "http://localhost:8000/api/jobhunter/cache/123"
    """
    try:
        # Call get_cached_analysis_by_id function
        result = get_cached_analysis_by_id(cache_id)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Cache item not found for id={cache_id}"
            )
        
        # Extract fields from result
        # analysis_dict is already deserialized in get_cached_analysis_by_id
        analysis_dict = result.get("analysis", {})
        
        # Calculate match_score and category for fit_summary if not present (same logic as analyze_jd endpoint)
        fit_summary = analysis_dict.get("fit_summary", {})
        constraints = analysis_dict.get("constraints", {})
        
        if isinstance(fit_summary, dict) and fit_summary:
            # Check if match_score already exists, if not, calculate it
            if "match_score" not in fit_summary or fit_summary.get("match_score") is None:
                # [Quick Filter] Check if skip_deep_analysis is True
                skip_deep_analysis = False
                if isinstance(constraints, dict):
                    skip_deep_analysis = constraints.get("skip_deep_analysis", False)
                
                # If skip_deep_analysis is True, set match_score=1 and category="C"
                if skip_deep_analysis:
                    match_score = 1
                    category = "C"
                else:
                    # Calculate match_score (1-10) based on strengths vs gaps
                    strengths = fit_summary.get("strengths", [])
                    gaps = fit_summary.get("gaps", [])
                    recommendation = fit_summary.get("recommendation") or fit_summary.get("recommendation_for_candidate", "SKIP")
                    
                    strengths_count = len(strengths)
                    gaps_count = len(gaps)
                    
                    # Base score from recommendation
                    if recommendation == "APPLY":
                        base_score = 8
                    elif recommendation == "MAYBE":
                        base_score = 5
                    else:  # SKIP
                        base_score = 3
                    
                    # Adjust based on strengths/gaps ratio
                    if strengths_count > 0 or gaps_count > 0:
                        ratio = strengths_count / max(strengths_count + gaps_count, 1)
                        match_score = int(base_score + (ratio - 0.5) * 4)  # Scale to 1-10
                        match_score = max(1, min(10, match_score))  # Clamp to 1-10
                    else:
                        match_score = base_score
                    
                    # Map recommendation to category
                    if recommendation == "APPLY":
                        category = "A"
                    elif recommendation == "MAYBE":
                        category = "B"
                    else:  # SKIP
                        category = "C"
                
                # Update fit_summary with calculated values
                fit_summary["match_score"] = match_score
                if "category" not in fit_summary or fit_summary.get("category") is None:
                    fit_summary["category"] = category
                if "recommendation" not in fit_summary:
                    fit_summary["recommendation"] = fit_summary.get("recommendation_for_candidate", "SKIP")
        
        return CachedJDDetail(
            id=result["id"],
            profile_id=result["profile_id"],
            job_url=result.get("job_url"),
            job_title=result.get("job_title"),
            raw_text=result.get("raw_text"),  # Include raw_text for deep analysis trigger
            analysis=analysis_dict,
            created_at=result.get("created_at"),
            updated_at=result.get("updated_at"),
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.exception(f"Error getting cached analysis detail for id={cache_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/jobhunter/batch_analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze_jobhunter(req: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
    """
    Analyze multiple clipped JDs in one shot.
    
    Intended input is the JSON exported by the JobHunter Clipper Chrome extension.
    
    This endpoint:
    1. Deduplicates clips by (url, title)
    2. Cleans JD text from LinkedIn/chrome noise
    3. Runs full JD analysis for each clip (using existing LangGraph pipeline)
    4. Returns scored list of jobs with match scores, categories, and recommendations
    
    Request body:
        version: int (optional, default: 1) - Export format version
        exported_at: str (optional) - ISO timestamp when export was created
        clips: List[BatchJobClipIn] - List of job clips to analyze
        profile_id: str (optional) - Profile identifier (e.g., 'data_engineer_gcp', 'llm_agent')
        max_jobs: int (optional, default: 30) - Safety limit on number of jobs to analyze
    
    Returns:
        BatchAnalyzeResponse with:
            - total_clips: int - Total number of clips in input
            - analyzed_jobs: int - Number of jobs analyzed (including quick-filtered)
            - skipped_jobs: int - Number of jobs skipped (too short, invalid, etc.)
            - results: List[BatchJobResult] - Analysis results for each job
    
    Example request:
        {
            "version": 1,
            "exported_at": "2025-12-16T23:30:43.114Z",
            "clips": [
                {
                    "id": "...",
                    "url": "...",
                    "title": "...",
                    "clippedAt": "...",
                    "source": "manual-clip-v1",
                    "text": "full flattened JD text..."
                }
            ],
            "profile_id": "data_engineer_gcp",
            "max_jobs": 30
        }
    """
    try:
        return await batch_analyze_jd_clips(req)
    except Exception as e:
        logger.exception(f"Error in batch_analyze endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/jobhunter/profile/resume", response_model=ResumeResponse)
async def get_resume(
    profile_id: str = Query(..., description="Profile identifier (e.g., 'data_engineer_gcp')"),
) -> ResumeResponse:
    """
    Get user resume text by profile_id.
    
    Query parameters:
        profile_id: Profile identifier (e.g., 'data_engineer_gcp')
    
    Returns:
        ResumeResponse with:
            - ok: bool - Success status
            - profile_id: str - Profile identifier
            - resume_text: Optional[str] - Resume text if found, None if not found
            - error: Optional[str] - Error message if ok=False
    
    Example request:
        GET /api/jobhunter/profile/resume?profile_id=data_engineer_gcp
    
    Example curl:
        curl "http://localhost:8000/api/jobhunter/profile/resume?profile_id=data_engineer_gcp"
    """
    try:
        resume_text = get_user_resume(DEMO_USER_ID, profile_id)
        
        # If resume_text is None, return ok=True with resume_text=None (not an error)
        return ResumeResponse(
            ok=True,
            profile_id=profile_id,
            resume_text=resume_text,
        )
        
    except Exception as e:
        logger.exception(f"Error getting resume for profile_id={profile_id}: {e}")
        return ResumeResponse(
            ok=False,
            profile_id=profile_id,
            error=f"Internal server error: {str(e)}",
        )


@router.post("/jobhunter/profile/resume", response_model=ResumeResponse)
async def save_resume(payload: ResumePayload) -> ResumeResponse:
    """
    Save or update user resume text.
    
    Request body:
        profile_id: str - Profile identifier (e.g., 'data_engineer_gcp')
        resume_text: str - Resume text content
    
    Returns:
        ResumeResponse with:
            - ok: bool - Success status
            - profile_id: str - Profile identifier
            - resume_text: str - Saved resume text
            - error: Optional[str] - Error message if ok=False
    
    Example request:
        POST /api/jobhunter/profile/resume
        {
            "profile_id": "data_engineer_gcp",
            "resume_text": "Full resume text here..."
        }
    
    Example curl:
        curl -X POST "http://localhost:8000/api/jobhunter/profile/resume" \
             -H "Content-Type: application/json" \
             -d '{"profile_id": "data_engineer_gcp", "resume_text": "Resume content..."}'
    """
    try:
        upsert_user_resume(DEMO_USER_ID, payload.profile_id, payload.resume_text)
        
        return ResumeResponse(
            ok=True,
            profile_id=payload.profile_id,
            resume_text=payload.resume_text,
        )
        
    except Exception as e:
        logger.exception(f"Error saving resume for profile_id={payload.profile_id}: {e}")
        return ResumeResponse(
            ok=False,
            profile_id=payload.profile_id,
            error=f"Internal server error: {str(e)}",
        )


@router.post("/jobhunter/applications", response_model=JobApplicationItem)
async def upsert_application(request: JobApplicationUpsertRequest) -> JobApplicationItem:
    """
    Create or update a job application record.
    
    This endpoint allows marking/updating the status of a job application
    (planned, applied, interviewing, offer, rejected, skipped).
    
    Request body:
        profile_id: str - Profile identifier (e.g., 'data_engineer_gcp')
        cache_id: int - JD analysis cache ID (from jd_analysis_cache.id)
        status: ApplicationStatus - Application status
        notes: Optional[str] - Optional notes
    
    Returns:
        JobApplicationItem with complete application record
    
    Raises:
        HTTPException 404: If cache_id not found
        HTTPException 500: On internal error
    
    Example request:
        POST /api/jobhunter/applications
        {
            "profile_id": "data_engineer_gcp",
            "cache_id": 3,
            "status": "applied",
            "notes": "Applied via LinkedIn on 2025-12-19"
        }
    
    Example curl:
        curl -X POST "http://localhost:8000/api/jobhunter/applications" \
             -H "Content-Type: application/json" \
             -d '{"profile_id": "data_engineer_gcp", "cache_id": 3, "status": "applied", "notes": "Applied via LinkedIn"}'
    """
    try:
        user_id = DEMO_USER_ID
        
        # Get cached analysis to extract job_url, job_title, and company
        cached_analysis = get_cached_analysis_by_id(request.cache_id)
        if cached_analysis is None:
            raise HTTPException(
                status_code=404,
                detail=f"Cache item not found for cache_id={request.cache_id}"
            )
        
        # Extract job information from cached analysis
        job_url = cached_analysis.get("job_url")
        job_title = cached_analysis.get("job_title")
        
        # Try to extract company from job_title (format: "Job Title | Company Name")
        company = None
        if job_title:
            # Simple parsing: split by '|' and take the last part as company
            parts = job_title.split('|')
            if len(parts) > 1:
                company = parts[-1].strip()
                # Update job_title to remove company part
                job_title = '|'.join(parts[:-1]).strip()
        
        # If company is still None, try to get from analysis.jd_summary
        if company is None:
            analysis = cached_analysis.get("analysis", {})
            jd_summary = analysis.get("jd_summary", {})
            if isinstance(jd_summary, dict):
                company = jd_summary.get("company")
        
        # Upsert job application
        upsert_job_application(
            user_id=user_id,
            profile_id=request.profile_id,
            cache_id=request.cache_id,
            job_url=job_url,
            job_title=job_title,
            company=company,
            status=request.status.value,
            notes=request.notes,
        )
        
        # Get the updated record
        application = get_job_application_by_cache_id(
            user_id=user_id,
            profile_id=request.profile_id,
            cache_id=request.cache_id,
        )
        
        if application is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve application record after upsert. The record may not have been saved correctly."
            )
        
        # Convert to JobApplicationItem
        return JobApplicationItem(
            id=application["id"],
            profile_id=application["profile_id"],
            cache_id=application["cache_id"],
            job_url=application["job_url"],
            job_title=application["job_title"],
            company=application["company"],
            status=ApplicationStatus(application["status"]),
            first_seen_at=application["first_seen_at"],
            applied_at=application["applied_at"],
            last_updated_at=application["last_updated_at"],
            notes=application["notes"],
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error upserting application: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/jobhunter/applications", response_model=JobApplicationListResponse)
async def list_applications(
    profile_id: Optional[str] = Query(None, description="Filter by profile ID (e.g., 'data_engineer_gcp')"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by application status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> JobApplicationListResponse:
    """
    List job application records.
    
    This endpoint returns a list of job applications, optionally filtered by
    profile_id and status.
    
    Query parameters:
        profile_id: Optional profile identifier to filter by (e.g., 'data_engineer_gcp')
        status: Optional application status to filter by
        limit: Maximum number of results (1-500, default: 100)
        offset: Number of results to skip (default: 0)
    
    Returns:
        JobApplicationListResponse with:
            - items: List[JobApplicationItem] - List of application records
            - total: int - Total number of items returned
    
    Example request:
        GET /api/jobhunter/applications?profile_id=data_engineer_gcp&status=applied
    
    Example curl:
        curl "http://localhost:8000/api/jobhunter/applications?profile_id=data_engineer_gcp"
    """
    try:
        user_id = DEMO_USER_ID
        
        # Convert ApplicationStatus enum to string if provided
        status_str = status.value if status else None
        
        # Get list of applications
        applications = list_job_applications(
            user_id=user_id,
            profile_id=profile_id,
            status=status_str,
            limit=limit,
            offset=offset,
        )
        
        # Convert to JobApplicationItem list
        items = []
        for app in applications:
            item = JobApplicationItem(
                id=app["id"],
                profile_id=app["profile_id"],
                cache_id=app["cache_id"],
                job_url=app["job_url"],
                job_title=app["job_title"],
                company=app["company"],
                status=ApplicationStatus(app["status"]),
                first_seen_at=app["first_seen_at"],
                applied_at=app["applied_at"],
                last_updated_at=app["last_updated_at"],
                notes=app["notes"],
            )
            items.append(item)
        
        logger.info(f"Returned {len(items)} applications for user_id={user_id}, profile_id={profile_id}, status={status_str}")
        
        return JobApplicationListResponse(
            items=items,
            total=len(items),
        )
        
    except Exception as e:
        logger.exception(f"Error listing applications: {e}")
        # Return empty list on error (graceful degradation)
        return JobApplicationListResponse(
            items=[],
            total=0,
        )


@router.delete("/jobhunter/applications", response_model=Dict[str, Any])
async def delete_application(
    profile_id: str = Query(..., description="Profile identifier (e.g., 'data_engineer_gcp')"),
    cache_id: int = Query(..., description="JD analysis cache ID (from jd_analysis_cache.id)"),
) -> Dict[str, Any]:
    """
    Delete a job application record.
    
    This endpoint allows removing the application status for a job posting,
    effectively marking it as "not applied" or removing the application record.
    
    Query parameters:
        profile_id: Profile identifier (e.g., 'data_engineer_gcp')
        cache_id: JD analysis cache ID (primary key from jd_analysis_cache table)
    
    Returns:
        Dict with:
            - ok: bool - Success status
            - deleted: bool - Whether a record was actually deleted
    
    Raises:
        HTTPException 500: On internal error
    
    Example request:
        DELETE /api/jobhunter/applications?profile_id=data_engineer_gcp&cache_id=3
    
    Example curl:
        curl -X DELETE "http://localhost:8000/api/jobhunter/applications?profile_id=data_engineer_gcp&cache_id=3"
    """
    try:
        user_id = DEMO_USER_ID
        
        deleted = delete_job_application(
            user_id=user_id,
            profile_id=profile_id,
            cache_id=cache_id,
        )
        
        return {
            "ok": True,
            "deleted": deleted,
        }
        
    except Exception as e:
        logger.exception(f"Error deleting application: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ========================================
# Career Chat Helper Functions
# ========================================

def build_career_chat_context(
    user_id: str,
    profile_id: str,
    cache_id: Optional[int],
    topic: str,
    messages: List[ChatMessage],
) -> Dict[str, Any]:
    """
    Build comprehensive context for career chat from JD analysis, resume, and conversation history.
    
    Args:
        user_id: User identifier (e.g., "andy_local")
        profile_id: Profile identifier (e.g., "data_engineer_gcp")
        cache_id: JD analysis cache ID (primary key)
        topic: Chat topic ("resume_opt", "gap_analysis", "tech_question")
        messages: Conversation history (List[ChatMessage])
    
    Returns:
        Dict containing:
            - profile_id: str
            - cache_id: Optional[int]
            - job_title: Optional[str]
            - job_url: Optional[str]
            - analysis: dict with jd_summary, fit_summary, constraints, lifecycle, spotlight_stories, core_signals, cn_fast_read
            - resume_text: Optional[str]
            - recent_messages: List[dict] (last 6 messages, simplified format)
            - topic: str
    """
    context = {
        "profile_id": profile_id,
        "cache_id": cache_id,
        "job_title": None,
        "job_url": None,
        "analysis": {
            "jd_summary": None,
            "fit_summary": None,
            "constraints": None,
            "lifecycle": None,
            "spotlight_stories": None,
            "core_signals": None,
            "cn_fast_read": None,
        },
        "resume_text": None,
        "recent_messages": [],
        "topic": topic,
    }
    
    # Step 1: Get JD analysis from cache (if cache_id exists)
    if cache_id is not None:
        try:
            analysis_result = get_cached_analysis_by_id(cache_id)
            if analysis_result:
                context["job_title"] = analysis_result.get("job_title")
                context["job_url"] = analysis_result.get("job_url")
                
                analysis_dict = analysis_result.get("analysis", {})
                if analysis_dict:
                    context["analysis"]["jd_summary"] = analysis_dict.get("jd_summary")
                    context["analysis"]["fit_summary"] = analysis_dict.get("fit_summary")
                    context["analysis"]["constraints"] = analysis_dict.get("constraints")
                    context["analysis"]["lifecycle"] = analysis_dict.get("lifecycle")
                    context["analysis"]["spotlight_stories"] = analysis_dict.get("spotlight_stories")
                    context["analysis"]["core_signals"] = analysis_dict.get("core_signals")
                    context["analysis"]["cn_fast_read"] = analysis_dict.get("cn_fast_read")
        except Exception as e:
            logger.warning(f"Failed to get cached analysis for cache_id={cache_id}: {e}")
    
    # Step 2: Get user resume
    try:
        resume_text = get_user_resume(user_id, profile_id)
        context["resume_text"] = resume_text
    except Exception as e:
        logger.warning(f"Failed to get user resume for user_id={user_id}, profile_id={profile_id}: {e}")
    
    # Step 3: Extract recent messages (last 6, including user and assistant)
    recent_messages = messages[-6:] if len(messages) > 6 else messages
    context["recent_messages"] = [
        {"role": msg.role, "content": msg.content}
        for msg in recent_messages
    ]
    
    return context


def build_career_chat_prompts(topic: str, context: Dict[str, Any]) -> Tuple[str, str]:
    """
    Build system prompt and user prompt for career chat based on topic and context.
    
    Args:
        topic: Chat topic ("resume_opt", "gap_analysis", "tech_question")
        context: Context dict from build_career_chat_context
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    analysis = context.get("analysis", {})
    jd_summary = analysis.get("jd_summary") or {}
    fit_summary = analysis.get("fit_summary") or {}
    constraints = analysis.get("constraints") or {}
    lifecycle = analysis.get("lifecycle") or {}
    spotlight_stories = analysis.get("spotlight_stories") or []
    core_signals = analysis.get("core_signals") or []
    cn_fast_read = analysis.get("cn_fast_read") or ""
    
    resume_text = context.get("resume_text")
    job_title = context.get("job_title") or ""
    job_url = context.get("job_url") or ""
    recent_messages = context.get("recent_messages", [])
    
    # Common system prompt base (shared across all topics)
    common_base = (
        "你是一名专业的职业教练和简历优化顾问，面向数据工程 / LLM / 平台工程类候选人。\n"
        "你必须结合以下信息进行分析和回答：\n"
        "- 当前 JD 的分析结果（jd_summary、core_signals、lifecycle、fit_summary、constraints）\n"
        "- 中文速读 cn_fast_read（如果有）\n"
        "- 候选人的简历文本 resume_text\n\n"
        "输出要求：\n"
        "- 使用条理清晰的 bullet points 或编号列表\n"
        "- 每一点尽量 1-2 句，简洁明了\n"
        "- 不要编造不存在于 JD / 简历里的公司名、技术栈\n"
        "- 基于已有信息给出具体、可执行的建议\n"
    )
    
    # Topic-specific system prompt extensions
    if topic == "resume_opt":
        topic_specific = (
            "\n【简历优化模式】\n"
            "你的任务是分析「这个工作要什么」 VS 「简历已经写了什么」，提供针对性的简历优化建议。\n\n"
            "输出格式（必须包含以下三部分）：\n"
            "1. 【可直接加入简历的新 bullet（英文）】\n"
            "   - 列出 3-5 条可以直接添加到简历中的新 bullet points（英文格式）\n"
            "   - 每条应该突出匹配 JD 的核心技能或经验\n"
            "   - 格式示例：\"• Built scalable data pipelines using Airflow and GCP, processing 10TB+ daily\"\n\n"
            "2. 【现有简历可精简/删除的点】\n"
            "   - 列出 2-3 条现有简历中可以精简或删除的内容\n"
            "   - 说明为什么这些内容对当前职位不太重要\n\n"
            "3. 【简历整体结构调整建议】\n"
            "   - 给出 2-3 条关于简历结构、顺序、重点突出的建议\n"
            "   - 帮助候选人更好地展示与职位匹配的经验"
        )
        system_prompt = common_base + topic_specific
    elif topic == "gap_analysis":
        topic_specific = (
            "\n【能力缺口分析模式】\n"
            "你的任务是客观分析候选人与目标职位的关键差距，并提供现实可行的补救建议。\n\n"
            "输出格式（必须包含以下三部分）：\n"
            "1. 【匹配度高的点】\n"
            "   - 列出 3-5 条候选人与职位要求匹配度高的方面\n"
            "   - 说明这些优势如何帮助候选人胜任该职位\n\n"
            "2. 【明显缺口（技能/经验）】\n"
            "   - 列出 3-5 条候选人与职位要求存在明显缺口的地方\n"
            "   - 每个缺口要具体说明缺少什么技能或经验\n\n"
            "3. 【最现实的补救方式】\n"
            "   - 针对每个缺口，给出 1 句最现实的补救方式\n"
            "   - 建议形式：项目实践 / 自学路线 / side project / 在线课程等\n"
            "   - 优先推荐可以在 1-3 个月内见效的方式"
        )
        system_prompt = common_base + topic_specific
    else:  # tech_question
        topic_specific = (
            "\n【技术问题辅导模式】\n"
            "你的任务是把用户的技术问题当成「面试辅导」，结合 JD 的技术栈要求给出专业回答。\n\n"
            "输出要求：\n"
            "1. 给清晰、简短的技术解释（1-2 段）\n"
            "2. 指出「和这个职位最相关的使用场景」\n"
            "3. 如有必要，给 1-2 个针对该职位的手写小例子或学习路线\n"
            "4. 如果问题与 JD 技术栈相关，重点说明在该职位中的实际应用"
        )
        system_prompt = common_base + topic_specific
    
    # Build user prompt
    user_prompt_parts = []
    
    # Add job title and cn_fast_read
    if job_title:
        user_prompt_parts.append(f"目标职位：{job_title}")
    if job_url:
        user_prompt_parts.append(f"职位链接：{job_url}")
    if cn_fast_read:
        user_prompt_parts.append(f"\n【中文速读】\n{cn_fast_read}")
    
    # Add resume text (if available)
    if resume_text:
        # Limit resume text to avoid token overflow
        resume_preview = resume_text[:2000] if len(resume_text) > 2000 else resume_text
        user_prompt_parts.append(f"\n【候选人当前简历】\n{resume_preview}")
    else:
        user_prompt_parts.append("\n【候选人简历】\n候选人尚未提供简历。")
    
    # Add recent conversation history
    if recent_messages:
        user_prompt_parts.append("\n【最近对话历史】")
        for msg in recent_messages:
            role_label = "用户" if msg["role"] == "user" else "助手"
            user_prompt_parts.append(f"{role_label}：{msg['content']}")
    
    # Add current user question (last user message)
    user_messages = [msg for msg in recent_messages if msg["role"] == "user"]
    if user_messages:
        current_question = user_messages[-1]["content"]
        user_prompt_parts.append(f"\n【用户当前问题】\n{current_question}")
    
    user_prompt = "\n".join(user_prompt_parts)
    
    return system_prompt, user_prompt


@router.post("/jobhunter/career_chat", response_model=CareerChatResponse)
async def career_chat(request: CareerChatRequest) -> CareerChatResponse:
    """
    Career Coach Chat API - Multi-topic conversational support based on JD analysis and resume.
    
    This endpoint provides career coaching conversations by combining:
    - JD analysis results (from cache_id)
    - User resume text (from profile_id)
    - Conversation history
    - Topic-specific guidance
    
    Request body:
        profile_id: str - Profile identifier (e.g., 'data_engineer_gcp')
        cache_id: int - JD analysis cache ID (primary key from jd_analysis_cache table)
        topic: Literal["resume_opt", "gap_analysis", "tech_question"] - Chat topic
        messages: List[ChatMessage] - Conversation history, last one is user question
    
    Returns:
        CareerChatResponse with:
            - ok: bool - Success status
            - answer: str - Assistant's reply
            - topic: str - Topic used
            - error: Optional[str] - Error message if ok=False
    
    Example request:
        POST /api/jobhunter/career_chat
        {
            "profile_id": "data_engineer_gcp",
            "cache_id": 123,
            "topic": "resume_opt",
            "messages": [
                {"role": "user", "content": "如何优化我的简历以匹配这个职位？"}
            ]
        }
    
    Example curl:
        curl -X POST "http://localhost:8000/api/jobhunter/career_chat" \
             -H "Content-Type: application/json" \
             -d '{"profile_id": "data_engineer_gcp", "cache_id": 123, "topic": "resume_opt", "messages": [{"role": "user", "content": "How can I optimize my resume?"}]}'
    """
    try:
        # Step 1: Basic validation
        if request.cache_id is None:
            return CareerChatResponse(
                ok=False,
                answer="",
                topic=request.topic,
                error="cache_id is required",
            )
        
        # Check that there's at least one user message
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            return CareerChatResponse(
                ok=False,
                answer="",
                topic=request.topic,
                error="At least one user message is required",
            )
        
        # Step 2: Build context
        context = build_career_chat_context(
            user_id=DEMO_USER_ID,
            profile_id=request.profile_id,
            cache_id=request.cache_id,
            topic=request.topic,
            messages=request.messages,
        )
        
        # Step 3: Build prompts
        system_prompt, user_prompt = build_career_chat_prompts(request.topic, context)
        
        # Step 4: Call OpenAI
        client = get_openai_client()
        if client is None:
            return CareerChatResponse(
                ok=False,
                answer="",
                topic=request.topic,
                error="OpenAI client not available",
            )
        
        # Build messages for LLM
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=llm_messages,
            temperature=0.5,  # Lower temperature for more focused responses
            max_tokens=800,
        )
        
        answer = (response.choices[0].message.content or "").strip()
        
        return CareerChatResponse(
            ok=True,
            answer=answer,
            topic=request.topic,
        )
        
    except Exception as e:
        logger.exception(f"Error in career_chat endpoint: {e}")
        return CareerChatResponse(
            ok=False,
            answer="",
            topic=request.topic,
            error=f"Internal server error: {str(e)}",
        )


# ========================================
# Resume Refinement Helper Functions
# ========================================

def determine_resume_refinement_step(
    current_step: Optional[ResumeRefinementStep],
    messages: List[ChatMessage],
    resume_text: Optional[str],
) -> ResumeRefinementStep:
    """
    Determine the current step in the resume refinement flow based on conversation state.
    
    Args:
        current_step: Explicitly provided step (if any)
        messages: Conversation history
        resume_text: Whether resume text is available
    
    Returns:
        Current step in the flow
    """
    # If step is explicitly provided, use it
    if current_step:
        return current_step
    
    # Otherwise, infer from conversation state
    user_messages = [msg for msg in messages if msg.role == "user"]
    assistant_messages = [msg for msg in messages if msg.role == "assistant"]
    
    # Step 1: If no resume text and no previous conversation, start with analyze_resume
    if not resume_text and len(user_messages) == 0:
        return ResumeRefinementStep.analyze_resume
    
    # Step 2: If resume is available but no optimization suggestions yet, move to identify_optimization
    if resume_text and len(assistant_messages) == 0:
        return ResumeRefinementStep.identify_optimization
    
    # Step 3: If we've identified optimization areas, provide suggestions
    if len(assistant_messages) >= 1 and len(user_messages) >= 1:
        # Check if last assistant message contains suggestions
        if assistant_messages:
            last_assistant = assistant_messages[-1].content.lower()
            if any(keyword in last_assistant for keyword in ["suggestion", "recommend", "add", "highlight", "restructure"]):
                return ResumeRefinementStep.provide_suggestions
    
    # Step 4: After suggestions, offer fine-tuning
    if len(assistant_messages) >= 2:
        return ResumeRefinementStep.offer_fine_tuning
    
    # Step 5: If user indicates they're done, move to summary
    if user_messages:
        last_user = user_messages[-1].content.lower()
        if any(keyword in last_user for keyword in ["done", "complete", "finished", "ready", "submit"]):
            return ResumeRefinementStep.summary_next_steps
    
    # Default: start from analyze_resume
    return ResumeRefinementStep.analyze_resume


def build_resume_refinement_prompts(
    step: ResumeRefinementStep,
    context: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Build system and user prompts for resume refinement based on current step.
    
    Args:
        step: Current step in the refinement flow
        context: Context dict with JD analysis, resume text, etc.
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    analysis = context.get("analysis", {})
    jd_summary = analysis.get("jd_summary") or {}
    fit_summary = analysis.get("fit_summary") or {}
    resume_text = context.get("resume_text")
    job_title = context.get("job_title") or ""
    recent_messages = context.get("recent_messages", [])
    
    # Base system prompt
    base_system = (
        "You are a professional resume optimization advisor helping candidates refine their resumes "
        "to better match specific job descriptions. Your goal is to provide actionable, personalized "
        "suggestions that help candidates stand out for the role.\n\n"
        "You have access to:\n"
        "- The job description analysis (JD summary, core skills, requirements)\n"
        "- The candidate's current resume\n"
        "- Job fit analysis (strengths, gaps, recommendations)\n\n"
        "Provide clear, specific, and actionable advice. Use bullet points and structured formatting "
        "for better readability."
    )
    
    # Step-specific prompts
    if step == ResumeRefinementStep.analyze_resume:
        system_prompt = (
            base_system + "\n\n"
            "**Current Step: Resume Analysis Request**\n"
            "Your task is to request the user's current resume so you can analyze it against the job description. "
            "Be friendly and explain why having their resume will help you provide better recommendations."
        )
        user_prompt = (
            f"**Job Position:** {job_title}\n\n"
            "The user wants to refine their resume for this position. "
            "Please request their current resume to begin the analysis."
        )
        
    elif step == ResumeRefinementStep.identify_optimization:
        system_prompt = (
            base_system + "\n\n"
            "**Current Step: Identify Optimization Areas**\n"
            "Your task is to cross-reference the job description with the candidate's current resume "
            "and identify key areas for optimization. Focus on:\n"
            "1. Skills mentioned in the JD that are missing or under-emphasized in the resume\n"
            "2. Experiences that could be restructured to better match the job requirements\n"
            "3. Relevant experiences that should be highlighted more prominently\n\n"
            "Provide a clear analysis with specific examples from both the JD and the resume."
        )
        
        user_prompt_parts = [f"**Job Position:** {job_title}"]
        
        # Add JD summary
        if jd_summary:
            if isinstance(jd_summary, dict):
                gold_points = jd_summary.get("gold_points", [])
                core_skills = jd_summary.get("core_skills", [])
            else:
                gold_points = getattr(jd_summary, "gold_points", [])
                core_skills = getattr(jd_summary, "core_skills", [])
            
            if gold_points:
                user_prompt_parts.append("\n**Key Job Requirements:**")
                for point in gold_points[:5]:
                    user_prompt_parts.append(f"- {point}")
            
            if core_skills:
                user_prompt_parts.append(f"\n**Core Skills Required:** {', '.join(core_skills[:10])}")
        
        # Add fit summary
        if fit_summary:
            if isinstance(fit_summary, dict):
                strengths = fit_summary.get("strengths", [])
                gaps = fit_summary.get("gaps", [])
            else:
                strengths = getattr(fit_summary, "strengths", [])
                gaps = getattr(fit_summary, "gaps", [])
            
            if strengths:
                user_prompt_parts.append("\n**Candidate Strengths (from fit analysis):**")
                for strength in strengths[:5]:
                    user_prompt_parts.append(f"- {strength}")
            
            if gaps:
                user_prompt_parts.append("\n**Identified Gaps (from fit analysis):**")
                for gap in gaps[:5]:
                    user_prompt_parts.append(f"- {gap}")
        
        # Add resume text
        if resume_text:
            resume_preview = resume_text[:3000] if len(resume_text) > 3000 else resume_text
            user_prompt_parts.append(f"\n**Candidate's Current Resume:**\n{resume_preview}")
        else:
            user_prompt_parts.append("\n**Candidate's Current Resume:**\n[Resume not provided yet]")
        
        user_prompt_parts.append(
            "\n**Task:** Based on the job description you provided and the current resume, "
            "identify key areas for optimization to make the resume stand out more effectively for this role."
        )
        
        user_prompt = "\n".join(user_prompt_parts)
        
    elif step == ResumeRefinementStep.provide_suggestions:
        system_prompt = (
            base_system + "\n\n"
            "**Current Step: Provide Personalized Suggestions**\n"
            "Your task is to provide specific, actionable suggestions for improving the resume. "
            "Structure your response with:\n\n"
            "1. **Add Highlighted Skills**: Emphasize skills such as AI, Big Data, or Data Engineering "
            "based on the job requirements. Provide specific bullet points that can be added.\n\n"
            "2. **Restructure Bullet Points**: Simplify and enhance existing bullet points to better "
            "match the job's core responsibilities. Show before/after examples.\n\n"
            "3. **Emphasize Relevant Experience**: Highlight experiences that directly relate to the "
            "desired position, such as leadership roles or technical achievements. Suggest which "
            "sections to move up or expand.\n\n"
            "Be specific and provide concrete examples that the candidate can directly use."
        )
        
        user_prompt_parts = [f"**Job Position:** {job_title}"]
        
        # Include context from previous messages
        if recent_messages:
            user_prompt_parts.append("\n**Previous Conversation:**")
            for msg in recent_messages[-4:]:  # Last 4 messages
                role_label = "User" if msg["role"] == "user" else "Assistant"
                user_prompt_parts.append(f"{role_label}: {msg['content']}")
        
        user_prompt_parts.append(
            "\n**Task:** Provide personalized suggestions for improving the resume, including:\n"
            "1. Adding key skills\n"
            "2. Restructuring bullet points\n"
            "3. Highlighting relevant experiences"
        )
        
        user_prompt = "\n".join(user_prompt_parts)
        
    elif step == ResumeRefinementStep.offer_fine_tuning:
        system_prompt = (
            base_system + "\n\n"
            "**Current Step: Offer Further Review**\n"
            "Your task is to offer the option for further review or fine-tuning. "
            "Ask if the user wants additional feedback or adjustments, and if they'd like to focus on specific areas."
        )
        
        user_prompt_parts = [f"**Job Position:** {job_title}"]
        
        if recent_messages:
            user_prompt_parts.append("\n**Previous Conversation:**")
            for msg in recent_messages[-2:]:  # Last 2 messages
                role_label = "User" if msg["role"] == "user" else "Assistant"
                user_prompt_parts.append(f"{role_label}: {msg['content']}")
        
        user_prompt_parts.append(
            "\n**Task:** Ask the user if they would like any further adjustments or improvements "
            "to their resume. Let them know if they'd like to focus on specific areas."
        )
        
        user_prompt = "\n".join(user_prompt_parts)
        
    else:  # summary_next_steps
        system_prompt = (
            base_system + "\n\n"
            "**Current Step: Summary and Next Steps**\n"
            "Your task is to provide a summary of the changes made and give next steps for applying to the job. "
            "Be encouraging and provide clear action items."
        )
        
        user_prompt_parts = [f"**Job Position:** {job_title}"]
        
        if recent_messages:
            user_prompt_parts.append("\n**Refinement Summary:**")
            # Extract key suggestions from conversation
            for msg in recent_messages:
                if msg["role"] == "assistant" and ("suggestion" in msg["content"].lower() or "add" in msg["content"].lower()):
                    user_prompt_parts.append(f"Assistant: {msg['content'][:500]}...")  # Truncate long messages
        
        user_prompt_parts.append(
            "\n**Task:** Provide a summary of the changes we made to the resume. "
            "Confirm that the user is now ready to apply for the position. "
            "Ask if they would like to submit their resume now."
        )
        
        user_prompt = "\n".join(user_prompt_parts)
    
    return system_prompt, user_prompt


@router.post("/jobhunter/resume_refine", response_model=ResumeRefinementResponse)
async def resume_refinement(request: ResumeRefinementRequest) -> ResumeRefinementResponse:
    """
    Resume Refinement API - Multi-turn conversation for optimizing resumes against job descriptions.
    
    This endpoint provides a structured 5-step flow for resume refinement:
    1. **Analyze Resume**: Request and analyze the user's current resume
    2. **Identify Optimization**: Cross-reference JD and resume to find optimization areas
    3. **Provide Suggestions**: Offer personalized suggestions (add skills, restructure bullets, highlight experience)
    4. **Offer Fine-tuning**: Ask if user wants further review or adjustments
    5. **Summary & Next Steps**: Provide summary of changes and next steps for applying
    
    Request body:
        profile_id: str - Profile identifier (e.g., 'data_engineer_gcp')
        cache_id: int - JD analysis cache ID (from jd_analysis_cache.id)
        current_step: Optional[ResumeRefinementStep] - Current step (auto-detected if not provided)
        messages: List[ChatMessage] - Conversation history, last one is user message
        resume_text: Optional[str] - Current resume text (loaded from profile if not provided)
    
    Returns:
        ResumeRefinementResponse with:
            - ok: bool - Success status
            - answer: str - Assistant's reply
            - current_step: ResumeRefinementStep - Current step in the flow
            - next_step: Optional[ResumeRefinementStep] - Next step (if applicable)
            - is_complete: bool - Whether the flow is complete
            - suggestions: Optional[Dict] - Structured suggestions (in provide_suggestions step)
            - error: Optional[str] - Error message if ok=False
    
    Example request:
        POST /api/jobhunter/resume_refine
        {
            "profile_id": "data_engineer_gcp",
            "cache_id": 123,
            "messages": [
                {"role": "user", "content": "I want to refine my resume for this job"}
            ]
        }
    
    Example curl:
        curl -X POST "http://localhost:8000/api/jobhunter/resume_refine" \\
             -H "Content-Type: application/json" \\
             -d '{"profile_id": "data_engineer_gcp", "cache_id": 123, "messages": [{"role": "user", "content": "Help me refine my resume"}]}'
    """
    try:
        # Step 1: Load resume text if not provided
        resume_text = request.resume_text
        if not resume_text:
            try:
                resume_text = get_user_resume(DEMO_USER_ID, request.profile_id)
            except Exception as e:
                logger.warning(f"Failed to load resume: {e}")
                resume_text = None
        
        # Step 2: Build context (similar to career_chat)
        context = build_career_chat_context(
            user_id=DEMO_USER_ID,
            profile_id=request.profile_id,
            cache_id=request.cache_id,
            topic="resume_opt",  # Use resume_opt topic for context building
            messages=request.messages,
        )
        
        # Override resume_text in context if provided
        if resume_text:
            context["resume_text"] = resume_text
        
        # Step 3: Determine current step
        current_step = determine_resume_refinement_step(
            current_step=request.current_step,
            messages=request.messages,
            resume_text=resume_text,
        )
        
        # Step 4: Build prompts for current step
        system_prompt, user_prompt = build_resume_refinement_prompts(current_step, context)
        
        # Step 5: Call OpenAI
        client = get_openai_client()
        if client is None:
            return ResumeRefinementResponse(
                ok=False,
                answer="",
                current_step=current_step,
                error="OpenAI client not available",
            )
        
        # Build messages for LLM
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=llm_messages,
            temperature=0.7,  # Slightly higher for more natural conversation
            max_tokens=1200,  # More tokens for detailed suggestions
        )
        
        answer = (response.choices[0].message.content or "").strip()
        
        # Step 6: Determine next step and completion status
        next_step = None
        is_complete = False
        
        if current_step == ResumeRefinementStep.analyze_resume:
            next_step = ResumeRefinementStep.identify_optimization
        elif current_step == ResumeRefinementStep.identify_optimization:
            next_step = ResumeRefinementStep.provide_suggestions
        elif current_step == ResumeRefinementStep.provide_suggestions:
            next_step = ResumeRefinementStep.offer_fine_tuning
        elif current_step == ResumeRefinementStep.offer_fine_tuning:
            next_step = ResumeRefinementStep.summary_next_steps
        else:  # summary_next_steps
            is_complete = True
        
        # Extract structured suggestions if in provide_suggestions step
        suggestions = None
        if current_step == ResumeRefinementStep.provide_suggestions:
            # Try to extract structured suggestions from the answer
            suggestions = {
                "answer": answer,
                "step": current_step.value,
            }
        
        return ResumeRefinementResponse(
            ok=True,
            answer=answer,
            current_step=current_step,
            next_step=next_step,
            is_complete=is_complete,
            suggestions=suggestions,
        )
        
    except Exception as e:
        logger.exception(f"Error in resume_refinement endpoint: {e}")
        return ResumeRefinementResponse(
            ok=False,
            answer="",
            current_step=request.current_step or ResumeRefinementStep.analyze_resume,
            error=f"Internal server error: {str(e)}",
        )


# Quick view strategy (Lv1):
# - Prefer cached quick_view_cn from DB
# - Else generate from full analysis if available
# - Else generate from raw JD text only (cheap, short summary)
# - Full heavy analysis (Lv2) is triggered separately and not from this endpoint
@router.post("/jobhunter/quick_view", response_model=QuickViewResponse)
async def quick_view_job(
    payload: QuickViewRequest,
) -> QuickViewResponse:
    """
    为指定的 JD 生成一个轻量的中文"Quick View / 快速概览"（Lv1 分析）。

    三层 fallback 逻辑：
    1. 如果 DB 已有 quick_view_cn：直接返回（最快）
    2. 如果已有 analysis_json：用 analysis 生成 quick view，然后写回 quick_view_cn
    3. 没有 analysis_json 或上一步失败：用 raw_text 生成 quick view
    
    注意：此 API 不会自动触发完整 /analyze，这样才能实现「先 Lv1，再按需 Lv2」。
    """
    cache_id = payload.cache_id
    
    try:
        # Get cached analysis record (includes quick_view_cn, analysis_json, raw_text)
        row = get_cached_analysis_by_id(cache_id)
        if not row:
            return QuickViewResponse(
                cache_id=cache_id,
                quick_view_cn="",
                error="Job not found"
            )
        
        # 1) 如果 DB 已有 quick_view_cn：直接返回（最快）
        quick_view_cn = row.get("quick_view_cn")
        if quick_view_cn:
            logger.info(f"Quick view cache HIT (quick_view_cn) for cache_id={cache_id}")
            return QuickViewResponse(
                cache_id=cache_id,
                quick_view_cn=quick_view_cn,
                error=None
            )
        
        # 2) 如果已有 analysis_json：用 analysis 生成 quick view，然后写回 quick_view_cn
        analysis = row.get("analysis")
        if analysis is not None and analysis != {}:
            try:
                text = generate_quick_view_cn(analysis)
                if text:
                    update_quick_view_cn(cache_id, text)
                    logger.info(f"Generated quick view from analysis_json for cache_id={cache_id}")
                    return QuickViewResponse(
                        cache_id=cache_id,
                        quick_view_cn=text,
                        error=None
                    )
                else:
                    # 如果生成失败，继续尝试 raw JD
                    logger.warning(f"generate_quick_view_cn returned empty for cache_id={cache_id}, falling back to raw JD")
            except Exception as e:
                logger.warning(f"Failed to generate quick_view from analysis_json for cache_id={cache_id}: {e}, falling back to raw JD")
        
        # 3) 没有 analysis_json 或上一步失败：用 raw_text 生成 quick view
        raw_text = row.get("raw_text")
        if raw_text:
            # Extract metadata from row
            job_title = row.get("job_title", "")
            # Try to parse company from job_title (format: "Title | Company")
            company = None
            title_only = job_title
            if job_title and "|" in job_title:
                parts = job_title.split("|")
                if len(parts) >= 2:
                    title_only = parts[0].strip()
                    company = parts[1].strip()
            
            meta = {}
            if title_only:
                meta["title"] = title_only
            if company:
                meta["company"] = company
            
            text = generate_quick_view_from_raw(raw_text, meta)
            if text:
                update_quick_view_cn(cache_id, text)
                logger.info(f"Generated quick view from raw JD for cache_id={cache_id}")
                return QuickViewResponse(
                    cache_id=cache_id,
                    quick_view_cn=text,
                    error=None
                )
        
        # 4) 三种方式都失败了
        return QuickViewResponse(
            cache_id=cache_id,
            quick_view_cn="",
            error="No quick view could be generated for this job yet."
        )
        
    except Exception as e:
        logger.exception(f"Failed to generate quick view for cache_id={cache_id}: {e}")
        return QuickViewResponse(
            cache_id=cache_id,
            quick_view_cn="",
            error=f"Failed to generate quick view: {str(e)}"
        )


@router.post("/jobhunter/analyze_cached", response_model=AnalyzeCachedResponse)
async def analyze_cached_jd(request: AnalyzeCachedRequest) -> AnalyzeCachedResponse:
    """
    按需触发 Lv2 深度分析：对指定的缓存 JD 运行完整 LangGraph 分析。
    
    此端点用于在用户点击"Run full analysis"按钮时，对某个已缓存的 JD（只有 Lv0/Lv1 Quick View）
    运行完整的 Lv2 分析，并将结果写回 jd_analysis_cache 表。
    
    逻辑：
    1. 根据 cache_id 从 jd_analysis_cache 表中读取该 JD
    2. 如果找不到，返回 ok=false, error="Job not found"
    3. 如果该行的 analysis_json 已经非空：
       - 出于安全&省钱考虑，只读取已有结果，不再重新调用 LLM
       - 直接返回 ok=true，并在日志中说明 "analysis already exists, skip recompute"
    4. 如果 analysis_json 为空（真正需要跑 Lv2 的情况）：
       - 从缓存中取出 raw_text, job_title, company_name, location, job_url 等
       - 调用已有的 run_jd_analysis 函数（复用 /api/jobhunter/analyze 的逻辑）
       - 用上 profile_id（比如 data_engineer_gcp）
       - 获得完整 analysis_json、auto_skip、auto_skip_reasons 等结果
       - 在 jd_analysis_cache 中对该 cache_id 执行 UPDATE：
         - 写入 analysis_json
         - 更新 auto_skip, auto_skip_reasons
         - 可选：同步更新 quick_view_cn
       - 最后返回 ok=true
    
    约束：
    - 绝对不要对 job_applications 表做任何 INSERT/DELETE
    - 不新增任何 schema 迁移（当前表结构够用）
    - 所有数据库操作都放在 try/except 里，出错时返回 ok=false, error=...
    
    Request body:
        cache_id: int - JD analysis cache ID (from jd_analysis_cache.id)
        profile_id: str - Profile identifier (e.g., 'data_engineer_gcp')
    
    Returns:
        AnalyzeCachedResponse with:
            - cache_id: int
            - ok: bool - Success status
            - error: Optional[str] - Error message if ok=False
    
    Example request:
        POST /api/jobhunter/analyze_cached
        {
            "cache_id": 76,
            "profile_id": "data_engineer_gcp"
        }
    
    Example curl:
        curl -X POST "http://localhost:8000/api/jobhunter/analyze_cached" \
             -H "Content-Type: application/json" \
             -d '{"cache_id": 76, "profile_id": "data_engineer_gcp"}'
    """
    try:
        cache_id = request.cache_id
        profile_id = request.profile_id
        
        # Step 1: Get cached JD record by cache_id
        row = get_cached_analysis_by_id(cache_id)
        if not row:
            logger.warning(f"Cache item not found for cache_id={cache_id}")
            return AnalyzeCachedResponse(
                cache_id=cache_id,
                ok=False,
                error="Job not found"
            )
        
        # Step 2: Check if analysis_json already exists
        analysis = row.get("analysis")
        analysis_json_str = row.get("analysis_json")
        
        # Check if analysis_json is non-empty (not None, not empty string, not empty dict)
        has_existing_analysis = False
        if analysis_json_str is not None and isinstance(analysis_json_str, str):
            analysis_json_str_clean = analysis_json_str.strip()
            has_existing_analysis = (
                analysis_json_str_clean != "" 
                and analysis_json_str_clean != "{}"
                and analysis is not None 
                and analysis != {}
            )
        
        if has_existing_analysis:
            logger.info(f"Analysis already exists for cache_id={cache_id}, skip recompute")
            return AnalyzeCachedResponse(
                cache_id=cache_id,
                ok=True,
                error=None
            )
        
        # Step 3: Run Lv2 analysis (analysis_json is empty)
        logger.info(f"Running Lv2 analysis for cache_id={cache_id}, profile_id={profile_id}")
        
        # Extract JD data from cache
        raw_text = row.get("raw_text")
        job_url = row.get("job_url")
        job_title = row.get("job_title")
        
        if not raw_text:
            logger.warning(f"raw_text is empty for cache_id={cache_id}")
            return AnalyzeCachedResponse(
                cache_id=cache_id,
                ok=False,
                error="Job description text is missing"
            )
        
        # Parse job_title to extract title and company (format: "Title | Company")
        title_only = job_title or ""
        company = None
        if job_title and "|" in job_title:
            parts = job_title.split("|")
            if len(parts) >= 2:
                title_only = parts[0].strip()
                company = parts[1].strip()
        
        # Load candidate profile
        candidate_profile = None
        try:
            profile_path = get_profile_path_for_mode(
                "data_eng" if profile_id == "data_engineer_gcp" else "agent"
            )
            candidate_profile = load_candidate_profile(profile_path)
        except Exception as e:
            logger.warning(f"Failed to load profile for profile_id={profile_id}: {e}, continuing without profile")
        
        # Create JobJDInput
        jd_input = JobJDInput(
            description=raw_text,
            title=title_only if title_only else None,
            company=company if company else None,
            location=None,  # Location may not be in cache
            job_id=None,
            candidate_profile=candidate_profile,
        )
        
        # Run JD analysis graph (this will run full LangGraph pipeline)
        result = run_jd_analysis(
            jd_input,
            candidate_profile=candidate_profile,
            profile_id=profile_id,
            job_url=job_url,
            job_title=job_title,
        )
        
        # Extract analysis result
        analysis_result = {
            "jd_summary": result.get("jd_summary"),
            "fit_summary": result.get("fit_summary"),
            "constraints": result.get("constraints"),
            "lifecycle": result.get("lifecycle"),
            "spotlight_stories": result.get("spotlight_stories"),
            "core_signals": result.get("core_signals"),
            "graph_steps": result.get("graph_steps", []),
        }
        
        # Convert Pydantic models to dicts
        def _convert_to_dict(obj: Any) -> Any:
            if obj is None:
                return None
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if isinstance(obj, list):
                return [_convert_to_dict(item) for item in obj]
            if isinstance(obj, dict):
                return {k: _convert_to_dict(v) for k, v in obj.items()}
            return obj
        
        analysis_result = {k: _convert_to_dict(v) for k, v in analysis_result.items()}
        
        # Generate cn_fast_read if not present
        if "cn_fast_read" not in result or not result.get("cn_fast_read"):
            from services.fiqa_api.jobhunter.graphs.jd_analysis_graph import generate_cn_fast_read
            cn_fast_read = generate_cn_fast_read(analysis_result)
            analysis_result["cn_fast_read"] = cn_fast_read
        
        # Step 4: Update jd_analysis_cache with analysis_json
        try:
            update_analysis_json(cache_id, analysis_result)
            logger.info(f"Updated analysis_json for cache_id={cache_id}")
        except Exception as e:
            logger.error(f"Failed to update analysis_json for cache_id={cache_id}: {e}")
            return AnalyzeCachedResponse(
                cache_id=cache_id,
                ok=False,
                error=f"Failed to save analysis result: {str(e)}"
            )
        
        # Step 5: Calculate and update auto_skip flags
        try:
            auto_skip, reasons = calculate_auto_skip(analysis_result)
            update_auto_skip_flags(
                cache_id=cache_id,
                auto_skip=1 if auto_skip else 0,
                reasons=reasons if reasons else None,
            )
            logger.info(f"Updated auto_skip flags for cache_id={cache_id}: auto_skip={auto_skip}, reasons={reasons}")
        except Exception as e:
            # Graceful degradation: if auto_skip calculation fails, log warning but don't fail the request
            logger.warning(f"Failed to calculate/update auto_skip flags for cache_id={cache_id}: {e}")
        
        # Step 6: Optionally update quick_view_cn (if not already set)
        try:
            existing_quick_view_cn = row.get("quick_view_cn")
            if not existing_quick_view_cn:
                quick_view_cn = generate_quick_view_cn(analysis_result)
                if quick_view_cn:
                    update_quick_view_cn(cache_id, quick_view_cn)
                    logger.info(f"Updated quick_view_cn for cache_id={cache_id}")
        except Exception as e:
            # Graceful degradation: if quick_view_cn generation fails, log warning but don't fail the request
            logger.warning(f"Failed to generate/update quick_view_cn for cache_id={cache_id}: {e}")
        
        return AnalyzeCachedResponse(
            cache_id=cache_id,
            ok=True,
            error=None
        )
        
    except Exception as e:
        logger.exception(f"Error analyzing cached JD for cache_id={request.cache_id}: {e}")
        return AnalyzeCachedResponse(
            cache_id=request.cache_id,
            ok=False,
            error=f"Internal server error: {str(e)}"
        )
