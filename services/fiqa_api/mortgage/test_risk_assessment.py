"""
test_risk_assessment.py - Simple test for risk assessment module
================================================================
Quick validation tests for the risk assessment module.
"""

import sys
from datetime import datetime
from typing import List

# Add project root to path
sys.path.insert(0, "/home/andy/searchforge")

from services.fiqa_api.mortgage.risk_assessment import (
    assess_risk,
    assess_risk_from_plan,
)
from services.fiqa_api.mortgage.schemas import (
    ApprovalScore,
    CaseState,
    MortgagePlan,
    MaxAffordabilitySummary,
    RiskAssessment,
    StressCheckResponse,
)


def test_assess_risk_high_dti():
    """Test risk assessment with high DTI ratio."""
    print("Test 1: High DTI ratio (85%)")
    
    stress_response = StressCheckResponse(
        total_monthly_payment=5000.0,
        principal_interest_payment=4000.0,
        estimated_tax_ins_hoa=1000.0,
        dti_ratio=0.85,  # 85% DTI - very high
        stress_band="high_risk",
        hard_warning="DTI exceeds 80%",
        wallet_snapshot={
            "monthly_income": 8000.0,
            "annual_income": 96000.0,
            "other_debts_monthly": 2000.0,
            "safe_payment_band": {"min_safe": 1000.0, "max_safe": 2000.0},
        },
        home_snapshot={
            "list_price": 500000.0,
            "loan_amount": 400000.0,
            "down_payment_pct": 0.20,
        },
        approval_score=ApprovalScore(score=15.0, bucket="unlikely", reasons=["high_dti"]),
    )
    
    result = assess_risk(stress_response=stress_response)
    
    assert result.hard_block is True, "High DTI (85%) should trigger hard_block"
    assert "very_high_dti" in result.risk_flags, "Should have very_high_dti flag"
    assert "high_risk_band" in result.risk_flags, "Should have high_risk_band flag"
    assert "unlikely_approval" in result.risk_flags, "Should have unlikely_approval flag"
    
    print(f"  ✓ Hard block: {result.hard_block}")
    print(f"  ✓ Risk flags: {result.risk_flags}")
    print("  ✓ PASSED\n")


def test_assess_risk_negative_cashflow():
    """Test risk assessment with negative cashflow."""
    print("Test 2: Negative cashflow")
    
    # Monthly income: $5000
    # Monthly payment: $4000
    # Other debts: $1500
    # Total expenses: $5500 > $5000 income → negative cashflow
    
    stress_response = StressCheckResponse(
        total_monthly_payment=4000.0,
        principal_interest_payment=3500.0,
        estimated_tax_ins_hoa=500.0,
        dti_ratio=0.45,
        stress_band="tight",
        hard_warning=None,
        wallet_snapshot={
            "monthly_income": 5000.0,
            "annual_income": 60000.0,
            "other_debts_monthly": 1500.0,  # Total: $5500 > $5000
            "safe_payment_band": {"min_safe": 1000.0, "max_safe": 3000.0},
        },
        home_snapshot={
            "list_price": 400000.0,
            "loan_amount": 320000.0,
            "down_payment_pct": 0.20,
        },
    )
    
    result = assess_risk(stress_response=stress_response)
    
    assert result.hard_block is True, "Negative cashflow should trigger hard_block"
    assert "negative_cashflow" in result.risk_flags, "Should have negative_cashflow flag"
    assert "high_dti" in result.risk_flags, "Should have high_dti flag (45%)"
    
    print(f"  ✓ Hard block: {result.hard_block}")
    print(f"  ✓ Risk flags: {result.risk_flags}")
    print("  ✓ PASSED\n")


def test_assess_risk_soft_warning():
    """Test risk assessment with soft warning (tight band)."""
    print("Test 3: Soft warning (tight band)")
    
    stress_response = StressCheckResponse(
        total_monthly_payment=3000.0,
        principal_interest_payment=2500.0,
        estimated_tax_ins_hoa=500.0,
        dti_ratio=0.42,  # Just below high threshold
        stress_band="tight",
        hard_warning=None,
        wallet_snapshot={
            "monthly_income": 8000.0,
            "annual_income": 96000.0,
            "other_debts_monthly": 500.0,
            "safe_payment_band": {"min_safe": 1000.0, "max_safe": 2800.0},  # Payment exceeds max
        },
        home_snapshot={
            "list_price": 400000.0,
            "loan_amount": 320000.0,
            "down_payment_pct": 0.20,
        },
    )
    
    result = assess_risk(stress_response=stress_response)
    
    assert result.hard_block is False, "Should not trigger hard_block"
    assert result.soft_warning is True, "Tight band should trigger soft_warning"
    assert "tight_band" in result.risk_flags, "Should have tight_band flag"
    assert "payment_above_safe_band" in result.risk_flags, "Should have payment_above_safe_band flag"
    
    print(f"  ✓ Hard block: {result.hard_block}")
    print(f"  ✓ Soft warning: {result.soft_warning}")
    print(f"  ✓ Risk flags: {result.risk_flags}")
    print("  ✓ PASSED\n")


