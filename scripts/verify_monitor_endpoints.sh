#!/usr/bin/env bash
# verify_monitor_endpoints.sh - Monitor Panel 端点验收脚本
# 验证：/readyz, /api/agent/summary, /api/metrics/mini, /ops/* 返回 410
# 输出：≤10行 PASS/FAIL 汇总

set -e

API_BASE="${API_BASE:-http://127.0.0.1:8011}"
TIMEOUT=5

echo "Monitor Endpoints Verification (API Only)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 1: /readyz
if curl -sf --max-time $TIMEOUT "${API_BASE}/readyz" >/dev/null; then
    echo "✅ PASS: /readyz reachable"
else
    echo "❌ FAIL: /readyz unreachable"
    exit 1
fi

# Test 2: /api/agent/summary (only /api, no fallback)
V3_RESP=$(curl -sf --max-time $TIMEOUT "${API_BASE}/api/agent/summary?v=3" 2>&1)
if [ $? -eq 0 ] && echo "$V3_RESP" | grep -q '"ok":true'; then
    echo "✅ PASS: /api/agent/summary?v=3 OK"
else
    V2_RESP=$(curl -sf --max-time $TIMEOUT "${API_BASE}/api/agent/summary?v=2" 2>&1)
    if [ $? -eq 0 ] && echo "$V2_RESP" | grep -q '"ok":true'; then
        echo "✅ PASS: /api/agent/summary?v=2 OK (v3 fallback)"
    else
        echo "❌ FAIL: /api/agent/summary unreachable"
        exit 1
    fi
fi

# Test 3: /api/metrics/mini (需要返回 p95 字段)
METRICS_RESP=$(curl -sf --max-time $TIMEOUT "${API_BASE}/api/metrics/mini?exp_id=auto&window_sec=30" 2>&1)
if [ $? -eq 0 ]; then
    if echo "$METRICS_RESP" | grep -q '"p95"'; then
        echo "✅ PASS: /api/metrics/mini returns p95"
    else
        echo "❌ FAIL: /api/metrics/mini missing p95"
        exit 1
    fi
else
    echo "❌ FAIL: /api/metrics/mini unreachable"
    exit 1
fi

# Test 4: /ops/agent/summary should return 410 Gone
OPS_STATUS=$(curl -s -w "%{http_code}" -o /tmp/ops_resp.json --max-time $TIMEOUT "${API_BASE}/ops/agent/summary?v=2")
if [ "$OPS_STATUS" = "410" ]; then
    if grep -q '"reason":"ops endpoints removed' /tmp/ops_resp.json 2>/dev/null && \
       curl -sI --max-time $TIMEOUT "${API_BASE}/ops/agent/summary?v=2" 2>/dev/null | grep -qi 'x-deprecated.*ops-removed'; then
        echo "✅ PASS: /ops/agent/summary returns 410 (deprecated)"
    else
        echo "❌ FAIL: /ops returns 410 but missing deprecation headers/body"
        exit 1
    fi
else
    echo "❌ FAIL: /ops/agent/summary should return 410, got $OPS_STATUS"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL TESTS PASSED"
echo ""
echo "Summary:"
echo "- /api endpoints: ✅ Working"
echo "- /ops endpoints: ✅ Properly deprecated (410)"
echo ""
echo "Next: Open http://localhost:8011/monitor"
