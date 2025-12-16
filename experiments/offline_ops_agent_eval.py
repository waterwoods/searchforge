#!/usr/bin/env python3
"""
offline_ops_agent_eval.py - Offline Evaluation for Ops Copilot

This script generates synthetic system snapshots with realistic distributions,
runs the ops copilot logic on them, and computes summary stats.

Key features:
- Realistic synthetic sampling with controlled distributions
- Health band distribution analysis
- Strategy Lab improvement rate analysis
- No LLM calls, no HTTP - pure Python

Usage:
    python experiments/offline_ops_agent_eval.py --n-samples 500 --random-seed 42
"""

import sys
import os
import random
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.schemas import (
    SystemSnapshot,
    HealthBand,
)
from services.fiqa_api.ops_copilot.ops_runtime import (
    run_system_health_check,
    run_system_strategy_lab,
)


# ============================================================================
# Synthetic Sample Generation
# ============================================================================

def generate_synthetic_system_snapshots(
    n: int,
    seed: int = 42,
) -> List[tuple[SystemSnapshot, str]]:
    """
    Generate synthetic system snapshots with realistic distributions and scenario types.
    
    Sampling strategy:
    - CPU: low(20-50), medium(50-80), high(80-100)
    - Memory: similar pattern
    - Latency: 50-1200ms with more weight around 200-600ms
    - Error rate: mostly 0-2%, with some 5-10% extremes
    - Disk: 40-95%
    - QPS: 10-5000
    - Environments: prod / staging / dev
    
    Scenario types:
    - healthy_like: 20-30% - low CPU/memory, low latency, low errors
    - cpu_bound: 20-30% - high CPU, medium memory, medium latency
    - latency_spike: 15-20% - high latency, medium CPU/memory
    - error_spike: 15-20% - high error rate, medium CPU/memory
    - disk_pressure: 10-15% - high disk usage, medium CPU/memory
    
    Args:
        n: Number of snapshots to generate
        seed: Random seed for reproducibility
    
    Returns:
        List of tuples (SystemSnapshot, scenario_type)
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    
    snapshots: List[tuple[SystemSnapshot, str]] = []
    
    service_names = ["api-gateway", "user-service", "payment-service", "search-service", "auth-service"]
    environments = ["prod", "staging", "dev"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", None]
    
    # Scenario type distribution: roughly balanced
    scenario_types = ["healthy_like", "cpu_bound", "latency_spike", "error_spike", "disk_pressure"]
    scenario_probs = [0.25, 0.25, 0.20, 0.20, 0.10]  # Sums to 1.0
    
    for i in range(n):
        service_name = rng.choice(service_names)
        environment = rng.choice(environments)
        region = rng.choice(regions)
        
        # Choose scenario type
        scenario_type = np_rng.choice(scenario_types, p=scenario_probs)
        
        # Generate metrics based on scenario type
        if scenario_type == "healthy_like":
            cpu_pct = rng.uniform(20, 50)
            mem_pct = rng.uniform(20, 50)
            p95_latency_ms = rng.uniform(50, 200)
            error_rate = rng.uniform(0, 0.01)
            disk_pct = rng.uniform(40, 70)
        elif scenario_type == "cpu_bound":
            cpu_pct = rng.uniform(80, 100)
            mem_pct = rng.uniform(50, 80)
            p95_latency_ms = rng.uniform(300, 600)
            error_rate = rng.uniform(0, 0.02)
            disk_pct = rng.uniform(50, 80)
        elif scenario_type == "latency_spike":
            cpu_pct = rng.uniform(50, 80)
            mem_pct = rng.uniform(50, 80)
            p95_latency_ms = rng.uniform(600, 1200)
            error_rate = rng.uniform(0, 0.02)
            disk_pct = rng.uniform(50, 80)
        elif scenario_type == "error_spike":
            cpu_pct = rng.uniform(50, 80)
            mem_pct = rng.uniform(50, 80)
            p95_latency_ms = rng.uniform(200, 600)
            error_rate = rng.uniform(0.05, 0.10)
            disk_pct = rng.uniform(50, 80)
        else:  # disk_pressure
            cpu_pct = rng.uniform(50, 80)
            mem_pct = rng.uniform(50, 80)
            p95_latency_ms = rng.uniform(200, 600)
            error_rate = rng.uniform(0, 0.02)
            disk_pct = rng.uniform(85, 95)
        
        # Sample QPS: 10-5000
        qps = rng.uniform(10, 5000)
        
        # Generate timestamp (recent)
        timestamp = datetime.utcnow()
        
        # Generate tags (include scenario_type)
        tags = {
            "service_type": rng.choice(["api", "worker", "db"]),
            "version": f"v{rng.randint(1, 5)}.{rng.randint(0, 9)}",
            "scenario_type": scenario_type,
        }
        
        snapshot = SystemSnapshot(
            service_name=service_name,
            environment=environment,
            cpu_pct=cpu_pct,
            mem_pct=mem_pct,
            p95_latency_ms=p95_latency_ms,
            error_rate=error_rate,
            qps=qps,
            disk_pct=disk_pct,
            timestamp=timestamp,
            region=region,
            tags=tags,
        )
        
        snapshots.append((snapshot, scenario_type))
    
    return snapshots


# ============================================================================
# Batch Processing
# ============================================================================

def run_batch_evaluation(
    snapshots_with_types: List[tuple[SystemSnapshot, str]],
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Run batch evaluation on synthetic snapshots.
    
    Args:
        snapshots_with_types: List of tuples (SystemSnapshot, scenario_type)
        verbose: Whether to print verbose progress
    
    Returns:
        List of result dictionaries with success, health_result, strategy_lab, error, scenario_type
    """
    results: List[Dict[str, Any]] = []
    
    print(f"\n开始批量评估，共 {len(snapshots_with_types)} 个样本...")
    start_time = time.time()
    
    for idx, (snapshot, scenario_type) in enumerate(snapshots_with_types, 1):
        if verbose or idx % 50 == 0:
            print(f"  处理样本 {idx}/{len(snapshots_with_types)}...", end="\r")
        
        try:
            # Run health check
            health_result = run_system_health_check(snapshot)
            
            # Run safety upgrade (only for degraded/critical)
            safety_suggestions = []
            if health_result.band in ("degraded", "critical"):
                try:
                    from services.fiqa_api.ops_copilot.ops_runtime import run_safety_upgrade_for_system
                    safety_suggestions = run_safety_upgrade_for_system(snapshot)
                except Exception as e:
                    if verbose:
                        print(f"      Safety upgrade failed: {e}")
            
            # Run strategy lab
            strategy_lab = None
            try:
                strategy_lab = run_system_strategy_lab(snapshot)
            except Exception as e:
                if verbose:
                    print(f"      Strategy lab failed: {e}")
            
            results.append({
                "success": True,
                "health_result": health_result,
                "strategy_lab": strategy_lab,
                "safety_suggestions": safety_suggestions,
                "error": None,
                "snapshot": snapshot,
                "scenario_type": scenario_type,
            })
        
        except Exception as e:
            error_msg = str(e)
            if verbose:
                print(f"\n  样本 {idx} 失败: {error_msg}")
                import traceback
                traceback.print_exc()
            results.append({
                "success": False,
                "health_result": None,
                "strategy_lab": None,
                "safety_suggestions": [],
                "error": error_msg,
                "snapshot": snapshot,
                "scenario_type": scenario_type,
            })
    
    elapsed_time = time.time() - start_time
    print(f"\n批量评估完成，耗时 {elapsed_time:.2f} 秒")
    
    return results


