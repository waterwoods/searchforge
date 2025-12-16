#!/usr/bin/env python3
"""
offline_ecommerce_agent_eval.py - Offline Evaluation for Ecommerce After-Sales Agent

This script reads evaluation cases from a JSON file, runs the ecommerce agent
on each case, and computes simple metrics (pass rate, refund eligibility accuracy, etc.).

Usage:
    python -m experiments.offline_ecommerce_agent_eval \
        --cases-file experiments/data/ecommerce_eval_cases.json \
        --output-file experiments/results/eval_run_001.json

Features:
- Batch evaluation of agent on predefined test cases
- Simple pass/fail based on expected vs actual refund eligibility and amounts
- Summary statistics (total, passed, failed, pass rate)
- Detailed results saved to JSON output file
"""

import sys
import json
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ecommerce.schemas import EcommerceAgentRequest
from services.fiqa_api.ecommerce.graphs.ecommerce_agent_graph import run_ecommerce_agent

# Cost per token (USD) - can be overridden via env var
# Default: rough estimate for gpt-4o-mini (input: $0.15/1M, output: $0.60/1M)
# Using average of $0.0000004 per token as default
DEFAULT_COST_PER_TOKEN = float(os.getenv("LLM_COST_PER_TOKEN", "0.0000004"))


# ============================================================================
# Data Models
# ============================================================================

class EvalCase(TypedDict, total=False):
    """Evaluation case schema from JSON file."""
    id: str
    description: Optional[str]
    user_message: str
    order_id: str
    expected_refund_eligible: Optional[bool]
    expected_refund_amount: Optional[float]
    expected_error: bool


class EvalResult(TypedDict, total=False):
    """Evaluation result for a single case."""
    case_id: str
    passed: bool
    error: Optional[str]
    actual_refund_eligible: Optional[bool]
    actual_refund_amount: Optional[float]
    failure_reason: Optional[str]
    requires_manual_review: Optional[bool]  # Whether judge flagged for manual review
    total_tokens: Optional[int]  # Total tokens used across all LLM calls
    total_latency_ms: Optional[float]  # Total latency across all LLM calls
    total_cost_usd: Optional[float]  # Estimated cost in USD


# ============================================================================
# Evaluation Logic
# ============================================================================

def evaluate_case(case: EvalCase) -> EvalResult:
    """
    Evaluate a single test case by running the agent and comparing results.
    
    Args:
        case: Evaluation case containing user message, order ID, and expected results
    
    Returns:
        EvalResult with pass/fail status and actual values
    """
    case_id = case.get("id", "unknown")
    expected_error = case.get("expected_error", False)
    
    try:
        # Construct request
        request = EcommerceAgentRequest(
            user_message=case["user_message"],
            order_id=case["order_id"],
        )
        
        # Run agent
        state = run_ecommerce_agent(request)
        
        # Extract actual values from state
        actual_refund_eligible = state.get("refund_eligible")
        refund = state.get("refund")
        requires_manual_review = state.get("requires_manual_review", False)
        # If refund_eligible is False, treat amount as 0.0 (even if refund is None)
        if actual_refund_eligible is False and refund is None:
            actual_refund_amount = 0.0
        else:
            actual_refund_amount = refund.eligible_amount if refund else None
        
        # Extract LLM metrics from state
        llm_metrics = state.get("llm_metrics", [])
        total_tokens = sum(m.get("total_tokens", 0) for m in llm_metrics)
        total_latency_ms = sum(m.get("latency_ms", 0.0) for m in llm_metrics)
        total_cost_usd = total_tokens * DEFAULT_COST_PER_TOKEN
        
        # Handle expected error case
        if expected_error:
            # If we expected an error but agent completed successfully, it's a failure
            return EvalResult(
                case_id=case_id,
                passed=False,
                error=None,
                actual_refund_eligible=actual_refund_eligible,
                actual_refund_amount=actual_refund_amount,
                failure_reason="Expected error but agent completed successfully",
                requires_manual_review=requires_manual_review,
                total_tokens=total_tokens if total_tokens > 0 else None,
                total_latency_ms=total_latency_ms if total_latency_ms > 0 else None,
                total_cost_usd=total_cost_usd if total_cost_usd > 0 else None,
            )
        
        # Compare results
        expected_refund_eligible = case.get("expected_refund_eligible")
        expected_refund_amount = case.get("expected_refund_amount")
        
        passed = True
        failure_reasons = []
        
        # Check refund eligibility
        if expected_refund_eligible is not None:
            if actual_refund_eligible != expected_refund_eligible:
                passed = False
                failure_reasons.append(
                    f"expected eligible={expected_refund_eligible}, got {actual_refund_eligible}"
                )
        
        # Check refund amount (use small tolerance for floating point comparison)
        if expected_refund_amount is not None:
            if actual_refund_amount is None:
                passed = False
                failure_reasons.append(
                    f"expected amount={expected_refund_amount}, got None"
                )
            else:
                # Use tolerance of 0.01 for floating point comparison
                tolerance = 0.01
                if abs(actual_refund_amount - expected_refund_amount) > tolerance:
                    passed = False
                    failure_reasons.append(
                        f"expected amount={expected_refund_amount}, got {actual_refund_amount}"
                    )
        
        return EvalResult(
            case_id=case_id,
            passed=passed,
            error=None,
            actual_refund_eligible=actual_refund_eligible,
            actual_refund_amount=actual_refund_amount,
            failure_reason="; ".join(failure_reasons) if failure_reasons else None,
            requires_manual_review=requires_manual_review,
            total_tokens=total_tokens if total_tokens > 0 else None,
            total_latency_ms=total_latency_ms if total_latency_ms > 0 else None,
            total_cost_usd=total_cost_usd if total_cost_usd > 0 else None,
        )
    
    except Exception as e:
        # Handle exceptions
        if expected_error:
            # Expected an error and got one - this is a pass
            return EvalResult(
                case_id=case_id,
                passed=True,
                error=str(e),
                actual_refund_eligible=None,
                actual_refund_amount=None,
                failure_reason=None,
                requires_manual_review=None,
                total_tokens=None,
                total_latency_ms=None,
                total_cost_usd=None,
            )
        else:
            # Unexpected error - this is a failure
            return EvalResult(
                case_id=case_id,
                passed=False,
                error=str(e),
                actual_refund_eligible=None,
                actual_refund_amount=None,
                failure_reason=f"Unexpected error: {str(e)}",
                requires_manual_review=None,
                total_tokens=None,
                total_latency_ms=None,
                total_cost_usd=None,
            )


