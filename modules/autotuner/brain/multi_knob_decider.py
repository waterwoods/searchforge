"""
AutoTuner Brain - Multi-Knob Decider

Implements multi-parameter tuning decisions with preset bundles and adaptive step sizing.
"""

from typing import Dict, Any, Optional, Tuple
from .contracts import TuningInput, Action, SLO
from .autotuner_config import ENABLE_COMPLEX_STEP, ENABLE_BANDIT


# Preset bundles for different optimization goals (reduced steps for safety)
BUNDLES = {
    "latency_drop": {
        "ef_search": -32,  # Reduced from -64
        "candidate_k": -25,  # Reduced from -50
        "threshold_T": 0.01  # Reduced from 0.02
    },
    "recall_gain": {
        "ef_search": 32,  # Reduced from 64
        "rerank_k": 6,  # Reduced from 10
        "threshold_T": -0.01  # Reduced from -0.02
    },
    "steady_nudge": {
        "ef_search": -16,  # Reduced from -32
        "candidate_k": -12,  # Reduced from -25
        "threshold_T": 0.005  # Reduced from 0.01
    }
}

# Round-robin state for bundle cycling
_bundle_round_robin = ["latency_drop", "recall_gain"]
_bundle_round_robin_index = 0
_bundle_cooldown_ticks = 2
_bundle_cooldown_remaining = 0


def decide_multi_knob(inp: TuningInput, macros: Optional[Dict[str, float]] = None) -> Action:
    """
    Decide multi-knob tuning action based on current performance and SLO.
    
    Args:
        inp: Tuning input with current performance metrics
        macros: Optional macro indicators (L/R bias)
        
    Returns:
        Multi-knob action with updates dict and mode
    """
    global _bundle_round_robin_index, _bundle_cooldown_remaining
    
    # Check cooldown first - during cooldown, switch to single-knob micro-steps
    if _bundle_cooldown_remaining > 0:
        _bundle_cooldown_remaining -= 1
        
        # During cooldown, provide single-knob micro-step
        micro_step = _get_cooldown_micro_step(inp, macros)
        if micro_step:
            return Action(
                kind="multi_knob",
                step=0.0,
                reason=f"COOLDOWN_MICRO_STEP_{_bundle_cooldown_remaining}",
                updates=micro_step,
                mode="sequential"
            )
        else:
            return Action(
                kind="noop",
                step=0.0,
                reason=f"BUNDLE_COOLDOWN_REMAINING_{_bundle_cooldown_remaining}",
                updates=None,
                mode="sequential"
            )
    
    # Check if we should use memory-based steady nudge
    memory_hit = _check_memory_sweet_spot(inp)
    
    # Determine which bundle to use based on performance vs SLO
    bundle_name, scale_factor = _select_bundle_with_rr(inp, macros, memory_hit)
    
    if bundle_name == "noop":
        return Action(
            kind="noop",
            step=0.0,
            reason="within_slo_or_uncertain",
            updates=None,
            mode="sequential"
        )
    
    # Get the base bundle and apply scaling
    base_updates = BUNDLES[bundle_name].copy()
    
    # ⚠️ Feature Freeze: Complex step scaling is disabled, use base scale only
    if ENABLE_COMPLEX_STEP:
        scaled_updates = _scale_updates(base_updates, scale_factor)
    else:
        # Simple scaling: only apply if scale_factor >= 0.5, else use base
        scaled_updates = _scale_updates(base_updates, max(0.5, scale_factor))
    
    # ⚠️ Feature Freeze: Atomic mode disabled, force sequential mode
    # Determine application mode (sequential for safety)
    mode = "sequential"
    
    # Create reason with bundle info
    reason = f"MULTI_KNOB_{bundle_name.upper()}"
    if memory_hit:
        reason += "_MEMORY_HIT"
    
    # Set cooldown for next bundle
    _bundle_cooldown_remaining = _bundle_cooldown_ticks
    
    return Action(
        kind="multi_knob",
        step=0.0,  # Not used in multi-knob mode
        reason=reason,
        updates=scaled_updates,
        mode=mode
    )


def _check_memory_sweet_spot(inp: TuningInput) -> bool:
    """
    Check if we're in a memory sweet spot for steady nudging.
    
    This is a simplified heuristic - in a real implementation,
    this would query the memory system.
    """
    # Simple heuristic: if we're close to SLO on both metrics
    p95_margin = inp.slo.p95_ms - inp.p95_ms
    recall_margin = inp.recall_at10 - inp.slo.recall_at10
    
    return (p95_margin > -50 and p95_margin < 50 and 
            recall_margin > -0.02 and recall_margin < 0.02)


def _select_bundle(inp: TuningInput, macros: Optional[Dict[str, float]], memory_hit: bool) -> Tuple[str, float]:
    """
    Select appropriate bundle based on performance vs SLO.
    
    Returns:
        Tuple of (bundle_name, scale_factor)
    """
    # Check for latency issues with recall margin
    if (inp.p95_ms > inp.slo.p95_ms and 
        inp.recall_at10 >= inp.slo.recall_at10 + 0.01):
        return "latency_drop", 1.0
    
    # Check for recall issues with latency margin  
    if (inp.recall_at10 < inp.slo.recall_at10 and 
        inp.p95_ms <= inp.slo.p95_ms - 10):
        return "recall_gain", 1.0
    
    # Check for macro bias
    if macros:
        L = macros.get("L", 0.0)
        R = macros.get("R", 0.0)
        
        if L > 0.5:  # Left bias -> latency focus
            return "latency_drop", 0.5
        elif R > 0.5:  # Right bias -> recall focus  
            return "recall_gain", 0.5
    
    # Memory-based steady nudge
    if memory_hit:
        return "steady_nudge", 0.5
    
    # No action needed
    return "noop", 1.0


