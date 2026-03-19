#!/bin/bash
# Pre-demo checklist for 陈魁 broker demo
# =========================================
# Run before a live broker demo to verify both Live and Offline paths.
# Runtime path: default 8001, recovery restore_8001_readiness.sh. See docs/runbooks/RUNTIME_PATH_STANDARD.md.
#
# Usage: bash scripts/demo_pre_checklist.sh [--strict]
#   --strict: exit 1 if workflow hints < 5 or offline pack < 5 items (drift guardrail)
#
# Output: results/demo_pre_checklist/YYYY-MM-DD_HHMMSS/CHECKLIST.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STRICT=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --strict) STRICT=true; shift ;;
    *) shift ;;
  esac
done

TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
OUT_DIR="$REPO_DIR/results/demo_pre_checklist/$TIMESTAMP"

cd "$REPO_DIR"
mkdir -p "$OUT_DIR"

echo "=========================================="
echo "Pre-Demo Checklist (Insurance Broker)"
echo "=========================================="
echo ""

# 0. Guardrail first (no backend needed; fail fast on drift)
echo "[0] Guardrail (question consistency, offline pack, copy-to-client)..."
if ! bash "$SCRIPT_DIR/guardrail_broker_demo.sh" 2>&1 | tee "$OUT_DIR/guardrail_log.txt"; then
  echo ""
  echo "  FAIL: Guardrail failed. Fix drift before demo. See $OUT_DIR/guardrail_log.txt"
  exit 1
fi
echo ""

# 1. Env check
echo "[1] Environment..."
QDRANT_OK=false
for f in .env .env.cloudrun; do
  [ -f "$f" ] && set -a && source "$f" 2>/dev/null && set +a
done
[ -n "${QDRANT_URL:-}" ] && [ -n "${QDRANT_API_KEY:-}" ] && QDRANT_OK=true
echo "  QDRANT_URL set: $([ -n "${QDRANT_URL:-}" ] && echo 'yes' || echo 'no')"
echo "  QDRANT_API_KEY set: $([ -n "${QDRANT_API_KEY:-}" ] && echo 'yes' || echo 'no')"
echo ""

