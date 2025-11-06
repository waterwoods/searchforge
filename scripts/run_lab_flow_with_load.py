#!/usr/bin/env python3
"""
Lab Flow Experiment Runner with Load Generation

Runs ABAB experiment with internal load generation:
- Warmup 60s
- A window (default 180s)
- B window (default 180s)
- A window (default 180s)
- B window (default 180s)

Ensures deterministic query sequence across A and B windows.
"""

import asyncio
import sys
import time
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend_core.lab_loadgen import LabLoadGenerator, get_redis_client
from backend_core.lab_flow_reporter import generate_flow_report
import httpx
import redis

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies(base_url: str) -> bool:
    """
    Check if Redis and Qdrant are healthy.
    
    Args:
        base_url: Base URL for health checks
        
    Returns:
        True if all dependencies healthy
    """
    try:
        # Check Redis
        r = get_redis_client()
        r.ping()
        logger.info("✓ Redis is healthy")
        
        # Check backend health (try multiple endpoints)
        health_endpoints = ["/health", "/healthz", "/ops/health"]
        health_ok = False
        for endpoint in health_endpoints:
            try:
                response = httpx.get(f"{base_url}{endpoint}", timeout=5.0)
                if response.status_code == 200:
                    health_ok = True
                    break
            except:
                continue
        
        if not health_ok:
            logger.error("✗ Backend health check failed on all endpoints")
            return False
        
        # Use the last successful response
        response = httpx.get(f"{base_url}/health", timeout=5.0)
        if response.status_code != 200:
            logger.error("✗ Backend health check failed")
            return False
        
        health_data = response.json()
        # Check for either "ok": true or "status": "healthy"
        if not (health_data.get("ok", False) or health_data.get("status") == "healthy"):
            logger.error("✗ Backend returned unhealthy status")
            return False
        
        logger.info("✓ Backend is healthy")
        
        # Check Qdrant (try to query collections)
        try:
            qdrant_response = httpx.get("http://localhost:6333/collections", timeout=5.0)
            if qdrant_response.status_code == 200:
                logger.info("✓ Qdrant is healthy")
            else:
                logger.error("✗ Qdrant is not responding")
                return False
        except Exception as e:
            logger.error(f"✗ Qdrant check failed: {e}")
            return False
        
        # Quiet Mode is optional - just log warning if not available
        logger.info("✓ All dependencies healthy")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Dependency check failed: {e}")
        return False


async def run_experiment(
    base_url: str,
    qps: float,
    concurrency: int,
    topk: int,
    window_sec: int,
    rounds: int,
    seed: int,
    recall_sample: float
):
    """
    Run ABAB flow experiment with load generation.
    
    Args:
        base_url: Base URL for search API
        qps: Target queries per second
        concurrency: Max concurrent requests
        topk: Top-K results
        window_sec: Duration of each A/B window
        rounds: Number of ABAB rounds
        seed: Random seed for deterministic queries
        recall_sample: Fraction to sample for recall
    """
    # Check dependencies
    logger.info("Checking dependencies...")
    if not check_dependencies(base_url):
        logger.error("Dependency check failed. Aborting.")
        sys.exit(1)
    
    # Generate experiment ID
    experiment_id = f"flow_load_{int(time.time())}"
    logger.info(f"Experiment ID: {experiment_id}")
    
    # Create load generator
    redis_client = get_redis_client()
    loadgen = LabLoadGenerator(
        base_url=base_url,
        qps=qps,
        concurrency=concurrency,
        topk=topk,
        seed=seed,
        redis_client=redis_client,
        experiment_id=experiment_id,
        recall_sample=recall_sample
    )
    
    # Configure flow control for baseline (optional)
    try:
        logger.info("Configuring flow control for baseline (A)...")
        response = httpx.post(
            f"{base_url}/ops/control/policy",
            json={"policy": "aimd"},
            timeout=5.0
        )
        if response.status_code == 200:
            logger.info("✓ Flow control policy set to 'aimd'")
        else:
            logger.warning(f"Flow control policy endpoint returned {response.status_code}")
    except Exception as e:
        logger.warning(f"Flow control not available: {e}")
    
    logger.info("✓ Ready to start load generation")
    
    # Run warmup phase
    logger.info(f"Starting warmup phase (60s)...")
    await loadgen.run_phase("warmup", 60)
    logger.info("✓ Warmup completed")
    
    # Run ABAB rounds
    for round_num in range(rounds):
        logger.info(f"=== Round {round_num + 1}/{rounds} ===")
        
        # Phase A (baseline)
        logger.info(f"Starting Phase A ({window_sec}s)...")
        loadgen.reset_query_sequence()  # Reset for deterministic sequence
        await loadgen.run_phase("A", window_sec)
        logger.info("✓ Phase A completed")
        
        # Phase B (variant)
        logger.info(f"Starting Phase B ({window_sec}s)...")
        loadgen.reset_query_sequence()  # Use same sequence as A
        await loadgen.run_phase("B", window_sec)
        logger.info("✓ Phase B completed")
    
    logger.info("Experiment completed!")
    
    # Generate report
    logger.info("Generating report...")
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / "LAB_FLOW_REPORT_MINI.txt"
    
    report_text = generate_flow_report(experiment_id, str(report_path))
    logger.info(f"✓ Report saved: {report_path}")
    print()
    print(report_text)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Lab Flow experiment with load generation"
    )
    
    parser.add_argument(
        "--qps",
        type=float,
        default=10.0,
        help="Target queries per second (default: 10.0)"
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Max concurrent requests (default: 5)"
    )
    
    parser.add_argument(
        "--topk",
        type=int,
        default=10,
        help="Top-K results to retrieve (default: 10)"
    )
    
    parser.add_argument(
        "--window",
        type=int,
        default=180,
        help="Duration of each A/B window in seconds (default: 180)"
    )
    
    parser.add_argument(
        "--rounds",
        type=int,
        default=2,
        help="Number of ABAB rounds (default: 2)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic queries (default: 42)"
    )
    
    parser.add_argument(
        "--recall-sample",
        type=float,
        default=0.0,
        help="Fraction of requests to sample for recall [0..1] (default: 0.0)"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL for API (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    # Validate args
    if args.qps <= 0:
        logger.error("QPS must be positive")
        sys.exit(1)
    
    if args.concurrency <= 0:
        logger.error("Concurrency must be positive")
        sys.exit(1)
    
    if args.recall_sample < 0 or args.recall_sample > 1:
        logger.error("Recall sample must be in [0, 1]")
        sys.exit(1)
    
    # Print configuration
    print("=" * 70)
    print("LAB FLOW EXPERIMENT WITH LOAD GENERATION")
    print("=" * 70)
    print(f"QPS: {args.qps}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Top-K: {args.topk}")
    print(f"Window Duration: {args.window}s")
    print(f"Rounds: {args.rounds}")
    print(f"Seed: {args.seed}")
    print(f"Recall Sample: {args.recall_sample}")
    print(f"Base URL: {args.base_url}")
    print("=" * 70)
    print()
    
    total_duration = 60 + (args.window * 2 * args.rounds)
    print(f"Total experiment duration: ~{total_duration}s ({total_duration // 60}m {total_duration % 60}s)")
    print()
    
    # Run experiment
    asyncio.run(run_experiment(
        base_url=args.base_url,
        qps=args.qps,
        concurrency=args.concurrency,
        topk=args.topk,
        window_sec=args.window,
        rounds=args.rounds,
        seed=args.seed,
        recall_sample=args.recall_sample
    ))


if __name__ == "__main__":
    main()

