#!/usr/bin/env python3
"""
Compare Run1 (FAISS concurrency) vs Run2 (Qdrant service exact) results.

This script:
1. Auto-detects latest result folders from both runs
2. Extracts metrics for comparison
3. Computes overhead metrics
4. Generates visualizations and reports
5. Identifies the "sweet spot" concurrency level
"""

import json
import pathlib
import time
import warnings
from typing import Dict, Optional, Tuple
from glob import glob

import numpy as np
import matplotlib.pyplot as plt

# Suppress matplotlib warnings
warnings.filterwarnings('ignore')


def load_report_file(report_path: pathlib.Path) -> Dict:
    """Load YAML or JSON report file."""
    if report_path.suffix in ['.yaml', '.yml']:
        try:
            import yaml
            with open(report_path, 'r') as f:
                return yaml.safe_load(f)
        except ImportError:
            # Fall back to JSON if YAML not available
            pass
    
    # Try JSON
    with open(report_path, 'r') as f:
        return json.load(f)


def find_latest_run_dir(pattern: str) -> Optional[pathlib.Path]:
    """
    Find the latest directory matching the pattern, sorted by modification time.
    
    Args:
        pattern: Glob pattern like "reports/run1_faiss_concurrency/*"
    
    Returns:
        Path to latest directory, or None if not found
    """
    matches = glob(pattern)
    if not matches:
        return None
    
    # Convert to Path objects and get modification times
    paths_with_time = [
        (pathlib.Path(p), pathlib.Path(p).stat().st_mtime)
        for p in matches
        if pathlib.Path(p).is_dir()
    ]
    
    if not paths_with_time:
        return None
    
    # Sort by modification time (descending) and return the latest
    paths_with_time.sort(key=lambda x: x[1], reverse=True)
    return paths_with_time[0][0]


def extract_metrics(report_data: Dict, concurrency_levels: list) -> Dict[str, Dict[str, float]]:
    """
    Extract QPS and P95 metrics for specified concurrency levels.
    
    Args:
        report_data: Loaded report data (YAML/JSON)
        concurrency_levels: List of concurrency levels to extract (as strings)
    
    Returns:
        Dictionary mapping concurrency level to metrics dict
        Format: {level: {"qps_mean": float, "p95_mean_ms": float}}
    """
    metrics = {}
    concurrency_results = report_data.get("concurrency_results", {})
    
    for level in concurrency_levels:
        level_str = str(level)
        if level_str not in concurrency_results:
            continue
        
        result = concurrency_results[level_str]
        qps_mean = result.get("qps_mean", None)
        p95_mean_ms = result.get("p95_mean_ms", None)
        
        if qps_mean is not None and p95_mean_ms is not None:
            metrics[level_str] = {
                "qps_mean": float(qps_mean),
                "p95_mean_ms": float(p95_mean_ms)
            }
        else:
            warnings.warn(f"Missing metrics for concurrency level {level_str}")
    
    return metrics


def compute_overhead(metrics_run1: Dict[str, float], metrics_run2: Dict[str, float]) -> Dict[str, float]:
    """
    Compute overhead metrics.
    
    Args:
        metrics_run1: Metrics from Run1 {"qps_mean": float, "p95_mean_ms": float}
        metrics_run2: Metrics from Run2 {"qps_mean": float, "p95_mean_ms": float}
    
    Returns:
        Dictionary with overhead metrics:
        - latency_overhead: (p95_run2 - p95_run1) / p95_run1
        - qps_drop: (qps_run1 - qps_run2) / qps_run1
    """
    p95_run1 = metrics_run1.get("p95_mean_ms", 0)
    p95_run2 = metrics_run2.get("p95_mean_ms", 0)
    qps_run1 = metrics_run1.get("qps_mean", 0)
    qps_run2 = metrics_run2.get("qps_mean", 0)
    
    if p95_run1 == 0:
        latency_overhead = float('inf') if p95_run2 > 0 else 0.0
    else:
        latency_overhead = (p95_run2 - p95_run1) / p95_run1
    
    if qps_run1 == 0:
        qps_drop = 1.0 if qps_run2 < qps_run1 else 0.0
    else:
        qps_drop = (qps_run1 - qps_run2) / qps_run1
    
    return {
        "latency_overhead": latency_overhead,
        "qps_drop": qps_drop
    }


def get_sla_p95(manifest: Dict) -> float:
    """
    Extract SLA P95 from manifest or use default.
    
    Args:
        manifest: Report data that might contain SLA defaults
    
    Returns:
        SLA P95 threshold in milliseconds (default: 2.0)
    """
    sla_defaults = manifest.get("sla_defaults", {})
    
    # Check for various possible SLA fields
    if "p95_ms" in sla_defaults:
        return float(sla_defaults["p95_ms"])
    if "p95" in sla_defaults:
        return float(sla_defaults["p95"])
    if "latency_p95_ms" in sla_defaults:
        return float(sla_defaults["latency_p95_ms"])
    
    # Default to 2ms
    return 2.0


