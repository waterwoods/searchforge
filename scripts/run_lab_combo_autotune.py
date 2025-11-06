#!/usr/bin/env python3
"""
COMBO Auto-Tune - Run multiple COMBO experiments with parameter sweeps

Automatically tests multiple parameter combinations and reports the best configuration.
"""

import asyncio
import argparse
import sys
import json
import time
import httpx
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from itertools import product

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_lab_combo_with_load import run_combo_experiment
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    """Result from a single experiment."""
    params: Dict[str, Any]
    delta_p95_pct: float
    delta_qps_pct: float
    error_rate_pct: float
    faiss_share_pct: float
    fallback_count: int
    success: bool
    experiment_id: str
    early_stopped: bool = False
    stop_reason: str = ""
    phase_a_requests: int = 0
    phase_b_requests: int = 0
    ab_balance_warning: bool = False


async def check_health_status(base_url: str) -> Tuple[bool, str]:
    """
    Check system health before starting experiment.
    
    Returns:
        (is_healthy, reason) tuple
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/lab/config", timeout=5)
            if response.status_code != 200:
                return False, "lab_config_unavailable"
            
            data = response.json()
            if not data.get("redis_ok"):
                return False, "redis_down"
            if not data.get("qdrant_ok"):
                return False, "qdrant_down"
            
            return True, "ok"
    except Exception as e:
        return False, f"health_check_failed: {e}"


async def enable_routing(base_url: str, mode: str, threshold: int) -> bool:
    """Enable routing for Phase B."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/ops/routing/flags",
                json={
                    "enabled": True,
                    "policy": mode,
                    "topk_threshold": threshold,
                    "manual_backend": None
                },
                timeout=5
            )
            if response.status_code == 200:
                logger.info(f"✓ Routing enabled: mode={mode}, threshold={threshold}")
                return True
            else:
                logger.warning(f"ROUTING_DISABLED_WARNING: HTTP {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Failed to enable routing: {e}")
        return False


