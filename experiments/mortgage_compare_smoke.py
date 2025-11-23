#!/usr/bin/env python3
"""
mortgage_compare_smoke.py - Mortgage Property Comparison Smoke Test

Minimal smoke test for POST /api/mortgage-agent/compare endpoint.

Usage:
    python experiments/mortgage_compare_smoke.py [--base-url http://localhost:8000]
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8000"

# Test borrower profile
TEST_BORROWER = {
    "income": 150000,
    "monthly_debts": 500,
    "down_payment_pct": 0.20,
    "state": "WA"
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_properties(base_url: str) -> List[Dict[str, Any]]:
    """
    Get sample properties from API.
    
    Args:
        base_url: API base URL
        
    Returns:
        List of property dictionaries
    """
    import requests
    
    url = f"{base_url}/api/mortgage-agent/properties"
    
    try:
        response = requests.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Failed to connect to {url}", file=sys.stderr)
        print(f"   Make sure the API server is running. Try:", file=sys.stderr)
        print(f"   - Check if server is running on a different port (default: 8011)", file=sys.stderr)
        print(f"   - Start server: cd services/fiqa_api && ./start_server.sh", file=sys.stderr)
        raise
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get properties: {e}", file=sys.stderr)
        raise


def call_compare_api(base_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call /api/mortgage-agent/compare API.
    
    Args:
        base_url: API base URL
        payload: Request payload
        
    Returns:
        dict: API response
    """
    import requests
    
    url = f"{base_url}/api/mortgage-agent/compare"
    
    try:
        start_time = time.perf_counter()
        response = requests.post(url, json=payload, timeout=30.0)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        response.raise_for_status()
        data = response.json()
        
        # Add measured latency
        data["_measured_latency_ms"] = elapsed_ms
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ API call failed: {e}", file=sys.stderr)
        raise


def format_property_comparison(entry: Dict[str, Any], index: int) -> str:
    """
    Format property comparison entry for display.
    
    Args:
        entry: Property comparison entry dictionary
        index: Entry index (1-based)
        
    Returns:
        str: Formatted string
    """
    parts = []
    prop = entry.get("property", {})
    metrics = entry.get("metrics", {})
    
    parts.append(f"\n  Property {index}: {prop.get('display_name', 'Unknown')}")
    parts.append(f"    Property ID: {prop.get('property_id', 'N/A')}")
    parts.append(f"    City: {prop.get('city', 'N/A')}")
    parts.append(f"    State: {prop.get('state', 'N/A')}")
    parts.append(f"    Listing Price: ${prop.get('listing_price', 0):,.0f}")
    parts.append(f"    Monthly Payment: ${metrics.get('monthly_payment', 0):,.2f}")
    parts.append(f"    DTI Ratio: {metrics.get('dti_ratio', 0):.2%}")
    parts.append(f"    Risk Level: {metrics.get('risk_level', 'unknown').upper()}")
    parts.append(f"    Within Affordability: {'✅ Yes' if metrics.get('within_affordability') else '❌ No'}")
    
    dti_excess = metrics.get('dti_excess_pct')
    if dti_excess is not None:
        if dti_excess > 0:
            parts.append(f"    DTI Excess: +{dti_excess:.1%} above target")
        else:
            parts.append(f"    DTI Excess: {dti_excess:.1%} (below target)")
    
    return "\n".join(parts)


