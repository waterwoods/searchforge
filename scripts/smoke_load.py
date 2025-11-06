#!/usr/bin/env python3
"""Smoke load test: 50-100 /search requests with rate limit respect"""
import requests, time, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL, NUM_REQUESTS = "http://localhost:8080", 60
QUERIES = ["invest stocks", "credit score tips", "retirement planning", "tax filing"]

def send_request(delay=0):
    time.sleep(delay)  # Respect rate limit
    try:
        start = time.time()
        resp = requests.post(f"{BASE_URL}/search", 
                           json={"query": QUERIES[int(time.time()) % len(QUERIES)], "top_k": 5}, timeout=5)
        return (resp.status_code == 200, (time.time() - start) * 1000)
    except:
        return (False, 0)

def main():
    print(f"🔥 Smoke Load Test: {NUM_REQUESTS} requests (batched for rate limit)\n")
    start = time.time()
    results = []
    # Send in batches of 3 per second
    for i in range(0, NUM_REQUESTS, 3):
        batch = min(3, NUM_REQUESTS - i)
        with ThreadPoolExecutor(max_workers=3) as ex:
            batch_results = [ex.submit(send_request).result() for _ in range(batch)]
            results.extend(batch_results)
        if i + 3 < NUM_REQUESTS:
            time.sleep(1.0)  # Wait 1s before next batch
    
    total_time = time.time() - start
    successes = [r for r in results if r[0]]
    latencies = [r[1] for r in successes]
    success_rate = len(successes) / len(results) * 100
    p95 = statistics.quantiles(latencies, n=20)[18] if latencies else 0
    
    print(f"[SANITY] success_rate={success_rate:.1f}% / P95={p95:.1f}ms / QPS={len(results)/total_time:.1f}")
    return 0 if success_rate > 90 else 1

if __name__ == "__main__":
    exit(main())

