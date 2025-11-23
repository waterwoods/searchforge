"""
mortgage_agent_runtime.py - Mortgage Agent Runtime Logic
==========================================================
Orchestrator for mortgage planning with rule-based stub implementation.

This module coordinates the mortgage planning workflow by:
1. Extracting and validating inputs
2. Generating mortgage plans
3. Computing affordability summaries
4. Returning structured responses

Future: Replace this with LangGraph-based agent or LLM-powered planner.
"""

import logging
import os
import time
import uuid
from time import perf_counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from services.fiqa_api.mortgage.mortgage_math import (
    calc_dti_ratio,
    calc_monthly_payment,
    compute_max_affordability,
)
from services.fiqa_api.mortgage.mortgage_profile import (
    MORTGAGE_RULES,
    assess_risk_level,
    build_hard_warning_if_needed,
    extract_inputs,
    generate_input_summary,
)
from services.fiqa_api.mortgage.schemas import (
    AgentStep,
    ApprovalScore,
    CaseState,
    MaxAffordabilitySummary,
    MortgageAgentRequest,
    MortgageAgentResponse,
    MortgageCompareRequest,
    MortgageCompareResponse,
    MortgagePlan,
    PropertyComparisonEntry,
    PropertyStressMetrics,
    MortgagePropertySummary,
    RiskAssessment,
    SingleHomeAgentRequest,
    SingleHomeAgentResponse,
    StressCheckRequest,
    StressCheckResponse,
    StressBand,
    SuggestedScenario,
    SaferHomeCandidate,
    SaferHomesResult,
    LocalListingSummary,
    SafetyUpgradeSuggestion,
    SafetyUpgradeResult,
    StrategyScenario,
    StrategyLabResult,
)
from services.fiqa_api.mortgage.risk_assessment import assess_risk
from services.fiqa_api.mortgage.tools.property_tool import get_property_by_id, search_listings_for_zip
from services.fiqa_api.mortgage.tools.rates_tool import get_mock_rate_for_state
from services.fiqa_api.mortgage.local_cost_factors import get_local_cost_factors, LocalCostFactors

logger = logging.getLogger("mortgage_agent")

# Feature flag for LangGraph-based single-home agent
USE_LANGGRAPH_SINGLE_HOME = os.getenv("USE_LANGGRAPH_SINGLE_HOME", "false").lower() in ("1", "true", "yes")


# ========================================
# Helper Functions
# ========================================