def find_sweet_spot(
    run1_metrics: Dict[str, Dict[str, float]],
    run2_metrics: Dict[str, Dict[str, float]],
    sla_p95_ms: float
) -> Tuple[Optional[str], Optional[str]]:
    """
    Find the "sweet spot" concurrency level = argmax QPS with p95 <= SLA.
    
    Args:
        run1_metrics: Metrics from Run1 by concurrency level
        run2_metrics: Metrics from Run2 by concurrency level
        sla_p95_ms: SLA P95 threshold in milliseconds
    
    Returns:
        Tuple of (sweet_spot_run1, sweet_spot_run2) concurrency levels
    """
    def find_sweet_spot_single(metrics: Dict[str, Dict[str, float]], run_name: str) -> Optional[str]:
        """Find sweet spot for a single run."""
        candidates = []
        for level, m in metrics.items():
            p95 = m.get("p95_mean_ms", float('inf'))
            qps = m.get("qps_mean", 0)
            if p95 <= sla_p95_ms:
                candidates.append((level, qps))
        
        if not candidates:
            return None
        
        # Return level with max QPS
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    sweet_spot_run1 = find_sweet_spot_single(run1_metrics, "Run1")
    sweet_spot_run2 = find_sweet_spot_single(run2_metrics, "Run2")
    
    return sweet_spot_run1, sweet_spot_run2


