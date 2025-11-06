"""
Cost estimator for routing decisions.

Estimates cost/latency for different backends.
"""

from typing import Dict, Any


class CostEstimator:
    """
    Cost estimator for backend routing.
    
    Estimates relative cost and latency for FAISS vs Qdrant.
    """
    
    def __init__(
        self,
        faiss_cost_per_query: float = 1.0,
        qdrant_cost_per_query: float = 2.0,
        faiss_avg_latency_ms: float = 10.0,
        qdrant_avg_latency_ms: float = 50.0
    ):
        self.faiss_cost_per_query = faiss_cost_per_query
        self.qdrant_cost_per_query = qdrant_cost_per_query
        self.faiss_avg_latency_ms = faiss_avg_latency_ms
        self.qdrant_avg_latency_ms = qdrant_avg_latency_ms
    
    def estimate(self, backend: str, topk: int) -> Dict[str, Any]:
        """
        Estimate cost and latency for a query.
        
        Args:
            backend: "faiss" or "qdrant"
            topk: Number of results
        
        Returns:
            Dict with cost and latency estimates
        """
        if backend == "faiss":
            # FAISS cost scales sub-linearly with topk
            cost = self.faiss_cost_per_query * (1 + (topk / 100))
            latency_ms = self.faiss_avg_latency_ms * (1 + (topk / 200))
        else:
            # Qdrant cost scales more linearly
            cost = self.qdrant_cost_per_query * (1 + (topk / 50))
            latency_ms = self.qdrant_avg_latency_ms * (1 + (topk / 100))
        
        return {
            "backend": backend,
            "estimated_cost": cost,
            "estimated_latency_ms": latency_ms,
            "topk": topk
        }
    
    def compare(self, topk: int) -> Dict[str, Any]:
        """
        Compare cost and latency for FAISS vs Qdrant.
        
        Args:
            topk: Number of results
        
        Returns:
            Dict with comparison data
        """
        faiss_est = self.estimate("faiss", topk)
        qdrant_est = self.estimate("qdrant", topk)
        
        cost_savings_pct = (
            (qdrant_est["estimated_cost"] - faiss_est["estimated_cost"]) /
            qdrant_est["estimated_cost"] * 100
        )
        
        latency_savings_pct = (
            (qdrant_est["estimated_latency_ms"] - faiss_est["estimated_latency_ms"]) /
            qdrant_est["estimated_latency_ms"] * 100
        )
        
        return {
            "faiss": faiss_est,
            "qdrant": qdrant_est,
            "cost_savings_pct": cost_savings_pct,
            "latency_savings_pct": latency_savings_pct,
            "recommended": "faiss" if cost_savings_pct > 0 else "qdrant"
        }

