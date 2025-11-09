#!/usr/bin/env python3
"""
Update SLA_POLICY.yaml based on actual experiment results.

This script extracts metrics from winners.json and updates SLA thresholds
with safety margins (recall: 90% of actual, p95: 110% of actual).
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from ruamel.yaml import YAML
except ImportError:
    print("ERROR: ruamel.yaml not installed. Run: pip install ruamel.yaml")
    sys.exit(1)


def find_winners_json(run_id: Optional[str] = None) -> Optional[Path]:
    """Find winners.json from run_id or latest report."""
    if run_id:
        # Try reports/{run_id}/winners.json
        candidates = [
            Path(f"reports/{run_id}/winners.json"),
            Path(f"reports/{run_id}/winners_json"),
        ]
        for cand in candidates:
            if cand.exists():
                return cand
        return None
    
    # Try to find from .last_run or latest report
    if Path(".last_run").exists():
        run_id = Path(".last_run").read_text().strip()
        cand = Path(f"reports/{run_id}/winners.json")
        if cand.exists():
            return cand
    
    # Try to find latest winners.json in reports/
    reports_dir = Path("reports")
    if reports_dir.exists():
        winners_files = list(reports_dir.glob("*/winners.json"))
        if winners_files:
            # Sort by modification time, newest first
            winners_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return winners_files[0]
    
    return None


def extract_metrics(winners_path: Path) -> Dict[str, float]:
    """Extract recall_at_10 and p95_ms from winners.json."""
    try:
        with winners_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load {winners_path}: {e}", file=sys.stderr)
        return {}
    
    # Try multiple paths: winner.metrics, winners.winner.metrics, winners.quality.metrics, etc.
    metrics = {}
    
    # Path 1: winner.metrics
    winner = data.get("winner", {})
    if isinstance(winner, dict):
        winner_metrics = winner.get("metrics", {})
        if winner_metrics:
            metrics["recall_at_10"] = float(winner_metrics.get("recall_at_10", 0))
            metrics["p95_ms"] = float(winner_metrics.get("p95_ms", 0))
    
    # Path 2: winners.winner.metrics (if winner is nested)
    if not metrics.get("recall_at_10") and not metrics.get("p95_ms"):
        winners = data.get("winners", {})
        if isinstance(winners, dict):
            # Try balanced winner first
            balanced = winners.get("balanced", {})
            if isinstance(balanced, dict):
                metrics["recall_at_10"] = float(balanced.get("recall_at_10", 0))
                metrics["p95_ms"] = float(balanced.get("p95_ms", 0))
            
            # Fallback to quality winner
            if not metrics.get("recall_at_10"):
                quality = winners.get("quality", {})
                if isinstance(quality, dict):
                    metrics["recall_at_10"] = float(quality.get("recall_at_10", 0))
                    metrics["p95_ms"] = float(quality.get("p95_ms", 0))
    
    # Path 3: Direct metrics field
    if not metrics.get("recall_at_10") and not metrics.get("p95_ms"):
        direct_metrics = data.get("metrics", {})
        if direct_metrics:
            metrics["recall_at_10"] = float(direct_metrics.get("recall_at_10", 0))
            metrics["p95_ms"] = float(direct_metrics.get("p95_ms", 0))
    
    return metrics


def calculate_sla_thresholds(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate SLA thresholds with safety margins.
    
    - recall_min = 90% of actual recall (with bounds [0.3, 0.99])
    - p95_max = 110% of actual p95 (with minimum 50ms)
    """
    recall = metrics.get("recall_at_10", 0.0)
    p95_ms = metrics.get("p95_ms", 0.0)
    
    # Calculate recall_min: 90% of actual, bounded [0.3, 0.99]
    if recall > 0:
        recall_min = max(0.3, min(0.99, round(0.9 * recall, 3)))
    else:
        recall_min = 0.3  # Default fallback
    
    # Calculate p95_max: 110% of actual, minimum 50ms
    if p95_ms > 0:
        p95_max = max(50.0, round(1.1 * p95_ms, 2))
    else:
        p95_max = 1500.0  # Default fallback
    
    return {
        "recall_at_10_min": recall_min,
        "p95_ms_max": p95_max,
    }


def update_sla_policy(sla_path: Path, new_thresholds: Dict[str, float], preserve_cost: bool = True) -> None:
    """Update SLA_POLICY.yaml with new thresholds."""
    yaml = YAML()
    yaml.preserve_quotes = True
    
    # Load existing policy
    if sla_path.exists():
        with sla_path.open("r", encoding="utf-8") as f:
            policy = yaml.load(f) or {}
    else:
        policy = {}
    
    # Preserve cost_max if requested
    if preserve_cost and "cost_max" not in policy:
        policy["cost_max"] = 5.0  # Default
    
    # Update thresholds
    policy["recall_at_10_min"] = new_thresholds["recall_at_10_min"]
    policy["p95_ms_max"] = new_thresholds["p95_ms_max"]
    
    # Write back
    with sla_path.open("w", encoding="utf-8") as f:
        yaml.dump(policy, f)
    
    print(f"✅ Updated {sla_path}")
    print(f"   recall_at_10_min: {new_thresholds['recall_at_10_min']}")
    print(f"   p95_ms_max: {new_thresholds['p95_ms_max']}")
    if preserve_cost and "cost_max" in policy:
        print(f"   cost_max: {policy['cost_max']} (preserved)")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update SLA_POLICY.yaml from experiment results")
    parser.add_argument("--run-id", help="Run ID to extract metrics from")
    parser.add_argument("--winners-json", help="Path to winners.json (overrides run-id)")
    parser.add_argument("--sla-path", default="configs/SLA_POLICY.yaml", help="Path to SLA_POLICY.yaml")
    parser.add_argument("--no-preserve-cost", action="store_true", help="Don't preserve cost_max")
    
    args = parser.parse_args()
    
    # Find winners.json
    if args.winners_json:
        winners_path = Path(args.winners_json)
    else:
        winners_path = find_winners_json(args.run_id)
    
    if not winners_path or not winners_path.exists():
        print(f"ERROR: winners.json not found", file=sys.stderr)
        print(f"  Tried: {winners_path}", file=sys.stderr)
        print(f"  Use --winners-json or ensure .last_run exists", file=sys.stderr)
        sys.exit(1)
    
    print(f"📊 Loading metrics from {winners_path}")
    
    # Extract metrics
    metrics = extract_metrics(winners_path)
    if not metrics.get("recall_at_10") and not metrics.get("p95_ms"):
        print(f"ERROR: Failed to extract metrics from {winners_path}", file=sys.stderr)
        print(f"  Found data keys: {list(metrics.keys())}", file=sys.stderr)
        sys.exit(1)
    
    print(f"   recall_at_10: {metrics.get('recall_at_10', 0):.4f}")
    print(f"   p95_ms: {metrics.get('p95_ms', 0):.2f}")
    
    # Calculate thresholds
    thresholds = calculate_sla_thresholds(metrics)
    
    # Update SLA policy
    sla_path = Path(args.sla_path)
    update_sla_policy(sla_path, thresholds, preserve_cost=not args.no_preserve_cost)
    
    print(f"\n✅ SLA policy updated successfully")


if __name__ == "__main__":
    main()

