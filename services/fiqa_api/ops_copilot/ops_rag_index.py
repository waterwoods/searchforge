"""
ops_rag_index.py - Ops Knowledge Base Vector Index Builder
==========================================================
Builds vector index from knowledge_base/*.md files for RAG retrieval.

This module:
- Reads markdown files from knowledge_base/
- Splits documents into chunks (by ## sections)
- Extracts service/symptom hints from headers
- Generates embeddings and stores in Qdrant collection
"""

import logging
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from modules.search.vector_search import VectorSearch

logger = logging.getLogger("ops_copilot.rag_index")

# Knowledge base directory (relative to project root)
_KB_DIR = Path(__file__).parent.parent.parent.parent / "knowledge_base"

# KB files to index
_KB_FILES = ["runbooks.md", "incidents.md", "configs.md", "lessons_learned.md"]


def _extract_service_symptom_from_header(header: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract service and symptom hints from markdown header.
    
    Examples:
        "## [service=payment-service][symptom=high-error-rate]" -> ("payment-service", "high-error-rate")
        "## [payment-service][prod][us-east-1][2024-11-05]" -> ("payment-service", None)
        "## Retry and Backoff Strategies" -> (None, None)
    
    Args:
        header: Markdown header line (e.g., "## [service=xxx][symptom=yyy]")
    
    Returns:
        Tuple of (service_hint, symptom_hint), both can be None
    """
    service_hint = None
    symptom_hint = None
    
    # Pattern 1: [service=xxx][symptom=yyy]
    match1 = re.search(r'\[service=([^\]]+)\]', header, re.IGNORECASE)
    if match1:
        service_hint = match1.group(1).strip()
    
    match2 = re.search(r'\[symptom=([^\]]+)\]', header, re.IGNORECASE)
    if match2:
        symptom_hint = match2.group(1).strip()
    
    # Pattern 2: [service-name] at start (for incidents, configs)
    if not service_hint:
        match3 = re.search(r'^##\s*\[([^\]]+)\]', header)
        if match3:
            # Check if it looks like a service name (contains hyphen, not date)
            candidate = match3.group(1).strip()
            if '-' in candidate and not re.match(r'\d{4}-\d{2}-\d{2}', candidate):
                service_hint = candidate
    
    # Pattern 3: Extract from text if service name appears
    if not service_hint:
        # Common service names
        service_patterns = [
            r'payment-service',
            r'api-gateway',
            r'search-service',
            r'search-api',
            r'user-service',
            r'auth-service',
        ]
        for pattern in service_patterns:
            if re.search(pattern, header, re.IGNORECASE):
                service_hint = pattern.replace(r'\-', '-')
                break
    
    return service_hint, symptom_hint


def _split_into_chunks(content: str, source_file: str) -> List[Dict[str, Any]]:
    """
    Split markdown content into chunks by ## headers.
    
    Args:
        content: Full markdown content
        source_file: Source file name (e.g., "runbooks.md")
    
    Returns:
        List of chunk dictionaries with keys: id, text, service_hint, symptom_hint, source_file
    """
    chunks = []
    
    # Split by ## headers
    sections = re.split(r'\n##\s+', content)
    
    # First section might be before first ##, handle it separately
    if sections and sections[0].strip():
        first_section = sections[0].strip()
        # Skip if it's just the title (very short)
        if len(first_section) > 50:
            # Extract hints from first line if it looks like a header
            lines = first_section.split('\n')
            header_line = lines[0] if lines else ""
            service_hint, symptom_hint = _extract_service_symptom_from_header(header_line)
            
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": first_section,
                "service_hint": service_hint,
                "symptom_hint": symptom_hint,
                "source_file": source_file,
            })
    
    # Process remaining sections (each starts with a header after ##)
    for section in sections[1:]:
        if not section.strip():
            continue
        
        lines = section.split('\n')
        if not lines:
            continue
        
        # First line is the header (after ##)
        header_line = lines[0].strip()
        service_hint, symptom_hint = _extract_service_symptom_from_header(header_line)
        
        # Rest is the content
        content_lines = lines[1:] if len(lines) > 1 else []
        text = '\n'.join(content_lines).strip()
        
        # Skip very short chunks
        if len(text) < 50:
            continue
        
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": text,
            "service_hint": service_hint,
            "symptom_hint": symptom_hint,
            "source_file": source_file,
        })
    
    return chunks


def _load_kb_files() -> Dict[str, str]:
    """
    Load all knowledge base markdown files.
    
    Returns:
        Dictionary mapping file name to content
    """
    kb_content = {}
    
    if not _KB_DIR.exists():
        logger.error(f"Knowledge base directory not found: {_KB_DIR}")
        return kb_content
    
    for filename in _KB_FILES:
        file_path = _KB_DIR / filename
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                kb_content[filename] = content
                logger.info(f"Loaded {len(content)} chars from {filename}")
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")
        else:
            logger.warning(f"Knowledge base file not found: {file_path}")
    
    return kb_content


def build_ops_kb_index(
    collection_name: str = "ops_kb",
    recreate: bool = False,
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> None:
    """
    Build or rebuild vector index for Ops knowledge base.
    
    This function:
    1. Loads markdown files from knowledge_base/
    2. Splits into chunks by ## sections
    3. Extracts service/symptom hints from headers
    4. Generates embeddings and stores in Qdrant
    
    Args:
        collection_name: Qdrant collection name (default: "ops_kb")
        recreate: If True, delete existing collection before creating new one
        embedding_model_name: SentenceTransformer model name for embeddings
    """
    logger.info(f"Building Ops KB index: collection={collection_name}, recreate={recreate}")
    
    # Initialize vector search
    try:
        vector_search = VectorSearch(embedding_model_name=embedding_model_name)
    except Exception as e:
        logger.error(f"Failed to initialize VectorSearch: {e}")
        raise
    
    # Check if collection exists
    collections = vector_search.list_collections()
    collection_exists = collection_name in collections
    
    if collection_exists and recreate:
        logger.info(f"Deleting existing collection: {collection_name}")
        try:
            vector_search.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection (may not exist): {e}")
        collection_exists = False
    
    # Load knowledge base files
    kb_content = _load_kb_files()
    if not kb_content:
        logger.error("No knowledge base files loaded")
        return
    
    # Split into chunks
    all_chunks = []
    for filename, content in kb_content.items():
        chunks = _split_into_chunks(content, filename)
        all_chunks.extend(chunks)
        logger.info(f"Split {filename} into {len(chunks)} chunks")
    
    if not all_chunks:
        logger.error("No chunks extracted from knowledge base")
        return
    
    logger.info(f"Total chunks: {len(all_chunks)}")
    
    # Create collection if needed
    if not collection_exists:
        logger.info(f"Creating collection: {collection_name}")
        try:
            # Get embedding dimension from model
            sample_embedding = vector_search.embedding_model.encode("test")
            vector_size = len(sample_embedding)
            
            from qdrant_client.http.models import Distance, VectorParams
            
            vector_search.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created collection: {collection_name} (vector_size={vector_size})")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    # Generate embeddings and upload to Qdrant
    logger.info(f"Generating embeddings and uploading {len(all_chunks)} chunks...")
    
    batch_size = 50
    uploaded_count = 0
    
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        
        # Prepare points for Qdrant
        points = []
        for chunk in batch:
            # Generate embedding
            embedding = vector_search.embedding_model.encode(chunk["text"]).tolist()
            
            # Prepare payload
            payload = {
                "text": chunk["text"],
                "service_hint": chunk["service_hint"],
                "symptom_hint": chunk["symptom_hint"],
                "source_file": chunk["source_file"],
            }
            
            # Create point
            from qdrant_client.http.models import PointStruct
            point = PointStruct(
                id=chunk["id"],
                vector=embedding,
                payload=payload,
            )
            points.append(point)
        
        # Upload batch
        try:
            vector_search.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            uploaded_count += len(batch)
            logger.info(f"Uploaded batch {i//batch_size + 1}: {len(batch)} chunks (total: {uploaded_count}/{len(all_chunks)})")
        except Exception as e:
            logger.error(f"Failed to upload batch {i//batch_size + 1}: {e}")
            raise
    
    logger.info(f"✅ Successfully built index: {collection_name} with {uploaded_count} chunks")
    
    # Print summary
    collection_info = vector_search.get_collection_info(collection_name)
    logger.info(f"Collection info: {collection_info}")


__all__ = ["build_ops_kb_index"]