def _record_step(
    agent_steps: List[AgentStep],
    step_id: str,
    step_name: str,
    status: str,
    duration_ms: Optional[float] = None,
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """
    Helper function to record an agent step.
    
    Args:
        agent_steps: List to append the step to
        step_id: Unique step identifier
        step_name: Human-readable step name
        status: Step status ("pending", "in_progress", "completed", "failed")
        duration_ms: Optional duration in milliseconds
        inputs: Optional lightweight inputs dict
        outputs: Optional lightweight outputs dict
        error: Optional error message if failed
    """
    agent_steps.append(
        AgentStep(
            step_id=step_id,
            step_name=step_name,
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=duration_ms,
            inputs=inputs,
            outputs=outputs,
            error=error,
        )
    )

def _maybe_generate_llm_explanation(
    req: MortgageAgentRequest,
    plans: List[MortgagePlan],
    max_affordability: Optional[MaxAffordabilitySummary],
    input_summary: str,
    hard_warning: Optional[str] = None,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Call LLM to generate natural language explanation of mortgage results.
    
    This function:
    - Does NOT perform any mathematical calculations
    - Does NOT modify any plan or max_affordability values
    - Only generates explanatory text based on pre-computed results
    - Returns (None, None) if LLM is disabled or call fails
    
    Args:
        req: MortgageAgentRequest instance
        plans: List of computed MortgagePlan instances
        max_affordability: Optional MaxAffordabilitySummary
        input_summary: Human-readable input summary string
        hard_warning: Optional hard warning text (if risk is very high)
    
    Returns:
        Tuple of (explanation_text, usage_dict) or (None, None) if disabled/failed
    """
    from services.fiqa_api.utils.llm_client import is_llm_generation_enabled
    from services.fiqa_api.clients import get_openai_client
    from services.fiqa_api.utils.env_loader import get_llm_conf
    
    # Check if LLM generation is enabled
    if not is_llm_generation_enabled():
        logger.info("[MORTGAGE_AGENT_LLM] LLM generation disabled by LLM_GENERATION_ENABLED env")
        return None, None
    
    # Get OpenAI client
    openai_client = get_openai_client()
    if openai_client is None:
        logger.info("[MORTGAGE_AGENT_LLM] OpenAI client not available")
        return None, None
    
    # Get LLM configuration
    try:
        llm_conf = get_llm_conf()
        model = llm_conf.get("model", "gpt-4o-mini")
        max_tokens = llm_conf.get("max_tokens", 512)
        input_per_mtok = llm_conf.get("input_per_mtok")
        output_per_mtok = llm_conf.get("output_per_mtok")
    except Exception as e:
        logger.warning(f"[MORTGAGE_AGENT_LLM] Failed to load LLM config: {e}")
        return None, None
    
    try:
        # Build system prompt
        system_prompt = (
            "You are a cautious mortgage assistant. "
            "You receive pre-computed loan plans and affordability estimates. "
            "NEVER change any numbers, interest rates, or DTI values you are given. "
            "Your job is only to explain, compare, and highlight risks in plain language. "
            "Always remind the user this is an educational estimate, not a loan approval or financial advice. "
            "If a hard_warning is provided, you MUST start your explanation by emphasizing the high risk "
            "or potential inability to get approval, using direct and clear language. "
            "However, do NOT change any numbers or calculation results."
        )
        
        # Build user prompt with structured data
        user_prompt_parts = []
        user_prompt_parts.append("User's question:")
        user_prompt_parts.append(req.user_message)
        user_prompt_parts.append("")
        user_prompt_parts.append("Input Summary:")
        user_prompt_parts.append(input_summary)
        user_prompt_parts.append("")
        
        # Add plans information
        user_prompt_parts.append("Mortgage Plans:")
        for idx, plan in enumerate(plans, 1):
            user_prompt_parts.append(f"\nPlan {idx}: {plan.name}")
            user_prompt_parts.append(f"  - Monthly Payment: ${plan.monthly_payment:,.2f}")
            user_prompt_parts.append(f"  - Interest Rate: {plan.interest_rate:.2f}%")
            user_prompt_parts.append(f"  - Loan Amount: ${plan.loan_amount:,.0f}")
            user_prompt_parts.append(f"  - Term: {plan.term_years} years")
            if plan.dti_ratio is not None:
                user_prompt_parts.append(f"  - DTI Ratio: {plan.dti_ratio:.1%}")
            user_prompt_parts.append(f"  - Risk Level: {plan.risk_level.upper()}")
            if plan.pros:
                user_prompt_parts.append(f"  - Pros: {', '.join(plan.pros)}")
            if plan.cons:
                user_prompt_parts.append(f"  - Cons: {', '.join(plan.cons)}")
        
        # Add max affordability if available
        if max_affordability:
            user_prompt_parts.append("")
            user_prompt_parts.append("Maximum Affordability Estimate:")
            user_prompt_parts.append(f"  - Max Monthly Payment: ${max_affordability.max_monthly_payment:,.2f}")
            user_prompt_parts.append(f"  - Max Loan Amount: ${max_affordability.max_loan_amount:,.0f}")
            user_prompt_parts.append(f"  - Max Home Price: ${max_affordability.max_home_price:,.0f}")
            user_prompt_parts.append(f"  - Assumed Interest Rate: {max_affordability.assumed_interest_rate:.2f}%")
            user_prompt_parts.append(f"  - Target DTI: {max_affordability.target_dti:.1%}")
        
        # Add hard warning if present
        if hard_warning:
            user_prompt_parts.append("")
            user_prompt_parts.append("⚠️ RISK FLAGS / WARNINGS:")
            user_prompt_parts.append(f"{hard_warning}")
            user_prompt_parts.append("")
            user_prompt_parts.append(
                "IMPORTANT: You MUST start your explanation by emphasizing this high risk "
                "or potential inability to get approval. Use direct and clear language. "
                "However, do NOT change any numbers or calculation results."
            )
        
        user_prompt_parts.append("")
        user_prompt_parts.append(
            "Please provide a clear, concise explanation with:\n"
            "1. A brief summary of the mortgage plans\n"
            "2. Risk considerations for each plan\n"
            "3. Next steps or recommendations\n"
            "Use bullet points or numbered lists for clarity. "
            "Remember: This is educational only, not financial advice."
        )
        
        user_prompt = "\n".join(user_prompt_parts)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        # Call LLM directly (synchronous call)
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=max_tokens,
        )
        
        # Extract content
        explanation = ""
        if response.choices and len(response.choices) > 0:
            explanation = response.choices[0].message.content or ""
        
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
            "prompt_tokens": tokens_in,
            "completion_tokens": tokens_out,
            "total_tokens": tokens_total,
            "cost_usd_est": cost_usd_est,
            "model": model,
        }
        
        logger.info(
            f"[MORTGAGE_AGENT_LLM] LLM explanation generated: "
            f"tokens={tokens_total}, cost=${cost_usd_est or 0.0:.6f}, model={model}"
        )
        
        return explanation, usage_dict
        
    except Exception as e:
        logger.exception("[MORTGAGE_AGENT_LLM_ERROR] Failed to generate LLM explanation")
        return None, None

def generate_plan(
    plan_id: str,
    name: str,
    loan_amount: float,
    interest_rate: float,
    term_years: int,
    monthly_debts: float,
    annual_income: float,
    property_id: Optional[str] = None,
) -> MortgagePlan:
    """
    Generate a mortgage plan with calculations.
    
    Args:
        plan_id: Unique plan identifier
        name: Plan name
        loan_amount: Total loan amount
        interest_rate: Annual interest rate (percentage)
        term_years: Loan term in years
        monthly_debts: Other monthly debt payments
        annual_income: Annual income
        property_id: Optional property ID to link this plan to a specific property
    
    Returns:
        MortgagePlan instance
    """
    monthly_payment = calc_monthly_payment(loan_amount, interest_rate, term_years)
    dti_ratio = calc_dti_ratio(monthly_payment, monthly_debts, annual_income)
    risk_level = assess_risk_level(dti_ratio)
    
    # Get pros/cons based on risk level
    pros = MORTGAGE_RULES["pros_templates"][risk_level].copy()
    cons = MORTGAGE_RULES["cons_templates"][risk_level].copy()
    
    return MortgagePlan(
        plan_id=plan_id,
        name=name,
        monthly_payment=monthly_payment,
        interest_rate=interest_rate,
        loan_amount=loan_amount,
        term_years=term_years,
        dti_ratio=dti_ratio,
        risk_level=risk_level,
        pros=pros,
        cons=cons,
        property_id=property_id,
    )


def build_lo_summary(
    inputs: Dict[str, Any],
    plans: List[MortgagePlan],
    max_affordability: Optional[MaxAffordabilitySummary],
    hard_warning: Optional[str],
) -> str:
    """
    Build a structured text summary for Loan Officer.
    
    This function:
    - Does NOT call LLM, uses pure Python string assembly
    - Generates a structured summary with:
      1. Borrower snapshot (income, monthly debts, target price, down payment %, state)
      2. Risk & DTI (representative plan DTI, risk_level, hard_warning status)
      3. Affordability vs target price (max_affordability vs purchase_price, percentage difference)
      4. Next steps for LO (2-3 bullet points with suggested actions)
    
    Format:
    - English language, for Loan Officer review
    - Structured sections with clear headers
    - Defensive handling: skips sections if data is missing
    
    Args:
        inputs: Dict with income, debts, purchase_price, down_payment_pct, state
        plans: List of MortgagePlan instances (at least one)
        max_affordability: Optional MaxAffordabilitySummary
        hard_warning: Optional hard warning text
    
    Returns:
        str: Structured summary text for Loan Officer
    """
    summary_parts = []
    
    # 1. Borrower Snapshot
    summary_parts.append("=" * 60)
    summary_parts.append("BORROWER SNAPSHOT")
    summary_parts.append("=" * 60)
    
    annual_income = inputs.get("income", 0)
    monthly_debts = inputs.get("debts", 0)
    purchase_price = inputs.get("purchase_price", 0)
    down_payment_pct = inputs.get("down_payment_pct", 0)
    state = inputs.get("state", "N/A")
    
    summary_parts.append(f"Annual Income: ${annual_income:,.0f}")
    summary_parts.append(f"Monthly Debts: ${monthly_debts:,.2f}")
    summary_parts.append(f"Target Home Price: ${purchase_price:,.0f}")
    summary_parts.append(f"Down Payment: {down_payment_pct * 100:.0f}% (${purchase_price * down_payment_pct:,.0f})")
    summary_parts.append(f"State: {state}")
    
    # Calculate loan amount
    loan_amount = purchase_price * (1 - down_payment_pct)
    summary_parts.append(f"Loan Amount: ${loan_amount:,.0f}")
    
    # 2. Risk & DTI
    summary_parts.append("")
    summary_parts.append("=" * 60)
    summary_parts.append("RISK & DTI ANALYSIS")
    summary_parts.append("=" * 60)
    
    if plans:
        # Select representative plan (first plan or lowest DTI plan)
        representative_plan = None
        if len(plans) > 0:
            # Try to find plan with lowest DTI, otherwise use first plan
            plans_with_dti = [p for p in plans if p.dti_ratio is not None]
            if plans_with_dti:
                representative_plan = min(plans_with_dti, key=lambda p: p.dti_ratio or float('inf'))
            else:
                representative_plan = plans[0]
        
        if representative_plan:
            dti_ratio = representative_plan.dti_ratio
            risk_level = representative_plan.risk_level
            plan_name = representative_plan.name
            
            summary_parts.append(f"Representative Plan: {plan_name}")
            if dti_ratio is not None:
                summary_parts.append(f"DTI Ratio: {dti_ratio:.1%}")
            else:
                summary_parts.append(f"DTI Ratio: N/A")
            summary_parts.append(f"Risk Level: {risk_level.upper()}")
            
            # Find highest DTI across all plans
            all_dtis = [p.dti_ratio for p in plans if p.dti_ratio is not None]
            if all_dtis:
                max_dti = max(all_dtis)
                if max_dti != dti_ratio:
                    summary_parts.append(f"Highest DTI Across Plans: {max_dti:.1%}")
    else:
        summary_parts.append("No plans available for DTI analysis")
    
    # Hard warning status
    if hard_warning:
        summary_parts.append("")
        summary_parts.append("⚠️ HARD WARNING PRESENT:")
        summary_parts.append(f"   {hard_warning}")
    else:
        summary_parts.append("")
        summary_parts.append("✅ No hard warnings")
    
    # 3. Affordability vs Target Price
    summary_parts.append("")
    summary_parts.append("=" * 60)
    summary_parts.append("AFFORDABILITY vs TARGET PRICE")
    summary_parts.append("=" * 60)
    
    if max_affordability and max_affordability.max_home_price > 0:
        max_home_price = max_affordability.max_home_price
        summary_parts.append(f"Maximum Affordable Price: ${max_home_price:,.0f}")
        summary_parts.append(f"Target Purchase Price: ${purchase_price:,.0f}")
        
        if purchase_price > 0:
            diff = purchase_price - max_home_price
            diff_pct = (diff / purchase_price) * 100
            
            if diff > 0:
                summary_parts.append(f"Gap: ${diff:,.0f} ({diff_pct:.1f}% above affordable limit)")
                summary_parts.append("⚠️ Target price exceeds affordable range")
            elif diff < 0:
                summary_parts.append(f"Buffer: ${abs(diff):,.0f} ({abs(diff_pct):.1f}% below affordable limit)")
                summary_parts.append("✅ Target price is within affordable range")
            else:
                summary_parts.append("Target price matches affordable limit")
            
            summary_parts.append(f"Assumed Interest Rate: {max_affordability.assumed_interest_rate:.2f}%")
            summary_parts.append(f"Target DTI Used: {max_affordability.target_dti:.1%}")
    else:
        summary_parts.append("Maximum affordability not calculated (may require income and debts)")
        summary_parts.append("Cannot compare with target price")
    
    # 4. Next Steps for LO
    summary_parts.append("")
    summary_parts.append("=" * 60)
    summary_parts.append("NEXT STEPS FOR LO")
    summary_parts.append("=" * 60)
    
    next_steps = []
    
    # Step 1: Risk-based action
    if plans:
        representative_plan = plans[0] if plans else None
        if representative_plan and representative_plan.risk_level == "high":
            next_steps.append("Review borrower's credit score and savings reserves - high DTI requires stronger compensating factors")
        elif representative_plan and representative_plan.risk_level == "medium":
            next_steps.append("Verify additional monthly expenses (property taxes, insurance, HOA) not included in current debt calculation")
        else:
            next_steps.append("Request credit report and verify income documentation - borrower profile looks favorable")
    
    # Step 2: Affordability gap action
    if max_affordability and max_affordability.max_home_price > 0 and purchase_price > max_affordability.max_home_price:
        next_steps.append(f"Discuss options: increase down payment by ${abs(purchase_price - max_affordability.max_home_price) * inputs.get('down_payment_pct', 0.2):,.0f} or consider lower purchase price")
    
    # Step 3: Hard warning action
    if hard_warning:
        next_steps.append("Schedule detailed review call - scenario may not qualify under current guidelines")
    else:
        next_steps.append("Proceed with pre-qualification application and gather required documentation")
    
    # Always add at least one generic step if none generated
    if not next_steps:
        next_steps.append("Collect required documentation (W-2, tax returns, bank statements) for pre-qualification")
    
    for i, step in enumerate(next_steps[:3], 1):  # Limit to 3 steps
        summary_parts.append(f"{i}. {step}")
    
    summary_parts.append("")
    summary_parts.append("=" * 60)
    
    return "\n".join(summary_parts)


# ========================================
# Core Runtime Logic
# ========================================

def run_mortgage_agent(req: MortgageAgentRequest) -> MortgageAgentResponse:
    """
    Run mortgage agent with rule-based stub logic.
    
    This function:
    1. Extracts and validates inputs
    2. If property_id is provided, loads property and overrides purchase_price
    3. Calculates loan amount
    4. Generates 2-3 mortgage plans with different rates/terms
    5. Calculates DTI and risk levels
    6. Returns structured response
    
    Args:
        req: MortgageAgentRequest instance
    
    Returns:
        MortgageAgentResponse with plans, summary, and follow-ups
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Initialize tracking
    agent_steps: List[AgentStep] = []
    case_id = f"mortgage_case_{int(time.time() * 1000)}"
    start_ts = datetime.utcnow().isoformat()
    
    # Step 1: Input Extraction
    step_start = perf_counter()
    try:
        inputs = extract_inputs(req)
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_1",
            step_name="Input Extraction",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "user_message": req.user_message,
                "profile": req.profile,
                "property_id": req.property_id,
                "has_inputs_dict": req.inputs is not None,
            },
            outputs={
                "income": inputs.get("income"),
                "debts": inputs.get("debts"),
                "purchase_price": inputs.get("purchase_price"),
                "down_payment_pct": inputs.get("down_payment_pct"),
                "state": inputs.get("state"),
            },
        )
    except Exception as e:
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_1",
            step_name="Input Extraction",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={"user_message": req.user_message, "profile": req.profile},
            error=str(e)[:200],
        )
        raise
    
    # Step 2: Property Lookup (if property_id provided)
    property_id = req.property_id
    if property_id:
        step_start = perf_counter()
        original_property_id = property_id  # Save original for logging
        try:
            property_obj = get_property_by_id(property_id)
            step_end = perf_counter()
            if property_obj:
                # Override purchase_price with property's price
                inputs["purchase_price"] = property_obj.purchase_price
                logger.info(
                    f"level=INFO property_id={property_id} "
                    f"property_name='{property_obj.name}' "
                    f"purchase_price_overridden={property_obj.purchase_price}"
                )
                _record_step(
                    agent_steps=agent_steps,
                    step_id="step_2",
                    step_name="Property Lookup",
                    status="completed",
                    duration_ms=(step_end - step_start) * 1000.0,
                    inputs={"property_id": original_property_id},
                    outputs={
                        "found": True,
                        "property_name": property_obj.name,
                        "purchase_price": property_obj.purchase_price,
                    },
                )
            else:
                # Property not found - log warning but continue with original purchase_price
                logger.warning(
                    f"level=WARN property_id={property_id} not_found "
                    f"using_original_purchase_price={inputs['purchase_price']}"
                )
                property_id = None  # Clear invalid property_id
                _record_step(
                    agent_steps=agent_steps,
                    step_id="step_2",
                    step_name="Property Lookup",
                    status="completed",
                    duration_ms=(step_end - step_start) * 1000.0,
                    inputs={"property_id": original_property_id},
                    outputs={"found": False},
                )
        except Exception as e:
            step_end = perf_counter()
            property_id = None  # Clear invalid property_id
            _record_step(
                agent_steps=agent_steps,
                step_id="step_2",
                step_name="Property Lookup",
                status="failed",
                duration_ms=(step_end - step_start) * 1000.0,
                inputs={"property_id": original_property_id},
                error=str(e)[:200],
            )
            logger.warning(f"level=WARN property_lookup_failed property_id={original_property_id} error='{str(e)}'")
    
    # Step 3: Base Loan Amount Calculation
    step_start = perf_counter()
    try:
        loan_amount = inputs["purchase_price"] * (1 - inputs["down_payment_pct"])
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_3",
            step_name="Base Loan Amount Calculation",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "purchase_price": inputs["purchase_price"],
                "down_payment_pct": inputs["down_payment_pct"],
            },
            outputs={"loan_amount": loan_amount},
        )
    except Exception as e:
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_3",
            step_name="Base Loan Amount Calculation",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "purchase_price": inputs.get("purchase_price"),
                "down_payment_pct": inputs.get("down_payment_pct"),
            },
            error=str(e)[:200],
        )
        raise
    
    # Log input summary
    logger.info(
        f"level=INFO profile={req.profile} "
        f"income={inputs['income']} "
        f"purchase_price={inputs['purchase_price']} "
        f"loan_amount={loan_amount} "
        f"inputs_complete=True"
    )
    
    # Step 4: Plan Generation
    step_start = perf_counter()
    try:
        plans: List[MortgagePlan] = []
        
        # Plan 1: 30-year fixed with lowest rate (conservative)
        plans.append(generate_plan(
            plan_id="plan_1",
            name=f"Conventional {MORTGAGE_RULES['loan_terms'][1]}-year fixed",
            loan_amount=loan_amount,
            interest_rate=MORTGAGE_RULES["interest_rates"][0],  # 5.5%
            term_years=MORTGAGE_RULES["loan_terms"][1],  # 30
            monthly_debts=inputs["debts"],
            annual_income=inputs["income"],
            property_id=property_id,
        ))
        
        # Plan 2: 30-year fixed with medium rate (standard)
        plans.append(generate_plan(
            plan_id="plan_2",
            name=f"Conventional {MORTGAGE_RULES['loan_terms'][1]}-year fixed (Standard)",
            loan_amount=loan_amount,
            interest_rate=MORTGAGE_RULES["interest_rates"][1],  # 6.0%
            term_years=MORTGAGE_RULES["loan_terms"][1],  # 30
            monthly_debts=inputs["debts"],
            annual_income=inputs["income"],
            property_id=property_id,
        ))
        
        # Plan 3: 15-year fixed with lowest rate (aggressive payoff)
        plans.append(generate_plan(
            plan_id="plan_3",
            name=f"Conventional {MORTGAGE_RULES['loan_terms'][0]}-year fixed",
            loan_amount=loan_amount,
            interest_rate=MORTGAGE_RULES["interest_rates"][0],  # 5.5%
            term_years=MORTGAGE_RULES["loan_terms"][0],  # 15
            monthly_debts=inputs["debts"],
            annual_income=inputs["income"],
            property_id=property_id,
        ))
        
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_4",
            step_name="Plan Generation",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "loan_amount": loan_amount,
                "has_income": inputs.get("income", 0) > 0,
                "has_debts": inputs.get("debts", 0) > 0,
                "scenario_count": 3,
            },
            outputs={
                "plan_count": len(plans),
                "plan_summary": [
                    {
                        "plan_id": p.plan_id,
                        "risk_level": p.risk_level,
                        "dti_ratio": p.dti_ratio,
                    }
                    for p in plans
                ],
            },
        )
    except Exception as e:
        step_end = perf_counter()
        plans = []
        _record_step(
            agent_steps=agent_steps,
            step_id="step_4",
            step_name="Plan Generation",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={"loan_amount": loan_amount},
            error=str(e)[:200],
        )
        raise
    
    # Generate input summary
    input_summary = generate_input_summary(inputs)
    
    # Select 2-3 follow-up questions
    followups = MORTGAGE_RULES["followup_questions"][:3]
    
    # Step 5: Affordability Analysis
    max_affordability = None
    step_start = perf_counter()
    try:
        # Use standard interest rate (middle rate from rules) and default DTI threshold
        interest_rate = MORTGAGE_RULES["interest_rates"][1]  # 6.0% (standard rate)
        target_dti = MORTGAGE_RULES["dti_low_threshold"]  # 0.36 (36%)
        term_years = MORTGAGE_RULES["loan_terms"][1]  # 30 years
        
        affordability_result = compute_max_affordability(
            annual_income=inputs["income"],
            monthly_debts=inputs["debts"],
            interest_rate_pct=interest_rate,
            target_dti=target_dti,
            term_years=term_years,
            down_payment_pct=inputs["down_payment_pct"],
        )
        
        max_affordability = MaxAffordabilitySummary(
            max_monthly_payment=affordability_result["max_monthly_payment"],
            max_loan_amount=affordability_result["max_loan_amount"],
            max_home_price=affordability_result["max_home_price"],
            assumed_interest_rate=interest_rate,
            target_dti=target_dti,
        )
        
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_5",
            step_name="Affordability Analysis",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "income": inputs["income"],
                "debts": inputs["debts"],
                "interest_rate": interest_rate,
                "target_dti": target_dti,
            },
            outputs={
                "max_monthly_payment": max_affordability.max_monthly_payment,
                "max_loan_amount": max_affordability.max_loan_amount,
                "max_home_price": max_affordability.max_home_price,
            },
        )
        
        logger.info(
            f"level=INFO max_affordability_computed "
            f"max_home_price={affordability_result['max_home_price']:.0f} "
            f"max_loan_amount={affordability_result['max_loan_amount']:.0f} "
            f"max_monthly_payment={affordability_result['max_monthly_payment']:.2f}"
        )
    except (ValueError, KeyError) as e:
        # If computation fails (e.g., missing inputs), log but don't fail the request
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_5",
            step_name="Affordability Analysis",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "income": inputs.get("income"),
                "debts": inputs.get("debts"),
            },
            error=str(e)[:200],
        )
        logger.warning(f"level=WARN max_affordability_computation_failed error='{str(e)}'")
    
    # Log plan generation
    logger.info(f"level=INFO plans_generated={len(plans)}")
    
    # Step 6: Risk Assessment
    step_start = perf_counter()
    try:
        hard_warning = build_hard_warning_if_needed(
            plans=plans,
            max_aff=max_affordability,
            target_purchase_price=inputs["purchase_price"],
        )
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_6",
            step_name="Risk Assessment",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "plan_count": len(plans),
                "has_max_affordability": max_affordability is not None,
                "target_purchase_price": inputs["purchase_price"],
            },
            outputs={"hard_warning_exists": hard_warning is not None},
        )
        if hard_warning:
            logger.warning(f"level=WARN hard_warning_triggered warning='{hard_warning[:100]}...'")
    except Exception as e:
        step_end = perf_counter()
        hard_warning = None
        _record_step(
            agent_steps=agent_steps,
            step_id="step_6",
            step_name="Risk Assessment",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={"plan_count": len(plans)},
            error=str(e)[:200],
        )
        logger.warning(f"level=WARN risk_assessment_failed error='{str(e)}'")
    
    # Step 7: LLM Explanation
    llm_explanation: Optional[str] = None
    llm_usage: Optional[Dict[str, Any]] = None
    step_start = perf_counter()
    try:
        llm_explanation, llm_usage = _maybe_generate_llm_explanation(
            req, plans, max_affordability, input_summary, hard_warning
        )
        step_end = perf_counter()
        from services.fiqa_api.utils.llm_client import is_llm_generation_enabled
        llm_enabled = is_llm_generation_enabled()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_7",
            step_name="LLM Explanation",
            status="completed" if llm_explanation else "pending",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "llm_enabled": llm_enabled,
                "plan_count": len(plans),
            },
            outputs={
                "explanation_generated": llm_explanation is not None,
                "token_usage": llm_usage.get("total_tokens") if llm_usage else None,
            },
        )
    except Exception as e:
        # Fallback protection: log and ignore
        step_end = perf_counter()
        logger.exception("[MORTGAGE_AGENT_LLM_ERROR] Failed to generate LLM explanation")
        llm_explanation, llm_usage = None, None
        _record_step(
            agent_steps=agent_steps,
            step_id="step_7",
            step_name="LLM Explanation",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={"llm_enabled": True, "plan_count": len(plans)},
            error=str(e)[:200],
        )
    
    # Step 8: LO Summary Generation
    lo_summary: Optional[str] = None
    step_start = perf_counter()
    try:
        lo_summary = build_lo_summary(
            inputs=inputs,
            plans=plans,
            max_affordability=max_affordability,
            hard_warning=hard_warning,
        )
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_8",
            step_name="LO Summary Generation",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "plan_count": len(plans),
                "has_max_affordability": max_affordability is not None,
                "has_hard_warning": hard_warning is not None,
            },
            outputs={
                "summary_length": len(lo_summary) if lo_summary else 0,
                "summary_generated": lo_summary is not None,
            },
        )
        logger.info("level=INFO lo_summary_generated")
    except Exception as e:
        # Defensive handling: log but don't fail the request
        step_end = perf_counter()
        logger.warning(f"level=WARN lo_summary_generation_failed error='{str(e)}'")
        lo_summary = None
        _record_step(
            agent_steps=agent_steps,
            step_id="step_8",
            step_name="LO Summary Generation",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={"plan_count": len(plans)},
            error=str(e)[:200],
        )
    
    # Build CaseState snapshot
    case_state = CaseState(
        case_id=case_id,
        timestamp=start_ts,
        inputs=inputs,
        plans=plans,
        max_affordability=max_affordability,
        risk_summary={
            "highest_dti": max((p.dti_ratio or 0.0) for p in plans) if plans else None,
            "risk_levels": [p.risk_level for p in plans],
            "hard_warning": hard_warning,
        },
    )
    
    return MortgageAgentResponse(
        ok=True,
        agent_version=MORTGAGE_RULES["agent_version"],
        disclaimer=MORTGAGE_RULES["disclaimer"],
        input_summary=input_summary,
        plans=plans,
        followups=followups,
        max_affordability=max_affordability,
        error=None,
        llm_explanation=llm_explanation,
        llm_usage=llm_usage,
        hard_warning=hard_warning,
        lo_summary=lo_summary,
        case_state=case_state,
        agent_steps=agent_steps,
    )


