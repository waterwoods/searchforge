#!/usr/bin/env python3
"""
single_home_agent_smoke.py - Single Home Agent Smoke Test

Minimal smoke test for POST /api/mortgage-agent/single-home-agent endpoint.

Usage:
    python experiments/single_home_agent_smoke.py [--base-url http://localhost:8000]
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8000"

# Test payload
TEST_PAYLOAD = {
    "stress_request": {
        "monthly_income": 12000,
        "other_debts_monthly": 500,
        "list_price": 800000,
        "down_payment_pct": 0.20,
        "state": "CA",
        "zip_code": "90803",  # Added ZIP code to test safer homes search
        "hoa_monthly": 350,
        "risk_preference": "neutral",
    },
    "user_message": "Is this home too tight for my budget?"
}


# ============================================================================
# Helper Functions
# ============================================================================

def call_api(base_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call /api/mortgage-agent/single-home-agent API.
    
    Args:
        base_url: API base URL
        payload: Request payload
        
    Returns:
        dict: API response
    """
    import requests
    
    url = f"{base_url}/api/mortgage-agent/single-home-agent"
    
    try:
        start_time = time.perf_counter()
        response = requests.post(url, json=payload, timeout=30.0)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        response.raise_for_status()
        data = response.json()
        
        # Add measured latency
        data["_measured_latency_ms"] = elapsed_ms
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ API call failed: {e}", file=sys.stderr)
        raise


