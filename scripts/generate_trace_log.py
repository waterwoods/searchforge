#!/usr/bin/env python3
"""
Generate comprehensive trace log for observability testing.
"""

import os
import sys
import json
import time
import uuid
from typing import List

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def generate_trace_events():
    """Generate comprehensive trace events for testing."""
    
    # Simulate the complete event sequence
    trace_id = str(uuid.uuid4())
    
    events = []
    
    # 0. RUN_INFO event
    events.append({
        "event": "RUN_INFO",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 0.0,
        "params": {
            "dataset": "beir_fiqa_full_ta",
            "collection": "beir_fiqa_full_ta",
            "TUNER_ENABLED": int(os.getenv("TUNER_ENABLED", "1")),
            "FORCE_CE_ON": int(os.getenv("FORCE_CE_ON", "1")),
            "FORCE_HYBRID_ON": int(os.getenv("FORCE_HYBRID_ON", "1")),
            "CE_CACHE_SIZE": int(os.getenv("CE_CACHE_SIZE", "0"))
        }
    })
    
    # 1. FETCH_QUERY
    events.append({
        "event": "FETCH_QUERY",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 0.0,
        "params": {"query": "What is ETF expense ratio?", "collection": "beir_fiqa_full_ta"},
        "stats": {"candidate_k": 100}
    })
    
    # 2. RETRIEVE_VECTOR
    events.append({
        "event": "RETRIEVE_VECTOR",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 45.2,
        "params": {"candidate_k": 100, "ef_search": 128},
        "stats": {"candidates_returned": 100}
    })
    
    # 3. RETRIEVE_BM25
    events.append({
        "event": "RETRIEVE_BM25",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 12.8,
        "params": {"bm25_top_k": 100},
        "stats": {"candidates_returned": 95}
    })
    
    # 4. FUSE_HYBRID
    events.append({
        "event": "FUSE_HYBRID",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 3.1,
        "params": {"alpha": 0.6, "vector_k": 100, "bm25_k": 100},
        "stats": {"candidates_fused": 150}
    })
    
    # 5. RERANK_CE
    events.append({
        "event": "RERANK_CE",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 350.0,
        "params": {
            "model": "cross-encoder/ms-marco-MiniLM-L-2-v2", 
            "batch_size": 32, 
            "cache_size": 0,
            "cache_hits": 0,
            "cache_miss": 50
        },
        "stats": {"top_10_ids": ["25438", "27261", "20233"]}
    })
    
    # 6. AUTOTUNER_SUGGEST
    events.append({
        "event": "AUTOTUNER_SUGGEST",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 0.0,
        "params": {
            "p95_ms": 850.0, 
            "recall_at10": 0.85,
            "suggest": {"ef_search": 160, "rerank_k": 50}
        },
        "stats": {"suggestions_made": 1}
    })
    
    # 7. PARAMS_APPLIED
    events.append({
        "event": "PARAMS_APPLIED",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 0.0,
        "applied": {"applied": True, "old_ef_search": 128, "new_ef_search": 160, "reason": "increase"},
        "note": "AutoTuner suggestion applied"
    })
    
    # 8. RESPONSE
    events.append({
        "event": "RESPONSE",
        "trace_id": trace_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "cost_ms": 450.0,
        "stats": {"total_results": 10, "top1_id": "25438"},
        "params": {"slo_violated": False, "slo_p95_ms": 1200}
    })
    
    return events

def generate_stage_events(stage_name: str, candidate_k: int, num_queries: int = 10):
    """Generate events for a specific stage."""
    all_events = []
    
    for i in range(num_queries):
        # Simulate different ef_search values over time
        ef_search = 128 + (i * 16) if i < 5 else 128 - ((i - 5) * 8)
        ef_search = max(64, min(256, ef_search))
        
        # Generate events for this query
        events = generate_trace_events()
        
        # Update candidate_k and ef_search values
        for event in events:
            if event["event"] == "FETCH_QUERY":
                event["stats"]["candidate_k"] = candidate_k
            elif event["event"] == "RETRIEVE_VECTOR":
                event["params"]["candidate_k"] = candidate_k
                event["params"]["ef_search"] = ef_search
            elif event["event"] == "RETRIEVE_BM25":
                event["params"]["bm25_top_k"] = candidate_k
            elif event["event"] == "FUSE_HYBRID":
                event["params"]["vector_k"] = candidate_k
                event["params"]["bm25_k"] = candidate_k
            elif event["event"] == "AUTOTUNER_SUGGEST":
                # Simulate different suggestions
                if i < 3:
                    event["params"]["suggest"] = {"ef_search": ef_search + 32, "rerank_k": 50}
                elif i < 6:
                    event["params"]["suggest"] = {"ef_search": ef_search, "rerank_k": 50}
                else:
                    event["params"]["suggest"] = {"ef_search": ef_search - 16, "rerank_k": 50}
            elif event["event"] == "PARAMS_APPLIED":
                # Find the AUTOTUNER_SUGGEST event in this query's events
                autotuner_event = None
                for e in events:
                    if e["event"] == "AUTOTUNER_SUGGEST":
                        autotuner_event = e
                        break
                
                if autotuner_event:
                    suggestion = autotuner_event["params"]["suggest"]
                    event["applied"]["old_ef_search"] = ef_search
                    event["applied"]["new_ef_search"] = suggestion["ef_search"]
                    event["applied"]["reason"] = "increase" if suggestion["ef_search"] > ef_search else "decrease" if suggestion["ef_search"] < ef_search else "keep"
            elif event["event"] == "RESPONSE":
                # Simulate latency based on candidate_k and ef_search
                base_latency = 200 + (candidate_k / 10) + (ef_search / 4)
                event["cost_ms"] = base_latency
                event["params"]["slo_violated"] = base_latency > 1200
        
        all_events.extend(events)
        time.sleep(0.1)  # Small delay between queries
    
    return all_events

def main():
    """Generate comprehensive trace log."""
    
    # Create output directory
    os.makedirs("reports/observed", exist_ok=True)
    
    # Generate events for all stages
    all_events = []
    
    # Stage 1: candidate_k = 100
    print("Generating events for stage 1 (candidate_k=100)...")
    stage1_events = generate_stage_events("stage_1_k100", 100, 15)
    all_events.extend(stage1_events)
    
    # Stage 2: candidate_k = 200
    print("Generating events for stage 2 (candidate_k=200)...")
    stage2_events = generate_stage_events("stage_2_k200", 200, 15)
    all_events.extend(stage2_events)
    
    # Stage 3: candidate_k = 400
    print("Generating events for stage 3 (candidate_k=400)...")
    stage3_events = generate_stage_events("stage_3_k400", 400, 15)
    all_events.extend(stage3_events)
    
    # Save to trace log
    trace_file = "reports/observed/trace.log"
    with open(trace_file, 'w') as f:
        for event in all_events:
            f.write(json.dumps(event) + '\n')
    
    print(f"Generated {len(all_events)} events in {trace_file}")
    
    # Print summary
    event_counts = {}
    for event in all_events:
        event_type = event["event"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    print("\nEvent summary:")
    for event_type, count in sorted(event_counts.items()):
        print(f"  {event_type}: {count}")

if __name__ == "__main__":
    main()
