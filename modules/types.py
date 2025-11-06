"""
Type definitions for the search system.

This module contains core data structures used throughout the search pipeline,
including documents, scored results, and query responses.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class Document:
    """
    Represents a document in the search system.
    
    A document is the basic unit of content that can be searched and retrieved.
    It contains the essential information needed for indexing and retrieval.
    """
    id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ScoredDocument:
    """
    Represents a document with its relevance score.
    
    Used to return search results with scoring information, allowing the system
    to rank and explain why certain documents were selected.
    """
    document: Document
    score: float
    explanation: Optional[str] = None


@dataclass
class QueryResult:
    """
    Represents the complete result of a search query.
    
    Contains the original query and a list of scored documents that match
    the search criteria, ordered by relevance.
    """
    query: str
    results: List[ScoredDocument]