async def disable_routing(base_url: str) -> bool:
    """Disable routing for Phase A."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/ops/routing/flags",
                json={
                    "enabled": False,
                    "manual_backend": None
                },
                timeout=5
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to disable routing: {e}")
        return False


async def monitor_early_stop(
    base_url: str,
    experiment_id: str,
    early_stop_threshold: int,
    check_interval: int = 5
) -> Tuple[bool, str]:
    """
    Monitor experiment for early stop condition.
    Checks Redis every 5s for ΔP95 degradation.
    
    Returns:
        (should_stop, reason) tuple
    """
    import redis
    consecutive_worse = 0
    
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
        
        while True:
            await asyncio.sleep(check_interval)
            
            # Check if experiment is still running
            try:
                async with httpx.AsyncClient() as client:
                    status_resp = await client.get(f"{base_url}/ops/lab/status", timeout=3)
                    if status_resp.status_code != 200:
                        return False, "status_check_failed"
                    
                    status = status_resp.json()
                    if not status.get("is_running"):
                        return False, "experiment_completed"
            except:
                return False, "status_check_failed"
            
            # Read aggregated metrics from Redis
            agg_key = f"lab:exp:{experiment_id}:agg"
            try:
                agg_data = redis_client.get(agg_key)
                if not agg_data:
                    continue
                
                import json
                metrics = json.loads(agg_data)
                
                # Get last 3 valid windows (noise <= 40)
                windows = []
                for m in metrics:
                    if m.get("noise_score", 100) <= 40:
                        windows.append(m)
                
                if len(windows) < 3:
                    continue
                
                recent = windows[-3:]
                
                # Calculate ΔP95 for Phase B vs A
                a_p95_sum = sum(m.get("p95", 0) for m in recent if m.get("phase") == "A")
                b_p95_sum = sum(m.get("p95", 0) for m in recent if m.get("phase") == "B")
                a_count = sum(1 for m in recent if m.get("phase") == "A")
                b_count = sum(1 for m in recent if m.get("phase") == "B")
                
                if a_count == 0 or b_count == 0:
                    continue
                
                a_p95 = a_p95_sum / a_count
                b_p95 = b_p95_sum / b_count
                delta_p95 = b_p95 - a_p95
                
                # Check if B is consistently worse
                if delta_p95 > 0:
                    consecutive_worse += 1
                    logger.debug(f"Early stop monitor: ΔP95={delta_p95:.1f}ms, consecutive={consecutive_worse}")
                    
                    if consecutive_worse >= early_stop_threshold:
                        return True, f"delta_p95_worse_x{consecutive_worse}"
                else:
                    consecutive_worse = 0
                    
            except Exception as e:
                logger.debug(f"Early stop monitor error: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Early stop monitor failed: {e}")
        return False, "monitor_error"


async def run_single_experiment(
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
    recall_sample: float,
    per_combo_cap: int = 0,
    early_stop_threshold: int = 0
) -> ExperimentResult:
    """
    Run a single experiment with given parameters.
    
    Returns:
        ExperimentResult with metrics and success status
    """
    params = {
        "flow_policy": flow_policy,
        "target_p95": target_p95,
        "conc_cap": conc_cap,
        "batch_cap": batch_cap,
        "routing_mode": routing_mode,
        "topk_threshold": topk_threshold
    }
    
    logger.info("=" * 70)
    logger.info(f"Running experiment with: {params}")
    logger.info("=" * 70)
    
    early_stopped = False
    stop_reason = ""
    phase_a_requests = 0
    phase_b_requests = 0
    
    # Step 1: Health check
    logger.info("Checking system health...")
    is_healthy, health_reason = await check_health_status(base_url)
    if not is_healthy:
        logger.error(f"HEALTH_GATE_BLOCKED: {health_reason}")
        return ExperimentResult(
            params=params,
            delta_p95_pct=0,
            delta_qps_pct=0,
            error_rate_pct=100,
            faiss_share_pct=0,
            fallback_count=0,
            success=False,
            experiment_id="health_blocked",
            early_stopped=False,
            stop_reason=f"health_gate: {health_reason}",
            phase_a_requests=0,
            phase_b_requests=0,
            ab_balance_warning=False
        )
    logger.info("✓ System healthy")
    
    try:
        # Step 2: Start experiment and optional early stop monitor
        monitor_task = None
        experiment_id_for_monitor = f"combo_{int(time.time())}"
        
        if early_stop_threshold > 0:
            # Launch background monitor
            monitor_task = asyncio.create_task(
                monitor_early_stop(base_url, experiment_id_for_monitor, early_stop_threshold)
            )
            logger.info(f"Early stop monitor started (threshold={early_stop_threshold})")
        
        # Run experiment
        experiment_task = asyncio.create_task(
            run_combo_experiment(
                base_url=base_url,
                qps=qps,
                concurrency=concurrency,
                topk=topk,
                window_sec=window_sec,
                rounds=rounds,
                seed=seed,
                flow_policy=flow_policy,
                target_p95=target_p95,
                conc_cap=conc_cap,
                batch_cap=batch_cap,
                routing_mode=routing_mode,
                topk_threshold=topk_threshold,
                recall_sample=recall_sample
            )
        )
        
        # Wait for either experiment completion or early stop
        if monitor_task:
            done, pending = await asyncio.wait(
                [experiment_task, monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Check if early stop triggered
            if monitor_task in done:
                should_stop, reason = monitor_task.result()
                if should_stop:
                    early_stopped = True
                    stop_reason = reason
                    logger.warning(f"EARLY_STOP triggered: {reason}")
                    
                    # Stop the experiment
                    try:
                        async with httpx.AsyncClient() as client:
                            await client.post(f"{base_url}/ops/lab/stop", timeout=5)
                    except:
                        pass
                    
                    # Wait for experiment task to finish
                    try:
                        await asyncio.wait_for(experiment_task, timeout=10)
                    except:
                        pass
            
            # Cancel any remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            exit_code = experiment_task.result() if experiment_task.done() else 1
        else:
            exit_code = await experiment_task
        
        # Step 3: Get metrics from mini endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/ops/lab/report?mini=1", timeout=5)
            if response.status_code == 200:
                metrics = response.json()
                if metrics.get("ok"):
                    # Check A/B balance
                    phase_a_requests = metrics.get("phase_a_requests", 0)
                    phase_b_requests = metrics.get("phase_b_requests", 0)
                    ab_balance_warning = False
                    
                    if phase_a_requests > 0 and phase_b_requests > 0:
                        diff_pct = abs(phase_a_requests - phase_b_requests) / max(phase_a_requests, phase_b_requests) * 100
                        if diff_pct > 5.0:
                            ab_balance_warning = True
                            logger.warning(f"UNBALANCED_AB: A={phase_a_requests}, B={phase_b_requests}, diff={diff_pct:.1f}%")
                    
                    return ExperimentResult(
                        params=params,
                        delta_p95_pct=metrics.get("delta_p95_pct", 0),
                        delta_qps_pct=metrics.get("delta_qps_pct", 0),
                        error_rate_pct=metrics.get("error_rate_pct", 0),
                        faiss_share_pct=metrics.get("faiss_share_pct", 0),
                        fallback_count=metrics.get("fallback_count", 0),
                        success=exit_code == 0,
                        experiment_id=metrics.get("experiment_id", "unknown"),
                        early_stopped=early_stopped,
                        stop_reason=stop_reason,
                        phase_a_requests=phase_a_requests,
                        phase_b_requests=phase_b_requests,
                        ab_balance_warning=ab_balance_warning
                    )
        
        # Fallback if metrics not available
        return ExperimentResult(
            params=params,
            delta_p95_pct=0,
            delta_qps_pct=0,
            error_rate_pct=100,
            faiss_share_pct=0,
            fallback_count=0,
            success=False,
            experiment_id="failed",
            early_stopped=early_stopped,
            stop_reason=stop_reason,
            phase_a_requests=0,
            phase_b_requests=0,
            ab_balance_warning=False
        )
        
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        return ExperimentResult(
            params=params,
            delta_p95_pct=0,
            delta_qps_pct=0,
            error_rate_pct=100,
            faiss_share_pct=0,
            fallback_count=0,
            success=False,
            experiment_id="error",
            early_stopped=early_stopped,
            stop_reason=str(e),
            phase_a_requests=0,
            phase_b_requests=0,
            ab_balance_warning=False
        )


def load_completed_results(jsonl_path: Path) -> Dict[str, ExperimentResult]:
    """Load completed experiments from JSONL file."""
    completed = {}
    if not jsonl_path.exists():
        return completed
    
    try:
        with open(jsonl_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                params_key = json.dumps(data['params'], sort_keys=True)
                completed[params_key] = ExperimentResult(
                    params=data['params'],
                    delta_p95_pct=data['delta_p95_pct'],
                    delta_qps_pct=data['delta_qps_pct'],
                    error_rate_pct=data['error_rate_pct'],
                    faiss_share_pct=data['faiss_share_pct'],
                    fallback_count=data['fallback_count'],
                    success=data['success'],
                    experiment_id=data['experiment_id'],
                    early_stopped=data.get('early_stopped', False),
                    stop_reason=data.get('stop_reason', ''),
                    phase_a_requests=data.get('phase_a_requests', 0),
                    phase_b_requests=data.get('phase_b_requests', 0),
                    ab_balance_warning=data.get('ab_balance_warning', False)
                )
    except Exception as e:
        logger.warning(f"Failed to load completed results: {e}")
    
    return completed


def append_result_to_jsonl(result: ExperimentResult, jsonl_path: Path):
    """Append experiment result to JSONL file."""
    try:
        jsonl_path.parent.mkdir(exist_ok=True)
        with open(jsonl_path, 'a') as f:
            data = {
                "params": result.params,
                "delta_p95_pct": result.delta_p95_pct,
                "delta_qps_pct": result.delta_qps_pct,
                "error_rate_pct": result.error_rate_pct,
                "faiss_share_pct": result.faiss_share_pct,
                "fallback_count": result.fallback_count,
                "success": result.success,
                "experiment_id": result.experiment_id,
                "early_stopped": result.early_stopped,
                "stop_reason": result.stop_reason,
                "phase_a_requests": result.phase_a_requests,
                "phase_b_requests": result.phase_b_requests,
                "ab_balance_warning": result.ab_balance_warning,
                "timestamp": time.time()
            }
            f.write(json.dumps(data) + '\n')
    except Exception as e:
        logger.error(f"Failed to append result to JSONL: {e}")


async def apply_best_config(base_url: str, best_result: ExperimentResult) -> bool:
    """Apply best configuration to /ops/flags."""
    logger.info("Applying best configuration to /ops/flags...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Apply flow control flags
            flow_response = await client.post(
                f"{base_url}/ops/control/flags",
                json={
                    "target_p95_ms": best_result.params['target_p95'],
                    "max_concurrency": best_result.params['conc_cap'],
                    "max_batch_size": best_result.params['batch_cap']
                },
                timeout=10
            )
            
            # Apply routing flags
            routing_response = await client.post(
                f"{base_url}/ops/routing/flags",
                json={
                    "enabled": True,
                    "policy": best_result.params['routing_mode'],
                    "topk_threshold": best_result.params['topk_threshold']
                },
                timeout=10
            )
            
            if flow_response.status_code == 200 and routing_response.status_code == 200:
                logger.info("✓ Best configuration applied successfully")
                return True
            else:
                logger.error(f"Failed to apply config: flow={flow_response.status_code}, routing={routing_response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to apply best configuration: {e}")
        return False


async def run_autotune(
    base_url: str,
    qps: float,
    concurrency: int,
    topk: int,
    window_sec: int,
    rounds: int,
    seed: int,
    flow_policy: str,
    target_p95_values: List[int],
    conc_cap_values: List[int],
    batch_cap_values: List[int],
    routing_mode: str,
    topk_threshold_values: List[int],
    recall_sample: float,
    cooldown_sec: int = 30,
    time_budget: int = 0,
    per_combo_cap: int = 0,
    early_stop_threshold: int = 0,
    apply_best: bool = False,
    resume: bool = False
):
    """
    Run auto-tune with multiple parameter combinations.
    
    Args:
        target_p95_values: List of target P95 values to test
        conc_cap_values: List of concurrency cap values
        batch_cap_values: List of batch cap values
        topk_threshold_values: List of topk threshold values
        cooldown_sec: Cooldown time between experiments
        time_budget: Total time budget in seconds (0 = unlimited)
        per_combo_cap: Per-combo time cap in seconds (0 = unlimited)
        early_stop_threshold: Early stop after N consecutive worse buckets (0 = disabled)
        apply_best: Apply best configuration to /ops/flags after completion
        resume: Resume from previous run (skip completed combos)
    """
    
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("COMBO AUTO-TUNE")
    logger.info("=" * 70)
    logger.info(f"Testing {len(target_p95_values)} target P95 values: {target_p95_values}")
    logger.info(f"Testing {len(conc_cap_values)} conc cap values: {conc_cap_values}")
    logger.info(f"Testing {len(batch_cap_values)} batch cap values: {batch_cap_values}")
    logger.info(f"Testing {len(topk_threshold_values)} topk threshold values: {topk_threshold_values}")
    logger.info(f"Time budget: {time_budget}s" if time_budget > 0 else "Time budget: unlimited")
    logger.info(f"Per-combo cap: {per_combo_cap}s" if per_combo_cap > 0 else "Per-combo cap: unlimited")
    logger.info(f"Early stop: {early_stop_threshold} buckets" if early_stop_threshold > 0 else "Early stop: disabled")
    logger.info(f"Apply best: {'yes' if apply_best else 'no'}")
    logger.info(f"Resume: {'yes' if resume else 'no'}")
    
    # Generate all combinations
    combinations = list(product(
        target_p95_values,
        conc_cap_values,
        batch_cap_values,
        topk_threshold_values
    ))
    
    total_experiments = len(combinations)
    logger.info(f"Total experiments to run: {total_experiments}")
    logger.info("=" * 70)
    
    # Setup result files
    jsonl_path = Path("reports/combo_autotune_results.jsonl")
    summary_path = Path("reports/combo_autotune_summary.json")
    best_config_path = Path("reports/best_config.json")
    
    # Load completed results if resume
    completed_results = {}
    if resume:
        completed_results = load_completed_results(jsonl_path)
        logger.info(f"Loaded {len(completed_results)} completed experiments")
    
    # Run all experiments
    results: List[ExperimentResult] = list(completed_results.values())
    
    budget_reached = False
    experiments_run = 0
    
    for idx, (target_p95, conc_cap, batch_cap, topk_threshold) in enumerate(combinations):
        # Check if already completed (for resume)
        params = {
            "flow_policy": flow_policy,
            "target_p95": target_p95,
            "conc_cap": conc_cap,
            "batch_cap": batch_cap,
            "routing_mode": routing_mode,
            "topk_threshold": topk_threshold
        }
        params_key = json.dumps(params, sort_keys=True)
        
        if params_key in completed_results:
            logger.info(f"[{idx + 1}/{total_experiments}] Skipping (already completed): {params}")
            continue
        
        # Check time budget
        if time_budget > 0:
            elapsed = time.time() - start_time
            remaining = time_budget - elapsed
            # Estimate time needed: experiment + cooldown
            estimated_needed = (window_sec * 2 * rounds) + cooldown_sec
            
            if remaining < estimated_needed:
                logger.warning(f"BUDGET_REACHED: {remaining:.0f}s remaining, need ~{estimated_needed:.0f}s")
                budget_reached = True
                break
        
        logger.info(f"\n[{idx + 1}/{total_experiments}] Starting experiment...")
        
        result = await run_single_experiment(
            base_url=base_url,
            qps=qps,
            concurrency=concurrency,
            topk=topk,
            window_sec=window_sec,
            rounds=rounds,
            seed=seed,
            flow_policy=flow_policy,
            target_p95=target_p95,
            conc_cap=conc_cap,
            batch_cap=batch_cap,
            routing_mode=routing_mode,
            topk_threshold=topk_threshold,
            recall_sample=recall_sample,
            per_combo_cap=per_combo_cap,
            early_stop_threshold=early_stop_threshold
        )
        
        results.append(result)
        experiments_run += 1
        
        # Append to JSONL immediately
        append_result_to_jsonl(result, jsonl_path)
        
        if result.early_stopped:
            logger.warning(f"EARLY_STOP combo={idx+1} reason={result.stop_reason}")
        
        # Cooldown between experiments
        if idx < total_experiments - 1:
            logger.info(f"Cooling down for {cooldown_sec}s before next experiment...")
            await asyncio.sleep(cooldown_sec)
    
    # Determine completion status
    total_completed = len(results)
    if budget_reached:
        status = "BUDGET_REACHED"
    elif total_completed == total_experiments:
        status = "ALL_DONE"
    else:
        status = "PARTIAL"
    
    logger.info(f"\n{status}: Completed {total_completed}/{total_experiments} experiments (ran {experiments_run} new)")
    
    # Analyze results
    logger.info("\n" + "=" * 70)
    logger.info("AUTO-TUNE RESULTS")
    logger.info("=" * 70)
    
    # Collect statistics
    ab_warnings = [r for r in results if r.ab_balance_warning]
    early_stopped_count = sum(1 for r in results if r.early_stopped)
    routing_warnings = sum(1 for r in results if "routing" in r.stop_reason.lower())
    
    faiss_shares = [r.faiss_share_pct for r in results if r.success]
    faiss_share_min = min(faiss_shares) if faiss_shares else 0.0
    faiss_share_max = max(faiss_shares) if faiss_shares else 0.0
    
    if ab_warnings:
        logger.warning(f"⚠ {len(ab_warnings)}/{len(results)} experiments had A/B balance warnings (>5% diff)")
    if early_stopped_count > 0:
        logger.info(f"📊 {early_stopped_count}/{len(results)} experiments stopped early")
    
    # Filter successful experiments
    successful = [r for r in results if r.success and r.error_rate_pct < 1.0 and r.faiss_share_pct >= 20.0]
    
    if not successful:
        logger.warning("⚠ No successful experiments meeting criteria (Err < 1%, FAISS ≥ 20%)")
        logger.info("\nAll results:")
        for r in results:
            logger.info(f"  {r.params}: ΔP95={r.delta_p95_pct:+.1f}%, FAISS={r.faiss_share_pct:.1f}%, Err={r.error_rate_pct:.2f}%")
        
        # Write summary even on failure
        summary_data = {
            "status": status,
            "timestamp": time.time(),
            "total_experiments": total_experiments,
            "completed": len(results),
            "successful": 0,
            "best": None,
            "apply_best": False,
            "ab_balance_warnings": len(ab_warnings),
            "early_stopped_count": early_stopped_count,
            "routing_warnings": routing_warnings,
            "faiss_share_min": round(faiss_share_min, 2),
            "faiss_share_max": round(faiss_share_max, 2)
        }
        summary_path.parent.mkdir(exist_ok=True)
        summary_path.write_text(json.dumps(summary_data, indent=2))
        logger.info(f"\n✓ Summary saved to: {summary_path}")
        return
    
    # Sort by: 1) ΔP95 ascending, 2) Error rate ascending, 3) ΔQPS descending
    successful.sort(key=lambda r: (r.delta_p95_pct, r.error_rate_pct, -r.delta_qps_pct))
    
    logger.info(f"\nSuccessful experiments: {len(successful)}/{total_experiments}")
    logger.info("")
    
    # Print top 5 results
    logger.info("TOP 5 CONFIGURATIONS:")
    logger.info("-" * 70)
    for i, r in enumerate(successful[:5]):
        logger.info(f"\n#{i + 1}: ΔP95 = {r.delta_p95_pct:+.1f}%")
        logger.info(f"  Parameters:")
        for k, v in r.params.items():
            logger.info(f"    {k}: {v}")
        logger.info(f"  Metrics:")
        logger.info(f"    ΔQPS: {r.delta_qps_pct:+.1f}%")
        logger.info(f"    Error Rate: {r.error_rate_pct:.2f}%")
        logger.info(f"    FAISS Share: {r.faiss_share_pct:.1f}%")
        logger.info(f"    Fallbacks: {r.fallback_count}")
    
    # Best configuration
    best = successful[0]
    logger.info("\n" + "=" * 70)
    logger.info("🏆 BEST CONFIGURATION")
    logger.info("=" * 70)
    logger.info(f"ΔP95: {best.delta_p95_pct:+.1f}%")
    logger.info(f"ΔQPS: {best.delta_qps_pct:+.1f}%")
    logger.info(f"Error Rate: {best.error_rate_pct:.2f}%")
    logger.info(f"FAISS Share: {best.faiss_share_pct:.1f}%")
    logger.info(f"\nRecommended parameters:")
    logger.info(f"  --target-p95 {best.params['target_p95']}")
    logger.info(f"  --conc-cap {best.params['conc_cap']}")
    logger.info(f"  --batch-cap {best.params['batch_cap']}")
    logger.info(f"  --topk-threshold {best.params['topk_threshold']}")
    logger.info("=" * 70)
    
    # Apply best configuration if requested
    apply_success = False
    if apply_best:
        apply_success = await apply_best_config(base_url, best)
        
        if apply_success:
            # Save best config
            best_config_data = {
                "timestamp": time.time(),
                "params": best.params,
                "metrics": {
                    "delta_p95_pct": best.delta_p95_pct,
                    "delta_qps_pct": best.delta_qps_pct,
                    "error_rate_pct": best.error_rate_pct,
                    "faiss_share_pct": best.faiss_share_pct,
                    "fallback_count": best.fallback_count
                },
                "applied": True
            }
            best_config_path.write_text(json.dumps(best_config_data, indent=2))
            logger.info(f"✓ Best config saved to: {best_config_path}")
        else:
            logger.error("✗ Failed to apply best configuration")
    
    # Save summary
    summary_data = {
        "status": status,
        "timestamp": time.time(),
        "total_experiments": total_experiments,
        "completed": len(results),
        "successful": len(successful),
        "best": {
            "params": best.params,
            "metrics": {
                "delta_p95_pct": best.delta_p95_pct,
                "delta_qps_pct": best.delta_qps_pct,
                "error_rate_pct": best.error_rate_pct,
                "faiss_share_pct": best.faiss_share_pct,
                "fallback_count": best.fallback_count
            }
        },
        "apply_best": apply_success if apply_best else False,
        "ab_balance_warnings": len(ab_warnings),
        "early_stopped_count": early_stopped_count,
        "routing_warnings": routing_warnings,
        "faiss_share_min": round(faiss_share_min, 2),
        "faiss_share_max": round(faiss_share_max, 2)
    }
    
    summary_path.write_text(json.dumps(summary_data, indent=2))
    logger.info(f"\n✓ Summary saved to: {summary_path}")


def parse_int_list(value: str) -> List[int]:
    """Parse comma-separated list of integers."""
    return [int(x.strip()) for x in value.split(',')]


def main():
    parser = argparse.ArgumentParser(description="Auto-tune COMBO experiment parameters")
    parser.add_argument("--base-url", default="http://localhost:8011", help="Base URL for API")
    parser.add_argument("--qps", type=float, default=10.0, help="Target queries per second")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent requests")
    parser.add_argument("--topk", default="10", help="Top-K or comma-separated mix")
    parser.add_argument("--window", type=int, default=60, help="Window duration in seconds (per phase)")
    parser.add_argument("--rounds", type=int, default=1, help="Number of ABAB rounds per experiment")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--flow-policy", default="aimd", help="Flow control policy (aimd/pid-lite)")
    parser.add_argument("--target-p95", required=True, help="Comma-separated target P95 values (e.g., '1200,1400,1600')")
    parser.add_argument("--conc-cap", default="32", help="Comma-separated conc cap values (default: '32')")
    parser.add_argument("--batch-cap", default="32", help="Comma-separated batch cap values (default: '32')")
    parser.add_argument("--routing-mode", default="rules", help="Routing mode (rules/cost)")
    parser.add_argument("--topk-threshold", required=True, help="Comma-separated topk threshold values (e.g., '16,32,48,64')")
    parser.add_argument("--recall-sample", type=float, default=0.0, help="Recall sampling rate (0..1)")
    parser.add_argument("--cooldown", type=int, default=30, help="Cooldown seconds between experiments")
    parser.add_argument("--time-budget", type=int, default=0, help="Total time budget in seconds (0=unlimited)")
    parser.add_argument("--per-combo-cap", type=int, default=0, help="Per-combo time cap in seconds (0=unlimited)")
    parser.add_argument("--early-stop", type=int, default=0, help="Early stop after N consecutive worse buckets (0=disabled)")
    parser.add_argument("--apply-best", action='store_true', help="Apply best configuration to /ops/flags")
    parser.add_argument("--resume", action='store_true', help="Resume from previous run")
    
    args = parser.parse_args()
    
    # Parse parameter lists
    target_p95_values = parse_int_list(args.target_p95)
    conc_cap_values = parse_int_list(args.conc_cap)
    batch_cap_values = parse_int_list(args.batch_cap)
    topk_threshold_values = parse_int_list(args.topk_threshold)
    
    result = asyncio.run(run_autotune(
        base_url=args.base_url,
        qps=args.qps,
        concurrency=args.concurrency,
        topk=args.topk,
        window_sec=args.window,
        rounds=args.rounds,
        seed=args.seed,
        flow_policy=args.flow_policy,
        target_p95_values=target_p95_values,
        conc_cap_values=conc_cap_values,
        batch_cap_values=batch_cap_values,
        routing_mode=args.routing_mode,
        topk_threshold_values=topk_threshold_values,
        recall_sample=args.recall_sample,
        cooldown_sec=args.cooldown,
        time_budget=args.time_budget,
        per_combo_cap=args.per_combo_cap,
        early_stop_threshold=args.early_stop,
        apply_best=args.apply_best,
        resume=args.resume
    ))
    
    sys.exit(0)


if __name__ == "__main__":
    main()

