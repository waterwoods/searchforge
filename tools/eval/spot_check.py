#!/usr/bin/env python3
"""
Spot Check Tool - Verify overlap between search results and qrels.

Given a query ID, calls the search API and checks how many top10 doc_ids
from the response match doc_ids in qrels for that query.
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Install with: pip install requests")
    sys.exit(1)


# ID normalization helpers (same as fiqa_lib.py)
def _norm_doc_id(x: any) -> str:
    """Normalize document ID: extract digits only, remove leading zeros."""
    if x is None:
        return ""
    s = re.sub(r'\D+', '', str(x))
    return str(int(s)) if s else ""


def _norm_qid(x: any) -> str:
    """Normalize query ID: extract digits only, remove leading zeros."""
    if x is None:
        return ""
    s = re.sub(r'\D+', '', str(x))
    return str(int(s)) if s else ""


def load_qrels(qrels_path: str) -> Dict[str, Set[str]]:
    """Load qrels file and return {normalized_query_id: set(normalized_doc_ids)}."""
    qrels_file = Path(qrels_path)
    if not qrels_file.exists():
        raise FileNotFoundError(f"Qrels file not found: {qrels_path}")
    
    qrels = {}
    with open(qrels_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0 and ("query_id" in line.lower() or line.startswith("query_id")):
                continue
            if line.strip():
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    raw_qid = parts[0].strip()
                    raw_docid = parts[1].strip()
                    if raw_qid and raw_docid:
                        qid = _norm_qid(raw_qid)
                        did = _norm_doc_id(raw_docid)
                        if qid and did:
                            if qid not in qrels:
                                qrels[qid] = set()
                            qrels[qid].add(did)
    return qrels


def load_queries(queries_path: str) -> List[Dict[str, str]]:
    """Load queries from JSONL file and normalize query IDs."""
    queries_file = Path(queries_path)
    if not queries_file.exists():
        raise FileNotFoundError(f"Queries file not found: {queries_path}")
    
    queries = []
    with open(queries_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                raw_qid = data.get("query_id", "")
                # Normalize query_id for consistent matching
                qid = _norm_qid(raw_qid)
                queries.append({
                    "query_id": qid,  # Store normalized ID
                    "text": data.get("text", data.get("question", ""))
                })
    return queries


def extract_doc_ids(response: Dict) -> List[str]:
    """Extract and normalize doc_ids from API response sources."""
    sources = response.get("sources", [])
    doc_ids_raw = []
    for src in sources:
        doc_id = src.get("doc_id")
        if not doc_id:
            payload = src.get("payload", {})
            if isinstance(payload, dict):
                doc_id = payload.get("doc_id")
        if not doc_id:
            doc_id = src.get("id")
        if doc_id:
            doc_ids_raw.append(doc_id)
    # Normalize all doc_ids
    return [_norm_doc_id(did) for did in doc_ids_raw if _norm_doc_id(did)]


def check_overlap(
    host: str,
    collection: str,
    query_id: str,
    query_text: str,
    qrels: Dict[str, Set[str]],
    top_k: int = 10
) -> Dict[str, any]:
    """Check overlap between search results and qrels for a query."""
    url = f"{host}/api/query"
    payload = {
        "question": query_text,
        "top_k": top_k,
        "collection": collection
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        response_data = resp.json()
        
        retrieved_doc_ids = extract_doc_ids(response_data)  # Already normalized
        # Normalize query_id for lookup
        norm_qid = _norm_qid(query_id)
        relevant_doc_ids = qrels.get(norm_qid, set())
        
        overlap = set(retrieved_doc_ids[:top_k]) & relevant_doc_ids
        overlap_count = len(overlap)
        
        return {
            "query_id": query_id,
            "norm_query_id": norm_qid,
            "retrieved_count": len(retrieved_doc_ids),
            "relevant_count": len(relevant_doc_ids),
            "overlap_count": overlap_count,
            "overlap_ratio": overlap_count / len(relevant_doc_ids) if relevant_doc_ids else 0.0,
            "retrieved_doc_ids": retrieved_doc_ids[:top_k],
            "overlap_doc_ids": list(overlap)
        }
    except Exception as e:
        return {
            "query_id": query_id,
            "error": str(e),
            "overlap_count": 0
        }


def main():
    parser = argparse.ArgumentParser(description="Spot Check Tool")
    parser.add_argument("--collection", type=str, required=True, help="Collection name")
    parser.add_argument("--qrels", type=str, required=True, help="Path to qrels TSV file")
    parser.add_argument("--host", type=str, default="http://127.0.0.1:8000", help="API host URL")
    parser.add_argument("--n", type=int, default=3, help="Number of queries to check")
    parser.add_argument("--queries", type=str, required=True, help="Path to queries JSONL file (required)")
    parser.add_argument("--top_k", type=int, default=10, help="Top-K for search results (default: 10)")
    parser.add_argument("--json-out", type=str, default=None, help="Optional path to write JSON output")
    
    args = parser.parse_args()
    
    # Load qrels
    qrels = load_qrels(args.qrels)
    print(f"Loaded {len(qrels)} query-doc pairs from {args.qrels}")
    
    # Load queries (required)
    queries = load_queries(args.queries)
    
    # Sample N queries
    if len(queries) > args.n:
        queries = random.sample(queries, args.n)
    
    print(f"\nChecking {len(queries)} queries...")
    print("=" * 80)
    
    results = []
    for query in queries:
        query_id = query["query_id"]
        query_text = query["text"]
        
        result = check_overlap(
            host=args.host,
            collection=args.collection,
            query_id=query_id,
            query_text=query_text,
            qrels=qrels,
            top_k=args.top_k
        )
        results.append(result)
        
        if "error" in result:
            print(f"❌ Query {query_id}: ERROR - {result['error']}")
        else:
            print(f"Query {query_id}:")
            print(f"  Retrieved: {result['retrieved_count']} doc_ids")
            print(f"  Relevant: {result['relevant_count']} doc_ids")
            print(f"  Overlap: {result['overlap_count']} doc_ids")
            print(f"  Overlap ratio: {result['overlap_ratio']:.2%}")
            if result['overlap_doc_ids']:
                print(f"  Overlap doc_ids: {result['overlap_doc_ids'][:5]}...")
            print()
    
    # Summary
    overlap_counts = [r.get("overlap_count", 0) for r in results if "error" not in r]
    if overlap_counts:
        avg_overlap = sum(overlap_counts) / len(overlap_counts)
        min_overlap = min(overlap_counts)
        max_overlap = max(overlap_counts)
        print("=" * 80)
        print(f"Summary: avg_overlap={avg_overlap:.1f}, min={min_overlap}, max={max_overlap}")
        print(f"All queries have overlap_count >= 1: {all(c >= 1 for c in overlap_counts)}")
    
    # Output JSON
    output = {
        "collection": args.collection,
        "qrels": args.qrels,
        "n_checked": len(results),
        "results": results,
        "summary": {
            "avg_overlap": avg_overlap if overlap_counts else 0.0,
            "min_overlap": min_overlap if overlap_counts else 0,
            "max_overlap": max_overlap if overlap_counts else 0,
            "all_ge_1": all(c >= 1 for c in overlap_counts) if overlap_counts else False
        }
    }
    print("\nJSON Output:")
    print(json.dumps(output, indent=2))
    
    # Write to file if requested
    if args.json_out:
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        print(f"\nJSON written to: {args.json_out}")
    
    # Exit code: 0 if all have overlap >= 1, else 1
    sys.exit(0 if (overlap_counts and all(c >= 1 for c in overlap_counts)) else 1)


if __name__ == "__main__":
    main()

