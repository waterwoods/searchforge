#!/usr/bin/env python3
"""
verify_vitals_e2e_post.py - End-to-end verification of vitals POST mode

Verifies that the vitals generator script can successfully POST data to the API
and that the data appears in the GET /api/vitals/latest endpoint.

Usage:
    python3 scripts/verify_vitals_e2e_post.py --endpoint-base http://localhost:8000
"""

import argparse
import json
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_latest_readings(endpoint_base: str, limit: int = 200) -> Tuple[List[Dict], Optional[str]]:
    """
    Fetch latest readings from API.
    
    Returns:
        (readings_list, error_message)
    """
    url = f"{endpoint_base}/api/vitals/latest?limit={limit}"
    try:
        req = Request(url, method='GET')
        with urlopen(req, timeout=5) as response:
            if response.status != 200:
                return [], f"HTTP {response.status}"
            data = json.loads(response.read().decode('utf-8'))
            readings = data.get('readings', [])
            return readings, None
    except HTTPError as e:
        return [], f"HTTP error {e.code}: {e.reason}"
    except URLError as e:
        return [], f"URL error: {e.reason}"
    except json.JSONDecodeError as e:
        return [], f"JSON decode error: {e}"
    except Exception as e:
        return [], f"Unexpected error: {e}"


def get_baseline(endpoint_base: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Get baseline reading (newest id and timestamp).
    
    Returns:
        (baseline_id, baseline_time_ms, error_message)
    """
    readings, error = get_latest_readings(endpoint_base, limit=50)
    if error:
        return None, None, error
    
    if not readings:
        # No existing readings, use 0 as baseline
        return 0, 0, None
    
    # Find newest reading
    newest = readings[0]  # API returns newest first
    baseline_id = newest.get('id', 0)
    baseline_time_ms = newest.get('time_ms') or 0
    
    return baseline_id, baseline_time_ms, None


def count_new_readings(
    endpoint_base: str,
    source: str,
    baseline_id: int,
    baseline_time_ms: int,
    max_polls: int = 10,
    poll_interval: float = 0.5
) -> Tuple[int, Optional[str], Optional[Dict]]:
    """
    Poll API and count new readings matching criteria.
    
    Returns:
        (count, error_message, newest_reading)
    """
    new_count = 0
    newest_reading = None
    
    for poll_num in range(max_polls):
        readings, error = get_latest_readings(endpoint_base, limit=200)
        if error:
            return 0, error, None
        
        # Count readings matching criteria
        for reading in readings:
            reading_source = reading.get('source', '')
            reading_id = reading.get('id', 0)
            reading_time_ms = reading.get('time_ms') or 0
            
            # Check if this reading is new and matches source
            is_new = (
                reading_source == source and
                (reading_id > baseline_id or reading_time_ms > baseline_time_ms)
            )
            
            if is_new:
                new_count += 1
                if newest_reading is None or reading_id > newest_reading.get('id', 0):
                    newest_reading = reading
        
        # If we found new readings, wait a bit more to ensure all are captured
        if new_count > 0 and poll_num < max_polls - 1:
            time.sleep(poll_interval)
        elif poll_num < max_polls - 1:
            time.sleep(poll_interval)
    
    return new_count, None, newest_reading


def run_generator(
    endpoint_base: str,
    duration_sec: float,
    interval_sec: float,
    source: str
) -> Tuple[bool, str, str]:
    """
    Run the generator script as subprocess.
    
    Returns:
        (success, stdout, stderr)
    """
    endpoint = f"{endpoint_base}/api/vitals/ingest"
    cmd = [
        sys.executable,
        'scripts/generate_vitals_stream.py',
        '--mode', 'post',
        '--endpoint', endpoint,
        '--duration-sec', str(duration_sec),
        '--interval-sec', str(interval_sec),
        '--source', source,
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration_sec + 10,  # Add buffer for cleanup
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, '', 'Generator script timed out'
    except Exception as e:
        return False, '', f"Failed to run generator: {e}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="End-to-end verification of vitals POST mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        '--endpoint-base',
        type=str,
        default='http://localhost:8000',
        help='Base URL of API endpoint (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--duration-sec',
        type=float,
        default=10.0,
        help='Duration to run generator (default: 10.0)'
    )
    parser.add_argument(
        '--interval-sec',
        type=float,
        default=1.0,
        help='Interval between readings (default: 1.0)'
    )
    parser.add_argument(
        '--source',
        type=str,
        default='e2e-test',
        help='Source identifier for test readings (default: e2e-test)'
    )
    parser.add_argument(
        '--min-new',
        type=int,
        default=5,
        help='Minimum new readings expected (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Step A: Get baseline
    print(f"[Step A] Getting baseline from {args.endpoint_base}/api/vitals/latest...", flush=True)
    baseline_id, baseline_time_ms, error = get_baseline(args.endpoint_base)
    if error:
        print(f"❌ FAIL: Cannot connect to API: {error}", file=sys.stderr)
        print(f"   Make sure the API is running at {args.endpoint_base}", file=sys.stderr)
        print(f"   Check: curl {args.endpoint_base}/healthz", file=sys.stderr)
        sys.exit(2)
    
    print(f"   Baseline: id={baseline_id}, time_ms={baseline_time_ms}")
    
    # Step B: Run generator
    print(f"\n[Step B] Running generator (POST mode, {args.duration_sec}s, interval {args.interval_sec}s)...")
    success, stdout, stderr = run_generator(
        args.endpoint_base,
        args.duration_sec,
        args.interval_sec,
        args.source
    )
    
    if not success:
        print(f"❌ FAIL: Generator failed", file=sys.stderr)
        if stderr:
            print(f"   stderr: {stderr}", file=sys.stderr)
        if stdout:
            print(f"   stdout: {stdout}", file=sys.stderr)
        sys.exit(1)
    
    print(f"   Generator completed successfully")
    if stderr:
        print(f"   Generator stderr: {stderr}")
    
    # Step C: Poll and count new readings
    print(f"\n[Step C] Polling for new readings (source={args.source})...")
    time.sleep(0.5)  # Brief wait for API to process
    
    new_count, error, newest_reading = count_new_readings(
        args.endpoint_base,
        args.source,
        baseline_id,
        baseline_time_ms,
        max_polls=10,
        poll_interval=0.5
    )
    
    if error:
        print(f"❌ FAIL: Error polling API: {error}", file=sys.stderr)
        sys.exit(1)
    
    print(f"   Found {new_count} new readings (min required: {args.min_new})")
    
    # Step D: PASS/FAIL determination
    print(f"\n[Step D] Verification Result:")
    print("=" * 60)
    
    if new_count >= args.min_new:
        print(f"✅ PASS")
        print(f"   New readings: {new_count} (required: {args.min_new})")
        if newest_reading:
            print(f"   Newest reading: id={newest_reading.get('id')}, "
                  f"hr={newest_reading.get('hr')}, "
                  f"spo2={newest_reading.get('spo2')}, "
                  f"source={newest_reading.get('source')}")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"❌ FAIL")
        print(f"   New readings: {new_count} (required: {args.min_new})")
        print(f"   Expected at least {args.min_new} new readings with source='{args.source}'")
        if newest_reading:
            print(f"   Newest reading found: id={newest_reading.get('id')}, "
                  f"source={newest_reading.get('source')}")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
