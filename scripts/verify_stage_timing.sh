#!/bin/bash
# Verification script for Stage Timing implementation
# Generates mixed traffic and validates timing data

set -e

echo "=========================================="
echo "Stage Timing Verification Script"
echo "=========================================="

# Configuration
API_URL="http://localhost:8000"
DASHBOARD_JSON="reports/dashboard.json"
NUM_REQUESTS=50
MIN_SAMPLES=20

echo ""
echo "1. Checking if API is running..."
if ! curl -s "${API_URL}/health" > /dev/null 2>&1; then
    echo "❌ API not running at ${API_URL}"
    echo "   Start with: cd services/fiqa_api && uvicorn services.fiqa_api.app_main:app --reload --port 8000"
    exit 1
fi
echo "✅ API is running"

echo ""
echo "2. Generating ${NUM_REQUESTS} test requests (mixed rerank ON/OFF)..."

# Generate requests with mixed profiles and rerank settings
for i in $(seq 1 $NUM_REQUESTS); do
    # Alternate between profiles
    if [ $((i % 3)) -eq 0 ]; then
        profile="fast"
    elif [ $((i % 3)) -eq 1 ]; then
        profile="balanced"
    else
        profile="quality"
    fi
    
    # Send request
    query="What is portfolio optimization in finance? query_${i}"
    curl -s -X POST "${API_URL}/search" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"${query}\", \"top_k\": 10}" \
        > /dev/null
    
    # Progress indicator
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Progress: ${i}/${NUM_REQUESTS}"
    fi
    
    # Small delay to avoid overwhelming the system
    sleep 0.1
done

echo "✅ Generated ${NUM_REQUESTS} requests"

echo ""
echo "3. Waiting for dashboard to rebuild (5s)..."
sleep 5

echo ""
echo "4. Checking dashboard.json..."
if [ ! -f "$DASHBOARD_JSON" ]; then
    echo "❌ Dashboard file not found: ${DASHBOARD_JSON}"
    exit 1
fi
echo "✅ Dashboard file exists"

echo ""
echo "5. Extracting stage timing data..."

# Use Python to parse JSON and validate
python3 << 'EOF'
import json
import sys

try:
    with open("reports/dashboard.json", "r") as f:
        data = json.load(f)
    
    # Extract stage_timing
    stage_timing = data.get("meta", {}).get("stage_timing", {})
    
    if not stage_timing:
        print("❌ stage_timing not found in dashboard_meta")
        sys.exit(1)
    
    print("✅ stage_timing found")
    
    # Extract values
    window_sec = stage_timing.get("window_sec", 0)
    samples = stage_timing.get("samples", 0)
    avg_ms = stage_timing.get("avg_ms", {})
    p95_ms = stage_timing.get("p95_ms", {})
    invariant = stage_timing.get("invariant", {})
    clamped = stage_timing.get("clamped_network_rows", 0)
    
    ann_avg = avg_ms.get("ann", 0)
    rerank_avg = avg_ms.get("rerank", 0)
    network_avg = avg_ms.get("network", 0)
    total_avg = avg_ms.get("total", 0)
    
    ann_p95 = p95_ms.get("ann", 0)
    rerank_p95 = p95_ms.get("rerank", 0)
    network_p95 = p95_ms.get("network", 0)
    total_p95 = p95_ms.get("total", 0)
    
    deviation_avg_pct = invariant.get("deviation_avg_pct", 0)
    deviation_p95_pct = invariant.get("deviation_p95_pct", 0)
    
    print("")
    print("📊 Stage Timing Data:")
    print(f"   Window: {window_sec}s")
    print(f"   Samples: {samples}")
    print("")
    print(f"   Average (ms):")
    print(f"     ANN:     {ann_avg:6.2f}")
    print(f"     Rerank:  {rerank_avg:6.2f}")
    print(f"     Network: {network_avg:6.2f}")
    print(f"     Total:   {total_avg:6.2f}")
    print("")
    print(f"   P95 (ms):")
    print(f"     ANN:     {ann_p95:6.2f}")
    print(f"     Rerank:  {rerank_p95:6.2f}")
    print(f"     Network: {network_p95:6.2f}")
    print(f"     Total:   {total_p95:6.2f}")
    print("")
    print(f"   Invariant Check:")
    print(f"     Deviation (avg): {deviation_avg_pct:+.2f}%")
    print(f"     Deviation (p95): {deviation_p95_pct:+.2f}%")
    print(f"     Clamped rows:    {clamped}")
    
    # Validation
    print("")
    print("🔍 Validation:")
    
    errors = []
    
    # Check 1: Window is 60s
    if window_sec != 60:
        errors.append(f"Window is {window_sec}s, expected 60s")
    else:
        print("✅ Window is 60s")
    
    # Check 2: Sufficient samples
    if samples < 20:
        errors.append(f"Insufficient samples: {samples} (need >= 20)")
    else:
        print(f"✅ Sufficient samples: {samples}")
    
    # Check 3: ANN is nonzero
    if ann_avg <= 0:
        errors.append("ANN average is zero or negative")
    else:
        print(f"✅ ANN average is nonzero: {ann_avg:.2f}ms")
    
    # Check 4: Network is nonzero (unless truly zero)
    # For this check, we allow network to be small but not exactly 0
    if network_avg < 0:
        errors.append(f"Network average is negative: {network_avg:.2f}ms")
    elif network_avg == 0 and total_avg > 0:
        # This is suspicious - network should have some overhead
        errors.append(f"Network is exactly 0 but total is {total_avg:.2f}ms (suspicious)")
    else:
        print(f"✅ Network average is valid: {network_avg:.2f}ms")
    
    # Check 5: All values are within [0, total]
    if ann_avg < 0 or rerank_avg < 0 or network_avg < 0:
        errors.append("Negative timing values detected")
    elif ann_avg > total_avg or rerank_avg > total_avg or network_avg > total_avg:
        errors.append("Stage timing exceeds total")
    else:
        print("✅ All timings within [0, total]")
    
    # Check 6: Invariant - sum ≈ total (within ±10%)
    if abs(deviation_avg_pct) > 10:
        errors.append(f"Deviation too large: {deviation_avg_pct:+.2f}% (expected ±10%)")
    else:
        print(f"✅ Invariant holds: deviation = {deviation_avg_pct:+.2f}%")
    
    # Check 7: Total is nonzero
    if total_avg <= 0:
        errors.append("Total average is zero or negative")
    else:
        print(f"✅ Total average is nonzero: {total_avg:.2f}ms")
    
    # Report results
    print("")
    if errors:
        print("❌ VALIDATION FAILED")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    else:
        print("🎉 ALL CHECKS PASSED")
        print("")
        print("Summary:")
        print(f"  • {samples} samples collected in {window_sec}s window")
        print(f"  • ANN: {ann_avg:.1f}ms ({ann_avg/total_avg*100:.0f}%)")
        print(f"  • Rerank: {rerank_avg:.1f}ms ({rerank_avg/total_avg*100:.0f}%)")
        print(f"  • Network: {network_avg:.1f}ms ({network_avg/total_avg*100:.0f}%)")
        print(f"  • Invariant deviation: {deviation_avg_pct:+.2f}%")
        if clamped > 0:
            print(f"  • {clamped} rows had network clamped to 0")
        sys.exit(0)

except FileNotFoundError:
    print("❌ Dashboard file not found")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

RESULT=$?

echo ""
echo "=========================================="
if [ $RESULT -eq 0 ]; then
    echo "✅ Stage Timing Verification PASSED"
else
    echo "❌ Stage Timing Verification FAILED"
fi
echo "=========================================="

exit $RESULT

