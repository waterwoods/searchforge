"""
mortgage_agent.py - Mortgage Agent Route Handler
==================================================
Handles /api/mortgage-agent/run endpoint for mortgage planning.
Core logic delegated to services/mortgage_agent_runtime.py.
"""

import logging
from typing import List, Optional, Dict, Any, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from services.fiqa_api.mortgage import (
    LocalCostFactors,
    MortgageAgentRequest,
    MortgageAgentResponse,
    MortgageCompareRequest,
    MortgageCompareResponse,
    SingleHomeAgentRequest,
    SingleHomeAgentResponse,
    StressCheckRequest,
    StressCheckResponse,
    SaferHomesResult,
    compare_properties_for_borrower,
    get_local_cost_factors,
    run_mortgage_agent,
    run_single_home_agent,
    run_stress_check,
    search_safer_homes_for_case,
)
from services.fiqa_api.mortgage.nl_to_stress_request import (
    nl_to_stress_request,
    PartialStressRequest,
    NLToStressRequestOutput,
)
from services.fiqa_api.mortgage.tools.property_tool import (
    get_sample_properties_list,
    MortgageProperty,
)

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter()


# ========================================
# Route Handler
# ========================================

@router.post("/mortgage-agent/run")
async def mortgage_agent_run(
    request: MortgageAgentRequest,
    response: Response,
) -> MortgageAgentResponse:
    """
    Mortgage agent endpoint.
    
    Takes user message and optional structured inputs, returns mortgage plans
    with monthly payments, interest rates, DTI ratios, and risk assessments.
    
    Request body:
        user_message: str - User's natural language question
        profile: str (optional) - Profile name (default: "us_default_simplified")
        inputs: dict (optional) - Structured inputs:
            - income: float - Annual income
            - debts: float - Monthly debt payments
            - purchase_price: float - Home purchase price
            - down_payment_pct: float - Down payment percentage (0-1)
            - state: str (optional) - US state code
    
    Returns:
        MortgageAgentResponse with:
            - ok: bool - Success status
            - agent_version: str - Agent version
            - disclaimer: str - Legal disclaimer
            - input_summary: str - Summary of inputs
            - plans: List[MortgagePlan] - 2-3 mortgage plans
            - followups: List[str] - Suggested follow-up questions
            - error: str (optional) - Error message if ok=False
    
    Example request:
        {
            "user_message": "Can I afford a 800k home in Seattle with 150k income?",
            "inputs": {
                "income": 150000,
                "debts": 500,
                "purchase_price": 800000,
                "down_payment_pct": 0.20
            }
        }
    """
    try:
        logger.info(f"level=INFO endpoint=mortgage_agent_run user_message='{request.user_message[:100]}' profile={request.profile}")
        result = run_mortgage_agent(request)
        logger.info(f"level=INFO endpoint=mortgage_agent_run status=success plans_count={len(result.plans)}")
        return result
    except ValueError as ve:
        # Input validation errors
        logger.warning(f"level=WARN status=VALIDATION_ERROR error='{str(ve)}'", exc_info=True)
        return MortgageAgentResponse(
            ok=False,
            agent_version="stub-v1.0.0",
            disclaimer="Educational only, not financial or lending advice.",
            input_summary="",
            plans=[],
            followups=[],
            error=str(ve),
            llm_explanation=None,
            llm_usage=None,
            hard_warning=None,
            lo_summary=None,
            case_state=None,
            agent_steps=None,
        )
    except Exception as e:
        # Unexpected errors - log full traceback for debugging
        logger.exception(f"level=ERROR status=ERROR error_type={type(e).__name__} error='{str(e)}'")
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": f"Internal error: {str(e)}"
            }
        )


