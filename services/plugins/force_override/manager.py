"""
Force Override Manager
======================
Stateless precedence resolution and parameter override logic.

Precedence Order:
1. Request params (user input)
2. FORCE_OVERRIDE (if enabled - replaces with forced values)
3. GUARDRAILS (placeholder for future constraints)
4. HARD_CAP (if enabled - clamps to max limits)
5. Defaults (fallback values)
"""

import logging
from typing import Dict, Any, Optional
from services.core import settings
from services.plugins.force_override.schemas import ForceStatus

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


def resolve(
    planned: Dict[str, Any],
    context: str = "unknown",
    defaults: Optional[Dict[str, Any]] = None
) -> ForceStatus:
    """
    Resolve parameters through full precedence chain.
    
    Args:
        planned: Planned/requested parameters
        context: Execution context for logging and key mapping
        defaults: Default values for missing parameters
        
    Returns:
        ForceStatus with complete precedence trace
    """
    if defaults is None:
        defaults = {}
    
    # Load configuration from environment
    config = settings.get_force_override_config()
    force_enabled = config["enabled"]
    force_params = config["params"]
    hard_cap_enabled = config["hard_cap_enabled"]
    hard_cap_limits = config["hard_cap_limits"]
    
    # Initialize tracking
    precedence_chain = []
    effective = planned.copy()
    
    # Step 1: Start with planned params
    precedence_chain.append(f"START: planned={planned}")
    
    # Step 2: Apply defaults for missing keys
    for key, default_value in defaults.items():
        if key not in effective:
            effective[key] = default_value
            precedence_chain.append(f"DEFAULT: {key} = {default_value}")
    
    # Step 3: Apply force override (if enabled)
    if force_enabled and force_params:
        for force_key, forced_value in force_params.items():
            # Map the force override key to context-specific key
            mapped_key = _get_mapped_key(force_key, context)
            
            original_value = effective.get(mapped_key)
            if original_value != forced_value:
                effective[mapped_key] = forced_value
                precedence_chain.append(
                    f"FORCE_OVERRIDE: {mapped_key} {original_value} → {forced_value}"
                )
                logger.info(
                    f"[FORCE_OVERRIDE] {context}: {mapped_key} {original_value} → {forced_value}"
                )
    elif force_enabled:
        precedence_chain.append("FORCE_OVERRIDE: enabled but no params configured")
    else:
        precedence_chain.append("FORCE_OVERRIDE: disabled")
    
    # Step 4: Apply guardrails (placeholder for future implementation)
    precedence_chain.append("GUARDRAILS: (not implemented)")
    
    # Step 5: Apply hard cap limits (if enabled)
    if hard_cap_enabled and hard_cap_limits:
        clamped_count = 0
        for key, limit in hard_cap_limits.items():
            if key in effective:
                original_value = effective[key]
                # Clamp to hard cap (assume limit is maximum)
                if isinstance(original_value, (int, float)) and original_value > limit:
                    effective[key] = limit
                    precedence_chain.append(
                        f"HARD_CAP: {key} {original_value} → {limit} (clamped to limit)"
                    )
                    logger.warning(
                        f"[HARD_CAP] {context}: {key} {original_value} → {limit}"
                    )
                    clamped_count += 1
        
        if clamped_count == 0:
            precedence_chain.append("HARD_CAP: (no clamping needed)")
    elif hard_cap_enabled:
        precedence_chain.append("HARD_CAP: enabled but no limits configured")
    else:
        precedence_chain.append("HARD_CAP: disabled")
    
    # Step 6: Final result
    precedence_chain.append(f"END: effective={effective}")
    
    # Log final effective parameters
    logger.info(
        f"[FORCE_OVERRIDE] {context}: effective_params={effective} "
        f"(force_enabled={force_enabled}, hard_cap_enabled={hard_cap_enabled})"
    )
    
    return ForceStatus(
        force_override=force_enabled,
        hard_cap_enabled=hard_cap_enabled,
        planned_params=planned,
        effective_params=effective,
        precedence_chain=precedence_chain,
        hard_cap_limits=hard_cap_limits,
        force_params=force_params
    )


def apply(
    params: Dict[str, Any],
    context: str = "unknown",
    defaults: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Apply force override and return effective parameters.
    
    This is a convenience wrapper around resolve() that just returns
    the effective_params dictionary.
    
    Args:
        params: Input parameters
        context: Execution context
        defaults: Default values
        
    Returns:
        Effective parameters after all overrides
    """
    status = resolve(params, context, defaults)
    return status.effective_params


def get_status() -> Dict[str, Any]:
    """
    Get current force override configuration without resolving parameters.
    
    Returns:
        Dictionary with current configuration:
        {
            "force_override": bool,
            "active_params": dict,
            "hard_cap_enabled": bool,
            "hard_cap_limits": dict
        }
    """
    config = settings.get_force_override_config()
    return {
        "force_override": config["enabled"],
        "active_params": config["params"],
        "hard_cap_enabled": config["hard_cap_enabled"],
        "hard_cap_limits": config["hard_cap_limits"]
    }


def is_enabled() -> bool:
    """Check if force override is currently enabled."""
    return settings.get_force_override_enabled()

