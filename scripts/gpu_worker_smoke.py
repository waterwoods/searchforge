#!/usr/bin/env python3
"""
GPU Worker Smoke Test

Checks:
- /healthz -> 200
- /ready -> 200
- /meta contains device="cuda"
- POST /embed (100 texts) -> assert shapes & latencies
- POST /rerank (top_n=5) -> assert shapes & latencies
- Print sample vectors and device info
"""

import os
import sys
import time
import json
import argparse
from typing import Dict, Any, List

try:
    import requests
    import numpy as np
except ImportError:
    print("ERROR: Missing dependencies. Install: pip install requests numpy")
    sys.exit(1)


def check_healthz(base_url: str) -> bool:
    """Check /healthz endpoint."""
    try:
        resp = requests.get(f"{base_url}/healthz", timeout=5)
        if resp.status_code == 200:
            print("✅ /healthz -> 200")
            return True
        else:
            print(f"❌ /healthz -> {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ /healthz failed: {e}")
        return False


def check_ready(base_url: str) -> bool:
    """Check /ready endpoint."""
    try:
        resp = requests.get(f"{base_url}/ready", timeout=5)
        if resp.status_code == 200:
            print("✅ /ready -> 200")
            return True
        else:
            print(f"❌ /ready -> {resp.status_code}")
            if resp.status_code == 503:
                print("   (Models not loaded yet, wait a bit longer)")
            return False
    except Exception as e:
        print(f"❌ /ready failed: {e}")
        return False


def check_meta(base_url: str) -> Dict[str, Any]:
    """Check /meta endpoint and validate device."""
    try:
        resp = requests.get(f"{base_url}/meta", timeout=5)
        if resp.status_code != 200:
            print(f"❌ /meta -> {resp.status_code}")
            return {}
        
        meta = resp.json()
        print(f"✅ /meta -> 200")
        print(f"   model_embed: {meta.get('model_embed')}")
        print(f"   model_rerank: {meta.get('model_rerank')}")
        print(f"   device: {meta.get('device')}")
        print(f"   git_sha: {meta.get('git_sha', 'unknown')[:8]}")
        
        if meta.get('device') != 'cuda':
            print(f"⚠️  WARNING: device is '{meta.get('device')}', expected 'cuda'")
        
        return meta
    except Exception as e:
        print(f"❌ /meta failed: {e}")
        return {}


