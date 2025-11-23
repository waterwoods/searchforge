"""
mortgage_math.py - Mortgage Calculation Functions
==================================================
Pure mathematical functions for mortgage calculations.

No dependencies on other mortgage modules - only standard library.
"""

import math
from typing import Dict


def calc_monthly_payment(
    loan_amount: float,
    annual_rate: float,
    term_years: int,
) -> float:
    """
    Calculate monthly mortgage payment using standard formula.
    
    Formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
    where:
        M = monthly payment
        P = principal (loan amount)
        r = monthly interest rate (annual_rate / 12)
        n = number of payments (term_years * 12)
    
    Args:
        loan_amount: Total loan amount (principal)
        annual_rate: Annual interest rate as percentage (e.g., 5.5 for 5.5%)
        term_years: Loan term in years
    
    Returns:
        Monthly payment amount
    """
    if loan_amount <= 0:
        return 0.0
    if annual_rate <= 0:
        return loan_amount / (term_years * 12)
    if term_years <= 0:
        return loan_amount
    
    monthly_rate = annual_rate / 100.0 / 12.0
    num_payments = term_years * 12
    
    if monthly_rate == 0:
        return loan_amount / num_payments
    
    # M = P * [r(1+r)^n] / [(1+r)^n - 1]
    numerator = monthly_rate * ((1 + monthly_rate) ** num_payments)
    denominator = ((1 + monthly_rate) ** num_payments) - 1
    
    monthly_payment = loan_amount * (numerator / denominator)
    return round(monthly_payment, 2)


def calc_dti_ratio(
    monthly_payment: float,
    monthly_debts: float,
    annual_income: float,
) -> float:
    """
    Calculate debt-to-income (DTI) ratio.
    
    DTI = (monthly_payment + monthly_debts) / (annual_income / 12)
    
    Args:
        monthly_payment: Monthly mortgage payment
        monthly_debts: Other monthly debt payments
        annual_income: Annual income
    
    Returns:
        DTI ratio (0.0 to 1.0+)
    """
    if annual_income <= 0:
        return 1.0  # Invalid: return max risk
    
    monthly_income = annual_income / 12.0
    total_monthly_debt = monthly_payment + monthly_debts
    
    dti = total_monthly_debt / monthly_income
    return round(dti, 4)


def calc_loan_amount_from_payment(
    monthly_payment: float,
    annual_rate: float,
    term_years: int,
) -> float:
    """
    Calculate loan amount from monthly payment (reverse of calc_monthly_payment).
    
    Formula: P = M * [(1+r)^n - 1] / [r(1+r)^n]
    where:
        P = principal (loan amount)
        M = monthly payment
        r = monthly interest rate (annual_rate / 12)
        n = number of payments (term_years * 12)
    
    Args:
        monthly_payment: Monthly payment amount
        annual_rate: Annual interest rate as percentage (e.g., 5.5 for 5.5%)
        term_years: Loan term in years
    
    Returns:
        Loan amount (principal)
    """
    if monthly_payment <= 0:
        return 0.0
    if term_years <= 0:
        return 0.0
    
    monthly_rate = annual_rate / 100.0 / 12.0
    num_payments = term_years * 12
    
    if monthly_rate == 0:
        return monthly_payment * num_payments
    
    # P = M * [(1+r)^n - 1] / [r(1+r)^n]
    denominator = monthly_rate * ((1 + monthly_rate) ** num_payments)
    numerator = ((1 + monthly_rate) ** num_payments) - 1
    
    loan_amount = monthly_payment * (numerator / denominator)
    return round(loan_amount, 2)


def compute_max_affordability(
    annual_income: float,
    monthly_debts: float,
    interest_rate_pct: float,
    target_dti: float = 0.36,
    term_years: int = 30,
    down_payment_pct: float = 0.20,
) -> Dict[str, float]:
    """
    Compute maximum affordable home price based on income and debt constraints.
    
    This is a simplified educational model that does NOT include:
    - Property taxes
    - Homeowner's insurance
    - HOA fees
    - PMI (Private Mortgage Insurance)
    - Other housing-related expenses
    
    Calculation logic:
    1. Monthly income = annual_income / 12
    2. Target total housing budget = target_dti * monthly_income
    3. Available for mortgage payment = max(0, housing_budget - monthly_debts)
    4. Reverse-calculate loan amount from monthly payment using standard mortgage formula
    5. Max home price = loan_amount / (1 - down_payment_pct)
    
    IMPORTANT: This is educational content only and does not constitute financial
    or lending advice. Actual mortgage terms depend on credit score, lender policies,
    market conditions, and other factors.
    
    Args:
        annual_income: Annual income in dollars
        monthly_debts: Other monthly debt payments in dollars
        interest_rate_pct: Annual interest rate as percentage (e.g., 5.5 for 5.5%)
        target_dti: Target debt-to-income ratio threshold (default: 0.36 = 36%)
        term_years: Loan term in years (default: 30)
        down_payment_pct: Down payment percentage as decimal (default: 0.20 = 20%)
    
    Returns:
        Dictionary with:
            - max_monthly_payment: Maximum affordable monthly payment
            - max_loan_amount: Maximum loan amount
            - max_home_price: Maximum affordable home price
    
    Raises:
        ValueError: If inputs are invalid
    """
    # Validation
    if annual_income <= 0:
        raise ValueError("annual_income must be greater than 0")
    if monthly_debts < 0:
        raise ValueError("monthly_debts must be non-negative")
    if interest_rate_pct < 0:
        raise ValueError("interest_rate_pct must be non-negative")
    if target_dti <= 0 or target_dti >= 1:
        raise ValueError("target_dti must be between 0 and 1")
    if term_years <= 0:
        raise ValueError("term_years must be greater than 0")
    if down_payment_pct < 0 or down_payment_pct >= 1:
        raise ValueError("down_payment_pct must be between 0 and 1")
    
    # Step 1: Calculate monthly income
    monthly_income = annual_income / 12.0
    
    # Step 2: Calculate target total housing budget (including debts)
    target_housing_budget = target_dti * monthly_income
    
    # Step 3: Calculate available for mortgage payment
    # Note: This assumes monthly_debts are already included in the DTI calculation
    # The housing budget should cover both mortgage and other debts
    max_monthly_payment = max(0.0, target_housing_budget - monthly_debts)
    
    # Step 4: Reverse-calculate loan amount from monthly payment
    if max_monthly_payment <= 0:
        # Cannot afford any mortgage
        return {
            "max_monthly_payment": 0.0,
            "max_loan_amount": 0.0,
            "max_home_price": 0.0,
        }
    
    max_loan_amount = calc_loan_amount_from_payment(
        monthly_payment=max_monthly_payment,
        annual_rate=interest_rate_pct,
        term_years=term_years,
    )
    
    # Step 5: Calculate max home price
    if down_payment_pct >= 1:
        # 100% down payment (edge case)
        max_home_price = max_loan_amount
    else:
        max_home_price = max_loan_amount / (1 - down_payment_pct)
    
    return {
        "max_monthly_payment": round(max_monthly_payment, 2),
        "max_loan_amount": round(max_loan_amount, 2),
        "max_home_price": round(max_home_price, 2),
    }


__all__ = [
    "calc_monthly_payment",
    "calc_dti_ratio",
    "calc_loan_amount_from_payment",
    "compute_max_affordability",
]