def test_assess_risk_low_risk():
    """Test risk assessment with low risk scenario."""
    print("Test 4: Low risk scenario")
    
    stress_response = StressCheckResponse(
        total_monthly_payment=2000.0,
        principal_interest_payment=1500.0,
        estimated_tax_ins_hoa=500.0,
        dti_ratio=0.30,  # Low DTI
        stress_band="loose",
        hard_warning=None,
        wallet_snapshot={
            "monthly_income": 8000.0,
            "annual_income": 96000.0,
            "other_debts_monthly": 500.0,
            "safe_payment_band": {"min_safe": 1000.0, "max_safe": 3000.0},
        },
        home_snapshot={
            "list_price": 300000.0,
            "loan_amount": 240000.0,
            "down_payment_pct": 0.20,
        },
        approval_score=ApprovalScore(score=85.0, bucket="likely", reasons=["strong_income"]),
    )
    
    result = assess_risk(stress_response=stress_response)
    
    assert result.hard_block is False, "Low risk should not trigger hard_block"
    assert result.soft_warning is False, "Low risk should not trigger soft_warning"
    assert len(result.risk_flags) == 0 or all(
        flag not in ["high_dti", "negative_cashflow", "high_risk_band", "tight_band"]
        for flag in result.risk_flags
    ), "Low risk should not have major risk flags"
    
    print(f"  ✓ Hard block: {result.hard_block}")
    print(f"  ✓ Soft warning: {result.soft_warning}")
    print(f"  ✓ Risk flags: {result.risk_flags}")
    print("  ✓ PASSED\n")


def test_assess_risk_from_plan():
    """Test risk assessment from plan data."""
    print("Test 5: Risk assessment from plan data")
    
    max_aff = MaxAffordabilitySummary(
        max_monthly_payment=3000.0,
        max_loan_amount=350000.0,
        max_home_price=400000.0,
        assumed_interest_rate=6.0,
        target_dti=0.36,
    )
    
    result = assess_risk_from_plan(
        dti_ratio=0.50,
        stress_band="tight",
        monthly_payment=3500.0,
        max_affordability={
            "max_home_price": 400000.0,
        },
        target_purchase_price=600000.0,  # 50% over max affordability
    )
    
    assert result.hard_block is True, "Large affordability gap should trigger hard_block"
    assert "affordability_gap" in result.risk_flags, "Should have affordability_gap flag"
    assert "high_dti" in result.risk_flags, "Should have high_dti flag"
    
    print(f"  ✓ Hard block: {result.hard_block}")
    print(f"  ✓ Risk flags: {result.risk_flags}")
    print("  ✓ PASSED\n")


def test_assess_risk_from_case_state():
    """Test risk assessment from case state."""
    print("Test 6: Risk assessment from case state")
    
    case_state = CaseState(
        case_id="test_case_001",
        timestamp=datetime.now().isoformat(),
        inputs={
            "monthly_income": 8000.0,
            "other_debts_monthly": 500.0,
            "list_price": 500000.0,
            "down_payment_pct": 0.20,
        },
        plans=[
            MortgagePlan(
                plan_id="plan_001",
                name="Test Plan",
                monthly_payment=4500.0,
                interest_rate=6.0,
                loan_amount=400000.0,
                term_years=30,
                dti_ratio=0.82,  # Very high DTI
                risk_level="high",
                pros=[],
                cons=[],
            )
        ],
        max_affordability=None,
        risk_summary={
            "dti_ratio": 0.82,
            "stress_band": "high_risk",
            "hard_warning": "DTI exceeds 80%",
        },
    )
    
    result = assess_risk(case_state=case_state)
    
    assert result.hard_block is True, "High DTI from case_state should trigger hard_block"
    assert "very_high_dti" in result.risk_flags, "Should have very_high_dti flag"
    assert "high_risk_band" in result.risk_flags, "Should have high_risk_band flag"
    
    print(f"  ✓ Hard block: {result.hard_block}")
    print(f"  ✓ Risk flags: {result.risk_flags}")
    print("  ✓ PASSED\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Risk Assessment Module Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_assess_risk_high_dti,
        test_assess_risk_negative_cashflow,
        test_assess_risk_soft_warning,
        test_assess_risk_low_risk,
        test_assess_risk_from_plan,
        test_assess_risk_from_case_state,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}\n")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

