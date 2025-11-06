#!/usr/bin/env python3
"""
Validation script for canary test setup
Checks all components are working correctly
"""

import sys
import requests
import csv
from pathlib import Path
from datetime import datetime


def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get("http://localhost:8080/health", timeout=2)
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API health check failed: status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        print("   Run: bash launch.sh")
        return False


def check_search_endpoint():
    """Test search endpoint with mode parameter"""
    try:
        # Test mode=on
        response_on = requests.get(
            "http://localhost:8080/search",
            params={"query": "What is an ETF?", "mode": "on"},
            timeout=5
        )
        
        # Test mode=off
        response_off = requests.get(
            "http://localhost:8080/search",
            params={"query": "What is an ETF?", "mode": "off"},
            timeout=5
        )
        
        if response_on.status_code == 200 and response_off.status_code == 200:
            data_on = response_on.json()
            data_off = response_off.json()
            
            print(f"✅ Search endpoint working")
            print(f"   mode=on:  {data_on.get('latency_ms', 0):.1f}ms, {len(data_on.get('answers', []))} results")
            print(f"   mode=off: {data_off.get('latency_ms', 0):.1f}ms, {len(data_off.get('answers', []))} results")
            return True
        else:
            print(f"❌ Search endpoint failed")
            print(f"   mode=on status: {response_on.status_code}")
            print(f"   mode=off status: {response_off.status_code}")
            return False
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
        return False


def check_metrics_csv():
    """Check if metrics CSV is being written with correct format"""
    root = Path(__file__).parent.parent
    csv_paths = [
        root / "services" / "fiqa_api" / "logs" / "api_metrics.csv",
        root / "logs" / "api_metrics.csv"
    ]
    
    for csv_path in csv_paths:
        if csv_path.exists():
            try:
                with open(csv_path, newline='') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    
                    # Check required columns
                    required = ["timestamp", "p95_ms", "recall_at10", "group"]
                    missing = [col for col in required if col not in headers]
                    
                    if missing:
                        print(f"⚠️  CSV missing columns: {missing}")
                        print(f"   Headers: {headers}")
                        return False
                    
                    # Read recent rows
                    rows = list(reader)
                    if not rows:
                        print(f"⚠️  CSV is empty: {csv_path}")
                        print("   Run a few search requests first")
                        return False
                    
                    recent_rows = rows[-10:] if len(rows) > 10 else rows
                    
                    # Check for mode/group values
                    modes = [row.get("group", row.get("mode", "")) for row in recent_rows]
                    has_on = any("on" in m.lower() for m in modes)
                    has_off = any("off" in m.lower() for m in modes)
                    
                    # Check recall values
                    recalls = [float(row.get("recall_at10", 0)) for row in recent_rows if row.get("recall_at10")]
                    
                    print(f"✅ Metrics CSV found: {csv_path}")
                    print(f"   Total rows: {len(rows)}")
                    print(f"   Recent recalls: min={min(recalls):.3f}, max={max(recalls):.3f}, avg={sum(recalls)/len(recalls):.3f}")
                    print(f"   Has mode=on: {has_on}, mode=off: {has_off}")
                    
                    if not recalls or all(r == 0 for r in recalls):
                        print(f"⚠️  Recall values are all zero - may need API restart")
                    
                    return True
                    
            except Exception as e:
                print(f"❌ Error reading CSV: {e}")
                return False
    
    print(f"❌ No metrics CSV found")
    print(f"   Expected: {csv_paths[0]}")
    return False


def check_reports_directory():
    """Check reports directory exists"""
    root = Path(__file__).parent.parent
    reports_dir = root / "reports"
    
    if reports_dir.exists():
        print(f"✅ Reports directory exists: {reports_dir}")
        
        # List existing files
        files = list(reports_dir.glob("*.json"))
        if files:
            print(f"   Existing reports: {len(files)} files")
            for f in sorted(files)[-5:]:
                print(f"     - {f.name}")
        
        return True
    else:
        print(f"⚠️  Reports directory missing (will be created automatically)")
        reports_dir.mkdir(exist_ok=True)
        return True


def check_query_files():
    """Check if query files exist"""
    root = Path(__file__).parent.parent
    query_files = [
        root / "data" / "fiqa_queries.txt",
        root / "data" / "fiqa" / "queries.jsonl"
    ]
    
    found = False
    for query_file in query_files:
        if query_file.exists():
            with open(query_file) as f:
                lines = [line.strip() for line in f if line.strip()]
                if len(lines) > 0:
                    print(f"✅ Query file found: {query_file}")
                    print(f"   Queries: {len(lines)}")
                    found = True
                    break
    
    if not found:
        print(f"⚠️  No query files found (will use built-in queries)")
    
    return True


def check_canary_script():
    """Check canary script exists and is executable"""
    script_path = Path(__file__).parent / "run_canary_30min.py"
    
    if not script_path.exists():
        print(f"❌ Canary script not found: {script_path}")
        return False
    
    print(f"✅ Canary script exists: {script_path}")
    print(f"   Size: {script_path.stat().st_size} bytes")
    
    # Check if executable
    if script_path.stat().st_mode & 0o111:
        print(f"   Executable: yes")
    else:
        print(f"   Executable: no (run: chmod +x {script_path})")
    
    return True


def check_dashboard_script():
    """Check build_dashboard script exists"""
    script_path = Path(__file__).parent / "build_dashboard.py"
    
    if not script_path.exists():
        print(f"❌ Dashboard script not found: {script_path}")
        return False
    
    print(f"✅ Dashboard script exists: {script_path}")
    return True


def main():
    print("🔍 Validating Canary Test Setup")
    print("=" * 70)
    
    checks = [
        ("API Health", check_api_health),
        ("Search Endpoint", check_search_endpoint),
        ("Metrics CSV", check_metrics_csv),
        ("Reports Directory", check_reports_directory),
        ("Query Files", check_query_files),
        ("Canary Script", check_canary_script),
        ("Dashboard Script", check_dashboard_script),
    ]
    
    results = []
    for name, check_fn in checks:
        print()
        try:
            result = check_fn()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print()
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("🎉 All checks passed! Ready to run canary test:")
        print()
        print("  # Quick test (30 seconds)")
        print("  python scripts/test_canary_quick.py")
        print()
        print("  # Full test (30 minutes)")
        print("  python scripts/run_canary_30min.py")
        print()
        return 0
    else:
        print()
        print("⚠️  Some checks failed. Fix issues above before running canary test.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())




