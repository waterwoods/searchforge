"""
Routing plugin for app_main integration.

Manages query routing between FAISS and Qdrant.
Provides runtime flag control and health monitoring.
"""

import logging
from typing import Dict, Any, Optional

from modules.routing import QueryRouter, CostEstimator

logger = logging.getLogger(__name__)


class RoutingPlugin:
    """
    Routing plugin for intelligent backend selection.
    
    Routes queries between FAISS and Qdrant based on rules and health.
    """
    
    def __init__(self):
        self.router = QueryRouter()
        self.cost_estimator = CostEstimator()
        
        # Configuration
        self.enabled = True
        self.policy = "rules"  # "rules" or "manual"
        self.manual_backend = None
    
    async def route(
        self,
        topk: int,
        has_filter: bool = False
    ) -> Dict[str, Any]:
        """
        Route a query to appropriate backend.
        
        Args:
            topk: Number of results requested
            has_filter: Whether query has metadata filters
        
        Returns:
            Routing decision with backend and metadata
        """
        if not self.enabled:
            return {
                "backend": "qdrant",
                "reason": "routing_disabled"
            }
        
        if self.policy == "manual" and self.manual_backend:
            return {
                "backend": self.manual_backend,
                "reason": "manual_override"
            }
        
        # Use rules-based routing
        return await self.router.route(topk, has_filter)
    
    async def set_flags(self, flags: Dict[str, Any]) -> Dict[str, Any]:
        """Update routing flags."""
        changes = []
        
        if "enabled" in flags:
            self.enabled = bool(flags["enabled"])
            changes.append(f"enabled={self.enabled}")
        
        if "policy" in flags:
            self.policy = flags["policy"]
            changes.append(f"policy={self.policy}")
        
        if "faiss" in flags:
            # Set FAISS health status
            self.router.set_faiss_health(bool(flags["faiss"]))
            changes.append(f"faiss_healthy={flags['faiss']}")
        
        if "manual_backend" in flags:
            self.manual_backend = flags["manual_backend"]
            changes.append(f"manual_backend={self.manual_backend}")
        
        return {
            "ok": True,
            "changes": changes
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get routing plugin status."""
        return {
            "enabled": self.enabled,
            "policy": self.policy,
            "manual_backend": self.manual_backend,
            "router": self.router.get_status()
        }
    
    def get_cost_comparison(self, topk: int) -> Dict[str, Any]:
        """Get cost comparison for a query."""
        return self.cost_estimator.compare(topk)


# Global instance
_routing_plugin: Optional[RoutingPlugin] = None


def get_routing_plugin() -> RoutingPlugin:
    """Get or create routing plugin instance."""
    global _routing_plugin
    if _routing_plugin is None:
        _routing_plugin = RoutingPlugin()
    return _routing_plugin

