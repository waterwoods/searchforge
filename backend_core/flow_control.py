"""
Flow Control Module - Clean Backend Core
==========================================
Implements AIMD and PID-lite controllers with no external dependencies.

This module provides standalone flow control algorithms that can be tested
independently and integrated into any search backend.

Controllers:
- FlowController: Main interface for flow control decisions
- AIMDController: Additive Increase, Multiplicative Decrease (TCP-inspired)
- PIDController: PID-lite for smooth adjustments

Usage:
    controller = FlowController(policy="aimd")
    controller.update_metrics(p95_ms=150, qps=100, err_rate=0.01)
    recommendation = controller.recommend()
    # => {"concurrency": 20, "batch_size": 10, "confidence": 0.85}
"""

from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass
import time
import math


@dataclass
class FlowMetrics:
    """Current flow metrics."""
    p95_ms: float
    qps: float
    err_rate: float = 0.0
    queue_depth: int = 0
    timestamp: float = 0.0


@dataclass
class FlowRecommendation:
    """Flow control recommendation."""
    concurrency: int
    batch_size: int
    confidence: float
    action: str  # "increase", "decrease", "hold"
    reason: str


class AIMDController:
    """
    AIMD (Additive Increase, Multiplicative Decrease) Controller.
    
    Inspired by TCP congestion control:
    - Additive increase when healthy (p95 < target)
    - Multiplicative decrease when overloaded (p95 > target)
    
    Parameters:
        target_p95_ms: Target P95 latency
        threshold_factor: Trigger decrease when p95 > target * threshold_factor
        increase_step: Additive increase step (default 0.05 = +5%)
        decrease_factor: Multiplicative decrease factor (default 0.7 = 70%)
        cooldown_sec: Cooldown period after decrease
    """
    
    def __init__(
        self,
        target_p95_ms: float = 100.0,
        threshold_factor: float = 1.2,
        increase_step: float = 0.05,
        decrease_factor: float = 0.7,
        cooldown_sec: int = 30
    ):
        self.target_p95_ms = target_p95_ms
        self.threshold_factor = threshold_factor
        self.increase_step = increase_step
        self.decrease_factor = decrease_factor
        self.cooldown_sec = cooldown_sec
        
        # State
        self.current_multiplier = 1.0
        self.last_decrease_time = 0.0
        self.decisions_count = 0
    
    def update(self, metrics: FlowMetrics) -> FlowRecommendation:
        """
        Update controller with new metrics and get recommendation.
        
        Args:
            metrics: Current flow metrics
            
        Returns:
            FlowRecommendation with action and parameters
        """
        self.decisions_count += 1
        now = time.time()
        
        # Check if we're in cooldown
        in_cooldown = (now - self.last_decrease_time) < self.cooldown_sec
        
        # Decision logic
        threshold = self.target_p95_ms * self.threshold_factor
        
        if metrics.p95_ms > threshold:
            # Overloaded: multiplicative decrease
            if not in_cooldown:
                self.last_decrease_time = now
                self.current_multiplier *= self.decrease_factor
                action = "decrease"
                reason = f"p95={metrics.p95_ms:.1f}ms > {threshold:.1f}ms"
                confidence = 0.9
            else:
                # In cooldown, hold
                action = "hold"
                cooldown_remaining = self.cooldown_sec - (now - self.last_decrease_time)
                reason = f"cooldown ({cooldown_remaining:.0f}s remaining)"
                confidence = 0.5
        
        elif metrics.p95_ms < self.target_p95_ms * 0.8:
            # Healthy: additive increase
            self.current_multiplier *= (1.0 + self.increase_step)
            action = "increase"
            reason = f"p95={metrics.p95_ms:.1f}ms < {self.target_p95_ms:.1f}ms"
            confidence = 0.85
        
        else:
            # In acceptable range, hold
            action = "hold"
            reason = f"p95={metrics.p95_ms:.1f}ms in acceptable range"
            confidence = 0.7
        
        # Clamp multiplier
        self.current_multiplier = max(0.1, min(2.0, self.current_multiplier))
        
        # Calculate concrete parameters
        base_concurrency = 20
        base_batch_size = 10
        
        concurrency = max(1, int(base_concurrency * self.current_multiplier))
        batch_size = max(1, int(base_batch_size * self.current_multiplier))
        
        return FlowRecommendation(
            concurrency=concurrency,
            batch_size=batch_size,
            confidence=confidence,
            action=action,
            reason=reason
        )
    
    def reset(self):
        """Reset controller state."""
        self.current_multiplier = 1.0
        self.last_decrease_time = 0.0
        self.decisions_count = 0


