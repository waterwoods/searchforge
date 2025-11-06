#!/usr/bin/env python3
"""
gold_prepare.py - Prepare Gold Standard Candidate CSV
====================================================
Merges BM25 and vector results, deduplicates, and exports candidate CSV for labeling.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas")
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None


def load_queries(queries_path: str) -> Dict[str, str]:
    """Load queries from TSV (qid, text) or JSONL."""
    queries = {}
    queries_path_obj = Path(queries_path)
    
    if queries_path_obj.suffix == '.tsv':
        df = pd.read_csv(queries_path, sep='\t', header=None, names=['qid', 'text'])
        for _, row in df.iterrows():
            queries[str(row['qid'])] = row['text']
    elif queries_path_obj.suffix == '.jsonl':
        with open(queries_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                qid = data.get("query_id") or data.get("_id", "")
                text = data.get("text", "")
                queries[str(qid)] = text
    
    return queries


def load_run_file(run_path: str) -> Dict[str, List[Dict]]:
    """Load run file (JSONL or TSV format)."""
    run_path_obj = Path(run_path)
    
    if run_path_obj.suffix == '.jsonl':
        runs = {}
        with open(run_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                qid = data.get("query_id") or data.get("qid", "")
                results = data.get("results", [])
                runs[qid] = results
        return runs
    
    elif run_path_obj.suffix == '.tsv':
        runs = defaultdict(list)
        df = pd.read_csv(run_path, sep='\t', header=None, names=['query_id', 'doc_id', 'rank', 'score'])
        for _, row in df.iterrows():
            qid = str(row['query_id'])
            runs[qid].append({
                "doc_id": str(row['doc_id']),
                "score": float(row['score']),
                "rank": int(row['rank'])
            })
        # Sort by rank
        for qid in runs:
            runs[qid].sort(key=lambda x: x['rank'])
        return dict(runs)
    
    else:
        print(f"ERROR: Unsupported file format: {run_path_obj.suffix}", file=sys.stderr)
        sys.exit(1)


def fetch_doc_info(qdrant_host: str, qdrant_port: int, collection: str, doc_ids: List[str]) -> Dict[str, Dict]:
    """Fetch document info from Qdrant."""
    if requests is None:
        return {}
    
    base_url = f"http://{qdrant_host}:{qdrant_port}"
    
    # Batch fetch points
    doc_info = {}
    batch_size = 100
    
    for i in range(0, len(doc_ids), batch_size):
        batch = doc_ids[i:i+batch_size]
        
        try:
            response = requests.post(
                f"{base_url}/collections/{collection}/points/retrieve",
                json={"ids": batch, "with_payload": True},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            for point in data.get("result", []):
                doc_id = str(point.get("id", ""))
                payload = point.get("payload", {})
                doc_info[doc_id] = {
                    "title": payload.get("title", ""),
                    "text": payload.get("text", "")[:200] if payload.get("text") else "",
                    "snippet": (payload.get("text", "") or payload.get("abstract", ""))[:200]
                }
        except Exception as e:
            print(f"WARNING: Failed to fetch batch: {e}", file=sys.stderr)
    
    return doc_info


def merge_and_deduplicate(
    vector_runs: Dict[str, List[Dict]],
    bm25_runs: Dict[str, List[Dict]],
    per_query: int = 20
) -> Dict[str, List[Dict]]:
    """Merge BM25 and vector results, deduplicate, and take top per_query."""
    merged = {}
    
    for qid in set(list(vector_runs.keys()) + list(bm25_runs.keys())):
        # Get results from both sources
        vector_results = vector_runs.get(qid, [])
        bm25_results = bm25_runs.get(qid, [])
        
        # Combine and deduplicate by doc_id (keep highest score)
        seen = {}
        for result in vector_results + bm25_results:
            doc_id = str(result.get("doc_id", ""))
            score = result.get("score", 0.0)
            source = "vector" if result in vector_results else "bm25"
            
            if doc_id not in seen or seen[doc_id]["score"] < score:
                seen[doc_id] = {
                    "doc_id": doc_id,
                    "score": score,
                    "source": source
                }
        
        # Sort by score and take top per_query
        sorted_results = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
        merged[qid] = sorted_results[:per_query]
    
    return merged


def main():
    parser = argparse.ArgumentParser(description="Prepare gold standard candidate CSV")
    parser.add_argument("--queries", required=True, help="Queries file (TSV or JSONL)")
    parser.add_argument("--runs", required=True, help="Vector run file (JSONL or TSV)")
    parser.add_argument("--bm25-runs", help="BM25 run file (JSONL or TSV, optional)")
    parser.add_argument("--per-query", type=int, default=20, help="Candidates per query (default: 20)")
    parser.add_argument("--qdrant-host", default="qdrant", help="Qdrant host for fetching doc info")
    parser.add_argument("--qdrant-port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--collection", help="Collection name for fetching doc info")
    parser.add_argument("--out", default="reports/gold_candidates.csv", help="Output CSV path")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetching doc info from Qdrant")
    
    args = parser.parse_args()
    
    # Load queries
    print(f"Loading queries from {args.queries}...")
    queries = load_queries(args.queries)
    print(f"Loaded {len(queries)} queries")
    
    # Load vector runs
    print(f"Loading vector runs from {args.runs}...")
    vector_runs = load_run_file(args.runs)
    print(f"Loaded {len(vector_runs)} vector runs")
    
    # Load BM25 runs if provided
    bm25_runs = {}
    if args.bm25_runs:
        print(f"Loading BM25 runs from {args.bm25_runs}...")
        bm25_runs = load_run_file(args.bm25_runs)
        print(f"Loaded {len(bm25_runs)} BM25 runs")
    
    # Merge and deduplicate
    print(f"Merging and deduplicating results (top {args.per_query} per query)...")
    merged = merge_and_deduplicate(vector_runs, bm25_runs, per_query=args.per_query)
    
    # Prepare CSV rows
    rows = []
    for qid, results in merged.items():
        query_text = queries.get(qid, "")
        for result in results:
            rows.append({
                "qid": qid,
                "query": query_text,
                "doc_id": result["doc_id"],
                "score": result["score"],
                "source": result["source"],
                "title": "",  # Will be filled if fetching
                "snippet": "",
                "label": ""  # For manual labeling
            })
    
    # Fetch doc info if requested
    if not args.skip_fetch and args.collection:
        print(f"Fetching document info from collection {args.collection}...")
        try:
            import requests
            all_doc_ids = [row["doc_id"] for row in rows]
            doc_info = fetch_doc_info(
                args.qdrant_host, args.qdrant_port, args.collection, all_doc_ids
            )
            
            # Update rows with doc info
            for row in rows:
                info = doc_info.get(row["doc_id"], {})
                row["title"] = info.get("title", "")
                row["snippet"] = info.get("snippet", "")
        except ImportError:
            print("WARNING: requests not available, skipping doc info fetch", file=sys.stderr)
        except Exception as e:
            print(f"WARNING: Failed to fetch doc info: {e}", file=sys.stderr)
    
    # Write CSV
    df = pd.DataFrame(rows)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding='utf-8')
    
    print(f"\n{'='*60}")
    print(f"Generated {len(rows)} candidate rows")
    print(f"Output written to: {out_path}")
    print(f"\nNext steps:")
    print(f"1. Open {out_path} in spreadsheet editor")
    print(f"2. Review candidates and mark relevant ones (label=1)")
    print(f"3. Run: python tools/eval/gold_finalize.py --labels {out_path} --out reports/qrels_gold.tsv")
    print(f"{'='*60}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()

