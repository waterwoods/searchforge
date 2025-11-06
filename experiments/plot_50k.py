#!/usr/bin/env python3
"""
plot_50k.py - Generate plots for FiQA 50k suite results

Generates:
- recall@10 vs p95 scatter plot
- cost/request vs p95 scatter plot
- Pareto front visualization
- Benchmark table (CSV)
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import yaml


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_yaml_report(report_path: Path) -> Dict:
    """Load YAML report from fiqa_suite_runner.py."""
    with open(report_path, 'r') as f:
        return yaml.safe_load(f)


def estimate_cost_per_request(config: Dict) -> float:
    """
    Estimate cost per request in USD.
    
    Rough estimates:
    - Base vector search: $0.00001
    - BM25 (hybrid): +$0.00001
    - Reranker: +$0.001 (expensive!)
    """
    cost = 0.00001  # Base vector search
    
    if config.get("use_hybrid", False):
        cost += 0.00001  # BM25
    
    if config.get("rerank", False):
        cost += 0.001  # Reranker dominates cost
    
    return cost


def generate_plots(results_dir: Path, output_dir: Path) -> List[str]:
    """
    Generate plots from YAML report.
    
    Args:
        results_dir: Directory containing fiqa_suite.yaml
        output_dir: Directory to save plots
        
    Returns:
        List of generated plot file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find YAML report - try multiple patterns
    yaml_candidates = [
        results_dir / "fiqa_suite.yaml",
        results_dir / "fiqa_50k_suite.yaml",
        results_dir / "fiqa_50k_stage_a.yaml",
        results_dir / "fiqa_50k_stage_b.yaml",
        results_dir / ".." / "fiqa_suite.yaml",
    ]
    
    # Also try to find any YAML file in the directory
    yaml_path = None
    for candidate in yaml_candidates:
        if candidate.exists():
            yaml_path = candidate
            break
    
    # If still not found, search for any .yaml file in results_dir
    if not yaml_path:
        yaml_files = list(results_dir.glob("*.yaml"))
        if yaml_files:
            yaml_path = yaml_files[0]  # Use first YAML file found
    
    if not yaml_path:
        print(f"❌ No YAML report found in {results_dir}")
        return []
    
    print(f"Loading YAML report: {yaml_path}")
    report_data = load_yaml_report(yaml_path)
    
    # Extract configurations
    configs = report_data.get("configurations", [])
    
    if not configs:
        print(f"❌ No configurations found in report")
        return []
    
    generated = []
    
    # Prepare data
    names = []
    recalls = []
    p95s = []
    costs = []
    
    for cfg in configs:
        names.append(cfg.get("name", "Unknown"))
        
        metrics = cfg.get("metrics", {})
        recall_metric = metrics.get("recall_at_10", {})
        p95_metric = metrics.get("p95_ms", {})
        
        recalls.append(recall_metric.get("mean", 0.0))
        p95s.append(p95_metric.get("mean", 0.0))
        costs.append(estimate_cost_per_request(cfg.get("config", {})))
    
    # Create figure with 3 subplots
    fig = plt.figure(figsize=(18, 6))
    
    # Plot 1: recall@10 vs p95
    ax1 = fig.add_subplot(131)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, (name, recall, p95) in enumerate(zip(names, recalls, p95s)):
        ax1.scatter(p95, recall, s=300, label=name, color=colors[i % len(colors)], 
                   alpha=0.7, edgecolors='black', linewidths=2)
        ax1.annotate(name, (p95, recall), xytext=(10, 10), 
                    textcoords='offset points', fontsize=11, fontweight='bold')
    
    ax1.set_xlabel('P95 Latency (ms)', fontsize=12)
    ax1.set_ylabel('Recall@10', fontsize=12)
    ax1.set_title('Recall vs Latency Trade-off', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='lower right')
    
    # Plot 2: cost vs p95
    ax2 = fig.add_subplot(132)
    
    for i, (name, cost, p95) in enumerate(zip(names, costs, p95s)):
        ax2.scatter(p95, cost, s=300, label=name, color=colors[i % len(colors)], 
                   alpha=0.7, edgecolors='black', linewidths=2)
        ax2.annotate(name, (p95, cost), xytext=(10, 10), 
                    textcoords='offset points', fontsize=11, fontweight='bold')
    
    ax2.set_xlabel('P95 Latency (ms)', fontsize=12)
    ax2.set_ylabel('Cost/Request (USD)', fontsize=12)
    ax2.set_title('Cost vs Latency Trade-off', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
    ax2.legend(loc='upper right')
    
    # Plot 3: Pareto front (recall/cost vs p95)
    ax3 = fig.add_subplot(133)
    
    # Calculate efficiency score (higher is better): recall / cost
    efficiencies = []
    for recall, cost in zip(recalls, costs):
        efficiency = recall / max(cost, 0.000001)  # Avoid division by zero
        efficiencies.append(efficiency)
    
    max_efficiency = max(efficiencies) if efficiencies else 1.0
    
    for i, (name, eff, p95) in enumerate(zip(names, efficiencies, p95s)):
        # Normalize efficiency for visual size
        size = 300 * (eff / max_efficiency)
        ax3.scatter(p95, eff, s=size, label=name, color=colors[i % len(colors)], 
                   alpha=0.7, edgecolors='black', linewidths=2)
        ax3.annotate(name, (p95, eff), xytext=(10, 10), 
                    textcoords='offset points', fontsize=11, fontweight='bold')
    
    ax3.set_xlabel('P95 Latency (ms)', fontsize=12)
    ax3.set_ylabel('Efficiency (Recall / Cost)', fontsize=12)
    ax3.set_title('Pareto Front: Efficiency vs Latency', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper right')
    
    plt.tight_layout()
    
    # Save combined plot
    plot_path = output_dir / "fiqa_50k_analysis.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    generated.append(str(plot_path))
    print(f"Generated: {plot_path}")
    
    plt.close()
    
    # Generate CSV benchmark table
    csv_path = output_dir / "fiqa_50k_benchmark.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Config', 'Recall@10', 'P95_Latency_ms', 'QPS', 'Cost_Per_Request_USD', 
                        'Efficiency', 'Success_Rate'])
        
        for name, recall, p95, cost, eff in zip(names, recalls, p95s, costs, efficiencies):
            # Estimate QPS (rough: inversely proportional to latency)
            qps = 1000.0 / max(p95, 10.0)  # Rough QPS estimate
            
            writer.writerow([
                name,
                f"{recall:.4f}",
                f"{p95:.1f}",
                f"{qps:.2f}",
                f"{cost:.6f}",
                f"{eff:.0f}",
                "1.00"  # Assume success for now
            ])
    
    print(f"Generated: {csv_path}")
    generated.append(str(csv_path))
    
    return generated