class PIDController:
    """
    PID (Proportional-Integral-Derivative) Controller (lite version).
    
    Uses classic PID loop for smooth, stable adjustments.
    
    Parameters:
        target_p95_ms: Target P95 latency
        kp: Proportional gain (response to current error)
        ki: Integral gain (response to accumulated error)
        kd: Derivative gain (response to error rate of change)
        max_adjustment: Maximum adjustment per step (default 0.3 = ±30%)
    """
    
    def __init__(
        self,
        target_p95_ms: float = 100.0,
        kp: float = 0.5,
        ki: float = 0.1,
        kd: float = 0.2,
        max_adjustment: float = 0.3
    ):
        self.target_p95_ms = target_p95_ms
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.max_adjustment = max_adjustment
        
        # PID state
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = 0.0
        self.current_multiplier = 1.0
        self.decisions_count = 0
    
    def update(self, metrics: FlowMetrics) -> FlowRecommendation:
        """
        Update controller with new metrics and get recommendation.
        
        Args:
            metrics: Current flow metrics
            
        Returns:
            FlowRecommendation with action and parameters
        """
        self.decisions_count += 1
        now = time.time()
        
        # Calculate error (negative when over target)
        error = (self.target_p95_ms - metrics.p95_ms) / self.target_p95_ms
        
        # Calculate dt
        if self.last_time == 0:
            dt = 1.0
        else:
            dt = max(now - self.last_time, 0.1)
        
        # Update integral with anti-windup
        self.integral += error * dt
        self.integral = max(-2.0, min(2.0, self.integral))  # Clamp integral
        
        # Calculate derivative
        derivative = (error - self.last_error) / dt if dt > 0 else 0.0
        
        # PID output
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        
        # Clamp output
        output = max(-self.max_adjustment, min(self.max_adjustment, output))
        
        # Update multiplier
        self.current_multiplier *= (1.0 + output)
        self.current_multiplier = max(0.1, min(2.0, self.current_multiplier))
        
        # Update state
        self.last_error = error
        self.last_time = now
        
        # Determine action
        if output > 0.02:
            action = "increase"
            reason = f"PID: error={error:.3f}, output=+{output:.3f}"
            confidence = 0.85
        elif output < -0.02:
            action = "decrease"
            reason = f"PID: error={error:.3f}, output={output:.3f}"
            confidence = 0.9
        else:
            action = "hold"
            reason = f"PID: error={error:.3f}, stable"
            confidence = 0.7
        
        # Calculate concrete parameters
        base_concurrency = 20
        base_batch_size = 10
        
        concurrency = max(1, int(base_concurrency * self.current_multiplier))
        batch_size = max(1, int(base_batch_size * self.current_multiplier))
        
        return FlowRecommendation(
            concurrency=concurrency,
            batch_size=batch_size,
            confidence=confidence,
            action=action,
            reason=reason
        )
    
    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = 0.0
        self.current_multiplier = 1.0
        self.decisions_count = 0


