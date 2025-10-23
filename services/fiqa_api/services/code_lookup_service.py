"""
code_lookup_service.py - Code Lookup Service Logic
==================================================
Pure business logic for semantic code search with LLM summarization.
No client creation - uses clients.py singletons.

Features:
- Hybrid search: Vector search + Symbol name filtering
- Re-ranking with boost for exact symbol matches
- Enhanced why_relevant field generation
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Tuple, Set

logger = logging.getLogger(__name__)

# ========================================
# Constants (configurable via env)
# ========================================

QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME", os.getenv("COLLECTION_NAME", "searchforge_codebase"))
MAX_RESULTS = int(os.getenv("CODE_LOOKUP_MAX_RESULTS", "5"))
MIN_SIMILARITY = float(os.getenv("CODE_LOOKUP_MIN_SIMILARITY", "0.4"))
LLM_MODEL = os.getenv("CODE_LOOKUP_LLM_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_MS = int(os.getenv("CODE_LOOKUP_LLM_TIMEOUT_MS", "3000"))

# Debug logging for collection name
logger.info(f"[CODE_LOOKUP_CONFIG] Using collection: {QDRANT_COLLECTION}")
logger.info(f"[CODE_LOOKUP_CONFIG] QDRANT_COLLECTION_NAME: {os.getenv('QDRANT_COLLECTION_NAME')}")
logger.info(f"[CODE_LOOKUP_CONFIG] COLLECTION_NAME: {os.getenv('COLLECTION_NAME')}")

# Hybrid search configuration
VECTOR_SEARCH_LIMIT = int(os.getenv("CODE_LOOKUP_VECTOR_LIMIT", "10"))
SYMBOL_SEARCH_LIMIT = int(os.getenv("CODE_LOOKUP_SYMBOL_LIMIT", "5"))
SYMBOL_MATCH_BOOST = float(os.getenv("CODE_LOOKUP_SYMBOL_BOOST", "1.0"))


# ========================================
# Symbol Extraction
# ========================================

def _extract_symbol_names(query: str) -> List[str]:
    """
    Extract potential function/class names from user query using heuristics.
    
    Patterns matched:
    - ClassName (PascalCase)
    - function_name (snake_case)
    - module.function or Class.method
    - camelCase identifiers
    
    Args:
        query: User query string
        
    Returns:
        List of extracted symbol names (deduplicated)
    """
    if not query or not query.strip():
        return []
    
    symbols = set()
    
    # Pattern 1: PascalCase (ClassName)
    pascal_case = re.findall(r'\b[A-Z][a-zA-Z0-9]*(?:[A-Z][a-zA-Z0-9]*)+\b', query)
    symbols.update(pascal_case)
    
    # Pattern 2: snake_case (function_name, including _private functions)
    # Match both 'function_name' and '_private_function'
    snake_case = re.findall(r'\b_?[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b', query)
    symbols.update(snake_case)
    
    # Pattern 3: camelCase
    camel_case = re.findall(r'\b[a-z][a-z0-9]*[A-Z][a-zA-Z0-9]*\b', query)
    symbols.update(camel_case)
    
    # Pattern 4: Dotted names (module.function, Class.method)
    dotted = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b', query)
    for item in dotted:
        # Add both the full dotted name and the last component
        symbols.add(item)
        parts = item.split('.')
        if len(parts) >= 2:
            symbols.add(parts[-1])  # Add the last component (function/method name)
    
    # Pattern 5: Simple identifier that looks like a symbol (at least 3 chars, starts with letter)
    # Only if it's surrounded by quotes or backticks (indicates it's a code reference)
    quoted = re.findall(r'[`"\']([A-Za-z_][A-Za-z0-9_]{2,})[`"\']', query)
    symbols.update(quoted)
    
    # Filter out common English words and very short symbols
    common_words = {
        'the', 'this', 'that', 'what', 'where', 'when', 'how', 'why', 
        'code', 'function', 'class', 'method', 'file', 'does', 'work',
        'get', 'set', 'add', 'new', 'old', 'use', 'find', 'show', 'make'
    }
    
    filtered_symbols = [s for s in symbols if s.lower() not in common_words and len(s) >= 3]
    
    logger.info(f"[SYMBOL_EXTRACT] Query: '{query[:50]}...' -> Symbols: {filtered_symbols}")
    
    return filtered_symbols


# ========================================
# Context Expansion with Neighbors
# ========================================

def expand_context_with_neighbors(
    client: Any,
    collection_name: str,
    top_hit: Dict[str, Any],
    max_neighbors: int = 10
) -> List[Dict[str, Any]]:
    """
    Expand context by finding one-hop neighbors (callers/callees/imports) using edge data.
    
    Args:
        client: QdrantClient instance
        collection_name: Qdrant collection name
        top_hit: A merged result dict with 'point' key containing the primary hit
        max_neighbors: Maximum number of neighbors to fetch
        
    Returns:
        List of neighbor snippet dicts with path, snippet, relation, name keys
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    try:
        point = top_hit['point']
        payload = point.payload
        file_path = payload.get('file_path') or payload.get('path')
        
        if not file_path:
            logger.warning("[EXPAND_NEIGHBORS] No file_path found in top_hit payload")
            return []
        
        # Step 1: Find the file point (kind='file') for this file_path
        try:
            file_filter = Filter(
                must=[
                    FieldCondition(key="file_path", match=MatchValue(value=file_path)),
                    FieldCondition(key="kind", match=MatchValue(value="file"))
                ]
            )
            
            # Search with the filter (we need a dummy vector, but filter is what matters)
            file_results = client.scroll(
                collection_name=collection_name,
                scroll_filter=file_filter,
                limit=1
            )
            
            if not file_results or not file_results[0]:
                logger.info(f"[EXPAND_NEIGHBORS] No file point found for {file_path}")
                return []
            
            file_point = file_results[0][0]  # scroll returns (points, next_offset)
            file_payload = file_point.payload
            
        except Exception as e:
            logger.warning(f"[EXPAND_NEIGHBORS] Failed to fetch file point: {e}")
            return []
        
        # Step 2: Parse edges_json
        edges_json_str = file_payload.get('edges_json', '[]')
        if not edges_json_str or edges_json_str == '[]':
            logger.info(f"[EXPAND_NEIGHBORS] No edges found for {file_path}")
            return []
        
        try:
            edges = json.loads(edges_json_str)
            if not isinstance(edges, list):
                logger.warning(f"[EXPAND_NEIGHBORS] edges_json is not a list for {file_path}")
                return []
        except json.JSONDecodeError as e:
            logger.warning(f"[EXPAND_NEIGHBORS] Failed to parse edges_json: {e}")
            return []
        
        # Step 3: Determine node_id of the top_hit
        # Try to construct node_id from payload (e.g., "file_path::function_name")
        hit_name = payload.get('name', '')
        hit_kind = payload.get('kind', '')
        
        # Build potential node IDs
        if hit_name and hit_kind in ['function', 'class', 'method']:
            node_id = f"{file_path}::{hit_name}"
        else:
            # Fallback: just use file_path (for module-level or unknown)
            node_id = file_path
        
        # Step 4: Find neighbors from edges
        neighbor_ids = set()
        neighbor_relations = {}  # neighbor_id -> relation type
        
        for edge in edges[:100]:  # Limit processing to first 100 edges
            if not isinstance(edge, dict):
                continue
            
            src = edge.get('src', '')
            dst = edge.get('dst', '')
            # Handle both 'type' and 'etype' keys
            edge_type = edge.get('type', edge.get('etype', 'unknown'))
            
            # Check if this edge involves our node
            if src == node_id and dst:
                neighbor_ids.add(dst)
                neighbor_relations[dst] = f"calls" if edge_type == 'calls' else edge_type
            elif dst == node_id and src:
                neighbor_ids.add(src)
                neighbor_relations[src] = f"called_by" if edge_type == 'calls' else f"imported_by" if edge_type == 'imports' else edge_type
        
        # Also try matching by name only (if full node_id didn't match)
        if not neighbor_ids and hit_name:
            for edge in edges[:100]:
                if not isinstance(edge, dict):
                    continue
                
                src = edge.get('src', '')
                dst = edge.get('dst', '')
                # Handle both 'type' and 'etype' keys
                edge_type = edge.get('type', edge.get('etype', 'unknown'))
                
                # Check if source/destination ends with our name
                if src.endswith(f"::{hit_name}") and dst:
                    neighbor_ids.add(dst)
                    neighbor_relations[dst] = f"calls" if edge_type == 'calls' else edge_type
                elif dst.endswith(f"::{hit_name}") and src:
                    neighbor_ids.add(src)
                    neighbor_relations[src] = f"called_by" if edge_type == 'calls' else f"imported_by" if edge_type == 'imports' else edge_type
        
        # Step 4.5: Also look for callers (functions in same file that call this one)
        # This is more reliable than external calls
        if hit_name and hit_kind in ['function', 'class', 'method']:
            for edge in edges[:100]:
                if not isinstance(edge, dict):
                    continue
                
                src = edge.get('src', '')
                dst = edge.get('dst', '')
                edge_type = edge.get('type', edge.get('etype', 'unknown'))
                
                # Check if dst matches our function name (someone is calling us)
                if dst == hit_name or dst.endswith(f'.{hit_name}'):
                    # The src is the caller (should be file::function format)
                    if '::' in src and src.startswith(file_path):
                        neighbor_ids.add(src)
                        neighbor_relations[src] = 'calls_this_function'
        
        if not neighbor_ids:
            logger.info(f"[EXPAND_NEIGHBORS] No neighbors found for node_id={node_id}")
            return []
        
        # Limit neighbors
        neighbor_ids = list(neighbor_ids)[:max_neighbors]
        logger.info(f"[EXPAND_NEIGHBORS] Found {len(neighbor_ids)} neighbors for {node_id}")
        
        # Step 5: Fetch neighbor snippets from Qdrant
        neighbor_snippets = []
        
        logger.info(f"[EXPAND_NEIGHBORS] Processing {len(neighbor_ids)} neighbor IDs: {neighbor_ids[:3]}...")
        
        for neighbor_id in neighbor_ids:
            try:
                # Parse neighbor_id to get file_path and name
                neighbor_file = None
                neighbor_name = None
                
                if '::' in neighbor_id:
                    # Format: /path/to/file.py::function_name
                    neighbor_file, neighbor_name = neighbor_id.rsplit('::', 1)
                    logger.info(f"[EXPAND_NEIGHBORS] Parsed neighbor_id '{neighbor_id}' -> file='{neighbor_file}', name='{neighbor_name}'")
                else:
                    # For destinations without '::', check if it looks like a codebase function
                    # Skip common built-ins and external library calls
                    skip_keywords = ['all', 'len', 'str', 'int', 'list', 'dict', 'set', 'print', 'open', 'range', 
                                    'hasattr', 'getattr', 'setattr', 'isinstance', 'issubclass', 'type', 'super',
                                    'property', 'staticmethod', 'classmethod', 'enumerate', 'zip', 'map', 'filter']
                    if neighbor_id in skip_keywords:
                        continue
                    if neighbor_id.startswith(('datetime.', 'json.', 'os.', 'sys.', 'math.', 'matplotlib.', 'numpy.', 'pandas.', 
                                               'logging.', 'pathlib.', 'typing.', 'collections.', 'itertools.', 'functools.')):
                        continue
                    
                    # Extract the function name (last part after dot)
                    neighbor_name = neighbor_id.split('.')[-1] if '.' in neighbor_id else neighbor_id
                    
                    # Skip if it looks like a method call on a variable (e.g., 'api_router.include_router')
                    # We want to skip things that start with lowercase (likely variable names)
                    if '.' in neighbor_id:
                        first_part = neighbor_id.split('.')[0]
                        if first_part and first_part[0].islower() and not first_part[0].isupper():
                            # This looks like a variable method call, skip it
                            continue
                    
                    # Try to find this function name in the codebase (any file)
                    # Don't restrict to same file - search globally
                    neighbor_file = None  # Will search all files
                
                # Build filter for neighbor
                if neighbor_name:
                    # Try to find by name (and optionally file_path if we have it)
                    filter_conditions = [FieldCondition(key="name", match=MatchValue(value=neighbor_name))]
                    if neighbor_file:
                        filter_conditions.append(FieldCondition(key="file_path", match=MatchValue(value=neighbor_file)))
                    
                    neighbor_filter = Filter(must=filter_conditions)
                else:
                    # Skip if we can't determine the neighbor
                    continue
                
                # Fetch neighbor snippet
                neighbor_results = client.scroll(
                    collection_name=collection_name,
                    scroll_filter=neighbor_filter,
                    limit=1
                )
                
                if neighbor_results and neighbor_results[0]:
                    neighbor_point = neighbor_results[0][0]
                    neighbor_payload = neighbor_point.payload
                    
                    snippet_text = neighbor_payload.get('text') or neighbor_payload.get('content') or ''
                    actual_file = neighbor_payload.get('file_path', neighbor_file or 'unknown')
                    
                    # Only add if we got actual content
                    if snippet_text and snippet_text.strip():
                        neighbor_snippets.append({
                            'path': actual_file,
                            'snippet': _clip_text(snippet_text, max_len=300),
                            'relation': neighbor_relations.get(neighbor_id, 'related'),
                            'name': neighbor_name,
                            'start_line': neighbor_payload.get('start_line', 0),
                            'end_line': neighbor_payload.get('end_line', 0)
                        })
                        logger.info(f"[EXPAND_NEIGHBORS] ✓ Found snippet for neighbor '{neighbor_name}' in {actual_file.split('/')[-1]}")
                    else:
                        logger.warning(f"[EXPAND_NEIGHBORS] Found point but no snippet text for '{neighbor_name}'")
                    
            except Exception as e:
                logger.warning(f"[EXPAND_NEIGHBORS] Failed to fetch neighbor {neighbor_id}: {e}")
                continue
        
        logger.info(f"[EXPAND_NEIGHBORS] Successfully fetched {len(neighbor_snippets)} neighbor snippets")
        return neighbor_snippets
        
    except Exception as e:
        logger.error(f"[EXPAND_NEIGHBORS] Unexpected error: {e}")
        return []


