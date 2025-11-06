#!/usr/bin/env python3
"""
run_50k_grid.py - Run FiQA 50k grid parameter sweep experiments

Supports:
- Stage-A: RRF grid + rerank grid sweep
- Stage-B: Run winners from Stage-A
"""

import argparse
import itertools
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Import shared evaluation library
from experiments.fiqa_lib import (
    load_queries_qrels as lib_load_queries_qrels,
    evaluate_config as lib_evaluate_config,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_suite_config(yaml_path: Path) -> Dict:
    """Load suite configuration from YAML file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def generate_grid_combinations(grid_config: Dict) -> List[Dict]:
    """
    Generate all combinations from grid configuration.
    
    Example:
    grid_config = {
        'top_k': [32, 48, 64],
        'rrf_k': [20, 40]
    }
    Returns: List of dicts with all combinations
    """
    if 'grid' not in grid_config:
        # No grid, return single config
        return [grid_config]
    
    grid = grid_config['grid']
    base_config = {k: v for k, v in grid_config.items() if k != 'grid'}
    
    # Get all parameter names and their values
    param_names = list(grid.keys())
    param_values = [grid[name] for name in param_names]
    
    # Generate all combinations
    combinations = []
    for combo in itertools.product(*param_values):
        config = base_config.copy()
        for name, value in zip(param_names, combo):
            config[name] = value
        combinations.append(config)
    
    return combinations


def run_stage_a(config_path: Path, repo_root: Path) -> int:
    """Run Stage-A: RRF grid + rerank grid sweep."""
    logger.info("="*80)
    logger.info("FiQA 50k Stage-A: RRF + Rerank Grid Sweep")
    logger.info("="*80)
    
    suite_config = load_suite_config(config_path)
    experiment = suite_config.get('experiment', {})
    common = suite_config.get('common', {})
    output = suite_config.get('output', {})
    
    dataset_name = experiment.get('dataset_name', 'fiqa_50k_v1')
    qrels_name = experiment.get('qrels_name', 'fiqa_qrels_50k_v1')
    base_url = common.get('base_url', 'http://localhost:8011')
    sample = common.get('sample', 1000)
    repeats = common.get('repeats', 1)
    warmup = common.get('warmup', 5)
    concurrency = common.get('concurrency', 16)
    timeout_s = common.get('timeout_s', 20.0)
    
    reports_dir = Path(output.get('reports_dir', 'reports/fiqa_50k/stage_a'))
    if not reports_dir.is_absolute():
        reports_dir = repo_root / reports_dir
    
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Load queries and qrels
    logger.info(f"Loading dataset: {dataset_name}, qrels: {qrels_name}")
    queries, qrels = lib_load_queries_qrels(
        dataset_name=dataset_name,
        qrels_name=qrels_name,
        sample=sample,
        seed=42
    )
    
    all_results = []
    
    # Part A: RRF grid sweep
    if 'stage_a_rrf' in suite_config:
        logger.info("\n" + "="*80)
        logger.info("Part A: RRF Grid Sweep")
        logger.info("="*80)
        
        rrf_config = suite_config['stage_a_rrf']
        rrf_combinations = generate_grid_combinations(rrf_config)
        
        logger.info(f"Running {len(rrf_combinations)} RRF configurations...")
        
        for i, config in enumerate(rrf_combinations, 1):
            top_k = config.get('top_k', common.get('top_k', 50))
            rrf_k = config.get('rrf_k', 60)
            
            name = f"RRF_topk{top_k}_rrfk{rrf_k}"
            logger.info(f"\n[{i}/{len(rrf_combinations)}] {name}")
            logger.info(f"  Config: {config}")
            
            # Prepare full config for API
            full_config = {
                'use_hybrid': True,
                'rerank': False,
                'top_k': top_k,
                'rrf_k': rrf_k,
            }
            
            # Run experiment
            metrics = lib_evaluate_config(
                cfg=full_config,
                base_url=base_url,
                queries=queries,
                qrels=qrels,
                top_k=top_k,
                concurrency=concurrency,
                repeats=repeats,
                timeout_s=timeout_s,
                warmup=warmup
            )
            
            result = {
                'name': name,
                'config': full_config,
                'metrics': metrics
            }
            all_results.append(result)
    
    # Part B: Rerank grid sweep (on best RRF)
    # Select best RRF based on acceptance criteria: Recall@10 >= 0.94, p95 <= 1800ms
    if 'stage_a_rerank' in suite_config and all_results:
        logger.info("\n" + "="*80)
        logger.info("Part B: Rerank Grid Sweep")
        logger.info("="*80)
        
        # Select best RRF from Part A results
        rrf_candidates = [r for r in all_results if 'RRF' in r['name']]
        valid_rrf = [r for r in rrf_candidates 
                    if r['metrics']['recall_at_10'] >= 0.94 and r['metrics']['p95_ms'] <= 1800]
        
        if not valid_rrf:
            logger.warning("No RRF configs meet acceptance criteria. Using best available RRF.")
            # Sort by p95 (ascending), then recall (descending)
            rrf_candidates.sort(key=lambda x: (x['metrics']['p95_ms'], -x['metrics']['recall_at_10']))
            best_rrf = rrf_candidates[0]
        else:
            # Sort valid ones: prefer lower p95, then higher recall
            valid_rrf.sort(key=lambda x: (x['metrics']['p95_ms'], -x['metrics']['recall_at_10']))
            best_rrf = valid_rrf[0]
        
        base_rrf_k = best_rrf['config'].get('rrf_k', 60)
        base_top_k = best_rrf['config'].get('top_k', 50)
        
        logger.info(f"Selected RRF base from Part A: {best_rrf['name']}")
        logger.info(f"  Metrics: Recall@10={best_rrf['metrics']['recall_at_10']:.4f}, "
                   f"P95={best_rrf['metrics']['p95_ms']:.1f}ms")
        logger.info(f"  Using RRF base: top_k={base_top_k}, rrf_k={base_rrf_k}")
        
        rerank_config = suite_config['stage_a_rerank']
        rerank_combinations = generate_grid_combinations(rerank_config)
        logger.info(f"Running {len(rerank_combinations)} rerank configurations...")
        
        for i, config in enumerate(rerank_combinations, 1):
            rerank_top_k = config.get('rerank_top_k', 20)
            rerank_budget_ms = config.get('rerank_budget_ms', 25)
            margin = config.get('rerank_if_margin_below', 0.12)
            
            name = f"Rerank_topk{rerank_top_k}_budget{rerank_budget_ms}_margin{margin}"
            logger.info(f"\n[{i}/{len(rerank_combinations)}] {name}")
            
            # Prepare full config
            full_config = {
                'use_hybrid': True,
                'rerank': True,
                'top_k': base_top_k,
                'rrf_k': base_rrf_k,
                'rerank_top_k': rerank_top_k,
                'rerank_budget_ms': rerank_budget_ms,
                'rerank_if_margin_below': margin,
                'max_rerank_trigger_rate': rerank_config.get('max_rerank_trigger_rate', 0.25),
            }
            
            # Run experiment
            metrics = lib_evaluate_config(
                cfg=full_config,
                base_url=base_url,
                queries=queries,
                qrels=qrels,
                top_k=base_top_k,
                concurrency=concurrency,
                repeats=repeats,
                timeout_s=timeout_s,
                warmup=warmup
            )
            
            result = {
                'name': name,
                'config': full_config,
                'metrics': metrics
            }
            all_results.append(result)
    
    # Generate reports
    logger.info("\n" + "="*80)
    logger.info("Generating reports...")
    logger.info("="*80)
    
    # Generate CSV
    csv_path = reports_dir / "fiqa_50k_stage_a_benchmark.csv"
    import csv
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Config', 'Recall@10', 'P95_Latency_ms', 'QPS', 
                        'Cost_Per_Request_USD', 'Efficiency', 'Success_Rate'])
        
        for r in all_results:
            m = r['metrics']
            cfg = r['config']
            
            # Estimate cost
            cost = 0.00001
            if cfg.get('use_hybrid'):
                cost += 0.00001
            if cfg.get('rerank'):
                cost += 0.001
            
            efficiency = m['recall_at_10'] / max(cost, 0.000001)
            
            writer.writerow([
                r['name'],
                f"{m['recall_at_10']:.4f}",
                f"{m['p95_ms']:.1f}",
                f"{m['qps']:.2f}",
                f"{cost:.6f}",
                f"{efficiency:.0f}",
                f"{1 - (m['failed_queries']/m['total_queries']) if m['total_queries'] > 0 else 0:.2f}"
            ])
    
    logger.info(f"Generated: {csv_path}")
    
    # Generate YAML report
    yaml_path = reports_dir / "fiqa_50k_stage_a.yaml"
    report_data = {
        'experiment': experiment,
        'configurations': []
    }
    
    for r in all_results:
        report_data['configurations'].append({
            'name': r['name'],
            'config': r['config'],
            'metrics': {
                'recall_at_10': {'mean': r['metrics']['recall_at_10']},
                'p95_ms': {'mean': r['metrics']['p95_ms']},
                'qps': {'mean': r['metrics']['qps']},
            },
            'total_queries': r['metrics']['total_queries'],
            'failed_queries': r['metrics']['failed_queries']
        })
    
    with open(yaml_path, 'w') as f:
        yaml.dump(report_data, f, default_flow_style=False)
    
    logger.info(f"Generated: {yaml_path}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ Stage-A complete!")
    logger.info("="*80)
    logger.info(f"Results: {reports_dir}")
    
    return 0


def run_stage_b(config_path: Path, winners_path: Path, repo_root: Path) -> int:
    """Run Stage-B: Full evaluation of winners."""
    logger.info("="*80)
    logger.info("FiQA 50k Stage-B: Full Evaluation")
    logger.info("="*80)
    
    suite_config = load_suite_config(config_path)
    experiment = suite_config.get('experiment', {})
    common = suite_config.get('common', {})
    output = suite_config.get('output', {})
    
    dataset_name = experiment.get('dataset_name', 'fiqa_50k_v1')
    qrels_name = experiment.get('qrels_name', 'fiqa_qrels_50k_v1')
    base_url = common.get('base_url', 'http://localhost:8011')
    sample = common.get('sample')  # None = all queries
    repeats = common.get('repeats', 3)
    warmup = common.get('warmup', 5)
    concurrency = common.get('concurrency', 16)
    timeout_s = common.get('timeout_s', 20.0)
    
    reports_dir = Path(output.get('reports_dir', 'reports/fiqa_50k/stage_b'))
    if not reports_dir.is_absolute():
        reports_dir = repo_root / reports_dir
    
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Load winners
    if not winners_path.is_absolute():
        winners_path = repo_root / winners_path
    
    if not winners_path.exists():
        logger.error(f"Winners file not found: {winners_path}")
        return 1
    
    with open(winners_path, 'r') as f:
        winners = json.load(f)
    
    logger.info(f"Loaded winners from: {winners_path}")
    
    # Load queries and qrels
    logger.info(f"Loading dataset: {dataset_name}, qrels: {qrels_name}")
    queries, qrels = lib_load_queries_qrels(
        dataset_name=dataset_name,
        qrels_name=qrels_name,
        sample=sample,
        seed=42
    )
    
    all_results = []
    
    # Run RRF winner
    if 'rrf_winner' in winners:
        logger.info("\n" + "="*80)
        logger.info("Running RRF Winner")
        logger.info("="*80)
        
        rrf_winner = winners['rrf_winner']
        config = rrf_winner.get('config', {})
        name = rrf_winner.get('name', 'RRF_Winner')
        
        logger.info(f"Config: {config}")
        
        top_k = config.get('top_k', common.get('top_k', 50))
        
        metrics = lib_evaluate_config(
            cfg=config,
            base_url=base_url,
            queries=queries,
            qrels=qrels,
            top_k=top_k,
            concurrency=concurrency,
            repeats=repeats,
            timeout_s=timeout_s,
            warmup=warmup
        )
        
        all_results.append({
            'name': name,
            'config': config,
            'metrics': metrics
        })
    
    # Run rerank winner if exists
    if 'rerank_winner' in winners:
        logger.info("\n" + "="*80)
        logger.info("Running Rerank Winner")
        logger.info("="*80)
        
        rerank_winner = winners['rerank_winner']
        config = rerank_winner.get('config', {})
        name = rerank_winner.get('name', 'Rerank_Winner')
        
        logger.info(f"Config: {config}")
        
        top_k = config.get('top_k', common.get('top_k', 50))
        
        metrics = lib_evaluate_config(
            cfg=config,
            base_url=base_url,
            queries=queries,
            qrels=qrels,
            top_k=top_k,
            concurrency=concurrency,
            repeats=repeats,
            timeout_s=timeout_s,
            warmup=warmup
        )
        
        all_results.append({
            'name': name,
            'config': config,
            'metrics': metrics
        })
    
    # Generate reports (similar to Stage-A)
    logger.info("\n" + "="*80)
    logger.info("Generating reports...")
    logger.info("="*80)
    
    # Generate CSV
    csv_path = reports_dir / "fiqa_50k_stage_b_benchmark.csv"
    import csv
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Config', 'Recall@10', 'P95_Latency_ms', 'QPS', 
                        'Cost_Per_Request_USD', 'Efficiency', 'Success_Rate'])
        
        for r in all_results:
            m = r['metrics']
            cfg = r['config']
            
            cost = 0.00001
            if cfg.get('use_hybrid'):
                cost += 0.00001
            if cfg.get('rerank'):
                cost += 0.001
            
            efficiency = m['recall_at_10'] / max(cost, 0.000001)
            
            writer.writerow([
                r['name'],
                f"{m['recall_at_10']:.4f}",
                f"{m['p95_ms']:.1f}",
                f"{m['qps']:.2f}",
                f"{cost:.6f}",
                f"{efficiency:.0f}",
                f"{1 - (m['failed_queries']/m['total_queries']) if m['total_queries'] > 0 else 0:.2f}"
            ])
    
    logger.info(f"Generated: {csv_path}")
    
    # Generate YAML report
    yaml_path = reports_dir / "fiqa_50k_stage_b.yaml"
    report_data = {
        'experiment': experiment,
        'configurations': []
    }
    
    for r in all_results:
        report_data['configurations'].append({
            'name': r['name'],
            'config': r['config'],
            'metrics': {
                'recall_at_10': {'mean': r['metrics']['recall_at_10']},
                'p95_ms': {'mean': r['metrics']['p95_ms']},
                'qps': {'mean': r['metrics']['qps']},
            },
            'total_queries': r['metrics']['total_queries'],
            'failed_queries': r['metrics']['failed_queries']
        })
    
    with open(yaml_path, 'w') as f:
        yaml.dump(report_data, f, default_flow_style=False)
    
    logger.info(f"Generated: {yaml_path}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ Stage-B complete!")
    logger.info("="*80)
    logger.info(f"Results: {reports_dir}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Run FiQA 50k grid parameter sweep experiments"
    )
    parser.add_argument(
        "--suite",
        type=str,
        required=True,
        help="Path to suite YAML config file"
    )
    parser.add_argument(
        "--winners",
        type=str,
        default=None,
        help="Path to winners.json (required for Stage-B)"
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=['a', 'b', 'auto'],
        default='auto',
        help="Stage to run (auto: detect from config)"
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
    
    config_path = Path(args.suite)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    
    if not config_path.exists():
        logger.error(f"Suite config not found: {config_path}")
        return 1
    
    # Determine stage
    if args.stage == 'auto':
        config = load_suite_config(config_path)
        if 'stage_a_rrf' in config or 'stage_a_rerank' in config:
            stage = 'a'
        elif 'winners' in config:
            stage = 'b'
        else:
            logger.error("Cannot auto-detect stage from config")
            return 1
    else:
        stage = args.stage
    
    # Run appropriate stage
    if stage == 'a':
        return run_stage_a(config_path, repo_root)
    elif stage == 'b':
        if not args.winners:
            logger.error("--winners required for Stage-B")
            return 1
        winners_path = Path(args.winners)
        return run_stage_b(config_path, winners_path, repo_root)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
