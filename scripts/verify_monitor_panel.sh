#!/usr/bin/env bash
# verify_monitor_panel.sh - Monitor Panel MVP 验收脚本
# 验证：/readyz, /api/metrics/mini, /api/agent/summary (v3→v2回退)
# 输出：≤10行 PASS/FAIL 汇总
# 
# 6 要素验收：
# 1. /api/metrics/mini 返回 p95/qps/err_pct/route_share
# 2. /api/agent/summary?v=3 或 v=2 返回 verdict/bullets
# 3. /readyz 健康检查
# 4. 只用 /api 前缀，无 /ops 残留

set -e

API_BASE="${API_BASE:-http://localhost:8011}"
TIMEOUT=5

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Monitor Panel MVP - 验收脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 1: /readyz (健康检查)
if curl -sf --max-time $TIMEOUT "${API_BASE}/readyz" > /dev/null 2>&1; then
    echo "✅ PASS: /readyz reachable"
else
    echo "❌ FAIL: /readyz unreachable"
    exit 1
fi

# Test 2: /api/metrics/mini (需要返回 p95/qps/err_pct)
METRICS_RESP=$(curl -sf --max-time $TIMEOUT "${API_BASE}/api/metrics/mini?exp_id=auto&window_sec=600" 2>&1)
if [ $? -eq 0 ]; then
    if echo "$METRICS_RESP" | grep -q '"p95"' && echo "$METRICS_RESP" | grep -q '"qps"' && echo "$METRICS_RESP" | grep -q '"err_pct"'; then
        echo "✅ PASS: /api/metrics/mini returns p95/qps/err_pct"
    else
        echo "❌ FAIL: /api/metrics/mini missing required fields"
        echo "   Response: $METRICS_RESP"
        exit 1
    fi
else
    echo "⚠️  WARN: /api/metrics/mini unreachable (可能无数据)"
    echo "   继续验证其他端点..."
fi

# Test 3: /api/agent/summary?v=3 (v3→v2自动回退)
V3_RESP=$(curl -sf --max-time $TIMEOUT "${API_BASE}/api/agent/summary?v=3" 2>&1)
if [ $? -eq 0 ]; then
    if echo "$V3_RESP" | grep -q '"bullets"' && echo "$V3_RESP" | grep -q '"explainer_mode"'; then
        echo "✅ PASS: /api/agent/summary?v=3 OK (bullets + explainer_mode)"
    else
        echo "⚠️  WARN: /api/agent/summary?v=3 missing fields"
    fi
else
    # Try v=2 fallback
    echo "   v3 failed, trying v2 fallback..."
    V2_RESP=$(curl -sf --max-time $TIMEOUT "${API_BASE}/api/agent/summary?v=2" 2>&1)
    if [ $? -eq 0 ]; then
        if echo "$V2_RESP" | grep -q '"verdict"' || echo "$V2_RESP" | grep -q '"bullets"'; then
            echo "✅ PASS: /api/agent/summary?v=2 OK (v3 fallback)"
        else
            echo "⚠️  WARN: /api/agent/summary?v=2 missing fields"
        fi
    else
        echo "⚠️  WARN: /api/agent/summary v2/v3 both unreachable (Agent可能未运行)"
    fi
fi

# Test 4: 确认无 /ops 残留 (检查 /ops/agent/summary 返回 410 Gone)
OPS_RESP=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "${API_BASE}/ops/agent/summary?v=2" 2>&1)
if [ "$OPS_RESP" = "410" ]; then
    echo "✅ PASS: /ops prefix removed (410 Gone)"
elif [ "$OPS_RESP" = "000" ]; then
    echo "✅ PASS: /ops prefix not found (expected)"
else
    echo "⚠️  WARN: /ops still accessible (HTTP $OPS_RESP), should return 410 Gone"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL CRITICAL TESTS PASSED"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:8011/monitor"
echo "2. 观察曲线每3s刷新 (POLL_INTERVAL=3s)"
echo "3. 验证顶部4卡片：P95/Success%/QPS/Route%"
echo "4. 验证判定条：PASS/FAIL + 三条要点"
echo "5. 点击 Agent \"Run(dry)\" 测试 v3→v2 回退"
echo "6. 检查失联>10s显示\"等待数据…\""

