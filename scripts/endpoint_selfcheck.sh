#!/usr/bin/env bash
# endpoint_selfcheck.sh — Auto-check & validation for frozen API contracts
# Usage: ./scripts/endpoint_selfcheck.sh [API_BASE]
# Example: ./scripts/endpoint_selfcheck.sh http://localhost:8001

set -euo pipefail

API_BASE="${1:-http://localhost:8001}"
PASS=0
FAIL=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Endpoint Consistency Self-Check (Frozen Contracts)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Base: $API_BASE"
echo ""

# Helper functions
pass() { echo "  ✅ $1"; ((PASS++)); }
fail() { echo "  ❌ $1"; ((FAIL++)); }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1: HTTP Status & JSON Shape
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "📋 STEP 1: HTTP Status & JSON Shape"
echo "──────────────────────────────────────────────────────────────"

for endpoint in "/auto/status" "/tuner/enabled" "/admin/warmup/status"; do
    echo ""
    echo "Testing: $endpoint"
    http_code=$(curl -s -w "%{http_code}" -o /tmp/endpoint_test.json "$API_BASE$endpoint")
    
    if [[ "$http_code" == "200" ]]; then
        pass "HTTP 200"
    else
        fail "HTTP $http_code (expected 200)"
    fi
    
    if jq empty /tmp/endpoint_test.json 2>/dev/null; then
        pass "Valid JSON"
    else
        fail "Invalid JSON response"
    fi
    
    echo "  Response: $(cat /tmp/endpoint_test.json | jq -c .)"
done

# Special check for /dashboard.json (should be 410)
echo ""
echo "Testing: /dashboard.json (deprecated)"
http_code=$(curl -s -w "%{http_code}" -o /tmp/endpoint_test.json "$API_BASE/dashboard.json")

if [[ "$http_code" == "410" ]]; then
    pass "HTTP 410 (Gone)"
else
    fail "HTTP $http_code (expected 410)"
fi

if jq -e '.ok==true and .deprecated==true' /tmp/endpoint_test.json >/dev/null 2>&1; then
    pass "Deprecation schema valid"
else
    fail "Missing ok/deprecated fields"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2: Schema Assertions (Frozen Contract)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo ""
echo "📋 STEP 2: Schema Assertions (Frozen Contract)"
echo "──────────────────────────────────────────────────────────────"

# /auto/status
echo ""
echo "Testing: /auto/status schema"
if curl -s "$API_BASE/auto/status" | jq -e '.ok==true' >/dev/null 2>&1; then
    pass "Has 'ok' field"
else
    fail "Missing 'ok' field"
fi

if curl -s "$API_BASE/auto/status" | jq -e '.running|type=="boolean"' >/dev/null 2>&1; then
    pass "Has 'running' (boolean)"
else
    fail "Missing/invalid 'running' field"
fi

if curl -s "$API_BASE/auto/status" | jq -e '.qps|type=="number"' >/dev/null 2>&1; then
    pass "Has 'qps' (number)"
else
    fail "Missing/invalid 'qps' field"
fi

if curl -s "$API_BASE/auto/status" | jq -e '.target_qps|type=="number"' >/dev/null 2>&1; then
    pass "Has 'target_qps' (number)"
else
    fail "Missing/invalid 'target_qps' field"
fi

if curl -s "$API_BASE/auto/status" | jq -e '.pattern|test("^(constant|step|saw|pulse)$")' >/dev/null 2>&1; then
    pass "Has 'pattern' (valid enum)"
else
    fail "Missing/invalid 'pattern' field (must be constant|step|saw|pulse)"
fi

# /tuner/enabled
echo ""
echo "Testing: /tuner/enabled schema"
if curl -s "$API_BASE/tuner/enabled" | jq -e '.ok==true' >/dev/null 2>&1; then
    pass "Has 'ok' field"
else
    fail "Missing 'ok' field"
fi

if curl -s "$API_BASE/tuner/enabled" | jq -e 'has("enabled") or has("paused")' >/dev/null 2>&1; then
    pass "Has 'enabled' or 'paused' field"
else
    fail "Missing both 'enabled' and 'paused' fields"
fi

# /admin/warmup/status
echo ""
echo "Testing: /admin/warmup/status schema"
if curl -s "$API_BASE/admin/warmup/status" | jq -e '.ok==true' >/dev/null 2>&1; then
    pass "Has 'ok' field"
else
    fail "Missing 'ok' field"
fi

if curl -s "$API_BASE/admin/warmup/status" | jq -e '.ready|type=="boolean"' >/dev/null 2>&1; then
    pass "Has 'ready' (boolean)"
else
    fail "Missing/invalid 'ready' field"
fi

if curl -s "$API_BASE/admin/warmup/status" | jq -e '.samples|type=="number"' >/dev/null 2>&1; then
    pass "Has 'samples' (number)"
else
    fail "Missing/invalid 'samples' field"
fi

if curl -s "$API_BASE/admin/warmup/status" | jq -e '.window_sec==60' >/dev/null 2>&1; then
    pass "Has 'window_sec' (value=60)"
else
    fail "Missing/invalid 'window_sec' field (must be 60)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3: Latency Check (p50/p90)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo ""
echo "📋 STEP 3: Latency Check (p50/p90)"
echo "──────────────────────────────────────────────────────────────"

for endpoint in "/auto/status" "/tuner/enabled" "/admin/warmup/status"; do
    echo ""
    echo "Testing: $endpoint latency"
    
    # Run 10 requests and measure time
    for i in {1..10}; do
        curl -s -o /dev/null -w "%{time_total}\n" "$API_BASE$endpoint"
    done | sort -n > /tmp/latency_test.txt
    
    p50=$(awk 'NR==5' /tmp/latency_test.txt)
    p90=$(awk 'NR==9' /tmp/latency_test.txt)
    
    echo "  p50: ${p50}s, p90: ${p90}s"
    
    # Check if p50 < 0.005 (5ms) and p90 < 0.010 (10ms)
    if awk -v p50="$p50" 'BEGIN {exit !(p50 < 0.005)}'; then
        pass "p50 < 5ms"
    else
        fail "p50 >= 5ms"
    fi
    
    if awk -v p90="$p90" 'BEGIN {exit !(p90 < 0.010)}'; then
        pass "p90 < 10ms"
    else
        fail "p90 >= 10ms"
    fi
done

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4: 404 Log Scan
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo ""
echo "📋 STEP 4: 404 Log Scan"
echo "──────────────────────────────────────────────────────────────"

# Try to find log files
if ls services/fiqa_api/*.log >/dev/null 2>&1; then
    if grep -E "404.*(auto/status|tuner/enabled|admin/warmup/status|dashboard\.json)" services/fiqa_api/*.log 2>/dev/null; then
        fail "Found 404 errors for monitored endpoints in logs"
    else
        pass "No 404 errors found in logs (NO_404 ✅)"
    fi
else
    echo "  ⚠️  No log files found in services/fiqa_api/*.log (skipping)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo "✅ All checks passed! Endpoints are frozen-contract compliant."
    echo ""
    echo "✨ Step 1 Complete — Ready for Black Swan E (Pre-warm + Progress)"
    exit 0
else
    echo "❌ Some checks failed. Please review and fix."
    exit 1
fi

