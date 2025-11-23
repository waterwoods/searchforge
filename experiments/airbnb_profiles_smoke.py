#!/usr/bin/env python3
"""
Smoke test for search profiles functionality.

Tests:
1. Baseline request (no profile, no filters) - should use default behavior
2. Profile request (profile_name specified, no filters) - should use profile defaults
3. Profile + override request (profile_name + explicit filters) - should override profile defaults
"""
import requests
import json
import sys

def test_baseline():
    """Test query without profile (baseline behavior)."""
    url = "http://localhost:8000/api/query"
    payload = {
        "question": "test baseline query",
        "top_k": 5,
        "collection": "airbnb_la_demo"
    }
    
    print(f"\n{'='*70}")
    print("TEST 1: Baseline (no profile, no filters)")
    print(f"{'='*70}\n")
    print("REQUEST PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"STATUS CODE: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"ERROR: Non-200 status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        
        print("RESPONSE ANALYSIS:")
        print("-" * 70)
        print(f"Collection used: {data.get('params', {}).get('collection', 'N/A')}")
        print(f"Trace ID: {data.get('trace_id', 'N/A')}")
        print(f"Results count: {len(data.get('sources', []))}")
        print()
        
        # Check backend logs for profile_name (should be None)
        print("Expected in backend logs:")
        print("  profile_name=None")
        print()
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server at http://localhost:8000")
        print("Make sure the backend is running.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_profile_defaults():
    """Test query with profile but no explicit filters."""
    url = "http://localhost:8000/api/query"
    payload = {
        "question": "test profile with defaults",
        "top_k": 5,
        "profile_name": "airbnb_la_location_first"
        # No collection, no filters - should use profile defaults
    }
    
    print(f"\n{'='*70}")
    print("TEST 2: Profile with defaults (profile_name specified, no filters)")
    print(f"{'='*70}\n")
    print("REQUEST PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"STATUS CODE: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"ERROR: Non-200 status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        
        print("RESPONSE ANALYSIS:")
        print("-" * 70)
        print(f"Collection used: {data.get('params', {}).get('collection', 'N/A')}")
        print(f"Trace ID: {data.get('trace_id', 'N/A')}")
        print(f"Results count: {len(data.get('sources', []))}")
        print()
        
        # Check backend logs for effective parameters
        print("Expected in backend logs:")
        print("  profile_name=airbnb_la_location_first")
        print("  effective_collection=airbnb_la_demo")
        print("  effective_price_max=200.0")
        print("  effective_min_bedrooms=1")
        print()
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server at http://localhost:8000")
        print("Make sure the backend is running.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_profile_override():
    """Test query with profile and explicit filters (override profile defaults)."""
    url = "http://localhost:8000/api/query"
    payload = {
        "question": "test profile with override",
        "top_k": 5,
        "profile_name": "airbnb_la_location_first",
        "price_max": 150.0  # Override profile default (200.0)
        # Should use profile collection (airbnb_la_demo) but override price_max
    }
    
    print(f"\n{'='*70}")
    print("TEST 3: Profile with override (profile_name + explicit filters)")
    print(f"{'='*70}\n")
    print("REQUEST PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"STATUS CODE: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"ERROR: Non-200 status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        
        print("RESPONSE ANALYSIS:")
        print("-" * 70)
        print(f"Collection used: {data.get('params', {}).get('collection', 'N/A')}")
        print(f"Trace ID: {data.get('trace_id', 'N/A')}")
        print(f"Results count: {len(data.get('sources', []))}")
        print()
        
        # Check backend logs for effective parameters
        print("Expected in backend logs:")
        print("  profile_name=airbnb_la_location_first")
        print("  effective_collection=airbnb_la_demo")
        print("  effective_price_max=150.0  (overridden from profile default 200.0)")
        print("  effective_min_bedrooms=1  (from profile default)")
        print()
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server at http://localhost:8000")
        print("Make sure the backend is running.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_filter_verification():
    """Test that filters are actually applied (verify results match filter criteria)."""
    url = "http://localhost:8000/api/query"
    payload = {
        "question": "affordable apartment in Long Beach",
        "top_k": 10,
        "profile_name": "airbnb_la_location_first",
        "price_max": 200.0,
        "min_bedrooms": 2,
        "neighbourhood": "Long Beach",
    }
    
    print(f"\n{'='*70}")
    print("TEST 4: Filter Verification (verify filters are applied)")
    print(f"{'='*70}\n")
    print("REQUEST PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    print("EXPECTED FILTERS:")
    print("  - price <= 200.0")
    print("  - bedrooms >= 2")
    print("  - neighbourhood = 'Long Beach' (case-insensitive)")
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"STATUS CODE: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"ERROR: Non-200 status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        sources = data.get('sources', [])
        
        print("RESPONSE ANALYSIS:")
        print("-" * 70)
        print(f"Results count: {len(sources)}")
        print()
        
        # Verify filter compliance for first 3 results
        print("VERIFICATION (first 3 results):")
        print("-" * 70)
        violations = []
        for i, source in enumerate(sources[:3], 1):
            price = source.get('price')
            bedrooms = source.get('bedrooms')
            neighbourhood = source.get('neighbourhood', '')
            
            print(f"\nResult {i}:")
            print(f"  price: {price}")
            print(f"  bedrooms: {bedrooms}")
            print(f"  neighbourhood: {neighbourhood}")
            
            # Check violations
            if price is not None and price > 200.0:
                violations.append(f"Result {i}: price {price} > 200.0")
            if bedrooms is not None and bedrooms < 2:
                violations.append(f"Result {i}: bedrooms {bedrooms} < 2")
            if neighbourhood and neighbourhood.lower() != "long beach":
                # Note: neighbourhood filter might not match exactly due to data format
                print(f"  ⚠️  neighbourhood mismatch (expected 'Long Beach', got '{neighbourhood}')")
        
        print()
        if violations:
            print("❌ FILTER VIOLATIONS DETECTED:")
            for v in violations:
                print(f"  - {v}")
        else:
            print("✅ All results comply with filters (price <= 200, bedrooms >= 2)")
        print()
        
        # Check backend logs
        print("Expected in backend logs:")
        print("  [FILTER] collection=airbnb_la_demo filter_used=True")
        print()
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server at http://localhost:8000")
        print("Make sure the backend is running.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_no_filter_baseline():
    """Test query without filters to compare with filtered results."""
    url = "http://localhost:8000/api/query"
    payload = {
        "question": "affordable apartment in Long Beach",
        "top_k": 10,
        "collection": "airbnb_la_demo",
        # No profile, no filters - should return all results
    }
    
    print(f"\n{'='*70}")
    print("TEST 5: No Filter Baseline (compare with filtered results)")
    print(f"{'='*70}\n")
    print("REQUEST PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    print("NOTE: This test shows results WITHOUT filters for comparison.")
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"STATUS CODE: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"ERROR: Non-200 status code: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        sources = data.get('sources', [])
        
        print("RESPONSE ANALYSIS:")
        print("-" * 70)
        print(f"Results count: {len(sources)}")
        print()
        
        # Show first 3 results for comparison
        print("SAMPLE RESULTS (first 3, no filters):")
        print("-" * 70)
        for i, source in enumerate(sources[:3], 1):
            price = source.get('price', 'N/A')
            bedrooms = source.get('bedrooms', 'N/A')
            neighbourhood = source.get('neighbourhood', 'N/A')
            
            print(f"\nResult {i}:")
            print(f"  price: {price}")
            print(f"  bedrooms: {bedrooms}")
            print(f"  neighbourhood: {neighbourhood}")
        
        print()
        print("Compare with TEST 4 results to verify filter effect.")
        print()
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server at http://localhost:8000")
        print("Make sure the backend is running.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Run all smoke tests."""
    print("\n" + "="*70)
    print("SEARCH PROFILES SMOKE TEST")
    print("="*70)
    print("\nThis test verifies:")
    print("1. Baseline behavior (no profile)")
    print("2. Profile defaults (profile_name only)")
    print("3. Profile + override (profile_name + explicit filters)")
    print("4. Filter verification (verify filters are applied)")
    print("5. No filter baseline (compare with filtered results)")
    print("\nNOTE: Check backend logs for effective parameters and filter usage.")
    print("="*70)
    
    test_baseline()
    test_profile_defaults()
    test_profile_override()
    test_filter_verification()
    test_no_filter_baseline()
    
    print("\n" + "="*70)
    print("SMOKE TEST COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Check backend logs to verify effective parameters")
    print("2. Verify profile merging logic is working correctly")
    print("3. Confirm request parameters override profile defaults")
    print("4. Verify Qdrant filters are applied (check [FILTER] logs)")
    print("5. Compare TEST 4 and TEST 5 results to confirm filter effect")
    print("="*70)


if __name__ == "__main__":
    main()

