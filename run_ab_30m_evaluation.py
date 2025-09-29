#!/usr/bin/env python3
"""
SmartSearchX 2×30min A/B Evaluation Runner

This script orchestrates the complete 2×30min evaluation with:
- Run A (Baseline 30m): probes qps=3, no bursts, chaos off, warm_cache=true, TopK=50, mirror=0.1
- Run B (High-Stress 30m): step qps 5→10→15→20 + bursts, chaos injection, warm_cache=false, TopK=80, mirror=0.7
- Recovery time tracking after each chaos window
- Assertions validation and reporting
- Timeline charts, recovery histograms, and one-pager PDF generation
"""

import os
import sys
import json
import asyncio
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from modules.evaluation.enhanced_ab_evaluator import EnhancedABEvaluator
from modules.evaluation.enhanced_ab_analyzer import EnhancedABAnalyzer

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ab_30m_evaluation.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_prerequisites():
    """Check if all required services are available."""
    logger = logging.getLogger(__name__)
    
    print("🔍 Checking prerequisites...")
    
    # Check if Qdrant is accessible
    try:
        import requests
        response = requests.get("http://localhost:6333/collections", timeout=5)
        if response.status_code == 200:
            print("✅ Qdrant service is accessible")
        else:
            print("⚠️  Qdrant service may not be running properly")
            return False
    except Exception as e:
        print(f"❌ Qdrant service check failed: {e}")
        return False
    
    # Check if LLM service is accessible
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        if response.status_code == 200:
            print("✅ LLM service is accessible")
        else:
            print("⚠️  LLM service may not be running properly")
            return False
    except Exception as e:
        print(f"❌ LLM service check failed: {e}")
        return False
    
    # Check if configuration file exists
    config_file = "reports/ab_30m/evaluation_config.json"
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return False
    print(f"✅ Configuration file found: {config_file}")
    
    return True

