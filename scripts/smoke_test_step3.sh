#!/bin/bash
# Smoke Test for Step 3: Translation Retrieval Pipeline
# =====================================================
# Tests end-to-end translation retrieval and response format

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

API_URL="${API_URL:-http://localhost:8000}"
COLLECTION="${COLLECTION:-auto_insurance}"

echo "=========================================="
echo "Step 3: Translation Retrieval Smoke Test"
echo "=========================================="
echo "API URL: $API_URL"
echo "Collection: $COLLECTION"
echo ""

# Check if backend is running
echo "Step 1: Checking backend availability..."
if ! curl -s -f "$API_URL/healthz" > /dev/null 2>&1; then
    echo "❌ FAIL: Backend not running at $API_URL"
    echo "   Start backend with: python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8000"
    exit 1
fi
echo "✅ Backend is running"
echo ""

# Test queries
declare -a TEST_QUERIES=(
    "加州最低汽车保险要求是什么？"
    "车险理赔流程怎么走？"
    "SR-22 是什么，什么时候需要？"
)

PASSED=0
FAILED=0

for idx in "${!TEST_QUERIES[@]}"; do
    query="${TEST_QUERIES[$idx]}"
    test_num=$((idx + 1))
    
    echo "Test $test_num: Chinese query with translation"
    echo "Query: $query"
    echo ""
    
    RESPONSE=$(curl -s -X POST "$API_URL/api/query" \
        -H "Content-Type: application/json" \
        -d "{
            \"question\": \"$query\",
            \"top_k\": 5,
            \"translation_mode\": \"auto\"
        }")
    
    # Check response structure
    if ! echo "$RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        echo "❌ FAIL: Invalid JSON response"
        echo "Response: $RESPONSE"
        FAILED=$((FAILED + 1))
        continue
    fi
    
    # Extract fields
    OK=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('ok', False))" 2>/dev/null || echo "false")
    TRANSLATION_APPLIED=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('translation_applied', False))" 2>/dev/null || echo "false")
    QUESTION_USED=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('question_used', ''))" 2>/dev/null || echo "")
    DETECTED_LANG=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('detected_lang', 'unknown'))" 2>/dev/null || echo "unknown")
    SOURCES_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('sources', [])))" 2>/dev/null || echo "0")
    HAS_TITLE_ZH=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); sources=data.get('sources', []); print('true' if any('title_zh' in s or 'translations' in s for s in sources) else 'false')" 2>/dev/null || echo "false")
    
    echo "Checks:"
    echo "  - ok: $OK"
    echo "  - translation_applied: $TRANSLATION_APPLIED"
    echo "  - detected_lang: $DETECTED_LANG"
    echo "  - question_used: ${QUESTION_USED:0:60}..."
    echo "  - sources count: $SOURCES_COUNT"
    echo "  - has title_zh: $HAS_TITLE_ZH"
    echo ""
    
    # Validation
    TESTS_PASSED=0
    TESTS_FAILED=0
    
    if [ "$OK" != "True" ] && [ "$OK" != "true" ]; then
        echo "  ❌ FAIL: ok should be true"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo "  ✅ PASS: ok is true"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    
    if [ "$TRANSLATION_APPLIED" != "True" ] && [ "$TRANSLATION_APPLIED" != "true" ]; then
        echo "  ❌ FAIL: translation_applied should be true for Chinese query"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo "  ✅ PASS: translation_applied is true"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    
    if [ -z "$QUESTION_USED" ]; then
        echo "  ❌ FAIL: question_used field is missing"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    elif [ "$QUESTION_USED" = "$query" ]; then
        echo "  ⚠️  WARN: question_used same as original (translation may have failed)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "  ✅ PASS: question_used contains translated query"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    
    if [ "$DETECTED_LANG" != "zh" ]; then
        echo "  ❌ FAIL: detected_lang should be 'zh', got '$DETECTED_LANG'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo "  ✅ PASS: detected_lang is 'zh'"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    
    if [ "$SOURCES_COUNT" -lt 3 ]; then
        echo "  ❌ FAIL: Expected at least 3 sources, got $SOURCES_COUNT"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo "  ✅ PASS: sources count >= 3"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo "✅ Test $test_num PASSED"
        PASSED=$((PASSED + 1))
    else
        echo "❌ Test $test_num FAILED ($TESTS_FAILED checks failed)"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo "✅ All smoke tests PASSED"
    exit 0
else
    echo "❌ Some tests FAILED"
    echo ""
    echo "Common issues:"
    echo "  1. Translation not enabled: Set TRANSLATION_ENABLED=1"
    echo "  2. Translation packages missing: Run 'python -m argostranslate.argostranslate --install-packages zh en'"
    echo "  3. Backend not running: Start with uvicorn"
    exit 1
fi
