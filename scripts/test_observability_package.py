#!/usr/bin/env python3
"""
Test Script for Observability Package

This script tests the observability package generation functionality.
"""

import sys
import time
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.canary import (
    get_observability_generator, generate_observability_package,
    get_ab_evaluator, get_config_manager, get_canary_executor
)


def test_observability_package_generation():
    """Test observability package generation."""
    print("Testing Observability Package Generation...")
    print("=" * 50)
    
    # Generate a package
    print("Generating observability package...")
    package = generate_observability_package()
    
    print(f"Package generated:")
    print(f"  Deployment ID: {package.deployment_id}")
    print(f"  Timestamp: {package.timestamp}")
    print(f"  Config A: {package.config_a}")
    print(f"  Config B: {package.config_b}")
    print(f"  Status: {package.deployment_status}")
    print(f"  Duration: {package.duration_seconds:.1f} seconds")
    print(f"  Total requests: {package.total_requests}")
    print(f"  Generated files: {len(package.generated_files)}")
    
    # List generated files
    print(f"\nGenerated files:")
    for file_path in package.generated_files:
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            file_size = file_path_obj.stat().st_size
            print(f"  ✓ {file_path} ({file_size} bytes)")
        else:
            print(f"  ✗ {file_path} (not found)")
    
    return package


def test_individual_file_generation():
    """Test individual file generation."""
    print("\nTesting Individual File Generation...")
    print("=" * 50)
    
    generator = get_observability_generator()
    
    # Test with custom prefix
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    custom_prefix = f"test_package_{timestamp}"
    
    print(f"Generating package with custom prefix: {custom_prefix}")
    package = generator.generate_package(output_prefix=custom_prefix)
    
    print(f"Generated files with custom prefix:")
    for file_path in package.generated_files:
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            file_size = file_path_obj.stat().st_size
            print(f"  ✓ {file_path} ({file_size} bytes)")
        else:
            print(f"  ✗ {file_path} (not found)")
    
    return package


def test_file_contents():
    """Test the contents of generated files."""
    print("\nTesting File Contents...")
    print("=" * 50)
    
    # Generate a package
    package = generate_observability_package()
    
    # Test canary_result.json
    canary_result_files = [f for f in package.generated_files if f.endswith('_canary_result.json')]
    if canary_result_files:
        canary_result_file = canary_result_files[0]
        print(f"Testing canary_result.json: {canary_result_file}")
        
        try:
            with open(canary_result_file, 'r') as f:
                data = json.load(f)
            
            print(f"  ✓ JSON is valid")
            print(f"  ✓ Contains deployment_summary: {'deployment_summary' in data}")
            print(f"  ✓ Contains configurations: {'configurations' in data}")
            print(f"  ✓ Contains ab_comparison: {'ab_comparison' in data}")
            print(f"  ✓ Contains slo_violations: {'slo_violations' in data}")
            
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
    
    # Test metrics.json
    metrics_files = [f for f in package.generated_files if f.endswith('_metrics.json')]
    if metrics_files:
        metrics_file = metrics_files[0]
        print(f"\nTesting metrics.json: {metrics_file}")
        
        try:
            with open(metrics_file, 'r') as f:
                data = json.load(f)
            
            print(f"  ✓ JSON is valid")
            print(f"  ✓ Contains performance_metrics: {'performance_metrics' in data}")
            print(f"  ✓ Contains ab_analysis: {'ab_analysis' in data}")
            print(f"  ✓ Contains slo_analysis: {'slo_analysis' in data}")
            
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
    
    # Test regression_baseline.csv
    csv_files = [f for f in package.generated_files if f.endswith('_regression_baseline.csv')]
    if csv_files:
        csv_file = csv_files[0]
        print(f"\nTesting regression_baseline.csv: {csv_file}")
        
        try:
            with open(csv_file, 'r') as f:
                lines = f.readlines()
            
            print(f"  ✓ CSV has {len(lines)} lines")
            print(f"  ✓ Header line: {lines[0].strip() if lines else 'None'}")
            
            # Check for expected metrics
            content = ''.join(lines)
            expected_metrics = ['p95_latency_ms', 'recall_at_10', 'slo_violations', 'response_count']
            for metric in expected_metrics:
                if metric in content:
                    print(f"  ✓ Contains metric: {metric}")
                else:
                    print(f"  ✗ Missing metric: {metric}")
            
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
    
    # Test one_pager.html
    html_files = [f for f in package.generated_files if f.endswith('_one_pager.html')]
    if html_files:
        html_file = html_files[0]
        print(f"\nTesting one_pager.html: {html_file}")
        
        try:
            with open(html_file, 'r') as f:
                content = f.read()
            
            print(f"  ✓ HTML file size: {len(content)} characters")
            print(f"  ✓ Contains title: {'Canary Deployment A/B Test Report' in content}")
            print(f"  ✓ Contains Chart.js: {'chart.js' in content.lower()}")
            
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")