@router.get("/mortgage-agent/properties")
async def mortgage_agent_properties() -> List[MortgageProperty]:
    """
    Get sample property listings for mortgage planning.
    
    Returns:
        List of MortgageProperty instances (3-5 sample properties)
    
    Example response:
        [
            {
                "id": "prop_001",
                "name": "Long Beach condo near ocean",
                "city": "Long Beach",
                "state": "CA",
                "purchase_price": 750000.0,
                "property_tax_rate_pct": 1.2,
                "hoa_monthly": 350.0,
                "note": "2BR/2BA, ocean view, walkable to beach"
            },
            ...
        ]
    """
    try:
        logger.info("level=INFO endpoint=mortgage_agent_properties")
        properties = get_sample_properties_list()
        logger.info(f"level=INFO endpoint=mortgage_agent_properties status=success properties_count={len(properties)}")
        return properties
    except Exception as e:
        logger.exception(f"level=ERROR status=ERROR error_type={type(e).__name__} error='{str(e)}'")
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": f"Internal error: {str(e)}"
            }
        )


@router.post("/mortgage-agent/compare", response_model=MortgageCompareResponse)
async def mortgage_agent_compare(
    request: MortgageCompareRequest,
    response: Response,
) -> MortgageCompareResponse:
    """
    Compare two properties for a borrower based on affordability and risk metrics.
    
    This endpoint:
    1. Takes borrower profile (income, debts, down payment %) and two property IDs
    2. Computes max affordability for the borrower
    3. Calculates monthly payment, DTI ratio, and risk level for each property
    4. Determines which property is "best" based on affordability and risk
    5. Returns structured comparison response
    
    Request body:
        income: float - Annual income
        monthly_debts: float - Monthly debt payments
        down_payment_pct: float - Down payment percentage (0-1)
        state: str (optional) - Borrower's state (for display)
        property_ids: List[str] - Exactly 2 property IDs to compare
    
    Returns:
        MortgageCompareResponse with:
            - ok: bool - Success status
            - borrower_profile_summary: str - Brief summary of borrower profile
            - target_dti: float - Target DTI ratio used
            - max_affordability: MaxAffordabilitySummary - Maximum affordability
            - properties: List[PropertyComparisonEntry] - Comparison results for each property
            - best_property_id: str (optional) - ID of the best property
            - error: str (optional) - Error message if ok=False
    
    Example request:
        {
            "income": 150000,
            "monthly_debts": 500,
            "down_payment_pct": 0.20,
            "state": "WA",
            "property_ids": ["prop_001", "prop_002"]
        }
    """
    try:
        logger.info(
            f"level=INFO endpoint=mortgage_agent_compare "
            f"income={request.income} "
            f"property_ids={request.property_ids}"
        )
        result = compare_properties_for_borrower(request)
        logger.info(
            f"level=INFO endpoint=mortgage_agent_compare status=success "
            f"properties_count={len(result.properties)} "
            f"best_property_id={result.best_property_id}"
        )
        return result
    except ValueError as ve:
        # Input validation errors
        logger.warning(
            f"level=WARN endpoint=mortgage_agent_compare status=VALIDATION_ERROR error='{str(ve)}'",
            exc_info=True
        )
        return MortgageCompareResponse(
            ok=False,
            borrower_profile_summary="",
            target_dti=0.0,
            max_affordability=None,
            properties=[],
            best_property_id=None,
            error=str(ve),
        )
    except Exception as e:
        # Unexpected errors - log full traceback for debugging
        logger.exception(
            f"level=ERROR endpoint=mortgage_agent_compare status=ERROR "
            f"error_type={type(e).__name__} error='{str(e)}'"
        )
        return MortgageCompareResponse(
            ok=False,
            borrower_profile_summary="",
            target_dti=0.0,
            max_affordability=None,
            properties=[],
            best_property_id=None,
            error=f"Internal error: {str(e)}",
        )


