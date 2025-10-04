"""
Retrievers module for SmartSearchX.

This module contains different retrieval strategies including BM25 and other
sparse retrieval methods.
"""

from .bm25 import BM25Retriever

__all__ = ["BM25Retriever"]
