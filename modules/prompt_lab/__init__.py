"""
Prompt & API Control Mini-Lab

A lightweight module for structured output experimentation with query rewriting.
Supports JSON Mode and Function Calling with strict schema validation.
"""

from .contracts import RewriteInput, RewriteOutput
from .providers import RewriterProvider, MockProvider
from .query_rewriter import QueryRewriter

__all__ = [
    "RewriteInput",
    "RewriteOutput",
    "RewriterProvider",
    "MockProvider",
    "QueryRewriter",
]
