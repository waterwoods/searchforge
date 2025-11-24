#!/usr/bin/env python3
"""
offline_agent_eval.py - Refined Offline Evaluation for Mortgage Agent

This script generates synthetic borrower + home samples with realistic distributions,
runs the full (or near-full) mortgage agent logic on them, and computes summary stats.

Key features:
- Realistic synthetic sampling with controlled distributions
- Stress band distribution analysis
- ApprovalScore vs band statistics
- Strategy Lab improvement rate analysis
- Optional markdown report generation
- LLM disabled for offline eval (no OpenAI dependency)

Usage:
    python experiments/offline_agent_eval.py --n-samples 500 --mode hybrid_approval --output-report report.md
"""

import sys
import os
import random
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from statistics import mean, median
from datetime import datetime

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# IMPORTANT: Disable LLM generation for offline eval
# This ensures the experiment exercises rules + ML ApprovalScore, risk assessment,
# safety upgrade and Strategy Lab, but does not depend on OpenAI availability/latency/cost.
os.environ["LLM_GENERATION_ENABLED"] = "false"

from services.fiqa_api.mortgage import (
    run_stress_check,
    run_strategy_lab,
    run_safety_upgrade_flow,
    StressCheckRequest,
    StressCheckResponse,
    StrategyLabResult,
    StressBand,
)
from services.fiqa_api.mortgage.mortgage_agent_runtime import (
    run_single_home_agent,
    SingleHomeAgentRequest,
    SingleHomeAgentResponse,
)


# ============================================================================
# Configuration
# ============================================================================

# Mock ZIP codes and states used in existing tests
# These are covered by MOCK_LOCAL_LISTINGS and local_cost_factors
MOCK_ZIP_STATES = [
    ("90803", "CA"),  # Long Beach, CA
    ("92648", "CA"),  # Huntington Beach, CA
    ("90210", "CA"),  # Beverly Hills, CA
    ("73301", "TX"),  # Austin, TX
    ("78701", "TX"),  # Austin, TX
    ("98101", "WA"),  # Seattle, WA
    ("75001", "TX"),  # Dallas, TX
]


# ============================================================================
# Refined Synthetic Sample Generation
# ============================================================================