def _select_bundle_with_rr(inp: TuningInput, macros: Optional[Dict[str, float]], memory_hit: bool) -> Tuple[str, float]:
    """
    Select bundle based on performance vs SLO, macro bias, and round-robin.
    
    Args:
        inp: Tuning input
        macros: Optional macro indicators
        memory_hit: Whether memory sweet spot was hit
        
    Returns:
        Tuple of (bundle_name, scale_factor)
    """
    global _bundle_round_robin_index
    
    if memory_hit:
        return "steady_nudge", 0.5
    
    # Check performance vs SLO
    p95_margin = inp.p95_ms - inp.slo.p95_ms
    recall_margin = inp.recall_at10 - inp.slo.recall_at10
    
    # Latency drop: high p95, good recall
    if p95_margin > 0 and recall_margin >= 0.01:
        return "latency_drop", 1.0
    
    # Recall gain: low recall, good latency
    if recall_margin < 0 and p95_margin <= -10:
        return "recall_gain", 1.0
    
    # ⚠️ Feature Freeze: Bandit exploration is disabled, skip macro bias
    # Apply macro bias if available (only when ENABLE_BANDIT is true)
    if ENABLE_BANDIT and macros:
        l_bias = macros.get("L", 0.0)
        r_bias = macros.get("R", 0.0)
        
        if l_bias > 0.1:  # Strong L bias
            return "latency_drop", 1.0
        elif r_bias > 0.1:  # Strong R bias
            return "recall_gain", 1.0
    
    # ⚠️ Feature Freeze: Bandit disabled, skip round-robin and return noop
    if not ENABLE_BANDIT:
        return "noop", 1.0
    
    # Round-robin fallback for uncertain cases (only when ENABLE_BANDIT is true)
    bundle_name = _bundle_round_robin[_bundle_round_robin_index]
    _bundle_round_robin_index = (_bundle_round_robin_index + 1) % len(_bundle_round_robin)
    return bundle_name, 1.0


def reset_round_robin():
    """Reset round-robin state for testing."""
    global _bundle_round_robin_index, _bundle_cooldown_remaining
    _bundle_round_robin_index = 0
    _bundle_cooldown_remaining = 0


def get_round_robin_state() -> Dict[str, int]:
    """Get current round-robin state for debugging."""
    return {
        "bundle_index": _bundle_round_robin_index,
        "cooldown_remaining": _bundle_cooldown_remaining
    }


def _get_cooldown_micro_step(inp: TuningInput, macros: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
    """
    Get single-knob micro-step during cooldown.
    
    Returns small single-parameter updates based on performance vs SLO.
    """
    # Check performance vs SLO for micro-step direction
    p95_margin = inp.p95_ms - inp.slo.p95_ms
    recall_margin = inp.recall_at10 - inp.slo.recall_at10
    
    # Micro-steps (very small changes)
    if p95_margin > 5:  # High latency
        return {"ef_search": -8}  # Small ef reduction
    elif recall_margin < -0.02:  # Low recall
        return {"ef_search": 8}  # Small ef increase
    elif macros:
        l_bias = macros.get("L", 0.0)
        r_bias = macros.get("R", 0.0)
        if l_bias > 0.1:
            return {"ef_search": -8}  # Small ef reduction for L bias
        elif r_bias > 0.1:
            return {"ef_search": 8}  # Small ef increase for R bias
    
    # Default micro-step based on round-robin
    if _bundle_round_robin_index == 0:  # latency_drop
        return {"ef_search": -8}
    else:  # recall_gain
        return {"ef_search": 8}


def _scale_updates(updates: Dict[str, float], scale_factor: float) -> Dict[str, float]:
    """
    Scale update values by the given factor.
    
    Args:
        updates: Base update dictionary
        scale_factor: Scaling factor to apply
        
    Returns:
        Scaled updates dictionary
    """
    return {k: v * scale_factor for k, v in updates.items()}


def get_adaptive_step_factor(consecutive_improvements: int, consecutive_regressions: int) -> float:
    """
    Compute adaptive step factor based on recent performance.
    
    Args:
        consecutive_improvements: Number of consecutive improvements
        consecutive_regressions: Number of consecutive regressions
        
    Returns:
        Step scaling factor (1.0 = no change, >1.0 = increase, <1.0 = decrease)
    """
    # ⚠️ Feature Freeze: Complex step adjustment is disabled, return fixed scale
    if not ENABLE_COMPLEX_STEP:
        return 1.0
    
    if consecutive_improvements >= 2:
        # Two consecutive improvements -> increase step size
        return min(1.5, 1.0 + consecutive_improvements * 0.25)
    elif consecutive_regressions >= 1:
        # Regression -> decrease step size
        return max(0.33, 1.0 - consecutive_regressions * 0.5)
    else:
        return 1.0


def analyze_multi_knob_input(inp: TuningInput) -> Dict[str, Any]:
    """
    Analyze input for multi-knob decision making.
    
    Args:
        inp: Tuning input
        
    Returns:
        Analysis dictionary with decision factors
    """
    return {
        'latency_violation': inp.p95_ms > inp.slo.p95_ms,
        'recall_violation': inp.recall_at10 < inp.slo.recall_at10,
        'recall_margin': inp.recall_at10 - inp.slo.recall_at10,
        'latency_margin': inp.slo.p95_ms - inp.p95_ms,
        'memory_hit': _check_memory_sweet_spot(inp),
        'current_params': inp.params.copy()
    }
