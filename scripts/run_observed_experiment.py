#!/usr/bin/env python3
"""
Observed Experiment Runner - Stress Test Orchestration Script

This script runs controlled stress tests with observability instrumentation,
collecting JSON event logs for analysis.
"""

import os
import sys
import time
import json
import argparse
import threading
import requests
from datetime import datetime
from typing import List, Dict, Any
import subprocess
from qdrant_client import QdrantClient

# Enable unbuffered output for real-time logging
os.environ["PYTHONUNBUFFERED"] = "1"
sys.stdout.reconfigure(line_buffering=True)

def verify_docid_field(collection):
    """Verify that the collection has doc_id field in payload for proper recall calculation."""
    client = QdrantClient()
    hits, _ = client.scroll(collection_name=collection, limit=3)
    for h in hits:
        if "doc_id" not in h.payload:
            raise ValueError("❌ Missing `doc_id` in payload — cannot compute recall properly!")
    print(f"✅ Verified collection '{collection}' has doc_id field in payload")

# Sanity check at startup
verify_docid_field("beir_fiqa_full_ta")

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def load_queries(query_file: str) -> List[str]:
    """Load queries from file."""
    with open(query_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def send_query(query: str, collection: str, candidate_k: int, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Send a single query to the RAG API."""
    try:
        response = requests.post(f"{base_url}/search", json={
            "query": query,
            "top_k": 10,
            "algorithm": "cross_encoder"
        }, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "query": query}
    except Exception as e:
        return {"error": str(e), "query": query}

def run_stage(stage_name: str, queries: List[str], candidate_k: int, qps: int, 
              duration_sec: int, base_url: str) -> List[Dict[str, Any]]:
    """Run a single stage of the experiment."""
    print(f"Starting stage: {stage_name} (candidate_k={candidate_k}, qps={qps}, duration={duration_sec}s)")
    
    # Set environment variable for candidate_k
    os.environ["CANDIDATE_K_OVERRIDE"] = str(candidate_k)
    
    results = []
    start_time = time.time()
    query_index = 0
    
    while time.time() - start_time < duration_sec:
        stage_start = time.time()
        
        # Send queries at target QPS
        for _ in range(qps):
            if time.time() - start_time >= duration_sec:
                break
                
            query = queries[query_index % len(queries)]
            result = send_query(query, "beir_fiqa_full_ta", candidate_k, base_url)
            results.append({
                "stage": stage_name,
                "candidate_k": candidate_k,
                "timestamp": time.time(),
                "result": result
            })
            query_index += 1
        
        # Wait to maintain QPS
        elapsed = time.time() - stage_start
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
    
    print(f"Completed stage: {stage_name} ({len(results)} queries)")
    return results

def run_experiment(collection: str, queries_file: str, qps: int, minutes: int, 
                  candidate_k_steps: str, base_url: str = "http://localhost:8000", 
                  outdir: str = "reports/observed") -> Dict[str, Any]:
    """Run the complete experiment."""
    print(f"Starting observed experiment:")
    print(f"  Collection: {collection}")
    print(f"  Queries: {queries_file}")
    print(f"  QPS: {qps}")
    print(f"  Duration: {minutes} minutes")
    print(f"  Candidate K steps: {candidate_k_steps}")
    
    # Load queries
    queries = load_queries(queries_file)
    print(f"Loaded {len(queries)} queries")
    
    # Parse candidate K steps
    k_steps = [int(k.strip()) for k in candidate_k_steps.split(',')]
    stage_duration = (minutes * 60) // len(k_steps)
    
    print(f"Will run {len(k_steps)} stages of {stage_duration}s each")
    
    all_results = []
    stage_results = {}
    
    for i, candidate_k in enumerate(k_steps):
        stage_name = f"stage_{i+1}_k{candidate_k}"
        stage_results[stage_name] = run_stage(
            stage_name, queries, candidate_k, qps, stage_duration, base_url
        )
        all_results.extend(stage_results[stage_name])
    
    # Create output directory
    os.makedirs(outdir, exist_ok=True)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save trace log (JSON events from stdout)
    trace_file = f"{outdir}/trace.log"
    print(f"Saving trace log to: {trace_file}")
    
    # Create empty trace.log file for now (will be populated by actual trace events)
    with open(trace_file, 'w') as f:
        f.write("# Trace log placeholder - actual events would be captured from search pipeline stdout\n")
        f.write(f"# Experiment: {collection}, Duration: {minutes}min, QPS: {qps}\n")
        f.write(f"# Generated: {timestamp}\n")
    
    # Create summary
    summary = {
        "experiment": {
            "collection": collection,
            "queries_file": queries_file,
            "qps": qps,
            "duration_minutes": minutes,
            "candidate_k_steps": candidate_k_steps,
            "timestamp": timestamp,
            "total_queries": len(all_results)
        },
        "stages": {},
        "aggregates": {
            "total_queries": len(all_results),
            "successful_queries": len([r for r in all_results if "error" not in r.get("result", {})]),
            "failed_queries": len([r for r in all_results if "error" in r.get("result", {})])
        }
    }
    
    for stage_name, stage_data in stage_results.items():
        summary["stages"][stage_name] = {
            "queries": len(stage_data),
            "successful": len([r for r in stage_data if "error" not in r.get("result", {})]),
            "failed": len([r for r in stage_data if "error" in r.get("result", {})])
        }
    
    summary_file = f"{outdir}/summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Experiment completed. Summary saved to: {summary_file}")
    return summary

def run_candidate_cycle_experiment(collection, queries_file, duration_sec, qps, cand_cycle, period_sec, base_url, outdir):
    """Run experiment with candidate_k cycling"""
    from modules.search.search_pipeline import SearchPipeline
    from modules.autotune.macros import get_macro_config, derive_params
    
    # Load queries
    queries = load_queries(queries_file)
    print(f"Loaded {len(queries)} queries")
    
    # Parse candidate cycle
    candidate_cycle = [int(x.strip()) for x in cand_cycle.split(',')]
    print(f"Candidate cycle: {candidate_cycle}, period: {period_sec}s")
    
    # Initialize pipeline
    pipeline = SearchPipeline(config={
        "retriever": {"type": "vector", "top_k": candidate_cycle[0]}, 
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
            cycle_index = 0
            last_cycle_time = start_time
            
            # Log initial RUN_INFO event
            run_info_event = {
                "event": "RUN_INFO",
                "trace_id": "mixed_one_experiment",
                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "cost_ms": 0.0,
                "params": {
                    "duration_sec": duration_sec,
                    "latency_guard": float(os.getenv("LATENCY_GUARD", "0.5")),
                    "recall_bias": float(os.getenv("RECALL_BIAS", "0.5")),
                    "candidate_cycle": candidate_cycle,
                    "period_sec": period_sec
                }
            }
            print(json.dumps(run_info_event), flush=True)
            
            # Log initial CYCLE_STEP event (t=0)
            initial_cycle_event = {
                "event": "CYCLE_STEP",
                "candidate_k": candidate_cycle[0],
                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            }
            print(json.dumps(initial_cycle_event), flush=True)
            
            while time.time() - start_time < duration_sec:
                current_time = time.time()
                
                # Check if we need to cycle candidate_k
                if current_time - last_cycle_time >= period_sec:
                    cycle_index = (cycle_index + 1) % len(candidate_cycle)
                    current_candidate_k = candidate_cycle[cycle_index]
                    
                    # Update pipeline config
                    pipeline.config["retriever"]["top_k"] = current_candidate_k
                    
                    # Get current T value from macro knobs
                    macro_config = get_macro_config()
                    derived_params = derive_params(macro_config["latency_guard"], macro_config["recall_bias"])
                    current_T = derived_params["T"]
                    
                    # Log cycle step event
                    cycle_event = {
                        "event": "CYCLE_STEP",
                        "candidate_k": current_candidate_k,
                        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                    }
                    print(json.dumps(cycle_event), flush=True)
                    
                    last_cycle_time = current_time
                    print(f"Cycled to candidate_k={current_candidate_k}, T={current_T}", file=original_stdout)
                
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
                time.sleep(1.0 / qps)
            
            # Log final RUN_INFO event
            final_run_info_event = {
                "event": "RUN_INFO",
                "trace_id": "mixed_one_experiment_end",
                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "cost_ms": 0.0,
                "params": {
                    "duration_sec": duration_sec,
                    "total_queries": query_count,
                    "status": "completed"
                }
            }
            print(json.dumps(final_run_info_event), flush=True)
    
    finally:
        # Restore stdout
        sys.stdout = original_stdout
    
    print(f"Experiment completed: {query_count} queries in {time.time() - start_time:.1f}s")
    print(f"Trace log saved to: {trace_file}")
    
    return query_count

def load_qrels(collection: str) -> Dict[str, List[str]]:
    """Load qrels for recall calculation."""
    try:
        # Try to load BEIR qrels
        from beir import util
        from beir.datasets.data_loader import GenericDataLoader
        
        # For FiQA dataset
        if "fiqa" in collection.lower():
            qrels_file = "data/fiqa/qrels/test.tsv"
        else:
            qrels_file = f"data/{collection}/qrels/test.tsv"
        
        if os.path.exists(qrels_file):
            qrels = {}
            with open(qrels_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if line_num == 1:  # Skip header
                        continue
                    parts = line.strip().split('\t')
                    if len(parts) >= 3:
                        query_id, doc_id, relevance = parts[0], parts[1], parts[2]
                        if query_id not in qrels:
                            qrels[query_id] = []
                        if int(relevance) > 0:  # Only positive relevance
                            qrels[query_id].append(doc_id)
            print(f"Loaded {len(qrels)} query qrels from {qrels_file}")
            return qrels
        else:
            print(f"Warning: Qrels file not found: {qrels_file}")
            return {}
    except Exception as e:
        print(f"Warning: Could not load qrels: {e}")
        return {}

def calculate_recall_at_10(results: List[Any], query_id: str, qrels: Dict[str, List[str]], debug_samples: List[Dict] = None) -> int:
    """Calculate hit@10 for a query result."""
    if not results:
        return None
    
    if query_id not in qrels:
        return None
    
    gold_docs = set(qrels[query_id])
    
    # Extract document IDs from ScoredDocument objects
    # Priority: document.metadata.doc_id > payload.doc_id > document.id
    result_ids = []
    for result in results[:10]:
        doc_id = None
        if hasattr(result, 'document') and hasattr(result.document, 'metadata'):
            doc_id = result.document.metadata.get('doc_id')
        elif hasattr(result, 'payload') and hasattr(result.payload, 'doc_id'):
            doc_id = result.payload.doc_id
        elif hasattr(result, 'document') and hasattr(result.document, 'id'):
            doc_id = result.document.id
        elif hasattr(result, 'id'):
            doc_id = result.id
        
        # 如果 metadata.doc_id 不存在，打警告日志
        if doc_id is None:
            print(f"[WARN] Missing doc_id in result, fallback to default ID {result.document.id}")
        elif hasattr(result, 'document') and hasattr(result.document, 'metadata') and not result.document.metadata.get('doc_id'):
            print(f"[WARN] Missing doc_id in metadata, using fallback ID {doc_id}")
        
        if doc_id:
            result_ids.append(str(doc_id))
    
    # Check if any of top-10 docs are in gold set
    hit_at10 = int(any(doc_id in gold_docs for doc_id in result_ids))
    
    # Add to debug samples if provided
    if debug_samples is not None and len(debug_samples) < 5:
        debug_samples.append({
            "query_id": query_id,
            "gold_ids": list(gold_docs)[:3],
            "top10_ids": result_ids[:5],
            "any_overlap": hit_at10 == 1
        })
    
    return hit_at10

def run_static_suite(collection, profile, outdir):
    """Run static experiment suite with A/B/C phases."""
    import random
    import json
    from modules.search.search_pipeline import SearchPipeline
    from modules.autotune.macros import get_macro_config, derive_params
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Load qrels for recall calculation first
    qrels = load_qrels(collection)
    
    # Load queries from queries.jsonl and filter to only those with qrels
    all_queries = {}
    with open("data/fiqa/queries.jsonl", 'r') as f:
        for line in f:
            if line.strip():
                query_data = json.loads(line)
                all_queries[query_data["_id"]] = query_data["text"]
    
    # Filter to queries that have qrels
    queries = []
    query_ids = []
    for qid in sorted(all_queries.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        if qid in qrels:
            queries.append(all_queries[qid])
            query_ids.append(qid)
            if len(queries) >= 100:
                break
    
    print(f"Loaded {len(queries)} queries for static suite (with qrels)")
    
    # Debug samples for recall verification
    debug_samples = []
    
    # Profile configurations
    if profile == "quick":
        warmup_sec = 3
        route_sec = 12
        ef_sec = 8
        trunc_sec = 12
    else:  # deep
        warmup_sec = 3
        route_sec = 18
        ef_sec = 12
        trunc_sec = 18
    
    # Initialize pipeline
    pipeline = SearchPipeline(config={
        "retriever": {"type": "vector", "top_k": 500}, 
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
            
            # Log initial RUN_INFO event
            run_info_event = {
                "event": "RUN_INFO",
                "trace_id": "static_suite_experiment",
                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "cost_ms": 0.0,
                "params": {
                    "suite": "static",
                    "profile": profile,
                    "collection": collection,
                    "warmup_sec": warmup_sec,
                    "route_sec": route_sec,
                    "ef_sec": ef_sec,
                    "latency_guard": float(os.getenv("LATENCY_GUARD", "0.5")),
                    "recall_bias": float(os.getenv("RECALL_BIAS", "0.5")),
                    "trunc_sec": trunc_sec,
                    "total_queries": len(queries)
                }
            }
            print(json.dumps(run_info_event), flush=True)
            
            # Phase A: Route sweep (N≤T→MEM / N>T→HNSW)
            print("Starting Phase A: Route sweep", file=original_stdout)
            macro_config = get_macro_config()
            derived_params = derive_params(macro_config["latency_guard"], macro_config["recall_bias"])
            T = derived_params["T"]
            
            route_candidates = [T-200, T-50, T-1, T, T+1, T+50, T+200]
            
            for i, candidate_k in enumerate(route_candidates):
                # Log CYCLE_STEP event
                cycle_event = {
                    "event": "CYCLE_STEP",
                    "candidate_k": candidate_k,
                    "phase": "route_sweep",
                    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                }
                print(json.dumps(cycle_event), flush=True)
                
                # Update pipeline config
                pipeline.config["retriever"]["top_k"] = candidate_k
                
                # Run queries for this candidate_k
                phase_start = time.time()
                while time.time() - phase_start < route_sec:
                    query = queries[query_count % len(queries)]
                    query_id = query_ids[query_count % len(queries)]  # Use actual query_id from queries.jsonl
                    try:
                        results = pipeline.search(query, collection)
                        
                        # Calculate recall@10
                        hit_at_10 = calculate_recall_at_10(results, query_id, qrels, debug_samples)
                        
                        # Log additional RESPONSE event with recall data
                        if hit_at_10 is not None:
                            recall_response_event = {
                                "event": "RESPONSE",
                                "trace_id": f"recall_{query_count}",
                                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                                "cost_ms": 0.0,
                                "hit_at10": hit_at_10,
                                "topk": 10,
                                "query_id": query_id
                            }
                            print(json.dumps(recall_response_event), flush=True)
                        
                        query_count += 1
                    except Exception as e:
                        print(f"Error in query {query_count}: {e}", file=original_stdout)
                        hit_at_10 = None
                    
                    time.sleep(1.0 / 5)  # 5 QPS
                
                print(f"Phase A: candidate_k={candidate_k} completed", file=original_stdout)
            
            # Phase B: EF sweep (fixed HNSW, scan ef)
            print("Starting Phase B: EF sweep", file=original_stdout)
            ef_values = [64, 96, 128, 160, 192, 224, 256]
            
            for i, ef in enumerate(ef_values):
                # Log CYCLE_STEP event
                cycle_event = {
                    "event": "CYCLE_STEP",
                    "candidate_k": T + 200,  # Force HNSW
                    "ef": ef,
                    "phase": "ef_sweep",
                    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                }
                print(json.dumps(cycle_event), flush=True)
                
                # Update pipeline config
                pipeline.config["retriever"]["top_k"] = T + 200
                pipeline.config["retriever"]["ef_search"] = ef
                
                # Run queries for this ef
                phase_start = time.time()
                while time.time() - phase_start < ef_sec:
                    query = queries[query_count % len(queries)]
                    query_id = query_ids[query_count % len(queries)]  # Use actual query_id from queries.jsonl
                    try:
                        results = pipeline.search(query, collection)
                        
                        # Calculate recall@10
                        hit_at_10 = calculate_recall_at_10(results, query_id, qrels, debug_samples)
                        
                        # Log additional RESPONSE event with recall data
                        if hit_at_10 is not None:
                            recall_response_event = {
                                "event": "RESPONSE",
                                "trace_id": f"recall_{query_count}",
                                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                                "cost_ms": 0.0,
                                "hit_at10": hit_at_10,
                                "topk": 10,
                                "query_id": query_id
                            }
                            print(json.dumps(recall_response_event), flush=True)
                        
                        query_count += 1
                    except Exception as e:
                        print(f"Error in query {query_count}: {e}", file=original_stdout)
                        hit_at_10 = None
                    
                    time.sleep(1.0 / 5)  # 5 QPS
                
                print(f"Phase B: ef={ef} completed", file=original_stdout)
            
            # Phase C: Truncation sweep
            print("Starting Phase C: Truncation sweep", file=original_stdout)
            trunc_configs = [
                {"Ncand_max": 1500, "rerank_multiplier": 4},
                {"Ncand_max": 1000, "rerank_multiplier": 4},
                {"Ncand_max": 500, "rerank_multiplier": 2}
            ]
            
            for i, config in enumerate(trunc_configs):
                # Log CYCLE_STEP event
                cycle_event = {
                    "event": "CYCLE_STEP",
                    "candidate_k": T + 200,  # Keep HNSW
                    "phase": "truncation_sweep",
                    "Ncand_max": config["Ncand_max"],
                    "rerank_multiplier": config["rerank_multiplier"],
                    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                }
                print(json.dumps(cycle_event), flush=True)
                
                # Update pipeline config
                pipeline.config["retriever"]["top_k"] = T + 200
                
                # Run queries for this config
                phase_start = time.time()
                while time.time() - phase_start < trunc_sec:
                    query = queries[query_count % len(queries)]
                    query_id = query_ids[query_count % len(queries)]  # Use actual query_id from queries.jsonl
                    try:
                        results = pipeline.search(query, collection)
                        
                        # Calculate recall@10
                        hit_at_10 = calculate_recall_at_10(results, query_id, qrels, debug_samples)
                        
                        # Log additional RESPONSE event with recall data
                        if hit_at_10 is not None:
                            recall_response_event = {
                                "event": "RESPONSE",
                                "trace_id": f"recall_{query_count}",
                                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                                "cost_ms": 0.0,
                                "hit_at10": hit_at_10,
                                "topk": 10,
                                "query_id": query_id
                            }
                            print(json.dumps(recall_response_event), flush=True)
                        
                        query_count += 1
                    except Exception as e:
                        print(f"Error in query {query_count}: {e}", file=original_stdout)
                        hit_at_10 = None
                    
                    time.sleep(1.0 / 5)  # 5 QPS
                
                print(f"Phase C: Ncand_max={config['Ncand_max']}, rerank_multiplier={config['rerank_multiplier']} completed", file=original_stdout)
            
            # Log final RUN_INFO event
            final_run_info_event = {
                "event": "RUN_INFO",
                "trace_id": "static_suite_experiment_end",
                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "cost_ms": 0.0,
                "params": {
                    "total_queries": query_count,
                    "status": "completed"
                }
            }
            print(json.dumps(final_run_info_event), flush=True)
            
            # Log debug samples as special events
            for i, sample in enumerate(debug_samples):
                debug_event = {
                    "event": "RECALL_DEBUG_SAMPLE",
                    "trace_id": f"debug_sample_{i}",
                    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                    "cost_ms": 0.0,
                    "params": sample
                }
                print(json.dumps(debug_event), flush=True)
    
    finally:
        # Restore stdout
        sys.stdout = original_stdout
    
    print(f"Static suite completed: {query_count} queries in {time.time() - start_time:.1f}s")
    print(f"Trace log saved to: {trace_file}")
    
    # Print debug samples for recall verification
    print("\n=== Recall@10 Debug Samples ===")
    for i, sample in enumerate(debug_samples):
        print(f"Sample {i+1}: query_id={sample['query_id']}, gold_ids={sample['gold_ids']}, top10_ids={sample['top10_ids']}, overlap={sample['any_overlap']}")
    
    return query_count

def main():
    parser = argparse.ArgumentParser(description="Run observed experiment with stress testing")
    parser.add_argument("--dataset", default="beir_fiqa_full_ta", help="Dataset/collection name")
    parser.add_argument("--queries", default="data/fiqa_queries.txt", help="Queries file")
    parser.add_argument("--qps", type=int, default=5, help="Queries per second")
    parser.add_argument("--duration", type=int, default=180, help="Total duration in seconds")
    parser.add_argument("--duration-sec", type=int, help="Total duration in seconds (alternative)")
    parser.add_argument("--base-url", default="http://localhost:8000", help="RAG API base URL")
    parser.add_argument("--outdir", default="reports/observed", help="Output directory")
    parser.add_argument("--out-dir", help="Output directory (alternative)")
    parser.add_argument("--cand-cycle", help="Comma-separated candidate_k cycle (e.g., '300,800,400,700,500')")
    parser.add_argument("--period-sec", type=int, default=18, help="Period in seconds for candidate_k cycling")
    parser.add_argument("--mixed-one", action="store_true", help="Run mixed-one experiment mode")
    parser.add_argument("--suite", choices=["static"], help="Run static experiment suite")
    parser.add_argument("--profile", choices=["quick", "deep"], default="quick", help="Profile for static suite: quick (3min) or deep (4.5min)")
    parser.add_argument("--collection", help="Collection name for static suite")
    
    args = parser.parse_args()
    
    # Handle alternative argument names
    duration = args.duration_sec if args.duration_sec else args.duration
    outdir = args.out_dir if args.out_dir else args.outdir
    
    # Check if we should run static suite
    if args.suite == "static":
        collection = args.collection or args.dataset
        query_count = run_static_suite(
            collection=collection,
            profile=args.profile,
            outdir=outdir
        )
        print(f"Static suite completed: {query_count} queries")
        return
    # Check if we should run candidate cycle experiment
    elif args.cand_cycle or args.mixed_one:
        run_candidate_cycle_experiment(
            collection=args.dataset,
            queries_file=args.queries,
            duration_sec=duration,
            qps=args.qps,
            cand_cycle=args.cand_cycle or "400,800,500,900,600",
            period_sec=args.period_sec,
            base_url=args.base_url,
            outdir=outdir
        )
    else:
        # Get candidate K steps from environment
        candidate_k_steps = os.getenv("CANDIDATE_K_STEP", "100,200,400")
        
        # Run experiment
        summary = run_experiment(
            collection=args.dataset,
            queries_file=args.queries,
            qps=args.qps,
            minutes=duration // 60,
            candidate_k_steps=candidate_k_steps,
            base_url=args.base_url,
            outdir=outdir
        )
    
    if not args.cand_cycle:
        print("Experiment completed successfully!")
        print(f"Total queries: {summary['aggregates']['total_queries']}")
        print(f"Successful: {summary['aggregates']['successful_queries']}")
        print(f"Failed: {summary['aggregates']['failed_queries']}")

if __name__ == "__main__":
    main()
