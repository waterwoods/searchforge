#!/usr/bin/env python3
"""
safer_homes_api_smoke.py - Safer Homes API Smoke Test

Smoke test for POST /api/mortgage-agent/safer-homes endpoint via HTTP.

Usage:
    python -m experiments.safer_homes_api_smoke
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests


# ============================================================================
# Configuration
# ============================================================================

# Default API base URL (can be overridden via env or CLI)
API_BASE_URL = "http://localhost:8000"


# ============================================================================
# Test Scenarios
# ============================================================================

def test_scenario_1_socal_tight():
    """
    Scenario 1: SoCal tight case - income 6500, debts 500, zip 90803, price 900k.
    This should return 1-3 safer home candidates.
    """
    print("=" * 80)
    print("Scenario 1: SoCal Tight Case (via HTTP API)")
    print("=" * 80)
    print("\nRequest:")
    print(f"   Monthly Income: $6,500")
    print(f"   Monthly Debts: $500")
    print(f"   ZIP Code: 90803")
    print(f"   List Price: $900,000")
    print(f"   Down Payment: 20%")
    print(f"   State: CA")
    print(f"   HOA Monthly: $300")
    print(f"   Risk Preference: neutral")
    
    payload = {
        "monthly_income": 6500.0,
        "other_debts_monthly": 500.0,
        "list_price": 900000.0,
        "down_payment_pct": 0.20,
        "zip_code": "90803",
        "state": "CA",
        "hoa_monthly": 300.0,
        "risk_preference": "neutral",
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/mortgage-agent/safer-homes",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        
        if response.status_code != 200:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
        
        result = response.json()
        
        print(f"\n📊 Results:")
        print(f"   ZIP Code Searched: {result.get('zip_code', 'N/A')}")
        print(f"   Baseline Band: {result.get('baseline_band', 'N/A')}")
        baseline_dti = result.get('baseline_dti_ratio')
        if baseline_dti is not None:
            print(f"   Baseline DTI: {baseline_dti:.1%}")
        else:
            print(f"   Baseline DTI: N/A")
        print(f"   Number of Safer Candidates: {len(result.get('candidates', []))}")
        
        candidates = result.get('candidates', [])
        if candidates:
            print(f"\n🏠 Safer Home Candidates:")
            for idx, candidate in enumerate(candidates, 1):
                listing = candidate.get('listing', {})
                print(f"\n   {idx}. {listing.get('title', 'N/A')}")
                print(f"      Location: {listing.get('city', 'N/A')}, {listing.get('state', 'N/A')} {listing.get('zip_code', 'N/A')}")
                print(f"      Price: ${listing.get('list_price', 0):,.0f}")
                if listing.get('beds') and listing.get('baths'):
                    print(f"      Size: {listing.get('beds')}BR/{listing.get('baths')}BA")
                if listing.get('hoa_monthly'):
                    print(f"      HOA: ${listing.get('hoa_monthly', 0):,.2f}/mo")
                print(f"      Stress Band: {candidate.get('stress_band', 'N/A').upper()}")
                dti = candidate.get('dti_ratio')
                if dti is not None:
                    print(f"      DTI Ratio: {dti:.1%}")
                else:
                    print(f"      DTI Ratio: N/A")
                payment = candidate.get('total_monthly_payment')
                if payment is not None:
                    print(f"      Monthly Payment: ${payment:,.2f}")
                else:
                    print(f"      Monthly Payment: N/A")
                comment = candidate.get('comment')
                if comment:
                    print(f"      💡 {comment}")
        else:
            print(f"\n   ⚠️  No safer candidates found")
        
        print("\n" + "=" * 80)
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ HTTP request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_scenario_2_austin_ok():
    """
    Scenario 2: Austin OK case - income 8000, debts 400, zip 78701, price 600k.
    This should return some safer home candidates.
    """
    print("=" * 80)
    print("Scenario 2: Austin OK Case (via HTTP API)")
    print("=" * 80)
    print("\nRequest:")
    print(f"   Monthly Income: $8,000")
    print(f"   Monthly Debts: $400")
    print(f"   ZIP Code: 78701")
    print(f"   List Price: $600,000")
    print(f"   Down Payment: 20%")
    print(f"   State: TX")
    print(f"   HOA Monthly: $200")
    print(f"   Risk Preference: neutral")
    
    payload = {
        "monthly_income": 8000.0,
        "other_debts_monthly": 400.0,
        "list_price": 600000.0,
        "down_payment_pct": 0.20,
        "zip_code": "78701",
        "state": "TX",
        "hoa_monthly": 200.0,
        "risk_preference": "neutral",
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/mortgage-agent/safer-homes",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        
        if response.status_code != 200:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
        
        result = response.json()
        
        print(f"\n📊 Results:")
        print(f"   ZIP Code Searched: {result.get('zip_code', 'N/A')}")
        print(f"   Baseline Band: {result.get('baseline_band', 'N/A')}")
        baseline_dti = result.get('baseline_dti_ratio')
        if baseline_dti is not None:
            print(f"   Baseline DTI: {baseline_dti:.1%}")
        else:
            print(f"   Baseline DTI: N/A")
        print(f"   Number of Safer Candidates: {len(result.get('candidates', []))}")
        
        candidates = result.get('candidates', [])
        if candidates:
            print(f"\n🏠 Safer Home Candidates:")
            for idx, candidate in enumerate(candidates, 1):
                listing = candidate.get('listing', {})
                print(f"\n   {idx}. {listing.get('title', 'N/A')}")
                print(f"      Location: {listing.get('city', 'N/A')}, {listing.get('state', 'N/A')} {listing.get('zip_code', 'N/A')}")
                print(f"      Price: ${listing.get('list_price', 0):,.0f}")
                if listing.get('beds') and listing.get('baths'):
                    print(f"      Size: {listing.get('beds')}BR/{listing.get('baths')}BA")
                if listing.get('hoa_monthly'):
                    print(f"      HOA: ${listing.get('hoa_monthly', 0):,.2f}/mo")
                print(f"      Stress Band: {candidate.get('stress_band', 'N/A').upper()}")
                dti = candidate.get('dti_ratio')
                if dti is not None:
                    print(f"      DTI Ratio: {dti:.1%}")
                else:
                    print(f"      DTI Ratio: N/A")
                payment = candidate.get('total_monthly_payment')
                if payment is not None:
                    print(f"      Monthly Payment: ${payment:,.2f}")
                else:
                    print(f"      Monthly Payment: N/A")
                comment = candidate.get('comment')
                if comment:
                    print(f"      💡 {comment}")
        else:
            print(f"\n   ⚠️  No safer candidates found")
        
        print("\n" + "=" * 80)
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ HTTP request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    print("=" * 80)
    print("Safer Homes API Smoke Test")
    print("=" * 80)
    print(f"\nTesting POST /api/mortgage-agent/safer-homes via HTTP")
    print(f"API Base URL: {API_BASE_URL}")
    print()
    
    # Check if API is reachable
    try:
        health_check = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_check.status_code == 200:
            print("✅ API is reachable")
        else:
            print(f"⚠️  API health check returned status {health_check.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Could not reach API at {API_BASE_URL}: {e}")
        print("   Continuing anyway...")
    print()
    
    try:
        # Run Scenario 1
        result1 = test_scenario_1_socal_tight()
        
        # Run Scenario 2
        result2 = test_scenario_2_austin_ok()
        
        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        
        if result1:
            print(f"\nScenario 1 (SoCal Tight):")
            print(f"   ZIP: {result1.get('zip_code', 'N/A')}")
            print(f"   Baseline Band: {result1.get('baseline_band', 'N/A')}")
            print(f"   Candidates Found: {len(result1.get('candidates', []))}")
        else:
            print(f"\nScenario 1 (SoCal Tight): ❌ FAILED")
        
        if result2:
            print(f"\nScenario 2 (Austin OK):")
            print(f"   ZIP: {result2.get('zip_code', 'N/A')}")
            print(f"   Baseline Band: {result2.get('baseline_band', 'N/A')}")
            print(f"   Candidates Found: {len(result2.get('candidates', []))}")
        else:
            print(f"\nScenario 2 (Austin OK): ❌ FAILED")
        
        # Validation checks
        print(f"\n✅ Validation Checks:")
        
        all_valid = True
        for idx, result in enumerate([result1, result2], 1):
            if not result:
                all_valid = False
                continue
            
            # Check response structure
            if 'zip_code' not in result:
                print(f"   ❌ Scenario {idx}: Missing 'zip_code' field")
                all_valid = False
            if 'candidates' not in result:
                print(f"   ❌ Scenario {idx}: Missing 'candidates' field")
                all_valid = False
            else:
                candidates = result.get('candidates', [])
                for candidate in candidates:
                    if 'listing' not in candidate:
                        print(f"   ❌ Scenario {idx}: Candidate missing 'listing' field")
                        all_valid = False
                    if 'stress_band' not in candidate:
                        print(f"   ❌ Scenario {idx}: Candidate missing 'stress_band' field")
                        all_valid = False
                    else:
                        stress_band = candidate.get('stress_band')
                        if stress_band not in ['loose', 'ok', 'tight', 'high_risk']:
                            print(f"   ❌ Scenario {idx}: Invalid stress_band: {stress_band}")
                            all_valid = False
        
        if all_valid:
            print(f"   ✅ All responses have valid structure")
        
        # Check that we got at least some candidates in at least one scenario
        candidates_found = False
        for result in [result1, result2]:
            if result and len(result.get('candidates', [])) > 0:
                candidates_found = True
                break
        
        if candidates_found:
            print(f"   ✅ At least one scenario returned safer home candidates")
        else:
            print(f"   ⚠️  No scenarios returned safer home candidates (this may be expected if no safer homes exist)")
        
        if result1 or result2:
            print("\n✅ API smoke test completed!")
            return 0
        else:
            print("\n❌ API smoke test FAILED: All scenarios failed")
            return 1
        
    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

