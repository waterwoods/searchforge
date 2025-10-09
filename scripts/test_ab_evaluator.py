#!/usr/bin/env python3
"""
Test Script for A/B Evaluator

This script tests the A/B evaluation functionality with simulated data.
"""

import sys
import time
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.canary import (
    get_ab_evaluator, get_report_generator, get_config_manager,
    get_metrics_collector, get_canary_executor
)


def simulate_ab_traffic():
    """Simulate A/B traffic with different performance characteristics."""
    print("Simulating A/B traffic...")
    
    ab_evaluator = get_ab_evaluator()
    metrics_collector = get_metrics_collector()
    
    # Simulate traffic for both configurations
    for i in range(100):
        # Generate trace ID
        trace_id = f"ab_test_{i:04d}"
        
        # Assign to bucket
        bucket = ab_evaluator.assign_bucket(trace_id)
        
        # Simulate different performance based on bucket
        if bucket == "A":  # last_good (90%)
            latency_ms = 850 + (i % 5) * 20  # 850-950ms
            recall_at_10 = 0.32 + (i % 3) * 0.01  # 0.32-0.34
        else:  # B (candidate) (10%)
            latency_ms = 780 + (i % 4) * 15  # 780-840ms (better)
            recall_at_10 = 0.36 + (i % 2) * 0.01  # 0.36-0.37 (better)
        
        # Record metrics
        metrics_collector.record_search(
            trace_id=trace_id,
            latency_ms=latency_ms,
            recall_at_10=recall_at_10,
            config_name="last_good" if bucket == "A" else "candidate_high_recall",
            slo_p95_ms=1200.0
        )
        
        if i % 20 == 0:
            print(f"  Processed {i+1} requests, bucket {bucket}")
    
    print(f"Completed {100} simulated requests")


def test_ab_evaluation():
    """Test A/B evaluation functionality."""
    print("Testing A/B Evaluation...")
    print("=" * 50)
    
    # Get components
    ab_evaluator = get_ab_evaluator()
    metrics_collector = get_metrics_collector()
    
    # Simulate traffic
    simulate_ab_traffic()
    
    # Process metrics buckets
    print("\nProcessing metrics buckets...")
    completed_buckets = metrics_collector.get_completed_buckets()
    ab_buckets = ab_evaluator.process_metrics_buckets(completed_buckets)
    print(f"  Processed {len(ab_buckets)} A/B buckets")
    
    # Get comparison results
    print("\nGetting A/B comparison...")
    comparison = ab_evaluator.get_comparison(window_minutes=10)
    
    print(f"  Total buckets: {comparison.total_buckets}")
    print(f"  Valid buckets: {comparison.valid_buckets}")
    print(f"  Validity rate: {comparison.valid_percentage:.1f}%")
    print(f"  Significant: {comparison.is_significant}")
    
    # Show performance comparison
    print("\nPerformance Comparison:")
    print(f"  Config A (Last Good):")
    print(f"    Avg P95: {comparison.config_a_stats['avg_p95_ms']:.2f} ms")
    print(f"    Avg Recall: {comparison.config_a_stats['avg_recall_at_10']:.3f}")
    print(f"    SLO Violations: {comparison.config_a_stats['total_slo_violations']}")
    
    print(f"  Config B (Candidate):")
    print(f"    Avg P95: {comparison.config_b_stats['avg_p95_ms']:.2f} ms")
    print(f"    Avg Recall: {comparison.config_b_stats['avg_recall_at_10']:.3f}")
    print(f"    SLO Violations: {comparison.config_b_stats['total_slo_violations']}")
    
    # Show improvements
    print("\nImprovements:")
    print(f"  P95 Latency: {comparison.p95_improvement:.2f} ms")
    print(f"  Recall@10: {comparison.recall_improvement:.3f}")
    print(f"  SLO Violations: {comparison.slo_violation_reduction}")
    
    # Generate KPI report
    print("\nGenerating KPI report...")
    kpi_report = ab_evaluator.generate_kpi_report(window_minutes=10)
    
    print(f"  Recommendation: {kpi_report['recommendation']}")
    print(f"  Valid: {kpi_report['summary']['is_valid']}")
    print(f"  Significant: {kpi_report['statistical_significance']['is_significant']}")
    
    # Show bucket distribution
    print("\nBucket Distribution:")
    distribution = ab_evaluator.get_bucket_distribution()
    print(f"  Total traces: {distribution['total_traces']}")
    print(f"  Bucket A: {distribution['bucket_a_count']} ({distribution['bucket_a_percentage']:.1f}%)")
    print(f"  Bucket B: {distribution['bucket_b_count']} ({distribution['bucket_b_percentage']:.1f}%)")
    
    return kpi_report


def test_html_report():
    """Test HTML report generation."""
    print("\nTesting HTML Report Generation...")
    print("=" * 50)
    
    report_generator = get_report_generator()
    
    # Generate HTML report
    output_file = "reports/canary/ab_test_report.html"
    report_generator.generate_html_report(output_file, window_minutes=10)
    
    print(f"✓ Generated HTML report: {output_file}")
    
    # Check if file exists and has content
    if Path(output_file).exists():
        file_size = Path(output_file).stat().st_size
        print(f"  File size: {file_size} bytes")
        
        # Show a preview of the HTML
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "Canary Deployment A/B Test Report" in content:
                print("  ✓ HTML report contains expected content")
            else:
                print("  ⚠ HTML report may be missing content")
    else:
        print("  ✗ HTML report file not found")


def test_export_functionality():
    """Test export functionality."""
    print("\nTesting Export Functionality...")
    print("=" * 50)
    
    ab_evaluator = get_ab_evaluator()
    
    # Export A/B report
    output_dir = Path("reports/canary")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Export JSON report
    json_file = output_dir / f"ab_report_{timestamp}.json"
    ab_evaluator.export_ab_report(str(json_file), window_minutes=10)
    print(f"✓ Exported A/B JSON report: {json_file}")
    
    # Export HTML report
    html_file = output_dir / f"ab_report_{timestamp}.html"
    report_generator = get_report_generator()
    report_generator.generate_html_report(str(html_file), window_minutes=10)
    print(f"✓ Exported A/B HTML report: {html_file}")
    
    # Verify exports
    if json_file.exists() and html_file.exists():
        json_size = json_file.stat().st_size
        html_size = html_file.stat().st_size
        print(f"  JSON size: {json_size} bytes")
        print(f"  HTML size: {html_size} bytes")
        print("  ✓ All exports successful")
    else:
        print("  ✗ Some exports failed")


def main():
    """Run all A/B evaluator tests."""
    print("A/B Evaluator Test Suite")
    print("=" * 60)
    
    try:
        # Test A/B evaluation
        kpi_report = test_ab_evaluation()
        
        # Test HTML report generation
        test_html_report()
        
        # Test export functionality
        test_export_functionality()
        
        print("\n🎉 All A/B evaluator tests completed successfully!")
        print("\nKey Results:")
        print(f"  - Validity Rate: {kpi_report['summary']['valid_percentage']:.1f}%")
        print(f"  - Recommendation: {kpi_report['recommendation']}")
        print(f"  - Statistical Significance: {kpi_report['statistical_significance']['confidence_level']:.0f}%")
        
        print("\nGenerated Files:")
        print("  - reports/canary/ab_test_report.html")
        print("  - reports/canary/ab_report_*.json")
        print("  - reports/canary/ab_report_*.html")
        
        print("\nNext Steps:")
        print("  1. Open reports/canary/ab_test_report.html in browser")
        print("  2. Review A/B comparison results")
        print("  3. Use recommendation for deployment decision")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