@router.post("/mortgage-agent/stress-check", response_model=StressCheckResponse)
async def mortgage_stress_check(
    req: StressCheckRequest,
    response: Response,
) -> StressCheckResponse:
    """
    Single-home stress check: is this home loose/ok/tight for this borrower?
    
    This endpoint:
    1. Takes borrower profile (monthly income, debts) and home details (price, down payment, etc.)
    2. Calculates total monthly payment (P&I + tax/insurance/HOA)
    3. Computes DTI ratio and classifies stress band (loose/ok/tight/high_risk)
    4. Returns structured response with payment breakdown and risk assessment
    
    Request body:
        monthly_income: float - Monthly income
        other_debts_monthly: float - Other monthly debt payments
        list_price: float - Home listing price
        down_payment_pct: float (optional) - Down payment percentage (0-1), default 0.20
        zip_code: str (optional) - Zip code for tax/insurance estimation
        state: str (optional) - State code for tax/insurance estimation
        hoa_monthly: float (optional) - Monthly HOA fees, default 0
        tax_rate_est: float (optional) - Property tax rate estimate (as decimal)
        insurance_ratio_est: float (optional) - Home insurance ratio estimate (as decimal)
        risk_preference: str (optional) - "conservative", "neutral", or "aggressive", default "neutral"
        profile_id: str (optional) - User profile ID (for future use, currently ignored)
    
    Returns:
        StressCheckResponse with:
            - total_monthly_payment: Total monthly payment (P&I + tax/ins/HOA)
            - principal_interest_payment: P&I payment only
            - estimated_tax_ins_hoa: Estimated tax, insurance, and HOA
            - dti_ratio: Debt-to-income ratio
            - stress_band: Classification (loose/ok/tight/high_risk)
            - hard_warning: Optional hard warning text if risk is very high
            - wallet_snapshot: Borrower wallet snapshot
            - home_snapshot: Home details snapshot
            - case_state: Optional case state snapshot
            - agent_steps: Step-by-step execution log
            - llm_explanation: Optional LLM explanation (currently None)
    
    Example request:
        {
            "monthly_income": 12500,
            "other_debts_monthly": 500,
            "list_price": 800000,
            "down_payment_pct": 0.20,
            "state": "CA",
            "hoa_monthly": 350
        }
    """
    try:
        logger.info(
            f"level=INFO endpoint=mortgage_stress_check "
            f"monthly_income={req.monthly_income} "
            f"list_price={req.list_price} "
            f"down_payment_pct={req.down_payment_pct}"
        )
        result = run_stress_check(req)
        logger.info(
            f"level=INFO endpoint=mortgage_stress_check status=success "
            f"stress_band={result.stress_band} dti_ratio={result.dti_ratio:.3f}"
        )
        return result
    except ValueError as ve:
        # Input validation errors
        logger.warning(
            f"level=WARN endpoint=mortgage_stress_check status=VALIDATION_ERROR error='{str(ve)}'",
            exc_info=True
        )
        # Return empty response with error indication
        return StressCheckResponse(
            total_monthly_payment=0.0,
            principal_interest_payment=0.0,
            estimated_tax_ins_hoa=0.0,
            dti_ratio=0.0,
            stress_band="high_risk",
            hard_warning=f"Validation error: {str(ve)}",
            wallet_snapshot={},
            home_snapshot={},
            case_state=None,
            agent_steps=None,
            llm_explanation=None,
        )
    except Exception as e:
        # Unexpected errors - log full traceback for debugging
        logger.exception(
            f"level=ERROR endpoint=mortgage_stress_check status=ERROR "
            f"error_type={type(e).__name__} error='{str(e)}'"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": f"Internal error: {str(e)}"
            }
        )


