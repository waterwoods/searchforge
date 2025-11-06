"""
Base Signal interface for control flow shaping.

Signals monitor system metrics and provide normalized readings.
They auto-disable on errors (fail-safe behavior).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class Signal(ABC):
    """Base class for control signals."""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.error_count = 0
        self.max_errors = 3
        self.last_error: Optional[str] = None
        self.last_value: Optional[float] = None
        self.last_read_time: float = 0
    
    @abstractmethod
    async def read(self) -> float:
        """
        Read the signal value.
        
        Returns:
            Normalized signal value (typically 0.0-1.0)
        
        Raises:
            Exception: If reading fails
        """
        pass
    
    async def safe_read(self) -> Dict[str, Any]:
        """
        Safe read with error handling and auto-disable.
        
        Returns:
            Dict with ok, value, error, and metadata
        """
        if not self.enabled:
            return {
                "ok": False,
                "value": None,
                "error": "signal_disabled",
                "signal": self.name,
                "last_error": self.last_error
            }
        
        try:
            value = await self.read()
            self.last_value = value
            self.last_read_time = time.time()
            self.error_count = 0  # Reset on success
            
            return {
                "ok": True,
                "value": value,
                "signal": self.name,
                "timestamp": self.last_read_time
            }
        
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            
            logger.error(
                f"Signal {self.name} read error ({self.error_count}/{self.max_errors}): {e}"
            )
            
            # Auto-disable after max_errors
            if self.error_count >= self.max_errors:
                self.enabled = False
                logger.warning(
                    f"Signal {self.name} auto-disabled after {self.max_errors} errors"
                )
            
            return {
                "ok": False,
                "value": None,
                "error": str(e),
                "signal": self.name,
                "error_count": self.error_count,
                "auto_disabled": not self.enabled
            }
    
    def reset(self):
        """Reset signal state (re-enable and clear errors)."""
        self.enabled = True
        self.error_count = 0
        self.last_error = None
        logger.info(f"Signal {self.name} reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get signal status."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_value": self.last_value,
            "last_read_time": self.last_read_time
        }