def generate_qps_vs_p95_plot(
    output_path: pathlib.Path,
    run1_metrics: Dict[str, Dict[str, float]],
    run2_metrics: Dict[str, Dict[str, float]]
):
    """
    Generate QPS vs P95 scatter/line plot.
    
    Args:
        output_path: Path to save the plot
        run1_metrics: Metrics from Run1 by concurrency level
        run2_metrics: Metrics from Run2 by concurrency level
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Extract data for Run1
    run1_levels = sorted(run1_metrics.keys(), key=int)
    run1_qps = [run1_metrics[level]["qps_mean"] for level in run1_levels]
    run1_p95 = [run1_metrics[level]["p95_mean_ms"] for level in run1_levels]
    
    # Extract data for Run2
    run2_levels = sorted(run2_metrics.keys(), key=int)
    run2_qps = [run2_metrics[level]["qps_mean"] for level in run2_levels]
    run2_p95 = [run2_metrics[level]["p95_mean_ms"] for level in run2_levels]
    
    # Plot scatter points with lines
    ax.plot(run1_p95, run1_qps, 'o-', linewidth=2.5, markersize=10, 
            label='Run1 (FAISS)', color='#2E86AB', alpha=0.8, zorder=3)
    ax.plot(run2_p95, run2_qps, 's-', linewidth=2.5, markersize=10,
            label='Run2 (Qdrant Service)', color='#A23B72', alpha=0.8, zorder=3)
    
    # Add labels for concurrency levels
    for i, level in enumerate(run1_levels):
        ax.annotate(f'C{level}', (run1_p95[i], run1_qps[i]),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=9, alpha=0.7)
    
    for i, level in enumerate(run2_levels):
        ax.annotate(f'C{level}', (run2_p95[i], run2_qps[i]),
                   xytext=(5, -15), textcoords='offset points',
                   fontsize=9, alpha=0.7)
    
    # Styling
    ax.set_xlabel('P95 Latency (ms)', fontsize=14, fontweight='bold')
    ax.set_ylabel('QPS (Queries Per Second)', fontsize=14, fontweight='bold')
    ax.set_title('QPS vs P95 Latency: FAISS vs Qdrant Service', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper right', fontsize=12, framealpha=0.9)
    
    # Set font sizes
    ax.tick_params(labelsize=11)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def generate_overhead_table(
    output_path: pathlib.Path,
    run1_metrics: Dict[str, Dict[str, float]],
    run2_metrics: Dict[str, Dict[str, float]],
    overheads: Dict[str, Dict[str, float]]
):
    """
    Generate markdown table with overhead metrics.
    
    Args:
        output_path: Path to save the markdown file
        run1_metrics: Metrics from Run1 by concurrency level
        run2_metrics: Metrics from Run2 by concurrency level
        overheads: Overhead metrics by concurrency level
    """
    levels = sorted(set(list(run1_metrics.keys()) + list(run2_metrics.keys())), key=int)
    
    lines = []
    lines.append("# Overhead Comparison: Run1 (FAISS) vs Run2 (Qdrant Service)\n")
    lines.append("| Concurrency | Run1 QPS | Run2 QPS | Run1 P95 (ms) | Run2 P95 (ms) | Latency Overhead | QPS Drop |")
    lines.append("|-------------|----------|----------|---------------|---------------|------------------|----------|")
    
    for level in levels:
        run1_data = run1_metrics.get(level, {})
        run2_data = run2_metrics.get(level, {})
        overhead = overheads.get(level, {})
        
        run1_qps = run1_data.get("qps_mean", 0)
        run2_qps = run2_data.get("qps_mean", 0)
        run1_p95 = run1_data.get("p95_mean_ms", 0)
        run2_p95 = run2_data.get("p95_mean_ms", 0)
        latency_oh = overhead.get("latency_overhead", 0)
        qps_drop = overhead.get("qps_drop", 0)
        
        # Format latency overhead as percentage
        if latency_oh == float('inf'):
            latency_oh_str = "∞"
        else:
            latency_oh_str = f"{latency_oh * 100:.1f}%"
        
        # Format QPS drop as percentage
        qps_drop_str = f"{qps_drop * 100:.1f}%"
        
        lines.append(
            f"| {level} | {run1_qps:.2f} | {run2_qps:.2f} | "
            f"{run1_p95:.4f} | {run2_p95:.4f} | {latency_oh_str} | {qps_drop_str} |"
        )
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def generate_csv_summary(
    output_path: pathlib.Path,
    run1_metrics: Dict[str, Dict[str, float]],
    run2_metrics: Dict[str, Dict[str, float]],
    overheads: Dict[str, Dict[str, float]]
):
    """
    Generate CSV summary with all raw values and computed deltas.
    
    Args:
        output_path: Path to save the CSV file
        run1_metrics: Metrics from Run1 by concurrency level
        run2_metrics: Metrics from Run2 by concurrency level
        overheads: Overhead metrics by concurrency level
    """
    levels = sorted(set(list(run1_metrics.keys()) + list(run2_metrics.keys())), key=int)
    
    lines = []
    # Header
    lines.append("concurrency,run1_qps_mean,run2_qps_mean,qps_delta,run1_p95_ms,run2_p95_ms,p95_delta_ms,latency_overhead_pct,qps_drop_pct")
    
    for level in levels:
        run1_data = run1_metrics.get(level, {})
        run2_data = run2_metrics.get(level, {})
        overhead = overheads.get(level, {})
        
        run1_qps = run1_data.get("qps_mean", 0)
        run2_qps = run2_data.get("qps_mean", 0)
        run1_p95 = run1_data.get("p95_mean_ms", 0)
        run2_p95 = run2_data.get("p95_mean_ms", 0)
        
        qps_delta = run2_qps - run1_qps
        p95_delta = run2_p95 - run1_p95
        latency_oh = overhead.get("latency_overhead", 0)
        qps_drop = overhead.get("qps_drop", 0)
        
        # Convert to percentages
        latency_oh_pct = latency_oh * 100 if latency_oh != float('inf') else float('inf')
        qps_drop_pct = qps_drop * 100
        
        lines.append(
            f"{level},{run1_qps:.2f},{run2_qps:.2f},{qps_delta:.2f},"
            f"{run1_p95:.4f},{run2_p95:.4f},{p95_delta:.4f},"
            f"{latency_oh_pct:.2f},{qps_drop_pct:.2f}"
        )
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    """Main execution function."""
    print("=" * 80)
    print("Run1 (FAISS) vs Run2 (Qdrant Service) Comparison")
    print("=" * 80)
    
    # Auto-detect latest folders
    print("\n[1/5] Auto-detecting latest result folders...")
    run1_dir = find_latest_run_dir("reports/run1_faiss_concurrency/*")
    run2_dir = find_latest_run_dir("reports/run2_qdrant_service_exact/*")
    
    if not run1_dir:
        raise FileNotFoundError("Could not find Run1 result directory")
    if not run2_dir:
        raise FileNotFoundError("Could not find Run2 result directory")
    
    print(f"  Run1 directory: {run1_dir}")
    print(f"  Run2 directory: {run2_dir}")
    
    # Find report files
    run1_report = None
    run2_report = None
    
    for suffix in ['.yaml', '.yml', '.json']:
        run1_candidate = run1_dir / f"run1_faiss_concurrency{suffix}"
        run2_candidate = run2_dir / f"run2_qdrant_service_exact{suffix}"
        
        if run1_candidate.exists():
            run1_report = run1_candidate
        if run2_candidate.exists():
            run2_report = run2_candidate
    
    # Alternative: look for any yaml/json file
    if not run1_report:
        candidates = list(run1_dir.glob("*.yaml")) + list(run1_dir.glob("*.yml")) + list(run1_dir.glob("*.json"))
        if candidates:
            run1_report = candidates[0]
    
    if not run2_report:
        candidates = list(run2_dir.glob("*.yaml")) + list(run2_dir.glob("*.yml")) + list(run2_dir.glob("*.json"))
        if candidates:
            run2_report = candidates[0]
    
    if not run1_report or not run1_report.exists():
        raise FileNotFoundError(f"Could not find Run1 report file in {run1_dir}")
    if not run2_report or not run2_report.exists():
        raise FileNotFoundError(f"Could not find Run2 report file in {run2_dir}")
    
    print(f"  Run1 report: {run1_report}")
    print(f"  Run2 report: {run2_report}")
    
    # Load reports
    print("\n[2/5] Loading report files...")
    run1_data = load_report_file(run1_report)
    run2_data = load_report_file(run2_report)
    
    # Extract metrics
    print("\n[3/5] Extracting metrics...")
    concurrency_levels = ["1", "4", "8", "16"]
    run1_metrics = extract_metrics(run1_data, concurrency_levels)
    run2_metrics = extract_metrics(run2_data, concurrency_levels)
    
    if not run1_metrics:
        raise ValueError("No metrics found in Run1 report")
    if not run2_metrics:
        raise ValueError("No metrics found in Run2 report")
    
    print(f"  Run1 metrics extracted for levels: {sorted(run1_metrics.keys(), key=int)}")
    print(f"  Run2 metrics extracted for levels: {sorted(run2_metrics.keys(), key=int)}")
    
    # Compute overheads
    print("\n[4/5] Computing overhead metrics...")
    overheads = {}
    all_levels = sorted(set(list(run1_metrics.keys()) + list(run2_metrics.keys())), key=int)
    
    for level in all_levels:
        run1_data = run1_metrics.get(level)
        run2_data = run2_metrics.get(level)
        
        if not run1_data or not run2_data:
            warnings.warn(f"Skipping level {level}: missing data in one or both runs")
            continue
        
        overheads[level] = compute_overhead(run1_data, run2_data)
        oh = overheads[level]
        print(f"  Level {level}: Latency overhead = {oh['latency_overhead']*100:.1f}%, "
              f"QPS drop = {oh['qps_drop']*100:.1f}%")
    
    # Create output directory
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = pathlib.Path(f"reports/compare/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[5/5] Generating outputs in: {output_dir}")
    
    # Generate plots
    plot_path = output_dir / "qps_vs_p95.png"
    generate_qps_vs_p95_plot(plot_path, run1_metrics, run2_metrics)
    print(f"  ✓ Saved plot: {plot_path}")
    
    # Generate overhead table
    table_path = output_dir / "overhead_table.md"
    generate_overhead_table(table_path, run1_metrics, run2_metrics, overheads)
    print(f"  ✓ Saved table: {table_path}")
    
    # Generate CSV summary
    csv_path = output_dir / "compare_summary.csv"
    generate_csv_summary(csv_path, run1_metrics, run2_metrics, overheads)
    print(f"  ✓ Saved CSV: {csv_path}")
    
    # Find sweet spot
    print("\n" + "=" * 80)
    print("Sweet Spot Analysis")
    print("=" * 80)
    
    sla_p95 = get_sla_p95(run2_data)  # Use Run2's manifest (should be same as Run1)
    print(f"SLA P95 threshold: {sla_p95} ms")
    
    sweet_spot_run1, sweet_spot_run2 = find_sweet_spot(run1_metrics, run2_metrics, sla_p95)
    
    if sweet_spot_run1:
        run1_sweet_data = run1_metrics[sweet_spot_run1]
        print(f"\nRun1 (FAISS) sweet spot: Concurrency = {sweet_spot_run1}")
        print(f"  QPS = {run1_sweet_data['qps_mean']:.2f}")
        print(f"  P95 = {run1_sweet_data['p95_mean_ms']:.4f} ms")
    else:
        print("\nRun1 (FAISS): No concurrency level found with P95 <= SLA")
    
    if sweet_spot_run2:
        run2_sweet_data = run2_metrics[sweet_spot_run2]
        print(f"\nRun2 (Qdrant Service) sweet spot: Concurrency = {sweet_spot_run2}")
        print(f"  QPS = {run2_sweet_data['qps_mean']:.2f}")
        print(f"  P95 = {run2_sweet_data['p95_mean_ms']:.4f} ms")
    else:
        print("\nRun2 (Qdrant Service): No concurrency level found with P95 <= SLA")
    
    print("\n" + "=" * 80)
    print("Comparison completed successfully!")
    print(f"Output directory: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()

