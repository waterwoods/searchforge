#!/usr/bin/env python3
"""
airbnb_lab_smoke.py - Airbnb LA Lab 验证脚本

对几条固定 query 调用 /api/query，指定 collection="airbnb_la_demo"，
打印 latency_ms 和 top 3 sources 的 title/neighbourhood/price。

用法:
    python experiments/airbnb_lab_smoke.py [--base-url http://localhost:8000]
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# ============================================================================
# 配置常量
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8000"
COLLECTION = "airbnb_la_demo"

# 测试查询
TEST_QUERIES = [
    "Find a 2-bedroom entire home in Hollywood under $250 per night.",
    "Quiet studio in Downtown LA with good availability.",
    "Family-friendly Airbnb near Santa Monica with at least 2 bedrooms.",
]


# ============================================================================
# 辅助函数
# ============================================================================

def call_api(base_url: str, query: str, collection: str = COLLECTION) -> Dict[str, Any]:
    """
    调用 /api/query API。
    
    Args:
        base_url: API 基础 URL
        query: 查询字符串
        collection: Collection 名称
        
    Returns:
        dict: API 响应
    """
    import requests
    
    url = f"{base_url}/api/query"
    payload = {
        "question": query,
        "top_k": 10,
        "collection": collection,
        "rerank": False,
        "generate_answer": False,
    }
    
    try:
        start_time = time.perf_counter()
        response = requests.post(url, json=payload, timeout=30.0)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        response.raise_for_status()
        data = response.json()
        
        # 添加实际测量的延迟
        data["_measured_latency_ms"] = elapsed_ms
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ API 调用失败: {e}", file=sys.stderr)
        raise


def format_source(source: Dict[str, Any]) -> str:
    """
    格式化 source 为字符串。
    
    Args:
        source: Source 字典
        
    Returns:
        str: 格式化后的字符串
    """
    parts = []
    
    title = source.get("title", source.get("doc_id", "Unknown"))
    parts.append(f"Title: {title}")
    
    if "price" in source and source["price"]:
        parts.append(f"Price: ${source['price']:.0f}/night")
    
    if "neighbourhood" in source and source["neighbourhood"]:
        parts.append(f"Neighbourhood: {source['neighbourhood']}")
    
    if "room_type" in source and source["room_type"]:
        parts.append(f"Room Type: {source['room_type']}")
    
    if "bedrooms" in source and source["bedrooms"]:
        parts.append(f"Bedrooms: {source['bedrooms']}")
    
    score = source.get("score", 0.0)
    parts.append(f"Score: {score:.3f}")
    
    return " | ".join(parts)


def print_results(query: str, response: Dict[str, Any]):
    """
    打印查询结果。
    
    Args:
        query: 查询字符串
        response: API 响应
    """
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    if not response.get("ok"):
        print(f"❌ 查询失败: {response.get('error', 'Unknown error')}")
        return
    
    # 延迟信息
    latency_ms = response.get("_measured_latency_ms") or response.get("latency_ms", 0.0)
    route = response.get("route", "unknown")
    print(f"✅ 成功 | Latency: {latency_ms:.1f}ms | Route: {route}")
    
    # Top 3 sources
    sources = response.get("sources", [])
    if not sources:
        print("⚠️  没有返回任何 sources")
        return
    
    print(f"\nTop {min(3, len(sources))} Sources:")
    for i, source in enumerate(sources[:3], start=1):
        formatted = format_source(source)
        print(f"  {i}. {formatted}")
        
        # 如果包含 Airbnb 字段，额外显示详细信息
        if "price" in source or "neighbourhood" in source:
            details = []
            if source.get("neighbourhood"):
                details.append(f"📍 {source['neighbourhood']}")
            if source.get("room_type"):
                details.append(f"🏠 {source['room_type']}")
            if source.get("price") and source["price"] > 0:
                details.append(f"💰 ${source['price']:.0f}/night")
            if source.get("bedrooms") and source["bedrooms"] > 0:
                details.append(f"🛏️  {source['bedrooms']} bedroom{'s' if source['bedrooms'] > 1 else ''}")
            if details:
                print(f"      {' • '.join(details)}")


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Airbnb LA Lab 验证脚本"
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API 基础 URL（默认: {DEFAULT_BASE_URL}）"
    )
    parser.add_argument(
        "--collection",
        default=COLLECTION,
        help=f"Collection 名称（默认: {COLLECTION}）"
    )
    parser.add_argument(
        "--query",
        default=None,
        help="单个查询字符串（用于测试单个查询）"
    )
    
    args = parser.parse_args()
    
    print(f"[配置] Base URL: {args.base_url}")
    print(f"[配置] Collection: {args.collection}")
    print(f"[配置] 测试查询数: {len(TEST_QUERIES)}")
    
    # 确定要测试的查询
    queries = [args.query] if args.query else TEST_QUERIES
    
    if not queries:
        print("❌ 错误: 没有查询可测试", file=sys.stderr)
        sys.exit(1)
    
    # 测试每个查询
    all_success = True
    for i, query in enumerate(queries, start=1):
        print(f"\n[{i}/{len(queries)}] 测试查询...")
        
        try:
            response = call_api(args.base_url, query, args.collection)
            print_results(query, response)
            
            if not response.get("ok"):
                all_success = False
        except Exception as e:
            print(f"❌ 查询失败: {e}", file=sys.stderr)
            all_success = False
    
    # 总结
    print(f"\n{'='*80}")
    if all_success:
        print("✅ 所有测试通过!")
    else:
        print("⚠️  部分测试失败")
        sys.exit(1)


if __name__ == '__main__':
    main()

