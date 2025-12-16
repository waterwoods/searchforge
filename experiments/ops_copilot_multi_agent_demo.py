#!/usr/bin/env python3
"""
ops_copilot_multi_agent_demo.py - Multi-Agent Demo for Ops Copilot
===================================================================
This script demonstrates the multi-agent architecture of Ops Copilot,
showing the three logical agents working together:

1. HealthAnalyst Agent: Analyzes system health and gathers context
2. RemediationPlanner Agent: Generates remediation strategies
3. Explainer Agent: Produces human-friendly explanations

Usage:
    # Run all scenarios (default)
    python experiments/ops_copilot_multi_agent_demo.py

    # Run a single scenario
    python experiments/ops_copilot_multi_agent_demo.py --scenario healthy
    python experiments/ops_copilot_multi_agent_demo.py --scenario degraded
    python experiments/ops_copilot_multi_agent_demo.py --scenario critical

    # Disable LLM (skip Explainer agent)
    python experiments/ops_copilot_multi_agent_demo.py --no-llm
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.schemas import SystemSnapshot
from services.fiqa_api.ops_copilot.ops_runtime import (
    run_health_analyst_agent,
    run_remediation_planner_agent,
    run_explainer_agent,
)


def create_healthy_snapshot() -> SystemSnapshot:
    """Create a healthy system snapshot - all metrics within safe thresholds."""
    return SystemSnapshot(
        service_name="api-gateway",
        environment="prod",
        cpu_pct=32.0,
        mem_pct=48.0,
        p95_latency_ms=120.0,
        error_rate=0.0002,
        qps=800.0,
        disk_pct=55.0,
        timestamp=datetime.utcnow(),
        region="us-east-1",
        tags={"team": "platform", "tier": "critical"},
    )


def create_degraded_snapshot() -> SystemSnapshot:
    """Create a degraded system snapshot - multiple warnings but not critical."""
    return SystemSnapshot(
        service_name="search-api",
        environment="prod",
        cpu_pct=78.0,
        mem_pct=82.0,
        p95_latency_ms=450.0,
        error_rate=0.018,
        qps=1500.0,
        disk_pct=82.0,
        timestamp=datetime.utcnow(),
        region="us-west-2",
        tags={"team": "search", "tier": "critical"},
    )


def create_critical_snapshot() -> SystemSnapshot:
    """Create a critical system snapshot - severe degradation requiring immediate action."""
    return SystemSnapshot(
        service_name="payment-service",
        environment="prod",
        cpu_pct=94.0,
        mem_pct=91.0,
        p95_latency_ms=950.0,
        error_rate=0.065,
        qps=2000.0,
        disk_pct=93.0,
        timestamp=datetime.utcnow(),
        region="eu-west-1",
        tags={"team": "payments", "tier": "critical"},
    )


def format_multi_agent_output(
    scenario_name: str,
    snapshot: SystemSnapshot,
    health_output,
    plan_output,
    explainer_output,
    llm_disabled: bool = False,
) -> str:
    """Format the multi-agent output for display."""
    lines = []
    
    # Header
    lines.append("")
    lines.append("=" * 80)
    lines.append(f"Scenario: {scenario_name} – {snapshot.service_name} ({snapshot.environment})")
    lines.append("-" * 80)
    lines.append("")
    
    # HealthAnalyst Agent
    lines.append("[HealthAnalyst]")
    health_result = health_output.health_result
    lines.append(f"  - band: {health_result.band}")
    lines.append(f"  - score: {health_result.score:.1f}")
    
    if health_result.risk_flags:
        risk_flags_str = ", ".join(health_result.risk_flags)
        lines.append(f"  - risk_flags: [{risk_flags_str}]")
    else:
        lines.append(f"  - risk_flags: []")
    
    if health_output.analysis_notes:
        lines.append("  - notes:")
        for note in health_output.analysis_notes:
            lines.append(f"    * {note}")
    
    lines.append("")
    
    # RemediationPlanner Agent
    lines.append("[RemediationPlanner]")
    
    safety_count = len(plan_output.safety_suggestions)
    if safety_count > 0:
        best_suggestion = plan_output.safety_suggestions[0]
        lines.append(f"  - safety suggestions: {safety_count} generated")
        lines.append(f"    Best: {best_suggestion.title}")
        if best_suggestion.estimated_result:
            lines.append(f"    Estimated improvement: {health_result.score:.1f} → {best_suggestion.estimated_result.score:.1f}")
    else:
        lines.append(f"  - safety suggestions: 0 (system is healthy)")
    
    if plan_output.strategy_lab and plan_output.strategy_lab.scenarios:
        baseline_score = plan_output.strategy_lab.baseline_health.score
        best_scenario = plan_output.strategy_lab.scenarios[0]
        score_delta = best_scenario.health_result.score - baseline_score
        lines.append(f"  - strategy lab: best scenario is '{best_scenario.title}'")
        lines.append(f"    Score change: {baseline_score:.1f} → {best_scenario.health_result.score:.1f} ({score_delta:+.1f})")
    else:
        lines.append(f"  - strategy lab: no scenarios generated")
    
    if plan_output.plan_notes:
        lines.append("  - notes:")
        for note in plan_output.plan_notes:
            lines.append(f"    * {note}")
    
    lines.append("")
    
    # Explainer Agent
    lines.append("[Explainer]")
    
    if llm_disabled:
        lines.append("  - skipped (LLM disabled)")
    elif explainer_output:
        if explainer_output.narrative:
            # Truncate narrative to first 2 sentences for display
            narrative = explainer_output.narrative
            sentences = narrative.split('.')
            truncated = ('.'.join(sentences[:2]) + '.').strip() if len(sentences) > 1 else narrative
            if len(truncated) > 150:
                truncated = truncated[:147] + "..."
            lines.append(f"  - narrative: {truncated}")
        else:
            lines.append(f"  - narrative: (none generated)")
        
        if explainer_output.recommended_actions:
            lines.append("  - recommended_actions:")
            for i, action in enumerate(explainer_output.recommended_actions, 1):
                lines.append(f"    {i}) {action}")
        else:
            lines.append("  - recommended_actions: (none)")
    else:
        lines.append("  - error generating explanation")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def run_scenario(
    scenario_name: str,
    snapshot: SystemSnapshot,
    llm_disabled: bool = False,
) -> None:
    """Run a single scenario through the multi-agent system."""
    request_id = f"multi_agent_demo_{scenario_name}_{datetime.utcnow().timestamp():.0f}"
    
    try:
        # Step 1: HealthAnalyst Agent
        health_output = run_health_analyst_agent(snapshot, request_id=request_id)
        
        # Step 2: RemediationPlanner Agent
        plan_output = run_remediation_planner_agent(
            snapshot,
            health_output,
            request_id=request_id,
        )
        
        # Step 3: Explainer Agent (skip if LLM disabled)
        explainer_output = None
        if not llm_disabled:
            explainer_output = run_explainer_agent(
                snapshot,
                health_output,
                plan_output,
                request_id=request_id,
            )
        
        # Format and display output
        output = format_multi_agent_output(
            scenario_name,
            snapshot,
            health_output,
            plan_output,
            explainer_output,
            llm_disabled=llm_disabled,
        )
        print(output)
        
    except Exception as e:
        print(f"\n❌ Error processing {scenario_name}: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-agent demo for Ops Copilot"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=["healthy", "degraded", "critical", "all"],
        default="all",
        help="Which scenario to run: healthy, degraded, critical, or all (default: all)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM (skip Explainer agent)",
    )
    
    args = parser.parse_args()
    
    # Check if LLM is disabled via env var or flag
    llm_env_disabled = os.getenv("LLM_GENERATION_ENABLED", "").lower() == "false"
    llm_disabled = args.no_llm or llm_env_disabled
    
    # If not explicitly set, disable LLM for demo consistency
    if not os.getenv("LLM_GENERATION_ENABLED"):
        os.environ["LLM_GENERATION_ENABLED"] = "false"
        llm_disabled = True
    
    # Define all scenarios
    all_scenarios = [
        ("healthy", "Healthy service", create_healthy_snapshot),
        ("degraded", "Degraded service", create_degraded_snapshot),
        ("critical", "Critical service", create_critical_snapshot),
    ]
    
    # Filter scenarios based on --scenario parameter
    if args.scenario == "all":
        scenarios = all_scenarios
    else:
        scenarios = [(key, name, fn) for key, name, fn in all_scenarios if key == args.scenario]
    
    # Print header
    print("=" * 80)
    print("Ops Copilot Multi-Agent Demo")
    print("=" * 80)
    print()
    print("This demo shows the three logical agents working together:")
    print("  1. HealthAnalyst: Analyze system health and gather context")
    print("  2. RemediationPlanner: Generate remediation strategies")
    print("  3. Explainer: Produce human-friendly explanations")
    print()
    
    if llm_disabled:
        print("⚠️  LLM disabled - Explainer agent will be skipped")
        print()
    
    if args.scenario != "all":
        print(f"Scenario filter: {args.scenario}")
        print()
    
    # Run scenarios
    for scenario_key, name, create_fn in scenarios:
        snapshot = create_fn()
        run_scenario(scenario_key, snapshot, llm_disabled=llm_disabled)
    
    print()
    print("=" * 80)
    print("Multi-Agent Demo Complete")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())

