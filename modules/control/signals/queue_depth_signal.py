"""
Queue depth signal for control flow shaping.

Monitors request queue depth and normalizes against capacity.
"""

import asyncio
from .base import Signal


class QueueDepthSignal(Signal):
    """
    Queue depth signal.
    
    Monitors current queue depth and normalizes against max capacity.
    Value > 1.0 indicates queue overflow risk.
    """
    
    def __init__(
        self,
        max_depth: int = 100,
        queue_key: str = "queue:depth"
    ):
        super().__init__("queue_depth")
        self.max_depth = max_depth
        self.queue_key = queue_key
    
    async def read(self) -> float:
        """
        Read current queue depth.
        
        Returns:
            Normalized value (current_depth / max_depth)
        """
        try:
            # Try to get from Redis
            from core.metrics import metrics_sink
            
            if metrics_sink and hasattr(metrics_sink, 'client'):
                # Get current queue depth
                depth_str = metrics_sink.client.get(self.queue_key)
                
                if depth_str:
                    current_depth = int(depth_str)
                    normalized = current_depth / self.max_depth
                    return normalized
            
            # Fallback: return low value (no congestion detected)
            return 0.1
        
        except Exception as e:
            # Re-raise to trigger fail-safe
            raise Exception(f"Failed to read queue depth: {e}")
    
    def get_status(self) -> dict:
        """Get extended status with config."""
        status = super().get_status()
        status.update({
            "max_depth": self.max_depth,
            "queue_key": self.queue_key
        })
        return status

