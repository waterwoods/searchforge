#!/bin/bash
# Test MMR functionality

set -e

BASE_URL="${BASE:-http://localhost:8000}"

echo "========================================="
echo "MMR Functionality Test"
echo "========================================="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Simple MMR query
echo "[TEST 1] MMR Query with λ=0.3 (balanced)"
curl -s -X POST "${BASE_URL}/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is portfolio diversification?",
    "top_k": 10,
    "collection": "fiqa_10k_v1",
    "mmr": true,
    "mmr_lambda": 0.3
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  ✓ Status: {data.get('ok', False)}\")
print(f\"  ✓ Results: {len(data.get('sources', []))} documents\")
print(f\"  ✓ Latency: {data.get('latency_ms', 0):.1f}ms\")
if 'metrics' in data and 'metrics_details' in data['metrics']:
    mmr_info = data['metrics'].get('metrics_details', {}).get('mmr', {})
    if mmr_info.get('enabled'):
        print(f\"  ✓ MMR: enabled, λ={mmr_info.get('lambda', 'N/A')}, {mmr_info.get('elapsed_ms', 0):.1f}ms\")
    else:
        print(f\"  ⚠ MMR: {mmr_info.get('reason', 'not enabled')}\")
"
echo ""

# Test 2: MMR with λ=0.1 (high diversity)
echo "[TEST 2] MMR Query with λ=0.1 (high diversity)"
curl -s -X POST "${BASE_URL}/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How to calculate return on investment?",
    "top_k": 10,
    "collection": "fiqa_10k_v1",
    "mmr": true,
    "mmr_lambda": 0.1
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  ✓ Status: {data.get('ok', False)}\")
print(f\"  ✓ Results: {len(data.get('sources', []))} documents\")
"
echo ""

# Test 3: Check response headers
echo "[TEST 3] Verify MMR Response Headers"
response=$(curl -s -i -X POST "${BASE_URL}/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a stock split?",
    "top_k": 10,
    "collection": "fiqa_10k_v1",
    "mmr": true,
    "mmr_lambda": 0.5
  }')

echo "$response" | grep -i "X-MMR:" || echo "  ⚠ X-MMR header not found"
echo "$response" | grep -i "X-MMR-Lambda:" || echo "  ⚠ X-MMR-Lambda header not found"
echo ""

# Test 4: Baseline (no MMR)
echo "[TEST 4] Baseline Query (MMR disabled)"
curl -s -X POST "${BASE_URL}/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is compound interest?",
    "top_k": 10,
    "collection": "fiqa_10k_v1",
    "mmr": false
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  ✓ Status: {data.get('ok', False)}\")
print(f\"  ✓ Results: {len(data.get('sources', []))} documents\")
print(f\"  ✓ Latency: {data.get('latency_ms', 0):.1f}ms\")
"
echo ""

echo "========================================="
echo "✅ MMR Tests Complete"
echo "========================================="

