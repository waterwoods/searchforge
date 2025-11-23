#!/usr/bin/env python3
"""
safer_homes_smoke.py - Safer Homes Search Smoke Test

Minimal smoke test for search_safer_homes_for_case() function.

Usage:
    python -m experiments.safer_homes_smoke
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import search_safer_homes_for_case, StressBand


# ============================================================================
# Test Scenarios
# ============================================================================

def test_scenario_1_socal_tight():
    """
    Scenario 1: SoCal tight case - income 6500, debts 500, zip 90803, target price 900000,
    baseline_band="tight", baseline_dti_ratio ~ 0.43.
    """
    print("=" * 80)
    print("Scenario 1: SoCal Tight Case")
    print("=" * 80)
    print("\nBaseline:")
    print(f"   Monthly Income: $6,500")
    print(f"   Monthly Debts: $500")
    print(f"   ZIP Code: 90803")
    print(f"   Target Price: $900,000")
    print(f"   Baseline Band: tight")
    print(f"   Baseline DTI: ~43%")
    
    result = search_safer_homes_for_case(
        monthly_income=6500.0,
        other_debts_monthly=500.0,
        zip_code="90803",
        target_list_price=900000.0,
        baseline_band="tight",
        baseline_dti_ratio=0.43,
        down_payment_pct=0.20,
        risk_preference="neutral",
        state="CA",
        max_candidates=5,
    )
    
    print(f"\n📊 Results:")
    print(f"   ZIP Code Searched: {result.zip_code}")
    print(f"   Baseline Band: {result.baseline_band}")
    print(f"   Baseline DTI: {result.baseline_dti_ratio:.1%}" if result.baseline_dti_ratio else "   Baseline DTI: N/A")
    print(f"   Number of Safer Candidates: {len(result.candidates)}")
    
    if result.candidates:
        print(f"\n🏠 Safer Home Candidates:")
        for idx, candidate in enumerate(result.candidates, 1):
            print(f"\n   {idx}. {candidate.listing.title}")
            print(f"      Location: {candidate.listing.city}, {candidate.listing.state} {candidate.listing.zip_code}")
            print(f"      Price: ${candidate.listing.list_price:,.0f}")
            if candidate.listing.beds and candidate.listing.baths:
                print(f"      Size: {candidate.listing.beds}BR/{candidate.listing.baths}BA")
            print(f"      Stress Band: {candidate.stress_band.upper()}")
            print(f"      DTI Ratio: {candidate.dti_ratio:.1%}" if candidate.dti_ratio else "      DTI Ratio: N/A")
            print(f"      Monthly Payment: ${candidate.total_monthly_payment:,.2f}" if candidate.total_monthly_payment else "      Monthly Payment: N/A")
            if candidate.comment:
                print(f"      💡 {candidate.comment}")
    else:
        print(f"\n   ⚠️  No safer candidates found")
    
    print("\n" + "=" * 80)
    return result


def test_scenario_2_high_risk():
    """
    Scenario 2: High-risk case - income 5000, debts 800, zip 78701, target 900000,
    baseline_band="high_risk".
    """
    print("=" * 80)
    print("Scenario 2: High-Risk Case")
    print("=" * 80)
    print("\nBaseline:")
    print(f"   Monthly Income: $5,000")
    print(f"   Monthly Debts: $800")
    print(f"   ZIP Code: 78701")
    print(f"   Target Price: $900,000")
    print(f"   Baseline Band: high_risk")
    
    result = search_safer_homes_for_case(
        monthly_income=5000.0,
        other_debts_monthly=800.0,
        zip_code="78701",
        target_list_price=900000.0,
        baseline_band="high_risk",
        baseline_dti_ratio=None,
        down_payment_pct=0.20,
        risk_preference="neutral",
        state="TX",
        max_candidates=5,
    )
    
    print(f"\n📊 Results:")
    print(f"   ZIP Code Searched: {result.zip_code}")
    print(f"   Baseline Band: {result.baseline_band}")
    print(f"   Baseline DTI: {result.baseline_dti_ratio:.1%}" if result.baseline_dti_ratio else "   Baseline DTI: N/A")
    print(f"   Number of Safer Candidates: {len(result.candidates)}")
    
    if result.candidates:
        print(f"\n🏠 Safer Home Candidates:")
        for idx, candidate in enumerate(result.candidates, 1):
            print(f"\n   {idx}. {candidate.listing.title}")
            print(f"      Location: {candidate.listing.city}, {candidate.listing.state} {candidate.listing.zip_code}")
            print(f"      Price: ${candidate.listing.list_price:,.0f}")
            if candidate.listing.beds and candidate.listing.baths:
                print(f"      Size: {candidate.listing.beds}BR/{candidate.listing.baths}BA")
            print(f"      Stress Band: {candidate.stress_band.upper()}")
            print(f"      DTI Ratio: {candidate.dti_ratio:.1%}" if candidate.dti_ratio else "      DTI Ratio: N/A")
            print(f"      Monthly Payment: ${candidate.total_monthly_payment:,.2f}" if candidate.total_monthly_payment else "      Monthly Payment: N/A")
            if candidate.comment:
                print(f"      💡 {candidate.comment}")
    else:
        print(f"\n   ⚠️  No safer candidates found")
    
    print("\n" + "=" * 80)
    return result


def test_scenario_3_no_baseline():
    """
    Scenario 3: Case without baseline band/DTI - just search for homes with DTI <= 38%.
    """
    print("=" * 80)
    print("Scenario 3: No Baseline Band/DTI Provided")
    print("=" * 80)
    print("\nBaseline:")
    print(f"   Monthly Income: $8,000")
    print(f"   Monthly Debts: $600")
    print(f"   ZIP Code: 90803")
    print(f"   Target Price: $750,000")
    print(f"   Baseline Band: N/A (will use default DTI <= 38%)")
    
    result = search_safer_homes_for_case(
        monthly_income=8000.0,
        other_debts_monthly=600.0,
        zip_code="90803",
        target_list_price=750000.0,
        baseline_band=None,
        baseline_dti_ratio=None,
        down_payment_pct=0.20,
        risk_preference="neutral",
        state="CA",
        max_candidates=5,
    )
    
    print(f"\n📊 Results:")
    print(f"   ZIP Code Searched: {result.zip_code}")
    print(f"   Baseline Band: {result.baseline_band or 'N/A'}")
    print(f"   Baseline DTI: {result.baseline_dti_ratio:.1%}" if result.baseline_dti_ratio else "   Baseline DTI: N/A")
    print(f"   Number of Safer Candidates: {len(result.candidates)}")
    
    if result.candidates:
        print(f"\n🏠 Safer Home Candidates (DTI <= 38%):")
        for idx, candidate in enumerate(result.candidates, 1):
            print(f"\n   {idx}. {candidate.listing.title}")
            print(f"      Location: {candidate.listing.city}, {candidate.listing.state} {candidate.listing.zip_code}")
            print(f"      Price: ${candidate.listing.list_price:,.0f}")
            if candidate.listing.beds and candidate.listing.baths:
                print(f"      Size: {candidate.listing.beds}BR/{candidate.listing.baths}BA")
            print(f"      Stress Band: {candidate.stress_band.upper()}")
            print(f"      DTI Ratio: {candidate.dti_ratio:.1%}" if candidate.dti_ratio else "      DTI Ratio: N/A")
            print(f"      Monthly Payment: ${candidate.total_monthly_payment:,.2f}" if candidate.total_monthly_payment else "      Monthly Payment: N/A")
            if candidate.comment:
                print(f"      💡 {candidate.comment}")
    else:
        print(f"\n   ⚠️  No safer candidates found")
    
    print("\n" + "=" * 80)
    return result


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    print("=" * 80)
    print("Safer Homes Search Smoke Test")
    print("=" * 80)
    print("\nTesting search_safer_homes_for_case() function directly (not HTTP)")
    print()
    
    try:
        # Run Scenario 1
        result1 = test_scenario_1_socal_tight()
        
        # Run Scenario 2
        result2 = test_scenario_2_high_risk()
        
        # Run Scenario 3
        result3 = test_scenario_3_no_baseline()
        
        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"\nScenario 1 (SoCal Tight):")
        print(f"   ZIP: {result1.zip_code}")
        print(f"   Baseline Band: {result1.baseline_band}")
        print(f"   Candidates Found: {len(result1.candidates)}")
        
        print(f"\nScenario 2 (High-Risk):")
        print(f"   ZIP: {result2.zip_code}")
        print(f"   Baseline Band: {result2.baseline_band}")
        print(f"   Candidates Found: {len(result2.candidates)}")
        
        print(f"\nScenario 3 (No Baseline):")
        print(f"   ZIP: {result3.zip_code}")
        print(f"   Baseline Band: {result3.baseline_band or 'N/A'}")
        print(f"   Candidates Found: {len(result3.candidates)}")
        
        # Validation checks
        print(f"\n✅ Validation Checks:")
        
        # Check that all candidates have required fields
        all_candidates_valid = True
        for result in [result1, result2, result3]:
            for candidate in result.candidates:
                if not candidate.listing:
                    print(f"   ❌ Candidate missing listing: {candidate}")
                    all_candidates_valid = False
                if candidate.stress_band not in ["loose", "ok", "tight", "high_risk"]:
                    print(f"   ❌ Invalid stress band: {candidate.stress_band}")
                    all_candidates_valid = False
                if candidate.dti_ratio and (candidate.dti_ratio < 0 or candidate.dti_ratio > 1):
                    print(f"   ❌ Invalid DTI ratio: {candidate.dti_ratio:.1%}")
                    all_candidates_valid = False
        
        if all_candidates_valid:
            print(f"   ✅ All candidates have valid required fields")
        
        # Check that candidates are actually safer (if we have baseline)
        for result in [result1, result2]:
            if result.baseline_band:
                band_order = {"loose": 0, "ok": 1, "tight": 2, "high_risk": 3}
                baseline_order = band_order.get(result.baseline_band, 999)
                for candidate in result.candidates:
                    candidate_order = band_order.get(candidate.stress_band, 999)
                    if candidate_order >= baseline_order:
                        print(f"   ⚠️  Candidate has same or worse band than baseline: {candidate.stress_band} vs {result.baseline_band}")
                    else:
                        print(f"   ✅ Candidate {candidate.listing.title} has better band: {candidate.stress_band} vs {result.baseline_band}")
        
        print("\n✅ Smoke test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

