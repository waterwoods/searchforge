#!/usr/bin/env python3
"""
Run COMBO Lab Experiment with Load Generation

Runs ABAB experiment with Flow Control + Routing enabled in phase B.
Uses deterministic load generation with seeded queries.
"""

import asyncio
import argparse
import sys
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend_core.lab_loadgen import LabLoadGenerator, get_redis_client
import httpx
import redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


async def run_combo_experiment(
    base_url: str,
    qps: float,
    concurrency: int,
    topk: int,
    window_sec: int,
    rounds: int,
    seed: int,
    flow_policy: str,
    target_p95: int,
    conc_cap: int,
    batch_cap: int,
    routing_mode: str,
    topk_threshold: int,
    recall_sample: float = 0.0
):
    """
    Run combo experiment with load generation.
    
    Args:
        base_url: Base URL for API (e.g., http://localhost:8011)
        qps: Target queries per second
        concurrency: Max concurrent requests
        topk: Top-K results to retrieve (or mix, comma-separated)
        window_sec: Window duration in seconds (per phase)
        rounds: Number of ABAB rounds
        seed: Random seed for deterministic generation
        flow_policy: Flow control policy (aimd/pid-lite)
        target_p95: Target P95 latency in ms
        conc_cap: Max concurrency cap
        batch_cap: Max batch size cap
        routing_mode: Routing mode (rules/cost)
        topk_threshold: TopK threshold for FAISS routing
        recall_sample: Fraction of requests to sample for recall (0..1)
    """
    
    logger.info("=" * 70)
    logger.info("COMBO LAB EXPERIMENT WITH LOAD GENERATION")
    logger.info("=" * 70)
    logger.info(f"Base URL: {base_url}")
    logger.info(f"QPS: {qps}")
    logger.info(f"Concurrency: {concurrency}")
    logger.info(f"TopK: {topk}")
    logger.info(f"Window: {window_sec}s")
    logger.info(f"Rounds: {rounds}")
    logger.info(f"Seed: {seed}")
    logger.info(f"Flow Policy: {flow_policy}")
    logger.info(f"Target P95: {target_p95}ms")
    logger.info(f"Conc Cap: {conc_cap}")
    logger.info(f"Batch Cap: {batch_cap}")
    logger.info(f"Routing Mode: {routing_mode}")
    logger.info(f"TopK Threshold: {topk_threshold}")
    logger.info("=" * 70)
    
    # Parse topk mix if comma-separated
    topk_mix = [int(t.strip()) for t in str(topk).split(',')] if ',' in str(topk) else [topk]
    
    # Generate experiment ID
    experiment_id = f"combo_{int(time.time())}"
    
    # Create Redis client
    redis_client = get_redis_client()
    
    # Create load generator
    loadgen = LabLoadGenerator(
        base_url=base_url,
        qps=qps,
        concurrency=concurrency,
        topk=topk_mix[0],
        seed=seed,
        redis_client=redis_client,
        experiment_id=experiment_id,
        recall_sample=recall_sample,
        topk_mix=topk_mix
    )
    
    # Step 1: Check health
    logger.info("[1/8] Checking system health...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/api/lab/config", timeout=5)
            if response.status_code != 200:
                logger.error(f"Health check failed: HTTP {response.status_code}")
                return 1
            
            health = response.json()
            if not health.get("ok"):
                logger.error("Health check failed")
                return 1
            
            logger.info("✓ System healthy")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return 1
    
    # Step 2: Enable quiet mode
    logger.info("[2/8] Enabling Quiet Mode...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/ops/quiet_mode/enable",
                timeout=5
            )
            if response.status_code != 200:
                logger.error(f"Failed to enable Quiet Mode: HTTP {response.status_code}")
                return 1
            logger.info("✓ Quiet Mode enabled")
        except Exception as e:
            logger.error(f"Failed to enable Quiet Mode: {e}")
            return 1
    
    # Step 3: Prewarm system
    logger.info("[3/8] Prewarming system (60s)...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/ops/lab/prewarm",
                json={"duration_sec": 60},
                timeout=5
            )
            if response.status_code != 200:
                logger.error(f"Failed to start prewarm: HTTP {response.status_code}")
                return 1
            logger.info("✓ Prewarm started, waiting 60s...")
            await asyncio.sleep(60)
            logger.info("✓ Prewarm completed")
        except Exception as e:
            logger.error(f"Failed to prewarm: {e}")
            return 1
    
    # Step 4: Start experiment
    logger.info("[4/8] Starting COMBO experiment...")
    async with httpx.AsyncClient() as client:
        try:
            b_config = {
                "flow_policy": flow_policy,
                "target_p95": target_p95,
                "conc_cap": conc_cap,
                "batch_cap": batch_cap,
                "routing_mode": routing_mode,
                "topk_threshold": topk_threshold
            }
            
            response = await client.post(
                f"{base_url}/ops/lab/start",
                json={
                    "experiment_type": "combo",
                    "a_ms": window_sec * 1000,
                    "b_ms": window_sec * 1000,
                    "rounds": rounds,
                    "b_config": b_config
                },
                timeout=5
            )
            
            if response.status_code != 200 or not response.json().get("ok"):
                logger.error(f"Failed to start experiment: {response.text}")
                return 1
            
            result = response.json()
            experiment_id = result.get("experiment_id", experiment_id)
            logger.info(f"✓ Experiment started: {experiment_id}")
        except Exception as e:
            logger.error(f"Failed to start experiment: {e}")
            return 1
    
    # Update loadgen with correct experiment ID
    loadgen.aggregator.experiment_id = experiment_id
    
    # Step 5: Run load for all ABAB phases
    logger.info("[5/8] Running load generation...")
    
    total_duration = window_sec * 2 * rounds  # A + B per round
    logger.info(f"Total load duration: {total_duration}s ({total_duration // 60}m {total_duration % 60}s)")
    
    for round_num in range(rounds):
        # Phase A - Disable routing (baseline: all → Qdrant)
        logger.info(f"Round {round_num + 1}/{rounds} - Phase A (baseline)")
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{base_url}/ops/routing/flags",
                    json={"enabled": False, "manual_backend": None},
                    timeout=5
                )
                logger.info("✓ Routing disabled for Phase A")
            except Exception as e:
                logger.warning(f"Failed to disable routing: {e}")
        
        loadgen.reset_query_sequence()  # Reset seed for deterministic queries
        await loadgen.run_phase("A", window_sec)
        
        # Phase B - Enable routing (variant: FAISS-first)
        logger.info(f"Round {round_num + 1}/{rounds} - Phase B (variant)")
        
        # Check FAISS readiness
        routing_ok = False
        async with httpx.AsyncClient() as client:
            try:
                # Check routing status
                status_resp = await client.get(f"{base_url}/ops/routing/status", timeout=3)
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    if not status_data.get("faiss_ready", False):
                        logger.warning("⚠️ ROUTING_DISABLED_WARNING: FAISS not ready, routing may fail")
                
                # Enable routing
                response = await client.post(
                    f"{base_url}/ops/routing/flags",
                    json={
                        "enabled": True,
                        "policy": routing_mode,
                        "topk_threshold": topk_threshold,
                        "manual_backend": None
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    logger.info(f"✓ Routing enabled: mode={routing_mode}, threshold={topk_threshold}")
                    routing_ok = True
                else:
                    logger.warning(f"⚠️ ROUTING_DISABLED_WARNING: HTTP {response.status_code}, Phase B will fallback to Qdrant")
            except Exception as e:
                logger.warning(f"⚠️ ROUTING_DISABLED_WARNING: {e}, Phase B will fallback to Qdrant")
        
        loadgen.reset_query_sequence()  # Reset seed for same queries
        await loadgen.run_phase("B", window_sec)
    
    logger.info("✓ Load generation completed")
    
    # Step 6: Stop experiment
    logger.info("[6/8] Stopping experiment...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{base_url}/ops/lab/stop", timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ Experiment stopped: {result.get('windows_collected', 0)} windows collected")
            else:
                logger.warning(f"Stop returned HTTP {response.status_code} (may have auto-completed)")
        except Exception as e:
            logger.warning(f"Failed to stop experiment: {e}")
    
    # Step 7: Fetch report
    logger.info("[7/8] Fetching report...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/ops/lab/report", timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    logger.info("✓ Report generated")
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("REPORT PREVIEW")
                    logger.info("=" * 70)
                    # Print first 30 lines of report
                    report_lines = result.get("report", "").split("\n")
                    for line in report_lines[:30]:
                        print(line)
                    if len(report_lines) > 30:
                        logger.info("...")
                    logger.info("=" * 70)
                else:
                    logger.warning("Report not available")
        except Exception as e:
            logger.warning(f"Failed to fetch report: {e}")
    
    # Step 8: Get mini metrics
    logger.info("[8/8] Fetching mini metrics...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/ops/lab/report?mini=1", timeout=5)
            if response.status_code == 200:
                metrics = response.json()
                if metrics.get("ok"):
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("MINI METRICS")
                    logger.info("=" * 70)
                    logger.info(f"ΔP95: {metrics.get('delta_p95_pct', 0):+.2f}%")
                    logger.info(f"ΔQPS: {metrics.get('delta_qps_pct', 0):+.2f}%")
                    logger.info(f"Error Rate: {metrics.get('error_rate_pct', 0):.2f}%")
                    logger.info(f"FAISS Share: {metrics.get('faiss_share_pct', 0):.2f}%")
                    logger.info(f"Fallback Count: {metrics.get('fallback_count', 0)}")
                    logger.info("=" * 70)
                    
                    # Check acceptance criteria
                    error_rate = metrics.get('error_rate_pct', 100)
                    faiss_share = metrics.get('faiss_share_pct', 0)
                    
                    if error_rate < 1.0 and faiss_share >= 20.0:
                        logger.info("✅ ACCEPTANCE CRITERIA MET")
                        logger.info(f"   - Error rate < 1%: {error_rate:.2f}% ✓")
                        logger.info(f"   - FAISS share ≥ 20%: {faiss_share:.2f}% ✓")
                    else:
                        logger.warning("⚠ ACCEPTANCE CRITERIA NOT MET")
                        if error_rate >= 1.0:
                            logger.warning(f"   - Error rate ≥ 1%: {error_rate:.2f}% ✗")
                        if faiss_share < 20.0:
                            logger.warning(f"   - FAISS share < 20%: {faiss_share:.2f}% ✗")
        except Exception as e:
            logger.warning(f"Failed to fetch mini metrics: {e}")
    
    # Disable quiet mode
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{base_url}/ops/quiet_mode/disable",
                timeout=5
            )
            logger.info("✓ Quiet Mode disabled")
        except:
            pass
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ COMBO EXPERIMENT COMPLETE")
    logger.info("=" * 70)
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run COMBO lab experiment with load generation")
    parser.add_argument("--base-url", default="http://localhost:8011", help="Base URL for API")
    parser.add_argument("--qps", type=float, default=10.0, help="Target queries per second")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent requests")
    parser.add_argument("--topk", default="10", help="Top-K or comma-separated mix (e.g., '16,32,64')")
    parser.add_argument("--window", type=int, default=120, help="Window duration in seconds (per phase)")
    parser.add_argument("--rounds", type=int, default=2, help="Number of ABAB rounds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--flow-policy", default="aimd", help="Flow control policy (aimd/pid-lite)")
    parser.add_argument("--target-p95", type=int, default=1200, help="Target P95 latency in ms")
    parser.add_argument("--conc-cap", type=int, default=32, help="Max concurrency cap")
    parser.add_argument("--batch-cap", type=int, default=32, help="Max batch size cap")
    parser.add_argument("--routing-mode", default="rules", help="Routing mode (rules/cost)")
    parser.add_argument("--topk-threshold", type=int, default=32, help="TopK threshold for FAISS routing")
    parser.add_argument("--recall-sample", type=float, default=0.0, help="Recall sampling rate (0..1)")
    
    args = parser.parse_args()
    
    result = asyncio.run(run_combo_experiment(
        base_url=args.base_url,
        qps=args.qps,
        concurrency=args.concurrency,
        topk=args.topk,
        window_sec=args.window,
        rounds=args.rounds,
        seed=args.seed,
        flow_policy=args.flow_policy,
        target_p95=args.target_p95,
        conc_cap=args.conc_cap,
        batch_cap=args.batch_cap,
        routing_mode=args.routing_mode,
        topk_threshold=args.topk_threshold,
        recall_sample=args.recall_sample
    ))
    
    sys.exit(result)


if __name__ == "__main__":
    main()