def main():
    parser = argparse.ArgumentParser(description="Generate plots for FiQA 50k results")
    parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Directory containing fiqa_suite.yaml (default: find latest in reports/fiqa_suite/)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: reports/fiqa_50k/)"
    )
    parser.add_argument(
        "--in",
        dest="input_dir",
        type=str,
        default=None,
        help="Alias for --results-dir (for compatibility with Make targets)"
    )
    parser.add_argument(
        "--out",
        dest="out_dir",
        type=str,
        default=None,
        help="Alias for --output-dir (for compatibility with Make targets)"
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Repository root (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    # Handle aliases
    if args.input_dir:
        args.results_dir = args.input_dir
    if args.out_dir:
        args.output_dir = args.out_dir
    
    # Find repo root
    if args.repo_root:
        repo_root = Path(args.repo_root)
    else:
        repo_root = find_repo_root()
    
    # Determine results directory
    if args.results_dir:
        results_dir = Path(args.results_dir)
        if not results_dir.is_absolute():
            results_dir = repo_root / results_dir
    else:
        # Find latest timestamped directory
        reports_dir = repo_root / "reports" / "fiqa_suite"
        if reports_dir.exists():
            timestamps = sorted([d for d in reports_dir.iterdir() if d.is_dir()], reverse=True)
            if timestamps:
                results_dir = timestamps[0]
            else:
                print(f"❌ No timestamped directories found in {reports_dir}")
                return 1
        else:
            print(f"❌ Reports directory not found: {reports_dir}")
            return 1
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = repo_root / output_dir
    else:
        output_dir = repo_root / "reports" / "fiqa_50k"
    
    print("="*80)
    print("FiQA 50k Plotting")
    print("="*80)
    print(f"Repository root: {repo_root}")
    print(f"Results dir: {results_dir}")
    print(f"Output dir: {output_dir}")
    print("="*80)
    
    # Generate plots
    generated = generate_plots(results_dir, output_dir)
    
    if not generated:
        print("\n❌ No plots generated")
        return 1
    
    # Create README
    readme_path = output_dir / "README.md"
    git_sha = None
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=repo_root
        )
        if result.returncode == 0:
            git_sha = result.stdout.strip()
    except:
        pass
    
    with open(readme_path, 'w') as f:
        f.write("# FiQA 50k Results\n\n")
        f.write("## Generated Files\n\n")
        for path in generated:
            rel_path = Path(path).relative_to(output_dir) if Path(path).is_absolute() else path
            f.write(f"- `{rel_path}`\n")
        f.write("\n## Configuration\n\n")
        f.write("Experiment families:\n")
        f.write("- Baseline: Pure vector search\n")
        f.write("- +RRF: Hybrid BM25 + vector fusion\n")
        f.write("- +Rerank: Hybrid + gated reranking\n\n")
        f.write("## Git SHA\n\n")
        if git_sha:
            f.write(f"`{git_sha}`\n")
        else:
            f.write("Run `git rev-parse HEAD` to get the current commit SHA.\n")
    
    print(f"Generated: {readme_path}")
    
    print("\n" + "="*80)
    print("✅ Plotting complete!")
    print("="*80)
    print(f"Output directory: {output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