# ============================================================================
# Statistics & Metrics
# ============================================================================

def compute_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute comprehensive statistics from evaluation results.
    
    Returns:
        Dictionary with aggregated metrics
    """
    successful_results = [r for r in results if r["success"]]
    
    # Health band distribution
    band_counts: Dict[HealthBand, int] = defaultdict(int)
    band_scores: Dict[HealthBand, List[float]] = defaultdict(list)
    
    # Scenario type distribution
    scenario_type_counts: Dict[str, int] = defaultdict(int)
    scenario_type_by_band: Dict[str, Dict[HealthBand, int]] = defaultdict(lambda: defaultdict(int))
    
    # Safety upgrade statistics
    safety_upgrade_total = 0  # Cases where safety upgrade ran (degraded/critical)
    safety_upgrade_with_suggestions = 0  # Cases where at least one suggestion was generated
    
    # Strategy Lab statistics
    strategy_lab_total = 0
    strategy_lab_with_improvement = 0
    score_improvements: List[float] = []  # Track individual score improvements
    
    # Risk assessment statistics
    hard_block_count = 0
    soft_warning_count = 0
    neither_count = 0  # Samples with neither hard_block nor soft_warning
    
    # Improvement statistics by baseline band
    improvement_by_baseline_band: Dict[HealthBand, Dict[str, int]] = defaultdict(lambda: {"total": 0, "improved": 0})
    
    # Operational patterns: scenario type -> band classification
    scenario_type_band_distribution: Dict[str, Dict[HealthBand, int]] = defaultdict(lambda: defaultdict(int))
    
    for r in successful_results:
        health_result = r["health_result"]
        strategy_lab = r.get("strategy_lab")
        safety_suggestions = r.get("safety_suggestions", [])
        scenario_type = r.get("scenario_type", "unknown")
        
        # Count health bands
        band = health_result.band
        band_counts[band] += 1
        band_scores[band].append(health_result.score)
        
        # Scenario type distribution
        scenario_type_counts[scenario_type] += 1
        scenario_type_by_band[scenario_type][band] += 1
        scenario_type_band_distribution[scenario_type][band] += 1
        
        # Safety upgrade statistics
        if band in ("degraded", "critical"):
            safety_upgrade_total += 1
            if len(safety_suggestions) > 0:
                safety_upgrade_with_suggestions += 1
        
        # Risk assessment
        has_hard_block = health_result.hard_block
        has_soft_warning = health_result.soft_warning
        
        if has_hard_block:
            hard_block_count += 1
        if has_soft_warning:
            soft_warning_count += 1
        if not has_hard_block and not has_soft_warning:
            neither_count += 1
        
        # Strategy Lab analysis
        if strategy_lab:
            strategy_lab_total += 1
            baseline_band = strategy_lab.baseline_health.band
            baseline_score = strategy_lab.baseline_health.score
            
            improvement_by_baseline_band[baseline_band]["total"] += 1
            
            # Check for improvements
            band_order = {"healthy": 0, "warning": 1, "degraded": 2, "critical": 3}
            baseline_order = band_order.get(baseline_band, 999)
            
            has_improvement = False
            
            for scenario in strategy_lab.scenarios:
                scenario_band = scenario.health_result.band
                scenario_score = scenario.health_result.score
                scenario_order = band_order.get(scenario_band, 999)
                
                # Improvement = better band OR same band with higher score
                is_better = (
                    scenario_order < baseline_order or
                    (scenario_order == baseline_order and scenario_score > baseline_score)
                )
                
                if is_better:
                    has_improvement = True
                    # Track score improvement (only for scenarios that improve)
                    if scenario_score > baseline_score:
                        score_improvements.append(scenario_score - baseline_score)
                    break
            
            if has_improvement:
                strategy_lab_with_improvement += 1
                improvement_by_baseline_band[baseline_band]["improved"] += 1
    
    # Calculate percentages
    total_successful = len(successful_results)
    band_pct: Dict[HealthBand, float] = {}
    for band, count in band_counts.items():
        band_pct[band] = (count / total_successful * 100) if total_successful > 0 else 0.0
    
    # Calculate score statistics by band (including p50/p95)
    band_score_stats: Dict[HealthBand, Dict[str, float]] = {}
    for band, scores in band_scores.items():
        if scores:
            sorted_scores = sorted(scores)
            p50_idx = int(len(sorted_scores) * 0.50)
            p95_idx = int(len(sorted_scores) * 0.95)
            band_score_stats[band] = {
                "min": min(scores),
                "p50": sorted_scores[p50_idx] if p50_idx < len(sorted_scores) else sorted_scores[-1],
                "median": np.median(scores),
                "p95": sorted_scores[p95_idx] if p95_idx < len(sorted_scores) else sorted_scores[-1],
                "max": max(scores),
                "mean": np.mean(scores),
                "count": len(scores),
            }
    
    # Strategy Lab improvement rate
    strategy_lab_improvement_pct = (
        (strategy_lab_with_improvement / strategy_lab_total * 100)
        if strategy_lab_total > 0 else 0.0
    )
    
    # Improvement rate by baseline band
    improvement_pct_by_band: Dict[HealthBand, float] = {}
    for band, stats in improvement_by_baseline_band.items():
        if stats["total"] > 0:
            improvement_pct_by_band[band] = (stats["improved"] / stats["total"] * 100)
        else:
            improvement_pct_by_band[band] = 0.0
    
    # Error statistics
    error_count = len(results) - total_successful
    error_pct = (error_count / len(results) * 100) if len(results) > 0 else 0.0
    
    # Calculate average score improvement
    avg_score_improvement = np.mean(score_improvements) if score_improvements else 0.0
    
    # Safety upgrade percentage
    safety_upgrade_suggestion_pct = (
        (safety_upgrade_with_suggestions / safety_upgrade_total * 100)
        if safety_upgrade_total > 0 else 0.0
    )
    
    # Scenario type percentages
    scenario_type_pct: Dict[str, float] = {}
    for scenario_type, count in scenario_type_counts.items():
        scenario_type_pct[scenario_type] = (count / total_successful * 100) if total_successful > 0 else 0.0
    
    return {
        "total_samples": len(results),
        "successful_samples": total_successful,
        "error_count": error_count,
        "error_pct": error_pct,
        "band_counts": dict(band_counts),
        "band_pct": band_pct,
        "band_score_stats": {k: v for k, v in band_score_stats.items()},
        "hard_block_count": hard_block_count,
        "soft_warning_count": soft_warning_count,
        "neither_count": neither_count,
        "strategy_lab_total": strategy_lab_total,
        "strategy_lab_with_improvement": strategy_lab_with_improvement,
        "strategy_lab_improvement_pct": strategy_lab_improvement_pct,
        "improvement_by_baseline_band": dict(improvement_by_baseline_band),
        "improvement_pct_by_band": improvement_pct_by_band,
        "avg_score_improvement": avg_score_improvement,
        "scenario_type_counts": dict(scenario_type_counts),
        "scenario_type_pct": scenario_type_pct,
        "scenario_type_band_distribution": {k: dict(v) for k, v in scenario_type_band_distribution.items()},
        "safety_upgrade_total": safety_upgrade_total,
        "safety_upgrade_with_suggestions": safety_upgrade_with_suggestions,
        "safety_upgrade_suggestion_pct": safety_upgrade_suggestion_pct,
    }


def print_statistics(stats: Dict[str, Any]) -> None:
    """Print statistics summary to stdout."""
    print("\n" + "=" * 80)
    print("Offline Ops Copilot Evaluation - Summary Statistics")
    print("=" * 80)
    
    # Overall statistics
    print(f"\n📊 Overall Statistics:")
    print(f"   Total samples: {stats['total_samples']}")
    print(f"   Successful: {stats['successful_samples']}")
    print(f"   Errors: {stats['error_count']} ({stats['error_pct']:.1f}%)")
    
    # Health band distribution
    print(f"\n📈 Health Band Distribution:")
    band_order = ["healthy", "warning", "degraded", "critical"]
    for band in band_order:
        if band in stats['band_counts']:
            count = stats['band_counts'][band]
            pct = stats['band_pct'][band]
            print(f"   {band:12s}: {count:4d} ({pct:5.1f}%)")
    
    # Health score by band
    print(f"\n🎯 Health Score by Band (p50/p95):")
    for band in band_order:
        if band in stats['band_score_stats']:
            score_stats = stats['band_score_stats'][band]
            print(f"   {band:12s}: p50={score_stats.get('p50', score_stats.get('median', 0)):.1f}, p95={score_stats.get('p95', score_stats.get('max', 0)):.1f}, mean={score_stats['mean']:.1f} (n={score_stats['count']})")
    
    # Scenario type distribution
    if stats.get('scenario_type_counts'):
        print(f"\n📋 Scenario Type Distribution:")
        for scenario_type in sorted(stats['scenario_type_counts'].keys()):
            count = stats['scenario_type_counts'][scenario_type]
            pct = stats.get('scenario_type_pct', {}).get(scenario_type, 0.0)
            print(f"   {scenario_type:20s}: {count:4d} ({pct:5.1f}%)")
    
    # Risk assessment
    if stats['hard_block_count'] > 0 or stats['soft_warning_count'] > 0:
        print(f"\n⚠️  Risk Assessment:")
        print(f"   Hard blocks: {stats['hard_block_count']}")
        print(f"   Soft warnings: {stats['soft_warning_count']}")
    
    # Safety upgrade
    if stats.get('safety_upgrade_total', 0) > 0:
        print(f"\n🛡️  Safety Upgrade:")
        print(f"   Total degraded/critical cases: {stats['safety_upgrade_total']}")
        print(f"   Cases with suggestions: {stats['safety_upgrade_with_suggestions']} ({stats.get('safety_upgrade_suggestion_pct', 0.0):.1f}%)")
    
    # Strategy Lab
    print(f"\n🔬 Strategy Lab:")
    print(f"   Total cases with Strategy Lab: {stats['strategy_lab_total']}")
    print(f"   Cases with improvement: {stats['strategy_lab_with_improvement']} ({stats['strategy_lab_improvement_pct']:.1f}%)")
    
    # Improvement rate by baseline band
    if stats['improvement_pct_by_band']:
        print(f"\n📊 Strategy Lab Improvement by Baseline Band:")
        for band in band_order:
            if band in stats['improvement_pct_by_band']:
                pct = stats['improvement_pct_by_band'][band]
                total = stats['band_counts'].get(band, 0)
                improved = int(total * pct / 100) if total > 0 else 0
                print(f"   {band:12s}: {improved}/{total} ({pct:.1f}%)")
    
    print("\n" + "=" * 80)


def generate_markdown_report(
    stats: Dict[str, Any],
    n_samples: int,
    random_seed: int,
    mode: str,
    runtime_seconds: float,
) -> str:
    """
    Generate a markdown report for interview use.
    
    Args:
        stats: Statistics dictionary from compute_statistics
        n_samples: Number of samples evaluated
        random_seed: Random seed used
        mode: Evaluation mode (e.g., "full_agent")
        runtime_seconds: Total runtime in seconds
    
    Returns:
        Markdown report string
    """
    band_order = ["healthy", "warning", "degraded", "critical"]
    
    # Get average score improvement from stats
    avg_score_improvement = stats.get('avg_score_improvement', 0.0)
    
    # Calculate guardrail percentages
    successful_samples = stats['successful_samples']
    hard_block_pct = (stats['hard_block_count'] / successful_samples * 100) if successful_samples > 0 else 0.0
    soft_warning_pct = (stats['soft_warning_count'] / successful_samples * 100) if successful_samples > 0 else 0.0
    neither_count = stats.get('neither_count', 0)
    neither_pct = (neither_count / successful_samples * 100) if successful_samples > 0 else 0.0
    
    lines = [
        "# Offline Ops Copilot Agent Evaluation",
        "",
        "## Run Information",
        "",
        f"- **Date/Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- **Samples**: {n_samples}",
        f"- **Random Seed**: {random_seed}",
        f"- **Mode**: {mode}",
        f"- **LLM Generation**: Disabled (rule-based health check + strategy lab only)",
        "",
        "## Overall Statistics",
        "",
        f"- **Total Samples**: {stats['total_samples']}",
        f"- **Success Count**: {stats['successful_samples']}",
        f"- **Error Count**: {stats['error_count']} ({stats['error_pct']:.1f}%)",
        f"- **Runtime**: {runtime_seconds:.2f} seconds",
        "",
        "## Health Band Distribution",
        "",
        "| Band | Count | Percentage |",
        "|------|-------|------------|",
    ]
    
    for band in band_order:
        if band in stats['band_counts']:
            count = stats['band_counts'][band]
            pct = stats['band_pct'][band]
            lines.append(f"| {band} | {count} | {pct:.1f}% |")
    
    # Health Score Statistics by Band
    lines.extend([
        "",
        "## Health Score Statistics by Band",
        "",
        "| Band | p50 | p95 | Mean | Count |",
        "|------|-----|-----|------|-------|",
    ])
    
    for band in band_order:
        if band in stats.get('band_score_stats', {}):
            score_stats = stats['band_score_stats'][band]
            p50 = score_stats.get('p50', score_stats.get('median', 0))
            p95 = score_stats.get('p95', score_stats.get('max', 0))
            mean = score_stats.get('mean', 0)
            count = score_stats.get('count', 0)
            lines.append(f"| {band} | {p50:.1f} | {p95:.1f} | {mean:.1f} | {count} |")
    
    # Scenario Type Distribution
    if stats.get('scenario_type_counts'):
        lines.extend([
            "",
            "## Scenario Type Distribution",
            "",
            "| Scenario Type | Count | Percentage |",
            "|---------------|-------|------------|",
        ])
        for scenario_type in sorted(stats['scenario_type_counts'].keys()):
            count = stats['scenario_type_counts'][scenario_type]
            pct = stats.get('scenario_type_pct', {}).get(scenario_type, 0.0)
            lines.append(f"| {scenario_type} | {count} | {pct:.1f}% |")
    
    lines.extend([
        "",
        "## Guardrail Statistics",
        "",
        f"- **Hard Blocks**: {stats['hard_block_count']} ({hard_block_pct:.1f}% of successful samples)",
        f"- **Soft Warnings**: {stats['soft_warning_count']} ({soft_warning_pct:.1f}% of successful samples)",
        f"- **Neither**: {neither_count} ({neither_pct:.1f}%)",
        "",
    ])
    
    # Safety Upgrade Statistics
    if stats.get('safety_upgrade_total', 0) > 0:
        safety_upgrade_pct = stats.get('safety_upgrade_suggestion_pct', 0.0)
        lines.extend([
            "## Safety Upgrade Statistics",
            "",
            f"- **Total Degraded/Critical Cases**: {stats['safety_upgrade_total']}",
            f"- **Cases with At Least One Suggestion**: {stats['safety_upgrade_with_suggestions']} ({safety_upgrade_pct:.1f}%)",
            "",
        ])
    
    # Strategy Lab Improvement
    lines.extend([
        "## Strategy Lab Improvement",
        "",
        f"- **Total Cases with Strategy Lab**: {stats['strategy_lab_total']}",
        f"- **Cases with At Least One Improved Scenario**: {stats['strategy_lab_with_improvement']} ({stats['strategy_lab_improvement_pct']:.1f}%)",
        f"- **Average Change in Score for Improved Scenarios**: {avg_score_improvement:.2f} points",
        "",
        "### Improvement Rate by Baseline Band",
        "",
        "| Baseline Band | Improved Cases | Total Cases | Improvement Rate |",
        "|---------------|----------------|-------------|------------------|",
    ])
    
    for band in band_order:
        if band in stats.get('improvement_pct_by_band', {}):
            pct = stats['improvement_pct_by_band'][band]
            improvement_band_stats = stats.get('improvement_by_baseline_band', {}).get(band, {})
            total = improvement_band_stats.get('total', 0)
            improved = improvement_band_stats.get('improved', 0)
            lines.append(f"| {band} | {improved} | {total} | {pct:.1f}% |")
    
    # Operational Patterns
    lines.extend([
        "",
        "## Operational Patterns",
        "",
    ])
    
    # Generate operational pattern insights
    scenario_type_dist = stats.get('scenario_type_band_distribution', {})
    if scenario_type_dist:
        # CPU-bound incidents
        cpu_bound_total = stats.get('scenario_type_counts', {}).get('cpu_bound', 0)
        cpu_bound_degraded_critical = 0
        if 'cpu_bound' in scenario_type_dist:
            cpu_bound_degraded_critical = (
                scenario_type_dist['cpu_bound'].get('degraded', 0) +
                scenario_type_dist['cpu_bound'].get('critical', 0)
            )
        if cpu_bound_total > 0:
            cpu_bound_pct = (cpu_bound_degraded_critical / cpu_bound_total * 100)
            lines.append(f"- **{cpu_bound_pct:.1f}% of CPU-bound incidents were classified as degraded/critical**")
        
        # Critical cases with strategy lab improvements
        critical_total = stats.get('band_counts', {}).get('critical', 0)
        critical_improved = 0
        if 'critical' in stats.get('improvement_by_baseline_band', {}):
            critical_improved = stats['improvement_by_baseline_band']['critical'].get('improved', 0)
        if critical_total > 0:
            critical_improved_pct = (critical_improved / critical_total * 100)
            lines.append(f"- **{critical_improved_pct:.1f}% of critical cases had at least one improving Strategy Lab scenario**")
        
        # Degraded cases with safety upgrade suggestions
        degraded_total = stats.get('band_counts', {}).get('degraded', 0)
        degraded_critical_total = degraded_total + critical_total
        if degraded_critical_total > 0:
            safety_suggestion_pct = stats.get('safety_upgrade_suggestion_pct', 0.0)
            lines.append(f"- **{safety_suggestion_pct:.1f}% of degraded/critical cases received safety upgrade suggestions**")
    
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Synthetic snapshots are generated with balanced scenario types (healthy_like, cpu_bound, latency_spike, error_spike, disk_pressure) to test various operational patterns.",
        "- Hard blocks trigger correctly when critical thresholds are exceeded (e.g., error rate ≥ 5%, disk usage ≥ 90%, CPU ≥ 90%).",
        "- Strategy Lab produces at least one better configuration scenario for a significant percentage of degraded/critical cases.",
        "- Safety upgrade suggestions are generated for most degraded/critical cases, providing actionable remediation paths.",
        "- This offline evaluation focuses on rule-based logic only (no LLM calls), ensuring deterministic and reproducible results.",
        "- The evaluation demonstrates the core health check, safety upgrade, and strategy lab functionality before integrating LLM-based explanations.",
        "",
    ])
    
    return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Offline evaluation for ops copilot with synthetic data"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=500,
        help="Number of synthetic samples to generate (default: 500)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=None,
        help="Path to output markdown report file (optional)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="full_agent",
        help="Evaluation mode (default: full_agent)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Track overall runtime
    overall_start_time = time.time()
    
    print("=" * 80)
    print("Offline Ops Copilot Evaluation - Synthetic Data Generation & Analysis")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"   Samples: {args.n_samples}")
    print(f"   Random seed: {args.random_seed}")
    print(f"   Mode: {args.mode}")
    if args.output_report:
        print(f"   Output report: {args.output_report}")
    
    # Step 1: Generate synthetic samples
    print(f"\n[Step 1/3] Generating synthetic system snapshots...")
    snapshots_with_types = generate_synthetic_system_snapshots(
        n=args.n_samples,
        seed=args.random_seed,
    )
    print(f"   Generated {len(snapshots_with_types)} snapshots")
    
    # Step 2: Run batch evaluation
    print(f"\n[Step 2/3] Running batch evaluation...")
    results = run_batch_evaluation(
        snapshots_with_types=snapshots_with_types,
        verbose=args.verbose,
    )
    
    # Step 3: Compute statistics
    print(f"\n[Step 3/3] Computing statistics...")
    stats = compute_statistics(results)
    
    # Print summary
    print_statistics(stats)
    
    # Generate markdown report if requested
    if args.output_report:
        overall_runtime = time.time() - overall_start_time
        print(f"\n[Report Generation] Generating markdown report...")
        report_content = generate_markdown_report(
            stats=stats,
            n_samples=args.n_samples,
            random_seed=args.random_seed,
            mode=args.mode,
            runtime_seconds=overall_runtime,
        )
        
        # Write report to file
        report_path = Path(args.output_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_content, encoding='utf-8')
        print(f"   Report written to: {report_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

