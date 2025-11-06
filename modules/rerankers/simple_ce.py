# NOTE: Standardized on Document.text.
# modules/rerankers/simple_ce.py
from __future__ import annotations
from typing import List, Optional
from sentence_transformers import CrossEncoder
from modules.types import Document, ScoredDocument
from collections import OrderedDict
import hashlib
import os
import time

def _hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

class CrossEncoderReranker:
    """
    Minimal local CrossEncoder reranker.
    强基线：本地可跑；失败时抛出清晰异常，便于上层降级或告警。
    """
    name = "cross_encoder"

    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L-2-v2", top_k: int = 50,
                 batch_size: int = 32, cache_size: int = 2000):
        self.model_name = model
        self.top_k = top_k
        self.batch_size = max(1, int(batch_size))
        # Override cache size from environment if set
        env_cache_size = int(os.getenv("CE_CACHE_SIZE", "0"))
        self.cache_size = env_cache_size if env_cache_size > 0 else max(0, int(cache_size))
        self._model = None  # lazy
        self._cache = OrderedDict() if self.cache_size > 0 else None
        self._cache_hits = 0
        self._cache_miss = 0

    def _ensure_model(self):
        if self._model is None:
            self._model = CrossEncoder(self.model_name)

    def rerank(self, query: str, documents: list[Document], top_k: int = None, trace_id: str = None) -> list[ScoredDocument]:
        if not documents:
            return []
        
        start_time = time.perf_counter()
        self._ensure_model()
        
        # try cache first
        pairs = []
        idx_to_predict = []
        scores = [None] * len(documents)
        cache_hits = 0
        
        for i, d in enumerate(documents):
            doc_key = d.metadata.get("doc_id") if (d.metadata and "doc_id" in d.metadata) else _hash(d.text or "")
            key = (query, doc_key)
            if self._cache is not None and key in self._cache:
                # LRU bump
                val = self._cache.pop(key)
                self._cache[key] = val
                scores[i] = val
                cache_hits += 1
                self._cache_hits += 1
            else:
                pairs.append((query, d.text))
                idx_to_predict.append(i)
                self._cache_miss += 1
        
        # batch predict for misses
        if idx_to_predict:
            preds = []
            for s in range(0, len(pairs), self.batch_size):
                chunk = pairs[s:s+self.batch_size]
                preds.extend(self._model.predict(chunk))
            # write back & fill cache
            p = 0
            for i in idx_to_predict:
                score = float(preds[p]); p += 1
                scores[i] = score
                if self._cache is not None:
                    key = (query, (documents[i].metadata.get("doc_id") if (documents[i].metadata and "doc_id" in documents[i].metadata) else _hash(documents[i].text or "")))
                    self._cache[key] = score
                    # evict
                    if len(self._cache) > self.cache_size:
                        self._cache.popitem(last=False)
        
        ranked = sorted(
            [ScoredDocument(document=d, score=float(s), explanation=f"CE:{self.model_name}") for d, s in zip(documents, scores)],
            key=lambda x: x.score, reverse=True
        )
        effective_top_k = top_k if top_k is not None else self.top_k
        
        # Log CE rerank performance
        total_cost = (time.perf_counter() - start_time) * 1000.0
        if trace_id:
            import json
            event_data = {
                "event": "RERANK_CE_INTERNAL",
                "trace_id": trace_id,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "cost_ms": round(total_cost, 3),
                "stats": {
                    "total_docs": len(documents),
                    "cache_hits": cache_hits,
                    "cache_size": self.cache_size,
                    "batch_size": self.batch_size
                }
            }
            print(json.dumps(event_data))
        
        return ranked[: effective_top_k]
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "cache_hits": self._cache_hits,
            "cache_miss": self._cache_miss,
            "cache_size": self.cache_size
        }