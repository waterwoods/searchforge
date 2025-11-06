#!/usr/bin/env python3
"""
gold_finalize.py - Generate Qrels from Labeled CSV
==================================================
Converts labeled CSV (with label=1 for relevant) to qrels TSV format.
"""
import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate qrels_gold.tsv from labeled CSV")
    parser.add_argument("--labels", required=True, help="Labeled CSV file (with label column)")
    parser.add_argument("--out", default="reports/qrels_gold.tsv", help="Output qrels TSV path")
    parser.add_argument("--label-col", default="label", help="Label column name (default: label)")
    parser.add_argument("--qid-col", default="qid", help="Query ID column name (default: qid)")
    parser.add_argument("--docid-col", default="doc_id", help="Document ID column name (default: doc_id)")
    
    args = parser.parse_args()
    
    # Load CSV
    if not Path(args.labels).exists():
        print(f"ERROR: Labels file not found: {args.labels}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading labels from {args.labels}...")
    df = pd.read_csv(args.labels)
    
    # Check required columns
    required_cols = [args.qid_col, args.docid_col, args.label_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing columns: {missing_cols}", file=sys.stderr)
        print(f"Available columns: {list(df.columns)}", file=sys.stderr)
        sys.exit(1)
    
    # Filter to relevant (label=1)
    relevant_df = df[df[args.label_col] == 1].copy()
    print(f"Found {len(relevant_df)} relevant judgments")
    
    if len(relevant_df) == 0:
        print("WARNING: No relevant judgments found (label=1). Output will be empty.", file=sys.stderr)
    
    # Generate qrels TSV format: qid \t 0 \t doc_id \t 1
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        for _, row in relevant_df.iterrows():
            qid = str(row[args.qid_col]).strip()
            doc_id = str(row[args.docid_col]).strip()
            # Qrels format: qid \t 0 \t doc_id \t relevance_score
            f.write(f"{qid}\t0\t{doc_id}\t1\n")
    
    print(f"\n{'='*60}")
    print(f"Generated qrels with {len(relevant_df)} judgments")
    print(f"Output written to: {out_path}")
    print(f"\nQrels format: qid \\t 0 \\t doc_id \\t 1")
    print(f"{'='*60}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()

