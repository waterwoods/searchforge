#!/usr/bin/env python3
"""
recall_eval_dedup.py - De-duplicated Recall Evaluation
=======================================================
Computes Recall@K with doc_id de-duplication before slicing top-k.
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


def load_qrels(qrels_path: str) -> Dict[str, Set[str]]:
    """Load qrels from TSV file (qid, 0, doc_id, relevance)."""
    qrels = {}
    with open(qrels_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                qid = parts[0].strip()
                doc_id = str(parts[2].strip())
                if qid not in qrels:
                    qrels[qid] = set()
                qrels[qid].add(doc_id)
    return qrels


def load_run_file(run_path: str) -> Dict[str, List[Dict]]:
    """Load run file (JSONL or TSV format)."""
    run_path_obj = Path(run_path)
    
    if run_path_obj.suffix == '.jsonl':
        # JSONL format: each line is {"query_id": "...", "results": [...]}
        runs = {}
        with open(run_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                qid = data.get("query_id") or data.get("qid", "")
                results = data.get("results", [])
                runs[qid] = results
        return runs
    
    elif run_path_obj.suffix == '.tsv':
        # TSV format: query_id, doc_id, rank, score
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


def deduplicate_results(results: List[Dict]) -> List[Dict]:
    """De-duplicate results by doc_id, keeping highest score."""
    seen = {}
    for result in results:
        doc_id = str(result.get("doc_id", ""))
        score = result.get("score", 0.0)
        if doc_id not in seen or seen[doc_id]["score"] < score:
            seen[doc_id] = result
    # Return sorted by score (descending)
    return sorted(seen.values(), key=lambda x: x.get("score", 0.0), reverse=True)


def calculate_recall_at_k(retrieved_doc_ids: List[str], relevant_doc_ids: Set[str], k: int) -> float:
    """Calculate Recall@K."""
    if not relevant_doc_ids:
        return 0.0
    
    retrieved_set = {str(doc_id) for doc_id in retrieved_doc_ids[:k]}
    hits = len(retrieved_set & relevant_doc_ids)
    
    return hits / min(k, len(relevant_doc_ids))


def main():
    parser = argparse.ArgumentParser(description="Compute Recall@K with de-duplication")
    parser.add_argument("--run", required=True, help="Run file (JSONL or TSV)")
    parser.add_argument("--qrels", required=True, help="Qrels TSV file")
    parser.add_argument("--k", type=int, default=10, help="K value for Recall@K (default: 10)")
    parser.add_argument("--out", default="reports/recall_at_k.json", help="Output JSON report path")
    
    args = parser.parse_args()
    
    # Load qrels
    print(f"Loading qrels from {args.qrels}...")
    qrels = load_qrels(args.qrels)
    print(f"Loaded {len(qrels)} queries")
    
    # Load run file
    print(f"Loading run file from {args.run}...")
    runs = load_run_file(args.run)
    print(f"Loaded {len(runs)} query runs")
    
    # Calculate Recall@K for each query
    recalls = []
    query_stats = []
    
    for qid, relevant_doc_ids in qrels.items():
        if qid not in runs:
            continue
        
        results = runs[qid]
        
        # De-duplicate
        dedup_results = deduplicate_results(results)
        
        # Extract doc_ids
        retrieved_doc_ids = [str(r.get("doc_id", "")) for r in dedup_results]
        
        # Calculate Recall@K
        recall = calculate_recall_at_k(retrieved_doc_ids, relevant_doc_ids, args.k)
        recalls.append(recall)
        
        query_stats.append({
            "query_id": qid,
            "recall_at_k": recall,
            "retrieved_count": len(retrieved_doc_ids),
            "relevant_count": len(relevant_doc_ids),
            "hits": len(set(retrieved_doc_ids[:args.k]) & relevant_doc_ids)
        })
    
    # Aggregate metrics
    mean_recall = sum(recalls) / len(recalls) if recalls else 0.0
    
    report = {
        "run_file": args.run,
        "qrels_file": args.qrels,
        "k": args.k,
        "metrics": {
            "mean_recall_at_k": round(mean_recall, 4),
            "num_queries": len(recalls),
            "min_recall": round(min(recalls), 4) if recalls else 0.0,
            "max_recall": round(max(recalls), 4) if recalls else 0.0
        },
        "query_stats": query_stats[:100]  # Sample first 100
    }
    
    # Write report
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Mean Recall@{args.k}: {mean_recall:.4f}")
    print(f"Queries evaluated: {len(recalls)}")
    print(f"Report written to: {out_path}")
    print(f"{'='*60}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()

