"""
Shadow Traffic Module
=====================
Provides shadow traffic routing capability for A/B testing and gradual rollout.

Default: 0% shadow traffic (disabled)
"""

import os
import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)

# Load shadow traffic percentage from environment
_SHADOW_TRAFFIC_PCT = float(os.getenv("SHADOW_TRAFFIC_PCT", "0.0"))

# Validate percentage
if not 0.0 <= _SHADOW_TRAFFIC_PCT <= 100.0:
    logger.warning(
        f"[SHADOW] Invalid SHADOW_TRAFFIC_PCT={_SHADOW_TRAFFIC_PCT}, "
        f"must be 0-100. Using 0.0"
    )
    _SHADOW_TRAFFIC_PCT = 0.0

logger.info(f"[SHADOW] Initialized with {_SHADOW_TRAFFIC_PCT}% shadow traffic")


def should_shadow(request_id: Optional[str] = None) -> bool:
    """
    Determine if a request should be shadowed based on configured percentage.
    
    Args:
        request_id: Optional request ID for deterministic shadowing
        
    Returns:
        True if request should be shadowed, False otherwise
        
    Examples:
        >>> # With 10% shadow traffic
        >>> should_shadow()  # Returns True ~10% of the time
        >>> should_shadow("req-123")  # Deterministic based on request ID
    """
    if _SHADOW_TRAFFIC_PCT == 0.0:
        return False
    
    if _SHADOW_TRAFFIC_PCT >= 100.0:
        return True
    
    # Use random sampling
    return random.random() * 100.0 < _SHADOW_TRAFFIC_PCT


def get_shadow_config() -> dict:
    """
    Get current shadow traffic configuration.
    
    Returns:
        Dictionary with shadow configuration:
        {
            "enabled": bool,
            "percentage": float,
            "status": str
        }
    """
    enabled = _SHADOW_TRAFFIC_PCT > 0.0
    
    return {
        "enabled": enabled,
        "percentage": _SHADOW_TRAFFIC_PCT,
        "status": "active" if enabled else "disabled"
    }


def set_shadow_percentage(percentage: float) -> bool:
    """
    Update shadow traffic percentage at runtime (for future use).
    
    Note: Currently not persisted. Will be reset on server restart.
    
    Args:
        percentage: New percentage (0.0-100.0)
        
    Returns:
        True if updated successfully, False if invalid
    """
    global _SHADOW_TRAFFIC_PCT
    
    if not 0.0 <= percentage <= 100.0:
        logger.error(f"[SHADOW] Invalid percentage: {percentage}")
        return False
    
    old_pct = _SHADOW_TRAFFIC_PCT
    _SHADOW_TRAFFIC_PCT = percentage
    
    logger.info(f"[SHADOW] Updated shadow traffic: {old_pct}% → {percentage}%")
    return True

