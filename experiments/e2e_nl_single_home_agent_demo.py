#!/usr/bin/env python3
"""
e2e_nl_single_home_agent_demo.py - End-to-End NL Single Home Agent Demo

Runs end-to-end regression/demo scenarios that exercise the full Mortgage Agent pipeline:
- From natural-language input (optional multi-turn),
- Through the /api/mortgage-agent/nl-to-stress-request NLU helper,
- Into a full agent run via /api/mortgage-agent/single-home-agent,
- Asserting key outputs like stress_band, ApprovalScore bucket, risk flags, and which LangGraph stages ran.

Usage:
    python experiments/e2e_nl_single_home_agent_demo.py                    # Run all scenarios
    python experiments/e2e_nl_single_home_agent_demo.py --scenario-id socal_tight_nl  # Run one scenario
    python experiments/e2e_nl_single_home_agent_demo.py --verbose         # Print more details
    python experiments/e2e_nl_single_home_agent_demo.py --base-url http://localhost:8000
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests


# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8000"


# ============================================================================
# Scenario Definitions
# ============================================================================

@dataclass
class Scenario:
    """E2E scenario definition."""
    id: str
    name: str
    entry_mode: Literal["nl", "form"]
    # For NL scenarios
    nl_turns: Optional[List[str]] = None
    # For form scenarios
    request_body: Optional[Dict[str, Any]] = None
    # Expectations
    expected_stress_band: Optional[Literal["loose", "ok", "tight", "high_risk"]] = None
    expected_hard_block: Optional[bool] = None
    safety_upgrade_expected_to_run: Optional[bool] = None
    mortgage_programs_expected_to_run: Optional[bool] = None
    strategy_lab_expected_to_run: Optional[bool] = None


# Scenario 1: SoCal High Price (Feels Tight, NL entry)
SCENARIO_SOCAL_TIGHT_NL = Scenario(
    id="socal_tight_nl",
    name="SoCal High Price via NL",
    entry_mode="nl",
    nl_turns=[
        "We make about $15k per month and are looking at a $1.1M home in 92648 with 20% down."
    ],
    expected_stress_band="high_risk",
    expected_hard_block=True,
    safety_upgrade_expected_to_run=True,
    mortgage_programs_expected_to_run=True,
    strategy_lab_expected_to_run=True,
)


# Scenario 2: Texas Starter Home (Comfortable, form entry)
SCENARIO_TEXAS_STARTER_FORM = Scenario(
    id="texas_starter_form",
    name="Texas Starter Home via form",
    entry_mode="form",
    request_body={
        "monthly_income": 9000.0,  # $108k annual
        "other_debts_monthly": 300.0,
        "list_price": 380000.0,
        "down_payment_pct": 0.20,
        "zip_code": "78701",  # Austin, TX
        "state": "TX",
        "hoa_monthly": 150.0,
        "risk_preference": "neutral",
    },
    expected_stress_band="loose",
    expected_hard_block=False,
    safety_upgrade_expected_to_run=False,
    mortgage_programs_expected_to_run=False,
    strategy_lab_expected_to_run=True,
)


# Scenario 3: Extreme High Risk (Hard Block, form entry)
SCENARIO_EXTREME_HIGH_RISK = Scenario(
    id="extreme_high_risk",
    name="Extreme High Risk via form",
    entry_mode="form",
    request_body={
        "monthly_income": 4500.0,  # $54k annual
        "other_debts_monthly": 1200.0,
        "list_price": 850000.0,
        "down_payment_pct": 0.05,  # Only 5% down
        "zip_code": "90803",  # Long Beach, CA
        "state": "CA",
        "hoa_monthly": 400.0,
        "risk_preference": "neutral",
    },
    expected_stress_band="high_risk",
    expected_hard_block=True,
    safety_upgrade_expected_to_run=True,
    mortgage_programs_expected_to_run=True,
    strategy_lab_expected_to_run=True,
)


# All scenarios
ALL_SCENARIOS: List[Scenario] = [
    SCENARIO_SOCAL_TIGHT_NL,
    SCENARIO_TEXAS_STARTER_FORM,
    SCENARIO_EXTREME_HIGH_RISK,
]


# ============================================================================
# Helper Functions
# ============================================================================

def run_nl_interaction(
    base_url: str,
    nl_turns: List[str],
    initial_request: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Runs 1-N turns of NL interaction against /api/mortgage-agent/nl-to-stress-request
    and returns the final merged_request dict.
    
    Args:
        base_url: API base URL
        nl_turns: List of user messages (1-3 messages)
        initial_request: Optional initial request state
        verbose: Whether to print verbose output
        
    Returns:
        Final merged_request dict ready for single-home-agent endpoint
    """
    url = f"{base_url}/api/mortgage-agent/nl-to-stress-request"
    
    current_request = initial_request.copy() if initial_request else None
    conversation_history: List[Dict[str, str]] = []
    
    for turn_idx, user_text in enumerate(nl_turns):
        if verbose:
            print(f"  NL Turn {turn_idx + 1}/{len(nl_turns)}: {user_text[:60]}...")
        
        payload = {
            "user_text": user_text,
            "current_request": current_request,
        }
        
        if conversation_history:
            # Convert to ConversationMessage format
            payload["conversation_history"] = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation_history
            ]
        
        try:
            response = requests.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            # Update current_request with merged_request
            merged_request = data.get("merged_request")
            if merged_request:
                current_request = merged_request
            
            # Update conversation history
            conv_history = data.get("conversation_history", [])
            if conv_history:
                conversation_history = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in conv_history
                ]
            
            if verbose:
                router_decision = data.get("router_decision", "unknown")
                missing_fields = data.get("missing_required_fields", [])
                print(f"    Router decision: {router_decision}, Missing: {missing_fields}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ NL interaction failed at turn {turn_idx + 1}: {e}", file=sys.stderr)
            raise
    
    # Return final merged_request (or empty dict if None)
    return current_request or {}


