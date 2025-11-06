"""
Base Actuator interface for applying control actions.

Actuators take policy decisions and apply them to system parameters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class Actuator(ABC):
    """Base class for control actuators."""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.current_value = None
    
    @abstractmethod
    async def apply(self, adjustment: float, reason: str) -> Dict[str, Any]:
        """
        Apply adjustment to the controlled parameter.
        
        Args:
            adjustment: Multiplier to apply (e.g., 0.7 for 70%, 1.1 for 110%)
            reason: Reason for adjustment
        
        Returns:
            Dict with ok, old_value, new_value, applied
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get actuator status."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "current_value": self.current_value
        }

