"""
PageIndex: Chapter→Paragraph Hierarchical Retrieval

[CORE] Pure functional implementation of two-stage retrieval with TF-IDF.
- Stage 1: Rank chapters by query relevance
- Stage 2: Rank paragraphs within top chapters
- Fusion: Combine chapter and paragraph scores

Design principles:
- Pure functions (no I/O in core logic)
- Deterministic (fixed seed for reproducibility)
- Fast (<50ms default timeout)
- Graceful degradation (fallback on timeout/empty)
"""

import re
import math
import time
from typing import List, Dict, Any, Iterable, Tuple, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, field


@dataclass
class PageIndexConfig:
    """Configuration for PageIndex."""
    top_chapters: int = 5
    alpha: float = 0.5  # Fusion weight: alpha*chapter + (1-alpha)*para
    timeout_ms: int = 50
    min_chapter_tokens: int = 120  # Min tokens to consider as chapter (lowered from 200)
    min_para_tokens: int = 10  # Min tokens to consider as paragraph
    max_chapter_tokens: int = 1500  # Max tokens per chapter (with spillover)


@dataclass
class Chapter:
    """Represents a document chapter/section."""
    chapter_id: str
    doc_id: str
    title: str
    text: str
    start_para_idx: int
    end_para_idx: int


@dataclass
class Paragraph:
    """Represents a paragraph within a chapter."""
    para_id: str
    chapter_id: str
    doc_id: str
    text: str
    tokens: List[str]


@dataclass
class PageIndex:
    """In-memory hierarchical index structure."""
    chapters: List[Chapter]
    paragraphs: List[Paragraph]
    chapter_vectors: Dict[str, Dict[str, float]]  # chapter_id -> {term: tfidf}
    para_vectors: Dict[str, Dict[str, float]]  # para_id -> {term: tfidf}
    idf: Dict[str, float]  # term -> idf value
    config: PageIndexConfig


@dataclass
class RankedParagraph:
    """Ranked paragraph result."""
    doc_id: str
    chapter_title: str
    para_text: str
    score: float
    chapter_id: str
    para_id: str
    chapter_score: float = 0.0
    para_score: float = 0.0


@dataclass
class RetrievalMetrics:
    """Explainability metrics for retrieval."""
    chapters_scored: List[Tuple[str, float]] = field(default_factory=list)  # (chapter_id, score)
    chosen_topC: List[str] = field(default_factory=list)  # Top C chapter IDs
    paras_per_chapter: Dict[str, int] = field(default_factory=dict)  # chapter_id -> count
    query_tokens: List[str] = field(default_factory=list)
    stage1_time_ms: float = 0.0
    stage2_time_ms: float = 0.0


# ==================== [CORE: splitter] ====================

