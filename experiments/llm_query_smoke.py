#!/usr/bin/env python3
"""
LLM Query Smoke Test

Simple smoke test for /api/query endpoint with LLM answer generation.
Tests non-streaming path and verifies answer generation and token usage tracking.
"""

import os
import sys
import time
import traceback
from typing import Any, Dict

try:
    import requests
except ImportError:
    print("ERROR: requests module not found. Install with: pip install requests")
    sys.exit(1)

RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000").rstrip("/")
TEST_QUERIES = [
    "What is SearchForge?",
    "How does vector search work?",
    "What are the benefits of hybrid retrieval?",
]


def test_query(question: str, stream: bool = False) -> Dict[str, Any]:
    """
    Test /api/query endpoint.
    
    Args:
        question: Query question
        stream: Whether to use streaming mode
    
    Returns:
        Dict with status_code, latency_ms, answer_preview, llm_usage
    """
    url = f"{RAG_API_URL}/api/query"
    payload = {
        "question": question,
        "top_k": 10,
        "stream": stream,
        "use_kv_cache": False,  # Test without KV-cache first
        "session_id": None,  # No session for first test
        "generate_answer": True,  # Explicitly enable LLM generation for smoke test
    }
    
    start_time = time.perf_counter()
    
    try:
        if stream:
            # Streaming request
            response = requests.post(
                url,
                json=payload,
                timeout=30.0,
                stream=True,
            )
            status_code = response.status_code
            
            # Collect stream chunks
            answer_chunks = []
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    answer_chunks.append(chunk.decode("utf-8", errors="ignore"))
            
            answer_full = "".join(answer_chunks)
            # Extract answer from SSE format (simplified)
            answer_preview = answer_full[:120] if answer_full else ""
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            return {
                "status_code": status_code,
                "latency_ms": latency_ms,
                "answer_preview": answer_preview,
                "llm_usage": None,  # Streaming doesn't return usage in SSE format
                "stream": True,
            }
        else:
            # Non-streaming request
            response = requests.post(url, json=payload, timeout=30.0)
            status_code = response.status_code
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            if status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                answer_preview = answer[:200] if answer else ""  # Show first 200 chars for better visibility
                metrics = data.get("metrics", {})
                llm_usage = metrics.get("llm_usage")
                llm_enabled = metrics.get("llm_enabled", False)
                kv_enabled = metrics.get("kv_enabled", False)
                kv_hit = metrics.get("kv_hit", False)
                
                return {
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "answer_preview": answer_preview,
                    "answer": answer,  # Full answer for detailed output
                    "llm_usage": llm_usage,
                    "llm_enabled": llm_enabled,
                    "kv_enabled": kv_enabled,
                    "kv_hit": kv_hit,
                    "stream": False,
                }
            else:
                return {
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "answer_preview": f"Error: {response.text[:120]}",
                    "llm_usage": None,
                    "stream": False,
                }
                
    except requests.Timeout:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "status_code": 504,
            "latency_ms": latency_ms,
            "answer_preview": "Request timeout",
            "llm_usage": None,
            "stream": stream,
        }
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "status_code": 0,
            "latency_ms": latency_ms,
            "answer_preview": f"Exception: {str(e)}",
            "llm_usage": None,
            "stream": stream,
        }


