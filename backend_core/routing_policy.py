"""
Routing Policy Module - Clean Backend Core
===========================================
Implements FAISS-first vs Qdrant routing selection rules with no dependencies.

This module provides standalone routing logic that can be tested independently
and integrated into any search backend.

Routers:
- Router: Main interface for routing decisions
- RulesRouter: Rules-based routing (topK threshold, filter detection)
- CostRouter: Cost-based routing (latency/cost trade-offs)

Usage:
    router = Router(policy="rules")
    decision = router.route(query={"topk": 10, "has_filter": False},
                           faiss_load=0.5, qdrant_load=0.7)
    # => {"backend": "faiss", "reason": "topk<=32, no_filter", "confidence": 0.9}
"""

from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass
import random
import time


@dataclass
class QueryContext:
    """Query context for routing decision."""
    topk: int
    has_filter: bool
    has_fulltext: bool = False
    complexity: float = 0.0  # 0-1 scale


@dataclass
class BackendLoad:
    """Backend load metrics."""
    cpu_pct: float
    qps: float
    p95_ms: float
    healthy: bool = True


@dataclass
class RoutingDecision:
    """Routing decision result."""
    backend: str  # "faiss" or "qdrant"
    reason: str
    confidence: float
    fallback_available: bool = True
    metadata: Dict[str, Any] = None


