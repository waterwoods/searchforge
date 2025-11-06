#!/usr/bin/env python3
"""
Extract metrics from experiment logs and update winners.json
"""
import json
import re
import sys
from pathlib import Path

def extract_metrics_from_log(log_content: str) -> dict:
    """Extract metrics from log content."""
    metrics = {
        "p95_ms": 0.0,
        "qps": 0.0,
        "recall_at_10": 0.0
    }
    
    # Pattern: "P95 latency: 123.4 ± 5.6 ms"
    p95_match = re.search(r'P95 latency:\s*([\d.]+)', log_content)
    if p95_match:
        metrics["p95_ms"] = float(p95_match.group(1))
    
    # Pattern: "QPS: 12.34"
    qps_match = re.search(r'QPS:\s*([\d.]+)', log_content)
    if qps_match:
        metrics["qps"] = float(qps_match.group(1))
    
    # Pattern: "Recall@10: 0.1234 ± 0.0056"
    recall_match = re.search(r'Recall@10:\s*([\d.]+)', log_content)
    if recall_match:
        metrics["recall_at_10"] = float(recall_match.group(1))
    
    return metrics

def main():
    winners_file = Path("winners.json")
    if not winners_file.exists():
        print(f"Error: {winners_file} not found")
        sys.exit(1)
    
    with open(winners_file, 'r') as f:
        data = json.load(f)
    
    # Job IDs to fetch logs for
    job_ids = [item["job_id"] for item in data["all"]]
    
    print(f"Fetching metrics for {len(job_ids)} jobs...")
    
    import subprocess
    
    for item in data["all"]:
        job_id = item["job_id"]
        print(f"  Processing {job_id}...")
        
        # Try to get metrics from artifacts API
        try:
            import urllib.request
            import urllib.parse
            
            api_base = "http://100.67.88.114:8000"
            artifacts_url = f"{api_base}/api/artifacts/{job_id}"
            
            with urllib.request.urlopen(artifacts_url) as response:
                artifacts_data = json.loads(response.read())
                
                if artifacts_data.get("ok") and artifacts_data.get("artifacts"):
                    report_data = artifacts_data["artifacts"].get("report_data", {})
                    configurations = report_data.get("configurations", [])
                    
                    # Get metrics from first configuration (Baseline)
                    if configurations:
                        config_metrics = configurations[0].get("metrics", {})
                        metrics = {
                            "p95_ms": config_metrics.get("p95_ms", {}).get("mean", 0.0),
                            "qps": config_metrics.get("qps", {}).get("mean", 0.0),
                            "recall_at_10": config_metrics.get("recall_at_10", {}).get("mean", 0.0)
                        }
                        
                        # Update item
                        item["p95_ms"] = metrics["p95_ms"]
                        item["qps"] = metrics["qps"]
                        item["recall_at_10"] = metrics["recall_at_10"]
                        
                        print(f"    ✅ recall={metrics['recall_at_10']:.4f}, p95={metrics['p95_ms']:.1f}ms, qps={metrics['qps']:.2f}")
                    else:
                        print(f"    ⚠️  No configurations found in artifacts")
                else:
                    print(f"    ⚠️  No artifacts data available")
                
                # Also extract params from status if missing
                if not item.get("top_k"):
                    status_url = f"{api_base}/api/experiment/status/{job_id}"
                    try:
                        with urllib.request.urlopen(status_url) as status_resp:
                            status_data = json.loads(status_resp.read())
                            job_data = status_data.get("job", status_data)
                            params = job_data.get("params", {})
                            item["top_k"] = params.get("top_k")
                            item["fast_mode"] = params.get("fast_mode", False)
                            item["dataset_name"] = params.get("dataset_name")
                    except:
                        pass
        except Exception as e:
            print(f"    ⚠️  Failed to fetch metrics: {e}")
    
    # Recalculate winners
    succeeded = [x for x in data["all"] if x.get("status") == "SUCCEEDED" or x.get("recall_at_10", 0) > 0]
    
    if succeeded:
        best_quality = max(succeeded, key=lambda x: x.get("recall_at_10", 0))
        best_latency = min([x for x in succeeded if x.get("p95_ms", 1e9) > 0], 
                          key=lambda x: x.get("p95_ms", 1e9), default=None)
        
        if best_latency:
            balanced = max(succeeded, key=lambda x: (x.get("recall_at_10", 0)) - 0.0005 * (x.get("p95_ms", 0)))
        else:
            balanced = best_quality
        
        data["winners"] = {
            "quality": best_quality,
            "latency": best_latency or best_quality,
            "balanced": balanced
        }
    
    # Save updated file
    with open(winners_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Updated {winners_file}")
    print(f"   Best quality: {data['winners']['quality']['job_id']} (recall={data['winners']['quality'].get('recall_at_10', 0):.4f})")
    if data['winners']['latency']:
        print(f"   Best latency: {data['winners']['latency']['job_id']} (p95={data['winners']['latency'].get('p95_ms', 0):.1f}ms)")

if __name__ == "__main__":
    main()

