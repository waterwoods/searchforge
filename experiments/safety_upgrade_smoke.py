#!/usr/bin/env python3
"""
safety_upgrade_smoke.py - Safety Upgrade Flow Smoke Test

Minimal smoke test for run_safety_upgrade_flow() function.

Usage:
    python -m experiments.safety_upgrade_smoke
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import run_safety_upgrade_flow, StressCheckRequest


# ============================================================================
# Test Scenarios
# ============================================================================

def test_scenario_1_loose_ok():
    """
    Scenario 1: Loose/OK baseline → no safer search, safe suggestion.
    """
    print("=" * 80)
    print("Scenario 1: Loose/OK Baseline - No Safer Search Needed")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=15000.0,  # $180k annual
        other_debts_monthly=500.0,
        list_price=600000.0,  # Modest for SoCal
        down_payment_pct=0.20,
        zip_code="90803",
        state="CA",
        hoa_monthly=350.0,
        risk_preference="neutral",
    )
    
    result = run_safety_upgrade_flow(req, max_candidates=5)
    
    print(f"\n📊 Baseline Results:")
    print(f"   Stress Band: {result.baseline_band}")
    print(f"   DTI: {result.baseline_dti:.1%}" if result.baseline_dti else "   DTI: N/A")
    print(f"   Total Payment: ${result.baseline_total_payment:,.2f}" if result.baseline_total_payment else "   Total Payment: N/A")
    print(f"   ZIP Code: {result.baseline_zip_code or 'N/A'}")
    print(f"   State: {result.baseline_state or 'N/A'}")
    print(f"   Is Tight or Worse: {result.baseline_is_tight_or_worse}")
    
    print(f"\n🔍 Safer Homes Search:")
    if result.safer_homes:
        print(f"   ZIP Searched: {result.safer_homes.zip_code}")
        print(f"   Candidates Found: {len(result.safer_homes.candidates)}")
    else:
        print(f"   ⏭️  No safer homes search performed (baseline is comfortable)")
    
    print(f"\n💡 Primary Suggestion:")
    if result.primary_suggestion:
        print(f"   Reason: {result.primary_suggestion.reason}")
        print(f"   Title: {result.primary_suggestion.title}")
        print(f"   Details: {result.primary_suggestion.details}")
        if result.primary_suggestion.notes:
            print(f"   Notes:")
            for note in result.primary_suggestion.notes:
                print(f"      - {note}")
    else:
        print(f"   ⚠️  No primary suggestion")
    
    print(f"\n📋 Alternative Suggestions: {len(result.alternative_suggestions)}")
    for idx, alt in enumerate(result.alternative_suggestions, 1):
        print(f"   {idx}. {alt.title}")
        print(f"      Reason: {alt.reason}")
    
    print("\n" + "=" * 80)
    return result


def test_scenario_2_tight_with_zip():
    """
    Scenario 2: Tight baseline with ZIP that has mock listings → safer homes suggested.
    """
    print("=" * 80)
    print("Scenario 2: Tight Baseline with ZIP - Safer Homes Suggested")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=6500.0,  # $78k annual
        other_debts_monthly=500.0,
        list_price=900000.0,  # High price for this income
        down_payment_pct=0.20,
        zip_code="90803",  # ZIP with mock listings
        state="CA",
        hoa_monthly=400.0,
        risk_preference="neutral",
    )
    
    result = run_safety_upgrade_flow(req, max_candidates=5)
    
    print(f"\n📊 Baseline Results:")
    print(f"   Stress Band: {result.baseline_band}")
    print(f"   DTI: {result.baseline_dti:.1%}" if result.baseline_dti else "   DTI: N/A")
    print(f"   Total Payment: ${result.baseline_total_payment:,.2f}" if result.baseline_total_payment else "   Total Payment: N/A")
    print(f"   ZIP Code: {result.baseline_zip_code or 'N/A'}")
    print(f"   Is Tight or Worse: {result.baseline_is_tight_or_worse}")
    
    print(f"\n🔍 Safer Homes Search:")
    if result.safer_homes:
        print(f"   ZIP Searched: {result.safer_homes.zip_code}")
        print(f"   Baseline Band: {result.safer_homes.baseline_band}")
        print(f"   Baseline DTI: {result.safer_homes.baseline_dti_ratio:.1%}" if result.safer_homes.baseline_dti_ratio else "   Baseline DTI: N/A")
        print(f"   Candidates Found: {len(result.safer_homes.candidates)}")
        
        if result.safer_homes.candidates:
            print(f"\n🏠 Top Safer Home Candidates:")
            for idx, candidate in enumerate(result.safer_homes.candidates[:3], 1):
                print(f"   {idx}. {candidate.listing.title}")
                print(f"      Price: ${candidate.listing.list_price:,.0f}")
                print(f"      Stress Band: {candidate.stress_band}")
                print(f"      DTI: {candidate.dti_ratio:.1%}" if candidate.dti_ratio else "      DTI: N/A")
    else:
        print(f"   ⚠️  No safer homes search performed")
    
    print(f"\n💡 Primary Suggestion:")
    if result.primary_suggestion:
        print(f"   Reason: {result.primary_suggestion.reason}")
        print(f"   Title: {result.primary_suggestion.title}")
        print(f"   Details: {result.primary_suggestion.details[:200]}..." if len(result.primary_suggestion.details) > 200 else f"   Details: {result.primary_suggestion.details}")
        if result.primary_suggestion.delta_dti is not None:
            print(f"   Delta DTI: {result.primary_suggestion.delta_dti:.1%}")
        if result.primary_suggestion.target_price is not None:
            print(f"   Target Price: ${result.primary_suggestion.target_price:,.0f}")
    else:
        print(f"   ⚠️  No primary suggestion")
    
    print(f"\n📋 Alternative Suggestions: {len(result.alternative_suggestions)}")
    for idx, alt in enumerate(result.alternative_suggestions, 1):
        print(f"   {idx}. {alt.title}")
        print(f"      Reason: {alt.reason}")
    
    print("\n" + "=" * 80)
    return result


def test_scenario_3_high_risk_no_zip():
    """
    Scenario 3: High risk with missing ZIP → warning about missing ZIP.
    """
    print("=" * 80)
    print("Scenario 3: High Risk with Missing ZIP - Warning About Missing ZIP")
    print("=" * 80)
    
    req = StressCheckRequest(
        monthly_income=5000.0,  # $60k annual
        other_debts_monthly=800.0,
        list_price=1200000.0,  # Very high price
        down_payment_pct=0.10,  # Low down payment
        zip_code=None,  # Missing ZIP!
        state="CA",
        hoa_monthly=500.0,
        risk_preference="neutral",
    )
    
    result = run_safety_upgrade_flow(req, max_candidates=5)
    
    print(f"\n📊 Baseline Results:")
    print(f"   Stress Band: {result.baseline_band}")
    print(f"   DTI: {result.baseline_dti:.1%}" if result.baseline_dti else "   DTI: N/A")
    print(f"   Total Payment: ${result.baseline_total_payment:,.2f}" if result.baseline_total_payment else "   Total Payment: N/A")
    print(f"   ZIP Code: {result.baseline_zip_code or 'N/A (MISSING)'}")
    print(f"   Is Tight or Worse: {result.baseline_is_tight_or_worse}")
    
    print(f"\n🔍 Safer Homes Search:")
    if result.safer_homes:
        print(f"   ZIP Searched: {result.safer_homes.zip_code}")
        print(f"   Candidates Found: {len(result.safer_homes.candidates)}")
    else:
        print(f"   ⏭️  No safer homes search performed (ZIP code missing)")
    
    print(f"\n💡 Primary Suggestion:")
    if result.primary_suggestion:
        print(f"   Reason: {result.primary_suggestion.reason}")
        print(f"   Title: {result.primary_suggestion.title}")
        print(f"   Details: {result.primary_suggestion.details}")
        if result.primary_suggestion.notes:
            print(f"   Notes:")
            for note in result.primary_suggestion.notes:
                print(f"      - {note}")
    else:
        print(f"   ⚠️  No primary suggestion")
    
    print(f"\n📋 Alternative Suggestions: {len(result.alternative_suggestions)}")
    for idx, alt in enumerate(result.alternative_suggestions, 1):
        print(f"   {idx}. {alt.title}")
    
    print("\n" + "=" * 80)
    return result


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    print("=" * 80)
    print("Safety Upgrade Flow Smoke Test")
    print("=" * 80)
    print("\nTesting run_safety_upgrade_flow() function directly (not HTTP)")
    print()
    
    try:
        # Run Scenario 1
        result1 = test_scenario_1_loose_ok()
        
        # Run Scenario 2
        result2 = test_scenario_2_tight_with_zip()
        
        # Run Scenario 3
        result3 = test_scenario_3_high_risk_no_zip()
        
        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        
        print(f"\nScenario 1 (Loose/OK):")
        print(f"   Baseline Band: {result1.baseline_band}")
        print(f"   Is Tight or Worse: {result1.baseline_is_tight_or_worse}")
        print(f"   Safer Homes Searched: {result1.safer_homes is not None}")
        print(f"   Primary Suggestion Reason: {result1.primary_suggestion.reason if result1.primary_suggestion else 'N/A'}")
        
        print(f"\nScenario 2 (Tight with ZIP):")
        print(f"   Baseline Band: {result2.baseline_band}")
        print(f"   Is Tight or Worse: {result2.baseline_is_tight_or_worse}")
        print(f"   Safer Homes Searched: {result2.safer_homes is not None}")
        if result2.safer_homes:
            print(f"   Candidates Found: {len(result2.safer_homes.candidates)}")
        print(f"   Primary Suggestion Reason: {result2.primary_suggestion.reason if result2.primary_suggestion else 'N/A'}")
        
        print(f"\nScenario 3 (High Risk, No ZIP):")
        print(f"   Baseline Band: {result3.baseline_band}")
        print(f"   Is Tight or Worse: {result3.baseline_is_tight_or_worse}")
        print(f"   ZIP Code: {result3.baseline_zip_code or 'MISSING'}")
        print(f"   Safer Homes Searched: {result3.safer_homes is not None}")
        print(f"   Primary Suggestion Reason: {result3.primary_suggestion.reason if result3.primary_suggestion else 'N/A'}")
        
        # Validation checks
        print(f"\n✅ Validation Checks:")
        
        # Check Scenario 1: should not search safer homes
        if not result1.baseline_is_tight_or_worse:
            print(f"   ✅ Scenario 1: Baseline is not tight/worse (correct)")
        else:
            print(f"   ⚠️  Scenario 1: Baseline is tight/worse (unexpected)")
        
        if result1.safer_homes is None:
            print(f"   ✅ Scenario 1: No safer homes search (correct)")
        else:
            print(f"   ⚠️  Scenario 1: Safer homes search performed (unexpected)")
        
        # Check Scenario 2: should search safer homes
        if result2.baseline_is_tight_or_worse:
            print(f"   ✅ Scenario 2: Baseline is tight/worse (correct)")
        else:
            print(f"   ⚠️  Scenario 2: Baseline is not tight/worse (unexpected)")
        
        if result2.safer_homes is not None:
            print(f"   ✅ Scenario 2: Safer homes search performed (correct)")
        else:
            print(f"   ⚠️  Scenario 2: No safer homes search (unexpected)")
        
        # Check Scenario 3: should not search (missing ZIP)
        if result3.baseline_is_tight_or_worse:
            print(f"   ✅ Scenario 3: Baseline is tight/worse (correct)")
        else:
            print(f"   ⚠️  Scenario 3: Baseline is not tight/worse (unexpected)")
        
        if result3.baseline_zip_code is None:
            print(f"   ✅ Scenario 3: ZIP code is missing (correct)")
        else:
            print(f"   ⚠️  Scenario 3: ZIP code is present (unexpected)")
        
        if result3.safer_homes is None:
            print(f"   ✅ Scenario 3: No safer homes search due to missing ZIP (correct)")
        else:
            print(f"   ⚠️  Scenario 3: Safer homes search performed despite missing ZIP (unexpected)")
        
        # Check all have primary suggestions
        all_have_suggestions = all(
            result.primary_suggestion is not None
            for result in [result1, result2, result3]
        )
        if all_have_suggestions:
            print(f"   ✅ All scenarios have primary suggestions")
        else:
            print(f"   ⚠️  Some scenarios missing primary suggestions")
        
        print("\n✅ Smoke test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

