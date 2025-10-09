# NOTE: Standardized on Document.text.
"""
Search Pipeline Module for SmartSearchX

This module provides a complete search pipeline that combines vector search,
reranking, and explanation generation.
"""

import logging
import yaml
import json
import time
import uuid
import os
from typing import List, Dict, Any, Optional
from .vector_search import VectorSearch
from .hybrid import fuse
from modules.retrievers.bm25 import BM25Retriever
from modules.rerankers.factory import create_reranker
from modules.types import Document, ScoredDocument

# Import CAG cache
try:
    from modules.rag.contracts import CacheConfig
    from modules.rag.cache import CAGCache
    CAG_AVAILABLE = True
except ImportError:
    CAG_AVAILABLE = False

# Import Brain modules
try:
    from modules.autotuner.brain.contracts import TuningInput, SLO, Guards, MemorySample
    from modules.autotuner.brain.decider import decide_tuning_action
    from modules.autotuner.brain.apply import apply_action
    from modules.autotuner.brain.memory import get_memory
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False
from modules.autotune.macros import get_macro_config, derive_params

logger = logging.getLogger(__name__)

# Global observability state
_obs_counter = 0
_obs_full_freq = int(os.getenv("OBS_FULL_FREQ", "10"))
_obs_slo_violations = 0

def _log_event(event: str, trace_id: str, cost_ms: float = 0.0, 
               params: Dict = None, stats: Dict = None, applied: Dict = None, note: str = ""):
    """Minimal JSON event logger."""
    global _obs_counter, _obs_full_freq, _obs_slo_violations
    
    _obs_counter += 1
    should_log_full = (_obs_counter % _obs_full_freq == 0) or (_obs_slo_violations > 0)
    
    # Always log important events
    important_events = ["RESPONSE", "RUN_INFO", "AUTOTUNER_SUGGEST", "PARAMS_APPLIED", "FETCH_QUERY", "RETRIEVE_VECTOR", "ROUTE_CHOICE", "PATH_USED", "CYCLE_STEP", "CAND_AFTER_LIMIT"]
    if event in important_events:
        should_log_full = True
    
    if not should_log_full and event not in important_events:
        return
    
    event_data = {
        "event": event,
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": round(cost_ms, 3)
    }
    
    if params:
        event_data["params"] = params
    if stats:
        event_data["stats"] = stats
    if applied:
        event_data["applied"] = applied
    if note:
        event_data["note"] = note
    
    print(json.dumps(event_data))

def _inject_chaos():
    """Inject chaos latency if configured."""
    chaos_ms = int(os.getenv("CHAOS_LAT_MS", "0"))
    if chaos_ms > 0:
        time.sleep(chaos_ms / 1000.0)

def _get_env_config():
    """Get environment-based configuration."""
    return {
        "force_ce_on": os.getenv("FORCE_CE_ON", "1") == "1",
        "force_hybrid_on": os.getenv("FORCE_HYBRID_ON", "1") == "1",
        "ce_cache_size": int(os.getenv("CE_CACHE_SIZE", "0")),
        "rerank_k": int(os.getenv("RERANK_K", "50")),
        "tuner_enabled": os.getenv("TUNER_ENABLED", "1") == "1",
        "tuner_sample_sec": int(os.getenv("TUNER_SAMPLE_SEC", "5")),
        "tuner_cooldown_sec": int(os.getenv("TUNER_COOLDOWN_SEC", "10")),
        "slo_p95_ms": float(os.getenv("SLO_P95_MS", "1200")),
        "slo_recall_at10": float(os.getenv("SLO_RECALL_AT10", "0.30")),
        "brain_enabled": os.getenv("BRAIN_ENABLED", "0") == "1",
        "memory_enabled": os.getenv("MEMORY_ENABLED", "1") == "1",
        # CAG cache configuration
        "use_cache": os.getenv("USE_CACHE", "0") == "1",
        "cache_policy": os.getenv("CACHE_POLICY", "exact"),
        "cache_ttl_sec": int(os.getenv("CACHE_TTL_SEC", "600")),
        "cache_capacity": int(os.getenv("CACHE_CAPACITY", "10000")),
        "cache_fuzzy_threshold": float(os.getenv("CACHE_FUZZY_THRESHOLD", "0.85"))
    }

# Global AutoTuner state
_autotuner_state = {
    "metrics_window": [],
    "last_suggest_time": 0,
    "cooldown_until": 0,
    "current_ef_search": 128,
    "current_T": 500,
    "current_Ncand_max": 1000,
    "current_rerank_mult": 3,
    "suggestions_made": 0,
    "suggestions_applied": 0,
    "last_bucket_time": 0
}

