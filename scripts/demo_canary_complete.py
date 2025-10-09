#!/usr/bin/env python3
"""
Complete Canary Deployment Demo Script

This script provides a one-click demonstration of the complete canary deployment system.
"""

import sys
import time
import subprocess
import webbrowser
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.canary import (
    get_config_manager, get_canary_executor, get_ab_evaluator,
    get_metrics_collector, get_slo_monitor, get_audit_logger,
    generate_observability_package, get_config_selector
)


class CanaryDemo:
    """
    Complete canary deployment demonstration.
    
    Features:
    - Automated canary deployment lifecycle
    - Traffic simulation with A/B testing
    - SLO monitoring and violation simulation
    - Automatic rollback/promotion decision
    - Comprehensive reporting and visualization
    """
    
    def __init__(self):
        """Initialize the demo."""
        self.config_manager = get_config_manager()
        self.canary_executor = get_canary_executor()
        self.ab_evaluator = get_ab_evaluator()
        self.metrics_collector = get_metrics_collector()
        self.slo_monitor = get_slo_monitor()
        self.audit_logger = get_audit_logger()
        
        self.demo_duration = 180  # 3 minutes
        self.traffic_rate = 10  # requests per second
        
        print("🚀 Canary Deployment Demo Initialized")
        print("=" * 50)
    
    def run_demo(self):
        """Run the complete canary deployment demo."""
        try:
            print("Starting Complete Canary Deployment Demo...")
            print(f"Duration: {self.demo_duration} seconds")
            print(f"Traffic Rate: {self.traffic_rate} requests/second")
            print()
            
            # Step 1: Setup
            self._setup_demo()
            
            # Step 2: Start canary deployment
            self._start_canary()
            
            # Step 3: Simulate traffic
            self._simulate_traffic()
            
            # Step 4: Monitor and decide
            self._monitor_and_decide()
            
            # Step 5: Generate reports
            self._generate_reports()
            
            # Step 6: Cleanup and summary
            self._cleanup_and_summary()
            
            print("\n🎉 Demo completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
            self._emergency_cleanup()
            sys.exit(1)
    
    def _setup_demo(self):
        """Setup demo environment."""
        print("📋 Step 1: Setting up demo environment...")
        
        # Check available configurations
        configs = self.config_manager.list_presets()
        print(f"  Available configurations: {configs}")
        
        # Ensure we have candidate configurations
        if "candidate_high_recall" not in configs:
            print("  ⚠️  candidate_high_recall not found, using last_good")
            candidate_config = "last_good"
        else:
            candidate_config = "candidate_high_recall"
        
        print(f"  Selected candidate: {candidate_config}")
        
        # Reset any existing canary deployments
        status = self.config_manager.get_canary_status()
        if status['status'] == 'running':
            print("  Stopping existing canary deployment...")
            self.canary_executor.stop_canary()
        
        print("  ✓ Demo environment ready")
        print()
    
    def _start_canary(self):
        """Start canary deployment."""
        print("🚀 Step 2: Starting canary deployment...")
        
        # Start canary with candidate configuration
        candidate_config = "candidate_high_recall"
        result = self.canary_executor.start_canary(candidate_config)
        
        if result.success:
            print(f"  ✓ Canary started successfully!")
            print(f"  Deployment ID: {result.deployment_id}")
            print(f"  Traffic Split: 90% last_good, 10% {candidate_config}")
            print(f"  Start Time: {result.start_time}")
        else:
            raise Exception(f"Failed to start canary: {result.error}")
        
        print()
    
    def _simulate_traffic(self):
        """Simulate traffic with A/B testing."""
        print("🌊 Step 3: Simulating traffic with A/B testing...")
        
        total_requests = self.demo_duration * self.traffic_rate
        print(f"  Simulating {total_requests} requests over {self.demo_duration} seconds...")
        
        start_time = time.time()
        request_count = 0
        
        # Simulate traffic in batches
        batch_size = 10
        batch_interval = 1.0  # 1 second between batches
        
        while time.time() - start_time < self.demo_duration:
            batch_start = time.time()
            
            # Generate batch of requests
            for i in range(batch_size):
                if time.time() - start_time >= self.demo_duration:
                    break
                
                trace_id = f"demo_trace_{request_count:06d}"
                request_count += 1
                
                # Simulate different performance characteristics
                if request_count % 10 < 2:  # 20% get candidate (simulate 10% split)
                    config_name = "candidate_high_recall"
                    latency_ms = 780 + (request_count % 5) * 20  # 780-860ms (better)
                    recall_at_10 = 0.36 + (request_count % 3) * 0.01  # 0.36-0.38 (better)
                else:  # 80% get last_good
                    config_name = "last_good"
                    latency_ms = 850 + (request_count % 5) * 30  # 850-980ms
                    recall_at_10 = 0.32 + (request_count % 4) * 0.01  # 0.32-0.35
                
                # Record metrics
                self.metrics_collector.record_search(
                    trace_id=trace_id,
                    latency_ms=latency_ms,
                    recall_at_10=recall_at_10,
                    config_name=config_name,
                    slo_p95_ms=1200.0
                )
                
                # Simulate occasional SLO violations for demo
                if request_count % 50 == 0:  # 2% violation rate
                    self.metrics_collector.record_search(
                        trace_id=f"demo_trace_violation_{request_count:06d}",
                        latency_ms=1300.0,  # Violates p95 <= 1200ms
                        recall_at_10=0.25,  # Violates recall >= 0.30
                        config_name=config_name,
                        slo_p95_ms=1200.0
                    )
            
            # Wait for batch interval
            elapsed = time.time() - batch_start
            if elapsed < batch_interval:
                time.sleep(batch_interval - elapsed)
            
            # Progress update
            progress = (time.time() - start_time) / self.demo_duration * 100
            print(f"  Progress: {progress:.1f}% ({request_count} requests)")
        
        print(f"  ✓ Traffic simulation completed: {request_count} requests")
        print()
    
    def _monitor_and_decide(self):
        """Monitor deployment and make promotion/rollback decision."""
        print("📊 Step 4: Monitoring deployment and making decision...")
        
        # Get A/B comparison results
        comparison = self.ab_evaluator.get_comparison(window_minutes=5)
        
        print(f"  A/B Analysis Results:")
        print(f"    Total buckets: {comparison.total_buckets}")
        print(f"    Valid buckets: {comparison.valid_buckets}")
        print(f"    Validity rate: {comparison.valid_percentage:.1f}%")
        print(f"    Statistical significance: {comparison.is_significant}")
        
        # Show performance comparison
        print(f"  Performance Comparison:")
        print(f"    Config A (last_good):")
        print(f"      Avg P95: {comparison.config_a_stats['avg_p95_ms']:.2f} ms")
        print(f"      Avg Recall: {comparison.config_a_stats['avg_recall_at_10']:.3f}")
        print(f"      SLO Violations: {comparison.config_a_stats['total_slo_violations']}")
        
        print(f"    Config B (candidate):")
        print(f"      Avg P95: {comparison.config_b_stats['avg_p95_ms']:.2f} ms")
        print(f"      Avg Recall: {comparison.config_b_stats['avg_recall_at_10']:.3f}")
        print(f"      SLO Violations: {comparison.config_b_stats['total_slo_violations']}")
        
        # Show improvements
        print(f"  Improvements:")
        print(f"    P95 Latency: {comparison.p95_improvement:.2f} ms")
        print(f"    Recall@10: {comparison.recall_improvement:.3f}")
        print(f"    SLO Violations: {comparison.slo_violation_reduction}")
        
        # Make decision based on results
        if comparison.valid_percentage >= 80.0 and comparison.is_significant:
            if comparison.p95_improvement < 0 or comparison.recall_improvement > 0:
                decision = "promote"
                print(f"  🎯 Decision: PROMOTE - Candidate shows improvements")
            else:
                decision = "rollback"
                print(f"  🎯 Decision: ROLLBACK - No improvements detected")
        else:
            decision = "rollback"
            print(f"  🎯 Decision: ROLLBACK - Insufficient data or significance")
        
        # Execute decision
        if decision == "promote":
            print(f"  🚀 Promoting candidate configuration...")
            self.canary_executor.promote_candidate()
            print(f"  ✓ Candidate promoted successfully!")
        else:
            print(f"  🔄 Rolling back to last_good configuration...")
            self.canary_executor.stop_canary()
            print(f"  ✓ Rollback completed successfully!")
        
        print()
    
    def _generate_reports(self):
        """Generate comprehensive reports."""
        print("📈 Step 5: Generating comprehensive reports...")
        
        # Generate observability package
        print("  Generating observability package...")
        package = generate_observability_package(output_prefix="demo_package")
        
        print(f"  Generated files:")
        for file_path in package.generated_files:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                file_size = file_path_obj.stat().st_size
                print(f"    ✓ {file_path_obj.name} ({file_size} bytes)")
        
        # Generate A/B report
        print("  Generating A/B evaluation report...")
        ab_report_file = "reports/canary/demo_ab_report.html"
        self.ab_evaluator.report_generator.generate_html_report(ab_report_file, window_minutes=10)
        
        ab_report_path = Path(ab_report_file)
        if ab_report_path.exists():
            file_size = ab_report_path.stat().st_size
            print(f"    ✓ {ab_report_path.name} ({file_size} bytes)")
        
        print("  ✓ All reports generated successfully!")
        print()
    
    def _cleanup_and_summary(self):
        """Cleanup and provide summary."""
        print("🧹 Step 6: Cleanup and summary...")
        
        # Get final status
        status = self.config_manager.get_canary_status()
        
        print(f"  Final Status:")
        print(f"    Canary Status: {status['status']}")
        print(f"    Active Config: {status['active_config']}")
        print(f"    Last Good Config: {status['last_good_config']}")
        
        # Get routing statistics
        routing_stats = get_config_selector().get_selection_stats()
        print(f"  Routing Statistics:")
        print(f"    Total Selections: {routing_stats['total_selections']}")
        print(f"    Bucket A: {routing_stats['bucket_a_percentage']:.1f}%")
        print(f"    Bucket B: {routing_stats['bucket_b_percentage']:.1f}%")
        
        # Get violations summary
        violations_summary = self.slo_monitor.get_violations()
        print(f"  SLO Violations: {len(violations_summary)}")
        
        print("  ✓ Demo cleanup completed!")
        print()
    
    def _emergency_cleanup(self):
        """Emergency cleanup in case of failure."""
        print("\n🚨 Emergency cleanup...")
        try:
            self.canary_executor.stop_canary()
            print("  ✓ Emergency rollback completed")
        except Exception as e:
            print(f"  ⚠️  Emergency cleanup failed: {e}")
    
    def open_reports(self):
        """Open generated reports in browser."""
        print("🌐 Opening reports in browser...")
        
        # Find the most recent one-pager HTML file
        reports_dir = Path("reports/canary")
        html_files = list(reports_dir.glob("*one_pager.html"))
        
        if html_files:
            # Get the most recent file
            latest_html = max(html_files, key=lambda f: f.stat().st_mtime)
            print(f"  Opening: {latest_html}")
            
            try:
                webbrowser.open(f"file://{latest_html.absolute()}")
                print("  ✓ Report opened in browser")
            except Exception as e:
                print(f"  ⚠️  Failed to open browser: {e}")
                print(f"  Please manually open: {latest_html}")
        else:
            print("  ⚠️  No HTML reports found")


def main():
    """Main demo function."""
    print("Canary Deployment System - Complete Demo")
    print("=" * 60)
    print()
    
    # Check if user wants to run the demo
    try:
        response = input("Run complete canary deployment demo? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Demo cancelled.")
            return
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
        return
    
    print()
    
    # Run the demo
    demo = CanaryDemo()
    demo.run_demo()
    
    # Ask if user wants to open reports
    try:
        response = input("\nOpen reports in browser? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            demo.open_reports()
    except KeyboardInterrupt:
        print("\nDemo completed.")


if __name__ == "__main__":
    main()