@router.post("/mortgage-agent/single-home-agent", response_model=SingleHomeAgentResponse)
async def single_home_agent_endpoint(
    payload: SingleHomeAgentRequest,
) -> SingleHomeAgentResponse:
    """
    Single Home Agent: understand a single-home question, call stress_check, and explain the result.
    
    This endpoint:
    1. Takes borrower profile (monthly income, debts) and home details (price, down payment, etc.)
    2. Calls stress_check to compute payment breakdown, DTI, and stress band
    3. Optionally generates LLM narrative to explain results in natural language
    4. Returns structured response with stress_result + narrative
    
    Request body:
        stress_request: StressCheckRequest - Stress check parameters
        user_message: str (optional) - Natural language question from borrower
    
    Returns:
        SingleHomeAgentResponse with:
            - stress_result: Complete StressCheckResponse (source of truth)
            - borrower_narrative: Optional short explanation
            - recommended_actions: Optional list of 1-3 next steps
            - llm_usage: Optional token usage metadata
    
    Example request:
        {
            "stress_request": {
                "monthly_income": 12000,
                "other_debts_monthly": 500,
                "list_price": 800000,
                "down_payment_pct": 0.20,
                "state": "CA",
                "hoa_monthly": 350,
                "risk_preference": "neutral"
            },
            "user_message": "Is this home too tight for my budget?"
        }
    """
    try:
        logger.info(
            f"level=INFO endpoint=single_home_agent_endpoint "
            f"monthly_income={payload.stress_request.monthly_income} "
            f"list_price={payload.stress_request.list_price} "
            f"user_message_present={payload.user_message is not None}"
        )
        result = run_single_home_agent(payload)
        logger.info(
            f"level=INFO endpoint=single_home_agent_endpoint status=success "
            f"stress_band={result.stress_result.stress_band} "
            f"narrative_present={result.borrower_narrative is not None}"
        )
        return result
    except ValueError as ve:
        # Input validation errors
        logger.warning(
            f"level=WARN endpoint=single_home_agent_endpoint status=VALIDATION_ERROR error='{str(ve)}'",
            exc_info=True
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Unexpected errors - log full traceback for debugging
        logger.exception(
            f"level=ERROR endpoint=single_home_agent_endpoint status=ERROR "
            f"error_type={type(e).__name__} error='{str(e)}'"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )


@router.post("/mortgage-agent/safer-homes", response_model=SaferHomesResult)
async def safer_homes_endpoint(
    req: StressCheckRequest,
) -> SaferHomesResult:
    """
    Search for safer homes nearby based on current stress check results.
    
    This endpoint:
    1. Takes a StressCheckRequest (same as stress-check endpoint)
    2. Runs stress check to compute baseline stress band and DTI
    3. Searches mock local listings in the same ZIP code
    4. Filters to only "safer" homes (better stress band or lower DTI)
    5. Returns structured response with candidate homes
    
    Request body:
        Same as StressCheckRequest:
        - monthly_income: float - Monthly income
        - other_debts_monthly: float - Other monthly debt payments
        - list_price: float - Target home listing price
        - down_payment_pct: float (optional) - Down payment percentage (0-1), default 0.20
        - zip_code: str (optional) - ZIP code to search (required for this endpoint)
        - state: str (optional) - State code
        - hoa_monthly: float (optional) - Monthly HOA fees, default 0
        - risk_preference: str (optional) - "conservative", "neutral", or "aggressive", default "neutral"
    
    Returns:
        SaferHomesResult with:
            - baseline_band: Baseline stress band from original case
            - baseline_dti_ratio: Baseline DTI ratio from original case
            - zip_code: ZIP code searched
            - candidates: List of safer home candidates (each with listing, stress_band, dti_ratio, etc.)
    
    Example request:
        {
            "monthly_income": 6500,
            "other_debts_monthly": 500,
            "list_price": 900000,
            "down_payment_pct": 0.20,
            "zip_code": "90803",
            "state": "CA",
            "hoa_monthly": 300,
            "risk_preference": "neutral"
        }
    """
    try:
        logger.info(
            f"level=INFO endpoint=safer_homes_endpoint "
            f"monthly_income={req.monthly_income} "
            f"list_price={req.list_price} "
            f"zip_code={req.zip_code}"
        )
        
        # Validate required fields
        if not req.zip_code:
            raise ValueError("zip_code is required for safer homes search")
        
        # Step 1: Run stress check to get baseline metrics
        stress_result = run_stress_check(req)
        baseline_band = stress_result.stress_band
        baseline_dti_ratio = stress_result.dti_ratio
        
        # Step 2: Extract parameters for search_safer_homes_for_case
        result = search_safer_homes_for_case(
            monthly_income=req.monthly_income,
            other_debts_monthly=req.other_debts_monthly,
            zip_code=req.zip_code,
            target_list_price=req.list_price,
            baseline_band=baseline_band,
            baseline_dti_ratio=baseline_dti_ratio,
            down_payment_pct=req.down_payment_pct or 0.20,
            risk_preference=req.risk_preference or "neutral",
            state=req.state,
            max_candidates=5,
        )
        
        logger.info(
            f"level=INFO endpoint=safer_homes_endpoint status=success "
            f"baseline_band={baseline_band} candidates_count={len(result.candidates)}"
        )
        return result
    except ValueError as ve:
        # Input validation errors
        logger.warning(
            f"level=WARN endpoint=safer_homes_endpoint status=VALIDATION_ERROR error='{str(ve)}'",
            exc_info=True
        )
        # Return empty result with error indication
        return SaferHomesResult(
            baseline_band=None,
            baseline_dti_ratio=None,
            zip_code=req.zip_code if req else None,
            candidates=[],
        )
    except Exception as e:
        # Unexpected errors - log full traceback for debugging
        logger.exception(
            f"level=ERROR endpoint=safer_homes_endpoint status=ERROR "
            f"error_type={type(e).__name__} error='{str(e)}'"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": f"Internal error: {str(e)}"
            }
        )


