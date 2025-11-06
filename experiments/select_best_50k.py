#!/usr/bin/env python3
"""
select_best_50k.py - Select best configurations from Stage-A results

Reads CSV results from Stage-A and selects:
- RRF winner: Recall@10 >= 0.94 and p95 <= 1.8s (prefer lower p95, ideally <=1.6s)
- Rerank winner: Relative to RRF winner, +>=0.01 Recall and p95 increment <=200ms
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_csv_results(csv_path: Path) -> List[Dict]:
    """Load results from CSV file."""
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse metrics
            result = {
                'name': row.get('Config', ''),
                'recall_at_10': float(row.get('Recall@10', 0)),
                'p95_ms': float(row.get('P95_Latency_ms', 0)),
                'qps': float(row.get('QPS', 0)),
                'cost_per_request': float(row.get('Cost_Per_Request_USD', 0)),
                'efficiency': float(row.get('Efficiency', 0)),
                'config': {}  # Will be populated from YAML report if available
            }
            results.append(result)
    return results


def load_config_from_yaml(yaml_path: Path, config_name: str) -> Optional[Dict]:
    """Try to load config from YAML report."""
    try:
        import yaml
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            configs = data.get('configurations', [])
            for cfg in configs:
                if cfg.get('name') == config_name:
                    config = cfg.get('config', {})
                    # If config is empty, try to extract from configs structure
                    if not config and 'config' in cfg:
                        config = cfg['config']
                    return config
    except Exception as e:
        print(f"⚠️  Warning: Could not load config from YAML: {e}")
    return None


def select_rrf_winner(results: List[Dict], yaml_path: Optional[Path] = None) -> Optional[Dict]:
    """
    Select RRF winner based on acceptance criteria:
    - Recall@10 >= 0.94
    - p95 <= 1800ms (1.8s)
    - Prefer lower p95 (ideally <=1600ms)
    """
    # Filter RRF candidates (those without rerank)
    rrf_candidates = []
    for r in results:
        # Check if this is an RRF config (name should contain "RRF" but not "Rerank")
        name = r['name'].lower()
        if 'rrf' in name and 'rerank' not in name:
            rrf_candidates.append(r)
    
    if not rrf_candidates:
        print("⚠️  No RRF candidates found in results")
        return None
    
    # Filter by acceptance criteria
    valid_candidates = []
    for r in rrf_candidates:
        if r['recall_at_10'] >= 0.94 and r['p95_ms'] <= 1800:
            valid_candidates.append(r)
    
    if not valid_candidates:
        print("❌ No RRF configs meet acceptance criteria (Recall@10 >= 0.94, p95 <= 1800ms)")
        return None
    
    # Sort: prefer lower p95, then higher recall
    valid_candidates.sort(key=lambda x: (x['p95_ms'], -x['recall_at_10']))
    
    winner = valid_candidates[0]
    
    print(f"✅ RRF Winner selected:")
    print(f"   Name: {winner['name']}")
    print(f"   Recall@10: {winner['recall_at_10']:.4f}")
    print(f"   P95: {winner['p95_ms']:.1f} ms")
    if winner['p95_ms'] <= 1600:
        print(f"   ✅ Excellent: p95 <= 1.6s")
    else:
        print(f"   ⚠️  p95 > 1.6s (but within 1.8s limit)")
    
    # Try to load config from YAML
    if yaml_path:
        config = load_config_from_yaml(yaml_path, winner['name'])
        if config:
            winner['config'] = config
    
    return winner


def select_rerank_winner(results: List[Dict], rrf_winner: Dict, yaml_path: Optional[Path] = None) -> Optional[Dict]:
    """
    Select rerank winner relative to RRF winner:
    - Recall@10 improvement >= 0.01
    - P95 increment <= 200ms
    """
    # Filter rerank candidates
    rerank_candidates = []
    for r in results:
        name = r['name'].lower()
        if 'rerank' in name:
            rerank_candidates.append(r)
    
    if not rerank_candidates:
        print("⚠️  No rerank candidates found")
        return None
    
    # Check relative to RRF winner
    rrf_recall = rrf_winner['recall_at_10']
    rrf_p95 = rrf_winner['p95_ms']
    
    valid_candidates = []
    for r in rerank_candidates:
        recall_delta = r['recall_at_10'] - rrf_recall
        p95_delta = r['p95_ms'] - rrf_p95
        
        if recall_delta >= 0.01 and p95_delta <= 200:
            valid_candidates.append({
                'result': r,
                'recall_delta': recall_delta,
                'p95_delta': p95_delta
            })
    
    if not valid_candidates:
        print("❌ No rerank configs meet acceptance criteria relative to RRF winner:")
        print(f"   Required: Recall +>=0.01, P95 +<=200ms")
        print(f"   RRF baseline: Recall={rrf_recall:.4f}, P95={rrf_p95:.1f}ms")
        return None
    
    # Sort: prefer higher recall improvement, then lower p95 increment
    valid_candidates.sort(key=lambda x: (-x['recall_delta'], x['p95_delta']))
    
    winner_data = valid_candidates[0]
    winner = winner_data['result']
    
    print(f"✅ Rerank Winner selected:")
    print(f"   Name: {winner['name']}")
    print(f"   Recall@10: {winner['recall_at_10']:.4f} (+{winner_data['recall_delta']:.4f})")
    print(f"   P95: {winner['p95_ms']:.1f} ms (+{winner_data['p95_delta']:.1f}ms)")
    
    # Try to load config from YAML
    if yaml_path:
        config = load_config_from_yaml(yaml_path, winner['name'])
        if config:
            winner['config'] = config
    
    return winner


def main():
    parser = argparse.ArgumentParser(
        description="Select best configurations from Stage-A results"
    )
    parser.add_argument(
        "csv_files",
        nargs="+",
        type=str,
        help="CSV file(s) from Stage-A results"
    )
    parser.add_argument(
        "--yaml-report",
        type=str,
        default=None,
        help="YAML report file to extract configs from"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="reports/fiqa_50k/winners.json",
        help="Output JSON file for winners"
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Repository root (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    # Find repo root
    if args.repo_root:
        repo_root = Path(args.repo_root)
    else:
        repo_root = find_repo_root()
    
    print("="*80)
    print("FiQA 50k Winner Selection")
    print("="*80)
    
    # Load CSV results
    all_results = []
    for csv_file in args.csv_files:
        csv_path = Path(csv_file)
        if not csv_path.is_absolute():
            csv_path = repo_root / csv_path
        
        if not csv_path.exists():
            print(f"⚠️  CSV file not found: {csv_path}")
            continue
        
        print(f"Loading results from: {csv_path}")
        results = load_csv_results(csv_path)
        all_results.extend(results)
    
    if not all_results:
        print("❌ No results loaded!")
        return 1
    
    print(f"Loaded {len(all_results)} configurations")
    
    # Load YAML report if provided
    yaml_path = None
    if args.yaml_report:
        yaml_path = Path(args.yaml_report)
        if not yaml_path.is_absolute():
            yaml_path = repo_root / yaml_path
        if not yaml_path.exists():
            print(f"⚠️  Warning: YAML report not found: {yaml_path}")
            yaml_path = None
        else:
            print(f"Using YAML report: {yaml_path}")
    
    # Select winners
    print("\n" + "="*80)
    print("Selecting RRF Winner...")
    print("="*80)
    rrf_winner = select_rrf_winner(all_results, yaml_path)
    
    if not rrf_winner:
        print("\n❌ Failed to select RRF winner")
        return 1
    
    print("\n" + "="*80)
    print("Selecting Rerank Winner...")
    print("="*80)
    rerank_winner = select_rerank_winner(all_results, rrf_winner, yaml_path)
    
    # Prepare winners JSON
    winners = {
        "rrf_winner": {
            "name": rrf_winner['name'],
            "metrics": {
                "recall_at_10": rrf_winner['recall_at_10'],
                "p95_ms": rrf_winner['p95_ms'],
                "qps": rrf_winner['qps'],
                "cost_per_request": rrf_winner['cost_per_request']
            },
            "config": rrf_winner.get('config', {})
        }
    }
    
    if rerank_winner:
        winners["rerank_winner"] = {
            "name": rerank_winner['name'],
            "metrics": {
                "recall_at_10": rerank_winner['recall_at_10'],
                "p95_ms": rerank_winner['p95_ms'],
                "qps": rerank_winner['qps'],
                "cost_per_request": rerank_winner['cost_per_request']
            },
            "config": rerank_winner.get('config', {})
        }
    
    # Write winners JSON
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = repo_root / out_path
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w') as f:
        json.dump(winners, f, indent=2)
    
    print("\n" + "="*80)
    print("Winners Summary")
    print("="*80)
    print(f"RRF Winner: {winners['rrf_winner']['name']}")
    if 'rerank_winner' in winners:
        print(f"Rerank Winner: {winners['rerank_winner']['name']}")
    else:
        print("Rerank Winner: None (no config met criteria)")
    print(f"\nWinners saved to: {out_path}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
