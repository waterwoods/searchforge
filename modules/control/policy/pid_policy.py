"""
PID (Proportional-Integral-Derivative) control policy.

Optional policy behind feature flag (PID-lite implementation).
"""

from typing import Dict, Any
import time
from .base import Policy


class PIDPolicy(Policy):
    """
    PID control policy (lite version).
    
    Uses PID loop to adjust system parameters smoothly.
    """
    
    def __init__(
        self,
        target: float = 0.5,
        kp: float = 0.5,  # Proportional gain
        ki: float = 0.1,  # Integral gain
        kd: float = 0.2,  # Derivative gain
        max_adjustment: float = 0.3  # Max +/- 30% per step
    ):
        super().__init__("pid")
        self.target = target
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.max_adjustment = max_adjustment
        
        # PID state
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = 0.0
        self.last_decision: Dict[str, Any] = {}
    
    async def decide(self, signals: Dict[str, float]) -> Dict[str, Any]:
        """
        Make PID control decision.
        
        Args:
            signals: Dict of signal values
        
        Returns:
            Dict with action and adjustment
        """
        now = time.time()
        
        # Calculate combined signal (average of all signals)
        if not signals:
            return {
                "action": "hold",
                "adjustment": 1.0,
                "reason": "no_signals",
                "policy": self.name
            }
        
        current_value = sum(signals.values()) / len(signals)
        
        # Calculate error
        error = self.target - current_value
        
        # Calculate dt
        if self.last_time == 0:
            dt = 1.0
        else:
            dt = max(now - self.last_time, 0.1)
        
        # Update integral
        self.integral += error * dt
        
        # Calculate derivative
        derivative = (error - self.last_error) / dt if dt > 0 else 0.0
        
        # PID output
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        
        # Clamp output
        output = max(-self.max_adjustment, min(self.max_adjustment, output))
        
        # Calculate adjustment (1.0 + output)
        adjustment = 1.0 + output
        
        # Update state
        self.last_error = error
        self.last_time = now
        
        # Determine action
        if output > 0.01:
            action = "increase"
        elif output < -0.01:
            action = "decrease"
        else:
            action = "hold"
        
        decision = {
            "action": action,
            "adjustment": adjustment,
            "reason": f"error={error:.3f}, output={output:.3f}",
            "policy": self.name,
            "current_value": current_value,
            "target": self.target,
            "pid_terms": {
                "p": self.kp * error,
                "i": self.ki * self.integral,
                "d": self.kd * derivative
            }
        }
        
        self.last_decision = decision
        return decision
    
    def reset(self):
        """Reset PID state."""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """Get extended status with config."""
        status = super().get_status()
        status.update({
            "target": self.target,
            "kp": self.kp,
            "ki": self.ki,
            "kd": self.kd,
            "max_adjustment": self.max_adjustment,
            "integral": self.integral,
            "last_error": self.last_error,
            "last_decision": self.last_decision
        })
        return status

