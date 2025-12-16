"""
ops_rag_retriever.py - Ops Knowledge Base RAG Retriever
=========================================================
Provides vector search interface for Ops knowledge base.

This module:
- Queries ops_kb collection using VectorSearch
- Constructs queries from service_name and symptom
- Returns relevant knowledge snippets with metadata
- Gracefully degrades if index/Qdrant unavailable
"""

import logging
from typing import List, Dict, Any, Optional

from modules.search.vector_search import VectorSearch

logger = logging.getLogger("ops_copilot.rag_retriever")

# Default collection name
_DEFAULT_COLLECTION = "ops_kb"

# Global vector search instance (lazy initialization)
_vector_search: Optional[VectorSearch] = None


def _get_vector_search() -> Optional[VectorSearch]:
    """
    Get or initialize VectorSearch instance (singleton pattern).
    
    Returns:
        VectorSearch instance or None if initialization fails
    """
    global _vector_search
    
    if _vector_search is not None:
        return _vector_search
    
    try:
        _vector_search = VectorSearch()
        return _vector_search
    except Exception as e:
        logger.warning(f"Failed to initialize VectorSearch: {e}")
        return None


def retrieve_ops_knowledge(
    service_name: str,
    symptom: Optional[str] = None,
    top_k: int = 5,
    collection_name: str = _DEFAULT_COLLECTION,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant knowledge snippets from Ops knowledge base.
    
    This function:
    1. Constructs a query string from service_name and symptom
    2. Performs vector search on ops_kb collection
    3. Returns top_k results with metadata
    
    Args:
        service_name: Service name (e.g., "payment-service", "api-gateway")
        symptom: Optional symptom identifier (e.g., "high_error_rate", "high_latency")
        top_k: Number of results to return (default: 5)
        collection_name: Qdrant collection name (default: "ops_kb")
    
    Returns:
        List of dictionaries, each containing:
        - text: Chunk text content
        - score: Similarity score (0-1)
        - source_file: Source markdown file (e.g., "runbooks.md")
        - service_hint: Extracted service hint from chunk
        - symptom_hint: Extracted symptom hint from chunk
    
    Example:
        >>> results = retrieve_ops_knowledge("payment-service", "high_error_rate", top_k=3)
        >>> for r in results:
        >>>     print(f"Score: {r['score']:.3f}, Source: {r['source_file']}")
        >>>     print(r['text'][:100])
    """
    # Initialize vector search
    vector_search = _get_vector_search()
    if vector_search is None:
        logger.warning("VectorSearch not available, returning empty results")
        return []
    
    # Check if collection exists
    try:
        collections = vector_search.list_collections()
        if collection_name not in collections:
            logger.warning(f"Collection '{collection_name}' not found. Available: {collections}")
            return []
    except Exception as e:
        logger.warning(f"Failed to check collections: {e}")
        return []
    
    # Construct query string
    if symptom:
        # Combine service and symptom for better matching
        query = f"{service_name} {symptom}"
    else:
        query = service_name
    
    logger.debug(f"Querying ops_kb: service={service_name}, symptom={symptom}, query='{query}'")
    
    # Perform vector search
    try:
        scored_docs = vector_search.vector_search(
            query=query,
            collection_name=collection_name,
            top_n=top_k,
        )
    except Exception as e:
        logger.warning(f"Vector search failed: {e}, returning empty results")
        return []
    
    # Format results
    results = []
    for scored_doc in scored_docs:
        doc = scored_doc.document
        metadata = doc.metadata or {}
        
        result = {
            "text": doc.text,
            "score": scored_doc.score,
            "source_file": metadata.get("source_file", "unknown"),
            "service_hint": metadata.get("service_hint"),
            "symptom_hint": metadata.get("symptom_hint"),
        }
        results.append(result)
    
    logger.info(f"Retrieved {len(results)} results for service={service_name}, symptom={symptom}")
    
    return results


__all__ = ["retrieve_ops_knowledge"]