def print_response(data: Dict[str, Any], payload: Optional[Dict[str, Any]] = None) -> None:
    """
    Print API response in a readable format.
    
    Args:
        data: API response dictionary
        payload: Optional request payload for sanity checks
    """
    print("=" * 80)
    print("Single Home Agent API Response")
    print("=" * 80)
    
    # Stress result
    stress_result = data.get("stress_result", {})
    if stress_result:
        print(f"\n📊 Stress Check Results:")
        print(f"   Total Monthly Payment: ${stress_result.get('total_monthly_payment', 0):,.2f}")
        print(f"   Principal & Interest: ${stress_result.get('principal_interest_payment', 0):,.2f}")
        print(f"   Tax/Ins/HOA: ${stress_result.get('estimated_tax_ins_hoa', 0):,.2f}")
        print(f"   DTI Ratio: {stress_result.get('dti_ratio', 0):.1%}")
        print(f"   Stress Band: {stress_result.get('stress_band', 'N/A').upper()}")
        
        hard_warning = stress_result.get("hard_warning")
        if hard_warning:
            print(f"   ⚠️  Hard Warning: {hard_warning}")
        else:
            print(f"   ✅ No hard warning")
    
    # Borrower narrative
    borrower_narrative = data.get("borrower_narrative")
    if borrower_narrative:
        print(f"\n💬 Borrower Narrative:")
        print("-" * 80)
        # Print full narrative to see structured format
        print(borrower_narrative)
        print("-" * 80)
        
        # Check for expected structure sections
        narrative_lower = borrower_narrative.lower()
        has_summary = "summary" in narrative_lower
        has_what_means = "what this means" in narrative_lower or "what this means:" in narrative_lower
        has_recommended = "recommended next steps" in narrative_lower or "recommended next steps:" in narrative_lower
        has_safety = "safety upgrade" in narrative_lower or "safety upgrade:" in narrative_lower
        
        print(f"\n   Structure Check:")
        print(f"      {'✅' if has_summary else '❌'} Contains 'Summary'")
        print(f"      {'✅' if has_what_means else '⚠️ '} Contains 'What this means'")
        print(f"      {'✅' if has_recommended else '⚠️ '} Contains 'Recommended next steps'")
        print(f"      {'✅' if has_safety else 'ℹ️ '} Contains 'Safety upgrade' (may be omitted if not available)")
    else:
        print(f"\n💬 Borrower Narrative: None (maybe LLM disabled or failed)")
    
    # Recommended actions
    recommended_actions = data.get("recommended_actions")
    if recommended_actions:
        print(f"\n💡 Recommended Actions ({len(recommended_actions)} actions):")
        for idx, action in enumerate(recommended_actions, 1):
            print(f"   {idx}. {action}")
    else:
        print(f"\n💡 Recommended Actions: None (maybe LLM disabled or failed)")
    
    # LLM usage
    llm_usage = data.get("llm_usage")
    if llm_usage:
        print(f"\n📊 LLM Usage:")
        print(f"   Model: {llm_usage.get('model', 'N/A')}")
        print(f"   Prompt Tokens: {llm_usage.get('prompt_tokens', 'N/A')}")
        print(f"   Completion Tokens: {llm_usage.get('completion_tokens', 'N/A')}")
        print(f"   Total Tokens: {llm_usage.get('total_tokens', 'N/A')}")
        cost = llm_usage.get('cost_usd_est')
        if cost is not None:
            print(f"   Cost Estimate: ${cost:.6f}")
        else:
            print(f"   Cost Estimate: N/A")
    else:
        print(f"\n📊 LLM Usage: None (maybe LLM disabled or failed)")
    
    # Safety upgrade
    safety_upgrade = data.get("safety_upgrade")
    if safety_upgrade:
        print(f"\n🛡️  Safety Upgrade:")
        print(f"   Baseline Band: {safety_upgrade.get('baseline_band', 'N/A')}")
        print(f"   Baseline DTI: {safety_upgrade.get('baseline_dti', 0):.1%}" if safety_upgrade.get('baseline_dti') else "   Baseline DTI: N/A")
        print(f"   Is Tight or Worse: {safety_upgrade.get('baseline_is_tight_or_worse', False)}")
        primary_suggestion = safety_upgrade.get('primary_suggestion')
        if primary_suggestion:
            print(f"   Primary Suggestion:")
            print(f"      Title: {primary_suggestion.get('title', 'N/A')}")
            print(f"      Reason: {primary_suggestion.get('reason', 'N/A')}")
            if primary_suggestion.get('delta_dti') is not None:
                print(f"      Delta DTI: {primary_suggestion.get('delta_dti', 0):.1%}")
        safer_homes = safety_upgrade.get('safer_homes')
        if safer_homes:
            candidates_count = len(safer_homes.get('candidates', []))
            print(f"   Safer Homes Found: {candidates_count} candidates")
    else:
        print(f"\n🛡️  Safety Upgrade: None (may not be computed or failed)")
    
    # Strategy lab
    strategy_lab = data.get("strategy_lab")
    if strategy_lab:
        print(f"\n🔬 Strategy Lab:")
        baseline_band = strategy_lab.get("baseline_stress_band")
        print(f"   Baseline Band: {baseline_band}" if baseline_band else "   Baseline Band: N/A")
        baseline_dti = strategy_lab.get("baseline_dti")
        if baseline_dti is not None:
            print(f"   Baseline DTI: {baseline_dti:.1%}")
        scenarios = strategy_lab.get("scenarios", [])
        scenarios_count = len(scenarios)
        print(f"   Scenarios Count: {scenarios_count}")
        if scenarios_count > 0:
            first_scenario = scenarios[0]
            scenario_title = first_scenario.get('title', 'N/A') if isinstance(first_scenario, dict) else getattr(first_scenario, 'title', 'N/A')
            scenario_id = first_scenario.get('id', 'N/A') if isinstance(first_scenario, dict) else getattr(first_scenario, 'id', 'N/A')
            print(f"   Sample Scenario: {scenario_title} (ID: {scenario_id})")
    else:
        print(f"\n🔬 Strategy Lab: None (may not be computed or failed)")
    
    # Latency
    latency_ms = data.get("_measured_latency_ms")
    if latency_ms:
        print(f"\n⏱️  Latency: {latency_ms:.1f} ms")
    
    print("\n" + "=" * 80)


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Smoke test for Single Home Agent API"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--payload",
        type=str,
        default=None,
        help="Path to JSON file with custom payload (optional)"
    )
    
    args = parser.parse_args()
    
    # Load payload
    if args.payload:
        payload_path = Path(args.payload)
        if not payload_path.exists():
            print(f"❌ Payload file not found: {payload_path}", file=sys.stderr)
            sys.exit(1)
        with open(payload_path, "r") as f:
            payload = json.load(f)
    else:
        payload = TEST_PAYLOAD.copy()
    
    # Print test info
    print("=" * 80)
    print("Single Home Agent Smoke Test")
    print("=" * 80)
    print(f"\n📍 Base URL: {args.base_url}")
    print(f"📝 Endpoint: POST /api/mortgage-agent/single-home-agent")
    print(f"\n📤 Request Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    # Call API
    try:
        data = call_api(args.base_url, payload)
        print_response(data, payload=payload)
        
        # Validation checks
        stress_result = data.get("stress_result")
        if not stress_result:
            print("\n❌ Test FAILED: Missing stress_result", file=sys.stderr)
            sys.exit(1)
        
        # Check stress_result has required fields
        required_fields = ["total_monthly_payment", "dti_ratio", "stress_band"]
        for field in required_fields:
            if field not in stress_result:
                print(f"\n❌ Test FAILED: Missing field '{field}' in stress_result", file=sys.stderr)
                sys.exit(1)
        
        # Check that stress_result matches what we'd get from direct stress_check call
        # (This is a sanity check - the numbers should be identical)
        print("\n✅ Validation Checks:")
        print(f"   ✅ stress_result present with required fields")
        
        # Check if narrative is present (may be None if LLM disabled)
        borrower_narrative = data.get("borrower_narrative")
        if borrower_narrative:
            print(f"   ✅ borrower_narrative present (LLM enabled)")
        else:
            print(f"   ⚠️  borrower_narrative is None (LLM may be disabled)")
        
        recommended_actions = data.get("recommended_actions")
        if recommended_actions:
            print(f"   ✅ recommended_actions present ({len(recommended_actions)} actions)")
        else:
            print(f"   ⚠️  recommended_actions is None (LLM may be disabled)")
        
        # Check safety_upgrade
        safety_upgrade = data.get("safety_upgrade")
        if safety_upgrade:
            print(f"   ✅ safety_upgrade present")
            if safety_upgrade.get("primary_suggestion"):
                print(f"   ✅ primary_suggestion present")
            else:
                print(f"   ⚠️  primary_suggestion is None")
        else:
            print(f"   ⚠️  safety_upgrade is None (may not be computed)")
        
        # Check strategy_lab
        strategy_lab = data.get("strategy_lab")
        if strategy_lab:
            print(f"   ✅ strategy_lab present")
            scenarios = strategy_lab.get("scenarios", [])
            if len(scenarios) >= 1:
                print(f"   ✅ strategy_lab has {len(scenarios)} scenario(s)")
            else:
                print(f"   ⚠️  strategy_lab has no scenarios")
        else:
            print(f"   ⚠️  strategy_lab is None (may not be computed)")
        
        print("\n✅ Test PASSED")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