# ========================================
# Property Comparison Logic
# ========================================

def compare_properties_for_borrower(req: MortgageCompareRequest) -> MortgageCompareResponse:
    """
    Compare two properties for a borrower based on affordability and risk metrics.
    
    This function:
    1. Validates borrower inputs
    2. Computes max affordability
    3. For each property, calculates monthly payment, DTI, and risk level
    4. Determines which property is "best" based on affordability and risk
    5. Returns structured comparison response
    
    Args:
        req: MortgageCompareRequest with borrower profile and property IDs
    
    Returns:
        MortgageCompareResponse with comparison results
    """
    # Validate inputs
    if req.income <= 0:
        return MortgageCompareResponse(
            ok=False,
            borrower_profile_summary="",
            target_dti=0.0,
            max_affordability=None,
            properties=[],
            best_property_id=None,
            error="income must be greater than 0",
        )
    
    if req.monthly_debts < 0:
        return MortgageCompareResponse(
            ok=False,
            borrower_profile_summary="",
            target_dti=0.0,
            max_affordability=None,
            properties=[],
            best_property_id=None,
            error="monthly_debts must be non-negative",
        )
    
    if req.down_payment_pct < 0 or req.down_payment_pct >= 1:
        return MortgageCompareResponse(
            ok=False,
            borrower_profile_summary="",
            target_dti=0.0,
            max_affordability=None,
            properties=[],
            best_property_id=None,
            error="down_payment_pct must be between 0 and 1",
        )
    
    if len(req.property_ids) != 2:
        return MortgageCompareResponse(
            ok=False,
            borrower_profile_summary="",
            target_dti=0.0,
            max_affordability=None,
            properties=[],
            best_property_id=None,
            error=f"property_ids must contain exactly 2 items, got {len(req.property_ids)}",
        )
    
    # Compute max affordability
    interest_rate = MORTGAGE_RULES["interest_rates"][1]  # 6.0% (standard rate)
    target_dti = MORTGAGE_RULES["dti_low_threshold"]  # 0.36 (36%)
    term_years = MORTGAGE_RULES["loan_terms"][1]  # 30 years
    
    try:
        affordability_result = compute_max_affordability(
            annual_income=req.income,
            monthly_debts=req.monthly_debts,
            interest_rate_pct=interest_rate,
            target_dti=target_dti,
            term_years=term_years,
            down_payment_pct=req.down_payment_pct,
        )
        
        max_affordability = MaxAffordabilitySummary(
            max_monthly_payment=affordability_result["max_monthly_payment"],
            max_loan_amount=affordability_result["max_loan_amount"],
            max_home_price=affordability_result["max_home_price"],
            assumed_interest_rate=interest_rate,
            target_dti=target_dti,
        )
        
        logger.info(
            f"level=INFO compare_properties max_affordability_computed "
            f"max_home_price={affordability_result['max_home_price']:.0f} "
            f"max_monthly_payment={affordability_result['max_monthly_payment']:.2f}"
        )
    except (ValueError, KeyError) as e:
        logger.warning(f"level=WARN compare_properties max_affordability_failed error='{str(e)}'")
        return MortgageCompareResponse(
            ok=False,
            borrower_profile_summary="",
            target_dti=target_dti,
            max_affordability=None,
            properties=[],
            best_property_id=None,
            error=f"Failed to compute max affordability: {str(e)}",
        )
    
    # Process each property
    property_entries: List[PropertyComparisonEntry] = []
    
    for property_id in req.property_ids:
        # Get property by ID
        property_obj = get_property_by_id(property_id)
        if not property_obj:
            logger.warning(f"level=WARN compare_properties property_not_found property_id={property_id}")
            continue
        
        listing_price = property_obj.purchase_price
        
        # Calculate loan amount
        loan_amount = listing_price * (1 - req.down_payment_pct)
        
        # Calculate monthly payment
        monthly_payment = calc_monthly_payment(
            loan_amount=loan_amount,
            annual_rate=interest_rate,
            term_years=term_years,
        )
        
        # Calculate DTI ratio
        dti_ratio = calc_dti_ratio(
            monthly_payment=monthly_payment,
            monthly_debts=req.monthly_debts,
            annual_income=req.income,
        )
        
        # Assess risk level
        risk_level = assess_risk_level(dti_ratio)
        
        # Check if within affordability
        within_affordability = (
            listing_price <= max_affordability.max_home_price and
            monthly_payment <= max_affordability.max_monthly_payment
        )
        
        # Calculate DTI excess percentage
        dti_excess_pct = None
        if target_dti > 0:
            dti_excess_pct = (dti_ratio - target_dti) / target_dti
        
        logger.info(
            f"level=INFO compare_properties property_processed "
            f"property_id={property_id} "
            f"listing_price={listing_price:.0f} "
            f"monthly_payment={monthly_payment:.2f} "
            f"dti_ratio={dti_ratio:.3f} "
            f"risk_level={risk_level} "
            f"within_affordability={within_affordability}"
        )
        
        # Build property summary
        display_name = property_obj.name
        if property_obj.city and property_obj.state:
            display_name = f"{property_obj.city}, {property_obj.state} – {property_obj.name}"
        
        property_summary = MortgagePropertySummary(
            property_id=property_id,
            display_name=display_name,
            city=property_obj.city,
            state=property_obj.state,
            listing_price=listing_price,
        )
        
        # Build stress metrics
        stress_metrics = PropertyStressMetrics(
            monthly_payment=monthly_payment,
            dti_ratio=dti_ratio,
            risk_level=risk_level,
            within_affordability=within_affordability,
            dti_excess_pct=dti_excess_pct,
        )
        
        # Build comparison entry
        entry = PropertyComparisonEntry(
            property=property_summary,
            metrics=stress_metrics,
        )
        
        property_entries.append(entry)
    
    # If no properties were successfully processed, return error
    if not property_entries:
        return MortgageCompareResponse(
            ok=False,
            borrower_profile_summary="",
            target_dti=target_dti,
            max_affordability=max_affordability,
            properties=[],
            best_property_id=None,
            error="No properties were found or processed successfully",
        )
    
    # Determine best property
    best_property_id = None
    if len(property_entries) == 1:
        # Only one property, select it
        best_property_id = property_entries[0].property.property_id
    else:
        # Two properties: select based on rules
        # Rule 1: Prefer properties within affordability
        affordable_properties = [
            entry for entry in property_entries
            if entry.metrics.within_affordability
        ]
        
        if affordable_properties:
            # If both are affordable, or one is affordable, select the one with lower DTI
            best_entry = min(affordable_properties, key=lambda e: e.metrics.dti_ratio)
            best_property_id = best_entry.property.property_id
        else:
            # Neither is affordable, select the one with lower DTI
            best_entry = min(property_entries, key=lambda e: e.metrics.dti_ratio)
            best_property_id = best_entry.property.property_id
    
    logger.info(
        f"level=INFO compare_properties best_property_selected "
        f"best_property_id={best_property_id} "
        f"properties_count={len(property_entries)}"
    )
    
    # Build borrower profile summary
    borrower_profile_summary = (
        f"Annual income: ${req.income:,.0f}, "
        f"Monthly debts: ${req.monthly_debts:,.0f}, "
        f"Down payment: {req.down_payment_pct*100:.0f}%"
    )
    if req.state:
        borrower_profile_summary += f", State: {req.state}"
    
    return MortgageCompareResponse(
        ok=True,
        borrower_profile_summary=borrower_profile_summary,
        target_dti=target_dti,
        max_affordability=max_affordability,
        properties=property_entries,
        best_property_id=best_property_id,
        error=None,
    )


# ========================================
# Stress Check Logic
# ========================================

def _estimate_tax_rate(
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    tax_rate_est: Optional[float] = None,
) -> float:
    """
    Estimate property tax rate.
    
    Args:
        state: State code (optional)
        zip_code: Zip code (optional, currently not used)
        tax_rate_est: User-provided tax rate estimate (takes precedence)
    
    Returns:
        Tax rate as decimal (e.g., 0.012 for 1.2%)
    """
    if tax_rate_est is not None:
        return tax_rate_est
    
    # Simple state-based defaults (can be enhanced later)
    state_defaults = {
        "CA": 0.012,  # ~1.2% typical for California
        "NY": 0.014,  # ~1.4% typical for New York
        "TX": 0.018,  # ~1.8% typical for Texas
        "FL": 0.011,  # ~1.1% typical for Florida
        "WA": 0.010,  # ~1.0% typical for Washington
    }
    
    if state and state.upper() in state_defaults:
        return state_defaults[state.upper()]
    
    # Global default
    return 0.012  # 1.2% default


def _estimate_insurance_rate(
    insurance_ratio_est: Optional[float] = None,
) -> float:
    """
    Estimate home insurance rate (annual as % of home value).
    
    Args:
        insurance_ratio_est: User-provided insurance rate estimate (takes precedence)
    
    Returns:
        Insurance rate as decimal (e.g., 0.003 for 0.3% annually)
    """
    if insurance_ratio_est is not None:
        return insurance_ratio_est
    
    # Default: ~0.3% of home value annually (typical range: 0.25% - 0.5%)
    return 0.003


def _classify_stress_band(
    dti_ratio: float,
    safe_payment_band: Tuple[float, float],
    total_monthly_payment: float,
    risk_preference: str = "neutral",
) -> StressBand:
    """
    Classify stress band based on DTI ratio and payment vs safe band.
    
    Args:
        dti_ratio: Debt-to-income ratio
        risk_preference: "conservative", "neutral", or "aggressive"
        safe_payment_band: Tuple of (min_safe, max_safe) monthly payment
        total_monthly_payment: Total monthly payment
    
    Returns:
        StressBand: "loose", "ok", "tight", or "high_risk"
    """
    # Adjust thresholds based on risk preference
    if risk_preference == "conservative":
        dti_ok_threshold = MORTGAGE_RULES["dti_low_threshold"] * 0.9  # Stricter
        dti_tight_threshold = MORTGAGE_RULES["dti_medium_threshold"] * 0.95
    elif risk_preference == "aggressive":
        dti_ok_threshold = MORTGAGE_RULES["dti_low_threshold"] * 1.1  # More lenient
        dti_tight_threshold = MORTGAGE_RULES["dti_medium_threshold"] * 1.05
    else:  # neutral
        dti_ok_threshold = MORTGAGE_RULES["dti_low_threshold"]
        dti_tight_threshold = MORTGAGE_RULES["dti_medium_threshold"]
    
    # High risk: DTI > 0.80 or payment way above safe band
    if dti_ratio > 0.80:
        return "high_risk"
    
    # Check if payment is way above safe band (more than 20% over)
    if safe_payment_band[1] > 0:
        payment_excess = (total_monthly_payment - safe_payment_band[1]) / safe_payment_band[1]
        if payment_excess > 0.20:
            return "high_risk"
    
    # Tight: DTI between medium and high threshold, or payment above safe band
    if dti_ratio >= dti_tight_threshold:
        return "tight"
    
    if safe_payment_band[1] > 0 and total_monthly_payment > safe_payment_band[1]:
        return "tight"
    
    # OK: DTI between low and medium threshold, payment within safe band
    if dti_ratio >= dti_ok_threshold:
        return "ok"
    
    # Loose: DTI below low threshold and payment well within safe band
    return "loose"


def compute_rule_based_approval_score(
    stress_band: StressBand,
    dti_ratio: float,
    wallet_snapshot: Dict[str, Any],
    home_snapshot: Dict[str, Any],
) -> ApprovalScore:
    """
    Compute mortgage approval likelihood score based on stress band, DTI, and snapshots.
    
    This is a simple, explainable heuristic that can later be replaced with a real ML model.
    The function is pure (no side effects) and safe for missing fields (uses defaults).
    
    Args:
        stress_band: Stress band classification (loose/ok/tight/high_risk)
        dti_ratio: Debt-to-income ratio
        wallet_snapshot: Dict with annual_income, monthly_income, etc.
        home_snapshot: Dict with list_price, loan_amount, down_payment_pct, etc.
    
    Returns:
        ApprovalScore with score (0-100), bucket (likely/borderline/unlikely), and reasons
    """
    # Base score
    base = 80.0
    
    # DTI penalty: treat 0.35 as "safe", 0.45 as "high", cap penalty
    dti_penalty = max(0.0, (dti_ratio - 0.35) * 200.0)  # rough scaling
    
    # LTV penalty: compute loan-to-value ratio
    list_price = home_snapshot.get("list_price", 0.0)
    loan_amount = home_snapshot.get("loan_amount", 0.0)
    
    if list_price > 0:
        ltv_ratio = loan_amount / list_price
    else:
        # Fallback to default if list_price missing
        ltv_ratio = 0.8
    
    # Penalize high LTV (treat 0.80 as "safe", 0.90 as "high")
    ltv_penalty = max(0.0, (ltv_ratio - 0.80) * 150.0)  # rough scaling
    
    # Stress band adjustment
    band_adjustments = {
        "loose": 5.0,    # small positive bump
        "ok": 0.0,       # no change
        "tight": -10.0,  # negative adjustment
        "high_risk": -25.0,  # large negative adjustment
    }
    band_adjustment = band_adjustments.get(stress_band, 0.0)
    
    # Compute raw score
    raw_score = base - dti_penalty - ltv_penalty + band_adjustment
    
    # Clamp to 0-100 and round to 1 decimal
    score = float(min(100.0, max(0.0, round(raw_score, 1))))
    
    # Derive bucket from score
    if score >= 70:
        bucket = "likely"
    elif score >= 40:
        bucket = "borderline"
    else:
        bucket = "unlikely"
    
    # Build reasons list
    reasons = []
    
    if dti_ratio > 0.43:
        reasons.append("high_dti")
    
    if ltv_ratio > 0.9:
        reasons.append("very_high_ltv")
    
    # Check if income is strong relative to home price
    annual_income = wallet_snapshot.get("annual_income", 0.0)
    if list_price > 0 and annual_income > 0:
        income_to_price_ratio = annual_income / list_price
        if income_to_price_ratio > 0.25:  # Income is > 25% of home price (strong)
            reasons.append("strong_income")
    
    return ApprovalScore(
        score=score,
        bucket=bucket,
        reasons=reasons,
    )


