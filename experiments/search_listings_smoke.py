#!/usr/bin/env python3
"""
search_listings_smoke.py - Smoke test for local listings search

Run from project root:
    cd /home/andy/searchforge
    python3 experiments/search_listings_smoke.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage.tools.property_tool import search_listings_for_zip


def print_listing(listing):
    """Print a single listing in a readable format."""
    hoa_str = f"${listing.hoa_monthly:.0f}/mo" if listing.hoa_monthly else "None"
    print(f"  - {listing.listing_id}: {listing.title}")
    print(f"    Price: ${listing.list_price:,.0f} | HOA: {hoa_str}")
    print(f"    {listing.city}, {listing.state} {listing.zip_code}")


def test_scenario(name, zip_code, max_price=None, min_price=None):
    """Test a search scenario and print results."""
    print(f"\n{'=' * 60}")
    print(f"Test: {name}")
    print(f"{'=' * 60}")
    print(f"ZIP: {zip_code}")
    if max_price:
        print(f"Max price: ${max_price:,.0f}")
    if min_price:
        print(f"Min price: ${min_price:,.0f}")
    print()
    
    results = search_listings_for_zip(
        zip_code=zip_code,
        max_price=max_price,
        min_price=min_price,
        limit=10,
    )
    
    if not results:
        print("No listings found for this search criteria.")
    else:
        print(f"Found {len(results)} listing(s):\n")
        for listing in results:
            print_listing(listing)
            print()


if __name__ == "__main__":
    print("=" * 60)
    print("Local Listings Search - Smoke Test")
    print("=" * 60)
    
    # Test 1: ZIP 90803 with max price filter
    test_scenario(
        name="South CA (90803) - Max $900k",
        zip_code="90803",
        max_price=900000,
    )
    
    # Test 2: ZIP 78701 with price range
    test_scenario(
        name="Austin (78701) - Price range $500k-$900k",
        zip_code="78701",
        min_price=500000,
        max_price=900000,
    )
    
    # Test 3: Non-existent ZIP
    test_scenario(
        name="Non-existent ZIP (99999)",
        zip_code="99999",
    )
    
    # Test 4: ZIP 92648 with lower max price (should filter some out)
    test_scenario(
        name="Huntington Beach (92648) - Max $600k",
        zip_code="92648",
        max_price=600000,
    )
    
    print("\n" + "=" * 60)
    print("Smoke test completed!")
    print("=" * 60)

