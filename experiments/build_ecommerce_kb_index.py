#!/usr/bin/env python3
"""
build_ecommerce_kb_index.py - Build vector index for ecommerce policy knowledge base

This script:
1. Scans knowledge_base/ecommerce/ directory for *.md files
2. Splits each document into chunks (by empty lines or ## headers)
3. Generates embeddings for each chunk using OpenAI
4. Saves index to data/ecommerce_kb_index/ (JSON metadata + numpy embeddings)

Usage:
    python experiments/build_ecommerce_kb_index.py
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.clients import get_openai_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
KB_DIR = project_root / "knowledge_base" / "ecommerce"
INDEX_DIR = project_root / "data" / "ecommerce_kb_index"
INDEX_META_PATH = INDEX_DIR / "index_meta.json"
INDEX_EMBEDDINGS_PATH = INDEX_DIR / "index_embeddings.npy"
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model


class PolicyChunk:
    """Represents a single chunk of policy text with metadata."""
    
    def __init__(self, chunk_id: str, source: str, text: str, embedding: List[float] = None):
        self.id = chunk_id
        self.source = source
        self.text = text
        self.embedding = embedding
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "text": self.text,
        }


def split_markdown_into_chunks(content: str, source_file: str) -> List[PolicyChunk]:
    """
    Split markdown content into chunks.
    
    Simple strategy: split by double newlines (paragraphs) or ## headers.
    Each chunk should be meaningful and not too long.
    
    Args:
        content: Full markdown content
        source_file: Source filename (e.g., "return_policy.md")
    
    Returns:
        List of PolicyChunk objects
    """
    chunks = []
    
    # Remove leading/trailing whitespace
    content = content.strip()
    
    # Split by double newlines first (paragraphs)
    paragraphs = re.split(r'\n\n+', content)
    
    chunk_id_counter = 0
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Skip if it's just a header without content
        if para.startswith('#') and len(para.split('\n')) == 1:
            continue
        
        # If paragraph is too long (>500 chars), try to split by single newlines
        if len(para) > 500:
            lines = para.split('\n')
            current_chunk_lines = []
            current_chunk_length = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # If adding this line would exceed 500 chars, finalize current chunk
                if current_chunk_length + len(line) > 500 and current_chunk_lines:
                    chunk_text = '\n'.join(current_chunk_lines)
                    chunk_id = f"{source_file}_{chunk_id_counter}"
                    chunks.append(PolicyChunk(
                        chunk_id=chunk_id,
                        source=source_file,
                        text=chunk_text
                    ))
                    chunk_id_counter += 1
                    current_chunk_lines = [line]
                    current_chunk_length = len(line)
                else:
                    current_chunk_lines.append(line)
                    current_chunk_length += len(line)
            
            # Add remaining lines as final chunk
            if current_chunk_lines:
                chunk_text = '\n'.join(current_chunk_lines)
                chunk_id = f"{source_file}_{chunk_id_counter}"
                chunks.append(PolicyChunk(
                    chunk_id=chunk_id,
                    source=source_file,
                    text=chunk_text
                ))
                chunk_id_counter += 1
        else:
            # Paragraph is short enough, use as single chunk
            chunk_id = f"{source_file}_{chunk_id_counter}"
            chunks.append(PolicyChunk(
                chunk_id=chunk_id,
                source=source_file,
                text=para
            ))
            chunk_id_counter += 1
    
    return chunks


def generate_embedding(text: str, client) -> List[float]:
    """
    Generate embedding for text using OpenAI API.
    
    Args:
        text: Text to embed
        client: OpenAI client instance
    
    Returns:
        List of floats representing the embedding vector
    """
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def build_index() -> None:
    """
    Main function to build the knowledge base index.
    
    Scans KB directory, splits documents, generates embeddings, and saves index.
    """
    # Ensure KB directory exists
    if not KB_DIR.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {KB_DIR}")
    
    # Get OpenAI client
    client = get_openai_client()
    if not client:
        raise ValueError("OpenAI client not available. Check OPENAI_API_KEY environment variable.")
    
    # Find all markdown files
    md_files = list(KB_DIR.glob("*.md"))
    if not md_files:
        raise ValueError(f"No markdown files found in {KB_DIR}")
    
    logger.info(f"Found {len(md_files)} markdown files in {KB_DIR}")
    
    # Process each file
    all_chunks = []
    for md_file in md_files:
        logger.info(f"Processing: {md_file.name}")
        
        # Read file content
        content = md_file.read_text(encoding='utf-8')
        
        # Split into chunks
        chunks = split_markdown_into_chunks(content, md_file.name)
        logger.info(f"  Split into {len(chunks)} chunks")
        
        # Generate embeddings for each chunk
        for chunk in chunks:
            logger.debug(f"  Generating embedding for chunk: {chunk.id}")
            embedding = generate_embedding(chunk.text, client)
            chunk.embedding = embedding
        
        all_chunks.extend(chunks)
    
    logger.info(f"Total chunks: {len(all_chunks)}")
    
    # Prepare data for saving
    # Metadata: list of chunk dicts (without embeddings)
    metadata = [chunk.to_dict() for chunk in all_chunks]
    
    # Embeddings: numpy array (n_chunks, embedding_dim)
    embeddings_array = np.array([chunk.embedding for chunk in all_chunks])
    
    # Create index directory
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save metadata as JSON
    logger.info(f"Saving metadata to {INDEX_META_PATH}")
    with open(INDEX_META_PATH, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Save embeddings as numpy array
    logger.info(f"Saving embeddings to {INDEX_EMBEDDINGS_PATH}")
    np.save(INDEX_EMBEDDINGS_PATH, embeddings_array)
    
    logger.info(f"✅ Index built successfully!")
    logger.info(f"  - Total chunks: {len(all_chunks)}")
    logger.info(f"  - Embedding dimension: {embeddings_array.shape[1]}")
    logger.info(f"  - Metadata: {INDEX_META_PATH}")
    logger.info(f"  - Embeddings: {INDEX_EMBEDDINGS_PATH}")


def main():
    """CLI entry point."""
    try:
        build_index()
        return 0
    except Exception as e:
        logger.error(f"Failed to build index: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

