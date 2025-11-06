"""
AIMD (Additive Increase, Multiplicative Decrease) control policy.

Primary policy for control flow shaping.
"""

from typing import Dict, Any
import time
from .base import Policy


class AIMDPolicy(Policy):
    """
    AIMD control policy.
    
    - Additive increase when healthy (signal < threshold)
    - Multiplicative decrease when overloaded (signal > threshold)
    """
    
    def __init__(
        self,
        threshold: float = 0.8,
        increase_step: float = 0.05,  # +5% per interval
        decrease_factor: float = 0.7,  # 70% of current
        cooldown_secs: int = 30
    ):
        super().__init__("aimd")
        self.threshold = threshold
        self.increase_step = increase_step
        self.decrease_factor = decrease_factor
        self.cooldown_secs = cooldown_secs
        self.last_decrease_time = 0
        self.last_decision: Dict[str, Any] = {}
    
    async def decide(self, signals: Dict[str, float]) -> Dict[str, Any]:
        """
        Make AIMD control decision.
        
        Args:
            signals: Dict of signal values
        
        Returns:
            Dict with action ("increase", "decrease", "hold") and adjustment
        """
        now = time.time()
        
        # Calculate combined signal (max of all signals)
        if not signals:
            return {
                "action": "hold",
                "adjustment": 1.0,
                "reason": "no_signals",
                "policy": self.name
            }
        
        max_signal = max(signals.values())
        signal_name = [k for k, v in signals.items() if v == max_signal][0]
        
        # Check if in cooldown
        in_cooldown = (now - self.last_decrease_time) < self.cooldown_secs
        
        # Make decision
        if max_signal > self.threshold:
            # Overloaded: multiplicative decrease
            if not in_cooldown:
                self.last_decrease_time = now
                decision = {
                    "action": "decrease",
                    "adjustment": self.decrease_factor,
                    "reason": f"{signal_name}={max_signal:.3f} > {self.threshold}",
                    "policy": self.name,
                    "signal": signal_name,
                    "signal_value": max_signal
                }
            else:
                # In cooldown, hold
                decision = {
                    "action": "hold",
                    "adjustment": 1.0,
                    "reason": "cooldown",
                    "policy": self.name,
                    "cooldown_remaining": self.cooldown_secs - (now - self.last_decrease_time)
                }
        else:
            # Healthy: additive increase
            decision = {
                "action": "increase",
                "adjustment": 1.0 + self.increase_step,
                "reason": f"{signal_name}={max_signal:.3f} < {self.threshold}",
                "policy": self.name,
                "signal": signal_name,
                "signal_value": max_signal
            }
        
        self.last_decision = decision
        return decision
    
    def get_status(self) -> Dict[str, Any]:
        """Get extended status with config."""
        status = super().get_status()
        status.update({
            "threshold": self.threshold,
            "increase_step": self.increase_step,
            "decrease_factor": self.decrease_factor,
            "cooldown_secs": self.cooldown_secs,
            "last_decision": self.last_decision
        })
        return status

