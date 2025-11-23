"""
mortgage_profile.py - Mortgage Rules and Input Processing
=========================================================
Mortgage rules, risk assessment, and input extraction/validation.

This module contains:
- MORTGAGE_RULES: Hard-coded rules and templates
- assess_risk_level: Risk assessment based on DTI
- extract_inputs: Input extraction and validation
- generate_input_summary: Human-readable input summary
"""

from typing import Any, Dict, List, Literal, Optional

from services.fiqa_api.mortgage.mortgage_math import calc_dti_ratio
from services.fiqa_api.mortgage.schemas import (
    MaxAffordabilitySummary,
    MortgageAgentRequest,
    MortgagePlan,
)


# ========================================
# Constants: Mortgage Rules
# ========================================
# These hard rules are not modified by LLM in this stub.
# Future: LLM can use these as constraints but won't change them directly.

MORTGAGE_RULES = {
    # Interest rate scenarios (annual percentage)
    "interest_rates": [5.5, 6.0, 6.5],  # Three scenarios: conservative, standard, aggressive
    
    # Loan terms (years)
    "loan_terms": [15, 30],  # 15-year and 30-year fixed
    
    # DTI thresholds (debt-to-income ratio)
    "dti_low_threshold": 0.36,    # DTI < 36% is low risk
    "dti_medium_threshold": 0.43,  # DTI 36-43% is medium risk
    # DTI > 43% is high risk
    
    # Default values for missing inputs
    "defaults": {
        "income": 100000.0,          # Annual income ($)
        "debts": 500.0,              # Monthly debt payments ($)
        "purchase_price": 500000.0,  # Home price ($)
        "down_payment_pct": 0.20,    # 20% down payment
        "state": "CA",               # California default
    },
    
    # Pros/Cons templates by risk level
    "pros_templates": {
        "low": [
            "Low DTI ratio indicates strong financial stability",
            "Monthly payment is well within your budget",
            "Good interest rate for current market conditions",
        ],
        "medium": [
            "Affordable monthly payment for your income level",
            "Standard interest rate with room for refinancing later",
            "Manageable debt load with potential to pay down faster",
        ],
        "high": [
            "Lower interest rate helps offset higher DTI",
            "Longer term provides payment flexibility",
            "May qualify with strong credit score and savings",
        ],
    },
    
    "cons_templates": {
        "low": [
            "Higher monthly payment compared to longer terms",
            "Requires larger down payment upfront",
        ],
        "medium": [
            "DTI ratio approaching lender limits",
            "Less flexibility for unexpected expenses",
        ],
        "high": [
            "DTI ratio exceeds most conventional lender thresholds",
            "High risk of payment stress if income decreases",
            "May need to consider lower purchase price or larger down payment",
        ],
    },
    
    # Follow-up questions
    "followup_questions": [
        "What is your credit score? (Higher scores can help qualify even with higher DTI)",
        "Do you have additional monthly expenses like HOA fees or property taxes?",
        "Are you planning to put down more than 20% to reduce monthly payments?",
        "Would you consider an ARM (Adjustable Rate Mortgage) for a lower initial rate?",
        "Do you have other assets or savings that could strengthen your application?",
    ],
    
    # Disclaimer text
    "disclaimer": (
        "This is educational content only and does not constitute financial or lending advice. "
        "Actual mortgage terms depend on credit score, lender policies, market conditions, and other factors. "
        "Consult with a licensed mortgage professional for personalized advice."
    ),
    
    # Agent version
    "agent_version": "stub-v1.0.0",
}


def assess_risk_level(dti_ratio: float) -> Literal["low", "medium", "high"]:
    """
    Assess risk level based on DTI ratio.
    
    Args:
        dti_ratio: Debt-to-income ratio
    
    Returns:
        Risk level: "low", "medium", or "high"
    """
    if dti_ratio < MORTGAGE_RULES["dti_low_threshold"]:
        return "low"
    elif dti_ratio < MORTGAGE_RULES["dti_medium_threshold"]:
        return "medium"
    else:
        return "high"


