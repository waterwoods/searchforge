#!/usr/bin/env python3
"""
Generate DATA TRIPLETS & ALIGNMENT AUDIT table for Experiment Orchestrator.

This script:
- Enumerates all allowed datasets/collections and their bound queries_path/qrels_path
- Shows label_type based on qrels filename
- Runs ID alignment audit per dataset
- Runs spot-check (N=10) per dataset
- Pulls latest winners/run metadata
- Emits Markdown table and CSV
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Install with: pip install pyyaml")
    sys.exit(1)


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load orchestrator config.yaml."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_policies(policies_path: Path) -> Dict[str, Any]:
    """Load policies.json."""
    with open(policies_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_winners(winners_path: Path) -> Optional[Dict[str, Any]]:
    """Load winners.final.json if it exists."""
    if not winners_path.exists():
        return None
    try:
        with open(winners_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: Failed to load winners.final.json: {e}")
        return None


def determine_label_type(qrels_path: str) -> str:
    """Determine label_type based on qrels filename."""
    qrels_lower = qrels_path.lower()
    if "hard" in qrels_lower:
        return "gold"
    elif "silver" in qrels_lower:
        return "silver"
    else:
        return "unknown"


def run_id_alignment_audit(
    collection: str,
    qrels_path: str,
    host: str,
    json_out_path: Path
) -> Dict[str, Any]:
    """Run ID alignment audit and return parsed results."""
    # Note: id_alignment_auditor connects to Qdrant (port 6333), not orchestrator
    # We'll use Qdrant host from environment or default
    qdrant_host = os.environ.get("QDRANT_URL", "http://localhost:6333")
    
    cmd = [
        sys.executable, "-m", "tools.eval.id_alignment_auditor",
        "--collection", collection,
        "--qrels", qrels_path,
        "--host", qdrant_host,
        "--json",
        "--json-out", str(json_out_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )
        
        if result.returncode != 0 and result.returncode != 1:
            # Exit code 1 is OK (mismatch found), but other errors are not
            return {
                "checked": 0,
                "found": 0,
                "mismatch": 0,
                "mismatch_rate": 1.0,
                "error": f"Command failed: {result.stderr[:200]}"
            }
        
        # Read JSON from file
        if json_out_path.exists():
            try:
                with open(json_out_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {
                    "checked": data.get("checked", 0),
                    "found": data.get("found", 0),
                    "mismatch": data.get("mismatch", 0),
                    "mismatch_rate": data.get("mismatch_rate", 1.0),
                    "error": data.get("error")
                }
            except json.JSONDecodeError as e:
                return {
                    "checked": 0,
                    "found": 0,
                    "mismatch": 0,
                    "mismatch_rate": 1.0,
                    "error": f"Failed to parse JSON: {e}"
                }
        else:
            # Fallback: try to parse from stdout
            try:
                data = json.loads(result.stdout)
                return {
                    "checked": data.get("checked", 0),
                    "found": data.get("found", 0),
                    "mismatch": data.get("mismatch", 0),
                    "mismatch_rate": data.get("mismatch_rate", 1.0),
                    "error": data.get("error")
                }
            except json.JSONDecodeError:
                return {
                    "checked": 0,
                    "found": 0,
                    "mismatch": 0,
                    "mismatch_rate": 1.0,
                    "error": "No JSON output found"
                }
    except subprocess.TimeoutExpired:
        return {
            "checked": 0,
            "found": 0,
            "mismatch": 0,
            "mismatch_rate": 1.0,
            "error": "Command timed out"
        }
    except Exception as e:
        return {
            "checked": 0,
            "found": 0,
            "mismatch": 0,
            "mismatch_rate": 1.0,
            "error": str(e)
        }


def run_spot_check(
    collection: str,
    queries_path: str,
    qrels_path: str,
    host: str,
    top_k: int,
    n: int,
    json_out_path: Path
) -> Dict[str, Any]:
    """Run spot-check and return parsed results."""
    cmd = [
        sys.executable, "-m", "tools.eval.spot_check",
        "--collection", collection,
        "--queries", queries_path,
        "--qrels", qrels_path,
        "--host", host,
        "--n", str(n),
        "--top_k", str(top_k),
        "--json-out", str(json_out_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )
        
        # Read JSON from file
        if json_out_path.exists():
            try:
                with open(json_out_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                summary = data.get("summary", {})
                return {
                    "avg_overlap": summary.get("avg_overlap", 0.0),
                    "min_overlap": summary.get("min_overlap", 0),
                    "max_overlap": summary.get("max_overlap", 0),
                    "all_ge_1": summary.get("all_ge_1", False),
                    "error": None
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to parse from stdout
        output_lines = result.stdout.split('\n')
        json_start = None
        for i, line in enumerate(output_lines):
            if line.strip().startswith('{') or '"summary"' in line:
                json_start = i
                break
        
        if json_start is not None:
            json_text = '\n'.join(output_lines[json_start:])
            try:
                data = json.loads(json_text)
                summary = data.get("summary", {})
                return {
                    "avg_overlap": summary.get("avg_overlap", 0.0),
                    "min_overlap": summary.get("min_overlap", 0),
                    "max_overlap": summary.get("max_overlap", 0),
                    "all_ge_1": summary.get("all_ge_1", False),
                    "error": None
                }
            except json.JSONDecodeError:
                pass
        
        # Last resort: try to extract from text output
        summary_line = None
        for line in output_lines:
            if "Summary:" in line:
                summary_line = line
                break
        
        if summary_line:
            import re
            avg_match = re.search(r'avg_overlap=([\d.]+)', summary_line)
            min_match = re.search(r'min=(\d+)', summary_line)
            max_match = re.search(r'max=(\d+)', summary_line)
            all_ge_1_match = re.search(r'all_ge_1=(\w+)', summary_line)
            
            return {
                "avg_overlap": float(avg_match.group(1)) if avg_match else 0.0,
                "min_overlap": int(min_match.group(1)) if min_match else 0,
                "max_overlap": int(max_match.group(1)) if max_match else 0,
                "all_ge_1": all_ge_1_match.group(1) == "True" if all_ge_1_match else False,
                "error": None
            }
        
        return {
            "avg_overlap": 0.0,
            "min_overlap": 0,
            "max_overlap": 0,
            "all_ge_1": False,
            "error": f"Failed to parse output: {result.stderr[:200] if result.stderr else 'No output'}"
        }
    except subprocess.TimeoutExpired:
        return {
            "avg_overlap": 0.0,
            "min_overlap": 0,
            "max_overlap": 0,
            "all_ge_1": False,
            "error": "Command timed out"
        }
    except Exception as e:
        return {
            "avg_overlap": 0.0,
            "min_overlap": 0,
            "max_overlap": 0,
            "all_ge_1": False,
            "error": str(e)
        }


def find_latest_winner(
    winners: Optional[Dict[str, Any]],
    policies: Dict[str, Any],
    dataset: str
) -> Dict[str, Any]:
    """Find latest winner entry for a dataset."""
    result = {
        "last_used_run_id": None,
        "last_recall_at_10": None,
        "last_p95_ms": None,
        "last_sla_verdict": None,
        "id_normalization": None
    }
    
    if not winners:
        return result
    
    # Try to find entry in winners.final.json
    # Structure might vary, so we'll try multiple patterns
    winner_entry = None
    
    # Pattern 1: winners is a dict with "winners" key
    if isinstance(winners, dict):
        winners_data = winners.get("winners", {})
        if isinstance(winners_data, dict):
            # Check each winner category
            for category, winner in winners_data.items():
                if isinstance(winner, dict):
                    winner_dataset = winner.get("dataset_name") or winner.get("dataset")
                    if winner_dataset == dataset:
                        winner_entry = winner
                        break
        
        # Pattern 2: Check "all" entries
        if not winner_entry:
            all_entries = winners.get("all", [])
            if isinstance(all_entries, list):
                # Find latest entry for this dataset
                matching = [e for e in all_entries if (e.get("dataset_name") or e.get("dataset")) == dataset]
                if matching:
                    # Sort by some timestamp or use last one
                    winner_entry = matching[-1]
    
    if winner_entry:
        result["last_used_run_id"] = winner_entry.get("job_id") or winner_entry.get("run_id") or winner_entry.get("id")
        
        # Extract metrics
        metrics = winner_entry.get("metrics", {})
        if isinstance(metrics, dict):
            result["last_recall_at_10"] = metrics.get("recall_at_10")
            result["last_p95_ms"] = metrics.get("p95_ms")
        else:
            result["last_recall_at_10"] = winner_entry.get("recall_at_10")
            result["last_p95_ms"] = winner_entry.get("p95_ms")
        
        result["last_sla_verdict"] = winner_entry.get("sla_verdict") or winner_entry.get("sla_status")
        result["id_normalization"] = winner_entry.get("id_normalization")
    
    # Also check policies for dataset mapping
    policies_data = policies.get("policies", {})
    for policy_name, policy in policies_data.items():
        if policy.get("dataset") == dataset:
            # This policy uses this dataset
            result["id_normalization"] = policy.get("id_normalization")
            break
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Generate DATA TRIPLETS & ALIGNMENT AUDIT table")
    parser.add_argument("--config", type=str, default="agents/orchestrator/config.yaml",
                       help="Path to orchestrator config.yaml")
    parser.add_argument("--policies", type=str, default="configs/policies.json",
                       help="Path to policies.json")
    parser.add_argument("--winners", type=str, default="reports/winners.final.json",
                       help="Path to winners.final.json")
    parser.add_argument("--orch-base", type=str, default=None,
                       help="Orchestrator base URL (default: from ORCH_BASE env or http://localhost:8000)")
    parser.add_argument("--top-k", type=int, default=None,
                       help="Top-K for spot-check (default: from config.run.default_top_k or 10)")
    parser.add_argument("--n", type=int, default=10,
                       help="Number of queries for spot-check (default: 10)")
    
    args = parser.parse_args()
    
    # Resolve paths
    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / args.config
    policies_path = repo_root / args.policies
    winners_path = repo_root / args.winners
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Load configs
    print("Loading configuration files...")
    config = load_config(config_path)
    policies = load_policies(policies_path)
    winners = load_winners(winners_path)
    
    # Get orchestrator base URL
    orch_base = args.orch_base or os.environ.get("ORCH_BASE", "http://localhost:8000")
    
    # Get top_k
    top_k = args.top_k or config.get("run", {}).get("default_top_k") or 10
    
    # Get datasets
    datasets_whitelist = config.get("datasets", {}).get("whitelist", [])
    datasets_disabled = config.get("datasets", {}).get("disabled", [])
    targets = [d for d in datasets_whitelist if d not in datasets_disabled]
    
    print(f"Found {len(targets)} target datasets: {', '.join(targets)}")
    
    # Get mappings
    qrels_map = config.get("datasets", {}).get("qrels_map", {})
    queries_map = config.get("datasets", {}).get("queries_map", {})
    
    # Process each dataset
    table_rows = []
    
    for dataset in targets:
        print(f"\n{'='*80}")
        print(f"Processing dataset: {dataset}")
        print(f"{'='*80}")
        
        collection = dataset
        queries_path = queries_map.get(dataset)
        qrels_path = qrels_map.get(dataset)
        
        if not queries_path or not qrels_path:
            print(f"WARNING: Missing queries_path or qrels_path for {dataset}")
            table_rows.append({
                "dataset": dataset,
                "collection": collection,
                "queries_path": queries_path or "MISSING",
                "qrels_path": qrels_path or "MISSING",
                "label_type": "unknown",
                "id_normalization": None,
                "checked": 0,
                "found": 0,
                "mismatch": 0,
                "mismatch_rate": 1.0,
                "avg_overlap": 0.0,
                "min_overlap": 0,
                "max_overlap": 0,
                "all_ge_1": False,
                "last_used_run_id": None,
                "last_recall_at_10": None,
                "last_p95_ms": None,
                "last_sla_verdict": None
            })
            continue
        
        # Resolve paths relative to repo root
        queries_path_full = repo_root / queries_path
        qrels_path_full = repo_root / qrels_path
        
        if not queries_path_full.exists():
            print(f"WARNING: Queries file not found: {queries_path_full}")
        if not qrels_path_full.exists():
            print(f"WARNING: Qrels file not found: {qrels_path_full}")
        
        # Determine label_type
        label_type = determine_label_type(qrels_path)
        
        # Run ID alignment audit
        print(f"Running ID alignment audit...")
        align_json_path = Path(f"/tmp/_align_{dataset}.json")
        align_result = run_id_alignment_audit(
            collection=collection,
            qrels_path=str(qrels_path_full),
            host=orch_base,
            json_out_path=align_json_path
        )
        
        if align_result.get("error"):
            print(f"  ERROR: {align_result['error']}")
        else:
            print(f"  checked={align_result['checked']}, found={align_result['found']}, "
                  f"mismatch={align_result['mismatch']}, rate={align_result['mismatch_rate']:.4f}")
        
        # Run spot-check
        print(f"Running spot-check (N={args.n}, top_k={top_k})...")
        spot_json_path = Path(f"/tmp/_spot_{dataset}.json")
        spot_result = run_spot_check(
            collection=collection,
            queries_path=str(queries_path_full),
            qrels_path=str(qrels_path_full),
            host=orch_base,
            top_k=top_k,
            n=args.n,
            json_out_path=spot_json_path
        )
        
        if spot_result.get("error"):
            print(f"  ERROR: {spot_result['error']}")
        else:
            print(f"  avg_overlap={spot_result['avg_overlap']:.2f}, "
                  f"min={spot_result['min_overlap']}, max={spot_result['max_overlap']}, "
                  f"all_ge_1={spot_result['all_ge_1']}")
        
        # Find latest winner
        winner_info = find_latest_winner(winners, policies, dataset)
        
        # Build row
        table_rows.append({
            "dataset": dataset,
            "collection": collection,
            "queries_path": queries_path,
            "qrels_path": qrels_path,
            "label_type": label_type,
            "id_normalization": winner_info["id_normalization"],
            "checked": align_result.get("checked", 0),
            "found": align_result.get("found", 0),
            "mismatch": align_result.get("mismatch", 0),
            "mismatch_rate": align_result.get("mismatch_rate", 0.0),
            "avg_overlap": spot_result.get("avg_overlap", 0.0),
            "min_overlap": spot_result.get("min_overlap", 0),
            "max_overlap": spot_result.get("max_overlap", 0),
            "all_ge_1": spot_result.get("all_ge_1", False),
            "last_used_run_id": winner_info["last_used_run_id"],
            "last_recall_at_10": winner_info["last_recall_at_10"],
            "last_p95_ms": winner_info["last_p95_ms"],
            "last_sla_verdict": winner_info["last_sla_verdict"]
        })
    
    # Generate Markdown table
    md_path = reports_dir / "DATA_TRIPLETS_AUDIT.md"
    csv_path = reports_dir / "DATA_TRIPLETS_AUDIT.csv"
    
    print(f"\n{'='*80}")
    print("Generating reports...")
    print(f"{'='*80}")
    
    # Write Markdown
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# DATA TRIPLETS & ALIGNMENT AUDIT\n\n")
        f.write("This report enumerates all allowed datasets/collections and their bound queries_path/qrels_path, ")
        f.write("shows label_type, runs ID alignment audit, spot-checks, and pulls latest winners metadata.\n\n")
        
        f.write("## Summary Table\n\n")
        f.write("| dataset | collection | queries_path | qrels_path | label_type | id_normalization | ")
        f.write("checked | found | mismatch | mismatch_rate | avg_overlap | min_overlap | max_overlap | ")
        f.write("all_ge_1 | last_used_run_id | last_recall_at_10 | last_p95_ms | last_sla_verdict |\n")
        f.write("|---|---|---|---|---|---|")
        f.write(":---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        
        for row in table_rows:
            f.write(f"| {row['dataset']} | {row['collection']} | {row['queries_path']} | {row['qrels_path']} | ")
            f.write(f"{row['label_type']} | {row['id_normalization'] or 'N/A'} | ")
            f.write(f"{row['checked']} | {row['found']} | {row['mismatch']} | {row['mismatch_rate']:.4f} | ")
            f.write(f"{row['avg_overlap']:.2f} | {row['min_overlap']} | {row['max_overlap']} | ")
            f.write(f"{'✓' if row['all_ge_1'] else '✗'} | ")
            f.write(f"{row['last_used_run_id'] or 'N/A'} | ")
            recall_str = f"{row['last_recall_at_10']:.4f}" if row['last_recall_at_10'] is not None else "N/A"
            f.write(f"{recall_str} | ")
            p95_str = f"{row['last_p95_ms']:.1f}" if row['last_p95_ms'] is not None else "N/A"
            f.write(f"{p95_str} | ")
            f.write(f"{row['last_sla_verdict'] or 'N/A'} |\n")
        
        # Add Fix Hints section if any mismatch_rate > 0
        failing_datasets = [row for row in table_rows if row['mismatch_rate'] > 0]
        if failing_datasets:
            f.write("\n## Fix Hints\n\n")
            f.write("The following datasets have mismatch_rate > 0:\n\n")
            for row in failing_datasets:
                f.write(f"- **{row['dataset']}**: qrels doc_id != collection payload.doc_id — ")
                f.write(f"fix by (a) reload collection with numeric doc_id, or (b) switch qrels to *_hard_50k_v1.tsv, ")
                f.write(f"or (c) update qrels_map to the matching file\n")
    
    # Write CSV
    import csv as csv_module
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv_module.writer(f)
        writer.writerow([
            "dataset", "collection", "queries_path", "qrels_path", "label_type", "id_normalization",
            "checked", "found", "mismatch", "mismatch_rate", "avg_overlap", "min_overlap", "max_overlap",
            "all_ge_1", "last_used_run_id", "last_recall_at_10", "last_p95_ms", "last_sla_verdict"
        ])
        
        for row in table_rows:
            writer.writerow([
                row['dataset'],
                row['collection'],
                row['queries_path'],
                row['qrels_path'],
                row['label_type'],
                row['id_normalization'] or '',
                row['checked'],
                row['found'],
                row['mismatch'],
                f"{row['mismatch_rate']:.4f}",
                f"{row['avg_overlap']:.2f}",
                row['min_overlap'],
                row['max_overlap'],
                'True' if row['all_ge_1'] else 'False',
                row['last_used_run_id'] or '',
                f"{row['last_recall_at_10']:.4f}" if row['last_recall_at_10'] is not None else '',
                f"{row['last_p95_ms']:.1f}" if row['last_p95_ms'] is not None else '',
                row['last_sla_verdict'] or ''
            ])
    
    # Print verification block
    print(f"\n{'='*80}")
    print("VERIFICATION - First 5 rows:")
    print(f"{'='*80}")
    for i, row in enumerate(table_rows[:5]):
        print(f"\nRow {i+1}:")
        print(f"  dataset: {row['dataset']}")
        print(f"  collection: {row['collection']}")
        print(f"  queries_path: {row['queries_path']}")
        print(f"  qrels_path: {row['qrels_path']}")
        print(f"  label_type: {row['label_type']}")
        print(f"  mismatch_rate: {row['mismatch_rate']:.4f}")
        print(f"  avg_overlap: {row['avg_overlap']:.2f}")
    
    print(f"\n{'='*80}")
    print("ARTIFACTS:")
    print(f"{'='*80}")
    print(f"Markdown: {md_path.absolute()}")
    print(f"CSV: {csv_path.absolute()}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