def generate_synthetic_samples(
    n_samples: int,
    random_seed: int = 42,
) -> List[StressCheckRequest]:
    """
    Generate synthetic borrower + home samples with realistic and controlled distribution.
    
    Sampling strategy:
    - Income bands: low (~50k-80k), mid (~80k-150k), high (~150k-300k) annually
    - Home price: mostly 2-8x annual income, with tail up to 10x for extreme cases
    - Down payment: mixture of 5-10%, 15-25%, and 30-40%
    - Other debts: uniform 0-1000, with small chance of 1500+
    - HOA: 0-400
    - Interest rate: 5-8% range, small tail to 9%
    - Location: random from supported states/ZIPs
    
    For ~50% of samples, bias towards "interesting" boundary region:
    - DTI ~30-60% (approximate via price/income ratio)
    - LTV ~70-100%
    
    For the other 50%, sample more broadly to cover loose and extreme high_risk cases.
    
    Args:
        n_samples: Number of samples to generate
        random_seed: Random seed for reproducibility
    
    Returns:
        List of StressCheckRequest objects
    """
    rng = random.Random(random_seed)
    np_rng = np.random.default_rng(random_seed)
    
    samples: List[StressCheckRequest] = []
    
    # Split samples: 50% boundary region, 50% broad
    n_boundary = n_samples // 2
    n_broad = n_samples - n_boundary
    
    # Generate boundary region samples (DTI ~30-60%, LTV ~70-100%)
    for i in range(n_boundary):
        zip_code, state = rng.choice(MOCK_ZIP_STATES)
        
        # Sample annual income in one of three bands, then convert to monthly
        income_band = np_rng.choice(["low", "mid", "high"], p=[0.3, 0.4, 0.3])
        if income_band == "low":
            annual_income = rng.uniform(50000, 80000)
        elif income_band == "mid":
            annual_income = rng.uniform(80000, 150000)
        else:  # high
            annual_income = rng.uniform(150000, 300000)
        
        income_monthly = annual_income / 12.0
        
        # Sample home price: target DTI ~30-60% and LTV ~70-100%
        # Approximate: home_price_multiplier ~ 3.5-7.0 for boundary region
        target_dti = rng.uniform(0.30, 0.60)
        target_ltv = rng.uniform(0.70, 1.00)
        
        # Rough approximation: monthly_payment ≈ home_price * (ltv * rate_factor + tax_ins_factor)
        # For 30-year at 6%: rate_factor ≈ 0.006, tax_ins ≈ 0.00125
        rate_factor = 0.006  # Approximate monthly rate factor
        tax_ins_factor = 0.00125  # Approximate monthly tax/ins factor
        
        # Solve: target_dti * income_monthly = (home_price * target_ltv * rate_factor) + (home_price * tax_ins_factor) + other_debts
        # Simplify: target_dti * income_monthly ≈ home_price * (target_ltv * rate_factor + tax_ins_factor)
        target_monthly_payment = target_dti * income_monthly
        denominator = target_ltv * rate_factor + tax_ins_factor
        if denominator > 0:
            home_price = target_monthly_payment / denominator
        else:
            home_price = annual_income * rng.uniform(3.5, 7.0)
        
        # Clamp to reasonable bounds
        home_price = max(150000, min(home_price, 3000000))
        
        # Compute down_payment_pct from target LTV
        down_payment_pct = 1.0 - target_ltv
        down_payment_pct = max(0.05, min(down_payment_pct, 0.40))
        
        # Sample other parameters
        if rng.random() < 0.1:  # 10% chance of high debt
            other_debts_monthly = rng.uniform(1000, 2000)
        else:
            other_debts_monthly = rng.uniform(0, 1000)
        
        hoa_monthly = rng.uniform(0, 400)
        
        # Interest rate: 5-8% mostly, small tail to 9%
        if rng.random() < 0.9:
            interest_rate_pct = rng.uniform(5.0, 8.0)
        else:
            interest_rate_pct = rng.uniform(8.0, 9.0)
        
        risk_preference = rng.choice(["conservative", "neutral", "aggressive"])
        
        samples.append(StressCheckRequest(
            monthly_income=income_monthly,
            other_debts_monthly=other_debts_monthly,
            list_price=home_price,
            down_payment_pct=down_payment_pct,
            zip_code=zip_code,
            state=state,
            hoa_monthly=hoa_monthly,
            risk_preference=risk_preference,
        ))
    
    # Generate broad samples (wider variety)
    for i in range(n_broad):
        zip_code, state = rng.choice(MOCK_ZIP_STATES)
        
        # Sample annual income in one of three bands
        income_band = np_rng.choice(["low", "mid", "high"], p=[0.3, 0.4, 0.3])
        if income_band == "low":
            annual_income = rng.uniform(50000, 80000)
        elif income_band == "mid":
            annual_income = rng.uniform(80000, 150000)
        else:  # high
            annual_income = rng.uniform(150000, 300000)
        
        income_monthly = annual_income / 12.0
        
        # Sample home price: 2-8x annual income mostly, tail up to 10x
        if rng.random() < 0.85:  # 85% in main range
            price_multiplier = rng.uniform(2.0, 8.0)
        else:  # 15% in tail
            price_multiplier = rng.uniform(8.0, 10.0)
        
        home_price = annual_income * price_multiplier
        home_price = max(150000, min(home_price, 3000000))
        
        # Sample down_payment_pct: mixture of 5-10%, 15-25%, 30-40%
        down_payment_choice = np_rng.choice(["low", "mid", "high"], p=[0.3, 0.4, 0.3])
        if down_payment_choice == "low":
            down_payment_pct = rng.uniform(0.05, 0.10)
        elif down_payment_choice == "mid":
            down_payment_pct = rng.uniform(0.15, 0.25)
        else:  # high
            down_payment_pct = rng.uniform(0.30, 0.40)
        
        # Sample other parameters
        if rng.random() < 0.1:  # 10% chance of high debt
            other_debts_monthly = rng.uniform(1000, 2000)
        else:
            other_debts_monthly = rng.uniform(0, 1000)
        
        hoa_monthly = rng.uniform(0, 400)
        
        # Interest rate: 5-8% mostly, small tail to 9%
        if rng.random() < 0.9:
            interest_rate_pct = rng.uniform(5.0, 8.0)
        else:
            interest_rate_pct = rng.uniform(8.0, 9.0)
        
        risk_preference = rng.choice(["conservative", "neutral", "aggressive"])
        
        samples.append(StressCheckRequest(
            monthly_income=income_monthly,
            other_debts_monthly=other_debts_monthly,
            list_price=home_price,
            down_payment_pct=down_payment_pct,
            zip_code=zip_code,
            state=state,
            hoa_monthly=hoa_monthly,
            risk_preference=risk_preference,
        ))
    
    # Shuffle samples
    rng.shuffle(samples)
    
    return samples


