"""
Vector Engine Abstraction Layer

Provides unified interface for different vector backends:
- FAISS (default, in-memory)
- Qdrant (production, persistent)
- Milvus (second lane, high-performance)
"""

# Optional import for MilvusEngine to avoid requiring sentence-transformers in API
try:
    from .milvus_engine import MilvusEngine
    MILVUS_ENGINE_AVAILABLE = True
except ImportError:
    MilvusEngine = None
    MILVUS_ENGINE_AVAILABLE = False

from .factory import VectorEngineRouter, get_router

__all__ = ["MilvusEngine", "VectorEngineRouter", "get_router", "MILVUS_ENGINE_AVAILABLE"]

