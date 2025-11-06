"""
Reranker Lite - MiniLM本地版
轻量级重排序实现，CPU可跑，超时/异常优雅回退
"""
import time
from typing import List, Tuple, Optional

# Global model cache (lazy loaded)
_MODEL_CACHE = None
_MODEL_NAME_CACHE = None


def rerank_passages(
    query: str,
    passages: List[str],
    top_k: int = 10,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    cache_dir: str = "./models",
    timeout_ms: int = 80
) -> Tuple[List[str], float, str]:
    """
    对候选段落进行重排序
    
    Args:
        query: 查询文本
        passages: 候选段落列表
        top_k: 返回top K个结果
        model_name: 模型名称
        cache_dir: 模型缓存目录
        timeout_ms: 超时时间（毫秒）
        
    Returns:
        (top_passages, latency_ms, model_used)
        超时/异常时返回原排序
    """
    start_time = time.time()
    
    # 快速路径：如果没有候选
    if not passages:
        latency_ms = (time.time() - start_time) * 1000
        return passages[:top_k], latency_ms, "fallback:insufficient"
    
    # 如果候选数量不多，仍然可以rerank（有助于调整顺序）
    if len(passages) < top_k:
        latency_ms = (time.time() - start_time) * 1000
        return passages, latency_ms, "fallback:too_few"
    
    try:
        # 延迟导入，避免启动时加载
        from sentence_transformers import CrossEncoder
        import torch
        
        global _MODEL_CACHE, _MODEL_NAME_CACHE
        
        # 使用缓存的模型（避免重复加载）
        model_loaded_from_cache = False
        if _MODEL_CACHE is not None and _MODEL_NAME_CACHE == model_name:
            model = _MODEL_CACHE
            model_loaded_from_cache = True
        else:
            # 首次加载模型（可能需要下载）
            # 首次加载不检查超时，允许完整加载
            model = CrossEncoder(model_name, max_length=512, device='cpu')
            _MODEL_CACHE = model
            _MODEL_NAME_CACHE = model_name
            model_loaded_from_cache = False
        
        # 超时检查：仅在使用缓存模型时检查
        if model_loaded_from_cache:
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > timeout_ms * 0.3:  # 30%超时预算（缓存命中应该很快）
                return passages[:top_k], elapsed_ms, "fallback:timeout_before_scoring"
        
        # 准备输入对 [[query, passage], ...]
        pairs = [[query, passage] for passage in passages]
        
        # 批量评分（向量化）
        # CrossEncoder.predict 返回相关性分数
        with torch.no_grad():
            scores = model.predict(pairs, batch_size=32, show_progress_bar=False)
        
        # 超时检查点3：评分后
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > timeout_ms:
            return passages[:top_k], elapsed_ms, "fallback:scoring_timeout"
        
        # 排序并取top_k
        # scores是numpy数组，需要转换为列表并配对索引
        scored_passages = list(zip(scores.tolist(), passages))
        scored_passages.sort(reverse=True, key=lambda x: x[0])
        
        # 提取top_k段落
        top_passages = [passage for _, passage in scored_passages[:top_k]]
        
        latency_ms = (time.time() - start_time) * 1000
        return top_passages, latency_ms, model_name
        
    except ImportError as e:
        # 依赖缺失 - 回退到原排序
        latency_ms = (time.time() - start_time) * 1000
        return passages[:top_k], latency_ms, f"fallback:import_error:{str(e)[:30]}"
    
    except Exception as e:
        # 任何其他异常 - 优雅回退
        latency_ms = (time.time() - start_time) * 1000
        error_type = type(e).__name__
        return passages[:top_k], latency_ms, f"fallback:error:{error_type}"


def test_reranker():
    """简单测试函数"""
    query = "What is a good investment strategy?"
    passages = [
        "Diversification is key to managing investment risk.",
        "The weather today is sunny and warm.",
        "Long-term investing in index funds is recommended.",
        "Pizza is a popular Italian food.",
        "Compound interest helps grow your wealth over time."
    ]
    
    print("Testing Reranker Lite...")
    top, latency, model = rerank_passages(query, passages, top_k=3)
    
    print(f"\nQuery: {query}")
    print(f"Latency: {latency:.2f}ms")
    print(f"Model: {model}")
    print("\nTop 3 passages:")
    for i, passage in enumerate(top, 1):
        print(f"  {i}. {passage}")


if __name__ == "__main__":
    test_reranker()

