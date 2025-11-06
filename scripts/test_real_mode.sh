#!/usr/bin/env bash
#
# test_real_mode.sh - Quick test to verify Black Swan real mode
#

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8001}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Black Swan Real Mode - Quick Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Check services
echo "[1/5] Checking services..."
app_v2=$(curl -sf ${API_BASE}/admin/health > /dev/null && echo "✅ Running" || echo "❌ Down")
fiqa=$(curl -sf http://localhost:8080/admin/health > /dev/null && echo "✅ Running" || echo "❌ Down")
qdrant=$(curl -sf http://localhost:6333/collections > /dev/null && echo "✅ Running" || echo "❌ Down")

echo "  • App_v2 (8001): $app_v2"
echo "  • FIQA API (8080): $fiqa"
echo "  • Qdrant (6333): $qdrant"
echo ""

# 2. Check configuration
echo "[2/5] Checking configuration..."
config=$(curl -sf ${API_BASE}/ops/black_swan/config)
use_real=$(echo "$config" | jq -r '.use_real')
nocache=$(echo "$config" | jq -r '.nocache')
fiqa_url=$(echo "$config" | jq -r '.fiqa_search_url')

echo "  • use_real: $use_real"
echo "  • nocache: $nocache"  
echo "  • fiqa_search_url: $fiqa_url"
echo ""

if [[ "$use_real" != "true" ]]; then
    echo "❌ ERROR: Real mode not enabled!"
    echo "   Set BLACK_SWAN_USE_REAL=true and restart backend"
    exit 1
fi

# 3. Get initial hits
echo "[3/5] Recording initial hit count..."
initial_hits=$(curl -sf ${API_BASE}/ops/qdrant/stats | jq -r '.hits')
echo "  • Initial hits: $initial_hits"
echo ""

# 4. Test single search
echo "[4/5] Testing single real query..."
search_result=$(curl -sf ${API_BASE}/search -H "Content-Type: application/json" -d '{"query":"financial advice","top_k":5}')
search_mode=$(echo "$search_result" | jq -r '.mode // "unknown"')
search_latency=$(echo "$search_result" | jq -r '.latency_ms // 0')

echo "  • Mode: $search_mode"
echo "  • Latency: ${search_latency}ms"

# Check hits increased (only if Black Swan was running)
if [[ "$search_mode" == "real" ]]; then
    sleep 1
    new_hits=$(curl -sf ${API_BASE}/ops/qdrant/stats | jq -r '.hits')
    echo "  • Hits after: $new_hits"
    
    if [[ $new_hits -gt $initial_hits ]]; then
        echo "  ✅ Hit counter increased!"
    fi
fi
echo ""

# 5. Summary
echo "[5/5] Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$use_real" == "true" ]] && [[ "$fiqa" == "✅ Running" ]]; then
    echo "✅ Real mode is configured and ready!"
    echo ""
    echo "To run full Black Swan test:"
    echo "  curl -X POST ${API_BASE}/ops/black_swan -d '{\"mode\":\"A\"}'"
    echo ""
    echo "To monitor hits:"
    echo "  watch -n 1 'curl -s ${API_BASE}/ops/qdrant/stats | jq .hits'"
else
    echo "⚠️  Real mode not fully configured"
    if [[ "$use_real" != "true" ]]; then
        echo "   • Set BLACK_SWAN_USE_REAL=true"
    fi
    if [[ "$fiqa" != "✅ Running" ]]; then
        echo "   • Start FIQA API on port 8080"
    fi
fi

echo ""