# ========================================
# NL to Stress Request Endpoint
# ========================================

class ConversationMessage(BaseModel):
    """Single conversation message."""
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class NLToStressRequestRequest(BaseModel):
    """Request model for NL to stress request endpoint."""
    user_text: str = Field(..., description="User's natural language query")
    current_request: Optional[Dict[str, Any]] = Field(
        None, description="Optional current form fields (snapshot of existing StressCheckRequest)"
    )
    conversation_history: Optional[List[ConversationMessage]] = Field(
        None, description="Optional conversation history (last 3-5 turns)"
    )


class NLToStressRequestResponse(BaseModel):
    """Response model for NL to stress request endpoint."""
    partial_request: Dict[str, Any] = Field(..., description="Fields extracted from NL (only non-None values)")
    merged_request: Optional[Dict[str, Any]] = Field(
        None, description="current_request with partial_request merged in (only if current_request was provided)"
    )
    missing_required_fields: List[str] = Field(..., description="List of required fields still missing after merge")
    low_confidence_fields: List[str] = Field(default_factory=list, description="Fields with low confidence extraction")
    intent_type: str = Field(..., description="Intent classification: new_plan, adjust_existing, ask_explanation, unknown")
    router_decision: Literal["have_enough_info", "need_more_info"] = Field(
        ..., description="Router decision: have_enough_info if all required fields present, else need_more_info"
    )
    followup_question: Optional[str] = Field(
        None, description="Optional follow-up question asking for missing required fields"
    )
    conversation_history: List[ConversationMessage] = Field(
        ..., description="Updated conversation history with new user message and assistant response"
    )


