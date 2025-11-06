#!/usr/bin/env python3
"""
Canary Deployment Demo Script

This script demonstrates the canary deployment system with simulated search requests
and automatic rollback on SLO violations.
"""

import sys
import time
import random
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.canary import (
    get_config_manager, get_canary_executor, get_audit_logger,
    get_metrics_collector, get_slo_monitor
)


def simulate_search_requests(canary_executor, num_requests: int = 100):
    """
    Simulate search requests with varying performance characteristics.
    
    Args:
        canary_executor: CanaryExecutor instance
        num_requests: Number of requests to simulate
    """
    print(f"Simulating {num_requests} search requests...")
    
    queries = [
        "machine learning algorithms",
        "neural network architecture",
        "deep learning frameworks",
        "computer vision applications",
        "natural language processing",
        "reinforcement learning",
        "data preprocessing techniques",
        "model evaluation metrics",
        "hyperparameter tuning",
        "feature engineering"
    ]
    
    for i in range(num_requests):
        # Select random query
        query = random.choice(queries)
        
        try:
            # Execute search with canary traffic splitting
            results, config_used = canary_executor.execute_search(
                query=query,
                collection_name="documents",
                trace_id=f"demo_{i:04d}"
            )
            
            if i % 10 == 0:
                print(f"  Request {i+1:3d}: '{query[:30]}...' -> {config_used} ({len(results)} results)")
        
        except Exception as e:
            print(f"  Request {i+1:3d}: ERROR - {e}")
        
        # Small delay between requests
        time.sleep(0.1)
    
    print(f"Completed {num_requests} search requests")


def simulate_slo_violation(canary_executor, config_name: str, num_requests: int = 50):
    """
    Simulate SLO violations by creating slow requests.
    
    Args:
        canary_executor: CanaryExecutor instance
        config_name: Configuration name to simulate violations for
        num_requests: Number of requests to simulate
    """
    print(f"Simulating SLO violations for {config_name}...")
    
    # Temporarily modify the search execution to simulate slow responses
    # This is a simplified simulation - in reality, SLO violations would come
    # from actual performance issues
    
    for i in range(num_requests):
        query = f"slow query {i}"
        
        try:
            # Execute search
            results, config_used = canary_executor.execute_search(
                query=query,
                collection_name="documents",
                trace_id=f"slow_{i:04d}"
            )
            
            if i % 10 == 0:
                print(f"  Slow request {i+1:3d}: {config_used} ({len(results)} results)")
        
        except Exception as e:
            print(f"  Slow request {i+1:3d}: ERROR - {e}")
        
        # Longer delay to simulate slow responses
        time.sleep(0.2)
    
    print(f"Completed {num_requests} slow requests")


