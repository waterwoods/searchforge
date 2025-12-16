#!/usr/bin/env python3
"""
ops_copilot_demo.py - Demo Script for Ops Copilot

This script demonstrates the Ops Copilot with 3 fixed scenarios:
1. healthy_service: low CPU/memory, low latency, low errors
2. degraded_service: high CPU/memory/latency but not catastrophic
3. critical_service: very high CPU + high error_rate + disk_near_full

Usage:
    # Run all scenarios (default)
    python experiments/ops_copilot_demo.py

    # Run a single scenario
    python experiments/ops_copilot_demo.py --scenario healthy
    python experiments/ops_copilot_demo.py --scenario degraded
    python experiments/ops_copilot_demo.py --scenario critical

    # HTTP call to local server
    python experiments/ops_copilot_demo.py --use-http --base-url http://localhost:8001

    # Enable verbose debug output
    python experiments/ops_copilot_demo.py --verbose
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.schemas import SystemSnapshot


def create_healthy_snapshot() -> SystemSnapshot:
    """Create a healthy system snapshot - all metrics within safe thresholds."""
    return SystemSnapshot(
        service_name="api-gateway",
        environment="prod",
        cpu_pct=32.0,  # Well below 70% warning threshold
        mem_pct=48.0,  # Well below 75% warning threshold
        p95_latency_ms=120.0,  # Well below 300ms warning threshold
        error_rate=0.0002,  # 0.02% - well below 1% warning threshold
        qps=800.0,
        disk_pct=55.0,  # Well below 75% warning threshold
        timestamp=datetime.utcnow(),
        region="us-east-1",
        tags={"team": "platform", "tier": "critical"},
    )


def create_degraded_snapshot() -> SystemSnapshot:
    """Create a degraded system snapshot - multiple warnings but not critical."""
    return SystemSnapshot(
        service_name="search-api",
        environment="prod",
        cpu_pct=78.0,  # Above 70% warning, below 90% critical
        mem_pct=82.0,  # Above 75% warning, below 90% critical
        p95_latency_ms=450.0,  # Above 300ms warning, below 800ms critical
        error_rate=0.018,  # 1.8% - above 1% warning, below 5% critical
        qps=1500.0,
        disk_pct=82.0,  # Above 75% warning, below 90% critical
        timestamp=datetime.utcnow(),
        region="us-west-2",
        tags={"team": "search", "tier": "critical"},
    )


def create_critical_snapshot() -> SystemSnapshot:
    """Create a critical system snapshot - severe degradation requiring immediate action."""
    return SystemSnapshot(
        service_name="payment-service",
        environment="prod",
        cpu_pct=94.0,  # Above 90% critical threshold
        mem_pct=91.0,  # Above 90% critical threshold
        p95_latency_ms=950.0,  # Above 800ms critical threshold
        error_rate=0.065,  # 6.5% - above 5% critical threshold
        qps=2000.0,
        disk_pct=93.0,  # Above 90% critical threshold
        timestamp=datetime.utcnow(),
        region="eu-west-1",
        tags={"team": "payments", "tier": "critical"},
    )


def format_summary(result: dict, name: str, snapshot: SystemSnapshot, verbose: bool = False) -> str:
    """Format a human-readable mini report of the result."""
    health_result = result["health_result"]
    safety_suggestions = result.get("safety_suggestions", [])
    strategy_lab = result.get("strategy_lab")
    narrative = result.get("narrative", "")
    recommended_actions = result.get("recommended_actions", [])
    context = result.get("context")
    
    lines = []
    
    # Header
    lines.append("")
    lines.append("=" * 80)
    scenario_title = f"Scenario: {name} – {snapshot.service_name} ({snapshot.environment})"
    lines.append(scenario_title)
    lines.append("-" * 80)
    
    # Critical banner for critical scenarios
    if health_result.band == "critical" and health_result.hard_block:
        lines.append("!!! CRITICAL: Immediate attention required (hard_block = True)")
        lines.append("")
    elif health_result.band == "degraded":
        lines.append("System is degraded but still serving traffic; prioritize mitigation.")
        lines.append("")
    
    # Key metrics (human-friendly formatting)
    cpu_str = f"{snapshot.cpu_pct:.0f}%"
    mem_str = f"{snapshot.mem_pct:.0f}%"
    latency_str = f"{snapshot.p95_latency_ms:.0f}ms"
    error_rate_str = f"{snapshot.error_rate*100:.2f}%"
    
    lines.append(f"Health:       {health_result.band}  (score: {health_result.score:.1f})")
    lines.append(f"Key metrics:  CPU {cpu_str}, Mem {mem_str}, Latency p95 {latency_str}, Error rate {error_rate_str}")
    
    # Risk flags
    if health_result.risk_flags:
        risk_flags_str = ", ".join(health_result.risk_flags)
        lines.append(f"Risk flags:   {risk_flags_str}")
    else:
        lines.append(f"Risk flags:   (none)")
    
    # Hard block and soft warning
    lines.append(f"Hard block:   {health_result.hard_block}")
    lines.append(f"Soft warning: {health_result.soft_warning}")
    
    # Safety suggestions
    lines.append("")
    if safety_suggestions:
        lines.append("Safety suggestions:")
        for i, suggestion in enumerate(safety_suggestions[:3], 1):
            lines.append(f"  {i}) {suggestion.title}")
    else:
        lines.append("Safety suggestions:")
        lines.append("  - (none, system is already healthy)")
    
    # Strategy Lab - best scenario
    lines.append("")
    if strategy_lab and strategy_lab.scenarios:
        baseline_score = strategy_lab.baseline_health.score
        best_scenario = strategy_lab.scenarios[0]  # Already sorted by score
        score_delta = best_scenario.health_result.score - baseline_score
        
        lines.append("Strategy Lab – best scenario:")
        lines.append(f"  - Name: \"{best_scenario.title}\"")
        
        # Extract change info from description
        change_info = best_scenario.description
        if len(change_info) > 80:
            change_info = change_info[:77] + "..."
        lines.append(f"    Change: {change_info}")
        
        # New health result
        new_band = best_scenario.health_result.band
        new_score = best_scenario.health_result.score
        delta_str = f"(+{score_delta:.1f})" if score_delta > 0 else f"({score_delta:.1f})"
        lines.append(f"    New health: {new_band} (score: {new_score:.1f}) {delta_str}")
    else:
        lines.append("Strategy Lab – best scenario:")
        lines.append("  - (none generated)")
    
    # LLM summary
    lines.append("")
    if narrative:
        # Extract first 1-2 sentences
        sentences = narrative.split('.')
        summary = ('.'.join(sentences[:2]) + '.').strip() if len(sentences) > 1 else narrative
        if len(summary) > 200:
            summary = summary[:197] + "..."
        lines.append("LLM summary:")
        lines.append(f"  {summary}")
    else:
        lines.append("LLM summary:")
        lines.append("  (LLM generation disabled)")
    
    # Recommended actions
    lines.append("")
    if recommended_actions:
        lines.append("Recommended actions:")
        for i, action in enumerate(recommended_actions[:3], 1):
            lines.append(f"  {i}) {action}")
    else:
        lines.append("Recommended actions:")
        lines.append("  (none generated)")
    
    lines.append("")
    lines.append("=" * 80)
    
    # Verbose debug section
    if verbose:
        lines.append("")
        lines.append("--- Debug Information (--verbose mode) ---")
        lines.append("")
        lines.append("Full result JSON:")
        # Convert result to JSON-serializable format
        result_copy = dict(result)
        # Convert Pydantic models to dicts
        if "health_result" in result_copy:
            result_copy["health_result"] = result_copy["health_result"].model_dump() if hasattr(result_copy["health_result"], "model_dump") else dict(result_copy["health_result"])
        if "strategy_lab" in result_copy and result_copy["strategy_lab"]:
            result_copy["strategy_lab"] = result_copy["strategy_lab"].model_dump() if hasattr(result_copy["strategy_lab"], "model_dump") else dict(result_copy["strategy_lab"])
        if "safety_suggestions" in result_copy:
            result_copy["safety_suggestions"] = [s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in result_copy["safety_suggestions"]]
        
        lines.append(json.dumps(result_copy, indent=2, default=str))
        lines.append("")
        lines.append("=" * 80)
    
    return "\n".join(lines)


def run_direct_call(snapshot: SystemSnapshot, request_id: str) -> dict:
    """Run the graph directly via Python (no HTTP)."""
    from services.fiqa_api.ops_copilot.graphs.system_health_graph import run_system_health_graph
    
    result = run_system_health_graph(snapshot, request_id=request_id)
    return result


def run_http_call(snapshot: SystemSnapshot, base_url: str, request_id: str) -> dict:
    """Run via HTTP POST to the endpoint."""
    import requests
    
    url = f"{base_url.rstrip('/')}/api/ops-copilot/system-health"
    
    # Convert snapshot to dict
    snapshot_dict = snapshot.model_dump()
    snapshot_dict["timestamp"] = snapshot_dict["timestamp"].isoformat()
    
    try:
        response = requests.post(
            url,
            json=snapshot_dict,
            headers={"Content-Type": "application/json"},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Demo script for Ops Copilot with 3 fixed scenarios"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=["healthy", "degraded", "critical", "all"],
        default="all",
        help="Which scenario to run: healthy, degraded, critical, or all (default: all)",
    )
    parser.add_argument(
        "--use-http",
        action="store_true",
        help="Use HTTP POST instead of direct Python call",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8001",
        help="Base URL for HTTP requests (default: http://localhost:8001)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="local",
        help="Execution mode (default: local, for docs compatibility)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with full JSON debug information",
    )
    
    args = parser.parse_args()
    
    # Disable LLM if not explicitly enabled (for demo consistency)
    if not os.getenv("LLM_GENERATION_ENABLED"):
        os.environ["LLM_GENERATION_ENABLED"] = "false"
    
    # Define all scenarios
    all_scenarios = [
        ("healthy", "Healthy service", create_healthy_snapshot),
        ("degraded", "Degraded service", create_degraded_snapshot),
        ("critical", "Critical service", create_critical_snapshot),
    ]
    
    # Filter scenarios based on --scenario parameter
    if args.scenario == "all":
        scenarios = all_scenarios
    else:
        scenarios = [(key, name, fn) for key, name, fn in all_scenarios if key == args.scenario]
    
    # Print header
    print("="*80)
    print("Ops Copilot Demo")
    print("="*80)
    if args.use_http:
        print(f"Mode: HTTP POST to {args.base_url}")
    else:
        print("Mode: Direct Python call")
    
    if args.scenario != "all":
        print(f"Scenario filter: {args.scenario}")
    
    if args.verbose:
        print("Verbose mode: enabled")
    print()
    
    # Run scenarios
    for scenario_key, name, create_fn in scenarios:
        snapshot = create_fn()
        request_id = f"demo_{scenario_key}_{datetime.utcnow().timestamp():.0f}"
        
        try:
            if args.use_http:
                result = run_http_call(snapshot, args.base_url, request_id)
            else:
                result = run_direct_call(snapshot, request_id)
            
            summary = format_summary(result, name, snapshot, verbose=args.verbose)
            print(summary)
            
        except Exception as e:
            print(f"\n❌ Error processing {name}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            continue
    
    print()
    print("="*80)
    print("Demo Complete")
    print("="*80)
    return 0


if __name__ == "__main__":
    sys.exit(main())

