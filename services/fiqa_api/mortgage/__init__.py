"""
mortgage - Mortgage Agent Package
==================================
Independent mortgage planning package with tools for rates, properties, etc.
"""

from services.fiqa_api.mortgage.mortgage_agent_runtime import (
    compare_properties_for_borrower,
    run_mortgage_agent,
    run_safety_upgrade_flow,
    run_single_home_agent,
    run_stress_check,
    run_strategy_lab,
    search_safer_homes_for_case,
)
from services.fiqa_api.mortgage.local_cost_factors import (
    LocalCostFactors,
    get_local_cost_factors,
)
from services.fiqa_api.mortgage.risk_assessment import (
    assess_risk,
    assess_risk_from_plan,
)
from services.fiqa_api.mortgage.schemas import (
    MaxAffordabilitySummary,
    MortgageAgentRequest,
    MortgageAgentResponse,
    MortgageCompareRequest,
    MortgageCompareResponse,
    MortgagePlan,
    RiskAssessment,
    SingleHomeAgentRequest,
    SingleHomeAgentResponse,
    StressCheckRequest,
    StressCheckResponse,
    StressBand,
    SaferHomeCandidate,
    SaferHomesResult,
    SafetyUpgradeSuggestion,
    SafetyUpgradeResult,
    StrategyScenario,
    StrategyLabResult,
)

__all__ = [
    "run_mortgage_agent",
    "compare_properties_for_borrower",
    "run_stress_check",
    "run_single_home_agent",
    "run_safety_upgrade_flow",
    "run_strategy_lab",
    "search_safer_homes_for_case",
    "assess_risk",
    "assess_risk_from_plan",
    "MortgageAgentRequest",
    "MortgageAgentResponse",
    "MortgageCompareRequest",
    "MortgageCompareResponse",
    "MortgagePlan",
    "MaxAffordabilitySummary",
    "RiskAssessment",
    "StressCheckRequest",
    "StressCheckResponse",
    "StressBand",
    "SingleHomeAgentRequest",
    "SingleHomeAgentResponse",
    "SaferHomeCandidate",
    "SaferHomesResult",
    "SafetyUpgradeSuggestion",
    "SafetyUpgradeResult",
    "StrategyScenario",
    "StrategyLabResult",
    "LocalCostFactors",
    "get_local_cost_factors",
]

