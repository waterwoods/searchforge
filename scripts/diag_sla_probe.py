#!/usr/bin/env python3
"""
SLA P95 诊断探针 - 定位 Actual P95=0 的根因
"""
import requests
import time
import csv
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE_URL = "http://localhost:8080"
PROJECT_ROOT = Path(__file__).parent.parent
METRICS_CSV = PROJECT_ROOT / "logs" / "api_metrics.csv"

def print_section(title):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_api_health():
    """检查 API 健康"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=2)
        if resp.ok:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API returned {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def get_dashboard_sla():
    """获取 dashboard.json 的 SLA 数据"""
    try:
        # 添加时间戳避免缓存
        resp = requests.get(f"{BASE_URL}/dashboard.json?ts={int(time.time())}", timeout=5)
        if resp.ok:
            data = resp.json()
            sla = data.get('sla', {})
            profile = data.get('profile', 'unknown')
            return {
                'profile': profile,
                'target_p95': sla.get('target_p95', 0),
                'current_p95': sla.get('current_p95', 0)
            }
        else:
            print(f"⚠️  Dashboard API returned {resp.status_code}")
            return None
    except Exception as e:
        print(f"⚠️  Failed to fetch dashboard: {e}")
        return None

def start_auto_traffic():
    """启动 auto-traffic 并等待完成"""
    try:
        print("🚀 Starting auto-traffic (duration=15s, qps=2)...")
        resp = requests.post(
            f"{BASE_URL}/auto/start?cycle=20&duration=15&qps=2",
            timeout=5
        )
        if resp.ok:
            print("✅ Auto-traffic started")
            print("⏳ Waiting 20s for traffic + rebuild cycle...")
            time.sleep(20)
            return True
        else:
            print(f"❌ Failed to start auto-traffic: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error starting auto-traffic: {e}")
        return False

def inspect_csv():
    """检查 CSV 文件内容"""
    if not METRICS_CSV.exists():
        print(f"❌ CSV file not found: {METRICS_CSV}")
        return None
    
    try:
        with open(METRICS_CSV, 'r') as f:
            lines = f.readlines()
        
        total_lines = len(lines) - 1  # 减去 header
        print(f"📊 CSV total rows: {total_lines}")
        
        if total_lines < 1:
            print("❌ No data in CSV")
            return None
        
        # 读取最近10条
        reader = csv.DictReader(lines)
        rows = list(reader)
        recent_10 = rows[-10:] if len(rows) >= 10 else rows
        
        print("\n📋 Recent 10 latency values:")
        latencies = []
        for i, row in enumerate(recent_10, 1):
            # 兼容两种列名
            latency = row.get('p95_ms') or row.get('latency_ms') or row.get('latency', '0')
            timestamp = row.get('timestamp', 'N/A')
            group = row.get('group', 'N/A')
            latencies.append(float(latency))
            print(f"  {i}. {latency} ms (ts={timestamp}, group={group})")
        
        if latencies:
            avg = sum(latencies) / len(latencies)
            print(f"\n💡 Average latency: {avg:.1f} ms")
            return avg
        
        return None
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return None

def rebuild_dashboard():
    """运行 build_dashboard.py"""
    try:
        print("\n🔨 Rebuilding dashboard...")
        build_script = PROJECT_ROOT / "scripts" / "build_dashboard.py"
        result = subprocess.run(
            [sys.executable, str(build_script)],
            timeout=30,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Dashboard rebuilt successfully")
            return True
        else:
            print(f"⚠️  Dashboard rebuild returned code {result.returncode}")
            if result.stderr:
                print(f"   stderr: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error rebuilding dashboard: {e}")
        return False

def main():
    print("🔍 SLA P95 Diagnostic Probe")
    print("=" * 60)
    
    # Step 1: Check API health
    print_section("Step 1: API Health Check")
    if not check_api_health():
        print("\n❌ [FAIL] API not available")
        return 1
    
    # Step 2: Get baseline dashboard state
    print_section("Step 2: Baseline Dashboard State")
    baseline = get_dashboard_sla()
    if baseline:
        print(f"📊 Profile: {baseline['profile']}")
        print(f"📊 Target P95: {baseline['target_p95']} ms")
        print(f"📊 Current P95 (before): {baseline['current_p95']} ms")
        if baseline['current_p95'] == 0:
            print("⚠️  Current P95 is ZERO (this is the problem)")
    
    # Step 3: Generate traffic
    print_section("Step 3: Generate Traffic")
    if not start_auto_traffic():
        print("\n❌ [FAIL] Could not generate traffic")
        return 1
    
    # Step 4: Inspect CSV
    print_section("Step 4: Inspect CSV Metrics")
    avg_latency = inspect_csv()
    
    # Step 5: Rebuild dashboard
    print_section("Step 5: Rebuild Dashboard")
    if not rebuild_dashboard():
        print("\n⚠️  Dashboard rebuild had issues, but continuing...")
    
    # Wait a moment for file to be written
    time.sleep(2)
    
    # Step 6: Check dashboard again
    print_section("Step 6: Verify Dashboard Update")
    after = get_dashboard_sla()
    if after:
        print(f"📊 Profile: {after['profile']}")
        print(f"📊 Target P95: {after['target_p95']} ms")
        print(f"📊 Current P95 (after): {after['current_p95']} ms")
        
        print_section("RESULTS")
        if after['current_p95'] > 0:
            print(f"✅ [OK] current_p95 = {after['current_p95']} ms")
            print(f"💡 P95 changed: {baseline['current_p95']} → {after['current_p95']}")
            return 0
        else:
            print(f"❌ [FAIL] current_p95 still ZERO")
            print("\n🔍 Root cause analysis:")
            print("   - CSV has data?", "YES" if avg_latency else "NO")
            print("   - Dashboard rebuild?", "YES")
            print("   - Likely issue: build_dashboard.py not computing current_p95 correctly")
            print("\n💡 Next steps:")
            print("   1. Check build_dashboard.py has compute_current_p95() function")
            print("   2. Verify CSV column names (latency_ms vs p95_ms)")
            print("   3. Check time window filter (5min window may be too narrow)")
            return 1
    else:
        print("❌ [FAIL] Could not fetch dashboard after rebuild")
        return 1

if __name__ == "__main__":
    sys.exit(main())
