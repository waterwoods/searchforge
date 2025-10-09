#!/usr/bin/env python3
"""
API Contract Validation Script
Validates FIQA API endpoints against frozen contract
"""
import sys
import time
import requests
from datetime import datetime

BASE_URL = "http://localhost:8080"
RESULTS = []

def log_test(name, passed, details=""):
    """Record test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    RESULTS.append((name, passed))
    print(f"  {status} {name}")
    if details:
        print(f"      {details}")
    return passed

def test_health():
    """Test /health endpoint returns 200"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=2)
        return log_test("/health → 200", resp.status_code == 200, f"Got: {resp.status_code}")
    except Exception as e:
        return log_test("/health → 200", False, str(e))

def test_search_empty_query():
    """Test /search with empty query returns 422 with unified error format"""
    try:
        resp = requests.post(f"{BASE_URL}/search", json={"query": "", "top_k": 5}, timeout=2)
        is_422 = resp.status_code == 422
        
        if is_422:
            body = resp.json()
            has_code = "code" in body
            has_msg = "msg" in body
            has_hint = "hint" in body
            has_ts = "ts" in body
            all_fields = has_code and has_msg and has_hint and has_ts
            return log_test(
                "/search (empty) → 422 {code,msg,hint,ts}", 
                all_fields,
                f"Fields present: code={has_code}, msg={has_msg}, hint={has_hint}, ts={has_ts}"
            )
        else:
            return log_test("/search (empty) → 422", False, f"Got: {resp.status_code}")
    except Exception as e:
        return log_test("/search (empty) → 422", False, str(e))

def test_rate_limit():
    """Test /search rate limiting returns 429 with unified error format"""
    try:
        # Send 5 rapid requests (limit is 3/sec)
        responses = []
        for i in range(5):
            resp = requests.post(
                f"{BASE_URL}/search", 
                json={"query": f"test query {i}", "top_k": 5}, 
                timeout=2
            )
            responses.append(resp)
        
        # Check if any returned 429
        rate_limited = [r for r in responses if r.status_code == 429]
        if not rate_limited:
            return log_test("/search (rate limit) → 429", False, "No 429 response received")
        
        # Check error format
        body = rate_limited[0].json()
        has_code = "code" in body
        has_msg = "msg" in body
        has_hint = "hint" in body
        has_ts = "ts" in body
        all_fields = has_code and has_msg and has_hint and has_ts
        
        return log_test(
            "/search (rate limit) → 429 {code,msg,hint,ts}",
            all_fields,
            f"Fields present: code={has_code}, msg={has_msg}, hint={has_hint}, ts={has_ts}"
        )
    except Exception as e:
        return log_test("/search (rate limit) → 429", False, str(e))

def test_metrics():
    """Test /metrics endpoint returns required fields"""
    try:
        resp = requests.get(f"{BASE_URL}/metrics", timeout=2)
        if resp.status_code != 200:
            return log_test("/metrics → 200", False, f"Got: {resp.status_code}")
        
        body = resp.json()
        required = ["count", "window_sec", "uptime_sec", "version"]
        missing = [k for k in required if k not in body]
        
        if missing:
            return log_test(
                "/metrics → {count,window_sec,uptime_sec,version}",
                False,
                f"Missing: {missing}"
            )
        
        # Verify version matches expected
        version_ok = body["version"] == "v1.0.0-fiqa"
        return log_test(
            "/metrics → {count,window_sec,uptime_sec,version}",
            version_ok,
            f"version={body['version']}, count={body['count']}, uptime={body['uptime_sec']}s"
        )
    except Exception as e:
        return log_test("/metrics → required fields", False, str(e))

def main():
    print("🔍 API Contract Validation")
    print("=" * 50)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}\n")
    
    # Run all tests
    test_health()
    time.sleep(0.5)
    test_search_empty_query()
    time.sleep(0.5)
    test_rate_limit()
    time.sleep(1.5)  # Wait for rate limit window to reset
    test_metrics()
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(1 for _, p in RESULTS if p)
    total = len(RESULTS)
    all_passed = passed == total
    
    status_emoji = "✓" if all_passed else "✗"
    print(f"[CONTRACT] {status_emoji} {passed}/{total} checks passed")
    
    # Print endpoint status
    endpoints = {"/health": False, "/search": False, "/metrics": False}
    for name, passed in RESULTS:
        if "/health" in name and passed:
            endpoints["/health"] = True
        if "/search" in name and passed:
            endpoints["/search"] = True
        if "/metrics" in name and passed:
            endpoints["/metrics"] = True
    
    endpoint_status = " | ".join(f"{ep}={'✓' if ok else '✗'}" for ep, ok in endpoints.items())
    print(f"Endpoints: {endpoint_status}\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

