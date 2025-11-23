#!/usr/bin/env python3
"""
mortgage_agent_quick_test.py - Quick Test for Mortgage Agent LLM Explanation

快速测试脚本，验证 LLM 解释功能是否正常工作。

Usage:
    python experiments/mortgage_agent_quick_test.py [--base-url http://localhost:8000]
"""

import argparse
import json
import sys
import requests
from typing import Dict, Any

DEFAULT_BASE_URL = "http://localhost:8000"

# 简单的测试 payload
TEST_PAYLOAD = {
    "user_message": "Can I afford a 500k home with 100k income?",
    "inputs": {
        "income": 100000,
        "debts": 500,
        "purchase_price": 500000,
        "down_payment_pct": 0.20,
        "state": "CA"
    }
}


def test_llm_explanation(base_url: str) -> bool:
    """
    快速测试 LLM 解释功能。
    
    Returns:
        True if test passes, False otherwise
    """
    url = f"{base_url}/api/mortgage-agent/run"
    
    print("=" * 60)
    print("Mortgage Agent LLM Explanation Quick Test")
    print("=" * 60)
    print(f"\n📍 Testing: {url}")
    print(f"📤 Request:")
    print(json.dumps(TEST_PAYLOAD, indent=2))
    print()
    
    try:
        response = requests.post(url, json=TEST_PAYLOAD, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        
        # 检查基本响应
        if not data.get("ok", False):
            print("❌ API returned ok=False")
            print(f"   Error: {data.get('error', 'Unknown')}")
            return False
        
        # 检查 plans
        plans = data.get("plans", [])
        if not plans:
            print("❌ No plans generated")
            return False
        
        print(f"✅ API Response OK")
        print(f"   Plans: {len(plans)}")
        
        # 检查 LLM 解释
        llm_explanation = data.get("llm_explanation")
        llm_usage = data.get("llm_usage")
        
        print("\n" + "-" * 60)
        print("LLM Explanation Check")
        print("-" * 60)
        
        if llm_explanation:
            print("✅ LLM Explanation: PRESENT")
            preview = llm_explanation[:200]
            if len(llm_explanation) > 200:
                preview += "..."
            print(f"   Preview: {preview}")
        else:
            print("⚠️  LLM Explanation: MISSING (may be disabled)")
            print("   Check LLM_GENERATION_ENABLED env var")
        
        if llm_usage:
            print("\n✅ LLM Usage: PRESENT")
            print(f"   Model: {llm_usage.get('model', 'N/A')}")
            print(f"   Tokens: {llm_usage.get('total_tokens', 'N/A')}")
            cost = llm_usage.get('cost_usd_est')
            if cost is not None:
                print(f"   Cost: ${cost:.6f}")
        else:
            print("\n⚠️  LLM Usage: MISSING")
        
        # 验证其他字段仍然存在
        print("\n" + "-" * 60)
        print("Backward Compatibility Check")
        print("-" * 60)
        
        required_fields = [
            "ok", "agent_version", "disclaimer", "input_summary",
            "plans", "followups"
        ]
        
        all_present = True
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing field: {field}")
                all_present = False
            else:
                print(f"✅ {field}: present")
        
        if not all_present:
            return False
        
        print("\n" + "=" * 60)
        print("✅ All checks passed!")
        print("=" * 60)
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API call failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Quick test for Mortgage Agent LLM explanation"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})"
    )
    
    args = parser.parse_args()
    
    success = test_llm_explanation(args.base_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()



