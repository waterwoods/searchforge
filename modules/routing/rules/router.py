"""
Query router for intelligent backend selection.

Routes queries between FAISS and Qdrant based on:
- Query characteristics (topK <= 32, no filters)
- Backend health status
- 5% sampling re-check to Qdrant
"""

import random
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Intelligent query router.
    
    Rules:
    1. If topK <= 32 AND no filters AND FAISS healthy -> FAISS
    2. Otherwise -> Qdrant
    3. 5% of FAISS-eligible queries sample Qdrant (for validation)
    """
    
    def __init__(
        self,
        topk_threshold: int = 32,
        sampling_pct: float = 0.05,
        faiss_health_check_interval: int = 60
    ):
        self.topk_threshold = topk_threshold
        self.sampling_pct = sampling_pct
        self.faiss_health_check_interval = faiss_health_check_interval
        
        # State
        self.faiss_healthy = True
        self.last_health_check = 0
        self.route_counts = {"faiss": 0, "qdrant": 0, "sampling": 0}
        self.enabled = True
    
    async def route(
        self,
        topk: int,
        has_filter: bool,
        force_backend: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route query to appropriate backend.
        
        Args:
            topk: Number of results requested
            has_filter: Whether query has metadata filters
            force_backend: Override backend selection (for testing)
        
        Returns:
            Dict with backend, reason, and metadata
        """
        if not self.enabled:
            return {
                "backend": "qdrant",
                "reason": "routing_disabled",
                "topk": topk,
                "has_filter": has_filter
            }
        
        # Force override
        if force_backend:
            return {
                "backend": force_backend,
                "reason": "forced_override",
                "topk": topk,
                "has_filter": has_filter
            }
        
        # Check FAISS health periodically
        await self._check_faiss_health()
        
        # Apply routing rules
        if topk <= self.topk_threshold and not has_filter and self.faiss_healthy:
            # Eligible for FAISS
            
            # 5% sampling to Qdrant
            if random.random() < self.sampling_pct:
                self.route_counts["sampling"] += 1
                return {
                    "backend": "qdrant",
                    "reason": "sampling_recheck",
                    "topk": topk,
                    "has_filter": has_filter,
                    "eligible_for_faiss": True
                }
            
            # Route to FAISS
            self.route_counts["faiss"] += 1
            return {
                "backend": "faiss",
                "reason": f"topk<={self.topk_threshold}, no_filter, faiss_healthy",
                "topk": topk,
                "has_filter": has_filter
            }
        
        # Default: route to Qdrant
        self.route_counts["qdrant"] += 1
        
        reasons = []
        if topk > self.topk_threshold:
            reasons.append(f"topk={topk}>{self.topk_threshold}")
        if has_filter:
            reasons.append("has_filter")
        if not self.faiss_healthy:
            reasons.append("faiss_unhealthy")
        
        return {
            "backend": "qdrant",
            "reason": ", ".join(reasons) if reasons else "default",
            "topk": topk,
            "has_filter": has_filter
        }
    
    async def _check_faiss_health(self):
        """Check FAISS backend health."""
        now = time.time()
        
        if (now - self.last_health_check) < self.faiss_health_check_interval:
            return
        
        self.last_health_check = now
        
        try:
            # TODO: Implement actual FAISS health check
            # For now, assume healthy
            self.faiss_healthy = True
            logger.debug("FAISS health check: healthy")
        
        except Exception as e:
            self.faiss_healthy = False
            logger.warning(f"FAISS health check failed: {e}")
    
    def set_faiss_health(self, healthy: bool):
        """Manually set FAISS health status."""
        self.faiss_healthy = healthy
        logger.info(f"FAISS health set to: {healthy}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get router status."""
        total_routes = sum(self.route_counts.values())
        
        return {
            "enabled": self.enabled,
            "faiss_healthy": self.faiss_healthy,
            "topk_threshold": self.topk_threshold,
            "sampling_pct": self.sampling_pct,
            "route_counts": self.route_counts.copy(),
            "total_routes": total_routes,
            "faiss_pct": (self.route_counts["faiss"] / total_routes * 100) if total_routes > 0 else 0,
            "qdrant_pct": (self.route_counts["qdrant"] / total_routes * 100) if total_routes > 0 else 0
        }
    
    def reset_counts(self):
        """Reset route counters."""
        self.route_counts = {"faiss": 0, "qdrant": 0, "sampling": 0}
        logger.info("Router counts reset")

