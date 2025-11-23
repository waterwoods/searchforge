"""
local_cost_factors.py - Local Cost Factors Tool
================================================
Reusable tool for estimating tax rates and insurance ratios by ZIP code and state.

This module provides a simple but structured way to get location-specific
cost factors (property tax rate and insurance ratio) for mortgage calculations.
Currently uses static mock data, but designed to be easily replaced with
real API calls in the future.
"""

from typing import Literal

from pydantic import BaseModel


class LocalCostFactors(BaseModel):
    """Local cost factors for a given location."""
    zip_code: str
    state: str | None = None
    tax_rate_est: float  # Annual tax rate as decimal (e.g., 0.012 for 1.2%)
    insurance_ratio_est: float  # Annual insurance ratio as decimal (e.g., 0.003 for 0.3%)
    source: Literal["zip_override", "state_default", "global_default"]  # Data source


# Static table: ZIP code -> (tax_rate_est, insurance_ratio_est)
LOCAL_COST_FACTORS_BY_ZIP: dict[str, tuple[float, float]] = {
    "90803": (0.011, 0.0028),  # SoCal beach condo (Long Beach area)
    "92648": (0.012, 0.0030),  # Huntington Beach
    "73301": (0.019, 0.0025),  # Austin, TX (mock)
    "78701": (0.019, 0.0025),  # Austin, TX downtown (mock)
}


# State defaults: state -> (tax_rate_est, insurance_ratio_est)
STATE_DEFAULTS: dict[str, tuple[float, float]] = {
    "CA": (0.012, 0.0030),  # California
    "TX": (0.019, 0.0025),  # Texas
    "NY": (0.014, 0.0032),  # New York
    "FL": (0.011, 0.0035),  # Florida (higher insurance due to hurricanes)
    "WA": (0.010, 0.0028),  # Washington
}


# Global defaults (fallback)
GLOBAL_DEFAULT_TAX_RATE = 0.012  # 1.2%
GLOBAL_DEFAULT_INSURANCE_RATIO = 0.003  # 0.3%


def get_local_cost_factors(
    zip_code: str | None = None,
    state: str | None = None,
    tax_rate_est: float | None = None,
    insurance_ratio_est: float | None = None,
) -> LocalCostFactors:
    """
    Get local cost factors (tax rate and insurance ratio) for a given location.
    
    Priority order:
    1. User-provided tax_rate_est / insurance_ratio_est (if provided)
    2. ZIP code override (if zip_code is in LOCAL_COST_FACTORS_BY_ZIP)
    3. State default (if state is in STATE_DEFAULTS)
    4. Global default
    
    Args:
        zip_code: ZIP code (optional)
        state: State code (optional)
        tax_rate_est: User-provided tax rate estimate (takes precedence if provided)
        insurance_ratio_est: User-provided insurance ratio estimate (takes precedence if provided)
    
    Returns:
        LocalCostFactors instance with tax_rate_est, insurance_ratio_est, and source
    
    Examples:
        >>> factors = get_local_cost_factors(zip_code="90803", state="CA")
        >>> factors.tax_rate_est
        0.011
        >>> factors.source
        'zip_override'
        
        >>> factors = get_local_cost_factors(state="TX")
        >>> factors.tax_rate_est
        0.019
        >>> factors.source
        'state_default'
        
        >>> factors = get_local_cost_factors(zip_code="00000")
        >>> factors.source
        'global_default'
    """
    # If user provided explicit estimates, use them with zip_override source
    if tax_rate_est is not None or insurance_ratio_est is not None:
        # Use provided values, fall back to defaults if only one is provided
        final_tax_rate = tax_rate_est if tax_rate_est is not None else GLOBAL_DEFAULT_TAX_RATE
        final_insurance_ratio = (
            insurance_ratio_est if insurance_ratio_est is not None else GLOBAL_DEFAULT_INSURANCE_RATIO
        )
        return LocalCostFactors(
            zip_code=zip_code or "",
            state=state,
            tax_rate_est=final_tax_rate,
            insurance_ratio_est=final_insurance_ratio,
            source="zip_override",  # User override takes precedence
        )
    
    # Priority 1: ZIP code override
    if zip_code and zip_code in LOCAL_COST_FACTORS_BY_ZIP:
        tax_rate, insurance_ratio = LOCAL_COST_FACTORS_BY_ZIP[zip_code]
        return LocalCostFactors(
            zip_code=zip_code,
            state=state,
            tax_rate_est=tax_rate,
            insurance_ratio_est=insurance_ratio,
            source="zip_override",
        )
    
    # Priority 2: State default
    if state and state.upper() in STATE_DEFAULTS:
        tax_rate, insurance_ratio = STATE_DEFAULTS[state.upper()]
        return LocalCostFactors(
            zip_code=zip_code or "",
            state=state,
            tax_rate_est=tax_rate,
            insurance_ratio_est=insurance_ratio,
            source="state_default",
        )
    
    # Priority 3: Global default
    return LocalCostFactors(
        zip_code=zip_code or "",
        state=state,
        tax_rate_est=GLOBAL_DEFAULT_TAX_RATE,
        insurance_ratio_est=GLOBAL_DEFAULT_INSURANCE_RATIO,
        source="global_default",
    )

