#!/usr/bin/env python3
"""
Proxy Smoke Test

Tests the end-to-end path: proxy → rag-api → GPU worker → Qdrant

This smoke test verifies:
1. Go proxy health endpoints (/healthz, /readyz)
2. Go proxy search endpoint (/v1/search)
3. rag-api endpoints with GPU worker integration
4. End-to-end query flow through the full stack

Note: Currently the proxy routes directly to Qdrant. This test verifies
both the proxy endpoints and the rag-api → GPU worker → Qdrant path.
"""

import os
import sys
import time
import json
import argparse
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: Missing dependency: requests. Install with: pip install requests")
    sys.exit(1)


# Default endpoints
DEFAULT_PROXY_URL = os.getenv("PROXY_URL", "http://localhost:7070")
DEFAULT_RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000")
DEFAULT_GPU_WORKER_URL = os.getenv("GPU_WORKER_URL", "http://localhost:8090")


def check_proxy_healthz(proxy_url: str) -> bool:
    """Check proxy /healthz endpoint."""
    try:
        resp = requests.get(f"{proxy_url}/healthz", timeout=5)
        if resp.status_code == 200:
            print("✅ Proxy /healthz -> 200")
            return True
        else:
            print(f"❌ Proxy /healthz -> {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Proxy /healthz failed: {e}")
        return False


