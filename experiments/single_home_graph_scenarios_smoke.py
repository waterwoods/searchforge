#!/usr/bin/env python3
"""
single_home_graph_scenarios_smoke.py - Single Home Graph Scenarios Smoke Test

Runs 3-4 highly distinguishable demo scenarios through the single-home LangGraph workflow
and validates which nodes executed. Used for interview demos and regression testing.

Usage:
    python experiments/single_home_graph_scenarios_smoke.py                    # Run all scenarios
    python experiments/single_home_graph_scenarios_smoke.py --scenario-id socal_tight  # Run one scenario
    python experiments/single_home_graph_scenarios_smoke.py --list                # List available scenarios
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage.demo_scenarios import (
    SINGLE_HOME_DEMO_SCENARIOS,
    SingleHomeDemoScenario,
)
from services.fiqa_api.mortgage.graphs import run_single_home_graph
from services.fiqa_api.mortgage.schemas import SingleHomeAgentRequest


def check_node_usage(
    response, scenario: SingleHomeDemoScenario
) -> Dict[str, Dict[str, bool]]:
    """
    Check which nodes were used and compare with expectations.
    
    Note: A node is considered "used" if it was executed, even if it returned
    empty results. This is different from a node that was skipped by the router.
    
    Returns:
        Dict mapping node names to validation results:
        {
            "safety_upgrade": {"used": bool, "expected": bool, "ok": bool},
            "mortgage_programs": {"used": bool, "expected": bool, "ok": bool},
            "strategy_lab": {"used": bool, "expected": bool, "ok": bool},
        }
    """
    # Check safety_upgrade usage
    # The node runs if safety_upgrade is not None (even if safer_homes is None or empty)
    safety_upgrade_used = response.safety_upgrade is not None
    
    # Check mortgage_programs usage
    # The node runs if mortgage_programs_preview is not None (even if empty list)
    # Note: mortgage_programs only runs if safety_upgrade path was taken
    mortgage_programs_used = response.mortgage_programs_preview is not None
    
    # Check strategy_lab usage
    # The node always runs (it's on both paths), so check if result exists
    strategy_lab_used = response.strategy_lab is not None
    
    return {
        "safety_upgrade": {
            "used": safety_upgrade_used,
            "expected": scenario.expected_use_safety_upgrade,
            "ok": safety_upgrade_used == scenario.expected_use_safety_upgrade,
        },
        "mortgage_programs": {
            "used": mortgage_programs_used,
            "expected": scenario.expected_use_mortgage_programs,
            "ok": mortgage_programs_used == scenario.expected_use_mortgage_programs,
        },
        "strategy_lab": {
            "used": strategy_lab_used,
            "expected": scenario.expected_use_strategy_lab,
            "ok": strategy_lab_used == scenario.expected_use_strategy_lab,
        },
    }


def get_node_execution_summary(response) -> Dict[str, str]:
    """
    Get a summary of which nodes executed based on response data.
    
    Returns:
        Dict mapping node names to execution status ("completed", "skipped", "unknown")
    """
    summary = {}
    
    # stress_check always runs (it's the entry point)
    summary["stress_check"] = "completed"
    
    # safety_upgrade: check if present and has data
    if response.safety_upgrade is not None:
        summary["safety_upgrade"] = "completed"
    else:
        summary["safety_upgrade"] = "skipped"
    
    # mortgage_programs: check if preview exists
    if response.mortgage_programs_preview is not None:
        summary["mortgage_programs"] = "completed"
    else:
        summary["mortgage_programs"] = "skipped"
    
    # strategy_lab: check if present
    if response.strategy_lab is not None:
        summary["strategy_lab"] = "completed"
    else:
        summary["strategy_lab"] = "skipped"
    
    # llm_explanation: check if narrative exists
    if response.borrower_narrative is not None:
        summary["llm_explanation"] = "completed"
    else:
        summary["llm_explanation"] = "skipped"
    
    return summary


def run_scenario(scenario: SingleHomeDemoScenario) -> tuple:
    """
    Run a single scenario through the LangGraph and return validation results.
    
    Returns:
        (all_expectations_met: bool, results_dict: Dict)
    """
    print(f"\n{'=' * 80}")
    print(f"[Scenario] {scenario.title} (id: {scenario.id})")
    print(f"{'=' * 80}")
    print(f"Description: {scenario.description}")
    print(f"\nRequest parameters:")
    print(f"  - Monthly income: ${scenario.request.monthly_income:,.2f}")
    print(f"  - Other debts: ${scenario.request.other_debts_monthly:,.2f}/month")
    print(f"  - List price: ${scenario.request.list_price:,.2f}")
    print(f"  - Down payment: {scenario.request.down_payment_pct:.1%}")
    print(f"  - Location: {scenario.request.zip_code or 'N/A'}, {scenario.request.state or 'N/A'}")
    print(f"  - HOA: ${scenario.request.hoa_monthly:,.2f}/month")
    
    # Build request
    agent_request = SingleHomeAgentRequest(
        stress_request=scenario.request,
        user_message=f"Evaluate this {scenario.title.lower()} scenario",
    )
    
    # Run the graph
    try:
        response = run_single_home_graph(agent_request)
    except Exception as e:
        print(f"\n❌ ERROR: Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {"error": str(e)}
    
    # Extract results
    stress_result = response.stress_result
    if not stress_result:
        print("\n❌ ERROR: stress_result is None")
        return False, {"error": "stress_result is None"}
    
    stress_band = stress_result.stress_band
    dti_ratio = stress_result.dti_ratio
    approval_score = stress_result.approval_score
    risk_assessment = stress_result.risk_assessment or response.risk_assessment
    
    # Print results summary
    print(f"\n📊 Results:")
    print(f"  - stress_band: {stress_band}")
    print(f"  - approval_score: {approval_score.score if approval_score else 'N/A'} / 100 ({approval_score.bucket if approval_score else 'N/A'})")
    print(f"  - dti_ratio: {dti_ratio:.1%}")
    print(f"  - total_monthly_payment: ${stress_result.total_monthly_payment:,.2f}")
    
    if risk_assessment:
        risk_flags = risk_assessment.risk_flags or []
        print(f"  - risk_assessment: hard_block={risk_assessment.hard_block}, soft_warning={risk_assessment.soft_warning}")
        if risk_flags:
            print(f"  - risk_flags: {', '.join(risk_flags)}")
    
    # Get node execution summary
    node_summary = get_node_execution_summary(response)
    print(f"\n🔍 Nodes executed:")
    for node_name, status in node_summary.items():
        icon = "✅" if status == "completed" else "⏭️"
        print(f"    {icon} {node_name}: {status}")
    
    # Check node usage against expectations
    node_usage = check_node_usage(response, scenario)
    
    # Validate expectations
    print(f"\n✅ Expectations validation:")
    
    all_ok = True
    
    # Check stress_band
    stress_band_ok = stress_band == scenario.expected_stress_band
    icon = "✅" if stress_band_ok else "❌"
    print(f"    {icon} expected_stress_band={scenario.expected_stress_band} -> {stress_band} {'OK' if stress_band_ok else 'MISMATCH'}")
    if not stress_band_ok:
        all_ok = False
    
    # Check hard_block
    hard_block_actual = risk_assessment.hard_block if risk_assessment else False
    hard_block_ok = hard_block_actual == scenario.expected_hard_block
    icon = "✅" if hard_block_ok else "❌"
    print(f"    {icon} expected_hard_block={scenario.expected_hard_block} -> {hard_block_actual} {'OK' if hard_block_ok else 'MISMATCH'}")
    if not hard_block_ok:
        all_ok = False
    
    # Check node usage expectations
    for node_name, usage_info in node_usage.items():
        icon = "✅" if usage_info["ok"] else "❌"
        expected_str = "expected" if usage_info["expected"] else "not expected"
        actual_str = "used" if usage_info["used"] else "not used"
        print(f"    {icon} expected_use_{node_name}={usage_info['expected']} -> {actual_str} {'OK' if usage_info['ok'] else 'MISMATCH'}")
        if not usage_info["ok"]:
            all_ok = False
    
    # Additional details
    if response.safety_upgrade:
        safer_homes_count = len(response.safety_upgrade.safer_homes.candidates) if response.safety_upgrade.safer_homes else 0
        print(f"\n  Safety upgrade details:")
        print(f"    - Safer homes found: {safer_homes_count}")
        print(f"    - Baseline band: {response.safety_upgrade.baseline_band}")
        print(f"    - Baseline DTI: {response.safety_upgrade.baseline_dti:.1%}" if response.safety_upgrade.baseline_dti else "    - Baseline DTI: N/A")
    
    if response.mortgage_programs_preview:
        programs_count = len(response.mortgage_programs_preview)
        print(f"\n  Mortgage programs details:")
        print(f"    - Programs found: {programs_count}")
        if programs_count > 0:
            for i, prog in enumerate(response.mortgage_programs_preview[:3], 1):
                print(f"      {i}. {prog.name} ({prog.state or 'N/A'})")
    
    if response.strategy_lab:
        scenarios_count = len(response.strategy_lab.scenarios)
        print(f"\n  Strategy lab details:")
        print(f"    - Scenarios tested: {scenarios_count}")
        if scenarios_count > 0:
            for i, scenario_result in enumerate(response.strategy_lab.scenarios[:3], 1):
                print(f"      {i}. {scenario_result.title}: {scenario_result.stress_band or 'N/A'}")
    
    return all_ok, {
        "scenario_id": scenario.id,
        "stress_band": stress_band,
        "stress_band_ok": stress_band_ok,
        "hard_block": hard_block_actual,
        "hard_block_ok": hard_block_ok,
        "node_usage": node_usage,
        "all_expectations_met": all_ok,
    }


def list_scenarios():
    """List all available scenarios."""
    print("Available scenarios:")
    print("=" * 80)
    for scenario in SINGLE_HOME_DEMO_SCENARIOS:
        print(f"\n  ID: {scenario.id}")
        print(f"  Title: {scenario.title}")
        print(f"  Description: {scenario.description}")
        print(f"  Expected stress band: {scenario.expected_stress_band}")
        print(f"  Expected hard block: {scenario.expected_hard_block}")
        print(f"  Expected nodes:")
        print(f"    - safety_upgrade: {scenario.expected_use_safety_upgrade}")
        print(f"    - mortgage_programs: {scenario.expected_use_mortgage_programs}")
        print(f"    - strategy_lab: {scenario.expected_use_strategy_lab}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run single-home LangGraph scenarios and validate expectations"
    )
    parser.add_argument(
        "--scenario-id",
        type=str,
        help="Run only the specified scenario ID (e.g., 'socal_tight')",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available scenarios and exit",
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_scenarios()
        return 0
    
    print("=" * 80)
    print("Single Home Graph Scenarios Smoke Test")
    print("=" * 80)
    print("\nRunning scenarios through LangGraph workflow...")
    print("This validates which nodes execute and compares with expectations.\n")
    
    # Filter scenarios if --scenario-id provided
    scenarios_to_run = SINGLE_HOME_DEMO_SCENARIOS
    if args.scenario_id:
        scenarios_to_run = [
            s for s in SINGLE_HOME_DEMO_SCENARIOS if s.id == args.scenario_id
        ]
        if not scenarios_to_run:
            print(f"❌ ERROR: Scenario ID '{args.scenario_id}' not found")
            print("\nAvailable scenario IDs:")
            for s in SINGLE_HOME_DEMO_SCENARIOS:
                print(f"  - {s.id}")
            return 1
    
    # Run scenarios
    results = []
    all_passed = True
    
    for scenario in scenarios_to_run:
        passed, result = run_scenario(scenario)
        results.append(result)
        if not passed:
            all_passed = False
    
    # Final summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    for result in results:
        if "error" in result:
            print(f"\n❌ {result['scenario_id']}: ERROR - {result['error']}")
            continue
        
        status = "✅ PASS" if result["all_expectations_met"] else "❌ FAIL"
        print(f"\n{status} {result['scenario_id']}:")
        print(f"  - Stress band: {result['stress_band']} ({'OK' if result['stress_band_ok'] else 'MISMATCH'})")
        print(f"  - Hard block: {result['hard_block']} ({'OK' if result['hard_block_ok'] else 'MISMATCH'})")
        for node_name, usage_info in result["node_usage"].items():
            status_icon = "✅" if usage_info["ok"] else "❌"
            print(f"  - {status_icon} {node_name}: {'OK' if usage_info['ok'] else 'MISMATCH'}")
    
    if all_passed:
        print("\n✅ All scenarios passed!")
        return 0
    else:
        print("\n❌ Some scenarios failed expectations")
        return 1


if __name__ == "__main__":
    sys.exit(main())

