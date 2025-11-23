#!/usr/bin/env python3
"""
single_home_agent_cloud_e2e.py - Cloud Run E2E Test for Single Home Agent

This script is intended for Cloud Run pre-demo checks and does not run by default in CI.
It tests the full cloud deployment by hitting the Cloud Run URL directly.

Usage:
    python experiments/single_home_agent_cloud_e2e.py \
        --base-url https://mortgage-agent-api-XXXX.us-west1.run.app \
        --verbose
"""

import argparse
import json
import sys
import time
from typing import Dict, Any, Optional

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library not found. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# Test Scenarios
# ============================================================================

SCENARIOS = {
    "socal_tight": {
        "name": "SoCal High Price, Feels Tight",
        "payload": {
            "stress_request": {
                "monthly_income": 12000,
                "other_debts_monthly": 500,
                "list_price": 950000,
                "down_payment_pct": 0.20,
                "state": "CA",
                "zip_code": "90803",
                "hoa_monthly": 350,
                "risk_preference": "neutral",
            },
            "user_message": "Is this home too tight for my budget?",
        },
        "expected": {
            "stress_band": "tight",  # or "high_risk"
            "hard_block": True,
            "has_safety_upgrade": True,
            "has_strategy_lab": True,
        },
    },
    "texas_loose": {
        "name": "Texas Starter Home, Comfortable",
        "payload": {
            "stress_request": {
                "monthly_income": 8000,
                "other_debts_monthly": 300,
                "list_price": 250000,
                "down_payment_pct": 0.20,
                "state": "TX",
                "zip_code": "75001",
                "hoa_monthly": 0,
                "risk_preference": "neutral",
            },
            "user_message": "Can I afford this home?",
        },
        "expected": {
            "stress_band": "loose",  # or "ok"
            "hard_block": False,
            "has_safety_upgrade": False,  # May be skipped for loose scenarios
            "has_strategy_lab": True,
        },
    },
    "extreme_high_risk": {
        "name": "Extreme High Risk, Hard Block",
        "payload": {
            "stress_request": {
                "monthly_income": 6000,
                "other_debts_monthly": 800,
                "list_price": 800000,
                "down_payment_pct": 0.10,
                "state": "CA",
                "zip_code": "90210",
                "hoa_monthly": 500,
                "risk_preference": "neutral",
            },
            "user_message": "What's my risk level?",
        },
        "expected": {
            "stress_band": "high_risk",
            "hard_block": True,
            "has_safety_upgrade": True,
            "has_strategy_lab": True,
        },
    },
}


# ============================================================================
# Helper Functions
# ============================================================================

