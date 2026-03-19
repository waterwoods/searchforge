#!/usr/bin/env python3
"""
E2E Test for Auto Insurance Collection
======================================
测试 3 个查询，验证结果相关性
"""

import sys
import json
import requests
from urllib.parse import urlparse
from typing import Dict, List, Any

API_BASE_URL = "http://localhost:8000"

TEST_QUERIES = [
    {
        "question": "加州最低汽车保险要求是什么？",
        "description": "中文查询 - 最低保险要求"
    },
    {
        "question": "How to file an auto insurance claim in California?",
        "description": "英文查询 - 理赔流程"
    },
    {
        "question": "SR-22 是什么？什么时候需要？",
        "description": "中文查询 - SR-22 文件"
    }
]

def get_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url:
        return "unknown"
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return "invalid"

def is_relevant(title: str, text: str, query: str) -> bool:
    """Check if result is relevant to the query."""
    query_lower = query.lower()
    title_lower = title.lower()
    text_lower = text.lower()
    
    # Keywords for each query type
    if "最低" in query or "minimum" in query_lower or "requirement" in query_lower:
        keywords = ["最低", "minimum", "requirement", "15/30/5", "liability", "coverage"]
        return any(kw in title_lower or kw in text_lower for kw in keywords)
    
    if "claim" in query_lower or "理赔" in query:
        keywords = ["claim", "理赔", "file", "report", "accident", "damage"]
        return any(kw in title_lower or kw in text_lower for kw in keywords)
    
    if "sr-22" in query_lower or "sr22" in query_lower:
        keywords = ["sr-22", "sr22", "certificate", "proof", "insurance"]
        return any(kw in title_lower or kw in text_lower for kw in keywords)
    
    # General relevance check
    return True

def test_query(query: str, description: str) -> Dict[str, Any]:
    """Test a single query."""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"Description: {description}")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/query",
            json={"question": query, "top_k": 5},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}
    
    if not data.get("ok"):
        print(f"❌ API returned error: {data}")
        return {"error": data}
    
    sources = data.get("sources", [])
    print(f"\n✅ Retrieved {len(sources)} results")
    print(f"   Latency: {data.get('latency_ms', 0):.1f}ms")
    
    relevant_count = 0
    results = []
    
    print(f"\nTop 5 Results:")
    print("-" * 70)
    for i, source in enumerate(sources[:5], 1):
        title = source.get("title", "") or "(no title)"
        text = source.get("text", "")[:100] or ""
        source_url = source.get("source_url", "") or ""
        score = source.get("score", 0.0)
        domain = get_domain(source_url)
        
        relevant = is_relevant(title, text, query)
        if relevant:
            relevant_count += 1
        
        results.append({
            "rank": i,
            "title": title[:80],
            "domain": domain,
            "score": score,
            "relevant": relevant,
            "url": source_url[:80]
        })
        
        status = "✅" if relevant else "❌"
        print(f"\n[{i}] {status} Score: {score:.4f}")
        print(f"    Title: {title[:80]}")
        print(f"    Domain: {domain}")
        print(f"    Preview: {text[:80]}...")
        print(f"    URL: {source_url[:80]}...")
    
    print(f"\n{'='*70}")
    print(f"Relevance: {relevant_count}/5 results are relevant")
    if relevant_count >= 3:
        print(f"✅ PASS: At least 3/5 results are relevant")
    else:
        print(f"❌ FAIL: Only {relevant_count}/5 results are relevant (need >= 3)")
    
    return {
        "query": query,
        "description": description,
        "total_results": len(sources),
        "relevant_count": relevant_count,
        "results": results,
        "passed": relevant_count >= 3
    }

def main():
    print("=" * 70)
    print("E2E Test for Auto Insurance Collection")
    print("=" * 70)
    
    # Test API connectivity
    try:
        health = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
        if health.status_code == 200:
            print("✅ Backend is accessible")
        else:
            print(f"❌ Backend health check failed: {health.status_code}")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print(f"   Make sure backend is running on {API_BASE_URL}")
        return 1
    
    # Run tests
    results = []
    for test in TEST_QUERIES:
        result = test_query(test["question"], test["description"])
        results.append(result)
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    passed = sum(1 for r in results if r.get("passed", False))
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.get("passed") else "❌ FAIL"
        print(f"  {i}. {result.get('description', 'Unknown')}: {status}")
        if not result.get("passed"):
            print(f"     Relevant: {result.get('relevant_count', 0)}/5")
    
    if passed == total:
        print(f"\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
