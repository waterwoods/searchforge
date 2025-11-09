#!/usr/bin/env python3
"""
Build hard query subset from 50k dataset.

Rule A: Prefer queries that recent silver runs missed (recall@10==0)
Rule B: Fallback to longest queries (by tokens) from 50k
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import re

def load_queries(queries_path: Path) -> List[Dict[str, str]]:
    """Load queries from JSONL file."""
    queries = []
    with open(queries_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                qid = data.get("_id") or data.get("id") or data.get("query_id", "")
                text = data.get("text", "") or data.get("query", "")
                if qid and text:
                    queries.append({"query_id": qid, "text": text})
    return queries

def load_qrels(qrels_path: Path) -> Dict[str, List[str]]:
    """Load qrels from JSONL file."""
    qrels = {}
    with open(qrels_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                qid = data.get("query_id", "")
                doc_ids = data.get("relevant_doc_ids", [])
                if qid and doc_ids:
                    qrels[qid] = doc_ids
    return qrels

def load_qrels_trec(qrels_path: Path) -> Dict[str, List[str]]:
    """Load qrels from TREC format."""
    qrels = {}
    with open(qrels_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 4:
                    qid = parts[0]
                    doc_id = parts[2]
                    score = int(parts[3])
                    if score > 0:
                        if qid not in qrels:
                            qrels[qid] = []
                        qrels[qid].append(doc_id)
    return qrels

def find_missed_queries_from_runs(runs_dir: Path) -> set:
    """Find query IDs with recall@10==0 from recent runs (Rule A)."""
    missed_qids = set()
    
    # Check recent metrics.json files
    for job_dir in sorted(runs_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        metrics_file = job_dir / "metrics.json"
        if not metrics_file.exists():
            continue
        
        try:
            with open(metrics_file) as f:
                metrics = json.load(f)
            
            # Check if this run has per-query metrics
            # If not, we'll use Rule B fallback
            if "per_query_recall" in metrics:
                for qid, recall in metrics["per_query_recall"].items():
                    if recall == 0.0:
                        missed_qids.add(qid)
        except Exception as e:
            print(f"Warning: Failed to read {metrics_file}: {e}", file=sys.stderr)
    
    return missed_qids

def count_tokens(text: str) -> int:
    """Simple token counter (split on whitespace)."""
    return len(text.split())

def main():
    repo_root = Path(__file__).parent
    data_dir = repo_root / "data" / "fiqa_v1"
    queries_path = data_dir / "fiqa_50k_v1" / "queries.jsonl"
    qrels_path = data_dir / "fiqa_qrels_50k_v1.jsonl"
    
    # Try TREC format if JSONL doesn't exist
    if not qrels_path.exists():
        qrels_path = data_dir / "fiqa_qrels_50k_v1.trec"
    
    runs_dir = Path("/app/.runs") if Path("/app").exists() else repo_root / ".runs"
    
    print(f"Loading queries from: {queries_path}")
    queries = load_queries(queries_path)
    print(f"Loaded {len(queries)} queries")
    
    print(f"Loading qrels from: {qrels_path}")
    if qrels_path.suffix == ".trec":
        qrels = load_qrels_trec(qrels_path)
    else:
        qrels = load_qrels(qrels_path)
    print(f"Loaded qrels for {len(qrels)} queries")
    
    # Filter to queries with ground truth
    queries_with_gt = [q for q in queries if q["query_id"] in qrels]
    print(f"Found {len(queries_with_gt)} queries with ground truth")
    
    # Rule A: Find queries missed in recent runs
    print("\nRule A: Checking recent runs for missed queries...")
    missed_qids = find_missed_queries_from_runs(runs_dir)
    print(f"Found {len(missed_qids)} queries with recall@10==0 in recent runs")
    
    # Rule B: Fallback to longest queries
    print("\nRule B: Sorting queries by length...")
    queries_with_lengths = [(q, count_tokens(q["text"])) for q in queries_with_gt]
    queries_with_lengths.sort(key=lambda x: x[1], reverse=True)
    
    # Select hard queries: prefer Rule A, then fill with Rule B
    target_count = 150
    hard_qids = set()
    hard_queries = []
    
    # First, add missed queries (Rule A)
    rule_a_count = 0
    for qid in missed_qids:
        if len(hard_qids) >= target_count:
            break
        # Find query in our list
        for q, _ in queries_with_lengths:
            if q["query_id"] == qid and qid not in hard_qids:
                hard_queries.append(q)
                hard_qids.add(qid)
                rule_a_count += 1
                break
    
    # Fill remaining with longest queries (Rule B)
    rule_b_count = 0
    for q, length in queries_with_lengths:
        if len(hard_qids) >= target_count:
            break
        if q["query_id"] not in hard_qids:
            hard_queries.append(q)
            hard_qids.add(q["query_id"])
            rule_b_count += 1
    
    print(f"\nSelected {len(hard_queries)} hard queries:")
    print(f"  Rule A (missed): {rule_a_count}")
    print(f"  Rule B (longest): {rule_b_count}")
    
    # Save hard queries
    output_dir = repo_root / "experiments" / "data" / "fiqa"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    hard_queries_path = output_dir / "fiqa_hard_50k.jsonl"
    with open(hard_queries_path, 'w', encoding='utf-8') as f:
        for q in hard_queries:
            f.write(json.dumps({"query_id": q["query_id"], "text": q["text"]}, ensure_ascii=False) + "\n")
    print(f"\nSaved hard queries to: {hard_queries_path}")
    
    # Save filtered qrels (TSV format)
    hard_qrels_path = output_dir / "fiqa_qrels_hard_50k_v1.tsv"
    with open(hard_qrels_path, 'w', encoding='utf-8') as f:
        f.write("query_id\tdoc_id\trelevance\n")
        for qid in hard_qids:
            if qid in qrels:
                for doc_id in qrels[qid]:
                    f.write(f"{qid}\t{doc_id}\t1\n")
    print(f"Saved hard qrels to: {hard_qrels_path}")
    
    print(f"\n✅ Hard subset created: {len(hard_queries)} queries, {len(hard_qids)} with qrels")

if __name__ == "__main__":
    main()