def _suggest_scenarios_for_stress_result(
    stress_response: StressCheckResponse,
) -> List[SuggestedScenario]:
    """
    Lightweight reflection/planner step:
    - Look at stress_band, dti_ratio, safe_payment_band and total_monthly_payment.
    - Return up to 2 SuggestedScenario objects, using fixed rules.
    - No LLM calls - this is a simple rule-based reflection to make the pipeline feel more agentic.
    
    This helper suggests existing what-if scenarios (income_minus_10, price_minus_50k) based on
    the stress result, keeping behavior safe and deterministic.
    
    Args:
        stress_response: StressCheckResponse instance with computed stress metrics
    
    Returns:
        List of SuggestedScenario objects (0-2 items)
    """
    scenarios: List[SuggestedScenario] = []
    band = stress_response.stress_band
    dti = stress_response.dti_ratio or 0.0
    wallet = stress_response.wallet_snapshot or {}
    safe_min, safe_max = None, None
    
    if wallet.get("safe_payment_band"):
        band_vals = wallet["safe_payment_band"]
        if isinstance(band_vals, dict):
            safe_min = band_vals.get("min_safe")
            safe_max = band_vals.get("max_safe")
        elif isinstance(band_vals, (list, tuple)) and len(band_vals) >= 2:
            safe_min = band_vals[0]
            safe_max = band_vals[1]
    
    # Rule 1: Tight / high_risk -> suggest lowering price and/or income scenario
    if band in ("tight", "high_risk"):
        scenarios.append(SuggestedScenario(
            id="income_minus_10",
            title="Try -10% income scenario",
            description="See how things look if your usable income drops by 10%.",
            scenario_key="income_minus_10",
            reason="Current stress band is high; this helps you see if things are still affordable under a downside case."
        ))
        scenarios.append(SuggestedScenario(
            id="price_minus_50k",
            title="Try -$50k cheaper home",
            description="Check a cheaper home price to reduce monthly payment and DTI.",
            scenario_key="price_minus_50k",
            reason="A cheaper home is a common way to bring DTI and stress down."
        ))
        return scenarios
    
    # Rule 2: OK band but monthly payment is near the top of safe band -> still suggest one safer scenario
    total_payment = stress_response.total_monthly_payment or 0.0
    if band == "ok" and safe_max is not None and total_payment > 0.9 * safe_max:
        scenarios.append(SuggestedScenario(
            id="price_minus_50k",
            title="Check a slightly cheaper home",
            description="See if a $50k cheaper home feels more comfortable.",
            scenario_key="price_minus_50k",
            reason="You are near the top of your safe payment range; a cheaper home may feel more comfortable."
        ))
        return scenarios
    
    # Rule 3: Loose band -> no strong suggestion
    return scenarios


def run_stress_check(req: StressCheckRequest, request_id: Optional[str] = None) -> StressCheckResponse:
    """
    Compute whether a *single* home is loose / ok / tight for this borrower.
    
    Reuse existing mortgage_math + mortgage_profile rules.
    Pure Python implementation - no LLM calls.
    
    Implementation notes:
    - Interest rate is fetched via rates_tool.get_mock_rate_for_state() (pluggable tool layer).
      The mock implementation can be replaced with a real-time API without changing core logic.
    - Response includes explicit assumed_interest_rate_pct, assumed_tax_rate_pct, and
      assumed_insurance_ratio_pct fields to show what assumptions were used in calculations.
    
    Args:
        req: StressCheckRequest with borrower profile and home details
    
    Returns:
        StressCheckResponse with payment breakdown, DTI, stress band, and snapshots
    """
    # Initialize tracking
    agent_steps: List[AgentStep] = []
    case_id = f"stress_check_{int(time.time() * 1000)}"
    start_ts = datetime.utcnow().isoformat()
    
    # Step 1: Input Extraction
    step_start = perf_counter()
    try:
        # Extract and validate inputs with defaults
        monthly_income = req.monthly_income
        other_debts_monthly = req.other_debts_monthly
        list_price = req.list_price
        down_payment_pct = req.down_payment_pct or 0.20
        hoa_monthly = req.hoa_monthly or 0.0
        risk_preference = req.risk_preference or "neutral"
        
        # Validate
        if monthly_income <= 0:
            raise ValueError("monthly_income must be greater than 0")
        if other_debts_monthly < 0:
            raise ValueError("other_debts_monthly must be non-negative")
        if list_price <= 0:
            raise ValueError("list_price must be greater than 0")
        if down_payment_pct < 0 or down_payment_pct >= 1:
            raise ValueError("down_payment_pct must be between 0 and 1")
        
        annual_income = monthly_income * 12.0
        
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_1",
            step_name="Input Extraction",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "monthly_income": monthly_income,
                "other_debts_monthly": other_debts_monthly,
                "list_price": list_price,
                "down_payment_pct": down_payment_pct,
            },
            outputs={
                "annual_income": annual_income,
                "validated": True,
            },
        )
    except Exception as e:
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_1",
            step_name="Input Extraction",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            error=str(e)[:200],
        )
        raise
    
    # Step 2: Market Data Fetch (Interest Rate + Local Cost Factors)
    # Note: Interest rate is now fetched via rates_tool.get_mock_rate_for_state().
    # Local cost factors (tax/insurance) are fetched via local_cost_factors.get_local_cost_factors().
    # This provides a pluggable abstraction - the mock implementations can be replaced
    # with real-time APIs in the future without changing the core logic.
    step_start = perf_counter()
    try:
        # Fetch interest rate using rates tool (currently mock, can be replaced with real API)
        interest_rate = get_mock_rate_for_state(
            state=req.state,
            loan_type="30y_fixed",
        )
        
        # Fetch local cost factors (tax rate and insurance ratio)
        local_factors: LocalCostFactors = get_local_cost_factors(
            zip_code=req.zip_code,
            state=req.state,
            tax_rate_est=req.tax_rate_est,
            insurance_ratio_est=req.insurance_ratio_est,
        )
        
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_2",
            step_name="Market Data Fetch",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "state": req.state,
                "zip_code": req.zip_code,
                "loan_type": "30y_fixed",
            },
            outputs={
                "assumed_interest_rate_pct": interest_rate,
                "assumed_tax_rate_pct": local_factors.tax_rate_est * 100.0,  # Convert to percent
                "assumed_insurance_ratio_pct": local_factors.insurance_ratio_est * 100.0,  # Convert to percent
                "local_cost_factors_source": local_factors.source,
            },
        )
    except Exception as e:
        step_end = perf_counter()
        # Fallback to default rate if rate fetch fails
        interest_rate = MORTGAGE_RULES["interest_rates"][1]  # 6.0% standard
        # Fallback to global defaults for local cost factors
        local_factors = get_local_cost_factors(
            zip_code=req.zip_code,
            state=req.state,
        )
        logger.warning(f"[STRESS_CHECK] Failed to fetch rate: {e}, using default {interest_rate}%")
        _record_step(
            agent_steps=agent_steps,
            step_id="step_2",
            step_name="Market Data Fetch",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "state": req.state,
                "zip_code": req.zip_code,
                "loan_type": "30y_fixed",
            },
            outputs={
                "assumed_interest_rate_pct": interest_rate,
                "assumed_tax_rate_pct": local_factors.tax_rate_est * 100.0,
                "assumed_insurance_ratio_pct": local_factors.insurance_ratio_est * 100.0,
                "local_cost_factors_source": local_factors.source,
                "fallback_used": True,
            },
            error=str(e)[:200],
        )
    
    # Step 3: Cost Profile Estimation
    step_start = perf_counter()
    try:
        # Calculate loan amount
        loan_amount = list_price * (1 - down_payment_pct)
        
        # Use tax and insurance rates from local cost factors (already fetched in Step 2)
        tax_rate = local_factors.tax_rate_est
        insurance_rate = local_factors.insurance_ratio_est
        
        # Use interest rate from market data fetch and term from rules
        term_years = MORTGAGE_RULES["loan_terms"][1]  # 30 years
        
        # Calculate principal and interest payment
        principal_interest_payment = calc_monthly_payment(
            loan_amount=loan_amount,
            annual_rate=interest_rate,
            term_years=term_years,
        )
        
        # Calculate estimated tax, insurance, and HOA
        annual_tax = list_price * tax_rate
        monthly_tax = annual_tax / 12.0
        
        annual_insurance = list_price * insurance_rate
        monthly_insurance = annual_insurance / 12.0
        
        estimated_tax_ins_hoa = monthly_tax + monthly_insurance + hoa_monthly
        
        # Total monthly payment
        total_monthly_payment = principal_interest_payment + estimated_tax_ins_hoa
        
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_3",
            step_name="Cost Estimation",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "loan_amount": loan_amount,
                "interest_rate": interest_rate,
                "term_years": term_years,
            },
            outputs={
                "principal_interest_payment": principal_interest_payment,
                "estimated_tax_ins_hoa": estimated_tax_ins_hoa,
                "total_monthly_payment": total_monthly_payment,
            },
        )
    except Exception as e:
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_3",
            step_name="Cost Estimation",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            error=str(e)[:200],
        )
        raise
    
    # Step 4: Risk Metrics
    step_start = perf_counter()
    try:
        # Calculate DTI ratio
        dti_ratio = calc_dti_ratio(
            monthly_payment=total_monthly_payment,
            monthly_debts=other_debts_monthly,
            annual_income=annual_income,
        )
        
        # Calculate safe payment band based on DTI thresholds
        # Adjust thresholds based on risk preference
        if risk_preference == "conservative":
            target_dti = MORTGAGE_RULES["dti_low_threshold"] * 0.9
        elif risk_preference == "aggressive":
            target_dti = MORTGAGE_RULES["dti_medium_threshold"] * 1.05
        else:  # neutral
            target_dti = MORTGAGE_RULES["dti_low_threshold"]
        
        max_safe_payment = monthly_income * target_dti - other_debts_monthly
        max_safe_payment = max(0.0, max_safe_payment)  # Ensure non-negative
        
        # Min safe payment (using a lower threshold, e.g., 20% DTI)
        min_safe_payment = monthly_income * 0.20 - other_debts_monthly
        min_safe_payment = max(0.0, min_safe_payment)
        
        safe_payment_band = (min_safe_payment, max_safe_payment)
        
        # Classify stress band
        stress_band = _classify_stress_band(
            dti_ratio=dti_ratio,
            risk_preference=risk_preference,
            safe_payment_band=safe_payment_band,
            total_monthly_payment=total_monthly_payment,
        )
        
        # Build hard warning if needed (reuse existing function)
        # Create a dummy plan for hard warning check
        dummy_plan = MortgagePlan(
            plan_id="dummy",
            name="Stress Check Plan",
            monthly_payment=total_monthly_payment,
            interest_rate=interest_rate,
            loan_amount=loan_amount,
            term_years=term_years,
            dti_ratio=dti_ratio,
            risk_level=assess_risk_level(dti_ratio),
            pros=[],
            cons=[],
        )
        
        # Create max affordability for comparison
        max_aff = None
        try:
            affordability_result = compute_max_affordability(
                annual_income=annual_income,
                monthly_debts=other_debts_monthly,
                interest_rate_pct=interest_rate,
                target_dti=target_dti,
                term_years=term_years,
                down_payment_pct=down_payment_pct,
            )
            max_aff = MaxAffordabilitySummary(
                max_monthly_payment=affordability_result["max_monthly_payment"],
                max_loan_amount=affordability_result["max_loan_amount"],
                max_home_price=affordability_result["max_home_price"],
                assumed_interest_rate=interest_rate,
                target_dti=target_dti,
            )
        except Exception:
            pass  # Ignore if max affordability calculation fails
        
        hard_warning = build_hard_warning_if_needed(
            plans=[dummy_plan],
            max_aff=max_aff,
            target_purchase_price=list_price,
        )
        
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_4",
            step_name="Risk Assessment",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={
                "total_monthly_payment": total_monthly_payment,
                "other_debts_monthly": other_debts_monthly,
                "annual_income": annual_income,
            },
            outputs={
                "dti_ratio": dti_ratio,
                "stress_band": stress_band,
                "hard_warning_exists": hard_warning is not None,
            },
        )
    except Exception as e:
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_4",
            step_name="Risk Assessment",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            error=str(e)[:200],
        )
        raise
    
    # Step 5: Build Snapshots
    step_start = perf_counter()
    try:
        # Wallet snapshot
        wallet_snapshot = {
            "monthly_income": monthly_income,
            "annual_income": annual_income,
            "other_debts_monthly": other_debts_monthly,
            "safe_payment_band": {
                "min_safe": safe_payment_band[0],
                "max_safe": safe_payment_band[1],
            },
            "risk_preference": risk_preference,
        }
        
        # Home snapshot
        home_snapshot = {
            "list_price": list_price,
            "down_payment_pct": down_payment_pct,
            "loan_amount": loan_amount,
            "zip_code": req.zip_code,
            "state": req.state,
            "hoa_monthly": hoa_monthly,
            "tax_rate_est": tax_rate,
            "insurance_ratio_est": insurance_rate,
        }
        
        # Build case state
        case_state = CaseState(
            case_id=case_id,
            timestamp=start_ts,
            inputs={
                "monthly_income": monthly_income,
                "other_debts_monthly": other_debts_monthly,
                "list_price": list_price,
                "down_payment_pct": down_payment_pct,
                "state": req.state,
                "zip_code": req.zip_code,
            },
            plans=[dummy_plan],  # Include dummy plan for consistency
            max_affordability=max_aff,
            risk_summary={
                "dti_ratio": dti_ratio,
                "stress_band": stress_band,
                "hard_warning": hard_warning,
            },
        )
        
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_6",
            step_name="Snapshot Assembly",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs={},
            outputs={
                "case_state_created": True,
                "wallet_snapshot_keys": list(wallet_snapshot.keys()),
                "home_snapshot_keys": list(home_snapshot.keys()),
            },
        )
    except Exception as e:
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_6",
            step_name="Snapshot Assembly",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            error=str(e)[:200],
        )
        raise
    
    # Compute rule-based approval score (wrap in try-except to avoid breaking the whole stress check)
    rule_approval_score = None
    try:
        rule_approval_score = compute_rule_based_approval_score(
            stress_band=stress_band,
            dti_ratio=dti_ratio,
            wallet_snapshot=wallet_snapshot,
            home_snapshot=home_snapshot,
        )
    except Exception as e:
        # Log but don't fail - approval_score will remain None
        logger.warning(f"Failed to compute rule-based approval_score: {e}", exc_info=True)
    
    approval_score = rule_approval_score  # Will be updated with ML adjustment below if enabled
    
    # Compute risk assessment (wrap in try-except to avoid breaking the whole stress check)
    # We need to construct a temporary StressCheckResponse to pass to assess_risk
    # since assess_risk prefers stress_response over case_state for completeness
    risk_assessment: Optional[RiskAssessment] = None
    try:
        # Construct a temporary stress_response for risk assessment
        # This will be replaced by the full response below
        temp_stress_response = StressCheckResponse(
            total_monthly_payment=round(total_monthly_payment, 2),
            principal_interest_payment=round(principal_interest_payment, 2),
            estimated_tax_ins_hoa=round(estimated_tax_ins_hoa, 2),
            dti_ratio=round(dti_ratio, 4),
            stress_band=stress_band,
            hard_warning=hard_warning,
            wallet_snapshot=wallet_snapshot,
            home_snapshot=home_snapshot,
            case_state=case_state,
            agent_steps=agent_steps,
            llm_explanation=None,
            assumed_interest_rate_pct=interest_rate,
            assumed_tax_rate_pct=tax_rate * 100.0,
            assumed_insurance_ratio_pct=insurance_rate * 100.0,
            approval_score=approval_score,
            risk_assessment=None,  # Not set yet
        )
        risk_assessment = assess_risk(stress_response=temp_stress_response)
        if risk_assessment and risk_assessment.hard_block:
            logger.warning(
                f"level=WARN risk_hard_block_triggered "
                f"risk_flags={risk_assessment.risk_flags} "
                f"dti={dti_ratio:.2%}"
            )
    except Exception as e:
        # Log but don't fail - risk_assessment will remain None
        logger.warning(f"Failed to compute risk_assessment: {e}", exc_info=True)
    
    # Build response
    # Note: interest_rate is in percent (e.g., 6.0 for 6.0%)
    # tax_rate and insurance_rate are decimals (e.g., 0.012 for 1.2%), convert to percent for response
    stress_response = StressCheckResponse(
        total_monthly_payment=round(total_monthly_payment, 2),
        principal_interest_payment=round(principal_interest_payment, 2),
        estimated_tax_ins_hoa=round(estimated_tax_ins_hoa, 2),
        dti_ratio=round(dti_ratio, 4),
        stress_band=stress_band,
        hard_warning=hard_warning,
        wallet_snapshot=wallet_snapshot,
        home_snapshot=home_snapshot,
        case_state=case_state,
        agent_steps=agent_steps,
        llm_explanation=None,  # Can be added later via helper
        assumed_interest_rate_pct=interest_rate,  # Already in percent
        assumed_tax_rate_pct=tax_rate * 100.0,  # Convert from decimal to percent
        assumed_insurance_ratio_pct=insurance_rate * 100.0,  # Convert from decimal to percent
        approval_score=approval_score,
        risk_assessment=risk_assessment,
    )
    
    # Step 5: Lightweight reflection/planner step - suggest what-if scenarios
    step_start = perf_counter()
    step_inputs = {
        "stress_band": stress_response.stress_band,
        "dti_ratio": stress_response.dti_ratio,
        "total_monthly_payment": stress_response.total_monthly_payment,
        "safe_payment_band": stress_response.wallet_snapshot.get("safe_payment_band")
        if stress_response.wallet_snapshot
        else None,
    }
    suggested: List[SuggestedScenario] = []
    try:
        suggested = _suggest_scenarios_for_stress_result(stress_response)
        if suggested:
            stress_response.recommended_scenarios = suggested
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_5",
            step_name="Reflection / Planner",
            status="completed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs=step_inputs,
            outputs={
                "recommended_count": len(suggested),
                "scenario_keys": [scenario.scenario_key for scenario in suggested],
            },
        )
    except Exception as e:
        step_end = perf_counter()
        _record_step(
            agent_steps=agent_steps,
            step_id="step_5",
            step_name="Reflection / Planner",
            status="failed",
            duration_ms=(step_end - step_start) * 1000.0,
            inputs=step_inputs,
            error=str(e)[:200],
        )
        # Fail-safe: do NOT break the main response if suggestion logic errors
        logger.exception("Failed to build recommended scenarios: %s", e)
    
    # Ensure stress_response.agent_steps reflects new entries and maintain natural ordering
    def _step_order(step: AgentStep) -> float:
        try:
            return int(step.step_id.split("_")[1])
        except Exception:
            return float("inf")
    
    agent_steps.sort(key=_step_order)
    stress_response.agent_steps = agent_steps
    
    # Apply ML adjustment to approval score if enabled (after response is built)
    if stress_response.approval_score is not None:
        try:
            # Try to import get_use_ml_approval_score, fallback gracefully if not available
            try:
                from services.core.settings import get_use_ml_approval_score
                use_ml = get_use_ml_approval_score()
            except ImportError:
                # Fallback: check environment variable directly if import fails
                use_ml = os.getenv("USE_ML_APPROVAL_SCORE", "false").lower() in ("1", "true", "yes")
                logger.debug(
                    "[ML_APPROVAL] Could not import get_use_ml_approval_score, "
                    f"using env var directly: USE_ML_APPROVAL_SCORE={use_ml}"
                )
            
            if use_ml:
                try:
                    from services.fiqa_api.mortgage.approval.ml_approval_score import (
                        predict_ml_approval_prob,
                        MLApprovalUnavailable,
                    )
                    from services.fiqa_api.mortgage.approval.hybrid_score import (
                        combine_rule_and_ml,
                    )
                    
                    # Predict ML approval probability
                    approve_prob = predict_ml_approval_prob(stress_response)
                    if approve_prob is not None:
                        # Combine rule-based and ML scores
                        final_approval = combine_rule_and_ml(
                            stress_response.approval_score,
                            approve_prob,
                        )
                        stress_response.approval_score = final_approval
                        logger.debug(
                            f"[ML_APPROVAL] Combined rule+ML score: "
                            f"rule_score={rule_approval_score.score:.1f}, "
                            f"ml_prob={approve_prob:.3f}, "
                            f"final_score={final_approval.score:.1f}"
                        )
                    
                except ImportError as e:
                    logger.warning(f"ML approval score module not available: {e}")
                except MLApprovalUnavailable as e:
                    logger.warning(
                        f"ML approval score unavailable, falling back to rule-based only: {e}"
                    )
                except Exception as e:
                    logger.exception(
                        f"Unexpected error in ML approval score adjustment: {e}"
                    )
        except Exception as e:
            logger.exception(f"Unexpected error checking ML approval score config: {e}")
    
    return stress_response


