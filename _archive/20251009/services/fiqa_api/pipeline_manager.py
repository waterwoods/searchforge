"""
Minimal Pipeline Manager - RAG Stub
"""

import time
import random


class PipelineManager:
    """Minimal pipeline manager with simulated RAG calls"""
    
    def __init__(self):
        self.ready = True
    
    def search(self, query: str, top_k: int = 10) -> dict:
        """
        Simulate RAG pipeline search.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            dict with answers, latency_ms, and cache_hit
        """
        # Simulate processing time
        t0 = time.time()
        time.sleep(random.uniform(0.05, 0.15))
        
        # Generate mock answers
        answers = [f"Answer {i+1} for '{query[:30]}...'" for i in range(top_k)]
        
        # Simulate cache hit
        cache_hit = random.choice([True, False])
        
        latency_ms = (time.time() - t0) * 1000
        
        return {
            "answers": answers,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit
        }
