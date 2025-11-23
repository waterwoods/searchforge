#!/usr/bin/env python3
"""
approval_score_smoke.py - Approval Score Smoke Test

Minimal smoke test for approval_score computation in run_stress_check().

Usage:
    python -m experiments.approval_score_smoke
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import run_stress_check, StressCheckRequest


# ============================================================================
# Test Scenarios
# ============================================================================

def test_scenario_1_safe_likely():
    """
    Scenario 1: "Safe/Likely" case (low DTI, reasonable price, high income).
    Expected: High score (>= 70), bucket "likely".
    """
    print("=" * 80)
    print("Scenario 1: Safe/Likely - Low DTI, Reasonable Price, High Income")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=15000.0,  # $180k annual (high income)
        other_debts_monthly=300.0,  # Low debt
        list_price=500000.0,  # Reasonable price
        down_payment_pct=0.25,  # Good down payment
        state="CA",
        hoa_monthly=200.0,
        risk_preference="neutral",
    )
    
    result = run_stress_check(req)
    
    print(f"\n📊 Results:")
    print(f"   Stress Band: {result.stress_band.upper()}")
    print(f"   DTI Ratio: {result.dti_ratio:.1%}")
    
    if result.approval_score:
        print(f"\n✅ Approval Score:")
        print(f"   Score: {result.approval_score.score:.1f}/100")
        print(f"   Bucket: {result.approval_score.bucket.upper()}")
        print(f"   Reasons: {result.approval_score.reasons if result.approval_score.reasons else 'None'}")
    else:
        print(f"\n❌ Approval Score: Not computed (None)")
    
    print("\n" + "=" * 80)
    return result


def test_scenario_2_borderline():
    """
    Scenario 2: "Borderline" case (moderate DTI, reasonable price).
    Expected: Mid score (40-70), bucket "borderline".
    """
    print("=" * 80)
    print("Scenario 2: Borderline - Moderate DTI, Reasonable Price")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=8000.0,  # $96k annual (moderate income)
        other_debts_monthly=600.0,  # Moderate debt
        list_price=550000.0,  # Reasonable price
        down_payment_pct=0.15,  # Moderate down payment
        state="CA",
        hoa_monthly=300.0,
        risk_preference="neutral",
    )
    
    result = run_stress_check(req)
    
    print(f"\n📊 Results:")
    print(f"   Stress Band: {result.stress_band.upper()}")
    print(f"   DTI Ratio: {result.dti_ratio:.1%}")
    
    if result.approval_score:
        print(f"\n✅ Approval Score:")
        print(f"   Score: {result.approval_score.score:.1f}/100")
        print(f"   Bucket: {result.approval_score.bucket.upper()}")
        print(f"   Reasons: {result.approval_score.reasons if result.approval_score.reasons else 'None'}")
    else:
        print(f"\n❌ Approval Score: Not computed (None)")
    
    print("\n" + "=" * 80)
    return result


def test_scenario_3_high_risk_unlikely():
    """
    Scenario 3: "High Risk/Unlikely" case (very high DTI, high price, low income).
    Expected: Low score (< 40), bucket "unlikely".
    """
    print("=" * 80)
    print("Scenario 3: High Risk/Unlikely - Very High DTI, High Price, Low Income")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=5000.0,  # $60k annual (low income)
        other_debts_monthly=1000.0,  # High debt
        list_price=1200000.0,  # Very high price
        down_payment_pct=0.10,  # Low down payment
        state="CA",
        hoa_monthly=500.0,
        risk_preference="neutral",
    )
    
    result = run_stress_check(req)
    
    print(f"\n📊 Results:")
    print(f"   Stress Band: {result.stress_band.upper()}")
    print(f"   DTI Ratio: {result.dti_ratio:.1%}")
    
    if result.approval_score:
        print(f"\n✅ Approval Score:")
        print(f"   Score: {result.approval_score.score:.1f}/100")
        print(f"   Bucket: {result.approval_score.bucket.upper()}")
        print(f"   Reasons: {result.approval_score.reasons if result.approval_score.reasons else 'None'}")
    else:
        print(f"\n❌ Approval Score: Not computed (None)")
    
    print("\n" + "=" * 80)
    return result


def test_scenario_4_edge_case():
    """
    Scenario 4: Edge case (moderate income, high price with good down payment).
    Expected: Varies, but should still compute a score.
    """
    print("=" * 80)
    print("Scenario 4: Edge Case - Moderate Income, High Price, Good Down Payment")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=10000.0,  # $120k annual (moderate income)
        other_debts_monthly=400.0,  # Moderate debt
        list_price=800000.0,  # High price
        down_payment_pct=0.30,  # Good down payment
        state="CA",
        hoa_monthly=400.0,
        risk_preference="conservative",
    )
    
    result = run_stress_check(req)
    
    print(f"\n📊 Results:")
    print(f"   Stress Band: {result.stress_band.upper()}")
    print(f"   DTI Ratio: {result.dti_ratio:.1%}")
    
    if result.approval_score:
        print(f"\n✅ Approval Score:")
        print(f"   Score: {result.approval_score.score:.1f}/100")
        print(f"   Bucket: {result.approval_score.bucket.upper()}")
        print(f"   Reasons: {result.approval_score.reasons if result.approval_score.reasons else 'None'}")
    else:
        print(f"\n❌ Approval Score: Not computed (None)")
    
    print("\n" + "=" * 80)
    return result


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    print("=" * 80)
    print("Approval Score Smoke Test")
    print("=" * 80)
    print("\nTesting approval_score computation in run_stress_check()")
    print()
    
    try:
        # Run Scenario 1: Safe/Likely
        result1 = test_scenario_1_safe_likely()
        
        # Run Scenario 2: Borderline
        result2 = test_scenario_2_borderline()
        
        # Run Scenario 3: High Risk/Unlikely
        result3 = test_scenario_3_high_risk_unlikely()
        
        # Run Scenario 4: Edge Case
        result4 = test_scenario_4_edge_case()
        
        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        
        results = [
            ("Scenario 1 (Safe/Likely)", result1),
            ("Scenario 2 (Borderline)", result2),
            ("Scenario 3 (High Risk/Unlikely)", result3),
            ("Scenario 4 (Edge Case)", result4),
        ]
        
        for name, result in results:
            print(f"\n{name}:")
            print(f"   Stress Band: {result.stress_band}")
            print(f"   DTI: {result.dti_ratio:.1%}")
            if result.approval_score:
                print(f"   Approval Score: {result.approval_score.score:.1f}/100")
                print(f"   Bucket: {result.approval_score.bucket}")
                print(f"   Reasons: {result.approval_score.reasons}")
            else:
                print(f"   Approval Score: None (not computed)")
        
        # Validation checks
        print(f"\n✅ Validation Checks:")
        
        # Check that all scenarios have approval_score
        all_have_scores = all(r.approval_score is not None for _, r in results)
        if all_have_scores:
            print(f"   ✅ All scenarios computed approval_score")
        else:
            print(f"   ⚠️  Some scenarios did not compute approval_score")
        
        # Check Scenario 1 should have high score and "likely" bucket
        if result1.approval_score:
            if result1.approval_score.score >= 70 and result1.approval_score.bucket == "likely":
                print(f"   ✅ Scenario 1 has high score ({result1.approval_score.score:.1f}) and 'likely' bucket")
            else:
                print(f"   ⚠️  Scenario 1 score={result1.approval_score.score:.1f}, bucket={result1.approval_score.bucket} (expected: >=70, 'likely')")
        
        # Check Scenario 3 should have low score and "unlikely" bucket
        if result3.approval_score:
            if result3.approval_score.score < 40 and result3.approval_score.bucket == "unlikely":
                print(f"   ✅ Scenario 3 has low score ({result3.approval_score.score:.1f}) and 'unlikely' bucket")
            else:
                print(f"   ⚠️  Scenario 3 score={result3.approval_score.score:.1f}, bucket={result3.approval_score.bucket} (expected: <40, 'unlikely')")
        
        # Check scores are in valid range
        valid_scores = all(
            r.approval_score is None or (0.0 <= r.approval_score.score <= 100.0)
            for _, r in results
        )
        if valid_scores:
            print(f"   ✅ All approval scores are in valid range [0, 100]")
        else:
            print(f"   ❌ Some approval scores are outside valid range [0, 100]")
        
        print("\n✅ Smoke test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

