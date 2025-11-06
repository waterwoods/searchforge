#!/bin/bash
# verify_preflight.sh - Preflight checks for observability
# Checks: /readyz, Redis TTL, /api/metrics/mini

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8011}"
PASS_COUNT=0
FAIL_COUNT=0

echo "━━━ Preflight Checks ━━━"

# 1. Check /readyz
echo -n "✓ /readyz... "
if curl -sf "$BASE_URL/readyz" >/dev/null 2>&1; then
    echo "PASS"
    ((PASS_COUNT++))
else
    echo "FAIL"
    ((FAIL_COUNT++))
fi

# 2. Check Redis connectivity
echo -n "✓ Redis ping... "
if redis-cli ping >/dev/null 2>&1; then
    echo "PASS"
    ((PASS_COUNT++))
else
    echo "FAIL"
    ((FAIL_COUNT++))
fi

# 3. Check Redis TTL (use a test key)
echo -n "✓ Redis TTL... "
redis-cli setex "preflight:test" 10 "ok" >/dev/null 2>&1
TTL=$(redis-cli ttl "preflight:test" 2>/dev/null || echo "-1")
if [ "$TTL" -gt 0 ]; then
    echo "PASS (ttl=$TTL)"
    ((PASS_COUNT++))
else
    echo "FAIL"
    ((FAIL_COUNT++))
fi

# 4. Check /api/metrics/mini (with dummy exp_id)
echo -n "✓ /api/metrics/mini... "
RESP=$(curl -sf "$BASE_URL/api/metrics/mini?exp_id=test&window_sec=30" 2>/dev/null || echo '{}')
if echo "$RESP" | jq -e '.p95' >/dev/null 2>&1 || echo "$RESP" | jq -e '.error' >/dev/null 2>&1; then
    echo "PASS"
    ((PASS_COUNT++))
else
    echo "FAIL"
    ((FAIL_COUNT++))
fi

# 5. Check /api/lab/snapshot
echo -n "✓ /api/lab/snapshot... "
SNAP_RESP=$(curl -sf -X POST "$BASE_URL/api/lab/snapshot" -H "Content-Type: application/json" -d '{"trigger":"preflight"}' 2>/dev/null || echo '{}')
if echo "$SNAP_RESP" | jq -e '.ok' >/dev/null 2>&1; then
    echo "PASS"
    ((PASS_COUNT++))
else
    echo "FAIL"
    ((FAIL_COUNT++))
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━"
echo "PASS: $PASS_COUNT | FAIL: $FAIL_COUNT"
if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ All preflight checks passed"
    exit 0
else
    echo "❌ Some checks failed"
    exit 1
fi
