# modules/rerankers/factory.py
from __future__ import annotations
from typing import Dict, Any, Optional
from modules.rerankers.base import AbstractReranker
from modules.rerankers.simple_ce import CrossEncoderReranker
try:
    from modules.rerankers.fake import FakeReranker
except Exception:
    FakeReranker = None

SUPPORTED = {
    "cross_encoder":CrossEncoderReranker ,
    "ce": CrossEncoderReranker,
    "fake": FakeReranker,
    "mock": FakeReranker,
    "demo": FakeReranker,
    # 未来可在此扩展： 'hybrid': HybridWeightReranker, 'cohere': CohereReranker, ...
}

def create_reranker(cfg: Optional[Dict[str, Any]]) -> Optional[AbstractReranker]:
    """
    Create a reranker from config dict. Safe-by-default:
    - cfg is None or {"type": "none"} -> return None (pipeline将跳过重排)
    - unknown type -> raise ValueError (便于显式发现配置错误)

    Expected cfg shape:
    {
      "type": "cross_encoder",
      "model": "cross-encoder/ms-marco-MiniLM-L-2-v2",
      "top_k": 50,
      "batch_size": 32,
      "cache_size": 2000
    }
    """
    if not cfg:
        return None
    rtype = str(cfg.get("type", "none")).lower()
    if rtype in ("none", "off", "false"):
        return None

    if rtype in ("cross_encoder", "ce", "simple_ce"):
        return CrossEncoderReranker(
            model=cfg.get("model"),
            top_k=int(cfg.get("top_k", 50)),
            batch_size=int(cfg.get("batch_size", 32)),
            cache_size=int(cfg.get("cache_size", 2000)),
        )

    cls = SUPPORTED.get(rtype)
    if not cls:
        raise ValueError(f"Unsupported reranker type: {rtype}")

    params = cfg.get("params", {}) or {}
    # 工厂只负责把参数透传下去；实现类里做容错（如 ImportError / 模型加载失败）
    return cls(**params)
