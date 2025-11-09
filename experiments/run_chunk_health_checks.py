#!/usr/bin/env python3
"""
Run Health Checks for Chunking Collections

This script runs qrels_doctor.py and embed_doctor.py for all three chunking collections
to verify:
1. Qrels coverage >= 99%
2. Embedding model consistency (all-MiniLM-L6-v2, dim=384)

Usage:
    python experiments/run_chunk_health_checks.py
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def run_qrels_doctor(
    collection_name: str,
    qrels_path: str,
    qdrant_host: str,
    qdrant_port: int,
    out_path: str
) -> Dict[str, Any]:
    """
    Run qrels_doctor.py for a collection.
    
    Returns:
        Report dictionary or None if failed
    """
    print(f"\n{'='*60}")
    print(f"Running qrels_doctor for {collection_name}")
    print(f"{'='*60}")
    
    cmd = [
        'python', 'tools/eval/qrels_doctor.py',
        '--collection', collection_name,
        '--qrels', qrels_path,
        '--qdrant-host', qdrant_host,
        '--qdrant-port', str(qdrant_port),
        '--out', out_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Load report
        if Path(out_path).exists():
            with open(out_path, 'r') as f:
                report = json.load(f)
            
            coverage = report.get('coverage', {}).get('percent', 0)
            status = report.get('status', 'UNKNOWN')
            
            print(f"\nCoverage: {coverage:.2f}%")
            print(f"Status: {status}")
            
            if result.returncode != 0:
                print(f"⚠️  qrels_doctor exited with code {result.returncode}")
            
            return report
        else:
            print(f"❌ Report file not found: {out_path}")
            return None
            
    except Exception as e:
        print(f"❌ Error running qrels_doctor: {e}")
        return None


def run_embed_doctor(
    collection_name: str,
    qdrant_host: str,
    qdrant_port: int,
    out_path: str,
    api_url: str = None
) -> Dict[str, Any]:
    """
    Run embed_doctor.py for a collection.
    
    Returns:
        Report dictionary or None if failed
    """
    print(f"\n{'='*60}")
    print(f"Running embed_doctor for {collection_name}")
    print(f"{'='*60}")
    
    cmd = [
        'python', 'tools/eval/embed_doctor.py',
        '--collection', collection_name,
        '--qdrant-host', qdrant_host,
        '--qdrant-port', str(qdrant_port),
        '--out', out_path
    ]
    
    if api_url:
        cmd.extend(['--api-url', api_url])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Load report
        if Path(out_path).exists():
            with open(out_path, 'r') as f:
                report = json.load(f)
            
            status = report.get('comparison', {}).get('status', 'UNKNOWN')
            model_match = report.get('comparison', {}).get('model_match', False)
            dim_match = report.get('comparison', {}).get('dim_match', False)
            
            print(f"\nModel match: {model_match}")
            print(f"Dimension match: {dim_match}")
            print(f"Status: {status}")
            
            if result.returncode != 0:
                print(f"⚠️  embed_doctor exited with code {result.returncode}")
            
            return report
        else:
            print(f"❌ Report file not found: {out_path}")
            return None
            
    except Exception as e:
        print(f"❌ Error running embed_doctor: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Run health checks for chunking collections"
    )
    parser.add_argument(
        '--qdrant-host',
        type=str,
        default='localhost',
        help='Qdrant host (default: localhost)'
    )
    parser.add_argument(
        '--qdrant-port',
        type=int,
        default=6333,
        help='Qdrant port (default: 6333)'
    )
    parser.add_argument(
        '--qrels-path',
        type=str,
        default='data/fiqa_v1/fiqa_qrels_50k_v1.jsonl',
        help='Path to qrels file'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default=None,
        help='API URL for embed_doctor (optional)'
    )
    
    args = parser.parse_args()
    
    repo_root = find_repo_root()
    reports_dir = repo_root / 'reports' / 'chunk_health'
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Define collections
    collections = [
        'fiqa_para_50k',
        'fiqa_sent_50k',
        'fiqa_win256_o64_50k'
    ]
    
    # Resolve qrels path
    qrels_path = Path(args.qrels_path)
    if not qrels_path.is_absolute():
        qrels_path = repo_root / qrels_path
    
    # Run health checks
    all_results = {}
    
    for collection_name in collections:
        print(f"\n\n{'#'*60}")
        print(f"# Health checks for {collection_name}")
        print(f"{'#'*60}\n")
        
        results = {
            'collection_name': collection_name,
            'qrels_doctor': None,
            'embed_doctor': None
        }
        
        # Run qrels_doctor
        qrels_out = reports_dir / f"qrels_{collection_name}.json"
        qrels_report = run_qrels_doctor(
            collection_name,
            str(qrels_path),
            args.qdrant_host,
            args.qdrant_port,
            str(qrels_out)
        )
        results['qrels_doctor'] = qrels_report
        
        # Run embed_doctor
        embed_out = reports_dir / f"embed_{collection_name}.json"
        embed_report = run_embed_doctor(
            collection_name,
            args.qdrant_host,
            args.qdrant_port,
            str(embed_out),
            args.api_url
        )
        results['embed_doctor'] = embed_report
        
        all_results[collection_name] = results
    
    # Generate summary report
    print(f"\n\n{'='*60}")
    print(f"HEALTH CHECK SUMMARY")
    print(f"{'='*60}\n")
    
    summary = {
        'collections': [],
        'all_pass': True
    }
    
    for collection_name, results in all_results.items():
        qrels_report = results.get('qrels_doctor')
        embed_report = results.get('embed_doctor')
        
        qrels_pass = False
        embed_pass = False
        
        if qrels_report:
            coverage = qrels_report.get('coverage', {}).get('percent', 0)
            qrels_status = qrels_report.get('status', 'UNKNOWN')
            qrels_pass = qrels_status == 'PASS' and coverage >= 99.0
        
        if embed_report:
            embed_status = embed_report.get('comparison', {}).get('status', 'UNKNOWN')
            embed_pass = embed_status == 'PASS'
        
        overall_pass = qrels_pass and embed_pass
        
        if not overall_pass:
            summary['all_pass'] = False
        
        summary['collections'].append({
            'name': collection_name,
            'qrels_coverage': qrels_report.get('coverage', {}).get('percent', 0) if qrels_report else 0,
            'qrels_pass': qrels_pass,
            'embed_pass': embed_pass,
            'overall_pass': overall_pass
        })
        
        print(f"{collection_name}:")
        print(f"  Qrels coverage: {qrels_report.get('coverage', {}).get('percent', 0):.2f}%" if qrels_report else "  Qrels: N/A")
        print(f"  Qrels status: {'✅ PASS' if qrels_pass else '❌ FAIL'}")
        print(f"  Embed status: {'✅ PASS' if embed_pass else '❌ FAIL'}")
        print(f"  Overall: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        print()
    
    # Write summary
    summary_path = reports_dir / 'health_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Summary written to: {summary_path}")
    
    # Exit code
    if summary['all_pass']:
        print(f"\n✅ All health checks PASSED!")
        sys.exit(0)
    else:
        print(f"\n❌ Some health checks FAILED!")
        print(f"Please review the reports in {reports_dir}")
        sys.exit(1)


if __name__ == '__main__':
    main()

