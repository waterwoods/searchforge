"""
SmartSearchX Search Module

This module provides a complete search pipeline that combines:
- Vector search using Qdrant
- Document reranking with various rerankers
- Explanation generation with different explainers
"""

from .vector_search import VectorSearch, vector_search
from .search_pipeline import (
    search_with_explain,
    search_with_multiple_configurations,
    get_available_rerankers,
    get_available_explainers
)

__all__ = [
    "VectorSearch",
    "vector_search",
    "search_with_explain",
    "search_with_multiple_configurations",
    "get_available_rerankers",
    "get_available_explainers"
] 