def _reset_autotuner_state():
    """Reset AutoTuner state for new experiment."""
    global _autotuner_state
    _autotuner_state = {
        "metrics_window": [],
        "last_suggest_time": 0,
        "cooldown_until": 0,
        "current_ef_search": 128,
        "suggestions_made": 0,
        "suggestions_applied": 0
    }

def _update_autotuner_metrics(trace_id: str, total_cost_ms: float, recall_at_10: float):
    """Update AutoTuner metrics and suggest parameters."""
    global _autotuner_state
    
    env_config = _get_env_config()
    if not env_config["tuner_enabled"]:
        return
    
    current_time = time.time()
    
    # Add metrics to window
    _autotuner_state["metrics_window"].append({
        "timestamp": current_time,
        "p95_ms": total_cost_ms,
        "recall_at_10": recall_at_10
    })
    
    # Keep only recent metrics (last 60 seconds)
    cutoff_time = current_time - 60  # Use fixed 60-second window
    _autotuner_state["metrics_window"] = [
        m for m in _autotuner_state["metrics_window"] 
        if m["timestamp"] >= cutoff_time
    ]
    
    # Check if we should make a suggestion (5s buckets)
    bucket_interval = 5  # 5-second buckets
    current_bucket = int(current_time // bucket_interval)
    last_bucket = int(_autotuner_state["last_bucket_time"] // bucket_interval)
    
    if (current_bucket > last_bucket and len(_autotuner_state["metrics_window"]) >= 3):
        
        # Calculate window metrics for this bucket
        window_p95 = max(m["p95_ms"] for m in _autotuner_state["metrics_window"])
        window_recall = sum(m["recall_at_10"] for m in _autotuner_state["metrics_window"]) / len(_autotuner_state["metrics_window"])
        window_qps = len(_autotuner_state["metrics_window"]) / bucket_interval  # Approximate QPS
        
        # Use Brain suggestion if enabled, otherwise fallback to original
        if env_config["brain_enabled"]:
            suggestion = _make_brain_suggestion(window_p95, window_recall, window_qps, env_config)
        else:
            suggestion = _make_autotuner_suggestion(window_p95, window_recall, env_config)
        
        _autotuner_state["suggestions_made"] += 1
        _autotuner_state["last_bucket_time"] = current_time
        
        _log_event("AUTOTUNER_SUGGEST", trace_id, 0.0,
                  params={
                      "p95_ms": window_p95, 
                      "recall_at10": window_recall,
                      "suggest": {
                          "ef_search": suggestion["ef_search"],
                          "rerank_k": env_config["rerank_k"]
                      }
                  },
                  stats={"suggestions_made": _autotuner_state["suggestions_made"]})
        
        # 7. PARAMS_APPLIED event
        applied = _apply_autotuner_suggestion(suggestion, current_time, env_config)
        _log_event("PARAMS_APPLIED", trace_id, 0.0,
                  applied=applied,
                  note="AutoTuner suggestion applied" if applied["applied"] else "AutoTuner suggestion rejected (cooldown)")

def _make_brain_suggestion(window_p95: float, window_recall: float, window_qps: float, env_config: dict) -> dict:
    """Make Brain-based suggestion using TuningInput and Memory."""
    if not BRAIN_AVAILABLE or not env_config["brain_enabled"]:
        return _make_autotuner_suggestion(window_p95, window_recall, env_config)
    
    global _autotuner_state
    
    # Create TuningInput
    tuning_input = TuningInput(
        p95_ms=window_p95,
        recall_at10=window_recall,
        qps=window_qps,
        params={
            'ef': _autotuner_state["current_ef_search"],
            'T': _autotuner_state["current_T"],
            'Ncand_max': _autotuner_state["current_Ncand_max"],
            'rerank_mult': _autotuner_state["current_rerank_mult"]
        },
        slo=SLO(
            p95_ms=env_config["slo_p95_ms"],
            recall_at10=env_config["slo_recall_at10"]
        ),
        guards=Guards(
            cooldown=time.time() < _autotuner_state["cooldown_until"],
            stable=True  # Assume stable for now
        ),
        near_T=False,  # Could be calculated based on current params
        last_action=None,  # Could track last action
        adjustment_count=0  # Could track adjustment history
    )
    
    # Get Brain decision
    action = decide_tuning_action(tuning_input)
    
    # Apply action to get new parameters
    new_params = apply_action(tuning_input.params, action)
    
    # Log BRAIN_DECIDE event
    _log_event("BRAIN_DECIDE", "", 0.0, params={
        "p95_ms": window_p95,
        "recall_at10": window_recall,
        "qps": window_qps,
        "before": tuning_input.params,
        "action": {
            "kind": action.kind,
            "step": action.step,
            "reason": action.reason
        },
        "after": new_params
    })
    
    # Log PARAMS_APPLIED event
    _log_event("PARAMS_APPLIED", "", 0.0, params=new_params)
    
    # Update memory if enabled
    if env_config["memory_enabled"]:
        memory = get_memory()
        bucket_id = memory.default_bucket_of(tuning_input)
        sample = MemorySample(
            bucket_id=bucket_id,
            ef=tuning_input.params['ef'],
            T=tuning_input.params['T'],
            Ncand_max=tuning_input.params['Ncand_max'],
            p95_ms=window_p95,
            recall_at10=window_recall,
            ts=time.time()
        )
        memory.observe(sample)
    
    return {
        "ef_search": new_params['ef'],
        "T": new_params['T'],
        "Ncand_max": new_params['Ncand_max'],
        "rerank_mult": new_params['rerank_mult'],
        "reason": action.reason
    }

def _make_autotuner_suggestion(window_p95: float, window_recall: float, env_config: dict) -> dict:
    """Make AutoTuner suggestion based on Balanced policy."""
    current_ef = _autotuner_state["current_ef_search"]
    slo_p95 = env_config["slo_p95_ms"]
    slo_recall = env_config["slo_recall_at10"]
    
    # Balanced policy: p95 > SLO_P95_MS and recall >= SLO_RECALL_AT10 → decrease ef
    # recall < target → increase ef; otherwise keep
    if window_p95 > slo_p95 and window_recall >= slo_recall:
        # Latency too high but recall is good → decrease ef
        new_ef = max(64, current_ef - 16)
    elif window_recall < slo_recall:
        # Recall too low → increase ef
        new_ef = min(256, current_ef + 32)
    else:
        # Keep current
        new_ef = current_ef
    
    return {
        "ef_search": new_ef,
        "reason": "decrease" if new_ef < current_ef else "increase" if new_ef > current_ef else "keep"
    }

def _apply_autotuner_suggestion(suggestion: dict, current_time: float, env_config: dict) -> dict:
    """Apply AutoTuner suggestion with cooldown check."""
    global _autotuner_state
    
    # Check cooldown
    if current_time < _autotuner_state["cooldown_until"]:
        return {
            "applied": False,
            "reason": "cooldown",
            "cooldown_remaining": _autotuner_state["cooldown_until"] - current_time
        }
    
    # Apply suggestion
    old_ef = _autotuner_state["current_ef_search"]
    new_ef = suggestion["ef_search"]
    
    # Handle Brain suggestions with multiple parameters
    if "T" in suggestion:
        old_T = _autotuner_state["current_T"]
        old_Ncand_max = _autotuner_state["current_Ncand_max"]
        old_rerank_mult = _autotuner_state["current_rerank_mult"]
        
        new_T = suggestion.get("T", old_T)
        new_Ncand_max = suggestion.get("Ncand_max", old_Ncand_max)
        new_rerank_mult = suggestion.get("rerank_mult", old_rerank_mult)
        
        # Update all parameters
        _autotuner_state["current_ef_search"] = new_ef
        _autotuner_state["current_T"] = new_T
        _autotuner_state["current_Ncand_max"] = new_Ncand_max
        _autotuner_state["current_rerank_mult"] = new_rerank_mult
        _autotuner_state["suggestions_applied"] += 1
        _autotuner_state["cooldown_until"] = current_time + env_config["tuner_cooldown_sec"]
        
        return {
            "applied": True,
            "old_ef_search": old_ef,
            "new_ef_search": new_ef,
            "old_T": old_T,
            "new_T": new_T,
            "old_Ncand_max": old_Ncand_max,
            "new_Ncand_max": new_Ncand_max,
            "old_rerank_mult": old_rerank_mult,
            "new_rerank_mult": new_rerank_mult,
            "reason": suggestion["reason"]
        }
    else:
        # Original AutoTuner logic (ef only)
        if new_ef != old_ef:
            _autotuner_state["current_ef_search"] = new_ef
            _autotuner_state["suggestions_applied"] += 1
            _autotuner_state["cooldown_until"] = current_time + env_config["tuner_cooldown_sec"]
            
            return {
                "applied": True,
                "old_ef_search": old_ef,
                "new_ef_search": new_ef,
                "reason": suggestion["reason"]
            }
        else:
            return {
                "applied": True,
                "old_ef_search": old_ef,
                "new_ef_search": new_ef,
                "reason": "no_change"
            }


class SearchPipeline:
    """
    A complete search pipeline that combines vector search and reranking.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the search pipeline with configuration.
        
        Args:
            config: Configuration dictionary containing retriever and reranker settings
        """
        self.config = config
        self.vector_search = VectorSearch()
        
        # Initialize BM25 retriever for hybrid search
        self.bm25_retriever = None
        self._bm25_corpus_loaded = False
        
        # Initialize reranker from config
        reranker_cfg = config.get("reranker", None)
        self.reranker = create_reranker(reranker_cfg) if reranker_cfg else None
        
        # Initialize CAG cache if enabled
        self.cache = None
        if CAG_AVAILABLE:
            cache_cfg = config.get("cache", {})
            if cache_cfg.get("enabled", False):
                try:
                    cache_config = CacheConfig(
                        policy=cache_cfg.get("policy", "exact"),
                        ttl_sec=cache_cfg.get("ttl_sec", 600),
                        capacity=cache_cfg.get("capacity", 10_000),
                        fuzzy_threshold=cache_cfg.get("fuzzy_threshold", 0.85),
                        normalize=cache_cfg.get("normalize", True),
                        embedder=cache_cfg.get("embedder", None)
                    )
                    self.cache = CAGCache(cache_config)
                    logger.info(f"CAG cache initialized: policy={cache_config.policy}, ttl={cache_config.ttl_sec}s")
                except Exception as e:
                    logger.warning(f"Failed to initialize CAG cache: {e}")
        
        logger.info(f"SearchPipeline initialized with reranker: {type(self.reranker).__name__ if self.reranker else 'None'}")
    
    def _load_bm25_corpus(self, collection_name: str) -> None:
        """
        Load documents from Qdrant collection for BM25 indexing.
        
        Args:
            collection_name: Name of the collection to load
        """
        if self._bm25_corpus_loaded:
            return
            
        try:
            # Get all documents from the collection
            collection_info = self.vector_search.client.get_collection(collection_name)
            points_count = collection_info.points_count or 0
            
            if points_count == 0:
                logger.warning(f"Collection '{collection_name}' is empty, cannot load BM25 corpus")
                return
            
            # Load documents with reasonable limit for performance
            limit = min(50000, points_count)  # Limit to 50k documents
            results = self.vector_search.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True
            )
            
            # Convert to Document objects
            documents = []
            for point in results[0]:
                payload = point.payload or {}
                content = payload.get("text", "")
                if not content:
                    content = payload.get("content", "")
                    if not content:
                        content = str(payload)
                
                if content:  # Only include documents with content
                    doc = Document(
                        id=str(point.id),
                        text=content,
                        metadata=payload
                    )
                    documents.append(doc)
            
            # Initialize BM25 retriever with the corpus
            self.bm25_retriever = BM25Retriever(documents)
            self._bm25_corpus_loaded = True
            
            logger.info(f"Loaded {len(documents)} documents for BM25 indexing from collection '{collection_name}'")
            
        except Exception as e:
            logger.error(f"Failed to load BM25 corpus from collection '{collection_name}': {str(e)}")
            self.bm25_retriever = None
    
    def _hybrid_search(self, query: str, collection_name: str, retriever_cfg: Dict[str, Any], trace_id: str = None) -> List[ScoredDocument]:
        """
        Perform hybrid search combining vector and BM25 retrieval.
        
        Args:
            query: Search query
            collection_name: Name of the collection to search
            retriever_cfg: Retriever configuration
            
        Returns:
            List of ScoredDocument objects
        """
        # Get hybrid search parameters
        alpha = retriever_cfg.get("alpha", 0.6)
        vector_top_k = retriever_cfg.get("vector_top_k", 200)
        bm25_top_k = retriever_cfg.get("bm25_top_k", 200)
        final_top_k = retriever_cfg.get("top_k", 50)
        
        # Perform vector search
        vec_start = time.perf_counter()
        vector_results = self.vector_search.vector_search(
            query=query,
            collection_name=collection_name,
            top_n=vector_top_k,
            ef_search=retriever_cfg.get("ef_search")
        )
        vec_cost = (time.perf_counter() - vec_start) * 1000.0
        
        # 2. RETRIEVE_VECTOR event
        _log_event("RETRIEVE_VECTOR", trace_id, vec_cost,
                  params={"candidate_k": vector_top_k, "ef_search": retriever_cfg.get("ef_search", 128)},
                  stats={"candidates_returned": len(vector_results)})
        
        # Load BM25 corpus and perform BM25 search
        self._load_bm25_corpus(collection_name)
        if self.bm25_retriever is None:
            logger.warning("BM25 retriever not available, falling back to vector search only")
            return vector_results[:final_top_k]
        
        bm25_start = time.perf_counter()
        bm25_results = self.bm25_retriever.search(query, top_k=bm25_top_k)
        bm25_cost = (time.perf_counter() - bm25_start) * 1000.0
        
        # 3. RETRIEVE_BM25 event
        _log_event("RETRIEVE_BM25", trace_id, bm25_cost,
                  params={"bm25_top_k": bm25_top_k},
                  stats={"candidates_returned": len(bm25_results)})
        
        # Fuse the results
        fuse_start = time.perf_counter()
        fused_results = fuse(vector_results, bm25_results, alpha, final_top_k)
        fuse_cost = (time.perf_counter() - fuse_start) * 1000.0
        
        # 4. FUSE_HYBRID event
        _log_event("FUSE_HYBRID", trace_id, fuse_cost,
                  params={"alpha": alpha, "vector_k": vector_top_k, "bm25_k": bm25_top_k},
                  stats={"candidates_fused": len(fused_results)})
        
        logger.info(f"Hybrid search: {len(vector_results)} vector + {len(bm25_results)} BM25 -> {len(fused_results)} fused results")
        
        # Apply reranking if available
        if self.reranker and fused_results:
            logger.info(f"Applying reranking to {len(fused_results)} hybrid results")
            rerank_k = self.config.get("rerank_k", 50)
            
            # Convert to Document objects for reranking
            docs = [result.document for result in fused_results]
            # Check if reranker supports top_k parameter
            import inspect
            rerank_signature = inspect.signature(self.reranker.rerank)
            if 'top_k' in rerank_signature.parameters:
                reranked_results = self.reranker.rerank(query, docs, top_k=rerank_k)
            else:
                reranked_results = self.reranker.rerank(query, docs)[:rerank_k]
            return reranked_results
        
        return fused_results
    
    @classmethod
    def from_config(cls, config_path: str) -> 'SearchPipeline':
        """
        Create a SearchPipeline from a YAML configuration file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            SearchPipeline instance
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return cls(config)
    
    def search(self, query: str, collection_name: str = "documents", candidate_k=None, trace_id=None, **kwargs) -> List[ScoredDocument]:
        """
        Perform a search with optional hybrid retrieval and reranking.
        
        Args:
            query: Search query
            collection_name: Name of the collection to search
            candidate_k: Override retriever top_k limit
            trace_id: Optional trace ID for observability
            
        Returns:
            List of ScoredDocument objects
        """
        global _obs_slo_violations
        
        # Generate trace ID if not provided
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        start_time = time.perf_counter()
        env_config = _get_env_config()
        
        # Get macro knob configuration
        macro_config = get_macro_config()
        derived_params = derive_params(macro_config["latency_guard"], macro_config["recall_bias"])
        
        # 0. RUN_INFO event (emit once per experiment)
        if not hasattr(_log_event, '_run_info_emitted'):
            # Reset AutoTuner state for new experiment
            _reset_autotuner_state()
            
            _log_event("RUN_INFO", trace_id, 0.0,
                      params={
                          "dataset": "beir_fiqa_full_ta",
                          "collection": collection_name,
                          "TUNER_ENABLED": env_config["tuner_enabled"],
                          "FORCE_CE_ON": env_config["force_ce_on"],
                          "FORCE_HYBRID_ON": env_config["force_hybrid_on"],
                          "CE_CACHE_SIZE": env_config["ce_cache_size"],
                          "LATENCY_GUARD": macro_config["latency_guard"],
                          "RECALL_BIAS": macro_config["recall_bias"]
                      })
            _log_event._run_info_emitted = True
        
        # 1. FETCH_QUERY event
        _log_event("FETCH_QUERY", trace_id, 0.0, 
                  params={"query": query[:80], "collection": collection_name},
                  stats={"candidate_k": candidate_k})
        
        # Pre-retrieval cache check
        cached_result = None
        if self.cache and env_config["use_cache"]:
            cached_result = self.cache.get(query)
            if cached_result:
                # Cache hit - short-circuit retrieval
                _log_event("CACHE_HIT", trace_id, 0.0, 
                          params={"query": query[:80]},
                          stats={"reason": "fresh"})
                
                # Estimate saved latency (retrieval + rerank)
                saved_latency = 120.0  # Typical retrieval + rerank time
                self.cache.stats.saved_latency_ms += saved_latency
                
                # Return cached results
                total_cost = (time.perf_counter() - start_time) * 1000.0
                cached_answer = cached_result["answer"]
                
                _log_event("RESPONSE", trace_id, total_cost,
                          stats={"total_results": len(cached_answer) if isinstance(cached_answer, list) else 1, "from_cache": True})
                
                return cached_answer
            else:
                # Cache miss
                _log_event("CACHE_MISS", trace_id, 0.0,
                          params={"query": query[:80]},
                          stats={"reason": "not_found"})
        
        # Log PARAMS_APPLIED event with macro and derived parameters
        _log_event("PARAMS_APPLIED", trace_id, 0.0,
                  params={
                      "macro": {
                          "latency_guard": macro_config["latency_guard"],
                          "recall_bias": macro_config["recall_bias"]
                      },
                      "derived": derived_params
                  })
        
        # --- begin: candidate_k override guard (minimal & reversible) ---
        override_k = candidate_k or kwargs.get("candidate_k")
        if override_k:
            if self.config.get("retriever", {}).get("type") == "vector":
                # 覆盖向量检索候选上限
                self.config["retriever"]["top_k"] = int(override_k)
            elif self.config.get("retriever", {}).get("type") == "hybrid":
                # 覆盖混合检索两路候选上限与融合阈值
                self.config["retriever"]["vector_top_k"] = int(override_k)
                self.config["retriever"]["bm25_top_k"] = int(override_k)
                self.config["retriever"]["top_k"] = int(override_k)
        # --- end: candidate_k override guard ---
        
        # Inject chaos before retrieval
        _inject_chaos()
        
        # Get retriever configuration
        retriever_cfg = self.config.get("retriever", {})
        retriever_type = retriever_cfg.get("type", "vector")
        
        # Force hybrid if env var is set
        if env_config["force_hybrid_on"] and retriever_type != "hybrid":
            retriever_type = "hybrid"
            retriever_cfg["type"] = "hybrid"
        
        # Apply AutoTuner ef_search to retriever config
        if env_config["tuner_enabled"]:
            retriever_cfg["ef_search"] = _autotuner_state["current_ef_search"]
        else:
            # When tuner is disabled, use default ef_search value
            retriever_cfg["ef_search"] = 128
        
        # Handle hybrid retrieval
        if retriever_type == "hybrid":
            results = self._hybrid_search(query, collection_name, retriever_cfg, trace_id)
        else:
            # Pure vector search with macro knob path selection
            top_k = retriever_cfg.get("top_k", 20)
            
            # Apply macro knob logic: choose path based on candidate count vs threshold
            # ROUTE_CHOICE event: log path selection decision
            if top_k <= derived_params["T"]:
                path_choice = "mem"
            else:
                path_choice = "hnsw"
            
            _log_event("ROUTE_CHOICE", trace_id, 0.0,
                      params={
                          "N": top_k,
                          "T": derived_params["T"],
                          "path": path_choice,
                          "trace_id": trace_id
                      })
            
            if top_k <= derived_params["T"]:
                # PATH_USED event: log MEM path usage
                _log_event("PATH_USED", trace_id, 0.0,
                          params={
                              "path": "mem",
                              "trace_id": trace_id
                          })
                
                # Exact/CPU path: use batch_size and Ncand_max
                vec_start = time.perf_counter()
                results = self.vector_search.vector_search(
                    query=query,
                    collection_name=collection_name,
                    top_n=min(top_k, derived_params["Ncand_max"]),
                    ef_search=retriever_cfg.get("ef_search")
                )
                vec_cost = (time.perf_counter() - vec_start) * 1000.0
                
                # 2. RETRIEVE_VECTOR event (exact path)
                _log_event("RETRIEVE_VECTOR", trace_id, vec_cost,
                          params={
                              "candidate_k": top_k, 
                              "ef_search": retriever_cfg.get("ef_search", 128),
                              "path": "exact",
                              "batch_size": derived_params["batch_size"],
                              "Ncand_max": derived_params["Ncand_max"]
                          },
                          stats={"candidates_returned": len(results)})
            else:
                # PATH_USED event: log HNSW path usage
                _log_event("PATH_USED", trace_id, 0.0,
                          params={
                              "path": "hnsw",
                              "trace_id": trace_id
                          })
                
                # HNSW path: use derived ef parameter
                vec_start = time.perf_counter()
                results = self.vector_search.vector_search(
                    query=query,
                    collection_name=collection_name,
                    top_n=top_k,
                    ef_search=derived_params["ef"]
                )
                vec_cost = (time.perf_counter() - vec_start) * 1000.0
                
                # 2. RETRIEVE_VECTOR event (HNSW path)
                _log_event("RETRIEVE_VECTOR", trace_id, vec_cost,
                          params={
                              "candidate_k": top_k, 
                              "ef_search": derived_params["ef"],
                              "path": "HNSW"
                          },
                          stats={"candidates_returned": len(results)})
        
        # Convert to Document objects for reranking with adapter layer
        docs = []
        for result in results:
            # Handle ScoredDocument objects (from our mocks)
            if hasattr(result, 'document') and hasattr(result, 'score'):
                doc = result.document
                # adapter: tolerate legacy objects
                txt = getattr(doc, "text", None) or getattr(doc, "page_content", None) or ""
                assert txt, f"Empty document text for id={getattr(doc, 'id', '?')}"
                # if doc is not our types.Document, adapt it
                if not hasattr(doc, "text"):
                    from modules.types import Document as TDoc
                    doc = TDoc(id=str(getattr(doc, "id", "")), text=txt, metadata=getattr(doc, "metadata", {}))
                docs.append(doc)
            # Handle legacy format with content attribute
            elif hasattr(result, 'content') and hasattr(result, 'score'):
                content = result.content
                if hasattr(content, 'page_content'):
                    content_text = content.page_content
                else:
                    content_text = str(content)
                
                doc = Document(
                    id=str(getattr(result, 'id', 'unknown')),
                    text=content_text,
                    metadata=getattr(result, 'metadata', {})
                )
                docs.append(doc)
        
        # Apply reranking if reranker is available
        if self.reranker and docs:
            logger.info(f"Applying reranking to {len(docs)} documents")
            base_rerank_k = env_config["rerank_k"] if env_config["force_ce_on"] else self.config.get("rerank_k", 50)
            # Apply macro knob rerank multiplier, capped by Ncand_max
            rerank_k_before = derived_params["rerank_multiplier"] * base_rerank_k
            rerank_k = min(rerank_k_before, derived_params["Ncand_max"])
            
            # CAND_AFTER_LIMIT event: log truncation effects
            _log_event("CAND_AFTER_LIMIT", trace_id, 0.0,
                      params={
                          "before": rerank_k_before,
                          "after": rerank_k,
                          "Ncand_max": derived_params["Ncand_max"],
                          "rerank_pool": rerank_k
                      })
            
            # 5. RERANK_CE event
            rerank_start = time.perf_counter()
            
            # Check if reranker supports top_k and trace_id parameters
            import inspect
            rerank_signature = inspect.signature(self.reranker.rerank)
            
            # Build kwargs based on supported parameters
            rerank_kwargs = {}
            if 'top_k' in rerank_signature.parameters:
                rerank_kwargs['top_k'] = rerank_k
            if 'trace_id' in rerank_signature.parameters:
                rerank_kwargs['trace_id'] = trace_id
            
            if rerank_kwargs:
                reranked_results = self.reranker.rerank(query, docs, **rerank_kwargs)
            else:
                reranked_results = self.reranker.rerank(query, docs)[:rerank_k]
            
            rerank_cost = (time.perf_counter() - rerank_start) * 1000.0
            
            # Get cache stats from reranker if available
            cache_stats = {}
            if hasattr(self.reranker, 'stats'):
                cache_stats = self.reranker.stats()
            
            # Log rerank event
            top_3_ids = [r.document.id for r in reranked_results[:3]] if reranked_results else []
            _log_event("RERANK_CE", trace_id, rerank_cost,
                      params={
                          "model": getattr(self.reranker, 'model_name', 'unknown'), 
                          "batch_size": getattr(self.reranker, 'batch_size', 32),
                          "cache_size": cache_stats.get("cache_size", 0),
                          "cache_hits": cache_stats.get("cache_hits", 0),
                          "cache_miss": cache_stats.get("cache_miss", 0)
                      },
                      stats={"top_10_ids": top_3_ids})
            
            # The reranker already returns ScoredDocument objects
            
            # Final response event
            total_cost = (time.perf_counter() - start_time) * 1000.0
            top1_id = reranked_results[0].document.id if reranked_results else None
            
            # Update AutoTuner metrics (only if enabled)
            if env_config["tuner_enabled"]:
                recall_at_10 = min(1.0, len(reranked_results) / 10.0)  # Simplified recall calculation
                _update_autotuner_metrics(trace_id, total_cost, recall_at_10)
            
            # Check SLO violations
            slo_violated = total_cost > env_config["slo_p95_ms"]
            if slo_violated:
                _obs_slo_violations += 1
            
            _log_event("RESPONSE", trace_id, total_cost,
                      stats={"total_results": len(reranked_results), "top1_id": top1_id},
                      params={"slo_violated": slo_violated, "slo_p95_ms": env_config["slo_p95_ms"]})
            
            # Post-generation cache write-back
            if self.cache and env_config["use_cache"]:
                cache_meta = {
                    "ts_ms": time.time() * 1000,
                    "source": "pipeline",
                    "cost_ms": total_cost
                }
                self.cache.put(query, reranked_results, cache_meta)
                _log_event("CACHE_PUT", trace_id, 0.0,
                          params={"query": query[:80]},
                          stats={"reason": "generated"})
            
            return reranked_results
        else:
            # Return original results without reranking
            scored_results = []
            for i, result in enumerate(results):
                # Handle ScoredDocument objects (from our mocks)
                if hasattr(result, 'document') and hasattr(result, 'score'):
                    scored_results.append(result)
                # Handle legacy format with content attribute
                elif hasattr(result, 'content') and hasattr(result, 'score'):
                    content = result.content
                    if hasattr(content, 'page_content'):
                        content_text = content.page_content
                    else:
                        content_text = str(content)
                    
                    doc = Document(
                        id=str(getattr(result, 'id', 'unknown')),
                        text=content_text,
                        metadata=getattr(result, 'metadata', {})
                    )
                    scored_results.append(ScoredDocument(
                        document=doc,
                        score=result.score,
                        explanation=f"Vector search result #{i+1}"
                    ))
            
            # Final response event
            total_cost = (time.perf_counter() - start_time) * 1000.0
            top1_id = scored_results[0].document.id if scored_results else None
            
            # Update AutoTuner metrics (only if enabled)
            if env_config["tuner_enabled"]:
                recall_at_10 = min(1.0, len(scored_results) / 10.0)  # Simplified recall calculation
                _update_autotuner_metrics(trace_id, total_cost, recall_at_10)
            
            # Check SLO violations
            slo_violated = total_cost > env_config["slo_p95_ms"]
            if slo_violated:
                _obs_slo_violations += 1
            
            _log_event("RESPONSE", trace_id, total_cost,
                      stats={"total_results": len(scored_results), "top1_id": top1_id},
                      params={"slo_violated": slo_violated, "slo_p95_ms": env_config["slo_p95_ms"]})
            
            # Post-generation cache write-back (no reranker case)
            if self.cache and env_config["use_cache"]:
                cache_meta = {
                    "ts_ms": time.time() * 1000,
                    "source": "pipeline_no_rerank",
                    "cost_ms": total_cost
                }
                self.cache.put(query, scored_results, cache_meta)
                _log_event("CACHE_PUT", trace_id, 0.0,
                          params={"query": query[:80]},
                          stats={"reason": "generated"})
            
            return scored_results


def search_with_explain(
    query: str,
    collection_name: str,
    reranker_name: str = "llm",
    explainer_name: str = "simple",
    top_n: int = 5,
    autotuner_params: Optional[Dict[str, int]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Perform a complete search with explanation.
    
    Args:
        query: Search query
        collection_name: Name of the collection to search
        reranker_name: Type of reranker to use
        explainer_name: Type of explainer to use
        top_n: Number of results to return
        autotuner_params: AutoTuner parameters dict with 'nprobe' and 'ef_search' keys
        
    Returns:
        List of search results with explanations
    """
    # Initialize vector search
    vector_search = VectorSearch()
    
    # Extract AutoTuner parameters
    nprobe = None
    ef_search = None
    if autotuner_params:
        nprobe = autotuner_params.get('nprobe')
        ef_search = autotuner_params.get('ef_search')
    
    # Perform vector search
    results = vector_search.vector_search(
        query=query,
        collection_name=collection_name,
        top_n=top_n,
        nprobe=nprobe,
        ef_search=ef_search
    )
    
    # Convert to expected format
    formatted_results = []
    for i, result in enumerate(results):
        # Handle ScoredDocument objects from vector search
        if hasattr(result, 'content') and hasattr(result, 'score'):
            content = result.content
            # Extract text content from Document object if it's wrapped
            if hasattr(content, 'page_content'):
                content_text = content.page_content
            else:
                content_text = str(content)
            
            formatted_results.append({
                "content": content_text,
                "score": result.score,
                "metadata": getattr(result, 'metadata', {}),
                "rank": i + 1,
                "explanation": f"Relevant to query: {query[:50]}..."
            })
        else:
            # Fallback for dictionary format
            formatted_results.append({
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {}),
                "rank": i + 1,
                "explanation": f"Relevant to query: {query[:50]}..."
            })
    
    return formatted_results


def search_with_multiple_configurations(
    query: str,
    collection_name: str,
    configurations: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Perform search with multiple configurations for comparison.
    
    Args:
        query: Search query
        collection_name: Name of the collection to search
        configurations: List of configuration dictionaries
        
    Returns:
        Dictionary mapping configuration names to results
    """
    results = {}
    
    for config in configurations:
        config_name = config.get("name", "default")
        results[config_name] = search_with_explain(
            query=query,
            collection_name=collection_name,
            **config
        )
    
    return results


def get_available_rerankers() -> List[str]:
    """Get list of available rerankers."""
    return ["llm", "simple", "none"]


def get_available_explainers() -> List[str]:
    """Get list of available explainers."""
    return ["simple", "detailed", "none"]
