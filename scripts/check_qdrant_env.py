#!/usr/bin/env python3
"""
Check Qdrant Environment Variables
===================================
验证 Qdrant 环境变量配置（不打印敏感信息）

Usage:
    python scripts/check_qdrant_env.py
"""

import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv()
    env_cloudrun = Path('.env.cloudrun')
    if env_cloudrun.exists():
        load_dotenv(env_cloudrun, override=True)
except ImportError:
    pass

def mask_secret(value: str, show_chars: int = 4) -> str:
    """Mask secret value, showing only first/last few characters"""
    if not value:
        return "NOT SET"
    if len(value) <= show_chars * 2:
        return "*" * len(value)
    return value[:show_chars] + "*" * (len(value) - show_chars * 2) + value[-show_chars:]

def main():
    print("=" * 80)
    print("Qdrant Environment Variables Check")
    print("=" * 80)
    print()
    
    # Check QDRANT_URL
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        # Mask URL but show domain
        if "://" in qdrant_url:
            parts = qdrant_url.split("://", 1)
            if len(parts) == 2:
                protocol = parts[0]
                rest = parts[1]
                # Show first part of domain
                if "." in rest:
                    domain_parts = rest.split(".", 2)
                    if len(domain_parts) >= 2:
                        masked = f"{protocol}://{domain_parts[0][:4]}***.{domain_parts[1]}"
                    else:
                        masked = f"{protocol}://***"
                else:
                    masked = f"{protocol}://***"
            else:
                masked = "***"
        else:
            masked = mask_secret(qdrant_url, 4)
        print(f"✅ QDRANT_URL: {masked}")
    else:
        print("❌ QDRANT_URL: NOT SET")
    
    # Check QDRANT_API_KEY
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    if qdrant_api_key:
        print(f"✅ QDRANT_API_KEY: {mask_secret(qdrant_api_key, 4)}")
    else:
        print("⚠️  QDRANT_API_KEY: NOT SET (may be required for Qdrant Cloud)")
    
    # Check QDRANT_COLLECTION
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "auto_insurance_demo_core")
    print(f"✅ QDRANT_COLLECTION: {qdrant_collection} (default: auto_insurance_demo_core)")
    
    print()
    print("=" * 80)
    
    # Summary
    all_set = bool(qdrant_url)
    api_key_set = bool(qdrant_api_key)
    
    if all_set:
        print("✅ Status: QDRANT_URL is set")
        if api_key_set:
            print("✅ Status: QDRANT_API_KEY is set (ready for Cloud)")
        else:
            print("⚠️  Status: QDRANT_API_KEY not set (may fail for Cloud, OK for local)")
        return 0
    else:
        print("❌ Status: QDRANT_URL is required but not set")
        print()
        print("To fix:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in your QDRANT_URL and QDRANT_API_KEY")
        print("  3. Or set environment variables directly:")
        print("     export QDRANT_URL='https://your-cluster.qdrant.io'")
        print("     export QDRANT_API_KEY='your-api-key'")
        return 1

if __name__ == "__main__":
    sys.exit(main())
