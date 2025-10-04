"""
BM25 Retriever Module for SmartSearchX

This module provides BM25/TF-IDF based text retrieval functionality.
It implements a simple BM25 algorithm for sparse retrieval.
"""

import math
import re
from typing import List, Dict, Set
from collections import defaultdict, Counter
from modules.types import Document, ScoredDocument


class SimpleTFIDF:
    """
    Simple TF-IDF implementation for BM25-style retrieval.
    """
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """
        Initialize TF-IDF with BM25 parameters.
        
        Args:
            k1: Term frequency saturation parameter (typically 1.2-2.0)
            b: Length normalization parameter (typically 0.75)
        """
        self.k1 = k1
        self.b = b
        self.doc_freq = defaultdict(int)  # Document frequency for each term
        self.idf = {}  # Inverse document frequency
        self.doc_lengths = {}  # Document lengths
        self.avg_doc_length = 0.0
        self.total_docs = 0
        self.vocabulary = set()
        
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization - lowercase, alphanumeric only."""
        # Convert to lowercase and extract alphanumeric sequences
        tokens = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
        return tokens
    
    def fit(self, documents: List[Document]) -> None:
        """
        Fit the TF-IDF model on a collection of documents.
        
        Args:
            documents: List of Document objects to index
        """
        self.total_docs = len(documents)
        if self.total_docs == 0:
            return
            
        # First pass: count document frequencies and document lengths
        doc_term_counts = []
        
        for doc in documents:
            tokens = self._tokenize(doc.text)
            self.vocabulary.update(tokens)
            
            # Count term frequencies in this document
            term_counts = Counter(tokens)
            doc_term_counts.append((doc.id, term_counts))
            
            # Track document length
            doc_length = len(tokens)
            self.doc_lengths[doc.id] = doc_length
            
            # Count document frequency for each unique term in this document
            for term in set(tokens):
                self.doc_freq[term] += 1
        
        # Calculate average document length
        self.avg_doc_length = sum(self.doc_lengths.values()) / self.total_docs
        
        # Calculate IDF scores
        for term, df in self.doc_freq.items():
            self.idf[term] = math.log(self.total_docs / df)
        
        # Store term frequencies for scoring
        self.doc_term_counts = dict(doc_term_counts)
    
    def score_document(self, query_terms: List[str], doc_id: str) -> float:
        """
        Calculate BM25 score for a document given query terms.
        
        Args:
            query_terms: List of query terms
            doc_id: Document ID to score
            
        Returns:
            BM25 score for the document
        """
        if doc_id not in self.doc_term_counts:
            return 0.0
            
        doc_term_counts = self.doc_term_counts[doc_id]
        doc_length = self.doc_lengths[doc_id]
        
        score = 0.0
        for term in query_terms:
            if term in doc_term_counts:
                tf = doc_term_counts[term]
                idf = self.idf.get(term, 0.0)
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                score += idf * (numerator / denominator)
        
        return score


class BM25Retriever:
    """
    BM25-based document retriever.
    
    This class provides sparse retrieval using BM25/TF-IDF scoring.
    """
    
    def __init__(self, corpus_store: List[Document] = None, k1: float = 1.2, b: float = 0.75):
        """
        Initialize the BM25 retriever.
        
        Args:
            corpus_store: List of documents to index (can be provided later via fit)
            k1: BM25 term frequency parameter
            b: BM25 length normalization parameter
        """
        self.tfidf = SimpleTFIDF(k1=k1, b=b)
        self.documents = {}
        
        if corpus_store:
            self.fit(corpus_store)
    
    def fit(self, documents: List[Document]) -> None:
        """
        Fit the BM25 model on a collection of documents.
        
        Args:
            documents: List of Document objects to index
        """
        self.documents = {doc.id: doc for doc in documents}
        self.tfidf.fit(documents)
    
    def search(self, query: str, top_k: int = 10) -> List[ScoredDocument]:
        """
        Search for documents using BM25 scoring.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of ScoredDocument objects sorted by relevance score
        """
        if not self.documents:
            return []
        
        # Tokenize query
        query_terms = self.tfidf._tokenize(query)
        if not query_terms:
            return []
        
        # Score all documents
        scored_docs = []
        for doc_id in self.documents:
            score = self.tfidf.score_document(query_terms, doc_id)
            if score > 0:  # Only include documents with positive scores
                doc = self.documents[doc_id]
                scored_docs.append(ScoredDocument(
                    document=doc,
                    score=score,
                    explanation=f"BM25 score: {score:.4f}"
                ))
        
        # Sort by score (descending) and return top_k
        scored_docs.sort(key=lambda x: x.score, reverse=True)
        return scored_docs[:top_k]
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics about the indexed corpus.
        
        Returns:
            Dictionary with corpus statistics
        """
        return {
            "total_documents": len(self.documents),
            "vocabulary_size": len(self.tfidf.vocabulary),
            "avg_doc_length": self.tfidf.avg_doc_length,
            "total_terms": sum(self.tfidf.doc_lengths.values())
        }
