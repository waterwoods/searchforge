"""
Tuning State Module for SmartSearchX

This module manages the state of the autotuner system.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time


@dataclass
class TuningState:
    """State management for the autotuner."""
    
    # Parameter ranges (updated for HNSW)
    hnsw_ef_range: tuple = (4, 256)
    rerank_range: tuple = (100, 1200)
    ema_alpha: float = 0.2
    
    # Current parameters (updated for HNSW)
    ef_search: int = 128  # Primary HNSW parameter
    rerank: int = 200
    
    # Performance metrics
    current_p95_ms: float = 0.0
    current_recall: float = 0.0
    current_coverage: float = 0.0
    
    # Historical data
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    parameter_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # State flags
    is_tuning: bool = False
    last_tuning_time: float = 0.0
    tuning_count: int = 0
    
    # SLA targets
    target_p95_ms: float = 30.0
    target_recall: float = 0.95
    target_coverage: float = 0.9
    
    # Additional attributes needed by controller
    ef_search: int = 128
    coverage: float = 1.0
    p95_ms: float = 0.0
    recall_at_10: float = 0.0
    recent_recall_queue: List[float] = field(default_factory=list)
    recent_metrics: List[Dict[str, Any]] = field(default_factory=list)
    batches_since_decrease: int = 0
    is_emergency_mode: bool = False
    emergency_mode: bool = False  # Alias for compatibility
    
    def update_performance(self, p95_ms: float, recall: float, coverage: float):
        """Update current performance metrics."""
        self.current_p95_ms = p95_ms
        self.current_recall = recall
        self.current_coverage = coverage
        
        # Add to history
        self.performance_history.append({
            "timestamp": time.time(),
            "p95_ms": p95_ms,
            "recall": recall,
            "coverage": coverage
        })
        
        # Keep only last 100 entries
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    def update_metrics(self, p95_ms: float, recall_at_10: float, coverage: float):
        """Update metrics (alias for update_performance for compatibility)."""
        self.update_performance(p95_ms, recall_at_10, coverage)
    
    def update_parameters(self, ef_search: int, rerank: int):
        """Update current parameters (updated for HNSW)."""
        self.ef_search = ef_search
        self.rerank = rerank
        
        # Add to history
        self.parameter_history.append({
            "timestamp": time.time(),
            "ef_search": ef_search,
            "rerank": rerank
        })
        
        # Keep only last 100 entries
        if len(self.parameter_history) > 100:
            self.parameter_history = self.parameter_history[-100:]
    
    def start_tuning(self):
        """Mark that tuning has started."""
        self.is_tuning = True
        self.last_tuning_time = time.time()
        self.tuning_count += 1
    
    def stop_tuning(self):
        """Mark that tuning has stopped."""
        self.is_tuning = False
    
    def get_sla_violations(self) -> Dict[str, bool]:
        """Check for SLA violations."""
        return {
            "p95_violation": self.current_p95_ms > self.target_p95_ms,
            "recall_violation": self.current_recall < self.target_recall,
            "coverage_violation": self.current_coverage < self.target_coverage
        }
    
    def get_performance_trend(self) -> str:
        """Get performance trend based on recent history."""
        if len(self.performance_history) < 2:
            return "unknown"
        
        recent_p95 = [entry["p95_ms"] for entry in self.performance_history[-5:]]
        if len(recent_p95) < 2:
            return "unknown"
        
        if recent_p95[-1] < recent_p95[0]:
            return "improving"
        elif recent_p95[-1] > recent_p95[0]:
            return "degrading"
        else:
            return "stable"
    
    def check_safety_limits(self, target_p95_ms: float, target_recall: float) -> Dict[str, bool]:
        """Check safety limits for autotuner."""
        return {
            "coverage_ok": self.current_coverage >= 0.98,
            "p95_spike": self.current_p95_ms > target_p95_ms * 3.0,  # 3x target is a spike
            "recall_ok": self.current_recall >= target_recall * 0.8  # 80% of target is minimum
        }
    
    def set_emergency_mode(self, enabled: bool):
        """Set emergency mode flag."""
        self.is_emergency_mode = getattr(self, 'is_emergency_mode', False)
        self.is_emergency_mode = enabled
    
    def get_smoothed_metrics(self) -> Dict[str, float]:
        """Get smoothed metrics (simplified implementation)."""
        return {
            "p95_ms": self.current_p95_ms,
            "recall_at_10": self.current_recall,
            "coverage": self.current_coverage
        }
    
    def get_current_params(self) -> Dict[str, int]:
        """Get current tuning parameters (updated for HNSW)."""
        return {
            "ef_search": getattr(self, 'ef_search', 128),
            "rerank_k": getattr(self, 'rerank', 200)
        }
    
    def update_params(self, **kwargs):
        """Update parameters from kwargs (updated for HNSW)."""
        if 'ef_search' in kwargs:
            self.ef_search = kwargs['ef_search']
        if 'rerank_k' in kwargs:
            self.rerank = kwargs['rerank_k']
        # Handle legacy nprobe parameter by mapping to ef_search
        if 'nprobe' in kwargs:
            self.ef_search = kwargs['nprobe']
    
    def get_convergence_status(self) -> Dict[str, Any]:
        """Get convergence status (simplified implementation)."""
        return {
            "converged": False,
            "stability_score": 0.5,
            "trend": "unknown"
        }
    
    def reset_failures(self):
        """Reset failure counters."""
        pass
