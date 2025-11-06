"""
Black Swan Async - Report Generator

Builds final JSON reports compatible with v2 frontend format.
Includes phase summaries, force override info, and guardrail events.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any
from .models import Report, PhaseReport, RunConfig, RunState, Metrics, RunMode
from .storage import get_storage

logger = logging.getLogger(__name__)


class Reporter:
    """
    Report generator for Black Swan test runs.
    
    Creates comprehensive reports with:
    - Configuration and mode details
    - Phase-by-phase metrics (warmup/baseline/trip/recovery)
    - Force override and hard cap information
    - Guardrail violations and watchdog events
    """
    
    def __init__(self):
        """Initialize reporter."""
        self.storage = get_storage()
    
    def build_report(
        self,
        state: RunState,
        config: RunConfig,
        phase_metrics: Dict[str, Metrics]
    ) -> Dict[str, Any]:
        """
        Build final report from run state and metrics.
        
        Args:
            state: Final run state
            config: Run configuration
            phase_metrics: Metrics for each phase
            
        Returns:
            Report dictionary (compatible with v2 format)
        """
        # Build phase reports
        warmup_report = self._build_phase_report(
            phase="warmup",
            metrics=phase_metrics.get("warmup", Metrics()),
            duration=config.warmup_duration,
            qps_target=config.warmup_qps
        )
        
        baseline_report = self._build_phase_report(
            phase="baseline",
            metrics=phase_metrics.get("baseline", Metrics()),
            duration=config.baseline_duration,
            qps_target=config.baseline_qps
        )
        
        trip_report = self._build_phase_report(
            phase="trip",
            metrics=phase_metrics.get("trip", Metrics()),
            duration=config.trip_duration,
            qps_target=config.trip_qps
        )
        
        recovery_report = self._build_phase_report(
            phase="recovery",
            metrics=phase_metrics.get("recovery", Metrics()),
            duration=config.recovery_duration,
            qps_target=config.recovery_qps
        )
        
        # Calculate totals
        total_duration = (
            config.warmup_duration +
            config.baseline_duration +
            config.trip_duration +
            config.recovery_duration
        )
        
        total_requests = sum(
            m.count for m in phase_metrics.values()
        )
        
        total_errors = sum(
            m.errors for m in phase_metrics.values()
        )
        
        # Get force override status
        force_info = self._get_force_override_info()
        
        # Build report
        report = {
            "run_id": state.run_id,
            "mode": state.mode.value if hasattr(state.mode, 'value') else state.mode,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            
            # Configuration
            "config": {
                "mode": config.mode.value if hasattr(config.mode, 'value') else config.mode,
                "warmup_duration": config.warmup_duration,
                "baseline_duration": config.baseline_duration,
                "trip_duration": config.trip_duration,
                "recovery_duration": config.recovery_duration,
                "warmup_qps": config.warmup_qps,
                "baseline_qps": config.baseline_qps,
                "trip_qps": config.trip_qps,
                "recovery_qps": config.recovery_qps,
                "concurrency": config.concurrency,
                "unique_queries": config.unique_queries,
                "bypass_cache": config.bypass_cache,
                "candidate_k": config.candidate_k,
                "rerank_top_k": config.rerank_top_k
            },
            
            # Phase reports (v2 format compatibility: Before/Trip/After)
            "Before": warmup_report,  # v2 compatibility
            "warmup": warmup_report,
            "baseline": baseline_report,
            "Trip": trip_report,  # v2 compatibility
            "trip": trip_report,
            "After": recovery_report,  # v2 compatibility
            "recovery": recovery_report,
            
            # Summary
            "summary": {
                "total_duration_sec": total_duration,
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": round(total_errors / total_requests, 4) if total_requests > 0 else 0.0,
                "phases_completed": len([p for p in phase_metrics.keys()]),
                "phases_expected": 4
            },
            
            # Force override info
            "force_override_enabled": force_info["enabled"],
            "force_params": force_info["params"],
            "hard_cap_enabled": force_info["hard_cap_enabled"],
            "hard_cap_limits": force_info["hard_cap_limits"],
            "precedence_chain": state.precedence_chain,
            
            # Guardrail events
            "guardrails": {
                "violations": state.guardrail_state.violations,
                "enabled": state.guardrail_state.enabled,
                "p95_threshold_ms": state.guardrail_state.p95_threshold_ms
            },
            
            # Watchdog events
            "watchdog": {
                "triggered": state.watchdog_state.triggered,
                "enabled": state.watchdog_state.enabled,
                "reason": state.watchdog_state.reason
            },
            
            # Timeline
            "progress_timeline": [
                "warmup", "baseline", "trip", "recovery", "complete"
            ],
            
            # Timing
            "started_at": state.started_at,
            "ended_at": state.ended_at,
            "duration_sec": (state.ended_at - state.started_at) if state.ended_at else 0
        }
        
        return report
    
    def _build_phase_report(
        self,
        phase: str,
        metrics: Metrics,
        duration: int,
        qps_target: int
    ) -> Dict[str, Any]:
        """
        Build report for a single phase.
        
        Args:
            phase: Phase name
            metrics: Phase metrics
            duration: Phase duration (seconds)
            qps_target: Target QPS
            
        Returns:
            Phase report dictionary
        """
        return {
            "phase": phase,
            "duration_sec": duration,
            "qps_target": qps_target,
            "qps_actual": metrics.qps,
            "samples": metrics.count,
            "errors": metrics.errors,
            "error_rate": metrics.error_rate,
            
            # Metrics (v2 compatibility)
            "window60s": {
                "p50_ms": metrics.p50_ms,
                "p95_ms": metrics.p95_ms,
                "p99_ms": metrics.p99_ms,
                "max_ms": metrics.max_ms,
                "tps": metrics.qps,
                "samples": metrics.count
            },
            
            # Direct metrics
            "metrics": {
                "count": metrics.count,
                "qps": metrics.qps,
                "p50_ms": metrics.p50_ms,
                "p95_ms": metrics.p95_ms,
                "p99_ms": metrics.p99_ms,
                "max_ms": metrics.max_ms,
                "error_rate": metrics.error_rate,
                "errors": metrics.errors
            }
        }
    
    def _get_force_override_info(self) -> Dict[str, Any]:
        """
        Get force override status.
        
        Returns:
            Force override info dictionary
        """
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent / "fiqa_api"))
            from force_override import get_force_override_status
            
            status = get_force_override_status()
            return {
                "enabled": status["force_override"],
                "params": status["active_params"],
                "hard_cap_enabled": status["hard_cap_enabled"],
                "hard_cap_limits": status["hard_cap_limits"]
            }
        
        except Exception as e:
            logger.warning(f"[BS:REPORTER] Failed to get force override status: {e}")
            return {
                "enabled": False,
                "params": {},
                "hard_cap_enabled": False,
                "hard_cap_limits": {}
            }
    
    async def save_report(self, report: Dict[str, Any]) -> bool:
        """
        Save report to Redis and optionally to file.
        
        Args:
            report: Report dictionary
            
        Returns:
            True if saved successfully
        """
        # Save to Redis
        saved = self.storage.save_report(report)
        
        if saved:
            logger.info(f"[BS:REPORTER] Report saved to Redis: run_id={report['run_id']}")
        else:
            logger.warning(f"[BS:REPORTER] Failed to save report to Redis (degraded mode)")
        
        return saved


# Global reporter instance
_global_reporter: Reporter = None


def get_reporter() -> Reporter:
    """
    Get or create global reporter instance.
    
    Returns:
        Reporter instance
    """
    global _global_reporter
    
    if _global_reporter is None:
        _global_reporter = Reporter()
    
    return _global_reporter

