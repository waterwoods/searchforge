"""
schemas.py - Mortgage Agent Data Models
========================================
Pydantic models for mortgage agent request/response.

These models define the API contract - field names and types must match
exactly with the frontend types in ui/src/types/api.types.ts.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MortgagePlan(BaseModel):
    """Mortgage plan model."""
    plan_id: str
    name: str = Field(..., description="Plan name, e.g., 'Conventional 30-year fixed'")
    monthly_payment: float = Field(..., description="Monthly payment amount")
    interest_rate: float = Field(..., description="Annual interest rate (percentage)")
    loan_amount: float = Field(..., description="Total loan amount")
    term_years: int = Field(..., description="Loan term in years")
    dti_ratio: Optional[float] = Field(None, description="Debt-to-income ratio")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Risk assessment")
    pros: List[str] = Field(..., description="List of advantages")
    cons: List[str] = Field(..., description="List of disadvantages")
    property_id: Optional[str] = Field(None, description="Linked property ID if this plan is for a specific property")


class MortgageAgentRequest(BaseModel):
    """Mortgage agent request model."""
    user_message: str = Field(..., description="User's natural language question")
    profile: Optional[str] = Field("us_default_simplified", description="Profile name")
    inputs: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional structured inputs: {income, debts, purchase_price, down_payment_pct, state}"
    )
    property_id: Optional[str] = Field(None, description="Selected property ID (if provided, will override purchase_price from inputs)")


class MaxAffordabilitySummary(BaseModel):
    """Maximum affordability summary model."""
    max_monthly_payment: float = Field(..., description="Maximum affordable monthly payment")
    max_loan_amount: float = Field(..., description="Maximum loan amount")
    max_home_price: float = Field(..., description="Maximum affordable home price")
    assumed_interest_rate: float = Field(..., description="Interest rate used for calculation")
    target_dti: float = Field(..., description="Target DTI ratio used for calculation")


class AgentStep(BaseModel):
    """Agent step log model for tracking each step in the mortgage agent workflow."""
    step_id: str = Field(..., description="Unique step identifier")
    step_name: str = Field(..., description="Human-readable step name")
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(
        ..., description="Step execution status"
    )
    timestamp: str = Field(..., description="ISO timestamp when step was recorded")
    duration_ms: Optional[float] = Field(None, description="Step duration in milliseconds")
    inputs: Optional[Dict[str, Any]] = Field(None, description="Step inputs (lightweight, avoid large objects)")
    outputs: Optional[Dict[str, Any]] = Field(None, description="Step outputs (lightweight, avoid large objects)")
    error: Optional[str] = Field(None, description="Error message if status is 'failed'")


class CaseState(BaseModel):
    """Complete case state snapshot for mortgage evaluation."""
    case_id: str = Field(..., description="Unique case identifier")
    timestamp: str = Field(..., description="ISO timestamp when case was processed")
    inputs: Dict[str, Any] = Field(..., description="Extracted input parameters")
    plans: List[MortgagePlan] = Field(..., description="Generated mortgage plans")
    max_affordability: Optional[MaxAffordabilitySummary] = Field(
        None, description="Maximum affordability summary if computed"
    )
    risk_summary: Dict[str, Any] = Field(..., description="Risk assessment summary including highest DTI, risk levels, and hard warning")


class MortgageAgentResponse(BaseModel):
    """Mortgage agent response model."""
    ok: bool
    agent_version: str = Field(..., description="Agent version identifier")
    disclaimer: str = Field(..., description="Legal disclaimer")
    input_summary: str = Field(..., description="Summary of inputs used")
    plans: List[MortgagePlan] = Field(..., description="List of mortgage plans")
    followups: List[str] = Field(..., description="Suggested follow-up questions")
    max_affordability: Optional[MaxAffordabilitySummary] = Field(
        None,
        description="Maximum affordability summary (computed when income and debts are provided)"
    )
    error: Optional[str] = Field(None, description="Error message if ok=False")
    llm_explanation: Optional[str] = Field(
        None,
        description="AI-generated explanation of the mortgage plans and affordability (educational only)"
    )
    llm_usage: Optional[Dict[str, Any]] = Field(
        None,
        description="LLM usage metadata (tokens, cost estimate, etc.)"
    )
    hard_warning: Optional[str] = Field(
        None,
        description="Hard warning text when risk is very high (e.g., DTI > 80% or unaffordable scenario)"
    )
    lo_summary: Optional[str] = Field(
        None,
        description="Structured text summary for Loan Officer: borrower snapshot, risk & DTI, affordability vs target price, and next steps"
    )
    case_state: Optional["CaseState"] = Field(
        None,
        description="Complete case state snapshot (evaluation snapshot)"
    )
    agent_steps: Optional[List["AgentStep"]] = Field(
        None,
        description="Step-by-step execution log of agent workflow"
    )


# ========================================
# Property Comparison Models
# ========================================

class MortgagePropertySummary(BaseModel):
    """Property summary for comparison."""
    property_id: str = Field(..., description="Property ID")
    display_name: str = Field(..., description="Display name, e.g., 'Seattle – 3BR Townhouse'")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State code")
    listing_price: float = Field(..., description="Listing price")


class PropertyStressMetrics(BaseModel):
    """Stress metrics for a property under borrower conditions."""
    monthly_payment: float = Field(..., description="Monthly mortgage payment")
    dti_ratio: float = Field(..., description="Debt-to-income ratio")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Risk assessment")
    within_affordability: bool = Field(..., description="Whether property is within max_affordability range")
    dti_excess_pct: Optional[float] = Field(
        None,
        description="DTI excess percentage relative to target DTI (positive = exceeds, negative = below)"
    )


class PropertyComparisonEntry(BaseModel):
    """Single property comparison entry."""
    property: MortgagePropertySummary = Field(..., description="Property summary")
    metrics: PropertyStressMetrics = Field(..., description="Stress metrics for this property")


class MortgageCompareRequest(BaseModel):
    """Request model for property comparison."""
    income: float = Field(..., description="Annual income")
    monthly_debts: float = Field(..., description="Monthly debt payments")
    down_payment_pct: float = Field(..., description="Down payment percentage (0-1)")
    state: Optional[str] = Field(None, description="Borrower's state (for display purposes)")
    property_ids: List[str] = Field(..., description="List of property IDs to compare (should be exactly 2)")


class MortgageCompareResponse(BaseModel):
    """Response model for property comparison."""
    ok: bool = Field(..., description="Success status")
    borrower_profile_summary: str = Field(..., description="Brief summary of borrower profile")
    target_dti: float = Field(..., description="Target DTI ratio used for calculations")
    max_affordability: Optional[MaxAffordabilitySummary] = Field(
        None,
        description="Maximum affordability summary"
    )
    properties: List[PropertyComparisonEntry] = Field(..., description="List of compared properties (1-2 entries)")
    best_property_id: Optional[str] = Field(
        None,
        description="Property ID of the best option based on affordability and risk"
    )
    error: Optional[str] = Field(None, description="Error message if ok=False")


# ========================================
# Stress Check Models
# ========================================

StressBand = Literal["loose", "ok", "tight", "high_risk"]


class ApprovalScore(BaseModel):
    """Approval score model for mortgage application likelihood."""
    score: float = Field(..., description="Score from 0-100, rounded to 1 decimal")
    bucket: Literal["likely", "borderline", "unlikely"] = Field(
        ..., description="Approval likelihood bucket"
    )
    reasons: List[str] = Field(
        default_factory=list, description="List of machine-readable reason tags"
    )


class SuggestedScenario(BaseModel):
    """Suggested what-if scenario for stress check reflection/planner step."""
    id: str = Field(..., description="Unique scenario identifier, e.g., 'income_minus_10', 'price_minus_50k'")
    title: str = Field(..., description="Short label for the button, e.g., 'Try -10% income scenario'")
    description: Optional[str] = Field(None, description="One-line hint for the user")
    scenario_key: Literal["income_minus_10", "price_minus_50k"] = Field(
        ..., description="Scenario key that maps to existing what-if handlers"
    )
    reason: Optional[str] = Field(None, description="Why this scenario is suggested")


class StressCheckRequest(BaseModel):
    """Request model for single-home stress check."""
    monthly_income: float = Field(..., description="Monthly income")
    other_debts_monthly: float = Field(..., description="Other monthly debt payments")
    list_price: float = Field(..., description="Home listing price")
    down_payment_pct: Optional[float] = Field(0.20, description="Down payment percentage (0-1), default 0.20")
    zip_code: Optional[str] = Field(None, description="Zip code (for tax/insurance estimation)")
    state: Optional[str] = Field(None, description="State code (for tax/insurance estimation)")
    hoa_monthly: Optional[float] = Field(0.0, description="Monthly HOA fees, default 0")
    tax_rate_est: Optional[float] = Field(None, description="Property tax rate estimate (as decimal, e.g., 0.012 for 1.2%)")
    insurance_ratio_est: Optional[float] = Field(None, description="Home insurance ratio estimate (as decimal, e.g., 0.003 for 0.3% of home value annually)")
    risk_preference: Optional[Literal["conservative", "neutral", "aggressive"]] = Field(
        "neutral", description="Risk preference for DTI threshold adjustment"
    )
    profile_id: Optional[str] = Field(None, description="User profile ID (for future use, currently ignored)")


class StressCheckResponse(BaseModel):
    """Response model for single-home stress check."""
    total_monthly_payment: float = Field(..., description="Total monthly payment (P&I + tax/ins/HOA)")
    principal_interest_payment: float = Field(..., description="Principal and interest payment only")
    estimated_tax_ins_hoa: float = Field(..., description="Estimated tax, insurance, and HOA monthly")
    dti_ratio: float = Field(..., description="Debt-to-income ratio")
    stress_band: StressBand = Field(..., description="Stress band classification: loose/ok/tight/high_risk")
    hard_warning: Optional[str] = Field(None, description="Hard warning text if risk is very high")
    wallet_snapshot: Dict[str, Any] = Field(..., description="Borrower wallet snapshot (income, debts, safe payment band, etc.)")
    home_snapshot: Dict[str, Any] = Field(..., description="Home snapshot (price, zip/state, hoa, tax_rate_est, etc.)")
    case_state: Optional["CaseState"] = Field(None, description="Case state snapshot if available")
    agent_steps: Optional[List["AgentStep"]] = Field(None, description="Step-by-step execution log")
    llm_explanation: Optional[str] = Field(None, description="LLM-generated explanation (optional, can be None)")
    assumed_interest_rate_pct: Optional[float] = Field(
        None, description="Annual interest rate in percent used for this stress check"
    )
    assumed_tax_rate_pct: Optional[float] = Field(
        None, description="Property tax rate in percent used for this stress check"
    )
    assumed_insurance_ratio_pct: Optional[float] = Field(
        None, description="Annual insurance cost as percent of home price"
    )
    recommended_scenarios: Optional[List["SuggestedScenario"]] = Field(
        None, description="AI-suggested what-if scenarios based on stress result (lightweight reflection/planner step)"
    )
    approval_score: Optional["ApprovalScore"] = Field(
        None, description="Mortgage approval likelihood score (0-100) with bucket and reasons"
    )
    risk_assessment: Optional["RiskAssessment"] = Field(
        None, description="Standardized risk assessment with risk flags, hard_block, and soft_warning"
    )


# ========================================
# Single Home Agent Models
# ========================================

class SingleHomeAgentRequest(BaseModel):
    """Input payload for the Single Home Agent, thin wrapper over StressCheckRequest."""
    stress_request: StressCheckRequest = Field(..., description="Stress check request parameters")
    user_message: Optional[str] = Field(
        default=None,
        description="Optional natural language question from the borrower, e.g., 'Is this too tight for me?'"
    )


class MortgageProgramPreview(BaseModel):
    """Lightweight preview model for mortgage assistance programs found via MCP."""
    program_id: str = Field(..., description="Program identifier")
    name: str = Field(..., description="Program name")
    state: Optional[str] = Field(None, description="State code if program is state-specific")
    max_dti: Optional[float] = Field(None, description="Maximum DTI ratio (0-1) if specified")
    summary: Optional[str] = Field(None, description="Short description or summary")
    tags: Optional[List[str]] = Field(None, description="Program tags or categories")


class SingleHomeAgentResponse(BaseModel):
    """Single Home Agent output: stress_check result + LLM narrative + safety upgrade suggestions."""
    stress_result: StressCheckResponse = Field(..., description="Complete stress check result (source of truth)")
    borrower_narrative: Optional[str] = Field(
        default=None,
        description="Short, friendly explanation for the borrower. Must not invent or change any numbers."
    )
    recommended_actions: Optional[List[str]] = Field(
        default=None,
        description="1–3 bullet-style next steps, derived from the stress_result only."
    )
    llm_usage: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Token usage / model name etc, similar to existing llm_usage in other responses."
    )
    safety_upgrade: Optional["SafetyUpgradeResult"] = Field(
        default=None,
        description="Safety upgrade workflow result with baseline metrics, safer homes (if found), and structured suggestions."
    )
    mortgage_programs_preview: Optional[List["MortgageProgramPreview"]] = Field(
        default=None,
        description="Lightweight preview of top 2-3 mortgage assistance programs found via MCP (only for tight/high_risk cases)."
    )
    risk_assessment: Optional["RiskAssessment"] = Field(
        default=None, description="Standardized risk assessment with risk flags, hard_block, and soft_warning (copied from stress_result for convenience)"
    )
    strategy_lab: Optional["StrategyLabResult"] = Field(
        default=None, description="Strategy lab result with baseline metrics and alternative scenario comparisons"
    )


# ========================================
# Local Listing Models
# ========================================

class LocalListingSummary(BaseModel):
    """Local listing summary for cheaper homes search."""
    listing_id: str = Field(..., description="Unique listing identifier")
    title: str = Field(..., description="Listing title, e.g., '2BR condo near beach'")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State code")
    zip_code: str = Field(..., description="ZIP code")
    list_price: float = Field(..., description="Listing price")
    hoa_monthly: Optional[float] = Field(None, description="Monthly HOA fees")
    beds: Optional[int] = Field(None, description="Number of bedrooms")
    baths: Optional[float] = Field(None, description="Number of bathrooms")
    sqft: Optional[int] = Field(None, description="Square footage")


# ========================================
# Safer Homes Models
# ========================================

class SaferHomeCandidate(BaseModel):
    """A single safer home candidate with stress check results."""
    listing: LocalListingSummary = Field(..., description="Property listing summary")
    stress_band: StressBand = Field(..., description="Stress band classification: loose/ok/tight/high_risk")
    dti_ratio: Optional[float] = Field(None, description="Debt-to-income ratio for this property")
    total_monthly_payment: Optional[float] = Field(None, description="Total monthly payment (P&I + tax/ins/HOA)")
    comment: Optional[str] = Field(None, description="Short human-readable hint, e.g., 'DTI drops from 48% to 36%'")


class SaferHomesResult(BaseModel):
    """Result of searching for safer homes given a stress-check context."""
    baseline_band: Optional[StressBand] = Field(None, description="Baseline stress band from original case")
    baseline_dti_ratio: Optional[float] = Field(None, description="Baseline DTI ratio from original case")
    zip_code: Optional[str] = Field(None, description="ZIP code searched")
    candidates: List[SaferHomeCandidate] = Field(default_factory=list, description="List of safer home candidates")


# ========================================
# Risk Assessment Models
# ========================================

class RiskAssessment(BaseModel):
    """Risk assessment result with standardized risk flags and warnings."""
    risk_flags: List[str] = Field(
        default_factory=list,
        description="List of risk flag identifiers, e.g., ['high_dti', 'negative_cashflow', 'high_ltv']"
    )
    hard_block: bool = Field(
        default=False,
        description="Whether this case should be strongly discouraged (hard block)"
    )
    soft_warning: bool = Field(
        default=False,
        description="Whether this case needs caution (soft warning)"
    )


# ========================================
# Safety Upgrade Models
# ========================================

class SafetyUpgradeSuggestion(BaseModel):
    """A single safety upgrade suggestion with structured details."""
    reason: str = Field(..., description="Short machine-readable reason, e.g., 'baseline_high_risk', 'safer_home_found', 'no_safer_option'")
    title: str = Field(..., description="Short human-facing title, e.g., 'This home is very tight for your income'")
    details: str = Field(..., description="More verbose explanation (pure Python text for now)")
    delta_dti: Optional[float] = Field(None, description="If safer home found, how much DTI improves vs baseline")
    target_price: Optional[float] = Field(None, description="If suggesting a 'max safe price' instead of specific homes")
    notes: Optional[List[str]] = Field(None, description="Bullet points we can show in UI or feed to LLM later")


class SafetyUpgradeResult(BaseModel):
    """Result of the safety upgrade flow: baseline stress check + safer homes search + suggestions."""
    baseline_band: Optional[StressBand] = Field(None, description="Baseline stress band from initial stress check")
    baseline_dti: Optional[float] = Field(None, description="Baseline DTI ratio from initial stress check")
    baseline_total_payment: Optional[float] = Field(None, description="Baseline total monthly payment")
    baseline_zip_code: Optional[str] = Field(None, description="ZIP code from baseline home")
    baseline_state: Optional[str] = Field(None, description="State from baseline home")
    baseline_is_tight_or_worse: bool = Field(..., description="Whether baseline is tight or high_risk")
    safer_homes: Optional[SaferHomesResult] = Field(None, description="Safer homes search result (may be None if not needed or none found)")
    primary_suggestion: Optional[SafetyUpgradeSuggestion] = Field(None, description="Primary upgrade suggestion")
    alternative_suggestions: List[SafetyUpgradeSuggestion] = Field(default_factory=list, description="Additional alternative suggestions")
    mortgage_programs_checked: bool = Field(default=False, description="Whether mortgage programs MCP server was called")
    mortgage_programs_hit_count: Optional[int] = Field(default=None, description="Number of mortgage programs found via MCP")


# ========================================
# Strategy Lab Models
# ========================================

class StrategyScenario(BaseModel):
    """单个方案实验结果。"""
    id: str = Field(..., description="Unique scenario identifier, e.g., 'lower_price_10', 'increase_down_25'")
    title: str = Field(..., description="User-facing name, e.g., 'Lower price by 10%'")
    description: Optional[str] = Field(None, description="Brief description")
    
    # 输入调整信息（相对于 baseline）
    price_delta_abs: Optional[float] = Field(None, description="Price change amount in dollars (positive or negative)")
    price_delta_pct: Optional[float] = Field(None, description="Price change percentage (-0.1 means 10% reduction)")
    down_payment_pct: Optional[float] = Field(None, description="New down payment percentage (e.g., 0.25)")
    risk_preference: Optional[Literal["conservative", "neutral", "aggressive"]] = Field(None, description="New risk preference")
    note_tags: List[str] = Field(default_factory=list, description="Tags like ['lower_price', 'more_down']")
    
    # 核心结果摘要（尽量轻量，便于前端展示）
    stress_band: Optional[StressBand] = Field(None, description="Stress band classification")
    dti_ratio: Optional[float] = Field(None, description="Debt-to-income ratio")
    total_payment: Optional[float] = Field(None, description="Total monthly payment")
    approval_score: Optional["ApprovalScore"] = Field(None, description="Mortgage approval likelihood score")
    risk_assessment: Optional["RiskAssessment"] = Field(None, description="Risk assessment result")


class StrategyLabResult(BaseModel):
    """方案实验室的整体输出。"""
    baseline_stress_band: Optional[StressBand] = Field(None, description="Baseline stress band")
    baseline_dti: Optional[float] = Field(None, description="Baseline DTI ratio")
    baseline_total_payment: Optional[float] = Field(None, description="Baseline total monthly payment")
    baseline_approval_score: Optional["ApprovalScore"] = Field(None, description="Baseline approval score")
    baseline_risk_assessment: Optional["RiskAssessment"] = Field(None, description="Baseline risk assessment")
    scenarios: List[StrategyScenario] = Field(default_factory=list, description="List of scenario results")


__all__ = [
    "MortgagePlan",
    "MortgageAgentRequest",
    "MaxAffordabilitySummary",
    "AgentStep",
    "CaseState",
    "MortgageAgentResponse",
    "MortgagePropertySummary",
    "PropertyStressMetrics",
    "PropertyComparisonEntry",
    "MortgageCompareRequest",
    "MortgageCompareResponse",
    "StressBand",
    "ApprovalScore",
    "SuggestedScenario",
    "StressCheckRequest",
    "StressCheckResponse",
    "SingleHomeAgentRequest",
    "SingleHomeAgentResponse",
    "MortgageProgramPreview",
    "LocalListingSummary",
    "SaferHomeCandidate",
    "SaferHomesResult",
    "SafetyUpgradeSuggestion",
    "SafetyUpgradeResult",
    "RiskAssessment",
    "StrategyScenario",
    "StrategyLabResult",
]