# ========================================
# Core Code Lookup Logic
# ========================================

def do_code_lookup(message: str) -> Dict[str, Any]:
    """
    Search codebase using hybrid search (vector + symbol name filtering) with LLM summarization.
    
    Args:
        message: User query string
        
    Returns:
        Dict with agent, intent, query, summary_md, files keys
        
    Raises:
        RuntimeError: If clients are not available
        Exception: On critical errors
    """
    from services.fiqa_api.clients import (
        get_embedding_model,
        get_qdrant_client,
        get_openai_client,
        ensure_qdrant_connection
    )
    from qdrant_client.models import Filter, FieldCondition, MatchAny
    
    # Ensure Qdrant connection is healthy before proceeding
    if not ensure_qdrant_connection():
        logger.warning("[CODE_LOOKUP] Qdrant connection unhealthy, search may fail")
    
    # Get clients
    embedding_model = get_embedding_model()
    qdrant_client = get_qdrant_client()
    openai_client = get_openai_client()
    
    # ========================================
    # Step 1: Extract potential symbol names
    # ========================================
    symbol_keywords = _extract_symbol_names(message)
    
    # ========================================
    # Step 2: Embed the query
    # ========================================
    try:
        query_vector = embedding_model.encode(message).tolist()
    except Exception as e:
        logger.error(f"[CODE_LOOKUP] Failed to embed query: {e}")
        raise RuntimeError(f"Failed to generate query embedding: {str(e)}")
    
    # ========================================
    # Step 3A: Vector Search
    # ========================================
    try:
        vector_results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=VECTOR_SEARCH_LIMIT
        )
        logger.info(f"[CODE_LOOKUP] Vector search returned {len(vector_results)} results")
    except Exception as e:
        logger.error(f"[CODE_LOOKUP] Qdrant vector search failed: {e}")
        raise RuntimeError(f"Vector search failed: {str(e)}")
    
    # ========================================
    # Step 3B: Symbol Filter Search
    # ========================================
    symbol_results = []
    if symbol_keywords:
        try:
            # Construct filter for name field matching
            name_filter = Filter(
                should=[
                    FieldCondition(
                        key="name",
                        match=MatchAny(any=symbol_keywords)
                    )
                ]
            )
            
            # Perform filter-only search (no vector needed)
            # We use a dummy query_vector but rely on the filter
            symbol_results = qdrant_client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector,  # Still need a vector for the search API
                query_filter=name_filter,
                limit=SYMBOL_SEARCH_LIMIT
            )
            logger.info(f"[CODE_LOOKUP] Symbol filter search returned {len(symbol_results)} results for keywords: {symbol_keywords}")
        except Exception as e:
            logger.warning(f"[CODE_LOOKUP] Symbol filter search failed: {e}")
            # Continue without symbol results
            symbol_results = []
    
    # ========================================
    # Step 4: Merge and Re-rank Results
    # ========================================
    merged_results = _merge_and_rerank(
        vector_results=vector_results,
        symbol_results=symbol_results,
        symbol_keywords=symbol_keywords
    )
    
    # Handle no results
    if not merged_results:
        return {
            "agent": "sf_agent_hybrid_v1.0",
            "intent": "code_lookup",
            "query": message,
            "summary_md": "没有找到相关代码片段。",
            "files": []
        }
    
    # Filter by similarity threshold
    filtered_results = [r for r in merged_results if r['original_score'] >= MIN_SIMILARITY]
    
    if not filtered_results:
        return {
            "agent": "sf_agent_hybrid_v1.0",
            "intent": "code_lookup",
            "query": message,
            "summary_md": "没有找到足够相关的代码片段。搜索结果相似度太低。",
            "files": []
        }
    
    # ========================================
    # Step 5: Prepare for LLM
    # ========================================
    # Take top results for LLM context
    top_for_llm = filtered_results[:3]
    top_snippets = _prepare_snippets_from_merged(top_for_llm)
    
    # ========================================
    # Step 5.5: Expand Context with Neighbors
    # ========================================
    neighbor_snippets = []
    neighbors_map = {}  # Map point_id -> list of neighbor dicts
    path_to_point_id_map = {}  # Map file_path -> point_id for easier lookup
    try:
        # Take top 3-5 primary hits and expand with neighbors (increased from 2)
        primary_hits = filtered_results[:5]
        logger.info(f"[CODE_LOOKUP] Expanding neighbors for {len(primary_hits)} primary hits")
        for primary_hit in primary_hits:
            point = primary_hit['point']
            point_id = point.id
            file_path = point.payload.get('file_path', 'unknown')
            func_name = point.payload.get('name', 'unknown')
            
            logger.info(f"[CODE_LOOKUP] Expanding neighbors for point {point_id}: {file_path}::{func_name}")
            
            neighbors = expand_context_with_neighbors(
                client=qdrant_client,
                collection_name=QDRANT_COLLECTION,
                top_hit=primary_hit,
                max_neighbors=5  # Limit to 5 neighbors per primary hit
            )
            
            # Store path -> point_id mapping for easier lookup later
            path_to_point_id_map[file_path] = point_id
            
            if neighbors:
                neighbors_map[point_id] = neighbors
                neighbor_snippets.extend(neighbors)
                logger.info(f"[CODE_LOOKUP] ✓ Found {len(neighbors)} neighbors for point {point_id} ({file_path})")
            else:
                logger.info(f"[CODE_LOOKUP] ✗ No neighbors found for point {point_id} ({file_path})")
        
        if neighbor_snippets:
            logger.info(f"[CODE_LOOKUP] Expanded context with {len(neighbor_snippets)} total neighbor snippets")
            logger.info(f"[CODE_LOOKUP] neighbors_map keys: {list(neighbors_map.keys())}")
    except Exception as e:
        logger.warning(f"[CODE_LOOKUP] Context expansion failed, continuing without neighbors: {e}")
        neighbor_snippets = []
        neighbors_map = {}
    
    # ========================================
    # Step 6: LLM Summarization
    # ========================================
    if openai_client:
        try:
            summary_md, files_output = _llm_summarize_hybrid_with_neighbors(
                openai_client=openai_client,
                message=message,
                top_snippets=top_snippets,
                neighbor_snippets=neighbor_snippets,
                filtered_results=filtered_results,
                neighbors_map=neighbors_map,
                path_to_point_id_map=path_to_point_id_map
            )
            logger.info(f"[CODE_LOOKUP] LLM summarization successful for query: {message[:50]}")
        except Exception as e:
            logger.warning(f"[CODE_LOOKUP] LLM summarization failed, falling back to raw results: {e}")
            summary_md, files_output = _fallback_response_hybrid(filtered_results[:3], neighbors_map)
    else:
        logger.info(f"[CODE_LOOKUP] OpenAI client not available, using fallback")
        summary_md, files_output = _fallback_response_hybrid(filtered_results[:3], neighbors_map)
    
    return {
        "agent": "sf_agent_hybrid_v1.0",
        "intent": "code_lookup",
        "query": message,
        "summary_md": summary_md,
        "files": files_output
    }


