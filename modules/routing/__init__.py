"""
Routing module for SearchForge.

This module provides intelligent routing between FAISS and Qdrant based on:
- Query characteristics (topK, filters)
- Backend health status
- Cost optimization
"""

from .rules.router import QueryRouter
from .cost.estimator import CostEstimator

__all__ = ["QueryRouter", "CostEstimator"]

