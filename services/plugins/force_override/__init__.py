"""
Force Override Plugin
=====================
Clean extraction of force override and hard cap functionality.

Usage:
    from services.plugins.force_override import resolve, apply, get_status
    
    # Get full precedence trace
    status = resolve({"num_candidates": 100})
    print(status.precedence_chain)
    
    # Just get effective params
    effective = apply({"num_candidates": 100})
    print(effective)
    
    # Check current config
    config = get_status()
    print(f"Force override: {config['force_override']}")
"""

from services.plugins.force_override.manager import (
    resolve,
    apply,
    get_status,
    is_enabled,
)
from services.plugins.force_override.schemas import (
    ForceStatus,
    OverrideEvent,
)

__all__ = [
    "resolve",
    "apply",
    "get_status",
    "is_enabled",
    "ForceStatus",
    "OverrideEvent",
]