def create_output_directories():
    """Create necessary output directories."""
    logger = logging.getLogger(__name__)
    
    print("📁 Creating output directories...")
    
    directories = [
        "reports/ab_30m",
        "reports/ab_30m/charts",
        "reports/ab_30m/timeline",
        "reports/ab_30m/recovery"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

async def run_baseline_evaluation(config_file: str, output_dir: str, seed: int):
    """Run baseline evaluation (Run A)."""
    logger = logging.getLogger(__name__)
    
    print("\n🚀 Starting Run A (Baseline 30m)...")
    print("   Configuration: qps=3, no bursts, chaos off, warm_cache=true, TopK=50, mirror=0.1")
    
    output_file = f"{output_dir}/baseline_results.json"
    
    evaluator = EnhancedABEvaluator(config_file)
    
    start_time = time.time()
    await evaluator.run_evaluation("baseline", output_file)
    duration = time.time() - start_time
    
    print(f"✅ Run A (Baseline) completed in {duration:.1f}s")
    print(f"   Results saved to: {output_file}")
    
    return output_file

async def run_stress_evaluation(config_file: str, output_dir: str, seed: int):
    """Run high-stress evaluation (Run B)."""
    logger = logging.getLogger(__name__)
    
    print("\n🔥 Starting Run B (High-Stress 30m)...")
    print("   Configuration: step qps 5→10→15→20 + bursts, chaos injection, warm_cache=false, TopK=80, mirror=0.7")
    print("   Chaos: +800ms latency, 20% loss, disconnects at 10m/20m")
    
    output_file = f"{output_dir}/stress_results.json"
    
    evaluator = EnhancedABEvaluator(config_file)
    
    start_time = time.time()
    await evaluator.run_evaluation("high_stress", output_file)
    duration = time.time() - start_time
    
    print(f"✅ Run B (High-Stress) completed in {duration:.1f}s")
    print(f"   Results saved to: {output_file}")
    
    return output_file

def run_analysis(baseline_file: str, stress_file: str, config_file: str, output_dir: str):
    """Run analysis and generate reports."""
    logger = logging.getLogger(__name__)
    
    print("\n📊 Starting analysis and report generation...")
    
    # Create analyzer
    analyzer = EnhancedABAnalyzer(baseline_file, stress_file)
    
    # Load configuration for assertions
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Generate charts
    charts_dir = f"{output_dir}/charts"
    print("📈 Generating timeline charts...")
    analyzer.create_timeline_charts(charts_dir)
    
    print("📈 Generating recovery analysis charts...")
    analyzer.create_recovery_analysis_charts(charts_dir)
    
    print("📈 Generating comparison charts...")
    analyzer.create_comparison_charts(charts_dir)
    
    # Generate reports
    print("📋 Generating enhanced diff report...")
    enhanced_report = analyzer.generate_enhanced_report(
        f"{output_dir}/enhanced_diff_report.json", config
    )
    
    print("📑 Generating one-pager PDF...")
    analyzer.generate_one_pager_pdf(
        f"{output_dir}/one_pager.pdf", config
    )
    
    # Print summary
    print("\n🎯 Evaluation Summary:")
    assertions = enhanced_report["assertions"]
    assessment = enhanced_report["overall_assessment"]
    
    print(f"   Duration OK: {'✓' if assertions['duration_ok'] else '✗'}")
    print(f"   Stress Effect (P95 Peak ≥ 3×): {'✓' if assertions['stress_effect'] else '✗'}")
    print(f"   Recovery Time ≤ 90s: {'✓' if assertions['recovery_time_ok'] else '✗'}")
    print(f"   Recovery Violation < 5%: {'✓' if assertions['recovery_violation_ok'] else '✗'}")
    print(f"   Tuner Actions ≥ 10: {'✓' if assertions['tuner_active'] else '✗'}")
    print(f"   Overall Status: {assessment['stress_status']}")
    print(f"   System Resilience: {assessment['system_resilience']}")
    print(f"   Recovery Performance: {assessment['recovery_performance']}")
    
    return enhanced_report

def print_file_paths(output_dir: str):
    """Print all generated file paths."""
    print("\n📁 Generated Files:")
    
    files = [
        f"{output_dir}/baseline_results.json",
        f"{output_dir}/stress_results.json",
        f"{output_dir}/enhanced_diff_report.json",
        f"{output_dir}/one_pager.pdf",
        f"{output_dir}/charts/timeline_charts.png",
        f"{output_dir}/charts/recovery_analysis.png",
        f"{output_dir}/charts/comparison_charts.png"
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (not found)")

async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="SmartSearchX 2×30min A/B Evaluation")
    parser.add_argument("--config", default="reports/ab_30m/evaluation_config.json", help="Configuration file")
    parser.add_argument("--output", default="reports/ab_30m", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline run")
    parser.add_argument("--skip-stress", action="store_true", help="Skip stress run")
    parser.add_argument("--analysis-only", action="store_true", help="Only run analysis")
    parser.add_argument("--force-full-run", action="store_true", help="Force full evaluation run (both baseline and stress)")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    print("🎬 SmartSearchX 2×30min A/B Evaluation")
    print("=====================================")
    print(f"Configuration: {args.config}")
    print(f"Output directory: {args.output}")
    print(f"Random seed: {args.seed}")
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites check failed. Please fix the issues above.")
        return 1
    
    # Create output directories
    create_output_directories()
    
    baseline_file = f"{args.output}/baseline_results.json"
    stress_file = f"{args.output}/stress_results.json"
    
    # Run evaluations
    if not args.analysis_only:
        # Force full run overrides skip flags
        if args.force_full_run:
            print("🔄 Force full run enabled - running both baseline and stress evaluations")
            baseline_file = await run_baseline_evaluation(args.config, args.output, args.seed)
            stress_file = await run_stress_evaluation(args.config, args.output, args.seed)
        else:
            if not args.skip_baseline:
                baseline_file = await run_baseline_evaluation(args.config, args.output, args.seed)
            
            if not args.skip_stress:
                stress_file = await run_stress_evaluation(args.config, args.output, args.seed)
    
    # Run analysis
    if os.path.exists(baseline_file) and os.path.exists(stress_file):
        enhanced_report = run_analysis(baseline_file, stress_file, args.config, args.output)
        
        # Print file paths
        print_file_paths(args.output)
        
        # Return exit code based on overall assessment
        if enhanced_report["assertions"]["overall_pass"]:
            print("\n🎉 Evaluation PASSED!")
            return 0
        else:
            print("\n❌ Evaluation FAILED!")
            return 1
    else:
        print("❌ Cannot run analysis - missing result files")
        print(f"   Baseline: {baseline_file} ({'exists' if os.path.exists(baseline_file) else 'missing'})")
        print(f"   Stress: {stress_file} ({'exists' if os.path.exists(stress_file) else 'missing'})")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
