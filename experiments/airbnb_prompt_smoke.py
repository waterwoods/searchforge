#!/usr/bin/env python3
"""
Airbnb Prompt Smoke Test
=========================
Tests Airbnb LA queries and inspects prompt construction.
Run this to verify that price/bedrooms fields are included in LLM context.
"""
import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000"

TEST_QUERIES = [
    "what is the cheapest room in Long Beach for 3 nights?",
    "Find a 2 bedroom place in West LA under $200 per night",
    "How much does it cost to stay in Hollywood for 2 days?",
]


def test_query(question: str, collection: str = "airbnb_la_demo"):
    """Test a single query and print results."""
    print(f"\n{'='*80}")
    print(f"Query: {question}")
    print(f"Collection: {collection}")
    print(f"{'='*80}\n")
    
    payload = {
        "question": question,
        "collection": collection,
        "top_k": 5,
        "generate_answer": True,
        "stream": False,
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/query",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        # Print answer preview
        print("📝 ANSWER (first 300 chars):")
        print("-" * 80)
        answer = data.get("answer", "")
        if answer:
            print(answer[:300] + ("..." if len(answer) > 300 else ""))
        else:
            print("(No answer generated)")
        print()
        
        # Print LLM usage metrics
        print("📊 LLM USAGE METRICS:")
        print("-" * 80)
        llm_usage = data.get("metrics", {}).get("llm_usage")
        if llm_usage:
            print(json.dumps(llm_usage, indent=2))
        else:
            print("(No LLM usage data)")
        print()
        
        # Print sources summary
        print("📚 SOURCES SUMMARY (first 3):")
        print("-" * 80)
        sources = data.get("sources", [])[:3]
        for i, source in enumerate(sources, 1):
            print(f"\nSource {i}:")
            print(f"  Title: {source.get('title', 'N/A')[:60]}")
            print(f"  Score: {source.get('score', 0):.4f}")
            if "price" in source:
                print(f"  Price: ${source.get('price', 0):.0f}/night")
            if "bedrooms" in source:
                print(f"  Bedrooms: {source.get('bedrooms', 0)}")
            if "neighbourhood" in source:
                print(f"  Neighbourhood: {source.get('neighbourhood', 'N/A')}")
            if "room_type" in source:
                print(f"  Room Type: {source.get('room_type', 'N/A')}")
            if "text" in source:
                text_len = len(source.get("text", ""))
                print(f"  Text length: {text_len} chars")
        print()
        
        # Print trace_id for log lookup
        trace_id = data.get("trace_id", "unknown")
        print("🔍 DEBUG INFO:")
        print("-" * 80)
        print(f"Trace ID: {trace_id}")
        print(f"Collection: {data.get('route', 'unknown')}")
        print(f"Latency: {data.get('latency_ms', 0):.1f}ms")
        print()
        print("💡 To see detailed prompt logs, run:")
        print(f"   grep '[AIRBNB_PROMPT_DEBUG].*{trace_id}' /tmp/backend.log")
        print("   or check your backend log file for lines containing:")
        print(f"   [AIRBNB_PROMPT_DEBUG] trace_id={trace_id}")
        print()
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response (text): {e.response.text[:500]}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run smoke tests."""
    print("=" * 80)
    print("Airbnb Prompt Smoke Test")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Check if backend is reachable
    try:
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"⚠️  Backend health check returned {health_response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach backend at {API_BASE}")
        print(f"   Error: {e}")
        print("\n💡 Make sure backend is running:")
        print("   python -m uvicorn services.fiqa_api.app_main:app --reload --port 8000")
        sys.exit(1)
    
    results = []
    for query in TEST_QUERIES:
        result = test_query(query)
        results.append((query, result))
        if result is None:
            print("⚠️  Query failed, continuing with next query...")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    successful = sum(1 for _, r in results if r is not None)
    print(f"Successful queries: {successful}/{len(TEST_QUERIES)}")
    
    # Check for common issues
    print("\n🔍 Common Issues to Check:")
    print("1. Look for [AIRBNB_PROMPT_DEBUG] logs in backend output")
    print("2. Verify that 'price' and 'bedrooms' appear in context_fields")
    print("3. Check if prompt_preview contains 'Price: $X/night' format")
    print("4. Verify answer mentions prices (not 'context does not contain')")
    print()
    
    return 0 if successful == len(TEST_QUERIES) else 1


if __name__ == "__main__":
    sys.exit(main())