def merge_partial_into_request(
    current: Optional[Dict[str, Any]],
    partial: PartialStressRequest
) -> Dict[str, Any]:
    """
    Merge partial_request into current_request, only overriding fields where partial has non-None values.
    
    Args:
        current: Optional current request dict (from form state)
        partial: PartialStressRequest with extracted fields
        
    Returns:
        Merged dict with current values updated by partial values
    """
    if current is None:
        current = {}
    
    merged = current.copy()
    
    # Only override fields where partial has non-None values
    if partial.income_monthly is not None:
        merged["monthly_income"] = partial.income_monthly
    if partial.other_debt_monthly is not None:
        merged["other_debts_monthly"] = partial.other_debt_monthly
    if partial.list_price is not None:
        merged["list_price"] = partial.list_price
    if partial.down_payment_pct is not None:
        merged["down_payment_pct"] = partial.down_payment_pct
    if partial.interest_rate_annual is not None:
        # Note: StressCheckRequest doesn't have interest_rate_annual, but we can store it for future use
        merged["interest_rate_annual"] = partial.interest_rate_annual
    if partial.loan_term_years is not None:
        # Note: StressCheckRequest doesn't have loan_term_years, but we can store it for future use
        merged["loan_term_years"] = partial.loan_term_years
    if partial.zip_code is not None:
        merged["zip_code"] = partial.zip_code
    if partial.state is not None:
        merged["state"] = partial.state
    
    return merged


def determine_router_decision(
    merged_request: Dict[str, Any],
    missing_required_fields: List[str]
) -> Literal["have_enough_info", "need_more_info"]:
    """
    Determine router decision based on missing required fields.
    
    Required fields for stress check: income_monthly, list_price
    
    Args:
        merged_request: Merged request dict
        missing_required_fields: List of missing required field names
        
    Returns:
        "have_enough_info" if all required fields present, else "need_more_info"
    """
    # Check if all required fields are present
    # Required fields: income_monthly (maps to monthly_income), list_price
    has_income = merged_request.get("monthly_income") is not None
    has_price = merged_request.get("list_price") is not None
    
    if has_income and has_price and len(missing_required_fields) == 0:
        return "have_enough_info"
    else:
        return "need_more_info"


def generate_followup_question(
    missing_required_fields: List[str],
    merged_request: Dict[str, Any],
    intent_type: str,
    router_decision: Literal["have_enough_info", "need_more_info"]
) -> str:
    """
    Generate a context-aware follow-up question based on missing fields and current state.
    
    Args:
        missing_required_fields: List of missing required field names
        merged_request: Merged request dict (current state after merge)
        intent_type: User intent classification
        router_decision: Router decision (have_enough_info or need_more_info)
        
    Returns:
        Follow-up question string (never None - always returns a message)
    """
    # If we have enough info, return a confirmation message
    if router_decision == "have_enough_info":
        return "I've filled the form on the left. Please review it and click 'Check Stress' when ready."
    
    # If missing fields, generate context-aware question
    has_income = merged_request.get("monthly_income") is not None
    has_price = merged_request.get("list_price") is not None
    
    missing_income = "income_monthly" in missing_required_fields
    missing_price = "list_price" in missing_required_fields
    
    # Context-aware messages based on what we know
    if missing_income and missing_price:
        return "To help you, I need at least your monthly income and the approximate home price."
    elif missing_income and has_price:
        return f"I know roughly how much the home costs (${merged_request.get('list_price', 0):,.0f}), but I still need your monthly income to estimate affordability."
    elif missing_price and has_income:
        income = merged_request.get("monthly_income", 0)
        return f"I know your income (${income:,.0f}/month), but I still need the approximate home price."
    elif missing_income:
        return "I still need your monthly income before I can estimate affordability."
    elif missing_price:
        return "Please tell me roughly how much the home costs."
    else:
        # Other missing fields
        return "I need a bit more information to complete the analysis."


