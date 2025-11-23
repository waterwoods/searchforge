#!/usr/bin/env python3
"""
stress_check_regression.py - Stress Check Regression Test

Simple regression checks for run_stress_check and single-home-agent.

Goal:
- Make sure key scenarios map to expected stress_bands / warnings.
- Ensure single-home-agent remains consistent with raw run_stress_check.

Usage:
    cd /home/andy/searchforge
    python3 experiments/stress_check_regression.py
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import run_stress_check, StressCheckRequest
from services.fiqa_api.mortgage.schemas import StressCheckResponse, SingleHomeAgentRequest

# Try to import TestClient for HTTP testing (optional)
HTTP_TESTING_AVAILABLE = False
try:
    from fastapi.testclient import TestClient
    # Try to import app - this may fail due to initialization requirements
    try:
        from services.fiqa_api.app_main import app
        HTTP_TESTING_AVAILABLE = True
    except Exception as e:
        # App import may fail due to missing env vars or initialization
        # This is OK - HTTP testing is optional
        pass
except ImportError:
    pass


# ============================================================================
# Test Cases
# ============================================================================

TEST_CASES = [
    {
        "name": "loose_case",
        "request": {
            "monthly_income": 15000.0,  # $180k annual
            "other_debts_monthly": 200.0,
            "list_price": 450000.0,
            "down_payment_pct": 0.30,
            "hoa_monthly": 200.0,
            "state": "CA",
            "risk_preference": "conservative",
        },
        "expected": {
            "expected_band": ["loose", "ok"],  # Should be loose or ok
            "max_dti": 0.35,
            "require_warning": False,
        },
    },
    {
        "name": "ok_case",
        "request": {
            "monthly_income": 10000.0,  # $120k annual
            "other_debts_monthly": 500.0,
            "list_price": 500000.0,  # Reduced price to make it more affordable
            "down_payment_pct": 0.20,
            "hoa_monthly": 300.0,
            "state": "CA",
            "risk_preference": "neutral",
        },
        "expected": {
            "expected_band": ["ok", "loose", "tight"],  # Should be ok, loose, or tight
            "max_dti": 0.50,
            "require_warning": False,
        },
    },
    {
        "name": "tight_case",
        "request": {
            "monthly_income": 8000.0,  # $96k annual (slightly higher)
            "other_debts_monthly": 400.0,
            "list_price": 550000.0,  # Moderate price
            "down_payment_pct": 0.15,
            "hoa_monthly": 300.0,
            "state": "CA",
            "risk_preference": "neutral",
        },
        "expected": {
            "expected_band": ["tight", "ok", "high_risk"],  # Should be tight, ok, or high_risk
            "min_dti": 0.40,
            "max_dti": 0.75,
            "require_warning": False,
        },
    },
    {
        "name": "high_risk_case",
        "request": {
            "monthly_income": 5000.0,  # $60k annual
            "other_debts_monthly": 800.0,
            "list_price": 1200000.0,  # Very high price
            "down_payment_pct": 0.10,  # Low down payment
            "hoa_monthly": 500.0,
            "state": "CA",
            "risk_preference": "neutral",
        },
        "expected": {
            "expected_band": ["high_risk", "tight"],  # Should be high_risk (or tight if borderline)
            "min_dti": 0.60,
            "require_warning": True,  # high_risk should have warning
        },
    },
    {
        "name": "edge_low_income",
        "request": {
            "monthly_income": 5000.0,  # $60k annual (low but not too low)
            "other_debts_monthly": 200.0,
            "list_price": 280000.0,  # Lower price to make it affordable
            "down_payment_pct": 0.20,
            "hoa_monthly": 100.0,
            "state": "TX",
            "risk_preference": "conservative",
        },
        "expected": {
            "expected_band": ["ok", "tight", "high_risk"],  # Should be ok, tight, or high_risk
            "max_dti": 0.70,
            "require_warning": False,
        },
    },
    {
        "name": "edge_high_debt",
        "request": {
            "monthly_income": 12000.0,  # $144k annual (good income)
            "other_debts_monthly": 2000.0,  # High existing debt
            "list_price": 700000.0,  # Slightly lower price
            "down_payment_pct": 0.20,
            "hoa_monthly": 350.0,
            "state": "CA",
            "risk_preference": "aggressive",
        },
        "expected": {
            "expected_band": ["tight", "high_risk"],  # High debt pushes it to tight or high_risk
            "min_dti": 0.45,
            "max_dti": 0.75,
            "require_warning": False,
        },
    },
]


# ============================================================================
# Helper Functions
# ============================================================================

def run_case_via_function(case: Dict[str, Any]) -> StressCheckResponse:
    """
    Run a test case via direct function call to run_stress_check.
    
    Args:
        case: Test case dict with "request" key
        
    Returns:
        StressCheckResponse
    """
    request = StressCheckRequest(**case["request"])
    return run_stress_check(request)


def check_expectations(
    case: Dict[str, Any], response: StressCheckResponse
) -> List[str]:
    """
    Check if response matches expectations.
    
    Args:
        case: Test case dict with "expected" key
        response: StressCheckResponse from run_stress_check
        
    Returns:
        List of error messages (empty if all checks pass)
    """
    errors: List[str] = []
    expected = case["expected"]
    
    # Check stress band (supports both single value and list of acceptable values)
    expected_band = expected.get("expected_band")
    if expected_band:
        if isinstance(expected_band, list):
            # List of acceptable bands
            if response.stress_band not in expected_band:
                errors.append(
                    f"expected band in {expected_band}, got={response.stress_band}"
                )
        else:
            # Single expected band
            if response.stress_band != expected_band:
                errors.append(
                    f"expected band={expected_band}, got={response.stress_band}"
                )
    
    # Check DTI bounds
    if "max_dti" in expected:
        max_dti = expected["max_dti"]
        if response.dti_ratio > max_dti + 1e-3:
            errors.append(
                f"DTI {response.dti_ratio:.3f} exceeds max {max_dti:.3f}"
            )
    
    if "min_dti" in expected:
        min_dti = expected["min_dti"]
        if response.dti_ratio < min_dti - 1e-3:
            errors.append(
                f"DTI {response.dti_ratio:.3f} below min {min_dti:.3f}"
            )
    
    # Check warning requirement
    if expected.get("require_warning", False):
        if not response.hard_warning:
            errors.append("expected warning=True, got=None")
    else:
        # If require_warning is False, we don't fail if warning exists
        # (warnings can be present even if not required)
        pass
    
    return errors


def run_all_cases_via_function() -> Dict[str, Any]:
    """
    Run all test cases via direct function call.
    
    Returns:
        Dict with summary stats
    """
    print("=" * 80)
    print("Regression via run_stress_check()")
    print("=" * 80)
    print()
    
    results = []
    passed = 0
    failed = 0
    
    for case in TEST_CASES:
        case_name = case["name"]
        try:
            response = run_case_via_function(case)
            errors = check_expectations(case, response)
            
            if errors:
                status = "FAIL"
                error_msg = "; ".join(errors)
                failed += 1
            else:
                status = "OK"
                error_msg = ""
                passed += 1
            
            # Print result
            status_line = f"[FUNCTION] {case_name:20s} {status:4s}"
            if error_msg:
                status_line += f"  {error_msg}"
            else:
                status_line += f"  (band={response.stress_band}, DTI={response.dti_ratio:.3f})"
            print(status_line)
            
            results.append({
                "name": case_name,
                "status": status,
                "errors": errors,
                "response": response,
            })
            
        except Exception as e:
            print(f"[FUNCTION] {case_name:20s} ERROR  {str(e)}")
            failed += 1
            results.append({
                "name": case_name,
                "status": "ERROR",
                "errors": [str(e)],
                "response": None,
            })
    
    print()
    print(f"Summary: {passed} passed, {failed} failed out of {len(TEST_CASES)} cases")
    
    return {
        "passed": passed,
        "failed": failed,
        "total": len(TEST_CASES),
        "results": results,
    }


def run_case_via_single_home_agent(
    case: Dict[str, Any], client: Any
) -> Optional[Dict[str, Any]]:
    """
    Run a test case via HTTP call to /api/mortgage-agent/single-home-agent.
    
    Args:
        case: Test case dict with "request" key
        client: FastAPI TestClient instance
        
    Returns:
        Response dict or None if error
    """
    payload = {
        "stress_request": case["request"],
        "user_message": "Is this home affordable for me?",
    }
    
    try:
        response = client.post(
            "/api/mortgage-agent/single-home-agent",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  HTTP error: {e}")
        return None


def run_all_cases_via_single_home_agent() -> Dict[str, Any]:
    """
    Run all test cases via HTTP endpoint and compare with function results.
    
    Returns:
        Dict with summary stats
    """
    if not HTTP_TESTING_AVAILABLE:
        print("⚠️  Skipping HTTP tests (TestClient not available)")
        return {"passed": 0, "failed": 0, "total": 0, "results": []}
    
    print("=" * 80)
    print("Regression via /single-home-agent")
    print("=" * 80)
    print()
    
    client = TestClient(app)
    results = []
    passed = 0
    failed = 0
    
    for case in TEST_CASES:
        case_name = case["name"]
        try:
            # Get function result for comparison
            func_response = run_case_via_function(case)
            
            # Get HTTP result
            http_data = run_case_via_single_home_agent(case, client)
            
            if http_data is None:
                print(f"[AGENT] {case_name:20s} ERROR  HTTP call failed")
                failed += 1
                results.append({
                    "name": case_name,
                    "status": "ERROR",
                    "errors": ["HTTP call failed"],
                })
                continue
            
            # Extract stress_result from HTTP response
            stress_result = http_data.get("stress_result")
            if not stress_result:
                print(f"[AGENT] {case_name:20s} FAIL   Missing stress_result in response")
                failed += 1
                results.append({
                    "name": case_name,
                    "status": "FAIL",
                    "errors": ["Missing stress_result"],
                })
                continue
            
            # Compare band
            http_band = stress_result.get("stress_band")
            func_band = func_response.stress_band
            
            # Compare DTI
            http_dti = stress_result.get("dti_ratio")
            func_dti = func_response.dti_ratio
            
            errors = []
            
            if http_band != func_band:
                errors.append(f"band mismatch: HTTP={http_band}, func={func_band}")
            
            dti_diff = abs(http_dti - func_dti)
            if dti_diff > 1e-3:
                errors.append(
                    f"DTI diff={dti_diff:.6f} (HTTP={http_dti:.6f}, func={func_dti:.6f})"
                )
            
            if errors:
                status = "FAIL"
                error_msg = "; ".join(errors)
                failed += 1
            else:
                status = "OK"
                error_msg = ""
                passed += 1
            
            # Print result
            status_line = f"[AGENT] {case_name:20s} {status:4s}"
            if error_msg:
                status_line += f"  {error_msg}"
            else:
                status_line += f"  (band={http_band}, DTI diff={dti_diff:.6f})"
            print(status_line)
            
            results.append({
                "name": case_name,
                "status": status,
                "errors": errors,
            })
            
        except Exception as e:
            print(f"[AGENT] {case_name:20s} ERROR  {str(e)}")
            failed += 1
            results.append({
                "name": case_name,
                "status": "ERROR",
                "errors": [str(e)],
            })
    
    print()
    print(f"Summary: {passed} passed, {failed} failed out of {len(TEST_CASES)} cases")
    
    return {
        "passed": passed,
        "failed": failed,
        "total": len(TEST_CASES),
        "results": results,
    }


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    """Main entry point."""
    print("=" * 80)
    print("Stress Check Regression Test")
    print("=" * 80)
    print()
    
    # Run function-based tests
    func_summary = run_all_cases_via_function()
    print()
    
    # Run HTTP-based tests (if available)
    if HTTP_TESTING_AVAILABLE:
        agent_summary = run_all_cases_via_single_home_agent()
        print()
        
        # Overall summary
        print("=" * 80)
        print("Overall Summary")
        print("=" * 80)
        print(f"Function tests: {func_summary['passed']}/{func_summary['total']} passed")
        print(f"Agent tests: {agent_summary['passed']}/{agent_summary['total']} passed")
        
        total_passed = func_summary['passed'] + agent_summary['passed']
        total_failed = func_summary['failed'] + agent_summary['failed']
        total_cases = func_summary['total'] + agent_summary['total']
        
        print(f"\nTotal: {total_passed}/{total_cases} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("\n✅ All regression tests passed!")
            return 0
        else:
            print(f"\n❌ {total_failed} test(s) failed")
            return 1
    else:
        # Function tests only
        print("=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"Function tests: {func_summary['passed']}/{func_summary['total']} passed")
        
        if func_summary['failed'] == 0:
            print("\n✅ All regression tests passed!")
            return 0
        else:
            print(f"\n❌ {func_summary['failed']} test(s) failed")
            return 1


if __name__ == "__main__":
    sys.exit(main())

