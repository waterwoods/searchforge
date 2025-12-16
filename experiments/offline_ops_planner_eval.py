#!/usr/bin/env python3
"""
offline_ops_planner_eval.py - Offline Evaluation: Deterministic vs ReAct Planner

This script compares the deterministic graph (run_system_health_graph) with the
ReAct planner graph (run_system_health_graph_with_planner) on a fixed set of
test scenarios.

Usage:
    # Run both deterministic and planner versions (default)
    python experiments/offline_ops_planner_eval.py

    # Run only planner version
    python experiments/offline_ops_planner_eval.py --use-planner-only

    # Enable verbose output (show agent step details)
    python experiments/offline_ops_planner_eval.py --verbose

This script is designed for interview demos and internal review to compare:
- Tool usage patterns (which tools are called, how many times)
- Step counts (deterministic vs planner agent_steps)
- Final health band, score, and action plan results
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

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


def create_critical_snapshot() -> SystemSnapshot:
    """Create a critical system snapshot."""
    return SystemSnapshot(
        service_name="payment-service",
        environment="prod",
        cpu_pct=92.0,  # Critical threshold
        mem_pct=88.0,  # Critical threshold
        p95_latency_ms=850.0,  # Critical threshold
        error_rate=0.06,  # 6% - critical threshold
        qps=1500.0,
        disk_pct=92.0,  # Critical threshold
        timestamp=datetime.utcnow(),
        region="eu-west-1",
        tags={"team": "payments", "tier": "critical"},
    )


def create_degraded_snapshot_variant() -> SystemSnapshot:
    """Create a variant degraded snapshot with different QPS/disk."""
    return SystemSnapshot(
        service_name="user-service",
        environment="prod",
        cpu_pct=72.0,
        mem_pct=76.0,
        p95_latency_ms=320.0,
        error_rate=0.012,  # 1.2%
        qps=900.0,  # Lower QPS
        disk_pct=78.0,  # Slightly lower disk
        timestamp=datetime.utcnow(),
        region="us-east-1",
        tags={"team": "platform", "tier": "standard"},
    )


def create_critical_snapshot_variant() -> SystemSnapshot:
    """Create a variant critical snapshot with different metrics."""
    return SystemSnapshot(
        service_name="analytics-service",
        environment="prod",
        cpu_pct=89.0,  # Slightly lower but still critical
        mem_pct=91.0,
        p95_latency_ms=920.0,
        error_rate=0.055,  # 5.5% - critical
        qps=1800.0,  # Higher QPS
        disk_pct=89.0,
        timestamp=datetime.utcnow(),
        region="us-west-2",
        tags={"team": "data", "tier": "critical"},
    )


def count_tool_calls(agent_steps: list) -> int:
    """
    Count tool calls from agent_steps.
    
    Tool calls are identified by step_id or step_name containing:
    - "health_check"
    - "safety_upgrade"
    - "strategy_lab"
    - "react_planner_step" (for planner steps that call tools)
    """
    tool_count = 0
    tool_names = ["health_check", "safety_upgrade", "strategy_lab"]
    
    for step in agent_steps:
        step_id = step.step_id if hasattr(step, "step_id") else ""
        step_name = step.step_name if hasattr(step, "step_name") else ""
        
        # Check if this is a tool call
        if any(tool in step_id.lower() or tool in step_name.lower() for tool in tool_names):
            tool_count += 1
        # Also count planner steps that call tools
        elif "react_planner_step" in step_id.lower():
            # Check if inputs contain a tool name
            inputs = step.inputs if hasattr(step, "inputs") else {}
            tool = inputs.get("tool", "") if isinstance(inputs, dict) else ""
            if tool in tool_names:
                tool_count += 1
    
    return tool_count


def count_planner_steps(agent_steps: list) -> int:
    """Count ReAct planner steps (steps with react_planner in step_id)."""
    return sum(1 for step in agent_steps if "react_planner" in (step.step_id if hasattr(step, "step_id") else ""))


def print_case_summary(
    case_name: str,
    snapshot: SystemSnapshot,
    deterministic_result: Optional[Dict[str, Any]],
    planner_result: Optional[Dict[str, Any]],
    verbose: bool = False,
):
    """Print comparison summary for a single test case."""
    print("\n" + "="*70)
    print(f"Case: {case_name} ({snapshot.service_name} in {snapshot.environment})")
    print("="*70)
    
    # Deterministic result
    if deterministic_result:
        det_health = deterministic_result.get("health_result")
        det_steps = deterministic_result.get("agent_steps", [])
        det_plan = deterministic_result.get("action_plan")
        det_tool_calls = count_tool_calls(det_steps)
        
        print("\nDeterministic:")
        if det_health:
            print(f"  band={det_health.band}, score={det_health.score:.1f}")
        print(f"  steps={len(det_steps)}, tool_calls={det_tool_calls}")
        if det_plan:
            print(f"  actions={len(det_plan.actions)}")
        else:
            print(f"  actions=0")
        
        if verbose and det_steps:
            print(f"\n  Step details (first 3):")
            for step in det_steps[:3]:
                step_name = step.step_name if hasattr(step, "step_name") else "unknown"
                print(f"    - {step_name}")
    else:
        print("\nDeterministic: (not run)")
    
    # Planner result
    if planner_result:
        plan_health = planner_result.get("health_result")
        plan_steps = planner_result.get("agent_steps", [])
        plan_plan = planner_result.get("action_plan")
        plan_tool_calls = count_tool_calls(plan_steps)
        plan_planner_steps = count_planner_steps(plan_steps)
        
        print("\nPlanner:")
        if plan_health:
            print(f"  band={plan_health.band}, score={plan_health.score:.1f}")
        print(f"  steps={len(plan_steps)}, tool_calls={plan_tool_calls}, planner_steps={plan_planner_steps}")
        if plan_plan:
            print(f"  actions={len(plan_plan.actions)}")
        else:
            print(f"  actions=0")
        
        if verbose and plan_steps:
            print(f"\n  Step details (first 3):")
            for step in plan_steps[:3]:
                step_name = step.step_name if hasattr(step, "step_name") else "unknown"
                inputs = step.inputs if hasattr(step, "inputs") else {}
                tool = inputs.get("tool", "") if isinstance(inputs, dict) else ""
                if tool:
                    print(f"    - {step_name} (tool: {tool})")
                else:
                    print(f"    - {step_name}")
        
        # Notes about planner behavior
        print("\nNotes:")
        if plan_planner_steps > 0:
            planner_tool_calls = []
            for step in plan_steps:
                if "react_planner_step" in (step.step_id if hasattr(step, "step_id") else ""):
                    inputs = step.inputs if hasattr(step, "inputs") else {}
                    tool = inputs.get("tool", "") if isinstance(inputs, dict) else ""
                    if tool and tool != "finish":
                        planner_tool_calls.append(tool)
            
            if planner_tool_calls:
                print(f"  - Planner called tools: {', '.join(set(planner_tool_calls))}")
            else:
                print(f"  - Planner used {plan_planner_steps} steps")
    else:
        print("\nPlanner: (not run)")
    
    print()


def run_evaluation(use_planner_only: bool = False, verbose: bool = False):
    """Run evaluation on all test cases."""
    print("="*70)
    print("Offline Ops Planner Evaluation: Deterministic vs ReAct Planner")
    print("="*70)
    
    # Define test cases
    test_cases = [
        ("healthy_prod", create_healthy_snapshot()),
        ("degraded_prod", create_degraded_snapshot()),
        ("critical_prod", create_critical_snapshot()),
        ("degraded_prod_variant", create_degraded_snapshot_variant()),
        ("critical_prod_variant", create_critical_snapshot_variant()),
    ]
    
    for case_name, snapshot in test_cases:
        deterministic_result = None
        planner_result = None
        
        # Run deterministic version (unless --use-planner-only)
        if not use_planner_only:
            try:
                request_id = f"eval_{case_name}_deterministic"
                deterministic_result = run_system_health_graph(snapshot, request_id=request_id)
            except Exception as e:
                print(f"Deterministic failed for case {case_name}: {e}")
                deterministic_result = None
        
        # Run planner version
        try:
            request_id = f"eval_{case_name}_planner"
            planner_result = run_system_health_graph_with_planner(snapshot, request_id=request_id)
        except Exception as e:
            print(f"Planner failed for case {case_name}: {e}")
            planner_result = None
        
        # Print comparison
        print_case_summary(case_name, snapshot, deterministic_result, planner_result, verbose)
    
    print("="*70)
    print("✅ Evaluation completed")
    print("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Offline evaluation: Compare deterministic vs ReAct planner"
    )
    parser.add_argument(
        "--use-planner-only",
        action="store_true",
        help="Only run planner version (skip deterministic)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed agent step information",
    )
    
    args = parser.parse_args()
    
    try:
        run_evaluation(use_planner_only=args.use_planner_only, verbose=args.verbose)
        return 0
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

