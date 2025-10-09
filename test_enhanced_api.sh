#!/bin/bash
# Enhanced API Integration Test

echo "=================================================="
echo "🧪 Enhanced FIQA API Integration Test"
echo "=================================================="
echo ""

# Test 1: Input Validation
echo "📝 Test 1: Input Validation"
echo "----------------------------"
echo -n "Empty query (expect 400): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" -d '{"query": "", "top_k": 5}')
[ "$STATUS" = "422" ] && echo "✓ PASS (422)" || echo "✗ FAIL ($STATUS)"

echo -n "top_k=0 (expect 400): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" -d '{"query": "test", "top_k": 0}')
[ "$STATUS" = "422" ] && echo "✓ PASS (422)" || echo "✗ FAIL ($STATUS)"

echo -n "top_k=25 (expect 400): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" -d '{"query": "test", "top_k": 25}')
[ "$STATUS" = "422" ] && echo "✓ PASS (422)" || echo "✗ FAIL ($STATUS)"

echo ""

# Test 2: Rate Limiting
echo "⏱️  Test 2: Rate Limiting (3 req/sec limit)"
echo "----------------------------"
SUCCESS_COUNT=0
RATE_LIMITED=0
for i in {1..5}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/search \
    -H "Content-Type: application/json" -d '{"query": "test", "top_k": 3}')
  if [ "$STATUS" = "200" ]; then
    ((SUCCESS_COUNT++))
  elif [ "$STATUS" = "429" ]; then
    ((RATE_LIMITED++))
  fi
done
echo "Successful: $SUCCESS_COUNT, Rate limited: $RATE_LIMITED"
[ "$RATE_LIMITED" -ge 2 ] && echo "✓ Rate limit working" || echo "✗ Rate limit not working"

echo ""

# Test 3: Smoke Load Test
echo "🔥 Test 3: Smoke Load Test"
echo "----------------------------"
python scripts/smoke_load.py
LOAD_EXIT=$?

echo ""

# Test 4: Enhanced Metrics
echo "📊 Test 4: Enhanced Metrics"
echo "----------------------------"
METRICS=$(curl -s http://localhost:8080/metrics)
echo "$METRICS" | python3 -c "
import sys, json
m = json.load(sys.stdin)
print(f\"[METRICS] avg_p95={m['avg_p95_ms']}ms / avg_recall={m['avg_recall']} / avg_cost={m['avg_cost']:.6f}\")
print(f\"         avg_tokens_in={m['avg_tokens_in']} / avg_tokens_out={m['avg_tokens_out']}\")

# Verify new fields exist
assert 'avg_tokens_in' in m, 'Missing avg_tokens_in'
assert 'avg_tokens_out' in m, 'Missing avg_tokens_out'
assert 'avg_cost' in m, 'Missing avg_cost'
print('✓ All enhanced metrics present')
"

echo ""
echo "=================================================="
echo "✅ Integration Test Complete"
echo "=================================================="

exit $LOAD_EXIT

