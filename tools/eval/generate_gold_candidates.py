#!/usr/bin/env python3
"""
generate_gold_candidates.py - Generate Vec + BM25 runs for gold standard
========================================================================
Submits Vec-only and BM25-only experiments, waits for completion, and exports runs.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


def get_api_base():
    """Get API base URL from environment or default."""
    return os.getenv("API_BASE", "http://andy-wsl:8000")


def submit_experiment(api_base, payload):
    """Submit experiment and return job_id."""
    url = f"{api_base}/api/experiment/run"
    try:
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        return result.get("job_id")
    except Exception as e:
        print(f"ERROR: Failed to submit experiment: {e}", file=sys.stderr)
        return None


def wait_for_completion(api_base, job_id, timeout_sec=1800):
    """Wait for job completion and return status."""
    url = f"{api_base}/api/experiment/status/{job_id}"
    start_time = time.time()
    
    while time.time() - start_time < timeout_sec:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            job = data.get("job") or {}
            status = job.get("status", "")
            
            if status in ("SUCCEEDED", "FAILED"):
                return status
            
            # Print progress
            progress = job.get("progress_hint", "")
            if progress:
                print(f"  Job {job_id}: {status} - {progress}")
            
            time.sleep(3)
        except Exception as e:
            print(f"WARNING: Status check failed: {e}", file=sys.stderr)
            time.sleep(3)
    
    return "TIMEOUT"


def export_logs(api_base, job_id, out_path):
    """Export job logs to file."""
    url = f"{api_base}/api/experiment/logs/{job_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return True
    except Exception as e:
        print(f"WARNING: Failed to export logs: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate Vec + BM25 runs for gold standard")
    parser.add_argument("--sample", type=int, default=300, help="Sample size (default: 300)")
    parser.add_argument("--top-k", type=int, default=30, help="Top K (default: 30)")
    parser.add_argument("--limit", type=int, help="Limit number of candidates per query (used for gold-prepare)")
    parser.add_argument("--dataset-name", default="fiqa_50k_v1", help="Dataset name")
    parser.add_argument("--qrels-name", default="fiqa_qrels_50k_v1", help="Qrels name")
    parser.add_argument("--api-base", help="API base URL (default: from env or http://andy-wsl:8000)")
    parser.add_argument("--vec-out", default="reports/vec_runs.jsonl", help="Vector runs output")
    parser.add_argument("--bm25-out", default="reports/bm25_runs.jsonl", help="BM25 runs output")
    parser.add_argument("--out", default="reports/gold_candidates.csv", help="Output CSV for candidates (if --limit is set)")
    parser.add_argument("--skip-vec", action="store_true", help="Skip vector run if output exists")
    parser.add_argument("--skip-bm25", action="store_true", help="Skip BM25 run if output exists")
    
    args = parser.parse_args()
    
    api_base = args.api_base or get_api_base()
    
    vec_out = Path(args.vec_out)
    bm25_out = Path(args.bm25_out)
    
    vec_out.parent.mkdir(parents=True, exist_ok=True)
    bm25_out.parent.mkdir(parents=True, exist_ok=True)
    
    # Vector-only run
    if not args.skip_vec and not vec_out.exists():
        print(f"Submitting vector-only experiment...")
        vec_payload = {
            "sample": args.sample,
            "repeats": 1,
            "fast_mode": True,
            "top_k": args.top_k,
            "dataset_name": args.dataset_name,
            "qrels_name": args.qrels_name,
            "use_hybrid": False,
            "rerank": False
        }
        
        vec_job = submit_experiment(api_base, vec_payload)
        if not vec_job:
            print("ERROR: Failed to submit vector experiment", file=sys.stderr)
            sys.exit(1)
        
        print(f"Vector job submitted: {vec_job}")
        print(f"Waiting for completion...")
        
        vec_status = wait_for_completion(api_base, vec_job)
        if vec_status != "SUCCEEDED":
            print(f"ERROR: Vector job failed with status: {vec_status}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Vector job completed. Exporting logs...")
        export_logs(api_base, vec_job, vec_out)
        print(f"Vector runs exported to: {vec_out}")
    else:
        if vec_out.exists():
            print(f"Vector runs already exist: {vec_out}")
        else:
            print(f"Skipping vector run (--skip-vec)")
    
    # BM25-only run
    if not args.skip_bm25 and not bm25_out.exists():
        print(f"\nSubmitting BM25-only experiment...")
        # Note: The API might not support "mode":"bm25" directly
        # We'll try with use_hybrid=False and see if there's a way to force BM25
        bm25_payload = {
            "sample": args.sample,
            "repeats": 1,
            "fast_mode": True,
            "top_k": args.top_k,
            "dataset_name": args.dataset_name,
            "qrels_name": args.qrels_name,
            "use_hybrid": False,
            "rerank": False,
            "mode": "bm25"  # May be ignored by API, but try it
        }
        
        bm25_job = submit_experiment(api_base, bm25_payload)
        if not bm25_job:
            print("ERROR: Failed to submit BM25 experiment", file=sys.stderr)
            sys.exit(1)
        
        print(f"BM25 job submitted: {bm25_job}")
        print(f"Waiting for completion...")
        
        bm25_status = wait_for_completion(api_base, bm25_job)
        if bm25_status != "SUCCEEDED":
            print(f"ERROR: BM25 job failed with status: {bm25_status}", file=sys.stderr)
            sys.exit(1)
        
        print(f"BM25 job completed. Exporting logs...")
        export_logs(api_base, bm25_job, bm25_out)
        print(f"BM25 runs exported to: {bm25_out}")
    else:
        if bm25_out.exists():
            print(f"BM25 runs already exist: {bm25_out}")
        else:
            print(f"Skipping BM25 run (--skip-bm25)")
    
    # If --limit is set, also generate the candidates CSV directly
    if args.limit:
        print(f"\nGenerating candidates CSV with limit={args.limit} per query...")
        try:
            from tools.eval.gold_prepare import load_queries, load_run_file, merge_and_deduplicate, fetch_doc_info
            import pandas as pd
            
            # Load queries
            queries_path = f"experiments/data/fiqa/fiqa_queries_{args.dataset_name.replace('fiqa_', '').replace('_v1', '')}_v1.jsonl"
            if not Path(queries_path).exists():
                # Try alternative paths
                for alt_path in [
                    f"experiments/data/fiqa/{args.dataset_name}_queries.jsonl",
                    f"experiments/data/fiqa/{args.dataset_name.replace('_v1', '')}_queries.jsonl"
                ]:
                    if Path(alt_path).exists():
                        queries_path = alt_path
                        break
            
            if not Path(queries_path).exists():
                print(f"WARNING: Queries file not found: {queries_path}", file=sys.stderr)
                print("  Skipping direct CSV generation. Run 'make gold-prepare' manually.", file=sys.stderr)
            else:
                queries = load_queries(queries_path)
                vector_runs = load_run_file(str(vec_out)) if vec_out.exists() else {}
                bm25_runs = load_run_file(str(bm25_out)) if bm25_out.exists() else {}
                
                merged = merge_and_deduplicate(vector_runs, bm25_runs, per_query=args.limit)
                
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
                            "title": "",
                            "snippet": "",
                            "label": ""
                        })
                
                df = pd.DataFrame(rows)
                out_path = Path(args.out)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(out_path, index=False, encoding='utf-8')
                print(f"✅ Candidates CSV generated: {out_path} ({len(rows)} rows)")
        except Exception as e:
            print(f"WARNING: Failed to generate candidates CSV directly: {e}", file=sys.stderr)
            print("  Run 'make gold-prepare' manually after this completes.", file=sys.stderr)
    
    print(f"\n{'='*60}")
    print(f"✅ Candidate generation complete!")
    print(f"  Vector runs: {vec_out}")
    print(f"  BM25 runs: {bm25_out}")
    if args.limit:
        print(f"  Candidates CSV: {args.out}")
    print(f"\nNext step: Run 'make gold-prepare' to merge candidates")
    print(f"{'='*60}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()

