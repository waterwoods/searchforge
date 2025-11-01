#!/usr/bin/env python3
"""
FiQA Parameter Tuner - Random Search with Early Stopping

This script performs random search over hyperparameters with early stopping
and two-stage evaluation (fast screening + full validation).

Features:
- Random sampling of hyperparameter space
- Early stopping when no improvement for N trials
- Two-stage evaluation (fast Stage-A + full Stage-B)
- Outputs trials CSV, top-k YAML, and best configuration
"""

import argparse
import csv
import logging
import os
import random
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml

from experiments.fiqa_lib import (
    load_queries_qrels,
    evaluate_config,
    objective,
    put_best_to_api
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fast mode defaults from environment variables (lower load)
FAST_SAMPLE = int(os.getenv("FAST_SAMPLE", "150"))
FAST_TOP_K = int(os.getenv("FAST_TOP_K", "30"))
FAST_CONCURRENCY = int(os.getenv("FAST_CONCURRENCY", "8"))
FAST_REPEATS = int(os.getenv("FAST_REPEATS", "1"))


# ============================================================================
# Health Check
# ============================================================================

def wait_for_health(base: str, tries: int = 30, sleep_s: int = 2) -> None:
    """
    Wait for backend health check to pass.
    
    Args:
        base: Base API URL
        tries: Number of retry attempts
        sleep_s: Sleep time between attempts (seconds)
        
    Raises:
        RuntimeError: If health check fails after all retries
    """
    url = f"{base}/api/health/qdrant"
    logger.info(f"Waiting for backend health at {url}...")
    
    for attempt in range(1, tries + 1):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("http_ok") and data.get("grpc_ok"):
                    logger.info(f"✅ Backend health OK (attempt {attempt}/{tries})")
                    return
                else:
                    logger.warning(f"Health check not ready: http_ok={data.get('http_ok')}, grpc_ok={data.get('grpc_ok')}")
            else:
                logger.warning(f"Health check returned {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Health check attempt {attempt}/{tries} failed: {e}")
        
        if attempt < tries:
            time.sleep(sleep_s)
    
    raise RuntimeError(f"后端未就绪: health check failed after {tries} attempts. Please ensure the backend is running and Qdrant is accessible.")


# ============================================================================
# Search Space Definition
# ============================================================================

def sample_trial_config(seed: Optional[int] = None) -> Dict:
    """
    Sample a random configuration from the search space.
    
    Args:
        seed: Optional random seed (for reproducibility)
        
    Returns:
        Configuration dictionary
    """
    if seed is not None:
        random.seed(seed)
    
    cfg = {}
    
    # use_hybrid: True (70%) or False (30%)
    cfg["use_hybrid"] = random.random() < 0.7
    
    # rrf_k: {10, 20, 25, 30} (tightened to avoid overload)
    cfg["rrf_k"] = random.choice([10, 20, 25, 30])
    
    # dense_k: {30, 40, 50} (used for top_k in fast mode)
    # This is represented via top_k parameter in evaluate_config
    
    # bm25_k: {20, 30, 40} (handled internally by hybrid, tightened)
    # This is represented via rrf_k which affects BM25 retrieval
    
    # rerank: True (50%) or False (50%)
    cfg["rerank"] = random.random() < 0.5
    
    # If rerank=True, add rerank parameters
    if cfg["rerank"]:
        # rerank_top_k: {6, 8, 10} (unchanged)
        cfg["rerank_top_k"] = random.choice([6, 8, 10])
        
        # rerank_if_margin_below: {0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18}
        cfg["rerank_if_margin_below"] = random.choice([0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18])
        
        # max_rerank_trigger_rate: {0.15, 0.25, 0.35}
        cfg["max_rerank_trigger_rate"] = random.choice([0.15, 0.25, 0.35])
        
        # rerank_budget_ms: {20, 30, 50}
        cfg["rerank_budget_ms"] = random.choice([20, 30, 50])
    
    return cfg


# ============================================================================
# Early Stopping Logic
# ============================================================================

class EarlyStopping:
    """Early stopping tracker."""
    
    def __init__(self, patience: int, min_improve: float):
        """
        Args:
            patience: Number of trials without improvement before stopping
            min_improve: Minimum improvement threshold
        """
        self.patience = patience
        self.min_improve = min_improve
        self.best_score = float('-inf')
        self.no_improve_count = 0
    
    def update(self, score: float) -> bool:
        """
        Update with new score and check if should stop.
        
        Args:
            score: New objective score
            
        Returns:
            True if should stop, False otherwise
        """
        if score > self.best_score + self.min_improve:
            self.best_score = score
            self.no_improve_count = 0
            return False
        else:
            self.no_improve_count += 1
            return self.no_improve_count >= self.patience
    
    def should_stop(self) -> bool:
        """Check if early stopping condition is met."""
        return self.no_improve_count >= self.patience


# ============================================================================
# Main Functions
# ============================================================================

def run_stage_a(
    n_trials: int,
    base_url: str,
    queries: List[Dict],
    qrels: Dict,
    sample: int,
    top_k: int,
    concurrency: int,
    repeats: int,
    timeout_s: float,
    seed: int,
    output_dir: Path,
    patience: int = 10,
    min_improve: float = 0.005
) -> List[Dict]:
    """
    Stage-A: Fast evaluation with random search and early stopping.
    
    Returns:
        List of trial results (sorted by score, descending)
    """
    # Wait for backend health before Stage-A
    wait_for_health(base_url)
    
    logger.info("="*80)
    logger.info("Stage-A: Random Search with Early Stopping")
    logger.info("="*80)
    logger.info(f"Trials: {n_trials}, Patience: {patience}, Min Improve: {min_improve}")
    logger.info(f"Fast params: sample={sample}, top_k={top_k}, concurrency={concurrency}, repeats={repeats}")
    logger.info("="*80)
    
    early_stop = EarlyStopping(patience=patience, min_improve=min_improve)
    trials = []
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    trials_csv_path = output_dir / "trials.csv"
    
    # Initialize CSV file
    with open(trials_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "trial", "score", "recall_at_10", "p95_ms", "rerank_trigger_rate",
            "use_hybrid", "rrf_k", "rerank", "rerank_top_k",
            "rerank_if_margin_below", "max_rerank_trigger_rate", "rerank_budget_ms"
        ])
    
    random.seed(seed)
    
    for trial_idx in range(n_trials):
        logger.info(f"\nTrial {trial_idx + 1}/{n_trials}")
        
        # Sample configuration
        cfg = sample_trial_config()
        logger.info(f"Config: {cfg}")
        
        # Evaluate configuration
        try:
            metrics = evaluate_config(
                cfg,
                base_url=base_url,
                queries=queries,
                qrels=qrels,
                top_k=top_k,
                concurrency=concurrency,
                repeats=repeats,
                timeout_s=timeout_s,
                warmup=3  # Reduced warmup for speed
            )
            
            # Calculate objective score
            score = objective(metrics)
            
            # Create trial record
            trial_record = {
                "trial": trial_idx + 1,
                "score": score,
                "metrics": metrics,
                "config": cfg.copy()
            }
            trials.append(trial_record)
            
            logger.info(f"  Recall@10: {metrics['recall_at_10']:.4f}")
            logger.info(f"  P95 (ms): {metrics['p95_ms']:.1f}")
            logger.info(f"  Rerank trigger rate: {metrics['rerank_trigger_rate']:.3f}")
            logger.info(f"  Objective score: {score:.4f}")
            
            # Write to CSV
            with open(trials_csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    trial_idx + 1,
                    f"{score:.6f}",
                    f"{metrics['recall_at_10']:.4f}",
                    f"{metrics['p95_ms']:.1f}",
                    f"{metrics['rerank_trigger_rate']:.3f}",
                    cfg.get("use_hybrid", False),
                    cfg.get("rrf_k", ""),
                    cfg.get("rerank", False),
                    cfg.get("rerank_top_k", ""),
                    cfg.get("rerank_if_margin_below", ""),
                    cfg.get("max_rerank_trigger_rate", ""),
                    cfg.get("rerank_budget_ms", "")
                ])
            
            # Check early stopping
            if early_stop.update(score):
                logger.info(f"\nEarly stopping triggered after {trial_idx + 1} trials")
                logger.info(f"  Best score: {early_stop.best_score:.4f}")
                logger.info(f"  No improvement for {early_stop.patience} trials")
                break
            
        except Exception as e:
            logger.error(f"Trial {trial_idx + 1} failed: {e}")
            continue
    
    # Sort trials by score (descending)
    trials.sort(key=lambda x: x["score"], reverse=True)
    
    logger.info(f"\nStage-A complete: {len(trials)} trials evaluated")
    logger.info(f"Best score: {trials[0]['score']:.4f} (trial {trials[0]['trial']})")
    
    return trials


