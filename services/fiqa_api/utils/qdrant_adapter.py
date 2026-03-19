"""
Qdrant API Adapter - Compatibility layer for different qdrant-client versions.

Handles API differences between qdrant-client versions:
- Newer versions (>=1.7.0): use query_points()
- Older versions: use search() or search_points()
"""

import logging
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


def qdrant_search(
    client,
    collection_name: str,
    query_vector: Union[List[float], List[List[float]]],
    limit: int = 10,
    with_payload: bool = True,
    score_threshold: Optional[float] = None,
    query_filter: Optional[Any] = None,
) -> List[Any]:
    """
    Unified Qdrant search adapter that works with different qdrant-client versions.
    
    Args:
        client: QdrantClient instance
        collection_name: Collection name to search
        query_vector: Query vector (1D list or 2D list)
        limit: Number of results to return
        with_payload: Whether to include payloads
        score_threshold: Minimum score threshold
        query_filter: Optional filter object
        
    Returns:
        List of search results (ScoredPoint objects or similar)
    """
    # Ensure query_vector is a list (not numpy array)
    if hasattr(query_vector, 'tolist'):
        query_vector = query_vector.tolist()
    
    # Try modern API first (query_points - qdrant-client >= 1.7.0)
    if hasattr(client, 'query_points'):
        try:
            # query_points API accepts raw vector directly as "query" parameter
            query_kwargs = {
                "collection_name": collection_name,
                "query": query_vector,  # Raw vector list
                "limit": limit,
                "with_payload": with_payload,
            }
            if score_threshold is not None:
                query_kwargs["score_threshold"] = score_threshold
            if query_filter is not None:
                query_kwargs["filter"] = query_filter  # Note: parameter name is "filter" not "query_filter"
            
            result = client.query_points(**query_kwargs)
            # query_points returns a QueryResponse object with .points attribute
            if hasattr(result, 'points'):
                return list(result.points)
            elif hasattr(result, 'result'):
                return list(result.result) if result.result else []
            elif isinstance(result, list):
                return result
            else:
                # Try to convert to list
                return list(result) if result else []
        except Exception as e:
            # Log the error for debugging
            error_str = str(e)
            logger.warning(f"[QDRANT_ADAPTER] query_points failed: {type(e).__name__}: {e}")
            # If it's a 404 (collection not found) or other HTTP error, don't fallback - re-raise
            if "404" in error_str or "Not Found" in error_str or "collection" in error_str.lower():
                logger.error(f"[QDRANT_ADAPTER] query_points failed with collection/HTTP error: {e}")
                raise
            # For other errors, try fallback (don't re-raise yet)
            logger.warning(f"[QDRANT_ADAPTER] query_points raised exception, trying fallback")
    
    # Fallback to search_points (intermediate API)
    if hasattr(client, 'search_points'):
        try:
            search_kwargs = {
                "collection_name": collection_name,
                "query_vector": query_vector,
                "limit": limit,
                "with_payload": with_payload,
            }
            if score_threshold is not None:
                search_kwargs["score_threshold"] = score_threshold
            if query_filter is not None:
                search_kwargs["query_filter"] = query_filter
            
            return client.search_points(**search_kwargs)
        except AttributeError:
            logger.debug("[QDRANT_ADAPTER] search_points failed, trying legacy search")
        except Exception as e:
            logger.warning(f"[QDRANT_ADAPTER] search_points raised exception: {e}, trying legacy search")
    
    # Fallback to legacy search() API
    if hasattr(client, 'search'):
        try:
            search_kwargs = {
                "collection_name": collection_name,
                "query_vector": query_vector,
                "limit": limit,
            }
            if query_filter is not None:
                search_kwargs["query_filter"] = query_filter
            
            return client.search(**search_kwargs)
        except AttributeError:
            raise AttributeError(
                f"QdrantClient has no search method. Available methods: {[m for m in dir(client) if not m.startswith('_')]}"
            )
    
    # If we get here, none of the methods exist
    raise AttributeError(
        f"QdrantClient has no compatible search method. "
        f"Available methods: {[m for m in dir(client) if 'search' in m.lower() or 'query' in m.lower()]}"
    )
