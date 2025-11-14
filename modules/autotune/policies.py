"""
Tuning policies for SLA-aware autotuner.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def _clamp_fraction(value: float) -> float:
    return max(0.05, min(0.30, float(value)))


class TuningPolicy:
    """Base class for tuning policies."""
    
    def __init__(self, name: str):
        self.name = name
    
    def calculate_step_size(self, current_metrics: Dict[str, float], 
                          target_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate step sizes for parameter updates."""
        raise NotImplementedError
    
    def get_emergency_adjustments(self) -> Dict[str, float]:
        """Get emergency parameter adjustments."""
        raise NotImplementedError



class LatencyFirstPolicy(TuningPolicy):
    """Policy that prioritizes latency over recall."""
    
    def __init__(self):
        super().__init__("LatencyFirst")
    
    def calculate_step_size(self, current_metrics: Dict[str, float], 
                          target_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate step sizes prioritizing latency."""
        target_p95 = target_metrics.get("p95_ms", 30.0)
        target_recall = target_metrics.get("recall", 0.95)
        
        current_p95 = current_metrics.get("p95_ms", 0.0)
        current_recall = current_metrics.get("recall_at_10", 0.0)
        
        # Base step sizes
        step_sizes = {
            "ef_search": 0.15,   # Moderate ef_search changes (HNSW parameter)
            "rerank_k": 0.25     # Aggressive rerank_k changes
        }
        
        # Adjust based on current performance
        if current_p95 > target_p95 * 1.2:  # 20% over target
            # Aggressive latency reduction
            step_sizes["rerank_k"] *= 2.0
            step_sizes["ef_search"] *= 1.5
        elif current_p95 < target_p95 * 0.8:  # 20% under target
            # Can afford to improve recall
            if current_recall < target_recall - 0.05:
                step_sizes["ef_search"] *= 0.8
                step_sizes["rerank_k"] *= 1.2
        
        return {k: _clamp_fraction(v) for k, v in step_sizes.items()}
    
    def get_emergency_adjustments(self) -> Dict[str, float]:
        """Emergency adjustments for latency-first policy."""
        return {
            "ef_search": 0.7,    # Reduce ef_search by 30%
            "rerank_k": 0.5      # Reduce rerank_k by 50%
        }


class RecallFirstPolicy(TuningPolicy):
    """Policy that prioritizes recall over latency."""
    
    def __init__(self):
        super().__init__("RecallFirst")
    
    def calculate_step_size(self, current_metrics: Dict[str, float], 
                          target_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate step sizes prioritizing recall."""
        target_p95 = target_metrics.get("p95_ms", 30.0)
        target_recall = target_metrics.get("recall", 0.95)
        
        current_p95 = current_metrics.get("p95_ms", 0.0)
        current_recall = current_metrics.get("recall_at_10", 0.0)
        
        # Base step sizes
        step_sizes = {
            "ef_search": 0.25,   # Aggressive ef_search changes (HNSW parameter)
            "rerank_k": 0.15     # Conservative rerank_k changes
        }
        
        # Adjust based on current performance
        if current_recall < target_recall - 0.05:  # 5% under target
            # Aggressive recall improvement
            step_sizes["ef_search"] *= 1.5
            step_sizes["rerank_k"] *= 1.2
        elif current_p95 > target_p95 * 1.5:  # 50% over target
            # Must reduce latency
            step_sizes["rerank_k"] *= 1.5
            step_sizes["ef_search"] *= 0.8
        
        return {k: _clamp_fraction(v) for k, v in step_sizes.items()}
    
    def get_emergency_adjustments(self) -> Dict[str, float]:
        """Emergency adjustments for recall-first policy."""
        return {
            "ef_search": 0.8,    # Reduce ef_search by 20%
            "rerank_k": 0.6      # Reduce rerank_k by 40%
        }


class BalancedPolicy(TuningPolicy):
    """Policy that balances latency and recall."""
    
    def __init__(self):
        super().__init__("Balanced")
    
    def calculate_step_size(self, current_metrics: Dict[str, float], 
                          target_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate balanced step sizes."""
        target_p95 = target_metrics.get("p95_ms", 30.0)
        target_recall = target_metrics.get("recall", 0.95)
        
        current_p95 = current_metrics.get("p95_ms", 0.0)
        current_recall = current_metrics.get("recall_at_10", 0.0)
        
        # Base step sizes
        step_sizes = {
            "ef_search": 0.2,    # Moderate ef_search changes (HNSW parameter)
            "rerank_k": 0.2      # Moderate rerank_k changes
        }
        
        # Calculate normalized distances from targets
        p95_distance = abs(current_p95 - target_p95) / target_p95
        recall_distance = abs(current_recall - target_recall) / target_recall
        
        # Adjust based on which target is further
        if p95_distance > recall_distance * 1.5:
            # Latency is the bigger problem
            step_sizes["rerank_k"] *= 1.3
            step_sizes["ef_search"] *= 1.2
        elif recall_distance > p95_distance * 1.5:
            # Recall is the bigger problem
            step_sizes["ef_search"] *= 1.3
            step_sizes["rerank_k"] *= 1.1
        
        return {k: _clamp_fraction(v) for k, v in step_sizes.items()}
    
    def get_emergency_adjustments(self) -> Dict[str, float]:
        """Emergency adjustments for balanced policy."""
        return {
            "ef_search": 0.75,   # Reduce ef_search by 25%
            "rerank_k": 0.55     # Reduce rerank_k by 45%
        }


def get_policy(policy_name: str) -> TuningPolicy:
    """Factory function to get tuning policy."""
    key = str(policy_name).strip().lower()
    policy_cls = _POLICY_REGISTRY.get(key)
    if policy_cls is None:
        raise ValueError(f"Unknown policy '{policy_name}'")
    return policy_cls()


_POLICY_CLASSES = {
    "LatencyFirst": LatencyFirstPolicy,
    "RecallFirst": RecallFirstPolicy,
    "Balanced": BalancedPolicy,
}
_POLICY_REGISTRY = {name.lower(): policy_cls for name, policy_cls in _POLICY_CLASSES.items()}
POLICY_NAMES = list(_POLICY_CLASSES.keys())