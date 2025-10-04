# NOTE: Standardized on Document.text.
from __future__ import annotations
from typing import List, Optional
from modules.types import Document, ScoredDocument

class FakeReranker:
    """
    A lightweight, deterministic reranker for demos/tests.
    Scoring = overlap_count(query, doc.text) * 10 - abs(len(doc.text) - 120)/120
    Higher is better; ties keep input order.
    """
    def __init__(self, weight: float = 1.0, top_k: Optional[int] = None):
        self.weight = float(weight)
        self.top_k = top_k

    def _score_one(self, query: str, doc: Document) -> float:
        q_tokens = {t.lower() for t in query.split()}
        d_tokens = {t.lower() for t in doc.text.split()}
        overlap = len(q_tokens & d_tokens)
        length_bonus = 1.0 - abs(len(doc.text) - 120) / 120.0
        return self.weight * (overlap * 10.0 + length_bonus)

    def rerank(self, query: str, documents: List[Document]) -> List[ScoredDocument]:
        # Guard rails: ensure all documents have text
        assert all(getattr(d, "text", "") for d in documents), "Reranker received empty text"
        
        scored = [
            ScoredDocument(
                document=d,
                score=self._score_one(query, d),
                explanation="fake_reranker: overlap & length heuristic"
            )
            for d in documents
        ]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[: self.top_k] if self.top_k else scored
