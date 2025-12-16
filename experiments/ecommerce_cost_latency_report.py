#!/usr/bin/env python3
"""
ecommerce_cost_latency_report.py - Cost and Latency Report Generator

Reads evaluation result JSON files and generates cost/latency summary reports.

Usage:
    python -m experiments.ecommerce_cost_latency_report \
        --eval-file experiments/results/ecommerce_eval_run_001.json \
        --output-file experiments/results/ecommerce_cost_latency_summary_001.json

This script extracts LLM cost and latency metrics from evaluation results
and generates a concise summary report.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional


def load_eval_results(eval_file: Path) -> Dict[str, Any]:
    """
    Load evaluation results from JSON file.
    
    Args:
        eval_file: Path to evaluation result JSON file
    
    Returns:
        Dictionary containing evaluation results
    """
    if not eval_file.exists():
        raise FileNotFoundError(f"Evaluation file not found: {eval_file}")
    
    with open(eval_file, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_cost_latency_summary(eval_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate cost and latency summary from evaluation results.
    
    Args:
        eval_results: Evaluation results dictionary with 'results' and 'summary' keys
    
    Returns:
        Dictionary containing cost/latency summary
    """
    results = eval_results.get("results", [])
    
    # Extract metrics from results
    valid_tokens = [r.get("total_tokens") for r in results if r.get("total_tokens") is not None]
    valid_latency = [r.get("total_latency_ms") for r in results if r.get("total_latency_ms") is not None]
    valid_cost = [r.get("total_cost_usd") for r in results if r.get("total_cost_usd") is not None]
    
    # Compute aggregates
    total_cases = len(results)
    cases_with_metrics = len(valid_tokens)
    
    sum_tokens = sum(valid_tokens) if valid_tokens else 0
    sum_latency_ms = sum(valid_latency) if valid_latency else 0.0
    sum_cost_usd = sum(valid_cost) if valid_cost else 0.0
    
    avg_tokens_per_case = (sum_tokens / len(valid_tokens)) if valid_tokens else 0.0
    avg_latency_ms_per_case = (sum_latency_ms / len(valid_latency)) if valid_latency else 0.0
    avg_cost_usd_per_case = (sum_cost_usd / len(valid_cost)) if valid_cost else 0.0
    
    # Compute min/max for additional insights
    min_tokens = min(valid_tokens) if valid_tokens else None
    max_tokens = max(valid_tokens) if valid_tokens else None
    min_latency_ms = min(valid_latency) if valid_latency else None
    max_latency_ms = max(valid_latency) if valid_latency else None
    min_cost_usd = min(valid_cost) if valid_cost else None
    max_cost_usd = max(valid_cost) if valid_cost else None
    
    return {
        "total_cases": total_cases,
        "cases_with_metrics": cases_with_metrics,
        "tokens": {
            "sum": sum_tokens,
            "avg_per_case": round(avg_tokens_per_case, 2),
            "min": min_tokens,
            "max": max_tokens,
        },
        "latency_ms": {
            "sum": round(sum_latency_ms, 2),
            "avg_per_case": round(avg_latency_ms_per_case, 2),
            "min": round(min_latency_ms, 2) if min_latency_ms is not None else None,
            "max": round(max_latency_ms, 2) if max_latency_ms is not None else None,
        },
        "cost_usd": {
            "sum": round(sum_cost_usd, 6),
            "avg_per_case": round(avg_cost_usd_per_case, 6),
            "min": round(min_cost_usd, 6) if min_cost_usd is not None else None,
            "max": round(max_cost_usd, 6) if max_cost_usd is not None else None,
        },
    }


def print_summary(summary: Dict[str, Any]):
    """
    Print cost and latency summary to console.
    
    Args:
        summary: Summary dictionary from generate_cost_latency_summary
    """
    print("=" * 60)
    print("Cost & Latency Summary Report")
    print("=" * 60)
    print(f"Total cases:        {summary['total_cases']}")
    print(f"Cases with metrics: {summary['cases_with_metrics']}")
    print()
    print("Tokens:")
    print(f"  Total:            {summary['tokens']['sum']:,}")
    print(f"  Avg per case:     {summary['tokens']['avg_per_case']:.2f}")
    if summary['tokens']['min'] is not None:
        print(f"  Min:              {summary['tokens']['min']}")
        print(f"  Max:              {summary['tokens']['max']}")
    print()
    print("Latency:")
    print(f"  Total:            {summary['latency_ms']['sum']:.2f} ms")
    print(f"  Avg per case:     {summary['latency_ms']['avg_per_case']:.2f} ms")
    if summary['latency_ms']['min'] is not None:
        print(f"  Min:              {summary['latency_ms']['min']:.2f} ms")
        print(f"  Max:              {summary['latency_ms']['max']:.2f} ms")
    print()
    print("Cost:")
    print(f"  Total:            ${summary['cost_usd']['sum']:.6f}")
    print(f"  Avg per case:     ${summary['cost_usd']['avg_per_case']:.6f}")
    if summary['cost_usd']['min'] is not None:
        print(f"  Min:              ${summary['cost_usd']['min']:.6f}")
        print(f"  Max:              ${summary['cost_usd']['max']:.6f}")
    print("=" * 60)


def main():
    """Main entry point for the cost/latency report script."""
    parser = argparse.ArgumentParser(
        description="Generate cost and latency summary report from evaluation results"
    )
    parser.add_argument(
        "--eval-file",
        type=str,
        required=True,
        help="Path to evaluation result JSON file",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Optional path to save summary JSON file",
    )
    
    args = parser.parse_args()
    
    # Load evaluation results
    eval_file = Path(args.eval_file)
    try:
        eval_results = load_eval_results(eval_file)
    except Exception as e:
        print(f"Error loading evaluation file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate summary
    try:
        summary = generate_cost_latency_summary(eval_results)
    except Exception as e:
        print(f"Error generating summary: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary to console
    print_summary(summary)
    
    # Save summary to file if output path specified
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "summary": summary,
            "results": eval_results.get("results", []),
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummary report saved to: {output_path}")


if __name__ == "__main__":
    main()
