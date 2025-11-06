#!/usr/bin/env python3
"""
Lab Routing Experiment Runner with Load Generation

Runs ABAB routing experiment with internal load generation:
- Warmup 60s
- A window (default 120s) - ALL→Qdrant baseline
- B window (default 120s) - Smart routing (FAISS-first)
- A window (default 120s) - ALL→Qdrant baseline
- B window (default 120s) - Smart routing (FAISS-first)

Ensures deterministic query sequence with topk mix across A and B windows.
"""

import asyncio
import sys
import time
import argparse
import logging
import os
from pathlib import Path

# Fix OpenMP library conflict between numpy and FAISS
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend_core.lab_loadgen import LabLoadGenerator, get_redis_client
from backend_core.lab_route_reporter import generate_route_report
import httpx
import redis

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def parse_topk_mix(topk_str: str) -> list[int]:
    """
    Parse topk mix from string like "16,32,64".
    
    Args:
        topk_str: Comma-separated topk values
        
    Returns:
        List of topk integers
    """
    try:
        values = [int(x.strip()) for x in topk_str.split(',')]
        if not values:
            raise ValueError("Empty topk mix")
        return values
    except Exception as e:
        logger.error(f"Failed to parse topk mix '{topk_str}': {e}")
        sys.exit(1)


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
        
        logger.info("✓ All dependencies healthy")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Dependency check failed: {e}")
        return False


async def configure_routing_baseline(base_url: str):
    """Configure routing for baseline (A) - all to Qdrant."""
    try:
        logger.info("Configuring routing baseline (A): ALL→Qdrant...")
        # Try to set routing flags to force Qdrant
        response = httpx.post(
            f"{base_url}/ops/routing/flags",
            json={
                "enabled": False,
                "manual_backend": "qdrant"
            },
            timeout=5.0
        )
        if response.status_code == 200:
            logger.info("✓ Routing configured for baseline (forced to Qdrant)")
        else:
            logger.warning(f"Routing flags endpoint returned {response.status_code}")
    except Exception as e:
        logger.warning(f"Routing configuration not available: {e}")
        logger.warning("Proceeding without explicit routing control")


async def configure_routing_variant(base_url: str, routing_mode: str):
    """Configure routing for variant (B) - smart routing."""
    try:
        logger.info(f"Configuring routing variant (B): {routing_mode} routing...")
        response = httpx.post(
            f"{base_url}/ops/routing/flags",
            json={
                "enabled": True,
                "mode": routing_mode,
                "manual_backend": None  # Clear manual override
            },
            timeout=5.0
        )
        if response.status_code == 200:
            logger.info(f"✓ Routing configured for variant ({routing_mode} mode)")
        else:
            logger.warning(f"Routing flags endpoint returned {response.status_code}")
    except Exception as e:
        logger.warning(f"Routing configuration not available: {e}")


