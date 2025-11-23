#!/usr/bin/env python3
"""
Smoke test for Mortgage Programs MCP Server

This test directly calls the search function to verify it works correctly
without needing a full MCP client-server setup.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import server module
sys.path.insert(0, str(Path(__file__).parent))

from server import search_mortgage_programs


def test_search_mortgage_programs():
    """Test the search_mortgage_programs function."""
    print("=" * 60)
    print("Mortgage Programs MCP Server - Smoke Test")
    print("=" * 60)
    print()
    
    # Test case: first-time buyer in CA with DTI 57%
    test_params = {
        "zip_code": "90803",
        "state": "CA",
        "profile_tags": ["first_time_buyer"],
        "current_dti": 0.57
    }
    
    print(f"Test Parameters:")
    print(f"  ZIP Code: {test_params['zip_code']}")
    print(f"  State: {test_params['state']}")
    print(f"  Profile Tags: {test_params['profile_tags']}")
    print(f"  Current DTI: {test_params['current_dti']*100:.1f}%")
    print()
    print("-" * 60)
    print()
    
    try:
        # Call the search function (now it's a regular function, not async)
        result_text = search_mortgage_programs(**test_params)
        
        # Parse the JSON string
        if result_text:
            programs = json.loads(result_text)
            
            print(f"✓ Search completed successfully!")
            print(f"✓ Found {len(programs)} matching program(s)")
            print()
            print("Results:")
            print("-" * 60)
            
            for i, program in enumerate(programs, 1):
                print(f"\n{i}. {program['name']} (ID: {program['id']})")
                print(f"   Description: {program['description']}")
                print(f"   Benefit: {program['benefit_summary']}")
                print(f"   Why Relevant: {program['why_relevant']}")
            
            print()
            print("=" * 60)
            print("✓ Smoke test PASSED")
            print("=" * 60)
            return True
        else:
            print("✗ No results returned")
            return False
            
    except Exception as e:
        print(f"✗ Smoke test FAILED with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_additional_cases():
    """Test additional edge cases."""
    print("\n" + "=" * 60)
    print("Additional Test Cases")
    print("=" * 60)
    print()
    
    test_cases = [
        {
            "name": "Veteran in TX",
            "params": {
                "zip_code": "78701",
                "state": "TX",
                "profile_tags": ["veteran"],
                "current_dti": 0.45
            }
        },
        {
            "name": "Low income, no state specified",
            "params": {
                "zip_code": "90001",
                "profile_tags": ["low_income"],
                "current_dti": 0.52
            }
        },
        {
            "name": "High DTI borrower",
            "params": {
                "zip_code": "98101",
                "state": "WA",
                "profile_tags": ["high_dti"],
                "current_dti": 0.58
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print("-" * 60)
        try:
            result_text = search_mortgage_programs(**test_case['params'])
            if result_text:
                programs = json.loads(result_text)
                print(f"✓ Found {len(programs)} program(s)")
                for prog in programs[:2]:  # Show first 2
                    print(f"  - {prog['name']}")
            else:
                print("  No matches found")
        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    success = test_search_mortgage_programs()
    test_additional_cases()
    
    sys.exit(0 if success else 1)

