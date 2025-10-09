#!/usr/bin/env python3
"""
2-Minute LIVE Test with Async + Cache Optimization Enabled
Demonstrates production-grade performance with full optimizations
"""
import os
import sys
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')

from labs.run_rag_rewrite_ab_live import *

# Override configuration for optimized 2-minute test
TEST_CONFIG["mode"] = "live"
TEST_CONFIG["duration_per_side_sec"] = 120  # 2 minutes per side
TEST_CONFIG["bucket_sec"] = 10  # 10-second buckets
TEST_CONFIG["target_qps"] = 12  # 12 queries per second
TEST_CONFIG["permutation_trials"] = 5000

print("=" * 70)
print("🚀 LIVE Test - 2 Minute Optimized (Async + Cache ENABLED)")
print("=" * 70)
print(f"\n⚡ Optimizations:")
print(f"   Async Rewrite: ✅ ENABLED (60-70% hit rate expected)")
print(f"   Cache: ✅ ENABLED (30-40% hit rate expected)")
print(f"\n⏱️  每组运行时间: 120 秒")
print(f"📊 预期样本数: ~144 per side (12 QPS × 120s)")
print(f"🗂️  预期分桶数: ~12 per side (10s buckets)")
print(f"\n预期门禁结果:")
print(f"   ΔP95: ~3-4ms (vs 12-16ms without async) ✅")
print(f"   Async Hit: ~60-70% ✅")
print(f"   Cache Hit: ~30-40% (after warmup) ✅")
print(f"\n总运行时间: ~4 分钟")
print("=" * 70)
print()

if __name__ == "__main__":
    main()
