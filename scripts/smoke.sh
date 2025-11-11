#!/usr/bin/env bash
# Smoke test script for Hybrid+RRF and gated reranking
# Tests: 1) RRF ID alignment, 2) Trigger rate constraint, 3) best.yaml deep merge

set -euo pipefail

# Configuration
BASE="${BASE:-http://localhost:8000}"
CURL_TIMEOUT=10

# Dependency checks
command -v jq >/dev/null || { echo "❌ Error: jq not found. Install with: brew install jq or apt-get install jq"; exit 1; }
command -v curl >/dev/null || { echo "❌ Error: curl not found"; exit 1; }

echo "=== Smoke Test Script ==="
echo "BASE=${BASE}"
echo ""

# ========================================
# Smoke Test 1: ID Alignment (RRF fusion overlap)
# ========================================
echo "### Smoke Test 1: RRF ID Alignment ###"

RESPONSE1=$(curl -sSf --max-time ${CURL_TIMEOUT} -X POST "${BASE}/api/query" \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "what is ETF?",
    "top_k": 10,
    "use_hybrid": true,
    "rrf_k": 60,
    "rerank": false
  }')

echo "Response:"
echo "${RESPONSE1}" | jq '.'

FUSION_OVERLAP=$(echo "${RESPONSE1}" | jq -r '.metrics.fusion_overlap // 0')

if [ "${FUSION_OVERLAP}" -ge 1 ]; then
  echo "✅ Smoke Test 1 PASSED: fusion_overlap=${FUSION_OVERLAP} >= 1"
else
  echo "❌ Smoke Test 1 FAILED: fusion_overlap=${FUSION_OVERLAP} < 1"
  echo "RRF ID alignment may be abnormal"
  exit 1
fi

echo ""

# ========================================
# Smoke Test 2: Trigger Rate Constraint
# ========================================
echo "### Smoke Test 2: Trigger Rate Constraint ###"

TRIGGERED_COUNT=0
TOTAL_ATTEMPTS=50  # Use 50 instead of 100 for faster testing

for i in $(seq 1 ${TOTAL_ATTEMPTS}); do
  RESPONSE=$(curl -sSf --max-time ${CURL_TIMEOUT} -X POST "${BASE}/api/query" \
    -H 'Content-Type: application/json' \
    -d '{
      "question": "index fund",
      "top_k": 10,
      "use_hybrid": true,
      "rrf_k": 60,
      "rerank": true,
      "rerank_if_margin_below": 0.12,
      "max_rerank_trigger_rate": 0.25,
      "rerank_budget_ms": 25
    }')
  
  TRIGGERED=$(echo "${RESPONSE}" | jq -r '.metrics.rerank_triggered // false')
  if [ "${TRIGGERED}" == "true" ]; then
    TRIGGERED_COUNT=$((TRIGGERED_COUNT + 1))
  fi
  
  # Progress indicator
  if [ $((i % 10)) -eq 0 ]; then
    echo "Progress: ${i}/${TOTAL_ATTEMPTS} (triggered: ${TRIGGERED_COUNT})"
  fi
done

TRIGGER_RATE=$(echo "scale=4; ${TRIGGERED_COUNT} / ${TOTAL_ATTEMPTS}" | bc)
MAX_ALLOWED=0.30  # Allow some flexibility (0.25 + 0.05 buffer)

echo "Total attempts: ${TOTAL_ATTEMPTS}"
echo "Triggered: ${TRIGGERED_COUNT}"
echo "Trigger rate: ${TRIGGER_RATE}"

if (( $(echo "${TRIGGER_RATE} <= ${MAX_ALLOWED}" | bc -l) )); then
  echo "✅ Smoke Test 2 PASSED: trigger_rate=${TRIGGER_RATE} <= ${MAX_ALLOWED}"
else
  echo "❌ Smoke Test 2 FAILED: trigger_rate=${TRIGGER_RATE} > ${MAX_ALLOWED}"
  exit 1
fi