# ========================================
# Hybrid Search Helper Functions
# ========================================

def _merge_and_rerank(
    vector_results: List[Any],
    symbol_results: List[Any],
    symbol_keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    Merge vector and symbol search results with intelligent re-ranking.
    
    Scoring strategy:
    - Exact symbol matches get a significant boost (+SYMBOL_MATCH_BOOST)
    - Results appearing in both searches get additional boost (+0.2)
    - Sort by final score (highest first)
    
    Args:
        vector_results: Results from vector search
        symbol_results: Results from symbol filter search
        symbol_keywords: List of symbol names used in filtering
        
    Returns:
        List of dicts with point, score, original_score, source, and name keys
    """
    final_results = []
    point_ids_seen = set()
    
    # Build a set of symbol result IDs for quick lookup
    symbol_ids = {hit.id for hit in symbol_results}
    vector_ids = {hit.id for hit in vector_results}
    
    # First, process symbol matches (highest priority)
    for hit in symbol_results:
        if hit.id not in point_ids_seen:
            original_score = float(hit.score)
            boosted_score = original_score + SYMBOL_MATCH_BOOST
            
            # Additional boost if also found in vector results
            source = 'symbol'
            if hit.id in vector_ids:
                boosted_score += 0.2
                source = 'symbol+vector'
            
            final_results.append({
                'point': hit,
                'score': boosted_score,
                'original_score': original_score,
                'source': source,
                'name': hit.payload.get('name', '')
            })
            point_ids_seen.add(hit.id)
    
    # Then, add vector results (already seen IDs are skipped)
    for hit in vector_results:
        if hit.id not in point_ids_seen:
            original_score = float(hit.score)
            score = original_score
            source = 'vector'
            
            final_results.append({
                'point': hit,
                'score': score,
                'original_score': original_score,
                'source': source,
                'name': hit.payload.get('name', '')
            })
            point_ids_seen.add(hit.id)
    
    # Sort by final score (highest first)
    final_results.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"[MERGE_RERANK] Merged {len(symbol_results)} symbol + {len(vector_results)} vector results -> {len(final_results)} total (deduplicated)")
    
    return final_results


def _prepare_snippets_from_merged(merged_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare merged search results for LLM input.
    
    Args:
        merged_results: List of merged result dicts
        
    Returns:
        List of dicts with path, snippet, score, source keys
    """
    snippets = []
    for result in merged_results:
        point = result['point']
        payload = point.payload
        snippets.append({
            "path": payload.get("file_path") or payload.get("path") or "unknown",
            "snippet": _clip_text(payload.get("text") or payload.get("content") or ""),
            "score": result['score'],
            "original_score": result['original_score'],
            "source": result['source'],
            "name": result['name']
        })
    return snippets


# ========================================
# Helper Functions
# ========================================

def _clip_text(text: str, max_len: int = 400) -> str:
    """Clip text to max length and remove null characters."""
    text = text.replace("\u0000", "")
    return (text[:max_len] + "…") if len(text) > max_len else text


def _prepare_snippets(results: List[Any]) -> List[Dict[str, Any]]:
    """
    Prepare search results for LLM input (legacy function, kept for compatibility).
    
    Args:
        results: List of Qdrant search results
        
    Returns:
        List of dicts with path, snippet, score keys
    """
    snippets = []
    for result in results:
        payload = result.payload
        snippets.append({
            "path": payload.get("file_path") or payload.get("path") or "unknown",
            "snippet": _clip_text(payload.get("text") or payload.get("content") or ""),
            "score": float(result.score)
        })
    return snippets


def _generate_why_relevant(source: str, name: str, score: float, original_score: float) -> str:
    """
    Generate why_relevant explanation based on search source.
    
    Args:
        source: Search source ('symbol', 'vector', 'symbol+vector')
        name: Symbol name if available
        score: Boosted score
        original_score: Original similarity score
        
    Returns:
        Human-readable explanation string
    """
    if source == 'symbol':
        if name:
            return f"Exact match for symbol name '{name}' (Score: {score:.2f})"
        else:
            return f"Exact symbol match (Score: {score:.2f})"
    elif source == 'symbol+vector':
        if name:
            return f"Exact symbol match '{name}' + high similarity (Score: {score:.2f})"
        else:
            return f"Exact symbol match + high similarity (Score: {score:.2f})"
    else:  # vector
        return f"High semantic similarity to query (Score: {original_score:.4f})"


def _llm_summarize(
    openai_client: Any,
    message: str,
    top_snippets: List[Dict[str, Any]],
    filtered_results: List[Any]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Use LLM to summarize search results (legacy function, kept for compatibility).
    
    Args:
        openai_client: OpenAI client instance
        message: User query
        top_snippets: Prepared snippets for LLM
        filtered_results: All filtered Qdrant results
        
    Returns:
        Tuple of (summary_md, files_output)
        
    Raises:
        Exception: On LLM call failure
    """
    # System prompt for LLM
    system_prompt = (
        "You are SearchForge Code Assistant.\n"
        "You will ONLY return a valid JSON object with exactly these keys:\n"
        "  summary_md: string (markdown),\n"
        "  files: array of {path, snippet, why_relevant}\n"
        "Rules:\n"
        "- Base your answer ONLY on provided snippets.\n"
        "- Select 1~2 most relevant files; add brief why_relevant.\n"
        "- Keep summary concise and cite files in markdown.\n"
        "- No extra keys. No code fences. Strict JSON.\n"
    )
    
    # User prompt with query and snippets
    user_prompt_data = {
        "query": message,
        "snippets": top_snippets
    }
    
    # Call OpenAI with strict JSON mode
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=512,
        timeout=LLM_TIMEOUT_MS / 1000.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt_data, ensure_ascii=False)}
        ]
    )
    
    # Parse LLM response
    content = response.choices[0].message.content
    llm_data = json.loads(content)
    
    # Validate JSON shape
    if not isinstance(llm_data, dict) or "summary_md" not in llm_data or "files" not in llm_data:
        raise ValueError("Invalid JSON shape from LLM")
    
    # Extract summary
    summary_md = llm_data["summary_md"]
    
    # Build files from LLM selection (limit to 3)
    files_output = []
    for file_item in llm_data["files"][:3]:
        # Find original result to get full metadata
        matched_result = None
        for result in filtered_results:
            if result.payload.get("file_path") == file_item.get("path"):
                matched_result = result
                break
        
        if matched_result:
            payload = matched_result.payload
            files_output.append({
                "path": file_item.get("path", "unknown"),
                "language": payload.get("language", "python"),
                "start_line": payload.get("chunk_index", 0) * 50,
                "end_line": (payload.get("chunk_index", 0) + 1) * 50,
                "snippet": _clip_text(file_item.get("snippet", "")),
                "why_relevant": file_item.get("why_relevant", "Selected by LLM")
            })
        else:
            # Fallback if path not found in original results
            files_output.append({
                "path": file_item.get("path", "unknown"),
                "language": "python",
                "start_line": 0,
                "end_line": 50,
                "snippet": _clip_text(file_item.get("snippet", "")),
                "why_relevant": file_item.get("why_relevant", "Selected by LLM")
            })
    
    return summary_md, files_output


def _llm_summarize_hybrid(
    openai_client: Any,
    message: str,
    top_snippets: List[Dict[str, Any]],
    filtered_results: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Use LLM to summarize hybrid search results with enhanced why_relevant field.
    
    Args:
        openai_client: OpenAI client instance
        message: User query
        top_snippets: Prepared snippets for LLM (from merged results)
        filtered_results: All filtered merged results
        
    Returns:
        Tuple of (summary_md, files_output)
        
    Raises:
        Exception: On LLM call failure
    """
    # System prompt for LLM
    system_prompt = (
        "You are SearchForge Code Assistant with Hybrid Search capabilities.\n"
        "You will ONLY return a valid JSON object with exactly these keys:\n"
        "  summary_md: string (markdown),\n"
        "  files: array of {path, snippet}\n"
        "Rules:\n"
        "- Base your answer ONLY on provided snippets.\n"
        "- Select 1~2 most relevant files.\n"
        "- Keep summary concise and cite files in markdown.\n"
        "- No extra keys. No code fences. Strict JSON.\n"
        "- NOTE: why_relevant will be auto-generated based on search type.\n"
    )
    
    # User prompt with query and snippets
    user_prompt_data = {
        "query": message,
        "snippets": top_snippets
    }
    
    # Call OpenAI with strict JSON mode
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=512,
        timeout=LLM_TIMEOUT_MS / 1000.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt_data, ensure_ascii=False)}
        ]
    )
    
    # Parse LLM response
    content = response.choices[0].message.content
    llm_data = json.loads(content)
    
    # Validate JSON shape
    if not isinstance(llm_data, dict) or "summary_md" not in llm_data or "files" not in llm_data:
        raise ValueError("Invalid JSON shape from LLM")
    
    # Extract summary
    summary_md = llm_data["summary_md"]
    
    # Build files from LLM selection (limit to MAX_RESULTS)
    files_output = []
    for file_item in llm_data["files"][:MAX_RESULTS]:
        # Find original merged result to get full metadata
        matched_result = None
        for result in filtered_results:
            if result['point'].payload.get("file_path") == file_item.get("path"):
                matched_result = result
                break
        
        if matched_result:
            point = matched_result['point']
            payload = point.payload
            
            # Generate why_relevant based on search source
            why_relevant = _generate_why_relevant(
                source=matched_result['source'],
                name=matched_result['name'],
                score=matched_result['score'],
                original_score=matched_result['original_score']
            )
            
            files_output.append({
                "path": file_item.get("path", "unknown"),
                "language": payload.get("language", "python"),
                "start_line": payload.get("start_line", 0),
                "end_line": payload.get("end_line", 0),
                "snippet": _clip_text(file_item.get("snippet", "")),
                "why_relevant": why_relevant
            })
        else:
            # Fallback if path not found in original results
            files_output.append({
                "path": file_item.get("path", "unknown"),
                "language": "python",
                "start_line": 0,
                "end_line": 0,
                "snippet": _clip_text(file_item.get("snippet", "")),
                "why_relevant": "Selected by LLM"
            })
    
    return summary_md, files_output