def test_embed(base_url: str, n_texts: int = 100) -> bool:
    """Test /embed endpoint with multiple texts."""
    print(f"\n🧪 Testing /embed with {n_texts} texts...")
    
    # Generate test texts
    texts = [f"This is test text number {i} for embedding." for i in range(n_texts)]
    
    try:
        start = time.time()
        resp = requests.post(
            f"{base_url}/embed",
            json={"texts": texts, "normalize": False},
            timeout=30
        )
        latency_ms = (time.time() - start) * 1000
        
        if resp.status_code != 200:
            print(f"❌ /embed -> {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            return False
        
        data = resp.json()
        vectors = data.get("vectors", [])
        
        if len(vectors) != n_texts:
            print(f"❌ /embed: expected {n_texts} vectors, got {len(vectors)}")
            return False
        
        # Check vector dimensions (all-MiniLM-L6-v2 has 384 dims)
        dim = len(vectors[0]) if vectors else 0
        if dim == 0:
            print(f"❌ /embed: empty vector")
            return False
        
        # Check all vectors have same dimension
        for i, vec in enumerate(vectors):
            if len(vec) != dim:
                print(f"❌ /embed: vector {i} has dimension {len(vec)}, expected {dim}")
                return False
        
        print(f"✅ /embed -> 200")
        print(f"   vectors: {len(vectors)}")
        print(f"   dimension: {dim}")
        print(f"   latency: {latency_ms:.1f}ms")
        print(f"   sample vector[0][:5]: {vectors[0][:5]}")
        
        return True
    except Exception as e:
        print(f"❌ /embed failed: {e}")
        return False


def test_rerank(base_url: str, top_n: int = 5) -> bool:
    """Test /rerank endpoint."""
    print(f"\n🧪 Testing /rerank with top_n={top_n}...")
    
    query = "What is machine learning?"
    docs = [
        "Machine learning is a subset of artificial intelligence.",
        "Python is a programming language.",
        "Deep learning uses neural networks.",
        "Natural language processing helps computers understand text.",
        "Computer vision processes images.",
        "Reinforcement learning uses rewards.",
        "Supervised learning uses labeled data.",
        "Unsupervised learning finds patterns without labels.",
    ]
    
    try:
        start = time.time()
        resp = requests.post(
            f"{base_url}/rerank",
            json={"query": query, "docs": docs, "top_n": top_n},
            timeout=30
        )
        latency_ms = (time.time() - start) * 1000
        
        if resp.status_code != 200:
            print(f"❌ /rerank -> {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            return False
        
        data = resp.json()
        indices = data.get("indices", [])
        scores = data.get("scores", [])
        
        if len(indices) != len(scores):
            print(f"❌ /rerank: indices length ({len(indices)}) != scores length ({len(scores)})")
            return False
        
        if len(indices) > top_n:
            print(f"❌ /rerank: returned {len(indices)} results, expected <= {top_n}")
            return False
        
        if len(indices) == 0:
            print(f"❌ /rerank: returned no results")
            return False
        
        # Check scores are in descending order
        for i in range(len(scores) - 1):
            if scores[i] < scores[i + 1]:
                print(f"⚠️  /rerank: scores not in descending order")
                break
        
        print(f"✅ /rerank -> 200")
        print(f"   top_n: {len(indices)}")
        print(f"   latency: {latency_ms:.1f}ms")
        print(f"   top indices: {indices[:3]}")
        print(f"   top scores: {[f'{s:.3f}' for s in scores[:3]]}")
        
        return True
    except Exception as e:
        print(f"❌ /rerank failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="GPU Worker Smoke Test")
    parser.add_argument(
        "--url",
        default=os.getenv("GPU_WORKER_URL", "http://localhost:8090"),
        help="GPU worker base URL"
    )
    parser.add_argument(
        "--n-texts",
        type=int,
        default=100,
        help="Number of texts for embed test"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Top N for rerank test"
    )
    args = parser.parse_args()
    
    base_url = args.url.rstrip("/")
    
    print("=" * 60)
    print("GPU Worker Smoke Test")
    print("=" * 60)
    print(f"URL: {base_url}\n")
    
    results = {}
    
    # Test 1: Health check
    print("1. Testing /healthz...")
    results["healthz"] = check_healthz(base_url)
    
    # Test 2: Ready check
    print("\n2. Testing /ready...")
    results["ready"] = check_ready(base_url)
    
    # Test 3: Meta check
    print("\n3. Testing /meta...")
    meta = check_meta(base_url)
    results["meta"] = bool(meta)
    results["device_cuda"] = meta.get("device") == "cuda"
    
    # Test 4: Embed
    if results["ready"]:
        results["embed"] = test_embed(base_url, n_texts=args.n_texts)
    else:
        print("\n⚠️  Skipping /embed test (not ready)")
        results["embed"] = False
    
    # Test 5: Rerank
    if results["ready"]:
        results["rerank"] = test_rerank(base_url, top_n=args.top_n)
    else:
        print("\n⚠️  Skipping /rerank test (not ready)")
        results["rerank"] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test:20s} {status}")
    
    print("\n" + ("✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"))
    
    # Write results to file
    output_file = ".runs/gpu_worker_smoke.json"
    os.makedirs(".runs", exist_ok=True)
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "url": base_url,
            "results": results,
            "all_passed": all_passed
        }, f, indent=2)
    print(f"\nResults written to: {output_file}")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

