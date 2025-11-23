"""
strategy_lab_smoke.py - Smoke test for Strategy Lab module
===========================================================
Simple smoke test to verify run_strategy_lab() works correctly.
"""

import sys

# Add project root to path
sys.path.insert(0, "/home/andy/searchforge")

from services.fiqa_api.mortgage import run_strategy_lab, StressCheckRequest


def test_relaxed_case():
    """Test with a relaxed case (good income, affordable price)."""
    print("\n" + "=" * 80)
    print("TEST 1: Relaxed Case")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=10000.0,  # $120k annual
        other_debts_monthly=500.0,
        list_price=400000.0,  # $400k home
        down_payment_pct=0.20,  # 20% down
        zip_code="98101",
        state="WA",
        hoa_monthly=200.0,
        risk_preference="neutral",
    )
    
    result = run_strategy_lab(req, max_scenarios=3)
    
    print(f"\nBaseline Metrics:")
    print(f"  Stress Band: {result.baseline_stress_band}")
    print(f"  DTI Ratio: {result.baseline_dti:.2%}" if result.baseline_dti else "  DTI Ratio: N/A")
    print(f"  Total Payment: ${result.baseline_total_payment:,.2f}" if result.baseline_total_payment else "  Total Payment: N/A")
    if result.baseline_approval_score:
        print(f"  Approval Score: {result.baseline_approval_score.score:.1f} ({result.baseline_approval_score.bucket})")
    
    print(f"\nScenarios Generated: {len(result.scenarios)}")
    for i, scenario in enumerate(result.scenarios, 1):
        print(f"\n  Scenario {i}: {scenario.title} (ID: {scenario.id})")
        if scenario.description:
            print(f"    Description: {scenario.description}")
        print(f"    Stress Band: {scenario.stress_band}")
        if scenario.dti_ratio is not None:
            print(f"    DTI Ratio: {scenario.dti_ratio:.2%}")
        if scenario.total_payment is not None:
            print(f"    Total Payment: ${scenario.total_payment:,.2f}")
        if scenario.approval_score:
            print(f"    Approval Score: {scenario.approval_score.score:.1f} ({scenario.approval_score.bucket})")
        if scenario.note_tags:
            print(f"    Tags: {', '.join(scenario.note_tags)}")


def test_tight_case():
    """Test with a tight case (lower income, higher price)."""
    print("\n" + "=" * 80)
    print("TEST 2: Tight Case")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=6000.0,  # $72k annual
        other_debts_monthly=800.0,
        list_price=500000.0,  # $500k home
        down_payment_pct=0.15,  # 15% down
        zip_code="98101",
        state="WA",
        hoa_monthly=300.0,
        risk_preference="neutral",
    )
    
    result = run_strategy_lab(req, max_scenarios=3)
    
    print(f"\nBaseline Metrics:")
    print(f"  Stress Band: {result.baseline_stress_band}")
    print(f"  DTI Ratio: {result.baseline_dti:.2%}" if result.baseline_dti else "  DTI Ratio: N/A")
    print(f"  Total Payment: ${result.baseline_total_payment:,.2f}" if result.baseline_total_payment else "  Total Payment: N/A")
    if result.baseline_approval_score:
        print(f"  Approval Score: {result.baseline_approval_score.score:.1f} ({result.baseline_approval_score.bucket})")
    
    print(f"\nScenarios Generated: {len(result.scenarios)}")
    for i, scenario in enumerate(result.scenarios, 1):
        print(f"\n  Scenario {i}: {scenario.title} (ID: {scenario.id})")
        if scenario.description:
            print(f"    Description: {scenario.description}")
        print(f"    Stress Band: {scenario.stress_band}")
        if scenario.dti_ratio is not None:
            print(f"    DTI Ratio: {scenario.dti_ratio:.2%}")
        if scenario.total_payment is not None:
            print(f"    Total Payment: ${scenario.total_payment:,.2f}")
        if scenario.approval_score:
            print(f"    Approval Score: {scenario.approval_score.score:.1f} ({scenario.approval_score.bucket})")
        if scenario.note_tags:
            print(f"    Tags: {', '.join(scenario.note_tags)}")


def test_high_risk_case():
    """Test with a high-risk case (low income, very high price)."""
    print("\n" + "=" * 80)
    print("TEST 3: High Risk Case")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=5000.0,  # $60k annual
        other_debts_monthly=1000.0,
        list_price=800000.0,  # $800k home
        down_payment_pct=0.10,  # 10% down (low)
        zip_code="98101",
        state="WA",
        hoa_monthly=400.0,
        risk_preference="aggressive",  # Aggressive risk preference
    )
    
    result = run_strategy_lab(req, max_scenarios=3)
    
    print(f"\nBaseline Metrics:")
    print(f"  Stress Band: {result.baseline_stress_band}")
    print(f"  DTI Ratio: {result.baseline_dti:.2%}" if result.baseline_dti else "  DTI Ratio: N/A")
    print(f"  Total Payment: ${result.baseline_total_payment:,.2f}" if result.baseline_total_payment else "  Total Payment: N/A")
    if result.baseline_approval_score:
        print(f"  Approval Score: {result.baseline_approval_score.score:.1f} ({result.baseline_approval_score.bucket})")
    
    print(f"\nScenarios Generated: {len(result.scenarios)}")
    for i, scenario in enumerate(result.scenarios, 1):
        print(f"\n  Scenario {i}: {scenario.title} (ID: {scenario.id})")
        if scenario.description:
            print(f"    Description: {scenario.description}")
        print(f"    Stress Band: {scenario.stress_band}")
        if scenario.dti_ratio is not None:
            print(f"    DTI Ratio: {scenario.dti_ratio:.2%}")
        if scenario.total_payment is not None:
            print(f"    Total Payment: ${scenario.total_payment:,.2f}")
        if scenario.approval_score:
            print(f"    Approval Score: {scenario.approval_score.score:.1f} ({scenario.approval_score.bucket})")
        if scenario.note_tags:
            print(f"    Tags: {', '.join(scenario.note_tags)}")


def main():
    """Run all smoke tests."""
    print("Strategy Lab Smoke Test")
    print("=" * 80)
    print("Testing run_strategy_lab() with various input cases...")
    
    try:
        test_relaxed_case()
        test_tight_case()
        test_high_risk_case()
        
        print("\n" + "=" * 80)
        print("All smoke tests completed successfully!")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Error during smoke test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