@router.post("/mortgage-agent/nl-to-stress-request", response_model=NLToStressRequestResponse)
async def nl_to_stress_request_endpoint(
    request: NLToStressRequestRequest,
) -> NLToStressRequestResponse:
    """
    Natural language to stress request converter endpoint.
    
    This endpoint:
    1. Takes user's natural language query and optional current form state
    2. Uses NLU to extract mortgage-related fields from the query
    3. Merges extracted fields into current form state (if provided)
    4. Determines if enough info is available to run a stress check
    5. Returns structured response with partial/merged request and follow-up hints
    
    Request body:
        user_text: str - User's natural language query (required)
        current_request: dict (optional) - Current form fields snapshot (StressCheckRequest-like dict)
    
    Returns:
        NLToStressRequestResponse with:
            - partial_request: Fields extracted from NL (only non-None values)
            - merged_request: current_request with partial_request merged (if current_request provided)
            - missing_required_fields: List of required fields still missing
            - low_confidence_fields: List of fields with low confidence extraction
            - intent_type: Intent classification
            - router_decision: "have_enough_info" or "need_more_info"
            - followup_question: Optional follow-up question for missing fields
    
    Example request:
        {
            "user_text": "I make $150k a year and I'm looking at a $750k home in 90803 with 20% down.",
            "current_request": {
                "monthly_income": 10000,
                "other_debts_monthly": 500,
                "list_price": 600000,
                "down_payment_pct": 0.15
            }
        }
    """
    try:
        logger.info(
            f"level=INFO endpoint=nl_to_stress_request_endpoint "
            f"user_text_length={len(request.user_text)} "
            f"has_current_request={request.current_request is not None} "
            f"conversation_history_length={len(request.conversation_history) if request.conversation_history else 0}"
        )
        
        # Step 1: Convert conversation_history to the format expected by nl_to_stress_request
        # (List[Dict[str, str]] with role/content keys)
        conversation_history_dicts: Optional[List[Dict[str, str]]] = None
        if request.conversation_history:
            conversation_history_dicts = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
            # Limit to last 8 messages (4 turns) to keep payloads manageable
            max_messages = 8
            if len(conversation_history_dicts) > max_messages:
                conversation_history_dicts = conversation_history_dicts[-max_messages:]
        
        # Step 2: Call NLU to extract fields
        nlu_output: NLToStressRequestOutput = nl_to_stress_request(
            user_text=request.user_text,
            conversation_history=conversation_history_dicts
        )
        
        # Step 2: Convert PartialStressRequest to dict (only non-None fields)
        partial_dict = {}
        partial = nlu_output.partial_request
        if partial.income_monthly is not None:
            partial_dict["monthly_income"] = partial.income_monthly
        if partial.other_debt_monthly is not None:
            partial_dict["other_debts_monthly"] = partial.other_debt_monthly
        if partial.list_price is not None:
            partial_dict["list_price"] = partial.list_price
        if partial.down_payment_pct is not None:
            partial_dict["down_payment_pct"] = partial.down_payment_pct
        if partial.interest_rate_annual is not None:
            partial_dict["interest_rate_annual"] = partial.interest_rate_annual
        if partial.loan_term_years is not None:
            partial_dict["loan_term_years"] = partial.loan_term_years
        if partial.zip_code is not None:
            partial_dict["zip_code"] = partial.zip_code
        if partial.state is not None:
            partial_dict["state"] = partial.state
        
        # Step 3: Merge partial into current_request if provided
        merged_request = None
        if request.current_request is not None:
            merged_request = merge_partial_into_request(request.current_request, partial)
        else:
            # If no current_request, merged_request is just the partial_dict
            merged_request = partial_dict.copy()
        
        # Step 4: Determine router decision
        router_decision = determine_router_decision(merged_request, nlu_output.missing_required_fields)
        
        # Step 5: Generate follow-up question (now context-aware)
        followup_question = generate_followup_question(
            nlu_output.missing_required_fields,
            merged_request,
            nlu_output.intent_type,
            router_decision
        )
        
        # Step 6: Build updated conversation_history
        # Start with existing history (if any)
        updated_conversation_history: List[Dict[str, str]] = []
        if conversation_history_dicts:
            updated_conversation_history = conversation_history_dicts.copy()
        
        # Append new user message
        updated_conversation_history.append({
            "role": "user",
            "content": request.user_text
        })
        
        # Append assistant response
        updated_conversation_history.append({
            "role": "assistant",
            "content": followup_question
        })
        
        # Limit total conversation history to 10 messages (5 turns) for response
        max_response_messages = 10
        if len(updated_conversation_history) > max_response_messages:
            updated_conversation_history = updated_conversation_history[-max_response_messages:]
        
        # Convert back to ConversationMessage objects for response
        conversation_history_response = [
            ConversationMessage(role=msg["role"], content=msg["content"])
            for msg in updated_conversation_history
        ]
        
        logger.info(
            f"level=INFO endpoint=nl_to_stress_request_endpoint status=success "
            f"intent={nlu_output.intent_type} "
            f"router_decision={router_decision} "
            f"missing_fields_count={len(nlu_output.missing_required_fields)}"
        )
        
        return NLToStressRequestResponse(
            partial_request=partial_dict,
            merged_request=merged_request,
            missing_required_fields=nlu_output.missing_required_fields,
            low_confidence_fields=nlu_output.low_confidence_fields,
            intent_type=nlu_output.intent_type,
            router_decision=router_decision,
            followup_question=followup_question,
            conversation_history=conversation_history_response,
        )
        
    except Exception as e:
        # On error, return a response indicating need_more_info
        logger.exception(
            f"level=ERROR endpoint=nl_to_stress_request_endpoint status=ERROR "
            f"error_type={type(e).__name__} error='{str(e)}'"
        )
        # Return a safe response even on error
        # Build error conversation history
        error_conversation_history: List[ConversationMessage] = []
        if request.conversation_history:
            error_conversation_history = request.conversation_history.copy()
        error_conversation_history.append(
            ConversationMessage(role="user", content=request.user_text)
        )
        error_conversation_history.append(
            ConversationMessage(
                role="assistant",
                content="Sorry, I couldn't understand that. Please try again or fill the form directly."
            )
        )
        # Limit error conversation history
        if len(error_conversation_history) > 10:
            error_conversation_history = error_conversation_history[-10:]
        
        return NLToStressRequestResponse(
            partial_request={},
            merged_request=request.current_request.copy() if request.current_request else {},
            missing_required_fields=["income_monthly", "list_price"],
            low_confidence_fields=[],
            intent_type="unknown",
            router_decision="need_more_info",
            followup_question="Sorry, I couldn't understand that. Please try again or fill the form directly.",
            conversation_history=error_conversation_history,
        )


