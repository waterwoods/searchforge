"""
Batch size actuator for control flow shaping.

Adjusts batch processing size with hard caps and gray rollout.
"""

import random
from typing import Dict, Any
from .base import Actuator


class BatchSizeActuator(Actuator):
    """
    Batch size control actuator.
    
    Adjusts batch processing size with:
    - Hard caps (min/max limits)
    - 10% gray rollout (only apply to 10% of traffic)
    """
    
    def __init__(
        self,
        initial_value: int = 32,
        min_value: int = 4,
        max_value: int = 128,
        gray_rollout_pct: float = 0.10
    ):
        super().__init__("batch_size")
        self.current_value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        self.gray_rollout_pct = gray_rollout_pct
        self.adjustment_count = 0
    
    async def apply(self, adjustment: float, reason: str) -> Dict[str, Any]:
        """
        Apply batch size adjustment.
        
        Args:
            adjustment: Multiplier (e.g., 0.7 for decrease, 1.1 for increase)
            reason: Reason for adjustment
        
        Returns:
            Dict with application result
        """
        if not self.enabled:
            return {
                "ok": False,
                "error": "actuator_disabled",
                "actuator": self.name
            }
        
        old_value = self.current_value
        
        # Calculate new value
        new_value = int(self.current_value * adjustment)
        
        # Apply hard caps
        new_value = max(self.min_value, min(self.max_value, new_value))
        
        # Gray rollout: only apply to X% of requests
        gray_applied = random.random() < self.gray_rollout_pct
        
        if gray_applied:
            self.current_value = new_value
            self.adjustment_count += 1
            applied = True
        else:
            applied = False
        
        return {
            "ok": True,
            "actuator": self.name,
            "old_value": old_value,
            "new_value": new_value,
            "applied": applied,
            "gray_rollout": gray_applied,
            "reason": reason,
            "adjustment_count": self.adjustment_count
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get extended status with config."""
        status = super().get_status()
        status.update({
            "min_value": self.min_value,
            "max_value": self.max_value,
            "gray_rollout_pct": self.gray_rollout_pct,
            "adjustment_count": self.adjustment_count
        })
        return status

