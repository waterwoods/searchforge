#!/usr/bin/env python3
"""
single_home_agent_integration_test.py - Direct Python test for single-home agent with safety upgrade

Tests the integration of run_safety_upgrade_flow into run_single_home_agent without HTTP.

Usage:
    python3 -m experiments.single_home_agent_integration_test
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import (
    run_single_home_agent,
    SingleHomeAgentRequest,
    StressCheckRequest,
)


def test_tight_case_with_zip():
    """Test tight case with ZIP code - should trigger safety upgrade flow."""
    print("=" * 80)
    print("Test 1: Tight Case with ZIP Code")
    print("=" * 80)
    
    req = SingleHomeAgentRequest(
        stress_request=StressCheckRequest(
            monthly_income=6500.0,
            other_debts_monthly=500.0,
            list_price=900000.0,
            down_payment_pct=0.20,
            zip_code="90803",
            state="CA",
            hoa_monthly=400.0,
            risk_preference="neutral",
        ),
        user_message="Is this home too tight for my budget?",
    )
    
    result = run_single_home_agent(req)
    
    print(f"\n📊 Stress Result:")
    print(f"   Stress Band: {result.stress_result.stress_band}")
    print(f"   DTI: {result.stress_result.dti_ratio:.1%}")
    
    print(f"\n🛡️  Safety Upgrade:")
    if result.safety_upgrade:
        print(f"   ✅ Present")
        print(f"   Baseline Band: {result.safety_upgrade.baseline_band}")
        print(f"   Is Tight or Worse: {result.safety_upgrade.baseline_is_tight_or_worse}")
        if result.safety_upgrade.primary_suggestion:
            print(f"   Primary Suggestion:")
            print(f"      Title: {result.safety_upgrade.primary_suggestion.title}")
            print(f"      Reason: {result.safety_upgrade.primary_suggestion.reason}")
        if result.safety_upgrade.safer_homes:
            print(f"   Safer Homes: {len(result.safety_upgrade.safer_homes.candidates)} candidates")
    else:
        print(f"   ❌ Missing (should be present)")
    
    print(f"\n💬 Borrower Narrative: {'✅ Present' if result.borrower_narrative else '⚠️  None (LLM may be disabled)'}")
    print(f"💡 Recommended Actions: {'✅ Present' if result.recommended_actions else '⚠️  None (LLM may be disabled)'}")
    
    print("\n" + "=" * 80)
    return result


def test_loose_case():
    """Test loose case - should show comfortable suggestion."""
    print("=" * 80)
    print("Test 2: Loose Case (Comfortable)")
    print("=" * 80)
    
    req = SingleHomeAgentRequest(
        stress_request=StressCheckRequest(
            monthly_income=15000.0,
            other_debts_monthly=500.0,
            list_price=600000.0,
            down_payment_pct=0.20,
            zip_code="90803",
            state="CA",
            hoa_monthly=350.0,
            risk_preference="neutral",
        ),
        user_message="How does this look?",
    )
    
    result = run_single_home_agent(req)
    
    print(f"\n📊 Stress Result:")
    print(f"   Stress Band: {result.stress_result.stress_band}")
    print(f"   DTI: {result.stress_result.dti_ratio:.1%}")
    
    print(f"\n🛡️  Safety Upgrade:")
    if result.safety_upgrade:
        print(f"   ✅ Present")
        print(f"   Baseline Band: {result.safety_upgrade.baseline_band}")
        print(f"   Is Tight or Worse: {result.safety_upgrade.baseline_is_tight_or_worse}")
        if result.safety_upgrade.primary_suggestion:
            print(f"   Primary Suggestion:")
            print(f"      Title: {result.safety_upgrade.primary_suggestion.title}")
            print(f"      Reason: {result.safety_upgrade.primary_suggestion.reason}")
    else:
        print(f"   ❌ Missing (should be present)")
    
    print("\n" + "=" * 80)
    return result


def main():
    """Main entry point."""
    print("=" * 80)
    print("Single Home Agent Integration Test (with Safety Upgrade)")
    print("=" * 80)
    print("\nTesting run_single_home_agent() with safety_upgrade integration")
    print()
    
    try:
        result1 = test_tight_case_with_zip()
        result2 = test_loose_case()
        
        # Validation
        print("\n" + "=" * 80)
        print("Validation Summary")
        print("=" * 80)
        
        all_have_safety_upgrade = all(
            result.safety_upgrade is not None
            for result in [result1, result2]
        )
        
        if all_have_safety_upgrade:
            print("✅ All tests have safety_upgrade present")
        else:
            print("❌ Some tests missing safety_upgrade")
        
        if result1.safety_upgrade and result1.safety_upgrade.baseline_is_tight_or_worse:
            print("✅ Test 1 correctly identifies tight/worse baseline")
        else:
            print("⚠️  Test 1 baseline classification may be incorrect")
        
        if result2.safety_upgrade and not result2.safety_upgrade.baseline_is_tight_or_worse:
            print("✅ Test 2 correctly identifies comfortable baseline")
        else:
            print("⚠️  Test 2 baseline classification may be incorrect")
        
        print("\n✅ Integration test completed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

