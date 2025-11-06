"""
Watchdog Plugin
===============
Minimal no-op implementation for system health monitoring.

Future: Add circuit breakers, anomaly detection, auto-recovery, etc.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

__all__ = ["record_event", "get_status", "WatchdogStatus"]


class WatchdogStatus:
    """Status of watchdog system."""
    
    def __init__(self):
        self.enabled = False
        self.mode = "noop"
        self.monitors_count = 0
        self.alerts_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "monitors_count": self.monitors_count,
            "alerts_count": self.alerts_count,
            "status": "ok"
        }


def record_event(event_type: str, data: Dict[str, Any], context: str = "unknown") -> None:
    """
    Record an event for watchdog monitoring (no-op for now).
    
    Args:
        event_type: Type of event (e.g., "latency_spike", "error_rate")
        data: Event data
        context: Context for event
    """
    logger.debug(f"[WATCHDOG] No-op event recording: {event_type} in {context}")


def get_status() -> Dict[str, Any]:
    """
    Get current watchdog status.
    
    Returns:
        Status dictionary with watchdog information
    """
    status = WatchdogStatus()
    return status.to_dict()


# Initialize
logger.info("[WATCHDOG] Initialized in no-op mode")

