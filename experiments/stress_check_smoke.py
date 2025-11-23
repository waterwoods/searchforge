#!/usr/bin/env python3
"""
stress_check_smoke.py - Stress Check Smoke Test

Minimal smoke test for run_stress_check() function.

Usage:
    python -m experiments.stress_check_smoke
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

def test_scenario_1_loose_ok():
    """
    Scenario 1: "Loose/OK" SoCal home (income high, price modest).
    """
    print("=" * 80)
    print("Scenario 1: Loose/OK - High Income, Modest Price")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=15000.0,  # $180k annual
        other_debts_monthly=500.0,
        list_price=600000.0,  # Modest for SoCal
        down_payment_pct=0.20,
        state="CA",
        hoa_monthly=350.0,
        risk_preference="neutral",
    )
    
    result = run_stress_check(req)
    
    print(f"\n📊 Results:")
    print(f"   Total Monthly Payment: ${result.total_monthly_payment:,.2f}")
    print(f"   Principal & Interest: ${result.principal_interest_payment:,.2f}")
    print(f"   Tax/Ins/HOA: ${result.estimated_tax_ins_hoa:,.2f}")
    print(f"   DTI Ratio: {result.dti_ratio:.1%}")
    print(f"   Stress Band: {result.stress_band.upper()}")
    
    if result.hard_warning:
        print(f"   ⚠️  Hard Warning: {result.hard_warning}")
    else:
        print(f"   ✅ No hard warning")
    
    if result.case_state:
        print(f"\n📸 Case State:")
        print(f"   Case ID: {result.case_state.case_id}")
        print(f"   Timestamp: {result.case_state.timestamp}")
        risk_summary = result.case_state.risk_summary
        if risk_summary:
            print(f"   DTI: {risk_summary.get('dti_ratio', 0):.1%}")
            print(f"   Stress Band: {risk_summary.get('stress_band', 'N/A')}")
    
    if result.agent_steps:
        print(f"\n🔍 Agent Steps ({len(result.agent_steps)} steps):")
        for idx, step in enumerate(result.agent_steps, 1):
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "pending": "⏳",
                "in_progress": "🔄",
            }.get(step.status, "❓")
            duration_str = f" ({step.duration_ms:.1f}ms)" if step.duration_ms else ""
            print(f"   {idx}. {status_icon} {step.step_name} [{step.status}]{duration_str}")
    
    print("\n" + "=" * 80)
    return result


def test_scenario_2_tight_high_risk():
    """
    Scenario 2: "Tight/High Risk" home (income modest, price very high).
    """
    print("=" * 80)
    print("Scenario 2: Tight/High Risk - Modest Income, Very High Price")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=5000.0,  # $60k annual (modest)
        other_debts_monthly=800.0,
        list_price=1200000.0,  # Very high price
        down_payment_pct=0.10,  # Low down payment
        state="CA",
        hoa_monthly=500.0,
        risk_preference="neutral",
    )
    
    result = run_stress_check(req)
    
    print(f"\n📊 Results:")
    print(f"   Total Monthly Payment: ${result.total_monthly_payment:,.2f}")
    print(f"   Principal & Interest: ${result.principal_interest_payment:,.2f}")
    print(f"   Tax/Ins/HOA: ${result.estimated_tax_ins_hoa:,.2f}")
    print(f"   DTI Ratio: {result.dti_ratio:.1%}")
    print(f"   Stress Band: {result.stress_band.upper()}")
    
    if result.hard_warning:
        print(f"   ⚠️  Hard Warning: {result.hard_warning}")
    else:
        print(f"   ✅ No hard warning")
    
    if result.case_state:
        print(f"\n📸 Case State:")
        print(f"   Case ID: {result.case_state.case_id}")
        print(f"   Timestamp: {result.case_state.timestamp}")
        risk_summary = result.case_state.risk_summary
        if risk_summary:
            print(f"   DTI: {risk_summary.get('dti_ratio', 0):.1%}")
            print(f"   Stress Band: {risk_summary.get('stress_band', 'N/A')}")
    
    if result.agent_steps:
        print(f"\n🔍 Agent Steps ({len(result.agent_steps)} steps):")
        for idx, step in enumerate(result.agent_steps, 1):
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "pending": "⏳",
                "in_progress": "🔄",
            }.get(step.status, "❓")
            duration_str = f" ({step.duration_ms:.1f}ms)" if step.duration_ms else ""
            print(f"   {idx}. {status_icon} {step.step_name} [{step.status}]{duration_str}")
    
    print("\n" + "=" * 80)
    return result


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    print("=" * 80)
    print("Stress Check Smoke Test")
    print("=" * 80)
    print("\nTesting run_stress_check() function directly (not HTTP)")
    print()
    
    try:
        # Run Scenario 1
        result1 = test_scenario_1_loose_ok()
        
        # Run Scenario 2
        result2 = test_scenario_2_tight_high_risk()
        
        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"\nScenario 1 (Loose/OK):")
        print(f"   Stress Band: {result1.stress_band}")
        print(f"   DTI: {result1.dti_ratio:.1%}")
        print(f"   Total Payment: ${result1.total_monthly_payment:,.2f}")
        
        print(f"\nScenario 2 (Tight/High Risk):")
        print(f"   Stress Band: {result2.stress_band}")
        print(f"   DTI: {result2.dti_ratio:.1%}")
        print(f"   Total Payment: ${result2.total_monthly_payment:,.2f}")
        
        # Validation checks
        print(f"\n✅ Validation Checks:")
        
        # Check Scenario 1 should be loose or ok
        if result1.stress_band in ["loose", "ok"]:
            print(f"   ✅ Scenario 1 stress band is {result1.stress_band} (expected: loose or ok)")
        else:
            print(f"   ⚠️  Scenario 1 stress band is {result1.stress_band} (expected: loose or ok)")
        
        # Check Scenario 2 should be tight or high_risk
        if result2.stress_band in ["tight", "high_risk"]:
            print(f"   ✅ Scenario 2 stress band is {result2.stress_band} (expected: tight or high_risk)")
        else:
            print(f"   ⚠️  Scenario 2 stress band is {result2.stress_band} (expected: tight or high_risk)")
        
        # Check DTI ratios are reasonable
        if 0.0 < result1.dti_ratio < 1.0:
            print(f"   ✅ Scenario 1 DTI ratio is valid: {result1.dti_ratio:.1%}")
        else:
            print(f"   ❌ Scenario 1 DTI ratio is invalid: {result1.dti_ratio:.1%}")
        
        if 0.0 < result2.dti_ratio < 1.0:
            print(f"   ✅ Scenario 2 DTI ratio is valid: {result2.dti_ratio:.1%}")
        else:
            print(f"   ❌ Scenario 2 DTI ratio is invalid: {result2.dti_ratio:.1%}")
        
        # Check payments are positive
        if result1.total_monthly_payment > 0:
            print(f"   ✅ Scenario 1 total payment is positive: ${result1.total_monthly_payment:,.2f}")
        else:
            print(f"   ❌ Scenario 1 total payment is not positive: ${result1.total_monthly_payment:,.2f}")
        
        if result2.total_monthly_payment > 0:
            print(f"   ✅ Scenario 2 total payment is positive: ${result2.total_monthly_payment:,.2f}")
        else:
            print(f"   ❌ Scenario 2 total payment is not positive: ${result2.total_monthly_payment:,.2f}")
        
        print("\n✅ Smoke test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


