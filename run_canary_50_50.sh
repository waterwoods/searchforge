#!/bin/bash
# Canary Deployment: 50% OFF / 50% ON (balanced A/B test)
# 10-minute test with production gates

cd /Users/nanxinli/Documents/dev/searchforge

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Canary Deployment Test: 50% OFF / 50% ON                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Rewrite OFF: 50% traffic"
echo "  Rewrite ON:  50% traffic"
echo "  Duration: 10 minutes (600s)"
echo "  QPS: 12"
echo "  Buckets: 10s"
echo ""

# Create canary test script
cat > /tmp/canary_50_50.py << 'PYEOF'
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')

from labs.run_rag_rewrite_ab_live import *

# Override config for 50/50 canary
TEST_CONFIG["mode"] = "live"
TEST_CONFIG["duration_per_side_sec"] = 300  # 5 minutes per group (50/50 split)
TEST_CONFIG["bucket_sec"] = 10
TEST_CONFIG["target_qps"] = 12

print("🚀 Running Canary: 50/50 Split")
print("   Group A (ON): 50% of traffic = 300s")
print("   Group B (OFF): 50% of traffic = 300s")
print()

if __name__ == "__main__":
    main()
    
    # Load results for gate check
    import json
    with open('reports/rag_rewrite_ab.json', 'r') as f:
        data = json.load(f)
    
    analysis = data['analysis']
    
    print("\n" + "=" * 60)
    print("🚦 Canary 50/50 Gate Check")
    print("=" * 60)
    
    delta_recall = analysis['deltas']['recall_delta']
    p_value = analysis['statistical']['p_value_recall']
    delta_p95 = analysis['deltas']['p95_delta_ms']
    fail_rate = analysis['group_a']['failure_rate_pct'] / 100
    cost = analysis['group_a']['cost_per_query_usd']
    async_hit = analysis['group_a']['async_hit_rate_pct']
    cache_hit = analysis['group_a']['cache_hit_rate_pct']
    
    gate_pass = (
        delta_recall >= 0.05 and
        p_value < 0.05 and
        delta_p95 <= 5 and
        fail_rate < 0.01 and
        cost <= 0.00005
    )
    
    print(f"\nGate Results:")
    print(f"  ΔRecall={delta_recall:.4f} (need ≥0.05): {'✓' if delta_recall >= 0.05 else '✗'}")
    print(f"  p={p_value:.4f} (need <0.05): {'✓' if p_value < 0.05 else '✗'}")
    print(f"  ΔP95={delta_p95:.1f}ms (need ≤5ms): {'✓' if delta_p95 <= 5 else '✗'}")
    print(f"  fail_rate={fail_rate:.2%} (need <1%): {'✓' if fail_rate < 0.01 else '✗'}")
    print(f"  cost=${cost:.6f} (need ≤$0.00005): {'✓' if cost <= 0.00005 else '✗'}")
    print(f"  async_hit={async_hit:.1f}%, cache_hit={cache_hit:.1f}%")
    
    print("\n" + "=" * 60)
    if gate_pass:
        print("✅ PASS - Canary 测试通过，可全量上线")
        print(f"   ΔRecall={delta_recall:.4f}, ΔP95={delta_p95:.1f}ms, p={p_value:.4f},")
        print(f"   cost=${cost:.6f}, fail_rate={fail_rate:.2%}, async_hit={async_hit:.1f}%, cache_hit={cache_hit:.1f}%")
        sys.exit(0)
    else:
        print("❌ FAIL - Canary 测试未通过，建议回滚或优化")
        sys.exit(1)
PYEOF

python /tmp/canary_50_50.py
exit_code=$?

echo ""
echo "Canary test exit code: $exit_code"
exit $exit_code
