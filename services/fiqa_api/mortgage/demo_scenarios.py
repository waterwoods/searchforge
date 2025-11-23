"""
demo_scenarios.py - Single Home Demo Scenarios

Defines 3-4 highly distinguishable scenario presets for the single-home LangGraph workflow.
These scenarios are used for interview demos and regression testing to show that the same
LangGraph graph takes very different paths depending on the borrower/home profile.
"""

from dataclasses import dataclass
from typing import List, Literal

from services.fiqa_api.mortgage.schemas import StressCheckRequest


@dataclass
class SingleHomeDemoScenario:
    """Demo scenario definition with request parameters and expected outcomes."""
    
    id: str
    title: str
    description: str
    request: StressCheckRequest
    expected_stress_band: Literal["loose", "ok", "tight", "high_risk"]
    expected_hard_block: bool
    expected_use_safety_upgrade: bool
    expected_use_mortgage_programs: bool
    expected_use_strategy_lab: bool


# ============================================================================
# Scenario 1: SoCal High Price, Feels Tight
# ============================================================================

SCENARIO_SOCAL_TIGHT = SingleHomeDemoScenario(
    id="socal_tight",
    title="SoCal High Price, Feels Tight",
    description=(
        "High income but very expensive SoCal home. Payment exceeds safe_band by >20%, "
        "so classified as high_risk even though DTI is in tight range. "
        "Should trigger safety_upgrade, mortgage_programs, and strategy_lab."
    ),
    request=StressCheckRequest(
        monthly_income=15000.0,  # $180k annual - high income
        other_debts_monthly=600.0,  # Car loan + credit cards
        list_price=1100000.0,  # Very expensive SoCal home
        down_payment_pct=0.20,  # 20% down = $220k
        zip_code="92648",  # Huntington Beach, CA
        state="CA",
        hoa_monthly=450.0,  # High HOA typical for SoCal
        risk_preference="neutral",
    ),
    expected_stress_band="high_risk",  # Payment exceeds safe_band by >20%, triggers high_risk even if DTI is in tight range
    expected_hard_block=True,  # Payment way above safe band triggers hard_block
    expected_use_safety_upgrade=True,  # Should search for safer homes
    expected_use_mortgage_programs=True,  # Tight/high_risk should trigger programs search
    expected_use_strategy_lab=True,  # Strategy lab always runs
)


# ============================================================================
# Scenario 2: Texas Starter Home, Comfortable
# ============================================================================

SCENARIO_TEXAS_STARTER_OK = SingleHomeDemoScenario(
    id="texas_starter_ok",
    title="Texas Starter Home, Comfortable",
    description=(
        "Moderate income, reasonable starter home in Texas. Good down payment, low HOA. "
        "DTI below 36% threshold, classified as loose. Should skip safety_upgrade and mortgage_programs, "
        "but still run strategy_lab."
    ),
    request=StressCheckRequest(
        monthly_income=9000.0,  # $108k annual - moderate income
        other_debts_monthly=300.0,  # Minimal debts
        list_price=380000.0,  # Reasonable starter home in Texas
        down_payment_pct=0.20,  # 20% down = $76k
        zip_code="78701",  # Austin, TX
        state="TX",
        hoa_monthly=150.0,  # Low HOA
        risk_preference="neutral",
    ),
    expected_stress_band="loose",  # DTI 32.5% is below 36% threshold, classified as loose
    expected_hard_block=False,
    expected_use_safety_upgrade=False,  # Path should skip safety_upgrade (ok band doesn't trigger it)
    expected_use_mortgage_programs=False,  # No need for assistance
    expected_use_strategy_lab=True,  # What-if lab still runs
)


# ============================================================================
# Scenario 3: Extreme High Risk, Hard Block
# ============================================================================

SCENARIO_EXTREME_HIGH_RISK = SingleHomeDemoScenario(
    id="extreme_high_risk",
    title="Extreme High Risk, Hard Block",
    description=(
        "Low/modest income, very high home_price or almost no down payment, high existing debts. "
        "DTI should be very high, risk flags should trigger hard_block=True. "
        "Should trigger all upgrade paths: safety_upgrade, mortgage_programs, strategy_lab."
    ),
    request=StressCheckRequest(
        monthly_income=4500.0,  # $54k annual - modest income
        other_debts_monthly=1200.0,  # High existing debts (car, credit cards, student loans)
        list_price=850000.0,  # Very high price relative to income
        down_payment_pct=0.05,  # Only 5% down = $42.5k (very low)
        zip_code="90803",  # Long Beach, CA
        state="CA",
        hoa_monthly=400.0,  # High HOA
        risk_preference="neutral",
    ),
    expected_stress_band="high_risk",
    expected_hard_block=True,  # Should trigger hard block
    expected_use_safety_upgrade=True,  # Agent should try to find safer options
    expected_use_mortgage_programs=True,  # Assistance programs are relevant
    expected_use_strategy_lab=True,  # Strategy lab always runs
)


# ============================================================================
# Scenario 4: Borderline but Aid-Eligible
# ============================================================================

SCENARIO_BORDERLINE_WITH_AID = SingleHomeDemoScenario(
    id="borderline_with_aid",
    title="Borderline but Aid-Eligible",
    description=(
        "Borderline DTI/LTV, moderate income. Payment exceeds safe_band by >20%, "
        "so classified as high_risk even though DTI is in tight range. "
        "Should trigger safety_upgrade and mortgage_programs with at least one program in preview."
    ),
    request=StressCheckRequest(
        monthly_income=8000.0,  # $96k annual - moderate income
        other_debts_monthly=500.0,  # Moderate debts
        list_price=550000.0,  # Borderline price for income
        down_payment_pct=0.15,  # 15% down = $82.5k (moderate)
        zip_code="92705",  # Irvine, CA (should have programs available)
        state="CA",
        hoa_monthly=350.0,  # Moderate HOA
        risk_preference="neutral",
    ),
    expected_stress_band="high_risk",  # Payment exceeds safe_band by >20%, triggers high_risk even if DTI is in tight range
    expected_hard_block=True,  # Payment way above safe band triggers hard_block
    expected_use_safety_upgrade=True,  # Tight band triggers safety_upgrade
    expected_use_mortgage_programs=True,  # Should find at least one program
    expected_use_strategy_lab=True,  # Strategy lab always runs
)


# ============================================================================
# Export List
# ============================================================================

SINGLE_HOME_DEMO_SCENARIOS: List[SingleHomeDemoScenario] = [
    SCENARIO_SOCAL_TIGHT,
    SCENARIO_TEXAS_STARTER_OK,
    SCENARIO_EXTREME_HIGH_RISK,
    SCENARIO_BORDERLINE_WITH_AID,
]


__all__ = [
    "SingleHomeDemoScenario",
    "SCENARIO_SOCAL_TIGHT",
    "SCENARIO_TEXAS_STARTER_OK",
    "SCENARIO_EXTREME_HIGH_RISK",
    "SCENARIO_BORDERLINE_WITH_AID",
    "SINGLE_HOME_DEMO_SCENARIOS",
]

