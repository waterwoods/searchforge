"""
Base classes for document reranking.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ScoredDocument:
    """A document with a relevance score."""
    content: str
    score: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseReranker:
    """Base class for document rerankers."""
    
    def rerank(self, query: str, documents: List[ScoredDocument]) -> List[ScoredDocument]:
        """Rerank documents based on query relevance."""
        raise NotImplementedError
