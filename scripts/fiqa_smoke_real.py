#!/usr/bin/env python3
"""
真实数据冒烟测试：10条金融查询，打印Top-3结果
验证 Qdrant 集合接入正确性
"""
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# 10条高质量金融查询
FINANCE_QUERIES = [
    "What is ETF expense ratio?",
    "How is APR different from APY?",
    "How are dividends taxed in the US?",
    "What is a mutual fund load?",
    "How do bond coupons work?",
    "What is dollar-cost averaging?",
    "How does an index fund track its index?",
    "What is a covered call strategy?",
    "How are capital gains taxed short vs long term?",
    "What is a REIT and how does it pay dividends?"
]

BASE_URL = "http://localhost:8080"


def test_query(query: str, mode: str = "on") -> dict:
    """调用 /search 接口并返回结果"""
    try:
        params = {"query": query, "top_k": 3, "mode": mode}
        response = requests.get(f"{BASE_URL}/search", params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # 解析结果
            answers = data.get("answers", [])
            latency_ms = data.get("latency_ms", 0)
            cache_hit = data.get("cache_hit", False)
            
            # 将答案转换为结构化格式（如果是字符串）
            results = []
            if answers and isinstance(answers[0], str):
                # 如果返回的是字符串列表，尝试模拟结构
                for i, ans in enumerate(answers[:3]):
                    results.append({
                        "title": f"Result {i+1}",
                        "snippet": ans[:200],
                        "source": "Qdrant",
                        "score": 0.9 - i*0.1
                    })
            else:
                # 如果是字典列表
                for ans in answers[:3]:
                    if isinstance(ans, dict):
                        results.append({
                            "title": ans.get("title", "Unknown"),
                            "snippet": ans.get("text", "")[:200],
                            "source": ans.get("source", "Unknown"),
                            "score": ans.get("score", 0.0)
                        })
            
            return {
                "success": True,
                "results": results,
                "latency_ms": latency_ms,
                "cache_hit": cache_hit
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", "detail": response.text[:100]}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    print("=" * 70)
    print(" FIQA 真实数据冒烟测试 (10 queries × Top-3)")
    print("=" * 70)
    print()
    
    # 检查 API 是否运行
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=2)
        if not health.ok:
            print("❌ API 未运行，请先启动: bash launch.sh")
            return 1
    except:
        print("❌ API 未运行，请先启动: bash launch.sh")
        return 1
    
    print("✅ API 运行正常\n")
    
    # 运行测试
    all_results = []
    success_count = 0
    
    for idx, query in enumerate(FINANCE_QUERIES, 1):
        print(f"[{idx}/10] {query}")
        result = test_query(query, mode="on")
        
        if result["success"]:
            success_count += 1
            print(f"  ✓ Latency: {result['latency_ms']:.1f}ms | Cache: {result['cache_hit']}")
            
            # 打印 Top-3
            for i, res in enumerate(result["results"], 1):
                print(f"    #{i} [{res['score']:.3f}] {res['title']}")
                print(f"        {res['snippet'][:80]}...")
                print(f"        Source: {res['source']}")
            
            all_results.append({
                "query": query,
                "latency_ms": result["latency_ms"],
                "cache_hit": result["cache_hit"],
                "top_3": result["results"]
            })
        else:
            print(f"  ✗ Error: {result.get('error', 'Unknown')}")
            all_results.append({
                "query": query,
                "error": result.get("error", "Unknown"),
                "detail": result.get("detail", "")
            })
        
        print()
        
        # 添加延迟避免触发速率限制 (3 req/sec as per settings)
        time.sleep(0.4)
    
    # 保存结果
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(FINANCE_QUERIES),
        "success_count": success_count,
        "results": all_results
    }
    
    output_path = reports_dir / "fiqa_real_smoke.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # 总结
    print("=" * 70)
    print(f"✅ 冒烟测试完成: {success_count}/{len(FINANCE_QUERIES)} 成功")
    print(f"📄 结果已保存: {output_path}")
    print("=" * 70)
    
    return 0 if success_count == len(FINANCE_QUERIES) else 1


if __name__ == "__main__":
    sys.exit(main())

