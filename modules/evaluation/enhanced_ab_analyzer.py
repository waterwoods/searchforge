#!/usr/bin/env python3
"""
Enhanced A/B Analyzer for SmartSearchX with Recovery Analysis

This module analyzes enhanced A/B evaluation results and generates:
- Timeline charts with chaos bands and recovery curves
- Recovery time histograms and CDFs
- Pass/fail assertions based on specified criteria
- One-pager PDF reports with X→Y metrics
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

class EnhancedABAnalyzer:
    """Enhanced analyzer with recovery time tracking and timeline analysis."""
    
    def __init__(self, baseline_file: str, stress_file: str):
        """Initialize with baseline and stress results."""
        with open(baseline_file, 'r') as f:
            self.baseline_data = json.load(f)
        
        with open(stress_file, 'r') as f:
            self.stress_data = json.load(f)
        
        self.baseline_metrics = self.baseline_data["metrics"]
        self.stress_metrics = self.stress_data["metrics"]
        self.baseline_timeline = self.baseline_data.get("timeline_metrics", [])
        self.stress_timeline = self.stress_data.get("timeline_metrics", [])
        
    def calculate_assertions(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Calculate pass/fail assertions based on requirements."""
        assertions = {}
        
        # Duration check (≥1080s for both)
        baseline_duration_ok = self.baseline_metrics["runtime_seconds"] >= 1080
        stress_duration_ok = self.stress_metrics["runtime_seconds"] >= 1080
        assertions["duration_ok"] = baseline_duration_ok and stress_duration_ok
        
        # Stress effect: p95_peak(B) ≥ 3× p95_med(A)
        baseline_p95 = self.baseline_metrics["p95_ms"]
        stress_p95 = self.stress_metrics["p95_ms"]
        stress_recovery_events = self.stress_metrics.get("recovery_events", [])
        stress_peak_p95 = max([event["peak_p95"] for event in stress_recovery_events], default=stress_p95)
        stress_effect = stress_peak_p95 >= (3.0 * baseline_p95)
        assertions["stress_effect"] = stress_effect
        
        # Recovery time assertions: recovery_time_each ≤ 90s; violation_rate < 5%
        recovery_times = [event["recovery_time_sec"] for event in stress_recovery_events 
                         if event["recovery_time_sec"] is not None]
        recovery_time_ok = all(rt <= 90.0 for rt in recovery_times) if recovery_times else True
        recovery_violation_rate = self.stress_metrics.get("recovery_violation_rate", 0.0)
        recovery_violation_ok = recovery_violation_rate < 0.05
        assertions["recovery_time_ok"] = recovery_time_ok
        assertions["recovery_violation_ok"] = recovery_violation_ok
        
        # Tuner activity: actions per chaos window ≥ 10
        chaos_windows = len(stress_recovery_events)
        tuner_actions = self.stress_metrics["autotuner_actions_count"]
        tuner_active = tuner_actions >= 10 if chaos_windows > 0 else True
        assertions["tuner_active"] = tuner_active
        
        # Overall pass/fail
        assertions["overall_pass"] = all([
            assertions["duration_ok"],
            assertions["stress_effect"],
            assertions["recovery_time_ok"],
            assertions["recovery_violation_ok"],
            assertions["tuner_active"]
        ])
        
        return assertions
    
    def create_timeline_charts(self, output_dir: str):
        """Create timeline charts with chaos bands and recovery curves."""
        if not self.stress_timeline:
            print("⚠️  No timeline data available for stress run")
            return
        
        # Convert timeline data to DataFrame
        df = pd.DataFrame(self.stress_timeline)
        df['time_minutes'] = df['timestamp'] / 60.0
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: P95/P99 latency with chaos bands
        ax1.plot(df['time_minutes'], df['p95_ms'], label='P95 Latency', linewidth=2, color='red')
        ax1.plot(df['time_minutes'], df['p99_ms'], label='P99 Latency', linewidth=2, color='darkred')
        
        # Add chaos bands
        chaos_periods = df[df['chaos_active'] == True]
        if not chaos_periods.empty:
            for _, period in chaos_periods.iterrows():
                ax1.axvspan(period['time_minutes'] - 1, period['time_minutes'] + 1, 
                           alpha=0.3, color='red', label='Chaos Window' if period['time_minutes'] == chaos_periods.iloc[0]['time_minutes'] else "")
        
        ax1.set_xlabel('Time (minutes)')
        ax1.set_ylabel('Latency (ms)')
        ax1.set_title('Latency Timeline with Chaos Bands')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: TopK/Batch size over time
        ax2.plot(df['time_minutes'], df['topk'], label='TopK', linewidth=2, color='blue')
        ax2_twin = ax2.twinx()
        ax2_twin.plot(df['time_minutes'], df['batch_size'], label='Batch Size', linewidth=2, color='green')
        
        ax2.set_xlabel('Time (minutes)')
        ax2.set_ylabel('TopK', color='blue')
        ax2_twin.set_ylabel('Batch Size', color='green')
        ax2.set_title('TopK and Batch Size Timeline')
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Route Alpha and Tuner Actions
        ax3.plot(df['time_minutes'], df['route_alpha'], label='Route Alpha', linewidth=2, color='purple')
        ax3_twin = ax3.twinx()
        ax3_twin.plot(df['time_minutes'], df['tuner_actions_count'], label='Tuner Actions', 
                     linewidth=2, color='orange', marker='o', markersize=4)
        
        ax3.set_xlabel('Time (minutes)')
        ax3.set_ylabel('Route Alpha', color='purple')
        ax3_twin.set_ylabel('Tuner Actions Count', color='orange')
        ax3.set_title('Route Alpha and Tuner Actions Timeline')
        ax3.legend(loc='upper left')
        ax3_twin.legend(loc='upper right')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: QPS and Recovery Status
        ax4.plot(df['time_minutes'], df['current_qps'], label='Current QPS', linewidth=2, color='green')
        
        # Add recovery periods
        recovery_periods = df[df['recovery_active'] == True]
        if not recovery_periods.empty:
            for _, period in recovery_periods.iterrows():
                ax4.axvspan(period['time_minutes'] - 0.5, period['time_minutes'] + 0.5, 
                           alpha=0.3, color='orange', label='Recovery Active' if period['time_minutes'] == recovery_periods.iloc[0]['time_minutes'] else "")
        
        ax4.set_xlabel('Time (minutes)')
        ax4.set_ylabel('QPS')
        ax4.set_title('QPS and Recovery Status Timeline')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/timeline_charts.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_recovery_analysis_charts(self, output_dir: str):
        """Create recovery time histogram and CDF."""
        recovery_events = self.stress_metrics.get("recovery_events", [])
        recovery_times = [event["recovery_time_sec"] for event in recovery_events 
                         if event["recovery_time_sec"] is not None]
        
        if not recovery_times:
            print("⚠️  No recovery time data available")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Histogram
        ax1.hist(recovery_times, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(x=90, color='red', linestyle='--', linewidth=2, label='90s threshold')
        ax1.set_xlabel('Recovery Time (seconds)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Recovery Time Histogram')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add statistics
        mean_rt = np.mean(recovery_times)
        median_rt = np.median(recovery_times)
        max_rt = np.max(recovery_times)
        ax1.text(0.7, 0.8, f'Mean: {mean_rt:.1f}s\nMedian: {median_rt:.1f}s\nMax: {max_rt:.1f}s', 
                transform=ax1.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # CDF
        sorted_times = np.sort(recovery_times)
        cdf_values = np.arange(1, len(sorted_times) + 1) / len(sorted_times)
        ax2.plot(sorted_times, cdf_values, linewidth=2, color='blue')
        ax2.axvline(x=90, color='red', linestyle='--', linewidth=2, label='90s threshold')
        ax2.axhline(y=0.95, color='green', linestyle=':', linewidth=2, label='95th percentile')
        
        ax2.set_xlabel('Recovery Time (seconds)')
        ax2.set_ylabel('Cumulative Probability')
        ax2.set_title('Recovery Time CDF')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Find 95th percentile
        p95_recovery = np.percentile(recovery_times, 95)
        ax2.axvline(x=p95_recovery, color='orange', linestyle=':', linewidth=2, 
                   label=f'95th percentile: {p95_recovery:.1f}s')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/recovery_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_comparison_charts(self, output_dir: str):
        """Create comparison charts between baseline and stress runs."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Latency comparison
        metrics = ['P95', 'P99', 'Mean', 'Jitter']
        baseline_values = [
            self.baseline_metrics["p95_ms"],
            self.baseline_metrics["p99_ms"],
            self.baseline_metrics["mean_latency_ms"],
            self.baseline_metrics["jitter_ms"]
        ]
        stress_values = [
            self.stress_metrics["p95_ms"],
            self.stress_metrics["p99_ms"],
            self.stress_metrics["mean_latency_ms"],
            self.stress_metrics["jitter_ms"]
        ]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, baseline_values, width, label='Baseline', color='skyblue', alpha=0.8)
        bars2 = ax1.bar(x + width/2, stress_values, width, label='High-Stress', color='coral', alpha=0.8)
        
        ax1.set_ylabel('Latency (ms)')
        ax1.set_title('Latency Metrics Comparison')
        ax1.set_xticks(x)
        ax1.set_xticklabels(metrics)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (baseline, stress) in enumerate(zip(baseline_values, stress_values)):
            ax1.text(i - width/2, baseline + 1, f'{baseline:.1f}', ha='center', va='bottom')
            ax1.text(i + width/2, stress + 1, f'{stress:.1f}', ha='center', va='bottom')
        
        # Recovery events analysis
        recovery_events = self.stress_metrics.get("recovery_events", [])
        if recovery_events:
            recovery_times = [event["recovery_time_sec"] for event in recovery_events 
                             if event["recovery_time_sec"] is not None]
            peak_p95s = [event["peak_p95"] for event in recovery_events]
            
            ax2.scatter(peak_p95s, recovery_times, alpha=0.7, s=100, color='red')
            ax2.axhline(y=90, color='red', linestyle='--', linewidth=2, label='90s threshold')
            ax2.set_xlabel('Peak P95 (ms)')
            ax2.set_ylabel('Recovery Time (s)')
            ax2.set_title('Peak P95 vs Recovery Time')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Autotuner activity
        runs = ['Baseline', 'High-Stress']
        actions = [
            self.baseline_metrics["autotuner_actions_count"],
            self.stress_metrics["autotuner_actions_count"]
        ]
        
        bars = ax3.bar(runs, actions, color=['skyblue', 'coral'], alpha=0.8)
        ax3.set_ylabel('Autotuner Actions Count')
        ax3.set_title('Autotuner Activity Comparison')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, action in zip(bars, actions):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(action), ha='center', va='bottom')
        
        # Violation rates
        violation_metrics = ['Query Violations', 'Recovery Violations']
        baseline_violations = [self.baseline_metrics["violation_rate"], 0.0]
        stress_violations = [self.stress_metrics["violation_rate"], 
                           self.stress_metrics.get("recovery_violation_rate", 0.0)]
        
        x = np.arange(len(violation_metrics))
        bars1 = ax4.bar(x - width/2, baseline_violations, width, label='Baseline', color='skyblue', alpha=0.8)
        bars2 = ax4.bar(x + width/2, stress_violations, width, label='High-Stress', color='coral', alpha=0.8)
        
        ax4.set_ylabel('Violation Rate')
        ax4.set_title('Violation Rates Comparison')
        ax4.set_xticks(x)
        ax4.set_xticklabels(violation_metrics)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Add percentage labels
        for i, (baseline, stress) in enumerate(zip(baseline_violations, stress_violations)):
            ax4.text(i - width/2, baseline + 0.001, f'{baseline:.1%}', ha='center', va='bottom')
            ax4.text(i + width/2, stress + 0.001, f'{stress:.1%}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/comparison_charts.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_one_pager_pdf(self, output_file: str, config: Dict[str, Any]):
        """Generate comprehensive one-pager PDF with X→Y metrics and pass/fail flags."""
        assertions = self.calculate_assertions(config)
        
        with PdfPages(output_file) as pdf:
            # Title page with executive summary
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.text(0.5, 0.95, 'SmartSearchX Enhanced A/B Evaluation Report', 
                   ha='center', va='center', fontsize=24, fontweight='bold')
            ax.text(0.5, 0.88, '2×30min Baseline vs High-Stress Comparison', 
                   ha='center', va='center', fontsize=18)
            ax.text(0.5, 0.82, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 
                   ha='center', va='center', fontsize=12)
            
            # Overall status
            status_color = 'green' if assertions["overall_pass"] else 'red'
            status_text = 'PASS' if assertions["overall_pass"] else 'FAIL'
            ax.text(0.5, 0.75, f'Overall Status: {status_text}', 
                   ha='center', va='center', fontsize=20, fontweight='bold', color=status_color)
            
            # Key metrics summary
            ax.text(0.05, 0.65, 'Key Metrics Summary:', fontsize=16, fontweight='bold')
            ax.text(0.05, 0.60, f'Baseline P95: {self.baseline_metrics["p95_ms"]:.1f}ms', fontsize=12)
            ax.text(0.05, 0.57, f'Stress Peak P95: {max([event["peak_p95"] for event in self.stress_metrics.get("recovery_events", [])], default=self.stress_metrics["p95_ms"]):.1f}ms', fontsize=12)
            
            recovery_events = self.stress_metrics.get("recovery_events", [])
            if recovery_events:
                recovery_times = [event["recovery_time_sec"] for event in recovery_events if event["recovery_time_sec"] is not None]
                if recovery_times:
                    ax.text(0.05, 0.54, f'Avg Recovery Time: {np.mean(recovery_times):.1f}s', fontsize=12)
                    ax.text(0.05, 0.51, f'Max Recovery Time: {np.max(recovery_times):.1f}s', fontsize=12)
            
            ax.text(0.05, 0.48, f'Baseline Queries: {self.baseline_metrics["total_queries"]}', fontsize=12)
            ax.text(0.05, 0.45, f'Stress Queries: {self.stress_metrics["total_queries"]}', fontsize=12)
            ax.text(0.05, 0.42, f'Stress Autotuner Actions: {self.stress_metrics["autotuner_actions_count"]}', fontsize=12)
            
            # Assertions with pass/fail flags
            ax.text(0.05, 0.35, 'Assertions (Pass/Fail):', fontsize=16, fontweight='bold')
            
            assertion_items = [
                ("Duration ≥ 1080s", assertions["duration_ok"]),
                ("P95 Peak Ratio ≥ 3×", assertions["stress_effect"]),
                ("Recovery Time ≤ 90s", assertions["recovery_time_ok"]),
                ("Recovery Violation < 5%", assertions["recovery_violation_ok"]),
                ("Tuner Actions ≥ 10", assertions["tuner_active"])
            ]
            
            y_pos = 0.30
            for item, passed in assertion_items:
                status = "✓ PASS" if passed else "✗ FAIL"
                color = 'green' if passed else 'red'
                ax.text(0.05, y_pos, f'{item}: {status}', fontsize=12, color=color)
                y_pos -= 0.03
            
            # X→Y metrics
            ax.text(0.05, 0.10, 'X→Y Metrics:', fontsize=16, fontweight='bold')
            
            baseline_p95 = self.baseline_metrics["p95_ms"]
            stress_p95 = self.stress_metrics["p95_ms"]
            p95_ratio = stress_p95 / baseline_p95 if baseline_p95 > 0 else 0
            
            ax.text(0.05, 0.07, f'P95: {baseline_p95:.1f}ms → {stress_p95:.1f}ms ({p95_ratio:.2f}×)', fontsize=12)
            
            baseline_queries = self.baseline_metrics["total_queries"]
            stress_queries = self.stress_metrics["total_queries"]
            ax.text(0.05, 0.04, f'Queries: {baseline_queries} → {stress_queries}', fontsize=12)
            
            baseline_actions = self.baseline_metrics["autotuner_actions_count"]
            stress_actions = self.stress_metrics["autotuner_actions_count"]
            ax.text(0.05, 0.01, f'Tuner Actions: {baseline_actions} → {stress_actions}', fontsize=12)
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
    
    def generate_enhanced_report(self, output_file: str, config: Dict[str, Any]):
        """Generate enhanced diff report with detailed analysis."""
        assertions = self.calculate_assertions(config)
        
        # Calculate detailed metrics
        baseline_p95 = self.baseline_metrics["p95_ms"]
        stress_p95 = self.stress_metrics["p95_ms"]
        recovery_events = self.stress_metrics.get("recovery_events", [])
        
        stress_peak_p95 = max([event["peak_p95"] for event in recovery_events], default=stress_p95)
        recovery_times = [event["recovery_time_sec"] for event in recovery_events 
                         if event["recovery_time_sec"] is not None]
        
        enhanced_report = {
            "evaluation_date": datetime.now().isoformat(),
            "configuration": config,
            "assertions": assertions,
            "baseline_summary": {
                "total_queries": self.baseline_metrics["total_queries"],
                "successful_queries": self.baseline_metrics["successful_queries"],
                "p95_ms": self.baseline_metrics["p95_ms"],
                "p99_ms": self.baseline_metrics["p99_ms"],
                "mean_latency_ms": self.baseline_metrics["mean_latency_ms"],
                "violation_rate": self.baseline_metrics["violation_rate"],
                "autotuner_actions": self.baseline_metrics["autotuner_actions_count"],
                "runtime_seconds": self.baseline_metrics["runtime_seconds"]
            },
            "stress_summary": {
                "total_queries": self.stress_metrics["total_queries"],
                "successful_queries": self.stress_metrics["successful_queries"],
                "p95_ms": self.stress_metrics["p95_ms"],
                "p99_ms": self.stress_metrics["p99_ms"],
                "mean_latency_ms": self.stress_metrics["mean_latency_ms"],
                "peak_p95_ms": stress_peak_p95,
                "violation_rate": self.stress_metrics["violation_rate"],
                "recovery_violation_rate": self.stress_metrics.get("recovery_violation_rate", 0.0),
                "autotuner_actions": self.stress_metrics["autotuner_actions_count"],
                "runtime_seconds": self.stress_metrics["runtime_seconds"],
                "recovery_events_count": len(recovery_events),
                "recovery_times": recovery_times,
                "avg_recovery_time": np.mean(recovery_times) if recovery_times else 0.0,
                "max_recovery_time": np.max(recovery_times) if recovery_times else 0.0
            },
            "comparison_metrics": {
                "p95_ratio": stress_p95 / baseline_p95 if baseline_p95 > 0 else 0,
                "peak_p95_ratio": stress_peak_p95 / baseline_p95 if baseline_p95 > 0 else 0,
                "queries_ratio": self.stress_metrics["total_queries"] / self.baseline_metrics["total_queries"],
                "actions_ratio": self.stress_metrics["autotuner_actions_count"] / max(self.baseline_metrics["autotuner_actions_count"], 1)
            },
            "overall_assessment": {
                "baseline_status": "PASS" if assertions["duration_ok"] else "FAIL",
                "stress_status": "PASS" if assertions["overall_pass"] else "FAIL",
                "system_resilience": "EXCELLENT" if all([assertions["recovery_time_ok"], assertions["recovery_violation_ok"], assertions["tuner_active"]]) else "NEEDS_IMPROVEMENT",
                "stress_impact": "SIGNIFICANT" if assertions["stress_effect"] else "MINIMAL",
                "recovery_performance": "GOOD" if assertions["recovery_time_ok"] and assertions["recovery_violation_ok"] else "POOR"
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(enhanced_report, f, indent=2)
        
        return enhanced_report

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enhanced A/B Analyzer for SmartSearchX")
    parser.add_argument("--baseline", required=True, help="Baseline results file")
    parser.add_argument("--stress", required=True, help="Stress results file")
    parser.add_argument("--config", required=True, help="Configuration file")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--charts", help="Charts output directory")
    parser.add_argument("--pdf", help="PDF report output file")
    
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # Create output directories
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    charts_dir = args.charts or str(output_dir / "charts")
    Path(charts_dir).mkdir(parents=True, exist_ok=True)
    
    # Create analyzer
    analyzer = EnhancedABAnalyzer(args.baseline, args.stress)
    
    print("📊 Generating enhanced comparison charts...")
    analyzer.create_timeline_charts(charts_dir)
    analyzer.create_recovery_analysis_charts(charts_dir)
    analyzer.create_comparison_charts(charts_dir)
    print(f"📈 Charts saved to: {charts_dir}")
    
    # Generate enhanced report
    print("📋 Generating enhanced diff report...")
    enhanced_report = analyzer.generate_enhanced_report(str(output_dir / "enhanced_diff_report.json"), config)
    print(f"📄 Enhanced report saved to: {output_dir / 'enhanced_diff_report.json'}")
    
    # Generate one-pager PDF if requested
    if args.pdf:
        print("📑 Generating one-pager PDF report...")
        analyzer.generate_one_pager_pdf(args.pdf, config)
        print(f"📚 One-pager PDF saved to: {args.pdf}")
    
    # Print summary
    print("\n🎯 Enhanced Evaluation Summary:")
    assertions = enhanced_report["assertions"]
    print(f"   Duration OK: {'✓' if assertions['duration_ok'] else '✗'}")
    print(f"   Stress Effect: {'✓' if assertions['stress_effect'] else '✗'}")
    print(f"   Recovery Time OK: {'✓' if assertions['recovery_time_ok'] else '✗'}")
    print(f"   Recovery Violation OK: {'✓' if assertions['recovery_violation_ok'] else '✗'}")
    print(f"   Tuner Active: {'✓' if assertions['tuner_active'] else '✗'}")
    print(f"   Overall Status: {enhanced_report['overall_assessment']['stress_status']}")
    print(f"   System Resilience: {enhanced_report['overall_assessment']['system_resilience']}")

if __name__ == "__main__":
    main()