# ========================================
# Strategy Lab Logic
# ========================================

def run_strategy_lab(
    req: StressCheckRequest,
    *,
    max_scenarios: int = 3,
) -> StrategyLabResult:
    """
    Given a baseline StressCheckRequest, generate a small set of alternative
    plan scenarios (e.g., lower price, higher down payment, different risk
    preference), run stress checks for each, and return a structured summary.
    
    No LLM calls. Pure Python + existing tools.
    
    Args:
        req: Baseline StressCheckRequest
        max_scenarios: Maximum number of scenarios to generate (default: 3)
    
    Returns:
        StrategyLabResult with baseline metrics and scenario comparisons
    """
    # Step 1: Run baseline stress check
    try:
        baseline_response = run_stress_check(req)
    except Exception as e:
        logger.error(f"[STRATEGY_LAB] Failed to run baseline stress check: {e}")
        # Return empty result with minimal baseline info
        return StrategyLabResult(
            baseline_stress_band=None,
            baseline_dti=None,
            baseline_total_payment=None,
            baseline_approval_score=None,
            baseline_risk_assessment=None,
            scenarios=[],
        )
    
    # Extract baseline metrics
    baseline_stress_band = baseline_response.stress_band
    baseline_dti = baseline_response.dti_ratio
    baseline_total_payment = baseline_response.total_monthly_payment
    baseline_approval_score = baseline_response.approval_score
    baseline_risk_assessment = baseline_response.risk_assessment
    
    # Step 2: Generate scenarios based on heuristics
    scenarios: List[StrategyScenario] = []
    
    # Scenario A: Lower price by 10%
    try:
        baseline_price = req.list_price
        new_price = baseline_price * 0.9  # 10% reduction
        
        # Round to nearest 5000 for cleaner numbers
        new_price = round(new_price / 5000) * 5000
        if new_price < 50000:  # Minimum reasonable price
            new_price = max(50000, round(new_price / 1000) * 1000)
        
        price_delta_abs = new_price - baseline_price
        price_delta_pct = (new_price - baseline_price) / baseline_price if baseline_price > 0 else 0.0
        
        # Create modified request
        scenario_req = StressCheckRequest(
            monthly_income=req.monthly_income,
            other_debts_monthly=req.other_debts_monthly,
            list_price=new_price,
            down_payment_pct=req.down_payment_pct,
            zip_code=req.zip_code,
            state=req.state,
            hoa_monthly=req.hoa_monthly,
            tax_rate_est=req.tax_rate_est,
            insurance_ratio_est=req.insurance_ratio_est,
            risk_preference=req.risk_preference,
            profile_id=req.profile_id,
        )
        
        scenario_response = run_stress_check(scenario_req)
        
        scenarios.append(
            StrategyScenario(
                id="lower_price_10",
                title="Lower price by 10%",
                description=f"Reduce listing price from ${baseline_price:,.0f} to ${new_price:,.0f}",
                price_delta_abs=price_delta_abs,
                price_delta_pct=price_delta_pct,
                down_payment_pct=None,
                risk_preference=None,
                note_tags=["lower_price"],
                stress_band=scenario_response.stress_band,
                dti_ratio=scenario_response.dti_ratio,
                total_payment=scenario_response.total_monthly_payment,
                approval_score=scenario_response.approval_score,
                risk_assessment=scenario_response.risk_assessment,
            )
        )
    except Exception as e:
        logger.warning(f"[STRATEGY_LAB] Failed to generate lower_price_10 scenario: {e}")
    
    # Scenario B: Increase down payment by 5 percentage points (if not already at 40%)
    try:
        baseline_down_pct = req.down_payment_pct or 0.20
        new_down_pct = min(0.40, baseline_down_pct + 0.05)  # Cap at 40%
        
        if new_down_pct > baseline_down_pct + 0.01:  # Only if meaningful increase
            scenario_req = StressCheckRequest(
                monthly_income=req.monthly_income,
                other_debts_monthly=req.other_debts_monthly,
                list_price=req.list_price,
                down_payment_pct=new_down_pct,
                zip_code=req.zip_code,
                state=req.state,
                hoa_monthly=req.hoa_monthly,
                tax_rate_est=req.tax_rate_est,
                insurance_ratio_est=req.insurance_ratio_est,
                risk_preference=req.risk_preference,
                profile_id=req.profile_id,
            )
            
            scenario_response = run_stress_check(scenario_req)
            
            scenarios.append(
                StrategyScenario(
                    id="increase_down_5",
                    title=f"Increase down payment to {new_down_pct*100:.0f}%",
                    description=f"Raise down payment from {baseline_down_pct*100:.0f}% to {new_down_pct*100:.0f}%",
                    price_delta_abs=None,
                    price_delta_pct=None,
                    down_payment_pct=new_down_pct,
                    risk_preference=None,
                    note_tags=["more_down"],
                    stress_band=scenario_response.stress_band,
                    dti_ratio=scenario_response.dti_ratio,
                    total_payment=scenario_response.total_monthly_payment,
                    approval_score=scenario_response.approval_score,
                    risk_assessment=scenario_response.risk_assessment,
                )
            )
    except Exception as e:
        logger.warning(f"[STRATEGY_LAB] Failed to generate increase_down_5 scenario: {e}")
    
    # Scenario C: More conservative risk preference (only if not already conservative)
    try:
        baseline_risk = req.risk_preference or "neutral"
        if baseline_risk != "conservative":
            scenario_req = StressCheckRequest(
                monthly_income=req.monthly_income,
                other_debts_monthly=req.other_debts_monthly,
                list_price=req.list_price,
                down_payment_pct=req.down_payment_pct,
                zip_code=req.zip_code,
                state=req.state,
                hoa_monthly=req.hoa_monthly,
                tax_rate_est=req.tax_rate_est,
                insurance_ratio_est=req.insurance_ratio_est,
                risk_preference="conservative",
                profile_id=req.profile_id,
            )
            
            scenario_response = run_stress_check(scenario_req)
            
            scenarios.append(
                StrategyScenario(
                    id="more_conservative_risk",
                    title="More conservative risk preference",
                    description="Use conservative risk preference for stricter DTI thresholds",
                    price_delta_abs=None,
                    price_delta_pct=None,
                    down_payment_pct=None,
                    risk_preference="conservative",
                    note_tags=["conservative"],
                    stress_band=scenario_response.stress_band,
                    dti_ratio=scenario_response.dti_ratio,
                    total_payment=scenario_response.total_monthly_payment,
                    approval_score=scenario_response.approval_score,
                    risk_assessment=scenario_response.risk_assessment,
                )
            )
    except Exception as e:
        logger.warning(f"[STRATEGY_LAB] Failed to generate more_conservative_risk scenario: {e}")
    
    # Sort scenarios by DTI ratio (lower DTI = safer = first)
    scenarios.sort(key=lambda s: s.dti_ratio if s.dti_ratio is not None else float('inf'))
    
    # Limit to max_scenarios
    scenarios = scenarios[:max_scenarios]
    
    # Build and return result
    return StrategyLabResult(
        baseline_stress_band=baseline_stress_band,
        baseline_dti=baseline_dti,
        baseline_total_payment=baseline_total_payment,
        baseline_approval_score=baseline_approval_score,
        baseline_risk_assessment=baseline_risk_assessment,
        scenarios=scenarios,
    )


