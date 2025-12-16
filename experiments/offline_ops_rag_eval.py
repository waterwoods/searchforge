#!/usr/bin/env python3
"""
offline_ops_rag_eval.py - Offline RAG Evaluation for Ops Copilot

This script evaluates RAG retrieval quality by:
1. Running fixed test cases (service_name + symptom)
2. Checking if retrieved snippets match expected source files
3. Computing hit@k and top1 hit rates
4. Generating evaluation report

Usage:
    python experiments/offline_ops_rag_eval.py [--top-k 5] [--verbose]
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
from statistics import mean

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.ops_rag_retriever import retrieve_ops_knowledge

logging.basicConfig(
    level=logging.WARNING,  # Suppress verbose logs from retrieval
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("ops_rag_eval")


# ============================================================================
# Test Cases
# ============================================================================

# Fixed test cases: each case has service_name, symptom, and expected source file patterns
TEST_CASES = [
    # High error rate cases - should hit runbooks
    {
        "id": "case_001",
        "service_name": "payment-service",
        "symptom": "high_error_rate",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "Payment service high error rate",
    },
    {
        "id": "case_002",
        "service_name": "api-gateway",
        "symptom": "high_error_rate",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "API gateway high error rate",
    },
    {
        "id": "case_003",
        "service_name": "search-api",
        "symptom": "high_error_rate",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "Search API high error rate",
    },
    
    # High latency cases - should hit runbooks
    {
        "id": "case_004",
        "service_name": "payment-service",
        "symptom": "high_latency",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "Payment service high latency",
    },
    {
        "id": "case_005",
        "service_name": "auth-service",
        "symptom": "high_latency",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "Auth service high latency",
    },
    
    # High CPU cases - should hit runbooks
    {
        "id": "case_006",
        "service_name": "api-gateway",
        "symptom": "high_cpu",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "API gateway high CPU",
    },
    {
        "id": "case_007",
        "service_name": "metrics-collector",
        "symptom": "high_cpu",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "Metrics collector high CPU",
    },
    
    # Disk near full - should hit runbooks
    {
        "id": "case_008",
        "service_name": "search-api",
        "symptom": "disk_near_full",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "Search API disk near full",
    },
    
    # Config-related cases - should hit configs
    {
        "id": "case_009",
        "service_name": "payment-service",
        "symptom": "retry_timeout",
        "expected_sources": ["configs", "configs.md"],
        "description": "Payment service retry timeout config",
    },
    {
        "id": "case_010",
        "service_name": "api-gateway",
        "symptom": "timeout_config",
        "expected_sources": ["configs", "configs.md"],
        "description": "API gateway timeout config",
    },
    
    # Incident-related cases - should hit incidents
    {
        "id": "case_011",
        "service_name": "payment-service",
        "symptom": "severe_outage",
        "expected_sources": ["incidents", "incidents.md"],
        "description": "Payment service severe outage",
    },
    {
        "id": "case_012",
        "service_name": "api-gateway",
        "symptom": "production_incident",
        "expected_sources": ["incidents", "incidents.md"],
        "description": "API gateway production incident",
    },
    
    # Lessons learned cases - should hit lessons_learned
    {
        "id": "case_013",
        "service_name": "search-api",
        "symptom": "lessons_learned",
        "expected_sources": ["lessons", "lessons_learned", "lessons_learned.md"],
        "description": "Search API lessons learned",
    },
    {
        "id": "case_014",
        "service_name": "payment-service",
        "symptom": "post_mortem",
        "expected_sources": ["lessons", "lessons_learned", "lessons_learned.md"],
        "description": "Payment service post-mortem",
    },
    
    # Slow queries - should hit runbooks
    {
        "id": "case_015",
        "service_name": "search-api",
        "symptom": "slow_queries",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "Search API slow queries",
    },
    
    # Memory issues - should hit runbooks
    {
        "id": "case_016",
        "service_name": "auth-service",
        "symptom": "high_memory",
        "expected_sources": ["runbooks", "runbooks.md"],
        "description": "Auth service high memory",
    },
]


# ============================================================================
# Evaluation Logic
# ============================================================================

def check_source_match(source_file: str, expected_sources: List[str]) -> bool:
    """
    Check if source_file matches any expected source pattern.
    
    Args:
        source_file: Actual source file name (e.g., "runbooks.md")
        expected_sources: List of expected patterns (e.g., ["runbooks", "runbooks.md"])
    
    Returns:
        True if source_file matches any expected pattern
    """
    source_lower = source_file.lower()
    for expected in expected_sources:
        if expected.lower() in source_lower:
            return True
    return False


def evaluate_case(
    case: Dict[str, Any],
    top_k: int = 5,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate a single test case.
    
    Args:
        case: Test case dictionary with service_name, symptom, expected_sources
        top_k: Number of results to retrieve
        verbose: Whether to print detailed information
    
    Returns:
        Dictionary with evaluation results
    """
    case_id = case["id"]
    service_name = case["service_name"]
    symptom = case["symptom"]
    expected_sources = case["expected_sources"]
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Case: {case_id}")
        print(f"Service: {service_name}, Symptom: {symptom}")
        print(f"Expected sources: {expected_sources}")
        print(f"{'='*60}")
    
    # Retrieve results
    try:
        results = retrieve_ops_knowledge(
            service_name=service_name,
            symptom=symptom,
            top_k=top_k,
        )
    except Exception as e:
        logger.error(f"Retrieval failed for {case_id}: {e}")
        return {
            "case_id": case_id,
            "service_name": service_name,
            "symptom": symptom,
            "expected_sources": expected_sources,
            "num_results": 0,
            "hit_at_k": False,
            "top1_hit": False,
            "avg_score": 0.0,
            "sources": [],
            "scores": [],
            "error": str(e),
        }
    
    num_results = len(results)
    
    # Check if index is available (empty results might indicate missing index)
    if num_results == 0:
        if verbose:
            print("⚠️  No results returned (index may not be available)")
        return {
            "case_id": case_id,
            "service_name": service_name,
            "symptom": symptom,
            "expected_sources": expected_sources,
            "num_results": 0,
            "hit_at_k": False,
            "top1_hit": False,
            "avg_score": 0.0,
            "sources": [],
            "scores": [],
            "index_unavailable": True,
        }
    
    # Extract sources and scores
    sources = [r.get("source_file", "unknown") for r in results]
    scores = [r.get("score", 0.0) for r in results]
    avg_score = mean(scores) if scores else 0.0
    
    # Check hit@k: any result in top_k matches expected?
    hit_at_k = any(
        check_source_match(source, expected_sources)
        for source in sources
    )
    
    # Check top1: first result matches expected?
    top1_hit = False
    if sources:
        top1_hit = check_source_match(sources[0], expected_sources)
    
    if verbose:
        print(f"Query: '{service_name} {symptom}'")
        print(f"Retrieved {num_results} results:")
        for i, (source, score) in enumerate(zip(sources, scores), 1):
            match_indicator = "✓" if check_source_match(source, expected_sources) else "✗"
            print(f"  {i}. {match_indicator} {source} (score: {score:.4f})")
        print(f"Hit@k: {hit_at_k}, Top1 hit: {top1_hit}, Avg score: {avg_score:.4f}")
    
    return {
        "case_id": case_id,
        "service_name": service_name,
        "symptom": symptom,
        "expected_sources": expected_sources,
        "num_results": num_results,
        "hit_at_k": hit_at_k,
        "top1_hit": top1_hit,
        "avg_score": avg_score,
        "sources": sources,
        "scores": scores,
        "index_unavailable": False,
    }