def check_proxy_readyz(proxy_url: str) -> bool:
    """Check proxy /readyz endpoint."""
    try:
        resp = requests.get(f"{proxy_url}/readyz", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            qdrant_ok = data.get("qdrant_ok", False)
            print(f"✅ Proxy /readyz -> 200 (qdrant_ok={qdrant_ok})")
            return qdrant_ok
        else:
            print(f"❌ Proxy /readyz -> {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Proxy /readyz failed: {e}")
        return False


def test_proxy_search(proxy_url: str, query: str = "what is ETF?", k: int = 8, budget_ms: int = 400) -> Dict[str, Any]:
    """Test proxy /v1/search endpoint."""
    print(f"\n🧪 Testing proxy /v1/search with query='{query}', k={k}, budget_ms={budget_ms}...")
    
    try:
        start = time.time()
        resp = requests.get(
            f"{proxy_url}/v1/search",
            params={"q": query, "k": k, "budget_ms": budget_ms},
            timeout=10
        )
        latency_ms = (time.time() - start) * 1000
        
        if resp.status_code != 200:
            print(f"❌ Proxy /v1/search -> {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        
        data = resp.json()
        # items may be missing or explicitly null; normalize to a list
        raw_items = data.get("items")
        items = raw_items or []
        ret_code = data.get("ret_code", "UNKNOWN")
        degraded = data.get("degraded", False)
        timings = data.get("timings", {})
        
        print(f"✅ Proxy /v1/search -> 200")
        print(f"   ret_code: {ret_code}")
        print(f"   degraded: {degraded}")
        print(f"   items: {len(items)}")
        print(f"   total_ms: {timings.get('total_ms', 'N/A')}")
        print(f"   cache_hit: {timings.get('cache_hit', False)}")
        print(f"   latency: {latency_ms:.1f}ms")
        
        if items:
            print(f"   sample item id: {items[0].get('id', 'N/A')}")
        
        return {
            "success": True,
            "ret_code": ret_code,
            "degraded": degraded,
            "items_count": len(items),
            "timings": timings,
            "latency_ms": latency_ms
        }
    except Exception as e:
        print(f"❌ Proxy /v1/search failed: {e}")
        return {"success": False, "error": str(e)}


def check_gpu_worker_ready(gpu_worker_url: str) -> bool:
    """Check GPU worker /ready endpoint."""
    try:
        resp = requests.get(f"{gpu_worker_url}/ready", timeout=5)
        if resp.status_code == 200:
            print("✅ GPU worker /ready -> 200")
            return True
        else:
            print(f"❌ GPU worker /ready -> {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ GPU worker /ready failed: {e}")
        return False


def check_gpu_worker_meta(gpu_worker_url: str) -> Dict[str, Any]:
    """Check GPU worker /meta endpoint."""
    try:
        resp = requests.get(f"{gpu_worker_url}/meta", timeout=5)
        if resp.status_code == 200:
            meta = resp.json()
            device = meta.get("device", "unknown")
            print(f"✅ GPU worker /meta -> 200 (device={device})")
            return meta
        else:
            print(f"❌ GPU worker /meta -> {resp.status_code}")
            return {}
    except Exception as e:
        print(f"❌ GPU worker /meta failed: {e}")
        return {}


def check_rag_api_health(rag_api_url: str) -> bool:
    """Check rag-api health endpoint."""
    try:
        resp = requests.get(f"{rag_api_url}/healthz", timeout=5)
        if resp.status_code == 200:
            print("✅ rag-api /healthz -> 200")
            return True
        else:
            print(f"❌ rag-api /healthz -> {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ rag-api /healthz failed: {e}")
        return False


def check_rag_api_ready(rag_api_url: str) -> bool:
    """Check rag-api /readyz endpoint."""
    try:
        resp = requests.get(f"{rag_api_url}/readyz", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            clients_ready = data.get("clients_ready", False)
            print(f"✅ rag-api /readyz -> 200 (clients_ready={clients_ready})")
            return clients_ready
        else:
            print(f"❌ rag-api /readyz -> {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ rag-api /readyz failed: {e}")
        return False


def test_rag_api_query(rag_api_url: str, query: str = "what is ETF?", top_k: int = 5) -> Dict[str, Any]:
    """Test rag-api /api/query endpoint (full path through GPU worker and Qdrant)."""
    print(f"\n🧪 Testing rag-api /api/query with query='{query}', top_k={top_k}...")
    
    try:
        start = time.time()
        resp = requests.post(
            f"{rag_api_url}/api/query",
            json={"question": query, "top_k": top_k, "rerank": False},
            timeout=15
        )
        latency_ms = (time.time() - start) * 1000
        
        if resp.status_code != 200:
            print(f"❌ rag-api /api/query -> {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        
        data = resp.json()
        items = data.get("items", [])
        route = data.get("route", "unknown")
        
        print(f"✅ rag-api /api/query -> 200")
        print(f"   route: {route}")
        print(f"   items: {len(items)}")
        print(f"   latency: {latency_ms:.1f}ms")
        
        if items:
            print(f"   sample item id: {items[0].get('id', 'N/A')}")
        
        return {
            "success": True,
            "route": route,
            "items_count": len(items),
            "latency_ms": latency_ms
        }
    except Exception as e:
        print(f"❌ rag-api /api/query failed: {e}")
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Proxy Smoke Test")
    parser.add_argument(
        "--proxy-url",
        default=DEFAULT_PROXY_URL,
        help="Proxy base URL"
    )
    parser.add_argument(
        "--rag-api-url",
        default=DEFAULT_RAG_API_URL,
        help="rag-api base URL"
    )
    parser.add_argument(
        "--gpu-worker-url",
        default=DEFAULT_GPU_WORKER_URL,
        help="GPU worker base URL"
    )
    parser.add_argument(
        "--query",
        default="what is ETF?",
        help="Test query"
    )
    parser.add_argument(
        "--output",
        default=".runs/proxy_smoke.json",
        help="Output JSON file path"
    )
    args = parser.parse_args()
    
    proxy_url = args.proxy_url.rstrip("/")
    rag_api_url = args.rag_api_url.rstrip("/")
    gpu_worker_url = args.gpu_worker_url.rstrip("/")
    
    print("=" * 70)
    print("Proxy Smoke Test")
    print("=" * 70)
    print(f"Proxy URL: {proxy_url}")
    print(f"rag-api URL: {rag_api_url}")
    print(f"GPU worker URL: {gpu_worker_url}")
    print(f"Test query: {args.query}\n")
    
    results = {}
    
    # Test 1: Proxy health endpoints
    print("1. Testing proxy health endpoints...")
    results["proxy_healthz"] = check_proxy_healthz(proxy_url)
    results["proxy_readyz"] = check_proxy_readyz(proxy_url)
    
    # Test 2: Proxy search endpoint
    print("\n2. Testing proxy search endpoint...")
    proxy_search_result = test_proxy_search(proxy_url, query=args.query)
    results["proxy_search"] = proxy_search_result.get("success", False)
    results["proxy_search_details"] = proxy_search_result
    
    # Test 3: GPU worker readiness
    print("\n3. Testing GPU worker readiness...")
    results["gpu_worker_ready"] = check_gpu_worker_ready(gpu_worker_url)
    gpu_meta = check_gpu_worker_meta(gpu_worker_url)
    results["gpu_worker_device"] = gpu_meta.get("device", "unknown")
    
    # Test 4: rag-api health endpoints
    print("\n4. Testing rag-api health endpoints...")
    results["rag_api_healthz"] = check_rag_api_health(rag_api_url)
    results["rag_api_readyz"] = check_rag_api_ready(rag_api_url)
    
    # Test 5: rag-api query (full path through GPU worker and Qdrant)
    print("\n5. Testing rag-api query (GPU worker + Qdrant path)...")
    rag_api_result = test_rag_api_query(rag_api_url, query=args.query)
    results["rag_api_query"] = rag_api_result.get("success", False)
    results["rag_api_query_details"] = rag_api_result
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    all_passed = (
        results.get("proxy_healthz") and
        results.get("proxy_readyz") and
        results.get("proxy_search") and
        results.get("gpu_worker_ready") and
        results.get("rag_api_healthz") and
        results.get("rag_api_readyz") and
        results.get("rag_api_query")
    )
    
    for test, passed in results.items():
        if isinstance(passed, bool):
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test:30s} {status}")
    
    print("\n" + ("✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"))
    
    # Write results to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "proxy_url": proxy_url,
            "rag_api_url": rag_api_url,
            "gpu_worker_url": gpu_worker_url,
            "query": args.query,
            "results": results,
            "all_passed": all_passed
        }, f, indent=2)
    print(f"\nResults written to: {output_path}")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

