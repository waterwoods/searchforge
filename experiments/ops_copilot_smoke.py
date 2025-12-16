#!/usr/bin/env python3
"""
ops_copilot_smoke.py - Smoke Test for Ops Copilot

Hard-coded test cases to verify basic functionality:
1. Healthy prod service
2. High-latency & high-error prod service (should be critical with hard_block=True)
3. Medium-load with some warning (band warning or degraded with soft_warning=True)

For each case:
- Print health band, score, risk flags
- Run strategy lab, print scenario titles and whether any scenario improved band/score

Exit with non-zero code if:
- Any snapshot fails unexpectedly
- Critical case does not produce any improved scenario
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot import (
    run_system_health_check,
    run_system_strategy_lab,
    SystemSnapshot,
)


def test_case_1_healthy():
    """Test case 1: Healthy prod service"""
    print("\n" + "=" * 80)
    print("Test Case 1: Healthy Prod Service")
    print("=" * 80)
    
    snapshot = SystemSnapshot(
        service_name="api-gateway",
        environment="prod",
        cpu_pct=35.0,
        mem_pct=40.0,
        p95_latency_ms=150.0,
        error_rate=0.001,  # 0.1%
        qps=500.0,
        disk_pct=45.0,
        timestamp=datetime.utcnow(),
        region="us-east-1",
        tags={"version": "v1.2.3"},
    )
    
    health_result = run_system_health_check(snapshot)
    
    print(f"Health Band: {health_result.band}")
    print(f"Health Score: {health_result.score:.1f}")
    print(f"Risk Flags: {health_result.risk_flags}")
    print(f"Hard Block: {health_result.hard_block}")
    print(f"Soft Warning: {health_result.soft_warning}")
    
    # Assertions
    assert health_result.band == "healthy", f"Expected 'healthy', got '{health_result.band}'"
    assert health_result.hard_block == False, f"Expected hard_block=False, got {health_result.hard_block}"
    assert health_result.score >= 70, f"Expected score >= 70, got {health_result.score}"
    
    print("✅ Test Case 1 PASSED")
    return True


def test_case_2_critical():
    """Test case 2: High-latency & high-error prod service (should be critical)"""
    print("\n" + "=" * 80)
    print("Test Case 2: Critical Prod Service (High Latency & High Error)")
    print("=" * 80)
    
    snapshot = SystemSnapshot(
        service_name="payment-service",
        environment="prod",
        cpu_pct=92.0,  # Critical
        mem_pct=70.0,  # Not critical, so improvements can help
        p95_latency_ms=900.0,  # Critical
        error_rate=0.06,  # 6% - Critical
        qps=3000.0,
        disk_pct=70.0,  # Not critical, so improvements can help
        timestamp=datetime.utcnow(),
        region="us-west-2",
        tags={"version": "v2.0.1"},
    )
    
    health_result = run_system_health_check(snapshot)
    
    print(f"Health Band: {health_result.band}")
    print(f"Health Score: {health_result.score:.1f}")
    print(f"Risk Flags: {health_result.risk_flags}")
    print(f"Hard Block: {health_result.hard_block}")
    print(f"Soft Warning: {health_result.soft_warning}")
    
    # Assertions
    assert health_result.band == "critical", f"Expected 'critical', got '{health_result.band}'"
    assert health_result.hard_block == True, f"Expected hard_block=True, got {health_result.hard_block}"
    assert "high_error_rate" in health_result.risk_flags, "Expected 'high_error_rate' in risk_flags"
    
    # Run strategy lab
    print("\nRunning Strategy Lab...")
    strategy_lab = run_system_strategy_lab(snapshot)
    
    print(f"Baseline Band: {strategy_lab.baseline_health.band}")
    print(f"Baseline Score: {strategy_lab.baseline_health.score:.1f}")
    print(f"Number of Scenarios: {len(strategy_lab.scenarios)}")
    
    # Check for improvements
    band_order = {"healthy": 0, "warning": 1, "degraded": 2, "critical": 3}
    baseline_order = band_order.get(strategy_lab.baseline_health.band, 999)
    baseline_score = strategy_lab.baseline_health.score
    
    has_improvement = False
    for scenario in strategy_lab.scenarios:
        print(f"\n  Scenario: {scenario.title}")
        print(f"    Band: {scenario.health_result.band}")
        print(f"    Score: {scenario.health_result.score:.1f}")
        
        scenario_order = band_order.get(scenario.health_result.band, 999)
        is_better = (
            scenario_order < baseline_order or
            (scenario_order == baseline_order and scenario.health_result.score > baseline_score)
        )
        
        if is_better:
            has_improvement = True
            print(f"    ✅ IMPROVEMENT")
        else:
            print(f"    ❌ No improvement")
    
    assert has_improvement, "Expected at least one scenario to improve band or score"
    
    print("\n✅ Test Case 2 PASSED")
    return True


def test_case_3_warning():
    """Test case 3: Medium-load with some warning"""
    print("\n" + "=" * 80)
    print("Test Case 3: Medium-Load Service with Warning")
    print("=" * 80)
    
    snapshot = SystemSnapshot(
        service_name="user-service",
        environment="prod",
        cpu_pct=75.0,  # Warning level
        mem_pct=60.0,
        p95_latency_ms=350.0,  # Warning level
        error_rate=0.015,  # 1.5% - warning level
        qps=1500.0,
        disk_pct=70.0,
        timestamp=datetime.utcnow(),
        region="eu-west-1",
        tags={"version": "v1.5.0"},
    )
    
    health_result = run_system_health_check(snapshot)
    
    print(f"Health Band: {health_result.band}")
    print(f"Health Score: {health_result.score:.1f}")
    print(f"Risk Flags: {health_result.risk_flags}")
    print(f"Hard Block: {health_result.hard_block}")
    print(f"Soft Warning: {health_result.soft_warning}")
    
    # Assertions
    assert health_result.band in ("warning", "degraded"), f"Expected 'warning' or 'degraded', got '{health_result.band}'"
    assert health_result.soft_warning == True, f"Expected soft_warning=True, got {health_result.soft_warning}"
    assert len(health_result.risk_flags) > 0, "Expected at least one risk flag"
    
    # Run strategy lab
    print("\nRunning Strategy Lab...")
    strategy_lab = run_system_strategy_lab(snapshot)
    
    print(f"Baseline Band: {strategy_lab.baseline_health.band}")
    print(f"Baseline Score: {strategy_lab.baseline_health.score:.1f}")
    print(f"Number of Scenarios: {len(strategy_lab.scenarios)}")
    
    for scenario in strategy_lab.scenarios:
        print(f"\n  Scenario: {scenario.title}")
        print(f"    Band: {scenario.health_result.band}")
        print(f"    Score: {scenario.health_result.score:.1f}")
    
    print("\n✅ Test Case 3 PASSED")
    return True


def main():
    """Main entry point."""
    print("=" * 80)
    print("Ops Copilot Smoke Test")
    print("=" * 80)
    
    all_passed = True
    
    try:
        # Test Case 1: Healthy
        test_case_1_healthy()
    except Exception as e:
        print(f"\n❌ Test Case 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        # Test Case 2: Critical
        test_case_2_critical()
    except Exception as e:
        print(f"\n❌ Test Case 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        # Test Case 3: Warning
        test_case_3_warning()
    except Exception as e:
        print(f"\n❌ Test Case 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

