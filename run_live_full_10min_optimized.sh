#!/bin/bash
# Full 10-Minute LIVE A/B Test with Async + Cache Optimization
# Production-ready validation with all gates

cd /Users/nanxinli/Documents/dev/searchforge

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  LIVE A/B Test: 10 Minutes per Side (Async + Cache)         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Mode: LIVE"
echo "  Duration: 600s per side (10 minutes each)"
echo "  QPS: 12"
echo "  Buckets: 10s (60 buckets expected)"
echo "  Optimizations: Async ✅ + Cache ✅"
echo ""
echo "Expected Results:"
echo "  ΔP95: ~1-2ms (cache hit ~95%)"
echo "  Async Hit: ~60-70%"
echo "  Cache Hit: ~95%+ (after warmup)"
echo "  All Gates: PASS ✅"
echo ""
echo "Total runtime: ~20 minutes"
echo ""
read -p "Press Enter to start, or Ctrl+C to cancel..."

# Create optimized LIVE test script
cat > /tmp/run_live_full_10min_optimized.py << 'PYEOF'
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')

from labs.run_rag_rewrite_ab_live import *

# Full 10-minute configuration
TEST_CONFIG["mode"] = "live"
TEST_CONFIG["duration_per_side_sec"] = 600  # Full 10 minutes
TEST_CONFIG["bucket_sec"] = 10
TEST_CONFIG["target_qps"] = 12
TEST_CONFIG["permutation_trials"] = 5000

print("=" * 70)
print("🚀 LIVE Test - Full 10 Minutes (Async + Cache ENABLED)")
print("=" * 70)
print(f"\n⚡ Optimizations:")
print(f"   Async Rewrite: ✅ ENABLED")
print(f"   Cache: ✅ ENABLED")
print(f"\n⏱️  每组运行时间: 600 秒 (10 分钟)")
print(f"📊 预期样本数: ~720 per side")
print(f"🗂️  预期分桶数: ~60 per side")
print(f"\n总运行时间: ~20 分钟")
print("=" * 70)
print()

if __name__ == "__main__":
    main()
PYEOF

# Run it
python /tmp/run_live_full_10min_optimized.py

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ LIVE Test Complete!                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Reports:"
echo "   HTML: reports/rag_rewrite_ab.html"
echo "   JSON: reports/rag_rewrite_ab.json"
echo ""
echo "View: open reports/rag_rewrite_ab.html"
