"""
ecommerce_rag_retriever.py - RAG Retriever for Ecommerce Policy Knowledge Base

This module provides retrieval functionality to query the policy knowledge base
and retrieve relevant policy snippets based on user queries.

Simple MVP implementation:
- Loads local vector index (JSON metadata + numpy embeddings)
- Uses OpenAI embeddings for query encoding
- Performs cosine similarity search
- Returns top-K policy snippets
"""

import json
import logging
import warnings
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import numpy as np
from pydantic import BaseModel

from services.fiqa_api.clients import get_openai_client

logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INDEX_META_PATH = PROJECT_ROOT / "data" / "ecommerce_kb_index" / "index_meta.json"
INDEX_EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "ecommerce_kb_index" / "index_embeddings.npy"
EMBEDDING_MODEL = "text-embedding-3-small"  # Must match the model used in build script

# Global cache for loaded index
_INDEX_CACHE: Optional[Tuple[np.ndarray, List[Dict[str, str]]]] = None


class PolicySnippet(BaseModel):
    """Represents a single policy snippet retrieved from the knowledge base."""
    
    id: str
    source: str  # e.g., "return_policy.md"
    text: str


def _load_index() -> Tuple[np.ndarray, List[PolicySnippet]]:
    """
    Load the policy knowledge base index from disk.
    
    Uses global cache to avoid reloading on every query.
    
    Returns:
        Tuple of (embeddings_array, policy_snippets_list)
        - embeddings_array: numpy array of shape (n_chunks, embedding_dim)
        - policy_snippets_list: List of PolicySnippet objects
    
    Raises:
        FileNotFoundError: If index files don't exist
        ValueError: If index files are corrupted
    """
    global _INDEX_CACHE
    
    # Return cached index if available
    if _INDEX_CACHE is not None:
        embeddings_array, metadata_list = _INDEX_CACHE
        snippets = [PolicySnippet(**meta) for meta in metadata_list]
        return embeddings_array, snippets
    
    # Check if index files exist
    if not INDEX_META_PATH.exists():
        raise FileNotFoundError(
            f"Index metadata file not found: {INDEX_META_PATH}. "
            f"Please run experiments/build_ecommerce_kb_index.py first."
        )
    
    if not INDEX_EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(
            f"Index embeddings file not found: {INDEX_EMBEDDINGS_PATH}. "
            f"Please run experiments/build_ecommerce_kb_index.py first."
        )
    
    # Load metadata
    logger.debug(f"Loading index metadata from {INDEX_META_PATH}")
    with open(INDEX_META_PATH, 'r', encoding='utf-8') as f:
        metadata_list = json.load(f)
    
    # Load embeddings
    logger.debug(f"Loading index embeddings from {INDEX_EMBEDDINGS_PATH}")
    embeddings_array = np.load(INDEX_EMBEDDINGS_PATH)
    
    # Validate dimensions match
    if len(metadata_list) != embeddings_array.shape[0]:
        raise ValueError(
            f"Index mismatch: metadata has {len(metadata_list)} entries, "
            f"but embeddings has {embeddings_array.shape[0]} rows"
        )
    
    # Cache for future use
    _INDEX_CACHE = (embeddings_array, metadata_list)
    
    # Convert metadata to PolicySnippet objects
    snippets = [PolicySnippet(**meta) for meta in metadata_list]
    
    logger.info(f"Loaded index: {len(snippets)} policy snippets, embedding dim={embeddings_array.shape[1]}")
    
    return embeddings_array, snippets


def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector (1D numpy array)
        vec2: Second vector (1D numpy array or 2D array for batch)
    
    Returns:
        Cosine similarity score(s)
    """
    # Normalize vectors
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
    
    if vec2.ndim == 1:
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
        return np.dot(vec1_norm, vec2_norm)
    else:
        # Batch computation
        vec2_norm = vec2 / (np.linalg.norm(vec2, axis=1, keepdims=True) + 1e-8)
        return np.dot(vec1_norm, vec2_norm.T)


def retrieve_policy_snippets(query: str, k: int = 3) -> List[PolicySnippet]:
    """
    Retrieve top-K relevant policy snippets based on query.
    
    Args:
        query: User query string
        k: Number of top snippets to return (default: 3)
    
    Returns:
        List of PolicySnippet objects, sorted by relevance (highest first)
        Returns empty list if index not found or query fails (logs warning)
    """
    try:
        # Load index
        embeddings_array, snippets = _load_index()
        
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            logger.warning("OpenAI client not available, cannot generate query embedding")
            return []
        
        # Generate query embedding
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=query
            )
            query_embedding = np.array(response.data[0].embedding)
        except Exception as e:
            logger.warning(f"Failed to generate query embedding: {e}")
            return []
        
        # Compute cosine similarities
        similarities = _cosine_similarity(query_embedding, embeddings_array)
        
        # Get top-K indices
        top_k_indices = np.argsort(similarities)[::-1][:k]
        
        # Retrieve top-K snippets
        results = [snippets[idx] for idx in top_k_indices]
        
        logger.debug(f"Retrieved {len(results)} policy snippets for query: {query[:50]}...")
        
        return results
        
    except FileNotFoundError as e:
        logger.warning(f"Policy index not found: {e}. Returning empty list.")
        return []
    except Exception as e:
        logger.warning(f"Error retrieving policy snippets: {e}", exc_info=True)
        return []

