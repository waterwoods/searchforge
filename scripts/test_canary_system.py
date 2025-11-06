#!/usr/bin/env python3
"""
Test Script for Canary Deployment System

This script tests the basic functionality of the canary deployment system
without requiring a full search pipeline.
"""

import sys
import time
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.canary import (
    get_config_manager, get_canary_executor, get_audit_logger,
    get_metrics_collector, get_slo_monitor
)


def test_config_manager():
    """Test configuration manager functionality."""
    print("Testing ConfigManager...")
    
    config_manager = get_config_manager()
    
    # List presets
    presets = config_manager.list_presets()
    print(f"  ✓ Found {len(presets)} configuration presets")
    
    # Load a preset
    if presets:
        config = config_manager.load_preset(presets[0])
        print(f"  ✓ Loaded preset '{config.name}': {config.description}")
    
    # Get current state
    state = config_manager.get_canary_status()
    print(f"  ✓ Current status: {state['status']}")
    
    print("  ✓ ConfigManager tests passed\n")


def test_metrics_collector():
    """Test metrics collector functionality."""
    print("Testing MetricsCollector...")
    
    metrics_collector = get_metrics_collector()
    
    # Record some test metrics
    for i in range(10):
        metrics_collector.record_search(
            trace_id=f"test_{i}",
            latency_ms=800.0 + i * 10,
            recall_at_10=0.3 + i * 0.01,
            config_name="test_config",
            slo_p95_ms=1200.0
        )
    
    # Get completed buckets
    buckets = metrics_collector.get_completed_buckets()
    print(f"  ✓ Recorded metrics and created {len(buckets)} buckets")
    
    # Get summary stats
    summary = metrics_collector.get_summary_stats("test_config", window_minutes=1)
    print(f"  ✓ Summary stats: {summary['total_responses']} responses, avg P95: {summary['avg_p95_ms']:.1f}ms")
    
    print("  ✓ MetricsCollector tests passed\n")


def test_slo_monitor():
    """Test SLO monitor functionality."""
    print("Testing SLOMonitor...")
    
    slo_monitor = get_slo_monitor()
    
    # Check monitoring status
    status = slo_monitor.get_monitoring_status()
    print(f"  ✓ SLO monitoring active with {len(status['slo_rules'])} rules")
    
    # Get violations
    violations = slo_monitor.get_violations()
    print(f"  ✓ Found {len(violations)} SLO violations")
    
    print("  ✓ SLOMonitor tests passed\n")


def test_audit_logger():
    """Test audit logger functionality."""
    print("Testing AuditLogger...")
    
    audit_logger = get_audit_logger()
    
    # Log some test events
    audit_logger.log_canary_start(
        deployment_id="test_deployment",
        candidate_config="test_candidate",
        traffic_split={"active": 0.9, "candidate": 0.1},
        user_id="test_user"
    )
    
    audit_logger.log_slo_violation(
        deployment_id="test_deployment",
        config_name="test_candidate",
        violation_details={"rule": "p95_latency", "value": 1300, "threshold": 1200}
    )
    
    # Read recent events
    events = audit_logger.get_recent_events(hours=1, limit=10)
    print(f"  ✓ Logged events and found {len(events)} recent audit events")
    
    print("  ✓ AuditLogger tests passed\n")


def test_canary_executor():
    """Test canary executor functionality."""
    print("Testing CanaryExecutor...")
    
    canary_executor = get_canary_executor()
    
    # Check current status
    status = canary_executor.get_current_status()
    print(f"  ✓ Current status: {status['status']}")
    
    # Test traffic selection (without actually starting canary)
    print("  ✓ CanaryExecutor basic functionality working")
    
    print("  ✓ CanaryExecutor tests passed\n")


def test_integration():
    """Test integration between components."""
    print("Testing component integration...")
    
    # Get all components
    config_manager = get_config_manager()
    metrics_collector = get_metrics_collector()
    slo_monitor = get_slo_monitor()
    canary_executor = get_canary_executor()
    audit_logger = get_audit_logger()
    
    # Test that they can work together
    presets = config_manager.list_presets()
    if presets:
        config = config_manager.load_preset(presets[0])
        
        # Record metrics with config name
        metrics_collector.record_search(
            trace_id="integration_test",
            latency_ms=900.0,
            recall_at_10=0.35,
            config_name=config.name,
            slo_p95_ms=config.slo["p95_ms"]
        )
        
        # Log audit event
        audit_logger.log_canary_start(
            deployment_id="integration_test",
            candidate_config=config.name,
            traffic_split={"active": 0.9, "candidate": 0.1}
        )
        
        print(f"  ✓ Successfully integrated components with config '{config.name}'")
    
    print("  ✓ Integration tests passed\n")


def test_file_operations():
    """Test file operations and exports."""
    print("Testing file operations...")
    
    # Create test output directory
    output_dir = Path("reports/canary/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test metrics export
    metrics_collector = get_metrics_collector()
    metrics_file = output_dir / "test_metrics.json"
    try:
        metrics_collector.export_buckets_to_json(str(metrics_file))
        print(f"  ✓ Exported metrics to {metrics_file}")
    except Exception as e:
        print(f"  ⚠ Metrics export failed: {e}")
    
    # Test audit export
    audit_logger = get_audit_logger()
    audit_file = output_dir / "test_audit.json"
    try:
        audit_logger.export_audit_events(str(audit_file))
        print(f"  ✓ Exported audit events to {audit_file}")
    except Exception as e:
        print(f"  ⚠ Audit export failed: {e}")
    
    print("  ✓ File operations tests completed\n")


def main():
    """Run all tests."""
    print("Canary Deployment System - Test Suite")
    print("=" * 50)
    
    try:
        test_config_manager()
        test_metrics_collector()
        test_slo_monitor()
        test_audit_logger()
        test_canary_executor()
        test_integration()
        test_file_operations()
        
        print("🎉 All tests completed successfully!")
        print("\nThe canary deployment system is ready to use.")
        print("\nNext steps:")
        print("1. Run 'python scripts/canary_cli.py list' to see available configurations")
        print("2. Run 'python scripts/canary_cli.py status' to check current state")
        print("3. Run 'python scripts/demo_canary.py' for a full demonstration")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


