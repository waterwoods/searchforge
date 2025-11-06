#!/usr/bin/env python3
"""
Poll /auto/status every second to monitor AutoTrafficWorker state changes.
Usage: python scripts/poll_auto_status.py [duration_seconds]
"""

import sys
import time
import requests
from datetime import datetime

def poll_status(duration=90, interval=1.0):
    """Poll /auto/status endpoint and log state changes"""
    url = "http://localhost:8084/auto/status"
    prev_state = {}
    
    print(f"{'Timestamp':<20} {'enabled':<8} {'running':<8} {'completed':<10} {'total':<10} {'cycle_sec':<10} {'duration':<10} {'qps':<6} {'next_eta':<9} {'heartbeat':<10} {'last_error':<20}")
    print("=" * 150)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                
                # Extract key fields
                enabled = data.get("enabled", False)
                running = data.get("running", False)
                completed = data.get("completed_cycles", 0)
                total = data.get("total_cycles", "∞")
                cycle_sec = data.get("cycle_sec", 0)
                duration_val = data.get("duration", 0)
                qps = data.get("qps", 0)
                next_eta = data.get("next_eta_sec", 0)
                heartbeat = data.get("heartbeat", 0)
                last_error = data.get("last_error") or "-"
                
                # Detect state changes
                current_state = {
                    "enabled": enabled,
                    "running": running,
                    "completed": completed,
                    "total": total
                }
                
                # Print timestamp
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # Highlight state changes
                marker = ""
                if prev_state:
                    if prev_state.get("enabled") != enabled:
                        marker = "⚠️ ENABLED CHANGED"
                    elif prev_state.get("running") != running:
                        marker = "▶️ RUNNING CHANGED"
                    elif prev_state.get("completed") != completed:
                        marker = "✅ CYCLE COMPLETED"
                
                print(f"{ts:<20} {str(enabled):<8} {str(running):<8} {str(completed):<10} {str(total):<10} {cycle_sec:<10} {duration_val:<10} {qps:<6.1f} {next_eta:<9} {heartbeat:<10} {last_error:<20} {marker}")
                
                prev_state = current_state
            else:
                print(f"{datetime.now().strftime('%H:%M:%S'):<20} ERROR: HTTP {resp.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"{datetime.now().strftime('%H:%M:%S'):<20} ERROR: {str(e)[:50]}")
        except Exception as e:
            print(f"{datetime.now().strftime('%H:%M:%S'):<20} EXCEPTION: {str(e)[:50]}")
        
        time.sleep(interval)
    
    print("\n" + "=" * 150)
    print(f"Polling completed after {duration} seconds")

if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    print(f"Starting AutoTrafficWorker status polling for {duration} seconds...")
    print(f"Monitoring: http://localhost:8084/auto/status\n")
    poll_status(duration)