echo ""

# ========================================
# Smoke Test 3: best.yaml Deep Merge
# ========================================
echo "### Smoke Test 3: best.yaml Deep Merge ###"

# Step A: Initial PUT
echo "Step A: Initial PUT with hybrid and metrics..."
RESPONSE_A=$(curl -sSf --max-time ${CURL_TIMEOUT} -X PUT "${BASE}/api/best" \
  -H 'Content-Type: application/json' \
  -d '{
    "pipeline": {
      "hybrid": true,
      "rrf_k": 60,
      "gated_rerank": {
        "top_k": 20,
        "margin": 0.12,
        "trigger_rate_cap": 0.25,
        "budget_ms": 25
      }
    },
    "metrics": {
      "recall_at_10": 0.72
    }
  }')

echo "Response A:"
echo "${RESPONSE_A}" | jq '.'

# Verify initial write
HYBRID_A=$(echo "${RESPONSE_A}" | jq -r '.pipeline.hybrid // false')
RECALL_A=$(echo "${RESPONSE_A}" | jq -r '.metrics.recall_at_10 // 0')

if [ "${HYBRID_A}" != "true" ] || [ "$(echo "${RECALL_A} == 0.72" | bc)" -ne 1 ]; then
  echo "❌ Smoke Test 3 Step A FAILED: Initial PUT validation failed"
  exit 1
fi

echo "✅ Step A PASSED"

# Step B: Second PUT (partial update)
echo "Step B: Second PUT with only metrics.p95_ms..."
RESPONSE_B=$(curl -sSf --max-time ${CURL_TIMEOUT} -X PUT "${BASE}/api/best" \
  -H 'Content-Type: application/json' \
  -d '{
    "metrics": {
      "p95_ms": 140
    }
  }')

echo "Response B:"
echo "${RESPONSE_B}" | jq '.'

# Verify deep merge
HYBRID_B=$(echo "${RESPONSE_B}" | jq -r '.pipeline.hybrid // false')
RECALL_B=$(echo "${RESPONSE_B}" | jq -r '.metrics.recall_at_10 // 0')
P95_B=$(echo "${RESPONSE_B}" | jq -r '.metrics.p95_ms // 0')

if [ "${HYBRID_B}" != "true" ]; then
  echo "❌ Smoke Test 3 Step B FAILED: pipeline.hybrid not preserved (got: ${HYBRID_B})"
  exit 1
fi

if [ "$(echo "${RECALL_B} == 0.72" | bc)" -ne 1 ]; then
  echo "❌ Smoke Test 3 Step B FAILED: metrics.recall_at_10 not preserved (got: ${RECALL_B})"
  exit 1
fi

if [ "$(echo "${P95_B} == 140" | bc)" -ne 1 ]; then
  echo "❌ Smoke Test 3 Step B FAILED: metrics.p95_ms not updated (got: ${P95_B})"
  exit 1
fi

echo "✅ Step B PASSED"

# Step C: Verify file contents
echo "Step C: Verify best.yaml file contents..."
BEST_YAML_PATH="reports/_latest/best.yaml"

if [ ! -f "${BEST_YAML_PATH}" ]; then
  echo "⚠️  Warning: ${BEST_YAML_PATH} not found, skipping file check"
else
  # Check for required fields using grep
  if grep -q "hybrid: true" "${BEST_YAML_PATH}" && \
     grep -q "recall_at_10: 0.72" "${BEST_YAML_PATH}" && \
     grep -q "p95_ms: 140" "${BEST_YAML_PATH}"; then
    echo "✅ Step C PASSED: best.yaml contains all required fields"
  else
    echo "❌ Smoke Test 3 Step C FAILED: best.yaml missing required fields"
    echo "File contents:"
    cat "${BEST_YAML_PATH}"
    exit 1
  fi
fi

echo ""

# ========================================
# All tests passed
# ========================================
echo "=========================================="
echo "✅ SMOKE OK - All tests passed!"
echo "=========================================="

