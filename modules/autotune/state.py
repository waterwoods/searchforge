"""
Tuning State Module for SmartSearchX

This module manages the state of the autotuner system.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TuningState:
    """State management for the autotuner."""

    # Parameters and valid ranges
    ef_search: int = 128
    rerank_k: int = 200
    hnsw_ef_range: tuple = (4, 256)
    rerank_range: tuple = (100, 1200)

    # Raw metrics (authoritative)
    p95_ms: float = 0.0
    recall_at_10: float = 0.0
    coverage: float = 1.0

    # Exponential moving averages
    ema_alpha: float = 0.3
    ema_p95_ms: Optional[float] = None
    ema_recall_at_10: Optional[float] = None

    # Targets
    target_p95_ms: float = 30.0
    target_recall: float = 0.95
    target_coverage: float = 0.98

    # History tracking
    recent_metrics: List[Dict[str, Any]] = field(default_factory=list)
    parameter_history: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 100
    history_len: int = 0  # Cumulative counter, increments on each update()
    _compact_count: int = 0  # Internal counter for compaction triggers

    # Guard bookkeeping
    recent_recall_queue: List[float] = field(default_factory=list)
    batches_since_decrease: int = 0
    is_emergency_mode: bool = False
    emergency_mode: bool = False  # legacy alias

    def update_metrics(self, p95_ms: float, recall_at_10: float, coverage: float):
        """Update raw metrics and maintain EMA history."""
        self.p95_ms = float(p95_ms)
        self.recall_at_10 = float(recall_at_10)
        self.coverage = float(coverage)

        alpha = self.ema_alpha
        if self.ema_p95_ms is None:
            self.ema_p95_ms = self.p95_ms
        else:
            self.ema_p95_ms = alpha * self.p95_ms + (1 - alpha) * self.ema_p95_ms

        if self.ema_recall_at_10 is None:
            self.ema_recall_at_10 = self.recall_at_10
        else:
            self.ema_recall_at_10 = alpha * self.recall_at_10 + (1 - alpha) * self.ema_recall_at_10

        snapshot = {
            "ts": time.time(),
            "p95_ms": self.p95_ms,
            "recall_at_10": self.recall_at_10,
            "coverage": self.coverage,
            "ema_p95_ms": self.ema_p95_ms,
            "ema_recall_at_10": self.ema_recall_at_10,
            "ef_search": self.ef_search,
            "rerank_k": self.rerank_k,
        }
        self.recent_metrics.append(snapshot)
        if len(self.recent_metrics) > self.max_history:
            self.recent_metrics.pop(0)

    def get_smoothed_metrics(self) -> Dict[str, float]:
        """Return smoothed metrics preferring EMA if present."""
        return {
            "p95_ms": self.ema_p95_ms if self.ema_p95_ms is not None else self.p95_ms,
            "recall_at_10": self.ema_recall_at_10 if self.ema_recall_at_10 is not None else self.recall_at_10,
            "coverage": self.coverage,
        }

    def get_current_params(self) -> Dict[str, int]:
        """Return current tuning parameters."""
        return {"ef_search": self.ef_search, "rerank_k": self.rerank_k}

    def _compact_if_needed(self):
        """
        Compact parameter_history if needed using sampling compression.
        
        Keeps most recent 10% in full, samples older entries (every N-th kept).
        Always preserves key statistics (recent window ema/max/min/last).
        """
        max_history = self.max_history
        compact_every = int(os.getenv("COMPACT_EVERY", "100"))
        compact_keep_every = int(os.getenv("COMPACT_KEEP_EVERY", "5"))
        
        current_len = len(self.parameter_history)
        should_compact = (
            current_len > max_history or
            (compact_every > 0 and self._compact_count >= compact_every)
        )
        
        if not should_compact:
            return
        
        if current_len <= max_history and current_len <= 100:
            # No compaction needed yet
            return
        
        # Keep most recent 10% in full
        keep_recent_pct = 0.10
        recent_threshold = max(int(current_len * keep_recent_pct), 10)
        recent_items = self.parameter_history[-recent_threshold:]
        older_items = self.parameter_history[:-recent_threshold]
        
        # Sample older items (keep every N-th)
        sampled_older = []
        for idx, item in enumerate(older_items):
            if idx % compact_keep_every == 0:
                sampled_older.append(item)
        
        # Reconstruct history: sampled older + full recent
        self.parameter_history = sampled_older + recent_items
        
        # Preserve key statistics: always keep first, last, max, min if they exist
        if len(self.parameter_history) > 0:
            first = self.parameter_history[0]
            last = self.parameter_history[-1]
            # Ensure first and last are present
            if self.parameter_history[0] is not first:
                self.parameter_history.insert(0, first)
            if self.parameter_history[-1] is not last:
                self.parameter_history.append(last)
        
        # Reset compact counter
        self._compact_count = 0
        
        # Ensure we don't exceed max_history
        if len(self.parameter_history) > max_history:
            self.parameter_history = self.parameter_history[-max_history:]

    def update_params(self, **kwargs):
        """Update parameters from kwargs (updated for HNSW)."""
        updated = False
        if "ef_search" in kwargs:
            self.ef_search = kwargs["ef_search"]
            updated = True
        if "rerank_k" in kwargs:
            self.rerank_k = kwargs["rerank_k"]
            updated = True
        if "nprobe" in kwargs:
            self.ef_search = kwargs["nprobe"]
            updated = True

        if updated:
            # Increment history_len counter (monotonically increasing)
            self.history_len += 1
            self._compact_count += 1
            
            snapshot = {
                "ts": time.time(),
                "ef_search": self.ef_search,
                "rerank_k": self.rerank_k,
            }
            self.parameter_history.append(snapshot)
            
            # Compact if needed
            self._compact_if_needed()
            
            # Final safety check: ensure we don't exceed max_history
            if len(self.parameter_history) > self.max_history:
                self.parameter_history = self.parameter_history[-self.max_history:]

    def check_safety_limits(self, target_p95_ms: float, target_recall: float) -> Dict[str, bool]:
        """Check safety limits for autotuner."""
        return {
            "coverage_ok": self.coverage >= 0.98,
            "p95_spike": self.p95_ms > target_p95_ms * 3.0,
            "recall_ok": self.recall_at_10 >= target_recall * 0.8,
        }

    def set_emergency_mode(self, enabled: bool):
        """Set emergency mode flag."""
        self.is_emergency_mode = enabled
        self.emergency_mode = enabled

    def get_convergence_status(self) -> Dict[str, Any]:
        """Get convergence status (simplified implementation)."""
        return {"converged": False, "stability_score": 0.5, "trend": "unknown"}

    def reset_failures(self):
        """Reset failure counters."""
        pass
