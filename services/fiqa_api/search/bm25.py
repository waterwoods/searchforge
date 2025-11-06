"""
bm25.py - BM25 Sparse Retrieval Module
========================================
Lazy-loading singleton BM25 index for hybrid retrieval.
"""

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    BM25Okapi = None  # type: ignore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4096)
def tokenize(text: str) -> Tuple[str, ...]:
    """
    Consistent tokenization for BM25 indexing and querying.
    Converts to lowercase and splits on whitespace/punctuation, keeping alphanumeric and underscores.
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of tokens (lowercase, alphanumeric + underscore only)
    """
    if not text:
        return []
    
    # Convert to lowercase
    text_lower = text.lower()
    
    # Extract tokens: alphanumeric characters and underscores
    # This regex pattern matches words with letters, numbers, and underscores
    tokens = re.findall(r'\b\w+\b', text_lower)
    
    # Return as tuple for cache compatibility
    return tuple(tokens)

# Global singleton instance
_bm25_index: Optional[BM25Okapi] = None
_corpus_docs: List[Dict[str, str]] = []


def get_bm25_corpus_path() -> Optional[Path]:
    """
    Get BM25 corpus path from environment or default.
    
    Returns:
        Path to corpus.jsonl file or None if not configured
    """
    env_path = os.getenv("BM25_CORPUS_PATH")
    
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        logger.warning(f"[BM25] BM25_CORPUS_PATH env var set but file not found: {path}")
        return None
    
    # Try default locations (try both relative and absolute paths)
    # First, try to find repo root (common in Docker: /app)
    repo_root_candidates = [
        Path("/app"),  # Docker container path
        Path(__file__).parent.parent.parent,  # From services/fiqa_api/search/bm25.py -> services -> fiqa_api -> parent
        Path.cwd(),  # Current working directory
    ]
    
    default_paths = []
    for repo_root in repo_root_candidates:
        if repo_root.exists():
            default_paths.extend([
                # Prefer v1 50k corpus if present (for fiqa_50k_v1)
                repo_root / "data" / "fiqa_v1" / "fiqa_50k_v1" / "corpus.jsonl",
                # Prefer v1 10k corpus if present
                repo_root / "data" / "fiqa_v1" / "fiqa_10k_v1" / "corpus.jsonl",
                repo_root / "data" / "fiqa_v1" / "corpus_50k_v1.jsonl",
                repo_root / "data" / "fiqa_v1" / "corpus_10k_v1.jsonl",
                # Legacy locations
                repo_root / "data" / "fiqa" / "corpus.jsonl",
                repo_root / "experiments" / "data" / "fiqa" / "corpus.jsonl",
            ])
    
    # Also try relative paths (for backward compatibility)
    default_paths.extend([
        Path("data/fiqa_v1/fiqa_50k_v1/corpus.jsonl"),
        Path("data/fiqa_v1/fiqa_10k_v1/corpus.jsonl"),
        Path("data/fiqa_v1/corpus_50k_v1.jsonl"),
        Path("data/fiqa_v1/corpus_10k_v1.jsonl"),
        Path("data/fiqa/corpus.jsonl"),
        Path("experiments/data/fiqa/corpus.jsonl"),
    ])
    
    for path in default_paths:
        if path.exists():
            logger.info(f"[BM25] Using default corpus path: {path}")
            return path
    
    logger.warning("[BM25] No corpus.jsonl found in default locations")
    return None


def load_corpus(corpus_path: Path) -> List[Dict[str, str]]:
    """
    Load corpus from JSONL file.
    
    Args:
        corpus_path: Path to corpus.jsonl
        
    Returns:
        List of {"doc_id": str, "text": str} dictionaries
    """
    docs = []
    
    try:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line.strip())
                    # Accept multiple schemas: v1 uses doc_id/title/abstract/text; legacy uses _id/text
                    doc_id = data.get("doc_id") or data.get("_id", "")
                    title = data.get("title", "")
                    abstract = data.get("abstract")
                    body_text = data.get("text", "")
                    abstract_or_text = abstract if (abstract and isinstance(abstract, str)) else body_text
                    bm25_text = f"{title}\n{abstract_or_text}".strip()

                    if doc_id and bm25_text:
                        docs.append({"doc_id": str(doc_id), "text": bm25_text})
                except json.JSONDecodeError as e:
                    logger.warning(f"[BM25] Skipping invalid JSON on line {line_num}: {e}")
                    continue
        
        logger.info(f"[BM25] Loaded {len(docs)} documents from {corpus_path}")
        return docs
        
    except Exception as e:
        logger.error(f"[BM25] Failed to load corpus from {corpus_path}: {e}")
        return []


def initialize_bm25() -> bool:
    """
    Initialize BM25 index singleton.
    
    Returns:
        True if successful, False otherwise
    """
    global _bm25_index, _corpus_docs
    
    if _bm25_index is not None:
        # Already initialized
        return True
    
    if not BM25_AVAILABLE:
        logger.warning("[BM25] rank-bm25 not available. Install with: pip install rank-bm25")
        return False
    
    # Get corpus path
    corpus_path = get_bm25_corpus_path()
    if not corpus_path:
        logger.warning("[BM25] No corpus path found")
        return False
    
    # Load corpus
    _corpus_docs = load_corpus(corpus_path)
    if not _corpus_docs:
        logger.warning("[BM25] No documents loaded")
        return False
    
    # Tokenize and build index (using consistent tokenize function)
    try:
        tokenized_corpus = []
        for doc in _corpus_docs:
            tokens = tokenize(doc["text"])
            tokenized_corpus.append(tokens)
        
        _bm25_index = BM25Okapi(tokenized_corpus)
        corpus_path_str = str(corpus_path) if corpus_path else "unknown"
        logger.info(f"[BM25] BM25 loaded: docs={len(_corpus_docs)}, corpus={corpus_path_str}")
        return True
        
    except Exception as e:
        logger.error(f"[BM25] Failed to build BM25 index: {e}")
        _bm25_index = None
        return False


def bm25_search(query: str, top_k: int = 10) -> List[Dict[str, float]]:
    """
    Search BM25 index.
    
    Args:
        query: Search query string
        top_k: Number of results to return
        
    Returns:
        List of {"doc_id": str, "score": float} dictionaries
    """
    global _bm25_index, _corpus_docs
    
    # Initialize if needed
    if _bm25_index is None:
        if not initialize_bm25():
            logger.warning("[BM25] BM25 not initialized, returning empty results")
            return []
    
    if _bm25_index is None or not _corpus_docs:
        return []
    
    try:
        # Tokenize query using consistent tokenize function (cached)
        query_tokens = list(tokenize(query))  # Convert tuple to list for BM25Okapi
        
        # Get scores
        scores = _bm25_index.get_scores(query_tokens)
        
        # Create (doc_id, score) pairs
        results = []
        for i, (doc, score) in enumerate(zip(_corpus_docs, scores)):
            results.append({
                "doc_id": doc["doc_id"],
                "score": float(score)
            })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        logger.error(f"[BM25] Search failed: {e}")
        return []


def is_bm25_ready() -> bool:
    """
    Check if BM25 is ready for use.
    
    Returns:
        True if BM25 is initialized and ready
    """
    global _bm25_index
    return _bm25_index is not None

