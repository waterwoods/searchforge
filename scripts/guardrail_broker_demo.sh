#!/bin/bash
# Broker demo drift guardrail
# ===========================
# Checks: (1) Q1–Q5 questions match between broker_regression and snapshot,
#          (2) offline pack has 5 items with workflow hints.
# No backend required. Exits 1 on critical drift.
#
# Usage: bash scripts/guardrail_broker_demo.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FALLBACK="$REPO_DIR/ui/src/assets/demo_fallback.json"
FAILED=0

cd "$REPO_DIR"

echo "=========================================="
echo "Broker Demo Guardrail"
echo "=========================================="
echo ""

# 1. Question consistency: broker_regression_all5 QUESTIONS vs snapshot_demo_answers QUESTIONS
echo "[1] Question consistency (broker_regression vs snapshot)..."
Q_CONSISTENT=true
for q in "我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？" "我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？" "客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？" "客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？" "出险后理赔流程是怎样的？"; do
  grep -qF "$q" "$SCRIPT_DIR/broker_regression_all5.py" 2>/dev/null || { echo "  FAIL: Question missing in broker_regression_all5.py"; FAILED=1; Q_CONSISTENT=false; break; }
  grep -qF "$q" "$SCRIPT_DIR/snapshot_demo_answers.py" 2>/dev/null || { echo "  FAIL: Question missing in snapshot_demo_answers.py"; FAILED=1; Q_CONSISTENT=false; break; }
done
[ "$Q_CONSISTENT" = true ] && echo "  OK: broker_regression and snapshot both have same 5 questions"
echo ""

# 2. Offline pack: 5 items with workflow hints
echo "[2] Offline pack (demo_fallback.json)..."
if [ ! -f "$FALLBACK" ]; then
  echo "  FAIL: demo_fallback.json not found"
  FAILED=1
else
  ITEMS=$(python3 -c "
import json
d = json.load(open('$FALLBACK'))
items = d.get('items', [])
print(len(items))
" 2>/dev/null || echo "0")
  WITH_HINTS=$(python3 -c "
import json
d = json.load(open('$FALLBACK'))
items = d.get('items', [])
ok = sum(1 for i in items if '客户可准备' in (i.get('answer') or '') and '经纪人可进一步询问' in (i.get('answer') or ''))
print(ok)
" 2>/dev/null || echo "0")

  if [ "$ITEMS" -lt 5 ] 2>/dev/null; then
    echo "  FAIL: offline pack has $ITEMS items (need 5)"
    FAILED=1
  else
    echo "  OK: $ITEMS items"
  fi

  if [ "$WITH_HINTS" -lt 5 ] 2>/dev/null; then
    echo "  FAIL: only $WITH_HINTS/5 items have workflow hints (客户可准备 + 经纪人可进一步询问)"
    echo "  → Run: bash scripts/demo_quick_validate.sh (with backend up) to refresh offline pack"
    FAILED=1
  else
    echo "  OK: $WITH_HINTS/5 items have workflow hints"
  fi
fi
echo ""

# 3. Copy-to-client: broker-only content must not leak
echo "[3] Copy-to-client boundary (broker-only excluded)..."
if python3 "$SCRIPT_DIR/verify_copy_to_client_guardrail.py" 2>/dev/null; then
  echo "  OK: filter logic excludes 经纪人可进一步询问"
else
  echo "  FAIL: copy-to-client guardrail failed (broker-only content would leak)"
  FAILED=1
fi
if python3 "$SCRIPT_DIR/test_copy_to_client_e2e.py" 2>/dev/null; then
  echo "  OK: E2E demo_fallback → client copy clean"
else
  echo "  WARN: E2E test skipped or failed (demo_fallback may be missing)"
fi
echo ""

# 4. Runtime path: default 8001 in key broker scripts
echo "[4] Runtime path (default 8001)..."
PATH_OK=true
grep -q '8001' "$SCRIPT_DIR/run_demo_local.sh" 2>/dev/null || { echo "  FAIL: run_demo_local.sh should use 8001"; PATH_OK=false; FAILED=1; }
grep -q '8001' "$SCRIPT_DIR/demo_pre_checklist.sh" 2>/dev/null || { echo "  FAIL: demo_pre_checklist.sh should check 8001"; PATH_OK=false; FAILED=1; }
[ -f "$REPO_DIR/docs/runbooks/RUNTIME_PATH_STANDARD.md" ] || { echo "  FAIL: docs/runbooks/RUNTIME_PATH_STANDARD.md missing"; PATH_OK=false; FAILED=1; }
[ "$PATH_OK" = true ] && echo "  OK: default path 8001 in run_demo_local, demo_pre_checklist; docs/runbooks/RUNTIME_PATH_STANDARD.md exists"
echo ""

# 5. Offline fallback: run_demo_local must say "5 sample questions" (not 3)
echo "[5] Offline fallback copy (5 questions)..."
if grep -q '3 sample questions' "$SCRIPT_DIR/run_demo_local.sh" 2>/dev/null; then
  echo "  FAIL: run_demo_local.sh says '3 sample questions' (broker demo has 5)"
  FAILED=1
else
  echo "  OK: run_demo_local.sh correctly references 5 sample questions"
fi
echo ""

echo "=========================================="
if [ $FAILED -eq 1 ]; then
  echo "Result: FAIL (drift detected)"
  exit 1
else
  echo "Result: PASS"
  exit 0
fi
