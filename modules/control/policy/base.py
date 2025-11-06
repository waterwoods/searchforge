"""
Base Policy interface for control decisions.

Policies take signals and output control actions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class Policy(ABC):
    """Base class for control policies."""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    @abstractmethod
    async def decide(self, signals: Dict[str, float]) -> Dict[str, Any]:
        """
        Make control decision based on signals.
        
        Args:
            signals: Dict of signal_name -> value
        
        Returns:
            Dict with action and metadata
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get policy status."""
        return {
            "name": self.name,
            "enabled": self.enabled
        }