# 2. Offline pack check
echo "[2] Offline pack..."
FALLBACK="$REPO_DIR/ui/src/assets/demo_fallback.json"
FALLBACK_OK=false
FALLBACK_HAS_ANSWERS=false
WORKFLOW_OK="0"
if [ -f "$FALLBACK" ]; then
  ITEMS=$(python3 -c "import json; d=json.load(open('$FALLBACK')); print(len(d.get('items',[])))" 2>/dev/null || echo "0")
  [ "$ITEMS" -ge 5 ] 2>/dev/null && FALLBACK_OK=true
  echo "  demo_fallback.json: $ITEMS items"
  # Check if answers exist (empty = DEFAULT_FALLBACK_ITEMS used at runtime)
  ANSWERS=$(python3 -c "
import json
d=json.load(open('$FALLBACK'))
items=d.get('items',[])
with_ans=sum(1 for i in items if (i.get('answer') or '').strip())
print(with_ans)
" 2>/dev/null || echo "0")
  [ "$ANSWERS" -ge 5 ] 2>/dev/null && FALLBACK_HAS_ANSWERS=true
  echo "  Items with answers: $ANSWERS"
  # Workflow alignment: Q1–Q5 should have 客户可准备 + 经纪人可进一步询问
  WORKFLOW_OK=$(python3 -c "
import json
d=json.load(open('$FALLBACK'))
items=d.get('items',[])
ok=sum(1 for i in items if '客户可准备' in (i.get('answer') or '') and '经纪人可进一步询问' in (i.get('answer') or ''))
print(ok)
" 2>/dev/null || echo "0")
  echo "  Workflow hints (客户可准备+经纪人可进一步询问): $WORKFLOW_OK/5"
else
  echo "  demo_fallback.json: not found (DEFAULT_FALLBACK_ITEMS used)"
  FALLBACK_OK=true
  FALLBACK_HAS_ANSWERS=true
fi
echo ""

# 3. Backend health (if running)
echo "[3] Backend (if running)..."
BACKEND_UP=false
if curl -sf http://127.0.0.1:8001/healthz >/dev/null 2>&1; then
  BACKEND_UP=true
  echo "  Backend: UP (8001)"
else
  echo "  Backend: not running"
fi
echo ""

# 4. Quick validate (if backend up)
echo "[4] Live validation (if backend up)..."
VALIDATE_PASS=false
if [ "$BACKEND_UP" = true ]; then
  if bash "$SCRIPT_DIR/demo_quick_validate.sh" 2>&1 | tee "$OUT_DIR/validate_log.txt"; then
    VALIDATE_PASS=true
  fi
  LATEST=$(ls -td results/demo_quick_validate/*/REPORT.md 2>/dev/null | head -1)
  [ -n "$LATEST" ] && cp "$LATEST" "$OUT_DIR/validate_REPORT.md"
else
  echo "  Skipped (backend not running)"
fi
echo ""

# 5. Write checklist
echo "[5] Writing checklist..."
{
  echo "# Pre-Demo Checklist Report"
  echo ""
  echo "**Timestamp:** $TIMESTAMP"
  echo ""
  echo "## Summary"
  echo ""
  echo "| Check | Status |"
  echo "|-------|--------|"
  echo "| Qdrant env | $([ "$QDRANT_OK" = true ] && echo '✅ Set' || echo '❌ Missing') |"
  echo "| Offline pack | $([ "$FALLBACK_OK" = true ] && echo '✅ Ready' || echo '❌ Missing') |"
  echo "| Workflow hints (Q1–Q5) | $([ "$WORKFLOW_OK" = "5" ] 2>/dev/null && echo '✅ Aligned' || echo '⚠️ Run demo_quick_validate to refresh') |"
  echo "| Copy-to-client boundary | $(python3 "$SCRIPT_DIR/verify_copy_to_client_guardrail.py" >/dev/null 2>&1 && echo '✅ Clean' || echo '❌ Check guardrail') |"
  echo "| Backend | $([ "$BACKEND_UP" = true ] && echo '✅ Running' || echo '❌ Not running') |"
  echo "| Live validate | $([ "$VALIDATE_PASS" = true ] && echo '✅ PASS' || echo '❌ FAIL / skipped') |"
  echo ""
  echo "## Which path to use"
  echo ""
  if [ "$VALIDATE_PASS" = true ]; then
    echo "**→ Use Live path.** Ask any of the 5 questions or type custom questions."
  else
    echo "**→ Use Offline path.** Click only the 5 recommended questions. Do not type custom questions."
  fi
  echo ""
  echo "## Demo commands"
  echo ""
  echo "1. Start: \`bash scripts/run_demo_local.sh\`"
  echo "2. URL: http://localhost:5173/demo"
  echo "3. If Live fails mid-demo: Refresh page, click 5 sample questions (Offline mode)"
  echo ""
  echo "## Recommended 5 questions (in order)"
  echo ""
  echo "1. 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？"
  echo "2. 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？"
  echo "3. 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？"
  echo "4. 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？"
  echo "5. 出险后理赔流程是怎样的？"
  echo ""
} > "$OUT_DIR/CHECKLIST.md"

echo "=========================================="
echo "Checklist: $OUT_DIR/CHECKLIST.md"
echo "=========================================="

# --strict: fail on drift (workflow hints < 5 or offline pack < 5)
if [ "$STRICT" = true ]; then
  if [ "$WORKFLOW_OK" != "5" ] 2>/dev/null; then
    echo ""
    echo "STRICT: Workflow hints $WORKFLOW_OK/5 (need 5). Run demo_quick_validate.sh with backend up to refresh."
    exit 1
  fi
  if [ -f "$FALLBACK" ]; then
    ITEMS_STRICT=$(python3 -c "import json; d=json.load(open('$FALLBACK')); print(len(d.get('items',[])))" 2>/dev/null || echo "0")
    if [ "${ITEMS_STRICT:-0}" -lt 5 ] 2>/dev/null; then
      echo ""
      echo "STRICT: Offline pack has $ITEMS_STRICT items (need 5)."
      exit 1
    fi
  else
    echo ""
    echo "STRICT: demo_fallback.json not found."
    exit 1
  fi
  echo "STRICT: All checks passed."
fi