def split_into_chapters(text: str, doc_id: str, title: str, min_tokens: int = 120) -> List[Chapter]:
    """
    [CORE: splitter] Split document text into chapters using improved heading heuristics.
    
    Heuristics (enhanced):
    1. Markdown headers (# ## ###)
    2. Chinese chapter markers (第一章, 第二章, etc)
    3. English chapter/appendix (Chapter 1, Appendix A)
    4. Numbered headings (1., 1.1, 1.1.1, I., A.)
    5. ALL CAPS lines (< 100 chars)
    6. Bullet-style headers (•, -, *)
    7. Post-processing: merge short chapters (<120 tokens), cap at ~1500 tokens
    
    Args:
        text: Document text
        doc_id: Document identifier
        title: Document title
        min_tokens: Minimum tokens to consider as chapter (default 120)
        
    Returns:
        List of Chapter objects with optimal sizes (120-1500 tokens)
    """
    chapters = []
    lines = text.split('\n')
    
    current_chapter_title = title or "Introduction"
    current_chapter_lines = []
    chapter_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        is_heading = False
        heading_text = ""
        
        # Heuristic 1: Markdown headers (# ## ###)
        if re.match(r'^#{1,3}\s+.+', line):
            is_heading = True
            heading_text = re.sub(r'^#{1,3}\s+', '', line)
        
        # Heuristic 2: Chinese chapter markers (第一章, 第二章, etc)
        elif re.match(r'^第[一二三四五六七八九十百千]+章', line):
            is_heading = True
            heading_text = line
        
        # Heuristic 3: English chapter/appendix markers
        elif re.match(r'^(Chapter|Appendix|Section|Part)\s+\d+', line, re.IGNORECASE) and len(line) < 100:
            is_heading = True
            heading_text = line
        
        # Heuristic 4: Numbered headings (1., 1.1, 1.1.1, I., A., etc)
        elif re.match(r'^(\d+(\.\d+)*|[IVX]+|[A-Z])\.?\s+[A-Z].+', line) and len(line) < 100:
            is_heading = True
            heading_text = re.sub(r'^(\d+(\.\d+)*|[IVX]+|[A-Z])\.?\s+', '', line)
        
        # Heuristic 5: Bullet-style headers (•, -, *, only if uppercase or title case)
        elif re.match(r'^[•\-\*]\s+[A-Z].+', line) and len(line) < 80:
            words = line[2:].split()
            if len(words) <= 8 and (line[2:].isupper() or line[2:].istitle()):
                is_heading = True
                heading_text = line[2:].strip()
        
        # Heuristic 6: Short line in uppercase
        elif len(line) < 100 and line.isupper() and len(line) > 3:
            is_heading = True
            heading_text = line.title()
        
        # Heuristic 7: Short line followed by blank line (potential heading)
        elif (len(line) < 100 and len(line) > 3 and 
              i + 1 < len(lines) and not lines[i + 1].strip()):
            next_non_blank = i + 1
            while next_non_blank < len(lines) and not lines[next_non_blank].strip():
                next_non_blank += 1
            if next_non_blank < len(lines) and len(lines[next_non_blank]) > 50:
                is_heading = True
                heading_text = line
        
        if is_heading:
            # Save previous chapter
            if current_chapter_lines:
                chapter_text = '\n'.join(current_chapter_lines).strip()
                tokens = _tokenize(chapter_text)
                if len(tokens) >= min_tokens:
                    chapter = Chapter(
                        chapter_id=f"{doc_id}_ch{chapter_count}",
                        doc_id=doc_id,
                        title=current_chapter_title,
                        text=chapter_text,
                        start_para_idx=0,
                        end_para_idx=0
                    )
                    chapters.append(chapter)
                    chapter_count += 1
            
            # Start new chapter
            current_chapter_title = heading_text if heading_text else line
            current_chapter_lines = []
        else:
            if line:
                current_chapter_lines.append(line)
        
        i += 1
    
    # Add last chapter
    if current_chapter_lines:
        chapter_text = '\n'.join(current_chapter_lines).strip()
        tokens = _tokenize(chapter_text)
        if len(tokens) >= min_tokens:
            chapter = Chapter(
                chapter_id=f"{doc_id}_ch{chapter_count}",
                doc_id=doc_id,
                title=current_chapter_title,
                text=chapter_text,
                start_para_idx=0,
                end_para_idx=0
            )
            chapters.append(chapter)
    
    # Post-processing: Merge short chapters (<120 tokens) and cap at ~1500 tokens
    if len(chapters) > 1:
        merged_chapters = []
        i = 0
        while i < len(chapters):
            current = chapters[i]
            current_tokens = _tokenize(current.text)
            
            # If current chapter is too short (<120), merge with next
            if len(current_tokens) < 120 and i < len(chapters) - 1:
                next_chapter = chapters[i + 1]
                next_tokens = _tokenize(next_chapter.text)
                
                # Merge if combined size is reasonable (<1500 tokens)
                if len(current_tokens) + len(next_tokens) < 1500:
                    merged_text = current.text + '\n\n' + next_chapter.text
                    merged = Chapter(
                        chapter_id=f"{doc_id}_ch{len(merged_chapters)}",
                        doc_id=doc_id,
                        title=current.title,
                        text=merged_text,
                        start_para_idx=0,
                        end_para_idx=0
                    )
                    merged_chapters.append(merged)
                    i += 2
                    continue
            
            # If chapter is too large (>1500 tokens), split it
            elif len(current_tokens) > 1500:
                # Split into chunks of ~1200 tokens
                chunk_size = 1200
                text_chunks = []
                tokens_so_far = 0
                current_chunk = []
                
                for line in current.text.split('\n'):
                    line_tokens = _tokenize(line)
                    if tokens_so_far + len(line_tokens) > chunk_size and current_chunk:
                        text_chunks.append('\n'.join(current_chunk))
                        current_chunk = [line]
                        tokens_so_far = len(line_tokens)
                    else:
                        current_chunk.append(line)
                        tokens_so_far += len(line_tokens)
                
                if current_chunk:
                    text_chunks.append('\n'.join(current_chunk))
                
                # Create sub-chapters
                for idx, chunk_text in enumerate(text_chunks):
                    chunk = Chapter(
                        chapter_id=f"{doc_id}_ch{len(merged_chapters)}",
                        doc_id=doc_id,
                        title=f"{current.title} ({idx+1})" if len(text_chunks) > 1 else current.title,
                        text=chunk_text,
                        start_para_idx=0,
                        end_para_idx=0
                    )
                    merged_chapters.append(chunk)
                i += 1
                continue
            
            # Otherwise, keep as is
            current.chapter_id = f"{doc_id}_ch{len(merged_chapters)}"
            merged_chapters.append(current)
            i += 1
        
        chapters = merged_chapters
    
    # Fallback: entire document as single chapter
    if not chapters:
        chapters.append(Chapter(
            chapter_id=f"{doc_id}_ch0",
            doc_id=doc_id,
            title=title or "Document",
            text=text.strip(),
            start_para_idx=0,
            end_para_idx=0
        ))
    
    return chapters