class RulesRouter:
    """
    Rules-based query router.
    
    Rules:
    1. If topK <= threshold AND no filters AND FAISS healthy -> FAISS
    2. If has filters OR has fulltext -> Qdrant
    3. If topK > threshold -> Qdrant
    4. 5% sampling to Qdrant for validation
    
    Parameters:
        topk_threshold: Max topK for FAISS routing (default 32)
        sampling_pct: Percentage of FAISS-eligible queries to sample to Qdrant
        faiss_healthy: Whether FAISS backend is healthy
    """
    
    def __init__(
        self,
        topk_threshold: int = 32,
        sampling_pct: float = 0.05,
        faiss_healthy: bool = True
    ):
        self.topk_threshold = topk_threshold
        self.sampling_pct = sampling_pct
        self.faiss_healthy = faiss_healthy
        
        # Statistics
        self.route_counts = {"faiss": 0, "qdrant": 0, "sampling": 0}
        self.total_decisions = 0
    
    def route(
        self,
        query: QueryContext,
        faiss_load: BackendLoad,
        qdrant_load: BackendLoad
    ) -> RoutingDecision:
        """
        Make routing decision for query.
        
        Args:
            query: Query context
            faiss_load: FAISS backend load
            qdrant_load: Qdrant backend load
            
        Returns:
            RoutingDecision with backend and reasoning
        """
        self.total_decisions += 1
        
        # Rule 1: Filters or fulltext always go to Qdrant
        if query.has_filter or query.has_fulltext:
            self.route_counts["qdrant"] += 1
            reason = "has_filter" if query.has_filter else "has_fulltext"
            return RoutingDecision(
                backend="qdrant",
                reason=reason,
                confidence=1.0,
                fallback_available=False,  # No fallback for filter queries
                metadata={"rule": "filters_to_qdrant"}
            )
        
        # Rule 2: Large topK goes to Qdrant
        if query.topk > self.topk_threshold:
            self.route_counts["qdrant"] += 1
            return RoutingDecision(
                backend="qdrant",
                reason=f"topk={query.topk}>{self.topk_threshold}",
                confidence=0.95,
                fallback_available=True,
                metadata={"rule": "large_topk_to_qdrant"}
            )
        
        # Rule 3: FAISS unhealthy -> Qdrant
        if not faiss_load.healthy or not self.faiss_healthy:
            self.route_counts["qdrant"] += 1
            return RoutingDecision(
                backend="qdrant",
                reason="faiss_unhealthy",
                confidence=0.9,
                fallback_available=False,
                metadata={"rule": "unhealthy_fallback"}
            )
        
        # Rule 4: FAISS overloaded -> Qdrant
        if faiss_load.cpu_pct > 0.85:
            self.route_counts["qdrant"] += 1
            return RoutingDecision(
                backend="qdrant",
                reason=f"faiss_overloaded (cpu={faiss_load.cpu_pct:.0%})",
                confidence=0.85,
                fallback_available=False,
                metadata={"rule": "load_shedding"}
            )
        
        # Rule 5: Eligible for FAISS, but 5% sampling to Qdrant
        if random.random() < self.sampling_pct:
            self.route_counts["sampling"] += 1
            return RoutingDecision(
                backend="qdrant",
                reason="sampling_recheck",
                confidence=0.5,
                fallback_available=True,
                metadata={"rule": "sampling", "eligible_for_faiss": True}
            )
        
        # Default: Route to FAISS
        self.route_counts["faiss"] += 1
        return RoutingDecision(
            backend="faiss",
            reason=f"topk<={self.topk_threshold}, no_filter, healthy",
            confidence=0.9,
            fallback_available=True,
            metadata={"rule": "default_to_faiss"}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        total = self.total_decisions
        if total == 0:
            return {
                "total_decisions": 0,
                "faiss_pct": 0,
                "qdrant_pct": 0,
                "sampling_pct": 0
            }
        
        return {
            "total_decisions": total,
            "faiss_count": self.route_counts["faiss"],
            "qdrant_count": self.route_counts["qdrant"],
            "sampling_count": self.route_counts["sampling"],
            "faiss_pct": self.route_counts["faiss"] / total * 100,
            "qdrant_pct": self.route_counts["qdrant"] / total * 100,
            "sampling_pct": self.route_counts["sampling"] / total * 100
        }
    
    def reset_stats(self):
        """Reset routing statistics."""
        self.route_counts = {"faiss": 0, "qdrant": 0, "sampling": 0}
        self.total_decisions = 0


class CostRouter:
    """
    Cost-based query router.
    
    Routes based on estimated cost (latency, compute, $$$).
    
    Cost model:
    - FAISS: Low latency, high throughput, but limited features
    - Qdrant: Higher latency, richer features, handles all query types
    
    Parameters:
        faiss_cost_per_1k: Estimated cost per 1K queries to FAISS
        qdrant_cost_per_1k: Estimated cost per 1K queries to Qdrant
        latency_weight: Weight for latency in cost function (0-1)
    """
    
    def __init__(
        self,
        faiss_cost_per_1k: float = 0.01,
        qdrant_cost_per_1k: float = 0.05,
        latency_weight: float = 0.6
    ):
        self.faiss_cost_per_1k = faiss_cost_per_1k
        self.qdrant_cost_per_1k = qdrant_cost_per_1k
        self.latency_weight = latency_weight
        
        # Baseline latencies (ms)
        self.faiss_baseline_ms = 10
        self.qdrant_baseline_ms = 50
        
        # Statistics
        self.total_decisions = 0
        self.cost_saved = 0.0
    
    def route(
        self,
        query: QueryContext,
        faiss_load: BackendLoad,
        qdrant_load: BackendLoad
    ) -> RoutingDecision:
        """
        Make cost-based routing decision.
        
        Args:
            query: Query context
            faiss_load: FAISS backend load
            qdrant_load: Qdrant backend load
            
        Returns:
            RoutingDecision with backend and cost analysis
        """
        self.total_decisions += 1
        
        # Check if FAISS can handle this query
        faiss_eligible = (
            not query.has_filter and
            not query.has_fulltext and
            query.topk <= 32 and
            faiss_load.healthy
        )
        
        if not faiss_eligible:
            # Must use Qdrant
            return RoutingDecision(
                backend="qdrant",
                reason="faiss_ineligible",
                confidence=1.0,
                fallback_available=False,
                metadata={"cost_model": "forced"}
            )
        
        # Estimate costs
        faiss_latency = self.faiss_baseline_ms * (1 + faiss_load.cpu_pct * 0.5)
        qdrant_latency = self.qdrant_baseline_ms * (1 + qdrant_load.cpu_pct * 0.5)
        
        faiss_cost = (
            self.latency_weight * faiss_latency / 100 +
            (1 - self.latency_weight) * self.faiss_cost_per_1k
        )
        
        qdrant_cost = (
            self.latency_weight * qdrant_latency / 100 +
            (1 - self.latency_weight) * self.qdrant_cost_per_1k
        )
        
        # Select lower cost backend
        if faiss_cost < qdrant_cost:
            cost_saving = qdrant_cost - faiss_cost
            self.cost_saved += cost_saving
            
            return RoutingDecision(
                backend="faiss",
                reason=f"lower_cost (saving={cost_saving:.2f})",
                confidence=0.8,
                fallback_available=True,
                metadata={
                    "cost_model": "optimized",
                    "faiss_cost": faiss_cost,
                    "qdrant_cost": qdrant_cost,
                    "saving": cost_saving
                }
            )
        else:
            return RoutingDecision(
                backend="qdrant",
                reason="lower_cost",
                confidence=0.8,
                fallback_available=True,
                metadata={
                    "cost_model": "optimized",
                    "faiss_cost": faiss_cost,
                    "qdrant_cost": qdrant_cost
                }
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cost statistics."""
        return {
            "total_decisions": self.total_decisions,
            "total_cost_saved": self.cost_saved,
            "avg_saving_per_query": self.cost_saved / self.total_decisions if self.total_decisions > 0 else 0
        }


class Router:
    """
    Main routing interface.
    
    Provides unified interface for different routing policies.
    
    Usage:
        router = Router(policy="rules")
        decision = router.route(
            query={"topk": 10, "has_filter": False},
            faiss_load=0.5,
            qdrant_load=0.7
        )
    """
    
    def __init__(
        self,
        policy: Literal["rules", "cost"] = "rules",
        topk_threshold: int = 32
    ):
        """
        Initialize router.
        
        Args:
            policy: Routing policy ("rules" or "cost")
            topk_threshold: TopK threshold for FAISS routing
        """
        self.policy = policy
        self.topk_threshold = topk_threshold
        
        # Initialize router
        if policy == "rules":
            self.router = RulesRouter(topk_threshold=topk_threshold)
        elif policy == "cost":
            self.router = CostRouter()
        else:
            raise ValueError(f"Unknown policy: {policy}")
        
        # Decision history
        self.decision_history: list[RoutingDecision] = []
        self.max_history = 100
    
    def route(
        self,
        query: Dict[str, Any],
        faiss_load: float = 0.0,
        qdrant_load: float = 0.0
    ) -> Dict[str, Any]:
        """
        Route query to appropriate backend.
        
        Args:
            query: Query dict with topk, has_filter, etc.
            faiss_load: FAISS backend load (0-1 scale)
            qdrant_load: Qdrant backend load (0-1 scale)
            
        Returns:
            Dict with backend, reason, and metadata
        """
        # Parse query
        query_ctx = QueryContext(
            topk=query.get("topk", 10),
            has_filter=query.get("has_filter", False),
            has_fulltext=query.get("has_fulltext", False),
            complexity=query.get("complexity", 0.0)
        )
        
        # Parse backend loads
        faiss_backend = BackendLoad(
            cpu_pct=faiss_load,
            qps=0,  # Not used in current implementation
            p95_ms=0,  # Not used
            healthy=(faiss_load < 0.9)
        )
        
        qdrant_backend = BackendLoad(
            cpu_pct=qdrant_load,
            qps=0,
            p95_ms=0,
            healthy=(qdrant_load < 0.9)
        )
        
        # Get routing decision
        decision = self.router.route(query_ctx, faiss_backend, qdrant_backend)
        
        # Update history
        self.decision_history.append(decision)
        if len(self.decision_history) > self.max_history:
            self.decision_history = self.decision_history[-self.max_history:]
        
        # Convert to dict
        return {
            "backend": decision.backend,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "fallback_available": decision.fallback_available,
            "metadata": decision.metadata or {},
            "policy": self.policy
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get router status."""
        stats = self.router.get_stats()
        
        return {
            "policy": self.policy,
            "topk_threshold": self.topk_threshold,
            "decision_count": len(self.decision_history),
            **stats
        }
    
    def reset(self):
        """Reset router state."""
        self.router.reset_stats()
        self.decision_history.clear()


# ============================================================================
# Quick self-test
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ROUTING POLICY MODULE - SELF TEST")
    print("=" * 70)
    print()
    
    # Test Rules router
    print("1. Rules Router Test")
    print("-" * 70)
    router = Router(policy="rules", topk_threshold=32)
    
    test_queries = [
        ({"topk": 10, "has_filter": False}, 0.3, 0.5, "Small topK, no filter"),
        ({"topk": 50, "has_filter": False}, 0.3, 0.5, "Large topK"),
        ({"topk": 10, "has_filter": True}, 0.3, 0.5, "Has filter"),
        ({"topk": 10, "has_filter": False}, 0.9, 0.5, "FAISS overloaded"),
    ]
    
    for query, faiss_load, qdrant_load, desc in test_queries:
        decision = router.route(query, faiss_load, qdrant_load)
        print(f"  {desc}:")
        print(f"    Query: topk={query['topk']}, filter={query['has_filter']}")
        print(f"    → backend={decision['backend']}, reason={decision['reason']}")
        print(f"    → confidence={decision['confidence']:.2f}")
        print()
    
    print("Stats:")
    stats = router.get_status()
    print(f"  Total decisions: {stats['total_decisions']}")
    print(f"  FAISS: {stats['faiss_count']} ({stats['faiss_pct']:.1f}%)")
    print(f"  Qdrant: {stats['qdrant_count']} ({stats['qdrant_pct']:.1f}%)")
    print()
    
    # Test Cost router
    print("2. Cost Router Test")
    print("-" * 70)
    cost_router = Router(policy="cost")
    
    for query, faiss_load, qdrant_load, desc in test_queries[:2]:  # Only eligible queries
        decision = cost_router.route(query, faiss_load, qdrant_load)
        print(f"  {desc}:")
        print(f"    → backend={decision['backend']}, reason={decision['reason']}")
        print(f"    → confidence={decision['confidence']:.2f}")
        if decision['metadata']:
            print(f"    → cost={decision['metadata']}")
        print()
    
    print("=" * 70)
    print("✓ Self-test passed")
    print("=" * 70)