def _llm_summarize_hybrid_with_neighbors(
    openai_client: Any,
    message: str,
    top_snippets: List[Dict[str, Any]],
    neighbor_snippets: List[Dict[str, Any]],
    filtered_results: List[Dict[str, Any]],
    neighbors_map: Dict[str, List[Dict[str, Any]]] = None,
    path_to_point_id_map: Dict[str, str] = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Use LLM to summarize hybrid search results with context expansion from neighbors.
    
    Args:
        openai_client: OpenAI client instance
        message: User query
        top_snippets: Prepared primary snippets for LLM (from merged results)
        neighbor_snippets: Related code snippets from one-hop neighbors
        filtered_results: All filtered merged results
        neighbors_map: Map of point_id -> list of neighbor dicts (optional)
        path_to_point_id_map: Map of file_path -> point_id (optional)
        
    Returns:
        Tuple of (summary_md, files_output)
        
    Raises:
        Exception: On LLM call failure
    """
    if neighbors_map is None:
        neighbors_map = {}
    if path_to_point_id_map is None:
        path_to_point_id_map = {}
    # System prompt for LLM with neighbor context instructions
    system_prompt = (
        "You are SearchForge Code Assistant with Enhanced Context capabilities.\n"
        "You will receive PRIMARY code snippets (direct search results) and RELATED code snippets (neighbors via call/import relationships).\n"
        "You will ONLY return a valid JSON object with exactly these keys:\n"
        "  summary_md: string (markdown),\n"
        "  files: array of {path, snippet}\n"
        "Rules:\n"
        "- FOCUS on PRIMARY snippets as the main answer.\n"
        "- Use RELATED snippets for additional context if they help explain the primary code.\n"
        "- Select 1~2 most relevant PRIMARY files for the 'files' output.\n"
        "- Keep summary concise and cite files in markdown.\n"
        "- No extra keys. No code fences. Strict JSON.\n"
    )
    
    # Build user prompt with separated primary and neighbor snippets
    prompt_parts = [f"Query: {message}\n"]
    
    # Add primary snippets
    prompt_parts.append("\n=== PRIMARY CODE SNIPPETS (Direct Search Results) ===")
    for i, snippet in enumerate(top_snippets, 1):
        prompt_parts.append(f"\n[Primary {i}] File: {snippet['path']}")
        if snippet.get('name'):
            prompt_parts.append(f"Symbol: {snippet['name']}")
        prompt_parts.append(f"Score: {snippet['score']:.2f} ({snippet['source']})")
        prompt_parts.append(f"Code:\n```\n{snippet['snippet']}\n```")
    
    # Add neighbor snippets if available
    if neighbor_snippets:
        prompt_parts.append("\n\n=== RELATED CODE (One-Hop Neighbors) ===")
        for i, neighbor in enumerate(neighbor_snippets, 1):
            prompt_parts.append(f"\n[Neighbor {i}] File: {neighbor['path']}")
            prompt_parts.append(f"Name: {neighbor['name']}")
            prompt_parts.append(f"Relationship: {neighbor['relation']}")
            prompt_parts.append(f"Code:\n```\n{neighbor['snippet']}\n```")
    
    user_prompt = "\n".join(prompt_parts)
    
    # Call OpenAI with strict JSON mode
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=512,
        timeout=LLM_TIMEOUT_MS / 1000.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    # Parse LLM response
    content = response.choices[0].message.content
    llm_data = json.loads(content)
    
    # Validate JSON shape
    if not isinstance(llm_data, dict) or "summary_md" not in llm_data or "files" not in llm_data:
        raise ValueError("Invalid JSON shape from LLM")
    
    # Extract summary
    summary_md = llm_data["summary_md"]
    
    # Build files from LLM selection (limit to MAX_RESULTS)
    files_output = []
    logger.info(f"[LLM_SUMMARIZE] Building files_output from {len(llm_data['files'])} LLM selections")
    logger.info(f"[LLM_SUMMARIZE] Available neighbors_map keys: {list(neighbors_map.keys())[:3]}")
    logger.info(f"[LLM_SUMMARIZE] Available path_to_point_id_map: {list(path_to_point_id_map.keys())[:3]}")
    
    for file_item in llm_data["files"][:MAX_RESULTS]:
        file_path = file_item.get("path", "unknown")
        
        # Find original merged result to get full metadata
        matched_result = None
        for result in filtered_results:
            if result['point'].payload.get("file_path") == file_path:
                matched_result = result
                break
        
        if matched_result:
            point = matched_result['point']
            payload = point.payload
            point_id = point.id
            
            logger.info(f"[LLM_SUMMARIZE] Matched LLM file '{file_path}' to point_id {point_id}")
            
            # Generate why_relevant based on search source
            why_relevant = _generate_why_relevant(
                source=matched_result['source'],
                name=matched_result['name'],
                score=matched_result['score'],
                original_score=matched_result['original_score']
            )
            
            file_entry = {
                "path": file_path,
                "language": payload.get("language", "python"),
                "start_line": payload.get("start_line", 0),
                "end_line": payload.get("end_line", 0),
                "snippet": _clip_text(file_item.get("snippet", "")),
                "why_relevant": why_relevant
            }
            
            # Add neighbors if available for this point
            # Try by point_id first, then by file_path
            if point_id in neighbors_map:
                file_entry["neighbors"] = neighbors_map[point_id]
                logger.info(f"[LLM_SUMMARIZE] ✓ Added {len(neighbors_map[point_id])} neighbors to {file_path.split('/')[-1]} (by point_id)")
            elif file_path in path_to_point_id_map:
                alt_point_id = path_to_point_id_map[file_path]
                if alt_point_id in neighbors_map:
                    file_entry["neighbors"] = neighbors_map[alt_point_id]
                    logger.info(f"[LLM_SUMMARIZE] ✓ Added {len(neighbors_map[alt_point_id])} neighbors to {file_path.split('/')[-1]} (by path lookup)")
                else:
                    file_entry["neighbors"] = []
                    logger.info(f"[LLM_SUMMARIZE] ✗ No neighbors for alt_point_id {alt_point_id}")
            else:
                file_entry["neighbors"] = []
                logger.info(f"[LLM_SUMMARIZE] ✗ No neighbors found for point_id {point_id} or path {file_path}")
            
            files_output.append(file_entry)
        else:
            # Fallback if path not found in original results
            logger.warning(f"[LLM_SUMMARIZE] Could not match LLM file '{file_item.get('path')}' to any search result")
            files_output.append({
                "path": file_item.get("path", "unknown"),
                "language": "python",
                "start_line": 0,
                "end_line": 0,
                "snippet": _clip_text(file_item.get("snippet", "")),
                "why_relevant": "Selected by LLM",
                "neighbors": []
            })
    
    return summary_md, files_output


def _fallback_response(results: List[Any]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate fallback response when LLM is unavailable (legacy function).
    
    Args:
        results: Top Qdrant search results
        
    Returns:
        Tuple of (summary_md, files_output)
    """
    files_output = []
    for result in results:
        payload = result.payload
        files_output.append({
            "path": payload.get("file_path", "unknown"),
            "language": payload.get("language", "python"),
            "start_line": payload.get("chunk_index", 0) * 50,
            "end_line": (payload.get("chunk_index", 0) + 1) * 50,
            "snippet": _clip_text(payload.get("text", "")[:500]),
            "why_relevant": f"Top-K by vector search (score: {result.score:.2f})"
        })
    
    # Generate simple markdown summary
    summary_md = f"LLM 不可用，展示前 {len(files_output)} 条原始匹配结果。\n\n"
    summary_md += "\n".join([
        f"- **{f['path']}** (相似度: {results[i].score:.2f})" 
        for i, f in enumerate(files_output)
    ])
    
    return summary_md, files_output


def _fallback_response_hybrid(results: List[Dict[str, Any]], neighbors_map: Dict[str, List[Dict[str, Any]]] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate fallback response when LLM is unavailable (hybrid search version).
    
    Args:
        results: Top merged search results with metadata
        neighbors_map: Map of point_id -> list of neighbor dicts (optional)
        
    Returns:
        Tuple of (summary_md, files_output)
    """
    if neighbors_map is None:
        neighbors_map = {}
    
    files_output = []
    for result in results:
        point = result['point']
        payload = point.payload
        point_id = point.id
        
        # Generate why_relevant based on search source
        why_relevant = _generate_why_relevant(
            source=result['source'],
            name=result['name'],
            score=result['score'],
            original_score=result['original_score']
        )
        
        file_entry = {
            "path": payload.get("file_path", "unknown"),
            "language": payload.get("language", "python"),
            "start_line": payload.get("start_line", 0),
            "end_line": payload.get("end_line", 0),
            "snippet": _clip_text(payload.get("text", "")[:500]),
            "why_relevant": why_relevant
        }
        
        # Add neighbors if available for this point
        if point_id in neighbors_map:
            file_entry["neighbors"] = neighbors_map[point_id]
            logger.info(f"[FALLBACK] Added {len(neighbors_map[point_id])} neighbors to {file_entry['path']}")
        else:
            file_entry["neighbors"] = []
        
        files_output.append(file_entry)
    
    # Generate simple markdown summary
    summary_md = f"LLM 不可用，展示前 {len(files_output)} 条混合搜索匹配结果（向量搜索 + 符号过滤）。\n\n"
    summary_md += "\n".join([
        f"- **{f['path']}** - {f['why_relevant']}" 
        for f in files_output
    ])
    
    return summary_md, files_output