def split_into_paragraphs(chapter: Chapter, min_tokens: int = 10) -> List[Paragraph]:
    """
    [CORE: splitter] Split chapter text into paragraphs.
    
    Heuristics:
    1. Split on blank lines (\\n\\n)
    2. Split on period + newline
    3. Keep paragraphs with >= min_tokens
    
    Args:
        chapter: Chapter object
        min_tokens: Minimum tokens per paragraph
        
    Returns:
        List of Paragraph objects
    """
    paragraphs = []
    
    # Split on double newlines
    raw_paras = re.split(r'\n\s*\n', chapter.text)
    
    para_idx = 0
    for raw_para in raw_paras:
        raw_para = raw_para.strip()
        if not raw_para:
            continue
        
        # Further split on period + newline
        sentences = re.split(r'\.\s*\n', raw_para)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Ensure sentence ends with period
            if not sentence.endswith('.'):
                sentence += '.'
            
            tokens = _tokenize(sentence)
            if len(tokens) >= min_tokens:
                para = Paragraph(
                    para_id=f"{chapter.chapter_id}_p{para_idx}",
                    chapter_id=chapter.chapter_id,
                    doc_id=chapter.doc_id,
                    text=sentence,
                    tokens=tokens
                )
                paragraphs.append(para)
                para_idx += 1
    
    # Fallback: entire chapter as single paragraph
    if not paragraphs:
        tokens = _tokenize(chapter.text)
        if tokens:
            para = Paragraph(
                para_id=f"{chapter.chapter_id}_p0",
                chapter_id=chapter.chapter_id,
                doc_id=chapter.doc_id,
                text=chapter.text,
                tokens=tokens
            )
            paragraphs.append(para)
    
    return paragraphs


# ==================== [CORE: tfidf_build] ====================

def compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    """
    [CORE: tfidf_build] Compute inverse document frequency (IDF).
    
    Args:
        documents: List of token lists
        
    Returns:
        Dictionary of term -> IDF value
    """
    if not documents:
        return {}
    
    # Count documents containing each term
    doc_count = defaultdict(int)
    for tokens in documents:
        unique_terms = set(tokens)
        for term in unique_terms:
            doc_count[term] += 1
    
    # Compute IDF: log(N / df)
    num_docs = len(documents)
    idf = {}
    for term, df in doc_count.items():
        idf[term] = math.log(num_docs / df)
    
    return idf


