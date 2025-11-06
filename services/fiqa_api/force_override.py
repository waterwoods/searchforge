"""
Force Override System for Black Swan
=====================================
Provides a global force override mechanism that bypasses all guardrails,
constraints, and auto-tuners to guarantee exact parameter usage.

Key Features:
- Master switch (FORCE_OVERRIDE) to enable/disable
- JSON-based parameter specification
- Optional hard cap safety limits
- Comprehensive logging of all overrides

Usage:
    from force_override import apply_force_override
    
    params = {"num_candidates": 100, "rerank_topk": 50, "qps": 60}
    result = apply_force_override(params)
    # result will contain forced values if FORCE_OVERRIDE=true
"""

import logging
from typing import Dict, Any

# Import settings
try:
    import settings
    FORCE_CONFIG = settings.FORCE_OVERRIDE_CONFIG
except ImportError:
    # Fallback if settings not available
    FORCE_CONFIG = {
        "enabled": False,
        "params": {},
        "hard_cap_enabled": False,
        "hard_cap_limits": {}
    }

logger = logging.getLogger(__name__)


# Key mapping for different contexts
# Maps standardized force override keys to context-specific parameter names
KEY_MAPPINGS = {
    "black_swan_mode_b": {
        "num_candidates": "num_candidates",
        "rerank_topk": "rerank_topk",
        "qps": "qps"
    },
    "black_swan_mode_a_playbook": {
        "num_candidates": "num_candidates",
        "rerank_topk": "rerank_topk",
        "qps": "burst_qps"  # Map qps to burst_qps for Mode A
    },
    "black_swan_mode_b_playbook": {
        "num_candidates": "num_candidates",
        "rerank_topk": "rerank_topk",
        "qps": "burst_qps"  # Map qps to burst_qps for Mode B
    },
    "black_swan_mode_c_playbook": {
        "num_candidates": "num_candidates",
        "rerank_topk": "rerank_topk",
        "qps": "burst_qps"  # Map qps to burst_qps for Mode C
    }
}


def _get_mapped_key(force_key: str, context: str) -> str:
    """
    Get the mapped parameter key for a given context.
    
    Args:
        force_key: Standardized force override key (e.g., "num_candidates", "qps")
        context: Context string (e.g., "black_swan_mode_b")
        
    Returns:
        Mapped key for the context, or original key if no mapping exists
    """
    if context in KEY_MAPPINGS:
        return KEY_MAPPINGS[context].get(force_key, force_key)
    return force_key