def extract_inputs(req: MortgageAgentRequest) -> Dict[str, Any]:
    """
    Extract and validate inputs from request.
    
    Args:
        req: MortgageAgentRequest instance
    
    Returns:
        Dict with validated inputs:
            - income: float
            - debts: float
            - purchase_price: float
            - down_payment_pct: float
            - state: str
    
    Raises:
        ValueError: If inputs are invalid
    """
    inputs = req.inputs or {}
    defaults = MORTGAGE_RULES["defaults"]
    
    try:
        income = float(inputs.get("income", defaults["income"]))
        debts = float(inputs.get("debts", defaults["debts"]))
        purchase_price = float(inputs.get("purchase_price", defaults["purchase_price"]))
        down_payment_pct = float(inputs.get("down_payment_pct", defaults["down_payment_pct"]))
        state = str(inputs.get("state", defaults["state"]))
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid input type: {str(e)}")
    
    # Validation
    if income <= 0:
        raise ValueError("income must be greater than 0")
    if debts < 0:
        raise ValueError("debts must be non-negative")
    if purchase_price <= 0:
        raise ValueError("purchase_price must be greater than 0")
    if down_payment_pct < 0 or down_payment_pct >= 1:
        raise ValueError("down_payment_pct must be between 0 and 1")
    
    return {
        "income": income,
        "debts": debts,
        "purchase_price": purchase_price,
        "down_payment_pct": down_payment_pct,
        "state": state,
    }


def generate_input_summary(inputs: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of inputs.
    
    Args:
        inputs: Dict with income, debts, purchase_price, down_payment_pct, state
    
    Returns:
        Summary string
    """
    down_payment = inputs["purchase_price"] * inputs["down_payment_pct"]
    loan_amount = inputs["purchase_price"] * (1 - inputs["down_payment_pct"])
    
    return (
        f"Annual income: ${inputs['income']:,.0f}, "
        f"Monthly debts: ${inputs['debts']:,.0f}, "
        f"Purchase price: ${inputs['purchase_price']:,.0f}, "
        f"Down payment: ${down_payment:,.0f} ({inputs['down_payment_pct']*100:.0f}%), "
        f"Loan amount: ${loan_amount:,.0f}, "
        f"State: {inputs['state']}"
    )


def build_hard_warning_if_needed(
    plans: List[MortgagePlan],
    max_aff: Optional[MaxAffordabilitySummary],
    target_purchase_price: Optional[float] = None,
) -> Optional[str]:
    """
    Build hard warning text if risk is very high.
    
    This is a pure Python rule-based function that does NOT call LLM.
    It checks:
    1. If any plan has DTI ratio > 0.80 (80%), or
    2. If max_affordability exists and max_home_price is significantly less than
       target purchase price (gap > 30%)
    
    Args:
        plans: List of MortgagePlan instances
        max_aff: Optional MaxAffordabilitySummary
        target_purchase_price: Optional target purchase price for comparison
    
    Returns:
        Hard warning text string if risk is very high, None otherwise
    """
    # Rule 1: Check if any plan has DTI > 80%
    for plan in plans:
        if plan.dti_ratio is not None and plan.dti_ratio > 0.80:
            return (
                "Based on your current income and debts, the DTI for this plan is very high (over 80%), "
                "and it is very likely to not be approved in reality. Please evaluate carefully and confirm with a loan officer."
            )
    
    # Rule 2: Check if max_affordability suggests unaffordability
    # (max_home_price is significantly less than target purchase price)
    if max_aff is not None and target_purchase_price is not None:
        if max_aff.max_home_price > 0:
            gap_ratio = (target_purchase_price - max_aff.max_home_price) / target_purchase_price
            if gap_ratio > 0.30:  # Gap > 30%
                return (
                    "Based on your current income and debts, the target home price significantly exceeds the affordable range. "
                    "It is recommended to consider reducing the purchase price or increasing the down payment, and confirm with a loan specialist."
                )
    
    return None


__all__ = [
    "MORTGAGE_RULES",
    "assess_risk_level",
    "extract_inputs",
    "generate_input_summary",
    "build_hard_warning_if_needed",
]

