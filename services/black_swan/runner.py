"""
Black Swan Async - Test Runner

Orchestrates Black Swan test runs with phases: warmup → baseline → trip → recovery → complete.
Supports modes A/B/C with different stress patterns and integrates force override.
"""

import asyncio
import time
import logging
import os
from typing import Optional, Dict, Any
from .models import RunConfig, Phase, Metrics, RunMode
from .state import BlackSwanState, get_state
from .loadgen import LoadGenerator, QueryBank
from .guards import Guards, get_guards
from .storage import get_storage

logger = logging.getLogger(__name__)


class BlackSwanRunner:
    """
    Black Swan test runner with async phase execution.
    
    Executes test in phases:
    1. Warmup: Light traffic to establish baseline
    2. Baseline: Capture normal performance metrics
    3. Trip: Apply stress according to mode (A/B/C)
    4. Recovery: Monitor system recovery
    5. Complete: Generate final report
    """
    
    def __init__(
        self,
        config: RunConfig,
        target_url: str = "http://localhost:8080/search",
        state: Optional[BlackSwanState] = None,
        guards: Optional[Guards] = None
    ):
        """
        Initialize runner.
        
        Args:
            config: Run configuration
            target_url: Target endpoint URL
            state: State manager (optional, will create if None)
            guards: Guards instance (optional, will create if None)
        """
        self.config = config
        self.target_url = target_url or os.getenv("FIQA_SEARCH_URL", "http://localhost:8011/search")
        self.state = state or get_state()
        self.guards = guards or get_guards()
        
        # Query bank (shared across phases)
        self.query_bank = QueryBank(unique=config.unique_queries)
        
        # Current load generator
        self.current_loadgen: Optional[LoadGenerator] = None
        
        # Phase metrics collection
        self.phase_metrics: Dict[str, Metrics] = {}
        
        # Run control
        self.run_id: Optional[str] = None
        self.start_time: int = 0
        self.should_stop = False
    
    async def run(self) -> str:
        """
        Execute full test run.
        
        Returns:
            Run ID
            
        Raises:
            RuntimeError: If run fails to start or encounters critical error
        """
        try:
            # Start run and get ID
            self.run_id = await self.state.start_run(self.config)
            self.start_time = int(time.time())
            
            # Note: config.mode is a string (due to use_enum_values=True in Pydantic)
            mode_str = self.config.mode if isinstance(self.config.mode, str) else self.config.mode.value
            logger.info(f"[BS:RUNNER] Starting run {self.run_id} (mode={mode_str})")
            
            # Apply force override to config params
            self._apply_force_override()
            
            # Execute phases
            await self._run_warmup()
            if self.should_stop:
                return self.run_id
            
            await self._run_baseline()
            if self.should_stop:
                return self.run_id
            
            await self._run_trip()
            if self.should_stop:
                return self.run_id
            
            await self._run_recovery()
            if self.should_stop:
                return self.run_id
            
            # Complete
            await self.state.complete(message="Black Swan test completed successfully")
            
            logger.info(f"[BS:RUNNER] Completed run {self.run_id}")
            return self.run_id
        
        except Exception as e:
            logger.exception(f"[BS:RUNNER] Run failed: {e}")
            await self.state.fail(error=str(e))
            raise
    
    def _apply_force_override(self) -> None:
        """Apply force override to configuration parameters."""
        try:
            # Import force override
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent / "fiqa_api"))
            from force_override import apply_force_override, get_force_override_status
            
            # Build params dict
            params = {
                "num_candidates": self.config.candidate_k or 100,
                "rerank_topk": self.config.rerank_top_k or 50,
                "qps": self.config.trip_qps
            }
            
            # Apply override
            mode_str = self.config.mode if isinstance(self.config.mode, str) else self.config.mode.value
            overridden = apply_force_override(params, context=f"black_swan_mode_{mode_str}")
            
            # Update config
            if overridden.get("num_candidates"):
                self.config.candidate_k = overridden["num_candidates"]
            if overridden.get("rerank_topk"):
                self.config.rerank_top_k = overridden["rerank_topk"]
            if overridden.get("qps"):
                self.config.trip_qps = overridden["qps"]
            
            # Get status for precedence chain
            status = get_force_override_status()
            precedence_chain = []
            
            if status["force_override"]:
                precedence_chain.append(f"FORCE_OVERRIDE: {status['active_params']}")
            
            if status["hard_cap_enabled"]:
                precedence_chain.append(f"HARD_CAP: {status['hard_cap_limits']}")
            
            mode_str = self.config.mode if isinstance(self.config.mode, str) else self.config.mode.value
            precedence_chain.append(f"MODE_{mode_str}_DEFAULTS")
            
            # Update state with precedence chain
            asyncio.create_task(self.state.update(precedence_chain=precedence_chain))
            
            logger.info(f"[BS:RUNNER] Force override applied: {overridden}")
        
        except Exception as e:
            logger.warning(f"[BS:RUNNER] Force override failed: {e}")
    
    async def _run_warmup(self) -> None:
        """Execute warmup phase."""
        await self._run_phase(
            phase=Phase.WARMUP,
            qps=self.config.warmup_qps,
            duration=self.config.warmup_duration,
            progress_start=0,
            progress_end=20
        )
    
    async def _run_baseline(self) -> None:
        """Execute baseline phase."""
        await self._run_phase(
            phase=Phase.BASELINE,
            qps=self.config.baseline_qps,
            duration=self.config.baseline_duration,
            progress_start=20,
            progress_end=30
        )
    
    async def _run_trip(self) -> None:
        """Execute trip phase with mode-specific stress."""
        # Mode-specific parameters
        candidate_k = self.config.candidate_k
        rerank_top_k = self.config.rerank_top_k
        
        # Mode B: use heavy params
        if self.config.mode == RunMode.B and (candidate_k or rerank_top_k):
            logger.info(
                f"[BS:RUNNER] Mode B heavy params: candidate_k={candidate_k}, rerank_top_k={rerank_top_k}"
            )
        
        await self._run_phase(
            phase=Phase.TRIP,
            qps=self.config.trip_qps,
            duration=self.config.trip_duration,
            progress_start=30,
            progress_end=70,
            candidate_k=candidate_k,
            rerank_top_k=rerank_top_k
        )
    
    async def _run_recovery(self) -> None:
        """Execute recovery phase."""
        await self._run_phase(
            phase=Phase.RECOVERY,
            qps=self.config.recovery_qps,
            duration=self.config.recovery_duration,
            progress_start=70,
            progress_end=100
        )
    
    async def _run_phase(
        self,
        phase: Phase,
        qps: int,
        duration: int,
        progress_start: int,
        progress_end: int,
        candidate_k: Optional[int] = None,
        rerank_top_k: Optional[int] = None
    ) -> None:
        """
        Execute a single phase.
        
        Args:
            phase: Phase to execute
            qps: Target QPS
            duration: Phase duration (seconds)
            progress_start: Progress at phase start (0-100)
            progress_end: Progress at phase end (0-100)
            candidate_k: Candidate K for retrieval (optional)
            rerank_top_k: Rerank top K (optional)
        """
        phase_start = int(time.time())
        
        # Notify phase change
        await self.guards.on_phase_change(
            from_phase=None if phase == Phase.WARMUP else Phase(list(Phase)[list(Phase).index(phase) - 1]),
            to_phase=phase,
            run_id=self.run_id,
            elapsed_sec=phase_start - self.start_time
        )
        
        # Update state
        await self.state.update(
            phase=phase,
            progress=progress_start,
            eta_sec=(progress_end - progress_start) * duration // (progress_end - progress_start),
            message=f"{phase.value.capitalize()} phase starting ({qps} QPS for {duration}s)"
        )
        
        logger.info(f"[BS:RUNNER] Phase {phase.value}: {qps} QPS × {duration}s")
        
        # Create load generator
        loadgen = LoadGenerator(
            target_url=self.target_url,
            qps=qps,
            duration=duration,
            concurrency=self.config.concurrency,
            unique_queries=self.config.unique_queries,
            bypass_cache=self.config.bypass_cache,
            candidate_k=candidate_k,
            rerank_top_k=rerank_top_k,
            query_bank=self.query_bank,
            phase=phase.value  # Pass phase for QA feed logging
        )
        
        self.current_loadgen = loadgen
        
        # Run load generator in background
        load_task = asyncio.create_task(loadgen.run())
        
        # Monitor progress
        start = time.time()
        while time.time() - start < duration and not self.should_stop:
            await asyncio.sleep(1)
            
            # Calculate progress
            elapsed = time.time() - start
            progress = progress_start + int((progress_end - progress_start) * (elapsed / duration))
            eta = int(duration - elapsed)
            
            # Get current metrics
            metrics_dict = loadgen.get_metrics()
            metrics = Metrics(**metrics_dict)
            
            # Update state
            await self.state.update(
                progress=progress,
                eta_sec=eta,
                metrics=metrics,
                message=f"{phase.value.capitalize()}: {metrics_dict['count']} reqs, P95={metrics_dict['p95_ms']}ms"
            )
            
            # Notify guards
            await self.guards.on_metric_tick(
                metrics=metrics,
                phase=phase,
                run_id=self.run_id,
                elapsed_sec=int(time.time() - self.start_time)
            )
            
            # Check watchdog
            if not self.guards.check_progress(progress, int(time.time())):
                logger.error(f"[BS:RUNNER] Watchdog: no progress in phase {phase.value}")
                should_abort = await self.guards.on_watchdog_trip(
                    reason="no_progress",
                    details={"phase": phase.value, "progress": progress},
                    phase=phase,
                    run_id=self.run_id
                )
                if should_abort:
                    await self.stop()
                    return
        
        # Wait for load generator to finish
        await load_task
        
        # Get final metrics
        final_metrics_dict = loadgen.get_metrics()
        final_metrics = Metrics(**final_metrics_dict)
        
        # Store phase metrics
        self.phase_metrics[phase.value] = final_metrics
        
        logger.info(
            f"[BS:RUNNER] Phase {phase.value} complete: "
            f"{final_metrics.count} reqs, P95={final_metrics.p95_ms}ms, "
            f"errors={final_metrics.errors} ({final_metrics.error_rate*100:.1f}%)"
        )
        
        # Update state with final metrics
        await self.state.update(
            progress=progress_end,
            metrics=final_metrics,
            message=f"{phase.value.capitalize()} phase complete"
        )
    
    async def stop(self) -> None:
        """Stop current run gracefully."""
        logger.info(f"[BS:RUNNER] Stopping run {self.run_id}")
        self.should_stop = True
        
        # Stop current load generator
        if self.current_loadgen:
            await self.current_loadgen.stop()
        
        # Mark as canceled
        await self.state.cancel(reason="Run stopped by user")


async def run_black_swan(
    config: RunConfig,
    target_url: Optional[str] = None
) -> str:
    """
    Run Black Swan test with given configuration.
    
    Args:
        config: Run configuration
        target_url: Target endpoint URL (optional)
        
    Returns:
        Run ID
    """
    runner = BlackSwanRunner(config=config, target_url=target_url)
    return await runner.run()

