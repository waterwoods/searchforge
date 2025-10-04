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
    important_events = ["RESPONSE", "RUN_INFO", "AUTOTUNER_SUGGEST", "PARAMS_APPLIED", "FETCH_QUERY", "RETRIEVE_VECTOR"]
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
        "slo_recall_at10": float(os.getenv("SLO_RECALL_AT10", "0.30"))
    }

# Global AutoTuner state
_autotuner_state = {
    "metrics_window": [],
    "last_suggest_time": 0,
    "cooldown_until": 0,
    "current_ef_search": 128,
    "suggestions_made": 0,
    "suggestions_applied": 0
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
    
    # Check if we should make a suggestion
    if (current_time - _autotuner_state["last_suggest_time"] >= env_config["tuner_sample_sec"] and
        len(_autotuner_state["metrics_window"]) >= 3):
        
        # Calculate window metrics
        window_p95 = max(m["p95_ms"] for m in _autotuner_state["metrics_window"])
        window_recall = sum(m["recall_at_10"] for m in _autotuner_state["metrics_window"]) / len(_autotuner_state["metrics_window"])
        
        # 6. AUTOTUNER_SUGGEST event
        suggestion = _make_autotuner_suggestion(window_p95, window_recall, env_config)
        _autotuner_state["suggestions_made"] += 1
        _autotuner_state["last_suggest_time"] = current_time
        
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
            if top_k <= derived_params["T"]:
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
            rerank_k = min(derived_params["rerank_multiplier"] * base_rerank_k, derived_params["Ncand_max"])
            
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
