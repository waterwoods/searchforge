#!/usr/bin/env python3
"""
Direct experiment runner that calls SearchPipeline directly to capture trace events
"""

import os
import sys
import time
import json
import argparse
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.search.search_pipeline import SearchPipeline

def load_queries(query_file: str):
    """Load queries from file."""
    with open(query_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

async def run_direct_experiment(collection, queries_file, duration_sec, qps, outdir):
    """Run experiment directly using SearchPipeline"""
    
    # Load queries
    queries = load_queries(queries_file)
    print(f"Loaded {len(queries)} queries")
    
    # Initialize pipeline with pure vector search to test macro knobs
    pipeline = SearchPipeline(config={
        "retriever": {"type": "vector", "top_k": int(os.getenv("CANDIDATE_K_STEP", "200"))}, 
        "reranker": None
    })
    
    # Create output directory
    os.makedirs(outdir, exist_ok=True)
    
    # Redirect stdout to capture trace events
    trace_file = f"{outdir}/trace.log"
    original_stdout = sys.stdout
    
    try:
        with open(trace_file, 'w') as f:
            sys.stdout = f
            
            start_time = time.time()
            query_count = 0
            
            while time.time() - start_time < duration_sec:
                # Select query
                query = queries[query_count % len(queries)]
                
                # Run search
                try:
                    results = pipeline.search(query, collection)
                    query_count += 1
                    
                    if query_count % 50 == 0:
                        print(f"Completed {query_count} queries", file=original_stdout)
                        
                except Exception as e:
                    print(f"Error in query {query_count}: {e}", file=original_stdout)
                
                # Wait for next query based on QPS
                await asyncio.sleep(1.0 / qps)
    
    finally:
        # Restore stdout
        sys.stdout = original_stdout
    
    print(f"Experiment completed: {query_count} queries in {time.time() - start_time:.1f}s")
    print(f"Trace log saved to: {trace_file}")
    
    return query_count

def main():
    parser = argparse.ArgumentParser(description="Run direct experiment with SearchPipeline")
    parser.add_argument("--collection", default="beir_fiqa_full_ta", help="Collection name")
    parser.add_argument("--queries", default="data/fiqa_queries.txt", help="Queries file")
    parser.add_argument("--duration", type=int, default=90, help="Duration in seconds")
    parser.add_argument("--qps", type=int, default=5, help="Queries per second")
    parser.add_argument("--outdir", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    # Run experiment
    asyncio.run(run_direct_experiment(
        collection=args.collection,
        queries_file=args.queries,
        duration_sec=args.duration,
        qps=args.qps,
        outdir=args.outdir
    ))

if __name__ == "__main__":
    main()