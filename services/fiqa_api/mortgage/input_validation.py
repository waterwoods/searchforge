"""
input_validation.py - Mortgage Agent Input Validation
======================================================
Hard error validation for stress check requests.

This module performs "hard error" validation - it checks for clearly invalid
inputs (negative values, out-of-range percentages, etc.) that would cause
errors in downstream calculations. It does NOT provide business recommendations
or soft warnings - those are handled by the risk assessment logic.
"""

from typing import List
from services.fiqa_api.mortgage.schemas import StressCheckRequest


def validate_stress_request_inputs(stress_request: StressCheckRequest) -> List[str]:
    """
    Validate stress check request inputs and return a list of error messages.
    
    Returns an empty list if all inputs are valid. If the list is non-empty,
    the request should be rejected with a 400 Bad Request.
    
    This function performs "hard error" validation only:
    - Checks for negative values where they're not allowed
    - Checks for out-of-range percentages
    - Checks for missing required fields (if applicable)
    - Does NOT check for "extreme but valid" values (those are handled by risk assessment)
    
    Args:
        stress_request: StressCheckRequest instance to validate
    
    Returns:
        List of error message strings (empty if valid)
    
    Example:
        errors = validate_stress_request_inputs(request)
        if errors:
            # Reject request with 400
            raise HTTPException(status_code=400, detail={"errors": errors})
    """
    errors: List[str] = []
    
    # 1. Monthly income must be positive
    if stress_request.monthly_income <= 0:
        errors.append("monthly_income must be greater than 0")
    
    # 2. List price must be positive
    if stress_request.list_price <= 0:
        errors.append("list_price must be greater than 0")
    
    # 3. Down payment percentage must be in valid range (0-100% as decimal 0-1)
    if stress_request.down_payment_pct is not None:
        if stress_request.down_payment_pct < 0:
            errors.append("down_payment_pct cannot be negative")
        elif stress_request.down_payment_pct > 1.0:
            errors.append("down_payment_pct cannot exceed 100% (1.0)")
        # Note: 0% down payment is technically allowed (though risky - that's handled by risk assessment)
    
    # 4. Other debts cannot be negative
    if stress_request.other_debts_monthly < 0:
        errors.append("other_debts_monthly cannot be negative")
    
    # 5. HOA monthly cannot be negative
    if stress_request.hoa_monthly is not None and stress_request.hoa_monthly < 0:
        errors.append("hoa_monthly cannot be negative")
    
    # 6. Tax rate estimate (if provided) should be reasonable
    # Note: Property tax rates can vary widely (0.5% to 2.5%+), but >10% is clearly wrong
    if stress_request.tax_rate_est is not None:
        if stress_request.tax_rate_est < 0:
            errors.append("tax_rate_est cannot be negative")
        elif stress_request.tax_rate_est > 0.10:  # 10% is extremely high
            # This is more of a "warning" level - we log it but don't hard-block
            # For now, we'll allow it but it's worth noting in logs
            pass  # Could add a "warning" list if needed
    
    # 7. Insurance ratio estimate (if provided) should be reasonable
    # Note: Home insurance typically 0.2% to 0.5% of home value annually
    if stress_request.insurance_ratio_est is not None:
        if stress_request.insurance_ratio_est < 0:
            errors.append("insurance_ratio_est cannot be negative")
        elif stress_request.insurance_ratio_est > 0.05:  # 5% is extremely high
            # Similar to tax rate - allow but could warn
            pass
    
    # 8. Risk preference must be one of the allowed values (if provided)
    if stress_request.risk_preference is not None:
        if stress_request.risk_preference not in ("conservative", "neutral", "aggressive"):
            errors.append(f"risk_preference must be one of: conservative, neutral, aggressive (got: {stress_request.risk_preference})")
    
    # 9. Extreme value warnings (not errors, but worth logging)
    # These are not hard-blocked, but could trigger additional security logging
    # Values like income > $500k/month or price > $20M are unusual but not impossible
    
    return errors


__all__ = ["validate_stress_request_inputs"]