def run_stage_b(
    top_k_configs: List[Dict],
    base_url: str,
    queries: List[Dict],
    qrels: Dict,
    top_k: int,
    concurrency: int,
    repeats: int,
    timeout_s: float,
    output_dir: Path
) -> Dict:
    """
    Stage-B: Full evaluation of top-k configurations.
    
    Args:
        top_k_configs: List of top-k trial records from Stage-A
        base_url: Base API URL
        queries: Full query list (no sampling)
        qrels: Ground truth
        top_k: Top-K parameter for full evaluation
        concurrency: Thread pool size
        repeats: Number of repeats
        timeout_s: Request timeout
        output_dir: Output directory
        
    Returns:
        Best configuration dictionary with metrics
    """
    # Wait for backend health before Stage-B
    wait_for_health(base_url)
    
    logger.info("="*80)
    logger.info("Stage-B: Full Evaluation of Top-K Configs")
    logger.info("="*80)
    logger.info(f"Evaluating {len(top_k_configs)} configurations")
    logger.info(f"Full params: all queries, top_k={top_k}, concurrency={concurrency}, repeats={repeats}")
    logger.info("="*80)
    
    best_config = None
    best_score = float('-inf')
    full_results = []
    
    for i, trial in enumerate(top_k_configs):
        cfg = trial["config"]
        logger.info(f"\n[{i+1}/{len(top_k_configs)}] Evaluating config: {cfg}")
        
        try:
            metrics = evaluate_config(
                cfg,
                base_url=base_url,
                queries=queries,
                qrels=qrels,
                top_k=top_k,
                concurrency=concurrency,
                repeats=repeats,
                timeout_s=timeout_s,
                warmup=5
            )
            
            score = objective(metrics)
            
            result = {
                "config": cfg.copy(),
                "metrics": metrics,
                "score": score
            }
            full_results.append(result)
            
            logger.info(f"  Recall@10: {metrics['recall_at_10']:.4f}")
            logger.info(f"  P95 (ms): {metrics['p95_ms']:.1f}")
            logger.info(f"  Objective score: {score:.4f}")
            
            if score > best_score:
                best_score = score
                best_config = {
                    **cfg.copy(),
                    "metrics": metrics,
                    "score": score
                }
                
        except Exception as e:
            logger.error(f"Evaluation failed for config {i+1}: {e}")
            continue
    
    # Save full evaluation results
    best_full_path = output_dir / "best_full.yaml"
    if best_config:
        with open(best_full_path, 'w') as f:
            yaml.dump(best_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"\nSaved best configuration to {best_full_path}")
    
    return best_config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FiQA Parameter Tuner - Random Search with Early Stopping"
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=40,
        help="Number of random trials (default: 40)"
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=10,
        help="Early stopping patience (default: 10)"
    )
    parser.add_argument(
        "--min-improve",
        type=float,
        default=0.005,
        help="Minimum improvement for early stopping (default: 0.005)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: sample=200, top_k=30, concurrency=12, repeats=1"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Sample N queries (overrides --fast default)"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=None,
        help="Top-K parameter (overrides --fast default)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Thread pool size (overrides --fast default)"
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=None,
        help="Number of repeats (overrides --fast default)"
    )
    parser.add_argument(
        "--base",
        type=str,
        default="http://localhost:8011",
        help="Base API URL (default: http://localhost:8011)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Request timeout in seconds (default: 15.0)"
    )
    parser.add_argument(
        "--promote-top-k",
        type=int,
        default=3,
        help="Number of top configs to promote to Stage-B (default: 3)"
    )
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Only run Stage-B (full evaluation) on existing top-k results"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="experiments/data/fiqa",
        help="Data directory (default: experiments/data/fiqa)"
    )
    
    args = parser.parse_args()
    
    # Apply --fast defaults if set (use environment variables if not explicitly set)
    if args.fast:
        if args.sample is None:
            args.sample = FAST_SAMPLE
        if args.top_k is None:
            args.top_k = FAST_TOP_K
        if args.concurrency is None:
            args.concurrency = FAST_CONCURRENCY
        if args.repeats is None:
            args.repeats = FAST_REPEATS
    else:
        # Normal mode defaults
        if args.sample is None:
            args.sample = None  # Use all queries
        if args.top_k is None:
            args.top_k = 50
        if args.concurrency is None:
            args.concurrency = 16
        if args.repeats is None:
            args.repeats = 3
    
    # Handle BASE environment variable override
    base_url = os.getenv("BASE", args.base)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("reports") / "tuning" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("="*80)
    logger.info("FiQA Parameter Tuner")
    logger.info("="*80)
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Output: {output_dir}")
    logger.info("="*80)
    
    # Wait for backend health (before any stage)
    wait_for_health(base_url)
    
    # Load queries and qrels
    queries, qrels = load_queries_qrels(
        data_dir=args.data_dir,
        sample=None,  # Always load full set for Stage-B
        seed=args.seed
    )
    
    if args.promote:
        # Stage-B only: load existing top-k results
        logger.info("Running Stage-B only (promote mode)")
        
        # Find latest tuning directory
        tuning_dir = Path("reports/tuning")
        if not tuning_dir.exists():
            logger.error("No tuning reports found. Run Stage-A first.")
            return 1
        
        # Get latest directory
        dirs = sorted(tuning_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not dirs:
            logger.error("No tuning reports found. Run Stage-A first.")
            return 1
        
        latest_dir = dirs[0]
        topk_yaml_path = latest_dir / "topk.yaml"
        
        if not topk_yaml_path.exists():
            logger.error(f"topk.yaml not found in {latest_dir}")
            return 1
        
        # Load top-k configs
        with open(topk_yaml_path, 'r') as f:
            topk_data = yaml.safe_load(f)
        
        top_k_configs = topk_data.get("top_k", [])[:args.promote_top_k]
        logger.info(f"Loaded {len(top_k_configs)} configs from {topk_yaml_path}")
        
        output_dir = latest_dir  # Use existing directory
        
    else:
        # Stage-A: Random search with early stopping
        # Use sampled queries for Stage-A
        stage_a_queries, _ = load_queries_qrels(
            data_dir=args.data_dir,
            sample=args.sample,
            seed=args.seed
        )
        
        trials = run_stage_a(
            n_trials=args.n_trials,
            base_url=base_url,
            queries=stage_a_queries,
            qrels=qrels,
            sample=args.sample,
            top_k=args.top_k,
            concurrency=args.concurrency,
            repeats=args.repeats,
            timeout_s=args.timeout,
            seed=args.seed,
            output_dir=output_dir,
            patience=args.patience,
            min_improve=args.min_improve
        )
        
        # Save top-k results
        top_k_configs = trials[:args.promote_top_k]
        topk_yaml_path = output_dir / "topk.yaml"
        with open(topk_yaml_path, 'w') as f:
            yaml.dump({
                "timestamp": timestamp,
                "top_k": [
                    {
                        "trial": t["trial"],
                        "score": t["score"],
                        "config": t["config"],
                        "metrics": t["metrics"]
                    }
                    for t in top_k_configs
                ]
            }, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        logger.info(f"\nSaved top-{args.promote_top_k} configs to {topk_yaml_path}")
    
    # Stage-B: Full evaluation
    best_config = run_stage_b(
        top_k_configs=top_k_configs,
        base_url=base_url,
        queries=queries,  # Full query set
        qrels=qrels,
        top_k=50,  # Full evaluation uses top_k=50
        concurrency=16,
        repeats=3,
        timeout_s=args.timeout,
        output_dir=output_dir
    )
    
    if best_config:
        # Update /api/best
        logger.info("\nUpdating /api/best with best configuration...")
        success = put_best_to_api(best_config, base_url)
        if success:
            logger.info("✅ Successfully updated /api/best")
        else:
            logger.warning("⚠ Failed to update /api/best")
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("TUNING COMPLETE")
        logger.info("="*80)
        logger.info(f"Best configuration:")
        logger.info(f"  Recall@10: {best_config['metrics']['recall_at_10']:.4f}")
        logger.info(f"  P95 (ms): {best_config['metrics']['p95_ms']:.1f}")
        logger.info(f"  Rerank trigger rate: {best_config['metrics']['rerank_trigger_rate']:.3f}")
        logger.info(f"  Objective score: {best_config['score']:.4f}")
        logger.info(f"\nConfig: {best_config.get('config', {})}")
        logger.info(f"Output directory: {output_dir}")
        logger.info("="*80)
        
        return 0
    else:
        logger.error("No valid configuration found!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

