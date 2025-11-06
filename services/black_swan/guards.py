"""
Black Swan Async - Guardrails & Watchdog Hooks

Provides hooks for monitoring and intervention during test runs:
- on_phase_change: Called when phase transitions
- on_metric_tick: Called every second with current metrics
- on_guardrail_violation: Called when SLA is violated
- on_watchdog_trip: Called when watchdog detects anomaly

All hooks are no-op by default but can be customized for production use.
"""

import logging
from typing import Optional, Dict, Any
from .models import Phase, Metrics

logger = logging.getLogger(__name__)


class Guards:
    """
    Guardrails and watchdog monitoring system.
    
    Provides hooks for external monitoring and intervention.
    Default implementation logs events but takes no action.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        p95_threshold_ms: float = 200.0,
        watchdog_no_progress_sec: int = 30,
        watchdog_p95_threshold_ms: float = 1000.0,
        log_events: bool = True
    ):
        """
        Initialize guards.
        
        Args:
            enabled: Enable guardrails
            p95_threshold_ms: P95 threshold for guardrail violations (ms)
            watchdog_no_progress_sec: Watchdog no-progress threshold (seconds)
            watchdog_p95_threshold_ms: Watchdog P95 threshold (ms)
            log_events: Log events to console
        """
        self.enabled = enabled
        self.p95_threshold_ms = p95_threshold_ms
        self.watchdog_no_progress_sec = watchdog_no_progress_sec
        self.watchdog_p95_threshold_ms = watchdog_p95_threshold_ms
        self.log_events = log_events
        
        # State tracking
        self.last_progress = 0
        self.last_progress_time = 0
        self.last_phase = None
        self.violation_count = 0
    
    async def on_phase_change(
        self,
        from_phase: Optional[Phase],
        to_phase: Phase,
        run_id: str,
        elapsed_sec: int
    ) -> None:
        """
        Called when phase transitions.
        
        Args:
            from_phase: Previous phase (None if starting)
            to_phase: New phase
            run_id: Run ID
            elapsed_sec: Elapsed time since run start
        """
        if self.log_events:
            if from_phase:
                logger.info(
                    f"[BS:GUARDS] Phase change: {from_phase.value} → {to_phase.value} "
                    f"(run={run_id}, elapsed={elapsed_sec}s)"
                )
            else:
                logger.info(
                    f"[BS:GUARDS] Phase started: {to_phase.value} "
                    f"(run={run_id}, elapsed={elapsed_sec}s)"
                )
        
        self.last_phase = to_phase
    
    async def on_metric_tick(
        self,
        metrics: Metrics,
        phase: Phase,
        run_id: str,
        elapsed_sec: int
    ) -> None:
        """
        Called every second with current metrics.
        
        Args:
            metrics: Current metrics
            phase: Current phase
            run_id: Run ID
            elapsed_sec: Elapsed time since run start
        """
        if not self.enabled:
            return
        
        # Check for guardrail violation (P95 threshold)
        if metrics.p95_ms and metrics.p95_ms > self.p95_threshold_ms:
            await self.on_guardrail_violation(
                metric_name="p95_ms",
                value=metrics.p95_ms,
                threshold=self.p95_threshold_ms,
                phase=phase,
                run_id=run_id
            )
    
    async def on_guardrail_violation(
        self,
        metric_name: str,
        value: float,
        threshold: float,
        phase: Phase,
        run_id: str
    ) -> None:
        """
        Called when a guardrail threshold is violated.
        
        Args:
            metric_name: Metric that violated (e.g., "p95_ms")
            value: Actual value
            threshold: Threshold value
            phase: Current phase
            run_id: Run ID
        """
        self.violation_count += 1
        
        if self.log_events:
            logger.warning(
                f"[BS:GUARDS] Guardrail violation #{self.violation_count}: "
                f"{metric_name}={value:.2f} > {threshold:.2f} "
                f"(phase={phase.value}, run={run_id})"
            )
        
        # Hook for external intervention (e.g., pause auto-tuner, send alert)
        # Default: no action
    
    async def on_watchdog_trip(
        self,
        reason: str,
        details: Dict[str, Any],
        phase: Phase,
        run_id: str
    ) -> bool:
        """
        Called when watchdog detects an anomaly.
        
        Args:
            reason: Trip reason ("no_progress", "p95_exceeded", "timeout")
            details: Additional details
            phase: Current phase
            run_id: Run ID
            
        Returns:
            True to abort run, False to continue
        """
        if self.log_events:
            logger.error(
                f"[BS:GUARDS] Watchdog trip: {reason} "
                f"(phase={phase.value}, run={run_id}, details={details})"
            )
        
        # Hook for external intervention (e.g., emergency stop, rollback)
        # Default: log but don't abort
        return False
    
    def check_progress(self, progress: int, current_time: int) -> bool:
        """
        Check if progress is advancing.
        
        Args:
            progress: Current progress (0-100)
            current_time: Current timestamp (Unix epoch)
            
        Returns:
            True if progress OK, False if stuck
        """
        # First call
        if self.last_progress_time == 0:
            self.last_progress = progress
            self.last_progress_time = current_time
            return True
        
        # Check if progress advanced
        if progress > self.last_progress:
            self.last_progress = progress
            self.last_progress_time = current_time
            return True
        
        # Check if stuck for too long
        stuck_duration = current_time - self.last_progress_time
        if stuck_duration > self.watchdog_no_progress_sec:
            return False
        
        return True


# Global guards instance
_global_guards: Optional[Guards] = None


def get_guards(enabled: bool = True) -> Guards:
    """
    Get or create global guards instance.
    
    Args:
        enabled: Enable guardrails
        
    Returns:
        Guards instance
    """
    global _global_guards
    
    if _global_guards is None:
        _global_guards = Guards(enabled=enabled)
    
    return _global_guards

