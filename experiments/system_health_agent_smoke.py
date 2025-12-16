#!/usr/bin/env python3
"""
system_health_agent_smoke.py - Smoke Test for System Health Agent

This script tests the system health agent workflow with 2-3 example snapshots:
- healthy case: should have band="healthy", hard_block=False
- degraded case: should have band="degraded", at least one strategy scenario improves
- critical case: should have band="critical", hard_block=True, at least one strategy scenario improves

Usage:
    python experiments/system_health_agent_smoke.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.schemas import SystemSnapshot
from services.fiqa_api.ops_copilot.graphs.system_health_graph import run_system_health_graph


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


def test_healthy_case():
    """Test healthy case: band should be 'healthy', hard_block should be False."""
    print("\n" + "="*80)
    print("TEST 1: Healthy System")
    print("="*80)
    
    snapshot = create_healthy_snapshot()
    print(f"Snapshot: {snapshot.service_name} ({snapshot.environment})")
    print(f"  CPU: {snapshot.cpu_pct:.1f}%, Mem: {snapshot.mem_pct:.1f}%, Latency: {snapshot.p95_latency_ms:.0f}ms")
    print(f"  Error rate: {snapshot.error_rate:.3f}, QPS: {snapshot.qps:.0f}, Disk: {snapshot.disk_pct:.1f}%")
    
    result = run_system_health_graph(snapshot, request_id="test_healthy")
    
    health_result = result["health_result"]
    print(f"\nHealth Result:")
    print(f"  Band: {health_result.band}")
    print(f"  Score: {health_result.score:.1f}")
    print(f"  Risk flags: {health_result.risk_flags}")
    print(f"  Hard block: {health_result.hard_block}")
    print(f"  Soft warning: {health_result.soft_warning}")
    
    # Assertions
    assert health_result.band == "healthy", f"Expected band='healthy', got '{health_result.band}'"
    assert health_result.hard_block == False, f"Expected hard_block=False, got {health_result.hard_block}"
    print("\n✅ PASS: Healthy case assertions passed")
    
    # Check strategy lab
    strategy_lab = result.get("strategy_lab")
    if strategy_lab:
        print(f"\nStrategy Lab: {len(strategy_lab.scenarios)} scenarios")
        if strategy_lab.scenarios:
            best = strategy_lab.scenarios[0]
            print(f"  Best scenario: {best.title} (band: {best.health_result.band}, score: {best.health_result.score:.1f})")
    
    # Check narrative
    narrative = result.get("narrative")
    if narrative:
        print(f"\nNarrative: {narrative[:200]}...")
    
    # Check recommended actions
    actions = result.get("recommended_actions", [])
    if actions:
        print(f"\nRecommended Actions:")
        for action in actions:
            print(f"  - {action}")
    
    # Check agent steps
    agent_steps = result.get("agent_steps", [])
    print(f"\nAgent Steps: {len(agent_steps)} steps")
    for step in agent_steps:
        print(f"  - {step.step_name}: {step.status} ({step.duration_ms:.1f}ms)")
    
    # Check action plan (should be None for healthy case)
    action_plan = result.get("action_plan")
    if action_plan:
        print(f"\nAction Plan: {len(action_plan.actions)} actions")
        for action in action_plan.actions:
            print(f"  - {action.summary} (severity: {action.severity})")


def test_degraded_case():
    """Test degraded case: band should be 'degraded', at least one strategy scenario should improve."""
    print("\n" + "="*80)
    print("TEST 2: Degraded System")
    print("="*80)
    
    snapshot = create_degraded_snapshot()
    print(f"Snapshot: {snapshot.service_name} ({snapshot.environment})")
    print(f"  CPU: {snapshot.cpu_pct:.1f}%, Mem: {snapshot.mem_pct:.1f}%, Latency: {snapshot.p95_latency_ms:.0f}ms")
    print(f"  Error rate: {snapshot.error_rate:.3f}, QPS: {snapshot.qps:.0f}, Disk: {snapshot.disk_pct:.1f}%")
    
    result = run_system_health_graph(snapshot, request_id="test_degraded")
    
    health_result = result["health_result"]
    print(f"\nHealth Result:")
    print(f"  Band: {health_result.band}")
    print(f"  Score: {health_result.score:.1f}")
    print(f"  Risk flags: {health_result.risk_flags}")
    print(f"  Hard block: {health_result.hard_block}")
    print(f"  Soft warning: {health_result.soft_warning}")
    
    # Assertions
    assert health_result.band in ("degraded", "warning"), f"Expected band in ('degraded', 'warning'), got '{health_result.band}'"
    print("\n✅ PASS: Degraded case band assertion passed")
    
    # Check safety suggestions (should be present for degraded/critical)
    safety_suggestions = result.get("safety_suggestions", [])
    print(f"\nSafety Suggestions: {len(safety_suggestions)} suggestions")
    if safety_suggestions:
        top_suggestion = safety_suggestions[0]
        print(f"  Top: {top_suggestion.title}")
        if top_suggestion.estimated_result:
            print(f"    Estimated band: {top_suggestion.estimated_result.band}, score: {top_suggestion.estimated_result.score:.1f}")
    
    # Check strategy lab - at least one scenario should improve
    strategy_lab = result.get("strategy_lab")
    assert strategy_lab is not None, "Expected strategy_lab to be present"
    assert len(strategy_lab.scenarios) > 0, "Expected at least one strategy scenario"
    
    baseline_score = strategy_lab.baseline_health.score
    improved_count = 0
    for scenario in strategy_lab.scenarios:
        if scenario.health_result.score > baseline_score:
            improved_count += 1
    
    print(f"\nStrategy Lab: {len(strategy_lab.scenarios)} scenarios")
    print(f"  Baseline score: {baseline_score:.1f}")
    print(f"  Improved scenarios: {improved_count}")
    for scenario in strategy_lab.scenarios[:3]:
        print(f"  - {scenario.title}: band={scenario.health_result.band}, score={scenario.health_result.score:.1f}")
    
    assert improved_count > 0, f"Expected at least one strategy scenario to improve score, but none did (baseline: {baseline_score:.1f})"
    print("\n✅ PASS: Degraded case strategy lab assertion passed")
    
    # Check narrative
    narrative = result.get("narrative")
    if narrative:
        print(f"\nNarrative: {narrative[:200]}...")
    
    # Check recommended actions
    actions = result.get("recommended_actions", [])
    if actions:
        print(f"\nRecommended Actions:")
        for action in actions:
            print(f"  - {action}")
    
    # Check action plan (should have actions for degraded case)
    action_plan = result.get("action_plan")
    assert action_plan is not None, "Expected action_plan to be present"
    assert len(action_plan.actions) >= 1, f"Expected at least 1 action, got {len(action_plan.actions)}"
    print(f"\nAction Plan Summary:")
    print(f"  Action plan has {len(action_plan.actions)} actions, "
          f"blocked={action_plan.num_actions_blocked}, "
          f"require_human={action_plan.num_actions_require_human}")
    print(f"\nAction Plan: {len(action_plan.actions)} actions")
    print(f"  num_actions_blocked: {action_plan.num_actions_blocked}")
    print(f"  num_actions_require_human: {action_plan.num_actions_require_human}")
    for action in action_plan.actions:
        print(f"  - {action.action_type}: {action.summary} (severity: {action.severity}, require_human: {action.require_human_approval})")
        if action.estimated_before_score is not None and action.estimated_after_score is not None:
            print(f"    Score improvement: {action.estimated_before_score:.1f} -> {action.estimated_after_score:.1f}")
        if action.reason:
            print(f"    Reason: {action.reason}")
    print("\n✅ PASS: Degraded case action plan assertion passed")


def test_critical_case():
    """Test critical case: band should be 'critical', hard_block should be True, at least one strategy scenario should improve."""
    print("\n" + "="*80)
    print("TEST 3: Critical System")
    print("="*80)
    
    snapshot = create_critical_snapshot()
    print(f"Snapshot: {snapshot.service_name} ({snapshot.environment})")
    print(f"  CPU: {snapshot.cpu_pct:.1f}%, Mem: {snapshot.mem_pct:.1f}%, Latency: {snapshot.p95_latency_ms:.0f}ms")
    print(f"  Error rate: {snapshot.error_rate:.3f}, QPS: {snapshot.qps:.0f}, Disk: {snapshot.disk_pct:.1f}%")
    
    result = run_system_health_graph(snapshot, request_id="test_critical")
    
    health_result = result["health_result"]
    print(f"\nHealth Result:")
    print(f"  Band: {health_result.band}")
    print(f"  Score: {health_result.score:.1f}")
    print(f"  Risk flags: {health_result.risk_flags}")
    print(f"  Hard block: {health_result.hard_block}")
    print(f"  Soft warning: {health_result.soft_warning}")
    
    # Assertions
    assert health_result.band == "critical", f"Expected band='critical', got '{health_result.band}'"
    assert health_result.hard_block == True, f"Expected hard_block=True, got {health_result.hard_block}"
    print("\n✅ PASS: Critical case assertions passed")
    
    # Check safety suggestions (should be present for degraded/critical)
    safety_suggestions = result.get("safety_suggestions", [])
    print(f"\nSafety Suggestions: {len(safety_suggestions)} suggestions")
    if safety_suggestions:
        top_suggestion = safety_suggestions[0]
        print(f"  Top: {top_suggestion.title}")
        if top_suggestion.estimated_result:
            print(f"    Estimated band: {top_suggestion.estimated_result.band}, score: {top_suggestion.estimated_result.score:.1f}")
    
    # Check strategy lab - at least one scenario should improve
    strategy_lab = result.get("strategy_lab")
    assert strategy_lab is not None, "Expected strategy_lab to be present"
    assert len(strategy_lab.scenarios) > 0, "Expected at least one strategy scenario"
    
    baseline_score = strategy_lab.baseline_health.score
    improved_count = 0
    for scenario in strategy_lab.scenarios:
        if scenario.health_result.score > baseline_score:
            improved_count += 1
    
    print(f"\nStrategy Lab: {len(strategy_lab.scenarios)} scenarios")
    print(f"  Baseline score: {baseline_score:.1f}")
    print(f"  Improved scenarios: {improved_count}")
    for scenario in strategy_lab.scenarios[:3]:
        print(f"  - {scenario.title}: band={scenario.health_result.band}, score={scenario.health_result.score:.1f}")
    
    assert improved_count > 0, f"Expected at least one strategy scenario to improve score, but none did (baseline: {baseline_score:.1f})"
    print("\n✅ PASS: Critical case strategy lab assertion passed")
    
    # Check narrative
    narrative = result.get("narrative")
    if narrative:
        print(f"\nNarrative: {narrative[:200]}...")
    
    # Check recommended actions
    actions = result.get("recommended_actions", [])
    if actions:
        print(f"\nRecommended Actions:")
        for action in actions:
            print(f"  - {action}")
        print(f"\n  First recommended action: {actions[0]}")
    
    # Check action plan (should have actions for critical case)
    action_plan = result.get("action_plan")
    assert action_plan is not None, "Expected action_plan to be present"
    assert len(action_plan.actions) >= 1, f"Expected at least 1 action, got {len(action_plan.actions)}"
    assert action_plan.hard_block == True, f"Expected hard_block=True in action plan, got {action_plan.hard_block}"
    print(f"\nAction Plan Summary:")
    print(f"  Action plan has {len(action_plan.actions)} actions, "
          f"blocked={action_plan.num_actions_blocked}, "
          f"require_human={action_plan.num_actions_require_human}")
    print(f"\nAction Plan: {len(action_plan.actions)} actions, hard_block={action_plan.hard_block}")
    print(f"  num_actions_blocked: {action_plan.num_actions_blocked}")
    print(f"  num_actions_require_human: {action_plan.num_actions_require_human}")
    
    # For critical case, all actions should require human approval
    if action_plan.actions:
        for action in action_plan.actions:
            assert action.require_human_approval == True, f"Expected require_human_approval=True for critical case, got {action.require_human_approval} for action {action.action_id}"
    
    for action in action_plan.actions:
        print(f"  - {action.action_type}: {action.summary} (severity: {action.severity}, require_human: {action.require_human_approval})")
        if action.estimated_before_score is not None and action.estimated_after_score is not None:
            print(f"    Score improvement: {action.estimated_before_score:.1f} -> {action.estimated_after_score:.1f}")
        if action.reason:
            print(f"    Reason: {action.reason}")
    
    # Print action plan summary for eyeball
    print(f"\nAction Plan Summary:")
    print(f"  Total actions: {len(action_plan.actions)}")
    print(f"  Actions blocked: {action_plan.num_actions_blocked}")
    print(f"  Actions requiring human approval: {action_plan.num_actions_require_human}")
    if action_plan.notes:
        print(f"  Notes: {len(action_plan.notes)} note(s)")
        for note in action_plan.notes[:3]:  # Show first 3 notes
            print(f"    - {note}")
    
    print("\n✅ PASS: Critical case action plan assertion passed")


def main():
    """Run all smoke tests."""
    print("="*80)
    print("System Health Agent Smoke Test")
    print("="*80)
    
    try:
        test_healthy_case()
        test_degraded_case()
        test_critical_case()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        return 0
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