@router.get("/mortgage-agent/local-cost-factors", response_model=LocalCostFactors)
async def get_local_cost_factors_route(
    zip_code: str,
    state: str | None = None,
) -> LocalCostFactors:
    """
    Get local cost factors (tax rate and insurance ratio) for a given ZIP code and state.
    
    This endpoint provides a reusable tool for estimating location-specific cost factors.
    Currently uses static mock data, but designed to be easily replaced with real API calls.
    
    Query parameters:
        zip_code: str - ZIP code (required)
        state: str (optional) - State code
    
    Returns:
        LocalCostFactors with:
            - zip_code: ZIP code
            - state: State code (if provided)
            - tax_rate_est: Annual tax rate as decimal (e.g., 0.012 for 1.2%)
            - insurance_ratio_est: Annual insurance ratio as decimal (e.g., 0.003 for 0.3%)
            - source: Data source ("zip_override", "state_default", or "global_default")
    
    Example request:
        GET /api/mortgage-agent/local-cost-factors?zip_code=90803&state=CA
    
    Example response:
        {
            "zip_code": "90803",
            "state": "CA",
            "tax_rate_est": 0.011,
            "insurance_ratio_est": 0.0028,
            "source": "zip_override"
        }
    """
    try:
        logger.info(
            f"level=INFO endpoint=get_local_cost_factors_route "
            f"zip_code={zip_code} state={state}"
        )
        result = get_local_cost_factors(zip_code=zip_code, state=state)
        logger.info(
            f"level=INFO endpoint=get_local_cost_factors_route status=success "
            f"source={result.source}"
        )
        return result
    except Exception as e:
        logger.exception(
            f"level=ERROR endpoint=get_local_cost_factors_route status=ERROR "
            f"error_type={type(e).__name__} error='{str(e)}'"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )

