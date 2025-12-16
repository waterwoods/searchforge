#!/usr/bin/env python3
"""
ops_copilot_llm_eval.py - LLM Quality Evaluation for Ops Copilot
=================================================================

This script evaluates the quality of LLM-generated narratives and recommendations
from the Ops Copilot system. It uses a fixed set of test cases (healthy, degraded,
critical scenarios) and checks whether the LLM output includes key information like
service names, health bands, and actionable recommendations.

Usage:
    # Run with default 15 cases
    python experiments/ops_copilot_llm_eval.py

    # Run with specific number of cases (max 30)
    python experiments/ops_copilot_llm_eval.py --n-cases 10

    # Enable verbose output with full narrative/action samples
    python experiments/ops_copilot_llm_eval.py --n-cases 20 --verbose
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.schemas import SystemSnapshot
from services.fiqa_api.ops_copilot.graphs.system_health_graph import run_system_health_graph


# ========================================
# Test Case Construction
# ========================================

def build_eval_cases() -> List[SystemSnapshot]:
    """
    Build a fixed set of 20 evaluation cases covering healthy, degraded, and critical scenarios.
    
    Returns:
        List of SystemSnapshot instances (20 cases total)
    """
    cases = []
    base_timestamp = datetime.utcnow()
    
    # ========================================
    # HEALTHY Cases (4 cases)
    # ========================================
    
    # Healthy Case 1: api-gateway with low everything
    cases.append(SystemSnapshot(
        service_name="api-gateway",
        environment="prod",
        cpu_pct=25.0,
        mem_pct=35.0,
        p95_latency_ms=80.0,
        error_rate=0.0001,  # 0.01%
        qps=500.0,
        disk_pct=40.0,
        timestamp=base_timestamp,
        region="us-east-1",
        tags={"team": "platform", "tier": "critical"},
    ))
    
    # Healthy Case 2: search-api with moderate but safe metrics
    cases.append(SystemSnapshot(
        service_name="search-api",
        environment="prod",
        cpu_pct=45.0,
        mem_pct=50.0,
        p95_latency_ms=150.0,
        error_rate=0.0005,  # 0.05%
        qps=800.0,
        disk_pct=55.0,
        timestamp=base_timestamp,
        region="us-west-2",
        tags={"team": "search", "tier": "critical"},
    ))
    
    # Healthy Case 3: auth-service with very low error rate
    cases.append(SystemSnapshot(
        service_name="auth-service",
        environment="staging",
        cpu_pct=30.0,
        mem_pct=40.0,
        p95_latency_ms=100.0,
        error_rate=0.0002,  # 0.02%
        qps=300.0,
        disk_pct=45.0,
        timestamp=base_timestamp,
        region="eu-west-1",
        tags={"team": "security", "tier": "critical"},
    ))
    
    # Healthy Case 4: notifications service in dev environment
    cases.append(SystemSnapshot(
        service_name="notifications",
        environment="dev",
        cpu_pct=20.0,
        mem_pct=30.0,
        p95_latency_ms=60.0,
        error_rate=0.0003,  # 0.03%
        qps=100.0,
        disk_pct=35.0,
        timestamp=base_timestamp,
        region="us-east-1",
        tags={"team": "messaging", "tier": "standard"},
    ))
    
    # ========================================
    # DEGRADED Cases (8 cases)
    # ========================================
    
    # Degraded Case 1: payment-service with high CPU + memory (warning level)
    cases.append(SystemSnapshot(
        service_name="payment-service",
        environment="prod",
        cpu_pct=72.0,  # Warning
        mem_pct=76.0,  # Warning
        p95_latency_ms=280.0,
        error_rate=0.008,  # 0.8%
        qps=1200.0,
        disk_pct=68.0,
        timestamp=base_timestamp,
        region="us-east-1",
        tags={"team": "payments", "tier": "critical"},
    ))
    
    # Degraded Case 2: search-api with high latency + error rate
    cases.append(SystemSnapshot(
        service_name="search-api",
        environment="prod",
        cpu_pct=68.0,
        mem_pct=65.0,
        p95_latency_ms=450.0,  # Warning
        error_rate=0.018,  # 1.8% - Warning
        qps=1500.0,
        disk_pct=70.0,
        timestamp=base_timestamp,
        region="us-west-2",
        tags={"team": "search", "tier": "critical"},
    ))
    
    # Degraded Case 3: api-gateway with high memory + disk
    cases.append(SystemSnapshot(
        service_name="api-gateway",
        environment="prod",
        cpu_pct=65.0,
        mem_pct=82.0,  # Warning
        p95_latency_ms=250.0,
        error_rate=0.006,
        qps=900.0,
        disk_pct=82.0,  # Warning
        timestamp=base_timestamp,
        region="eu-west-1",
        tags={"team": "platform", "tier": "critical"},
    ))
    
    # Degraded Case 4: metrics-collector with high CPU
    cases.append(SystemSnapshot(
        service_name="metrics-collector",
        environment="prod",
        cpu_pct=78.0,  # Warning
        mem_pct=72.0,
        p95_latency_ms=200.0,
        error_rate=0.004,
        qps=2000.0,
        disk_pct=65.0,
        timestamp=base_timestamp,
        region="us-east-1",
        tags={"team": "observability", "tier": "standard"},
    ))
    
    # Degraded Case 5: auth-service with high error rate but normal resources
    cases.append(SystemSnapshot(
        service_name="auth-service",
        environment="prod",
        cpu_pct=55.0,
        mem_pct=60.0,
        p95_latency_ms=180.0,
        error_rate=0.022,  # 2.2% - Warning
        qps=600.0,
        disk_pct=58.0,
        timestamp=base_timestamp,
        region="us-west-2",
        tags={"team": "security", "tier": "critical"},
    ))
    
    # Degraded Case 6: notifications with high latency
    cases.append(SystemSnapshot(
        service_name="notifications",
        environment="prod",
        cpu_pct=62.0,
        mem_pct=68.0,
        p95_latency_ms=520.0,  # Warning
        qps=400.0,
        error_rate=0.012,  # 1.2% - Warning
        disk_pct=72.0,
        timestamp=base_timestamp,
        region="eu-west-1",
        tags={"team": "messaging", "tier": "standard"},
    ))
    
    # Degraded Case 7: payment-service with multiple warnings
    cases.append(SystemSnapshot(
        service_name="payment-service",
        environment="staging",
        cpu_pct=74.0,  # Warning
        mem_pct=79.0,  # Warning
        p95_latency_ms=380.0,  # Warning
        error_rate=0.009,
        qps=800.0,
        disk_pct=76.0,  # Warning
        timestamp=base_timestamp,
        region="us-east-1",
        tags={"team": "payments", "tier": "critical"},
    ))
    
    # Degraded Case 8: metrics-collector with high disk usage
    cases.append(SystemSnapshot(
        service_name="metrics-collector",
        environment="prod",
        cpu_pct=70.0,
        mem_pct=74.0,
        p95_latency_ms=240.0,
        error_rate=0.005,
        qps=1800.0,
        disk_pct=84.0,  # Warning
        timestamp=base_timestamp,
        region="us-west-2",
        tags={"team": "observability", "tier": "standard"},
    ))
    
    # ========================================
    # CRITICAL Cases (8 cases)
    # ========================================
    
    # Critical Case 1: payment-service with very high CPU + error rate
    cases.append(SystemSnapshot(
        service_name="payment-service",
        environment="prod",
        cpu_pct=94.0,  # Critical
        mem_pct=88.0,
        p95_latency_ms=920.0,  # Critical
        error_rate=0.068,  # 6.8% - Critical
        qps=2000.0,
        disk_pct=92.0,  # Critical
        timestamp=base_timestamp,
        region="us-east-1",
        tags={"team": "payments", "tier": "critical"},
    ))
    
    # Critical Case 2: search-api with extreme latency + high error rate
    cases.append(SystemSnapshot(
        service_name="search-api",
        environment="prod",
        cpu_pct=91.0,  # Critical
        mem_pct=93.0,  # Critical
        p95_latency_ms=1200.0,  # Critical
        error_rate=0.055,  # 5.5% - Critical
        qps=1800.0,
        disk_pct=85.0,
        timestamp=base_timestamp,
        region="us-west-2",
        tags={"team": "search", "tier": "critical"},
    ))
    
    # Critical Case 3: api-gateway with disk near full + high CPU
    cases.append(SystemSnapshot(
        service_name="api-gateway",
        environment="prod",
        cpu_pct=96.0,  # Critical
        mem_pct=91.0,  # Critical
        p95_latency_ms=850.0,  # Critical
        error_rate=0.048,  # 4.8% - Warning (close to critical)
        qps=1200.0,
        disk_pct=95.0,  # Critical
        timestamp=base_timestamp,
        region="eu-west-1",
        tags={"team": "platform", "tier": "critical"},
    ))
    
    # Critical Case 4: auth-service with extreme error rate
    cases.append(SystemSnapshot(
        service_name="auth-service",
        environment="prod",
        cpu_pct=88.0,
        mem_pct=85.0,
        p95_latency_ms=780.0,
        error_rate=0.095,  # 9.5% - Critical
        qps=700.0,
        disk_pct=88.0,
        timestamp=base_timestamp,
        region="us-east-1",
        tags={"team": "security", "tier": "critical"},
    ))
    
    # Critical Case 5: notifications with all metrics critical
    cases.append(SystemSnapshot(
        service_name="notifications",
        environment="prod",
        cpu_pct=93.0,  # Critical
        mem_pct=92.0,  # Critical
        p95_latency_ms=980.0,  # Critical
        error_rate=0.072,  # 7.2% - Critical
        qps=500.0,
        disk_pct=94.0,  # Critical
        timestamp=base_timestamp,
        region="us-west-2",
        tags={"team": "messaging", "tier": "standard"},
    ))
    
    # Critical Case 6: metrics-collector with high CPU + memory + disk
    cases.append(SystemSnapshot(
        service_name="metrics-collector",
        environment="prod",
        cpu_pct=95.0,  # Critical
        mem_pct=94.0,  # Critical
        p95_latency_ms=650.0,
        error_rate=0.038,  # 3.8%
        qps=2500.0,
        disk_pct=96.0,  # Critical
        timestamp=base_timestamp,
        region="eu-west-1",
        tags={"team": "observability", "tier": "standard"},
    ))
    
    # Critical Case 7: payment-service with extreme error rate + high latency
    cases.append(SystemSnapshot(
        service_name="payment-service",
        environment="prod",
        cpu_pct=87.0,
        mem_pct=89.0,
        p95_latency_ms=1100.0,  # Critical
        error_rate=0.110,  # 11% - Critical
        qps=1500.0,
        disk_pct=82.0,
        timestamp=base_timestamp,
        region="us-east-1",
        tags={"team": "payments", "tier": "critical"},
    ))
    
    # Critical Case 8: search-api with disk critical + high CPU
    cases.append(SystemSnapshot(
        service_name="search-api",
        environment="staging",
        cpu_pct=92.0,  # Critical
        mem_pct=88.0,
        p95_latency_ms=720.0,
        error_rate=0.042,  # 4.2%
        qps=1000.0,
        disk_pct=97.0,  # Critical
        timestamp=base_timestamp,
        region="us-west-2",
        tags={"team": "search", "tier": "critical"},
    ))
    
    return cases


# ========================================
# LLM Evaluation Result Data Class
# ========================================

@dataclass
class LlmEvalResult:
    """
    Result of LLM quality evaluation for a single test case.
    
    Attributes:
        case_id: Test case ID (1-based)
        service_name: Service name from snapshot
        band: Health band (healthy, warning, degraded, critical)
        score: Health score (0-100)
        has_narrative: Whether narrative exists and is non-empty
        mentions_service_name: Whether narrative mentions the service name
        mentions_band: Whether narrative mentions the health band
        actions_count: Number of recommended actions
        has_action_verbs: Whether at least one action contains action verbs
        is_high_risk: Whether the case is high risk (degraded/critical)
    """
    case_id: int
    service_name: str
    band: str
    score: float
    has_narrative: bool
    mentions_service_name: bool
    mentions_band: bool
    actions_count: int
    has_action_verbs: bool
    is_high_risk: bool


# ========================================
# LLM Evaluation Logic
# ========================================

# Action verb keywords to check for in recommended_actions
ACTION_VERBS = [
    "restart", "scale", "reduce", "increase", "throttle", "reroute",
    "investigate", "check", "roll back", "rollback", "add", "remove",
    "upgrade", "downgrade", "review", "monitor", "alert", "disable",
    "enable", "deploy", "redeploy", "migrate", "optimize", "tune",
]


def check_has_action_verbs(recommended_actions: List[str]) -> bool:
    """
    Check if at least one recommended action contains action verbs.
    
    Args:
        recommended_actions: List of recommended action strings
    
    Returns:
        True if at least one action contains an action verb
    """
    if not recommended_actions:
        return False
    
    for action in recommended_actions:
        action_lower = action.lower()
        for verb in ACTION_VERBS:
            if verb in action_lower:
                return True
    
    return False


def run_llm_eval(cases: List[SystemSnapshot], verbose: bool = False) -> List[LlmEvalResult]:
    """
    Run LLM evaluation on a list of test cases.
    
    Args:
        cases: List of SystemSnapshot instances
        verbose: Whether to print verbose debug information
    
    Returns:
        List of LlmEvalResult instances
    """
    results = []
    
    for idx, snapshot in enumerate(cases, 1):
        case_id = idx
        request_id = f"llm-eval-{case_id}"
        
        try:
            # Call run_system_health_graph
            result = run_system_health_graph(snapshot, request_id=request_id)
            
            # Extract key fields
            health_result = result.get("health_result")
            narrative = result.get("narrative")
            recommended_actions = result.get("recommended_actions", [])
            
            # Validate health_result exists
            if health_result is None:
                print(f"⚠️  [CASE {case_id:02d}] Missing health_result for {snapshot.service_name}", file=sys.stderr)
                # Create a minimal result with has_narrative=False
                results.append(LlmEvalResult(
                    case_id=case_id,
                    service_name=snapshot.service_name,
                    band="unknown",
                    score=0.0,
                    has_narrative=False,
                    mentions_service_name=False,
                    mentions_band=False,
                    actions_count=0,
                    has_action_verbs=False,
                    is_high_risk=False,
                ))
                continue
            
            band = health_result.band
            score = health_result.score
            
            # Check narrative quality
            has_narrative = bool(narrative and narrative.strip())
            
            mentions_service_name = False
            mentions_band = False
            if has_narrative:
                narrative_lower = narrative.lower()
                service_name_lower = snapshot.service_name.lower()
                
                # Check if service name appears in narrative
                mentions_service_name = service_name_lower in narrative_lower
                
                # Check if band word appears in narrative
                # Look for any of the band keywords
                band_keywords = ["healthy", "warning", "degraded", "critical"]
                for keyword in band_keywords:
                    if keyword in narrative_lower:
                        mentions_band = True
                        break
            
            # Check recommended actions
            actions_count = len(recommended_actions) if recommended_actions else 0
            has_action_verbs = check_has_action_verbs(recommended_actions)
            
            # Determine if high risk
            is_high_risk = band in ("degraded", "critical")
            
            # Build result
            eval_result = LlmEvalResult(
                case_id=case_id,
                service_name=snapshot.service_name,
                band=band,
                score=score,
                has_narrative=has_narrative,
                mentions_service_name=mentions_service_name,
                mentions_band=mentions_band,
                actions_count=actions_count,
                has_action_verbs=has_action_verbs,
                is_high_risk=is_high_risk,
            )
            
            results.append(eval_result)
            
        except Exception as e:
            print(f"⚠️  [CASE {case_id:02d}] Exception for {snapshot.service_name}: {e}", file=sys.stderr)
            # Create a minimal result with has_narrative=False
            results.append(LlmEvalResult(
                case_id=case_id,
                service_name=snapshot.service_name,
                band="error",
                score=0.0,
                has_narrative=False,
                mentions_service_name=False,
                mentions_band=False,
                actions_count=0,
                has_action_verbs=False,
                is_high_risk=False,
            ))
    
    return results


# ========================================
# Per-Case Result Printing
# ========================================

def print_case_result(result: LlmEvalResult, verbose: bool = False) -> None:
    """
    Print a human-readable summary of a single case result.
    
    Args:
        result: LlmEvalResult instance
        verbose: Whether to print verbose information (narrative snippet, action snippet)
    """
    # Format case header
    case_header = f"[CASE {result.case_id:02d}] {result.service_name} (band={result.band}, score={result.score:.1f})"
    print(case_header)
    
    # Narrative line
    narrative_status = "OK" if result.has_narrative else "MISSING"
    mentions_service_str = "YES" if result.mentions_service_name else "NO"
    mentions_band_str = "YES" if result.mentions_band else "NO"
    print(f"  - narrative: {narrative_status}, mentions service: {mentions_service_str}, mentions band: {mentions_band_str}")
    
    # Actions line
    has_verbs_str = "YES" if result.has_action_verbs else "NO"
    print(f"  - actions: {result.actions_count} (has action verbs: {has_verbs_str})")
    
    # Verbose mode: show snippets (not implemented in this version, placeholder)
    if verbose:
        # Could add narrative[:100] and first action here if we stored them
        pass


# ========================================
# Summary Report
# ========================================

def print_summary(results: List[LlmEvalResult]) -> None:
    """
    Print a summary report of all evaluation results.
    
    Args:
        results: List of LlmEvalResult instances
    """
    if not results:
        print("\n⚠️  No results to summarize.")
        return
    
    total_cases = len(results)
    
    # Narrative coverage
    has_narrative_count = sum(1 for r in results if r.has_narrative)
    mentions_service_count = sum(1 for r in results if r.mentions_service_name)
    mentions_band_count = sum(1 for r in results if r.mentions_band)
    
    # Action quality
    has_2plus_actions_count = sum(1 for r in results if r.actions_count >= 2)
    has_action_verbs_count = sum(1 for r in results if r.has_action_verbs)
    
    # High risk performance
    high_risk_cases = [r for r in results if r.is_high_risk]
    high_risk_count = len(high_risk_cases)
    high_risk_mentions_band_count = sum(1 for r in high_risk_cases if r.mentions_band)
    high_risk_has_action_verbs_count = sum(1 for r in high_risk_cases if r.has_action_verbs)
    
    print("\n" + "="*80)
    print("LLM Quality Evaluation Summary")
    print("="*80)
    print()
    
    print(f"Total test cases: {total_cases}")
    print()
    
    print("LLM Narrative Coverage:")
    print(f"  - {has_narrative_count}/{total_cases} cases have narrative ({has_narrative_count/total_cases*100:.1f}%)")
    print(f"  - {mentions_service_count}/{total_cases} narratives mention service name ({mentions_service_count/total_cases*100:.1f}%)")
    print(f"  - {mentions_band_count}/{total_cases} narratives mention health band ({mentions_band_count/total_cases*100:.1f}%)")
    print()
    
    print("Recommended Actions Quality:")
    print(f"  - {has_2plus_actions_count}/{total_cases} cases have ≥2 recommended actions ({has_2plus_actions_count/total_cases*100:.1f}%)")
    print(f"  - {has_action_verbs_count}/{total_cases} cases have at least one action verb ({has_action_verbs_count/total_cases*100:.1f}%)")
    print()
    
    if high_risk_count > 0:
        print(f"High-Risk Cases (degraded/critical): {high_risk_count}/{total_cases}")
        print(f"  - {high_risk_mentions_band_count}/{high_risk_count} narratives mention band ({high_risk_mentions_band_count/high_risk_count*100:.1f}%)")
        print(f"  - {high_risk_has_action_verbs_count}/{high_risk_count} have action verb recommendations ({high_risk_has_action_verbs_count/high_risk_count*100:.1f}%)")
    else:
        print("High-Risk Cases (degraded/critical): 0")
    print()
    
    # One-sentence summary
    useful_cases = has_narrative_count
    high_risk_action_ratio = high_risk_has_action_verbs_count / high_risk_count if high_risk_count > 0 else 1.0
    
    print(f"Overall: {useful_cases}/{total_cases} cases have useful LLM output, " +
          f"{high_risk_has_action_verbs_count}/{high_risk_count} high-risk cases include explicit action recommendations.")
    print()
    
    # Exit code logic
    narrative_coverage_ratio = has_narrative_count / total_cases if total_cases > 0 else 0.0
    
    if narrative_coverage_ratio < 0.8:
        print("⚠️  WARNING: Narrative coverage < 80%, LLM quality may be insufficient.")
    elif high_risk_action_ratio < 0.7:
        print("⚠️  WARNING: High-risk action verb coverage < 70%, LLM quality may be insufficient.")
    else:
        print("✅ LLM quality meets acceptance criteria.")
    print()


# ========================================
# Main Entry Point
# ========================================

def main() -> int:
    """
    Main entry point for LLM evaluation script.
    
    Returns:
        Exit code (0 = success, 1 = quality threshold not met)
    """
    parser = argparse.ArgumentParser(
        description="Evaluate LLM output quality for Ops Copilot system health checks"
    )
    parser.add_argument(
        "--n-cases",
        type=int,
        default=15,
        help="Number of test cases to run (default: 15, max: 30)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed per-case information",
    )
    
    args = parser.parse_args()
    
    # Validate n-cases
    if args.n_cases < 1:
        print("Error: --n-cases must be at least 1", file=sys.stderr)
        return 1
    if args.n_cases > 30:
        print("Error: --n-cases must be at most 30", file=sys.stderr)
        return 1
    
    # Build all evaluation cases
    all_cases = build_eval_cases()
    
    # Take subset if requested
    cases_to_run = all_cases[:args.n_cases]
    
    print("="*80)
    print("Ops Copilot LLM Quality Evaluation")
    print("="*80)
    print(f"Running {len(cases_to_run)} test cases...")
    print()
    
    # Run evaluation
    results = run_llm_eval(cases_to_run, verbose=args.verbose)
    
    # Print per-case results
    for result in results:
        print_case_result(result, verbose=args.verbose)
    
    # Print summary
    print_summary(results)
    
    # Determine exit code based on quality metrics
    total_cases = len(results)
    has_narrative_count = sum(1 for r in results if r.has_narrative)
    narrative_coverage_ratio = has_narrative_count / total_cases if total_cases > 0 else 0.0
    
    high_risk_cases = [r for r in results if r.is_high_risk]
    high_risk_count = len(high_risk_cases)
    high_risk_has_action_verbs_count = sum(1 for r in high_risk_cases if r.has_action_verbs)
    high_risk_action_ratio = high_risk_has_action_verbs_count / high_risk_count if high_risk_count > 0 else 1.0
    
    # Exit with error if quality is insufficient
    if narrative_coverage_ratio < 0.8 or high_risk_action_ratio < 0.7:
        print("="*80)
        print("❌ LLM quality evaluation FAILED")
        print("="*80)
        return 1
    
    print("="*80)
    print("✅ LLM quality evaluation PASSED")
    print("="*80)
    return 0


if __name__ == "__main__":
    sys.exit(main())