def call_api(base_url: str, payload: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Call /api/mortgage-agent/single-home-agent API.
    
    Args:
        base_url: API base URL (e.g., https://mortgage-agent-api-XXXX.us-west1.run.app)
        payload: Request payload
        verbose: If True, print request details
        
    Returns:
        dict: API response
    """
    url = f"{base_url}/api/mortgage-agent/single-home-agent"
    
    if verbose:
        print(f"  📤 POST {url}")
        print(f"  📝 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.perf_counter()
        response = requests.post(url, json=payload, timeout=60.0)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        response.raise_for_status()
        data = response.json()
        
        # Add measured latency
        data["_measured_latency_ms"] = elapsed_ms
        
        if verbose:
            print(f"  ✅ Response: {response.status_code} ({elapsed_ms:.1f}ms)")
        
        return data
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"  ❌ API call failed: {e}", file=sys.stderr)
        raise


def validate_response(
    data: Dict[str, Any],
    scenario_name: str,
    expected: Dict[str, Any],
    verbose: bool = False,
) -> tuple[bool, list[str]]:
    """
    Validate API response against expected values.
    
    Args:
        data: API response dictionary
        scenario_name: Scenario name for logging
        expected: Expected values dictionary
        verbose: If True, print validation details
        
    Returns:
        (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Check HTTP status (should be 200, but we already checked in call_api)
    stress_result = data.get("stress_result", {})
    if not stress_result:
        errors.append("Missing 'stress_result' in response")
        return False, errors
    
    # Check stress_band
    stress_band = stress_result.get("stress_band")
    expected_band = expected.get("stress_band")
    if stress_band != expected_band:
        # Allow some flexibility: "tight" or "high_risk" both acceptable for high-risk scenarios
        if expected_band == "tight" and stress_band == "high_risk":
            if verbose:
                print(f"  ⚠️  stress_band is '{stress_band}' (expected '{expected_band}', but acceptable)")
        elif expected_band == "loose" and stress_band == "ok":
            if verbose:
                print(f"  ⚠️  stress_band is '{stress_band}' (expected '{expected_band}', but acceptable)")
        else:
            errors.append(f"stress_band mismatch: got '{stress_band}', expected '{expected_band}'")
    
    # Check hard_block
    risk_assessment = stress_result.get("risk_assessment", {})
    hard_block = risk_assessment.get("hard_block", False)
    expected_hard_block = expected.get("hard_block", False)
    if hard_block != expected_hard_block:
        errors.append(f"hard_block mismatch: got {hard_block}, expected {expected_hard_block}")
    
    # Check safety_upgrade presence
    has_safety_upgrade = data.get("safety_upgrade") is not None
    expected_has_safety_upgrade = expected.get("has_safety_upgrade", False)
    if has_safety_upgrade != expected_has_safety_upgrade:
        # For tight/high_risk scenarios, safety_upgrade should be present
        if expected_has_safety_upgrade and not has_safety_upgrade:
            errors.append("Expected safety_upgrade to be present but it's None")
        # For loose scenarios, it's OK if safety_upgrade is skipped
        elif not expected_has_safety_upgrade and has_safety_upgrade:
            if verbose:
                print(f"  ℹ️  safety_upgrade present (not required for this scenario, but OK)")
    
    # Check strategy_lab presence
    has_strategy_lab = data.get("strategy_lab") is not None
    expected_has_strategy_lab = expected.get("has_strategy_lab", True)
    if has_strategy_lab != expected_has_strategy_lab:
        if expected_has_strategy_lab and not has_strategy_lab:
            errors.append("Expected strategy_lab to be present but it's None")
        elif not expected_has_strategy_lab and has_strategy_lab:
            if verbose:
                print(f"  ℹ️  strategy_lab present (not required for this scenario, but OK)")
    
    return len(errors) == 0, errors


def run_scenario(
    scenario_id: str,
    scenario: Dict[str, Any],
    base_url: str,
    verbose: bool = False,
) -> bool:
    """
    Run a single scenario and validate the response.
    
    Args:
        scenario_id: Scenario identifier
        scenario: Scenario dictionary with name, payload, expected
        base_url: API base URL
        verbose: If True, print detailed output
        
    Returns:
        True if scenario passed, False otherwise
    """
    print(f"\n{'=' * 80}")
    print(f"[Scenario] {scenario['name']} ({scenario_id})")
    print(f"{'=' * 80}")
    
    if verbose:
        print(f"Expected:")
        for key, value in scenario["expected"].items():
            print(f"  - {key}: {value}")
        print()
    
    try:
        # Call API
        data = call_api(base_url, scenario["payload"], verbose=verbose)
        
        # Validate response
        is_valid, errors = validate_response(
            data, scenario_id, scenario["expected"], verbose=verbose
        )
        
        # Print results
        stress_result = data.get("stress_result", {})
        stress_band = stress_result.get("stress_band", "N/A")
        risk_assessment = stress_result.get("risk_assessment", {})
        hard_block = risk_assessment.get("hard_block", False)
        latency_ms = data.get("_measured_latency_ms", 0)
        
        print(f"  📊 Stress Band: {stress_band}")
        print(f"  🚫 Hard Block: {hard_block}")
        print(f"  ⏱️  Latency: {latency_ms:.1f}ms")
        
        if is_valid:
            print(f"  ✅ PASS")
            return True
        else:
            print(f"  ❌ FAIL")
            for error in errors:
                print(f"     - {error}")
            return False
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cloud Run E2E test for Single Home Agent API"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        required=True,
        help="Cloud Run base URL (e.g., https://mortgage-agent-api-XXXX.us-west1.run.app)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Run specific scenario only (socal_tight, texas_loose, extreme_high_risk)",
    )
    
    args = parser.parse_args()
    
    # Normalize base URL (remove trailing slash)
    base_url = args.base_url.rstrip("/")
    
    # Test health endpoint first
    print("=" * 80)
    print("Testing Health Endpoint")
    print("=" * 80)
    try:
        health_url = f"{base_url}/healthz"
        response = requests.get(health_url, timeout=10.0)
        response.raise_for_status()
        health_data = response.json()
        print(f"✅ Health check passed: {health_data.get('status', 'unknown')}")
        if args.verbose:
            print(f"   Service: {health_data.get('service', 'N/A')}")
            print(f"   Version: {health_data.get('version', 'N/A')}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("   Continuing with scenario tests anyway...")
    
    # Run scenarios
    scenarios_to_run = {}
    if args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"❌ Unknown scenario: {args.scenario}", file=sys.stderr)
            print(f"   Available scenarios: {', '.join(SCENARIOS.keys())}", file=sys.stderr)
            sys.exit(1)
        scenarios_to_run[args.scenario] = SCENARIOS[args.scenario]
    else:
        scenarios_to_run = SCENARIOS
    
    results = {}
    for scenario_id, scenario in scenarios_to_run.items():
        passed = run_scenario(scenario_id, scenario, base_url, verbose=args.verbose)
        results[scenario_id] = passed
    
    # Summary
    print(f"\n{'=' * 80}")
    print("Summary")
    print(f"{'=' * 80}")
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    
    for scenario_id, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {scenario_id}")
    
    print(f"\nTotal: {passed_count}/{total_count} scenarios passed")
    
    # Exit code
    if passed_count == total_count:
        print("\n✅ All scenarios passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total_count - passed_count} scenario(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

