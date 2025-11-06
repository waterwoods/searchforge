# modules/rerankers/base.py
from __future__ import annotations
from typing import List, Protocol
from modules.types import Document, ScoredDocument

class AbstractReranker(Protocol):
    """
    Minimal, stable interface for all rerankers.
    """
    name: str

    def rerank(self, query: str, docs: List[Document], top_k: int = 50) -> List[ScoredDocument]:
        """
        Given a query and candidate documents, return top_k ScoredDocument.
        Implementations must be pure (no side effects) and stable under errors
        (raise or return original order handled by caller/factory).
        """
        ...