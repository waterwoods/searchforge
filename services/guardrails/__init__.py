"""
Guardrails Plugin
=================
Minimal no-op implementation for parameter validation and constraints.

Future: Add intelligent parameter validation, budget enforcement, etc.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

__all__ = ["validate", "get_status", "GuardrailsStatus"]


class GuardrailsStatus:
    """Status of guardrails system."""
    
    def __init__(self):
        self.enabled = False
        self.mode = "noop"
        self.rules_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "rules_count": self.rules_count,
            "status": "ok"
        }


def validate(params: Dict[str, Any], context: str = "unknown") -> Dict[str, Any]:
    """
    Validate parameters through guardrails (no-op for now).
    
    Args:
        params: Parameters to validate
        context: Context for validation
        
    Returns:
        Validated parameters (unchanged in no-op mode)
    """
    logger.debug(f"[GUARDRAILS] No-op validation for {context}: {params}")
    return params


def get_status() -> Dict[str, Any]:
    """
    Get current guardrails status.
    
    Returns:
        Status dictionary with guardrails information
    """
    status = GuardrailsStatus()
    return status.to_dict()


# Initialize
logger.info("[GUARDRAILS] Initialized in no-op mode")

