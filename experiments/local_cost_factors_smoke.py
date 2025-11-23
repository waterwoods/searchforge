#!/usr/bin/env python3
"""
local_cost_factors_smoke.py - Local Cost Factors Smoke Test

Simple smoke test for the local_cost_factors tool and its integration with run_stress_check.

Goal:
- Confirm get_local_cost_factors can distinguish zip_override / state_default / global_default
- Confirm run_stress_check's Market Data Fetch step includes new fields (zip_code, state, local_cost_factors_source)

Usage:
    cd /home/andy/searchforge
    python3 experiments/local_cost_factors_smoke.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import run_stress_check, StressCheckRequest
from services.fiqa_api.mortgage.local_cost_factors import get_local_cost_factors


def main() -> None:
    """Run smoke tests for local cost factors."""
    print("=" * 80)
    print("Local Cost Factors Smoke Test")
    print("=" * 80)
    print()
    
    # Test 1: Print local cost factors for various ZIP codes
    print("Test 1: Testing get_local_cost_factors() with various inputs")
    print("-" * 80)
    
    test_cases = [
        ("90803", "CA", "zip_override"),  # Should use zip_override
        ("92648", "CA", "zip_override"),  # Should use zip_override
        ("73301", "TX", "zip_override"),  # Should use zip_override
        ("78701", "TX", "zip_override"),  # Should use zip_override
        ("90210", "CA", "state_default"),  # Should use state_default (CA)
        ("75001", "TX", "state_default"),  # Should use state_default (TX)
        ("00000", None, "global_default"),  # Should use global_default
        ("12345", "NY", "state_default"),  # Should use state_default (NY)
    ]
    
    for zip_code, state, expected_source in test_cases:
        factors = get_local_cost_factors(zip_code=zip_code, state=state)
        status = "✓" if factors.source == expected_source else "✗"
        print(
            f"{status} ZIP={zip_code:6s} State={str(state):4s} "
            f"Tax={factors.tax_rate_est:.4f} ({factors.tax_rate_est*100:.2f}%) "
            f"Insurance={factors.insurance_ratio_est:.4f} ({factors.insurance_ratio_est*100:.2f}%) "
            f"Source={factors.source:15s} (expected: {expected_source})"
        )
        if factors.source != expected_source:
            print(f"  ⚠️  WARNING: Expected source {expected_source}, got {factors.source}")
    
    print()
    
    # Test 2: Run stress check with SoCal ZIP (90803) and verify values
    print("Test 2: Running stress_check with ZIP 90803 (SoCal)")
    print("-" * 80)
    
    req = StressCheckRequest(
        monthly_income=12000.0,  # $144k annual
        other_debts_monthly=500.0,
        list_price=750000.0,
        down_payment_pct=0.20,
        zip_code="90803",
        state="CA",
        hoa_monthly=350.0,
        risk_preference="neutral",
    )
    
    resp = run_stress_check(req)
    
    print(f"Stress Band: {resp.stress_band}")
    print(f"DTI Ratio: {resp.dti_ratio:.4f}")
    print(f"Assumed Tax Rate: {resp.assumed_tax_rate_pct:.2f}%")
    print(f"Assumed Insurance Ratio: {resp.assumed_insurance_ratio_pct:.2f}%")
    print()
    
    # Verify tax/insurance values match ZIP override
    expected_tax_rate_pct = 0.011 * 100.0  # 1.1% from LOCAL_COST_FACTORS_BY_ZIP["90803"]
    expected_insurance_pct = 0.0028 * 100.0  # 0.28% from LOCAL_COST_FACTORS_BY_ZIP["90803"]
    
    tax_match = abs(resp.assumed_tax_rate_pct - expected_tax_rate_pct) < 0.01
    insurance_match = abs(resp.assumed_insurance_ratio_pct - expected_insurance_pct) < 0.01
    
    print(f"Tax rate check: {resp.assumed_tax_rate_pct:.2f}% (expected ~{expected_tax_rate_pct:.2f}%) {'✓' if tax_match else '✗'}")
    print(f"Insurance check: {resp.assumed_insurance_ratio_pct:.2f}% (expected ~{expected_insurance_pct:.2f}%) {'✓' if insurance_match else '✗'}")
    print()
    
    # Test 3: Check Market Data Fetch step for new fields
    print("Test 3: Checking Market Data Fetch step for new fields")
    print("-" * 80)
    
    market_data_steps = [
        s for s in resp.agent_steps if s.step_name == "Market Data Fetch"
    ]
    
    if not market_data_steps:
        print("✗ ERROR: No 'Market Data Fetch' step found in agent_steps")
        return
    
    step = market_data_steps[0]
    print(f"Step ID: {step.step_id}")
    print(f"Step Name: {step.step_name}")
    print(f"Status: {step.status}")
    print()
    
    # Check inputs
    print("Inputs:")
    if step.inputs:
        for key in ["state", "zip_code", "loan_type"]:
            value = step.inputs.get(key)
            status = "✓" if value is not None else "✗"
            print(f"  {status} {key}: {value}")
    else:
        print("  ✗ No inputs found")
    print()
    
    # Check outputs
    print("Outputs:")
    required_outputs = [
        "assumed_interest_rate_pct",
        "assumed_tax_rate_pct",
        "assumed_insurance_ratio_pct",
        "local_cost_factors_source",
    ]
    
    if step.outputs:
        for key in required_outputs:
            value = step.outputs.get(key)
            status = "✓" if value is not None else "✗"
            print(f"  {status} {key}: {value}")
        
        # Verify source is zip_override for 90803
        source = step.outputs.get("local_cost_factors_source")
        if source == "zip_override":
            print(f"  ✓ Source is 'zip_override' as expected for ZIP 90803")
        else:
            print(f"  ⚠️  WARNING: Expected source 'zip_override', got '{source}'")
    else:
        print("  ✗ No outputs found")
    print()
    
    # Test 4: Test with state-only (no ZIP override)
    print("Test 4: Running stress_check with state-only (TX, no ZIP override)")
    print("-" * 80)
    
    req2 = StressCheckRequest(
        monthly_income=10000.0,
        other_debts_monthly=400.0,
        list_price=500000.0,
        down_payment_pct=0.20,
        zip_code="75001",  # Not in LOCAL_COST_FACTORS_BY_ZIP
        state="TX",
        hoa_monthly=0.0,
        risk_preference="neutral",
    )
    
    resp2 = run_stress_check(req2)
    
    market_data_steps2 = [
        s for s in resp2.agent_steps if s.step_name == "Market Data Fetch"
    ]
    
    if market_data_steps2:
        step2 = market_data_steps2[0]
        source2 = step2.outputs.get("local_cost_factors_source") if step2.outputs else None
        print(f"Source: {source2}")
        if source2 == "state_default":
            print("  ✓ Source is 'state_default' as expected for state-only lookup")
        else:
            print(f"  ⚠️  WARNING: Expected source 'state_default', got '{source2}'")
        print(f"Tax Rate: {resp2.assumed_tax_rate_pct:.2f}%")
        print(f"Insurance Ratio: {resp2.assumed_insurance_ratio_pct:.2f}%")
    
    print()
    print("=" * 80)
    print("Smoke test completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