def run_single_home_agent(
    base_url: str,
    stress_request: Dict[str, Any],
    user_message: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Runs the single-home-agent endpoint with a stress request.
    
    Args:
        base_url: API base URL
        stress_request: StressCheckRequest-compatible dict
        user_message: Optional user message
        verbose: Whether to print verbose output
        
    Returns:
        SingleHomeAgentResponse dict
    """
    url = f"{base_url}/api/mortgage-agent/single-home-agent"
    
    payload = {
        "stress_request": stress_request,
    }
    
    if user_message:
        payload["user_message"] = user_message
    
    if verbose:
        print(f"  Calling single-home-agent with request keys: {list(stress_request.keys())}")
    
    try:
        response = requests.post(url, json=payload, timeout=60.0)
        if not response.ok:
            # Try to extract error details from response
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", str(response.text))
                if verbose:
                    print(f"  ❌ API Error ({response.status_code}): {error_msg}")
            except:
                error_msg = response.text
                if verbose:
                    print(f"  ❌ API Error ({response.status_code}): {error_msg}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Single-home-agent call failed: {e}", file=sys.stderr)
        raise


def check_node_usage(response: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check which nodes were used based on response data.
    
    Returns:
        Dict mapping node names to whether they were used
    """
    return {
        "safety_upgrade": response.get("safety_upgrade") is not None,
        "mortgage_programs": response.get("mortgage_programs_preview") is not None,
        "strategy_lab": response.get("strategy_lab") is not None,
    }


def run_scenario(scenario: Scenario, base_url: str, verbose: bool = False) -> tuple:
    """
    Run a single scenario through the E2E pipeline.
    
    Returns:
        (all_expectations_met: bool, results_dict: Dict)
    """
    print(f"\n{'=' * 80}")
    print(f"[Scenario] {scenario.name} (id: {scenario.id})")
    print(f"{'=' * 80}")
    print(f"Entry mode: {scenario.entry_mode}")
    
    try:
        # Step 1: Get final stress_request
        if scenario.entry_mode == "nl":
            if not scenario.nl_turns:
                print("❌ ERROR: NL scenario missing nl_turns")
                return False, {"error": "missing_nl_turns"}
            
            if verbose:
                print(f"\n📝 Running NL interaction ({len(scenario.nl_turns)} turn(s))...")
            
            stress_request = run_nl_interaction(
                base_url=base_url,
                nl_turns=scenario.nl_turns,
                initial_request=None,
                verbose=verbose,
            )
            
            # Check if we have required fields
            if not stress_request.get("monthly_income") or not stress_request.get("list_price"):
                print("❌ ERROR: NL interaction did not extract required fields (monthly_income, list_price)")
                return False, {"error": "missing_required_fields_after_nl"}
        
        else:  # form entry
            if not scenario.request_body:
                print("❌ ERROR: Form scenario missing request_body")
                return False, {"error": "missing_request_body"}
            
            stress_request = scenario.request_body.copy()
        
        # Ensure required fields have defaults
        if "other_debts_monthly" not in stress_request:
            stress_request["other_debts_monthly"] = 0.0
        if "down_payment_pct" not in stress_request:
            stress_request["down_payment_pct"] = 0.20
        if "hoa_monthly" not in stress_request:
            stress_request["hoa_monthly"] = 0.0
        if "risk_preference" not in stress_request:
            stress_request["risk_preference"] = "neutral"
        
        if verbose:
            print(f"\n📋 Final stress_request:")
            print(f"  - monthly_income: ${stress_request.get('monthly_income', 0):,.2f}")
            print(f"  - list_price: ${stress_request.get('list_price', 0):,.2f}")
            print(f"  - down_payment_pct: {stress_request.get('down_payment_pct', 0.20):.1%}")
            print(f"  - zip_code: {stress_request.get('zip_code', 'N/A')}")
            print(f"  - state: {stress_request.get('state', 'N/A')}")
        
        # Step 2: Run single-home-agent
        if verbose:
            print(f"\n🚀 Running single-home-agent...")
        
        agent_response = run_single_home_agent(
            base_url=base_url,
            stress_request=stress_request,
            user_message=None,
            verbose=verbose,
        )
        
        # Step 3: Extract results
        stress_result = agent_response.get("stress_result")
        if not stress_result:
            print("❌ ERROR: stress_result is None")
            return False, {"error": "stress_result_is_none"}
        
        stress_band = stress_result.get("stress_band")
        dti_ratio = stress_result.get("dti_ratio", 0.0)
        approval_score = stress_result.get("approval_score")
        risk_assessment = agent_response.get("risk_assessment") or stress_result.get("risk_assessment")
        
        # Print results summary
        print(f"\n📊 Results:")
        print(f"  - stress_band: {stress_band}")
        if approval_score:
            score = approval_score.get("score", "N/A")
            bucket = approval_score.get("bucket", "N/A")
            print(f"  - approval_score: {score} / 100 ({bucket})")
        print(f"  - dti_ratio: {dti_ratio:.1%}")
        print(f"  - total_monthly_payment: ${stress_result.get('total_monthly_payment', 0):,.2f}")
        
        if risk_assessment:
            hard_block = risk_assessment.get("hard_block", False)
            soft_warning = risk_assessment.get("soft_warning", False)
            risk_flags = risk_assessment.get("risk_flags", [])
            print(f"  - risk_assessment: hard_block={hard_block}, soft_warning={soft_warning}")
            if risk_flags:
                print(f"  - risk_flags: {', '.join(risk_flags)}")
        
        # Check node usage
        node_usage = check_node_usage(agent_response)
        print(f"\n🔍 Nodes executed:")
        for node_name, used in node_usage.items():
            icon = "✅" if used else "⏭️"
            print(f"    {icon} {node_name}: {'used' if used else 'skipped'}")
        
        # Step 4: Validate expectations
        print(f"\n✅ Expectations validation:")
        
        all_ok = True
        
        # Check stress_band
        if scenario.expected_stress_band:
            stress_band_ok = stress_band == scenario.expected_stress_band
            icon = "✅" if stress_band_ok else "❌"
            print(f"    {icon} expected_stress_band={scenario.expected_stress_band} -> {stress_band} {'OK' if stress_band_ok else 'MISMATCH'}")
            if not stress_band_ok:
                all_ok = False
        
        # Check hard_block
        if scenario.expected_hard_block is not None:
            hard_block_actual = risk_assessment.get("hard_block", False) if risk_assessment else False
            hard_block_ok = hard_block_actual == scenario.expected_hard_block
            icon = "✅" if hard_block_ok else "❌"
            print(f"    {icon} expected_hard_block={scenario.expected_hard_block} -> {hard_block_actual} {'OK' if hard_block_ok else 'MISMATCH'}")
            if not hard_block_ok:
                all_ok = False
        
        # Check node usage expectations
        if scenario.safety_upgrade_expected_to_run is not None:
            safety_ok = node_usage["safety_upgrade"] == scenario.safety_upgrade_expected_to_run
            icon = "✅" if safety_ok else "❌"
            expected_str = "expected" if scenario.safety_upgrade_expected_to_run else "not expected"
            actual_str = "used" if node_usage["safety_upgrade"] else "not used"
            print(f"    {icon} expected_use_safety_upgrade={scenario.safety_upgrade_expected_to_run} -> {actual_str} {'OK' if safety_ok else 'MISMATCH'}")
            if not safety_ok:
                all_ok = False
        
        if scenario.mortgage_programs_expected_to_run is not None:
            programs_ok = node_usage["mortgage_programs"] == scenario.mortgage_programs_expected_to_run
            icon = "✅" if programs_ok else "❌"
            expected_str = "expected" if scenario.mortgage_programs_expected_to_run else "not expected"
            actual_str = "used" if node_usage["mortgage_programs"] else "not used"
            print(f"    {icon} expected_use_mortgage_programs={scenario.mortgage_programs_expected_to_run} -> {actual_str} {'OK' if programs_ok else 'MISMATCH'}")
            if not programs_ok:
                all_ok = False
        
        if scenario.strategy_lab_expected_to_run is not None:
            strategy_ok = node_usage["strategy_lab"] == scenario.strategy_lab_expected_to_run
            icon = "✅" if strategy_ok else "❌"
            expected_str = "expected" if scenario.strategy_lab_expected_to_run else "not expected"
            actual_str = "used" if node_usage["strategy_lab"] else "not used"
            print(f"    {icon} expected_use_strategy_lab={scenario.strategy_lab_expected_to_run} -> {actual_str} {'OK' if strategy_ok else 'MISMATCH'}")
            if not strategy_ok:
                all_ok = False
        
        return all_ok, {
            "scenario_id": scenario.id,
            "stress_band": stress_band,
            "stress_band_ok": stress_band == scenario.expected_stress_band if scenario.expected_stress_band else None,
            "hard_block": risk_assessment.get("hard_block", False) if risk_assessment else False,
            "hard_block_ok": (risk_assessment.get("hard_block", False) == scenario.expected_hard_block) if (scenario.expected_hard_block is not None and risk_assessment) else None,
            "node_usage": node_usage,
            "all_expectations_met": all_ok,
        }
    
    except Exception as e:
        print(f"\n❌ ERROR: Scenario execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="End-to-end NL Single Home Agent regression/demo script"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--scenario-id",
        type=str,
        help="Run only the specified scenario ID (e.g., 'socal_tight_nl')",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("E2E NL Single Home Agent Demo")
    print("=" * 80)
    print(f"\n📍 Base URL: {args.base_url}")
    print("Running end-to-end scenarios through NL → single-home-agent pipeline...\n")
    
    # Filter scenarios if --scenario-id provided
    scenarios_to_run = ALL_SCENARIOS
    if args.scenario_id:
        scenarios_to_run = [
            s for s in ALL_SCENARIOS if s.id == args.scenario_id
        ]
        if not scenarios_to_run:
            print(f"❌ ERROR: Scenario ID '{args.scenario_id}' not found")
            print("\nAvailable scenario IDs:")
            for s in ALL_SCENARIOS:
                print(f"  - {s.id}")
            return 1
    
    # Run scenarios
    results = []
    all_passed = True
    
    for scenario in scenarios_to_run:
        passed, result = run_scenario(scenario, args.base_url, verbose=args.verbose)
        results.append(result)
        if not passed:
            all_passed = False
    
    # Final summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    for result in results:
        if "error" in result:
            print(f"\n❌ {result.get('scenario_id', 'unknown')}: ERROR - {result['error']}")
            continue
        
        status = "✅ PASS" if result["all_expectations_met"] else "❌ FAIL"
        print(f"\n{status} {result['scenario_id']}:")
        
        if result.get("stress_band_ok") is not None:
            print(f"  - Stress band: {result['stress_band']} ({'OK' if result['stress_band_ok'] else 'MISMATCH'})")
        
        if result.get("hard_block_ok") is not None:
            print(f"  - Hard block: {result['hard_block']} ({'OK' if result['hard_block_ok'] else 'MISMATCH'})")
        
        node_usage = result.get("node_usage", {})
        for node_name, used in node_usage.items():
            status_icon = "✅" if used else "⏭️"
            print(f"  - {status_icon} {node_name}: {'used' if used else 'skipped'}")
    
    if all_passed:
        print("\n✅ All scenarios passed!")
        return 0
    else:
        print("\n❌ Some scenarios failed expectations")
        return 1


if __name__ == "__main__":
    sys.exit(main())

