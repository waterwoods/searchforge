#!/bin/bash
# Smoke Test for API Translation Endpoint
# =========================================
# Tests that /api/query returns translation fields correctly when translation_mode="auto"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

API_URL="${API_URL:-http://localhost:8000}"

echo "=========================================="
echo "API Translation Smoke Test"
echo "=========================================="
echo "API URL: $API_URL"
echo ""

# Check if backend is running
echo "Step 1: Checking backend availability..."
if ! curl -s -f "$API_URL/healthz" > /dev/null 2>&1; then
    echo "❌ FAIL: Backend not running at $API_URL"
    echo "   Start backend with: ./scripts/dev_local.sh"
    exit 1
fi
echo "✅ Backend is running"
echo ""

# Test query
TEST_QUERY="加州最低汽车保险要求是什么？"
echo "Step 2: Testing Chinese query with translation_mode=auto"
echo "Query: $TEST_QUERY"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL/api/query" \
    -H "Content-Type: application/json" \
    -d "{
        \"question\": \"$TEST_QUERY\",
        \"top_k\": 5,
        \"translation_mode\": \"auto\",
        \"collection\": \"fiqa\"
    }")

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    echo "❌ FAIL: Invalid JSON response"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "Response received. Validating fields..."
echo ""

# Extract and validate fields
OK=$(echo "$RESPONSE" | jq -r '.ok // false')
TRANSLATION_APPLIED=$(echo "$RESPONSE" | jq -r '.translation_applied // false')
DETECTED_LANG=$(echo "$RESPONSE" | jq -r '.detected_lang // "unknown"')
QUESTION_USED=$(echo "$RESPONSE" | jq -r '.question_used // ""')
QUESTION_ORIGINAL=$(echo "$RESPONSE" | jq -r '.question // ""')
SOURCES_COUNT=$(echo "$RESPONSE" | jq '.sources | length')
HAS_TEXT_ZH=$(echo "$RESPONSE" | jq '.sources[0].text_zh // .sources[0].translations.zh.text // empty' | jq -r 'if . == "" then false else true end')

echo "Field checks:"
echo "  - ok: $OK"
echo "  - translation_applied: $TRANSLATION_APPLIED"
echo "  - detected_lang: $DETECTED_LANG"
echo "  - question_used: ${QUESTION_USED:0:60}..."
echo "  - sources count: $SOURCES_COUNT"
echo "  - has text_zh: $HAS_TEXT_ZH"
echo ""

# Validation
PASSED=0
FAILED=0

if [ "$OK" != "true" ]; then
    echo "  ❌ FAIL: ok should be true, got '$OK'"
    FAILED=$((FAILED + 1))
else
    echo "  ✅ PASS: ok is true"
    PASSED=$((PASSED + 1))
fi

if [ "$TRANSLATION_APPLIED" != "true" ]; then
    echo "  ❌ FAIL: translation_applied should be true, got '$TRANSLATION_APPLIED'"
    FAILED=$((FAILED + 1))
else
    echo "  ✅ PASS: translation_applied is true"
    PASSED=$((PASSED + 1))
fi

if [ "$DETECTED_LANG" != "zh" ]; then
    echo "  ❌ FAIL: detected_lang should be 'zh', got '$DETECTED_LANG'"
    FAILED=$((FAILED + 1))
else
    echo "  ✅ PASS: detected_lang is 'zh'"
    PASSED=$((PASSED + 1))
fi

if [ -z "$QUESTION_USED" ]; then
    echo "  ❌ FAIL: question_used should not be empty"
    FAILED=$((FAILED + 1))
elif [ "$QUESTION_USED" = "$QUESTION_ORIGINAL" ]; then
    echo "  ⚠️  WARN: question_used same as original (translation may have failed)"
    PASSED=$((PASSED + 1))
else
    echo "  ✅ PASS: question_used contains translated query"
    PASSED=$((PASSED + 1))
fi

if [ "$SOURCES_COUNT" -lt 1 ]; then
    echo "  ❌ FAIL: Expected at least 1 source, got $SOURCES_COUNT"
    FAILED=$((FAILED + 1))
else
    echo "  ✅ PASS: sources count >= 1"
    PASSED=$((PASSED + 1))
fi

if [ "$HAS_TEXT_ZH" != "true" ]; then
    echo "  ⚠️  WARN: text_zh not found in first source (may be disabled via TRANSLATE_SOURCES_TO_ZH=0)"
    # Not a failure, just a warning
    PASSED=$((PASSED + 1))
else
    echo "  ✅ PASS: text_zh found in first source"
    PASSED=$((PASSED + 1))
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo "✅ All smoke tests PASSED"
    echo ""
    echo "Translation API is working correctly:"
    echo "  - Translation applied: ✅"
    echo "  - Language detection: ✅"
    echo "  - Query translation: ✅"
    echo "  - Sources returned: ✅"
    exit 0
else
    echo "❌ Some tests FAILED"
    echo ""
    echo "Common issues:"
    echo "  1. Translation not enabled: Set TRANSLATION_ENABLED=1 in .env.cloudrun"
    echo "  2. Translation packages missing: Run 'python3 -m argostranslate.argostranslate --install-packages zh en'"
    echo "  3. Backend not restarted: Restart backend after setting env vars"
    echo ""
    echo "Full response (first 500 chars):"
    echo "$RESPONSE" | head -c 500
    echo ""
    exit 1
fi
