#!/usr/bin/env python3
"""
AutoTrafficWorker Diagnostic Tool
Monitors worker status and reports health without modifying any code.
"""

import requests
import time
import sys
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8080"
MONITOR_DURATION = 35  # seconds to monitor for flipping states

def check_api_health():
    """Check if API is running"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=2)
        return resp.ok
    except:
        return False

def get_worker_status():
    """Get current AutoTrafficWorker status"""
    try:
        resp = requests.get(f"{BASE_URL}/auto/status", timeout=2)
        if resp.ok:
            return resp.json()
    except:
        pass
    return None

def check_thread_alive(status):
    """Check if thread is running"""
    # API doesn't expose thread.is_alive() directly
    # Infer from enabled flag and recent activity
    if not status:
        return False, "Status unavailable"
    
    enabled = status.get("enabled", False)
    if not enabled:
        return False, "Worker disabled (enabled=False)"
    
    return True, "Worker thread should be alive (enabled=True)"

def scan_logs_for_auto_messages(max_lines=100):
    """Scan recent log output for [AUTO] messages"""
    # Since FastAPI logs to stdout, we can't easily read them
    # Instead, check if metrics CSV has recent entries
    project_root = Path(__file__).parent.parent
    metrics_csv = project_root / "logs" / "api_metrics.csv"
    
    if not metrics_csv.exists():
        return [], "No metrics CSV found"
    
    try:
        with open(metrics_csv, 'r') as f:
            lines = f.readlines()
        
        if len(lines) <= 1:  # Only header or empty
            return [], "No metrics logged yet"
        
        # Get last few entries
        recent = lines[-min(20, len(lines)-1):]
        return recent, "ok"
    except Exception as e:
        return [], f"Error reading logs: {e}"

def monitor_running_flips(duration=MONITOR_DURATION):
    """Monitor running flag over time to detect flips"""
    print(f"\n🔍 Monitoring worker status for {duration} seconds...")
    print(f"   Looking for 'running' flag transitions (True ↔ False)\n")
    
    samples = []
    start_time = time.time()
    last_running = None
    flip_count = 0
    
    while time.time() - start_time < duration:
        status = get_worker_status()
        if status:
            current_running = status.get("running", False)
            current_enabled = status.get("enabled", False)
            next_eta = status.get("next_eta_sec", -1)
            last_run = status.get("last_run", None)
            
            samples.append({
                "ts": time.time(),
                "enabled": current_enabled,
                "running": current_running,
                "next_eta_sec": next_eta,
                "last_run": last_run
            })
            
            # Detect flip
            if last_running is not None and last_running != current_running:
                flip_count += 1
                transition = "False→True" if current_running else "True→False"
                print(f"   [{datetime.now().strftime('%H:%M:%S')}] 🔄 FLIP detected: running {transition}")
            
            last_running = current_running
        
        time.sleep(1.0)
    
    return samples, flip_count

def print_diagnostic_report(samples, flip_count):
    """Print comprehensive diagnostic report"""
    if not samples:
        print("\n" + "="*60)
        print("⚠️  DIAGNOSTIC REPORT: NO DATA")
        print("="*60)
        print("❌ Could not retrieve worker status")
        print("   Reason: API may be down or /auto/status endpoint unavailable")
        print("="*60)
        return
    
    # Analyze samples
    latest = samples[-1]
    first = samples[0]
    
    enabled = latest["enabled"]
    running = latest["running"]
    next_eta = latest["next_eta_sec"]
    last_run = latest["last_run"]
    
    # Calculate time since last run
    if last_run:
        try:
            from datetime import datetime, timezone
            last_run_dt = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
            now_dt = datetime.now(timezone.utc)
            seconds_since_last = (now_dt - last_run_dt).total_seconds()
        except:
            seconds_since_last = -1
    else:
        seconds_since_last = -1
    
    # Count how many times running was True
    running_true_count = sum(1 for s in samples if s["running"])
    
    # Print report
    print("\n" + "="*60)
    print("🔍 AUTOTRAFFIC WORKER DIAGNOSTIC REPORT")
    print("="*60)
    
    # 1. Thread alive check
    print(f"\n1️⃣ Thread Status:")
    if enabled:
        print(f"   ✅ Thread alive: YES (enabled=True)")
    else:
        print(f"   ❌ Thread alive: NO (enabled=False)")
    
    # 2. Enabled check
    print(f"\n2️⃣ Enabled Flag:")
    if enabled:
        print(f"   ✅ Enabled: TRUE")
    else:
        print(f"   ❌ Enabled: FALSE (worker is stopped)")
    
    # 3. Running flips
    print(f"\n3️⃣ Running Flag Transitions:")
    if flip_count > 0:
        print(f"   ✅ Running flips detected: {flip_count} transitions in {MONITOR_DURATION}s")
        print(f"   ℹ️  running=True occurred {running_true_count} times")
    else:
        if running_true_count > 0:
            print(f"   ⚠️  Running stuck at TRUE (no transitions detected)")
        else:
            print(f"   ⚠️  Running always FALSE (no transitions detected)")
    
    # 4. Last run timestamp
    print(f"\n4️⃣ Last Run Activity:")
    if last_run:
        if seconds_since_last >= 0:
            print(f"   ✅ Last run: {int(seconds_since_last)}s ago")
            print(f"      Timestamp: {last_run}")
        else:
            print(f"   ⚠️  Last run: {last_run} (parse error)")
    else:
        print(f"   ❌ Last run: NEVER (worker hasn't run yet)")
    
    # 5. Dashboard rebuild frequency
    print(f"\n5️⃣ Dashboard Rebuild Schedule:")
    cycle_sec = latest.get("cycle_sec", 20)
    duration_sec = latest.get("duration", 15)
    if next_eta >= 0:
        print(f"   ⏱️  Next run in: {next_eta}s")
        print(f"   ⚙️  Cycle interval: {cycle_sec}s")
        print(f"   ⚙️  Traffic duration: {duration_sec}s per cycle")
        expected_freq = f"every {cycle_sec}s"
        print(f"   📊 Expected rebuild frequency: {expected_freq}")
    else:
        print(f"   ⚠️  Next run: Not scheduled (eta={next_eta})")
    
    # 6. Recent exceptions (check via metrics)
    print(f"\n6️⃣ Recent Exceptions:")
    recent_logs, log_status = scan_logs_for_auto_messages()
    if recent_logs:
        print(f"   ✅ Metrics CSV accessible ({len(recent_logs)} recent entries)")
        print(f"   ℹ️  Check service logs for [AUTO] messages:")
        print(f"      • Look for '[AUTO] Dashboard rebuilt'")
        print(f"      • Look for '[AUTO] run_once error:'")
    else:
        print(f"   ⚠️  {log_status}")
    
    # Final verdict
    print("\n" + "="*60)
    print("📋 FINAL VERDICT:")
    print("="*60)
    
    if not enabled:
        print("⚠️  AutoTrafficWorker is STOPPED")
        print("   Reason: enabled=False")
        print("\n💡 Solution: Call POST /auto/start to enable worker")
    elif flip_count == 0 and running_true_count == 0:
        if last_run:
            print("⚠️  Worker is IDLE but has run before")
            print(f"   Reason: No activity detected, last run {int(seconds_since_last)}s ago")
            print(f"   Next cycle scheduled in {next_eta}s")
        else:
            print("⚠️  Worker is STALLED (never ran)")
            print("   Reason: enabled=True but no executions detected")
            print("\n💡 Possible causes:")
            print("   • Thread died after start")
            print("   • run_canary_parallel.py failing silently")
            print("   • next_run_at never reached")
    elif flip_count == 0 and running_true_count > 0:
        print("⚠️  Worker is STUCK (running=True continuously)")
        print("   Reason: Traffic generation not completing")
        print("\n💡 Possible causes:")
        print("   • subprocess hanging (timeout not working)")
        print("   • run_canary_parallel.py infinite loop")
        print("   • Lock contention preventing running=False")
    elif flip_count > 0:
        print("✅ AutoTrafficWorker is WORKING NORMALLY")
        print(f"   • {flip_count} execution cycles detected in {MONITOR_DURATION}s")
        print(f"   • Last successful run: {int(seconds_since_last)}s ago")
        print(f"   • Next cycle in: {next_eta}s")
        if flip_count >= 2:
            print("\n🎯 Dashboard should be rebuilding regularly every ~20s")
    
    print("="*60 + "\n")

def main():
    print("="*60)
    print("🩺 AutoTrafficWorker Diagnostic Tool")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Monitor duration: {MONITOR_DURATION}s")
    
    # Check API health
    print("\n📡 Checking API health...")
    if not check_api_health():
        print("❌ API is not responding")
        print(f"   Please ensure FastAPI is running on {BASE_URL}")
        print(f"   Start command: cd services/fiqa_api && uvicorn app:app --port 8080")
        sys.exit(1)
    
    print("✅ API is healthy\n")
    
    # Get initial status
    print("📊 Getting initial worker status...")
    initial_status = get_worker_status()
    if initial_status:
        print(f"   enabled: {initial_status.get('enabled')}")
        print(f"   running: {initial_status.get('running')}")
        print(f"   cycle_sec: {initial_status.get('cycle_sec')}")
        print(f"   qps: {initial_status.get('qps')}")
    else:
        print("⚠️  Could not get worker status")
    
    # Monitor for flips
    samples, flip_count = monitor_running_flips()
    
    # Print diagnostic report
    print_diagnostic_report(samples, flip_count)
    
    return 0 if flip_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())


