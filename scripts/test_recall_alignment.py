#!/usr/bin/env python3
"""
Test script to verify doc_id alignment and Recall@10 calculation.
Runs a small canary test with real queries and compares before/after Recall@10.
"""

import requests
import json
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_test_queries(limit: int = 10) -> List[tuple]:
    """Load test queries with their IDs from qrels."""
    qrels_file = Path(__file__).parent.parent / "data" / "fiqa" / "qrels" / "test.tsv"
    queries_file = Path(__file__).parent.parent / "data" / "fiqa" / "queries.jsonl"
    
    if not qrels_file.exists() or not queries_file.exists():
        print(f"❌ Required files not found")
        return []
    
    # Load qrels to get query IDs
    qrels = {}
    with open(qrels_file, 'r') as f:
        for i, line in enumerate(f):
            if i == 0:  # Skip header
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                query_id, doc_id, relevance = parts[0], parts[1], parts[2]
                if int(relevance) > 0:
                    if query_id not in qrels:
                        qrels[query_id] = set()
                    qrels[query_id].add(doc_id)
    
    # Load query texts
    queries_map = {}
    with open(queries_file, 'r') as f:
        for line in f:
            if line.strip():
                query_data = json.loads(line)
                queries_map[query_data["_id"]] = query_data["text"]
    
    # Create test set: query_id, query_text, relevant_docs
    test_queries = []
    for qid in sorted(qrels.keys()):
        if qid in queries_map and len(test_queries) < limit:
            test_queries.append((qid, queries_map[qid], qrels[qid]))
    
    return test_queries


def calculate_recall_at_10(doc_ids: List[str], relevant_docs: Set[str]) -> float:
    """Calculate Recall@10."""
    if not relevant_docs:
        return 0.0
    
    hits = sum(1 for doc_id in doc_ids[:10] if doc_id in relevant_docs)
    return hits / min(10, len(relevant_docs))


def test_recall_alignment(api_url: str = "http://localhost:8080"):
    """Test Recall@10 with and without query_id."""
    print("="*60)
    print("RECALL@10 ALIGNMENT TEST")
    print("="*60)
    
    # Check API availability
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not available at {api_url}")
            return 1
    except Exception as e:
        print(f"❌ API not reachable: {e}")
        print(f"   Start the API with: ./launch_real_env.sh")
        return 1
    
    print(f"✓ API is reachable at {api_url}\n")
    
    # Load test queries
    test_queries = load_test_queries(limit=10)
    
    if not test_queries:
        print("❌ No test queries loaded")
        return 1
    
    print(f"✓ Loaded {len(test_queries)} test queries\n")
    
    # Test with query_id (should calculate real Recall@10)
    print("Testing WITH query_id (real Recall@10):")
    print("-" * 60)
    
    recalls_with_qid = []
    for qid, query_text, relevant_docs in test_queries:
        try:
            response = requests.post(
                f"{api_url}/search",
                json={"query": query_text, "top_k": 10, "query_id": qid},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                doc_ids = result.get("doc_ids", [])
                
                # Calculate recall manually
                recall = calculate_recall_at_10(doc_ids, relevant_docs)
                recalls_with_qid.append(recall)
                
                print(f"  Query {qid}: Recall@10 = {recall:.3f}")
                print(f"    Top 3 doc_ids: {doc_ids[:3]}")
                print(f"    Relevant docs (sample): {list(relevant_docs)[:3]}")
            else:
                print(f"  Query {qid}: ERROR {response.status_code}")
        
        except Exception as e:
            print(f"  Query {qid}: Exception: {e}")
    
    avg_recall_with_qid = sum(recalls_with_qid) / len(recalls_with_qid) if recalls_with_qid else 0.0
    
    print(f"\n✓ Average Recall@10 (with query_id): {avg_recall_with_qid:.3f}")
    print(f"  Expected range: 0.3 - 0.8 for FIQA")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if avg_recall_with_qid > 0.2:
        print(f"✅ PASS: Recall@10 = {avg_recall_with_qid:.3f} (doc_id alignment working)")
        print(f"   Doc IDs are correctly extracted from Qdrant payload")
        print(f"   Real Recall@10 calculation is functional")
        return 0
    else:
        print(f"❌ FAIL: Recall@10 = {avg_recall_with_qid:.3f} (too low)")
        print(f"   Expected: > 0.2 for FIQA dataset")
        print(f"   Possible issues:")
        print(f"     - Doc IDs not correctly extracted from Qdrant")
        print(f"     - Mismatch between Qdrant doc_ids and qrels doc_ids")
        print(f"   Check fix.log for details")
        return 1


if __name__ == "__main__":
    sys.exit(test_recall_alignment())

