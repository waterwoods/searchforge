# NOTE: Standardized on Document.text.
"""
Vector Search Module for SmartSearchX

This module provides vector search functionality using Qdrant as the backend.
It handles query embedding, vector similarity search, and result formatting.
"""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import numpy as np

from modules.types import Document, ScoredDocument

logger = logging.getLogger(__name__)


class VectorSearch:
    """
    Vector search implementation using Qdrant and SentenceTransformers.
    
    This class provides a simple interface for performing vector similarity
    search on document collections stored in Qdrant.
    """
    
    def __init__(
        self, 
        host: str = None, 
        port: int = None,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize the vector search service.
        
        Args:
            host: Qdrant server host (defaults to QDRANT_HOST env var or localhost)
            port: Qdrant server port (defaults to QDRANT_PORT env var or 6333)
            embedding_model_name: Name of the SentenceTransformer model to use
        """
        import os
        host = host or os.environ.get("QDRANT_HOST", "localhost")
        port = port or int(os.environ.get("QDRANT_PORT", "6333"))
        self.client = QdrantClient(host=host, port=port)
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
    def vector_search(
        self, 
        query: str, 
        collection_name: str, 
        top_n: int = 5,
        nprobe: Optional[int] = None,
        ef_search: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        debug_mode: bool = False
    ) -> Any:
        """
        Perform vector similarity search on a Qdrant collection.
        If debug_mode is True, returns (scored_documents, debug_info).
        
        Args:
            query: The search query string
            collection_name: Name of the Qdrant collection to search
            top_n: Number of top results to return
            nprobe: Number of clusters to search (for IVF index). Higher values increase recall but latency.
            ef_search: Size of dynamic candidate list (for HNSW index). Higher values increase recall but latency.
            metadata_filter: Optional metadata filter for the search
            debug_mode: If True, returns debug information
            
        Returns:
            List of ScoredDocument objects containing the search results
            or a tuple (scored_documents, debug_info) if debug_mode is True
            
        Raises:
            ValueError: If collection doesn't exist or search fails
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                raise ValueError(f"Collection '{collection_name}' not found. Available collections: {collection_names}")
            
            # Generate query embedding
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Prepare search parameters
            search_limit = max(top_n, 100) if debug_mode else top_n
            search_params = {
                "collection_name": collection_name,
                "query_vector": query_vector,
                "limit": search_limit,
                "with_payload": True
            }
            
            # Add AutoTuner parameters if provided
            # Note: Use HNSW parameters - both nprobe and ef_search map to hnsw_ef
            from qdrant_client.http.models import SearchParams
            
            search_params_obj = None
            if nprobe is not None or ef_search is not None:
                search_params_obj = SearchParams()
                
                # Map both nprobe and ef_search to hnsw_ef (HNSW search parameter)
                if ef_search is not None:
                    search_params_obj.hnsw_ef = ef_search
                elif nprobe is not None:
                    search_params_obj.hnsw_ef = nprobe
                
                # Add exact search parameter (False = approximate, True = exact)
                # For AutoTuner, we typically want approximate search for performance
                search_params_obj.exact = False
            
            if search_params_obj:
                search_params["search_params"] = search_params_obj
            
            # Add metadata filter if provided
            if metadata_filter:
                search_params["query_filter"] = metadata_filter
            
            # Perform search
            results = self.client.search(**search_params)
            
            # Convert to ScoredDocument format
            scored_documents = []
            all_scores = []
            for result in results:
                all_scores.append(result.score)
                payload = result.payload or {}
                content = payload.get("text", "")
                if not content:
                    # Fallback to other common field names
                    content = payload.get("content", "")
                    if not content:
                        content = str(payload)
                
                # Create Document object
                document = Document(
                    id=str(result.id),
                    text=content,
                    metadata={
                        "score": result.score,
                        **payload
                    }
                )
                
                # Create ScoredDocument
                scored_doc = ScoredDocument(
                    document=document,
                    score=result.score,
                    explanation=f"Vector similarity score: {result.score:.4f}"
                )
                scored_documents.append(scored_doc)
            
            logger.info(f"Found {len(scored_documents)} results for query: '{query}'")
            if debug_mode:
                arr = np.array(all_scores)
                debug_info = {
                    "all_scores": all_scores,
                    "min": float(np.min(arr)) if arr.size > 0 else None,
                    "max": float(np.max(arr)) if arr.size > 0 else None,
                    "mean": float(np.mean(arr)) if arr.size > 0 else None,
                    "median": float(np.median(arr)) if arr.size > 0 else None,
                    "std": float(np.std(arr)) if arr.size > 0 else None,
                    "raw_results": results
                }
                logger.info(f"Similarity stats: min={debug_info['min']}, max={debug_info['max']}, mean={debug_info['mean']}, median={debug_info['median']}, std={debug_info['std']}")
                return scored_documents[:top_n], debug_info
            return scored_documents
            
        except Exception as e:
            logger.error(f"Vector search failed for query '{query}' in collection '{collection_name}': {str(e)}")
            raise ValueError(f"Search failed: {str(e)}")
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a Qdrant collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary containing collection information
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                "name": getattr(collection_info, 'name', collection_name),
                "vectors_count": getattr(collection_info, 'vectors_count', 0),
                "points_count": getattr(collection_info, 'points_count', 0),
                "segments_count": getattr(collection_info, 'segments_count', 0),
                "config": getattr(collection_info, 'config', {})
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for '{collection_name}': {str(e)}")
            return {}
    
    def list_collections(self) -> List[str]:
        """
        List all available collections.
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            return []
    
    def get_unique_metadata_values(self, collection_name: str, field_name: str) -> List[str]:
        """
        Get unique values for a specific metadata field in a collection.
        
        Args:
            collection_name: Name of the collection
            field_name: Name of the metadata field (e.g., 'source_type')
            
        Returns:
            List of unique values for the specified field
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                logger.warning(f"Collection '{collection_name}' not found")
                return []
            
            # Get collection info to check if it has data
            collection_info = self.client.get_collection(collection_name)
            if collection_info.points_count == 0:
                logger.info(f"Collection '{collection_name}' is empty")
                return []
            
            # Scan the collection to get all unique values for the field
            # We'll use a simple approach: get a sample of points and extract unique values
            # For large collections, this might need to be optimized
            
            # Get all points (with a reasonable limit to avoid memory issues)
            points_count = collection_info.points_count or 0
            limit = min(10000, points_count)  # Limit to 10k points for performance
            
            results = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True
            )
            
            unique_values = set()
            for point in results[0]:  # results[0] contains the points
                payload = point.payload or {}
                if field_name in payload:
                    value = payload[field_name]
                    if value is not None and str(value).strip():
                        unique_values.add(str(value))
            
            # Convert to sorted list
            unique_values_list = sorted(list(unique_values))
            logger.info(f"Found {len(unique_values_list)} unique values for field '{field_name}' in collection '{collection_name}': {unique_values_list}")
            
            return unique_values_list
            
        except Exception as e:
            logger.error(f"Failed to get unique metadata values for field '{field_name}' in collection '{collection_name}': {str(e)}")
            return []


# Convenience function for direct use
def vector_search(
    query: str, 
    collection_name: str, 
    top_n: int = 5,
    metadata_filter: Optional[Dict[str, Any]] = None,
    host: str = "localhost",
    port: int = 6333,
    debug_mode: bool = False
) -> Any:
    """
    Convenience function for performing vector search.
    If debug_mode is True, returns (scored_documents, debug_info).
    
    Args:
        query: The search query string
        collection_name: Name of the Qdrant collection to search
        top_n: Number of top results to return
        metadata_filter: Optional metadata filter for the search
        host: Qdrant server host
        port: Qdrant server port
        debug_mode: If True, returns debug information
        
    Returns:
        List of ScoredDocument objects containing the search results
        or a tuple (scored_documents, debug_info) if debug_mode is True
    """
    searcher = VectorSearch(host=host, port=port)
    return searcher.vector_search(
        query=query,
        collection_name=collection_name,
        top_n=top_n,
        metadata_filter=metadata_filter,
        debug_mode=debug_mode
    ) 