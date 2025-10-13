"""
Performance Profiler for Auto Tuner System
Tracks latency distribution across key components: I/O, compute, logs, rendering

Usage:
    from profiler import profiled, get_profile_report, prof
    
    @profiled("component.operation")
    def some_function():
        ...
    
    # Context manager (safe for enabled/disabled):
    with prof("custom.operation"):
        do_something()
    
    # Get report via /admin/profiler/report endpoint
"""
import time
import statistics
from collections import defaultdict, deque
from typing import Dict, List, Any, Callable
from functools import wraps
from datetime import datetime
import threading
from contextlib import nullcontext


class ProfileStats:
    """Rolling window statistics for a labeled operation"""
    
    def __init__(self, label: str, window_size: int = 100):
        self.label = label
        self.window_size = window_size
        self.samples = deque(maxlen=window_size)
        self.lock = threading.Lock()
    
    def record(self, latency_ms: float):
        """Record a latency sample"""
        with self.lock:
            self.samples.append(latency_ms)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for current window"""
        with self.lock:
            if not self.samples:
                return {
                    "count": 0,
                    "avg_ms": 0.0,
                    "p50_ms": 0.0,
                    "p95_ms": 0.0,
                    "p99_ms": 0.0,
                    "max_ms": 0.0,
                    "min_ms": 0.0
                }
            
            sorted_samples = sorted(self.samples)
            count = len(sorted_samples)
            
            return {
                "count": count,
                "avg_ms": round(statistics.mean(sorted_samples), 2),
                "p50_ms": round(sorted_samples[int(count * 0.50)] if count > 0 else 0.0, 2),
                "p95_ms": round(sorted_samples[int(count * 0.95)] if count > 0 else 0.0, 2),
                "p99_ms": round(sorted_samples[int(count * 0.99)] if count > 0 else 0.0, 2),
                "max_ms": round(max(sorted_samples), 2),
                "min_ms": round(min(sorted_samples), 2)
            }


class Profiler:
    """Global profiler instance"""
    
    def __init__(self):
        self.stats: Dict[str, ProfileStats] = {}
        self.lock = threading.Lock()
        self.enabled = True
    
    def record(self, label: str, latency_ms: float):
        """Record a timing measurement"""
        if not self.enabled:
            return
        
        with self.lock:
            if label not in self.stats:
                self.stats[label] = ProfileStats(label)
        
        self.stats[label].record(latency_ms)
    
    def get_report(self) -> Dict[str, Any]:
        """Generate full profiling report"""
        report = {}
        
        with self.lock:
            for label, stat_obj in self.stats.items():
                report[label] = stat_obj.get_stats()
        
        # Group by category for better readability
        categorized = {
            "io": {},
            "compute": {},
            "dashboard": {},
            "api": {},
            "other": {}
        }
        
        for label, stats in report.items():
            if "search" in label or "qdrant" in label or "db" in label:
                categorized["io"][label] = stats
            elif "tuner" in label or "judge" in label or "aggregate" in label:
                categorized["compute"][label] = stats
            elif "dashboard" in label or "build" in label:
                categorized["dashboard"][label] = stats
            elif "api" in label or "endpoint" in label:
                categorized["api"][label] = stats
            else:
                categorized["other"][label] = stats
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_labels": len(report),
            "by_category": categorized,
            "raw": report
        }
    
    def reset(self):
        """Clear all stats"""
        with self.lock:
            self.stats.clear()
    
    def disable(self):
        """Disable profiling"""
        self.enabled = False
    
    def enable(self):
        """Enable profiling"""
        self.enabled = True


# Global profiler instance
_profiler = Profiler()


def profiled(label: str):
    """
    Decorator to profile a function's execution time
    
    Args:
        label: Identifier for this operation (e.g. "tuner.loop", "dashboard.build")
    
    Example:
        @profiled("search.query")
        def search(q):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                latency_ms = (time.perf_counter() - t0) * 1000
                _profiler.record(label, latency_ms)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                latency_ms = (time.perf_counter() - t0) * 1000
                _profiler.record(label, latency_ms)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_profile_report() -> Dict[str, Any]:
    """Get current profiling report"""
    return _profiler.get_report()


def reset_profiler():
    """Reset profiler stats"""
    _profiler.reset()


def disable_profiler():
    """Disable profiling"""
    _profiler.disable()


def enable_profiler():
    """Enable profiling"""
    _profiler.enable()


# Context manager for manual timing
class ProfileContext:
    """Context manager for profiling code blocks"""
    
    def __init__(self, label: str):
        self.label = label
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            latency_ms = (time.perf_counter() - self.start_time) * 1000
            _profiler.record(self.label, latency_ms)
        return False


def profile(label: str) -> ProfileContext:
    """
    Context manager for profiling code blocks (legacy, use prof() instead)
    
    Example:
        with profile("custom.operation"):
            do_something()
    """
    return ProfileContext(label)


# Global flag for profiler availability
PROFILER_ENABLED = True


def prof(label: str):
    """
    Stable context factory: returns ProfileContext when enabled, nullcontext when disabled.
    This prevents "NoneType is not callable" errors when profiler is disabled.
    
    Usage:
        with prof("api.search.pipeline"):
            result = do_search()
    
    Args:
        label: Identifier for this operation (e.g. "tuner.loop", "dashboard.build")
    
    Returns:
        ProfileContext if PROFILER_ENABLED, else nullcontext (no-op)
    """
    if PROFILER_ENABLED and _profiler.enabled:
        return ProfileContext(label)
    return nullcontext()


# Alias for backward compatibility (but prefer prof() in new code)
profile_ctx = prof