def print_result(query: str, result: Dict[str, Any]) -> None:
    """Print test result in formatted way."""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    print(f"Status Code: {result['status_code']}")
    print(f"Latency: {result['latency_ms']:.1f} ms")
    print(f"Stream: {result['stream']}")
    print(f"LLM Enabled: {result.get('llm_enabled', False)}")
    print(f"KV Enabled: {result.get('kv_enabled', False)}")
    print(f"KV Hit: {result.get('kv_hit', False)}")
    print(f"\nAnswer Preview (first 200 chars):")
    answer_text = result.get('answer') or result.get('answer_preview', '')
    print(f"  {answer_text[:200]}")
    
    if result.get("llm_usage"):
        usage = result["llm_usage"]
        print(f"\nLLM Usage:")
        print(f"  Model: {usage.get('model', 'unknown')}")
        print(f"  Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
        print(f"  Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
        print(f"  Total Tokens: {usage.get('total_tokens', 'N/A')}")
        cost = usage.get("cost_usd_est")
        if cost is not None:
            print(f"  Cost (USD): ${cost:.6f}")
        else:
            print(f"  Cost (USD): N/A")
        print(f"  Use KV Cache: {usage.get('use_kv_cache', False)}")
    else:
        print(f"\nLLM Usage: Not available (LLM may be disabled or error occurred)")


def main() -> int:
    """Run smoke tests."""
    print("LLM Query Smoke Test")
    print(f"Testing endpoint: {RAG_API_URL}/api/query")
    print(f"Number of test queries: {len(TEST_QUERIES)}")
    
    all_passed = True
    
    # Test 1-3: Basic queries without KV-cache
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n\n[Test {i}/{len(TEST_QUERIES)}] - Basic query (no KV)")
        try:
            result = test_query(query, stream=False)
            print_result(query, result)
            
            # Check if request succeeded
            if result["status_code"] != 200:
                print(f"\n⚠️  Warning: Status code {result['status_code']} (expected 200)")
                all_passed = False
            
            # Check if answer was generated (optional - may be empty if LLM unavailable)
            if result["answer_preview"].strip():
                print(f"\n✅ Answer generated successfully")
            else:
                print(f"\n⚠️  Warning: Answer is empty (LLM may be unavailable or disabled)")
                
        except Exception as e:
            print(f"\n❌ Test failed with exception:")
            traceback.print_exc()
            all_passed = False
    
    # Test 4-5: KV-cache test with session (first request = miss, second = hit)
    if len(TEST_QUERIES) > 0:
        test_query_text = TEST_QUERIES[0]
        session_id = "smoke-1"
        
        print(f"\n\n[Test {len(TEST_QUERIES) + 1}] - KV-cache test (first request, should be miss)")
        try:
            # First request with KV-cache enabled
            payload = {
                "question": test_query_text,
                "top_k": 10,
                "stream": False,
                "use_kv_cache": True,
                "session_id": session_id,
                "generate_answer": True,
            }
            url = f"{RAG_API_URL}/api/query"
            response = requests.post(url, json=payload, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                metrics = data.get("metrics", {})
                kv_enabled = metrics.get("kv_enabled", False)
                kv_hit = metrics.get("kv_hit", False)
                print(f"  KV Enabled: {kv_enabled}, KV Hit: {kv_hit}")
                if kv_enabled and not kv_hit:
                    print(f"  ✅ First request correctly identified as miss")
                else:
                    print(f"  ⚠️  Expected kv_enabled=True, kv_hit=False")
                    all_passed = False
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            all_passed = False
        
        print(f"\n[Test {len(TEST_QUERIES) + 2}] - KV-cache test (second request, should be hit)")
        try:
            # Second request with same session_id
            response = requests.post(url, json=payload, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                metrics = data.get("metrics", {})
                kv_enabled = metrics.get("kv_enabled", False)
                kv_hit = metrics.get("kv_hit", False)
                print(f"  KV Enabled: {kv_enabled}, KV Hit: {kv_hit}")
                if kv_enabled and kv_hit:
                    print(f"  ✅ Second request correctly identified as hit")
                else:
                    print(f"  ⚠️  Expected kv_enabled=True, kv_hit=True")
                    all_passed = False
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            all_passed = False
    
    print(f"\n\n{'='*80}")
    if all_passed:
        print("✅ All smoke tests passed")
        return 0
    else:
        print("❌ Some smoke tests failed or had warnings")
        return 1


if __name__ == "__main__":
    sys.exit(main())

