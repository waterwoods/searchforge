import csv, sys, json, pathlib, yaml, argparse
"""
Usage: 
  python scripts/select_golden.py <csv_path> > /dev/stdout
  python scripts/select_golden.py --csv <csv_path> --out <output_yaml>
CSV 需包含列：candidate_k,rerank_k,p95_ms,recall_at10（以及可选 top1_rate）
选择规则：先最大 recall_at10；若并列，选 p95_ms 最小；若仍并列，candidate_k 最小，再 rerank_k 最小。
输出 JSON：{"candidate_k":..., "rerank_k":..., "recall":..., "p95":...}
"""
def parse_float(x):
    try: return float(x)
    except: return float("inf")
def parse_int(x):
    try: return int(float(x))
    except: return 0
def create_golden_config(candidate_k, rerank_k, dataset_name):
    """Create golden configuration YAML."""
    config = {
        "retriever": {
            "type": "vector",
            "top_k": candidate_k
        },
        "reranker": {
            "type": "cross_encoder",
            "model": "cross-encoder/ms-marco-MiniLM-L-2-v2",
            "top_k": rerank_k,
            "batch_size": 32,
            "cache_size": 2000
        }
    }
    return config

def main():
    parser = argparse.ArgumentParser(description="Select golden parameters from sweep results")
    parser.add_argument("--csv", help="CSV file path")
    parser.add_argument("--out", help="Output YAML file path")
    
    args = parser.parse_args()
    
    # Support legacy single argument usage
    if not args.csv and len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        csv_path = pathlib.Path(sys.argv[1])
    elif args.csv:
        csv_path = pathlib.Path(args.csv)
    else:
        print("ERROR: No CSV file specified")
        sys.exit(1)
    
    rows = []
    with csv_path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            ck = parse_int(row.get("candidate_k", 0))
            rk = parse_int(row.get("rerank_k", 0))
            rec = parse_float(row.get("recall_at10", 0))
            p95 = parse_float(row.get("p95_ms", 1e18))
            rows.append((rec, -p95, -ck, -rk, ck, rk, p95))  # 排序键
    if not rows:
        print(json.dumps({"error":"empty_csv"}))
        return
    rows.sort(reverse=True)
    best = rows[0]
    recall, _, _, _, ck, rk, p95 = best
    
    result = {"candidate_k": ck, "rerank_k": rk, "recall": recall, "p95": p95}
    
    # Print JSON result
    print(json.dumps(result))
    
    # Generate golden config if output path specified
    if args.out:
        output_path = pathlib.Path(args.out)
        dataset_name = output_path.stem.replace("demo_", "").replace("_golden", "")
        
        config = create_golden_config(ck, rk, dataset_name)
        
        # Add collection if we can infer it from the dataset name
        if "scifact" in dataset_name:
            config["retriever"]["collection"] = "beir_scifact_full_ta"
        elif "fiqa" in dataset_name:
            config["retriever"]["collection"] = "beir_fiqa_small"
        
        output_path.write_text(yaml.safe_dump(config, sort_keys=False))
        print(f"Generated golden config: {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
