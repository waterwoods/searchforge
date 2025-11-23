#!/usr/bin/env python3
"""
kv_experiment_api_smoke.py - Smoke test for KV/Streaming Experiment API

Simple smoke test script that calls POST /api/kv-experiment/run and prints results.
"""

import json
import os
import sys
from pathlib import Path

import requests

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000").rstrip("/")


def main() -> int:
    """Run smoke test for KV experiment API."""
    print("=" * 80)
    print("KV/Streaming Experiment API Smoke Test")
    print("=" * 80)
    
    # Test request
    request_payload = {
        "question": "Find a 2 bedroom place in West LA under $200 per night",
        "collection": "airbnb_la_demo",
        "profile_name": "airbnb_la_location_first",
        "runs_per_mode": 3,
        "filters": {
            "price_max": 200,
            "min_bedrooms": 2,
            "neighbourhood": "Long Beach",
            "room_type": "Entire home/apt"
        }
    }
    
    print(f"\nRequest URL: {RAG_API_URL}/api/kv-experiment/run")
    print(f"Request payload:")
    print(json.dumps(request_payload, indent=2))
    print("\nSending request...")
    
    try:
        response = requests.post(
            f"{RAG_API_URL}/api/kv-experiment/run",
            json=request_payload,
            timeout=300.0,  # 5 minutes timeout for experiment
        )
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return 1
        
        result = response.json()
        
        if not result.get("ok", False):
            print(f"ERROR: Experiment failed")
            print(f"Error: {result.get('error', 'unknown error')}")
            return 1
        
        print("\n" + "=" * 80)
        print("Experiment Results")
        print("=" * 80)
        
        print(f"\nQuestion: {result.get('question')}")
        print(f"Collection: {result.get('collection')}")
        print(f"Profile: {result.get('profile_name')}")
        
        print("\n" + "-" * 80)
        print("Mode Comparison")
        print("-" * 80)
        print(
            f"{'Mode':<20} {'P50(ms)':<12} {'P95(ms)':<12} {'P50-FT(ms)':<14} "
            f"{'Avg Tokens':<12} {'Avg Cost($)':<12} {'KV Hit%':<10} {'Stream Err%':<12}"
        )
        print("-" * 80)
        
        modes = result.get("modes", {})
        for mode_name in ["baseline", "kv_only", "stream_only", "kv_and_stream"]:
            if mode_name not in modes:
                print(f"{mode_name:<20} {'N/A':<12} {'N/A':<12} {'N/A':<14} {'N/A':<12} {'N/A':<12} {'N/A':<10} {'N/A':<12}")
                continue
            
            mode_data = modes[mode_name]
            print(
                f"{mode_name:<20} "
                f"{mode_data.get('p50_ms', 0):<12.1f} "
                f"{mode_data.get('p95_ms', 0):<12.1f} "
                f"{mode_data.get('p50_first_token_ms', 0):<14.1f} "
                f"{mode_data.get('avg_total_tokens', 0):<12.1f} "
                f"{mode_data.get('avg_cost_usd', 0):<12.6f} "
                f"{mode_data.get('kv_hit_rate', 0)*100:<10.2f} "
                f"{mode_data.get('stream_error_rate', 0)*100:<12.2f}"
            )
        
        print("=" * 80)
        
        # Validation: Check that all 4 modes have data
        missing_modes = []
        for mode_name in ["baseline", "kv_only", "stream_only", "kv_and_stream"]:
            if mode_name not in modes:
                missing_modes.append(mode_name)
            elif modes[mode_name].get("num_runs", 0) == 0:
                missing_modes.append(f"{mode_name} (no runs)")
        
        if missing_modes:
            print(f"\nWARNING: Missing or empty modes: {', '.join(missing_modes)}")
            return 1
        
        print("\n✅ All 4 modes have data. Smoke test passed!")
        return 0
        
    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out (experiment took too long)")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Could not connect to {RAG_API_URL}")
        print("Make sure the API server is running.")
        return 1
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())




