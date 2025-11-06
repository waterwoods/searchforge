#!/usr/bin/env python3
"""
Smoke test for RAG API - collects latency metrics and error rates
"""

import argparse
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple
import sys

try:
    import aiohttp
except ImportError:
    print("Error: aiohttp not installed. Install with: pip install aiohttp", file=sys.stderr)
    sys.exit(1)


# Fixed set of test queries
TEST_QUERIES = [
    "what is python",
    "how does search work",
    "explain vector database",
    "what is machine learning",
    "how to optimize performance",
]


async def single_request(session: aiohttp.ClientSession, base_url: str, query: str, timeout_sec: float) -> Tuple[float, bool, str]:
    """Execute a single request and return (latency_ms, success, error_msg)"""
    url = f"{base_url}/search"
    start_time = time.perf_counter()
    error_msg = ""
    
    try:
        payload = {"query": query, "top_k": 10}
        # Use timeout for both connect and read
        timeout = aiohttp.ClientTimeout(total=timeout_sec, connect=timeout_sec, sock_read=timeout_sec)
        async with session.post(url, json=payload, timeout=timeout) as resp:
            latency_ms = (time.perf_counter() - start_time) * 1000
            # Success = 200 <= status < 300
            if 200 <= resp.status < 300:
                return (latency_ms, True, "")
            else:
                error_msg = f"HTTP {resp.status}"
                return (latency_ms, False, error_msg)
    except asyncio.TimeoutError:
        # On timeout, count as error with latency = timeout
        latency_ms = timeout_sec * 1000
        return (latency_ms, False, "timeout")
    except Exception as e:
        # On any exception, count as error with latency = timeout
        latency_ms = timeout_sec * 1000
        return (latency_ms, False, str(e))


async def run_smoke_test(base_url: str, n: int, concurrency: int, warmup: int, timeout_sec: float) -> Dict:
    """Run smoke test with specified parameters"""
    # Health check first
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return {
                        "error": f"Health check failed: HTTP {resp.status}",
                        "n": n,
                        "warmup": warmup,
                        "concurrency": concurrency,
                        "timeout": timeout_sec,
                        "p50": None,
                        "p95": None,
                        "avg": None,
                        "error_rate": 1.0,
                        "total_requests": 0,
                        "successful_requests": 0,
                    }
    except Exception as e:
        return {
            "error": f"Health check failed: {e}",
            "n": n,
            "warmup": warmup,
            "concurrency": concurrency,
            "timeout": timeout_sec,
            "p50": None,
            "p95": None,
            "avg": None,
            "error_rate": 1.0,
            "total_requests": 0,
            "successful_requests": 0,
        }
    
    # Prepare queries (cycle through test queries to reach N requests)
    queries = (TEST_QUERIES * ((n // len(TEST_QUERIES)) + 1))[:n]
    
    # Run requests with concurrency limit
    semaphore = asyncio.Semaphore(concurrency)
    results: List[Tuple[float, bool, str]] = []
    
    async def bounded_request(session, query):
        async with semaphore:
            return await single_request(session, base_url, query, timeout_sec)
    
    async with aiohttp.ClientSession() as session:
        tasks = [bounded_request(session, query) for query in queries]
        results = await asyncio.gather(*tasks)
    
    # Exclude first 'warmup' samples from metrics
    if warmup > 0 and len(results) > warmup:
        results = results[warmup:]
    
    # Calculate metrics
    latencies = [r[0] for r in results]
    successes = [r[1] for r in results]
    errors = [r[2] for r in results if not r[1]]
    
    if not latencies:
        return {
            "error": "No requests completed",
            "n": n,
            "warmup": warmup,
            "concurrency": concurrency,
            "timeout": timeout_sec,
            "p50": None,
            "p95": None,
            "avg": None,
            "error_rate": 1.0,
            "total_requests": 0,
            "successful_requests": 0,
        }
    
    latencies.sort()
    total = len(latencies)
    successful = sum(successes)
    error_rate = (total - successful) / total if total > 0 else 0.0
    
    p50_idx = int(total * 0.50)
    p95_idx = int(total * 0.95)
    p50 = latencies[p50_idx] if p50_idx < total else latencies[-1]
    p95 = latencies[p95_idx] if p95_idx < total else latencies[-1]
    avg = sum(latencies) / total
    
    return {
        "n": n,
        "warmup": warmup,
        "concurrency": concurrency,
        "timeout": timeout_sec,
        "p50": round(p50, 2),
        "p95": round(p95, 2),
        "avg": round(avg, 2),
        "error_rate": round(error_rate, 4),
        "total_requests": total,
        "successful_requests": successful,
        "min": round(latencies[0], 2) if latencies else None,
        "max": round(latencies[-1], 2) if latencies else None,
        "errors": errors[:10] if errors else [],  # Sample of first 10 errors
    }


def main():
    parser = argparse.ArgumentParser(description="Run smoke test on RAG API")
    parser.add_argument("--n", type=int, default=30, help="Number of requests (default: 30)")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrency level (default: 5)")
    parser.add_argument("--warmup", type=int, default=10, help="Number of warmup requests to exclude from metrics (default: 10)")
    parser.add_argument("--timeout", type=float, default=3.0, help="Request timeout in seconds (default: 3.0)")
    parser.add_argument("--base", required=True, help="Base URL (e.g., http://localhost:8000)")
    args = parser.parse_args()
    
    # Ensure base URL doesn't end with /
    base_url = args.base.rstrip("/")
    
    # Run async test
    result = asyncio.run(run_smoke_test(base_url, args.n, args.concurrency, args.warmup, args.timeout))
    
    # Output JSON to stdout
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
