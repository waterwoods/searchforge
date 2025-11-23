"""
rates_tool.py - Mortgage Interest Rates Tool
=============================================
Tool for fetching mortgage interest rates (real-time or mock data).

This module provides a pluggable abstraction for mortgage interest rates.
Currently uses mock data via get_mock_rate_for_state(), but can be easily
replaced with real-time API calls without changing the core logic in
mortgage_agent_runtime.py.

Future: Replace mock implementation with real-time rate API integration.
"""

from typing import Any, Dict, List, Optional


def get_mock_rates() -> List[Dict[str, Any]]:
    """
    Get mock mortgage interest rates.
    
    Returns:
        List of rate dictionaries with keys:
            - rate_type: str (e.g., "30-year fixed", "15-year fixed")
            - rate_pct: float (annual percentage rate)
            - last_updated: str (timestamp)
    
    Note: This is a stub implementation. Future versions will fetch
    real-time rates from external APIs or databases.
    """
    return [
        {
            "rate_type": "30-year fixed",
            "rate_pct": 6.0,
            "last_updated": "2024-01-01T00:00:00Z",
        },
        {
            "rate_type": "15-year fixed",
            "rate_pct": 5.5,
            "last_updated": "2024-01-01T00:00:00Z",
        },
    ]


def get_mock_rate_for_state(
    state: Optional[str] = None,
    loan_type: str = "30y_fixed",
) -> float:
    """
    Return a mock annual interest rate (in percent, e.g. 6.25)
    based on state and loan_type. Keep it simple but realistic.
    
    Note: This is a mock implementation. Future versions will fetch
    real-time rates from external APIs or databases.
    
    Args:
        state: State code (optional, e.g., "CA", "NY", "TX")
        loan_type: Loan type identifier (default: "30y_fixed")
    
    Returns:
        Annual interest rate in percent (e.g., 6.0 for 6.0%)
    """
    # Simple state-based rate variations (mock data)
    # In production, this would call a real rate API
    state_rate_adjustments = {
        "CA": 0.0,   # California: baseline
        "NY": 0.1,   # New York: slightly higher
        "TX": -0.15, # Texas: slightly lower
        "FL": -0.05, # Florida: slightly lower
        "WA": 0.05,  # Washington: slightly higher
    }
    
    # Base rate by loan type
    base_rates = {
        "30y_fixed": 6.0,
        "15y_fixed": 5.5,
        "30y_arm": 5.75,
    }
    
    # Get base rate for loan type (default to 30y_fixed)
    base_rate = base_rates.get(loan_type, 6.0)
    
    # Apply state adjustment if available
    if state and state.upper() in state_rate_adjustments:
        adjustment = state_rate_adjustments[state.upper()]
        return base_rate + adjustment
    
    # Default to base rate
    return base_rate


__all__ = ["get_mock_rates", "get_mock_rate_for_state"]

