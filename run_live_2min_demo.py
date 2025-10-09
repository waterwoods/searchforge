#!/usr/bin/env python3
"""
2-Minute LIVE Test for demonstration
This produces enough buckets (≥10) while being faster than full 10-minute test
"""
import os
import sys
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')

# Import modules
from labs.run_rag_rewrite_ab_live import *

# Override configuration for 2-minute test
TEST_CONFIG["mode"] = "live"
TEST_CONFIG["duration_per_side_sec"] = 120  # 2 minutes per side
TEST_CONFIG["bucket_sec"] = 10  # 10-second buckets → 12 buckets per side
TEST_CONFIG["target_qps"] = 12  # 12 queries per second
TEST_CONFIG["permutation_trials"] = 5000

print("=" * 70)
print("🚀 LIVE Test - 2 Minute Version (Demo)")
print("=" * 70)
print(f"\n⏱️  每组运行时间: 120 秒")
print(f"📊 预期样本数: ~144 per side (12 QPS × 120s)")
print(f"🗂️  预期分桶数: ~12 per side (10s buckets)")
print(f"\n总运行时间: ~4 分钟")
print("=" * 70)
print()

if __name__ == "__main__":
    main()