def run_evaluation(
    top_k: int = 5,
    verbose: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run evaluation on all test cases.
    
    Args:
        top_k: Number of results to retrieve per case
        verbose: Whether to print detailed information
    
    Returns:
        Tuple of (case_results, summary_stats)
    """
    print(f"Running RAG evaluation on {len(TEST_CASES)} test cases...")
    print(f"Top-k: {top_k}")
    
    case_results = []
    index_unavailable_count = 0
    
    for case in TEST_CASES:
        result = evaluate_case(case, top_k=top_k, verbose=verbose)
        case_results.append(result)
        
        if result.get("index_unavailable", False):
            index_unavailable_count += 1
    
    # Check if index is unavailable (all cases returned empty)
    if index_unavailable_count == len(TEST_CASES):
        print("\n❌ ERROR: Index appears to be unavailable.")
        print("   All test cases returned empty results.")
        print("   Please run: python experiments/build_ops_kb_index.py")
        return case_results, {"index_unavailable_count": index_unavailable_count}
    
    # Compute summary statistics
    valid_results = [r for r in case_results if not r.get("index_unavailable", False)]
    
    if not valid_results:
        return case_results, {}
    
    total_cases = len(valid_results)
    hit_at_k_count = sum(1 for r in valid_results if r["hit_at_k"])
    top1_hit_count = sum(1 for r in valid_results if r["top1_hit"])
    
    # Group by expected source type
    source_stats = defaultdict(lambda: {"total": 0, "hit_at_k": 0, "top1_hit": 0})
    
    for result in valid_results:
        # Determine source type from expected_sources
        expected = result["expected_sources"][0].lower()
        if "runbook" in expected:
            source_type = "runbooks"
        elif "config" in expected:
            source_type = "configs"
        elif "incident" in expected:
            source_type = "incidents"
        elif "lesson" in expected:
            source_type = "lessons_learned"
        else:
            source_type = "other"
        
        source_stats[source_type]["total"] += 1
        if result["hit_at_k"]:
            source_stats[source_type]["hit_at_k"] += 1
        if result["top1_hit"]:
            source_stats[source_type]["top1_hit"] += 1
    
    summary = {
        "total_cases": total_cases,
        "hit_at_k_count": hit_at_k_count,
        "top1_hit_count": top1_hit_count,
        "hit_at_k_rate": hit_at_k_count / total_cases if total_cases > 0 else 0.0,
        "top1_hit_rate": top1_hit_count / total_cases if total_cases > 0 else 0.0,
        "avg_num_results": mean([r["num_results"] for r in valid_results]) if valid_results else 0.0,
        "avg_score": mean([r["avg_score"] for r in valid_results]) if valid_results else 0.0,
        "source_stats": dict(source_stats),
        "index_unavailable_count": index_unavailable_count,
    }
    
    return case_results, summary


def print_summary(summary: Dict[str, Any]) -> None:
    """Print evaluation summary to console."""
    if not summary:
        return
    
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Total cases: {summary['total_cases']}")
    print(f"Hit@k rate: {summary['hit_at_k_rate']:.1%} ({summary['hit_at_k_count']}/{summary['total_cases']})")
    print(f"Top1 hit rate: {summary['top1_hit_rate']:.1%} ({summary['top1_hit_count']}/{summary['total_cases']})")
    print(f"Average results per query: {summary['avg_num_results']:.1f}")
    print(f"Average score: {summary['avg_score']:.4f}")
    
    if summary.get("source_stats"):
        print("\nBy Source Type:")
        for source_type, stats in sorted(summary["source_stats"].items()):
            hit_rate = stats["hit_at_k"] / stats["total"] if stats["total"] > 0 else 0.0
            top1_rate = stats["top1_hit"] / stats["total"] if stats["total"] > 0 else 0.0
            print(f"  {source_type}:")
            print(f"    Hit@k: {hit_rate:.1%} ({stats['hit_at_k']}/{stats['total']})")
            print(f"    Top1: {top1_rate:.1%} ({stats['top1_hit']}/{stats['total']})")


def generate_report(
    case_results: List[Dict[str, Any]],
    summary: Dict[str, Any],
    output_path: Optional[Path] = None,
) -> None:
    """
    Generate Markdown evaluation report.
    
    Args:
        case_results: List of case evaluation results
        summary: Summary statistics
        output_path: Optional path to write report (default: docs/ops_rag_eval_report.md)
    """
    if not summary:
        return
    
    if output_path is None:
        output_path = project_root / "docs" / "ops_rag_eval_report.md"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        "# Ops RAG Evaluation Report",
        f"**Generated:** {timestamp}",
        f"**Test Cases:** {summary['total_cases']}",
        f"**Top-k:** {len(case_results[0]['sources']) if case_results and case_results[0].get('sources') else 'N/A'}",
        "",
        "---",
        "## Overall Statistics",
        f"- Total cases: {summary['total_cases']}",
        f"- Hit@k rate: {summary['hit_at_k_rate']:.1%} ({summary['hit_at_k_count']}/{summary['total_cases']})",
        f"- Top1 hit rate: {summary['top1_hit_rate']:.1%} ({summary['top1_hit_count']}/{summary['total_cases']})",
        f"- Average results per query: {summary['avg_num_results']:.1f}",
        f"- Average score: {summary['avg_score']:.4f}",
        "",
    ]
    
    if summary.get("source_stats"):
        lines.extend([
            "## By Source Type",
            "",
            "| Source Type | Cases | Hit@k | Hit@k Rate | Top1 Hit | Top1 Rate |",
            "|-------------|-------|-------|------------|----------|-----------|",
        ])
        
        for source_type, stats in sorted(summary["source_stats"].items()):
            hit_rate = stats["hit_at_k"] / stats["total"] if stats["total"] > 0 else 0.0
            top1_rate = stats["top1_hit"] / stats["total"] if stats["total"] > 0 else 0.0
            lines.append(
                f"| {source_type} | {stats['total']} | {stats['hit_at_k']} | {hit_rate:.1%} | "
                f"{stats['top1_hit']} | {top1_rate:.1%} |"
            )
        
        lines.append("")
    
    lines.extend([
        "## Test Cases",
        "",
        "| Case ID | Service | Symptom | Expected | Hit@k | Top1 | Avg Score |",
        "|---------|---------|---------|----------|-------|------|-----------|",
    ])
    
    for result in case_results:
        if result.get("index_unavailable", False):
            continue
        
        expected_str = ", ".join(result["expected_sources"][:2])  # Show first 2
        hit_at_k_str = "✓" if result["hit_at_k"] else "✗"
        top1_str = "✓" if result["top1_hit"] else "✗"
        avg_score_str = f"{result['avg_score']:.3f}"
        
        lines.append(
            f"| {result['case_id']} | {result['service_name']} | {result['symptom']} | "
            f"{expected_str} | {hit_at_k_str} | {top1_str} | {avg_score_str} |"
        )
    
    lines.append("")
    lines.append("## Interpretation")
    lines.append("<!-- TODO: Add interpretation notes here -->")
    lines.append("")
    
    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    print(f"\n✅ Report written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Offline RAG evaluation for Ops Copilot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to retrieve per query (default: 5)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed information for each test case",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating Markdown report",
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    case_results, summary = run_evaluation(top_k=args.top_k, verbose=args.verbose)
    
    # Check if index is unavailable
    index_unavailable_count = summary.get("index_unavailable_count", 0)
    if index_unavailable_count == len(TEST_CASES):
        print("\n❌ ERROR: Index not available. Please run:")
        print("   python experiments/build_ops_kb_index.py")
        return 1
    
    # Print summary
    print_summary(summary)
    
    # Generate report
    if not args.no_report:
        generate_report(case_results, summary)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