def print_response(data: Dict[str, Any]) -> None:
    """
    Print API response in a readable format.
    
    Args:
        data: API response dictionary
    """
    print("=" * 80)
    print("Mortgage Property Comparison API Response")
    print("=" * 80)
    
    # Status
    ok = data.get("ok", False)
    status_icon = "✅" if ok else "❌"
    print(f"\n{status_icon} Status: {'OK' if ok else 'ERROR'}")
    
    if not ok:
        error = data.get("error", "Unknown error")
        print(f"   Error: {error}")
        return
    
    # Borrower profile summary
    borrower_summary = data.get("borrower_profile_summary", "")
    if borrower_summary:
        print(f"\n👤 Borrower Profile:")
        print(f"   {borrower_summary}")
    
    # Target DTI
    target_dti = data.get("target_dti", 0)
    print(f"\n📊 Target DTI: {target_dti:.1%}")
    
    # Max affordability
    max_affordability = data.get("max_affordability")
    if max_affordability:
        print(f"\n💰 Max Affordability Summary:")
        print(f"   Max Monthly Payment: ${max_affordability.get('max_monthly_payment', 0):,.2f}")
        print(f"   Max Loan Amount: ${max_affordability.get('max_loan_amount', 0):,.0f}")
        print(f"   Max Home Price: ${max_affordability.get('max_home_price', 0):,.0f}")
        print(f"   Assumed Interest Rate: {max_affordability.get('assumed_interest_rate', 0):.2f}%")
        print(f"   Target DTI: {max_affordability.get('target_dti', 0):.1%}")
    else:
        print(f"\n⚠️  Max Affordability: Not computed")
    
    # Properties comparison
    properties = data.get("properties", [])
    if properties:
        print(f"\n🏠 Property Comparison ({len(properties)} properties):")
        for idx, entry in enumerate(properties, 1):
            print(format_property_comparison(entry, idx))
    else:
        print("\n⚠️  No properties in comparison result")
    
    # Best property
    best_property_id = data.get("best_property_id")
    if best_property_id:
        print(f"\n⭐ Best Property ID: {best_property_id}")
        # Find and display best property details
        for entry in properties:
            if entry.get("property", {}).get("property_id") == best_property_id:
                prop = entry.get("property", {})
                print(f"   Name: {prop.get('display_name', 'N/A')}")
                print(f"   Price: ${prop.get('listing_price', 0):,.0f}")
                break
    else:
        print(f"\n⚠️  Best Property: Not determined")
    
    # Latency
    latency_ms = data.get("_measured_latency_ms")
    if latency_ms:
        print(f"\n⏱️  Latency: {latency_ms:.1f} ms")
    
    print("\n" + "=" * 80)


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Smoke test for Mortgage Property Comparison API"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--property-ids",
        type=str,
        nargs=2,
        default=None,
        help="Two property IDs to compare (default: auto-select cheapest and most expensive)"
    )
    
    args = parser.parse_args()
    
    # Get properties
    print("=" * 80)
    print("Mortgage Property Comparison Smoke Test")
    print("=" * 80)
    print(f"\n📍 Base URL: {args.base_url}")
    print(f"📝 Endpoint: POST /api/mortgage-agent/compare")
    
    try:
        print("\n📋 Fetching sample properties...")
        properties = get_properties(args.base_url)
        print(f"   Found {len(properties)} properties")
        
        if len(properties) < 2:
            print(f"❌ Need at least 2 properties, got {len(properties)}", file=sys.stderr)
            sys.exit(1)
        
        # Select property IDs
        if args.property_ids:
            property_ids = args.property_ids
        else:
            # Auto-select: cheapest and most expensive
            sorted_props = sorted(properties, key=lambda p: p.get("purchase_price", 0))
            property_ids = [
                sorted_props[0].get("id"),
                sorted_props[-1].get("id")
            ]
            print(f"\n📋 Auto-selected properties:")
            print(f"   Property 1 (cheapest): {sorted_props[0].get('name')} (${sorted_props[0].get('purchase_price', 0):,.0f})")
            print(f"   Property 2 (most expensive): {sorted_props[-1].get('name')} (${sorted_props[-1].get('purchase_price', 0):,.0f})")
        
        # Build payload
        payload = {
            **TEST_BORROWER,
            "property_ids": property_ids
        }
        
        print(f"\n📤 Request Payload:")
        print(json.dumps(payload, indent=2))
        print()
        
        # Call API
        data = call_compare_api(args.base_url, payload)
        print_response(data)
        
        # Check if OK
        if not data.get("ok", False):
            print("\n❌ Test FAILED: Response indicates error", file=sys.stderr)
            sys.exit(1)
        
        # Check if properties were compared
        properties = data.get("properties", [])
        if not properties:
            print("\n⚠️  Test WARNING: No properties in comparison result", file=sys.stderr)
            sys.exit(0)
        
        print("\n✅ Test PASSED")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

