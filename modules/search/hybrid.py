"""
Hybrid Search Module for SmartSearchX

This module provides hybrid fusion functionality that combines vector search
results with BM25/sparse retrieval results.
"""

import logging
from typing import List, Dict, Set
from modules.types import ScoredDocument

logger = logging.getLogger(__name__)


def normalize_scores(scored_docs: List[ScoredDocument]) -> List[ScoredDocument]:
    """
    Normalize scores using min-max normalization.
    
    Args:
        scored_docs: List of ScoredDocument objects
        
    Returns:
        List of ScoredDocument objects with normalized scores
    """
    if not scored_docs:
        return []
    
    scores = [doc.score for doc in scored_docs]
    min_score = min(scores)
    max_score = max(scores)
    
    # Handle case where all scores are the same
    if max_score == min_score:
        normalized_score = 1.0 if max_score > 0 else 0.0
        return [
            ScoredDocument(
                document=doc.document,
                score=normalized_score,
                explanation=doc.explanation
            )
            for doc in scored_docs
        ]
    
    # Min-max normalization: (score - min) / (max - min)
    normalized_docs = []
    for doc in scored_docs:
        normalized_score = (doc.score - min_score) / (max_score - min_score)
        normalized_docs.append(ScoredDocument(
            document=doc.document,
            score=normalized_score,
            explanation=doc.explanation
        ))
    
    return normalized_docs


def fuse(
    vector_hits: List[ScoredDocument], 
    bm25_hits: List[ScoredDocument], 
    alpha: float, 
    top_k: int
) -> List[ScoredDocument]:
    """
    Fuse vector search and BM25 search results using normalized score combination.
    
    Args:
        vector_hits: List of ScoredDocument objects from vector search
        bm25_hits: List of ScoredDocument objects from BM25 search
        alpha: Weight for vector scores (0.0 = pure BM25, 1.0 = pure vector)
        top_k: Number of final results to return
        
    Returns:
        List of ScoredDocument objects with fused scores, sorted by score
    """
    if alpha < 0.0 or alpha > 1.0:
        raise ValueError(f"Alpha must be between 0.0 and 1.0, got {alpha}")
    
    # Normalize scores for both result sets
    norm_vector_hits = normalize_scores(vector_hits)
    norm_bm25_hits = normalize_scores(bm25_hits)
    
    # Create a mapping of document IDs to scores
    doc_scores = {}
    doc_explanations = {}
    
    # Add vector scores
    for scored_doc in norm_vector_hits:
        doc_id = scored_doc.document.id
        doc_scores[doc_id] = alpha * scored_doc.score
        doc_explanations[doc_id] = f"Vector: {scored_doc.score:.3f}"
    
    # Add BM25 scores (combine if document appears in both)
    for scored_doc in norm_bm25_hits:
        doc_id = scored_doc.document.id
        if doc_id in doc_scores:
            # Document appears in both - combine scores
            doc_scores[doc_id] += (1.0 - alpha) * scored_doc.score
            doc_explanations[doc_id] += f", BM25: {scored_doc.score:.3f}"
        else:
            # Document only in BM25 results
            doc_scores[doc_id] = (1.0 - alpha) * scored_doc.score
            doc_explanations[doc_id] = f"BM25: {scored_doc.score:.3f}"
    
    # Create final fused results
    fused_results = []
    for scored_doc in norm_vector_hits + norm_bm25_hits:
        doc_id = scored_doc.document.id
        if doc_id in doc_scores:
            fused_score = doc_scores[doc_id]
            fused_results.append(ScoredDocument(
                document=scored_doc.document,
                score=fused_score,
                explanation=f"Hybrid (α={alpha:.1f}): {doc_explanations[doc_id]}, Final: {fused_score:.3f}"
            ))
            # Remove from dict to avoid duplicates
            del doc_scores[doc_id]
    
    # Sort by fused score (descending) and return top_k
    fused_results.sort(key=lambda x: x.score, reverse=True)
    
    logger.info(f"Fused {len(vector_hits)} vector + {len(bm25_hits)} BM25 results into {len(fused_results)} unique documents")
    
    return fused_results[:top_k]


def get_fusion_stats(
    vector_hits: List[ScoredDocument], 
    bm25_hits: List[ScoredDocument],
    fused_results: List[ScoredDocument]
) -> Dict[str, any]:
    """
    Get statistics about the fusion process.
    
    Args:
        vector_hits: Original vector search results
        bm25_hits: Original BM25 search results  
        fused_results: Final fused results
        
    Returns:
        Dictionary with fusion statistics
    """
    vector_doc_ids = {doc.document.id for doc in vector_hits}
    bm25_doc_ids = {doc.document.id for doc in bm25_hits}
    fused_doc_ids = {doc.document.id for doc in fused_results}
    
    # Calculate overlaps
    vector_bm25_overlap = len(vector_doc_ids & bm25_doc_ids)
    vector_only = len(vector_doc_ids - bm25_doc_ids)
    bm25_only = len(bm25_doc_ids - vector_doc_ids)
    
    return {
        "vector_results": len(vector_hits),
        "bm25_results": len(bm25_hits),
        "fused_results": len(fused_results),
        "vector_bm25_overlap": vector_bm25_overlap,
        "vector_only": vector_only,
        "bm25_only": bm25_only,
        "unique_documents": len(vector_doc_ids | bm25_doc_ids)
    }
