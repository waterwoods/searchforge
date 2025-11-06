#!/usr/bin/env python3
"""
10-minute A/B test for comprehensive validation
"""
import subprocess
import time
import json
from pathlib import Path

def run_test_cycle(duration_sec=300):
    """Run alternating baseline and reranker tests for specified duration"""
    print(f"🚀 Starting 10-minute A/B test (duration: {duration_sec}s)")
    start_time = time.time()
    cycle = 0
    
    while time.time() - start_time < duration_sec:
        cycle += 1
        elapsed = int(time.time() - start_time)
        remaining = duration_sec - elapsed
        
        print(f"\n{'='*60}")
        print(f"CYCLE {cycle} | Elapsed: {elapsed}s / Remaining: {remaining}s")
        print(f"{'='*60}")
        
        # Run baseline
        print(f"\n[{cycle}.1] Running BASELINE...")
        subprocess.run(["python", "scripts/smoke_fiqa.py", "--rerank", "off"], 
                      capture_output=False, timeout=60)
        
        # Check time
        if time.time() - start_time >= duration_sec:
            break
            
        # Run reranker
        print(f"\n[{cycle}.2] Running RERANKER...")
        subprocess.run(["python", "scripts/smoke_fiqa.py", "--rerank", "on"], 
                      capture_output=False, timeout=60)
    
    print(f"\n✅ 10-minute test completed! Total cycles: {cycle}")
    
    # Load and compare results
    reports_dir = Path("reports")
    baseline = json.load(open(reports_dir / "fiqa_smoke_baseline.json"))
    rerank = json.load(open(reports_dir / "fiqa_smoke_rerank.json"))
    
    return baseline, rerank

if __name__ == "__main__":
    baseline, rerank = run_test_cycle(duration_sec=600)  # 10 minutes
    
    # Print final summary
    delta_recall = (rerank["recall@10"] - baseline["recall@10"]) / baseline["recall@10"] * 100
    delta_p95 = rerank["p95_latency_ms"] - baseline["p95_latency_ms"]
    
    print("\n" + "="*60)
    print("🏆 10-MINUTE A/B TEST SUMMARY")
    print("="*60)
    print(f"✅ ΔRecall@10: {delta_recall:+.1f}%")
    print(f"⏱️  ΔP95: {delta_p95:+.1f}ms")
    print(f"🎯 Rerank Hit Rate: {rerank['rerank_hit_rate']*100:.1f}%")
    print(f"✓ Success Rate: {rerank['success_rate']*100:.1f}%")
    print("="*60)