class FlowController:
    """
    Main flow controller interface.
    
    Provides unified interface for different control policies.
    
    Usage:
        controller = FlowController(policy="aimd")
        controller.update_metrics(p95_ms=150, qps=100, err_rate=0.01)
        recommendation = controller.recommend()
    """
    
    def __init__(
        self,
        policy: Literal["aimd", "pid"] = "aimd",
        target_p95_ms: float = 100.0
    ):
        """
        Initialize flow controller.
        
        Args:
            policy: Control policy ("aimd" or "pid")
            target_p95_ms: Target P95 latency in milliseconds
        """
        self.policy = policy
        self.target_p95_ms = target_p95_ms
        
        # Initialize controller
        if policy == "aimd":
            self.controller = AIMDController(target_p95_ms=target_p95_ms)
        elif policy == "pid":
            self.controller = PIDController(target_p95_ms=target_p95_ms)
        else:
            raise ValueError(f"Unknown policy: {policy}")
        
        # Metrics history
        self.metrics_history: list[FlowMetrics] = []
        self.max_history = 100
        
        # Latest recommendation
        self.last_recommendation: Optional[FlowRecommendation] = None
    
    def update_metrics(self, p95_ms: float, qps: float, err_rate: float = 0.0, queue_depth: int = 0):
        """
        Update controller with new metrics.
        
        Args:
            p95_ms: P95 latency in milliseconds
            qps: Queries per second
            err_rate: Error rate (0.0 to 1.0)
            queue_depth: Current queue depth
        """
        metrics = FlowMetrics(
            p95_ms=p95_ms,
            qps=qps,
            err_rate=err_rate,
            queue_depth=queue_depth,
            timestamp=time.time()
        )
        
        # Update history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        # Get recommendation
        self.last_recommendation = self.controller.update(metrics)
    
    def recommend(self) -> Dict[str, Any]:
        """
        Get current recommendation.
        
        Returns:
            Dict with concurrency, batch_size, and metadata
        """
        if self.last_recommendation is None:
            # No metrics yet, return defaults
            return {
                "concurrency": 20,
                "batch_size": 10,
                "confidence": 0.0,
                "action": "hold",
                "reason": "no_metrics_yet"
            }
        
        rec = self.last_recommendation
        return {
            "concurrency": rec.concurrency,
            "batch_size": rec.batch_size,
            "confidence": rec.confidence,
            "action": rec.action,
            "reason": rec.reason,
            "policy": self.policy
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get controller status."""
        return {
            "policy": self.policy,
            "target_p95_ms": self.target_p95_ms,
            "decisions_count": self.controller.decisions_count,
            "metrics_count": len(self.metrics_history),
            "last_recommendation": self.recommend() if self.last_recommendation else None
        }
    
    def reset(self):
        """Reset controller state."""
        self.controller.reset()
        self.metrics_history.clear()
        self.last_recommendation = None


# ============================================================================
# Quick self-test
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("FLOW CONTROL MODULE - SELF TEST")
    print("=" * 70)
    print()
    
    # Test AIMD controller
    print("1. AIMD Controller Test")
    print("-" * 70)
    aimd = FlowController(policy="aimd", target_p95_ms=100.0)
    
    test_scenarios = [
        (50, 100, 0.0, "Low latency (healthy)"),
        (120, 95, 0.0, "High latency (overloaded)"),
        (90, 100, 0.0, "Normal latency"),
    ]
    
    for p95, qps, err_rate, desc in test_scenarios:
        aimd.update_metrics(p95_ms=p95, qps=qps, err_rate=err_rate)
        rec = aimd.recommend()
        print(f"  {desc}: p95={p95}ms")
        print(f"    → action={rec['action']}, concurrency={rec['concurrency']}, "
              f"batch_size={rec['batch_size']}")
        print(f"    → reason: {rec['reason']}")
        print()
    
    # Test PID controller
    print("2. PID Controller Test")
    print("-" * 70)
    pid = FlowController(policy="pid", target_p95_ms=100.0)
    
    for p95, qps, err_rate, desc in test_scenarios:
        pid.update_metrics(p95_ms=p95, qps=qps, err_rate=err_rate)
        rec = pid.recommend()
        print(f"  {desc}: p95={p95}ms")
        print(f"    → action={rec['action']}, concurrency={rec['concurrency']}, "
              f"batch_size={rec['batch_size']}")
        print(f"    → reason: {rec['reason']}")
        print()
    
    print("=" * 70)
    print("✓ Self-test passed")
    print("=" * 70)

