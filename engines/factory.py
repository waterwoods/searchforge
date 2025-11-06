#!/usr/bin/env python3
"""
Vector Engine Factory

Creates appropriate vector engine based on VECTOR_BACKEND environment variable.
Supports:
- faiss: In-memory FAISS (default, fallback)
- qdrant: Qdrant vector database  
- milvus: Milvus vector database (second lane)

Routing Policy:
- If VECTOR_BACKEND=milvus, use Milvus for all queries
- If top_k <= 32, prefer Milvus (low-latency lane)
- On Milvus failure, fallback to Qdrant
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class VectorEngineRouter:
    """
    Routes vector search requests to appropriate backend.
    
    Features:
    - Environment-based backend selection
    - Automatic fallback on errors
    - Shadow query support for A/B testing
    - Metrics collection for routing decisions
    """
    
    def __init__(self):
        """Initialize router with configured backends."""
        self.backend = os.getenv("VECTOR_BACKEND", "faiss").lower()
        self.milvus_shadow_pct = float(os.getenv("MILVUS_SHADOW_PCT", "0.1"))  # 10% shadow queries
        self.topk_threshold = int(os.getenv("MILVUS_TOPK_THRESHOLD", "32"))
        
        # ✅ FAISS disable switch
        self.faiss_disabled = os.getenv("DISABLE_FAISS", "false").lower() == "true"
        if self.faiss_disabled:
            logger.info("[FAISS] DISABLED via DISABLE_FAISS=true")
            # If FAISS was default backend and disabled, switch to Qdrant
            if self.backend == "faiss":
                self.backend = "qdrant"
                logger.info("[FAISS] Backend switched from faiss to qdrant")
        
        # Initialize engines
        self._milvus_engine = None
        self._qdrant_engine = None
        self._faiss_engine = None
        
        # Routing metrics
        self.routing_stats = {
            "milvus_count": 0,
            "qdrant_count": 0,
            "faiss_count": 0,
            "milvus_errors": 0,
            "fallback_count": 0
        }
        
        logger.info(f"VectorEngineRouter initialized: backend={self.backend}, "
                   f"faiss_disabled={self.faiss_disabled}, shadow_pct={self.milvus_shadow_pct}, "
                   f"topk_threshold={self.topk_threshold}")
    
    def get_milvus_engine(self):
        """Lazy-load Milvus engine."""
        if self._milvus_engine is None:
            try:
                from engines.milvus_engine import MilvusEngine
                self._milvus_engine = MilvusEngine()
                self._milvus_engine.connect()
                logger.info("Milvus engine initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Milvus engine: {e}")
                return None
        return self._milvus_engine
    
    def get_qdrant_engine(self):
        """Lazy-load Qdrant engine."""
        if self._qdrant_engine is None:
            try:
                from modules.search.vector_search import VectorSearch
                self._qdrant_engine = VectorSearch()
                logger.info("Qdrant engine initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant engine: {e}")
                return None
        return self._qdrant_engine
    
    def select_backend(
        self,
        top_k: int,
        trace_id: Optional[str] = None,
        force_backend: Optional[str] = None
    ) -> str:
        """
        Select backend based on routing policy.
        
        Policy:
        1. If force_backend specified, use it
        2. If VECTOR_BACKEND=milvus, use Milvus
        3. If top_k <= threshold, prefer Milvus (low-latency)
        4. Otherwise use Qdrant
        
        Args:
            top_k: Number of results requested
            trace_id: Optional trace ID for logging
            force_backend: Force specific backend
        
        Returns:
            Backend name: "milvus", "qdrant", or "faiss"
        """
        # Force backend if specified
        if force_backend:
            return force_backend
        
        # Use configured backend
        if self.backend == "milvus":
            return "milvus"
        
        # Smart routing: small top_k -> Milvus (low latency)
        if top_k <= self.topk_threshold:
            # Shadow query: 10% traffic to Milvus for testing
            import random
            if random.random() < self.milvus_shadow_pct:
                logger.debug(f"Shadow query to Milvus (trace={trace_id}, top_k={top_k})")
                return "milvus"
        
        # Default to configured backend or Qdrant
        return self.backend if self.backend in ["qdrant", "faiss"] else "qdrant"
    
    def search(
        self,
        query: str,
        collection_name: str = "fiqa",
        top_k: int = 10,
        ef_search: Optional[int] = None,
        nprobe: Optional[int] = None,
        force_backend: Optional[str] = None,
        trace_id: Optional[str] = None,
        with_fallback: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute search with automatic backend selection and fallback.
        
        Args:
            query: Search query text
            collection_name: Collection to search
            top_k: Number of results
            ef_search: HNSW search parameter
            nprobe: IVF search parameter (for FAISS)
            force_backend: Force specific backend
            trace_id: Trace ID for logging
            with_fallback: Enable fallback on errors
        
        Returns:
            Tuple of (results, debug_info)
        """
        # Select backend
        backend = self.select_backend(top_k, trace_id, force_backend)
        
        # Track routing decision
        route_header = f"X-Search-Route: {backend}"
        
        # Try primary backend
        results, debug_info = self._search_backend(
            backend, query, collection_name, top_k, ef_search, nprobe
        )
        
        # Update routing stats
        self.routing_stats[f"{backend}_count"] += 1
        
        # Check if search succeeded
        if results or not with_fallback:
            debug_info["routed_to"] = backend
            debug_info["route_header"] = route_header
            return results, debug_info
        
        # Fallback: Try Qdrant if Milvus failed
        if backend == "milvus" and with_fallback:
            logger.warning(f"Milvus search failed, falling back to Qdrant (trace={trace_id})")
            self.routing_stats["milvus_errors"] += 1
            self.routing_stats["fallback_count"] += 1
            
            results, debug_info = self._search_backend(
                "qdrant", query, collection_name, top_k, ef_search, nprobe
            )
            debug_info["routed_to"] = "qdrant"
            debug_info["fallback_from"] = "milvus"
            debug_info["route_header"] = f"X-Search-Route: qdrant (fallback from milvus)"
            
            return results, debug_info
        
        # No results and no fallback
        debug_info["routed_to"] = backend
        debug_info["route_header"] = route_header
        return results, debug_info
    
    def _search_backend(
        self,
        backend: str,
        query: str,
        collection_name: str,
        top_k: int,
        ef_search: Optional[int],
        nprobe: Optional[int]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Execute search on specific backend."""
        try:
            if backend == "milvus":
                engine = self.get_milvus_engine()
                if engine:
                    return engine.search(query, top_k, ef_search, collection_name=collection_name)
                else:
                    return [], {"error": "Milvus engine not available"}
            
            elif backend == "qdrant":
                engine = self.get_qdrant_engine()
                if engine:
                    # Adapt to Qdrant interface
                    results = engine.vector_search(
                        query, collection_name, top_k, 
                        nprobe=nprobe, ef_search=ef_search
                    )
                    # Convert to standard format
                    formatted = []
                    for r in results:
                        # Handle ScoredDocument structure (document.id, document.text, etc.)
                        doc = r.document if hasattr(r, 'document') else r
                        formatted.append({
                            "id": getattr(doc, 'id', getattr(doc, 'doc_id', 'unknown')),
                            "text": getattr(doc, 'text', ''),
                            "score": r.score if hasattr(r, 'score') else 0.0,
                            "metadata": getattr(doc, 'metadata', {})
                        })
                    return formatted, {"backend": "qdrant", "result_count": len(formatted)}
                else:
                    return [], {"error": "Qdrant engine not available"}
            
            else:  # faiss or unknown
                # ✅ Check if FAISS is disabled
                if self.faiss_disabled:
                    logger.info(f"FAISS disabled, using Qdrant instead")
                    return self._search_backend("qdrant", query, collection_name, top_k, ef_search, nprobe)
                
                # FAISS not implemented yet, fallback to Qdrant
                logger.warning(f"Backend '{backend}' not implemented, using Qdrant")
                return self._search_backend("qdrant", query, collection_name, top_k, ef_search, nprobe)
        
        except Exception as e:
            logger.error(f"Search failed on {backend}: {e}")
            return [], {"error": str(e), "backend": backend}
    
    def health(self) -> Dict[str, Any]:
        """Check health of all backends."""
        health = {
            "router": "ok",
            "configured_backend": self.backend,
            "routing_stats": self.routing_stats.copy(),
            "backends": {}
        }
        
        # Check Milvus
        if self.backend == "milvus" or self.milvus_shadow_pct > 0:
            engine = self.get_milvus_engine()
            if engine:
                health["backends"]["milvus"] = engine.health()
            else:
                health["backends"]["milvus"] = {"ok": False, "error": "Engine not initialized"}
        
        # Check Qdrant
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333"))
            )
            collections = client.get_collections()
            health["backends"]["qdrant"] = {
                "ok": True,
                "collections": [c.name for c in collections.collections]
            }
        except Exception as e:
            health["backends"]["qdrant"] = {"ok": False, "error": str(e)}
        
        return health
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing metrics for reporting."""
        total = sum([
            self.routing_stats["milvus_count"],
            self.routing_stats["qdrant_count"],
            self.routing_stats["faiss_count"]
        ])
        
        if total == 0:
            return {
                "total_queries": 0,
                "milvus_share_pct": 0.0,
                "qdrant_share_pct": 0.0,
                "faiss_share_pct": 0.0,
                "milvus_error_rate": 0.0,
                "fallback_rate": 0.0
            }
        
        return {
            "total_queries": total,
            "milvus_share_pct": round(self.routing_stats["milvus_count"] / total * 100, 2),
            "qdrant_share_pct": round(self.routing_stats["qdrant_count"] / total * 100, 2),
            "faiss_share_pct": round(self.routing_stats["faiss_count"] / total * 100, 2),
            "milvus_error_rate": round(
                self.routing_stats["milvus_errors"] / max(1, self.routing_stats["milvus_count"]) * 100, 2
            ),
            "fallback_rate": round(self.routing_stats["fallback_count"] / total * 100, 2)
        }


# Global router instance
_global_router = None

def get_router() -> VectorEngineRouter:
    """Get or create global router instance."""
    global _global_router
    if _global_router is None:
        _global_router = VectorEngineRouter()
    return _global_router

