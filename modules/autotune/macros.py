"""
Macro knobs for high-level search pipeline control.

This module provides macro-level parameters that can be used to control
the search pipeline behavior at a high level, with automatic derivation
of lower-level parameters.
"""

import os
from typing import Dict, Any


def clamp01(x: float) -> float:
    """
    Clamp a value to the range [0, 1].
    
    Args:
        x: Value to clamp
        
    Returns:
        Clamped value in range [0, 1]
    """
    return max(0.0, min(1.0, x))


def derive_params(latency_guard: float, recall_bias: float) -> Dict[str, Any]:
    """
    Derive search pipeline parameters from macro knobs.
    
    Args:
        latency_guard: Latency preference (0=recall-focused, 1=latency-focused)
        recall_bias: Recall preference (0=latency-focused, 1=recall-focused)
        
    Returns:
        Dictionary of derived parameters
    """
    # Clamp inputs to valid range
    LG = clamp01(latency_guard)
    RB = clamp01(recall_bias)
    
    # Derive parameters based on macro knobs
    T = round(200 + 1000 * LG)  # Threshold for exact vs HNSW path
    Ncand_max = round(1500 - 1000 * LG)  # Maximum candidates
    
    # Batch size based on latency guard
    if LG < 0.33:
        batch_size = 256
    elif LG < 0.66:
        batch_size = 128
    else:
        batch_size = 64
    
    # EF search parameter based on recall bias
    ef_options = [64, 96, 128, 160, 192, 224, 256]
    ef_index = round(6 * RB)
    ef_index = max(0, min(len(ef_options) - 1, ef_index))
    ef = ef_options[ef_index]
    
    # Rerank multiplier based on recall bias
    rerank_multipliers = [2, 3, 4, 5, 6]
    rerank_index = round(4 * RB)
    rerank_index = max(0, min(len(rerank_multipliers) - 1, rerank_index))
    rerank_multiplier = rerank_multipliers[rerank_index]
    
    # Clamp derived values to sensible ranges
    T = max(100, min(2000, T))
    Ncand_max = max(100, min(2000, Ncand_max))
    batch_size = max(32, min(512, batch_size))
    ef = max(32, min(512, ef))
    rerank_multiplier = max(1, min(10, rerank_multiplier))
    
    return {
        "T": T,
        "Ncand_max": Ncand_max,
        "batch_size": batch_size,
        "ef": ef,
        "rerank_multiplier": rerank_multiplier
    }


def get_macro_config() -> Dict[str, Any]:
    """
    Get macro knob configuration from environment variables with defaults.
    
    Returns:
        Dictionary containing latency_guard and recall_bias values
    """
    latency_guard = float(os.getenv("LATENCY_GUARD", "0.5"))
    recall_bias = float(os.getenv("RECALL_BIAS", "0.5"))
    
    return {
        "latency_guard": clamp01(latency_guard),
        "recall_bias": clamp01(recall_bias)
    }
