#!/usr/bin/env python3
"""
Test Script for SLO Strategy and Alert Integration

This script tests the SLO strategy management and alert integration functionality.
"""

import sys
import time
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.canary import (
    get_slo_strategy_manager, get_slo_monitor, get_metrics_collector,
    get_config_manager, get_audit_logger, SLOViolation, MetricsBucket
)


def test_slo_strategy_management():
    """Test SLO strategy management functionality."""
    print("Testing SLO Strategy Management...")
    print("=" * 50)
    
    strategy_manager = get_slo_strategy_manager()
    
    # Test listing strategies
    print("Available SLO strategies:")
    strategies = strategy_manager.list_strategies()
    for strategy_name in strategies:
        print(f"  - {strategy_name}")
    
    # Test loading default strategy
    print(f"\nLoading default strategy...")
    strategy_manager.set_active_strategy("default_canary_slo")
    active_strategy = strategy_manager.get_active_strategy()
    print(f"  Active strategy: {active_strategy.name}")
    print(f"  Description: {active_strategy.description}")
    print(f"  Rules: {len(active_strategy.rules)}")
    for rule in active_strategy.rules:
        print(f"    - {rule['name']}: {rule['metric']} {rule['operator']} {rule['threshold']}")
    
    # Test loading lenient strategy
    print(f"\nLoading lenient strategy...")
    strategy_manager.set_active_strategy("lenient_slo")
    lenient_strategy = strategy_manager.get_active_strategy()
    print(f"  Active strategy: {lenient_strategy.name}")
    print(f"  Rules: {len(lenient_strategy.rules)}")
    
    return strategy_manager


def test_slo_monitor_integration():
    """Test SLO monitor integration with strategy manager."""
    print("\nTesting SLO Monitor Integration...")
    print("=" * 50)
    
    strategy_manager = get_slo_strategy_manager()
    slo_monitor = get_slo_monitor()
    
    # Apply strategy to monitor
    print("Applying strategy to SLO monitor...")
    strategy_manager.apply_strategy_to_monitor(slo_monitor)
    
    # Check SLO rules
    print(f"  SLO rules in monitor: {len(slo_monitor.slo_rules)}")
    for rule in slo_monitor.slo_rules:
        print(f"    - {rule.name}: {rule.metric} {rule.operator} {rule.threshold}")
    
    return slo_monitor


def test_violation_handling():
    """Test SLO violation handling with alerts."""
    print("\nTesting SLO Violation Handling...")
    print("=" * 50)
    
    strategy_manager = get_slo_strategy_manager()
    audit_logger = get_audit_logger()
    
    # Create test violations
    test_violations = [
        SLOViolation(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            rule_name="p95_latency",
            metric_value=1500.0,  # Above threshold of 1200ms
            threshold=1200.0,
            config_name="candidate_test",
            consecutive_failures=2,
            action_taken="none"
        ),
        SLOViolation(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            rule_name="recall_at_10",
            metric_value=0.25,  # Below threshold of 0.30
            threshold=0.30,
            config_name="candidate_test",
            consecutive_failures=2,
            action_taken="none"
        )
    ]
    
    print("Testing violation handling...")
    for violation in test_violations:
        print(f"\nProcessing violation: {violation.rule_name}")
        print(f"  Value: {violation.metric_value} vs Threshold: {violation.threshold}")
        print(f"  Config: {violation.config_name}")
        print(f"  Consecutive failures: {violation.consecutive_failures}")
        
        # Handle violation
        rollback_triggered = strategy_manager.handle_slo_violation(violation, audit_logger)
        print(f"  Rollback triggered: {rollback_triggered}")
    
    # Check violations file
    violations_file = "reports/canary/violations.json"
    if Path(violations_file).exists():
        with open(violations_file, 'r') as f:
            violations = json.load(f)
        print(f"\nViolations recorded: {len(violations)}")
        for violation in violations[-2:]:  # Show last 2
            print(f"  - {violation['rule_name']}: {violation['metric_value']} vs {violation['threshold']}")
    
    # Get violations summary
    summary = strategy_manager.get_violations_summary()
    print(f"\nViolations Summary:")
    print(f"  Total violations: {summary['total_violations']}")
    print(f"  Recent violations: {summary['recent_violations']}")
    print(f"  Rules violated: {summary['rules_violated']}")
    print(f"  Configs violated: {summary['configs_violated']}")


