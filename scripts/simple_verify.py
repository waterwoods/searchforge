#!/usr/bin/env python3
"""
Simple verification script to test ef_search parameter flow
"""

import os
import sys
import json
import time

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.search.search_pipeline import SearchPipeline

def test_ef_search_flow():
    """Test that ef_search parameter flows through the system."""
    
    # Set environment variables
    os.environ["TUNER_ENABLED"] = "1"
    os.environ["FORCE_HYBRID_ON"] = "0"
    os.environ["CE_CACHE_SIZE"] = "0"
    os.environ["FORCE_CE_ON"] = "0"
    os.environ["TUNER_SAMPLE_SEC"] = "1"
    os.environ["TUNER_COOLDOWN_SEC"] = "1"
    
    # Initialize pipeline
    config = {
        "retriever": {
            "type": "vector",
            "top_k": 10,
            "ef_search": 128
        },
        "reranker": {
            "type": "cross_encoder",
            "model": "cross-encoder/ms-marco-MiniLM-L-2-v2",
            "top_k": 50
        }
    }
    
    pipeline = SearchPipeline(config)
    
    # Test query
    query = "What is ETF expense ratio?"
    collection_name = "beir_fiqa_full_ta"
    
    print("=== Testing EF Search Flow ===")
    print(f"Query: {query}")
    print(f"Collection: {collection_name}")
    print(f"Initial ef_search: 128")
    
    # Capture stdout
    import io
    import contextlib
    
    stdout_capture = io.StringIO()
    
    with contextlib.redirect_stdout(stdout_capture):
        # Run search
        search_results = pipeline.search(
            query=query,
            collection_name=collection_name,
            candidate_k=50
        )
        
        print(f"Search completed. Results: {len(search_results)}")
        
        # Run a few more queries to trigger AutoTuner
        for i in range(3):
            time.sleep(0.5)
            search_results = pipeline.search(
                query=f"Test query {i+1}",
                collection_name=collection_name,
                candidate_k=50
            )
    
    # Parse captured output
    captured_output = stdout_capture.getvalue()
    print("\n=== Captured Output ===")
    print(captured_output)
    
    # Parse JSON events
    events = []
    for line in captured_output.split('\n'):
        line = line.strip()
        if line and line.startswith('{'):
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue
    
    print(f"\n=== Parsed Events ({len(events)}) ===")
    for event in events:
        print(f"{event.get('event', 'UNKNOWN')}: {event}")
    
    # Check for RETRIEVE_VECTOR events
    vector_events = [e for e in events if e.get('event') == 'RETRIEVE_VECTOR']
    print(f"\n=== RETRIEVE_VECTOR Events ({len(vector_events)}) ===")
    for event in vector_events:
        ef_search = event.get('params', {}).get('ef_search', 'NOT_FOUND')
        print(f"ef_search: {ef_search}")
    
    # Check for AutoTuner events
    autotuner_events = [e for e in events if e.get('event') == 'AUTOTUNER_SUGGEST']
    print(f"\n=== AUTOTUNER_SUGGEST Events ({len(autotuner_events)}) ===")
    for event in autotuner_events:
        suggest = event.get('params', {}).get('suggest', {})
        ef_search = suggest.get('ef_search', 'NOT_FOUND')
        print(f"Suggested ef_search: {ef_search}")
    
    return events

if __name__ == "__main__":
    events = test_ef_search_flow()