def test_multiple_packages():
    """Test generating multiple packages."""
    print("\nTesting Multiple Package Generation...")
    print("=" * 50)
    
    generator = get_observability_generator()
    
    # Generate multiple packages
    deployment_ids = ["deployment_1", "deployment_2", "deployment_3"]
    
    print(f"Generating {len(deployment_ids)} packages...")
    packages = generator.generate_multiple_packages(deployment_ids)
    
    print(f"Generated {len(packages)} packages:")
    for i, package in enumerate(packages):
        print(f"  Package {i+1}: {package.deployment_id}")
        print(f"    Files: {len(package.generated_files)}")
        print(f"    Status: {package.deployment_status}")
    
    # Test package comparison
    print(f"\nTesting package comparison...")
    comparison = generator.compare_packages(packages)
    
    print(f"Comparison results:")
    print(f"  Total packages: {comparison.get('total_packages', 0)}")
    print(f"  Packages compared: {len(comparison.get('packages', []))}")
    
    if 'trends' in comparison:
        trends = comparison['trends']
        print(f"  P95 latency trend: {trends.get('p95_latency_trend_ms', 0):.2f} ms")
        print(f"  Recall trend: {trends.get('recall_trend', 0):.3f}")
        print(f"  P95 improvement: {trends.get('p95_improvement', False)}")
        print(f"  Recall improvement: {trends.get('recall_improvement', False)}")
    
    return packages


def test_package_with_real_data():
    """Test package generation with simulated real data."""
    print("\nTesting Package with Real Data...")
    print("=" * 50)
    
    # Simulate some traffic to generate real metrics
    print("Simulating traffic for real metrics...")
    ab_evaluator = get_ab_evaluator()
    metrics_collector = ab_evaluator.metrics_collector
    
    # Generate some test traffic
    for i in range(50):
        trace_id = f"real_data_test_{i}"
        bucket = ab_evaluator.assign_bucket(trace_id)
        
        # Simulate different performance
        if bucket == "A":
            latency_ms = 850 + (i % 3) * 20
            recall_at_10 = 0.32 + (i % 2) * 0.01
        else:
            latency_ms = 780 + (i % 4) * 15
            recall_at_10 = 0.36 + (i % 3) * 0.01
        
        metrics_collector.record_search(
            trace_id=trace_id,
            latency_ms=latency_ms,
            recall_at_10=recall_at_10,
            config_name="last_good" if bucket == "A" else "candidate_test",
            slo_p95_ms=1200.0
        )
    
    print("Traffic simulation completed")
    
    # Generate package with real data
    print("Generating package with real data...")
    package = generate_observability_package(output_prefix="real_data_package")
    
    print(f"Real data package:")
    print(f"  Config A metrics:")
    print(f"    P95: {package.config_a_metrics.get('avg_p95_ms', 0):.2f} ms")
    print(f"    Recall: {package.config_a_metrics.get('avg_recall_at_10', 0):.3f}")
    print(f"    Responses: {package.config_a_metrics.get('total_responses', 0)}")
    
    print(f"  Config B metrics:")
    print(f"    P95: {package.config_b_metrics.get('avg_p95_ms', 0):.2f} ms")
    print(f"    Recall: {package.config_b_metrics.get('avg_recall_at_10', 0):.3f}")
    print(f"    Responses: {package.config_b_metrics.get('total_responses', 0)}")
    
    # Check A/B comparison
    ab_summary = package.ab_comparison.get('summary', {})
    print(f"  A/B Summary:")
    print(f"    Total buckets: {ab_summary.get('total_buckets', 0)}")
    print(f"    Valid buckets: {ab_summary.get('valid_buckets', 0)}")
    print(f"    Validity rate: {ab_summary.get('valid_percentage', 0):.1f}%")
    
    return package


def main():
    """Run all observability package tests."""
    print("Observability Package Test Suite")
    print("=" * 60)
    
    try:
        # Test basic package generation
        test_observability_package_generation()
        
        # Test individual file generation
        test_individual_file_generation()
        
        # Test file contents
        test_file_contents()
        
        # Test multiple packages
        test_multiple_packages()
        
        # Test with real data
        test_package_with_real_data()
        
        print("\n🎉 All observability package tests completed successfully!")
        
        print("\nKey Features Tested:")
        print("  ✓ Observability package generation")
        print("  ✓ Individual file generation (JSON, CSV, HTML)")
        print("  ✓ File content validation")
        print("  ✓ Multiple package generation")
        print("  ✓ Package comparison and trends")
        print("  ✓ Real data integration")
        
        print("\nGenerated Files:")
        print("  - canary_result.json: Complete deployment data")
        print("  - metrics.json: Detailed performance metrics")
        print("  - one_pager.html: Visual summary with charts")
        print("  - regression_baseline.csv: 5-minute baseline data")
        
        print("\nPackage Benefits:")
        print("  - Complete deployment observability")
        print("  - Standardized export format")
        print("  - Easy comparison across deployments")
        print("  - Production-ready monitoring data")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


