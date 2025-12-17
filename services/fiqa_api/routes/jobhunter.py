"""
jobhunter.py - JobHunter Agent Route Handler
=============================================
Handles /api/jobhunter/* endpoints for job description analysis and career coaching.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal

from services.fiqa_api.jobhunter.graphs.jd_analysis_graph import run_jd_analysis
from services.fiqa_api.jobhunter.graphs.jd_chat_graph import run_jd_chat_turn
from services.fiqa_api.jobhunter.jd_interpreter import batch_analyze_jd_clips
from services.fiqa_api.jobhunter.sqlite_cache import list_cached_analyses, get_cached_analysis_by_id
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

logger = logging.getLogger(__name__)

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
    analysis: Dict[str, Any] = Field(..., description="Complete analysis JSON (includes core_signals, lifecycle, spotlight_stories, constraints, graph_steps, etc.)")
    created_at: Optional[str] = Field(None, description="ISO timestamp when record was created")
    updated_at: Optional[str] = Field(None, description="ISO timestamp when record was last updated")


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
        user_id = "local_demo_user"
        
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
            
            item = CachedJDItem(
                id=cache_id,
                job_url=job_url,
                job_title=job_title,
                match_score=match_score,
                category=category,
                recommendation=recommendation,
                last_analyzed_at=last_analyzed_at,
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
