#!/usr/bin/env python3
"""
Test script to inspect /api/query response for Airbnb LA collection.
"""
import requests
import json

def test_airbnb_query(question: str):
    """Test a query against airbnb_la_demo collection."""
    url = "http://localhost:8000/api/query"
    payload = {
        "question": question,
        "collection": "airbnb_la_demo",
        "top_k": 5,
        "generate_answer": True,
    }
    
    print(f"\n{'='*60}")
    print(f"Query: {question}")
    print(f"{'='*60}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Print answer
        print("ANSWER:")
        print("-" * 60)
        print(data.get("answer", "No answer"))
        print()
        
        # Print sources structure
        print("SOURCES (first 2):")
        print("-" * 60)
        for i, source in enumerate(data.get("sources", [])[:2], 1):
            print(f"\nSource {i}:")
            print(f"  doc_id: {source.get('doc_id')}")
            print(f"  title: {source.get('title', '')[:80]}")
            print(f"  url: {source.get('url', '')}")
            print(f"  score: {source.get('score', 0.0)}")
            # Airbnb fields
            if 'price' in source:
                print(f"  price: {source.get('price')}")
            if 'bedrooms' in source:
                print(f"  bedrooms: {source.get('bedrooms')}")
            if 'neighbourhood' in source:
                print(f"  neighbourhood: {source.get('neighbourhood')}")
            if 'room_type' in source:
                print(f"  room_type: {source.get('room_type')}")
        
        # Print LLM usage
        print("\nLLM USAGE:")
        print("-" * 60)
        llm_usage = data.get("metrics", {}).get("llm_usage")
        if llm_usage:
            print(json.dumps(llm_usage, indent=2))
        else:
            print("No LLM usage data")
        
        # Print full response (truncated)
        print("\nFULL RESPONSE (truncated, sources text removed):")
        print("-" * 60)
        response_copy = data.copy()
        # Remove long text fields for readability
        for source in response_copy.get("sources", []):
            if "text" in source:
                source["text"] = "[...truncated...]"
        print(json.dumps(response_copy, indent=2)[:2000])
        print("...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_airbnb_query("How much is a 2-day stay in LA?")
    test_airbnb_query("Find a 2 bedroom place in West LA under $200 per night")