# ========================================
# Single Home Agent Logic
# ========================================
#
# TODO: Safety Upgrade Integration Plan
# ======================================
# 1. After run_stress_check() in run_single_home_agent():
#    - Call run_safety_upgrade_flow(req.stress_request) to get SafetyUpgradeResult
#    - Pass safety_upgrade into SingleHomeAgentResponse
#    - Handle errors gracefully (log warning, continue with safety_upgrade=None)
#
# 2. In _generate_single_home_narrative():
#    - Add safety_upgrade: Optional[SafetyUpgradeResult] parameter
#    - Include safety_upgrade data in LLM prompt (structured JSON block)
#    - Update system prompt to explain how to use safety_upgrade suggestions:
#      * If baseline_is_tight_or_worse: explain why tight/high_risk, summarize primary_suggestion
#      * If safer_homes found: mention safer options but don't invent addresses/prices
#      * If baseline is loose/ok: reassure user, mention distance from tighter thresholds
#    - Remind LLM: DO NOT change numbers, only explain and suggest
#
# 3. Frontend integration:
#    - Add safety_upgrade field to SingleHomeAgentResponse type in api.types.ts
#    - In SingleHomeStressPage.tsx, conditionally show primary_suggestion under AI Answer
#    - Show title, notes, and delta_dti if present

def _generate_single_home_narrative(
    stress_result: StressCheckResponse,
    *,
    user_message: Optional[str] = None,
    safety_upgrade: Optional[SafetyUpgradeResult] = None,
    mortgage_programs: Optional[List[Dict[str, Any]]] = None,
    approval_score: Optional[ApprovalScore] = None,
    risk_assessment: Optional[RiskAssessment] = None,
) -> Tuple[Optional[str], Optional[List[str]], Optional[Dict[str, Any]]]:
    """
    Use LLM to turn a StressCheckResponse into:
    - borrower_narrative: short explanation
    - recommended_actions: 1-3 bullet point next steps
    - llm_usage: token stats etc
    
    IMPORTANT:
    - Must NEVER change any numeric values.
    - Must not promise loan approval.
    - Must respect existing safety / disclaimer style.
    
    Args:
        stress_result: StressCheckResponse instance (source of truth)
        user_message: Optional user question for context
        safety_upgrade: Optional SafetyUpgradeResult with structured upgrade suggestions
        mortgage_programs: Optional list of mortgage program dicts to reference in the explanation
        approval_score: Optional ApprovalScore with mortgage approval likelihood information
        risk_assessment: Optional RiskAssessment with standardized risk flags, hard_block, and soft_warning
    
    Returns:
        Tuple of (borrower_narrative, recommended_actions, llm_usage) or (None, None, None) if disabled/failed
    """
    from services.fiqa_api.utils.llm_client import is_llm_generation_enabled
    from services.fiqa_api.clients import get_openai_client
    from services.fiqa_api.utils.env_loader import get_llm_conf
    
    # Check if LLM generation is enabled
    if not is_llm_generation_enabled():
        logger.info("[SINGLE_HOME_AGENT_LLM] LLM generation disabled by LLM_GENERATION_ENABLED env")
        return None, None, None
    
    # Get OpenAI client
    openai_client = get_openai_client()
    if openai_client is None:
        logger.info("[SINGLE_HOME_AGENT_LLM] OpenAI client not available")
        return None, None, None
    
    # Get LLM configuration
    try:
        llm_conf = get_llm_conf()
        model = llm_conf.get("model", "gpt-4o-mini")
        max_tokens = llm_conf.get("max_tokens", 512)
        input_per_mtok = llm_conf.get("input_per_mtok")
        output_per_mtok = llm_conf.get("output_per_mtok")
    except Exception as e:
        logger.warning(f"[SINGLE_HOME_AGENT_LLM] Failed to load LLM config: {e}")
        return None, None, None
    
    try:
        # Build system prompt - structured, short, human-readable format
        system_prompt = (
            "You are a mortgage AI assistant. Your job is to explain stress check results in simple, structured language. "
            "You must NOT recalculate any numbers or change values from the provided data. "
            "You only explain and suggest based on the computed results.\n\n"
            "Output Format Requirements:\n"
            "You must output plain text (NOT JSON, NOT Markdown with # headers) with exactly two sections:\n\n"
            "1. Borrower Narrative (2-3 short paragraphs, each 1-3 sentences):\n"
            "- First paragraph: One sentence summary stating the current stress band and whether this home is generally affordable or tight. "
            "If approval_score is provided, include ONE short sentence about approval likelihood (e.g., \"Based on your financial profile, loan approval appears [likely/borderline/unlikely] with a score of [X] out of 100.\"). "
            "IMPORTANT: When mentioning the score, use the integer value from the score field (e.g., if score is 78.5, say '78 out of 100', NOT '78.5 out of 100' or '0.785 out of 100'). "
            "Keep this sentence factual and do not promise approval.\n"
            "- Second paragraph: Explain DTI ratio and monthly payment relative to the safe payment range. Keep it concise (1-2 sentences).\n"
            "- Third paragraph (ONLY if safety_upgrade is provided and has actionable info): Mention safety upgrade suggestions in 1 sentence. "
            "For example: \"We searched ZIP [code] and found safer options that could reduce your DTI by [X] percentage points.\" "
            "Or: \"We searched ZIP [code] but couldn't find clearly safer homes; consider increasing down payment or exploring nearby ZIPs.\"\n"
            "- If safety_upgrade is None or not useful, omit the third paragraph entirely.\n\n"
            "2. Recommended Actions (maximum 3 bullets, each under 120 characters):\n"
            "- Prioritize: adjust down payment, adjust target price, explore safer homes, or modify loan profile.\n"
            "- If approval_score is provided and bucket is \"borderline\" or \"unlikely\", optionally include ONE bullet about improving approval odds (e.g., \"Consider reducing debt or increasing down payment to improve approval likelihood\").\n"
            "- Use the format: \"- [action]\" (one bullet per line).\n"
            "- Each bullet must be actionable and under 120 characters.\n"
            "- If safety_upgrade.primary_suggestion exists, incorporate its suggestions into these bullets.\n\n"
            "Formatting Rules:\n"
            "- Use blank lines to separate paragraphs within borrower_narrative.\n"
            "- Use \"- \" for bullets (no markdown headers like ##).\n"
            "- Total borrower_narrative should be 2-3 paragraphs (3-6 sentences total).\n"
            "- Keep recommended_actions to exactly 1-3 bullets.\n"
            "- Use short sentences. Avoid lengthy disclaimers.\n"
            "- Do NOT include a disclaimer in the output (it will be added separately).\n\n"
            "Approval Score Data Structure (if provided):\n"
            "- score: float from 0-100 (approval likelihood score, where 0-100 is the full range)\n"
            "- bucket: \"likely\", \"borderline\", or \"unlikely\"\n"
            "- reasons: list of machine-readable reason tags\n"
            "- Include approval information ONLY in the first paragraph of Borrower Narrative (one short sentence).\n"
            "- When mentioning the score, ALWAYS use the integer value (rounded) and say \"X out of 100\" (e.g., \"78 out of 100\", NOT \"0.78 out of 100\" or \"78.5 out of 100\").\n"
            "- Do NOT promise loan approval or guarantee any outcome.\n"
            "- Use factual language like \"appears likely\" or \"may be challenging\" rather than definitive statements.\n\n"
            "Safety Upgrade Data Structure:\n"
            "- baseline_band: loose/ok/tight/high_risk\n"
            "- baseline_dti: DTI ratio from baseline stress check\n"
            "- baseline_is_tight_or_worse: boolean indicating if baseline is tight or high_risk\n"
            "- primary_suggestion: object with title, details, delta_dti (DTI improvement), target_price, notes\n"
            "- safer_homes.candidates: list of safer home candidates (each has listing.title, list_price, stress_band, dti_ratio)\n"
            "- Use only the first 1-2 safer home candidates if listing them.\n\n"
            "Risk Assessment Guidelines (if provided):\n"
            "- risk_assessment.hard_block = True: This is a HIGH RISK scenario. You MUST:\n"
            "  * State clearly in the FIRST paragraph that this scenario is high risk and strongly recommend caution.\n"
            "  * Do NOT encourage the user to proceed with this plan.\n"
            "  * Emphasize the need to reduce purchase price, increase down payment, or explore safer alternatives.\n"
            "  * Use direct, warning language (e.g., \"This scenario presents significant financial risk\", \"We strongly advise against proceeding with this plan\").\n"
            "- risk_assessment.soft_warning = True: This scenario requires CAUTION. You should:\n"
            "  * Mention the need for careful consideration in your explanation.\n"
            "  * Suggest optimizations (reduce price, increase down payment, etc.) but allow that the plan may still be workable.\n"
            "  * Use cautious but not alarming language (e.g., \"This scenario requires careful consideration\", \"Consider optimizing your financial profile\").\n"
            "- risk_flags: These are machine-readable risk identifiers (e.g., 'high_dti', 'negative_cashflow', 'high_ltv').\n"
            "  * Do NOT list all flags verbatim - instead, incorporate their meaning naturally into your explanation.\n"
            "  * Use the risk_assessment structure to guide your tone and recommendations, not to re-analyze risks yourself.\n\n"
            "Tone:\n"
            "- Friendly but professional.\n"
            "- For hard_block=True: Direct and warning - strongly advise against proceeding.\n"
            "- For soft_warning=True: Cautious but not alarming - suggest optimizations.\n"
            "- For high_risk/tight: cautious but not panicky.\n"
            "- For loose/ok: reassuring and encouraging.\n"
        )

        program_lines: List[str] = []
        if mortgage_programs:
            for program in mortgage_programs[:3]:
                if hasattr(program, "model_dump"):
                    data = program.model_dump() or {}
                elif isinstance(program, dict):
                    data = program
                else:
                    data = getattr(program, "__dict__", {}) or {}
                name = (
                    data.get("name")
                    or data.get("program_name")
                    or data.get("title")
                    or data.get("id")
                    or "Mortgage program"
                )
                location = (
                    data.get("location_state")
                    or data.get("state")
                    or data.get("location")
                    or ""
                )
                max_dti = data.get("max_dti")
                max_dti_display = None
                if isinstance(max_dti, (int, float)):
                    max_dti_display = f"{max_dti * 100:.0f}%"
                elif isinstance(max_dti, str) and max_dti.strip():
                    max_dti_display = max_dti.strip()

                details: List[str] = []
                if location:
                    details.append(f"state {location}")
                if max_dti_display:
                    details.append(f"max DTI ~ {max_dti_display}")

                line = f"- {name}"
                if details:
                    line += f" ({', '.join(details)})"
                program_lines.append(line)

        if program_lines:
            system_prompt += (
                "\n\nYou are also given a list of candidate mortgage assistance programs. "
                "If relevant, briefly mention how one of them could help reduce stress "
                "by allowing higher DTI or other flexibilities, but do NOT promise eligibility."
            )
        
        # Build user prompt with structured data
        user_prompt_parts = []
        
        # User question (if provided)
        if user_message and user_message.strip():
            user_prompt_parts.append("User Question:")
            user_prompt_parts.append(user_message)
            user_prompt_parts.append("")
            user_prompt_parts.append("Please explain the stress check results and provide recommendations.")
        else:
            user_prompt_parts.append("Please explain this stress check result and provide recommendations.")
        
        user_prompt_parts.append("")
        user_prompt_parts.append("Stress Check Results:")
        
        # Extract key metrics from stress_result
        stress_band_display = stress_result.stress_band.upper().replace("_", " ")
        user_prompt_parts.append(f"  stress_band: {stress_result.stress_band} ({stress_band_display})")
        user_prompt_parts.append(f"  total_monthly_payment: ${stress_result.total_monthly_payment:,.2f}")
        user_prompt_parts.append(f"  dti_ratio: {stress_result.dti_ratio:.1%} ({stress_result.dti_ratio * 100:.1f}%)")
        
        # Wallet snapshot
        wallet = stress_result.wallet_snapshot or {}
        monthly_income = wallet.get("monthly_income")
        safe_band = wallet.get("safe_payment_band", {})
        min_safe = safe_band.get("min_safe", 0)
        max_safe = safe_band.get("max_safe", 0)
        
        if monthly_income:
            user_prompt_parts.append(f"  wallet_snapshot.monthly_income: ${monthly_income:,.2f}")
        if min_safe > 0 or max_safe > 0:
            user_prompt_parts.append(f"  wallet_snapshot.safe_payment_band: ${min_safe:,.2f} - ${max_safe:,.2f}")
        
        # Home snapshot
        home = stress_result.home_snapshot or {}
        list_price = home.get("list_price")
        zip_code = home.get("zip_code")
        state = home.get("state")
        
        if list_price:
            user_prompt_parts.append(f"  home_snapshot.list_price: ${list_price:,.0f}")
        if zip_code:
            user_prompt_parts.append(f"  home_snapshot.zip_code: {zip_code}")
        if state:
            user_prompt_parts.append(f"  home_snapshot.state: {state}")
        
        # Hard warning if present
        if stress_result.hard_warning:
            user_prompt_parts.append("")
            user_prompt_parts.append("⚠️ RISK WARNING:")
            user_prompt_parts.append(f"  {stress_result.hard_warning}")
            user_prompt_parts.append("")
            user_prompt_parts.append("NOTE: You MUST emphasize this high risk in your explanation. Use direct, clear language.")
        
        # Risk assessment if provided
        if risk_assessment:
            user_prompt_parts.append("")
            user_prompt_parts.append("Risk Assessment:")
            user_prompt_parts.append(f"  hard_block: {risk_assessment.hard_block}")
            user_prompt_parts.append(f"  soft_warning: {risk_assessment.soft_warning}")
            if risk_assessment.risk_flags:
                user_prompt_parts.append(f"  risk_flags: {', '.join(risk_assessment.risk_flags)}")
            user_prompt_parts.append("")
            if risk_assessment.hard_block:
                user_prompt_parts.append("⚠️ CRITICAL: risk_assessment.hard_block = True")
                user_prompt_parts.append("  You MUST start your Borrower Narrative by clearly stating this is a HIGH RISK scenario.")
                user_prompt_parts.append("  You MUST strongly recommend NOT proceeding with this plan as-is.")
                user_prompt_parts.append("  Use direct, warning language. Do NOT encourage the user to continue.")
                user_prompt_parts.append("  Emphasize the need to reduce purchase price, increase down payment, or explore safer alternatives.")
            elif risk_assessment.soft_warning:
                user_prompt_parts.append("⚠️ NOTE: risk_assessment.soft_warning = True")
                user_prompt_parts.append("  You should mention the need for careful consideration in your explanation.")
                user_prompt_parts.append("  Suggest optimizations but allow that the plan may still be workable with adjustments.")
                user_prompt_parts.append("  Use cautious but not alarming language.")
            user_prompt_parts.append("")
            user_prompt_parts.append("IMPORTANT: Use the risk_assessment structure above to guide your tone and recommendations.")
            user_prompt_parts.append("Do NOT recalculate risks yourself - trust the provided risk_assessment flags and warnings.")
        
        # Approval score if provided
        if approval_score:
            user_prompt_parts.append("")
            user_prompt_parts.append("Approval Score:")
            # Format score as integer (0-100 range) for clarity
            score_int = int(round(approval_score.score))
            user_prompt_parts.append(f"  score: {score_int} (out of 100, range 0-100)")
            user_prompt_parts.append(f"  bucket: {approval_score.bucket}")
            if approval_score.reasons:
                user_prompt_parts.append(f"  reasons: {', '.join(approval_score.reasons)}")
            user_prompt_parts.append("")
            user_prompt_parts.append("NOTE: Include ONE short sentence about approval likelihood in the first paragraph of Borrower Narrative. "
                                     "Use factual language (e.g., 'appears likely', 'may be challenging') and do NOT promise approval. "
                                     f"When mentioning the score, use the integer value {score_int} out of 100 (e.g., 'with a score of {score_int} out of 100').")
        
        # Safety upgrade data if present - structured clearly
        if safety_upgrade:
            user_prompt_parts.append("")
            user_prompt_parts.append("Safety Upgrade Analysis:")
            user_prompt_parts.append(f"  baseline_band: {safety_upgrade.baseline_band}")
            user_prompt_parts.append(f"  baseline_dti: {safety_upgrade.baseline_dti:.1%} ({safety_upgrade.baseline_dti * 100:.1f}%)" if safety_upgrade.baseline_dti else "  baseline_dti: N/A")
            user_prompt_parts.append(f"  baseline_is_tight_or_worse: {safety_upgrade.baseline_is_tight_or_worse}")
            
            if safety_upgrade.baseline_zip_code:
                user_prompt_parts.append(f"  baseline_zip_code: {safety_upgrade.baseline_zip_code}")
            if safety_upgrade.baseline_state:
                user_prompt_parts.append(f"  baseline_state: {safety_upgrade.baseline_state}")
            
            # Primary suggestion
            if safety_upgrade.primary_suggestion:
                user_prompt_parts.append("")
                user_prompt_parts.append("  primary_suggestion:")
                user_prompt_parts.append(f"    title: {safety_upgrade.primary_suggestion.title}")
                user_prompt_parts.append(f"    details: {safety_upgrade.primary_suggestion.details}")
                if safety_upgrade.primary_suggestion.delta_dti is not None:
                    user_prompt_parts.append(f"    delta_dti: {safety_upgrade.primary_suggestion.delta_dti:.1%} improvement")
                if safety_upgrade.primary_suggestion.target_price is not None:
                    user_prompt_parts.append(f"    target_price: ${safety_upgrade.primary_suggestion.target_price:,.0f}")
                if safety_upgrade.primary_suggestion.notes:
                    user_prompt_parts.append(f"    notes: {', '.join(safety_upgrade.primary_suggestion.notes)}")
            
            # Safer homes candidates (only first 1-2)
            if safety_upgrade.safer_homes and safety_upgrade.safer_homes.candidates:
                user_prompt_parts.append("")
                user_prompt_parts.append(f"  safer_homes.candidates (showing first {min(2, len(safety_upgrade.safer_homes.candidates))} of {len(safety_upgrade.safer_homes.candidates)}):")
                for candidate in safety_upgrade.safer_homes.candidates[:2]:
                    user_prompt_parts.append(f"    - listing.title: {candidate.listing.title}")
                    user_prompt_parts.append(f"      list_price: ${candidate.listing.list_price:,.0f}")
                    user_prompt_parts.append(f"      stress_band: {candidate.stress_band}")
                    if candidate.dti_ratio is not None:
                        user_prompt_parts.append(f"      dti_ratio: {candidate.dti_ratio:.1%} ({candidate.dti_ratio * 100:.1f}%)")
                    if candidate.comment:
                        user_prompt_parts.append(f"      comment: {candidate.comment}")

        if program_lines:
            user_prompt_parts.append("")
            user_prompt_parts.append("Mortgage Programs Context:")
            user_prompt_parts.append("These mortgage programs might help:")
            user_prompt_parts.extend(program_lines)
        
        user_prompt_parts.append("")
        user_prompt_parts.append("Output Instructions:")
        user_prompt_parts.append("Please provide your response in the structured format described in the system prompt:")
        user_prompt_parts.append("- Borrower Narrative: 2-3 short paragraphs (first: summary, second: DTI/payment explanation, third: safety upgrade if available)")
        user_prompt_parts.append("- Recommended Actions: 1-3 bullets, each under 120 characters")
        user_prompt_parts.append("")
        user_prompt_parts.append("CRITICAL: Use the EXACT numbers provided above. Do NOT change, recalculate, or invent any values.")
        user_prompt_parts.append("Output plain text with blank lines separating paragraphs. Do NOT output JSON or Markdown headers.")
        
        user_prompt = "\n".join(user_prompt_parts)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        # Call LLM directly (synchronous call) with timeout
        LLM_EXPLANATION_TIMEOUT_SEC = 20.0
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens,
                timeout=LLM_EXPLANATION_TIMEOUT_SEC,
            )
        except (TimeoutError, Exception) as e:
            # Log timeout/error and return fallback
            error_type = type(e).__name__
            if "timeout" in str(e).lower() or isinstance(e, TimeoutError):
                logger.warning(
                    f'{{"event": "llm_explanation_timeout", "error_type": "{error_type}"}}'
                )
            else:
                logger.warning(
                    f'{{"event": "llm_explanation_error", "error_type": "{error_type}"}}',
                    exc_info=True
                )
            # Return fallback narrative
            return (
                "The system completed the numeric stress check, but AI explanation is temporarily unavailable. Please review the numeric results above.",
                None,
                None
            )
        
        # Extract content
        explanation = ""
        if response.choices and len(response.choices) > 0:
            explanation = response.choices[0].message.content or ""
        
        # Parse plain text structured response
        borrower_narrative = None
        recommended_actions = None
        
        if explanation:
            # Use the entire response as borrower_narrative (structured text format)
            borrower_narrative = explanation.strip()
            
            # Extract recommended_actions from the "Recommended Actions" section
            # Look for lines that start with "- " after "Recommended Actions"
            try:
                lines = explanation.split("\n")
                in_recommended_section = False
                actions = []
                
                for line in lines:
                    line_lower = line.lower().strip()
                    # Check if we're entering the recommended section
                    if "recommended actions" in line_lower or "recommended actions:" in line_lower:
                        in_recommended_section = True
                        continue
                    
                    # Check if we're leaving the recommended section (blank line followed by non-bullet text, or end of text)
                    if in_recommended_section:
                        # Extract bullet points that start with "- "
                        if line.strip().startswith("- "):
                            action_text = line.strip()[2:].strip()  # Remove "- " prefix
                            if action_text and len(action_text) <= 120:  # Enforce 120 char limit
                                actions.append(action_text)
                        elif line.strip() and not line.strip().startswith("- "):
                            # Non-bullet text means we've left the section
                            break
                
                if actions:
                    recommended_actions = actions[:3]  # Limit to 3 actions max
            except Exception as e:
                logger.warning(f"[SINGLE_HOME_AGENT_LLM] Failed to extract recommended_actions from structured text: {e}")
                recommended_actions = None
        
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
            "prompt_tokens": tokens_in,
            "completion_tokens": tokens_out,
            "total_tokens": tokens_total,
            "cost_usd_est": cost_usd_est,
            "model": model,
        }
        
        logger.info(
            f"[SINGLE_HOME_AGENT_LLM] LLM narrative generated: "
            f"tokens={tokens_total}, cost=${cost_usd_est or 0.0:.6f}, model={model}"
        )
        
        return borrower_narrative, recommended_actions, usage_dict
        
    except Exception as e:
        logger.exception("[SINGLE_HOME_AGENT_LLM_ERROR] Failed to generate LLM narrative")
        return None, None, None


