#!/usr/bin/env python3
"""
Smoke test to diagnose why LLM is disabled in Search Lab Playground.

Tests /api/query with explicit parameters to check:
- Is generate_answer actually sent as True?
- Is LLM generation called?
- What does the response metrics show?
"""
import requests
import json
import sys

def test_llm_enabled():
    """Test query with explicit LLM generation enabled."""
    url = "http://localhost:8000/api/query"
    payload = {
        "question": "test LLM enabled",
        "generate_answer": True,
        "stream": False,
        "use_kv_cache": False,
        "collection": "airbnb_la_demo",
        "top_k": 5
    }
    
    print(f"\n{'='*70}")
    print("SMOKE TEST: LLM Enabled Check")
    print(f"{'='*70}\n")
    print("REQUEST PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"STATUS CODE: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"ERROR: Non-200 status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        
        # Check key fields
        print("RESPONSE ANALYSIS:")
        print("-" * 70)
        print(f"answer (length): {len(data.get('answer', ''))}")
        print(f"answer (preview): {data.get('answer', '')[:200]}...")
        print()
        
        metrics = data.get("metrics", {})
        print("METRICS:")
        print(f"  llm_enabled: {metrics.get('llm_enabled')}")
        print(f"  llm_usage: {metrics.get('llm_usage')}")
        print()
        
        # Full metrics dump
        print("FULL METRICS:")
        print(json.dumps(metrics, indent=2))
        print()
        
        # Full response (truncated for readability)
        print("FULL RESPONSE (answer and sources truncated):")
        response_copy = data.copy()
        if "answer" in response_copy and len(response_copy["answer"]) > 300:
            response_copy["answer"] = response_copy["answer"][:300] + "...[truncated]"
        for source in response_copy.get("sources", []):
            if "text" in source:
                source["text"] = "[...truncated...]"
        print(json.dumps(response_copy, indent=2)[:2000])
        print("...")
        
        # Diagnosis
        print("\n" + "="*70)
        print("DIAGNOSIS:")
        print("="*70)
        llm_enabled = metrics.get("llm_enabled")
        llm_usage = metrics.get("llm_usage")
        
        if llm_enabled:
            print("✅ LLM is enabled in metrics")
            if llm_usage:
                print(f"✅ LLM was called (tokens: {llm_usage.get('total_tokens', 'N/A')})")
            else:
                print("⚠️  LLM enabled but no usage data (unexpected)")
        else:
            print("❌ LLM is DISABLED in metrics")
            print("\nPossible causes:")
            print("  1. LLM_GENERATION_ENABLED env var not set or set to false")
            print("  2. OPENAI_API_KEY not set")
            print("  3. Exception occurred during LLM call (check backend logs)")
            print("  4. generate_answer was not properly sent in request")
        
        if not data.get("answer"):
            print("\n⚠️  No answer generated (empty string)")
        else:
            print(f"\n✅ Answer generated ({len(data.get('answer', ''))} chars)")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server at http://localhost:8000")
        print("Make sure the backend is running.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_llm_enabled()




