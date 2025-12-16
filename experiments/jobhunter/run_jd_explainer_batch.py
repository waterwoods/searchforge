#!/usr/bin/env python3
"""
run_jd_explainer_batch.py - Run JD explainer on multiple jobs
=============================================================

This script runs the JD explainer CLI on a list of job IDs and saves
the results to individual markdown files.

Usage:
    python3 experiments/jobhunter/run_jd_explainer_batch.py \
        --scored-file data/jobhunter/scored/jobs_scored_llm_core_latest.json \
        --job-ids 4985877008 4974302008 4946314008 4952079008 4949336008 \
        --output-dir reports/jobhunter
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def run_jd_explainer(
    scored_file: str,
    job_id: str,
    output_file: Path,
    use_default_profile: bool = True,
) -> bool:
    """
    Run JD explainer CLI for a single job.
    
    Returns:
        True if successful, False otherwise
    """
    cmd = [
        sys.executable,
        "-m",
        "experiments.jobhunter.jd_explainer_cli",
        "--from-scored-file",
        scored_file,
        "--job-id",
        job_id,
    ]
    
    if use_default_profile:
        cmd.append("--use-default-profile")
    
    print(f"Running JD explainer for job {job_id}...")
    
    try:
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Run command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )
        
        if result.returncode != 0:
            print(f"Error running JD explainer for job {job_id}:")
            print(result.stderr)
            return False
        
        # Save output to file
        output_file.write_text(result.stdout, encoding="utf-8")
        print(f"Saved output to {output_file}")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"Timeout running JD explainer for job {job_id}")
        return False
    except Exception as e:
        print(f"Error running JD explainer for job {job_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run JD explainer on multiple jobs"
    )
    parser.add_argument(
        "--scored-file",
        type=str,
        required=True,
        help="Path to scored jobs JSON file",
    )
    parser.add_argument(
        "--job-ids",
        type=str,
        nargs="+",
        required=True,
        help="List of job IDs to process",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for summary files",
    )
    parser.add_argument(
        "--use-default-profile",
        action="store_true",
        default=True,
        help="Use default candidate profile (Andy's profile)",
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = Path(__file__).parent.parent.parent
    scored_file = project_root / args.scored_file if not Path(args.scored_file).is_absolute() else Path(args.scored_file)
    output_dir = project_root / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each job
    success_count = 0
    failed_jobs = []
    
    for job_id in args.job_ids:
        output_file = output_dir / f"jd_summary_{job_id}_andy_agents.md"
        
        if run_jd_explainer(
            str(scored_file),
            job_id,
            output_file,
            use_default_profile=args.use_default_profile,
        ):
            success_count += 1
        else:
            failed_jobs.append(job_id)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {success_count}/{len(args.job_ids)} jobs processed successfully")
    if failed_jobs:
        print(f"Failed jobs: {', '.join(failed_jobs)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()