def run_single_home_agent(req: SingleHomeAgentRequest, request_id: Optional[str] = None) -> SingleHomeAgentResponse:
    """
    Single Home Agent: thin "reason + explain" wrapper over run_stress_check.
    
    This function:
    1. Calls run_stress_check with the provided stress_request
    2. Runs safety upgrade flow to get structured upgrade suggestions
    3. Optionally generates LLM narrative if LLM_GENERATION_ENABLED is true
    4. Returns SingleHomeAgentResponse with stress_result + narrative + safety_upgrade
    
    Designed for single-home borrower UX and demoing agentic behavior.
    The stress_result is the source of truth - narrative only explains, never changes numbers.
    
    Now supports an optional LangGraph-based implementation controlled
    by USE_LANGGRAPH_SINGLE_HOME feature flag.
    
    Args:
        req: SingleHomeAgentRequest with stress_request and optional user_message
        request_id: Optional request ID for logging (generated if not provided)
    
    Returns:
        SingleHomeAgentResponse with stress_result, borrower_narrative, recommended_actions, llm_usage, and safety_upgrade
    """
    # Generate request_id if not provided
    if request_id is None:
        request_id = uuid.uuid4().hex
    
    overall_start = perf_counter()
    
    if USE_LANGGRAPH_SINGLE_HOME:
        # 走 LangGraph 版本
        from services.fiqa_api.mortgage.graphs import run_single_home_graph
        langgraph_start = perf_counter()
        result = run_single_home_graph(req)
        langgraph_duration_ms = (perf_counter() - langgraph_start) * 1000
        overall_duration_ms = (perf_counter() - overall_start) * 1000
        logger.info(
            f'{{"event": "langgraph_run", "request_id": "{request_id}", '
            f'"duration_ms": {langgraph_duration_ms:.1f}, "overall_duration_ms": {overall_duration_ms:.1f}, '
            f'"stress_band": "{result.stress_result.stress_band}", "dti": {result.stress_result.dti_ratio:.3f}}}'
        )
        return result
    
    # === 原有实现保留（不要删除）===
    # 之前顺序：run_stress_check → run_safety_upgrade_flow → (optional LLM)
    
    # Step 1: Extract StressCheckRequest from req.stress_request
    stress_request = req.stress_request
    
    # Step 2: Call run_stress_check directly (Python function, not HTTP)
    stress_check_start = perf_counter()
    stress_result = run_stress_check(stress_request, request_id=request_id)
    stress_check_duration_ms = (perf_counter() - stress_check_start) * 1000
    logger.info(
        f'{{"event": "stress_check_done", "request_id": "{request_id}", '
        f'"duration_ms": {stress_check_duration_ms:.1f}, "stress_band": "{stress_result.stress_band}", '
        f'"dti": {stress_result.dti_ratio:.3f}}}'
    )
    
    # Step 3: Run safety upgrade flow to get structured suggestions
    safety_upgrade = None
    try:
        safety_upgrade = run_safety_upgrade_flow(
            req=stress_request,
            max_candidates=5,
        )
        logger.info(
            f"[SINGLE_HOME_AGENT] Safety upgrade flow completed: "
            f"baseline_band={safety_upgrade.baseline_band}, "
            f"is_tight_or_worse={safety_upgrade.baseline_is_tight_or_worse}, "
            f"has_safer_homes={safety_upgrade.safer_homes is not None}, "
            f"has_primary_suggestion={safety_upgrade.primary_suggestion is not None}"
        )
    except Exception as e:
        # Degrade gracefully - log warning but continue
        logger.warning(
            f"[SINGLE_HOME_AGENT] Safety upgrade flow failed: {e}",
            exc_info=True
        )
        safety_upgrade = None
    
    # Step 4: Run strategy lab to explore alternative scenarios
    strategy_lab = None
    try:
        strategy_lab = run_strategy_lab(
            req=stress_request,
            max_scenarios=3,
        )
        logger.info(
            f"[SINGLE_HOME_AGENT] Strategy lab completed: "
            f"baseline_band={strategy_lab.baseline_stress_band}, "
            f"scenarios_count={len(strategy_lab.scenarios)}"
        )
    except Exception as e:
        # Degrade gracefully - log warning but continue
        logger.warning(
            f"[SINGLE_HOME_AGENT] Strategy lab failed: {e}",
            exc_info=True
        )
        strategy_lab = None
    
    # Step 5: Generate LLM narrative if enabled (pass safety_upgrade for richer context)
    borrower_narrative = None
    recommended_actions = None
    llm_usage = None
    
    from services.fiqa_api.utils.llm_client import is_llm_generation_enabled
    if is_llm_generation_enabled():
        llm_start = perf_counter()
        try:
            borrower_narrative, recommended_actions, llm_usage = _generate_single_home_narrative(
                stress_result=stress_result,
                user_message=req.user_message,
                safety_upgrade=safety_upgrade,
                mortgage_programs=None,
                approval_score=stress_result.approval_score,
                risk_assessment=stress_result.risk_assessment,
            )
            llm_duration_ms = (perf_counter() - llm_start) * 1000
            logger.info(
                f'{{"event": "llm_explanation", "request_id": "{request_id}", '
                f'"duration_ms": {llm_duration_ms:.1f}, "success": true}}'
            )
        except Exception as e:
            llm_duration_ms = (perf_counter() - llm_start) * 1000
            logger.warning(
                f'{{"event": "llm_explanation", "request_id": "{request_id}", '
                f'"duration_ms": {llm_duration_ms:.1f}, "success": false, "error_type": "{type(e).__name__}"}}'
            )
            # Set fallback narrative
            borrower_narrative = (
                "The system completed the numeric stress check, but AI explanation is temporarily unavailable. "
                "Please review the numeric results above."
            )
    
    # Step 6: Assemble response
    overall_duration_ms = (perf_counter() - overall_start) * 1000
    logger.info(
        f'{{"event": "single_home_agent_complete", "request_id": "{request_id}", '
        f'"duration_ms": {overall_duration_ms:.1f}, "stress_band": "{stress_result.stress_band}"}}'
    )
    return SingleHomeAgentResponse(
        stress_result=stress_result,
        borrower_narrative=borrower_narrative,
        recommended_actions=recommended_actions,
        llm_usage=llm_usage,
        safety_upgrade=safety_upgrade,
        risk_assessment=stress_result.risk_assessment,  # Copy from stress_result for convenience
        strategy_lab=strategy_lab,
    )


# ========================================
# Safer Homes Search Logic
# ========================================

