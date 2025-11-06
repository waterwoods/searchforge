#!/usr/bin/env python3
"""
Auto Dashboard Health Check - 4-Minute System Validation
Tests bucket alignment, profile isolation, data flow, and synchronization.
"""
import requests
import time
import json
import sys
from datetime import datetime
from collections import defaultdict

BASE_URL = "http://localhost:8080"
PROFILES = ["fast", "balanced", "quality"]
TIMEOUT = 4

# Test results tracking
results = []
warnings = []
start_time = time.time()


def log(emoji, message):
    """Print timestamped log message"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {emoji} {message}")


def check_result(passed, check_name, message):
    """Record check result"""
    if passed:
        results.append((check_name, True))
        log("✅", f"{check_name}: {message}")
    else:
        results.append((check_name, False))
        warnings.append(check_name)
        log("⚠️", f"{check_name}: {message}")


def fetch_dashboard(profile="balanced", silent=False):
    """Fetch dashboard JSON with cache-busting"""
    try:
        url = f"{BASE_URL}/dashboard.json?profile={profile}&ts={int(time.time()*1000)}"
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        else:
            if not silent:
                log("⚠️", f"Dashboard returned {resp.status_code}")
            return None
    except Exception as e:
        if not silent:
            log("⚠️", f"Dashboard fetch failed: {e}")
        return None


def check_api_reachable():
    """Pre-flight: ensure API is up"""
    log("🔍", "Pre-flight: Checking API health...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if resp.status_code == 200:
            log("✅", "API is reachable")
            return True
    except:
        pass
    
    log("❌", "API not reachable at localhost:8080")
    return False


def check_bucket_alignment():
    """Test 1: Verify 5-second bucket spacing"""
    log("🔍", "Test 1/7: Checking 5s bucket alignment...")
    data = fetch_dashboard()
    if not data or 'series' not in data:
        check_result(False, "Bucket Alignment", "No series data available")
        return
    
    p95_on = data['series'].get('p95_on', [])
    if len(p95_on) < 2:
        check_result(False, "Bucket Alignment", f"Insufficient data (n={len(p95_on)})")
        return
    
    # Calculate deltas between timestamps
    deltas = []
    for i in range(1, len(p95_on)):
        delta = p95_on[i][0] - p95_on[i-1][0]
        deltas.append(delta)
    
    if not deltas:
        check_result(False, "Bucket Alignment", "No deltas to compute")
        return
    
    # Compute median delta
    deltas.sort()
    median_delta = deltas[len(deltas) // 2]
    
    # Expected: 5000ms ± 1000ms
    aligned = 4000 <= median_delta <= 6000
    check_result(
        aligned,
        "Bucket Alignment",
        f"Median Δ={median_delta}ms (expected ~5000ms)" if aligned
        else f"Misaligned: median Δ={median_delta}ms (expected 4000-6000ms)"
    )


def check_profile_isolation():
    """Test 2: Verify multi-profile independence"""
    log("🔍", "Test 2/7: Checking profile isolation...")
    time.sleep(0.5)  # Brief pause
    
    dashboards = {}
    for profile in ["fast", "quality"]:
        dashboards[profile] = fetch_dashboard(profile)
    
    if not all(dashboards.values()):
        check_result(False, "Profile Isolation", "Failed to fetch profiles")
        return
    
    fast_data = dashboards["fast"]['series'].get('p95_on', [])
    quality_data = dashboards["quality"]['series'].get('p95_on', [])
    
    # Check if data differs
    if len(fast_data) == len(quality_data) and fast_data == quality_data:
        check_result(False, "Profile Isolation", "Same data across profiles (should differ)")
    else:
        check_result(
            True,
            "Profile Isolation",
            f"Independent data (fast={len(fast_data)}, quality={len(quality_data)})"
        )


def check_recall_sufficiency():
    """Test 3: Verify recall data availability"""
    log("🔍", "Test 3/7: Checking recall data sufficiency...")
    time.sleep(0.5)
    
    data = fetch_dashboard()
    if not data or 'series' not in data:
        check_result(False, "Recall Data", "No dashboard data")
        return
    
    recall_on = data['series'].get('recall_on', [])
    recall_off = data['series'].get('recall_off', [])
    
    total = len(recall_on) + len(recall_off)
    sufficient = total >= 5
    
    if sufficient:
        check_result(
            True,
            "Recall Data",
            f"Lines active (on={len(recall_on)}, off={len(recall_off)})"
        )
    else:
        check_result(
            False,
            "Recall Data",
            f"Insufficient data (on={len(recall_on)}, off={len(recall_off)}, need >=5)"
        )


def check_rebuild_throttling():
    """Test 4: Verify background rebuild throttling"""
    log("🔍", "Test 4/7: Checking rebuild throttling (10 rapid requests)...")
    
    # Make 10 rapid requests
    fetch_times = []
    for i in range(10):
        t0 = time.time()
        fetch_dashboard(silent=True)
        fetch_times.append(time.time() - t0)
    
    # If all requests are fast (<0.5s), throttling likely works
    # (no blocking rebuild during requests)
    fast_requests = sum(1 for t in fetch_times if t < 0.5)
    
    if fast_requests >= 8:  # At least 8/10 should be fast
        check_result(
            True,
            "Rebuild Throttling",
            f"Non-blocking: {fast_requests}/10 requests <500ms"
        )
    else:
        check_result(
            False,
            "Rebuild Throttling",
            f"Possible blocking: only {fast_requests}/10 requests were fast"
        )


def check_event_lane():
    """Test 5: Verify event lane population"""
    log("🔍", "Test 5/7: Checking event lane...")
    time.sleep(0.5)
    
    data = fetch_dashboard()
    if not data:
        check_result(False, "Event Lane", "No dashboard data")
        return
    
    events = data.get('events', [])
    
    if len(events) >= 1:
        check_result(True, "Event Lane", f"Populated (n={len(events)})")
    else:
        check_result(
            False,
            "Event Lane",
            "Empty — SLA/AutoTuner may not emit events yet"
        )


def check_tps_p95_correlation():
    """Test 6: Verify TPS and P95 synchronization"""
    log("🔍", "Test 6/7: Checking TPS↔P95 correlation...")
    time.sleep(0.5)
    
    data = fetch_dashboard()
    if not data or 'series' not in data:
        check_result(False, "TPS↔P95 Sync", "No series data")
        return
    
    tps = data['series'].get('tps', [])
    p95_on = data['series'].get('p95_on', [])
    
    if len(tps) < 3 or len(p95_on) < 3:
        check_result(False, "TPS↔P95 Sync", "Insufficient data for correlation")
        return
    
    # Compare last 3 points
    tps_vals = [p[1] for p in tps[-3:]]
    p95_vals = [p[1] for p in p95_on[-3:]]
    
    # Check if both are increasing or both stable
    tps_trend = tps_vals[-1] - tps_vals[0]
    p95_trend = p95_vals[-1] - p95_vals[0]
    
    # Heuristic: if TPS increased >20%, P95 should increase or stay stable
    tps_increased = tps_trend > 0.2 * tps_vals[0] if tps_vals[0] > 0 else False
    
    if tps_increased:
        # Expect P95 to rise or be stable (not drop significantly)
        if p95_trend >= -10:  # Allow small drops
            check_result(True, "TPS↔P95 Sync", "Correlation plausible (TPS↑ → P95 stable/↑)")
        else:
            check_result(
                False,
                "TPS↔P95 Sync",
                f"Unresponsive: TPS↑{tps_trend:.1f} but P95↓{p95_trend:.1f}"
            )
    else:
        # No strong TPS change, just verify data exists
        check_result(True, "TPS↔P95 Sync", "Data present, correlation not testable (low TPS variance)")


def check_mock_mode():
    """Test 7: Check for mock mode fallback"""
    log("🔍", "Test 7/7: Checking mock mode status...")
    time.sleep(0.5)
    
    data = fetch_dashboard()
    if not data:
        check_result(False, "Mock Mode", "No dashboard data")
        return
    
    mock_mode = data.get('mock_mode', False)
    
    if mock_mode:
        check_result(False, "Mock Mode", "Active (Qdrant down or unavailable)")
    else:
        check_result(True, "Mock Mode", "Real DB mode active")


def print_summary():
    """Print final summary report"""
    elapsed = time.time() - start_time
    passed = sum(1 for _, p in results if p)
    total = len(results)
    warning_count = len(warnings)
    
    print("\n" + "="*50)
    print("🏁 DASHBOARD HEALTH SUMMARY")
    print("="*50)
    
    for check_name, passed in results:
        emoji = "✅" if passed else "⚠️"
        print(f"{emoji} {check_name}")
    
    print("-"*50)
    print(f"📊 Score: {passed}/{total} checks passed")
    
    if warning_count > 0:
        print(f"⚠️  {warning_count} potential issue(s) detected:")
        for w in warnings:
            print(f"   • {w}")
    else:
        print("✅ All systems healthy!")
    
    print(f"⏱️  Completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print("="*50)
    
    return 0 if warning_count == 0 else 1


def main():
    """Run all health checks"""
    print("\n" + "="*50)
    print("🚀 DASHBOARD HEALTH CHECK")
    print("="*50)
    log("🔍", "Starting 4-min Dashboard Health Scan...")
    print()
    
    # Pre-flight check
    if not check_api_reachable():
        print("\n❌ Cannot proceed without API access.")
        print("💡 Start the API with: ./launch_real_env.sh")
        return 1
    
    print()
    
    # Run all tests
    try:
        check_bucket_alignment()
        time.sleep(1)
        
        check_profile_isolation()
        time.sleep(1)
        
        check_recall_sufficiency()
        time.sleep(1)
        
        check_rebuild_throttling()
        time.sleep(1)
        
        check_event_lane()
        time.sleep(1)
        
        check_tps_p95_correlation()
        time.sleep(1)
        
        check_mock_mode()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Health check interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    return print_summary()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

