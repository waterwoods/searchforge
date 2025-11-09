#!/usr/bin/env python3
"""
Master Script for Chunking Strategy Comparison

This script orchestrates the full pipeline:
1. Build three chunking collections (Para, Sent, Window)
2. Write collection metadata
3. Run health checks (qrels_doctor, embed_doctor)
4. Run experiments (Top-K x MMR grid)
5. Analyze results and generate reports
6. Generate visualizations

Usage:
    python experiments/run_chunk_comparison.py --api-url http://andy-wsl:8000
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def run_command(cmd: list, step_name: str, check: bool = True) -> int:
    """
    Run a command and log output.
    
    Returns:
        Return code
    """
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            check=check,
            text=True
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ {step_name} completed successfully ({elapsed:.1f}s)")
        else:
            print(f"\n⚠️  {step_name} exited with code {result.returncode} ({elapsed:.1f}s)")
        
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"\n❌ {step_name} failed ({elapsed:.1f}s)")
        print(f"Error: {e}")
        return e.returncode
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ {step_name} failed ({elapsed:.1f}s)")
        print(f"Error: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Run complete chunking strategy comparison"
    )
    parser.add_argument(
        '--api-url',
        type=str,
        required=True,
        help='API base URL (e.g., http://andy-wsl:8000)'
    )
    parser.add_argument(
        '--corpus-path',
        type=str,
        default='data/fiqa_v1/corpus_50k_v1.jsonl',
        help='Path to corpus JSONL file'
    )
    parser.add_argument(
        '--qrels-path',
        type=str,
        default='data/fiqa_v1/fiqa_qrels_50k_v1.jsonl',
        help='Path to qrels file'
    )
    parser.add_argument(
        '--qdrant-host',
        type=str,
        default='localhost',
        help='Qdrant host'
    )
    parser.add_argument(
        '--qdrant-port',
        type=int,
        default=6333,
        help='Qdrant port'
    )
    parser.add_argument(
        '--sample-queries',
        type=int,
        default=None,
        help='Sample N queries for faster testing'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip collection building (use existing collections)'
    )
    parser.add_argument(
        '--skip-health',
        action='store_true',
        help='Skip health checks'
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate collections if they exist'
    )
    
    args = parser.parse_args()
    
    repo_root = find_repo_root()
    start_time = time.time()
    
    print(f"""
{'#'*60}
# CHUNKING STRATEGY COMPARISON PIPELINE
{'#'*60}

Configuration:
  API URL: {args.api_url}
  Corpus: {args.corpus_path}
  Qrels: {args.qrels_path}
  Qdrant: {args.qdrant_host}:{args.qdrant_port}
  Sample queries: {args.sample_queries or 'all'}
  
Steps:
  1. Build collections (Para, Sent, Window)
  2. Health checks (qrels_doctor, embed_doctor)
  3. Run experiments (Top-K x MMR grid)
  4. Analyze results
  5. Generate reports

{'#'*60}
    """)
    
    # Step 1: Build collections
    if not args.skip_build:
        cmd = [
            'python', 'experiments/build_chunk_collections.py',
            '--corpus-path', args.corpus_path,
            '--qdrant-host', args.qdrant_host,
            '--qdrant-port', str(args.qdrant_port)
        ]
        
        if args.recreate:
            cmd.append('--recreate')
        
        returncode = run_command(cmd, "Build Collections")
        if returncode != 0:
            print("\n❌ Collection building failed. Aborting.")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping collection building (--skip-build)")
    
    # Step 2: Health checks
    if not args.skip_health:
        cmd = [
            'python', 'experiments/run_chunk_health_checks.py',
            '--qdrant-host', args.qdrant_host,
            '--qdrant-port', str(args.qdrant_port),
            '--qrels-path', args.qrels_path,
            '--api-url', args.api_url
        ]
        
        returncode = run_command(cmd, "Health Checks", check=False)
        if returncode != 0:
            print("\n⚠️  Health checks failed, but continuing...")
            print("Please review health check reports in reports/chunk_health/")
        else:
            print("\n✅ All health checks passed!")
    else:
        print("\n⏭️  Skipping health checks (--skip-health)")
    
    # Step 3: Run experiments
    cmd = [
        'python', 'experiments/run_chunk_experiments.py',
        '--api-url', args.api_url
    ]
    
    if args.sample_queries:
        cmd.extend(['--sample-queries', str(args.sample_queries)])
    
    returncode = run_command(cmd, "Run Experiments")
    if returncode != 0:
        print("\n❌ Experiments failed. Aborting.")
        sys.exit(1)
    
    # Find the results file (most recent chunk_experiments_*.json)
    reports_dir = repo_root / 'reports'
    results_files = sorted(reports_dir.glob('chunk_experiments_*.json'))
    
    if not results_files:
        print("\n❌ No experiment results found. Aborting.")
        sys.exit(1)
    
    latest_results = results_files[-1]
    print(f"\nUsing results file: {latest_results}")
    
    # Step 4: Analyze results
    cmd = [
        'python', 'experiments/analyze_chunk_results.py',
        '--input', str(latest_results)
    ]
    
    returncode = run_command(cmd, "Analyze Results")
    if returncode != 0:
        print("\n❌ Analysis failed. Aborting.")
        sys.exit(1)
    
    # Final summary
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"\nGenerated artifacts:")
    print(f"  - Collections: fiqa_para_50k, fiqa_sent_50k, fiqa_win256_o64_50k")
    print(f"  - Metadata: configs/collection_tags/*.json")
    print(f"  - Health checks: reports/chunk_health/")
    print(f"  - Experiment results: {latest_results}")
    print(f"  - Winners: reports/winners_chunk.json")
    print(f"  - Charts: reports/chunk_charts/")
    print(f"  - Recommendations: reports/chunk_recommendations.txt")
    print(f"\n✅ All steps completed successfully!")
    print(f"\nNext steps:")
    print(f"  - Review winners: cat reports/winners_chunk.json")
    print(f"  - Review recommendations: cat reports/chunk_recommendations.txt")
    print(f"  - View charts: open reports/chunk_charts/")


if __name__ == '__main__':
    main()

