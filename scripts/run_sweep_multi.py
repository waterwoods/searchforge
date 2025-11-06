#!/usr/bin/env python3
"""
Multi-dataset parameter sweep runner.
Runs parameter sweeps across multiple datasets.
"""

import argparse
import subprocess
import sys
import pathlib
from dataset_registry import get_dataset_registry, validate_dataset_files

def run_sweep_for_dataset(dataset_name, trials, outdir):
    """Run parameter sweep for a single dataset."""
    registry = get_dataset_registry()
    if dataset_name not in registry:
        print(f"ERROR: Unknown dataset '{dataset_name}'")
        return False
    
    config = registry[dataset_name]
    
    # Validate files exist
    if not validate_dataset_files(dataset_name):
        print(f"ERROR: Missing required files for dataset '{dataset_name}'")
        return False
    
    # Create output directory for this dataset
    dataset_outdir = pathlib.Path(outdir) / f"sweep_{dataset_name}"
    dataset_outdir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== Running sweep for dataset: {dataset_name} ===")
    print(f"Collection: {config['collection']}")
    print(f"Config: {config['hybrid_cfg']}")
    print(f"Queries: {config['queries_file']}")
    print(f"Output: {dataset_outdir}")
    
    # Use grid from registry if available, otherwise use defaults
    if "grid" in config:
        candidate_grid = ",".join(map(str, config["grid"]["candidate_k"]))
        rerank_grid = ",".join(map(str, config["grid"]["rerank_k"]))
        print(f"Using registry grid: candidate_k={candidate_grid}, rerank_k={rerank_grid}")
    else:
        candidate_grid = "100,200,400"
        rerank_grid = "20,50,80"
        print(f"Using default grid: candidate_k={candidate_grid}, rerank_k={rerank_grid}")
    
    # Run parameter sweep using existing script
    cmd = [
        "python", "scripts/param_sweep_report.py",
        "--config", config["hybrid_cfg"],
        "--collection", config["collection"],
        "--queries", config["queries_file"],
        "--candidate-grid", candidate_grid,
        "--rerank-grid", rerank_grid,
        "--trials", str(trials),
        "--output-dir", str(dataset_outdir)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"SUCCESS: Sweep completed for {dataset_name}")
        print(f"CSV: {dataset_outdir}/sweep_metrics.csv")
        print(f"Charts: {dataset_outdir}/sweep_combined.png")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Sweep failed for {dataset_name}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run parameter sweeps across multiple datasets")
    parser.add_argument("--datasets", nargs="+", required=True, help="Dataset names to process")
    parser.add_argument("--trials", type=int, default=3, help="Number of trials per parameter combination")
    parser.add_argument("--outdir", default="reports/rerank_html", help="Output directory")
    
    args = parser.parse_args()
    
    print(f"Multi-dataset parameter sweep")
    print(f"Datasets: {args.datasets}")
    print(f"Trials: {args.trials}")
    print(f"Output dir: {args.outdir}")
    
    # Create output directory
    pathlib.Path(args.outdir).mkdir(parents=True, exist_ok=True)
    
    # Run sweep for each dataset
    results = {}
    for dataset in args.datasets:
        success = run_sweep_for_dataset(
            dataset, 
            args.trials, 
            args.outdir
        )
        results[dataset] = success
    
    # Summary
    print(f"\n=== SUMMARY ===")
    for dataset, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"{dataset}: {status}")
    
    # Exit with error if any dataset failed
    if not all(results.values()):
        sys.exit(1)

if __name__ == "__main__":
    main()
