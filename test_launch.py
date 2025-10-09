#!/usr/bin/env python3
"""
Simple test script for launch.sh service validation
"""
import requests
import sys
from pathlib import Path

BASE_URL = "http://localhost:8080"
METRICS_FILE = Path("services/fiqa_api/logs/api_metrics.csv")

def test_health_endpoint():
    """Test /health endpoint returns 200"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, f"Health check failed: {response.status_code}"
    print(f"✅ /health endpoint: {response.status_code} OK")
    return response

def test_search_endpoint():
    """Test /search endpoint returns 200"""
    payload = {"query": "How to invest in stocks?", "top_k": 5}
    response = requests.post(f"{BASE_URL}/search", json=payload)
    assert response.status_code == 200, f"Search failed: {response.status_code}"
    print(f"✅ /search endpoint: {response.status_code} OK")
    return response

def test_metrics_endpoint():
    """Test /metrics endpoint returns 200"""
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200, f"Metrics failed: {response.status_code}"
    print(f"✅ /metrics endpoint: {response.status_code} OK")
    print(f"   Metrics: {response.json()}")
    return response

def test_metrics_file():
    """Test logs/api_metrics.csv exists and has >1 lines"""
    assert METRICS_FILE.exists(), f"Metrics file not found: {METRICS_FILE}"
    
    lines = METRICS_FILE.read_text().strip().split('\n')
    assert len(lines) > 1, f"Metrics file has only {len(lines)} line(s), expected >1"
    
    print(f"✅ Metrics file exists: {METRICS_FILE}")
    print(f"✅ Metrics file has {len(lines)} lines (header + data)")
    return lines

def main():
    print("🧪 Running launch.sh service tests...\n")
    
    try:
        # Test all endpoints
        test_health_endpoint()
        test_search_endpoint()
        test_metrics_endpoint()
        
        # Test metrics file
        lines = test_metrics_file()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
        
        # Show sample metrics
        print("\n📊 Sample metrics (last 3 lines):")
        for line in lines[-3:]:
            print(f"  {line[:80]}{'...' if len(line) > 80 else ''}")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {BASE_URL}")
        print("   Make sure launch.sh is running on port 8080")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

