"""
jobhunter.py - JobHunter Agent Route Handler
=============================================
Handles /api/jobhunter/* endpoints for job description analysis and career coaching.
"""

import asyncio
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.fiqa_api.jobhunter.graphs.jd_analysis_graph import run_jd_analysis
from services.fiqa_api.jobhunter.graphs.jd_chat_graph import run_jd_chat_turn
from services.fiqa_api.jobhunter.schemas import (
    JobJDInput,
    JobJDSummary,
    JobHunterChatRequest,
    JobHunterChatResponse,
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
        
        # Run JD analysis graph
        logger.info(f"Running JD analysis for job: {jd_input.title or 'Untitled'} at {jd_input.company or 'Unknown'}")
        result = run_jd_analysis(jd_input, candidate_profile=candidate_profile, profile_id=profile_id)
        
        # Extract results
        jd_summary = result.get("jd_summary")
        fit_summary = result.get("fit_summary")
        constraints = result.get("constraints")
        graph_steps = result.get("graph_steps")  # [Engineering View] Graph execution steps
        
        # Convert to dict for response
        jd_summary_dict = None
        if jd_summary:
            jd_summary_dict = jd_summary.model_dump()
        
        constraints_dict = None
        if constraints:
            constraints_dict = constraints.model_dump()
        
        fit_summary_dict = None
        if fit_summary:
            # Convert JobFitSummary to dict and add match_score/category for frontend compatibility
            fit_dict = fit_summary.model_dump()
            
            # [Quick Filter] Check if skip_deep_analysis is True (from constraints)
            skip_deep_analysis = False
            if constraints and hasattr(constraints, "skip_deep_analysis"):
                skip_deep_analysis = constraints.skip_deep_analysis
            
            # [Quick Filter] If skip_deep_analysis is True, set match_score=1 and category="C"
            if skip_deep_analysis:
                match_score = 1
                category = "C"
            else:
                # Calculate match_score (1-10) based on strengths vs gaps
                # Simple heuristic: more strengths = higher score, more gaps = lower score
                strengths_count = len(fit_summary.strengths)
                gaps_count = len(fit_summary.gaps)
                
                # Base score from recommendation
                if fit_summary.recommendation_for_candidate == "APPLY":
                    base_score = 8
                elif fit_summary.recommendation_for_candidate == "MAYBE":
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
                if fit_summary.recommendation_for_candidate == "APPLY":
                    category = "A"
                elif fit_summary.recommendation_for_candidate == "MAYBE":
                    category = "B"
                else:  # SKIP
                    category = "C"
            
            # Add fields expected by frontend
            fit_dict["match_score"] = match_score
            fit_dict["category"] = category
            fit_dict["recommendation"] = fit_summary.recommendation_for_candidate
            
            # [Quick Filter] Build reasoning_summary from profile_mismatch_reasons if skip_deep_analysis
            if skip_deep_analysis and constraints and hasattr(constraints, "profile_mismatch_reasons"):
                reasons = constraints.profile_mismatch_reasons or []
                summary_reason = (
                    "This role appears to be primarily a sales/financial-advisory position, "
                    "which does not align with the selected profile."
                )
                if reasons:
                    summary_reason += " " + " ".join(reasons)
                fit_dict["reasoning_summary"] = summary_reason
            elif jd_summary and hasattr(jd_summary, "reasoning_summary"):
                # Safely extract reasoning_summary from jd_summary if available
                fit_dict["reasoning_summary"] = jd_summary.reasoning_summary
            elif hasattr(fit_summary, "reasoning_summary"):
                # Check if fit_summary has reasoning_summary attribute (from quick filter)
                fit_dict["reasoning_summary"] = fit_summary.reasoning_summary
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
