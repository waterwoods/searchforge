#!/usr/bin/env python3
"""
update_presets_gold.py - Update presets with gold qrels
=======================================================
Adds gold qrels mappings to presets_v10.json and creates *-gold preset aliases.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Update presets with gold qrels")
    parser.add_argument("--presets-file", default="configs/presets_v10.json", help="Presets file path")
    parser.add_argument("--gold-qrels-name", default="fiqa_qrels_50k_v1_gold", help="Gold qrels name")
    parser.add_argument("--dataset-name", default="fiqa_50k_v1", help="Dataset name")
    parser.add_argument("--collection", default="fiqa_50k_v1", help="Collection name")
    parser.add_argument("--out", help="Output file (default: overwrite input)")
    
    args = parser.parse_args()
    
    presets_path = Path(args.presets_file)
    if not presets_path.exists():
        print(f"ERROR: Presets file not found: {presets_path}", file=sys.stderr)
        sys.exit(1)
    
    # Load presets
    with open(presets_path, 'r', encoding='utf-8') as f:
        presets_data = json.load(f)
    
    presets = presets_data.get("presets", [])
    
    # Find presets matching the dataset
    updated = False
    for preset in presets:
        if preset.get("dataset_name") == args.dataset_name:
            # Update qrels_name to gold version
            original_qrels = preset.get("qrels_name", "")
            if original_qrels and not original_qrels.endswith("_gold"):
                # Create a copy with gold qrels
                gold_preset = preset.copy()
                gold_preset["qrels_name"] = args.gold_qrels_name
                # Update name to indicate it's gold
                original_name = preset.get("name", "")
                if original_name and not original_name.endswith("-gold"):
                    gold_preset["name"] = f"{original_name} (Gold)"
                presets.append(gold_preset)
                updated = True
                print(f"Added gold preset: {gold_preset['name']} (qrels: {args.gold_qrels_name})")
    
    # Also add a dedicated gold preset if not found
    has_dedicated_gold = any(
        p.get("qrels_name") == args.gold_qrels_name 
        for p in presets
    )
    
    if not has_dedicated_gold:
        # Create a new gold preset
        gold_preset = {
            "name": "FIQA Fast - Baseline (50k Gold)",
            "dataset_name": args.dataset_name,
            "qrels_name": args.gold_qrels_name,
            "collection": args.collection,
            "top_k": 40,
            "mmr": False,
            "rerank": False
        }
        presets.append(gold_preset)
        updated = True
        print(f"Added dedicated gold preset: {gold_preset['name']}")
    
    if not updated:
        print(f"WARNING: No presets updated for dataset {args.dataset_name}", file=sys.stderr)
    
    # Update presets data
    presets_data["presets"] = presets
    
    # Write output
    out_path = Path(args.out) if args.out else presets_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(presets_data, f, indent=4, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Updated presets written to: {out_path}")
    print(f"Gold qrels name: {args.gold_qrels_name}")
    print(f"Total presets: {len(presets)}")
    print(f"{'='*60}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()

