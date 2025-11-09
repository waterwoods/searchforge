#!/usr/bin/env python3
"""
Chunking Strategies Module

Provides different chunking strategies for document splitting:
- Paragraph-based chunking
- Sentence-based chunking
- Sliding window chunking with overlap
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ChunkResult:
    """Result from chunking a document."""
    chunk_id: str
    doc_id: str
    text: str
    chunk_index: int
    start_offset: int = 0
    end_offset: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def normalize_text(text: str) -> str:
    """Normalize whitespace in text."""
    return re.sub(r'\s+', ' ', text).strip()


def split_into_paragraphs(doc: Dict[str, Any]) -> List[ChunkResult]:
    """
    Split document into paragraph chunks.
    
    Strategy:
    - Split on double newlines (\n\n)
    - Merge very short paragraphs (< 50 chars)
    - Keep metadata from original document
    
    Args:
        doc: Document dict with 'doc_id', 'text', 'title'
        
    Returns:
        List of ChunkResult objects
    """
    doc_id = doc.get('doc_id', doc.get('id', 'unknown'))
    title = doc.get('title', '')
    text = doc.get('text', '')
    
    # Split on double newlines
    raw_paras = re.split(r'\n\s*\n', text)
    
    chunks = []
    chunk_idx = 0
    offset = 0
    
    for para in raw_paras:
        para = para.strip()
        if not para:
            continue
        
        # Merge short paragraphs
        if len(para) < 50 and chunks:
            # Merge with previous chunk
            last_chunk = chunks[-1]
            last_chunk.text = last_chunk.text + " " + para
            last_chunk.end_offset = offset + len(para)
            offset += len(para)
            continue
        
        chunk = ChunkResult(
            chunk_id=f"{doc_id}_para_{chunk_idx}",
            doc_id=doc_id,
            text=para,
            chunk_index=chunk_idx,
            start_offset=offset,
            end_offset=offset + len(para),
            metadata={
                'title': title,
                'chunking_strategy': 'paragraph',
                'doc_id': doc_id
            }
        )
        chunks.append(chunk)
        chunk_idx += 1
        offset += len(para)
    
    # Fallback: if no paragraphs found, use entire text
    if not chunks:
        chunk = ChunkResult(
            chunk_id=f"{doc_id}_para_0",
            doc_id=doc_id,
            text=text,
            chunk_index=0,
            start_offset=0,
            end_offset=len(text),
            metadata={
                'title': title,
                'chunking_strategy': 'paragraph',
                'doc_id': doc_id
            }
        )
        chunks.append(chunk)
    
    return chunks


def split_into_sentences(doc: Dict[str, Any]) -> List[ChunkResult]:
    """
    Split document into sentence chunks.
    
    Strategy:
    - Split on sentence boundaries (., !, ?)
    - Group into 1-3 sentence chunks to avoid overly small chunks
    - Keep metadata from original document
    
    Args:
        doc: Document dict with 'doc_id', 'text', 'title'
        
    Returns:
        List of ChunkResult objects
    """
    doc_id = doc.get('doc_id', doc.get('id', 'unknown'))
    title = doc.get('title', '')
    text = doc.get('text', '')
    
    # Split on sentence boundaries (period, question mark, exclamation)
    # Keep the delimiter
    sentences = re.split(r'([.!?]+\s+)', text)
    
    # Reconstruct sentences with their delimiters
    reconstructed = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i]
        delimiter = sentences[i + 1] if i + 1 < len(sentences) else ''
        reconstructed.append((sentence + delimiter).strip())
    
    # Handle last sentence if no delimiter
    if len(sentences) % 2 == 1:
        reconstructed.append(sentences[-1].strip())
    
    # Group sentences into chunks (1-3 sentences per chunk)
    chunks = []
    chunk_idx = 0
    offset = 0
    
    i = 0
    while i < len(reconstructed):
        # Take 1-3 sentences based on length
        group = []
        group_len = 0
        
        while i < len(reconstructed) and len(group) < 3:
            sent = reconstructed[i]
            if not sent:
                i += 1
                continue
            
            group.append(sent)
            group_len += len(sent)
            i += 1
            
            # If we have a reasonable chunk size, stop
            if group_len >= 100:
                break
        
        if not group:
            continue
        
        chunk_text = ' '.join(group)
        chunk = ChunkResult(
            chunk_id=f"{doc_id}_sent_{chunk_idx}",
            doc_id=doc_id,
            text=chunk_text,
            chunk_index=chunk_idx,
            start_offset=offset,
            end_offset=offset + len(chunk_text),
            metadata={
                'title': title,
                'chunking_strategy': 'sentence',
                'sentence_count': len(group),
                'doc_id': doc_id
            }
        )
        chunks.append(chunk)
        chunk_idx += 1
        offset += len(chunk_text)
    
    # Fallback: if no sentences found, use entire text
    if not chunks:
        chunk = ChunkResult(
            chunk_id=f"{doc_id}_sent_0",
            doc_id=doc_id,
            text=text,
            chunk_index=0,
            start_offset=0,
            end_offset=len(text),
            metadata={
                'title': title,
                'chunking_strategy': 'sentence',
                'doc_id': doc_id
            }
        )
        chunks.append(chunk)
    
    return chunks


def split_into_sliding_window(
    doc: Dict[str, Any],
    window_size: int = 256,
    overlap: int = 64
) -> List[ChunkResult]:
    """
    Split document into sliding window chunks.
    
    Strategy:
    - Fixed-size windows (default 256 chars)
    - Overlap between windows (default 64 chars)
    - Try to break on word boundaries
    
    Args:
        doc: Document dict with 'doc_id', 'text', 'title'
        window_size: Size of each window in characters
        overlap: Overlap between windows in characters
        
    Returns:
        List of ChunkResult objects
    """
    doc_id = doc.get('doc_id', doc.get('id', 'unknown'))
    title = doc.get('title', '')
    text = doc.get('text', '')
    
    chunks = []
    chunk_idx = 0
    step = window_size - overlap
    
    i = 0
    while i < len(text):
        # Extract window
        end = min(i + window_size, len(text))
        window = text[i:end]
        
        # Try to break on word boundary (unless we're at the end)
        if end < len(text):
            # Find last space in window
            last_space = window.rfind(' ')
            if last_space > window_size * 0.7:  # Only if we're not cutting too much
                end = i + last_space
                window = text[i:end]
        
        window = window.strip()
        if not window:
            i += step
            continue
        
        chunk = ChunkResult(
            chunk_id=f"{doc_id}_win_{chunk_idx}",
            doc_id=doc_id,
            text=window,
            chunk_index=chunk_idx,
            start_offset=i,
            end_offset=end,
            metadata={
                'title': title,
                'chunking_strategy': 'sliding_window',
                'window_size': window_size,
                'overlap': overlap,
                'doc_id': doc_id
            }
        )
        chunks.append(chunk)
        chunk_idx += 1
        i += step
    
    # Fallback: if no windows created, use entire text
    if not chunks:
        chunk = ChunkResult(
            chunk_id=f"{doc_id}_win_0",
            doc_id=doc_id,
            text=text,
            chunk_index=0,
            start_offset=0,
            end_offset=len(text),
            metadata={
                'title': title,
                'chunking_strategy': 'sliding_window',
                'window_size': window_size,
                'overlap': overlap,
                'doc_id': doc_id
            }
        )
        chunks.append(chunk)
    
    return chunks


def chunk_document(
    doc: Dict[str, Any],
    strategy: str,
    **kwargs
) -> List[ChunkResult]:
    """
    Chunk a document using the specified strategy.
    
    Args:
        doc: Document dict with 'doc_id', 'text', 'title'
        strategy: Chunking strategy ('paragraph', 'sentence', 'sliding_window')
        **kwargs: Additional arguments for the chunking strategy
        
    Returns:
        List of ChunkResult objects
    """
    if strategy == 'paragraph':
        return split_into_paragraphs(doc)
    elif strategy == 'sentence':
        return split_into_sentences(doc)
    elif strategy == 'sliding_window':
        window_size = kwargs.get('window_size', 256)
        overlap = kwargs.get('overlap', 64)
        return split_into_sliding_window(doc, window_size, overlap)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")