def run_eval(cases: List[EvalCase]) -> Dict[str, Any]:
    """
    Run evaluation on all test cases and compute summary statistics.
    
    Args:
        cases: List of evaluation cases
    
    Returns:
        Dictionary containing summary stats and detailed results
    """
    results: List[EvalResult] = []
    
    for case in cases:
        result = evaluate_case(case)
        results.append(result)
    
    # Compute statistics
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r.get("passed", False))
    failed_cases = total_cases - passed_cases
    pass_rate = (passed_cases / total_cases * 100) if total_cases > 0 else 0.0
    manual_review_cases = sum(1 for r in results if r.get("requires_manual_review", False))
    
    # Compute cost and latency statistics
    valid_tokens = [r.get("total_tokens") for r in results if r.get("total_tokens") is not None]
    valid_latency = [r.get("total_latency_ms") for r in results if r.get("total_latency_ms") is not None]
    valid_cost = [r.get("total_cost_usd") for r in results if r.get("total_cost_usd") is not None]
    
    sum_tokens = sum(valid_tokens) if valid_tokens else 0
    sum_latency_ms = sum(valid_latency) if valid_latency else 0.0
    sum_cost_usd = sum(valid_cost) if valid_cost else 0.0
    
    avg_tokens_per_case = (sum_tokens / len(valid_tokens)) if valid_tokens else 0.0
    avg_latency_ms_per_case = (sum_latency_ms / len(valid_latency)) if valid_latency else 0.0
    avg_cost_usd_per_case = (sum_cost_usd / len(valid_cost)) if valid_cost else 0.0
    
    return {
        "summary": {
            "total_cases": total_cases,
            "passed_cases": passed_cases,
            "failed_cases": failed_cases,
            "pass_rate": round(pass_rate, 2),
            "manual_review_cases": manual_review_cases,
            "sum_tokens": sum_tokens,
            "avg_tokens_per_case": round(avg_tokens_per_case, 2),
            "sum_latency_ms": round(sum_latency_ms, 2),
            "avg_latency_ms_per_case": round(avg_latency_ms_per_case, 2),
            "sum_cost_usd": round(sum_cost_usd, 6),
            "avg_cost_usd_per_case": round(avg_cost_usd_per_case, 6),
        },
        "results": results,
    }


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the evaluation script."""
    parser = argparse.ArgumentParser(
        description="Offline evaluation for ecommerce after-sales agent"
    )
    parser.add_argument(
        "--cases-file",
        type=str,
        default="experiments/data/ecommerce_eval_cases.json",
        help="Path to JSON file containing evaluation cases",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Optional path to save detailed results JSON file",
    )
    
    args = parser.parse_args()
    
    # Load cases
    cases_path = Path(args.cases_file)
    if not cases_path.exists():
        print(f"Error: Cases file not found: {cases_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(cases_path, "r", encoding="utf-8") as f:
        cases: List[EvalCase] = json.load(f)
    
    if not cases:
        print("Error: No cases found in file", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(cases)} evaluation cases from {cases_path}")
    print("Running evaluation...")
    
    # Run evaluation
    try:
        eval_results = run_eval(cases)
    except Exception as e:
        print(f"Error during evaluation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    summary = eval_results["summary"]
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Total cases:    {summary['total_cases']}")
    print(f"Passed cases:   {summary['passed_cases']}")
    print(f"Failed cases:   {summary['failed_cases']}")
    print(f"Pass rate:      {summary['pass_rate']:.2f}%")
    print(f"Manual review cases: {summary['manual_review_cases']}")
    print()
    print("Cost & Latency Summary:")
    print(f"  Total tokens:     {summary.get('sum_tokens', 0)}")
    print(f"  Avg tokens/case:   {summary.get('avg_tokens_per_case', 0.0):.2f}")
    print(f"  Total latency:     {summary.get('sum_latency_ms', 0.0):.2f} ms")
    print(f"  Avg latency/case: {summary.get('avg_latency_ms_per_case', 0.0):.2f} ms")
    print(f"  Total cost:        ${summary.get('sum_cost_usd', 0.0):.6f}")
    print(f"  Avg cost/case:     ${summary.get('avg_cost_usd_per_case', 0.0):.6f}")
    print("=" * 60)
    
    # Print failed cases
    failed_results = [r for r in eval_results["results"] if not r.get("passed", False)]
    if failed_results:
        print("\nFailed Cases:")
        print("-" * 60)
        for result in failed_results:
            print(f"  - {result['case_id']}: {result.get('failure_reason', 'Unknown reason')}")
    
    # Save detailed results if output file specified
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(eval_results, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results saved to: {output_path}")
    
    # Exit with non-zero code if any cases failed
    if summary["failed_cases"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

