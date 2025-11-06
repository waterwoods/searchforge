#!/usr/bin/env python3
"""
Test script to generate observability trace logs directly from the search pipeline.
"""

import os
import sys
import json
import time
from typing import List

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_search_pipeline():
    """Test the search pipeline with observability."""
    from modules.search.search_pipeline import SearchPipeline
    
    # Create a simple config
    config = {
        "retriever": {
            "type": "vector",
            "top_k": 100
        },
        "reranker": {
            "type": "simple_ce",
            "model": "cross-encoder/ms-marco-MiniLM-L-2-v2",
            "top_k": 50,
            "batch_size": 32,
            "cache_size": 0
        },
        "rerank_k": 50
    }
    
    # Initialize pipeline
    pipeline = SearchPipeline(config)
    
    # Test queries
    queries = [
        "What is ETF expense ratio?",
        "How is APR different from APY?",
        "How are dividends taxed in the US?",
        "What is a mutual fund load?",
        "How do bond coupons work?"
    ]
    
    print("Testing search pipeline with observability...")
    
    # Run queries
    for i, query in enumerate(queries):
        print(f"Query {i+1}: {query}")
        try:
            results = pipeline.search(
                query=query,
                collection_name="beir_fiqa_full_ta",
                candidate_k=100 + (i * 100)  # Vary candidate_k
            )
            print(f"  Results: {len(results)} documents")
        except Exception as e:
            print(f"  Error: {e}")
        
        time.sleep(1)  # Small delay between queries
    
    print("Observability test completed!")

if __name__ == "__main__":
    test_search_pipeline()