def main():
    """Main demo function."""
    print("Canary Deployment System Demo")
    print("=" * 50)
    
    # Initialize components
    config_manager = get_config_manager()
    canary_executor = get_canary_executor()
    audit_logger = get_audit_logger()
    metrics_collector = get_metrics_collector()
    slo_monitor = get_slo_monitor()
    
    print("✓ Initialized canary deployment components")
    
    # Show available configurations
    print("\nAvailable Configurations:")
    presets = config_manager.list_presets()
    for preset in presets:
        print(f"  • {preset}")
    
    # Check if we have candidate configurations
    candidate_configs = [p for p in presets if p.startswith('candidate_')]
    if not candidate_configs:
        print("\nNo candidate configurations found. Creating one...")
        try:
            config = config_manager.create_config_from_current(
                "candidate_demo",
                "Demo candidate configuration for canary deployment"
            )
            config_manager.save_preset(config)
            candidate_configs = ["candidate_demo"]
            print("✓ Created demo candidate configuration")
        except Exception as e:
            print(f"✗ Failed to create demo configuration: {e}")
            return
    
    # Select a candidate configuration
    candidate_config = candidate_configs[0]
    print(f"\nUsing candidate configuration: {candidate_config}")
    
    # Start canary deployment
    print(f"\nStarting canary deployment with {candidate_config}...")
    try:
        result = canary_executor.start_canary(candidate_config)
        print(f"✓ Canary deployment started: {result.deployment_id}")
        print(f"  Traffic split: {result.traffic_split}")
        print(f"  Start time: {result.start_time}")
    except Exception as e:
        print(f"✗ Failed to start canary deployment: {e}")
        return
    
    # Log audit event
    audit_logger.log_canary_start(
        deployment_id=result.deployment_id,
        candidate_config=candidate_config,
        traffic_split=result.traffic_split,
        user_id="demo_user"
    )
    
    # Simulate normal traffic
    print("\nPhase 1: Simulating normal traffic...")
    simulate_search_requests(canary_executor, num_requests=50)
    
    # Check metrics
    print("\nMetrics after normal traffic:")
    metrics_collector.get_completed_buckets()  # Process any pending buckets
    status = canary_executor.get_current_status()
    print(f"  Total requests: {status['total_requests']}")
    
    # Simulate some SLO violations
    print("\nPhase 2: Simulating SLO violations...")
    simulate_slo_violation(canary_executor, candidate_config, num_requests=20)
    
    # Process metrics and check for violations
    print("\nProcessing metrics and checking SLO violations...")
    completed_buckets = metrics_collector.get_completed_buckets()
    violations = slo_monitor.process_buckets(completed_buckets)
    
    if violations:
        print(f"  Detected {len(violations)} SLO violations")
        for violation in violations:
            print(f"    - {violation.rule_name}: {violation.metric_value} vs {violation.threshold}")
    
    # Show final status
    print("\nFinal Status:")
    final_status = canary_executor.get_current_status()
    print(f"  Deployment ID: {final_status['deployment_id']}")
    print(f"  Status: {final_status['status']}")
    print(f"  Total requests: {final_status['total_requests']}")
    print(f"  Duration: {final_status['duration_seconds']:.1f} seconds")
    
    # Show metrics summary
    print("\nMetrics Summary:")
    active_summary = metrics_collector.get_summary_stats(
        final_status['active_config'], window_minutes=10
    )
    candidate_summary = metrics_collector.get_summary_stats(
        final_status['candidate_config'], window_minutes=10
    )
    
    print(f"  Active config ({active_summary['config_name']}):")
    print(f"    Responses: {active_summary['total_responses']}")
    print(f"    Avg P95: {active_summary['avg_p95_ms']:.2f} ms")
    print(f"    Avg Recall: {active_summary['avg_recall_at_10']:.3f}")
    print(f"    SLO violations: {active_summary['total_slo_violations']}")
    
    print(f"  Candidate config ({candidate_summary['config_name']}):")
    print(f"    Responses: {candidate_summary['total_responses']}")
    print(f"    Avg P95: {candidate_summary['avg_p95_ms']:.2f} ms")
    print(f"    Avg Recall: {candidate_summary['avg_recall_at_10']:.3f}")
    print(f"    SLO violations: {candidate_summary['total_slo_violations']}")
    
    # Ask user what to do
    print("\nDemo completed. What would you like to do?")
    print("1. Promote candidate configuration")
    print("2. Rollback to last good configuration")
    print("3. Export results and exit")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\nPromoting candidate configuration...")
            result = canary_executor.stop_canary(promote=True)
            audit_logger.log_canary_promote(
                deployment_id=result.deployment_id,
                candidate_config=result.candidate_config,
                metrics_summary=result.metrics_summary,
                user_id="demo_user"
            )
            print(f"✓ Candidate configuration promoted!")
        
        elif choice == "2":
            print("\nRolling back to last good configuration...")
            result = canary_executor.stop_canary(promote=False, reason="Demo rollback")
            audit_logger.log_canary_rollback(
                deployment_id=result.deployment_id,
                candidate_config=result.candidate_config,
                reason=result.rollback_reason or "Demo rollback",
                metrics_summary=result.metrics_summary,
                user_id="demo_user"
            )
            print(f"✓ Rolled back to last good configuration!")
        
        elif choice == "3":
            print("\nStopping canary deployment...")
            canary_executor.stop_canary(promote=False, reason="Demo completed")
        
        else:
            print("Invalid choice. Stopping canary deployment...")
            canary_executor.stop_canary(promote=False, reason="Demo completed")
    
    except KeyboardInterrupt:
        print("\nDemo interrupted. Stopping canary deployment...")
        canary_executor.stop_canary(promote=False, reason="Demo interrupted")
    
    # Export results
    print("\nExporting results...")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path("reports/canary")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Export canary result
        result_file = output_dir / f"demo_canary_result_{timestamp}.json"
        canary_executor.export_result_to_json(str(result_file))
        print(f"✓ Canary result exported to: {result_file}")
        
        # Export metrics
        metrics_file = output_dir / f"demo_metrics_{timestamp}.json"
        canary_executor.get_metrics_export(str(metrics_file))
        print(f"✓ Metrics exported to: {metrics_file}")
        
        # Export audit events
        audit_file = output_dir / f"demo_audit_{timestamp}.json"
        audit_logger.export_audit_events(str(audit_file))
        print(f"✓ Audit events exported to: {audit_file}")
        
    except Exception as e:
        print(f"✗ Failed to export results: {e}")
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    main()