def compute_tfidf_vector(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    """
    [CORE: tfidf_build] Compute TF-IDF vector for a document.
    
    Args:
        tokens: Document tokens
        idf: IDF dictionary
        
    Returns:
        TF-IDF vector (term -> tfidf value)
    """
    if not tokens:
        return {}
    
    # Compute normalized TF
    tf_counts = Counter(tokens)
    max_freq = max(tf_counts.values())
    
    tfidf = {}
    for term, freq in tf_counts.items():
        tf_val = freq / max_freq
        idf_val = idf.get(term, 0.0)
        tfidf[term] = tf_val * idf_val
    
    return tfidf


def build_index(
    docs: Iterable[Dict[str, Any]],
    config: Optional[PageIndexConfig] = None,
    return_metrics: bool = False
) -> PageIndex:
    """
    [CORE: tfidf_build] Build hierarchical PageIndex from documents.
    
    Args:
        docs: Iterable of documents, each with {doc_id, title, text}
        config: Optional PageIndexConfig
        return_metrics: If True, log avg_chapter_len and chapter_count
        
    Returns:
        PageIndex object (or tuple with metrics if return_metrics=True)
    """
    if config is None:
        config = PageIndexConfig()
    
    all_chapters = []
    all_paragraphs = []
    
    # Step 1: Split documents into chapters and paragraphs
    for doc in docs:
        doc_id = doc.get('doc_id', doc.get('id', doc.get('_id', 'unknown')))
        title = doc.get('title', '')
        text = doc.get('text', '')
        
        # Split into chapters
        chapters = split_into_chapters(
            text=text,
            doc_id=doc_id,
            title=title,
            min_tokens=config.min_chapter_tokens
        )
        
        # Split each chapter into paragraphs
        for chapter in chapters:
            para_start_idx = len(all_paragraphs)
            paras = split_into_paragraphs(chapter, min_tokens=config.min_para_tokens)
            all_paragraphs.extend(paras)
            
            # Update chapter paragraph indices
            chapter.start_para_idx = para_start_idx
            chapter.end_para_idx = len(all_paragraphs)
            all_chapters.append(chapter)
    
    # Step 2: Compute IDF for all paragraphs
    all_para_tokens = [para.tokens for para in all_paragraphs]
    idf = compute_idf(all_para_tokens)
    
    # Step 3: Compute TF-IDF vectors for chapters
    chapter_vectors = {}
    for chapter in all_chapters:
        tokens = _tokenize(chapter.text)
        chapter_vectors[chapter.chapter_id] = compute_tfidf_vector(tokens, idf)
    
    # Step 4: Compute TF-IDF vectors for paragraphs
    para_vectors = {}
    for para in all_paragraphs:
        para_vectors[para.para_id] = compute_tfidf_vector(para.tokens, idf)
    
    # Compute metrics if requested
    if return_metrics:
        chapter_lens = [len(_tokenize(ch.text)) for ch in all_chapters]
        avg_chapter_len = sum(chapter_lens) / len(chapter_lens) if chapter_lens else 0
        metrics = {
            'chapter_count': len(all_chapters),
            'avg_chapter_len': avg_chapter_len,
            'paragraph_count': len(all_paragraphs)
        }
    
    index = PageIndex(
        chapters=all_chapters,
        paragraphs=all_paragraphs,
        chapter_vectors=chapter_vectors,
        para_vectors=para_vectors,
        idf=idf,
        config=config
    )
    
    if return_metrics:
        return index, metrics
    return index


# ==================== [CORE: tfidf_score] ====================

def score_documents(
    query_vector: Dict[str, float],
    doc_vectors: Dict[str, Dict[str, float]]
) -> List[Tuple[str, float]]:
    """
    [CORE: tfidf_score] Score documents against query using cosine similarity.
    
    Args:
        query_vector: Query TF-IDF vector
        doc_vectors: Document vectors (doc_id -> vector)
        
    Returns:
        List of (doc_id, score) tuples
    """
    scores = []
    for doc_id, doc_vec in doc_vectors.items():
        score = _cosine_similarity(query_vector, doc_vec)
        scores.append((doc_id, score))
    return scores


# ==================== [CORE: fuse_scores] ====================

def fuse_scores(
    chapter_score: float,
    para_score: float,
    alpha: float
) -> float:
    """
    [CORE: fuse_scores] Fuse chapter and paragraph scores.
    
    Args:
        chapter_score: Chapter relevance score
        para_score: Paragraph relevance score
        alpha: Fusion weight (0-1)
        
    Returns:
        Fused score
    """
    return alpha * chapter_score + (1 - alpha) * para_score


# ==================== [CORE: retrieve] ====================

def retrieve(
    query: str,
    index: PageIndex,
    top_k: int = 10,
    top_chapters: Optional[int] = None,
    alpha: Optional[float] = None,
    timeout_ms: Optional[int] = None,
    return_metrics: bool = False
) -> Tuple[List[RankedParagraph], Optional[RetrievalMetrics]]:
    """
    [CORE: retrieve] Two-stage hierarchical retrieval with explainability.
    
    Stage 1: Rank chapters by query relevance
    Stage 2: Rank paragraphs within top chapters
    Fusion: final_score = alpha * chapter_score + (1 - alpha) * para_score
    
    Args:
        query: Query string
        index: PageIndex object
        top_k: Number of paragraphs to return
        top_chapters: Number of top chapters to consider (default: config.top_chapters)
        alpha: Fusion weight (default: config.alpha)
        timeout_ms: Timeout in milliseconds (default: config.timeout_ms)
        return_metrics: If True, return metrics for explainability
        
    Returns:
        (List of RankedParagraph objects, Optional[RetrievalMetrics])
        Empty list on timeout or empty index
    """
    start_time = time.time()
    
    # Initialize metrics
    metrics = RetrievalMetrics() if return_metrics else None
    
    # Use config defaults if not specified
    if top_chapters is None:
        top_chapters = index.config.top_chapters
    if alpha is None:
        alpha = index.config.alpha
    if timeout_ms is None:
        timeout_ms = index.config.timeout_ms
    
    timeout_sec = timeout_ms / 1000.0
    
    # Check for empty index
    if not index.chapters or not index.paragraphs:
        return ([], metrics) if return_metrics else []
    
    # Tokenize and vectorize query
    query_tokens = _tokenize(query)
    if not query_tokens:
        return ([], metrics) if return_metrics else []
    
    if metrics:
        metrics.query_tokens = query_tokens
    
    query_vector = compute_tfidf_vector(query_tokens, index.idf)
    
    # Stage 1: Rank chapters
    stage1_start = time.time()
    chapter_scores = score_documents(query_vector, index.chapter_vectors)
    
    # Check timeout
    if (time.time() - start_time) > timeout_sec:
        return ([], metrics) if return_metrics else []
    
    # Sort chapters by score descending
    chapter_scores.sort(key=lambda x: x[1], reverse=True)
    top_chapter_items = chapter_scores[:top_chapters]
    
    if metrics:
        metrics.chapters_scored = chapter_scores
        metrics.chosen_topC = [ch_id for ch_id, _ in top_chapter_items]
        metrics.stage1_time_ms = (time.time() - stage1_start) * 1000
    
    # Stage 2: Rank paragraphs within top chapters
    stage2_start = time.time()
    candidate_paras = []
    
    # Build chapter lookup
    chapter_map = {ch.chapter_id: ch for ch in index.chapters}
    
    for chapter_id, chapter_score in top_chapter_items:
        # Check timeout
        if (time.time() - start_time) > timeout_sec:
            return ([], metrics) if return_metrics else []
        
        chapter = chapter_map.get(chapter_id)
        if not chapter:
            continue
        
        # Get paragraphs for this chapter
        para_count = 0
        for para_idx in range(chapter.start_para_idx, chapter.end_para_idx):
            if para_idx >= len(index.paragraphs):
                continue
            
            para = index.paragraphs[para_idx]
            para_vec = index.para_vectors.get(para.para_id, {})
            para_score = _cosine_similarity(query_vector, para_vec)
            
            # Fusion: combine chapter and paragraph scores
            final_score = fuse_scores(chapter_score, para_score, alpha)
            
            ranked_para = RankedParagraph(
                doc_id=para.doc_id,
                chapter_title=chapter.title,
                para_text=para.text,
                score=final_score,
                chapter_id=chapter.chapter_id,
                para_id=para.para_id,
                chapter_score=chapter_score,
                para_score=para_score
            )
            
            candidate_paras.append(ranked_para)
            para_count += 1
        
        if metrics:
            metrics.paras_per_chapter[chapter_id] = para_count
    
    if metrics:
        metrics.stage2_time_ms = (time.time() - stage2_start) * 1000
    
    # Sort by final score descending
    candidate_paras.sort(key=lambda x: x.score, reverse=True)
    
    # Return top K
    results = candidate_paras[:top_k]
    
    if return_metrics:
        return results, metrics
    return results


# ==================== Helper Functions ====================

def _tokenize(text: str) -> List[str]:
    """
    Simple tokenization: lowercase + split on non-alphanumeric.
    
    Args:
        text: Input text
        
    Returns:
        List of tokens
    """
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """
    Compute cosine similarity between two sparse vectors.
    
    Args:
        vec1: First vector (term -> value)
        vec2: Second vector (term -> value)
        
    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    if not vec1 or not vec2:
        return 0.0
    
    # Compute dot product
    common_terms = set(vec1.keys()) & set(vec2.keys())
    dot_product = sum(vec1[term] * vec2[term] for term in common_terms)
    
    # Compute magnitudes
    mag1 = math.sqrt(sum(v * v for v in vec1.values()))
    mag2 = math.sqrt(sum(v * v for v in vec2.values()))
    
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


# ==================== Persistence (Optional) ====================

def save_index(index: PageIndex, filepath: str) -> None:
    """
    Save index to JSON file (optional thin wrapper).
    
    Args:
        index: PageIndex object
        filepath: Output file path
    """
    import json
    
    data = {
        'chapters': [
            {
                'chapter_id': ch.chapter_id,
                'doc_id': ch.doc_id,
                'title': ch.title,
                'text': ch.text,
                'start_para_idx': ch.start_para_idx,
                'end_para_idx': ch.end_para_idx
            }
            for ch in index.chapters
        ],
        'paragraphs': [
            {
                'para_id': p.para_id,
                'chapter_id': p.chapter_id,
                'doc_id': p.doc_id,
                'text': p.text,
                'tokens': p.tokens
            }
            for p in index.paragraphs
        ],
        'chapter_vectors': index.chapter_vectors,
        'para_vectors': index.para_vectors,
        'idf': index.idf,
        'config': {
            'top_chapters': index.config.top_chapters,
            'alpha': index.config.alpha,
            'timeout_ms': index.config.timeout_ms,
            'min_chapter_tokens': index.config.min_chapter_tokens,
            'min_para_tokens': index.config.min_para_tokens
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_index(filepath: str) -> PageIndex:
    """
    Load index from JSON file (optional thin wrapper).
    
    Args:
        filepath: Input file path
        
    Returns:
        PageIndex object
    """
    import json
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    config = PageIndexConfig(**data['config'])
    
    chapters = [Chapter(**ch) for ch in data['chapters']]
    paragraphs = [Paragraph(**p) for p in data['paragraphs']]
    
    return PageIndex(
        chapters=chapters,
        paragraphs=paragraphs,
        chapter_vectors=data['chapter_vectors'],
        para_vectors=data['para_vectors'],
        idf=data['idf'],
        config=config
    )


# Backward compatibility: expose retrieve without metrics
def retrieve_simple(
    query: str,
    index: PageIndex,
    top_k: int = 10,
    top_chapters: Optional[int] = None,
    alpha: Optional[float] = None,
    timeout_ms: Optional[int] = None
) -> List[RankedParagraph]:
    """
    Simple retrieve without metrics (backward compatible).
    """
    result = retrieve(query, index, top_k, top_chapters, alpha, timeout_ms, return_metrics=False)
    if isinstance(result, tuple):
        return result[0]
    return result
