#!/usr/bin/env python3
"""
system_health_agent_react_demo.py - Demo comparing deterministic vs ReAct planner

This script demonstrates the difference between:
- run_system_health_graph() (deterministic flow)
- run_system_health_graph_with_planner() (ReAct planner flow)

Usage:
    python experiments/system_health_agent_react_demo.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.schemas import SystemSnapshot
from services.fiqa_api.ops_copilot.graphs.system_health_graph import (
    run_system_health_graph,
    run_system_health_graph_with_planner,
)


def create_healthy_snapshot() -> SystemSnapshot:
    """Create a healthy system snapshot."""
    return SystemSnapshot(
        service_name="search-api",
        environment="prod",
        cpu_pct=45.0,
        mem_pct=50.0,
        p95_latency_ms=150.0,
        error_rate=0.001,  # 0.1%
        qps=800.0,
        disk_pct=60.0,
        timestamp=datetime.utcnow(),
        region="us-east-1",
        tags={"team": "search", "tier": "critical"},
    )


def create_degraded_snapshot() -> SystemSnapshot:
    """Create a degraded system snapshot."""
    return SystemSnapshot(
        service_name="api-gateway",
        environment="prod",
        cpu_pct=75.0,  # Warning threshold
        mem_pct=78.0,  # Warning threshold
        p95_latency_ms=350.0,  # Warning threshold
        error_rate=0.015,  # 1.5% - warning threshold
        qps=1200.0,
        disk_pct=80.0,  # Warning threshold
        timestamp=datetime.utcnow(),
        region="us-west-2",
        tags={"team": "platform", "tier": "critical"},
    )


def print_comparison(
    snapshot: SystemSnapshot,
    deterministic_result: dict,
    planner_result: dict,
):
    """Print comparison between deterministic and planner results."""
    print("\n" + "="*80)
    print(f"Service: {snapshot.service_name} ({snapshot.environment})")
    print("="*80)
    
    # Health result comparison
    det_health = deterministic_result["health_result"]
    plan_health = planner_result["health_result"]
    
    print(f"\nHealth Result:")
    print(f"  Deterministic: band={det_health.band}, score={det_health.score:.1f}")
    print(f"  Planner:       band={plan_health.band}, score={plan_health.score:.1f}")
    
    # Safety suggestions comparison
    det_safety = deterministic_result.get("safety_suggestions") or []
    plan_safety = planner_result.get("safety_suggestions") or []
    
    print(f"\nSafety Suggestions:")
    print(f"  Deterministic: {len(det_safety)} suggestions")
    print(f"  Planner:       {len(plan_safety)} suggestions")
    
    # Strategy lab comparison
    det_strategy = deterministic_result.get("strategy_lab")
    plan_strategy = planner_result.get("strategy_lab")
    
    print(f"\nStrategy Lab:")
    det_scenarios = len(det_strategy.scenarios) if det_strategy else 0
    plan_scenarios = len(plan_strategy.scenarios) if plan_strategy else 0
    print(f"  Deterministic: {det_scenarios} scenarios")
    print(f"  Planner:       {plan_scenarios} scenarios")
    
    # Agent steps comparison
    det_steps = deterministic_result.get("agent_steps", [])
    plan_steps = planner_result.get("agent_steps", [])
    
    print(f"\nAgent Steps:")
    print(f"  Deterministic: {len(det_steps)} steps")
    print(f"  Planner:       {len(plan_steps)} steps")
    
    # Planner-specific: show planner steps
    planner_steps = [s for s in plan_steps if "react_planner" in s.step_id]
    if planner_steps:
        print(f"\nPlanner Steps ({len(planner_steps)}):")
        for step in planner_steps:
            tool = step.inputs.get("tool", "unknown") if hasattr(step, "inputs") else "unknown"
            reason = step.inputs.get("reason", "") if hasattr(step, "inputs") else ""
            print(f"  - {step.step_name}: tool={tool}, reason={reason[:50]}")
    
    # Action plan comparison
    det_plan = deterministic_result.get("action_plan")
    plan_plan = planner_result.get("action_plan")
    
    print(f"\nAction Plan:")
    det_actions = len(det_plan.actions) if det_plan else 0
    plan_actions = len(plan_plan.actions) if plan_plan else 0
    print(f"  Deterministic: {det_actions} actions")
    print(f"  Planner:       {plan_actions} actions")


def test_healthy_case():
    """Test healthy case comparison."""
    print("\n" + "="*80)
    print("CASE 1: Healthy System")
    print("="*80)
    
    snapshot = create_healthy_snapshot()
    
    # Run deterministic flow
    print("\nRunning deterministic flow...")
    deterministic_result = run_system_health_graph(snapshot, request_id="demo_healthy_deterministic")
    
    # Run planner flow
    print("Running planner flow...")
    planner_result = run_system_health_graph_with_planner(snapshot, request_id="demo_healthy_planner")
    
    # Print comparison
    print_comparison(snapshot, deterministic_result, planner_result)


def test_degraded_case():
    """Test degraded case comparison."""
    print("\n" + "="*80)
    print("CASE 2: Degraded System")
    print("="*80)
    
    snapshot = create_degraded_snapshot()
    
    # Run deterministic flow
    print("\nRunning deterministic flow...")
    deterministic_result = run_system_health_graph(snapshot, request_id="demo_degraded_deterministic")
    
    # Run planner flow
    print("Running planner flow...")
    planner_result = run_system_health_graph_with_planner(snapshot, request_id="demo_degraded_planner")
    
    # Print comparison
    print_comparison(snapshot, deterministic_result, planner_result)


def main():
    """Run demo."""
    print("="*80)
    print("System Health Agent: Deterministic vs ReAct Planner Comparison")
    print("="*80)
    
    try:
        test_healthy_case()
        test_degraded_case()
        
        print("\n" + "="*80)
        print("✅ DEMO COMPLETED")
        print("="*80)
        return 0
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