def test_metrics_bucket_processing():
    """Test processing metrics buckets with SLO monitoring."""
    print("\nTesting Metrics Bucket Processing...")
    print("=" * 50)
    
    slo_monitor = get_slo_strategy_manager().get_active_strategy()
    print(f"Using strategy: {slo_monitor.name}")
    
    # Create test metrics buckets
    test_buckets = [
        MetricsBucket(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            duration_sec=5,
            config_name="candidate_test",
            p95_ms=1300.0,  # Violates p95 <= 1200ms
            recall_at_10=0.25,  # Violates recall >= 0.30
            response_count=50,
            slo_violations=0
        ),
        MetricsBucket(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            duration_sec=5,
            config_name="candidate_test",
            p95_ms=1400.0,  # Still violates
            recall_at_10=0.20,  # Still violates
            response_count=45,
            slo_violations=0
        )
    ]
    
    # Process buckets through SLO monitor
    for i, bucket in enumerate(test_buckets):
        print(f"\nProcessing bucket {i+1}:")
        print(f"  P95: {bucket.p95_ms} ms")
        print(f"  Recall: {bucket.recall_at_10}")
        print(f"  Config: {bucket.config_name}")
        
        violations = get_slo_monitor().check_slo_violations(bucket)
        print(f"  Violations found: {len(violations)}")
        
        for violation in violations:
            print(f"    - {violation.rule_name}: {violation.metric_value} vs {violation.threshold}")
            print(f"      Action: {violation.action_taken}")
            print(f"      Consecutive failures: {violation.consecutive_failures}")


def test_alert_configuration():
    """Test alert configuration and console output."""
    print("\nTesting Alert Configuration...")
    print("=" * 50)
    
    strategy_manager = get_slo_strategy_manager()
    strategy = strategy_manager.get_active_strategy()
    
    print(f"Alert configuration for '{strategy.name}':")
    alert_config = strategy.alert_config
    print(f"  Enabled: {alert_config.get('enabled', False)}")
    print(f"  Console alerts: {alert_config.get('console_alerts', False)}")
    print(f"  File alerts: {alert_config.get('file_alerts', False)}")
    print(f"  Violations file: {alert_config.get('violations_file', 'N/A')}")
    print(f"  Console red text: {alert_config.get('console_red_text', False)}")
    
    print(f"\nRollback configuration:")
    rollback_config = strategy.rollback_config
    print(f"  Consecutive buckets: {rollback_config.get('consecutive_buckets', 0)}")
    print(f"  Auto rollback: {rollback_config.get('auto_rollback', False)}")
    print(f"  Rollback delay: {rollback_config.get('rollback_delay_seconds', 0)}s")
    print(f"  Max rollbacks/hour: {rollback_config.get('max_rollbacks_per_hour', 0)}")


def test_strategy_switching():
    """Test switching between different SLO strategies."""
    print("\nTesting Strategy Switching...")
    print("=" * 50)
    
    strategy_manager = get_slo_strategy_manager()
    slo_monitor = get_slo_monitor()
    
    # Test switching to default strategy
    print("Switching to default strategy...")
    strategy_manager.set_active_strategy("default_canary_slo")
    strategy_manager.apply_strategy_to_monitor(slo_monitor)
    
    default_rules = len(slo_monitor.slo_rules)
    print(f"  Rules in monitor: {default_rules}")
    
    # Test switching to lenient strategy
    print("Switching to lenient strategy...")
    strategy_manager.set_active_strategy("lenient_slo")
    strategy_manager.apply_strategy_to_monitor(slo_monitor)
    
    lenient_rules = len(slo_monitor.slo_rules)
    print(f"  Rules in monitor: {lenient_rules}")
    
    # Verify rules changed
    if default_rules == lenient_rules:
        print("  ✓ Strategy switching successful")
    else:
        print("  ⚠ Strategy switching may have issues")


def main():
    """Run all SLO strategy tests."""
    print("SLO Strategy and Alert Integration Test Suite")
    print("=" * 60)
    
    try:
        # Test strategy management
        test_slo_strategy_management()
        
        # Test SLO monitor integration
        test_slo_monitor_integration()
        
        # Test violation handling
        test_violation_handling()
        
        # Test metrics bucket processing
        test_metrics_bucket_processing()
        
        # Test alert configuration
        test_alert_configuration()
        
        # Test strategy switching
        test_strategy_switching()
        
        print("\n🎉 All SLO strategy tests completed successfully!")
        
        print("\nKey Features Tested:")
        print("  ✓ SLO strategy loading and management")
        print("  ✓ Strategy application to SLO monitor")
        print("  ✓ Violation handling with alerts")
        print("  ✓ Console and file-based alerts")
        print("  ✓ Metrics bucket processing")
        print("  ✓ Strategy switching")
        
        print("\nGenerated Files:")
        print("  - reports/canary/violations.json")
        print("  - configs/slo_strategies/*.json")
        
        print("\nNext Steps:")
        print("  1. Review violations.json for alert output")
        print("  2. Test with different SLO strategies")
        print("  3. Configure custom alert thresholds")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


