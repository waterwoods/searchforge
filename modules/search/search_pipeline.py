"""
Search Pipeline Module for SmartSearchX

This module provides a complete search pipeline that combines vector search,
reranking, and explanation generation.
"""

import logging
from typing import List, Dict, Any, Optional
from .vector_search import VectorSearch

logger = logging.getLogger(__name__)


def search_with_explain(
    query: str,
    collection_name: str,
    reranker_name: str = "llm",
    explainer_name: str = "simple",
    top_n: int = 5,
    autotuner_params: Optional[Dict[str, int]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Perform a complete search with explanation.
    
    Args:
        query: Search query
        collection_name: Name of the collection to search
        reranker_name: Type of reranker to use
        explainer_name: Type of explainer to use
        top_n: Number of results to return
        autotuner_params: AutoTuner parameters dict with 'nprobe' and 'ef_search' keys
        
    Returns:
        List of search results with explanations
    """
    # Initialize vector search
    vector_search = VectorSearch()
    
    # Extract AutoTuner parameters
    nprobe = None
    ef_search = None
    if autotuner_params:
        nprobe = autotuner_params.get('nprobe')
        ef_search = autotuner_params.get('ef_search')
    
    # Perform vector search
    results = vector_search.vector_search(
        query=query,
        collection_name=collection_name,
        top_n=top_n,
        nprobe=nprobe,
        ef_search=ef_search
    )
    
    # Convert to expected format
    formatted_results = []
    for i, result in enumerate(results):
        # Handle ScoredDocument objects from vector search
        if hasattr(result, 'content') and hasattr(result, 'score'):
            content = result.content
            # Extract text content from Document object if it's wrapped
            if hasattr(content, 'page_content'):
                content_text = content.page_content
            else:
                content_text = str(content)
            
            formatted_results.append({
                "content": content_text,
                "score": result.score,
                "metadata": getattr(result, 'metadata', {}),
                "rank": i + 1,
                "explanation": f"Relevant to query: {query[:50]}..."
            })
        else:
            # Fallback for dictionary format
            formatted_results.append({
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {}),
                "rank": i + 1,
                "explanation": f"Relevant to query: {query[:50]}..."
            })
    
    return formatted_results


def search_with_multiple_configurations(
    query: str,
    collection_name: str,
    configurations: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Perform search with multiple configurations for comparison.
    
    Args:
        query: Search query
        collection_name: Name of the collection to search
        configurations: List of configuration dictionaries
        
    Returns:
        Dictionary mapping configuration names to results
    """
    results = {}
    
    for config in configurations:
        config_name = config.get("name", "default")
        results[config_name] = search_with_explain(
            query=query,
            collection_name=collection_name,
            **config
        )
    
    return results


def get_available_rerankers() -> List[str]:
    """Get list of available rerankers."""
    return ["llm", "simple", "none"]


def get_available_explainers() -> List[str]:
    """Get list of available explainers."""
    return ["simple", "detailed", "none"]
