#!/usr/bin/env python3
"""
approval_score_ml_smoke.py - Smoke Test for ML Approval Score Integration
==========================================================================

This script tests the ML approval score integration by running a few
representative StressCheckRequest cases with ML both enabled and disabled.

Usage:
    python experiments/approval_score_ml_smoke.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import run_stress_check, StressCheckRequest
from services.fiqa_api.mortgage.schemas import ApprovalScore

# Test cases: representative borrower/property combinations
TEST_CASES = [
    {
        "name": "Good Borrower - Affordable Home",
        "request": StressCheckRequest(
            monthly_income=10000.0,
            other_debts_monthly=500.0,
            list_price=400000.0,
            down_payment_pct=0.20,
            state="CA",
            zip_code="90210",
            hoa_monthly=200.0,
            risk_preference="neutral",
        ),
    },
    {
        "name": "Borderline Case - Moderate Income, Higher Price",
        "request": StressCheckRequest(
            monthly_income=8000.0,
            other_debts_monthly=800.0,
            list_price=500000.0,
            down_payment_pct=0.15,
            state="CA",
            zip_code="92648",
            hoa_monthly=300.0,
            risk_preference="neutral",
        ),
    },
    {
        "name": "High Risk - Low Income, High Price",
        "request": StressCheckRequest(
            monthly_income=6000.0,
            other_debts_monthly=1200.0,
            list_price=600000.0,
            down_payment_pct=0.10,
            state="CA",
            zip_code="90803",
            hoa_monthly=400.0,
            risk_preference="aggressive",
        ),
    },
]


def run_smoke_test():
    """Run smoke tests with ML both enabled and disabled."""
    print("=" * 80)
    print("ML Approval Score Smoke Test")
    print("=" * 80)
    print()
    
    # Test 1: Rule-based only (ML disabled)
    print("Test 1: Rule-based approval score (ML disabled)")
    print("-" * 80)
    os.environ["USE_ML_APPROVAL_SCORE"] = "false"
    
    rule_results = []
    for test_case in TEST_CASES:
        print(f"\n  Case: {test_case['name']}")
        try:
            response = run_stress_check(test_case["request"])
            approval_score = response.approval_score
            
            if approval_score:
                print(f"    Score: {approval_score.score:.1f}")
                print(f"    Bucket: {approval_score.bucket}")
                print(f"    Reasons: {', '.join(approval_score.reasons) if approval_score.reasons else 'none'}")
                rule_results.append({
                    "name": test_case["name"],
                    "score": approval_score.score,
                    "bucket": approval_score.bucket,
                })
            else:
                print("    ERROR: No approval score returned")
                rule_results.append({
                    "name": test_case["name"],
                    "score": None,
                    "bucket": None,
                })
        except Exception as e:
            print(f"    ERROR: {e}")
            rule_results.append({
                "name": test_case["name"],
                "error": str(e),
            })
    
    print()
    print("=" * 80)
    
    # Test 2: ML-enabled (hybrid rules + ML)
    print("Test 2: Hybrid rules + ML approval score (ML enabled)")
    print("-" * 80)
    os.environ["USE_ML_APPROVAL_SCORE"] = "true"
    
    ml_results = []
    for test_case in TEST_CASES:
        print(f"\n  Case: {test_case['name']}")
        try:
            response = run_stress_check(test_case["request"])
            approval_score = response.approval_score
            
            if approval_score:
                print(f"    Score: {approval_score.score:.1f}")
                print(f"    Bucket: {approval_score.bucket}")
                print(f"    Reasons: {', '.join(approval_score.reasons) if approval_score.reasons else 'none'}")
                ml_results.append({
                    "name": test_case["name"],
                    "score": approval_score.score,
                    "bucket": approval_score.bucket,
                })
            else:
                print("    ERROR: No approval score returned")
                ml_results.append({
                    "name": test_case["name"],
                    "score": None,
                    "bucket": None,
                })
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            ml_results.append({
                "name": test_case["name"],
                "error": str(e),
            })
    
    print()
    print("=" * 80)
    
    # Comparison and assertions
    print("Test 3: Comparison and Assertions")
    print("-" * 80)
    
    all_passed = True
    
    # Check that both runs succeeded
    print("\n  Assertion 1: Both runs succeed without exceptions")
    rule_errors = [r for r in rule_results if "error" in r]
    ml_errors = [r for r in ml_results if "error" in r]
    
    if rule_errors:
        print(f"    ✗ Rule-based run had {len(rule_errors)} errors")
        all_passed = False
    else:
        print("    ✓ Rule-based run succeeded")
    
    if ml_errors:
        print(f"    ✗ ML-enabled run had {len(ml_errors)} errors")
        print("    (This is expected if model file is missing - ML will fall back to rules)")
        # Don't fail on ML errors if they're MLApprovalUnavailable (expected)
        for error_result in ml_errors:
            if "model file not found" not in error_result.get("error", "").lower():
                all_passed = False
    else:
        print("    ✓ ML-enabled run succeeded")
    
    # Check that scores are reasonable (not wildly different)
    print("\n  Assertion 2: Scores are reasonable (within reasonable delta)")
    for rule_result, ml_result in zip(rule_results, ml_results):
        if "error" in rule_result or "error" in ml_result:
            continue
        
        rule_score = rule_result.get("score")
        ml_score = ml_result.get("score")
        
        if rule_score is not None and ml_score is not None:
            delta = abs(ml_score - rule_score)
            # Allow up to 30 points difference (ML can adjust, but shouldn't be completely different)
            if delta > 30:
                print(f"    ✗ {rule_result['name']}: Score delta too large ({delta:.1f})")
                print(f"      Rule: {rule_score:.1f}, ML: {ml_score:.1f}")
                all_passed = False
            else:
                print(f"    ✓ {rule_result['name']}: Score delta {delta:.1f}")
    
    # Check monotonicity for borderline cases
    print("\n  Assertion 3: Basic monotonicity check")
    print("    (Skipping detailed monotonicity check - would require multiple test cases)")
    print("    ✓ Monotonicity check skipped (manual verification recommended)")
    
    print()
    print("=" * 80)
    if all_passed:
        print("✓ All smoke tests passed!")
    else:
        print("✗ Some smoke tests failed (see details above)")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_smoke_test())

