#!/usr/bin/env python3
"""
Analyze B/C scenario comparison results and generate Chinese verdict.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

def load_scenario_metadata(result_dir: Path) -> Optional[Dict[str, Any]]:
    """Load scenario metadata from results directory."""
    metadata_file = result_dir / "metadata.json"
    if not metadata_file.exists():
        return None
    
    with open(metadata_file) as f:
        return json.load(f)

def extract_metrics(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics from metadata."""
    if not metadata:
        return {}
    
    scenario_meta = metadata.get("scenario_metadata", {})
    first_scenario = list(scenario_meta.keys())[0] if scenario_meta else None
    
    if not first_scenario or first_scenario not in scenario_meta:
        return {}
    
    meta = scenario_meta[first_scenario]
    
    return {
        "delta_p95_ms": meta.get("delta_p95_ms", 0),
        "delta_recall": meta.get("delta_recall", 0),
        "p_value": meta.get("p_value", 1.0),
        "safety_rate": meta.get("safety_rate", 0),
        "apply_rate": meta.get("apply_rate", 0),
        "buckets_used": meta.get("buckets_per_side", 0),
        "duration_sec": meta.get("duration_per_side", 0)
    }

def format_verdict(scenario: str, single_metrics: Dict, multi_metrics: Dict) -> str:
    """Format Chinese verdict for a scenario."""
    
    if not single_metrics or not multi_metrics:
        return f"场景{scenario}: ❌ 数据不完整"
    
    # Comparison
    delta_p95_diff = multi_metrics["delta_p95_ms"] - single_metrics["delta_p95_ms"]
    delta_recall_diff = multi_metrics["delta_recall"] - single_metrics["delta_recall"]
    
    # Pass/fail checks
    multi_passed = (
        multi_metrics["delta_p95_ms"] > 0 and
        multi_metrics["p_value"] < 0.05 and
        multi_metrics["delta_recall"] >= -0.01 and
        multi_metrics["safety_rate"] >= 0.99 and
        multi_metrics["apply_rate"] >= 0.95
    )
    
    status = "✅ PASS" if multi_passed else "⚠️  FAIL"
    
    verdict = f"""
{'='*60}
场景{scenario} 对比分析
{'='*60}

单旋钮基线 (10分钟):
  ΔP95: {single_metrics['delta_p95_ms']:+.1f}ms
  ΔRecall@10: {single_metrics['delta_recall']:+.3f}
  p-value: {single_metrics['p_value']:.4f}
  安全率: {single_metrics['safety_rate']:.3f}
  应用率: {single_metrics['apply_rate']:.3f}
  桶数: {single_metrics['buckets_used']}

多旋钮完整 (45分钟):
  ΔP95: {multi_metrics['delta_p95_ms']:+.1f}ms
  ΔRecall@10: {multi_metrics['delta_recall']:+.3f}
  p-value: {multi_metrics['p_value']:.4f}
  安全率: {multi_metrics['safety_rate']:.3f}
  应用率: {multi_metrics['apply_rate']:.3f}
  桶数: {multi_metrics['buckets_used']}

对比差异 (Multi - Single):
  ΔΔP95: {delta_p95_diff:+.1f}ms {'(更好)' if delta_p95_diff > 0 else '(更差)'}
  ΔΔRecall: {delta_recall_diff:+.3f} {'(更好)' if delta_recall_diff > 0 else '(更差)'}

判定: {status}
{'='*60}
"""
    return verdict

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_bc_results.py <results_dir>")
        print("Example: python analyze_bc_results.py ~/Downloads/autotuner_runs/20251008_1234")
        sys.exit(1)
    
    results_dir = Path(sys.argv[1]).expanduser()
    
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("📊 B/C场景对比分析报告")
    print("="*60 + "\n")
    
    # Analyze each scenario
    for scenario in ["B", "C"]:
        single_dir = results_dir / f"{scenario}_single"
        multi_dir = results_dir / f"{scenario}_multi"
        
        if not single_dir.exists() or not multi_dir.exists():
            print(f"❌ 场景{scenario}数据不完整")
            continue
        
        # Load metadata
        single_meta = load_scenario_metadata(single_dir)
        multi_meta = load_scenario_metadata(multi_dir)
        
        # Extract metrics
        single_metrics = extract_metrics(single_meta)
        multi_metrics = extract_metrics(multi_meta)
        
        # Print verdict
        print(format_verdict(scenario, single_metrics, multi_metrics))
    
    print("\n" + "="*60)
    print("分析完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