# ============================================================================
# Batch Processing
# ============================================================================

def run_batch_evaluation(
    samples: List[StressCheckRequest],
    mode: str = "hybrid_approval",
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Run batch evaluation on synthetic samples.
    
    Args:
        samples: List of StressCheckRequest samples
        mode: Evaluation mode ("rule_only", "hybrid_approval", "full_agent")
        verbose: Whether to print verbose progress
    
    Returns:
        List of result dictionaries with success, result, error, case
    """
    results: List[Dict[str, Any]] = []
    
    print(f"\n开始批量评估，共 {len(samples)} 个样本...")
    start_time = time.time()
    
    for idx, case in enumerate(samples, 1):
        if verbose or idx % 50 == 0:
            print(f"  处理样本 {idx}/{len(samples)}...", end="\r")
        
        try:
            if mode == "full_agent":
                # Use full agent (but LLM is disabled via env var)
                agent_req = SingleHomeAgentRequest(stress_request=case)
                agent_response: SingleHomeAgentResponse = run_single_home_agent(agent_req)
                
                result = {
                    "stress_result": agent_response.stress_result,
                    "safety_upgrade": agent_response.safety_upgrade,
                    "strategy_lab": agent_response.strategy_lab,
                }
            else:
                # Use direct function calls (same as offline_strategy_eval.py)
                stress_result = run_stress_check(case)
                
                safety_upgrade = None
                try:
                    safety_upgrade = run_safety_upgrade_flow(
                        req=case,
                        max_candidates=5,
                    )
                except Exception as e:
                    if verbose:
                        print(f"      Safety upgrade failed: {e}")
                
                strategy_lab = None
                try:
                    strategy_lab = run_strategy_lab(
                        req=case,
                        max_scenarios=3,
                    )
                except Exception as e:
                    if verbose:
                        print(f"      Strategy lab failed: {e}")
                
                result = {
                    "stress_result": stress_result,
                    "safety_upgrade": safety_upgrade,
                    "strategy_lab": strategy_lab,
                }
            
            results.append({
                "success": True,
                "result": result,
                "error": None,
                "case": case,
            })
        
        except Exception as e:
            error_msg = str(e)
            if verbose:
                print(f"\n  样本 {idx} 失败: {error_msg}")
                import traceback
                traceback.print_exc()
            results.append({
                "success": False,
                "result": None,
                "error": error_msg,
                "case": case,
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
    
    # Stress band distribution
    band_counts: Dict[StressBand, int] = defaultdict(int)
    band_scores: Dict[StressBand, List[float]] = defaultdict(list)
    
    # Strategy Lab statistics
    strategy_lab_total = 0
    strategy_lab_with_improvement = 0
    strategy_lab_price_changes: List[float] = []
    strategy_lab_down_payment_changes: List[float] = []
    
    # Risk assessment statistics
    hard_block_count = 0
    soft_warning_count = 0
    
    for r in successful_results:
        result = r["result"]
        stress_result: StressCheckResponse = result["stress_result"]
        case: StressCheckRequest = r["case"]
        
        # Count stress bands
        band = stress_result.stress_band
        band_counts[band] += 1
        
        # Collect approval scores
        if stress_result.approval_score:
            score = stress_result.approval_score.score
            band_scores[band].append(score)
        
        # Risk assessment
        if stress_result.risk_assessment:
            if stress_result.risk_assessment.hard_block:
                hard_block_count += 1
            if stress_result.risk_assessment.soft_warning:
                soft_warning_count += 1
        
        # Strategy Lab analysis
        strategy_lab: Optional[StrategyLabResult] = result.get("strategy_lab")
        if strategy_lab:
            strategy_lab_total += 1
            baseline_band = strategy_lab.baseline_stress_band
            baseline_dti = strategy_lab.baseline_dti
            baseline_list_price = case.list_price
            baseline_down_payment_pct = case.down_payment_pct or 0.20
            
            if baseline_band and baseline_dti is not None:
                # Check for improvements
                band_order = {"loose": 0, "ok": 1, "tight": 2, "high_risk": 3}
                baseline_order = band_order.get(baseline_band, 999)
                
                has_improvement = False
                best_price_change = 0.0
                best_down_payment_change = 0.0
                
                for scenario in strategy_lab.scenarios:
                    if scenario.stress_band and scenario.dti_ratio is not None:
                        scenario_order = band_order.get(scenario.stress_band, 999)
                        
                        # Improvement = better band OR same band with lower DTI
                        is_better = (
                            scenario_order < baseline_order or
                            (scenario_order == baseline_order and scenario.dti_ratio < baseline_dti)
                        )
                        
                        if is_better:
                            has_improvement = True
                            
                            # Track price and down payment changes
                            # Use price_delta_pct if available, otherwise compute from price_delta_abs
                            if scenario.price_delta_pct is not None:
                                price_change_pct = scenario.price_delta_pct * 100  # Convert to percentage
                                if price_change_pct < best_price_change:  # More negative = better
                                    best_price_change = price_change_pct
                            elif scenario.price_delta_abs is not None and baseline_list_price > 0:
                                price_change_pct = (scenario.price_delta_abs / baseline_list_price) * 100
                                if price_change_pct < best_price_change:
                                    best_price_change = price_change_pct
                            
                            if scenario.down_payment_pct is not None:
                                down_payment_change_pp = (scenario.down_payment_pct - baseline_down_payment_pct) * 100
                                if down_payment_change_pp > best_down_payment_change:  # More positive = better
                                    best_down_payment_change = down_payment_change_pp
                
                if has_improvement:
                    strategy_lab_with_improvement += 1
                    if best_price_change < 0:  # Only track negative changes
                        strategy_lab_price_changes.append(best_price_change)
                    if best_down_payment_change > 0:  # Only track positive changes
                        strategy_lab_down_payment_changes.append(best_down_payment_change)
    
    # Calculate percentages
    total_successful = len(successful_results)
    band_pct: Dict[StressBand, float] = {}
    for band, count in band_counts.items():
        band_pct[band] = (count / total_successful * 100) if total_successful > 0 else 0.0
    
    # Calculate approval score statistics by band
    band_score_stats: Dict[StressBand, Dict[str, float]] = {}
    for band, scores in band_scores.items():
        if scores:
            band_score_stats[band] = {
                "min": min(scores),
                "median": median(scores),
                "max": max(scores),
                "mean": mean(scores),
                "count": len(scores),
            }
    
    # Strategy Lab improvement rate
    strategy_lab_improvement_pct = (
        (strategy_lab_with_improvement / strategy_lab_total * 100)
        if strategy_lab_total > 0 else 0.0
    )
    
    # Average price/down payment changes
    avg_price_change = mean(strategy_lab_price_changes) if strategy_lab_price_changes else 0.0
    avg_down_payment_change = mean(strategy_lab_down_payment_changes) if strategy_lab_down_payment_changes else 0.0
    
    # Error statistics
    error_count = len(results) - total_successful
    error_pct = (error_count / len(results) * 100) if len(results) > 0 else 0.0
    
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
        "strategy_lab_total": strategy_lab_total,
        "strategy_lab_with_improvement": strategy_lab_with_improvement,
        "strategy_lab_improvement_pct": strategy_lab_improvement_pct,
        "avg_price_change_pct": avg_price_change,
        "avg_down_payment_change_pp": avg_down_payment_change,
    }


def print_statistics(stats: Dict[str, Any]) -> None:
    """Print statistics summary to stdout."""
    print("\n" + "=" * 80)
    print("Offline Agent Evaluation - Summary Statistics")
    print("=" * 80)
    
    # Overall statistics
    print(f"\n📊 Overall Statistics:")
    print(f"   Total samples: {stats['total_samples']}")
    print(f"   Successful: {stats['successful_samples']}")
    print(f"   Errors: {stats['error_count']} ({stats['error_pct']:.1f}%)")
    
    # Stress band distribution
    print(f"\n📈 Stress Band Distribution:")
    band_order = ["loose", "ok", "tight", "high_risk"]
    for band in band_order:
        if band in stats['band_counts']:
            count = stats['band_counts'][band]
            pct = stats['band_pct'][band]
            print(f"   {band:12s}: {count:4d} ({pct:5.1f}%)")
    
    # ApprovalScore by band
    print(f"\n🎯 ApprovalScore by Band (median):")
    for band in band_order:
        if band in stats['band_score_stats']:
            score_stats = stats['band_score_stats'][band]
            print(f"   {band:12s}: {score_stats['median']:.1f} (min={score_stats['min']:.1f}, max={score_stats['max']:.1f}, n={score_stats['count']})")
    
    # Risk assessment
    if stats['hard_block_count'] > 0 or stats['soft_warning_count'] > 0:
        print(f"\n⚠️  Risk Assessment:")
        print(f"   Hard blocks: {stats['hard_block_count']}")
        print(f"   Soft warnings: {stats['soft_warning_count']}")
    
    # Strategy Lab
    print(f"\n🔬 Strategy Lab:")
    print(f"   Total cases with Strategy Lab: {stats['strategy_lab_total']}")
    print(f"   Cases with improvement: {stats['strategy_lab_with_improvement']} ({stats['strategy_lab_improvement_pct']:.1f}%)")
    if stats['avg_price_change_pct'] < 0:
        print(f"   Avg price change for improved: {stats['avg_price_change_pct']:.1f}%")
    if stats['avg_down_payment_change_pp'] > 0:
        print(f"   Avg down payment change for improved: +{stats['avg_down_payment_change_pp']:.1f}pp")
    
    print("\n" + "=" * 80)


# ============================================================================
# Markdown Report Generation
# ============================================================================

def write_markdown_report(
    stats: Dict[str, Any],
    n_samples: int,
    random_seed: int,
    mode: str,
    output_path: str,
) -> None:
    """
    Write a markdown report with evaluation results.
    
    Args:
        stats: Statistics dictionary from compute_statistics
        n_samples: Number of samples evaluated
        random_seed: Random seed used
        mode: Evaluation mode
        output_path: Path to write the report
    """
    report_lines = []
    
    report_lines.append("# Offline Agent Evaluation Report\n")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_lines.append(f"**Samples:** {n_samples}\n")
    report_lines.append(f"**Random Seed:** {random_seed}\n")
    report_lines.append(f"**Mode:** {mode}\n")
    report_lines.append("\n---\n")
    
    # Overall statistics
    report_lines.append("## Overall Statistics\n")
    report_lines.append(f"- Total samples: {stats['total_samples']}\n")
    report_lines.append(f"- Successful: {stats['successful_samples']}\n")
    report_lines.append(f"- Errors: {stats['error_count']} ({stats['error_pct']:.1f}%)\n")
    report_lines.append("\n")
    
    # Stress band distribution
    report_lines.append("## Stress Band Distribution\n")
    report_lines.append("| Band | Count | Percentage |\n")
    report_lines.append("|------|-------|------------|\n")
    band_order = ["loose", "ok", "tight", "high_risk"]
    for band in band_order:
        if band in stats['band_counts']:
            count = stats['band_counts'][band]
            pct = stats['band_pct'][band]
            report_lines.append(f"| {band} | {count} | {pct:.1f}% |\n")
    report_lines.append("\n")
    
    # ApprovalScore by band
    report_lines.append("## ApprovalScore by Band\n")
    report_lines.append("| Band | Min | Median | Max | Count |\n")
    report_lines.append("|------|-----|--------|-----|-------|\n")
    for band in band_order:
        if band in stats['band_score_stats']:
            score_stats = stats['band_score_stats'][band]
            report_lines.append(
                f"| {band} | {score_stats['min']:.1f} | {score_stats['median']:.1f} | "
                f"{score_stats['max']:.1f} | {score_stats['count']} |\n"
            )
    report_lines.append("\n")
    
    # Strategy Lab
    report_lines.append("## Strategy Lab Improvement Statistics\n")
    report_lines.append(f"- Total cases with Strategy Lab: {stats['strategy_lab_total']}\n")
    report_lines.append(
        f"- Cases with at least one improved scenario: {stats['strategy_lab_with_improvement']} "
        f"({stats['strategy_lab_improvement_pct']:.1f}%)\n"
    )
    if stats['avg_price_change_pct'] < 0:
        report_lines.append(f"- Average price change for improved cases: {stats['avg_price_change_pct']:.1f}%\n")
    if stats['avg_down_payment_change_pp'] > 0:
        report_lines.append(
            f"- Average down payment change for improved cases: +{stats['avg_down_payment_change_pp']:.1f}pp\n"
        )
    report_lines.append("\n")
    
    # Interpretation placeholder
    report_lines.append("## Interpretation\n")
    report_lines.append("<!-- TODO: Add interpretation notes here -->\n")
    report_lines.append("\n")
    
    # Write to file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path_obj, "w", encoding="utf-8") as f:
        f.writelines(report_lines)
    
    print(f"\n✅ Markdown report written to: {output_path}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Offline evaluation for mortgage agent with synthetic data"
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
        "--mode",
        type=str,
        choices=["rule_only", "hybrid_approval", "full_agent"],
        default="hybrid_approval",
        help="Evaluation mode (default: hybrid_approval)",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=None,
        help="Optional path to write markdown report (e.g., docs/offline_agent_eval_report.md)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Offline Agent Evaluation - Synthetic Data Generation & Analysis")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"   Samples: {args.n_samples}")
    print(f"   Random seed: {args.random_seed}")
    print(f"   Mode: {args.mode}")
    print(f"   LLM Generation: DISABLED (offline eval mode)")
    if args.output_report:
        print(f"   Report output: {args.output_report}")
    
    # Step 1: Generate synthetic samples
    print(f"\n[Step 1/3] Generating synthetic samples...")
    samples = generate_synthetic_samples(
        n_samples=args.n_samples,
        random_seed=args.random_seed,
    )
    print(f"   Generated {len(samples)} samples")
    
    # Step 2: Run batch evaluation
    print(f"\n[Step 2/3] Running batch evaluation...")
    results = run_batch_evaluation(
        samples=samples,
        mode=args.mode,
        verbose=args.verbose,
    )
    
    # Step 3: Compute statistics
    print(f"\n[Step 3/3] Computing statistics...")
    stats = compute_statistics(results)
    
    # Print summary
    print_statistics(stats)
    
    # Write markdown report if requested
    if args.output_report:
        write_markdown_report(
            stats=stats,
            n_samples=args.n_samples,
            random_seed=args.random_seed,
            mode=args.mode,
            output_path=args.output_report,
        )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

