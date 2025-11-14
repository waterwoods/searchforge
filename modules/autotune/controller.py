"""
SLA-aware autotuner controller with closed-loop control.
"""
from typing import Dict, Any, Optional, Tuple, Union
import logging
import collections
from .state import TuningState
from .policies import get_policy, TuningPolicy

logger = logging.getLogger(__name__)


class AutoTuner:
    """SLA-aware autotuner with closed-loop control."""
    
    def __init__(self, engine: str, policy: Union[str, TuningPolicy] = "Balanced",
                 hnsw_ef_range: tuple = (4, 256), rerank_range: tuple = (100, 1200), 
                 ema_alpha: float = 0.2, target_p95_ms: float = 30, target_recall: float = 0.95,
                 latency_hi: float = 1.2, latency_lo: float = 0.9, 
                 recall_margin: float = 0.02, min_batches: int = 160,
                 guard_recall_margin: float = 0.01, guard_recall_batches: int = 8,
                 cooldown_decrease_batches: int = 10,
                 step_up: int = 32, step_down: int = 16,
                 state: Optional[TuningState] = None):
        """
        Initialize autotuner.
        
        Args:
            engine: Search engine type ('hnsw' - HNSW is the primary supported type)
            policy: Tuning policy ('LatencyFirst', 'RecallFirst', 'Balanced')
            hnsw_ef_range: Valid range for HNSW ef parameter (equivalent to ef_search)
            rerank_range: Valid range for rerank_k parameter
            ema_alpha: Exponential moving average alpha
            target_p95_ms: Target p95 latency in milliseconds
            target_recall: Target recall@10
            latency_hi: High latency threshold multiplier
            latency_lo: Low latency threshold multiplier
            recall_margin: Recall margin for hysteresis
            min_batches: Minimum batches before early stop
            guard_recall_margin: Margin above target for decrease guard
            guard_recall_batches: Number of batches to check for guard
            cooldown_decrease_batches: Cooldown before allowing decreases
            step_up: Step size for increasing hnsw_ef parameter
            step_down: Step size for decreasing hnsw_ef parameter
        """
        engine_name = engine.lower()
        if engine_name != "hnsw":
            logger.warning(f"AutoTuner only supports HNSW; forcing engine to 'hnsw' (was '{engine}')")
            engine_name = "hnsw"
        self.engine = engine_name
        
        # Engine-aware default policy
        if isinstance(policy, TuningPolicy):
            self.policy = policy
        else:
            self.policy = get_policy(policy)
        self.policy_name = getattr(self.policy, "name", str(policy))
        self.target_p95_ms = target_p95_ms
        self.target_recall = target_recall
        
        # Step sizes for parameter adjustment
        self.step_up = step_up
        self.step_down = step_down
        
        # Hysteresis thresholds
        self.latency_hi = latency_hi
        self.latency_lo = latency_lo
        self.recall_margin = recall_margin
        
        # Decrease guard parameters
        self.guard_recall_margin = guard_recall_margin
        self.guard_recall_batches = guard_recall_batches
        self.cooldown_decrease_batches = cooldown_decrease_batches
        
        # Minimum batches before early stop
        self.min_batches = min_batches
        
        # Initialize state
        provided_state = state is not None
        self.state = state or TuningState(
            hnsw_ef_range=hnsw_ef_range,
            rerank_range=rerank_range,
            ema_alpha=ema_alpha
        )
        self.state.hnsw_ef_range = hnsw_ef_range
        self.state.rerank_range = rerank_range
        self.state.ema_alpha = ema_alpha
        
        # Set initial parameters based on engine when state not provided
        if not provided_state:
            self.state.ef_search = max(128, 64)  # Enforce quality floor for HNSW
            # Ensure search ceiling for better recall
            if self.state.hnsw_ef_range[1] < 256:
                self.state.hnsw_ef_range = (self.state.hnsw_ef_range[0], 256)
            
            self.state.rerank_k = max(1000, 400)  # Enforce quality floor; was 900
            
            # Optional: For HNSW, if rerank floor < 500, set rerank_k to at least 500
            if self.state.rerank_k < 500:
                self.state.rerank_k = max(self.state.rerank_k, 500)
        
        # Initialize decrease guard counters
        self.state.batches_since_decrease = 0
        self.state.recent_recall_queue = collections.deque(maxlen=self.guard_recall_batches)
        
        # HNSW rescue mechanism for recall dips
        self.rescue_window = 3
        self.rescue_ef = 16  # HNSW equivalent of rescue_nprobe
        self.rescue_rerank = 200
        
        logger.info(f"Initialized {self.engine.upper()} autotuner with {self.policy_name} policy")
        logger.info(f"Targets: p95={target_p95_ms}ms, recall={target_recall}")
        logger.info(f"Hysteresis: latency_hi={latency_hi}, latency_lo={latency_lo}, recall_margin={recall_margin}")
        logger.info(f"Decrease guard: margin={guard_recall_margin}, batches={guard_recall_batches}, cooldown={cooldown_decrease_batches}")
        logger.info(f"Min batches before early stop: {min_batches}")

    def _step(self, val: int, frac: float, min_step: int = 1) -> int:
        """Helper function to ensure minimum step size."""
        return max(min_step, int(max(1, val) * frac))

    def suggest(self, last_metrics: Dict[str, float]) -> Dict[str, int]:
        """
        Suggest next parameters based on current metrics.
        
        Args:
            last_metrics: Dictionary with keys 'p95_ms', 'recall_at_10', 'coverage'
            
        Returns:
            Dictionary with next parameters
        """
        # Update state with new metrics (raw + EMA)
        self.state.update_metrics(
            p95_ms=last_metrics.get("p95_ms", 0.0),
            recall_at_10=last_metrics.get("recall_at_10", 0.0),
            coverage=last_metrics.get("coverage", 1.0)
        )
        
        # Update decrease guard tracking
        self.state.recent_recall_queue.append(last_metrics.get("recall_at_10", 0.0))
        
        # Check safety limits first
        safety_checks = self.state.check_safety_limits(self.target_p95_ms, self.target_recall)
        
        if not safety_checks["coverage_ok"]:
            logger.error(f"Coverage too low: {self.state.coverage:.3f} < 0.98")
            raise RuntimeError("Coverage below safety threshold - check data integrity")
        
        if safety_checks["p95_spike"]:
            logger.warning("P95 latency spike detected - entering emergency mode")
            self.state.set_emergency_mode(True)
            return self._emergency_adjustment()
        
        # Get smoothed metrics for decision making
        smoothed_metrics = self.state.get_smoothed_metrics()
        
        # Track last-batch recall and detect any recent dip
        if not hasattr(self.state, "recent_recalls"): 
            self.state.recent_recalls = collections.deque(maxlen=self.rescue_window)
        self.state.recent_recalls.append(self.state.recall_at_10)

        recent_dip = (len(self.state.recent_recalls) == self.rescue_window and 
                      min(self.state.recent_recalls) < self.target_recall)

        if recent_dip and self.engine == "hnsw":
            cp = self.state.get_current_params()
            rescue = {
              "ef_search": self._clamp(cp["ef_search"] + self.rescue_ef, *self.state.hnsw_ef_range),
              "rerank_k": self._clamp(cp["rerank_k"] + self.rescue_rerank, *self.state.rerank_range)
            }
            self.state.update_params(**rescue)
            logger.info(f"HNSW rescue bump applied: {rescue}")
            # Skip normal decreases this batch; continue with rest logic
        
        # Calculate step sizes based on policy
        step_sizes = self.policy.calculate_step_size(smoothed_metrics, {
            "p95_ms": self.target_p95_ms,
            "recall": self.target_recall
        })
        
        # Calculate parameter adjustments
        new_params = self._calculate_parameter_adjustments(step_sizes, smoothed_metrics)
        
        # Clamp parameters to configured ranges
        new_params["ef_search"] = self._clamp(
            new_params.get("ef_search", self.state.ef_search),
            *self.state.hnsw_ef_range
        )
        new_params["rerank_k"] = self._clamp(
            new_params.get("rerank_k", self.state.rerank_k),
            *self.state.rerank_range
        )
        
        # Apply decrease guard to prevent premature decreases
        current_params = self.state.get_current_params()
        new_params = self._apply_decrease_guard(new_params, current_params)
        
        # Apply adjustments to state
        self.state.update_params(**new_params)
        
        # Check if we should exit emergency mode
        if (self.state.is_emergency_mode and 
            smoothed_metrics["p95_ms"] < self.target_p95_ms * 1.5):
            logger.info("Exiting emergency mode")
            self.state.set_emergency_mode(False)
            self.state.reset_failures()
        
        logger.info(f"Suggested params: {new_params}")
        return new_params
    
    def _clamp(self, value: int, lower: int, upper: int) -> int:
        return max(lower, min(upper, int(value)))
    
    def _calculate_parameter_adjustments(self, step_sizes: Dict[str, float], 
                                      metrics: Dict[str, float]) -> Dict[str, int]:
        """Calculate new parameter values based on step sizes and current performance."""
        current_params = self.state.get_current_params()
        new_params = {}
        
        # Calculate target metrics
        target_p95 = self.target_p95_ms
        target_recall = self.target_recall
        
        current_p95 = metrics["p95_ms"]
        current_recall = metrics["recall_at_10"]
        
        # Determine adjustment direction and magnitude
        if self.engine == "hnsw":
            # Adjust ef_search based on recall vs latency trade-off using fixed step sizes
            if current_recall < target_recall - self.recall_margin:
                # Recall too low - increase ef_search
                new_params["ef_search"] = min(self.state.hnsw_ef_range[1], 
                                            current_params["ef_search"] + self.step_up)
            elif current_p95 > target_p95 * self.latency_hi:
                # Latency too high - decrease ef_search
                new_params["ef_search"] = max(self.state.hnsw_ef_range[0], 
                                            current_params["ef_search"] - self.step_down)
            else:
                new_params["ef_search"] = current_params["ef_search"]
        
        
        # Adjust rerank_k based on latency
        if current_p95 > target_p95:
            # Latency too high - decrease rerank_k
            rerank_step = self._step(current_params["rerank_k"], step_sizes["rerank_k"])
            new_params["rerank_k"] = max(100, current_params["rerank_k"] - rerank_step)
        elif current_p95 < target_p95 * self.latency_lo and current_recall < target_recall - self.recall_margin:
            # Latency is good, can afford to improve recall
            rerank_step = self._step(current_params["rerank_k"], step_sizes["rerank_k"] * 0.5)
            new_params["rerank_k"] = min(1200, current_params["rerank_k"] + rerank_step)
        else:
            new_params["rerank_k"] = current_params["rerank_k"]
        
        return new_params
    
    def _apply_decrease_guard(self, new_params: Dict[str, int], current_params: Dict[str, int]) -> Dict[str, int]:
        """Apply decrease guard to prevent premature parameter decreases."""
        decrease_attempted = False

        if self.engine == "hnsw" and "ef_search" in new_params:
            if new_params["ef_search"] < current_params["ef_search"]:
                decrease_attempted = True

        if "rerank_k" in new_params and new_params["rerank_k"] < current_params["rerank_k"]:
            decrease_attempted = True

        if decrease_attempted:
            if self._decrease_allowed():
                logger.info("Decrease guard conditions met - allowing decrease")
                self.state.batches_since_decrease = 0
            else:
                logger.info(
                    "Decrease blocked by guard: recall_queue_len=%s, min_recall=%s, batches_since_decrease=%s",
                    len(self.state.recent_recall_queue),
                    min(self.state.recent_recall_queue) if self.state.recent_recall_queue else "N/A",
                    self.state.batches_since_decrease,
                )
                new_params = current_params.copy()
                # Do not change cooldown counter when guard blocks decrease
        else:
            self.state.batches_since_decrease = min(
                self.state.batches_since_decrease + 1, self.cooldown_decrease_batches
            )

        return new_params

    def _decrease_allowed(self) -> bool:
        queue = getattr(self.state, "recent_recall_queue", [])
        full = len(queue) == self.guard_recall_batches
        recall_ok = full and min(queue) >= (self.target_recall + self.guard_recall_margin)
        cooldown_ok = self.state.batches_since_decrease >= self.cooldown_decrease_batches
        return full and recall_ok and cooldown_ok
    
    def _emergency_adjustment(self) -> Dict[str, int]:
        """Apply emergency parameter adjustments."""
        emergency_adjustments = self.policy.get_emergency_adjustments()
        current_params = self.state.get_current_params()
        
        new_params = {}

        if self.engine == "hnsw":
            new_params["ef_search"] = self._clamp(
                current_params["ef_search"] * emergency_adjustments["ef_search"],
                *self.state.hnsw_ef_range
            )
        
        new_params["rerank_k"] = self._clamp(
            current_params["rerank_k"] * emergency_adjustments["rerank_k"],
            *self.state.rerank_range
        )
        
        # Apply to state
        self.state.update_params(**new_params)
        
        logger.warning(f"Emergency adjustment applied: {new_params}")
        return new_params
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current autotuner state."""
        return {
            "engine": self.engine,
            "policy": self.policy_name,
            "targets": {
                "p95_ms": self.target_p95_ms,
                "recall": self.target_recall
            },
            "current_params": self.state.get_current_params(),
            "current_metrics": {
                "p95_ms": self.state.p95_ms,
                "recall_at_10": self.state.recall_at_10,
                "coverage": self.state.coverage
            },
            "smoothed_metrics": self.state.get_smoothed_metrics(),
            "safety_checks": self.state.check_safety_limits(self.target_p95_ms, self.target_recall),
            "convergence": self.state.get_convergence_status()
        }
    
    def reset(self):
        """Reset autotuner state."""
        self.state = TuningState(
            hnsw_ef_range=self.state.hnsw_ef_range,
            rerank_range=self.state.rerank_range,
            ema_alpha=self.state.ema_alpha
        )
        
        # Reset to initial parameters
        if self.engine == "hnsw":
            self.state.ef_search = 156   # Stabilize tail batches; was 144
        
        self.state.rerank_k = max(1000, 400)  # Enforce quality floor; was 900
        
        # Optional: For HNSW, if rerank floor < 500, set rerank_k to at least 500
        if self.engine == "hnsw" and self.state.rerank_k < 500:
            self.state.rerank_k = max(self.state.rerank_k, 500)
        
        # Reset decrease guard counters
        self.state.batches_since_decrease = 0
        self.state.recent_recall_queue = collections.deque(maxlen=self.guard_recall_batches)
        
        # Reset rescue mechanism
        if hasattr(self.state, "recent_recalls"):
            self.state.recent_recalls.clear()
        else:
            self.state.recent_recalls = collections.deque(maxlen=self.rescue_window)
        
        self.state.set_emergency_mode(False)
        
        logger.info("Reset autotuner to initial state")
    
    def should_stop_tuning(self) -> bool:
        """Check if tuning should stop."""
        # Minimum batches guard
        if not self.state.recent_metrics or len(self.state.recent_metrics) < self.min_batches:
            return False
        
        convergence = self.state.get_convergence_status()
        
        # Stop if converged AND targets are met
        if convergence["converged"]:
            # Check if targets are actually met
            recent_metrics = self.state.recent_metrics[-5:] if self.state.recent_metrics else []
            if len(recent_metrics) >= 5:
                p95_ok = all(m["p95_ms"] <= self.target_p95_ms for m in recent_metrics)
                recall_ok = all(m["recall_at_10"] >= self.target_recall for m in recent_metrics)
                
                if p95_ok and recall_ok:
                    logger.info("Tuning converged and targets met - stopping")
                    return True
                else:
                    logger.info("Tuning converged but targets not met - continuing")
                    return False
        
        # Stop if targets are met consistently for more batches
        recent_metrics = self.state.recent_metrics[-15:] if self.state.recent_metrics else []
        if len(recent_metrics) >= 15:
            p95_ok = all(m["p95_ms"] <= self.target_p95_ms for m in recent_metrics)
            recall_ok = all(m["recall_at_10"] >= self.target_recall for m in recent_metrics)
            
            if p95_ok and recall_ok:
                logger.info("Targets consistently met for 15+ batches - stopping")
                return True
        
        return False 