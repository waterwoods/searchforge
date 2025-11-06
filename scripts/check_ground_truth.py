#!/usr/bin/env python3
"""
Step 1: 真值检查 - 打印最近200次/metrics聚合，检测ON功能是否生效
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from logs.metrics_logger import MetricsLogger

def check_ground_truth():
    """检查最近200次请求的真值指标"""
    logger = MetricsLogger(log_dir="services/fiqa_api/logs")
    
    # 获取最近200条记录
    recent = logger.get_recent_metrics(window=200)
    
    if not recent:
        print("❌ NO DATA - 无法读取metrics数据")
        print("\n📋 排查清单：")
        print("  1. 检查服务是否启动：curl http://localhost:8080/health")
        print("  2. 执行测试请求：curl 'http://localhost:8080/search?query=ETF&mode=on'")
        print("  3. 查看日志文件：cat logs/api_metrics.csv")
        return
    
    print(f"📊 最近 {len(recent)} 次请求聚合分析\n")
    
    # 计算关键指标
    count = len(recent)
    rerank_hits = sum(int(m.get("rerank_hit", 0)) for m in recent)
    rerank_hit_rate = rerank_hits / count if count > 0 else 0
    
    # page_index_used: 检查collection_name是否包含page_index相关标识
    page_index_used_count = sum(1 for m in recent if "page" in m.get("collection_name", "").lower())
    page_index_used = page_index_used_count / count if count > 0 else 0
    
    # rr_timeout_rate
    def parse_bool(val):
        if isinstance(val, bool):
            return val
        return str(val).lower() == 'true'
    
    timeouts = sum(1 for m in recent if parse_bool(m.get("rerank_timeout", False)))
    rr_timeout_rate = timeouts / count if count > 0 else 0
    
    # 平均延迟
    avg_latency = sum(float(m["p95_ms"]) for m in recent) / count if count > 0 else 0
    avg_rerank_latency = sum(float(m.get("rerank_latency_ms", 0)) for m in recent) / count if count > 0 else 0
    
    print(f"✅ rerank_hit_rate:    {rerank_hit_rate:.2%} ({rerank_hits}/{count})")
    print(f"✅ page_index_used:    {page_index_used:.2%} ({page_index_used_count}/{count})")
    print(f"✅ rr_timeout_rate:    {rr_timeout_rate:.2%} ({timeouts}/{count})")
    print(f"   avg_latency_ms:     {avg_latency:.1f}")
    print(f"   avg_rerank_latency: {avg_rerank_latency:.1f}")
    
    # 判断ON功能是否生效
    issues = []
    if rerank_hit_rate == 0:
        issues.append("rerank_hit_rate == 0")
    if page_index_used == 0:
        issues.append("page_index_used == 0")
    
    if issues:
        print(f"\n⚠️  ON 未生效 - 检测到问题: {', '.join(issues)}")
        print("\n📋 排查项：")
        print("  1. ENV变量检查:")
        print("     - ENABLE_RERANKER=True")
        print("     - ENABLE_PAGE_INDEX=True")
        print("     - COLLECTION_NAME=beir_fiqa_full_ta")
        print("  2. settings.py配置:")
        print("     - ENABLE_RERANKER (当前可能被覆盖)")
        print("     - ENABLE_PAGE_INDEX (当前可能被覆盖)")
        print("  3. mode参数检查:")
        print("     - 请求时需带 mode=on 参数")
        print("     - 示例: /search?query=ETF&mode=on")
        print("  4. 缓存命中:")
        print("     - rerank缓存可能使rerank_hit=0但实际已生效")
        print("     - 检查 rerank_model 字段是否为 'disabled'")
        
        # 显示最近的rerank_model分布
        rerank_models = [m.get("rerank_model", "unknown") for m in recent[-20:]]
        model_dist = {}
        for model in rerank_models:
            model_dist[model] = model_dist.get(model, 0) + 1
        print("\n  最近20次 rerank_model 分布:")
        for model, cnt in sorted(model_dist.items(), key=lambda x: -x[1]):
            print(f"     {model}: {cnt}")
    else:
        print("\n✅ ON 功能已生效")
    
    # 显示最近5条记录的详细信息
    print("\n📄 最近5条记录详情:")
    for i, m in enumerate(recent[-5:], 1):
        print(f"  {i}. rerank_hit={m.get('rerank_hit', 0)}, "
              f"model={m.get('rerank_model', 'unknown')[:30]}, "
              f"trigger={m.get('trigger_reason', 'N/A')}, "
              f"collection={m.get('collection_name', 'unknown')[:20]}")

if __name__ == "__main__":
    check_ground_truth()