def apply_force_override(params: Dict[str, Any], context: str = "unknown") -> Dict[str, Any]:
    """
    Apply force override to parameters, bypassing all guardrails.
    
    This function:
    1. If FORCE_OVERRIDE=false, returns params unchanged
    2. If FORCE_OVERRIDE=true:
       - Replaces runtime parameters with forced values
       - Skips all constraint/guardrail/clamp logic
       - Optionally applies hard cap limits as safety fuse
       - Logs all actions clearly
    
    Args:
        params: Runtime parameters (num_candidates, rerank_topk, qps, etc.)
        context: Context string for logging (e.g., "mode_b_request", "search_pipeline")
        
    Returns:
        Modified parameters with force override applied (if enabled)
        
    Examples:
        >>> # With FORCE_OVERRIDE=false
        >>> apply_force_override({"num_candidates": 100})
        {"num_candidates": 100}  # unchanged
        
        >>> # With FORCE_OVERRIDE=true, FORCE_PARAMS_JSON='{"num_candidates":2000}'
        >>> apply_force_override({"num_candidates": 100})
        {"num_candidates": 2000}  # forced override
        
        >>> # With HARD_CAP enabled and limit num_candidates=5000
        >>> apply_force_override({"num_candidates": 8000})
        {"num_candidates": 5000}  # clamped to hard cap
    """
    # Quick exit if force override is disabled
    if not FORCE_CONFIG["enabled"]:
        return params
    
    # Start with original params
    result = params.copy()
    
    # Apply forced parameters with key mapping
    forced_params = FORCE_CONFIG["params"]
    if forced_params:
        # Track what was changed
        changed = {}
        for force_key, forced_value in forced_params.items():
            # Map the force override key to context-specific key
            mapped_key = _get_mapped_key(force_key, context)
            
            original_value = result.get(mapped_key)
            if original_value != forced_value:
                changed[mapped_key] = {"from": original_value, "to": forced_value}
            result[mapped_key] = forced_value
        
        if changed:
            logger.info(f"[FORCE_OVERRIDE] Applied params in {context}: {changed}")
            print(f"[FORCE_OVERRIDE] Applied params in {context}: {_format_changes(changed)}")
    
    # Apply hard cap limits if enabled
    if FORCE_CONFIG["hard_cap_enabled"] and FORCE_CONFIG["hard_cap_limits"]:
        hard_caps = FORCE_CONFIG["hard_cap_limits"]
        clamped = {}
        
        for key, limit in hard_caps.items():
            if key in result:
                original_value = result[key]
                # Clamp to hard cap (assume limit is maximum)
                if isinstance(original_value, (int, float)) and original_value > limit:
                    result[key] = limit
                    clamped[key] = {"from": original_value, "to": limit, "limit": limit}
        
        if clamped:
            logger.warning(f"[HARD_CAP] Clamped values in {context}: {clamped}")
            print(f"[HARD_CAP] Clamped values in {context}: {_format_clamps(clamped)}")
    
    return result


def _format_changes(changes: Dict[str, Dict]) -> str:
    """Format parameter changes for logging."""
    parts = []
    for key, change in changes.items():
        parts.append(f"{key}: {change['from']} → {change['to']}")
    return ", ".join(parts)


def _format_clamps(clamps: Dict[str, Dict]) -> str:
    """Format hard cap clamps for logging."""
    parts = []
    for key, clamp in clamps.items():
        parts.append(f"{key}: {clamp['from']} → {clamp['to']} (limit={clamp['limit']})")
    return ", ".join(parts)


def get_force_override_status() -> Dict[str, Any]:
    """
    Get current force override configuration and status.
    
    Returns:
        Dictionary with current configuration:
        {
            "force_override": bool,
            "active_params": dict,
            "hard_cap_enabled": bool,
            "hard_cap_limits": dict
        }
    """
    # Ensure FORCE_CONFIG is up-to-date (in case settings are reloaded or changed)
    import settings as app_settings
    global FORCE_CONFIG
    FORCE_CONFIG = app_settings.FORCE_OVERRIDE_CONFIG
    
    return {
        "force_override": FORCE_CONFIG["enabled"],
        "active_params": FORCE_CONFIG["params"],
        "hard_cap_enabled": FORCE_CONFIG["hard_cap_enabled"],
        "hard_cap_limits": FORCE_CONFIG["hard_cap_limits"]
    }


def is_force_override_enabled() -> bool:
    """Check if force override is currently enabled."""
    return FORCE_CONFIG["enabled"]


# Initialize FORCE_CONFIG from settings at module load time
try:
    import settings as app_settings
    FORCE_CONFIG = app_settings.FORCE_OVERRIDE_CONFIG
except ImportError:
    # Fallback if settings not available
    pass

# Log module initialization
if FORCE_CONFIG["enabled"]:
    logger.info(f"[FORCE_OVERRIDE] Module loaded: ENABLED with params {FORCE_CONFIG['params']}")
    if FORCE_CONFIG["hard_cap_enabled"]:
        logger.info(f"[FORCE_OVERRIDE] Hard cap ENABLED with limits: {FORCE_CONFIG['hard_cap_limits']}")
    else:
        logger.info("[FORCE_OVERRIDE] Hard cap DISABLED")
else:
    logger.info("[FORCE_OVERRIDE] Module loaded: DISABLED")