def search_safer_homes_for_case(
    *,
    monthly_income: float,
    other_debts_monthly: float,
    zip_code: str,
    target_list_price: float,
    baseline_band: Optional[StressBand] = None,
    baseline_dti_ratio: Optional[float] = None,
    down_payment_pct: float = 0.20,
    risk_preference: str = "neutral",
    state: Optional[str] = None,
    max_candidates: int = 5,
) -> SaferHomesResult:
    """
    Search for nearby homes that are less stressful (lower DTI / better stress band) than the target home.
    
    This function:
    1. Searches mock local listings in the given ZIP code
    2. Filters listings by price range (50%-150% of target price)
    3. Runs stress check on each candidate listing
    4. Filters to only "safer" homes (better stress band or lower DTI)
    5. Sorts and returns top candidates
    
    Currently uses static mock listings and local cost factors via LocalCostFactors.
    Designed to be replaced by real property APIs in the future.
    
    Args:
        monthly_income: Borrower's monthly income
        other_debts_monthly: Other monthly debt payments
        zip_code: ZIP code to search (must match existing mock listings)
        target_list_price: Target home listing price (used for filtering and baseline comparison)
        baseline_band: Optional baseline stress band (if known, used for filtering)
        baseline_dti_ratio: Optional baseline DTI ratio (if known, used for filtering)
        down_payment_pct: Down payment percentage (0-1), default 0.20
        risk_preference: Risk preference ("conservative", "neutral", "aggressive"), default "neutral"
        state: Optional state code (for local cost factors)
        max_candidates: Maximum number of candidates to return, default 5
    
    Returns:
        SaferHomesResult with baseline info and list of safer home candidates
    """
    # Validate inputs
    if monthly_income <= 0 or not zip_code:
        return SaferHomesResult(
            baseline_band=baseline_band,
            baseline_dti_ratio=baseline_dti_ratio,
            zip_code=zip_code,
            candidates=[],
        )
    
    # Get listings for ZIP code
    try:
        listings = search_listings_for_zip(
            zip_code=zip_code,
            min_price=None,
            max_price=None,
            limit=20,
        )
    except Exception as e:
        logger.warning(f"[SAFER_HOMES] Failed to search listings for ZIP {zip_code}: {e}")
        return SaferHomesResult(
            baseline_band=baseline_band,
            baseline_dti_ratio=baseline_dti_ratio,
            zip_code=zip_code,
            candidates=[],
        )
    
    # Filter listings by price range (50%-150% of target price)
    min_price = target_list_price * 0.50
    max_price = target_list_price * 1.50
    filtered_listings = [
        listing for listing in listings
        if min_price <= listing.list_price <= max_price
    ]
    
    if not filtered_listings:
        logger.info(f"[SAFER_HOMES] No listings in price range ${min_price:,.0f}-${max_price:,.0f} for ZIP {zip_code}")
        return SaferHomesResult(
            baseline_band=baseline_band,
            baseline_dti_ratio=baseline_dti_ratio,
            zip_code=zip_code,
            candidates=[],
        )
    
    # Run stress check on each listing
    candidates: List[SaferHomeCandidate] = []
    
    for listing in filtered_listings:
        try:
            # Construct StressCheckRequest for this listing
            stress_req = StressCheckRequest(
                monthly_income=monthly_income,
                other_debts_monthly=other_debts_monthly,
                list_price=listing.list_price,
                down_payment_pct=down_payment_pct,
                zip_code=listing.zip_code,
                state=listing.state,
                hoa_monthly=listing.hoa_monthly or 0.0,
                risk_preference=risk_preference,
            )
            
            # Run stress check directly (pure Python, no HTTP)
            stress_result = run_stress_check(stress_req)
            
            # Get stress metrics
            candidate_band = stress_result.stress_band
            candidate_dti = stress_result.dti_ratio
            candidate_payment = stress_result.total_monthly_payment
            
            # Determine if this listing is "safer" than baseline
            is_safer = False
            
            if baseline_band is not None:
                # Use stress band comparison: loose < ok < tight < high_risk
                band_order = {"loose": 0, "ok": 1, "tight": 2, "high_risk": 3}
                baseline_order = band_order.get(baseline_band, 999)
                candidate_order = band_order.get(candidate_band, 999)
                
                # Only keep if candidate band is strictly better (lower order)
                is_safer = candidate_order < baseline_order
            elif baseline_dti_ratio is not None:
                # Use DTI comparison if we don't have baseline band
                is_safer = candidate_dti < baseline_dti_ratio
            else:
                # Default: keep if DTI <= 0.38 (OK-ish cap)
                is_safer = candidate_dti <= 0.38
            
            if is_safer:
                # Build comment
                if baseline_dti_ratio is not None:
                    comment = f"DTI improves from {baseline_dti_ratio:.1%} to {candidate_dti:.1%}"
                else:
                    comment = f"DTI around {candidate_dti:.1%}, in the {candidate_band.upper()} range"
                
                candidates.append(SaferHomeCandidate(
                    listing=listing,
                    stress_band=candidate_band,
                    dti_ratio=candidate_dti,
                    total_monthly_payment=candidate_payment,
                    comment=comment,
                ))
        except Exception as e:
            logger.warning(f"[SAFER_HOMES] Failed to run stress check for listing {listing.listing_id}: {e}")
            continue
    
    # Sort candidates:
    # 1. By stress band (safer first: loose, ok, tight, high_risk)
    # 2. By DTI ratio (ascending)
    # 3. By list price (ascending)
    band_order = {"loose": 0, "ok": 1, "tight": 2, "high_risk": 3}
    
    def sort_key(candidate: SaferHomeCandidate) -> Tuple[int, float, float]:
        band_ord = band_order.get(candidate.stress_band, 999)
        dti = candidate.dti_ratio or 999.0
        price = candidate.listing.list_price
        return (band_ord, dti, price)
    
    candidates.sort(key=sort_key)
    
    # Truncate to max_candidates
    candidates = candidates[:max_candidates]
    
    # Return result
    return SaferHomesResult(
        baseline_band=baseline_band,
        baseline_dti_ratio=baseline_dti_ratio,
        zip_code=zip_code,
        candidates=candidates,
    )


# ========================================
# Safety Upgrade Flow Logic
# ========================================

def run_safety_upgrade_flow(
    req: StressCheckRequest,
    *,
    max_candidates: int = 5,
) -> SafetyUpgradeResult:
    """
    Orchestrate a safety upgrade workflow that:
    1. Runs a baseline stress check
    2. If tight/high_risk, searches for safer homes
    3. Builds structured upgrade suggestions
    
    This is a pure Python orchestration function - no LLM calls, no HTTP endpoints.
    Designed to be called from other Python code or future HTTP endpoints.
    
    Args:
        req: StressCheckRequest with borrower profile and home details
        max_candidates: Maximum number of safer home candidates to return, default 5
    
    Returns:
        SafetyUpgradeResult with baseline metrics, safer homes (if found), and suggestions
    """
    # Step 1: Run baseline stress check
    baseline_result = run_stress_check(req)
    
    # Extract baseline metrics
    baseline_band = baseline_result.stress_band
    baseline_dti = baseline_result.dti_ratio
    baseline_total_payment = baseline_result.total_monthly_payment
    
    # Extract location from home_snapshot or request
    home_snapshot = baseline_result.home_snapshot or {}
    zip_code = home_snapshot.get("zip_code") or req.zip_code
    state = home_snapshot.get("state") or req.state
    
    # Determine if baseline is tight or worse
    baseline_is_tight_or_worse = baseline_band in ("tight", "high_risk")
    
    # Step 2: Decide whether to search safer homes
    safer_homes_result: Optional[SaferHomesResult] = None
    primary_suggestion: Optional[SafetyUpgradeSuggestion] = None
    alternative_suggestions: List[SafetyUpgradeSuggestion] = []
    
    if not baseline_is_tight_or_worse:
        # Baseline is loose or ok - no need to search safer homes
        if baseline_band in ("loose", "ok"):
            primary_suggestion = SafetyUpgradeSuggestion(
                reason="baseline_comfortable",
                title="This home already looks comfortable for your income",
                details=(
                    f"Your stress check shows a '{baseline_band}' band with a DTI of {baseline_dti:.1%}. "
                    f"This home appears to be within a comfortable range for your income. "
                    f"No safer homes are necessary at this time."
                ),
                delta_dti=None,
                target_price=None,
                notes=[
                    f"Current stress band: {baseline_band}",
                    f"Current DTI: {baseline_dti:.1%}",
                    f"Total monthly payment: ${baseline_total_payment:,.2f}",
                ],
            )
        else:
            # No band but low DTI - similar safe message
            if baseline_dti and baseline_dti < 0.38:
                primary_suggestion = SafetyUpgradeSuggestion(
                    reason="baseline_low_dti",
                    title="Your DTI is in a safe range",
                    details=(
                        f"Your DTI of {baseline_dti:.1%} is below the typical threshold of 38%. "
                        f"This home appears manageable for your current income level."
                    ),
                    delta_dti=None,
                    target_price=None,
                    notes=[
                        f"Current DTI: {baseline_dti:.1%}",
                        f"Total monthly payment: ${baseline_total_payment:,.2f}",
                    ],
                )
            else:
                # Edge case: no band but unclear DTI
                primary_suggestion = SafetyUpgradeSuggestion(
                    reason="baseline_unknown",
                    title="Stress check completed",
                    details="Stress check completed successfully. Review the results above.",
                    delta_dti=None,
                    target_price=None,
                    notes=[],
                )
    else:
        # Baseline is tight or high_risk - check if we can search safer homes
        if not zip_code:
            # Missing ZIP code - cannot search safer homes
            primary_suggestion = SafetyUpgradeSuggestion(
                reason="missing_zip_code",
                title="Your stress level is high, but we need your ZIP code",
                details=(
                    f"Your stress check shows a '{baseline_band}' band with a DTI of {baseline_dti:.1%}. "
                    f"However, we don't know your ZIP code to search for safer homes nearby. "
                    f"Try adding a ZIP code and re-running the stress check."
                ),
                delta_dti=None,
                target_price=None,
                notes=[
                    f"Current stress band: {baseline_band}",
                    f"Current DTI: {baseline_dti:.1%}",
                    "ZIP code required to search safer homes",
                ],
            )
        else:
            # Search for safer homes
            safer_homes_result = search_safer_homes_for_case(
                monthly_income=req.monthly_income,
                other_debts_monthly=req.other_debts_monthly,
                zip_code=zip_code,
                target_list_price=req.list_price,
                baseline_band=baseline_band,
                baseline_dti_ratio=baseline_dti,
                down_payment_pct=req.down_payment_pct or 0.20,
                risk_preference=req.risk_preference or "neutral",
                state=state,
                max_candidates=max_candidates,
            )
            
            # Step 3: Build suggestions based on safer homes result
            if safer_homes_result.candidates:
                # Found safer homes - pick the best candidate
                best_candidate = safer_homes_result.candidates[0]
                
                # Compute delta DTI
                delta_dti = None
                if baseline_dti is not None and best_candidate.dti_ratio is not None:
                    delta_dti = baseline_dti - best_candidate.dti_ratio
                
                # Build primary suggestion
                primary_suggestion = SafetyUpgradeSuggestion(
                    reason="safer_home_found",
                    title="We found a safer home in your area",
                    details=(
                        f"Your current home shows a '{baseline_band}' band with a DTI of {baseline_dti:.1%}. "
                        f"We found a safer option: {best_candidate.listing.title} at ${best_candidate.listing.list_price:,.0f}. "
                        f"This home has a '{best_candidate.stress_band}' band with a DTI of {best_candidate.dti_ratio:.1%}. "
                        f"{best_candidate.comment or ''}"
                    ),
                    delta_dti=delta_dti,
                    target_price=best_candidate.listing.list_price,
                    notes=[
                        f"Baseline: {baseline_band} band, {baseline_dti:.1%} DTI",
                        f"Safer option: {best_candidate.stress_band} band, {best_candidate.dti_ratio:.1%} DTI",
                        f"Price: ${best_candidate.listing.list_price:,.0f}",
                        f"Monthly payment: ${best_candidate.total_monthly_payment:,.2f}" if best_candidate.total_monthly_payment else "Monthly payment: N/A",
                    ],
                )
                
                # Optionally add alternative suggestion about price range
                if len(safer_homes_result.candidates) > 1:
                    # Find price range that typically lands in OK band
                    ok_candidates = [c for c in safer_homes_result.candidates if c.stress_band == "ok"]
                    if ok_candidates:
                        min_ok_price = min(c.listing.list_price for c in ok_candidates)
                        max_ok_price = max(c.listing.list_price for c in ok_candidates)
                        alternative_suggestions.append(SafetyUpgradeSuggestion(
                            reason="price_range_ok_band",
                            title=f"Consider homes in the ${min_ok_price:,.0f} - ${max_ok_price:,.0f} range",
                            details=(
                                f"Homes in this price range typically land you in the 'ok' stress band "
                                f"for your income level in {zip_code}."
                            ),
                            delta_dti=None,
                            target_price=(min_ok_price + max_ok_price) / 2.0,
                            notes=[
                                f"Price range: ${min_ok_price:,.0f} - ${max_ok_price:,.0f}",
                                f"Found {len(ok_candidates)} homes in 'ok' band",
                            ],
                        ))
            else:
                # No safer homes found but baseline is tight/high_risk
                primary_suggestion = SafetyUpgradeSuggestion(
                    reason="no_safer_option_in_zip",
                    title="This ZIP is pricey for your current income",
                    details=(
                        f"Your stress check shows a '{baseline_band}' band with a DTI of {baseline_dti:.1%}. "
                        f"We searched for safer homes in ZIP {zip_code}, but couldn't find options that significantly improve your situation. "
                        f"Consider these alternatives: increase your down payment, lower your target price, "
                        f"or explore nearby ZIP codes that may have more affordable options."
                    ),
                    delta_dti=None,
                    target_price=None,
                    notes=[
                        f"Current stress band: {baseline_band}",
                        f"Current DTI: {baseline_dti:.1%}",
                        f"Searched ZIP: {zip_code}",
                        "Consider: increase down payment, lower target price, or explore nearby ZIPs",
                    ],
                )
    
    # Build and return result
    return SafetyUpgradeResult(
        baseline_band=baseline_band,
        baseline_dti=baseline_dti,
        baseline_total_payment=baseline_total_payment,
        baseline_zip_code=zip_code,
        baseline_state=state,
        baseline_is_tight_or_worse=baseline_is_tight_or_worse,
        safer_homes=safer_homes_result,
        primary_suggestion=primary_suggestion,
        alternative_suggestions=alternative_suggestions,
        mortgage_programs_checked=False,
        mortgage_programs_hit_count=None,
    )

