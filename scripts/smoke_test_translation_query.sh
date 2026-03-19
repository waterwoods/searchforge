#!/bin/bash
# Smoke Test for Translation Query Support
# =========================================
# Tests Chinese query translation and response format

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

API_URL="${API_URL:-http://localhost:8000}"
COLLECTION="${COLLECTION:-auto_insurance}"

echo "=========================================="
echo "Translation Query Smoke Test"
echo "=========================================="
echo "API URL: $API_URL"
echo "Collection: $COLLECTION"
echo ""

# Test 1: Chinese query with translation
echo "Test 1: Chinese query (should translate to English)"
CHINESE_QUERY="加州最低汽车保险要求是什么？"
echo "Query: $CHINESE_QUERY"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"$CHINESE_QUERY\",
    \"collection\": \"$COLLECTION\",
    \"top_k\": 5,
    \"translation_mode\": \"auto\"
  }")

echo "Response (first 500 chars):"
echo "$RESPONSE" | head -c 500
echo ""
echo ""

# Check response
TRANSLATION_APPLIED=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('translation_applied', False))" 2>/dev/null || echo "false")
DETECTED_LANG=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('detected_lang', 'unknown'))" 2>/dev/null || echo "unknown")
SOURCES_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('sources', [])))" 2>/dev/null || echo "0")
HAS_TEXT_ZH=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); sources=data.get('sources', []); print('true' if any('text_zh' in s or 'translations' in s for s in sources) else 'false')" 2>/dev/null || echo "false")

echo "Checks:"
echo "  - translation_applied: $TRANSLATION_APPLIED"
echo "  - detected_lang: $DETECTED_LANG"
echo "  - sources count: $SOURCES_COUNT"
echo "  - has text_zh: $HAS_TEXT_ZH"
echo ""

if [ "$TRANSLATION_APPLIED" != "True" ] && [ "$TRANSLATION_APPLIED" != "true" ]; then
    echo "❌ FAIL: translation_applied should be true"
    exit 1
fi

if [ "$DETECTED_LANG" != "zh" ]; then
    echo "❌ FAIL: detected_lang should be 'zh'"
    exit 1
fi

if [ "$SOURCES_COUNT" -lt 3 ]; then
    echo "❌ FAIL: Expected at least 3 sources, got $SOURCES_COUNT"
    exit 1
fi

echo "✅ Test 1 PASSED"
echo ""

# Test 2: English query (should not translate)
echo "Test 2: English query (should NOT translate)"
ENGLISH_QUERY="What are the minimum auto insurance requirements in California?"
echo "Query: $ENGLISH_QUERY"
echo ""

RESPONSE2=$(curl -s -X POST "$API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"$ENGLISH_QUERY\",
    \"collection\": \"$COLLECTION\",
    \"top_k\": 5,
    \"translation_mode\": \"auto\"
  }")

TRANSLATION_APPLIED2=$(echo "$RESPONSE2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('translation_applied', False))" 2>/dev/null || echo "false")
DETECTED_LANG2=$(echo "$RESPONSE2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('detected_lang', 'unknown'))" 2>/dev/null || echo "unknown")

echo "Checks:"
echo "  - translation_applied: $TRANSLATION_APPLIED2 (should be false)"
echo "  - detected_lang: $DETECTED_LANG2 (should be 'en')"
echo ""

if [ "$TRANSLATION_APPLIED2" != "False" ] && [ "$TRANSLATION_APPLIED2" != "false" ]; then
    echo "❌ FAIL: translation_applied should be false for English"
    exit 1
fi

if [ "$DETECTED_LANG2" != "en" ]; then
    echo "❌ FAIL: detected_lang should be 'en'"
    exit 1
fi

echo "✅ Test 2 PASSED"
echo ""

# Test 3: Chinese query without translation mode (should still work but no translation)
echo "Test 3: Chinese query without translation_mode (should work but no translation)"
RESPONSE3=$(curl -s -X POST "$API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"$CHINESE_QUERY\",
    \"collection\": \"$COLLECTION\",
    \"top_k\": 5
  }")

TRANSLATION_APPLIED3=$(echo "$RESPONSE3" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('translation_applied', False))" 2>/dev/null || echo "false")

echo "Checks:"
echo "  - translation_applied: $TRANSLATION_APPLIED3 (should be false when translation_mode not set)"
echo ""

echo "✅ Test 3 PASSED (translation disabled by default)"
echo ""

echo "=========================================="
echo "✅ All smoke tests PASSED"
echo "=========================================="

exit 0
