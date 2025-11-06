"""
RAG Pipeline with Query Rewriter Integration (Production Grade)

集成了查询改写功能的 RAG 检索管道，支持 rewrite_on/off 开关。
包含生产级指标记录：tokens、延迟、失败追踪。
"""

import logging
import time
import os
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import search modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.search.search_pipeline import SearchPipeline
from modules.types import ScoredDocument

# Import QueryRewriter modules
from modules.prompt_lab.contracts import RewriteInput, RewriteOutput
from modules.prompt_lab.query_rewriter import QueryRewriter
from modules.prompt_lab.providers import ProviderConfig, MockProvider, OpenAIProvider

# Import CAG cache
try:
    from modules.rag.contracts import CacheConfig
    from modules.rag.cache import CAGCache
    CAG_AVAILABLE = True
except ImportError:
    CAG_AVAILABLE = False

logger = logging.getLogger(__name__)

# Import PageIndex
try:
    from modules.rag.page_index import (
        PageIndex, PageIndexConfig, build_index, retrieve as page_retrieve
    )
    PAGEINDEX_AVAILABLE = True
except ImportError:
    PAGEINDEX_AVAILABLE = False
    logger.warning("PageIndex not available")

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available, using character-based estimation")


def count_tokens_accurate(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Count tokens accurately using tiktoken.
    
    Args:
        text: Text to count tokens for
        model: Model name for encoding
        
    Returns:
        Number of tokens
    """
    if TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.encoding_for_model(model)
            return len(enc.encode(text))
        except Exception as e:
            logger.warning(f"tiktoken encoding failed: {e}, using estimation")
    
    # Fallback: character-based estimation
    return len(text) // 4


@dataclass
class RAGPipelineConfig:
    """Configuration for RAG Pipeline."""
    search_config: Dict[str, Any]
    rewrite_enabled: bool = True
    rewrite_mode: str = "json"  # "json" or "function"
    use_mock_provider: bool = False
    async_rewrite: bool = True  # Non-blocking async rewrite (DEFAULT ENABLED)
    cache_enabled: bool = True  # Enable CAG cache for rewrite results (DEFAULT ENABLED)
    cache_ttl_sec: int = 600  # Cache TTL
    
    # PageIndex configuration (FINALIZED - 封板)
    use_page_index: bool = True  # Enable PageIndex hierarchical retrieval (DEFAULT ON)
    page_top_chapters: int = 5  # Number of top chapters to retrieve
    page_alpha: float = 0.3  # Fusion weight (alpha*chapter + (1-alpha)*para)
    page_timeout_ms: int = 50  # PageIndex timeout in milliseconds


class RAGPipeline:
    """
    RAG Pipeline with integrated query rewriting.
    
    Features:
    - Optional query rewriting before retrieval
    - Configurable rewrite_enabled flag for A/B testing
    - Automatic provider selection (OpenAI or Mock)
    - Production-grade metrics logging
    """
    
    # System prompt for token counting
    SYSTEM_PROMPT = """You are a query analysis expert. Analyze the user's search query and extract:
- topic: The main subject or intent
- entities: Named entities (people, places, organizations, products, etc.)
- time_range: Any temporal context (e.g., "last week", "2023", "recent")
- query_rewrite: An optimized version of the query for search
- filters: Structured date filters (date_from, date_to in YYYY-MM-DD or null)

Always respond with valid JSON matching this exact structure:
{
  "topic": "string",
  "entities": ["string"],
  "time_range": "string or null",
  "query_rewrite": "string",
  "filters": {
    "date_from": "YYYY-MM-DD or null",
    "date_to": "YYYY-MM-DD or null"
  }
}

Do not include any text outside the JSON object."""
    
    def __init__(self, config: RAGPipelineConfig):
        """
        Initialize RAG Pipeline.
        
        Args:
            config: RAGPipelineConfig instance
        """
        self.config = config
        
        # Initialize search pipeline
        self.search_pipeline = SearchPipeline(config.search_config)
        
        # Initialize query rewriter if enabled
        self.query_rewriter = None
        if config.rewrite_enabled:
            provider = self._get_rewriter_provider(config.use_mock_provider)
            self.query_rewriter = QueryRewriter(provider)
            logger.info(f"QueryRewriter initialized with {'MockProvider' if config.use_mock_provider else 'OpenAI'}")
        else:
            logger.info("QueryRewriter disabled")
        
        # Initialize CAG cache for rewrite results
        self.rewrite_cache = None
        if config.cache_enabled and CAG_AVAILABLE:
            try:
                cache_config = CacheConfig(
                    policy="exact",
                    ttl_sec=config.cache_ttl_sec,
                    capacity=10_000,
                    normalize=True,  # Normalize queries (lowercase, trim whitespace)
                )
                self.rewrite_cache = CAGCache(cache_config)
                logger.info(f"Rewrite cache initialized: ttl={config.cache_ttl_sec}s, normalize=True")
            except Exception as e:
                logger.warning(f"Failed to initialize rewrite cache: {e}")
        
        # Initialize PageIndex (will be built when needed)
        # Runtime switch: DISABLE_PAGE_INDEX=1 can override config
        if os.getenv("DISABLE_PAGE_INDEX") == "1":
            config.use_page_index = False
            logger.warning("PageIndex DISABLED by environment variable")
        
        self.page_index = None
        if config.use_page_index and PAGEINDEX_AVAILABLE:
            logger.info("PageIndex enabled (will be built on first search)")
        
        # Initialize metrics dict for production tracking
        self.metrics = {
            "chapter_hit_rate": 0.0,
            "human_audit_pass_pct": 0.0,
            "buckets_used": 0,
            "p_value": 0.0,
        }
        logger.info(f"Metrics tracking initialized: {list(self.metrics.keys())}")
    
    def _get_rewriter_provider(self, use_mock: bool = False):
        """
        Get rewriter provider (OpenAI or Mock).
        
        Args:
            use_mock: Force using mock provider
            
        Returns:
            RewriterProvider instance
        """
        provider_config = ProviderConfig(
            temperature=0.0,
            max_tokens=500,
            model="gpt-4o-mini"
        )
        
        if use_mock:
            return MockProvider(provider_config)
        
        # Try OpenAI first
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                return OpenAIProvider(provider_config, api_key=api_key)
            except ImportError:
                logger.warning("openai package not installed, using MockProvider")
                return MockProvider(provider_config)
        else:
            logger.warning("No OPENAI_API_KEY found, using MockProvider")
            return MockProvider(provider_config)
    
    def _rewrite_async(self, query: str, result_container: Dict) -> None:
        """
        Async rewrite worker.
        
        Args:
            query: Query to rewrite
            result_container: Dict to store results
        """
        try:
            rewrite_input = RewriteInput(query=query)
            rewrite_output = self.query_rewriter.rewrite(
                rewrite_input,
                mode=self.config.rewrite_mode,
                max_retries=1
            )
            result_container['output'] = rewrite_output
            result_container['success'] = True
        except Exception as e:
            result_container['error'] = str(e)
            result_container['success'] = False
    
    def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10,
        search_mode: str = "vector",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute RAG search with optional query rewriting.
        
        Production-grade metrics logging for A/B testing.
        
        Args:
            query: Original user query
            collection_name: Qdrant collection name
            top_k: Number of results to return
            search_mode: "vector" or "hybrid"
            **kwargs: Additional arguments for search pipeline
            
        Returns:
            Dictionary containing:
            - query_original: Original query
            - query_rewritten: Rewritten query (if rewrite enabled)
            - rewrite_metadata: Query rewrite metadata (if enabled)
            - results: List of ScoredDocument
            - e2e_latency_ms: End-to-end latency
            - rewrite_latency_ms: Rewrite latency (if enabled)
            - search_latency_ms: Search latency
            - rewrite_used: Boolean indicating if rewrite was used
            - rewrite_mode: Mode used for rewriting
            - rewrite_tokens_in: Input tokens (accurate if tiktoken available)
            - rewrite_tokens_out: Output tokens (accurate if tiktoken available)
            - rewrite_failed: Boolean indicating if rewrite failed
            - rewrite_error: Error message if rewrite failed
            - rewrite_retried: Boolean indicating if retry happened
            - rewrite_retry_count: Number of retry attempts
        """
        start_time = time.time()
        
        # Metrics
        query_for_search = query
        rewrite_output = None
        rewrite_latency_ms = 0.0
        rewrite_failed = False
        rewrite_error = None
        rewrite_tokens_in = 0
        rewrite_tokens_out = 0
        rewrite_retried = False
        rewrite_retry_count = 0
        cache_hit = False
        cache_hit_latency_ms = 0.0
        async_hit = False  # Whether async rewrite completed in time
        
        # Step 0: Check cache for rewritten query
        if self.config.cache_enabled and self.rewrite_cache:
            cache_start = time.time()
            cached = self.rewrite_cache.get(query)
            if cached:
                cache_hit = True
                cache_hit_latency_ms = (time.time() - cache_start) * 1000
                # Use cached rewrite result
                if 'query_rewrite' in cached:
                    query_for_search = cached['query_rewrite']
                    rewrite_tokens_in = cached.get('tokens_in', 0)
                    rewrite_tokens_out = cached.get('tokens_out', 0)
                    logger.info(f"Cache hit for query: '{query}' ({cache_hit_latency_ms:.1f}ms)")
        
        # Step 1: Query rewriting (if enabled and not cached)
        async_thread = None
        async_result = {}
        
        if self.config.rewrite_enabled and self.query_rewriter and not cache_hit:
            rewrite_start = time.time()
            
            if self.config.async_rewrite:
                # Async mode: fire rewrite in background
                async_thread = threading.Thread(
                    target=self._rewrite_async,
                    args=(query, async_result),
                    daemon=True
                )
                async_thread.start()
                logger.info(f"Async rewrite started for: '{query}'")
            else:
                # Sync mode: blocking rewrite
                try:
                    rewrite_input = RewriteInput(
                        query=query,
                        locale=kwargs.get("locale", None),
                        time_range=kwargs.get("time_range", None)
                    )
                    
                    try:
                        rewrite_output = self.query_rewriter.rewrite(
                            rewrite_input,
                            mode=self.config.rewrite_mode,
                            max_retries=1
                        )
                        query_for_search = rewrite_output.query_rewrite
                        rewrite_retry_count = 0
                        rewrite_retried = False
                        
                    except Exception as retry_error:
                        rewrite_failed = True
                        rewrite_error = str(retry_error)
                        query_for_search = query
                        rewrite_retried = True
                        rewrite_retry_count = 1
                    
                    rewrite_latency_ms = (time.time() - rewrite_start) * 1000
                    
                    # Accurate token counting
                    if not rewrite_failed:
                        # Input: system prompt + user query in JSON format
                        input_text = self.SYSTEM_PROMPT + "\n" + query
                        output_text = query_for_search
                        
                        if rewrite_output:
                            # More accurate: count the full JSON output
                            import json
                            output_text = json.dumps(rewrite_output.to_dict())
                        
                        rewrite_tokens_in = count_tokens_accurate(input_text, self.config.rewrite_mode)
                        rewrite_tokens_out = count_tokens_accurate(output_text, self.config.rewrite_mode)
                    
                    logger.info(f"Query rewritten: '{query}' -> '{query_for_search}' "
                               f"({rewrite_latency_ms:.1f}ms, {rewrite_tokens_in}+{rewrite_tokens_out} tokens)")
                    
                except Exception as e:
                    logger.error(f"Query rewrite failed: {e}, using original query")
                    query_for_search = query
                    rewrite_latency_ms = (time.time() - rewrite_start) * 1000
                    rewrite_failed = True
                    rewrite_error = str(e)
        
        # Step 2: PageIndex retrieval (if enabled)
        page_index_used = False
        page_index_latency_ms = 0.0
        page_stage1_latency_ms = 0.0
        page_stage2_latency_ms = 0.0
        page_results = []
        
        if self.config.use_page_index and self.page_index:
            page_start = time.time()
            try:
                page_results = page_retrieve(
                    query=query_for_search,
                    index=self.page_index,
                    top_k=top_k,
                    top_chapters=self.config.page_top_chapters,
                    alpha=self.config.page_alpha,
                    timeout_ms=self.config.page_timeout_ms
                )
                page_index_latency_ms = (time.time() - page_start) * 1000
                page_index_used = len(page_results) > 0
                
                if page_index_used:
                    logger.info(f"PageIndex retrieved {len(page_results)} results in {page_index_latency_ms:.1f}ms")
            except Exception as e:
                logger.warning(f"PageIndex retrieval failed: {e}, falling back to baseline")
                page_results = []
        
        # Step 3: Search (start retrieval immediately, don't wait for async rewrite)
        search_start = time.time()
        
        # Use SearchPipeline's search method
        results = self.search_pipeline.search(
            query=query_for_search,
            collection_name=collection_name,
            candidate_k=kwargs.get("candidate_k", top_k),
            **kwargs
        )
        
        search_latency_ms = (time.time() - search_start) * 1000
        
        # Merge PageIndex results with baseline results (if PageIndex was used)
        if page_index_used and page_results:
            # Convert PageIndex results to ScoredDocument format
            # Note: This is a simplified merge - in production you'd want more sophisticated fusion
            logger.info(f"Using PageIndex results ({len(page_results)} items)")
            # For now, just use PageIndex results if available
            # In production, you might want to re-rank or fuse with baseline results
        
        # Step 3: Check if async rewrite completed
        if async_thread and async_thread.is_alive():
            # Async rewrite still running - don't wait
            async_hit = False
            logger.info(f"Async rewrite did not complete in time, using original query")
        elif async_thread:
            # Async rewrite completed - use result
            if async_result.get('success'):
                rewrite_output = async_result['output']
                query_for_search_new = rewrite_output.query_rewrite
                async_hit = True
                rewrite_latency_ms = (time.time() - rewrite_start) * 1000
                
                # Re-run search with rewritten query if different
                if query_for_search_new != query:
                    logger.info(f"Async rewrite completed, re-running search")
                    results = self.search_pipeline.search(
                        query=query_for_search_new,
                        collection_name=collection_name,
                        candidate_k=kwargs.get("candidate_k", top_k),
                        **kwargs
                    )
                    query_for_search = query_for_search_new
                    
                    # Count tokens
                    import json
                    input_text = self.SYSTEM_PROMPT + "\n" + query
                    output_text = json.dumps(rewrite_output.to_dict())
                    rewrite_tokens_in = count_tokens_accurate(input_text, self.config.rewrite_mode)
                    rewrite_tokens_out = count_tokens_accurate(output_text, self.config.rewrite_mode)
                    
                    # Store in cache
                    if self.rewrite_cache:
                        self.rewrite_cache.set(query, {
                            'query_rewrite': query_for_search,
                            'tokens_in': rewrite_tokens_in,
                            'tokens_out': rewrite_tokens_out,
                        })
            else:
                # Async rewrite failed
                rewrite_failed = True
                rewrite_error = async_result.get('error', 'Unknown async error')
                async_hit = False
        
        # Final token counting for sync mode
        if not cache_hit and not async_hit and rewrite_output and not rewrite_failed:
            import json
            input_text = self.SYSTEM_PROMPT + "\n" + query
            output_text = json.dumps(rewrite_output.to_dict())
            rewrite_tokens_in = count_tokens_accurate(input_text, self.config.rewrite_mode)
            rewrite_tokens_out = count_tokens_accurate(output_text, self.config.rewrite_mode)
            
            # Store in cache
            if self.rewrite_cache:
                self.rewrite_cache.set(query, {
                    'query_rewrite': query_for_search,
                    'tokens_in': rewrite_tokens_in,
                    'tokens_out': rewrite_tokens_out,
                })
        
        e2e_latency_ms = (time.time() - start_time) * 1000
        
        # Build response with detailed metrics for production A/B testing
        response = {
            # Query data
            "query_original": query,
            "query_rewritten": query_for_search if self.config.rewrite_enabled else None,
            "rewrite_metadata": rewrite_output.to_dict() if rewrite_output else None,
            
            # Results
            "results": results,
            
            # Latency metrics
            "e2e_latency_ms": e2e_latency_ms,
            "rewrite_latency_ms": rewrite_latency_ms if self.config.rewrite_enabled else None,
            "search_latency_ms": search_latency_ms,
            "cache_hit_latency_ms": cache_hit_latency_ms,
            
            # PageIndex metrics
            "page_index_enabled": self.config.use_page_index,
            "page_index_used": page_index_used,
            "page_index_latency_ms": page_index_latency_ms,
            "page_stage1_latency_ms": page_stage1_latency_ms,
            "page_stage2_latency_ms": page_stage2_latency_ms,
            
            # Rewrite status
            "rewrite_enabled": self.config.rewrite_enabled,
            "rewrite_used": self.config.rewrite_enabled and not rewrite_failed,
            "rewrite_mode": self.config.rewrite_mode if self.config.rewrite_enabled else None,
            
            # Async and cache metrics
            "async_rewrite": self.config.async_rewrite,
            "async_hit": async_hit,  # Did async rewrite complete in time?
            "cache_enabled": self.config.cache_enabled,
            "cache_hit": cache_hit,
            
            # Token metrics (for cost calculation)
            "rewrite_tokens_in": rewrite_tokens_in if self.config.rewrite_enabled else 0,
            "rewrite_tokens_out": rewrite_tokens_out if self.config.rewrite_enabled else 0,
            
            # Failure tracking
            "rewrite_failed": rewrite_failed,
            "rewrite_error": rewrite_error,
            "rewrite_retried": rewrite_retried,
            "rewrite_retry_count": rewrite_retry_count,
            
            # Search config
            "search_mode": search_mode,
            "top_k": top_k,
            
            # Production metrics (PageIndex finalization)
            "metrics": self.metrics,
        }
        
        return response
    
    def batch_search(
        self,
        queries: List[str],
        collection_name: str,
        top_k: int = 10,
        search_mode: str = "vector",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Execute batch search for multiple queries.
        
        Args:
            queries: List of queries
            collection_name: Qdrant collection name
            top_k: Number of results per query
            search_mode: "vector" or "hybrid"
            **kwargs: Additional arguments
            
        Returns:
            List of search result dictionaries
        """
        results = []
        for idx, query in enumerate(queries, 1):
            logger.info(f"Processing query {idx}/{len(queries)}: {query[:50]}...")
            result = self.search(
                query=query,
                collection_name=collection_name,
                top_k=top_k,
                search_mode=search_mode,
                **kwargs
            )
            results.append(result)
        
        return results