async def run_experiment(
    base_url: str,
    qps: float,
    concurrency: int,
    topk_mix: list[int],
    window_sec: int,
    rounds: int,
    seed: int,
    recall_sample: float,
    routing_mode: str
):
    """
    Run ABAB routing experiment with load generation.
    
    Args:
        base_url: Base URL for search API
        qps: Target queries per second
        concurrency: Max concurrent requests
        topk_mix: List of topk values to cycle through
        window_sec: Duration of each A/B window
        rounds: Number of ABAB rounds
        seed: Random seed for deterministic queries
        recall_sample: Fraction to sample for recall
        routing_mode: Routing mode ("rules" or "cost")
    """
    # Check dependencies
    logger.info("Checking dependencies...")
    if not check_dependencies(base_url):
        logger.error("Dependency check failed. Aborting.")
        sys.exit(1)
    
    # Generate experiment ID
    experiment_id = f"route_load_{int(time.time())}"
    logger.info(f"Experiment ID: {experiment_id}")
    
    # Create load generator
    redis_client = get_redis_client()
    loadgen = LabLoadGenerator(
        base_url=base_url,
        qps=qps,
        concurrency=concurrency,
        topk=topk_mix[0],  # Default topk
        seed=seed,
        redis_client=redis_client,
        experiment_id=experiment_id,
        recall_sample=recall_sample,
        topk_mix=topk_mix  # Pass topk mix for cycling
    )
    
    # Configure routing for baseline
    await configure_routing_baseline(base_url)
    
    logger.info("✓ Ready to start load generation")
    
    # Run warmup phase
    logger.info(f"Starting warmup phase (60s)...")
    await loadgen.run_phase("warmup", 60)
    logger.info("✓ Warmup completed")
    
    # Run ABAB rounds
    for round_num in range(rounds):
        logger.info(f"=== Round {round_num + 1}/{rounds} ===")
        
        # Phase A (baseline - all to Qdrant)
        logger.info(f"Starting Phase A ({window_sec}s) - ALL→Qdrant...")
        await configure_routing_baseline(base_url)
        loadgen.reset_query_sequence()  # Reset for deterministic sequence
        await loadgen.run_phase("A", window_sec)
        logger.info("✓ Phase A completed")
        
        # Phase B (variant - smart routing)
        logger.info(f"Starting Phase B ({window_sec}s) - {routing_mode} routing...")
        await configure_routing_variant(base_url, routing_mode)
        loadgen.reset_query_sequence()  # Use same sequence as A
        await loadgen.run_phase("B", window_sec)
        logger.info("✓ Phase B completed")
    
    # Restore baseline
    await configure_routing_baseline(base_url)
    
    logger.info("Experiment completed!")
    
    # Generate report
    logger.info("Generating report...")
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / "LAB_ROUTE_REPORT_MINI.txt"
    
    result = generate_route_report(experiment_id, str(report_path))
    report_text = result.get("report_text", "")
    metrics = result.get("metrics", {})
    
    logger.info(f"✓ Report saved: {report_path}")
    
    # Display report
    print()
    print(report_text)
    print()
    
    # Display key metrics
    print("=" * 70)
    print("KEY METRICS")
    print("=" * 70)
    print(f"ΔP95: {metrics.get('delta_p95_pct', 0):+.1f}%")
    print(f"ΔQPS: {metrics.get('delta_qps_pct', 0):+.1f}%")
    print(f"Error Rate: {metrics.get('error_rate_pct', 0):.2f}%")
    print(f"FAISS Share: {metrics.get('faiss_share_pct', 0):.1f}%")
    print(f"Fallback Count: {metrics.get('fallback_count', 0)}")
    if metrics.get('delta_recall_pct') is not None:
        print(f"ΔRecall: {metrics.get('delta_recall_pct'):+.1f}%")
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Lab Routing experiment with load generation"
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
        type=str,
        default="16,32,64",
        help="Comma-separated topk values to cycle (default: '16,32,64')"
    )
    
    parser.add_argument(
        "--window",
        type=int,
        default=120,
        help="Duration of each A/B window in seconds (default: 120)"
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
        "--routing-mode",
        type=str,
        choices=["rules", "cost"],
        default="rules",
        help="Routing policy mode (default: rules)"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8011",
        help="Base URL for API (default: http://localhost:8011 - app_main with routing)"
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
    
    # Parse topk mix
    topk_mix = parse_topk_mix(args.topk)
    
    # Print configuration
    print("=" * 70)
    print("LAB ROUTING EXPERIMENT WITH LOAD GENERATION")
    print("=" * 70)
    print(f"QPS: {args.qps}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Top-K Mix: {topk_mix}")
    print(f"Window Duration: {args.window}s")
    print(f"Rounds: {args.rounds}")
    print(f"Seed: {args.seed}")
    print(f"Recall Sample: {args.recall_sample}")
    print(f"Routing Mode: {args.routing_mode}")
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
        topk_mix=topk_mix,
        window_sec=args.window,
        rounds=args.rounds,
        seed=args.seed,
        recall_sample=args.recall_sample,
        routing_mode=args.routing_mode
    ))


if __name__ == "__main__":
    main()

