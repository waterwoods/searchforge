"""
P95 latency signal for control flow shaping.

Monitors p95 latency from metrics store and normalizes to 0-1 range.
"""

import asyncio
from typing import Optional
from .base import Signal


class P95Signal(Signal):
    """
    P95 latency signal.
    
    Reads p95 latency from metrics and normalizes against target.
    Value > 1.0 indicates overload.
    """
    
    def __init__(
        self,
        target_ms: float = 100.0,
        window_secs: int = 60
    ):
        super().__init__("p95")
        self.target_ms = target_ms
        self.window_secs = window_secs
    
    async def read(self) -> float:
        """
        Read current p95 latency.
        
        Returns:
            Normalized value (actual_p95 / target_p95)
        """
        try:
            # Try to get from Redis metrics store
            from core.metrics import metrics_sink
            
            if metrics_sink and hasattr(metrics_sink, 'client'):
                # Get recent latencies from sorted set
                now = asyncio.get_event_loop().time()
                window_start = now - self.window_secs
                
                # Fetch latency samples from last window
                key = "metrics:latencies"
                samples = metrics_sink.client.zrangebyscore(
                    key, 
                    window_start, 
                    now,
                    withscores=False
                )
                
                if samples:
                    # Parse latency values
                    latencies = [float(s) for s in samples]
                    latencies.sort()
                    
                    # Calculate p95
                    p95_idx = int(len(latencies) * 0.95)
                    p95_value = latencies[p95_idx] if p95_idx < len(latencies) else latencies[-1]
                    
                    # Normalize against target
                    normalized = p95_value / self.target_ms
                    return normalized
            
            # Fallback: return neutral value
            return 0.5
        
        except Exception as e:
            # Re-raise to trigger fail-safe
            raise Exception(f"Failed to read p95: {e}")
    
    def get_status(self) -> dict:
        """Get extended status with config."""
        status = super().get_status()
        status.update({
            "target_ms": self.target_ms,
            "window_secs": self.window_secs
        })
        return status

